"""
This library implements various methods for working with the Google Taskqueue
APIs.

## Installation

```console
$ pip install --upgrade gcloud-aio-taskqueue
```

## Usage

We're still working on documentation -- for now, you can use the
[smoke tests][smoke-tests] as an example.

## Emulators

For testing purposes, you may want to use `gcloud-aio-taskqueue` along with a
local emulator. Setting the `$CLOUDTASKS_EMULATOR_HOST` environment variable to
the address of your emulator should be enough to do the trick.

[smoke-tests]:
https://github.com/talkiq/gcloud-aio/tree/master/taskqueue/tests/integration
"""
from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-taskqueue').version

from gcloud.aio.taskqueue.queue import PushQueue
from gcloud.aio.taskqueue.queue import SCOPES
from gcloud.aio.taskqueue.utils import decode
from gcloud.aio.taskqueue.utils import encode


__all__ = [
    'PushQueue',
    'SCOPES',
    '__version__',
    'decode',
    'encode',
]
