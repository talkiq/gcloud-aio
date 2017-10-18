import functools
import logging
import uuid

import ujson
from gcloud.aio.auth import Token
from gcloud.aio.core.http import post


API_ROOT = 'https://www.googleapis.com/bigquery/v2'
INSERT_TEMPLATE = 'projects/{proj}/datasets/{dataset}/tables/{table}/insertAll'
SCOPES = [
    'https://www.googleapis.com/auth/bigquery.insertdata'
]

log = logging.getLogger(__name__)


def make_insert_body(rows, skip_invalid=False, ignore_unknown=True):

    return {
        'kind': 'bigquery#tableDataInsertAllRequest',
        'skipInvalidRows': skip_invalid,
        'ignoreUnknownValues': ignore_unknown,
        'rows': rows
    }


def new_insert_id():

    return uuid.uuid4().hex


def make_rows(rows):

    bq_rows = [{
        'insertId': new_insert_id(),
        'json': row
    } for row in rows]

    return bq_rows


class Table(object):

    def __init__(self, project, service_file, dataset_name, table_name,
                 session=None, token=None):
        # pylint: disable=too-many-arguments

        self.project = project
        self.table_name = table_name
        self.dataset_name = dataset_name
        self.session = session
        self.token = token or Token(
            project,
            service_file,
            session=session,
            scopes=SCOPES
        )

    async def headers(self):

        token = await self.token.get()

        return {
            'Authorization': 'Bearer {}'.format(token)
        }

    async def insert(self, rows, skip_invalid=False, ignore_unknown=True,
                     session=None):

        session = session or self.session

        body = make_insert_body(
            rows,
            skip_invalid=skip_invalid,
            ignore_unknown=ignore_unknown
        )

        headers = await self.headers()

        url = '{}/{}'.format(
            API_ROOT,
            INSERT_TEMPLATE.format(
                proj=self.project,
                dataset=self.dataset_name,
                table=self.table_name
            )
        )

        log.info('Inserting %d rows to %s', len(rows), url)

        status, content = await post(
            url,
            payload=body,
            headers=headers
        )

        success = 299 >= status >= 200 and 'insertErrors' not in content

        if success:
            return success

        log.debug('response code: %d', status)
        log.debug('url: %s', url)
        log.debug('body:\n%s\n', body)

        raise Exception('Could not insert: {}'.format(ujson.dumps(
            content, sort_keys=True
        )))


async def stream_insert(table, rows):

    insert_rows = make_rows(rows)
    result = await table.insert(insert_rows)

    return result


def make_stream_insert(project, service_file, dataset_name, table_name,
                       session=None):

    table = Table(
        project,
        service_file,
        dataset_name,
        table_name,
        session=session
    )

    return functools.partial(stream_insert, table)


# async def smoke(project, service_file, dataset_name, table_name, rows):

#     import aiohttp

#     with aiohttp.ClientSession() as session:

#         stream_insert = make_stream_insert(
#             project,
#             service_file,
#             dataset_name,
#             table_name,
#             session=session
#         )

#         result = await stream_insert(rows)

#     print('success: {}'.format(result))


# if __name__ == "__main__":

#     import asyncio
#     import sys

#     from utils.aio import fire

#     args = sys.argv[1:]

#     if not args or args[0] != 'smoke':
#         exit(1)

#     project = 'talkiq-integration'
#     service_file = 'service-integration.json'
#     dataset_name = 'test'
#     table_name = 'test'
#     rows = [
#         {'key': uuid.uuid4().hex, 'value': uuid.uuid4().hex}
#         for i in range(3)
#     ]

#     loop = asyncio.get_event_loop()

#     task = fire(
#         smoke,
#         project,
#         service_file,
#         dataset_name,
#         table_name,
#         rows
#     )

#     loop.run_until_complete(task)

#     pending = asyncio.Task.all_tasks()
#     loop.run_until_complete(asyncio.gather(*pending))
