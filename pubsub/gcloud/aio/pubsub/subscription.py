import asyncio
import concurrent.futures
import signal
from asyncio import Future  # pylint: disable=ungrouped-imports
from typing import Any
from typing import Callable
from typing import Optional

from google.api_core import exceptions
from google.cloud import pubsub
from google.cloud.pubsub_v1.subscriber.message import Message
from google.cloud.pubsub_v1.types import FlowControl
from google.cloud.pubsub_v1.types import Scheduler

from .utils import convert_google_future_to_concurrent_future


class Subscription:

    def __init__(self,
                 subscription: str,
                 *,
                 loop: Optional[asyncio.AbstractEventLoop] = None
                 ) -> None:
        self.subscription = subscription
        self._subscriber = pubsub.SubscriberClient()

        if not loop:
            loop = asyncio.get_event_loop()
        self.loop = loop

    def create_subscription(self,
                            topic: str,
                            *,
                            ack_deadline_seconds: int = 5
                            ) -> None:
        """Create subscription if it does not exist"""
        try:
            self._subscriber.create_subscription(
                self.subscription,
                topic,
                ack_deadline_seconds=ack_deadline_seconds
            )
        except exceptions.AlreadyExists:
            pass

    def subscribe(self,
                  callback: Callable[[Message], None],
                  *,
                  flow_control: FlowControl = (),
                  scheduler: Optional[Scheduler] = None
                  ) -> Future[Any]:
        """
        Create subscription through pubsub client, hijack the returned
        "non-concurrent Future" and coerce it into being a "concurrent Future",
        wrap it into a asyncio Future and return it.
        """
        sub_keepalive: Future[Any] = self._subscriber.subscribe(
            self.subscription,
            self._wrap_callback(callback),
            flow_control=flow_control,
            scheduler=scheduler
        )

        convert_google_future_to_concurrent_future(
            sub_keepalive, loop=self.loop
        )
        _ = asyncio.wrap_future(sub_keepalive)
        self.loop.add_signal_handler(signal.SIGTERM, sub_keepalive.cancel)

        return sub_keepalive

    def run_forever(self, sub_keepalive: Future[Any]) -> None:
        """
        Start the asyncio loop, running until it is either SIGTERM-ed or killed
        by keyboard interrupt. The Future parameter is used to cancel
        subscription Future in the case that an unexpected exception is thrown.
        You can also directly pass the `.subscribe()` method call instead like
        so:
            sub.run_forever(sub.subscribe(callback))
        """
        try:
            self.loop.run_forever()
        except (KeyboardInterrupt, concurrent.futures.CancelledError):
            pass
        finally:
            # 1. stop the `SubscriberClient` future, which will prevent more
            #    tasks from being leased
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
                       callback: Callable[[Message], None]
                       ) -> Callable[[Message], None]:
        """Wrap callback function in an asyncio task"""
        def _callback_wrapper(message: Message) -> None:
            self.loop.create_task(callback(message))

        return _callback_wrapper
