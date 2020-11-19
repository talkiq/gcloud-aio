import base64
import datetime
import json
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module

if BUILD_GCLOUD_REST:
    from google.cloud.pubsub_v1.subscriber.message import Message

    class SubscriberMessage:
        def __init__(self, *args: List[Any],
                     google_cloud_message: Message = None,
                     **kwargs: Dict[str, Any]) -> None:
            if google_cloud_message:
                self._message = google_cloud_message
                return
            self._message = Message(*args, **kwargs)

        @staticmethod
        def from_google_cloud(message: Message) -> 'SubscriberMessage':
            return SubscriberMessage(google_cloud_message=message)

        @property
        def google_cloud_message(self) -> Message:
            return self._message

        @property
        def message_id(self) -> str:  # indirects to a Google protobuff field
            return str(self._message.message_id)

        def __repr__(self) -> str:
            return repr(self._message)

        @property
        def attributes(self) -> Any:  # Google .ScalarMapContainer
            return self._message.attributes

        @property
        def data(self) -> bytes:
            return bytes(self._message.data)

        @property
        def publish_time(self) -> datetime.datetime:
            published: datetime.datetime = self._message.publish_time
            return published

        @property
        def ordering_key(self) -> str:
            return str(self._message.ordering_key)

        @property
        def size(self) -> int:
            return int(self._message.size)

        @property
        def ack_id(self) -> str:
            return str(self._message.ack_id)

        @property
        def delivery_attempt(self) -> Optional[int]:
            if self._message.delivery_attempt:
                return int(self._message.delivery_attempt)
            return None

        def ack(self) -> None:
            self._message.ack()

        def drop(self) -> None:
            self._message.drop()

        def modify_ack_deadline(self, seconds: int) -> None:
            self._message.modify_ack_deadline(seconds)

        def nack(self) -> None:
            self._message.nack()

else:

    def parse_publish_time(publish_time: str) -> datetime.datetime:
        try:
            return datetime.datetime.strptime(
                publish_time, '%Y-%m-%dT%H:%M:%S.%f%z')
        except ValueError:
            return datetime.datetime.strptime(
                publish_time, '%Y-%m-%dT%H:%M:%S%z')

    class SubscriberMessage:  # type: ignore[no-redef]
        def __init__(self, ack_id: str, message_id: str,
                     publish_time: 'datetime.datetime',
                     data: Dict[str, Any],
                     attributes: Dict[str, Any]):
            self.ack_id = ack_id
            self.message_id = message_id
            self.publish_time = publish_time
            self.data = data
            self.attributes = attributes
            self._callback = self._default_callback()

        @staticmethod
        def from_api_dict(received_message: Dict[str, Any]
                         ) -> 'SubscriberMessage':
            ack_id = received_message['ackId']
            message_id = received_message['message']['messageId']
            data = json.loads(
                base64.b64decode(received_message['message']['data']))
            attributes = received_message['message']['attributes']
            publish_time: datetime.datetime = parse_publish_time(
                received_message['message']['publishTime'])
            return SubscriberMessage(ack_id=ack_id, message_id=message_id,
                                     publish_time=publish_time, data=data,
                                     attributes=attributes)

        @staticmethod
        def _default_callback(
            ) -> Callable[['SubscriberMessage', bool], Awaitable[None]]:
            async def f(message: 'SubscriberMessage', ack: bool) -> None:
                raise NotImplementedError(
                    'Ack callback is not set for this message')
            return f

        def add_ack_callback(
                self,
                callback: Callable[['SubscriberMessage', bool], Awaitable[None]]
            ) -> None:
            self._callback = callback

        async def ack(self) -> None:
            await self._callback(self, True)

        async def nack(self) -> None:
            await self._callback(self, False)
