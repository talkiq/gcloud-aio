"""
An asynchronous task manager for Google Appengine Task Queues
"""
import asyncio
import collections
import datetime
import json
import logging
import random
import traceback

from gcloud.aio.core.aio import call_later
from gcloud.aio.core.aio import fire
from gcloud.aio.core.astate import AwaitableState
from gcloud.aio.core.astate import make_stepper
from gcloud.aio.taskqueue.utils import decode


TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

log = logging.getLogger(__name__)


def backoff(base=2, factor=1, max_value=None):

    """Generator for exponential decay.

    The Google docs warn to back off from polling their API if there is no
    work available in a task queue. So we does.

    # modified from:
    # https://github.com/litl/backoff/blob/master/backoff.py

        base: the mathematical base of the exponentiation operation
        factor: factor to multiply the exponentation by.
        max_value: The maximum value to yield. Once the value in the
             true exponential sequence exceeds this, the value
             of max_value will forever after be yielded.
    """

    n = 0

    # initial backoff delay is nothing
    yield 0

    while True:

        a = factor * base ** n

        if max_value is None or a < max_value:
            yield a
            n += 1
        else:
            yield max_value - random.random() * max_value / 10


class FailFastError(Exception):

    """
    Raise this error if the task item cannot be processed, and you want to
    handle it (by, for instance, transferring it to a failed tasks location)

    :source - a string to identity what process the error originated from,
    could be the source file name, or the name of the service

    :title - short text

    :desc - long text, if necessary

    :data - a dict of any pertinent data, if any

    """

    def __init__(self, source='unknown', title='', desc='', data=None):

        super().__init__()

        self.source = source
        self.title = title
        self.desc = desc
        self.timestamp = str(datetime.datetime.now())
        self.data = data or {}

    def __str__(self):

        return '{} ({}) {}: {}'.format(
            self.timestamp,
            self.title,
            self.desc,
            self.data
        )

    def __state__(self):

        return dict(
            source=self.source,
            title=self.title,
            desc=self.desc,
            timestamp=self.timestamp,
            data=self.data
        )


async def _default_worker(_payload):

    await asyncio.sleep(1.0)
    raise Exception('No worker.')


def deserialize_task(task):

    data = decode(task['payloadBase64']).decode('utf-8')

    return json.loads(data)


class RollingAverage(collections.deque):

    @property
    def avg(self):

        if not self:
            return 0

        return sum(self) / len(self)


class TaskManager:
    # pylint: disable=too-many-instance-attributes

    def __init__(self, task_queue, worker, deadletter_upsert=None,
                 lease_seconds=10, poll_interval=1, max_poll_interval=30.0,
                 max_concurrency=20, batch_size=1, retry_limit=50):
        # pylint: disable=too-many-arguments

        self.queue = task_queue
        self.worker = worker
        self.deadletter_upsert = deadletter_upsert

        self.lease_seconds = lease_seconds
        self.poll_interval = poll_interval
        self.max_poll_interval = max_poll_interval
        self.backoff = backoff(base=1.1, max_value=max_poll_interval)
        self.max_concurrency = max_concurrency
        self.batch_size = max(batch_size, 1)
        self.retry_limit = retry_limit

        self.running = False
        self.completed_tasks = 0
        self.created_at = datetime.datetime.now()
        self.failed = 0  # raw failures
        self.flunked_tasks = 0  # failures that were sent to dead letter store
        self.tasks_processing = {}
        self.state = None
        self.durations = RollingAverage(maxlen=100)
        self.sizes = RollingAverage(maxlen=100)

        call_later(1, self.print_stats)

    @property
    def no_tasks(self):

        return len(self.tasks_processing.keys())

    @property
    def ids(self):

        return sorted(self.tasks_processing.keys())

    def start(self):

        if self.running:
            return self

        log.info('Starting task manager.')
        self.running = True
        fire(self.poll)

        return self

    def stop(self):

        log.info('Stopping task manager.')
        self.running = False

    async def get_stats(self):

        stats = await self.queue.get_stats()

        return {
            'task_queue': stats,
            'instance': {
                'tasks': {
                    'completed': self.completed_tasks,
                    'flunked': self.flunked_tasks,
                    'failed': self.failed,
                    'progressing': self.no_tasks,
                    'rolling_duration': self.durations.avg,
                    'rolling_size': self.sizes.avg
                },
                'created_at': str(self.created_at),
                'state': getattr(self.state, 'name', None)
            }
        }

    async def print_stats(self):

        stats = await self.get_stats()
        log.info(stats)

        call_later(10, self.print_stats)

    async def poll(self):

        """
        poll a task queue for work at self.poll_interval
        """

        state = None
        args = None

        default_step = self.try_to_lease
        state_step = {'LEASE': self.after_lease}
        stepper = make_stepper(default_step, state_step, name='TM')

        # TODO: migrate away from stepper + AwaitableState
        while self.running:
            state, args = await stepper(state, args)
            self.state = state

    def after_lease(self, tasks):

        if not tasks:

            interval = self.poll_interval + next(self.backoff)

            return AwaitableState(
                'NO_TASKS',
                asyncio.sleep(interval)
            )

        # reset the backoff
        self.backoff = backoff(base=1.1, max_value=self.max_poll_interval)

        for task in tasks:

            payload = deserialize_task(task)
            self.process_task(task, payload)

        return AwaitableState(
            'PROCESS',
            asyncio.sleep(self.poll_interval),
            data=len(tasks)
        )

    def try_to_lease(self):

        if self.no_tasks >= self.max_concurrency:

            return AwaitableState(
                'MAX_CONCURRENCY',
                asyncio.sleep(1.0)  # check every second
            )

        return AwaitableState(
            'LEASE',
            self.lease()
        )

    def process_task(self, task, payload):

        id_ = task['id']

        log.info('processing task: %s', id_)

        self.auto_renew(id_, payload)

        processed = fire(self.worker, payload)

        def done(future):

            try:
                result = future.result()
            except Exception as ex:  # pylint: disable=broad-except
                fail(ex)
                return

            object_id, size = result
            duration = self.let_go_of(id_)
            fire(self.delete, id_)
            self.completed_tasks += 1

            self.sizes.append(size)

            if duration is not None:
                self.durations.append(duration)

            log.info('Finished {{id: %s, size: %s, duration: %ds}}', object_id,
                     size, duration)

        def fail(ex):

            self.failed += 1

            log.error('Worker did not complete task %s for %s', id_,
                      payload['name'])
            log.exception(ex)

            log.error('Current retry_count: %d', task['retry_count'])

            if not self.deadletter_upsert:
                self.let_go_of(id_)
                return

            fail_fast = isinstance(ex, FailFastError)

            if int(task['retry_count']) < self.retry_limit and not fail_fast:
                self.let_go_of(id_)
                return

            log.info('Moving task %s to dead letter queue', id_)

            do_insert = fire(self.flunk_to_store, id_, payload, ex)

            @do_insert.add_done_callback
            def after_insert(_future):  # pylint: disable=unused-variable

                self.let_go_of(id_)

        processed.add_done_callback(done)

    def auto_renew(self, id_, payload):

        self.hold_onto(id_, payload)

        half_lease = self.lease_seconds / 2
        call_later(half_lease, self.renew, id_, half_lease)

        return self

    def hold_onto(self, id_, payload):

        self.tasks_processing[id_] = (payload, datetime.datetime.now())

        return self

    def let_go_of(self, id_):

        if id_ not in self.tasks_processing:
            return

        start = self.tasks_processing[id_][1]

        try:
            del self.tasks_processing[id_]
        except Exception:  # pylint: disable=broad-except
            pass

        return (datetime.datetime.now() - start).total_seconds()

    async def delete(self, id_):

        try:
            result = await self.queue.delete_task(id_)
            return result
        except Exception as e:  # pylint: disable=broad-except
            log.error('Could not delete task')
            log.exception(e)

            return False

    async def renew(self, id_, renew_rate=0):

        if id_ not in self.tasks_processing.keys():
            # log.info('Task id %s is no longer renewable.', id_)
            return

        if renew_rate:

            call_later(renew_rate, self.renew, id_, renew_rate)

        log.info('RENEW task %s', id_)

        try:
            result = await self.queue.renew_task(id_, self.lease_seconds)
            if result:
                log.info('LEASE extended for %s', id_)
            else:
                log.error('LEASE was not extended for %s', id_)

        except Exception as e:  # pylint: disable=broad-except
            log.error('Could not renew lease for task %s', id_)
            log.exception(e)

            self.let_go_of(id_)

    async def lease(self):

        tasks = []

        try:
            tasks = await self.queue.lease_task(
                lease_seconds=self.lease_seconds,
                num_tasks=self.batch_size
            )
        except Exception as e:  # pylint: disable=broad-except
            log.error('Could not lease tasks')
            log.exception(e)

        if tasks:
            log.info('Got %d tasks.', len(tasks))

        return tasks

    async def insert(self, payload):

        result = await self.queue.insert_task(payload)

        return result

    async def flunk_to_store(self, task_id, payload, ex):

        result = await self._store(payload, ex)

        if result:
            log.info('Successfully flunked task %s to datastore', task_id)
            self.flunked_tasks += 1
            fire(self.delete, task_id)

        return result

    async def _store(self, payload, ex):

        properties = self.get_exception_properties(payload, ex)
        name = payload.get('name')

        try:
            await self.deadletter_upsert(name, properties)

            return True
        except Exception as e:  # pylint: disable=broad-except
            log.error('Could not insert payload into datastore: %s Task: %s',
                      e, payload)

            return False

    def get_exception_properties(self, payload, ex):

        name = payload['name']

        call_id, side, link, _file = name.split('/')

        properties = {
            'call_id': call_id,
            'link': link,
            'side': side
        }

        properties.update(
            {p: payload.get(p, None) for p in [
                'timeCreated',
                'bucket',
                'metageneration',
                'generation',
                'updated'
            ]}
        )

        # a timestampValue
        if properties['timeCreated']:
            properties['time_created'] = datetime.datetime.strptime(
                properties['timeCreated'], TIMESTAMP_FORMAT)

            del properties['timeCreated']

        trace = ''.join(traceback.format_tb(ex.__traceback__))

        if len(trace) > 1000:
            trace = trace[:500] + '...snip...' + trace[-500:]

        properties.update({
            'source_queue': self.queue.task_queue,
            'error': str(ex),
            'traceback': trace
        })

        return properties
