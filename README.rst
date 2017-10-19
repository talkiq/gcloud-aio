Asyncio Google Cloud Client Library for Python
==============================================

This project is a collection of Google Cloud client libraries which have been
built to work with Python's asyncio.

|pypi| |circleci| |coverage| |pythons|

The following clients are available:

- `Google Cloud BigQuery`_ (`BigQuery README`_)
- `Google Cloud Storage`_ (`Storage README`_)
- `Google Cloud Task Queue`_ (`Task Queue README`_)

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-aio

.. _Google Cloud BigQuery: https://pypi.org/project/gcloud-aio-bigquery/
.. _Google Cloud Storage: https://pypi.org/project/gcloud-aio-storage/
.. _Google Cloud Task Queue: https://pypi.org/project/gcloud-aio-taskqueue/
.. _BigQuery README: https://github.com/talkiq/gcloud-aio/blob/master/bigquery/README.rst
.. _Storage README: https://github.com/talkiq/gcloud-aio/blob/master/storage/README.rst
.. _Task Queue README: https://github.com/talkiq/gcloud-aio/blob/master/taskqueue/README.rst

.. |pypi| image:: https://img.shields.io/pypi/v/gcloud-aio-storage.svg?style=flat-square
    :alt: Latest PyPI Version
    :target: https://pypi.org/project/gcloud-aio-storage/

.. |circleci| image:: https://img.shields.io/circleci/project/github/talkiq/gcloud-aio/master.svg?style=flat-square
    :alt: CircleCI Test Status
    :target: https://circleci.com/gh/talkiq/gcloud-aio/tree/master

.. |coverage| image:: https://img.shields.io/codecov/c/github/talkiq/gcloud-aio/master.svg?style=flat-square
    :alt: Code Coverage
    :target: https://codecov.io/gh/talkiq/gcloud-aio

.. |pythons| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-storage.svg?style=flat-square
    :alt: Python Version Support
    :target: https://pypi.org/project/gcloud-aio-storage/
