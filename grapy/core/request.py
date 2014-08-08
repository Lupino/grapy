import json
import re
import asyncio
import aiohttp
from ..utils import logger
from urllib.parse import urljoin
from .response import Response
from .exceptions import IgnoreRequest, RetryRequest
import requests

__all__ = ['Request']

class Request(object):
    '''
    the Request object
    '''

    _keys = ['url', 'method', 'callback', 'callback_args', 'kwargs', 'spider',
            'req_id', 'group']
    _default = [{}, (), 'get', None, [], 'default']

    _json_keys = ['callback_args', 'kwargs']

    _null_char = '\x01'

    __slots__ = ['url', 'method', 'callback', 'callback_args', 'kwargs',
                 'spider', 'unique', 'req_id', 'ref', 'group', 'engine']

    def __init__(self, url, method='get',
            callback='parse', callback_args = [], **kwargs):
        self.url = re.sub('#.+', '', url)
        self.method = method
        self.callback = callback
        self.callback_args = callback_args
        self.kwargs = kwargs
        self.spider = 'default'
        self.unique = True
        self.req_id = 0
        self.ref = 0
        self.group = 0
        self.engine = None

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
        return bytes(self._null_char.join(map(_pack, self._keys)), 'utf-8')

    def unpack(self, payload):
        '''
        unpack the Request payload
        '''
        payload = str(payload, 'utf-8')
        payload = payload.split(self._null_char)
        payload = dict(zip(self._keys, payload))

        for json_key in self._json_keys:
            if payload[json_key]:
                payload[json_key] = json.loads(payload[json_key])

        return payload

    def __bytes__(self):
        return self.pack()

    @classmethod
    def build(cls, payload):
        '''
        build a Request
        '''
        req = Request('')
        payload = req.unpack(payload)
        for key, val in payload.items():
            if val:
                if hasattr(req, key):
                    setattr(req, key, val)
        return req

    @asyncio.coroutine
    def request(self):
        '''
        do request default timeout is 300s

        >>> req = Request('http://example.com')
        >>> rsp = yield from req.request()
        '''
        method = self.method.lower()
        headers = self.engine.headers.copy()

        headers.update(self.kwargs.get('headers', {}))

        kwargs = {
            'connector': aiohttp.TCPConnector(loop=self.engine.loop, conn_timeout=300)
        }
        kwargs.update(self.kwargs.copy())
        kwargs['headers'] = headers

        url = self.url

        try:
            rsp = yield from aiohttp.request(method, url, **kwargs)
            ct = rsp.headers.get('content-type', '')
            logger.info('Request: {} {} {} {}'.format(method.upper(), url, rsp.status, ct))
            yield from asyncio.sleep(5)
            if rsp.status >= 400 and rsp.status < 500:
                raise IgnoreRequest(url)
            if rsp.status == 200:
                if re.search('html|json|text|xml|rss', ct, re.I):
                    content = yield from rsp.read()
                    rsp.close()
                    return Response(urljoin(url, rsp.url), content, rsp)
                else:
                    raise IgnoreRequest(url)
            else:
                logger.error('Request fail: {} {}'.format(url, rsp.status))
                raise RetryRequest(url)

        except (aiohttp.IncompleteRead, aiohttp.BadStatusLine) as exc:
            logger.error(str(exc) + ': ' + url)
            rsp = requests.get(url, **kwargs)
            ct = rsp.headers['content-type']
            if rsp.status_code >= 400 and rsp.status_code < 500:
                raise IgnoreRequest(url)
            if rsp.status_code == 200:
                if re.search('html|json|text|xml|rss', ct, re.I):
                    return Response(urljoin(url, rsp.url), rsp.content, rsp)
                else:
                    raise IgnoreRequest(url)
            else:
                logger.error('Request fail: {} {}'.format(url, rsp.status_code))
                raise RetryRequest(url)
        except aiohttp.errors.OsConnectionError as e:
            logger.error("Request fail OsConnectionError: {} {}".format(url, e))
            raise IgnoreRequest(url)

        except ValueError as e:
            logger.error("Request fail ValueError: {} {}".format(url, e))
            raise IgnoreRequest(url)
