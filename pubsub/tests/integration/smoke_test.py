import json
import os
import uuid

import gcloud.aio.pubsub as pubsub
import pytest


@pytest.mark.asyncio
async def test_pubsub_lifecycle():
    project = os.environ['GCLOUD_PROJECT']

    topic_name = 'test-topic'
    subscription_name = 'test-subscription'

    subscriber = pubsub.Client(project)

    # create an empty topic
    topic = subscriber.topic(topic_name)
    topic.create_if_missing()

    # create an empty subscription
    subscription = topic.subscription(subscription_name)
    subscription.create_if_missing()
    subscription.pull(return_immediately=True, max_messages=1_000_000)

    # push four jobs
    num_jobs = 4

    uuids = [uuid.uuid4().hex for _ in range(num_jobs)]
    for i in range(num_jobs):
        data = {'this': {'is': {'a': {'test': uuids[i]}}}}
        topic.publish(json.dumps(data).encode('utf-8'))

    num_processed = 0
    async for job_id, message in subscription.poll():
        job = json.loads(message.data.decode('utf-8'))
        assert job['this']['is']['a']['test'] in uuids

        await subscription.acknowledge([job_id])
        num_processed += 1

        if num_processed == num_jobs:
            break

    subscription.delete()
    topic.delete()
