from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module


def test_importable():
    assert True


if BUILD_GCLOUD_REST:
    pass


else:
    from gcloud.aio.pubsub.subscriber_client import FlowControl
    from gcloud.aio.pubsub.subscriber_client import SubscriberClient
    from gcloud.aio.pubsub.subscriber_message import SubscriberMessage  # pylint: disable=unused-import


    def test_construct_subscriber_client():
        SubscriberClient()

    def test_construct_flow_control():
        FlowControl()
