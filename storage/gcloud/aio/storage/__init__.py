from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-storage').version

from gcloud.aio.storage.blob import Blob
from gcloud.aio.storage.bucket import Bucket
from gcloud.aio.storage.storage import SCOPES
from gcloud.aio.storage.storage import Storage


__all__ = ['__version__', 'Blob', 'Bucket', 'SCOPES', 'Storage']
