import json
import uuid

import pytest
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.storage import Storage

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import HTTPError as ResponseError
    from requests import Session
else:
    from aiohttp import ClientResponseError as ResponseError
    from aiohttp import ClientSession as Session


@pytest.mark.asyncio
@pytest.mark.parametrize('uploaded_data,expected_data,file_extension', [
    ('test', b'test', 'txt'),
    (b'test', b'test', 'bin'),
    (json.dumps({'data': 1}), json.dumps({'data': 1}).encode('utf-8'), 'json'),
])
async def test_object_life_cycle(bucket_name, creds, uploaded_data,
                                 expected_data, file_extension):
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.{file_extension}'
    copied_object_name = f'copyof_{object_name}'

    async with Session() as session:
        storage = Storage(service_file=creds, session=session)
        await storage.upload(bucket_name, object_name, uploaded_data)

        bucket = storage.get_bucket(bucket_name)
        blob = await bucket.get_blob(object_name)
        constructed_result = await blob.download()
        assert constructed_result == expected_data

        direct_result = await storage.download(bucket_name, object_name)
        assert direct_result == expected_data

        await storage.copy(bucket_name, object_name, bucket_name,
                           new_name=copied_object_name)

        direct_result = await storage.download(bucket_name, copied_object_name)
        assert direct_result == expected_data

        await storage.delete(bucket_name, object_name)
        await storage.delete(bucket_name, copied_object_name)

        with pytest.raises(ResponseError):
            await storage.download(bucket_name, object_name)

        with pytest.raises(ResponseError):
            await storage.download(bucket_name, copied_object_name)
