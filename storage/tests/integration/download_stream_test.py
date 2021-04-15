import io
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
@pytest.mark.parametrize('uploaded_data,expected_data', [
    (io.BytesIO(RANDOM_BINARY), RANDOM_BINARY),
    (io.StringIO(RANDOM_STRING), RANDOM_STRING.encode('utf-8')),
])
async def test_download_stream(bucket_name, creds, uploaded_data,
                               expected_data):
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}'

    async with Session() as session:
        storage = Storage(service_file=creds, session=session)
        res = await storage.upload(bucket_name, object_name, uploaded_data)

        with io.BytesIO(b'') as downloaded_data:
            download_stream = await storage.download_stream(
                bucket_name, res['name'])
            while True:
                chunk = await download_stream.read(4096)
                if not chunk:
                    break
                downloaded_data.write(chunk)

            assert expected_data == downloaded_data.getvalue()

        await storage.delete(bucket_name, res['name'])
