# pylint: disable=too-many-locals
import asyncio
import os

import aiohttp
from gcloud.aio.taskqueue import encode
from gcloud.aio.taskqueue import TaskManager


async def do_task_lifecycle(mocker, project, creds, task_queue):
    def get_mock_coro(return_value):
        @asyncio.coroutine
        def mock_coro(*args, **kwargs):
            # pylint: disable=unused-argument
            return return_value

        return mocker.Mock(wraps=mock_coro)

    with aiohttp.ClientSession() as session:
        tasks = [
            '{"test_idx": 1}',
            '{"test_idx": 2}',
            '{"test_idx": 3}',
            '{"test_idx": 4}',
            'not-a-json-task',
        ]

        worker = get_mock_coro('ok')

        tm = TaskManager(project, creds, task_queue, worker,
                         batch_size=len(tasks), session=session)

        # DRAIN
        await tm.tq.drain()

        # START
        tm.start()

        # INSERT
        for task in tasks:
            await tm.tq.insert(encode(task))

        await asyncio.sleep(3)
        tm.stop()

        assert worker.mock_calls == [mocker.call(t) for t in tasks]


def test_task_lifecycle(mocker):
    project = os.environ['GCLOUD_PROJECT']
    creds = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

    task_queue = 'test-pull'

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        do_task_lifecycle(mocker, project, creds, task_queue))
