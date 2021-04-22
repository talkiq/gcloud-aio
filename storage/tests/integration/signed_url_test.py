import uuid

import pytest
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.storage import Bucket
from gcloud.aio.storage import Storage

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session


@pytest.mark.asyncio
@pytest.mark.parametrize('data', ['test'])
async def test_gcs_signed_url(bucket_name, creds, data):
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.txt'

    async with Session() as session:
        storage = Storage(service_file=creds, session=session)
        await storage.upload(bucket_name, object_name, data,
                             force_resumable_upload=True)

        bucket = Bucket(storage, bucket_name)
        blob = await bucket.get_blob(object_name, session=session)

        signed_url = await blob.get_signed_url(60)

        resp = await session.get(signed_url)

        try:
            downloaded_data: str = await resp.text()
        except (AttributeError, TypeError):
            downloaded_data: str = str(resp.text)

        try:
            assert data == downloaded_data
        finally:
            await storage.delete(bucket_name, blob.name)
