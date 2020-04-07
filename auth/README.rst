(Asyncio OR Threadsafe) Python Client for Google Cloud Auth
===========================================================

    This is a shared codebase for ``gcloud-aio-auth`` and ``gcloud-rest-auth``

This library implements an ``IamClient`` class, which can be used to interact
with GCP public keys and URL sign blobs.

It additionally implements a ``Token`` class, which is used for authorizing
against Google Cloud. The other ``gcloud-aio-*`` package components accept a
``Token`` instance as an argument; you can define a single token for all of
these components or define one for each. Each component corresponds to a given
Google Cloud service and each service requires "`scopes`_".

|pypi| |pythons-aio| |pythons-rest|

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-{aio,rest}-auth

Usage
-----

.. code-block:: python

    from gcloud.aio.auth import IamClient

    client = IamClient()
    pubkeys = await client.list_public_keys()


    from gcloud.rest.auth import Token

    token = Token()
    print(token.get())

Additionally, the ``Token`` constructor accepts the following optional
arguments:

* ``service_file``: path to a `service account`_, authorized user file, or any
  other application credentials. Alternatively, you can pass a file-like
  object, like an ``io.StringIO`` instance, in case your credentials are not
  stored in a file but in memory. If omitted, will attempt to find one on your
  path or fallback to generating a token from GCE metadata.
* ``session``: an ``aiohttp.ClientSession`` instance to be used for all
  requests. If omitted, a default session will be created. If you use the
  default session, you may be interested in using ``Token()`` as a context
  manager (``async with Token(..) as token:``) or explicitly calling the
  ``Token.close()`` method to ensure the session is cleaned up appropriately.
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
      -H "Authorization: Bearer $(python3 -c 'from gcloud.rest.auth import Token; print(Token().get())')" \
      "https://monitoring.googleapis.com/v3/projects/PROJECT_ID/uptimeCheckConfigs"

    # using a service account (make sure to provide a scope!)
    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service.json
    curl \
      -H "Authorization: Bearer $(python3 -c 'from gcloud.rest.auth import Token; print(Token(scopes=["'"https://www.googleapis.com/auth/cloud-platform"'"]).get())')" \
      "https://monitoring.googleapis.com/v3/projects/PROJECT_ID/uptimeCheckConfigs"

    # using legacy account credentials
    export GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcloud/legacy_credentials/EMAIL@DOMAIN.TLD/adc.json
    curl \
      -H "Authorization: Bearer $(python3 -c 'from gcloud.rest.auth import Token; print(Token().get())')" \
      "https://monitoring.googleapis.com/v3/projects/PROJECT_ID/uptimeCheckConfigs"

Contributing
------------

Please see our `contributing guide`_.

.. _contributing guide: https://github.com/talkiq/gcloud-aio/blob/master/.github/CONTRIBUTING.rst
.. _scopes: https://developers.google.com/identity/protocols/googlescopes
.. _service account: https://console.cloud.google.com/iam-admin/serviceaccounts
.. _smoke test: https://github.com/talkiq/gcloud-aio/blob/master/auth/tests/integration/smoke_test.py

.. |pypi| image:: https://img.shields.io/pypi/v/gcloud-aio-auth.svg?style=flat-square
    :alt: Latest PyPI Version (gcloud-aio-auth)
    :target: https://pypi.org/project/gcloud-aio-auth/

.. |pythons-aio| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-auth.svg?style=flat-square&label=python (aio)
    :alt: Python Version Support (gcloud-aio-auth)
    :target: https://pypi.org/project/gcloud-aio-auth/

.. |pythons-rest| image:: https://img.shields.io/pypi/pyversions/gcloud-rest-auth.svg?style=flat-square&label=python (rest)
    :alt: Python Version Support (gcloud-rest-auth)
    :target: https://pypi.org/project/gcloud-rest-auth/
