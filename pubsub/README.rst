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

At the moment, ``gcloud-{aio,rest}-pubsub`` only provides a set of handles
to call Pubsub REST API.

Here's the rough usage pattern for using ``SubscriberClient``:

.. code-block:: python

    from gcloud.aio.pubsub import SubscriberClient
    from gcloud.aio.pubsub import SubscriberMessage

    client = SubscriberClient()
    # create subscription
    client.create_subscription(
        'projects/<project_name>/subscriptions/<subscription_name>',
        'projects/<project_name>/topics/<topic_name>')

    # pull messages
    client.pull(
        'projects/<project_name>/subscriptions/<subscription_name>',
        max_messages=10)


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
