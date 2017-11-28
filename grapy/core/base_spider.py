__all__ = ['BaseSpider']

class BaseSpider(object):
    '''The BaseSpider, all the spider recommend to extends this'''

    name = None

    def __init__(self, name=None):
        '''
        @name: the spider name, unique
        '''
        if not self.name:
            self.name = name

    def start_request(self):
        '''you mast rewrite it for a start request'''
        return []

    def parse(self, response):
        '''
        the default spider parse function.
        you must rewrite on a sub class.
        '''
        raise NotImplementedError('you must rewrite at sub class')
