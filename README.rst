Asyncio Google Cloud Client Library for Python
==============================================

This project is a collection of Google Cloud client libraries which have been
built to work with Python's asyncio.

|circleci| |pythons|

The following clients are available:

- |pypia| `Google Cloud Auth`_ (`Auth README`_)
- |pypibq| `Google Cloud BigQuery`_ (`BigQuery README`_)
- |pypids| `Google Cloud Datastore`_ (`Datastore README`_)
- |pypikms| `Google Cloud KMS`_ (`KMS README`_)
- |pypips| `Google Cloud PubSub`_ (`PubSub README`_)
- |pypist| `Google Cloud Storage`_ (`Storage README`_)
- |pypitq| `Google Cloud Task Queue`_ (`Task Queue README`_)

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-aio-{client_name}

.. _Google Cloud Auth: https://pypi.org/project/gcloud-aio-auth/
.. _Google Cloud BigQuery: https://pypi.org/project/gcloud-aio-bigquery/
.. _Google Cloud Datastore: https://pypi.org/project/gcloud-aio-datastore/
.. _Google Cloud KMS: https://pypi.org/project/gcloud-aio-kms/
.. _Google Cloud PubSub: https://pypi.org/project/gcloud-aio-pubsub/
.. _Google Cloud Storage: https://pypi.org/project/gcloud-aio-storage/
.. _Google Cloud Task Queue: https://pypi.org/project/gcloud-aio-taskqueue/
.. _Auth README: https://github.com/talkiq/gcloud-aio/blob/master/auth/README.rst
.. _BigQuery README: https://github.com/talkiq/gcloud-aio/blob/master/bigquery/README.rst
.. _Datastore README: https://github.com/talkiq/gcloud-aio/blob/master/datastore/README.rst
.. _KMS README: https://github.com/talkiq/gcloud-aio/blob/master/kms/README.rst
.. _PubSub README: https://github.com/talkiq/gcloud-aio/blob/master/pubsub/README.rst
.. _Storage README: https://github.com/talkiq/gcloud-aio/blob/master/storage/README.rst
.. _Task Queue README: https://github.com/talkiq/gcloud-aio/blob/master/taskqueue/README.rst

.. |pypia| image:: https://img.shields.io/pypi/v/gcloud-aio-auth.svg?style=flat-square
    :alt: Latest PyPI Version
    :target: https://pypi.org/project/gcloud-aio-auth/

.. |pypibq| image:: https://img.shields.io/pypi/v/gcloud-aio-bigquery.svg?style=flat-square
    :alt: Latest PyPI Version
    :target: https://pypi.org/project/gcloud-aio-bigquery/

.. |pypids| image:: https://img.shields.io/pypi/v/gcloud-aio-datastore.svg?style=flat-square
    :alt: Latest PyPI Version
    :target: https://pypi.org/project/gcloud-aio-datastore/

.. |pypikms| image:: https://img.shields.io/pypi/v/gcloud-aio-kms.svg?style=flat-square
    :alt: Latest PyPI Version
    :target: https://pypi.org/project/gcloud-aio-kms/

.. |pypips| image:: https://img.shields.io/pypi/v/gcloud-aio-pubsub.svg?style=flat-square
    :alt: Latest PyPI Version
    :target: https://pypi.org/project/gcloud-aio-pubsub/

.. |pypist| image:: https://img.shields.io/pypi/v/gcloud-aio-storage.svg?style=flat-square
    :alt: Latest PyPI Version
    :target: https://pypi.org/project/gcloud-aio-storage/

.. |pypitq| image:: https://img.shields.io/pypi/v/gcloud-aio-taskqueue.svg?style=flat-square
    :alt: Latest PyPI Version
    :target: https://pypi.org/project/gcloud-aio-taskqueue/

.. |circleci| image:: https://img.shields.io/circleci/project/github/talkiq/gcloud-aio/master.svg?style=flat-square
    :alt: CircleCI Test Status
    :target: https://circleci.com/gh/talkiq/gcloud-aio/tree/master

.. |pythons| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-auth.svg?style=flat-square
    :alt: Python Version Support
    :target: https://pypi.org/project/gcloud-aio-auth/
