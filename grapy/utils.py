from importlib import import_module as _import_module
import logging

__all__ = ['import_module', 'import_pipelines', 'import_middlewares',
           'import_spiders', "logger"]

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

def import_pipelines(pipelines):
    '''
    import module from a list like::

        [
            {'class_or_method:index': args},
            {'class_or_method:index': kwargs},
            {'class_or_method:index': None}
        ]

    the index is a number or string for order
    '''
    retval = []
    for module_name, values in pipelines.items():
        args = []
        kwargs = {}
        idx = module_name.find(':')
        order = 0
        if idx > -1:
            order = int(module_name[idx+1:])
            module_name = module_name[:idx]
        tp = type(values)
        if tp == tuple or tp == list:
            args = values
        elif tp == dict:
            keys = values.keys()
            if 'args' in keys or 'kwargs' in keys:
                args = values.get('args', ())
                kwargs = values.get('kwargs', {})
            else:
                kwargs = values

        elif values is not None:
            args.append(values)

        retval.append((import_module(module_name, *args, **kwargs), order))

    retval = [ret[0] for ret in sorted(retval, key=lambda x: x[1])]

    return retval

import_middlewares = import_pipelines
import_spiders = import_pipelines

