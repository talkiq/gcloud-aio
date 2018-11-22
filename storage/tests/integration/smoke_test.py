import json
import os
import uuid

import aiohttp
import pytest
from gcloud.aio.storage import Storage

PROJECT = os.environ['GCLOUD_PROJECT']
CREDS = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
BUCKET_NAME = os.environ['BUCKET_NAME']


@pytest.mark.asyncio
@pytest.mark.parametrize('uploaded_data,expected_data,content_type', [
    ('test', 'test', 'text/plain'),
    (json.dumps({'data': 1}), json.dumps({'data': 1}), 'application/json'),
])
async def test_object_life_cycle(uploaded_data, expected_data, content_type):
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.txt'

    async with aiohttp.ClientSession() as session:
        storage = Storage(PROJECT, CREDS, session=session)
        await storage.upload(BUCKET_NAME, object_name, uploaded_data, content_type)

        bucket = storage.get_bucket(BUCKET_NAME)
        blob = await bucket.get_blob(object_name)
        contructed_result = await blob.download()

        assert contructed_result == expected_data

        direct_result = await storage.download(BUCKET_NAME,
                                               object_name)

        assert direct_result == expected_data

        await storage.delete(BUCKET_NAME, object_name)

        with pytest.raises(aiohttp.client_exceptions.ClientResponseError):
            await storage.download(BUCKET_NAME, object_name)
