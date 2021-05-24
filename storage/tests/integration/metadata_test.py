import uuid

import pytest
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.storage import Storage

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session


@pytest.mark.asyncio
async def test_metadata_multipart(bucket_name, creds):
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.txt'
    original_data = f'{uuid.uuid4().hex}'
    original_metadata = {'Content-Disposition': 'inline',
                         'metadata':
                         {'a': 1,
                          'b': 2,
                          'c': [1, 2, 3],
                          'd': {'a': 4, 'b': 5}}}
    # Google casts all metadata elements as string.
    google_metadata = {'Content-Disposition': 'inline',
                       'metadata':
                       {'a': str(1),
                        'b': str(2),
                        'c': str([1, 2, 3]),
                        'd': str({'a': 4, 'b': 5})}}

    async with Session() as session:
        storage = Storage(service_file=creds, session=session)

        # Without metadata
        res0 = await storage.upload(bucket_name, object_name, original_data,
                                    force_resumable_upload=False)
        data0 = await storage.download(bucket_name, res0['name'])
        await storage.download_metadata(bucket_name, res0['name'])

        # With metadata
        res = await storage.upload(bucket_name, object_name, original_data,
                                   metadata=original_metadata)
        data = await storage.download(bucket_name, res['name'])
        data_metadata = await storage.download_metadata(bucket_name,
                                                        res['name'])

        assert res['name'] == object_name
        assert str(data, 'utf-8') == original_data
        assert data == data0

        assert data_metadata.pop('contentDisposition') == 'inline'
        assert data_metadata['metadata'] == google_metadata['metadata']


@pytest.mark.asyncio
async def test_metadata_resumable(bucket_name, creds):
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.txt'
    original_data = f'{uuid.uuid4().hex}'
    original_metadata = {'Content-Disposition': 'inline',
                         'metadata':
                         {'a': 1,
                          'b': 2,
                          'c': [1, 2, 3],
                          'd': {'a': 4, 'b': 5}}}
    # Google casts all metadata elements as string.
    google_metadata = {'Content-Disposition': 'inline',
                       'metadata':
                       {'a': str(1),
                        'b': str(2),
                        'c': str([1, 2, 3]),
                        'd': str({'a': 4, 'b': 5})}}

    async with Session() as session:
        storage = Storage(service_file=creds, session=session)

        # Without metadata
        res0 = await storage.upload(bucket_name, object_name, original_data,
                                    force_resumable_upload=True)
        data0 = await storage.download(bucket_name, res0['name'])
        await storage.download_metadata(bucket_name, res0['name'])

        # With metadata
        res = await storage.upload(bucket_name, object_name, original_data,
                                   metadata=original_metadata,
                                   force_resumable_upload=True)
        data = await storage.download(bucket_name, res['name'])
        data_metadata = await storage.download_metadata(bucket_name,
                                                        res['name'])

        assert res['name'] == object_name
        assert str(data, 'utf-8') == original_data
        assert data == data0

        assert data_metadata.pop('contentDisposition') == 'inline'
        assert data_metadata['metadata'] == google_metadata['metadata']
