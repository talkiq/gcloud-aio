"""
An asynchronous task manager for Google Appengine Task Queues
"""
import asyncio
import concurrent.futures
import datetime
import logging
import multiprocessing
import time
import traceback

import aiohttp
import requests
from gcloud.aio.taskqueue.error import FailFastError
from gcloud.aio.taskqueue.taskqueue import API_ROOT
from gcloud.aio.taskqueue.taskqueue import LOCATION
from gcloud.aio.taskqueue.taskqueue import TaskQueue
from gcloud.aio.taskqueue.utils import backoff
from gcloud.aio.taskqueue.utils import decode


log = logging.getLogger(__name__)


def log_future_exception(fut):
    e = fut.exception()
    if e:
        log.exception(e)


class LeaseManager:
    def __init__(self, event, executor, headers, task, lease_seconds):
        # pylint: disable=too-many-arguments
        self.event = event
        self.executor = executor
        self.future = None

        # TODO: token rotation
        self.headers = headers
        self.task = task
        self.lease_seconds = lease_seconds

    def start(self, loop=None):
        loop = loop or asyncio.get_event_loop()
        self.future = loop.run_in_executor(
            self.executor, self.autorenew, self.event, self.headers, self.task,
            self.lease_seconds)
        return self

    async def stop(self):
        if not self.future:
            return
        self.event.set()
        try:
            return await self.future
        except concurrent.futures.process.BrokenProcessPool:
            # if the ProcessPool broke, hopefully it did so before renewing
            return self.task

    @staticmethod
    def autorenew(event, headers, task, lease_seconds):
        url = f'{API_ROOT}/{task["name"]}:renewLease'
        body = {
            'leaseDuration': f'{lease_seconds}s',
            'responseView': 'FULL',
        }

        while not event.is_set():
            for _ in range(int(lease_seconds // 2) * 10):
                time.sleep(0.1)
                if event.is_set():
                    break

            body['scheduleTime'] = task['scheduleTime']

            try:
                resp = requests.post(url, headers=headers, json=body)
                resp.raise_for_status()
                task = resp.json()
            except requests.exceptions.HTTPError as e:
                log.error('failed to autorenew task: %s', task['name'])
                try:
                    log.error(resp.json())
                except ValueError:
                    log.error(resp.text())
                log.exception(e)
                event.set()
            except Exception as e:  # pylint: disable=broad-except
                log.error('failed to autorenew task: %s', task['name'])
                log.exception(e)
                event.set()

        return task


class TaskManager:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, project, service_file, taskqueue, worker,
                 backoff_base=2, backoff_factor=1.1, backoff_max_value=60,
                 batch_size=10, deadletter_insert_function=None,
                 lease_seconds=10, location=LOCATION,
                 max_concurrency=100, retry_limit=None, session=None,
                 token=None):
        # pylint: disable=too-many-arguments,too-many-locals
        self.worker = worker

        self.backoff = backoff(base=backoff_base, factor=backoff_factor,
                               max_value=backoff_max_value)
        self.batch_size = max(batch_size, 1)
        self.deadletter_insert_function = deadletter_insert_function
        self.lease_seconds = lease_seconds
        self.retry_limit = retry_limit

        self.executor = concurrent.futures.ProcessPoolExecutor(max_concurrency)
        self.manager = multiprocessing.Manager()
        self.semaphore = asyncio.BoundedSemaphore(max_concurrency)
        self.tq = TaskQueue(project, service_file, taskqueue,
                            location=location, session=session, token=token)

        self.running = False

    @staticmethod
    def get_session():
        connector = aiohttp.TCPConnector(enable_cleanup_closed=True,
                                         force_close=True, limit_per_host=1)
        return aiohttp.ClientSession(connector=connector, conn_timeout=10,
                                     read_timeout=10)

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
                    async with self.get_session() as session:
                        task_lease = await self.tq.lease(
                            lease_seconds=self.lease_seconds,
                            num_tasks=self.batch_size, session=session)
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
                f = asyncio.ensure_future(self.process(task))
                f.add_done_callback(log_future_exception)

            await asyncio.sleep(0)

    async def process(self, task):
        name = task['name']
        payload = decode(task['pullMessage']['payload'])

        autorenew = None
        try:
            autorenew = LeaseManager(self.manager.Event(), self.executor,
                                     await self.tq.headers(), task,
                                     self.lease_seconds).start()
        # N.B. theoretically, we should only catch
        # concurrent.futures.process.BrokenProcessPool but I've come across
        # several other errors (such as EOFError and ConnectionRefusedError)
        # and at this point I'm sick of having to update the blacklist. If we
        # get an exception while creating a LeaseManager, that's enough for me
        # to be reasonably sure the pool is broken without needing proof.
        except Exception as e:  # pylint: disable=broad-except
            log.error('process pool broke, quitting TaskManager')
            log.exception(e)
            self.running = False
            return

        try:
            async with self.semaphore, self.get_session() as session:
                log.info('processing task: %s', name)

                try:
                    await self.worker(payload)
                except FailFastError as e:
                    log.error('[FailFastError] failed to process task: %s',
                              name)
                    log.exception(e)

                    if autorenew is not None:
                        task = await autorenew.stop()
                    await self.tq.delete(name, session=session)
                    await self.fail(task, payload, e)
                    return
                except Exception as e:  # pylint: disable=broad-except
                    log.error('failed to process task: %s', name)
                    log.exception(e)

                    if autorenew is not None:
                        task = await autorenew.stop()

                    tries = task['status']['attemptDispatchCount']
                    if self.retry_limit is None or tries < self.retry_limit:
                        await self.tq.cancel(task, session=session)
                        return

                    log.warning('exceeded retry_limit, failing task')
                    await self.tq.delete(name, session=session)
                    await self.fail(task, payload, e)
                    return

                log.info('successfully processed task: %s', name)
                if autorenew is not None:
                    task = await autorenew.stop()
                await self.tq.ack(task, session=session)
        except Exception as e:  # pylint: disable=broad-except
            log.exception(e)
        finally:
            if autorenew is not None:
                await autorenew.stop()

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
        self.executor.shutdown(wait=True)
