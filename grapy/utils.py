from importlib import import_module as _import_module
import logging
import glob
import os.path

__all__ = ['import_module', 'logger', 'import_spiders']

logger = logging.getLogger('grapy')

def import_module(module_name, *args, **kwargs):
    '''
    import the module and init it
    '''
    logger.debug('import module[%s]'%module_name)
    idx = module_name.rfind('.')
    module = _import_module(module_name[:idx])
    obj = getattr(module, module_name[idx+1:])
    return obj(*args, **kwargs)


def fixed_module_name(module_name):
    if os.path.isfile(module_name):
        if module_name.endswith('.py'):
            module_name = module_name[:-3]

        if module_name.startswith('./'):
            module_name = module_name[2:]

        return module_name.replace('/', '.')

    return module_name


def import_spiders(spider_path, module_prefix=None, ignore_cls_names=['BaseSpider']):
    spiders = []

    for path in glob.glob(os.path.join(spider_path, '*.py')):
        if path.endswith('__init__.py'):
            continue

        module_path = fixed_module_name(path)
        if module_prefix:
            spider_name = os.path.basename(path)[:-3]
            module_path = module_prefix + spider_name

        module = _import_module(module_path)
        ignore = getattr(module, 'ignore', False)

        if ignore:
            continue

        for cls_name in dir(module):
            if not cls_name.endswith('Spider'):
                continue

            if cls_name in ignore_cls_names:
                continue

            spiderclass = getattr(module, cls_name, None)
            if spiderclass:
                spider = spiderclass()
                if spider.name is None:
                    spider.name = cls_name[:-6]
                spiders.append(spider)
            else:
                logging.error('{}.{} invalid.'.format(module_path,
                                                      cls_name))

    return spiders
