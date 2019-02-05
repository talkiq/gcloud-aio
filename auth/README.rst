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

CLI
~~~

This project can also be used to help you manually authenticate to test GCP
routes, eg. we can list our project's uptime checks with a tool such as
``curl``:

.. code-block:: console

    # using default application credentials
    curl \
      -H "Authorization: Bearer $(python3 -c 'import asyncio; from gcloud.aio.auth import Token; print(asyncio.run(Token().get()))')" \
      "https://monitoring.googleapis.com/v3/projects/PROJECT_ID/uptimeCheckConfigs"

    # using a service account (make sure to provide a scope!)
    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service.json
    curl \
      -H "Authorization: Bearer $(python3 -c 'import asyncio; from gcloud.aio.auth import Token; print(asyncio.run(Token(scopes=["'"https://www.googleapis.com/auth/cloud-platform"'"]).get()))')" \
      "https://monitoring.googleapis.com/v3/projects/PROJECT_ID/uptimeCheckConfigs"

    # using legacy account credentials
    export GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcloud/legacy_credentials/EMAIL@DOMAIN.TLD/adc.json
    curl \
      -H "Authorization: Bearer $(python3 -c 'import asyncio; from gcloud.aio.auth import Token; print(asyncio.run(Token().get()))')" \
      "https://monitoring.googleapis.com/v3/projects/PROJECT_ID/uptimeCheckConfigs"

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
