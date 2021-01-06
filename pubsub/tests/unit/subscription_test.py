import base64
import datetime
import json

from gcloud.aio.pubsub.subscriber_client import SubscriberClient
from gcloud.aio.pubsub.subscriber_message import SubscriberMessage  # pylint: disable=unused-import


def test_importable():
    assert True


def test_construct_subscriber_client():
    SubscriberClient()


def test_construct_subscriber_message_from_message_dict():
    message_dict = {
        'ackId': 'some_ack_id',
        'message': {
            'data': base64.b64encode(
                json.dumps({'foo': 'bar'}).encode('utf-8')),
            'attributes': {'attr_key': 'attr_value'},
            'messageId': '123',
            'publishTime': '2020-01-01T00:00:01.000Z'
        }
    }
    message = SubscriberMessage.from_repr(message_dict)
    assert message.ack_id == 'some_ack_id'
    assert message.attributes == {'attr_key': 'attr_value'}
    assert message.message_id == '123'
    assert message.data == b'{"foo": "bar"}'
    assert message.publish_time == datetime.datetime(
        2020, 1, 1, 0, 0, 1)
