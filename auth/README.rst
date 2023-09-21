(Asyncio OR Threadsafe) Python Client for Google Cloud Auth
===========================================================

    This is a shared codebase for ``gcloud-aio-auth`` and ``gcloud-rest-auth``

This library implements an ``IamClient`` class, which can be used to interact
with GCP public keys and URL sign blobs.

It also implements an ``IapToken`` class which is used for authorizing against
an `Identity-Aware Proxy`_ (IAP) secured GCP service. IAP uses identity tokens
which are specific to the target service and allows administrators to configure
a list of identities (ex. service accounts, users, or groups) that may access
the service. Therefore each ``IapToken`` instance corresponds to an ID token
which may be used to authorize against a single IAP service.

It additionally implements a ``Token`` class, which is used for authorizing
against Google Cloud. The other ``gcloud-aio-*`` package components accept a
``Token`` instance as an argument; you can define a single token for all of
these components or define one for each. Each component corresponds to a given
Google Cloud service and each service requires various "`scopes`_".

|pypi| |pythons-aio| |pythons-rest|

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-{aio,rest}-auth

Usage
-----

See `our docs`_.

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

Similarly it can be used to quickly test your IAP-secured endpoints:

.. code-block:: console

    # using default application credentials
    curl \
      -H "Authorization: Bearer $(python3 -c 'from gcloud.rest.auth import IapToken; print(IapToken(APP_URL, impersonating_service_account=SA))')" \
      APP_URL

Contributing
------------

Please see our `contributing guide`_.

.. _contributing guide: https://github.com/talkiq/gcloud-aio/blob/master/.github/CONTRIBUTING.rst
.. _our docs: https://talkiq.github.io/gcloud-aio
.. _Identity-Aware Proxy: https://cloud.google.com/iap
.. _scopes: https://developers.google.com/identity/protocols/googlescopes

.. |pypi| image:: https://img.shields.io/pypi/v/gcloud-aio-auth.svg?style=flat-square
    :alt: Latest PyPI Version (gcloud-aio-auth)
    :target: https://pypi.org/project/gcloud-aio-auth/

.. |pythons-aio| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-auth.svg?style=flat-square&label=python (aio)
    :alt: Python Version Support (gcloud-aio-auth)
    :target: https://pypi.org/project/gcloud-aio-auth/

.. |pythons-rest| image:: https://img.shields.io/pypi/pyversions/gcloud-rest-auth.svg?style=flat-square&label=python (rest)
    :alt: Python Version Support (gcloud-rest-auth)
    :target: https://pypi.org/project/gcloud-rest-auth/
