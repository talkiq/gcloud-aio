from gcloud.aio.pubsub import SubscriberClient

def test_importable():
    assert True

def test_constructor():
    subscription = SubscriberClient()
    assert subscription
