import warnings

from .pushqueue import LOCATION
from .pushqueue import PushQueue


def TaskQueue(project, service_file, taskqueue, location=LOCATION,
              session=None, token=None):
    warnings.warn('The TaskQueue class has been renamed to PushQueue and will '
                  'be removed in the next major release.', DeprecationWarning)
    return PushQueue(project, service_file, taskqueue, location=location,
                     session=session, token=token)
