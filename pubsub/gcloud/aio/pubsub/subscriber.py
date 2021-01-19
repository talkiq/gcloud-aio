from gcloud.aio.auth import BUILD_GCLOUD_REST

if BUILD_GCLOUD_REST:
    pass
else:
    import asyncio
    import logging
    import time
    from typing import Awaitable
    from typing import Callable
    from typing import List
    from typing import Optional
    from typing import Tuple
    from typing import TYPE_CHECKING
    from typing import TypeVar

    from gcloud.aio.pubsub.subscriber_client import SubscriberClient
    from gcloud.aio.pubsub.subscriber_message import SubscriberMessage
    from gcloud.aio.pubsub.metrics_agent import MetricsAgent

    log = logging.getLogger(__name__)

    if TYPE_CHECKING:
        MessageQueue = asyncio.Queue[Tuple[SubscriberMessage,  # pylint: disable=unsubscriptable-object
                                           float]]
    else:
        MessageQueue = asyncio.Queue
    ApplicationHandler = Callable[[SubscriberMessage], Awaitable[None]]
    T = TypeVar('T')

    class AckDeadlineCache:
        def __init__(self, subscriber_client: SubscriberClient,
                     subscription: str, cache_timout: int):
            self.subscriber_client = subscriber_client
            self.subscription = subscription
            self.cache_timeout = cache_timout
            self.ack_deadline: float = float('inf')
            self.last_refresh: float = float('-inf')

        async def get(self) -> float:
            if self.cache_outdated():
                await self.refresh()
            return self.ack_deadline

        async def refresh(self) -> None:
            try:
                sub = await self.subscriber_client.get_subscription(
                    self.subscription)
                self.ack_deadline = float(sub['ackDeadlineSeconds'])
            except Exception as e:
                log.warning(
                    'Failed to refresh ackDeadlineSeconds value', exc_info=e)
            self.last_refresh = time.perf_counter()

        def cache_outdated(self) -> bool:
            if (time.perf_counter() - self.last_refresh) > self.cache_timeout:
                return True
            return False

    async def _budgeted_queue_get(queue: 'asyncio.Queue[T]',
                                  time_budget: float) -> List[T]:
        result = []
        while time_budget > 0:
            start = time.perf_counter()
            try:
                message = await asyncio.wait_for(
                    queue.get(), timeout=time_budget)
                result.append(message)
                queue.task_done()
            except asyncio.TimeoutError:
                break
            time_budget -= (time.perf_counter() - start)
        return result

    async def acker(subscription: str,
                    ack_queue: 'asyncio.Queue[str]',
                    subscriber_client: 'SubscriberClient',
                    ack_window: float,
                    metrics_client: MetricsAgent) -> None:
        ack_ids: List[str] = []
        while True:
            if not ack_ids:
                ack_ids.append(await ack_queue.get())
                ack_queue.task_done()

            ack_ids += await _budgeted_queue_get(ack_queue, ack_window)

            # acknowledge endpoint limit is 524288 bytes
            # which is ~2744 ack_ids
            if len(ack_ids) > 2500:
                log.error(
                    'acker is falling behind, dropping %d unacked messages',
                    len(ack_ids) - 2500)
                ack_ids = ack_ids[-2500:]
            try:
                await subscriber_client.acknowledge(subscription,
                                                    ack_ids=ack_ids)
            except Exception as e:
                log.warning(
                    'Ack request failed, better luck next batch', exc_info=e)
                metrics_client.increment('pubsub.acker.batch.failed')
                continue

            metrics_client.histogram('pubsub.acker.batch', len(ack_ids))

            ack_ids = []

    async def nacker(subscription: str,
                     nack_queue: 'asyncio.Queue[str]',
                     subscriber_client: 'SubscriberClient',
                     nack_window: float,
                     metrics_client: MetricsAgent) -> None:
        ack_ids: List[str] = []
        while True:
            if not ack_ids:
                ack_ids.append(await nack_queue.get())
                nack_queue.task_done()

            ack_ids += await _budgeted_queue_get(nack_queue, nack_window)

            # modifyAckDeadline endpoint limit is 524288 bytes
            # which is ~2744 ack_ids
            if len(ack_ids) > 2500:
                log.error(
                    'nacker is falling behind, dropping %d unacked messages',
                    len(ack_ids) - 2500)
                ack_ids = ack_ids[-2500:]
            try:
                await subscriber_client.modify_ack_deadline(
                    subscription,
                    ack_ids=ack_ids,
                    ack_deadline_seconds=0)
            except asyncio.CancelledError:  # pylint: disable=try-except-raise
                raise
            except Exception as e:
                log.warning(
                    'Nack request failed, better luck next batch', exc_info=e)
                metrics_client.increment('pubsub.nacker.batch.failed')
                continue

            metrics_client.histogram('pubsub.nacker.batch', len(ack_ids))

            ack_ids = []

    async def _execute_callback(message: SubscriberMessage,
                                callback: ApplicationHandler,
                                ack_queue: 'asyncio.Queue[str]',
                                nack_queue: 'Optional[asyncio.Queue[str]]',
                                metrics_client: MetricsAgent
                                ) -> None:
        try:
            start = time.perf_counter()
            await callback(message)
            await ack_queue.put(message.ack_id)
            metrics_client.increment('pubsub.consumer.succeeded')
            metrics_client.histogram('pubsub.consumer.latency.runtime',
                                     time.perf_counter() - start)
        except Exception:
            if nack_queue:
                await nack_queue.put(message.ack_id)
            log.exception('Application callback raised an exception')
            metrics_client.increment('pubsub.consumer.failed')

    async def consumer(  # pylint: disable=too-many-locals
            message_queue: MessageQueue,
            callback: ApplicationHandler,
            ack_queue: 'asyncio.Queue[str]',
            ack_deadline_cache: AckDeadlineCache,
            max_tasks: int,
            nack_queue: 'Optional[asyncio.Queue[str]]',
            metrics_client: MetricsAgent) -> None:
        try:
            semaphore = asyncio.Semaphore(max_tasks)

            async def _consume_one(message: SubscriberMessage,
                                   pulled_at: float) -> None:
                await semaphore.acquire()

                ack_deadline = await ack_deadline_cache.get()
                if (time.perf_counter() - pulled_at) >= ack_deadline:
                    metrics_client.increment('pubsub.consumer.failfast')
                    message_queue.task_done()
                    semaphore.release()
                    return

                metrics_client.histogram(
                    'pubsub.consumer.latency.receive',
                    # publish_time is in UTC Zulu
                    # https://cloud.google.com/pubsub/docs/reference/rest/v1/PubsubMessage
                    time.time() - message.publish_time.timestamp())

                task = asyncio.ensure_future(_execute_callback(
                    message,
                    callback,
                    ack_queue,
                    nack_queue,
                    metrics_client,
                ))
                task.add_done_callback(lambda _f: semaphore.release())
                message_queue.task_done()

            while True:
                message, pulled_at = await message_queue.get()
                await asyncio.shield(_consume_one(message, pulled_at))
        except asyncio.CancelledError:
            log.info('Consumer worker cancelled. Gracefully terminating...')
            for _ in range(max_tasks):
                await semaphore.acquire()

            await ack_queue.join()
            if nack_queue:
                await nack_queue.join()
            log.info('Consumer terminated gracefully.')
            raise

    async def producer(
            subscription: str,
            message_queue: MessageQueue,
            subscriber_client: 'SubscriberClient',
            max_messages: int,
            metrics_client: MetricsAgent) -> None:
        try:
            while True:
                new_messages = []
                try:
                    new_messages = await subscriber_client.pull(
                        subscription=subscription,
                        max_messages=max_messages,
                        # it is important to have this value reasonably high
                        # as long lived connections may be left hanging
                        # on a server which will cause delay in message
                        # delivery or even false deadlettering if it is enabled
                        timeout=30)
                except (asyncio.TimeoutError, KeyError):
                    continue

                metrics_client.histogram(
                    'pubsub.producer.batch', len(new_messages))

                pulled_at = time.perf_counter()
                while new_messages:
                    await message_queue.put((new_messages[-1], pulled_at))
                    new_messages.pop()

                await message_queue.join()
        except asyncio.CancelledError:
            log.info('Producer worker cancelled. Gracefully terminating...')
            pulled_at = time.perf_counter()
            for m in new_messages:
                await message_queue.put((m, pulled_at))

            await message_queue.join()
            log.info('Producer terminated gracefully.')
            raise

    async def subscribe(subscription: str,  # pylint: disable=too-many-locals
                        handler: ApplicationHandler,
                        subscriber_client: SubscriberClient,
                        *,
                        num_producers: int = 1,
                        max_messages_per_producer: int = 100,
                        ack_window: float = 0.3,
                        ack_deadline_cache_timeout: int = 60,
                        num_tasks_per_consumer: int = 1,
                        enable_nack: bool = True,
                        nack_window: float = 0.3,
                        metrics_client: Optional[MetricsAgent] = None
                        ) -> None:
        ack_queue: 'asyncio.Queue[str]' = asyncio.Queue(
            maxsize=(max_messages_per_producer * num_producers))
        nack_queue: 'Optional[asyncio.Queue[str]]' = None
        ack_deadline_cache = AckDeadlineCache(subscriber_client,
                                              subscription,
                                              ack_deadline_cache_timeout)
        metrics_client = metrics_client or MetricsAgent()
        acker_tasks = []
        consumer_tasks = []
        producer_tasks = []
        try:
            acker_tasks.append(asyncio.ensure_future(
                acker(subscription, ack_queue, subscriber_client,
                      ack_window=ack_window, metrics_client=metrics_client)
            ))
            if enable_nack:
                nack_queue = asyncio.Queue(
                    maxsize=(max_messages_per_producer * num_producers))
                acker_tasks.append(asyncio.ensure_future(
                    nacker(subscription, nack_queue, subscriber_client,
                           nack_window=nack_window,
                           metrics_client=metrics_client)
                ))
            for _ in range(num_producers):
                q: MessageQueue = asyncio.Queue(
                    maxsize=max_messages_per_producer)
                consumer_tasks.append(asyncio.ensure_future(
                    consumer(q,
                             handler,
                             ack_queue,
                             ack_deadline_cache,
                             num_tasks_per_consumer,
                             nack_queue,
                             metrics_client=metrics_client)
                ))
                producer_tasks.append(asyncio.ensure_future(
                    producer(subscription,
                             q,
                             subscriber_client,
                             max_messages=max_messages_per_producer,
                             metrics_client=metrics_client)
                ))

            all_tasks = [*producer_tasks, *consumer_tasks, *acker_tasks]
            done, _ = await asyncio.wait(all_tasks,
                                         return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                task.result()
            raise Exception('A subscriber worker shut down unexpectedly!')
        except Exception as e:
            log.info('Subscriber exited', exc_info=e)
            for task in producer_tasks:
                task.cancel()
            await asyncio.wait(producer_tasks,
                               return_when=asyncio.ALL_COMPLETED)

            for task in consumer_tasks:
                task.cancel()
            await asyncio.wait(consumer_tasks,
                               return_when=asyncio.ALL_COMPLETED)

            for task in acker_tasks:
                task.cancel()
            await asyncio.wait(acker_tasks, return_when=asyncio.ALL_COMPLETED)
        raise asyncio.CancelledError('Subscriber shut down')
