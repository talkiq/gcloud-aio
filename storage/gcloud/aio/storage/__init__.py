from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-storage').version

from gcloud.aio.storage.storage import Blob
from gcloud.aio.storage.storage import Bucket
from gcloud.aio.storage.storage import make_download
from gcloud.aio.storage.storage import Storage


__all__ = ['__version__', 'Blob', 'Bucket', 'make_download', 'Storage']
