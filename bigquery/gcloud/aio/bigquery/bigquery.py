import json
import logging
import os
from enum import Enum
from typing import Any
from typing import AnyStr
from typing import IO

from gcloud.aio.auth import AioSession  # pylint: disable=no-name-in-module
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session  # type: ignore[assignment]


SCOPES = [
    'https://www.googleapis.com/auth/bigquery.insertdata',
    'https://www.googleapis.com/auth/bigquery',
]

log = logging.getLogger(__name__)


def init_api_root(api_root: str | None) -> tuple[bool, str]:
    if api_root:
        return True, api_root

    host = os.environ.get('BIGQUERY_EMULATOR_HOST')
    if host:
        return True, f'http://{host}/bigquery/v2'

    return False, 'https://www.googleapis.com/bigquery/v2'


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
    _project: str | None
    _api_root: str
    _api_is_dev: bool

    def __init__(
            self, project: str | None = None,
            service_file: str | IO[AnyStr] | None = None,
            session: Session | None = None, token: Token | None = None,
            api_root: str | None = None,
    ) -> None:
        self._api_is_dev, self._api_root = init_api_root(api_root)
        self.session = AioSession(session)
        self.token = token or Token(
            service_file=service_file, scopes=SCOPES,
            session=self.session.session,  # type: ignore[arg-type]
        )

        self._project = project
        if self._api_is_dev and not project:
            self._project = (
                os.environ.get('BIGQUERY_PROJECT_ID')
                or os.environ.get('GOOGLE_CLOUD_PROJECT')
                or 'dev'
            )

    async def project(self) -> str:
        if self._project:
            return self._project

        self._project = await self.token.get_project()
        if self._project:
            return self._project

        raise Exception('could not determine project, please set it manually')

    async def headers(self) -> dict[str, str]:
        if self._api_is_dev:
            return {}

        token = await self.token.get()
        return {
            'Authorization': f'Bearer {token}',
        }

    async def _post_json(
            self, url: str, body: dict[str, Any], session: Session | None,
            timeout: int, params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = json.dumps(body).encode('utf-8')

        headers = await self.headers()
        headers.update({
            'Content-Length': str(len(payload)),
            'Content-Type': 'application/json',
        })

        s = AioSession(session) if session else self.session
        resp = await s.post(url, data=payload, headers=headers,
                            timeout=timeout, params=params or {})
        data: dict[str, Any] = await resp.json()
        return data

    async def _get_url(
            self, url: str, session: Session | None, timeout: int,
            params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = await self.headers()

        s = AioSession(session) if session else self.session
        resp = await s.get(url, headers=headers, timeout=timeout,
                           params=params or {})
        data: dict[str, Any] = await resp.json()
        return data

    async def _delete(
        self, url: str, session: Session | None, timeout: int,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = await self.headers()

        s = AioSession(session) if session else self.session
        resp = await s.delete(url, headers=headers, timeout=timeout,
                              params=params or {})
        data: dict[str, Any] = await resp.json()
        return data

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> 'BigqueryBase':
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
