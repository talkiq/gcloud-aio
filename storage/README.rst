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

        async with open('/path/to/my/file', mode='r') as f:
            status = await client.upload('my-bucket-name',
                                         'path/to/gcs/folder',
                                         f.read())
            print(status)

Note that there are multiple ways to accomplish the above, ie,. by making use
of the ``Bucket`` and ``Blob`` convenience classes if that better fits your
use-case.

You can also refer `smoke test`_ for more info and examples.

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
