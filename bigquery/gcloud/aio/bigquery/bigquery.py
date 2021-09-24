import io
import json
import os
from enum import Enum
from typing import Any
from typing import Dict
from typing import Optional
from typing import Union

from gcloud.aio.auth import AioSession  # pylint: disable=no-name-in-module
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session  # type: ignore[no-redef]


API_ROOT = 'https://www.googleapis.com/bigquery/v2'
SCOPES = [
    'https://www.googleapis.com/auth/bigquery.insertdata',
    'https://www.googleapis.com/auth/bigquery',
]

BIGQUERY_EMULATOR_HOST = os.environ.get('BIGQUERY_EMULATOR_HOST')
if BIGQUERY_EMULATOR_HOST:
    API_ROOT = f'http://{BIGQUERY_EMULATOR_HOST}/bigquery/v2'


class SourceFormat(Enum):
    AVRO = 'AVRO'
    CSV = 'CSV'
    DATASTORE_BACKUP = 'DATASTORE_BACKUP'
    NEWLINE_DELIMITED_JSON = 'NEWLINE_DELIMITED_JSON'
    ORC = 'ORC'
    PARQUET = 'PARQUET'


class Disposition(Enum):
    WRITE_APPEND = 'WRITE_APPEND'
    WRITE_EMPTY = 'WRITE_EMPTY'
    WRITE_TRUNCATE = 'WRITE_TRUNCATE'


class SchemaUpdateOption(Enum):
    ALLOW_FIELD_ADDITION = 'ALLOW_FIELD_ADDITION'
    ALLOW_FIELD_RELAXATION = 'ALLOW_FIELD_RELAXATION'


class BigqueryBase:
    def __init__(self,
                 project: Optional[str] = None,
                 service_file: Optional[Union[str, io.IOBase]] = None,
                 session: Optional[Session] = None,
                 token: Optional[Token] = None) -> None:
        self._project = project
        self.session = AioSession(session)
        self.token = token or Token(service_file=service_file, scopes=SCOPES,
                                    session=self.session.session)

    async def project(self) -> str:
        if self._project:
            return self._project

        if BIGQUERY_EMULATOR_HOST:
            self._project = str(os.environ.get('BIGQUERY_PROJECT_ID', 'dev'))
            return self._project

        self._project = await self.token.get_project()
        if self._project:
            return self._project

        raise Exception('could not determine project, please set it manually')

    async def headers(self) -> Dict[str, str]:
        if BIGQUERY_EMULATOR_HOST:
            return {}

        token = await self.token.get()
        return {
            'Authorization': f'Bearer {token}',
        }

    async def _post_json(
            self, url: str, body: Dict[str, Any], session: Optional[Session],
            timeout: int) -> Dict[str, Any]:
        payload = json.dumps(body).encode('utf-8')

        headers = await self.headers()
        headers.update({
            'Content-Length': str(len(payload)),
            'Content-Type': 'application/json',
        })

        s = AioSession(session) if session else self.session
        resp = await s.post(url, data=payload, headers=headers, params=None,
                            timeout=timeout)
        data: Dict[str, Any] = await resp.json()
        return data

    async def _get_url(
            self, url: str, session: Optional[Session],
            timeout: int,
            params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        headers = await self.headers()

        s = AioSession(session) if session else self.session
        resp = await s.get(url, headers=headers, timeout=timeout,
                           params=params or {})
        data: Dict[str, Any] = await resp.json()
        return data

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> 'BigqueryBase':
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
