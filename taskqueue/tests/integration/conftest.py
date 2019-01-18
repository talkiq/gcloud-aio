import os

import aiohttp
import pytest
from gcloud.aio.taskqueue import PullQueue
from gcloud.aio.taskqueue import PushQueue


PROJECT = 'voiceai-staging'
CREDS = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
PULL_QUEUE_NAME = 'public-test'
PUSH_QUEUE_NAME = 'public-test-push'


@pytest.fixture(scope='module')  # type: ignore
def creds() -> str:
    # TODO: bundle public creds into this repo
    return CREDS


@pytest.fixture(scope='module')  # type: ignore
def project() -> str:
    return PROJECT


@pytest.fixture(scope='module')  # type: ignore
def pull_queue_name() -> str:
    return PULL_QUEUE_NAME


@pytest.yield_fixture(scope='function')  # type: ignore
async def pull_queue_context():
    # main purpose is to be do proper teardown of tasks created by tests
    async with aiohttp.ClientSession() as session:
        tq = PullQueue(PROJECT, CREDS, PULL_QUEUE_NAME, session=session)
        context = {'queue': tq, 'tasks_to_cleanup': []}
        yield context

        # try deleting the task created by tests
        for task in context['tasks_to_cleanup']:
            await tq.delete(task['name'])


@pytest.yield_fixture(scope='function')  # type: ignore
async def push_queue_context():
    # main purpose is to be do proper teardown of tasks created by tests
    async with aiohttp.ClientSession() as session:
        tq = PushQueue(PROJECT, CREDS, PUSH_QUEUE_NAME, session=session)
        context = {'queue': tq, 'tasks_to_cleanup': []}
        yield context

        # try deleting the task created by tests
        for task in context['tasks_to_cleanup']:
            await tq.delete(task['name'])
