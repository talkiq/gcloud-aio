import json
import time
import uuid

import gcloud.aio.pubsub as pubsub
import pytest


@pytest.mark.asyncio
async def test_pubsub_lifecycle(project, subscription, topic):
    subscriber = pubsub.Client(project)

    # create an empty topic
    topic_ = subscriber.topic(f'{topic}-{uuid.uuid4().hex}')
    topic_.create_if_missing()

    # create an empty subscription
    subscription_ = topic_.subscription(f'{subscription}-{uuid.uuid4().hex}')
    subscription_.create_if_missing()
    subscription_.pull(return_immediately=True, max_messages=1_000_000)

    # push four jobs
    num_jobs = 4

    uuids = [uuid.uuid4().hex for _ in range(num_jobs)]
    for i in range(num_jobs):
        data = {'this': {'is': {'a': {'test': uuids[i]}}}}
        topic_.publish(json.dumps(data).encode('utf-8'))

    # try to avoid some flakiness
    time.sleep(1)

    num_processed = 0
    async for job_id, message in subscription_.poll():
        job = json.loads(message.data.decode('utf-8'))
        assert job['this']['is']['a']['test'] in uuids

        await subscription_.acknowledge([job_id])
        num_processed += 1

        if num_processed == num_jobs:
            break

    subscription_.delete()
    topic_.delete()
