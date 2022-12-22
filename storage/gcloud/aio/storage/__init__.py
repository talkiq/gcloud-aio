"""
This library implements various methods for working with the Google Storage
APIs.

## Installation

```console
$ pip install --upgrade gcloud-aio-storage
```

## Usage

To upload a file, you might do something like the following:

```python
import aiofiles
import aiohttp
from gcloud.aio.storage import Storage


async with aiohttp.ClientSession() as session:
    client = Storage(session=session)

    async with aiofiles.open('/path/to/my/file', mode="r") as f:
        output = await f.read()
        status = await client.upload(
            'my-bucket-name',
            'path/to/gcs/folder',
            output,
        )
        print(status)
```

Note that there are multiple ways to accomplish the above, ie,. by making use
of the `Bucket` and `Blob` convenience classes if that better fits your
use-case.

Of course, the major benefit of using an async library is being able to
parallelize operations like this. Since `gcloud-aio-storage` is fully
asyncio-compatible, you can use any of the builtin asyncio method to perform
more complicated operations:

```python
my_files = {
    '/local/path/to/file.1': 'path/in/gcs.1',
    '/local/path/to/file.2': 'path/in/gcs.2',
    '/local/path/to/file.3': 'different/gcs/path/filename.3',
}

async with Storage() as client:
    # Prepare all our upload data
    uploads = []
    for local_name, gcs_name in my_files.items():
        async with aiofiles.open(local_name, mode="r") as f:
            contents = await f.read()
            uploads.append((gcs_name, contents))

    # Simultaneously upload all files
    await asyncio.gather(
        *[
            client.upload('my-bucket-name', path, file_)
            for path, file_ in uploads
        ]
    )
```

You can also refer to the [smoke test][smoke-test] for more info and examples.

Note that you can also let `gcloud-aio-storage` do its own session management,
so long as you give us a hint when to close that session:

```python
async with Storage() as client:
    # closes the client.session on leaving the context manager

# OR

client = Storage()
# do stuff
await client.close()  # close the session explicitly
```

## File Encodings

In some cases, `aiohttp` needs to transform the objects returned from GCS into
strings, eg. for debug logging and other such issues. The built-in `await
response.text()` operation relies on [chardet][chardet] for guessing the
character encoding in any cases where it can not be determined based on the
file metadata.

Unfortunately, this operation can be extremely slow, especially in cases where
you might be working with particularly large files. If you notice odd latency
issues when reading your results, you may want to set your character encoding
more explicitly within GCS, eg. by ensuring you set the `contentType` of the
relevant objects to something suffixed with `; charset=utf-8`. For example, in
the case of `contentType='application/x-netcdf'` files exhibiting latency, you
could instead set `contentType='application/x-netcdf; charset=utf-8`. See
[Issue #172][issue-172] for more info!

## Emulators

For testing purposes, you may want to use `gcloud-aio-storage` along with a
local GCS emulator. Setting the `$STORAGE_EMULATOR_HOST` environment variable
to the address of your emulator should be enough to do the trick.

For example, using [fsouza/fake-gcs-server][fake-gcs-server], you can do:

```shell
docker run -d -p 4443:4443 -v $PWD/my-sample-data:/data fsouza/fake-gcs-server
export STORAGE_EMULATOR_HOST='0.0.0.0:4443'
```

Any `gcloud-aio-storage` requests made with that environment variable set will
query `fake-gcs-server` instead of the official GCS API.

Note that some emulation systems require disabling SSL -- if you're using a
custom http session, you may need to disable SSL verification.

## Customization

This library mostly tries to stay agnostic of potential use-cases; as such, we
do not implement any sort of retrying or other policies under the assumption
that we wouldn't get things right for every user's situation.

As such, we recommend configuring your own policies on an as-needed basis. The
[backoff][backoff] library can make this quite straightforward! For example,
you may find it useful to configure something like:

```python
class StorageWithBackoff(gcloud.aio.storage.Storage):
    @backoff.on_exception(backoff.expo, aiohttp.ClientResponseError,
                          max_tries=5, jitter=backoff.full_jitter)
    async def copy(self, *args: Any, **kwargs: Any):
        return await super().copy(*args, **kwargs)

    @backoff.on_exception(backoff.expo, aiohttp.ClientResponseError,
                          max_tries=10, jitter=backoff.full_jitter)
    async def download(self, *args: Any, **kwargs: Any):
        return await super().download(*args, **kwargs)
```

[backoff]: https://pypi.org/project/backoff/
[chardet]: https://pypi.org/project/chardet/
[fake-gcs-server]: https://github.com/fsouza/fake-gcs-server
[issue-172]: https://github.com/talkiq/gcloud-aio/issues/172
[smoke-test]:
https://github.com/talkiq/gcloud-aio/blob/master/storage/tests/integration/smoke_test.py
"""
from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-storage').version

from gcloud.aio.storage.blob import Blob
from gcloud.aio.storage.bucket import Bucket
from gcloud.aio.storage.storage import SCOPES
from gcloud.aio.storage.storage import Storage
from gcloud.aio.storage.storage import StreamResponse


__all__ = [
    'Blob',
    'Bucket',
    'SCOPES',
    'Storage',
    'StreamResponse',
    '__version__',
]
