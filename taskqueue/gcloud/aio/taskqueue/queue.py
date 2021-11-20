"""
An asynchronous push queue for Google Appengine Task Queues
"""
import io
import json
import logging
import os
from typing import Any
from typing import Dict
from typing import Optional
from typing import Union

import backoff
from gcloud.aio.auth import AioSession  # pylint: disable=no-name-in-module
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session  # type: ignore[no-redef]

API_ROOT = 'https://cloudtasks.googleapis.com'
LOCATION = 'us-central1'
SCOPES = [
    'https://www.googleapis.com/auth/cloud-tasks',
]

CLOUDTASKS_EMULATOR_HOST = os.environ.get('CLOUDTASKS_EMULATOR_HOST')
if CLOUDTASKS_EMULATOR_HOST:
    API_ROOT = f'http://{CLOUDTASKS_EMULATOR_HOST}'

log = logging.getLogger(__name__)


class PushQueue:
    def __init__(self, project: str, taskqueue: str,
                 service_file: Optional[Union[str, io.IOBase]] = None,
                 location: str = LOCATION,
                 session: Optional[Session] = None,
                 token: Optional[Token] = None) -> None:
        self.base_api_root = f'{API_ROOT}/v2beta3'
        self.api_root = (f'{self.base_api_root}/projects/{project}/'
                         f'locations/{location}/queues/{taskqueue}')
        self.session = AioSession(session)
        self.token = token or Token(service_file=service_file, scopes=SCOPES,
                                    session=self.session.session)

    async def headers(self) -> Dict[str, str]:
        if CLOUDTASKS_EMULATOR_HOST:
            return {'Content-Type': 'application/json'}

        token = await self.token.get()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/create
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    async def create(self, task: Dict[str, Any],
                     session: Optional[Session] = None) -> Any:
        url = f'{self.api_root}/tasks'
        payload = json.dumps({
            'task': task,
            'responseView': 'FULL',
        }).encode('utf-8')

        headers = await self.headers()

        s = AioSession(session) if session else self.session
        resp = await s.post(url, headers=headers, data=payload)
        return await resp.json()

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/delete
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    async def delete(self, tname: str,
                     session: Optional[Session] = None) -> Any:
        url = f'{self.base_api_root}/{tname}'

        headers = await self.headers()

        s = AioSession(session) if session else self.session
        resp = await s.delete(url, headers=headers)
        return await resp.json()

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/get
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    async def get(self, tname: str, full: bool = False,
                  session: Optional[Session] = None) -> Any:
        url = f'{self.base_api_root}/{tname}'
        params = {
            'responseView': 'FULL' if full else 'BASIC',
        }

        headers = await self.headers()

        s = AioSession(session) if session else self.session
        resp = await s.get(url, headers=headers, params=params)
        return await resp.json()

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/list
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    async def list(self, full: bool = False, page_size: int = 1000,
                   page_token: str = '',
                   session: Optional[Session] = None) -> Any:
        url = f'{self.api_root}/tasks'
        params = {
            'responseView': 'FULL' if full else 'BASIC',
            'pageSize': page_size,
            'pageToken': page_token,
        }

        headers = await self.headers()

        s = AioSession(session) if session else self.session
        resp = await s.get(url, headers=headers, params=params)
        return await resp.json()

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/run
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    async def run(self, tname: str, full: bool = False,
                  session: Optional[Session] = None) -> Any:
        url = f'{self.base_api_root}/{tname}:run'
        payload = json.dumps({
            'responseView': 'FULL' if full else 'BASIC',
        }).encode('utf-8')

        headers = await self.headers()

        s = AioSession(session) if session else self.session
        resp = await s.post(url, headers=headers, data=payload)
        return await resp.json()

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> 'PushQueue':
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
