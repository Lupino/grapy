import aiohttp
from urllib.parse import urljoin
from .response import Response
from .core import BaseRequest
from .core.exceptions import RetryRequest
import requests
from time import time
import logging
import anyio

__all__ = ['Request']

logger = logging.getLogger(__name__)


class Request(BaseRequest):
    '''
    the Request object
    '''

    async def _aio_request(self):
        method = self.method.lower()
        kwargs = self.kwargs.copy()

        connector = getattr(self, 'connector', None)

        proxy = getattr(self, 'proxy', None)
        if proxy:
            kwargs['proxy'] = proxy

        url = self.url

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(connector=connector,
                                         timeout=timeout) as client:
            async with client.request(method, url, **kwargs) as rsp:
                ct = rsp.headers.get('content-type', '')
                status = rsp.status
                rsp_url = urljoin(url, str(rsp.url))
                logger.info(f'{method.upper()} {url} {status} {ct}')
                content = await rsp.read()
                rsp.close()
                return Response(rsp_url, content, rsp, status, ct)

    def _request(self):
        url = self.url
        method = self.method.lower()
        kwargs = self.kwargs.copy()
        proxy = getattr(self, 'proxy', None)
        if proxy:
            kwargs['proxies'] = {
                'http': proxy,
                'https': proxy,
            }
        func = getattr(requests, method)
        rsp = func(url, timeout=self.timeout, **kwargs)
        ct = rsp.headers['content-type']
        status = rsp.status_code
        logger.info(f'{method.upper()} {url} {status} {ct}')
        rsp_url = urljoin(url, str(rsp.url))
        return Response(rsp_url, rsp.content, rsp, status, ct)

    def set_cached(self, content, content_type):
        self.cached = Response(self.url, content, None, 200, content_type)

    async def request(self):
        '''
        do request

        >>> req = Request('http://example.com')
        >>> rsp = await req.request()
        '''
        start_time = time()

        try:
            cached = getattr(self, 'cached', None)
            if cached:
                return cached

            if self.sync:
                return await anyio.to_thread.run_sync(self._request)

            return await self._aio_request()
        except aiohttp.client_exceptions.ClientError as e:
            logger.error(f"OsConnectionError: {self.url} {e}")
            raise RetryRequest()
        except Exception as exc:
            logger.error(str(exc) + ': ' + self.url)
            start_time = time()
            return await anyio.to_thread.run_sync(self._request)
        finally:
            self.request_time = time() - start_time
