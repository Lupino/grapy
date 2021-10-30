from .core import BaseScheduler
import hashlib
import re
from .utils import logger
from .core.exceptions import IgnoreRequest, RetryRequest
from asyncio_pool import AioPool
from bloom_filter2 import BloomFilter

re_url = re.compile('^https?://[^/]+')

__all__ = ['Scheduler']


def hash_req(req):
    h = hashlib.sha256()
    h.update(bytes(req))
    return h.hexdigest()


class Scheduler(BaseScheduler):
    def __init__(self,
                 size=10,
                 filter=BloomFilter(max_elements=10000, error_rate=0.1)):
        BaseScheduler.__init__(self)
        self._pool = AioPool(size=size)
        self._filter = filter

    async def push_req(self, req):
        if not re_url.match(req.url):
            return
        key = hash_req(req)
        if req.unique and key in self._filter:
            return

        self._pool.spawn_n(self.submit_req(req))
        self._filter.add(key)

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
