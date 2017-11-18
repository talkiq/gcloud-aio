from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-datastore').version

from gcloud.aio.datastore.datastore import Datastore


__all__ = ['__version__', 'Datastore']
