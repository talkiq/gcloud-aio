import uuid

import pytest
from gcloud.aio.auth import AioSession as RestSession  # pylint: disable=no-name-in-module
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.bigquery import Table

# Selectively load libraries based on the package
# TODO: Can we somehow just pick up the pacakge name instead of this
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session

@pytest.mark.asyncio  # type: ignore
async def test_data_is_inserted(creds: str, dataset: str, project: str,
                                table: str) -> None:
    rows = [{'key': uuid.uuid4().hex, 'value': uuid.uuid4().hex}
            for i in range(3)]

    async with Session() as _s:
        s = RestSession()
        s.session = _s
        t = Table(dataset, table, project=project, service_file=creds,
                  session=s)
        await t.insert(rows)
