from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-taskqueue').version

from gcloud.aio.taskqueue.queue import PushQueue
from gcloud.aio.taskqueue.queue import SCOPES
from gcloud.aio.taskqueue.utils import decode
from gcloud.aio.taskqueue.utils import encode


__all__ = ['__version__', 'decode', 'encode', 'PushQueue', 'SCOPES']
