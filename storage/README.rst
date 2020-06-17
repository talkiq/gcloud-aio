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

    import aiohttp
    from gcloud.aio.storage import Storage


    async with aiohttp.ClientSession() as session:
        client = Storage(session=session)

        with open('/path/to/my/file', mode='r') as f:
            status = await client.upload('my-bucket-name',
                                         'path/to/gcs/folder',
                                         f.read())
            print(status)

Note that there are multiple ways to accomplish the above, ie,. by making use
of the ``Bucket`` and ``Blob`` convenience classes if that better fits your
use-case.

Of course, the major benefit of using an async library is being able to
parallelize operations like this. Since `gcloud-aio-storage` is fully
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
            with open(local_name, mode='r') as f:
                uploads.append((gcs_name, f.read()))

        # Simultaneously upload all files
        await asyncio.gather(*[client.upload('my-bucket-name', path, file_)
                               for path, file_ in uploads])

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

Contributing
------------

Please see our `contributing guide`_.

.. _contributing guide: https://github.com/talkiq/gcloud-aio/blob/master/.github/CONTRIBUTING.rst
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
