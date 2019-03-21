from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-taskqueue').version

from gcloud.aio.taskqueue.basequeue import SCOPES
from gcloud.aio.taskqueue.pullqueue import PullQueue
from gcloud.aio.taskqueue.pushqueue import PushQueue
from gcloud.aio.taskqueue.taskmanager import FailFastError
from gcloud.aio.taskqueue.taskmanager import TaskManager
from gcloud.aio.taskqueue.utils import decode
from gcloud.aio.taskqueue.utils import encode


__all__ = ['__version__', 'decode', 'encode', 'FailFastError', 'PullQueue',
           'PushQueue', 'SCOPES', 'TaskManager']
