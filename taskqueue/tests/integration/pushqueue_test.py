import datetime

import pytest
from gcloud.aio.taskqueue import PushQueue


@pytest.mark.asyncio
async def test_task_lifecycle_in_push_queue(
        project, creds, push_queue_name, push_queue_location
):
    # Set to run in the future, giving us enough time to test all
    # functionalities before the task gets dispatched automatically.
    schedule_time = (datetime.datetime.now(datetime.timezone.utc)
                     + datetime.timedelta(days=1))

    task = {
        'scheduleTime': f'{schedule_time.isoformat("T")}',
        'appEngineHttpRequest': {
            'httpMethod': 'POST',
            # something that we know won't work,
            # so that 'run' task operation doesn't end up deleting the task.
            'relativeUri': '/some/test/uri',
        },
    }

    async with PushQueue(
        project, push_queue_name, service_file=creds,
        location=push_queue_location,
    ) as push_queue:
        # CREATE
        created = await push_queue.create(task)
        assert created

        try:
            # GET
            assert created == await push_queue.get(created['name'], full=True)

            # LIST
            listed = await push_queue.list(full=True)
            assert listed.get('tasks')
            assert created in listed['tasks']

            # RUN
            run = await push_queue.run(created['name'], full=True)
            assert all(item in run.items() for item in created.items())
        finally:
            # DELETE
            assert not await push_queue.delete(created['name'])
