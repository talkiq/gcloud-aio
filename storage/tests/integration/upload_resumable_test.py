import io
import os
import uuid
import string
import random
import json
import aiohttp
import pytest

from gcloud.aio.storage import Storage

PROJECT = os.environ['GCLOUD_PROJECT']
CREDS = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
BUCKET_NAME = os.environ['BUCKET_NAME']


@pytest.mark.asyncio
@pytest.mark.parametrize('data_to_upload,expected_data,file_extension', [
    ('test', 'test', 'txt'),
    (json.dumps({'data': 1}), '{"data": 1}', 'json'),
    (json.dumps([1, 2, 3]), json.dumps([1, 2, 3]), 'json'),
    ('test'.encode('utf-8'), 'test'.encode('utf-8'), 'bin'),
])
async def test_upload_resumable(data_to_upload, expected_data, file_extension):
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.{file_extension}'

    async with aiohttp.ClientSession() as session:
        storage = Storage(PROJECT, CREDS, session=session)
        res = await storage.upload(BUCKET_NAME, object_name, data_to_upload,
                                   force_resumable_upload=True)

        downloaded_data = await storage.download(BUCKET_NAME, res['name'])

        assert expected_data == downloaded_data
        await storage.delete(BUCKET_NAME, res['name'])


@pytest.mark.asyncio
async def test_upload_string_stream():
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.txt'
    count_chars = 1054
    random_string = ''.join(random.choice(string.ascii_letters)
                            for _ in range(count_chars))
    stream = io.StringIO(random_string)

    async with aiohttp.ClientSession() as session:
        storage = Storage(PROJECT, CREDS, session=session)
        res = await storage.upload(BUCKET_NAME, object_name, stream,
                                   force_resumable_upload=True)

        downloaded_data = await storage.download(BUCKET_NAME, res['name'])

        assert downloaded_data == random_string

        await storage.delete(BUCKET_NAME, res['name'])


@pytest.mark.asyncio
async def test_upload_binary_stream():
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.bin'
    file_size = 2045
    content = os.urandom(file_size)
    stream = io.BytesIO(content)

    async with aiohttp.ClientSession() as session:
        storage = Storage(PROJECT, CREDS, session=session)
        res = await storage.upload(BUCKET_NAME, object_name, stream,
                                   force_resumable_upload=True)

        downloaded_data = await storage.download(BUCKET_NAME, res['name'])

        assert downloaded_data == content

        await storage.delete(BUCKET_NAME, res['name'])


