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

The library supports multiple authentication methods:
- Service account credentials
- Authorized user credentials
- GCE metadata credentials
- Impersonated service account credentials
- External account credentials (for workload identity federation)

|pypi| |pythons|

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-{aio,rest}-auth

Usage
-----

Basic Usage
~~~~~~~~~~

.. code-block:: python

    from gcloud.aio.auth import Token

    # Using default credentials (searches for credentials in standard locations)
    token = Token()
    access_token = await token.get()

    # Using a specific service account file
    token = Token(service_file='path/to/service-account.json')
    access_token = await token.get()

    # Using a custom session
    import aiohttp
    async with aiohttp.ClientSession() as session:
        token = Token(session=session)
        access_token = await token.get()

Service Account Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from gcloud.aio.auth import Token

    # Using service account with specific scopes
    token = Token(
        service_file='path/to/service-account.json',
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    access_token = await token.get()

    # Get the project ID
    project_id = await token.get_project()

Authorized User Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from gcloud.aio.auth import Token

    # Using authorized user credentials (e.g., from gcloud auth application-default login)
    token = Token(service_file='~/.config/gcloud/application_default_credentials.json')
    access_token = await token.get()

GCE Metadata Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from gcloud.aio.auth import Token

    # When running on Google Compute Engine, metadata server is used automatically
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

The library supports external account credentials for workload identity federation. This allows you to use credentials from external identity providers (like AWS, Azure, or OIDC) to access Google Cloud resources.

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
- URL: Fetches token from a URL endpoint (supports both text and JSON responses)
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

.. |pythons| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-auth.svg?style=flat-square&label=python
    :alt: Python Version Support
    :target: https://pypi.org/project/gcloud-aio-auth/
