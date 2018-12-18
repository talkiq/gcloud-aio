from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-datastore').version

from gcloud.aio.datastore.constants import Mode
from gcloud.aio.datastore.constants import Operation
from gcloud.aio.datastore.datastore import Datastore
from gcloud.aio.datastore.key import Key
from gcloud.aio.datastore.key import PathElement


__all__ = ['__version__', 'Datastore', 'Key', 'Mode', 'Operation',
           'PathElement']
