from datetime import datetime
from datetime import timedelta

import pytest


@pytest.mark.asyncio
async def test_task_lifecycle_in_push_queue(push_queue_context):
    tq = push_queue_context['queue']

    # Set to run in the future, giving us enough time to test all
    # functionalities before the task gets dispatched automatically.
    schedule_time = datetime.utcnow() + timedelta(days=1)

    task = {
        'scheduleTime': f'{schedule_time.isoformat("T")}Z',
        'appEngineHttpRequest': {
            'httpMethod': 'POST',
            # something that we know won't work,
            # so that 'run' task operation doesn't end up deleting the task.
            'relativeUri': '/some/test/uri',
        }
    }

    # CREATE
    created = await tq.create(task)
    assert created

    # Add created task (and the queue to delete it from) to the tasks list
    # so the teardown will clean it up regardless of what happens.
    push_queue_context['tasks_to_cleanup'].append(created)

    # GET
    assert created == await tq.get(created['name'], full=True)

    # LIST
    listed = await tq.list(full=True)
    assert listed.get('tasks')
    assert created in listed['tasks']

    # RUN
    run = await tq.run(created['name'], full=True)
    assert all(item in run.items() for item in created.items())

    # DELETE
    assert not await tq.delete(created['name'])

    # Created task has been deleted successfully, so remove it from the list to
    # avoid unnecessary delete attempt in teardown.
    push_queue_context['tasks_to_cleanup'].remove(created)
