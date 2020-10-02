import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

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
