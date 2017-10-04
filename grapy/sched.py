from .core import BaseScheduler
import hashlib
import asyncio
import re
re_url = re.compile('^https?://[^/]+')

__all__ = ['Scheduler']

def hash_url(url):
    h = hashlib.sha1()
    h.update(bytes(url, 'utf-8'))
    return h.hexdigest()

class Scheduler(BaseScheduler):
    def __init__(self, storage = {}, queue=[], max_tasks=5):
        BaseScheduler.__init__(self)
        self._storage = storage
        self._queue = queue
        self._sem = asyncio.Semaphore(max_tasks)

    def push_req(self, req):
        if not re_url.match(req.url):
            return
        key = hash_url(req.url)
        if req.unique and key in self._storage:
            return

        self._queue.insert(0, req)
        self._storage[key] = {'key': key, 'req': req, 'crawled': False}

        self.start()

    def run(self):
        while True:
            if len(self._queue) == 0:
                break

            req = self._queue.pop()
            yield from self._sem.acquire()
            task = self.engine.loop.create_task(self.submit_req(req))
            task.add_done_callback(lambda t: self._sem.release())

        self.is_running = False

    def submit_req(self, req):
        try:
            yield from BaseScheduler.submit_req(self, req)
        except:
            pass
        key = hash_url(req.url)
        self._storage[key] = {'key': key, 'req': req, 'crawled': True}

    def submit_item(self, item):
        try:
            yield from BaseScheduler.submit_item(self, item)
        except:
            pass
