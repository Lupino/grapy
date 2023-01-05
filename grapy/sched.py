from .core import BaseScheduler
from .core.exceptions import IgnoreRequest, RetryRequest
from .core.item import load_item
from asyncio_pool import AioPool
from .request import Request
from asyncio import sleep
import logging
from time import time

__all__ = ['Scheduler', 'PeriodicScheduler']

logger = logging.getLogger(__name__)


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
            req.unique = False
            await self.push_req(req)
            logger.exception(e)

    async def join(self):
        await self._pool.join()


class PeriodicScheduler(BaseScheduler):

    async def push_req(self, req):
        key = req.get_hash()
        data = bytes(req)
        for i in range(self._retry_count):
            await sleep(i * 0.01)
            try:
                await self._worker.submit_job('submit_req', key, data)
                break
            except Exception as e:
                logger.exception(e)

    async def submit_req(self, job):
        req = Request.build(job.workload)
        try:
            await BaseScheduler.submit_req(self, req)
        except IgnoreRequest:
            pass
        except RetryRequest:
            return await job.sched_later(job.payload.count + 10, 1)
        except Exception as e:
            logger.exception(e)
            return await job.sched_later(job.payload.count + 10, 1)

        await job.done()

    async def push_item(self, item):
        key = item.get_hash()
        data = bytes(item)
        for i in range(self._retry_count):
            await sleep(i * 0.01)
            try:

                sched_at = int(time())
                later = getattr(item, 'later', None)
                if isinstance(later, int):
                    sched_at += later

                await self._worker.submit_job('submit_item',
                                              key,
                                              data,
                                              sched_at=sched_at)
                break
            except Exception as e:
                logger.exception(e)

    async def submit_item(self, job):
        item = load_item(job.workload)
        await BaseScheduler.submit_item(self, item)
        await job.done()

    async def init(self,
                   worker,
                   submit_req=True,
                   submit_item=True,
                   retry_count=10):
        self._worker = worker
        self._retry_count = retry_count
        if submit_req:
            await self._worker.add_func('submit_req', self.submit_req)
        if submit_item:
            await self._worker.add_func('submit_item', self.submit_item)
