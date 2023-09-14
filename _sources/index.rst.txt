(Asyncio OR Threadsafe) Google Cloud Client Libraries for Python
================================================================

These docs describe the shared codebase for ``gcloud-aio-*`` and
``gcloud-rest-*``. Both of them are HTTP implementations of the Google Cloud
client libraries: the former has been built to with asyncio (using the
``aiohttp`` library) and the latter is a threadsafe ``requests``-based
implementation.

Table of Contents
-----------------

.. toctree::
    :maxdepth: 1

    autoapi/auth/index
    autoapi/bigquery/index
    autoapi/datastore/index
    autoapi/kms/index
    autoapi/pubsub/index
    autoapi/storage/index
    autoapi/taskqueue/index
    .github/CONTRIBUTING.rst
    .github/RELEASE.rst

* :ref:`modindex`
