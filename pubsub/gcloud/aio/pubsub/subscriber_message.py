from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module

if BUILD_GCLOUD_REST:
    class Message:
        def __init__(self, **kwargs) -> None:
            raise NotImplementedError('this class is only implemented in aio')
else:
    from typing import Any
    from typing import Dict
    from typing import Optional

    from google.cloud.pubsub_v1.subscriber.message import Message \
        as GoogleMessage

    class Message:
        def __init__(self, **kwargs: Dict[str, Any]) -> None:
            self._message = GoogleMessage(**kwargs)

        @property
        def google_message(self):
            return self._message

        @property
        def message_id(self):
            return self._message.message_id  # indirects: protocol buffer field

        @property
        def __repr__(self) -> str:
            return repr(self._message)

        @property
        def attributes(self) -> Any:  # ScalarMapContainer
            return self._message.attributes

        @property
        def data(self) -> bytes:
            return bytes(self._message.data)

        @property
        def publish_time(self):  # datetime
            return self._message.publish_time

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
