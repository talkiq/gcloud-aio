# pylint: disable=too-many-locals
import asyncio
import os
import time

import aiohttp
import pytest
from gcloud.aio.taskqueue import encode
from gcloud.aio.taskqueue import TaskManager


async def do_task_lifecycle(mocker, project, creds, task_queue):
    def get_mock_coro(return_value):
        @asyncio.coroutine
        def mock_coro(*args, **kwargs):
            # pylint: disable=unused-argument
            return return_value

        return mocker.Mock(wraps=mock_coro)

    tasks = [
        '{"test_idx": 1}',
        '{"test_idx": 2}',
        '{"test_idx": 3}',
        '{"test_idx": 4}',
        'not-a-json-task',
    ]

    worker = get_mock_coro('ok')

    async with aiohttp.ClientSession() as session:
        tm = TaskManager(project, creds, task_queue, worker,
                         batch_size=len(tasks), session=session)

        # DRAIN
        await tm.tq.drain()

        # START
        tm.start()

        # INSERT
        for task in tasks:
            await tm.tq.insert(
                encode(task), tag=encode('gcloud-aio-manager-test-lifecycle'))

        await asyncio.sleep(3)
        tm.stop()

    assert worker.mock_calls == [mocker.call(t) for t in tasks]


@pytest.mark.slow
async def do_task_multiple_leases(caplog, mocker, project, creds, task_queue):
    def get_mock_coro(return_value):
        @asyncio.coroutine
        def mock_coro(*args, **kwargs):
            # pylint: disable=unused-argument
            yield  # ensure all tasks are processed at once
            time.sleep(9)
            return return_value

        return mocker.Mock(wraps=mock_coro)

    tasks = [
        '{"test_idx": 1}',
        '{"test_idx": 2}',
    ]

    worker = get_mock_coro('ok')

    async with aiohttp.ClientSession() as session:
        tm = TaskManager(project, creds, task_queue, worker,
                         batch_size=len(tasks), lease_seconds=4,
                         session=session)

        # drain old tasks
        await tm.tq.drain()

        # insert new ones
        for task in tasks:
            await tm.tq.insert(
                encode(task), tag=encode('gcloud-aio-manager-test-multilease'))

        tm.start()
        await asyncio.sleep(10)
        tm.stop()

    assert worker.mock_calls == [mocker.call(t) for t in tasks]
    for record in caplog.records:
        assert record.levelname != 'ERROR'


def test_task_lifecycle(mocker):
    project = os.environ['GCLOUD_PROJECT']
    creds = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

    task_queue = 'test-pull'

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        do_task_lifecycle(mocker, project, creds, task_queue))


def test_task_multiple_leases(caplog, mocker):
    project = os.environ['GCLOUD_PROJECT']
    creds = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

    task_queue = 'test-pull'

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        do_task_multiple_leases(caplog, mocker, project, creds, task_queue))
