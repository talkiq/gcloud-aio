import asyncio
import os
import uuid

import aiohttp
from gcloud.aio.taskqueue import deserialize_task
from gcloud.aio.taskqueue import TaskQueue


async def do_task_lifecycle(project, creds, task_queue):
    with aiohttp.ClientSession() as session:
        tq = TaskQueue(project, creds, task_queue, session=session)

        payload = {'this': {'is': {'a': {'test': uuid.uuid4().hex}}}}
        tag = 'smoke-test'

        # INSERT
        result = await tq.insert_task(payload, tag=tag)
        assert result

        # STATS
        stats = await tq.get_stats()
        assert stats['id'].endswith(task_queue)
        assert stats['stats']['totalTasks'] > 0

        # LEASE
        tasks = await tq.lease_task(lease_seconds=10, num_tasks=1)
        assert len(tasks) == 1

        payload = deserialize_task(tasks[0])
        assert payload

        # RENEW
        task_id = tasks[0]['id']
        result = await tq.renew_task(task_id, lease_seconds=10)
        assert result

        # DELETE
        result = await tq.delete_task(task_id)
        assert result


def test_task_lifecycle():
    project = os.environ['GCLOUD_PROJECT']
    creds = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

    task_queue = 'test-pull'

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        do_task_lifecycle(project, creds, task_queue))
