from importlib import import_module as _import_module
import logging
import glob
import os.path
from .core.base_spider import BaseSpider

__all__ = [
    'import_module', 'import_spiders', 'middleware', 'make_spider',
    'before_push_request', 'before_request', 'after_request'
]

logger = logging.getLogger(__name__)


def import_module(module_name, *args, **kwargs):
    '''
    import the module and init it
    '''
    logger.debug('import module[%s]' % module_name)
    idx = module_name.rfind('.')
    module = _import_module(module_name[:idx])
    obj = getattr(module, module_name[idx + 1:])
    return obj(*args, **kwargs)


def fixed_module_name(module_name):
    if os.path.isfile(module_name):
        if module_name.endswith('.py'):
            module_name = module_name[:-3]

        if module_name.startswith('./'):
            module_name = module_name[2:]

        return module_name.replace('/', '.')

    return module_name


def import_spiders(spider_path,
                   module_prefix=None,
                   pattern='*',
                   ignore_cls_names=['BaseSpider']):
    spiders = []

    for path in glob.glob(os.path.join(spider_path, pattern + '.py')):
        if path.endswith('__init__.py'):
            continue

        module_path = fixed_module_name(path)
        if module_prefix:
            spider_name = os.path.basename(path)[:-3]
            module_path = module_prefix + spider_name

        logger.error(f'import spider[{module_path}]')
        module = _import_module(module_path)
        ignore = getattr(module, 'ignore', False)

        if ignore:
            continue

        for cls_name in dir(module):
            if cls_name in ignore_cls_names:
                continue

            spiderclass = getattr(module, cls_name, None)
            if isinstance(spiderclass, BaseSpider):
                spiders.append(spiderclass)
                logger.error(f'import spider[{spiderclass.name}]')
            elif cls_name.endswith('Spider'):
                spider = spiderclass()
                if spider.name is None:
                    spider.name = cls_name[:-6]
                spiders.append(spider)
                logger.error(f'import spider[{spider.name}]')

    return spiders


class Middleware(object):
    __slots__ = ['before_request', 'after_request', 'before_push_request']


def middleware(name):
    def _middleware(func):
        m = Middleware()
        setattr(m, name, func)
        return m

    return _middleware


before_push_request = middleware('before_push_request')
before_request = middleware('before_request')
after_request = middleware('after_request')


def make_spider(func_name=None, start_urls=[]):
    '''Make a spider
    @param func_name the spider name
    @param start_urls Request list
    '''
    def _spider(func):
        name = func_name
        if name is None:
            name = func.__name__
        s = BaseSpider(name)
        s.parse = func

        def start_request():
            return start_urls

        s.start_request = start_request

        return s

    return _spider
