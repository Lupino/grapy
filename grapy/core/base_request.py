import json
import re
import hashlib
import base64

__all__ = ['BaseRequest']


class BaseRequest(object):
    '''The BaseRequest, all the request recommend to extends this'''

    _keys = [
        'url', 'method', 'callback', 'callback_args', 'kwargs', 'spider',
        'req_id', 'group', 'sync', 'timeout'
    ]
    _default = [{}, (), 'get', None, [], 'default']

    _json_keys = ['callback_args', 'kwargs']

    _null_char = '\x01'

    __slots__ = [
        'url', 'method', 'callback', 'callback_args', 'kwargs', 'spider',
        'unique', 'req_id', 'group', 'engine', 'request_time', 'sync',
        'timeout'
    ]

    def __init__(self,
                 url,
                 method='get',
                 callback='parse',
                 callback_args=[],
                 spider=None,
                 sync=False,
                 timeout=60,
                 **kwargs):
        self.url = re.sub('#.+', '', url)
        self.method = method
        self.callback = callback
        self.callback_args = callback_args
        self.kwargs = kwargs
        self.spider = spider
        self.unique = True
        self.req_id = 0
        self.group = 0
        self.engine = None
        self.request_time = 0
        self.sync = sync
        self.timeout = timeout

    def pack(self):
        '''
        pack the Request object on bytes
        '''

        def _pack(key):
            val = getattr(self, key, '')
            if val not in self._default:
                if key in self._json_keys:
                    val = json.dumps(val)
            else:
                val = ''
            if not isinstance(val, str):
                val = str(val)
            return val

        return self._null_char.join(map(_pack, self._keys))

    def unpack(self, payload):
        '''
        unpack the Request payload
        '''
        if isinstance(payload, bytes):
            payload = str(payload, 'utf-8')
        payload = payload.split(self._null_char)
        payload = dict(zip(self._keys, payload))

        for json_key in self._json_keys:
            if payload[json_key]:
                payload[json_key] = json.loads(payload[json_key])

        return payload

    def __bytes__(self):
        return bytes(self.pack(), 'utf-8')

    @classmethod
    def build(cls, payload):
        '''
        build a Request
        '''
        req = cls('')
        payload = req.unpack(payload)
        for key, val in payload.items():
            if val:
                if hasattr(req, key):
                    setattr(req, key, val)
        return req

    async def request(self):
        '''
        do request

        >>> req = Request('http://example.com')
        >>> rsp = await req.request()
        '''
        raise NotImplementedError('you must rewrite at sub class')

    def get_hash(self):
        h = hashlib.sha256()
        h.update(bytes(self))
        return str(base64.urlsafe_b64encode((h.digest())), 'UTF-8').strip('=')
