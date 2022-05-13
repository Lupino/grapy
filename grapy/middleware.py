from .core.exceptions import IgnoreRequest, RetryRequest
from .utils import after_request
import re
from bloom_filter2 import BloomFilter


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
        key = req.get_hash()
        if req.unique and key in self.filter:
            raise IgnoreRequest()

        self.filter.add(key)
