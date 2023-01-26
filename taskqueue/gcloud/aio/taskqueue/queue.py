"""
An asynchronous push queue for Google Appengine Task Queues
"""
import json
import logging
import os
from typing import Any
from typing import AnyStr
from typing import Dict
from typing import IO
from typing import Optional
from typing import Tuple
from typing import Union

from gcloud.aio.auth import AioSession  # pylint: disable=no-name-in-module
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session  # type: ignore[assignment]

SCOPES = [
    'https://www.googleapis.com/auth/cloud-tasks',
]

log = logging.getLogger(__name__)


def init_api_root(api_root: Optional[str]) -> Tuple[bool, str]:
    if api_root:
        return True, api_root

    host = os.environ.get('CLOUDTASKS_EMULATOR_HOST')
    if host:
        return True, f'http://{host}/v2beta3'

    return False, 'https://cloudtasks.googleapis.com/v2beta3'


class PushQueue:
    _api_root: str
    _api_is_dev: bool
    _queue_path: str

    def __init__(
            self, project: str, taskqueue: str, location: str = 'us-central1',
            service_file: Optional[Union[str, IO[AnyStr]]] = None,
            session: Optional[Session] = None, token: Optional[Token] = None,
            api_root: Optional[str] = None,
    ) -> None:
        self._api_is_dev, self._api_root = init_api_root(api_root)
        self._queue_path = (
            f'projects/{project}/locations/{location}/queues/{taskqueue}'
        )

        self.session = AioSession(session)
        self.token = token or Token(
            service_file=service_file, scopes=SCOPES,
            session=self.session.session,  # type: ignore[arg-type]
        )

    async def headers(self) -> Dict[str, str]:
        if self._api_is_dev:
            return {'Content-Type': 'application/json'}

        token = await self.token.get()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

    def task_name(self, task_id: str) -> str:
        return f'{self._queue_path}/tasks/{task_id}'

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/create
    async def create(
        self, task: Dict[str, Any],
        session: Optional[Session] = None,
        timeout: int = 10,
    ) -> Any:
        url = f'{self._api_root}/{self._queue_path}/tasks'
        payload = json.dumps({
            'task': task,
            'responseView': 'FULL',
        }).encode('utf-8')

        headers = await self.headers()

        s = AioSession(session) if session else self.session
        resp = await s.post(url, headers=headers, data=payload,
                            timeout=timeout)
        return await resp.json()

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/delete
    async def delete(
        self, tname: str,
        session: Optional[Session] = None,
        timeout: int = 10,
    ) -> Any:
        url = f'{self._api_root}/{tname}'

        headers = await self.headers()

        s = AioSession(session) if session else self.session
        resp = await s.delete(url, headers=headers, timeout=timeout)
        return await resp.json()

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/get
    async def get(
        self, tname: str, full: bool = False,
        session: Optional[Session] = None,
        timeout: int = 10,
    ) -> Any:
        url = f'{self._api_root}/{tname}'
        params = {
            'responseView': 'FULL' if full else 'BASIC',
        }

        headers = await self.headers()

        s = AioSession(session) if session else self.session
        resp = await s.get(url, headers=headers, params=params,
                           timeout=timeout)
        return await resp.json()

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/list
    async def list(
        self, full: bool = False, page_size: int = 1000,
        page_token: str = '',
        session: Optional[Session] = None,
        timeout: int = 10,
    ) -> Any:
        url = f'{self._api_root}/{self._queue_path}/tasks'
        params: Dict[str, Union[int, str]] = {
            'responseView': 'FULL' if full else 'BASIC',
            'pageSize': page_size,
            'pageToken': page_token,
        }

        headers = await self.headers()

        s = AioSession(session) if session else self.session
        resp = await s.get(url, headers=headers, params=params,
                           timeout=timeout)
        return await resp.json()

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/run
    async def run(
        self, tname: str, full: bool = False,
        session: Optional[Session] = None,
        timeout: int = 10,
    ) -> Any:
        url = f'{self._api_root}/{tname}:run'
        payload = json.dumps({
            'responseView': 'FULL' if full else 'BASIC',
        }).encode('utf-8')

        headers = await self.headers()

        s = AioSession(session) if session else self.session
        resp = await s.post(url, headers=headers, data=payload,
                            timeout=timeout)
        return await resp.json()

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> 'PushQueue':
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
