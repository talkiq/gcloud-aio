import io
import json
import os
import random
import string
import uuid

import pytest
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.storage import Storage

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session

# TODO: use hypothesis
RANDOM_BINARY = os.urandom(2045)

# Updated statement to make it compatible with python2
rand_str_list = [random.choice(string.ascii_letters) for r in range(0, 1054)]
RANDOM_STRING = ''.join(rand_str_list)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'uploaded_data,range_header,expected_data,file_extension', [
        (json.dumps([1, 2, 3]), 'bytes=0-1', json.dumps(
            [1, 2, 3]).encode('utf-8')[0:2], 'json'),
        ('test'.encode('utf-8'), 'bytes=2-3', 'test'.encode('utf-8')[2:4],
         'bin'),
        (io.BytesIO(RANDOM_BINARY), 'bytes=1-1000', RANDOM_BINARY[1:1001],
         'bin'),
        (io.StringIO(RANDOM_STRING), 'bytes=10-100',
         RANDOM_STRING.encode('utf-8')[10:101], 'txt'),
    ])
async def test_download_range(bucket_name, creds, uploaded_data, range_header,
                              expected_data, file_extension):
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.{file_extension}'

    async with Session() as session:
        storage = Storage(service_file=creds, session=session)
        res = await storage.upload(bucket_name, object_name, uploaded_data)

        downloaded_data = await storage.download(
            bucket_name, res['name'], headers={'Range': range_header})
        assert expected_data == downloaded_data

        await storage.delete(bucket_name, res['name'])
