from .core import BaseScheduler
import hashlib
import asyncio
import re
from .utils import logger
from .core.exceptions import IgnoreRequest, RetryRequest
from asyncio_pool import AioPool

re_url = re.compile('^https?://[^/]+')

__all__ = ['Scheduler']


def hash_url(url):
    h = hashlib.sha256()
    h.update(bytes(url, 'utf-8'))
    return h.hexdigest()


class Scheduler(BaseScheduler):
    def __init__(self, size=10):
        BaseScheduler.__init__(self)
        self._storage = {}
        self._pool = AioPool(size = size)

    async def push_req(self, req):
        if not re_url.match(req.url):
            return
        key = hash_url(req.url)
        if req.unique and key in self._storage:
            return

        await self._pool.spawn(self.submit_req(req))
        self._storage[key] = True

    async def submit_req(self, req):
        try:
            await BaseScheduler.submit_req(self, req)
        except IgnoreRequest:
            pass
        except RetryRequest:
            req.unique = False
            await self.push_req(req)
        except Exception as e:
            logger.exception(e)

    async def join(self):
        await self._pool.join()
