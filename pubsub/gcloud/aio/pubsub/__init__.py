from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-pubsub').version

from gcloud.aio.auth import BUILD_GCLOUD_REST
from gcloud.aio.pubsub.publisher_client import PublisherClient
from gcloud.aio.pubsub.subscriber_client import SubscriberClient
from gcloud.aio.pubsub.utils import PubsubMessage
from gcloud.aio.pubsub.subscriber_message import SubscriberMessage

__all__ = ['__version__', 'PublisherClient', 'PubsubMessage',
           'SubscriberClient', 'SubscriberMessage']

if not BUILD_GCLOUD_REST:
    from gcloud.aio.pubsub.subscriber import subscribe
    __all__.append('subscribe')
