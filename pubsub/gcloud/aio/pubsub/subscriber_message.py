import base64
import datetime
import json
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Dict

def parse_publish_time(publish_time: str) -> datetime.datetime:
    try:
        return datetime.datetime.strptime(
            publish_time, '%Y-%m-%dT%H:%M:%S.%f%z')
    except ValueError:
        return datetime.datetime.strptime(
            publish_time, '%Y-%m-%dT%H:%M:%S%z')


class SubscriberMessage:
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
