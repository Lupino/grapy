import asyncio
from .base_request import BaseRequest
import inspect
from .item import Item
from ..utils import logger
from .exceptions import EngineError, IgnoreRequest, ItemError, DropItem

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

    async def process(self, req):
        req.engine = self
        req = await self.process_middleware('before_process_request', req)

        rsp = await req.request()

        rsp.req = req

        rsp = await self.process_middleware('after_process_response', rsp)

        await self.process_response(rsp)

    async def process_middleware(self, name, obj):
        for mid in self.middlewares:
            if hasattr(mid, name):
                func = getattr(mid, name)
                if asyncio.iscoroutinefunction(func):
                    obj = await func(obj)
                else:
                    obj = func(obj)

        return obj

    async def process_item(self, item, pipelines=None):
        if not pipelines:
            pipelines = self.pipelines

        for pip in pipelines:
            if asyncio.iscoroutinefunction(pip.process):
                item = await pip.process(item)
            else:
                item = pip.process(item)

    async def process_response(self, rsp):
        spider_name = rsp.req.spider
        callback = rsp.req.callback
        args = list(rsp.req.callback_args)
        spider = self.get_spider(spider_name)
        func = getattr(spider, callback)
        async def process_response_item(item):
            if isinstance(item, BaseRequest):
                item.spider = spider.name
                logger.debug('Find url[{}] on requset[{}] by spider[{}]'.\
                        format(item.url, rsp.url, spider.name))

                item.group = rsp.req.group
                item.ref = rsp.url

                await self.push_req(item)
            elif isinstance(item, Item):
                await self.push_item(item)
            else:
                raise EngineError('Unknow type')

        if asyncio.iscoroutinefunction(func):
            args.append(process_response_item)
            await func(rsp, *args)
        else:
            items = func(rsp, *args)
            if items is None:
                return
            for item in items:
                await process_response_item(item)

    async def push_req(self, req):
        try:
            req = await self.process_middleware('before_push_request', req)
            await self.sched.push_req(req)
        except IgnoreRequest:
            pass
        except Exception as e:
            logger.exception(e)

    async def push_item(self, item):
        try:
            await self.sched.push_item(item)
        except (DropItem, ItemError):
            pass
        except Exception as e:
            logger.exception(e)

    async def start_request(self):
        async def push_req(req, spider):
            req.spider = spider.name
            await self.push_req(req)

        for spider in self.spiders.values():
            if asyncio.iscoroutinefunction(spider.start_request):
                await spider.start_request(lambda req: push_req(req, spider))
            else:
                for req in spider.start_request():
                    await push_req(req, spider)

    async def run(self):
        await self.start_request()
        self.sched.start()

    def start(self, forever = True):
        self.loop.create_task(self.run())
        if forever:
            self.loop.run_forever()

    def shutdown(self):
        if self.loop.is_running():
            self.loop.stop()
        else:
            self.loop.close()
