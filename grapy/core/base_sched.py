import asyncio

__all__ = ["BaseScheduler"]

class BaseScheduler(object):
    def __init__(self):
        self.engine = None
        self.is_running = False

    def push_req(self, req):
        '''
        push the request
        '''
        raise NotImplementedError('you must rewrite at sub class')

    def push_item(self, item):
        yield from self.submit_item(item)

    def submit_req(self, req):
        yield from self.engine.process(req)

    def submit_item(self, item):
        yield from self.engine.process_item(item)

    @asyncio.coroutine
    def run(self):
        '''
        run the scheduler
        '''
        raise NotImplementedError('you must rewrite at sub class')

    def start(self):
        if self.is_running:
            return

        self.is_running = True
        return asyncio.Task(self.run())
