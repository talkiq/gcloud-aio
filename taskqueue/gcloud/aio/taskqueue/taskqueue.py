import warnings

from .pullqueue import LOCATION
from .pullqueue import PullQueue


def TaskQueue(project, taskqueue, service_file=None, location=LOCATION,
              session=None, token=None):
    warnings.warn('The TaskQueue class has been renamed to PullQueue and will '
                  'be removed in the next major release.', DeprecationWarning)
    return PullQueue(project, taskqueue, service_file=service_file,
                     location=location, session=session, token=token)
