from .core import BaseScheduler
from .utils import logger
from .core.exceptions import IgnoreRequest, RetryRequest
from asyncio_pool import AioPool

__all__ = ['Scheduler']


class Scheduler(BaseScheduler):
    def __init__(self, size=10):
        BaseScheduler.__init__(self)
        self._pool = AioPool(size=size)

    async def push_req(self, req):
        self._pool.spawn_n(self.submit_req(req))

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
