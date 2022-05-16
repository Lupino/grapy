from .core.exceptions import IgnoreRequest, RetryRequest
from .utils import after_request
import re
from bloom_filter2 import BloomFilter
from asyncio import sleep


@after_request
def check_response_status(rsp):
    if rsp.status >= 400 and rsp.status < 500:
        raise IgnoreRequest()
    if rsp.status >= 300:
        raise RetryRequest()


@after_request
def check_response_content_type(rsp):
    if not re.search('html|json|text|xml|rss', rsp.content_type, re.I):
        raise IgnoreRequest()


re_url = re.compile('^https?://[^/]+')


class RequestFilter():
    def __init__(self, filter=None):
        if filter is None:
            filter = BloomFilter(max_elements=10000, error_rate=0.1)

        self.filter = filter

    def before_push_request(self, req):
        if not re_url.match(req.url):
            raise IgnoreRequest()

        if not req.unique:
            return

        key = req.get_hash()
        if key in self.filter:
            raise IgnoreRequest()

        self.filter.add(key)


class PeriodicRequestFilter(RequestFilter):
    async def before_push_request(self, req):
        if not req.unique:
            return
        key = req.get_hash()

        for retry_count in range(self._retry_count):
            await sleep(retry_count * 0.01)
            exists = b'True'
            try:
                exists = await self._worker.run_job('bloom_filter', key)
            except Exception:
                continue

            if exists == b'True':
                raise IgnoreRequest()
            if exists == b'False':
                break

    async def bloom_filter(self, job):
        exists = job.name in self.filter
        self.filter.add(job.name)

        await job.done(str(exists))

    async def init(self, worker, retry_count=10, filter=True):
        self._worker = worker
        self._retry_count = retry_count
        if filter:
            await self._worker.add_func('bloom_filter', self.bloom_filter)
