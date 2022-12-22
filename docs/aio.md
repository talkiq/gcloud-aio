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
