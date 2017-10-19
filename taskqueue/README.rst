Asyncio Python Client for Google Cloud Task Queue
=================================================

|pypi| |pythons|

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-aio-taskqueue

Usage
-----

We're still working on documentation -- for now, you can use the `smoke test`_
as an example.

In addition to the `TaskManager` implementation -- which directly maps to the
Google Cloud API -- this project implements a Pull Task Queue Manager, which:
This implements a pull task queue manager, which:

- leases tasks from a single pull task queue
- renews tasks as necessary
- releases tasks on failure
- deletes tasks when they are completed successfully
- dead-letters and deletes tasks when they have failed too many times

.. _smoke test: https://github.com/talkiq/gcloud-aio/blob/master/taskqueue/tests/integration/smoke_test.py

.. |pypi| image:: https://img.shields.io/pypi/v/gcloud-aio-taskqueue.svg?style=flat-square
    :alt: Latest PyPI Version
    :target: https://pypi.org/project/gcloud-aio-taskqueue/

.. |pythons| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-taskqueue.svg?style=flat-square
    :alt: Python Version Support
    :target: https://pypi.org/project/gcloud-aio-taskqueue/
