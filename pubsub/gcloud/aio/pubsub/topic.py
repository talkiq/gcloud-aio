import google.cloud.pubsub as pubsub
from gcloud.aio.pubsub.subscription import Subscription


class Topic(pubsub.topic.Topic):
    # pylint: disable=too-few-public-methods
    def subscription(self, name, ack_deadline=None, push_endpoint=None,
                     retain_acked_messages=None,
                     message_retention_duration=None):
        # pylint: disable=too-many-arguments
        return Subscription(
            name, self, ack_deadline=ack_deadline, push_endpoint=push_endpoint,
            retain_acked_messages=retain_acked_messages,
            message_retention_duration=message_retention_duration)
