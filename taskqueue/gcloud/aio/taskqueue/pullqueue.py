"""
An asynchronous pull queue for Google Appengine Task Queues
"""
import asyncio
from typing import Any
from typing import Dict
from typing import Optional

import aiohttp
from gcloud.aio.auth import Token  # pylint: disable=no-name-in-module
from gcloud.aio.taskqueue.basequeue import API_ROOT
from gcloud.aio.taskqueue.basequeue import BaseQueue
from gcloud.aio.taskqueue.basequeue import LOCATION


class PullQueue(BaseQueue):  # type: ignore
    # 'v2beta2' is only used for pull queue, while the support lasts
    base_api_root = f'{API_ROOT}/v2beta2'

    def __init__(self, project: str, taskqueue: str,
                 service_file: Optional[str] = None, location: str = LOCATION,
                 session: Optional[aiohttp.ClientSession] = None,
                 token: Optional[Token] = None) -> None:
        super().__init__(self.base_api_root, project, taskqueue,
                         service_file=service_file, location=location,
                         session=session, token=token)

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/acknowledge
    async def ack(self, task: Dict[str, Any],
                  session: Optional[aiohttp.ClientSession] = None) -> Any:
        url = f'{self.base_api_root}/{task["name"]}:acknowledge'
        body = {
            'scheduleTime': task['scheduleTime'],
        }

        return await self._request('POST', url, json=body, session=session)

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/cancelLease
    async def cancel(self, task: Dict[str, Any],
                     session: Optional[aiohttp.ClientSession] = None) -> Any:
        url = f'{self.base_api_root}/{task["name"]}:cancelLease'
        body = {
            'scheduleTime': task['scheduleTime'],
            'responseView': 'BASIC',
        }

        return await self._request('POST', url, json=body, session=session)

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/delete
    async def delete(self, tname: str,
                     session: Optional[aiohttp.ClientSession] = None) -> Any:
        url = f'{self.base_api_root}/{tname}'

        return await self._request('DELETE', url, session=session)

    async def drain(self) -> None:
        resp = await self.lease(num_tasks=1000)
        while resp:
            await asyncio.wait([self.delete(t['name']) for t in resp['tasks']])
            resp = await self.lease(num_tasks=1000)

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/get
    async def get(self, tname: str, full: bool = False,
                  session: Optional[aiohttp.ClientSession] = None) -> Any:
        url = f'{self.base_api_root}/{tname}'
        params = {
            'responseView': 'FULL' if full else 'BASIC',
        }

        return await self._request('GET', url, params=params, session=session)

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/create
    async def insert(self, payload: str, tag: Optional[str] = None,
                     session: Optional[aiohttp.ClientSession] = None) -> Any:
        url = f'{self.api_root}/tasks'
        body = {
            'task': {
                'pullMessage': {
                    'payload': payload,
                    'tag': tag,
                },
            },
            'responseView': 'FULL',
        }

        return await self._request('POST', url, json=body, session=session)

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/lease
    async def lease(self, num_tasks: int = 1, lease_seconds: int = 60,
                    task_filter: Optional[str] = None,
                    session: Optional[aiohttp.ClientSession] = None) -> Any:
        url = f'{self.api_root}/tasks:lease'
        body = {
            'maxTasks': min(num_tasks, 1000),
            'leaseDuration': f'{lease_seconds}s',
            'responseView': 'FULL',
        }
        if task_filter:
            body['filter'] = task_filter

        return await self._request('POST', url, json=body, session=session)

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/list
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

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/renewLease
    async def renew(self, task: Dict[str, Any], lease_seconds: int = 60,
                    session: Optional[aiohttp.ClientSession] = None) -> Any:
        url = f'{self.base_api_root}/{task["name"]}:renewLease'
        body = {
            'scheduleTime': task['scheduleTime'],
            'leaseDuration': f'{lease_seconds}s',
            'responseView': 'FULL',
        }

        return await self._request('POST', url, json=body, session=session)
