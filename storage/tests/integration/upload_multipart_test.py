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
@pytest.mark.parametrize('uploaded_data,expected_data,file_extension', [
    ('test', b'test', 'txt'),
    (json.dumps({'data': 1}), json.dumps({'data': 1}).encode('utf-8'), 'json'),
    (json.dumps([1, 2, 3]), json.dumps([1, 2, 3]).encode('utf-8'), 'json'),
    ('test'.encode('utf-8'), 'test'.encode('utf-8'), 'bin'),
    (io.BytesIO(RANDOM_BINARY), RANDOM_BINARY, 'bin'),
    (io.StringIO(RANDOM_STRING), RANDOM_STRING.encode('utf-8'), 'txt'),
])
async def test_upload_multipart(bucket_name, creds, uploaded_data,
                                expected_data, file_extension):
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.{file_extension}'

    async with Session() as session:
        storage = Storage(service_file=creds, session=session)
        res = await storage.upload(bucket_name, object_name, uploaded_data,
                                   metadata={'Content-Disposition': 'inline'})

        try:
            assert res['name'] == object_name

            downloaded_data = await storage.download(bucket_name, res['name'])
            assert downloaded_data == expected_data

            downloaded_metadata = await storage.download_metadata(bucket_name,
                                                                  res['name'])
            assert downloaded_metadata.pop('contentDisposition') == 'inline'
        finally:
            # TODO: don't bother
            # await storage.delete(bucket_name, res['name'])
            pass
