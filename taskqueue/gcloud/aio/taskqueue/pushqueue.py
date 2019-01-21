"""
An asynchronous push queue for Google Appengine Task Queues
"""
from gcloud.aio.taskqueue.basequeue import API_ROOT
from gcloud.aio.taskqueue.basequeue import BaseQueue
from gcloud.aio.taskqueue.basequeue import LOCATION


class PushQueue(BaseQueue):
    base_api_root = f'{API_ROOT}/v2beta3'

    def __init__(self, project, service_file, taskqueue, location=LOCATION,
                 session=None, token=None):
        super().__init__(self.base_api_root, project, service_file,
                         taskqueue, location, session, token)

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/create
    async def create(self, task, session=None):
        url = f'{self.api_root}/tasks'
        body = {
            'task': task,
            'responseView': 'FULL',
        }

        return await self._request('POST', url, json=body, session=session)

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/delete
    async def delete(self, tname, session=None):
        url = f'{self.base_api_root}/{tname}'

        return await self._request('DELETE', url, session=session)

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/get
    async def get(self, tname, full=False, session=None):
        url = f'{self.base_api_root}/{tname}'
        params = {
            'responseView': 'FULL' if full else 'BASIC',
        }

        return await self._request('GET', url, params=params, session=session)

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/list
    async def list(self, full=False, page_size=1000, page_token='', session=None):
        url = f'{self.api_root}/tasks'
        params = {
            'responseView': 'FULL' if full else 'BASIC',
            'pageSize': page_size,
            'pageToken': page_token,
        }

        return await self._request('GET', url, params=params, session=session)

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/run
    async def run(self, tname, full=False, session=None):
        url = f'{self.base_api_root}/{tname}:run'
        body = {
            'responseView': 'FULL' if full else 'BASIC',
        }

        return await self._request('POST', url, json=body, session=session)
