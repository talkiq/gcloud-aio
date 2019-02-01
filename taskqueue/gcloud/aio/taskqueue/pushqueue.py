"""
An asynchronous push queue for Google Appengine Task Queues
"""
from typing import Any
from typing import Dict
from typing import Optional

import aiohttp
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module
from gcloud.aio.taskqueue.basequeue import API_ROOT
from gcloud.aio.taskqueue.basequeue import BaseQueue
from gcloud.aio.taskqueue.basequeue import LOCATION


class PushQueue(BaseQueue):  # type: ignore
    base_api_root = f'{API_ROOT}/v2beta3'

    def __init__(self, project: str, taskqueue: str,
                 service_file: Optional[str] = None, location: str = LOCATION,
                 session: Optional[aiohttp.ClientSession] = None,
                 token: Optional[Token] = None) -> None:
        super().__init__(self.base_api_root, project, taskqueue,
                         service_file=service_file, location=location,
                         session=session, token=token)

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
