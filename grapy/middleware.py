from .core.exceptions import IgnoreRequest, RetryRequest
from .utils import after_request
import re


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
