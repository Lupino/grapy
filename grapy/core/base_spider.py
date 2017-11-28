__all__ = ['BaseSpider']

class BaseSpider(object):
    '''The BaseSpider, all the spider recommend to extends this'''

    name = None
    start_urls = []

    def __init__(self, name=None, start_urls=[]):
        '''
        @name: the spider name, unique

        @start_urls: the start request url
        '''
        if not self.name:
            self.name = name
        if not self.start_urls:
            self.start_urls = start_urls

    def start_request(self):
        '''you must rewrite it for a start request'''
        raise NotImplementedError('you must rewrite at sub class')

    def parse(self, response):
        '''
        the default spider parse function.
        you must rewrite on a sub class.
        '''
        raise NotImplementedError('you must rewrite at sub class')
