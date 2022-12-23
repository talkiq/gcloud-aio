from gcloud.aio.auth import BUILD_GCLOUD_REST

# pylint: disable=too-complex
if BUILD_GCLOUD_REST:
    pass
else:
    import aiohttp
    import asyncio
    import logging
    import time
    import warnings
    from typing import Awaitable
    from typing import Callable
    from typing import List
    from typing import Optional
    from typing import Tuple
    from typing import TYPE_CHECKING
    from typing import TypeVar

    from gcloud.aio.pubsub import metrics
    from gcloud.aio.pubsub.subscriber_client import SubscriberClient
    from gcloud.aio.pubsub.subscriber_message import SubscriberMessage
    from gcloud.aio.pubsub.metrics_agent import MetricsAgent

    log = logging.getLogger(__name__)

    if TYPE_CHECKING:
        MessageQueue = asyncio.Queue[
            Tuple[
                SubscriberMessage,  # pylint: disable=unsubscriptable-object
                float,
            ]
        ]
    else:
        MessageQueue = asyncio.Queue

    ApplicationHandler = Callable[[SubscriberMessage], Awaitable[None]]
    T = TypeVar('T')

    class AckDeadlineCache:
        def __init__(
            self, subscriber_client: SubscriberClient,
            subscription: str, cache_timeout: float,
        ):
            self.subscriber_client = subscriber_client
            self.subscription = subscription
            self.cache_timeout = cache_timeout
            self.ack_deadline: float = float('inf')
            self.last_refresh: float = float('-inf')

        async def get(self) -> float:
            if self.cache_outdated():
                await self.refresh()
            return self.ack_deadline

        async def refresh(self) -> None:
            try:
                sub = await self.subscriber_client.get_subscription(
                    self.subscription,
                )
                self.ack_deadline = float(sub['ackDeadlineSeconds'])
            except Exception as e:
                log.warning(
                    'failed to refresh ackDeadlineSeconds value',
                    exc_info=e,
                )
            self.last_refresh = time.perf_counter()

        def cache_outdated(self) -> bool:
            if (
                time.perf_counter() - self.last_refresh > self.cache_timeout
                or self.ack_deadline == float('inf')
            ):
                return True
            return False

    async def _budgeted_queue_get(
        queue: 'asyncio.Queue[T]',
        time_budget: float,
    ) -> List[T]:
        result = []
        while time_budget > 0:
            start = time.perf_counter()
            try:
                message = await asyncio.wait_for(
                    queue.get(), timeout=time_budget,
                )
                result.append(message)
            except asyncio.TimeoutError:
                break
            time_budget -= (time.perf_counter() - start)
        return result

    async def acker(
        subscription: str,
        ack_queue: 'asyncio.Queue[str]',
        subscriber_client: 'SubscriberClient',
        ack_window: float,
        metrics_client: MetricsAgent,
    ) -> None:
        ack_ids: List[str] = []
        while True:
            if not ack_ids:
                ack_ids.append(await ack_queue.get())

            ack_ids += await _budgeted_queue_get(ack_queue, ack_window)

            # acknowledge endpoint limit is 524288 bytes
            # which is ~2744 ack_ids
            if len(ack_ids) > 2500:
                log.error(
                    'acker is falling behind, dropping unacked messages',
                    extra={'count': len(ack_ids) - 2500},
                )
                ack_ids = ack_ids[-2500:]
                for _ in range(len(ack_ids) - 2500):
                    ack_queue.task_done()

            try:
                await subscriber_client.acknowledge(
                    subscription,
                    ack_ids=ack_ids,
                )
                for _ in ack_ids:
                    ack_queue.task_done()
            except aiohttp.client_exceptions.ClientResponseError as e:
                if e.status == 400:
                    log.exception(
                        'unrecoverable ack error, one or more '
                        'messages may be dropped: %s', e,
                    )

                    async def maybe_ack(ack_id: str) -> None:
                        try:
                            await subscriber_client.acknowledge(
                                subscription,
                                ack_ids=[ack_id],
                            )
                        except Exception as ex:
                            log.warning(
                                'ack failed', extra={'ack_id': ack_id},
                                exc_info=ex,
                            )
                        finally:
                            ack_queue.task_done()

                    for ack_id in ack_ids:
                        asyncio.ensure_future(maybe_ack(ack_id))
                    ack_ids = []

                log.warning(
                    'ack request failed, better luck next batch',
                    exc_info=e,
                )
                metrics_client.increment('pubsub.acker.batch.failed')
                metrics.BATCH_STATUS.labels(
                    component='acker',
                    outcome='failed',
                ).inc()

                continue
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.warning(
                    'ack request failed, better luck next batch',
                    exc_info=e,
                )
                metrics_client.increment('pubsub.acker.batch.failed')
                metrics.BATCH_STATUS.labels(
                    component='acker',
                    outcome='failed',
                ).inc()

                continue

            metrics_client.histogram('pubsub.acker.batch', len(ack_ids))
            metrics.BATCH_STATUS.labels(
                component='acker',
                outcome='succeeded',
            ).inc()
            metrics.MESSAGES_PROCESSED.labels(component='acker').inc(
                len(ack_ids),
            )

            ack_ids = []

    async def nacker(
        subscription: str,
        nack_queue: 'asyncio.Queue[str]',
        subscriber_client: 'SubscriberClient',
        nack_window: float,
        metrics_client: MetricsAgent,
    ) -> None:
        ack_ids: List[str] = []
        while True:
            if not ack_ids:
                ack_ids.append(await nack_queue.get())

            ack_ids += await _budgeted_queue_get(nack_queue, nack_window)

            # modifyAckDeadline endpoint limit is 524288 bytes
            # which is ~2744 ack_ids
            if len(ack_ids) > 2500:
                log.error(
                    'nacker is falling behind, dropping unacked '
                    'messages', extra={'count': len(ack_ids) - 2500},
                )
                ack_ids = ack_ids[-2500:]
                for _ in range(len(ack_ids) - 2500):
                    nack_queue.task_done()
            try:
                await subscriber_client.modify_ack_deadline(
                    subscription,
                    ack_ids=ack_ids,
                    ack_deadline_seconds=0,
                )
                for _ in ack_ids:
                    nack_queue.task_done()
            except aiohttp.client_exceptions.ClientResponseError as e:
                if e.status == 400:
                    log.exception(
                        'unrecoverable nack error, one or more '
                        'messages may be dropped: %s', e,
                    )

                    async def maybe_nack(ack_id: str) -> None:
                        try:
                            await subscriber_client.modify_ack_deadline(
                                subscription,
                                ack_ids=[ack_id],
                                ack_deadline_seconds=0,
                            )
                        except Exception as ex:
                            log.warning(
                                'nack failed',
                                extra={'ack_id': ack_id}, exc_info=ex,
                            )
                        finally:
                            nack_queue.task_done()

                    for ack_id in ack_ids:
                        asyncio.ensure_future(maybe_nack(ack_id))
                    ack_ids = []

                log.warning(
                    'nack request failed, better luck next batch',
                    exc_info=e,
                )
                metrics_client.increment('pubsub.nacker.batch.failed')
                metrics.BATCH_STATUS.labels(
                    component='nacker', outcome='failed',
                ).inc()

                continue
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.warning(
                    'nack request failed, better luck next batch',
                    exc_info=e,
                )
                metrics_client.increment('pubsub.nacker.batch.failed')
                metrics.BATCH_STATUS.labels(
                    component='nacker', outcome='failed',
                ).inc()

                continue

            metrics_client.histogram('pubsub.nacker.batch', len(ack_ids))
            metrics.BATCH_STATUS.labels(
                component='nacker',
                outcome='succeeded',
            ).inc()
            metrics.MESSAGES_PROCESSED.labels(component='nacker').inc(
                len(ack_ids),
            )

            ack_ids = []

    async def _execute_callback(
        message: SubscriberMessage,
        callback: ApplicationHandler,
        ack_queue: 'asyncio.Queue[str]',
        nack_queue: 'Optional[asyncio.Queue[str]]',
        insertion_time: float,
        metrics_client: MetricsAgent,
    ) -> None:
        try:
            start = time.perf_counter()
            metrics.CONSUME_LATENCY.labels(phase='queueing').observe(
                start - insertion_time,
            )
            with metrics.CONSUME_LATENCY.labels(phase='runtime').time():
                await callback(message)
                await ack_queue.put(message.ack_id)
            metrics_client.histogram(
                'pubsub.consumer.latency.runtime',
                time.perf_counter() - start,
            )
            metrics_client.increment('pubsub.consumer.succeeded')
            metrics.CONSUME.labels(outcome='succeeded').inc()

        except asyncio.CancelledError:
            if nack_queue:
                await nack_queue.put(message.ack_id)
            log.warning('application callback was cancelled')
            metrics_client.increment('pubsub.consumer.cancelled')
            metrics.CONSUME.labels(outcome='cancelled').inc()
        except Exception as e:
            if nack_queue:
                await nack_queue.put(message.ack_id)
            log.exception('application callback raised an exception: %s', e)
            metrics_client.increment('pubsub.consumer.failed')
            metrics.CONSUME.labels(outcome='failed').inc()

    async def consumer(  # pylint: disable=too-many-locals
            message_queue: MessageQueue,
            callback: ApplicationHandler,
            ack_queue: 'asyncio.Queue[str]',
            ack_deadline_cache: AckDeadlineCache,
            max_tasks: int,
            nack_queue: 'Optional[asyncio.Queue[str]]',
            metrics_client: MetricsAgent,
    ) -> None:
        try:
            semaphore = asyncio.Semaphore(max_tasks)

            async def _consume_one(
                message: SubscriberMessage,
                pulled_at: float,
            ) -> None:
                await semaphore.acquire()

                ack_deadline = await ack_deadline_cache.get()
                if (time.perf_counter() - pulled_at) >= ack_deadline:
                    metrics_client.increment('pubsub.consumer.failfast')
                    metrics.CONSUME.labels(outcome='failfast').inc()
                    message_queue.task_done()
                    semaphore.release()
                    return

                # publish_time is in UTC Zulu
                # https://cloud.google.com/pubsub/docs/reference/rest/v1/PubsubMessage
                recv_latency = time.time() - message.publish_time.timestamp()
                metrics_client.histogram(
                    'pubsub.consumer.latency.receive', recv_latency,
                )
                metrics.CONSUME_LATENCY.labels(phase='receive').observe(
                    recv_latency,
                )

                task = asyncio.ensure_future(
                    _execute_callback(
                        message,
                        callback,
                        ack_queue,
                        nack_queue,
                        time.perf_counter(),
                        metrics_client,
                    ),
                )
                task.add_done_callback(lambda _f: semaphore.release())
                message_queue.task_done()

            while True:
                message, pulled_at = await message_queue.get()
                await asyncio.shield(_consume_one(message, pulled_at))
        except asyncio.CancelledError:
            log.info('consumer worker cancelled, gracefully terminating...')
            for _ in range(max_tasks):
                await semaphore.acquire()

            await ack_queue.join()
            if nack_queue:
                await nack_queue.join()
            log.info('consumer terminated gracefully')
            raise

    async def producer(
            subscription: str,
            message_queue: MessageQueue,
            subscriber_client: 'SubscriberClient',
            max_messages: int,
            metrics_client: MetricsAgent,
    ) -> None:
        try:
            while True:
                new_messages = []
                try:
                    pull_task = asyncio.ensure_future(
                        subscriber_client.pull(
                            subscription=subscription,
                            max_messages=max_messages,
                            # it is important to have this value reasonably
                            # high as long lived connections may be left
                            # hanging on a server which will cause delay in
                            # message delivery or even false deadlettering if
                            # it is enabled
                            timeout=30,
                        ),
                    )
                    new_messages = await asyncio.shield(pull_task)
                except (asyncio.TimeoutError, KeyError):
                    continue

                metrics_client.histogram(
                    'pubsub.producer.batch', len(new_messages),
                )
                metrics.MESSAGES_RECEIVED.inc(len(new_messages))
                metrics.BATCH_SIZE.observe(len(new_messages))

                pulled_at = time.perf_counter()
                while new_messages:
                    await message_queue.put((new_messages[-1], pulled_at))
                    new_messages.pop()

                await message_queue.join()
        except asyncio.CancelledError:
            log.info('producer worker cancelled, gracefully terminating...')

            if not pull_task.done():
                # Leaving the connection hanging can result in redelivered
                # messages, so try to finish before shutting down
                try:
                    new_messages += await asyncio.wait_for(pull_task, 5)
                except (asyncio.TimeoutError, KeyError):
                    pass

            pulled_at = time.perf_counter()
            for m in new_messages:
                await message_queue.put((m, pulled_at))

            await message_queue.join()
            log.info('producer terminated gracefully')
            raise

    async def subscribe(
        subscription: str,
        handler: ApplicationHandler,
        subscriber_client: SubscriberClient,
        *,
        num_producers: int = 1,
        max_messages_per_producer: int = 100,
        ack_window: float = 0.3,
        ack_deadline_cache_timeout: float = float('inf'),
        num_tasks_per_consumer: int = 1,
        enable_nack: bool = True,
        nack_window: float = 0.3,
        metrics_client: Optional[MetricsAgent] = None
    ) -> None:
        # pylint: disable=too-many-locals
        ack_queue: 'asyncio.Queue[str]' = asyncio.Queue(
            maxsize=(max_messages_per_producer * num_producers),
        )
        nack_queue: 'Optional[asyncio.Queue[str]]' = None
        ack_deadline_cache = AckDeadlineCache(
            subscriber_client,
            subscription,
            ack_deadline_cache_timeout,
        )

        if metrics_client is not None:
            warnings.warn(
                'Using MetricsAgent in subscribe() is deprecated. '
                'Refer to Prometheus metrics instead.',
                DeprecationWarning,
            )
        metrics_client = metrics_client or MetricsAgent()
        acker_tasks = []
        consumer_tasks = []
        producer_tasks = []
        try:
            acker_tasks.append(
                asyncio.ensure_future(
                    acker(
                        subscription, ack_queue, subscriber_client,
                        ack_window=ack_window, metrics_client=metrics_client,
                    ),
                ),
            )
            if enable_nack:
                nack_queue = asyncio.Queue(
                    maxsize=(max_messages_per_producer * num_producers),
                )
                acker_tasks.append(
                    asyncio.ensure_future(
                        nacker(
                            subscription, nack_queue, subscriber_client,
                            nack_window=nack_window,
                            metrics_client=metrics_client,
                        ),
                    ),
                )
            for _ in range(num_producers):
                q: MessageQueue = asyncio.Queue(
                    maxsize=max_messages_per_producer,
                )
                consumer_tasks.append(
                    asyncio.ensure_future(
                        consumer(
                            q,
                            handler,
                            ack_queue,
                            ack_deadline_cache,
                            num_tasks_per_consumer,
                            nack_queue,
                            metrics_client=metrics_client,
                        ),
                    ),
                )
                producer_tasks.append(
                    asyncio.ensure_future(
                        producer(
                            subscription,
                            q,
                            subscriber_client,
                            max_messages=max_messages_per_producer,
                            metrics_client=metrics_client,
                        ),
                    ),
                )

            # TODO: since this is in a `not BUILD_GCLOUD_REST` section, we
            # shouldn't have to care about py2 support. Using splat syntax
            # here, though, breaks the coverage.py reporter for this file even
            # though it would never be loaded at runtime in py2.
            # all_tasks = [*producer_tasks, *consumer_tasks, *acker_tasks]
            all_tasks = producer_tasks + consumer_tasks + acker_tasks
            done, _ = await asyncio.wait(
                all_tasks,
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in done:
                task.result()
            raise Exception('a subscriber worker shut down unexpectedly')
        except (asyncio.CancelledError, Exception) as e:
            log.warning('subscriber exited', exc_info=e)
            for task in producer_tasks:
                task.cancel()
            await asyncio.wait(
                producer_tasks,
                return_when=asyncio.ALL_COMPLETED,
            )

            for task in consumer_tasks:
                task.cancel()
            await asyncio.wait(
                consumer_tasks,
                return_when=asyncio.ALL_COMPLETED,
            )

            for task in acker_tasks:
                task.cancel()
            await asyncio.wait(acker_tasks, return_when=asyncio.ALL_COMPLETED)

        raise asyncio.CancelledError('subscriber shut down')
