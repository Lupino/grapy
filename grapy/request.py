import httpx
from urllib.parse import urljoin
from .response import Response
from .core import BaseRequest
from time import time
import logging
import anyio

__all__ = ['Request']

logger = logging.getLogger(__name__)


class Request(BaseRequest):
    '''
    the Request object
    '''

    def _prepare_client(self, cls):
        transport = getattr(self, 'transport', None)
        proxies = getattr(self, 'proxy', None)
        timeout = int(self.timeout)
        return cls(transport=transport, timeout=timeout, proxies=proxies)

    def _prepare_request(self, client):
        method = self.method.lower()
        kwargs = self.kwargs.copy()
        url = self.url
        return client.request(method, url, **kwargs)

    def _parse_response(self, rsp):
        method = self.method.lower()
        url = self.url

        ct = rsp.headers.get('content-type', '')
        status = rsp.status_code
        rsp_url = urljoin(url, str(rsp.url))
        spider = self.spider
        logger.info(f'{method.upper()} {url} {status} {ct} {spider}')
        content = rsp.content
        return Response(rsp_url, content, rsp, status, ct, rsp.headers)

    async def _async_request(self):
        self.sync = False
        async with self._prepare_client(httpx.AsyncClient) as client:
            rsp = await self._prepare_request(client)
            return self._parse_response(rsp)

    def _request(self):
        self.sync = True
        with self._prepare_client(httpx.Client) as client:
            rsp = self._prepare_request(client)
            return self._parse_response(rsp)

    def set_cached(self, content, content_type):
        self.cached = Response(self.url, content, None, 200, content_type, {})

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

            return await self._async_request()
        except Exception as exc:
            cls = str(exc.__class__)[8:-2]
            logger.error(cls + str(exc) + ': ' + self.url)
            start_time = time()
            return await anyio.to_thread.run_sync(self._request)
        finally:
            self.request_time = time() - start_time
