import asyncio
import os
import uuid

import aiohttp
from gcloud.aio.bigquery import make_stream_insert


async def insert_data(project, creds, dataset_name, table_name, rows):
    async with aiohttp.ClientSession() as session:
        stream_insert = make_stream_insert(project, creds, dataset_name,
                                           table_name, session=session)
        result = await stream_insert(rows)

    assert result


def test_data_is_inserted():
    project = os.environ['GCLOUD_PROJECT']
    creds = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    dataset_name = 'test'
    table_name = 'test'
    rows = [{'key': uuid.uuid4().hex, 'value': uuid.uuid4().hex}
            for i in range(3)]

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        insert_data(project, creds, dataset_name, table_name, rows))
