from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from google.cloud.pubsub_v1.subscriber.message import Message
from google.cloud.pubsub_v1.types import FlowControl as _FlowControl

from .subscriber_message import SubscriberMessage

class FlowControl:
    def __init__(self, *args: List[Any], **kwargs: Dict[str, Any]) -> None:
        """
        FlowControl transitional wrapper.
        (FlowControl fields docs)[https://github.com/googleapis/python-pubsub/blob/v1.7.0/google/cloud/pubsub_v1/types.py#L124-L166]  # pylint: disable=line-too-long
        Google uses a named tuple; here are the fields, defaults:
        - max_bytes: int = 100 * 1024 * 1024
        - max_messages: int = 1000
        - max_lease_duration: int = 1 * 60 * 60
        - max_duration_per_lease_extension: int = 0
        """
        self._flow_control = _FlowControl(*args, **kwargs)

    def __repr__(self) -> str:
        result: str = self._flow_control.__repr__()
        return result

    def __getitem__(self, index: int) -> int:
        result: int = self._flow_control[index]
        return result

    def __getattr__(self, attr: str) -> Any:
        return getattr(self._flow_control, attr)

if BUILD_GCLOUD_REST:
    from google.cloud import pubsub_v1 as pubsub
    from google.cloud.pubsub_v1.subscriber.futures import StreamingPullFuture


    class SubscriberClient:
        def __init__(self, **kwargs: Dict[str, Any]) -> None:
            self._subscriber = pubsub.SubscriberClient(**kwargs)

        def create_subscription(self,
                                subscription: str,
                                topic: str,
                                **kwargs: Dict[str, Any]
                                ) -> None:
            """
            Create subscription if it does not exist. Check out the official
            [create_subscription docs](https://github.com/googleapis/google-cloud-python/blob/11c72ade8b282ae1917fba19e7f4e0fe7176d12b/pubsub/google/cloud/pubsub_v1/gapic/subscriber_client.py#L236)  # pylint: disable=line-too-long
            for more details
            """
            try:
                self._subscriber.create_subscription(
                    subscription,
                    topic,
                    **kwargs
                )
            except exceptions.AlreadyExists:
                pass

        def subscribe(self,
                      subscription: str,
                      callback: Callable[[SubscriberMessage], Any],
                      *,
                      flow_control: Union[FlowControl, Tuple[int, ...]] = ()
                      ) -> StreamingPullFuture:
            """
            Pass call to the google-cloud-pubsub SubscriberClient class.
            This method will most likely be deprecated once gcloud-rest-pubsub
            stop using google-cloud-pubsub under the hood. If this is
            what you need we strongly recommend using official library.

            """
            sub_keepalive: StreamingPullFuture = (
                self._subscriber.subscribe(
                    subscription,
                    self._wrap_callback(callback),
                    flow_control=flow_control))

            return sub_keepalive

        @staticmethod
        def _wrap_callback(callback: Callable[[SubscriberMessage], None]
                           ) -> Callable[[Message], None]:
            """
            Make callback work with vanilla
            google.cloud.pubsub_v1.subscriber.message.Message

            """
            def _callback_wrapper(message: Message) -> None:
                callback(SubscriberMessage.from_google_cloud(message))

            return _callback_wrapper

else:
    import asyncio
    import concurrent.futures
    import signal


    from google.api_core import exceptions
    from google.cloud import pubsub

    from .utils import convert_google_future_to_concurrent_future


    class SubscriberClient:  # type: ignore[no-redef]
        def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None,
                     **kwargs: Dict[str, Any]) -> None:
            self._subscriber = pubsub.SubscriberClient(**kwargs)
            self.loop = loop or asyncio.get_event_loop()

        def create_subscription(self,
                                subscription: str,
                                topic: str,
                                **kwargs: Dict[str, Any]
                                ) -> None:
            """
            Create subscription if it does not exist. Check out the official
            [create_subscription docs](https://github.com/googleapis/google-cloud-python/blob/11c72ade8b282ae1917fba19e7f4e0fe7176d12b/pubsub/google/cloud/pubsub_v1/gapic/subscriber_client.py#L236)  # pylint: disable=line-too-long
            for more details
            """
            try:
                self._subscriber.create_subscription(
                    subscription,
                    topic,
                    **kwargs
                )
            except exceptions.AlreadyExists:
                pass

        def subscribe(self,
                      subscription: str,
                      callback: Callable[[SubscriberMessage], Any],
                      *,
                      flow_control: Union[FlowControl, Tuple[int, ...]] = ()
                      ) -> asyncio.Future:  # type: ignore
            """
            Create subscription through pubsub client, hijack the returned
            "non-concurrent Future" and coerce it into being a "concurrent
            Future", wrap it into a asyncio Future and return it.
            """
            sub_keepalive: asyncio.Future = (  # type: ignore
                self._subscriber.subscribe(
                    subscription,
                    self._wrap_callback(callback),
                    flow_control=flow_control))

            convert_google_future_to_concurrent_future(
                sub_keepalive, loop=self.loop)

            _ = asyncio.wrap_future(sub_keepalive)
            self.loop.add_signal_handler(signal.SIGTERM, sub_keepalive.cancel)

            return sub_keepalive

        def run_forever(self,
                        sub_keepalive: asyncio.Future) -> None:  # type: ignore
            """
            Start the asyncio loop, running until it is either SIGTERM-ed or
            killed by keyboard interrupt. The Future parameter is used to
            cancel subscription Future in the case that an unexpected exception
            is thrown. You can also directly pass the `.subscribe()` method
            call instead like so:
                sub.run_forever(sub.subscribe(callback))
            """
            try:
                self.loop.run_forever()
            except (KeyboardInterrupt, concurrent.futures.CancelledError):
                pass
            finally:
                # 1. stop the `SubscriberClient` future, which will prevent
                #    more tasks from being leased
                if not sub_keepalive.cancelled():
                    sub_keepalive.cancel()
                # 2. cancel the tasks we already have, which should just be
                #    `worker` instances; note they have
                #    `except CancelledError: pass`
                for task in asyncio.Task.all_tasks(loop=self.loop):
                    task.cancel()
                # 3. stop the `asyncio` event loop
                self.loop.stop()

        def _wrap_callback(self,
                           callback: Callable[[SubscriberMessage], None]
                           ) -> Callable[[Message], None]:
            """Schedule callback to be called from the event loop"""
            def _callback_wrapper(message: Message) -> None:
                asyncio.run_coroutine_threadsafe(
                    callback(  # type: ignore
                        SubscriberMessage.from_google_cloud(
                            message)),
                    self.loop)

            return _callback_wrapper
