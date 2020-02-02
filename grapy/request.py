import re
import aiohttp
from .utils import logger
from urllib.parse import urljoin
from .response import Response
from .core import BaseRequest
from .core.exceptions import IgnoreRequest, RetryRequest
import requests
from time import time

__all__ = ['Request']

class Request(BaseRequest):
    '''
    the Request object
    '''

    async def _aio_request(self):
        method = self.method.lower()
        kwargs = self.kwargs.copy()

        url = self.url

        start_time = time()

        async with aiohttp.ClientSession() as client:
            async with client.request(method, url, **kwargs) as rsp:
                ct = rsp.headers.get('content-type', '')
                logger.info('Request: {} {} {} {}'.format(method.upper(),
                                                          url, rsp.status, ct))
                if rsp.status >= 400 and rsp.status < 500:
                    raise IgnoreRequest(url)
                if rsp.status == 200:
                    if re.search('html|json|text|xml|rss', ct, re.I):
                        content = await rsp.read()
                        rsp.close()
                        self.request_time = time() - start_time
                        return Response(urljoin(url, str(rsp.url)), content, rsp)
                    else:
                        raise IgnoreRequest(url)
                else:
                    logger.error('Request fail: {} {}'.format(url, rsp.status))
                    raise RetryRequest(url)

    def _request(self):
        url = self.url
        method = self.method.lower()
        kwargs = self.kwargs.copy()
        func = getattr(requests, method)
        rsp = func(url, **kwargs)
        ct = rsp.headers['content-type']
        if rsp.status_code >= 400 and rsp.status_code < 500:
            raise IgnoreRequest(url)
        if rsp.status_code == 200:
            if re.search('html|json|text|xml|rss', ct, re.I):
                return Response(urljoin(url, rsp.url), rsp.content, rsp)
            else:
                raise IgnoreRequest(url)
        else:
            logger.error('Request fail: {} {}'.format(url, rsp.status_code))
            raise RetryRequest(url)

    async def request(self):
        '''
        do request

        >>> req = Request('http://example.com')
        >>> rsp = await req.request()
        '''
        start_time = time()

        try:
            return (await self._aio_request())
        except (aiohttp.http_exceptions.BadHttpMessage, aiohttp.http_exceptions.BadStatusLine, ValueError) as exc:
            logger.error(str(exc) + ': ' + self.url)
            start_time = time()
            return self._request()
        except aiohttp.client_exceptions.ClientError as e:
            logger.error("Request fail OsConnectionError: {} {}".format(self.url, e))
            raise IgnoreRequest(self.url)

        self.request_time = time() - start_time
