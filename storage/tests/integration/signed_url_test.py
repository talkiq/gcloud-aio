
import aiohttp
import pytest
from gcloud.aio.auth import IamCredentialsClient
from gcloud.aio.storage import Bucket
from gcloud.aio.storage import Storage


@pytest.mark.asyncio
@pytest.mark.parametrize('uploaded_data,expected_data,file_extension', [
    ('test', b'test', 'txt'),
])
async def test_upload_resumable(project, bucket_name, creds, uploaded_data,
                                expected_data, file_extension):
    object_name = f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.{file_extension}'

    async with aiohttp.ClientSession() as session:
        storage = Storage(service_file=creds, session=session)
        await storage.upload(bucket_name, object_name, uploaded_data, force_resumable_upload=True)

        bucket = Bucket(storage, bucket_name)
        blob = bucket.get_blob(object_name, session=session)

        iam_credentials_client = IamCredentialsClient(service_file=creds, project=project,
                                                      session=session)

        signed_url = await blob.get_signed_url(60, am_credenditals_client=iam_credentials_client)

        resp = await session.get(signed_url)
        assert False, resp

        #downloaded_data = await storage.download(bucket_name, res['name'])
        #try:
        #  assert expected_data == downloaded_data
        #finally:
        #  await storage.delete(bucket_name, res['name'])
