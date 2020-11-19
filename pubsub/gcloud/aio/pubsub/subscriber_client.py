import json
import os
from typing import Any
from typing import AnyStr
from typing import Callable
from typing import Dict
from typing import IO
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from gcloud.aio.auth import AioSession
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token
from google.api_core import exceptions
from google.cloud.pubsub_v1.subscriber.futures import StreamingPullFuture
from google.cloud.pubsub_v1.subscriber.message import Message
from google.cloud.pubsub_v1.types import FlowControl as _FlowControl

from .subscriber_message import SubscriberMessage

API_ROOT = 'https://pubsub.googleapis.com'
VERIFY_SSL = True

SCOPES = [
    'https://www.googleapis.com/auth/pubsub'
]

PUBSUB_EMULATOR_HOST = os.environ.get('PUBSUB_EMULATOR_HOST')
if PUBSUB_EMULATOR_HOST:
    API_ROOT = f'http://{PUBSUB_EMULATOR_HOST}'
    VERIFY_SSL = False

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
    from google.cloud import pubsub
    from aiohttp import ClientSession as Session

    class SubscriberClient:  # type: ignore[no-redef]
        def __init__(self, *,
                     service_file: Optional[Union[str, IO[AnyStr]]] = None,
                     token: Optional[Token] = None,
                     session: Optional[Session] = None,
                     **kwargs: Dict[str, Any]) -> None:
            self._subscriber = pubsub.SubscriberClient(**kwargs)
            self.session = AioSession(session, verify_ssl=VERIFY_SSL)
            self.token = token or Token(service_file=service_file,
                                        scopes=SCOPES,
                                        session=self.session.session)

        async def _headers(self) -> Dict[str, str]:
            if PUBSUB_EMULATOR_HOST:
                return {}

            token = await self.token.get()
            return {
                'Authorization': f'Bearer {token}'
            }

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

        # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/pull
        async def pull(self, subscription: str, max_messages: int,
                       *, session: Optional[Session] = None
                       ) -> List[SubscriberMessage]:
            """
            Pull messages from subscription
            """
            url = f'{API_ROOT}/v1/{subscription}:pull'
            headers = await self._headers()
            body = {
                'maxMessages': max_messages,
            }
            encoded = json.dumps(body).encode()
            s = AioSession(session) if session else self.session
            resp = await s.post(url, data=encoded, headers=headers)
            resp = await resp.json()
            return [
                SubscriberMessage.from_api_dict(m)
                for m in resp['receivedMessages']
            ]

        # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/acknowledge
        async def acknowledge(self, subscription: str, ack_ids: List[str],
                              *, session: Optional[Session] = None) -> None:
            """
            Acknowledge messages by ackIds
            """
            url = f'{API_ROOT}/v1/{subscription}:acknowledge'
            headers = await self._headers()
            body = {
                'ackIds': ack_ids,
            }
            encoded = json.dumps(body).encode()
            s = AioSession(session) if session else self.session
            await s.post(url, data=encoded, headers=headers)


        # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/modifyAckDeadline
        async def modify_ack_deadline(self, subscription: str,
                                      ack_ids: List[str],
                                      ack_deadline_seconds: int,
                                      *, session: Optional[Session] = None
                                      ) -> None:
            """
            Modify messages' ack deadline.
            Set ack deadline to 0 to nack messages.
            """
            url = f'{API_ROOT}/v1/{subscription}:modifyAckDeadline'
            headers = await self._headers()
            body = {
                'ackIds': ack_ids,
                'ackDeadlineSeconds': ack_deadline_seconds,
            }
            s = AioSession(session) if session else self.session
            await s.post(url, data=json.dumps(body).encode('utf-8'), headers=headers)
