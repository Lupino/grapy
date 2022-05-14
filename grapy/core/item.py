import json
import re
from .exceptions import ItemError
from ..utils import import_module
import base64
import hashlib

__all__ = ['Item', 'load_item']


class Item(object):
    __slots__ = ['__dict__']

    def __init__(self, payload={}):
        self.update(payload)

    def __getitem__(self, key, default=None):
        '''x.__getitem__(y) <==> x[y]'''
        return getattr(self, key, default)

    def __setitem__(self, key, val):
        '''x.__setitem__(i, y) <==> x[i]=y'''
        if isinstance(val, str):
            val = val.strip()
        setattr(self, key, val)

    def keys(self):
        '''D.keys() -> a set-like object providing a view on D's keys'''
        return self.__dict__.keys()

    def values(self):
        '''D.values() -> an object providing a view on D's values'''
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def pop(self, key, default=None):
        '''
        D.pop(k[,d]) -> v, remove specified key and
        return the corresponding value.
        If key is not found, d is returned if given,
        otherwise KeyError is raised
        '''
        return self.__dict__.pop(key, default)

    def get(self, key, default=None):
        '''D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None.'''
        return self.__dict__.get(key, default)

    def update(self, item):
        '''
        D.update([E, ]**F) -> None.
        * Update D from dict/iterable E and F.
        * If E present and has a .keys() method, does:
        *    for k in E:
        *        D[k] = E[k]
        * If E present and lacks .keys() method, does:
        *    for (k, v) in E:
        *        D[k] = v
        * In either case, this is followed by:
        *    for k in F:
        *        D[k] = F[k]
        '''
        for k, v in item.items():
            if isinstance(v, str):
                item[k] = v.strip()
        return self.__dict__.update(item)

    def copy(self):
        return self.__dict__.copy()

    def __str__(self):
        return json.dumps(self.__dict__, indent=2)

    def __bytes__(self):
        cls = self.__class__
        name = re.search("'([^']+)'", str(cls)).group(1)
        data = json.dumps(self.__dict__)
        return bytes(f'{name}${data}', 'utf-8')

    def get_hash(self):
        h = hashlib.sha256()
        h.update(bytes(self))
        return str(base64.urlsafe_b64encode((h.digest())), 'UTF-8').strip('=')


def load_item(payload):
    '''load the Item'''
    if isinstance(payload, bytes):
        payload = str(payload, 'utf-8')
    idx = payload.find('$')
    name = payload[:idx]
    data = json.loads(payload[idx + 1:])
    klass = import_module(name, data)
    if not isinstance(klass, Item):
        raise ItemError(f'ItemError: {name} is not instance {__name__}.Item')
    return klass
