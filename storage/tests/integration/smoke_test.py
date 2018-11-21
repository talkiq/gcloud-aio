import json
import os
import uuid

import aiohttp
import pytest
from gcloud.aio.storage import Storage

PROJECT = os.environ['GCLOUD_PROJECT']
CREDS = os.environ['GOOGLE_APPLICATION_CREDENTIALS']


@pytest.mark.asyncio
@pytest.mark.parametrize('uploaded_data,expected_data,content_type', [
    ('test', 'test', 'text/plain'),
    (json.dumps({'data': 1}), json.dumps({'data': 1}), 'application/json'),
])
async def test_object_life_cycle(uploaded_data, expected_data, content_type):
    bucket_name = 'talkiq-integration-test'
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.txt'

    async with aiohttp.ClientSession() as session:
        storage = Storage(PROJECT, CREDS, session=session)
        await storage.upload(bucket_name, object_name, uploaded_data, content_type)

        bucket = storage.get_bucket(bucket_name)
        blob = await bucket.get_blob(object_name)
        contructed_result = await blob.download()

        assert contructed_result == expected_data

        direct_result = await storage.download(bucket_name,
                                               object_name)

        assert direct_result == expected_data

        await storage.delete(bucket_name, object_name)

        with pytest.raises(aiohttp.client_exceptions.ClientResponseError):
            await storage.download(bucket_name, object_name)
