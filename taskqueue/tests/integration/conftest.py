# pylint: disable=redefined-outer-name
import os

import aiohttp
import pytest
from gcloud.aio.taskqueue import PullQueue
from gcloud.aio.taskqueue import PushQueue


@pytest.fixture(scope='module')  # type: ignore
def creds() -> str:
    # TODO: bundle public creds into this repo
    return os.environ['GOOGLE_APPLICATION_CREDENTIALS']


@pytest.fixture(scope='module')  # type: ignore
def project() -> str:
    return 'voiceai-staging'


@pytest.fixture(scope='module')  # type: ignore
def pull_queue_name() -> str:
    return 'public-test'


@pytest.fixture(scope='module')  # type: ignore
def push_queue_name() -> str:
    return 'public-test-push'


@pytest.yield_fixture(scope='function')  # type: ignore
async def pull_queue_context(project, creds, pull_queue_name):
    # main purpose is to be do proper teardown of tasks created by tests
    async with aiohttp.ClientSession() as session:
        tq = PullQueue(project, pull_queue_name, service_file=creds,
                       session=session)
        context = {'queue': tq, 'tasks_to_cleanup': []}
        yield context

        # try deleting the task created by tests
        for task in context['tasks_to_cleanup']:
            await tq.delete(task['name'])


@pytest.yield_fixture(scope='function')  # type: ignore
async def push_queue_context(project, creds, push_queue_name):
    # main purpose is to be do proper teardown of tasks created by tests
    async with aiohttp.ClientSession() as session:
        tq = PushQueue(project, push_queue_name, service_file=creds,
                       session=session)
        context = {'queue': tq, 'tasks_to_cleanup': []}
        yield context

        # try deleting the task created by tests
        for task in context['tasks_to_cleanup']:
            await tq.delete(task['name'])
