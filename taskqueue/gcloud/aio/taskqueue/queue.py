"""
An asynchronous push queue for Google Appengine Task Queues
"""
import logging
from typing import Any
from typing import Dict
from typing import Optional

import aiohttp
import backoff
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module


API_ROOT = 'https://cloudtasks.googleapis.com'
LOCATION = 'us-central1'
SCOPES = [
    'https://www.googleapis.com/auth/cloud-tasks',
]

log = logging.getLogger(__name__)


class PushQueue:
    def __init__(self, project: str, taskqueue: str,
                 service_file: Optional[str] = None, location: str = LOCATION,
                 session: Optional[aiohttp.ClientSession] = None,
                 token: Optional[Token] = None) -> None:
        self.base_api_root = f'{API_ROOT}/v2beta3'
        self.api_root = (f'{self.base_api_root}/projects/{project}/'
                         f'locations/{location}/queues/{taskqueue}')
        self.session = session
        self.token = token or Token(service_file=service_file, scopes=SCOPES,
                                    session=self.session)

    async def headers(self) -> Dict[str, str]:
        token = await self.token.get()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)  # type: ignore
    async def _request(self, method: str, url: str,
                       session: Optional[aiohttp.ClientSession] = None,
                       **kwargs: Any) -> Any:
        if not self.session:
            self.session = aiohttp.ClientSession(conn_timeout=10,
                                                 read_timeout=10)
        s = session or self.session
        headers = await self.headers()

        resp = await s.request(method, url, headers=headers, **kwargs)
        # N.B. This is awaited early to give an extra helping hand to various
        # debug tools, which tend to be able to capture assigned variables but
        # not un-awaited data.
        data = await resp.json()
        resp.raise_for_status()
        return data

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/create
    async def create(self, task: Dict[str, Any],
                     session: Optional[aiohttp.ClientSession] = None) -> Any:
        url = f'{self.api_root}/tasks'
        body = {
            'task': task,
            'responseView': 'FULL',
        }

        return await self._request('POST', url, json=body, session=session)

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/delete
    async def delete(self, tname: str,
                     session: Optional[aiohttp.ClientSession] = None) -> Any:
        url = f'{self.base_api_root}/{tname}'

        return await self._request('DELETE', url, session=session)

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/get
    async def get(self, tname: str, full: bool = False,
                  session: Optional[aiohttp.ClientSession] = None) -> Any:
        url = f'{self.base_api_root}/{tname}'
        params = {
            'responseView': 'FULL' if full else 'BASIC',
        }

        return await self._request('GET', url, params=params, session=session)

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/list
    async def list(self, full: bool = False, page_size: int = 1000,
                   page_token: str = '',
                   session: Optional[aiohttp.ClientSession] = None) -> Any:
        url = f'{self.api_root}/tasks'
        params = {
            'responseView': 'FULL' if full else 'BASIC',
            'pageSize': page_size,
            'pageToken': page_token,
        }

        return await self._request('GET', url, params=params, session=session)

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/run
    async def run(self, tname: str, full: bool = False,
                  session: Optional[aiohttp.ClientSession] = None) -> Any:
        url = f'{self.base_api_root}/{tname}:run'
        body = {
            'responseView': 'FULL' if full else 'BASIC',
        }

        return await self._request('POST', url, json=body, session=session)
