"""
This library implements various methods for working with the Google IAM / auth
APIs. This includes authenticating for the purpose of using other Google APIs,
managing service accounts and public keys, URL-signing blobs, etc.

## Installation

```console
$ pip install --upgrade gcloud-aio-auth
```

## Usage

```python
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

The `IapToken` constructor accepts the following optional arguments:

* `service_file`: path to a [service account][service-account], authorized user
  file, or any other application credentials. Alternatively, you can pass a
  file-like object, like an `io.StringIO` instance, in case your credentials
  are not stored in a file but in memory. If omitted, will attempt to find one
  on your path or fallback to generating a token from GCE metadata.
* `session`: an `aiohttp.ClientSession` instance to be used for all requests.
  If omitted, a default session will be created. If you use the default
  session, you may be interested in using `Token()` as a context manager
  (`async with Token(..) as token:`) or explicitly calling the `Token.close()`
  method to ensure the session is cleaned up appropriately.
* `service_account`: an optional string denoting a GCP service account which
  takes the form of an email address. Only valid (and required!) for
  authentication with a project's authorized users. [Impersonating a service
  account][impersonating-sa] is required when generating an ID token in this
  case.

The `Token` constructor accepts the following optional arguments:

* `service_file`: path to a [service account][service-account], authorized user
  file, or any other application credentials. Alternatively, you can pass a
  file-like object, like an `io.StringIO` instance, in case your credentials
  are not stored in a file but in memory. If omitted, will attempt to find one
  on your path or fallback to generating a token from GCE metadata.
* `session`: an `aiohttp.ClientSession` instance to be used for all requests.
  If omitted, a default session will be created. If you use the default
  session, you may be interested in using `Token()` as a context manager
  (`async with Token(..) as token:`) or explicitly calling the `Token.close()`
  method to ensure the session is cleaned up appropriately.
* `scopes`: an optional list of GCP `scopes`_ for which to generate our token.
  Only valid (and required!) for [service account][service-account]
  authentication.

[impersonating-sa]: https://cloud.google.com/iap/docs/authentication-howto#obtaining_an_oidc_token_in_all_other_cases  # pylint: ignore=line-too-long
[service-account]: https://console.cloud.google.com/iam-admin/serviceaccounts
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
