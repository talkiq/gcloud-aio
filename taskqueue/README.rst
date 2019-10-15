(Asyncio OR Threadsafe) Python Client for Google Cloud Task Queue
=================================================================

|pypi| |pythons-aio| |pythons-rest|

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-{aio,rest}-taskqueue

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

.. |pypi| image:: https://img.shields.io/pypi/v/gcloud-aio-taskqueue.svg?style=flat-square
    :alt: Latest PyPI Version (gcloud-aio-taskqueue)
    :target: https://pypi.org/project/gcloud-aio-taskqueue/

.. |pythons-aio| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-taskqueue.svg?style=flat-square&label=python (aio)
    :alt: Python Version Support (gcloud-aio-taskqueue)
    :target: https://pypi.org/project/gcloud-aio-taskqueue/

.. |pythons-rest| image:: https://img.shields.io/pypi/pyversions/gcloud-rest-taskqueue.svg?style=flat-square&label=python (rest)
    :alt: Python Version Support (gcloud-rest-taskqueue)
    :target: https://pypi.org/project/gcloud-rest-taskqueue/
