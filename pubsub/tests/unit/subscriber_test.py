# pylint: disable=redefined-outer-name
from gcloud.aio.auth import BUILD_GCLOUD_REST

if BUILD_GCLOUD_REST:
    pass
else:
    import asyncio
    import time
    from unittest.mock import call
    from unittest.mock import MagicMock
    from unittest.mock import patch

    import pytest

    from gcloud.aio.pubsub.subscriber import AckDeadlineCache
    from gcloud.aio.pubsub.subscriber import acker
    from gcloud.aio.pubsub.subscriber import consumer
    from gcloud.aio.pubsub.subscriber import producer
    from gcloud.aio.pubsub.subscriber import subscribe
    from gcloud.aio.pubsub.subscriber import nacker

    @pytest.fixture(scope='function')
    def message():
        mock = MagicMock()
        mock.ack_id = 'ack_id'
        return mock

    @pytest.fixture(scope='function')
    def subscriber_client(message):
        mock = MagicMock()

        f = asyncio.Future()
        f.set_result({'ackDeadlineSeconds': 42})
        mock.get_subscription = MagicMock(return_value=f)

        async def g(*_args, **_kwargs):
            return [message]
        mock.pull = g

        f = asyncio.Future()
        f.set_result(None)
        mock.acknowledge = MagicMock(return_value=f)

        f = asyncio.Future()
        f.set_result(None)
        mock.modify_ack_deadline = MagicMock(return_value=f)

        return mock

    @pytest.fixture(scope='function')
    def ack_deadline_cache():
        f = asyncio.Future()
        f.set_result(float('inf'))

        mock = MagicMock()
        mock.get = MagicMock(return_value=f)
        return mock

    @pytest.fixture(scope='function')
    def application_callback():
        f = asyncio.Future()
        f.set_result(None)

        return MagicMock(return_value=f)

    # ================
    # AckDeadlineCache
    # ================

    @pytest.mark.asyncio
    async def test_ack_dealine_cache_defaults(subscriber_client):
        cache = AckDeadlineCache(
            subscriber_client, 'fake_subscription', 1)
        assert cache.cache_timeout == 1
        assert cache.ack_deadline == float('inf')
        assert cache.last_refresh == float('-inf')

    @pytest.mark.asyncio
    async def test_ack_deadline_cache_cache_outdated_false(subscriber_client):
        cache = AckDeadlineCache(
            subscriber_client, 'fake_subscription', 1000)
        cache.last_refresh = time.perf_counter()
        assert not cache.cache_outdated()

    @pytest.mark.asyncio
    async def test_ack_deadline_cache_cache_outdated_true(subscriber_client):
        cache = AckDeadlineCache(
            subscriber_client, 'fake_subscription', 0)
        cache.last_refresh = time.perf_counter()
        assert cache.cache_outdated()

    @pytest.mark.asyncio
    async def test_ack_deadline_cache_refresh_updates_value_and_last_refresh(
        subscriber_client
    ):
        cache = AckDeadlineCache(
            subscriber_client, 'fake_subscription', 1)
        await cache.refresh()
        assert cache.ack_deadline == 42
        assert cache.last_refresh
        subscriber_client.get_subscription.assert_called_once_with(
            'fake_subscription')

    @pytest.mark.asyncio
    async def test_ack_deadline_cache_refresh_is_cool_about_failures(
        subscriber_client
    ):
        f = asyncio.Future()
        f.set_exception(RuntimeError)
        subscriber_client.get_subscription = MagicMock(
            return_value=f)
        cache = AckDeadlineCache(
            subscriber_client, 'fake_subscription', 1)
        cache.ack_deadline = 55.0
        await cache.refresh()
        assert cache.ack_deadline == 55.0
        assert cache.last_refresh

    @pytest.mark.asyncio
    async def test_ack_deadline_cache_get_calls_refresh_first_time(
        subscriber_client
    ):
        cache = AckDeadlineCache(
            subscriber_client, 'fake_subscription', 1)
        assert await cache.get() == 42
        assert cache.last_refresh

    @pytest.mark.asyncio
    async def test_ack_deadline_cache_get_no_call_if_not_outdated(
        subscriber_client
    ):
        cache = AckDeadlineCache(
            subscriber_client, 'fake_subscription', 1000)
        cache.ack_deadline = 33
        cache.last_refresh = time.perf_counter()
        assert await cache.get() == 33
        subscriber_client.get_subscription.assert_not_called()

    @pytest.mark.asyncio
    async def test_ack_deadline_cache_get_no_call_first_time_if_not_outdated(
        subscriber_client
    ):
        cache = AckDeadlineCache(
            subscriber_client, 'fake_subscription', 1000)
        cache.last_refresh = time.perf_counter()
        assert await cache.get() == float('inf')
        subscriber_client.get_subscription.assert_not_called()

    @pytest.mark.asyncio
    async def test_ack_deadline_cache_get_refreshes_if_outdated(
            subscriber_client):
        cache = AckDeadlineCache(
            subscriber_client, 'fake_subscription', 0)
        cache.ack_deadline = 33
        assert await cache.get() == 42
        assert cache.last_refresh
        subscriber_client.get_subscription.assert_called_once()

    @pytest.mark.asyncio
    async def test_ack_deadline_cache_first_get_failed(subscriber_client):
        f = asyncio.Future()
        f.set_exception(RuntimeError)
        subscriber_client.get_subscription = MagicMock(
            return_value=f)
        cache = AckDeadlineCache(
            subscriber_client, 'fake_subscription', 10)
        assert await cache.get() == float('inf')
        assert cache.last_refresh
        subscriber_client.get_subscription.assert_called_once()

    # ========
    # producer
    # ========

    @pytest.mark.asyncio
    async def test_producer_fetches_messages(subscriber_client):
        queue = asyncio.Queue()
        producer_task = asyncio.ensure_future(
            producer(
                'fake_subscription',
                queue,
                subscriber_client,
                max_messages=1,
                metrics_client=MagicMock()
            )
        )
        message, pulled_at = await asyncio.wait_for(queue.get(), 0.1)
        producer_task.cancel()
        assert message
        assert isinstance(pulled_at, float)

    @pytest.mark.asyncio
    async def test_producer_timeout_error_is_ok(subscriber_client):
        mock = MagicMock()

        async def f(*args, **kwargs):
            await asyncio.sleep(0)
            mock(*args, **kwargs)
            raise asyncio.TimeoutError

        subscriber_client.pull = f
        queue = asyncio.Queue()
        producer_task = asyncio.ensure_future(
            producer(
                'fake_subscription',
                queue,
                subscriber_client,
                max_messages=1,
                metrics_client=MagicMock()
            )
        )
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        mock.assert_called_once()
        assert queue.qsize() == 0
        assert not producer_task.done()
        producer_task.cancel()

    @pytest.mark.asyncio
    async def test_producer_key_error_is_ok(subscriber_client):
        mock = MagicMock()

        async def f(*args, **kwargs):
            await asyncio.sleep(0)
            mock(*args, **kwargs)
            raise KeyError

        subscriber_client.pull = f
        queue = asyncio.Queue()
        producer_task = asyncio.ensure_future(
            producer(
                'fake_subscription',
                queue,
                subscriber_client,
                max_messages=1,
                metrics_client=MagicMock()
            )
        )
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        mock.assert_called_once()
        assert queue.qsize() == 0
        assert not producer_task.done()
        producer_task.cancel()

    @pytest.mark.asyncio
    async def test_producer_exits_on_exceptions(subscriber_client):
        mock = MagicMock()

        async def f(*args, **kwargs):
            await asyncio.sleep(0)
            mock(*args, **kwargs)
            raise RuntimeError

        subscriber_client.pull = f
        queue = asyncio.Queue()
        producer_task = asyncio.ensure_future(
            producer(
                'fake_subscription',
                queue,
                subscriber_client,
                max_messages=1,
                metrics_client=MagicMock()
            )
        )
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        mock.assert_called_once()
        assert queue.qsize() == 0
        assert producer_task.done()
        assert producer_task.exception()

    @pytest.mark.asyncio
    async def test_producer_gracefully_shutsdown(subscriber_client):
        with patch('time.perf_counter',
                   side_effect=(asyncio.CancelledError, 1)):
            queue = asyncio.Queue()
            producer_task = asyncio.ensure_future(
                producer(
                    'fake_subscription',
                    queue,
                    subscriber_client,
                    max_messages=1,
                    metrics_client=MagicMock()
                )
            )
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            assert queue.qsize() == 1
            assert not producer_task.done()
            await queue.get()
            queue.task_done()
            await asyncio.sleep(0)
            assert producer_task.done()

    @pytest.mark.asyncio
    async def test_producer_fetches_once_then_waits_for_consumer(
            subscriber_client):
        queue = asyncio.Queue()
        producer_task = asyncio.ensure_future(
            producer(
                'fake_subscription',
                queue,
                subscriber_client,
                max_messages=1,
                metrics_client=MagicMock()
            )
        )
        await asyncio.sleep(0)
        await asyncio.wait_for(queue.get(), 1.0)
        producer_task.cancel()
        queue.task_done()
        await asyncio.sleep(0)
        assert queue.qsize() == 0

    # ========
    # consumer
    # ========

    @pytest.mark.asyncio
    async def test_consumer_calls_none_means_ack(ack_deadline_cache,
                                                 message,
                                                 application_callback):
        queue = asyncio.Queue()
        ack_queue = asyncio.Queue()
        nack_queue = asyncio.Queue()
        consumer_task = asyncio.ensure_future(
            consumer(
                queue,
                application_callback,
                ack_queue,
                ack_deadline_cache,
                1,
                nack_queue,
                MagicMock()
            )
        )
        await queue.put((message, 0.0))
        await asyncio.sleep(0)
        consumer_task.cancel()
        result = await asyncio.wait_for(ack_queue.get(), 1)
        assert result == 'ack_id'
        application_callback.assert_called_once()
        assert queue.qsize() == 0
        assert nack_queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_consumer_tasks_limited_by_pool_size(ack_deadline_cache):
        queue = asyncio.Queue()
        ack_queue = asyncio.Queue()

        async def callback(mock):
            mock()
            await asyncio.sleep(10)

        mock1 = MagicMock()
        mock1.ack_id = 'ack_id'
        mock2 = MagicMock()
        mock2.ack_id = 'ack_id'
        mock3 = MagicMock()
        mock3.ack_id = 'ack_id'
        mock4 = MagicMock()
        mock4.ack_id = 'ack_id'

        asyncio.ensure_future(
            consumer(
                queue,
                callback,
                ack_queue,
                ack_deadline_cache,
                2,
                None,
                MagicMock()
            )
        )
        for m in [mock1, mock2, mock3, mock4]:
            await queue.put((m, 0.0))
        await asyncio.sleep(0.1)
        mock1.assert_called_once()
        mock2.assert_called_once()
        mock3.assert_not_called()
        assert queue.qsize() == 1
        assert ack_queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_consumer_drops_expired_messages(ack_deadline_cache,
                                                   message,
                                                   application_callback):
        f = asyncio.Future()
        f.set_result(0.0)
        ack_deadline_cache.get = MagicMock(return_value=f)

        queue = asyncio.Queue()
        ack_queue = asyncio.Queue()
        nack_queue = asyncio.Queue()
        consumer_task = asyncio.ensure_future(
            consumer(
                queue,
                application_callback,
                ack_queue,
                ack_deadline_cache,
                1,
                nack_queue,
                MagicMock()
            )
        )
        await queue.put((message, 0.0))
        await asyncio.sleep(0)
        consumer_task.cancel()
        application_callback.assert_not_called()
        assert ack_queue.qsize() == 0
        assert nack_queue.qsize() == 0
        assert queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_consumer_handles_callback_exception_no_nack(
        ack_deadline_cache, message
    ):
        queue = asyncio.Queue()
        ack_queue = asyncio.Queue()
        mock = MagicMock()

        async def f(*args):
            mock(*args)
            raise RuntimeError

        consumer_task = asyncio.ensure_future(
            consumer(
                queue,
                f,
                ack_queue,
                ack_deadline_cache,
                1,
                None,
                MagicMock()
            )
        )
        await queue.put((message, 0.0))
        await asyncio.sleep(0.1)
        consumer_task.cancel()
        mock.assert_called_once()
        assert ack_queue.qsize() == 0
        assert queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_consumer_handles_callback_exception_nack(
        ack_deadline_cache, message
    ):
        queue = asyncio.Queue()
        ack_queue = asyncio.Queue()
        nack_queue = asyncio.Queue()
        mock = MagicMock()

        async def f(*args):
            mock(*args)
            raise RuntimeError

        consumer_task = asyncio.ensure_future(
            consumer(
                queue,
                f,
                ack_queue,
                ack_deadline_cache,
                1,
                nack_queue,
                MagicMock()
            )
        )
        await queue.put((message, 0.0))
        await asyncio.sleep(0.1)
        consumer_task.cancel()
        mock.assert_called_once()
        assert ack_queue.qsize() == 0
        assert nack_queue.qsize() == 1
        assert queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_consumer_gracefull_shutdown(
        ack_deadline_cache, message
    ):
        queue = asyncio.Queue()
        ack_queue = asyncio.Queue()
        nack_queue = asyncio.Queue()
        mock = MagicMock()
        event = asyncio.Event()

        async def f(*args):
            mock(*args)
            await event.wait()

        consumer_task = asyncio.ensure_future(
            consumer(
                queue,
                f,
                ack_queue,
                ack_deadline_cache,
                1,
                nack_queue,
                MagicMock()
            )
        )
        await queue.put((message, 0.0))
        await asyncio.sleep(0.1)
        mock.assert_called_once()
        consumer_task.cancel()
        await asyncio.sleep(0.1)
        assert not consumer_task.done()
        event.set()
        await asyncio.sleep(0)
        assert ack_queue.qsize() == 1
        await ack_queue.get()
        ack_queue.task_done()
        await asyncio.sleep(0.1)
        assert consumer_task.done()

    @pytest.mark.asyncio
    async def test_consumer_gracefull_shutdown_without_pending_tasks(
        ack_deadline_cache
    ):
        queue = asyncio.Queue()
        ack_queue = asyncio.Queue()
        nack_queue = asyncio.Queue()

        consumer_task = asyncio.ensure_future(
            consumer(
                queue,
                lambda _x: None,
                ack_queue,
                ack_deadline_cache,
                1,
                nack_queue,
                MagicMock()
            )
        )
        await asyncio.sleep(0.1)
        consumer_task.cancel()
        await asyncio.sleep(0.1)
        assert consumer_task.done()

    # ========
    # acker
    # ========

    @pytest.mark.asyncio
    async def test_acker_does_ack(subscriber_client):
        queue = asyncio.Queue()
        acker_task = asyncio.ensure_future(
            acker(
                'fake_subscription',
                queue,
                subscriber_client,
                0.0,
                MagicMock()
            )
        )
        await queue.put('ack_id')
        await asyncio.sleep(0)
        acker_task.cancel()
        subscriber_client.acknowledge.assert_called_once_with(
            'fake_subscription', ack_ids=['ack_id'])
        assert queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_acker_handles_exception(subscriber_client):
        mock = MagicMock()

        async def f(*args, **kwargs):
            await asyncio.sleep(0)
            mock(*args, **kwargs)
            raise RuntimeError
        subscriber_client.acknowledge = f

        queue = asyncio.Queue()
        acker_task = asyncio.ensure_future(
            acker(
                'fake_subscription',
                queue,
                subscriber_client,
                0.0,
                MagicMock()
            )
        )
        await queue.put('ack_id')
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        mock.assert_called_once()
        assert queue.qsize() == 0
        assert not acker_task.done()
        acker_task.cancel()

    @pytest.mark.asyncio
    async def test_acker_does_batching(subscriber_client):
        queue = asyncio.Queue()
        acker_task = asyncio.ensure_future(
            acker(
                'fake_subscription',
                queue,
                subscriber_client,
                0.1,
                MagicMock()
            )
        )
        await queue.put('ack_id_1')
        await queue.put('ack_id_2')
        await asyncio.sleep(0.2)
        acker_task.cancel()
        subscriber_client.acknowledge.assert_called_once_with(
            'fake_subscription', ack_ids=['ack_id_1', 'ack_id_2'])
        assert queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_acker_batches_are_retried_next_time(subscriber_client):
        mock = MagicMock()

        async def f(*args, **kwargs):
            await asyncio.sleep(0)
            mock(*args, **kwargs)
            raise TimeoutError
        subscriber_client.acknowledge = f

        queue = asyncio.Queue()
        acker_task = asyncio.ensure_future(
            acker(
                'fake_subscription',
                queue,
                subscriber_client,
                0.1,
                MagicMock()
            )
        )
        await queue.put('ack_id_1')
        await queue.put('ack_id_2')
        await asyncio.sleep(0.3)
        acker_task.cancel()
        assert queue.qsize() == 0
        mock.assert_has_calls(
            [
                call('fake_subscription', ack_ids=['ack_id_1', 'ack_id_2']),
                call('fake_subscription', ack_ids=['ack_id_1', 'ack_id_2']),
            ]
        )

    # ========
    # nacker
    # ========

    @pytest.mark.asyncio
    async def test_nacker_does_modify_ack_deadline(subscriber_client):
        queue = asyncio.Queue()
        nacker_task = asyncio.ensure_future(
            nacker(
                'fake_subscription',
                queue,
                subscriber_client,
                0.0,
                MagicMock()
            )
        )
        await queue.put('ack_id')
        await asyncio.sleep(0)
        nacker_task.cancel()
        subscriber_client.modify_ack_deadline.assert_called_once_with(
            'fake_subscription', ack_ids=['ack_id'], ack_deadline_seconds=0)
        assert queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_nacker_handles_exception(subscriber_client):
        mock = MagicMock()

        async def f(*args, **kwargs):
            await asyncio.sleep(0)
            mock(*args, **kwargs)
            raise RuntimeError
        subscriber_client.modify_ack_deadline = f

        queue = asyncio.Queue()
        nacker_task = asyncio.ensure_future(
            nacker(
                'fake_subscription',
                queue,
                subscriber_client,
                0.0,
                MagicMock()
            )
        )
        await queue.put('ack_id')
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        mock.assert_called_once()
        assert queue.qsize() == 0
        assert not nacker_task.done()
        nacker_task.cancel()

    @pytest.mark.asyncio
    async def test_nacker_does_batching(subscriber_client):
        queue = asyncio.Queue()
        nacker_task = asyncio.ensure_future(
            nacker(
                'fake_subscription',
                queue,
                subscriber_client,
                0.1,
                MagicMock()
            )
        )
        await queue.put('ack_id_1')
        await queue.put('ack_id_2')
        await asyncio.sleep(0.2)
        nacker_task.cancel()
        subscriber_client.modify_ack_deadline.assert_called_once_with(
            'fake_subscription',
            ack_ids=['ack_id_1', 'ack_id_2'],
            ack_deadline_seconds=0)
        assert queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_nacker_batches_are_retried_next_time(subscriber_client):
        mock = MagicMock()

        async def f(*args, **kwargs):
            await asyncio.sleep(0)
            mock(*args, **kwargs)
            raise TimeoutError
        subscriber_client.modify_ack_deadline = f

        queue = asyncio.Queue()
        nacker_task = asyncio.ensure_future(
            nacker(
                'fake_subscription',
                queue,
                subscriber_client,
                0.1,
                MagicMock()
            )
        )
        await queue.put('ack_id_1')
        await queue.put('ack_id_2')
        await asyncio.sleep(0.3)
        nacker_task.cancel()
        assert queue.qsize() == 0
        mock.assert_has_calls(
            [
                call('fake_subscription',
                     ack_ids=['ack_id_1', 'ack_id_2'], ack_deadline_seconds=0),
                call('fake_subscription',
                     ack_ids=['ack_id_1', 'ack_id_2'], ack_deadline_seconds=0),
            ]
        )

    # =========
    # subscribe
    # =========

    @pytest.mark.asyncio
    async def test_subscribe_integrates_whole_chain(subscriber_client,
                                                    application_callback):
        subscribe_task = asyncio.ensure_future(
            subscribe(
                'fake_subscription',
                application_callback,
                subscriber_client,
                num_producers=1,
                max_messages_per_producer=100,
                ack_window=0.0,
                ack_deadline_cache_timeout=1000,
                num_tasks_per_consumer=1,
                enable_nack=True,
                nack_window=0.0
            )
        )
        await asyncio.sleep(0.1)
        subscribe_task.cancel()
        application_callback.assert_called()
        subscriber_client.acknowledge.assert_called_with(
            'fake_subscription', ack_ids=['ack_id'])
