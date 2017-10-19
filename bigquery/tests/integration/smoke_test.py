import asyncio
import os
import uuid

import aiohttp
from gcloud.aio.bigquery import make_stream_insert
from gcloud.aio.core.utils.aio import fire


async def insert_data(project, creds, dataset_name, table_name, rows):
    with aiohttp.ClientSession() as session:
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

    task = fire(insert_data, project, creds, dataset_name, table_name, rows)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(task)

    pending = asyncio.Task.all_tasks()
    loop.run_until_complete(asyncio.gather(*pending))
