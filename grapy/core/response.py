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

    def select(self, selector):
        '''
        select elements use the css selector
        '''
        soup = self.soup
        re_tag = re.compile('^[a-z0-9]+$', re.I | re.U)
        re_attribute = re.compile('^(?P<tag>\w+)?\[(?P<attribute>[a-z\-_]+)(?P<operator>[=~\|\^\$\*]?)=?"?(?P<value>[^\]"]*)"?\]$')

        def attribute_checker(operator, attribute, value = ''):
            """
            Takes an operator, attribute and optional value; returns a function
            that will return True for elements that match that combination.
            """

            return {
                '=': lambda el: el.get(attribute) == value,
                # attribute includes value as one of a set of space separated tokens
                '~': lambda el: value in el.get(attribute, '').split(),
                # attribute starts with value
                '^': lambda el: el.get(attribute, '').startswith(value),
                # attribute ends with value
                '$': lambda el: el.get(attribute, '').endswith(value),
                # attribute contains value
                '*': lambda el: value in el.get(attribute, ''),
                # attribute is either exactly value or starts with value-
                '|': lambda el: el.get(attribute, '') == value \
                        or el.get(attribute, '').startswith('%s-' % value),
            }.get(operator, lambda el: el.has_attr(attribute))

        tokens = selector.split()
        current_context = [soup]

        for index, token in enumerate(tokens):
            if tokens[index - 1] == '>':
                continue

            m = re_attribute.match(token)
            if m:
                # Attribute selector
                tag, attribute, operator, value = m.groups()

                if not tag:
                    tag = True

                checker = attribute_checker(operator, attribute, value)

                found = []
                for context in current_context:
                    found.extend([el for el in context.find_all(tag) if checker(el)])

                current_context = found
                continue

            if '#' in token:
                # ID selector
                tag, id = token.split('#', 1)
                if not tag:
                    tag = True

                el = current_context[0].find(tag, {'id': id})
                if not el:
                    return []

                current_context = [el]
                continue

            if '.' in token:
                # Class selector
                tag, klass = token.split('.', 1)
                if not tag:
                    tag = True

                klasses = set(klass.split('.'))
                found = []
                for context in current_context:
                    found.extend(
                        context.find_all(tag, {'class': lambda attr:
                            attr and klasses.issubset(attr.split())})
                    )

                current_context = found
                continue

            if '*' in token:
                # Star selector
                found = []
                for context in current_context:
                    found.extend(context.find_all(True))

                current_context = found
                continue

            if token == '>':
                # Child selector
                tag = tokens[index + 1]
                if not tag:
                    tag = True

                found = []
                for context in current_context:
                    found.extend(context.find_all(tag, recursive=False))

                current_context = found
                continue

            # Here we should just have a regular tag
            if not re_tag.match(token):
                return []

            found = []
            for context in current_context:
                found.extend(context.find_all(token))

            current_context = found

        return current_context
