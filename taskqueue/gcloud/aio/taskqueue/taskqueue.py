"""
An asynchronous queue for Google Appengine Task Queues
"""
import asyncio
import logging

import aiohttp
from gcloud.aio.auth import Token
from gcloud.aio.taskqueue.utils import raise_for_status
from gcloud.aio.taskqueue.utils import retry


API_ROOT = 'https://cloudtasks.googleapis.com/v2beta2'
LOCATION = 'us-central1'
SCOPES = [
    'https://www.googleapis.com/auth/cloud-tasks',
]

aiohttp.ClientResponse.raise_for_status = raise_for_status

log = logging.getLogger(__name__)


class TaskQueue:
    def __init__(self, project, service_file, taskqueue, location=LOCATION,
                 session=None, token=None):
        # pylint: disable=too-many-arguments
        self.session = session or aiohttp.ClientSession(conn_timeout=10,
                                                        read_timeout=10)

        self.api_root = '{}/projects/{}/locations/{}/queues/{}'.format(
            API_ROOT, project, location, taskqueue)

        self.token = token or Token(project, service_file, scopes=SCOPES,
                                    session=self.session)

    async def headers(self):
        return {
            'Authorization': 'Bearer {}'.format(await self.token.get()),
            'Content-Type': 'application/json',
        }

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/acknowledge
    async def ack(self, task, session=None):
        url = '{}/{}:acknowledge'.format(API_ROOT, task['name'])
        body = {
            'scheduleTime': task['scheduleTime'],
        }

        s = session or self.session
        resp = await retry(s.post(url, headers=await self.headers(),
                                  json=body))
        resp.raise_for_status()
        return await resp.json()

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/cancelLease
    async def cancel(self, task, session=None):
        url = '{}/{}:cancelLease'.format(API_ROOT, task['name'])
        body = {
            'scheduleTime': task['scheduleTime'],
            'responseView': 'BASIC',
        }

        s = session or self.session
        resp = await retry(s.post(url, headers=await self.headers(),
                                  json=body))
        resp.raise_for_status()
        return await resp.json()

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/delete
    async def delete(self, tname, session=None):
        url = '{}/{}'.format(API_ROOT, tname)

        s = session or self.session
        resp = await retry(s.delete(url, headers=await self.headers()))
        resp.raise_for_status()
        return await resp.json()

    async def drain(self):
        resp = await self.lease(num_tasks=1000)
        while resp:
            await asyncio.wait([self.delete(t['name']) for t in resp['tasks']])
            resp = await self.lease(num_tasks=1000)

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/get
    async def get(self, tname, full=False, session=None):
        url = '{}/{}'.format(API_ROOT, tname)
        params = {
            'responseView': 'FULL' if full else 'BASIC',
        }

        s = session or self.session
        resp = await retry(s.get(url, headers=await self.headers(),
                                 params=params))
        resp.raise_for_status()
        return await resp.json()

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/create
    async def insert(self, payload, tag=None, session=None):
        url = '{}/tasks'.format(self.api_root)
        body = {
            'task': {
                'pullMessage': {
                    'payload': payload,
                    'tag': tag,
                },
            },
            'responseView': 'FULL',
        }

        s = session or self.session
        resp = await retry(s.post(url, headers=await self.headers(),
                                  json=body))
        resp.raise_for_status()
        return await resp.json()

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/lease
    async def lease(self, num_tasks=1, lease_seconds=60, task_filter=None,
                    session=None):
        url = '{}/tasks:lease'.format(self.api_root)
        body = {
            'maxTasks': min(num_tasks, 1000),
            'leaseDuration': '{}s'.format(lease_seconds),
            'responseView': 'FULL',
        }
        if task_filter:
            body['filter'] = task_filter

        s = session or self.session
        resp = await retry(s.post(url, headers=await self.headers(),
                                  json=body))
        resp.raise_for_status()
        return await resp.json()

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/list
    async def list(self, full=False, page_size=1000, page_token='',
                   session=None):
        url = '{}/tasks'.format(self.api_root)
        params = {
            'responseView': 'FULL' if full else 'BASIC',
            'pageSize': page_size,
            'pageToken': page_token,
        }

        s = session or self.session
        resp = await retry(s.get(url, headers=await self.headers(),
                                 params=params))
        resp.raise_for_status()
        return await resp.json()

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/renewLease
    async def renew(self, task, lease_seconds=60, session=None):
        url = '{}/{}:renewLease'.format(API_ROOT, task['name'])
        body = {
            'scheduleTime': task['scheduleTime'],
            'leaseDuration': '{}s'.format(lease_seconds),
            'responseView': 'FULL',
        }

        s = session or self.session
        resp = await retry(s.post(url, headers=await self.headers(),
                                  json=body))
        resp.raise_for_status()
        return await resp.json()
