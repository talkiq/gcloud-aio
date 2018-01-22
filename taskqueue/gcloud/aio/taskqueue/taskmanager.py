"""
An asynchronous task manager for Google Appengine Task Queues
"""
import asyncio
import concurrent.futures
import contextlib
import datetime
import logging
import sys
import traceback

from gcloud.aio.taskqueue.error import FailFastError
from gcloud.aio.taskqueue.taskqueue import LOCATION
from gcloud.aio.taskqueue.taskqueue import TaskQueue
from gcloud.aio.taskqueue.utils import backoff
from gcloud.aio.taskqueue.utils import decode


log = logging.getLogger(__name__)


class TaskManager:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, project, service_file, taskqueue, worker,
                 backoff_base=2, backoff_factor=1.1, backoff_max_value=60,
                 batch_size=1, deadletter_insert_function=None,
                 lease_seconds=10, location=LOCATION,
                 max_concurrency=sys.maxsize, retry_limit=None, session=None,
                 token=None):
        # pylint: disable=too-many-arguments,too-many-locals
        self.worker = worker

        self.backoff = backoff(base=backoff_base, factor=backoff_factor,
                               max_value=backoff_max_value)
        self.batch_size = max(batch_size, 1)
        self.deadletter_insert_function = deadletter_insert_function
        self.lease_seconds = lease_seconds
        self.retry_limit = retry_limit

        self.semaphore = asyncio.BoundedSemaphore(max_concurrency)
        self.tq = TaskQueue(project, service_file, taskqueue,
                            location=location, session=session, token=token)

        self.running = False
        self.tasks = dict()

    async def autorenew(self, name):
        try:
            while True:
                # N.B. the below is an interuptible version of:
                #     await asyncio.sleep(self.lease_seconds / 2)
                for _ in range(int(self.lease_seconds // 2)):
                    await asyncio.sleep(1)

                task = await self.tq.renew(self.tasks[name],
                                           lease_seconds=self.lease_seconds)
                self.tasks[name] = task
        except (concurrent.futures.CancelledError,
                concurrent.futures.TimeoutError):
            pass
        except Exception as e:  # pylint: disable=broad-except
            log.error('failed to autorenew task: %s', name)
            log.exception(e)

    async def fail(self, task, payload, exception):
        if not self.deadletter_insert_function:
            return

        properties = {
            'error': str(exception),
            'generation': None,
            'metageneration': None,
            'payload': payload,
            'time_created': datetime.datetime.now(datetime.timezone.utc),
            'traceback': traceback.format_exc(),
            'update': None,
        }

        await self.deadletter_insert_function(task['name'], properties)

    async def poll(self):
        while self.running:
            # only lease new tasks when we have room
            async with self.semaphore:
                task_lease = None
                try:
                    task_lease = await self.tq.lease(
                        lease_seconds=self.lease_seconds,
                        num_tasks=self.batch_size)
                except concurrent.futures.CancelledError:
                    return
                except concurrent.futures.TimeoutError:
                    pass
                except Exception as e:  # pylint: disable=broad-except
                    log.exception(e)

            if not task_lease:
                await asyncio.sleep(next(self.backoff))
                continue

            tasks = task_lease.get('tasks')
            log.info('grabbed %d tasks', len(tasks))

            for task in tasks:
                asyncio.ensure_future(self.process(task))

    async def process(self, task):
        name = task['name']
        payload = decode(task['pullMessage']['payload'])
        self.tasks[name] = task

        autorenew = asyncio.ensure_future(self.autorenew(name))

        async with self.semaphore:
            log.info('processing task: %s', name)

            try:
                await self.worker(payload)
            except FailFastError as e:
                log.error('[FailFastError] failed to process task: %s', name)
                log.exception(e)

                autorenew.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await autorenew

                task = self.tasks[name]
                del self.tasks[name]

                await self.tq.delete(task)
                await self.fail(task, payload, e)
                return
            except Exception as e:  # pylint: disable=broad-except
                log.error('failed to process task: %s', name)
                log.exception(e)

                autorenew.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await autorenew

                task = self.tasks[name]
                del self.tasks[name]

                tries = task['status']['attemptDispatchCount']
                if self.retry_limit is None or tries < self.retry_limit:
                    await self.tq.cancel(task)
                    return

                log.warning('exceeded retry_limit, failing task')
                await self.tq.delete(name)
                await self.fail(task, payload, e)
                return

            log.info('successfully processed task: %s', name)

            autorenew.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await autorenew

            task = self.tasks[name]
            del self.tasks[name]

            await self.tq.ack(task)

    def start(self):
        if self.running:
            return self

        log.info('starting task manager')
        self.running = True
        asyncio.ensure_future(self.poll())

        return self

    def stop(self):
        log.info('stopping task manager')
        self.running = False
