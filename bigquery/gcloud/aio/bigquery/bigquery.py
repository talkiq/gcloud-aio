import functools
import logging
import uuid
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import aiohttp
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module
try:
    import ujson as json
except ModuleNotFoundError:
    import json  # type: ignore


API_ROOT = 'https://www.googleapis.com/bigquery/v2'
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


def make_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{
        'insertId': new_insert_id(),
        'json': row
    } for row in rows]


class Table:
    def __init__(self, dataset_name: str, table_name: str,
                 project: Optional[str] = None,
                 service_file: Optional[str] = None,
                 session: Optional[aiohttp.ClientSession] = None,
                 token: Optional[Token] = None) -> None:
        self._project = project
        self.dataset_name = dataset_name
        self.table_name = table_name

        self.session = session
        self.token = token or Token(service_file=service_file, session=session,
                                    scopes=SCOPES)

    async def project(self) -> str:
        if self._project:
            return self._project

        self._project = self.token.get_project()
        if self._project:
            return self._project

        raise Exception('could not determine project, please set it manually')

    async def headers(self) -> Dict[str, str]:
        token = await self.token.get()
        return {
            'Authorization': f'Bearer {token}',
        }

    async def insert(self, rows: List[Dict[str, Any]],
                     skip_invalid: bool = False, ignore_unknown: bool = True,
                     session: Optional[aiohttp.ClientSession] = None):
        project = await self.project()
        url = (f'{API_ROOT}/projects/{project}/datasets/{self.dataset_name}/'
               f'tables/{self.table_name}/insertAll')

        body = make_insert_body(rows, skip_invalid=skip_invalid,
                                ignore_unknown=ignore_unknown)
        payload = json.dumps(body).encode('utf-8')

        headers = await self.headers()
        headers.update({
            'Content-Length': str(len(payload)),
            'Content-Type': 'application/json'
        })

        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        session = session or self.session
        response = await session.post(url, data=payload, headers=headers,
                                      params=None, timeout=60)
        content = await response.json()

        if 299 >= response.status >= 200 and 'insertErrors' not in content:
            return True

        log.debug('response code: %d', response.status)
        log.debug('url: %s', url)
        log.debug('body:\n%s\n', payload)

        content_blob = json.dumps(content, sort_keys=True)
        raise Exception(f'could not insert: {content_blob}')


async def stream_insert(table, rows):
    return await table.insert(make_rows(rows))


def make_stream_insert(dataset_name, table_name, project=None,
                       service_file=None, session=None):
    table = Table(dataset_name, table_name, project=project,
                  service_file=service_file, session=session)

    return functools.partial(stream_insert, table)
