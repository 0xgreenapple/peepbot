import asyncio
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Callable


class Executor:
    def __init__(
            self, loop: asyncio.AbstractEventLoop,
            max_workers=None):

        self.loop = loop
        self.max_workers: int = max_workers
        if self.max_workers is None:
            self.max_workers = multiprocessing.cpu_count()
        self.thread_pool_executor = ThreadPoolExecutor(
            max_workers=self.max_workers)

    async def execute(self, function: Callable, *args, **kwargs):
        result = await self.loop.run_in_executor(
            self.thread_pool_executor, lambda: function(*args, **kwargs))
        return result

    async def shutdown(self):
        self.thread_pool_executor.shutdown()