import uuid

import aiohttp
import pytest
from gcloud.aio.bigquery import Table


@pytest.mark.asyncio  # type: ignore
async def test_data_is_inserted(creds: str, dataset: str, project: str,
                                table: str) -> None:
    rows = [{'key': uuid.uuid4().hex, 'value': uuid.uuid4().hex}
            for i in range(3)]

    async with aiohttp.ClientSession() as session:
        t = Table(dataset, table, project=project, service_file=creds,
                  session=session)
        await t.insert(rows)
