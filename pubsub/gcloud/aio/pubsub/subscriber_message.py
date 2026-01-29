import base64
import datetime
from typing import Any


def parse_publish_time(publish_time: str) -> datetime.datetime:
    try:
        return datetime.datetime.strptime(
            publish_time, '%Y-%m-%dT%H:%M:%S.%fZ',
        )
    except ValueError:
        return datetime.datetime.strptime(
            publish_time, '%Y-%m-%dT%H:%M:%SZ',
        )


class SubscriberMessage:
    def __init__(
        self, ack_id: str, message_id: str,
        publish_time: 'datetime.datetime',
        data: bytes | None,
        attributes: dict[str, Any] | None,
        delivery_attempt: int | None = None,
    ):
        self.ack_id = ack_id
        self.message_id = message_id
        self.publish_time = publish_time
        self.data = data
        self.attributes = attributes
        self.delivery_attempt = delivery_attempt

    @staticmethod
    def from_repr(
        received_message: dict[str, Any],
    ) -> 'SubscriberMessage':
        ack_id = received_message['ackId']
        message_id = received_message['message']['messageId']
        raw_data = received_message['message'].get('data')
        data = base64.b64decode(raw_data) if raw_data is not None else None
        attributes = received_message['message'].get('attributes')
        publish_time: datetime.datetime = parse_publish_time(
            received_message['message']['publishTime'],
        )
        delivery_attempt = received_message.get('deliveryAttempt')
        return SubscriberMessage(
            ack_id=ack_id, message_id=message_id,
            publish_time=publish_time, data=data,
            attributes=attributes,
            delivery_attempt=delivery_attempt,
        )

    def to_repr(self) -> dict[str, Any]:
        r: dict[str, Any] = {
            'ackId': self.ack_id,
            'message': {
                'messageId': self.message_id,
                'publishTime': (
                    self.publish_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                ),
            },
        }
        if self.attributes is not None:
            r['message']['attributes'] = self.attributes
        if self.data is not None:
            r['message']['data'] = base64.b64encode(self.data)
        if self.delivery_attempt is not None:
            r['deliveryAttempt'] = self.delivery_attempt
        return r
