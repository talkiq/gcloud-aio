import google.cloud.pubsub as pubsub
from gcloud.aio.pubsub.topic import Topic


class Client(pubsub.client.Client):
    # pylint: disable=too-few-public-methods
    def topic(self, name, timestamp_messages=False):
        return Topic(name, client=self, timestamp_messages=timestamp_messages)
