import base64
import datetime
from typing import Any
from typing import Dict
from typing import Optional


def parse_publish_time(publish_time: str) -> datetime.datetime:
    try:
        return datetime.datetime.strptime(
            publish_time, '%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        return datetime.datetime.strptime(
            publish_time, '%Y-%m-%dT%H:%M:%SZ')


class SubscriberMessage:
    def __init__(self, ack_id: str, message_id: str,
                 publish_time: 'datetime.datetime',
                 data: bytes,
                 attributes: Optional[Dict[str, Any]]):
        self.ack_id = ack_id
        self.message_id = message_id
        self.publish_time = publish_time
        self.data = data
        self.attributes = attributes

    @staticmethod
    def from_repr(received_message: Dict[str, Any]
                  ) -> 'SubscriberMessage':
        ack_id = received_message['ackId']
        message_id = received_message['message']['messageId']
        data = base64.b64decode(received_message['message']['data'])
        attributes = received_message['message'].get('attributes')
        publish_time: datetime.datetime = parse_publish_time(
            received_message['message']['publishTime'])
        return SubscriberMessage(ack_id=ack_id, message_id=message_id,
                                 publish_time=publish_time, data=data,
                                 attributes=attributes)

    def to_repr(self) -> Dict[str, Any]:
        return {
            'ackId': self.ack_id,
            'message': {
                'messageId': self.message_id,
                'attributes': self.attributes,
                'data': base64.b64encode(self.data),
                'publishTime': self.publish_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
        }
