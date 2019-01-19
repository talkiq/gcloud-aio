"""
An asynchronous pull queue for Google Appengine Task Queues
"""
import asyncio

from gcloud.aio.taskqueue.basequeue import BaseQueue
from gcloud.aio.taskqueue.basequeue import LOCATION


class PullQueue(BaseQueue):
    def __init__(self, project, service_file, taskqueue, location=LOCATION,
                 session=None, token=None):
        api_version = 'v2beta2'  # only used for pull queue, while the support lasts
        super().__init__(api_version, project, service_file,
                         taskqueue, location, session, token)

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/acknowledge
    async def ack(self, task, session=None):
        url = f'{self.base_api_root}/{task["name"]}:acknowledge'
        body = {
            'scheduleTime': task['scheduleTime'],
        }

        return await self._request('POST', url, json=body, session=session)

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/cancelLease
    async def cancel(self, task, session=None):
        url = f'{self.base_api_root}/{task["name"]}:cancelLease'
        body = {
            'scheduleTime': task['scheduleTime'],
            'responseView': 'BASIC',
        }

        return await self._request('POST', url, json=body, session=session)

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/delete
    async def delete(self, tname, session=None):
        url = f'{self.base_api_root}/{tname}'

        return await self._request('DELETE', url, session=session)

    async def drain(self):
        resp = await self.lease(num_tasks=1000)
        while resp:
            await asyncio.wait([self.delete(t['name']) for t in resp['tasks']])
            resp = await self.lease(num_tasks=1000)

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/get
    async def get(self, tname, full=False, session=None):
        url = f'{self.base_api_root}/{tname}'
        params = {
            'responseView': 'FULL' if full else 'BASIC',
        }

        return await self._request('GET', url, params=params, session=session)

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/create
    async def insert(self, payload, tag=None, session=None):
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
    async def lease(self, num_tasks=1, lease_seconds=60, task_filter=None,
                    session=None):
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
    async def list(self, full=False, page_size=1000, page_token='',
                   session=None):
        url = f'{self.api_root}/tasks'
        params = {
            'responseView': 'FULL' if full else 'BASIC',
            'pageSize': page_size,
            'pageToken': page_token,
        }

        return await self._request('GET', url, params=params, session=session)

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/renewLease
    async def renew(self, task, lease_seconds=60, session=None):
        url = f'{self.base_api_root}/{task["name"]}:renewLease'
        body = {
            'scheduleTime': task['scheduleTime'],
            'leaseDuration': f'{lease_seconds}s',
            'responseView': 'FULL',
        }

        return await self._request('POST', url, json=body, session=session)
