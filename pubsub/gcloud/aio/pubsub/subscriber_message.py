from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module

if BUILD_GCLOUD_REST:
    class Message:
        def __init__(self, **kwargs) -> None:
            raise NotImplementedError('this class is only implemented in aio')

    class FlowControl:
        def __init__(self, **kwargs) -> None:
            raise NotImplementedError('this class is only implemented in aio')

else:
    import datetime

    from typing import Any
    from typing import Dict
    from typing import Optional

    from google.cloud.pubsub_v1.subscriber.message import Message \
        as GoogleMessage


    class FlowControl:
        def __init__(self,
                     max_bytes: int = 100 * 1024 * 1024,
                     max_messages: int = 1000,
                     max_lease_duration: int = 1 * 60 * 60,
                     max_duration_per_lease_extension: int = 0) -> None:
            self.max_bytes = max_bytes
            self.max_messages = max_messages
            self.max_lease_duration = max_lease_duration
            self.max_duration_per_lease_extension = (
                max_duration_per_lease_extension)


    class Message:
        def __init__(self, *args, **kwargs: Dict[str, Any]) -> None:
            self._message = GoogleMessage(*args, **kwargs)

        @property
        def google_message(self) -> GoogleMessage:
            return self._message

        @property
        def message_id(self) -> str:  # indirects to a Google protobuff field
            return str(self._message.message_id)

        @property
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
