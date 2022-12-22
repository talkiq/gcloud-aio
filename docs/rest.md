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
