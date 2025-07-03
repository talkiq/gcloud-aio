import uuid

import pytest
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.storage import Storage

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'shard_data,expected_data,content_type,file_extension', [
        (['foo ', 'bar ', 'baz'], b'foo bar baz', 'text/plain', 'txt'),
    ],
)
async def test_compose(
    bucket_name, creds, shard_data,
    expected_data, content_type, file_extension,
):
    def random_name():
        return f'{uuid.uuid4().hex}/{uuid.uuid4().hex}.{file_extension}'

    shard_names = [random_name() for _ in shard_data]
    object_name = random_name()

    async with Session() as session:
        storage = Storage(service_file=creds, session=session)

        for shard_name, shard_datum in zip(shard_names, shard_data):
            await storage.upload(
                bucket_name,
                shard_name,
                shard_datum,
                metadata={
                    'Content-Disposition': 'inline',
                },
            )
        res = await storage.compose(
            bucket_name,
            object_name,
            shard_names,
            content_type=content_type,
        )

        try:
            assert res['name'] == object_name
            assert res['contentType'] == content_type

            downloaded_data = await storage.download(bucket_name, res['name'])
            assert downloaded_data == expected_data

        finally:
            pass
