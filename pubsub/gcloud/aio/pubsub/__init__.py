from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-pubsub').version

from gcloud.aio.pubsub.publisher_client import PublisherClient
from gcloud.aio.pubsub.subscriber_client import SubscriberClient
from gcloud.aio.pubsub.utils import PubsubMessage


__all__ = ['__version__', 'PublisherClient', 'PubsubMessage',
           'SubscriberClient']
