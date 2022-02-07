from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-pubsub').version

from gcloud.aio.auth import BUILD_GCLOUD_REST
from gcloud.aio.pubsub.metrics_agent import configure_prometheus
from gcloud.aio.pubsub.publisher_client import PublisherClient
from gcloud.aio.pubsub.subscriber_client import SubscriberClient
from gcloud.aio.pubsub.subscriber_message import SubscriberMessage
from gcloud.aio.pubsub.utils import PubsubMessage

__all__ = ['__version__', 'configure_prometheus', 'PublisherClient',
           'PubsubMessage', 'SubscriberClient', 'SubscriberMessage']

if not BUILD_GCLOUD_REST:
    from gcloud.aio.pubsub.subscriber import subscribe
    __all__.append('subscribe')
