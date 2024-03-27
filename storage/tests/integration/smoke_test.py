import gzip
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
    from aiohttp import ClientError as ResponseError
    from aiohttp import ClientSession as Session


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'uploaded_data,expected_data,file_extension', [
        ('test', b'test', 'txt'),
        (b'test', b'test', 'bin'),
        (
            json.dumps({'data': 1}), json.dumps(
                {'data': 1},
            ).encode('utf-8'), 'json',
        ),
    ],
)
async def test_object_life_cycle(
    bucket_name, creds, uploaded_data,
    expected_data, file_extension,
):
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.{file_extension}'
    copied_object_name = f'copyof_{object_name}'

    async with Session() as session:
        storage = Storage(service_file=creds, session=session)
        await storage.upload(bucket_name, object_name, uploaded_data)

        bucket = storage.get_bucket(bucket_name)
        blob = await bucket.get_blob(object_name)
        constructed_result = await blob.download()
        _assert_expected_data(expected_data, constructed_result)

        direct_result = await storage.download(bucket_name, object_name)
        _assert_expected_data(expected_data, direct_result)

        await storage.copy(
            bucket_name, object_name, bucket_name,
            new_name=copied_object_name,
        )

        direct_result = await storage.download(bucket_name, copied_object_name)
        _assert_expected_data(expected_data, direct_result)

        await storage.delete(bucket_name, object_name)
        await storage.delete(bucket_name, copied_object_name)

        with pytest.raises(ResponseError):
            await storage.download(bucket_name, object_name)

        with pytest.raises(ResponseError):
            await storage.download(bucket_name, copied_object_name)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'uploaded_data,expected_data,file_extension', [
        ('test', b'test', 'txt'),
        (b'test', b'test', 'bin'),
        (
            json.dumps({'data': 1}), json.dumps(
                {'data': 1},
            ).encode('utf-8'), 'json',
        ),
    ],
)
async def test_zipped_upload(
    bucket_name, creds, uploaded_data,
    expected_data, file_extension,
):
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.{file_extension}'

    async with Session() as session:
        storage = Storage(service_file=creds, session=session)
        await storage.upload(bucket_name, object_name, uploaded_data,
                             zipped=True)

        bucket = storage.get_bucket(bucket_name)
        blob = await bucket.get_blob(object_name)

        # Download file from GCS without the Accept-Encoding: gzip. The
        # data will be served uncompressed by GCS
        constructed_result = await blob.download()
        _assert_expected_data(expected_data, constructed_result)

        # Specify that the file should be downloaded compressed
        constructed_result = await blob.download(auto_decompress=False)
        _assert_expected_data(expected_data, constructed_result,
                              compressed=True)

        # Do the same but using the storage directly
        direct_result = await storage.download(bucket_name, object_name)
        _assert_expected_data(expected_data, direct_result)

        direct_result = await storage.download(
            bucket_name, object_name, headers={'Accept-Encoding': 'gzip'})
        _assert_expected_data(expected_data, direct_result, compressed=True)


def _assert_expected_data(expected_data, actual_data, compressed=False):
    actual_data = gzip.decompress(actual_data) if compressed else actual_data
    assert expected_data == actual_data
