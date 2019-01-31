Auth Helpers for Asyncio Google Cloud Library
=============================================

This library is not meant to be a standalone project, rather it is used by
various ``gcloud-aio-*`` packages.

This library implements a ``Token`` class, which is used for authorizing
against Google Cloud. The other ``gcloud-aio-*`` package components accept a
``Token`` instance as an argument; you can define a single token for all of
these components or define one for each. Each component corresponds to a given
Google Cloud service and each service requires "`scopes`_".

|pypi| |pythons|

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-aio-auth

Usage
-----

.. code-block:: python

    from gcloud.aio.auth import Token

    token = Token()

Additionally, the ``Token`` constructor accepts the following optional
arguments:

* ``service_file``: path to a `service account`_, authorized user file, or any
  other application credentials. If omitted, will attempt to find one on your
  path or fallback to generating a token from GCE metadata.
* ``session``: an ``aiohttp.ClientSession`` instance to be used for all
  requests. If omitted, a default session will be created.
* ``scopes``: an optional list of GCP `scopes`_ for which to generate our
  token. Only valid (and required!) for `service account`_ authentication.

Contributing
------------

Please see our `contributing guide`_.

.. _contributing guide: https://github.com/talkiq/gcloud-aio/blob/master/.github/CONTRIBUTING.rst
.. _scopes: https://developers.google.com/identity/protocols/googlescopes
.. _service account: https://console.cloud.google.com/iam-admin/serviceaccounts
.. _smoke test: https://github.com/talkiq/gcloud-aio/blob/master/auth/tests/integration/smoke_test.py

.. |pypi| image:: https://img.shields.io/pypi/v/gcloud-aio-auth.svg?style=flat-square
    :alt: Latest PyPI Version
    :target: https://pypi.org/project/gcloud-aio-auth/

.. |pythons| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-auth.svg?style=flat-square
    :alt: Python Version Support
    :target: https://pypi.org/project/gcloud-aio-auth/
