import base64
import datetime
import json

import pytest
from gcloud.aio.pubsub.subscriber_client import SubscriberClient
from gcloud.aio.pubsub.subscriber_message import SubscriberMessage


@pytest.mark.asyncio
async def test_construct_subscriber_client():
    SubscriberClient()


def test_construct_subscriber_message_from_message():
    message_dict = {
        'ackId': 'some_ack_id',
        'message': {
            'data': base64.b64encode(
                json.dumps({'foo': 'bar'}).encode('utf-8'),
            ),
            'attributes': {'attr_key': 'attr_value'},
            'messageId': '123',
            'publishTime': '2020-01-01T00:00:01.000Z',
        },
        'deliveryAttempt': 1,
    }
    message = SubscriberMessage.from_repr(message_dict)
    assert message.ack_id == 'some_ack_id'
    assert message.attributes == {'attr_key': 'attr_value'}
    assert message.message_id == '123'
    assert message.data == b'{"foo": "bar"}'
    assert message.publish_time == datetime.datetime(
        2020, 1, 1, 0, 0, 1,
    )
    assert message.delivery_attempt == 1


def test_construct_subscriber_message_no_metadata():
    message_dict = {
        'ackId': 'some_ack_id',
        'message': {
            'messageId': '123',
            'publishTime': '2020-01-01T00:00:01.000Z',
        },
    }
    message = SubscriberMessage.from_repr(message_dict)
    assert message.ack_id == 'some_ack_id'
    assert message.attributes is None
    assert message.message_id == '123'
    assert message.data is None
    assert message.publish_time == datetime.datetime(
        2020, 1, 1, 0, 0, 1,
    )
    assert message.delivery_attempt is None


@pytest.mark.parametrize(
    'publish_time',
    [
        datetime.datetime(2020, 1, 1, 0, 0, 1, 123456),
        datetime.datetime(2020, 1, 1, 0, 0, 1, 123456, tzinfo=datetime.UTC),
        datetime.datetime(
            2020, 1, 1, 2, 0, 1, 123456,
            tzinfo=datetime.timezone(datetime.timedelta(hours=2)),
        ),
        datetime.datetime(
            2019, 12, 31, 19, 0, 1, 123456,
            tzinfo=datetime.timezone(datetime.timedelta(hours=-5)),
        ),
    ],
)
def test_subscriber_message_to_repr_publish_time_is_utc(publish_time):
    message = SubscriberMessage(
        ack_id='some_ack_id', message_id='123', publish_time=publish_time,
        data=None, attributes=None,
    )
    assert message.to_repr()['message']['publishTime'] == (
        '2020-01-01T00:00:01.123456Z'
    )
