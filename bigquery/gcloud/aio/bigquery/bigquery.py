import io
import uuid
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import aiohttp
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module
try:
    import ujson as json
except ModuleNotFoundError:
    import json  # type: ignore


API_ROOT = 'https://www.googleapis.com/bigquery/v2'
SCOPES = [
    'https://www.googleapis.com/auth/bigquery.insertdata',
]


class Table:
    def __init__(self, dataset_name: str, table_name: str,
                 project: Optional[str] = None,
                 service_file: Optional[Union[str, io.IOBase]] = None,
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

        self._project = await self.token.get_project()
        if self._project:
            return self._project

        raise Exception('could not determine project, please set it manually')

    @staticmethod
    def _mk_unique_insert_id(row: Dict[str, Any]) -> str:
        return uuid.uuid4().hex

    @staticmethod
    def _make_insert_body(rows: List[Dict[str, Any]],
                          skip_invalid: bool,
                          ignore_unknown: bool,
                          insert_id_fn: Callable[[Dict[str, Any]], str]) -> Dict[str, Any]:
        return {
            'kind': 'bigquery#tableDataInsertAllRequest',
            'skipInvalidRows': skip_invalid,
            'ignoreUnknownValues': ignore_unknown,
            'rows': [{
                'insertId': insert_id_fn(row),
                'json': row
            } for row in rows],
        }

    async def headers(self) -> Dict[str, str]:
        token = await self.token.get()
        return {
            'Authorization': f'Bearer {token}',
        }

    async def insert(self, rows: List[Dict[str, Any]],
                     skip_invalid: bool = False, ignore_unknown: bool = True,
                     session: Optional[aiohttp.ClientSession] = None,
                     timeout: int = 60,
                     insert_id_fn: Callable[[Dict[str, Any]], str] = _mk_unique_insert_id) -> Dict[str, Any]:
        """
        Streams data into BigQuery

        By default, each row is assigned a unique insertId, this can be customized this by 
        supplying a insert_id_fn, taking a row an returning an insert id.

        The response payload will include an `insertErrors` key if a subset of
        the rows failed to get inserted.
        """
        if not rows:
            return

        project = await self.project()
        url = (f'{API_ROOT}/projects/{project}/datasets/{self.dataset_name}/'
               f'tables/{self.table_name}/insertAll')

        body = self._make_insert_body(rows, skip_invalid=skip_invalid,
                                      ignore_unknown=ignore_unknown,
                                      insert_id_fn=insert_id_fn)
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
        resp = await session.post(url, data=payload, headers=headers,
                                  params=None, timeout=timeout)
        resp.raise_for_status()
        return await resp.json()
