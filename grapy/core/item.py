import json
import re
from .exceptions import ItemError
from ..utils import import_module
from uuid import uuid1 as uuid

__all__ = ['Item', 'load_item', 'dump_item']

class Item(object):
    _null_char = '\x01'

    _extra_field = {'name': 'extra', 'type': 'json'}

    _fields =  [
        {'name': 'extra', 'type': 'json'}
    ]

    __slots__ = ['__dict__']

    def __init__(self, payload = {}):

        if self._extra_field not in self._fields:
            self._fields.append(self._extra_field)

        if not isinstance(payload, dict):
            payload = self.unpack(payload)

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
        D.pop(k[,d]) -> v, remove specified key and return the corresponding value.
        If key is not found, d is returned if given, otherwise KeyError is raised
        '''
        return self.__dict__.pop(key, default)

    def get(self, key, default=None):
        '''D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None.'''
        return self.__dict__.get(key, default)

    def update(self, item):
        '''
        D.update([E, ]**F) -> None.
        * Update D from dict/iterable E and F.
        * If E present and has a .keys() method, does:     for k in E: D[k] = E[k]
        * If E present and lacks .keys() method, does:     for (k, v) in E: D[k] = v
        * In either case, this is followed by: for k in F: D[k] = F[k]
        '''
        for k, v in item.items():
            if isinstance(v, str):
                item[k] = v.strip()
        return self.__dict__.update(item)

    def copy(self):
        return self.__dict__.copy()

    def pack(self):
        '''D.pack() -> a bytes object. pack item'''
        payload = dict(self)
        keys = list(map(lambda x: x['name'], self._fields))
        tps = list(map(lambda x: x['type'], self._fields))
        tps = dict(zip(keys, tps))

        none_keys = list(filter(lambda x: not payload[x], payload.keys()))
        list(map(payload.pop, none_keys))

        other_keys = filter(lambda x : x not in keys, payload.keys())
        other = dict(zip(other_keys, map(lambda x: payload[x], other_keys)))

        payload[self._extra_field['name']] = other

        def _pack(key):
            val = payload.get(key, '')
            tp = tps[key]

            if val:
                if tp == 'json':
                    val = json.dumps(val)
            else:
                val = ''
            if not isinstance(val, str):
                val = str(val)
            return val
        return self._null_char.join(map(_pack, keys))

    def unpack(self, payload):
        '''unpack item'''
        if isinstance(payload, bytes):
            payload = str(payload, 'utf-8')

        keys = list(map(lambda x: x['name'], self._fields))
        tps = list(map(lambda x: x['type'], self._fields))
        tps = dict(zip(keys, tps))

        payload = payload.split(self._null_char)

        def _unpack(pack):
            key, val = pack
            tp = tps[key]
            if not val:
                return key, val
            if tp == 'json':
                val = json.loads(val)
            elif tp == 'int':
                val = int(val)
            elif tp == 'float':
                val = float(val)
            elif tp == 'bool':
                val = bool(val)
            return key, val

        payload = dict(map(_unpack, zip(keys, payload)))

        if payload.get(self._extra_field['name']):
            other = payload.pop(self._extra_field['name'])
            if isinstance(other, dict):
                payload.update(other)

        return payload

    def __str__(self):
        return json.dumps(self.__dict__, indent=2)

    def __bytes__(self):
        return bytes(self.pack(), 'utf-8')

    @property
    def unique(self):
        return str(uuid())

NULL_CHAR = '\x02\x00\x00'
def dump_item(klass, *args, **kwargs):
    '''dump the Item'''
    cls = klass.__class__
    cls_name = re.search("'([^']+)'", str(cls)).group(1)
    if not isinstance(klass, Item):
        raise ItemError(
                'ItemError: %s is not instance crawl.core.item.Item'%cls_name)
    retval = NULL_CHAR.join([cls_name, klass.pack()])
    return retval

def load_item(string):
    '''load the Item'''
    cls_name, data = string.split(NULL_CHAR)
    klass = import_module(cls_name, data)
    if not isinstance(klass, Item):
        raise ItemError(
                'ItemError: %s is not instance crawl.core.item.Item'%cls_name)
    return klass
