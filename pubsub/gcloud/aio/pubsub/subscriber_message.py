import base64
import datetime
import json
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

class SubscriberMessage:
    def __init__(self, ack_id: str, message_id: str,
                 publish_time: datetime.datetime,
                 data: Dict[str, Any],
                 attributes: Dict[str, Any]):
        self.ack_id = ack_id
        self.message_id = message_id
        self.publish_time = publish_time
        self.data = data
        self.attributes = attributes

    @staticmethod
    def from_api_dict(received_message: Dict[str, Any]) -> 'SubscriberMessage':
        ack_id = received_message['ackId']
        message_id = received_message['message']['messageId']
        data = json.loads(
            base64.b64decode(received_message['message']['data']))
        attributes = received_message['message']['attributes']
        publish_time = datetime.datetime.strptime(
            received_message['message']['publishTime'], '%Y-%m-%dT%H:%M:%S.%f%z'
        )
        return SubscriberMessage(ack_id=ack_id, message_id=message_id,
                                 publish_time=publish_time, data=data,
                                 attributes=attributes)
