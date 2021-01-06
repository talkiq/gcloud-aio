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

``gcloud-{aio,rest}-pubsub`` provides ``SubscriberClient``
as an interface to call pubsub's HTTP API:

.. code-block:: python

    from gcloud.aio.pubsub import SubscriberClient
    from gcloud.aio.pubsub import SubscriberMessage

    client = SubscriberClient()
    # create subscription
    await client.create_subscription(
        'projects/<project_name>/subscriptions/<subscription_name>',
        'projects/<project_name>/topics/<topic_name>')

    # pull messages
    messages: List[SubscriberMessage] = await client.pull(
        'projects/<project_name>/subscriptions/<subscription_name>',
        max_messages=10)


There's also ``gcloud.aio.pubsub.subscribe`` helper function you can use to
setup a pubsub processing pipeline. It is built with ``asyncio`` and thus only
available in ``gcloud-aio-pubsub`` package. The usage is fairly simple:

.. code-block:: python

    from gcloud.aio.pubsub import SubscriberClient
    from gcloud.aio.pubsub import subscribe
    from gcloud.aio.pubsub.metrics_agent import MetricsAgent

    subscriber_client = SubscriberClient()

    async def handler(message):
        return

    await subscribe(
        'projects/<my_project>/subscriptions/<my_subscription>',
        handler,
        subscriber_client,
        num_producers=1,
        max_messages_per_producer=100,
        ack_window=0.3,
        num_tasks_per_consumer=1,
        enable_nack=True,
        nack_window=0.3,
        metrics_client=MetricsAgent()
    )

While defaults are somewhat sensible, it is highly recommended to performance
test your application and tweak function parameter to your specific needs.
Here's a few hints:

:``handler``:
    an async function that will be called for each message. It should accept an
    instance of ``SubscriberMessage`` as its only argument and return ``None``
    if the message should be acked. An exception raised within the handler will
    result in the message being left to expire, and thus it will be redelivered
    according to your subscription's ack deadline.

:``num_producers``:
    number of workers that will be making ``pull`` requests to pubsub. Please
    note that a worker will only fetch new batch once the ``handler`` was called
    for each message from the previous batch. This means that running only a
    single worker will most likely make your application IO bound. If you notice
    this being an issue don't hesitate to bump this parameter.

:``max_messages_per_producer``:
    number of pubsub messages a worker will try to fetch in a single batch. This
    value is passed to ``pull`` `endpoint`_ as ``maxMessages`` parameter. A rule
    of thumb here is the faster your handler is the bigger this value should be.

:``ack_window``:
    ack requests are handled separately and are done in batches. This parameters
    specifies how often ack requests will be made. Setting it to ``0.0`` will
    effectively disable batching.

:``num_tasks_per_consumer``:
    how many ``handle`` calls a worker can make until it blocks to wait for them
    to return. If you process messages independently from each other you should
    be good with the default value of ``1``. If you do something fancy (e.g.
    aggregate messages before processing them), you'll want a higher pool here.
    You can think of ``num_producers * num_tasks_per_consumer`` as an upper
    limit of how many messages can possibly be within your application state at
    any given moment.

:``enable_nack``:
    if enabled messages for which ``callback`` raised an exception will be
    explicitly nacked using ``modifyAckDeadline`` endpoint so they can be
    retried immediately.

:``nack_window``:
    same as ``ack_window`` but for nack requests


``subscribe`` has also an optional ``metrics_client`` argument. You can provide
any metrics agent that implements the same interface as ``MetricsAgent``
(Datadog client will do ;) ) and get the following metrics:

- ``pubsub.producer.batch`` - [histogram] actual size of a batch retrieved from
  pubsub.

- ``pubsub.consumer.failfast`` - [increment] a message was dropped due to its
  lease being expired.

- ``pubsub.consumer.latency.receive`` - [histogram] how many seconds it took for
  a message to reach handler after it was published.

- ``pubsub.consumer.succeeded`` - [increment] ``handler`` call was successfull.

- ``pubsub.consumer.failed`` - [increment] ``handler`` call raised an exception.

- ``pubsub.consumer.latency.runtime`` - [histogram] ``handler`` execution time
  in seconds.

- ``pubsub.acker.batch.failed`` - [increment] ack request failed.

- ``pubsub.acker.batch`` - [histogram] actual number of messages that was acked
  in a single request.


Publisher
~~~~~~~~~

The ``PublisherClient`` is a dead-simple alternative to the official Google
Cloud Pub/Sub publisher client. The main design goal was to eliminate all the
additional gRPC overhead implemented by the upstream client.

If migrating between this library and the official one, the main difference is
this: the ``gcloud-{aio,rest}-pubsub`` publisher's ``.publish()`` method *immediately*
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

.. _endpoint: https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/pull#request-body
