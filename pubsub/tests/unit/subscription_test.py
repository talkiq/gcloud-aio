from queue import Queue

from gcloud.aio.pubsub.subscriber_client import FlowControl
from gcloud.aio.pubsub.subscriber_client import SubscriberClient
from gcloud.aio.pubsub.subscriber_message import SubscriberMessage  # pylint: disable=unused-import
from google.cloud.pubsub_v1.subscriber.message import Message
from google.cloud.pubsub_v1.types import PubsubMessage


def test_importable():
    assert True


def test_construct_subscriber_client():
    SubscriberClient()


def test_construct_flow_control():
    FlowControl()


def test_flow_control_getattr():
    f = FlowControl(
        max_messages=1,
        max_bytes=100,
        max_lease_duration=10,
        max_duration_per_lease_extension=0)

    assert f.max_messages == 1
    assert f.max_bytes == 100
    assert f.max_lease_duration == 10
    assert f.max_duration_per_lease_extension == 0

def test_construct_subscriber_message_from_google_message():
    ack_id = 'some_ack_id'
    delivery_attempt = 0
    request_queue = Queue()

    pubsub_message = PubsubMessage()
    pubsub_message.attributes['style'] = 'cool'
    google_message = Message(pubsub_message, ack_id, delivery_attempt,
                             request_queue)

    subscriber_message = SubscriberMessage.from_google_cloud(google_message)
    assert subscriber_message.ack_id == ack_id
    assert subscriber_message.delivery_attempt is None  # only an int if >0
    assert subscriber_message.attributes['style'] == 'cool'
