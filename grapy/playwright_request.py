from .response import Response
from .core import BaseRequest
from time import time
import logging

logger = logging.getLogger(__name__)

__all__ = ['PlaywrightRequest', 'PlaywrightRequestError', 'AssignBrowser']


class PlaywrightRequestError(Exception):
    pass


class PlaywrightRequest(BaseRequest):
    '''
    the PlaywrightRequest object
    '''

    def set_browser(self, browser):
        self.browser = browser

    async def get_page(self):
        browser = getattr(self, 'browser', None)
        if browser is None:
            raise PlaywrightRequestError('browser is not initial')

        return await browser.new_page()

    async def custom_action(self, page):
        pass

    async def request(self):
        '''
        do request

        >>> req = PlaywrightRequest('http://example.com')
        >>> rsp = await req.request()
        '''
        start_time = time()

        page = await self.get_page()

        status = 101
        ct = 'text/html'
        rsp = None
        method = self.method.lower()

        def handler(res):
            nonlocal rsp, status, ct
            if res.url == self.url:
                rsp = res
                status = rsp.status
                ct = rsp.headers.get('content-type', '')

        page.on("response", handler)

        try:
            await page.goto(self.url)
            await self.custom_action(page)
            content = await page.content()
            logger.info(f'{method.upper()} {self.url} {status} {ct}')
            return Response(page.url, bytes(content, 'utf-8'), rsp, status, ct)
        finally:
            await page.close()
            self.request_time = time() - start_time


class AssignBrowser():
    '''
    >>> from playwright.async_api import async_playwright
    >>> async with async_playwright() as ctx:
    >>>     browser = await ctx.firefox.launch()
    >>>     context = await browser.new_context();
    >>>     assignBrowser = AssignBrowser(context)
    '''

    def __init__(self, browser):
        self.browser = browser

    def before_request(self, req):
        if isinstance(req, PlaywrightRequest):
            req.set_browser(self.browser)
