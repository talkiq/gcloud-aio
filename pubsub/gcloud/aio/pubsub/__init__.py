from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-pubsub').version

from gcloud.aio.pubsub.client import Client


__all__ = ['__version__', 'Client']
