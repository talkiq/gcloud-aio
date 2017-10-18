import asyncio
import sys
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures.process import BrokenProcessPool


MULTIPROCESSING_POOL_SIZE = 1
# for pickling deeply nested objects, like data sci models, you
# may need to increase this from the default of 1000
RECURSION_LIMIT = 1000
THREADING_POOL_SIZE = 10


sys.setrecursionlimit(RECURSION_LIMIT)


class ProcessPool(object):

    def __init__(self, loop, *args, **kwargs):

        self.loop = loop or asyncio.get_event_loop()
        self.args = args
        self.kwargs = kwargs

        self.pool = None
        self.create_pool()

    def __getattr__(self, name):

        return getattr(self.pool, name)

    async def submit(self, fn, *args):

        pool_id = id(self.pool)

        try:

            result = await self.loop.run_in_executor(self.pool, fn, *args)
            return result

        except BrokenProcessPool:

            print('Pool broke.')
            self.create_pool(pool_id)

            # maybe do a call_later or call_soon here
            result = await self.submit(fn, *args)
            return result

    def create_pool(self, pool_id=None):

        if self.pool is None:
            print('Creating pool')
            self.pool = ProcessPoolExecutor(*self.args, **self.kwargs)
            return

        if pool_id == id(self.pool):
            print('Recreating pool.')
            self.pool = ProcessPoolExecutor(*self.args, **self.kwargs)
            return

        print('No need to recreate.')


def make_thread_pool():

    return ThreadPoolExecutor(
        max_workers=THREADING_POOL_SIZE
    )


def make_process_pool(loop=None):

    return ProcessPool(
        loop,
        max_workers=MULTIPROCESSING_POOL_SIZE
    )


pools = {
    'thread': make_thread_pool(),
    'process': make_process_pool()
}
