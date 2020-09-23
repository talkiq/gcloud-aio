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
