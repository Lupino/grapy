from .request import Request

__all__ = ['BaseSpider']

class BaseSpider(object):
    '''The BaseSpider, all the spider recommend to extends this'''

    __slots__ = ['name', 'start_urls']

    def __init__(self, name=None, start_urls=[]):
        '''
        @name: the spider name, unique

        @start_urls: the start request url
        '''
        self.name = name
        self.start_urls = start_urls

    def start_request(self):
        '''you can rewrite it for custem start request'''
        for url in self.start_urls:
            req = Request(url)
            req.unique = False
            yield req

    def parse(self, response):
        '''
        the default spider parse function.
        you must rewrite on a sub class.
        '''
        raise NotImplementedError('you must rewrite at sub class')
