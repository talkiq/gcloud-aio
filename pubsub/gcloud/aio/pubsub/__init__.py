from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-pubsub').version

from gcloud.aio.pubsub.subscriber_client import SubscriberClient


__all__ = ['__version__', 'SubscriberClient']
