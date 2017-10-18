from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-taskqueue').version

from gcloud.aio.taskqueue.something import Something


__all__ = ['__version__', 'Something']
