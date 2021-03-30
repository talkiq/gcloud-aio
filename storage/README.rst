(Asyncio OR Threadsafe) Python Client for Google Cloud Storage
==============================================================

    This is a shared codebase for ``gcloud-aio-storage`` and
    ``gcloud-rest-storage``

|pypi| |pythons-aio| |pythons-rest|

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-{aio,rest}-storage

Usage
-----

To upload a file, you might do something like the following:

.. code-block:: python

    import aiofiles
    import aiohttp
    from gcloud.aio.storage import Storage


    async with aiohttp.ClientSession() as session:
        client = Storage(session=session)

        async with aiofiles.open('/path/to/my/file', mode="r") as f:
            contents = await f.read()
            status = await client.upload(
                'my-bucket-name',
                'path/to/gcs/folder',
                output,
            )
            print(status)

Note that there are multiple ways to accomplish the above, ie,. by making use
of the ``Bucket`` and ``Blob`` convenience classes if that better fits your
use-case.

Of course, the major benefit of using an async library is being able to
parallelize operations like this. Since ``gcloud-aio-storage`` is fully
asyncio-compatible, you can use any of the builtin asyncio method to perform
more complicated operations:

.. code-block:: python

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
                client.upload('my-bucket-name', path, file_) for path, file_ in uploads
            ]
        )

You can also refer `smoke test`_ for more info and examples.

Note that you can also let ``gcloud-aio-storage`` do its own session
management, so long as you give us a hint when to close that session:

.. code-block:: python

    async with Storage() as client:
        # closes the client.session on leaving the context manager

    # OR

    client = Storage()
    # do stuff
    await client.close()  # close the session explicitly

File Encodings
~~~~~~~~~~~~~~

In some cases, ``aiohttp`` needs to transform the objects returned from GCS
into strings, eg. for debug logging and other such issues. The built-in
``await response.text()`` operation relies on `chardet`_ for guessing the
character encoding in any cases where it can not be determined based on the
file metadata.

Unfortunately, this operation can be extremely slow, especially in cases where
you might be working with particularly large files. If you notice odd latency
issues when reading your results, you may want to set your character encoding
more explicitly within GCS, eg. by ensuring you set the ``contentType`` of the
relevant objects to something suffixed with ``; charset=utf-8``. For example,
in the case of ``contentType='application/x-netcdf'`` files exhibiting latency,
you could instead set ``contentType='application/x-netcdf; charset=utf-8``. See
`#172`_ for more info!

Emulators
~~~~~~~~~

For testing purposes, you may want to use ``gcloud-aio-storage`` along with a
local GCS emulator. Setting the ``$STORAGE_EMULATOR_HOST`` environment variable
to the address of your emulator should be enough to do the trick.

For example, using `fsouza/fake-gcs-server`_, you can do:

.. code-block:: console

    docker run -d -p 4443:4443 -v $PWD/my-sample-data:/data fsouza/fake-gcs-server
    export STORAGE_EMULATOR_HOST='0.0.0.0:4443'

Any ``gcloud-aio-storage`` requests made with that environment variable set
will query ``fake-gcs-server`` instead of the official GCS API.

Note that some emulation systems require disabling SSL -- if you're using a
custom http session, you may need to disable SSL verification.

Contributing
------------

Please see our `contributing guide`_.

.. _#172: https://github.com/talkiq/gcloud-aio/issues/172
.. _chardet: https://pypi.org/project/chardet/
.. _contributing guide: https://github.com/talkiq/gcloud-aio/blob/master/.github/CONTRIBUTING.rst
.. _fsouza/fake-gcs-server: https://github.com/fsouza/fake-gcs-server
.. _smoke test: https://github.com/talkiq/gcloud-aio/blob/master/storage/tests/integration/smoke_test.py

.. |pypi| image:: https://img.shields.io/pypi/v/gcloud-aio-storage.svg?style=flat-square
    :alt: Latest PyPI Version (gcloud-aio-storage)
    :target: https://pypi.org/project/gcloud-aio-storage/

.. |pythons-aio| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-storage.svg?style=flat-square&label=python (aio)
    :alt: Python Version Support (gcloud-aio-storage)
    :target: https://pypi.org/project/gcloud-aio-storage/

.. |pythons-rest| image:: https://img.shields.io/pypi/pyversions/gcloud-rest-storage.svg?style=flat-square&label=python (rest)
    :alt: Python Version Support (gcloud-rest-storage)
    :target: https://pypi.org/project/gcloud-rest-storage/
