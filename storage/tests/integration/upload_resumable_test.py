import json
import uuid

import aiohttp
import pytest
from gcloud.aio.storage import Storage


@pytest.mark.asyncio
@pytest.mark.parametrize('uploaded_data,expected_data,file_extension', [
    ('test', b'test', 'txt'),
    (json.dumps({'data': 1}), json.dumps({'data': 1}).encode('utf-8'), 'json'),
    (json.dumps([1, 2, 3]), json.dumps([1, 2, 3]).encode('utf-8'), 'json'),
    ('test'.encode('utf-8'), 'test'.encode('utf-8'), 'bin'),
])
async def test_upload_resumable(bucket_name, creds, project, uploaded_data,
                                expected_data, file_extension):
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.{file_extension}'

    async with aiohttp.ClientSession() as session:
        storage = Storage(project, creds, session=session)
        res = await storage.upload(bucket_name, object_name, uploaded_data,
                                   force_resumable_upload=True)

        downloaded_data = await storage.download(bucket_name, res['name'])
        assert expected_data == downloaded_data

        await storage.delete(bucket_name, res['name'])
