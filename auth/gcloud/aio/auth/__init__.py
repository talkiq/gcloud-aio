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

Basic Usage
~~~~~~~~~~~

.. code-block:: python

    from gcloud.aio.auth import Token

    # Use default credentials (searches for credentials in standard locations)
    token = Token()
    access_token = await token.get()

    # Use a specific service account file
    token = Token(service_file='path/to/service-account.json')
    access_token = await token.get()

    # Use a custom session
    import aiohttp
    async with aiohttp.ClientSession() as session:
        token = Token(session=session)
        access_token = await token.get()

Service Account Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from gcloud.aio.auth import Token

    # Use service account with specific scopes
    token = Token(
        service_file='path/to/service-account.json',
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    access_token = await token.get()

Authorized User Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from gcloud.aio.auth import Token

    # Use authorized user credentials (e.g., from gcloud auth application-default login)
    token = Token(service_file='~/.config/gcloud/application_default_credentials.json')
    access_token = await token.get()

GCE Metadata Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from gcloud.aio.auth import Token

    # When running on GCE, the metadata server is used automatically
    token = Token()
    access_token = await token.get()

Service Account Impersonation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from gcloud.aio.auth import Token

    # Impersonate a service account
    token = Token(
        service_file='path/to/source-credentials.json',
        target_principal='target-service@project.iam.gserviceaccount.com',
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    access_token = await token.get()

    # With delegation chain
    token = Token(
        service_file='path/to/source-credentials.json',
        target_principal='target-service@project.iam.gserviceaccount.com',
        delegates=['delegate-service@project.iam.gserviceaccount.com'],
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    access_token = await token.get()

External Account Credentials
---------------------------

The library supports external account credentials for workload identity
federation. This allows you to use credentials from external identity providers
(like AWS, Azure, or OIDC) to access Google Cloud resources.

Example configuration file:

.. code-block:: json

    {
        "type": "external_account",
        "audience": "//iam.googleapis.com/projects/123456/locations/global/workloadIdentityPools/pool/subject",
        "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
        "token_url": "https://sts.googleapis.com/v1/token",
        "credential_source": {
            "type": "url",
            "url": "http://169.254.169.254/metadata/identity/oauth2/token",
            "headers": {
                "Metadata": "true"
            }
        }
    }

Usage:

.. code-block:: python

    from gcloud.aio.auth import Token

    # Basic usage with external account credentials
    token = Token(service_file='path/to/external_account_credentials.json')
    access_token = await token.get()

    # With specific scopes
    token = Token(
        service_file='path/to/external_account_credentials.json',
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    access_token = await token.get()

The library supports multiple credential source types:
- URL: Fetches token from a URL endpoint (supports both plaintext and JSON)
- File: Reads token from a file
- Environment: Gets token from an environment variable

IAP Token Usage
~~~~~~~~~~~~~

.. code-block:: python

    from gcloud.aio.auth import IapToken

    # Basic IAP token usage
    iap_token = IapToken('https://your-iap-secured-service.com')
    id_token = await iap_token.get()

    # With service account impersonation
    iap_token = IapToken(
        'https://your-iap-secured-service.com',
        impersonating_service_account='service@project.iam.gserviceaccount.com'
    )
    id_token = await iap_token.get()

IAM Client Usage
~~~~~~~~~~~~~~

.. code-block:: python

    from gcloud.aio.auth import IamClient

    # List public keys
    client = IamClient()
    pubkeys = await client.list_public_keys()

    # Get a specific public key
    key = await client.get_public_key('key-id')

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
