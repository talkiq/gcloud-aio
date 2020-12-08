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

    import aiohttp
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

    class AckDeadlineCache:
        def __init__(self, subscriber_client: SubscriberClient,
                     subscription: str, cache_timout: int):
            self.subscriber_client = subscriber_client
            self.subscription = subscription
            self.cache_timeout = cache_timout
            self.ack_deadline: float = float('inf')
            self.last_refresh: float = 0

        async def get(self) -> float:
            if self.ack_deadline == float('inf') or self.cache_outdated():
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

    async def acker(subscription: str,
                    ack_queue: 'asyncio.Queue[str]',
                    subscriber_client: 'SubscriberClient',
                    ack_window: float,
                    metrics_client: MetricsAgent) -> None:
        ack_ids: List[str] = []
        while True:
            time_budget = ack_window
            if not ack_ids:
                ack_ids.append(await ack_queue.get())
                ack_queue.task_done()

            while time_budget > 0:
                start = time.perf_counter()
                try:
                    ack_id = await asyncio.wait_for(
                        ack_queue.get(), timeout=time_budget)
                    ack_ids.append(ack_id)
                    ack_queue.task_done()
                except asyncio.TimeoutError:
                    break
                time_budget -= (time.perf_counter() - start)

            try:
                await subscriber_client.acknowledge(subscription,
                                                    ack_ids=ack_ids)
            except Exception as e:
                log.warning(
                    'Ack request failed, better luck next batch', exc_info=e)
                continue

            metrics_client.histogram('pubsub.acker.batch', len(ack_ids))

            ack_ids = []

    async def _fire_callback(semaphore: asyncio.Semaphore,
                             message: SubscriberMessage,
                             callback: ApplicationHandler,
                             ack_queue: 'asyncio.Queue[str]',
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
            log.exception('Application callback raised an exception')
            metrics_client.increment('pubsub.consumer.failed')
        finally:
            semaphore.release()

    async def consumer(
            message_queue: MessageQueue,
            callback: ApplicationHandler,
            ack_queue: 'asyncio.Queue[str]',
            ack_deadline_cache: AckDeadlineCache,
            consumer_pool_size: int,
            metrics_client: MetricsAgent) -> None:
        semaphore = asyncio.Semaphore(consumer_pool_size)
        while True:
            await semaphore.acquire()

            message, pulled_at = await message_queue.get()

            ack_deadline = await ack_deadline_cache.get()
            if (time.perf_counter() - pulled_at) >= ack_deadline:
                metrics_client.increment('pubsub.consumer.failfast')
                message_queue.task_done()
                semaphore.release()
                continue

            metrics_client.histogram(
                'pubsub.consumer.latency.receive',
                # publish_time is in UTC Zulu
                # https://cloud.google.com/pubsub/docs/reference/rest/v1/PubsubMessage
                time.time() - message.publish_time.timestamp())

            asyncio.ensure_future(_fire_callback(
                semaphore,
                message,
                callback,
                ack_queue,
                metrics_client,
            ))
            message_queue.task_done()

    async def producer(
            subscription: str,
            message_queue: MessageQueue,
            subscriber_client: 'SubscriberClient',
            max_messages: int,
            metrics_client: MetricsAgent
    ) -> None:
        while True:
            try:
                new_messages = await subscriber_client.pull(
                    subscription=subscription, max_messages=max_messages)
            except asyncio.TimeoutError:
                continue

            pulled_at = time.perf_counter()
            for m in new_messages:
                await message_queue.put((m, pulled_at))

            metrics_client.histogram(
                'pubsub.producer.batch', len(new_messages))

            await message_queue.join()

    async def subscribe(subscription: str,  # pylint: disable=too-many-locals
                        handler: ApplicationHandler,
                        *,
                        num_workers: int = 1,
                        max_messages: int = 100,
                        ack_window: float = 0.3,
                        ack_deadline_cache_timeout: int = 10,
                        consumer_pool_size: int = 1,
                        subscriber_client: Optional[SubscriberClient] = None,
                        metrics_client: Optional[MetricsAgent] = None
                        ) -> None:
        async with aiohttp.ClientSession() as session:
            ack_queue: 'asyncio.Queue[str]' = asyncio.Queue(
                maxsize=(max_messages * num_workers))
            subscriber = subscriber_client or SubscriberClient(session=session)
            ack_deadline_cache = AckDeadlineCache(subscriber,
                                                  subscription,
                                                  ack_deadline_cache_timeout)
            metrics_client = metrics_client or MetricsAgent()
            tasks = []
            try:
                tasks.append(asyncio.ensure_future(
                    acker(subscription, ack_queue, subscriber,
                          ack_window=ack_window, metrics_client=metrics_client)
                ))
                for _ in range(num_workers):
                    q: MessageQueue = asyncio.Queue(
                        maxsize=max_messages)
                    tasks.append(asyncio.ensure_future(
                        consumer(q,
                                 handler,
                                 ack_queue,
                                 ack_deadline_cache,
                                 consumer_pool_size,
                                 metrics_client=metrics_client)
                    ))
                    tasks.append(asyncio.ensure_future(
                        producer(subscription,
                                 q,
                                 subscriber,
                                 max_messages=max_messages,
                                 metrics_client=metrics_client)
                    ))

                await asyncio.wait(
                    tasks, return_when=asyncio.FIRST_COMPLETED)
                raise Exception('A subscriber worker shut down unexpectedly!')
            except Exception:
                log.exception('Subscriber exited')
                for task in tasks:
                    task.cancel()
                await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
            raise asyncio.CancelledError('Subscriber shut down')
