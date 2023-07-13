import asyncio
from .base_request import BaseRequest
from .item import Item
from .exceptions import EngineError, IgnoreRequest, ItemError, DropItem
import logging
from time import time

__all__ = ['Engine']

logger = logging.getLogger(__name__)


class Engine(object):

    __slots__ = ['pipelines', 'spiders', 'middlewares', 'sched', 'event_fun']

    def __init__(self):
        self.pipelines = []
        self.spiders = {}
        self.middlewares = []
        self.sched = None
        self.event_fun = []

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
            raise EngineError('Spider[%s] is already exists' % spider.name)
        self.spiders[spider.name] = spider

    def remove_spider(self, spider_name):
        self.spiders.pop(spider_name)

    def get_spider(self, name):
        spider = self.spiders.get(name)
        if spider:
            return spider
        else:
            raise EngineError('Spider[%s] is not found' % name)

    def set_pipelines(self, pipelines):
        self.pipelines = pipelines

    def set_middlewares(self, middlewares):
        self.middlewares = middlewares

    def set_sched(self, sched):
        self.sched = sched
        self.sched.engine = self

    def add_event(self, func):
        self.event_fun.append(func)

    async def emit(self, event_name, *args, **kwargs):
        for event in self.event_fun:
            ret = event(event_name, *args, **kwargs)
            if asyncio.iscoroutine(ret):
                await ret

    async def process(self, req):
        start_time = time()
        err = None
        events = []
        try:
            await self._process(req)
        except Exception as e:
            err = e

        events.append(
            dict(
                event_name='process',
                spider=req.spider,
                spent=time() - start_time,
                exc=err,
            ))

        await self.emit('events', events=events[:])

        if err is not None:
            raise err

    async def _process(self, req, events=[]):
        req.engine = self
        req = await self.process_middleware('before_request', req)

        rsp = await req.request()

        events.append(
            dict(
                event_name='request',
                spider=req.spider,
                spent=req.request_time,
                status=rsp.status,
                data_bytes=len(rsp.content),
            ))

        rsp.req = req

        rsp = await self.process_middleware('after_request', rsp)

        await self.process_response(rsp, events)

    async def process_middleware(self, name, obj):
        for mid in self.middlewares:
            if hasattr(mid, name):
                func = getattr(mid, name)
                new_obj = func(obj)
                if asyncio.iscoroutine(new_obj):
                    new_obj = await new_obj

                if new_obj is not None:
                    obj = new_obj

        return obj

    async def process_item(self, item, pipelines=None):
        if not pipelines:
            pipelines = self.pipelines

        for pip in pipelines:
            new_item = None
            if hasattr(pip, 'process'):
                new_item = pip.process(item)
            elif str(type(pip)) == "<class 'function'>":
                new_item = pip(item)

            if asyncio.iscoroutine(new_item):
                new_item = await new_item
            if new_item is not None:
                item = new_item

    async def process_response(self, rsp, events=[]):
        spider_name = rsp.req.spider
        callback = rsp.req.callback
        args = list(rsp.req.callback_args)
        spider = self.get_spider(spider_name)
        func = getattr(spider, callback)

        async def process_response_item(item):
            if len(events) > 100:
                await self.emit('events', events=events[:])
                events.clear()

            if isinstance(item, BaseRequest):
                if item.spider is None:
                    item.spider = spider.name

                item.group = rsp.req.group
                item.ref = rsp.url

                await self.push_req(item)
                events.append(
                    dict(
                        event_name='push_req',
                        spider=spider.name,
                        count=1,
                    ))
            elif isinstance(item, Item):
                await self.push_item(item)
                events.append(
                    dict(
                        event_name='push_item',
                        spider=spider.name,
                        count=1,
                    ))
            elif isinstance(item, list):
                for sub in item:
                    await process_response_item(sub)
            else:
                raise EngineError('Unknow type')

        if asyncio.iscoroutinefunction(func):
            async for item in func(rsp, *args):
                await process_response_item(item)
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
            req.unique = False
            await self.push_req(req)

        for spider in self.spiders.values():
            reqs = spider.start_request()
            if asyncio.iscoroutine(reqs):
                reqs = await reqs

            for req in reqs:
                await push_req(req, spider)

    async def start(self):
        await self.start_request()
