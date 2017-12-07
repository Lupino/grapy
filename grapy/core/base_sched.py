import asyncio

__all__ = ["BaseScheduler"]

class BaseScheduler(object):
    def __init__(self):
        self.engine = None
        self.is_running = False

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

    async def run(self):
        '''
        run the scheduler
        '''
        raise NotImplementedError('you must rewrite at sub class')

    def start(self):
        if self.is_running:
            return

        self.is_running = True
        return self.engine.loop.create_task(self.run())
