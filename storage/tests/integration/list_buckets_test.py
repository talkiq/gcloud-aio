import pytest
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.storage import Storage

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session


@pytest.mark.asyncio
async def test_list_buckets(project_name, creds, expected_buckets):

    async with Session() as session:
        storage = Storage(service_file=creds, session=session)

        buckets = await storage.list_buckets(project_name)

        # there are 4 buckets in dialpad-oss project
        assert len(buckets) == 4

        for bucket in buckets:
            assert bucket.name in expected_buckets
