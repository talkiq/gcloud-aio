from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-storage').version

from gcloud.aio.storage.blob import Blob
from gcloud.aio.storage.bucket import Bucket
from gcloud.aio.storage.storage import Storage
from gcloud.aio.storage.utils import make_download


__all__ = ['__version__', 'Blob', 'Bucket', 'Storage', 'make_download']
