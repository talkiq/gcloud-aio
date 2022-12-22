"""
This library implements various methods for working with the Google Pubsub
APIs.

## Installation

```console
$ pip install --upgrade gcloud-aio-pubsub
```

## Usage

### Subscriber

`gcloud-aio-pubsub` provides `SubscriberClient` as an interface to call
pubsub's HTTP API:

```python
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
```

There's also `gcloud.aio.pubsub.subscribe` helper function you can use to setup
a pubsub processing pipeline. It is built with `asyncio` and thus only
available in the `gcloud-aio-pubsub` package. The usage is fairly simple:

```python
from gcloud.aio.pubsub import SubscriberClient
from gcloud.aio.pubsub import subscribe

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
)
```

While defaults are somewhat sensible, it is highly recommended to performance
test your application and tweak function parameter to your specific needs.
Here's a few hints:

- `handler`: An async function that will be called for each message. It should
  accept an instance of `SubscriberMessage` as its only argument and return
  `None` if the message should be acked. An exception raised within the handler
  will result in the message being left to expire, and thus it will be
  redelivered according to your subscription's ack deadline.
- `num_producers`: Number of workers that will be making `pull` requests to
  pubsub. Please note that a worker will only fetch new batch once the
  `handler` was called for each message from the previous batch. This means
  that running only a single worker will most likely make your application IO
  bound. If you notice this being an issue don't hesitate to bump this
  parameter.
- `max_messages_per_producer`: Number of pubsub messages a worker will try to
  fetch in a single batch. This value is passed to `pull` [endpoint][endpoint]
  as `maxMessages` parameter. A rule of thumb here is the faster your handler
  is the bigger this value should be.
- `ack_window`: Ack requests are handled separately and are done in batches.
  This parameters specifies how often ack requests will be made. Setting it to
  `0.0` will effectively disable batching.
- `num_tasks_per_consumer`: How many `handle` calls a worker can make until it
  blocks to wait for them to return. If you process messages independently from
  each other you should be good with the default value of `1`. If you do
  something fancy (e.g. aggregate messages before processing them), you'll want
  a higher pool here. You can think of `num_producers * num_tasks_per_consumer`
  as an upper limit of how many messages can possibly be within your
  application state at any given moment.
- `enable_nack`: If enabled messages for which `callback` raised an exception
  will be explicitly nacked using `modifyAckDeadline` endpoint so they can be
  retried immediately.
- `nack_window`: Same as `ack_window` but for nack requests.

Note that this method was built under the assumption that it is the main thread
of your application. It may work just fine otherwise, but be aware that the
usecase of running it in a background thread has not been extensively tested.

As it is generally assumed to run in the foreground, it relies on task
cancellation to shut itself down (ie. caused by process termination). To cancel
it from a thread, you can send an `asyncio.CancelledError` event via
`Task.cancel()`:

```python
subscribe_task = asyncio.create_task(gcloud.aio.pubsub.subscribe(...))

# snip

subscribe_task.cancel()
```

### Prometheus Metrics

If you like pull-based metrics like Prometheus you will be pleased to know that
the subscriber records Prometheus metrics in the form
`gcloud_aio_pubsub_<metric>`, which will have no effect if you don't use
Prometheus to scrape app metrics:

- `subscriber_batch_size` - [histogram] how many messages were pulled from the
  subscription in a single batch
- `subscriber_consume` (labels: `outcome = {'succeeded', 'cancelled', 'failed',
  'failfast'}`) - [counter] a consume operation has completed with a given
  outcome
- `subscriber_consume_latency_seconds` (labels: `phase = {'receive',
  'queueing', 'runtime'}`) - [histogram] how many seconds taken to receive a
  message, while waiting for processing, or to complete the callback
- `subscriber_batch_status` (labels: `component = {'acker', 'nacker'}, outcome
  = {'succeeded', 'failed'}`) - [counter] a batch has succeeded or failed to be
  acked or nacked
- `subscriber_messages_processed` (labels: `component = {'acker', 'nacker'}`) -
  [counter] the number of messages that were processed, either by being acked
  or nacked
- `subscriber_messages_received` - [counter] the number of messages pulled from
  pubsub

### Metrics Agent (Deprecated)

`subscribe` has also an optional `metrics_client` argument which will be
removed in a future release. You can provide any metrics agent that implements
the same interface as `MetricsAgent` (Datadog client will do ;) ) and get the
following metrics:

- `pubsub.producer.batch` - [histogram] actual size of a batch retrieved from
  pubsub.
- `pubsub.consumer.failfast` - [increment] a message was dropped due to its
  lease being expired.
- `pubsub.consumer.latency.receive` - [histogram] how many seconds it took for
  a message to reach handler after it was published.
- `pubsub.consumer.succeeded` - [increment] `handler` call was successfull.
- `pubsub.consumer.failed` - [increment] `handler` call raised an exception.
- `pubsub.consumer.latency.runtime` - [histogram] `handler` execution time in
  seconds.
- `pubsub.acker.batch.failed` - [increment] ack request failed.
- `pubsub.acker.batch` - [histogram] actual number of messages that was acked
  in a single request.

## Publisher

The `PublisherClient` is a dead-simple alternative to the official Google Cloud
Pub/Sub publisher client. The main design goal was to eliminate all the
additional gRPC overhead implemented by the upstream client.

If migrating between this library and the official one, the main difference is
this: the `gcloud-{aio,rest}-pubsub` publisher's `.publish()` method
*immediately* publishes the messages you've provided, rather than maintaining
our own publishing queue, implementing batching and flow control, etc. If
you're looking for a full-featured publishing library with all the bells and
whistles built in, you may be interested in the upstream provider. If you're
looking to manage your own batching / timeouts / retry / threads / etc, this
library should be a bit easier to work with.

```python
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
```

## Emulators

For testing purposes, you may want to use `gcloud-aio-pubsub` along with a
local Pubsub emulator. Setting the `$PUBSUB_EMULATOR_HOST` environment variable
to the local address of your emulator should be enough to do the trick.

For example, using the official Google Pubsub emulator:

```shell
gcloud beta emulators pubsub start --host-port=0.0.0.0:8681
export PUBSUB_EMULATOR_HOST='0.0.0.0:8681'
```

Any `gcloud-aio-pubsub` Publisher requests made with that environment variable
set will query the emulator instead of the official GCS APIs.

For easier ergonomics, you may be interested in
[thekevjames/gcloud-pubsub-emulator][emulator-docker].

## Customization

This library mostly tries to stay agnostic of potential use-cases; as such, we
do not implement any sort of retrying or other policies under the assumption
that we wouldn't get things right for every user's situation.

As such, we recommend configuring your own policies on an as-needed basis. The
[backoff][backoff] library can make this quite straightforward! For example,
you may find it useful to configure something like:

```python
class SubscriberClientWithBackoff(SubscriberClient):
    @backoff.on_exception(backoff.expo, aiohttp.ClientResponseError,
                          max_tries=5, jitter=backoff.full_jitter)
    async def pull(self, *args: Any, **kwargs: Any):
        return await super().pull(*args, **kwargs)
```

[backoff]: https://pypi.org/project/backoff/
[emulator-docker]:
https://github.com/TheKevJames/tools/tree/master/docker-gcloud-pubsub-emulator
[endpoint]:
https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/pull#request-body
"""
from pkg_resources import get_distribution
__version__ = get_distribution('gcloud-aio-pubsub').version

from gcloud.aio.auth import BUILD_GCLOUD_REST  # pylint: disable=no-name-in-module
from gcloud.aio.pubsub.publisher_client import PublisherClient
from gcloud.aio.pubsub.subscriber_client import SubscriberClient
from gcloud.aio.pubsub.subscriber_message import SubscriberMessage
from gcloud.aio.pubsub.utils import PubsubMessage

__all__ = [
    'PublisherClient',
    'PubsubMessage',
    'SubscriberClient',
    'SubscriberMessage',
    '__version__',
]

if not BUILD_GCLOUD_REST:
    from gcloud.aio.pubsub.subscriber import subscribe
    __all__.append('subscribe')
