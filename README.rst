(Asyncio OR Threadsafe) Google Cloud Client Library for Python
==============================================================

This repository contains a shared codebase for two projects: ``gcloud-aio-*``
and ``gcloud-rest-*``. Both of them are HTTP implementations of the Google
Cloud client libraries. The former has been built to work with Python 3's
asyncio. The later is a threadsafe ``requests``-based implementation which
should be compatible all the way back to Python 2.7.

|circleci| |pythons-aio| |pythons-rest|

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

Compatibility
-------------

Here are notes on compatibility issues. While we cannot offer specific support
for issues originating from other projects, we can point toward known
resolutions.

- Google Cloud Functions pins ``yarl``; ``gcloud-aio-*`` indirectly requires
  ``yarl`` via ``aiohttp`` and an unpinned version of ``yarl`` can cause your
  cloud functions to stop building. Please pin your requirements as described
  here: `Google Cloud Function Dependencies`_.

Contributing
-------------

Developer? See our `docs`_ on how you can contribute.

.. gcloud-aio links

.. _Google Cloud Auth: https://github.com/talkiq/gcloud-aio/blob/master/auth/README.rst
.. _Google Cloud BigQuery: https://github.com/talkiq/gcloud-aio/blob/master/bigquery/README.rst
.. _Google Cloud Datastore: https://github.com/talkiq/gcloud-aio/blob/master/datastore/README.rst
.. _Google Cloud KMS: https://github.com/talkiq/gcloud-aio/blob/master/kms/README.rst
.. _Google Cloud PubSub: https://github.com/talkiq/gcloud-aio/blob/master/pubsub/README.rst
.. _Google Cloud Storage: https://github.com/talkiq/gcloud-aio/blob/master/storage/README.rst
.. _Google Cloud Task Queue: https://github.com/talkiq/gcloud-aio/blob/master/taskqueue/README.rst
.. _docs: https://github.com/talkiq/gcloud-aio/blob/master/.github/CONTRIBUTING.rst

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

.. |pythons-aio| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-auth.svg?style=flat-square&label=python (aio)
    :alt: Python Version Support (aio)
    :target: https://pypi.org/project/gcloud-aio-auth/

.. |pythons-rest| image:: https://img.shields.io/pypi/pyversions/gcloud-rest-auth.svg?style=flat-square&label=python (rest)
    :alt: Python Version Support (rest)
    :target: https://pypi.org/project/gcloud-rest-auth/

.. external links

.. _Google Cloud Function Dependencies: https://cloud.google.com/functions/docs/writing/specifying-dependencies-python
