(Asyncio OR Threadsafe) Python Client for Google Cloud Pub/Sub
==============================================================

    This is a shared codebase for ``gcloud-aio-pubsub`` and
    ``gcloud-rest-pubsub``

|pypi| |pythons-aio| |pythons-rest|

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-{aio,rest}-pubsub

Usage
-----

Subscriber
~~~~~~~~~~

Currently we have only implemented an asyncio version of ``SubscriberClient``
as the subscription pattern does not work with asyncio by default. The official
Google publisher returns a future which is mostly useable as-is. This patch is
a noop under ``gcloud-rest`` (ie. when not using ``asyncio``) -- in that case,
using the official library is preferred.

An HTTP-oriented version, in keeping with the other ``gcloud-aio-*`` libraries,
will likely be coming soon -- though our current approach works reasonably well
for allowing the official ``grpc`` client to be used under ``asyncio``, we
continue to see threading oddities now and again which we've not been able to
solve. As such, we do not wholeheartedly recommend using the
``SubscriberClient`` of this library in production, though a resilient enough
environment for your use-case may be possible.

Here's the rough usage pattern for subscribing:

.. code-block:: python

    from gcloud.aio.pubsub import SubscriberClient
    from google.cloud.pubsub_v1.subscriber.message import Message

    client = SubscriberClient()
    # create subscription if it doesn't already exist
    client.create_subscription('subscription_name', 'topic_name')

    async def message_callback(message: Message) -> None:
        try:
            # just an example: process the message however you need to here...
            result = handle(message)
            await upload_result(result)
        except Exception:
            message.nack()
        else:
            message.ack()

    # subscribe to the subscription, receiving a Future that acts as a keepalive
    keep_alive = client.subscribe('subscription_name', message_callback)

    # have the client run forever, pulling messages from this subscription,
    # passing them to the specified callback function, and wrapping it in an
    # asyncio task.
    client.run_forever(keep_alive)

Configuration
^^^^^^^^^^^^^

Our create_subscription method is a thing wrapper and thus supports all keyword
configuration arguments from the official pubsub client which you can find in
the `official Google documentation`_.

When subscribing to a subscription you can optionally pass in a ``FlowControl``
and/or ``Scheduler`` instance.

.. code-block:: python

    example_flow_control = FlowControl(
        max_messages=1,
        resume_threshold=0.8,
        max_request_batch_size=1,
        max_request_batch_latency=0.1,
        max_lease_duration=10,
    )

    keep_alive = client.subscribe(
        'subscription_name',
        message_callback,
        flow_control=example_flow_control
    )

Understanding how modifying ``FlowControl`` affects how your pubsub runtime
will operate can be confusing so here's a handy dandy guide!

Welcome to @TheKevJames's guide to configuring Google Pubsub Subscription
policies! Settle in, grab a drink, and stay a while.

The Subscriber is controlled by a FlowControl configuration tuple defined
`here <https://github.com/GoogleCloudPlatform/google-cloud-python/blob/de5b775811d914270df3249ac24e165964c10dd2/pubsub/google/cloud/pubsub_v1/types.py#L53-L67>`_:
that configuration object ``f`` gets used by the Subscriber in the following
ways:

Max Concurrency
_______________

The subscriber is allowed to lease new tasks whenever its currently leased
tasks ``x`` satisfy:

.. code-block:: python

    (
        (len(x) < f.resume_threshold * f.max_messages)
        and (sum(x.bytes) < f.resume_threshold * f.max_bytes)
    )

In practice, this means we should set these values with the following
restrictions:

- the maximum number of concurrently leased tasks at peak is:
  ``= (f.max_messages * f.resume_threshold) + f.max_request_batch_size``
- the maximum memory usage of our leased tasks at peak is:
  ``= (f.max_bytes * f.resume_threshold) + (f.max_request_batch_size *
  bytes_per_task)``
- these values are constrain each other, ie. we limit ourselves to the lesser
  of these values given:
  ``max_tasks * bytes_per_task <> max_memory``

Aside: it seems like OCNs on Pubsub are ~1538 bytes each

Leasing Requests
________________

When leasing new tasks, the ``Subscriber`` uses the following algorithm:

.. code-block:: python

    def lease_more_tasks():
        start = time.now()
        yield queue.Queue.get(block=True)  # always returns >=1

        for _ in range(f.max_request_batch_size - 1):
            elapsed = time.now() - start
            yield queue.Queue.get(
                block=False,
                timeout=f.max_request_batch_latency-elapsed)
            if elapsed >= f.max_request_batch_latency:
                break

In practice, this means we should set ``f.max_request_batch_size`` given the
above concurrent concerns and set ``f.max_request_batch_latency`` given
whatever latency ratio we are willing to accept.

The expected best-case time for ``Queue.get()`` off a full queue is no worse
than 0.3ms. This Queue should be filling up as fast as grpc can make requests
to Google Pubsub, which should be Fast Enough(tm) to keep it filled, given
*those* requests are batched.

Therefore, we can expect:

- avg_lease_latency: ``~= f.max_request_batch_size * 0.0003``
- worst_case_latency: ``~= f.max_request_batch_latency``

Note that leasing occurs based on ``f.resume_threshold``, so some of this
latency is concurrent with task execution.

Task Expiry
___________

Any task which has not been acked or nacked counts against the current leased
task count. Our worker thread should ensure all tasks are acked or nacked, but
the ``FlowControl`` config allows us to handle any other cases. Note that
leasing works as follows:

- When a subscriber leases a task, Google Pubsub will not re-lease that
  task until ``subscription.ack_deadline_seconds = 10`` (configurable
  per-subscription) seconds have passed.
- If a client calls ``ack()`` on a task, it is immediately removed from Google
  Pubsub.
- If a client calls ``nack()`` on a task, it immediately allows Google Pubsub
  to re-lease that task to a new client. The client drops the task from its
  memory.
- If ``f.max_lease_duration`` passes between a message being leased and acked,
  the client will send a ``nack`` (see above workflow). It will NOT drop the
  task from its memory -- eg. the ``worker(task)`` process may still be run.

Notes:

- all steps are best-effort, eg. read "a task will be deleted" as "a task will
  probably get deleted, if the distributed-system luck is with you"
- in the above workflow "Google Pubsub" refers to the server-side system, eg.
  managed by Google where the tasks are actually stored.

In practice, we should thus set ``f.max_lease_duration`` to no lower than
our 95% percentile task latency at high load. The lower this value is,
the better our throughput will be in extreme cases.

Confusion
_________

``f.max_requests`` is defined, but seems to be unused.

Publisher
~~~~~~~~~

The ``PublisherClient`` is a dead-simple alternative to the official Google
Cloud Pub/Sub publisher client. The main design goal was to eliminate all the
additional gRPC overhead implemented by the upstream client.

If migrating between this library and the official one, the main difference is
this: the ``gcloud-aio-pubsub`` publisher's ``.publish()`` method *immediately*
publishes the messages you've provided, rather than maintaining our own
publishing queue, implementing batching and flow control, etc. If you're
looking for a full-featured publishing library with all the bells and whistles
built in, you may be interested in the upstream provider. If you're looking to
manage your own batching / timeouts / retry / threads / etc, this library
should be a bit easier to work with.

Sample usage:

.. code-block:: python

    from gcloud.aio.pubsub import PubsubMessage
    from gcloud.aio.pubsub import PublisherClient

    async with aiohttp.ClientSession() as session:
        client = PublisherClient(session=session)

        topic = client.topic_path('my-gcp-project', 'my-topic-name')

        messages = [
            PubsubMessage(b'payload', attribute='value'),
            PubsubMessage(b'other payload', other_attribute='whatever',
                          more_attributes='something else'),
        ]
        response = await client.publish(topic, messages)
        # response == {'messageIds': ['1', '2']}

Emulators
^^^^^^^^^

For testing purposes, you may want to use ``gcloud-aio-pubsub`` along with a
local GCS emulator. Setting the ``$PUBSUB_EMULATOR_HOST`` environment variable
to the local address of your emulator should be enough to do the trick.

For example, using the official Google Pubsub emulator:

.. code-block:: console

    gcloud beta emulators pubsub start --host-port=0.0.0.0:8681
    export PUBSUB_EMULATOR_HOST='0.0.0.0:8681'

Any ``gcloud-aio-pubsub`` Publisher requests made with that environment
variable set will query the emulator instead of the official GCS APIs.

For easier ergonomics, you may be interested in
`messagebird/gcloud-pubsub-emulator`_.

Contributing
------------

Please see our `contributing guide`_.

.. _contributing guide: https://github.com/talkiq/gcloud-aio/blob/master/.github/CONTRIBUTING.rst
.. _messagebird/gcloud-pubsub-emulator: https://github.com/marcelcorso/gcloud-pubsub-emulator#gcloud-pubsub-emulator
.. _official Google documentation: https://github.com/googleapis/google-cloud-python/blob/11c72ade8b282ae1917fba19e7f4e0fe7176d12b/pubsub/google/cloud/pubsub_v1/gapic/subscriber_client.py#L236

.. |pypi| image:: https://img.shields.io/pypi/v/gcloud-aio-pubsub.svg?style=flat-square
    :alt: Latest PyPI Version
    :target: https://pypi.org/project/gcloud-aio-pubsub/

.. |pythons-aio| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-pubsub.svg?style=flat-square&label=python (aio)
    :alt: Python Version Support (gcloud-aio-pubsub)
    :target: https://pypi.org/project/gcloud-aio-pubsub/

.. |pythons-rest| image:: https://img.shields.io/pypi/pyversions/gcloud-rest-pubsub.svg?style=flat-square&label=python (rest)
    :alt: Python Version Support (gcloud-rest-pubsub)
    :target: https://pypi.org/project/gcloud-rest-pubsub/
