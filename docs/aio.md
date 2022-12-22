## Emulator Usage

All of our API clients are integrated to make use of the official Google emulators, where those exist. As a general rule, this means you can set the `$FOO_EMULATOR_HOST` environment variable (where `$FOO` is the service being emulated, such as `PUBSUB_EMULATOR_HOST`) and your `gcloud` client will point to the emulator rather than the live APIs.

Alternatively, you can provide the `api_root` option to any relevant constructor to have full control over the API being used. Note that while the environment variable expects just the hostname (to support the standard Google emulator usecase), if you assign this value manually via the contructor arg you must include the entire path.

If you override the API value (either by constructor option or environment variable), tls verification and other such security measures will be disabled as needed. This feature is not intended for production use!

Note also that this library only supports a single version of the Google APIs at a given time (generally the most recent version). If the API you point to does not conform to the correct version of the spec, we make no promises as to what might happen.

For example:

```python
client = gcloud.aio.datastore.Datastore()
assert client._api_root == 'https://datastore.googleapis.com/v1'

# generally set via `gcloud emulators datastore env-init`
os.environ['DATASTORE_EMULATOR_HOST'] = '127.0.0.1:8432'
client = gcloud.aio.datastore.Datastore()
assert client._api_root == 'http://127.0.0.1:8432/v1'

client = gcloud.aio.datastore.Datastore(api_root='http://example.com/datastoreapi')
assert client._api_root == 'http://example.com/datastoreapi'
```

Note that, in any case, these values will be loaded at the time the class instance is constructed.

## Session Management

Since we use `aiohttp` under the hood, ensuring we properly close our `ClientSession` upon shutdown is important to avoid "unclosed connection" errors.

As such, there are several possible ways to handle session management depending on your use-case. Note that these methods apply to all `gcloud-aio-*` classes.

**Manually Close the Class**

If you've created the class manually, you'll have to close it:

```python
client = gcloud.aio.datastore.Datastore(...)
# use the class
await client.close()
```

**Context Manager**

Alternatively, you can let a context manager handle that for you:

```python
async with gcloud.aio.datastore.Datastore(...) as client:
    # use the class
```

**Manage Your Own Session**

If you need to manage your own session, you'll want to make sure you handle everything:

```python
async with aiohttp.ClientSession() as session:
    client = gcloud.aio.datastore.Datastore(..., session=session)
    # use the class

    # DO NOT call `client.close()`, or the `async with ClientSession` will
    # attempt to close a second time.
```

## Token Management

By default, you should not need to care about managing a `gcloud.aio.auth.Token` instance. When you initialize a given client library, it will handle creating a token with the correct scopes.

However, in some cases you may find it valuable to share a token across multiple libraries (eg. to include the HTTP calls in a single session or to reduce how many individual refreshes need to happen). In that case, you can pass it in as follows.

Note that if you are using a service account file, setting explicit scopes is mandatory! As such, you'll need to make sure your token has the correct scopes for all the libraries you plan to use it with.

```python
scopes = [
    'https://www.googleapis.com/auth/cloudkms',
    'https://www.googleapis.com/auth/datastore',
]

async with gcloud.aio.auth.Token(scopes=scopes) as token:
    datastore = gcloud.aio.datastore.Datastore(..., token=token)
    kms = gcloud.aio.kms.KMS(..., token=token)
```

## Compatibility

Here are notes on compatibility issues. While we cannot offer specific support for issues originating from other projects, we can point toward known resolutions.

- Google Cloud Functions pins `yarl`; `gcloud-aio-*` indirectly requires `yarl` via `aiohttp` and an unpinned version of `yarl` can cause your cloud functions to stop building. Please pin your requirements as described here: [Google Cloud Function Dependencies](https://cloud.google.com/functions/docs/writing/specifying-dependencies-python).
