from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-auth').version

from gcloud.aio.auth.iam import IamClient
from gcloud.aio.auth.token import Token
from gcloud.aio.auth.utils import decode
from gcloud.aio.auth.utils import encode


__all__ = ['__version__', 'IamClient', 'Token', 'decode', 'encode']
