from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-auth').version

from gcloud.aio.auth.auth import Token


__all__ = ['__version__', 'Token']
