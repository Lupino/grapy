import asyncio
from .request import Request
import inspect
from .item import Item
from ..logging import logger
from .exceptions import EngineError

__all__ = ['Engine']

class Engine(object):

    __slots__ = ['pipelines', 'spiders', 'middlewares', 'sched', 'loop']

    def __init__(self, loop=None):
        self.pipelines = []
        self.spiders = {}
        self.middlewares = []
        self.sched = None
        self.loop = loop
        if not self.loop:
            self.loop = asyncio.get_event_loop()

    def set_spiders(self, spiders):
        self.spiders = {}
        if isinstance(spiders, dict):
            for name, spider in spiders.items():
                self.spiders[name] = spider

        else:
            self.add_spiders(spiders)

    def add_spiders(self, spiders):
        for spider in spiders:
            self.add_spider(spider)

    def add_spider(self, spider):
        if spider.name in self.spiders.keys():
            raise EngineError('Spider[%s] is already exists'%spider.name)
        self.spiders[spider.name] = spider

    def remove_spider(self, spider_name):
        self.spiders.pop(spider_name)

    def get_spider(self, name):
        spider = self.spiders.get(name)
        if spider:
            return spider
        else:
            raise EngineError('Spider[%s] is not found'%name)

    def set_pipelines(self, pipelines):
        self.pipelines = pipelines

    def set_middlewares(self, middlewares):
        self.middlewares = middlewares

    def set_sched(self, sched):
        self.sched = sched
        self.sched.engine = self

    @asyncio.coroutine
    def process(self, req):
        req = yield from self.process_middleware('before_process_request', req)

        rsp = yield from req.request()

        rsp.req = req

        rsp = yield from self.process_middleware('after_process_response', rsp)

        yield from self.process_response(rsp)

    @asyncio.coroutine
    def process_middleware(self, name, obj):
        for mid in self.middlewares:
            if hasattr(mid, name):
                func = getattr(mid, name)
                obj = func(obj)
                if isinstance(obj, asyncio.Future) or inspect.isgenerator(obj):
                    obj = yield from obj

        return obj

    @asyncio.coroutine
    def process_item(self, item, pipelines=None):
        if not pipelines:
            pipelines = self.pipelines

        for pip in pipelines:

            item = pip.process(item)
            if isinstance(item, asyncio.Future) or inspect.isgenerator(item):
                item = yield from item

    @asyncio.coroutine
    def process_response(self, rsp):
        spider_name = rsp.req.spider
        callback = rsp.req.callback
        args = rsp.req.callback_args
        spider = self.get_spider(spider_name)
        func = getattr(spider, callback)
        items = func(rsp, *args)
        if items is None:
            return
        for item in items:
            if isinstance(item, Request):
                item.spider = spider.name
                logger.info('Find url[{}] on requset[{}] by spider[{}]'.\
                        format(item.url, rsp.url, spider.name))

                item.group = rsp.req.group
                item.ref = rsp.req.req_id

                yield from self.push_req(item)
            elif isinstance(item, Item):
                yield from self.push_item(item)
            else:
                raise EngineError('Unknow type')

    @asyncio.coroutine
    def push_req(self, req, middleware=True):
        if middleware:
            req = yield from self.process_middleware('before_push_request', req)

        req = self.sched.push_req(req)
        if isinstance(req, asyncio.Future) or inspect.isgenerator(req):
            req = yield from req

    @asyncio.coroutine
    def push_item(self, item):
            ret = self.sched.push_item(item)
            if isinstance(ret, asyncio.Future) or inspect.isgenerator(ret):
                ret = yield from ret

    def start_request(self):
        for spider in self.spiders.values():
            for req in spider.start_request():
                req.spider = spider.name
                yield from self.push_req(req)

    def run(self):
        yield from self.start_request()
        self.sched.start()

    def start(self):
        asyncio.Task(self.run())
        self.loop.run_forever()

    def shutdown(self):
        self.loop.close()
