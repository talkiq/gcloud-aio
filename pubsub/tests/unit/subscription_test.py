import base64
import datetime
import json

import hypothesis
import pytest
from gcloud.aio.pubsub.subscriber_client import SubscriberClient
from gcloud.aio.pubsub.subscriber_message import parse_publish_time
from gcloud.aio.pubsub.subscriber_message import SubscriberMessage
from hypothesis import strategies


# strftime does not zero-pad years before 1000 on every platform, see
# https://github.com/python/cpython/issues/120713
NAIVE_DATETIMES = strategies.datetimes(
    min_value=datetime.datetime(1000, 1, 2),
    max_value=datetime.datetime(9999, 12, 30),
)
AWARE_DATETIMES = strategies.datetimes(
    min_value=datetime.datetime(1000, 1, 2),
    max_value=datetime.datetime(9999, 12, 30),
    timezones=strategies.builds(
        datetime.timezone,
        strategies.timedeltas(
            min_value=-datetime.timedelta(hours=23, minutes=59),
            max_value=datetime.timedelta(hours=23, minutes=59),
        ),
    ),
)


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
        2020, 1, 1, 0, 0, 1, tzinfo=datetime.UTC,
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
        2020, 1, 1, 0, 0, 1, tzinfo=datetime.UTC,
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


@pytest.mark.parametrize(
    'publish_time,expected',
    [
        (
            '2020-01-01T00:00:01.123456789Z',
            datetime.datetime(
                2020, 1, 1, 0, 0, 1, 123456, tzinfo=datetime.UTC,
            ),
        ),
        (
            '2020-01-01T00:00:01.123Z',
            datetime.datetime(
                2020, 1, 1, 0, 0, 1, 123000, tzinfo=datetime.UTC,
            ),
        ),
        (
            '2020-01-01T00:00:01Z',
            datetime.datetime(2020, 1, 1, 0, 0, 1, tzinfo=datetime.UTC),
        ),
        (
            '2020-01-01T00:00:01',
            datetime.datetime(2020, 1, 1, 0, 0, 1, tzinfo=datetime.UTC),
        ),
        (
            '2020-01-01T02:00:01.123456+02:00',
            datetime.datetime(
                2020, 1, 1, 0, 0, 1, 123456, tzinfo=datetime.UTC,
            ),
        ),
    ],
)
def test_parse_publish_time(publish_time, expected):
    parsed = parse_publish_time(publish_time)
    assert parsed == expected
    assert parsed.utcoffset() == datetime.timedelta(0)


def _roundtrip(publish_time):
    message = SubscriberMessage(
        ack_id='some_ack_id', message_id='123', publish_time=publish_time,
        data=None, attributes=None,
    )
    return SubscriberMessage.from_repr(message.to_repr()).publish_time


@hypothesis.given(dt=AWARE_DATETIMES)
def test_publish_time_repr_roundtrip(dt):
    roundtripped = _roundtrip(dt)

    assert roundtripped == dt
    assert roundtripped.utcoffset() == datetime.timedelta(0)


@hypothesis.given(dt=NAIVE_DATETIMES)
def test_naive_publish_time_repr_roundtrip_is_utc(dt):
    assert _roundtrip(dt) == dt.replace(tzinfo=datetime.UTC)
