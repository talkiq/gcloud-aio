# pylint: disable=too-many-locals
import asyncio
import time

import pytest
from gcloud.aio.taskqueue import encode
from gcloud.aio.taskqueue import TaskManager


@pytest.mark.asyncio
async def test_task_lifecycle(mocker, creds, project, pull_queue_name):
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

    tm = TaskManager(project, pull_queue_name, worker, service_file=creds,
                     batch_size=len(tasks))

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


@pytest.mark.asyncio
@pytest.mark.slow
async def test_task_multiple_leases(caplog, mocker, creds, project,
                                    pull_queue_name):
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

    tm = TaskManager(project, pull_queue_name, worker, service_file=creds,
                     batch_size=len(tasks), lease_seconds=4)

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
