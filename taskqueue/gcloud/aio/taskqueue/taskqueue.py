import warnings

from .pullqueue import LOCATION
from .pullqueue import PullQueue


def TaskQueue(project, service_file, taskqueue, location=LOCATION,
              session=None, token=None):
    warnings.warn('The TaskQueue class has been renamed to PullQueue and will '
                  'be removed in the next major release.', DeprecationWarning)
    return PullQueue(project, service_file, taskqueue, location=location,
                     session=session, token=token)

# only used for pull queue, while the support lasts.
ALPHA_API_ROOT = 'https://cloudtasks.googleapis.com/v2beta2'

API_ROOT = 'https://cloudtasks.googleapis.com/v2beta3'
LOCATION = 'us-central1'
SCOPES = [
    'https://www.googleapis.com/auth/cloud-tasks',
]

log = logging.getLogger(__name__)


class BaseQueue:
    def __init__(self, api_root, project, service_file, session=None, token=None):
        self.api_root = api_root
        self.session = session
        self.token = token or Token(project, service_file, scopes=SCOPES,
                                    session=self.session)

    async def headers(self):
        token = await self.token.get()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    async def _request(self, method, url, session=None, **kwargs):
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


class PullQueue(BaseQueue):
    def __init__(self, project, service_file, taskqueue, location=LOCATION,
                 session=None, token=None):
        api_root = (f'{ALPHA_API_ROOT}/projects/{project}/'
                         f'locations/{location}/queues/{taskqueue}')
        super().__init__(api_root, project, service_file, session, token)

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/acknowledge
    async def ack(self, task, session=None):
        url = f'{ALPHA_API_ROOT}/{task["name"]}:acknowledge'
        body = {
            'scheduleTime': task['scheduleTime'],
        }

        return await self._request('POST', url, json=body, session=session)

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/cancelLease
    async def cancel(self, task, session=None):
        url = f'{ALPHA_API_ROOT}/{task["name"]}:cancelLease'
        body = {
            'scheduleTime': task['scheduleTime'],
            'responseView': 'BASIC',
        }

        return await self._request('POST', url, json=body, session=session)

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/delete
    async def delete(self, tname, session=None):
        url = f'{ALPHA_API_ROOT}/{tname}'

        return await self._request('DELETE', url, session=session)

    async def drain(self):
        resp = await self.lease(num_tasks=1000)
        while resp:
            await asyncio.wait([self.delete(t['name']) for t in resp['tasks']])
            resp = await self.lease(num_tasks=1000)

    # https://cloud.google.com/cloud-tasks/docs/reference/rest/v2beta2/projects.locations.queues.tasks/get
    async def get(self, tname, full=False, session=None):
        url = f'{ALPHA_API_ROOT}/{tname}'
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
        url = f'{ALPHA_API_ROOT}/{task["name"]}:renewLease'
        body = {
            'scheduleTime': task['scheduleTime'],
            'leaseDuration': f'{lease_seconds}s',
            'responseView': 'FULL',
        }

        return await self._request('POST', url, json=body, session=session)


class PushQueue(BaseQueue):
    def __init__(self, project, service_file, taskqueue, location=LOCATION,
                 session=None, token=None):
        api_root = (f'{API_ROOT}/projects/{project}/'
                         f'locations/{location}/queues/{taskqueue}')
        super().__init__(api_root, project, service_file, session, token)

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
        url = f'{API_ROOT}/{tname}'

        return await self._request('DELETE', url, session=session)

    # https://cloud.google.com/tasks/docs/reference/rest/v2beta3/projects.locations.queues.tasks/get
    async def get(self, tname, full=False, session=None):
        url = f'{API_ROOT}/{tname}'
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
        url = f'{API_ROOT}/{tname}:run'
        body = {
            'responseView': 'FULL' if full else 'BASIC',
        }

        return await self._request('POST', url, json=body, session=session)
