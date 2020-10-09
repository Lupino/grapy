import re
from bs4 import BeautifulSoup
import json

RE_XML = re.compile('<\?xml.+encoding=["\']([^\'"]+?)["\'].+\?>', re.I)
RE_HTML = re.compile('<meta.+charset=["\']([^\'"]+?)[\'"].+>', re.I)

__all__ = ['Response']

class Response(object):

    __slots__ = ['url', 'raw', 'encoding', 'content', '_soup', 'req', 'headers']

    def __init__(self, url, content, raw):
        self.raw = raw
        self.url = url
        self._soup = None
        self.encoding = None
        self.content = content
        self.req = None
        self.headers = raw.headers

    @property
    def text(self):
        'return the unicode document'
        content = self.content
        if self.encoding:
            return str(content, self.encoding, errors = 'ignore')

        charset = self._get_charset(content)
        if charset:
            self.encoding = charset
            return str(content, charset, errors = 'ignore')
        else:
            try:
                self.encoding = 'GBK'
                return str(content, 'GBK')
            except UnicodeDecodeError:
                self.encoding = 'UTF-8'
                return str(content, 'UTF-8', errors = 'ignore')

    def json(self):
        '''return json document, maybe raise'''
        data = self.content
        data = json.loads(data.decode('utf-8'))
        return data


    @property
    def soup(self):
        '''return the instance of BeautifulSoup'''
        if self._soup is None:
            text = self.text
            self._soup = BeautifulSoup(text, 'html.parser')
        return self._soup

    def _get_charset(self, content):

        def map_charset(charset):
            if charset:
                charset = charset.upper()
                if charset == 'GB2312':
                    charset = 'GBK'
            return charset

        ct = ''
        try:
            ct = self.headers.get('content-type', '').lower()
        except:
            pass
        p = re.search('charset=(.+)$', ct)
        if p:
            charset = p.group(1)
            return map_charset(charset)

        content = str(content, 'utf-8', errors='ignore')
        xml = RE_XML.search(content)
        if xml:
            charset = xml.group(1)
            return map_charset(charset)

        html = RE_HTML.search(content)
        if html:
            charset = html.group(1)
            return map_charset(charset)

        return None

    def select_one(self, selector, namespaces=None, **kwargs):
        """Perform a CSS selection operation on the current element.

        :param selector: A CSS selector.

        :param namespaces: A dictionary mapping namespace prefixes
           used in the CSS selector to namespace URIs. By default,
           Beautiful Soup will use the prefixes it encountered while
           parsing the document.

        :param kwargs: Keyword arguments to be passed into SoupSieve's
           soupsieve.select() method.

        :return: A PageElement.
        :rtype: bs4.element.PageElement
        """
        soup = self.soup
        return soup.select_one(selector, namespaces, **kwargs):

    def select(self, selector, namespaces=None, limit=None, **kwargs):
        """Perform a CSS selection operation on the current element.

        This uses the SoupSieve library.

        :param selector: A string containing a CSS selector.

        :param namespaces: A dictionary mapping namespace prefixes
           used in the CSS selector to namespace URIs. By default,
           Beautiful Soup will use the prefixes it encountered while
           parsing the document.

        :param limit: After finding this number of results, stop looking.

        :param kwargs: Keyword arguments to be passed into SoupSieve's
           soupsieve.select() method.

        :return: A ResultSet of PageElements.
        :rtype: bs4.element.ResultSet
        """
        soup = self.soup
        return soup.select(selector, namespaces, limit, **kwargs)
