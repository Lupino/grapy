import asyncio

__all__ = ["BaseScheduler"]


class BaseScheduler(object):

    def __init__(self):
        self.engine = None
        self.is_running = False
        self.locker = asyncio.Lock()

    async def push_req(self, req):
        '''
        push the request
        '''
        raise NotImplementedError('you must rewrite at sub class')

    async def push_item(self, item):
        await self.submit_item(item)

    async def submit_req(self, req):
        await self.engine.process(req)

    async def submit_item(self, item):
        await self.engine.process_item(item)
