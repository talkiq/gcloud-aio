from gcloud.aio.pubsub import SubscriberClient


# This ain't a great test, but we need *somethign* in this directory to avoid
# pytest failing and this does at least validate the auth token to some extent.
def test_constructor():
    subscriber = SubscriberClient()
    assert subscriber
