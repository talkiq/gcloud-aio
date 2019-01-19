# pylint: disable=too-many-locals
import json
import uuid

import pytest
from gcloud.aio.taskqueue import decode
from gcloud.aio.taskqueue import encode


@pytest.mark.asyncio
async def test_task_lifecycle_in_pull_queue(pull_queue_context):
    tq = pull_queue_context['queue']

    payload = {'this': {'is': {'a': {'test': uuid.uuid4().hex}}}}
    tag = 'smoke-test'

    # DRAIN
    await tq.drain()

    # INSERT
    inserted = await tq.insert(encode(json.dumps(payload)),
                               tag=encode(tag))
    assert inserted

    # add created task(and the queue to delete it from) to the tasks list,
    # so that regardless of what happens, the teardown will clean it up.
    pull_queue_context['tasks_to_cleanup'].append(inserted)

    # GET
    assert inserted == await tq.get(inserted['name'], full=True)

    # LIST
    listed = await tq.list(full=True)
    assert listed.get('tasks')
    assert inserted in listed['tasks']

    # LEASE
    leased = await tq.lease(num_tasks=1, lease_seconds=10,
                            task_filter=f'tag={encode(tag)}')
    assert leased.get('tasks') and len(leased['tasks']) == 1

    leased_message = leased['tasks'][0]['pullMessage']
    assert payload == json.loads(decode(leased_message['payload']))
    assert tag == decode(leased_message['tag'])

    # RENEW
    renewed = await tq.renew(leased['tasks'][0], lease_seconds=10)
    for k, v in renewed.items():
        if k == 'scheduleTime':
            assert v != leased['tasks'][0][k]
        else:
            assert v == leased['tasks'][0][k]

    # ack?
    # cancel?

    # DELETE
    assert not await tq.delete(renewed['name'])

    # inserted task has been deleted successfully,
    # so remove it from the list to avoid unnecessary delete attempt
    pull_queue_context['tasks_to_cleanup'].remove(inserted)
