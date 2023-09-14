(Asyncio OR Threadsafe) Google Cloud Client Libraries for Python
================================================================

This repository contains a shared codebase for two projects: ``gcloud-aio-*``
and ``gcloud-rest-*``. Both of them are HTTP implementations of the Google
Cloud client libraries. The former has been built to work with Python 3's
asyncio. The later is a threadsafe ``requests``-based implementation.

|circleci| |pythons|

The following clients are available:

- `Google Cloud Auth`_: |pypia|
- `Google Cloud BigQuery`_: |pypibq|
- `Google Cloud Datastore`_: |pypids|
- `Google Cloud KMS`_: |pypikms|
- `Google Cloud PubSub`_: |pypips|
- `Google Cloud Storage`_: |pypist|
- `Google Cloud Task Queue`_: |pypitq|

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-{aio,rest}-{client_name}

Docs
----

Please see our `documentation`_ for usage details.

Contributing
-------------

Developer? See our `contribution guide`_ for how you can contribute.

.. _Google Cloud Auth: https://github.com/talkiq/gcloud-aio/blob/master/auth/README.rst
.. _Google Cloud BigQuery: https://github.com/talkiq/gcloud-aio/blob/master/bigquery/README.rst
.. _Google Cloud Datastore: https://github.com/talkiq/gcloud-aio/blob/master/datastore/README.rst
.. _Google Cloud Function Dependencies: https://cloud.google.com/functions/docs/writing/specifying-dependencies-python
.. _Google Cloud KMS: https://github.com/talkiq/gcloud-aio/blob/master/kms/README.rst
.. _Google Cloud PubSub: https://github.com/talkiq/gcloud-aio/blob/master/pubsub/README.rst
.. _Google Cloud Storage: https://github.com/talkiq/gcloud-aio/blob/master/storage/README.rst
.. _Google Cloud Task Queue: https://github.com/talkiq/gcloud-aio/blob/master/taskqueue/README.rst
.. _contribution guide: https://github.com/talkiq/gcloud-aio/blob/master/.github/CONTRIBUTING.rst
.. _documentation: https://talkiq.github.io/gcloud-aio/

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
    :alt: Test Status
    :target: https://circleci.com/gh/talkiq/gcloud-aio/tree/master

.. |pythons| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-auth.svg?style=flat-square&label=python
    :alt: Python Version Support
    :target: https://pypi.org/project/gcloud-aio-auth/
