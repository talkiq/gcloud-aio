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

.. code:: python

    import asyncio
    import aiohttp
    # pip install aiofile
    from aiofile import AIOFile
    from gcloud.aio.storage import Storage 

    BUCKET_NAME = '<bucket_name>'
    FILE_NAME  = '<file_name>'
    async def async_upload_to_bucket(blob_name, file_obj, folder='uploads'):
        """ Upload files to bucket. """
        async with aiohttp.ClientSession() as session:
            storage = Storage(service_file='./creds.json', session=session) 
            status = await storage.upload(BUCKET_NAME, f'{folder}/{blob_name}', file_obj)
            #info of the uploaded file
            # print(status)
            return status['selfLink']


    async def main():
        async with AIOFile(FILE_NAME, mode='r') as afp:
            f = await afp.read()
            url = await async_upload_to_bucket(FILE_NAME, f)
            print(url)


    # Python 3.6
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

    # Python 3.7+
    # asyncio.run(main())
    
You can also refer `smoke test`_.

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
