# pylint: disable=redefined-outer-name
import os

import aiohttp
import pytest
from gcloud.aio.taskqueue import PushQueue


def pytest_configure(config):
    config.addinivalue_line(
        'markers', 'slow: marks tests as slow (deselect with `-m "not slow"`)'
    )


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


@pytest.fixture(scope='function')  # type: ignore
async def session() -> str:
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture(scope='function')  # type: ignore
async def tm_session() -> str:
    connector = aiohttp.TCPConnector(enable_cleanup_closed=True,
                                     force_close=True, limit_per_host=1)
    timeout = aiohttp.ClientTimeout(connect=10, total=10)
    async with aiohttp.ClientSession(connector=connector,
                                     timeout=timeout) as session:
        yield session


@pytest.fixture(scope='function')  # type: ignore
async def push_queue_context(project, creds, push_queue_name, session):
    # main purpose is to be do proper teardown of tasks created by tests
    tq = PushQueue(project, push_queue_name, service_file=creds,
                   session=session)
    context = {'queue': tq, 'tasks_to_cleanup': []}
    yield context

    # try deleting the task created by tests
    for task in context['tasks_to_cleanup']:
        await tq.delete(task['name'])
