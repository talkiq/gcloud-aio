# pylint: disable=redefined-outer-name
import os

import pytest
from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.taskqueue import PushQueue

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session


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
    return 'dialpad-oss'


@pytest.fixture(scope='module')  # type: ignore
def push_queue_name() -> str:
    return 'public-test-push'


@pytest.fixture(scope='module')  # type: ignore
def push_queue_location() -> str:
    return 'us-west2'


@pytest.fixture(scope='function')  # type: ignore
async def session() -> str:
    async with Session() as session:
        yield session


@pytest.fixture(scope='function')  # type: ignore
async def push_queue_context(project, creds, push_queue_name,
                             push_queue_location, session):
    # main purpose is to be do proper teardown of tasks created by tests
    tq = PushQueue(project, push_queue_name, service_file=creds,
                   location=push_queue_location, session=session)
    context = {'queue': tq, 'tasks_to_cleanup': []}
    yield context

    # try deleting the task created by tests
    for task in context['tasks_to_cleanup']:
        await tq.delete(task['name'])
