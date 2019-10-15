Asyncio Python Client for Google Cloud Task Queue
=================================================

|aio-pypi| |aio-pythons| |rest-pypi| |rest-pythons|

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-aio-taskqueue
    # or
    $ pip install --upgrade gcloud-rest-taskqueue

Usage
-----

We're still working on documentation -- for now, you can use the `smoke tests`_
as an example.

In addition to the ``PullQueue`` and ``PushQueue`` implementations -- which
directly map to the Google Cloud API (v2beta2 / v2beta3) -- this project
implements a Pull Task Queue Manager, which:

- leases tasks from a single pull task queue
- renews tasks as necessary
- releases tasks on failure
- deletes tasks when they are completed successfully
- dead-letters and deletes tasks when they have failed too many times

Contributing
------------

Please see our `contributing guide`_.

.. _contributing guide: https://github.com/talkiq/gcloud-aio/blob/master/.github/CONTRIBUTING.rst
.. _smoke tests: https://github.com/talkiq/gcloud-aio/tree/master/taskqueue/tests/integration

.. |aio-pypi| image:: https://img.shields.io/pypi/v/gcloud-aio-taskqueue.svg?style=flat-square&label=pypi (aio)
    :alt: Latest PyPI Version (gcloud-aio-taskqueue)
    :target: https://pypi.org/project/gcloud-aio-taskqueue/

.. |aio-pythons| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-taskqueue.svg?style=flat-square&label=python (aio)
    :alt: Python Version Support (gcloud-aio-taskqueue)
    :target: https://pypi.org/project/gcloud-aio-taskqueue/

.. |rest-pypi| image:: https://img.shields.io/pypi/v/gcloud-rest-taskqueue.svg?style=flat-square&label=pypi (rest)
    :alt: Latest PyPI Version (gcloud-rest-taskqueue)
    :target: https://pypi.org/project/gcloud-rest-taskqueue/

.. |rest-pythons| image:: https://img.shields.io/pypi/pyversions/gcloud-rest-taskqueue.svg?style=flat-square&label=python (rest)
    :alt: Python Version Support (gcloud-rest-taskqueue)
    :target: https://pypi.org/project/gcloud-rest-taskqueue/
