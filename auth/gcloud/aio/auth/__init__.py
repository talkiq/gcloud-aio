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
from gcloud.aio.auth import Token


client = IamClient()
pubkeys = await client.list_public_keys()

token = Token()
print(await token.get())
```

Additionally, the `Token` constructor accepts the following optional arguments:

* `service_file`: path to a [service account][service-account] authorized user
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

[service-account]: https://console.cloud.google.com/iam-admin/serviceaccounts
"""
from pkg_resources import get_distribution

__version__ = get_distribution('gcloud-aio-auth').version

from gcloud.aio.auth.build_constants import BUILD_GCLOUD_REST
from gcloud.aio.auth.iam import IamClient
from gcloud.aio.auth.session import AioSession
from gcloud.aio.auth.token import Token
from gcloud.aio.auth.utils import decode, encode

__all__ = [
    'AioSession',
    'BUILD_GCLOUD_REST',
    'IamClient',
    'Token',
    '__version__',
    'decode',
    'encode',
]
