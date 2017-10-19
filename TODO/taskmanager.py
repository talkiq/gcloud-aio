"""
An asynchronous task manager for Google Appengine Task Queues
"""
import asyncio
import base64
import collections
import datetime
import json
import random
import traceback
import types

from config import config
from utils.aio import call_later
from utils.aio import complete
from utils.aio import fire
from utils.aio import maybe_async
from utils.b64 import clean_b64decode
from utils.log import log
from utils.misc import backoff

from .astate import AwaitableState
from .astate import make_stepper


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

        super(self.__class__, self).__init__()

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


async def _default_worker(payload):

    await asyncio.sleep(1.0)
    raise Exception('No worker.')


def deserialize_task(task):

    data = clean_b64decode(task['payloadBase64']).decode('utf-8')

    return json.loads(data)


class RollingAverage(collections.deque):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

    @property
    def avg(self):

        if len(self) == 0:
            return 0

        return sum(self) / len(self)


class TaskManager(object):

    def __init__(self, task_queue, worker, deadletter_upsert=None,
                 lease_seconds=10, poll_interval=1, max_poll_interval=30.0,
                 max_concurrency=20, batch_size=1, retry_limit=50,
                 session=None):

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
        log.info('{}'.format(stats))

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

        # TODO: this stepper + AwaitableState abstraction has hardly been worth
        # it, and I regret it
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

        id = task['id']

        log.info('processing task: {}'.format(id))

        self.auto_renew(id, payload)

        processed = fire(self.worker, payload)

        def done(future):

            try:
                result = future.result()
            except Exception as ex:
                fail(ex)
                return

            object_id, size = result
            duration = self.let_go_of(id)
            fire(self.delete, id)
            self.completed_tasks += 1

            self.sizes.append(size)

            if duration is not None:
                self.durations.append(duration)

            log.info('Finished {{id: {}, size: {}, duration: {}s}}'.format(
                object_id,
                size,
                duration
            ))

        def fail(ex):

            self.failed += 1

            log.error('Worker did not complete task {} for {}: {}, "{}"'.format(
                id,
                payload['name'],
                ''.join(traceback.format_tb(ex.__traceback__)),
                ex
            ))

            log.error('Current retry_count: {}'.format(task['retry_count']))

            if not self.deadletter_upsert:
                self.let_go_of(id)
                return

            fail_fast = isinstance(ex, FailFastError)

            if int(task['retry_count']) < self.retry_limit and not fail_fast:
                self.let_go_of(id)
                return

            log.info('Moving task {} to dead letter queue'.format(id))

            do_insert = fire(self.flunk_to_store, id, payload, ex)

            @do_insert.add_done_callback
            def after_insert(future):

                self.let_go_of(id)

        processed.add_done_callback(done)

    def auto_renew(self, id, payload):

        self.hold_onto(id, payload)

        call_later(
            self.lease_seconds / 2,
            self.renew,
            id, self.lease_seconds / 2
        )

        return self

    def hold_onto(self, id, payload):

        self.tasks_processing[id] = (payload, datetime.datetime.now())

        return self

    def let_go_of(self, id):

        if id not in self.tasks_processing:
            return

        start = self.tasks_processing[id][1]

        try:
            del self.tasks_processing[id]
        except:
            pass

        return (datetime.datetime.now() - start).total_seconds()

    async def delete(self, id):

        try:
            result = await self.queue.delete_task(id)
            return result
        except Exception as ex:
            log.error('Could not delete task: {}'.format(
                traceback.format_exc())
            )

            return False

    async def renew(self, id, renew_rate=0):

        if id not in self.tasks_processing.keys():
            # log.info('Task id {} is no longer renewable.'.format(id))
            return

        if renew_rate:

            call_later(
                renew_rate,
                self.renew,
                id, renew_rate
            )

        log.info('RENEW task {}'.format(id))

        try:
            result = await self.queue.renew_task(id, self.lease_seconds)
            if result:
                log.info('LEASE extended for {}'.format(id))
            else:
                log.error('LEASE was not extended for {}'.format(id))

        except Exception as ex:
            log.error('Could not renew lease for task {}: {}'.format(id, ex))
            self.let_go_of(id)

    async def lease(self):

        tasks = []

        try:
            tasks = await self.queue.lease_task(
                lease_seconds=self.lease_seconds,
                num_tasks=self.batch_size
            )
        except Exception as ex:
            log.error('Could not lease: {}'.format(traceback.format_exc()))

        if tasks:
            log.info('Got {} tasks.'.format(len(tasks)))

        return tasks

    async def insert(self, payload, new_id=None):

        result = await self._insert(
            self.queue, payload, new_id=new_id
        )

        return result

    async def flunk_to_store(self, task_id, payload, ex):

        result = await self._store(payload, ex)

        if result:
            log.info(
                'Successfully flunked task {} to datastore'.format(
                    task_id
                )
            )
            self.flunked_tasks += 1
            fire(self.delete, task_id)

        return result

    async def _store(self, payload, ex):

        properties = self.get_exception_properties(payload, ex)
        name = payload.get('name')

        try:
            await self.deadletter_upsert(name, properties)

            return True
        except Exception as ex:
            log.error(
                'Could not insert payload into datastore: {} Task: {}'.format(
                    ex,
                    payload
                )
            )

            return False

    def get_exception_properties(self, payload, ex):

        name = payload['name']

        call_id, side, link, file = name.split('/')

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
                properties['timeCreated'], config.gcloud.timestamp_format
            )

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


async def smoke(project, service_file, kind_name):

    import aiohttp

    with aiohttp.ClientSession() as session:

        result = None
        raise Exception('Not implemented.')

    print('success: {}'.format(len(result)))


if __name__ == '__main__':

    import sys

    from utils.aio import fire

    args = sys.argv[1:]

    if not args or args[0] != 'smoke':
        exit(1)

    project = 'talkiq-integration'
    service_file = 'service-integration.json'
    kind_name = 'some_kind'

    loop = asyncio.get_event_loop()

    task = fire(
        smoke,
        project,
        service_file,
        kind_name
    )

    loop.run_until_complete(task)
