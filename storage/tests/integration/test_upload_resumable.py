import os
import uuid
import json
import aiohttp
import pytest

from gcloud.aio.storage import Storage

PROJECT = os.environ['GCLOUD_PROJECT']
CREDS = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
BUCKET_NAME = os.environ['BUCKET_NAME']


@pytest.mark.asyncio
@pytest.mark.parametrize('data_to_upload,expected_data,content_type', [
    ('test', 'test', 'text/plain'),
    (json.dumps({'data': 1}), '{"data": 1}', 'application/json'),
    (json.dumps([1, 2, 3]), json.dumps([1, 2, 3]), 'application/json'),
    ('test'.encode('utf-8'), 'test'.encode('utf-8'), 'application/octet-stream'),
])
async def test_given_dict_when_upload_resumable_then_check_upload(data_to_upload, expected_data, content_type):
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.txt'

    async with aiohttp.ClientSession() as session:
        storage = Storage(PROJECT, CREDS, session=session)
        res = await storage.upload(BUCKET_NAME, object_name, data_to_upload, content_type,
                                   upload_type_resumable_always=True)

        downloaded_data = await storage.download(BUCKET_NAME, res['name'])

        assert expected_data == downloaded_data
        await storage.delete(BUCKET_NAME, res['name'])
