# pylint: disable=line-too-long
"""
This library implements various methods for working with the Google IAM / auth
APIs. This includes authenticating for the purpose of using other Google APIs,
managing service accounts and public keys, URL-signing blobs, etc.

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-aio-auth

Usage
-----

.. code-block:: python

    from gcloud.aio.auth import IamClient
    from gcloud.aio.auth import IapToken
    from gcloud.aio.auth import Token


    client = IamClient()
    pubkeys = await client.list_public_keys()

    iap_token = IapToken('https://your.service.url.com')
    print(await iap_token.get())

    token = Token()
    print(await token.get())
```

The ``IapToken`` constructor accepts the following optional arguments:

* ``service_file``: path to a `service account`_, authorized user file, or any
  other application credentials. Alternatively, you can pass a file-like
  object, like an ``io.StringIO`` instance, in case your credentials are not
  stored in a file but in memory. If omitted, will attempt to find one on your
  path or fallback to generating a token from GCE metadata.
* ``session``: an ``aiohttp.ClientSession`` instance to be used for all
  requests. If omitted, a default session will be created. If you use the
  default session, you may be interested in using ``IapToken()`` as a context
  manager (``async with IapToken(..) as token:``) or explicitly calling the
  ``IapToken.close()`` method to ensure the session is cleaned up
  appropriately.
* ``impersonating_service_account``: an optional string denoting a GCP service
  account which takes the form of an email address. Only valid (and required!)
  for authentication with a project's authorized users. `Impersonating a
  service account`_ is required when generating an ID token in this case.

The ``Token`` constructor accepts the following optional arguments:

* ``service_file``: path to a `service account`_ authorized user file, or any
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
* ``target_principal``: The service account to generate the access token for.
  The **iam.serviceAccounts.getAccessToken** permission on that service account
  is required.
* ``delegates``: The sequence of service accounts in a delegation chain. This
  field is required for delegated requests. Each service account must be
  granted the **roles/iam.serviceAccountTokenCreator** role on its next service
  account in the chain. The last service account in the chain must be granted
  the **roles/iam.serviceAccountTokenCreator** role on the service account that
  is specified in the ``target_principal``.

CLI
---

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

.. _service account: https://console.cloud.google.com/iam-admin/serviceaccounts
.. _Impersonating a service account: https://cloud.google.com/iap/docs/authentication-howto#obtaining_an_oidc_token_in_all_other_cases
.. _scopes: https://developers.google.com/identity/protocols/oauth2/scopes
"""
import importlib.metadata

from .build_constants import BUILD_GCLOUD_REST
from .iam import IamClient
from .session import AioSession
from .token import IapToken
from .token import Token
from .utils import decode
from .utils import encode


__version__ = importlib.metadata.version('gcloud-aio-auth')
__all__ = [
    'AioSession',
    'BUILD_GCLOUD_REST',
    'IamClient',
    'IapToken',
    'Token',
    '__version__',
    'decode',
    'encode',
]
