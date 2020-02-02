from .core import BaseScheduler
import hashlib
import asyncio
import re
from .utils import logger
from .core.exceptions import IgnoreRequest, RetryRequest
re_url = re.compile('^https?://[^/]+')

__all__ = ['Scheduler']

def hash_url(url):
    h = hashlib.sha1()
    h.update(bytes(url, 'utf-8'))
    return h.hexdigest()

class Scheduler(BaseScheduler):
    def __init__(self, max_tasks=5, auto_shutdown=True):
        BaseScheduler.__init__(self)
        self._storage = {}
        self._queue = []
        self._sem = asyncio.Semaphore(max_tasks)
        self.tasks = []
        self.auto_shutdown = auto_shutdown

    async def push_req(self, req):
        if not re_url.match(req.url):
            return
        key = hash_url(req.url)
        if req.unique and key in self._storage:
            return

        self._queue.insert(0, req)
        self._storage[key] = True

        self.start()

    async def run(self):
        while True:
            if len(self._queue) == 0:
                break

            req = self._queue.pop()
            await self._sem.acquire()
            task = self.engine.loop.create_task(self.submit_req(req))
            task.add_done_callback(lambda t: self._sem.release())
            task.add_done_callback(lambda t: self.tasks.remove(t))
            self.tasks.append(task)

        self.is_running = False

        if self.auto_shutdown:
            await asyncio.gather(*self.tasks)
            if not self.is_running:
                self.engine.shutdown()

    async def submit_req(self, req):
        try:
            await BaseScheduler.submit_req(self, req)
            key = hash_url(req.url)
        except IgnoreRequest:
            pass
        except RetryRequest:
            req.unique = False
            await self.push_req(req)
        except Exception as e:
            logger.exception(e)
