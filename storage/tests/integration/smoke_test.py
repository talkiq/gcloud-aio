import json
import uuid

import aiohttp
import pytest
from gcloud.aio.storage import Storage


@pytest.mark.asyncio
@pytest.mark.parametrize('uploaded_data,expected_data,file_extension', [
    ('test', b'test', 'txt'),
    (b'test', b'test', 'bin'),
    (json.dumps({'data': 1}), json.dumps({'data': 1}).encode('utf-8'), 'json'),
])
async def test_object_life_cycle(bucket_name, creds, uploaded_data,
                                 expected_data, file_extension):
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.{file_extension}'

    async with aiohttp.ClientSession() as session:
        storage = Storage(service_file=creds, session=session)
        await storage.upload(bucket_name, object_name, uploaded_data)

        bucket = storage.get_bucket(bucket_name)
        blob = await bucket.get_blob(object_name)
        constructed_result = await blob.download()
        assert constructed_result == expected_data

        direct_result = await storage.download(bucket_name, object_name)
        assert direct_result == expected_data

        await storage.delete(bucket_name, object_name)

        with pytest.raises(aiohttp.client_exceptions.ClientResponseError):
            await storage.download(bucket_name, object_name)
