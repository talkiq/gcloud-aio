import io
import json
import os
import random
import string
import uuid

import aiohttp
import pytest
from gcloud.aio.storage import Storage


# TODO: use hypothesis
RANDOM_BINARY = os.urandom(2045)
RANDOM_STRING = ''.join(random.choices(string.ascii_letters, k=1054))


@pytest.mark.asyncio
@pytest.mark.parametrize('uploaded_data,expected_data,file_extension', [
    ('test', b'test', 'txt'),
    (json.dumps({'data': 1}), json.dumps({'data': 1}).encode('utf-8'), 'json'),
    (json.dumps([1, 2, 3]), json.dumps([1, 2, 3]).encode('utf-8'), 'json'),
    ('test'.encode('utf-8'), 'test'.encode('utf-8'), 'bin'),
    (io.BytesIO(RANDOM_BINARY), RANDOM_BINARY, 'bin'),
    (io.StringIO(RANDOM_STRING), RANDOM_STRING.encode('utf-8'), 'txt'),
])
async def test_upload_resumable(bucket_name, creds, uploaded_data,
                                expected_data, file_extension):
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.{file_extension}'

    async with aiohttp.ClientSession() as session:
        storage = Storage(service_file=creds, session=session)
        res = await storage.upload(bucket_name, object_name, uploaded_data,
                                   force_resumable_upload=True)

        downloaded_data = await storage.download(bucket_name, res['name'])
        assert expected_data == downloaded_data

        await storage.delete(bucket_name, res['name'])
