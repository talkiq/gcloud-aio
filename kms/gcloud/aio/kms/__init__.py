from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-kms').version

from gcloud.aio.kms.kms import KMS
from gcloud.aio.kms.kms import SCOPES
from gcloud.aio.kms.utils import decode
from gcloud.aio.kms.utils import encode


__all__ = ['__version__', 'decode', 'encode', 'KMS', 'SCOPES']
