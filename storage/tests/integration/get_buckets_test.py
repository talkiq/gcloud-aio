import pytest
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.storage import Storage

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session

# get_buckets() method has a timeout=DEFAULT_TIMEOUT which I
# will assume it's ok and there's no need to test it


@pytest.mark.asyncio
async def test_get_buckets(project_name, creds, expected_buckets):

    async with Session() as session:
        storage = Storage(service_file=creds, session=session)

        buckets = await storage.get_buckets(project_name)

        assert len(buckets) == 4

        for bucket in buckets:
            assert bucket.get_name() in expected_buckets
