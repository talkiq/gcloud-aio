from gcloud.aio.pubsub import Subscription

def test_importable():
    assert True

def test_constructor(subscription_name):
    subscription = Subscription(subscription_name)
    assert subscription
