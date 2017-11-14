import asyncio
import os
import uuid

import gcloud.aio.pubsub as pubsub


async def do_lifecycle(project, topic, subscription):
    subscriber = pubsub.Client(project)
    topic = subscriber.topic(topic)
    subscription = topic.subscription(subscription)

    # empty the subscription
    subscription.pull(return_immediately=True, max_messages=1_000_000)

    # push four jobs
    payloads = [
        {'this': {'is': {'a': {'test': uuid.uuid4().hex}}}},
        {'this': {'is': {'a': {'test': uuid.uuid4().hex}}}},
        {'this': {'is': {'a': {'test': uuid.uuid4().hex}}}},
        {'this': {'is': {'a': {'test': uuid.uuid4().hex}}}},
    ]
    for payload in payloads:
        topic.publish(payload)

    async for idx, (job_id, message) in enumerate(subscription.poll()):
        assert message in payloads
        await subscription.acknowledge([job_id])

        if idx == len(payloads) - 1:
            break


def test_pubsub_lifecycle():
    project = os.environ['GCLOUD_PROJECT']

    topic = 'test-topic'
    subscription = 'test-subscription'

    loop = asyncio.get_event_loop()
    loop.run_until_complete(do_lifecycle(project, topic, subscription))
