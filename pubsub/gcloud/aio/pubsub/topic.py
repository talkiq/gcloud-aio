import google.cloud.pubsub as pubsub
import google.gax.errors
import grpc
from gcloud.aio.pubsub.subscription import Subscription


class Topic(pubsub.topic.Topic):
    def create_if_missing(self, client=None):
        if self.exists(client=client):
            return

        try:
            self.create(client=client)
        except google.gax.errors.RetryError as e:
            if e.cause._state != grpc.StatusCode.ALREADY_EXISTS:  # pylint: disable=protected-access
                raise

    def subscription(self, name, ack_deadline=None, push_endpoint=None,
                     retain_acked_messages=None,
                     message_retention_duration=None):
        # pylint: disable=too-many-arguments
        return Subscription(
            name, self, ack_deadline=ack_deadline, push_endpoint=push_endpoint,
            retain_acked_messages=retain_acked_messages,
            message_retention_duration=message_retention_duration)
