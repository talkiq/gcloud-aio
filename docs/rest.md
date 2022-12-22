## Emulator Usage

All of our API clients are integrated to make use of the official Google emulators, where those exist. As a general rule, this means you can set the `$FOO_EMULATOR_HOST` environment variable (where `$FOO` is the service being emulated, such as `PUBSUB_EMULATOR_HOST`) and your `gcloud` client will point to the emulator rather than the live APIs.

Alternatively, you can provide the `api_root` option to any relevant constructor to have full control over the API being used. Note that while the environment variable expects just the hostname (to support the standard Google emulator usecase), if you assign this value manually via the contructor arg you must include the entire path.

If you override the API value (either by constructor option or environment variable), tls verification and other such security measures will be disabled as needed. This feature is not intended for production use!

Note also that this library only supports a single version of the Google APIs at a given time (generally the most recent version). If the API you point to does not conform to the correct version of the spec, we make no promises as to what might happen.

For example:

```python
client = gcloud.rest.datastore.Datastore()
assert client._api_root == 'https://datastore.googleapis.com/v1'

# generally set via `gcloud emulators datastore env-init`
os.environ['DATASTORE_EMULATOR_HOST'] = '127.0.0.1:8432'
client = gcloud.rest.datastore.Datastore()
assert client._api_root == 'http://127.0.0.1:8432/v1'

client = gcloud.rest.datastore.Datastore(api_root='http://example.com/datastoreapi')
assert client._api_root == 'http://example.com/datastoreapi'
```

Note that, in any case, these values will be loaded at the time the class instance is constructed.

## Token Management

By default, you should not need to care about managing a `gcloud.rest.auth.Token` instance. When you initialize a given client library, it will handle creating a token with the correct scopes.

However, in some cases you may find it valuable to share a token across multiple libraries (eg. to include the HTTP calls in a single session or to reduce how many individual refreshes need to happen). In that case, you can pass it in as follows.

Note that if you are using a service account file, setting explicit scopes is mandatory! As such, you'll need to make sure your token has the correct scopes for all the libraries you plan to use it with.

```python
scopes = [
    'https://www.googleapis.com/auth/cloudkms',
    'https://www.googleapis.com/auth/datastore',
]

with gcloud.rest.auth.Token(scopes=scopes) as token:
    datastore = gcloud.rest.datastore.Datastore(..., token=token)
    kms = gcloud.rest.kms.KMS(..., token=token)
```
