Asyncio Python Client for Google Cloud Pub/Sub
==============================================

|pypi| |pythons-aio|

Installation
------------

.. code-block:: console

    $ pip install --upgrade gcloud-aio-pubsub

Usage
-----

This Pub/Sub implementation is based on ``google-cloud-pubsub >= 0.29.4``

Currently we have only implemented an asyncio version of ``SubscriberClient``
as the subscription pattern does not work with asyncio by default. The official
Google publisher returns a future which is mostly useable as-is. We've not yet
seen a need to build a non-asyncio threadsafe version of the library -- the
upstream Google libraries have this well-handled.

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
-------------

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
~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~

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
~~~~~~~~~

``f.max_requests`` is defined, but seems to be unused.

Contributing
------------

Please see our `contributing guide`_.

.. _contributing guide: https://github.com/talkiq/gcloud-aio/blob/master/.github/CONTRIBUTING.rst
.. _official Google documentation: https://github.com/googleapis/google-cloud-python/blob/11c72ade8b282ae1917fba19e7f4e0fe7176d12b/pubsub/google/cloud/pubsub_v1/gapic/subscriber_client.py#L236

.. |pypi| image:: https://img.shields.io/pypi/v/gcloud-aio-pubsub.svg?style=flat-square
    :alt: Latest PyPI Version
    :target: https://pypi.org/project/gcloud-aio-pubsub/

.. |pythons-aio| image:: https://img.shields.io/pypi/pyversions/gcloud-aio-pubsub.svg?style=flat-square
    :alt: Python Version Support
    :target: https://pypi.org/project/gcloud-aio-pubsub/
