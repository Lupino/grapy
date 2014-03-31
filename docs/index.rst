.. grapy documentation master file, created by
   sphinx-quickstart on Thu Dec  5 10:47:15 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to grapy's documentation!
=================================

Contents:

.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

===============
Crawl Tutorial
===============

In this tutorial, we'll assume that Crawl is already installed on your system.
If that's not the case, see :ref:`intro-install`.

We are going to use `Open directory project (dmoz) <http://www.dmoz.org/>`_ as
our example domain to scrape.

This tutorial will walk you through these tasks:

1. Creating a new Crawl project
2. Defining the Items you will extract
3. Writing a :ref:`spider <topics-spiders>` to grapy a site and extract
   :ref:`Items <topics-items>`
4. Writing an :ref:`Item Pipeline <topics-item-pipeline>` to store the
   extracted Items

Crawl is written in Python_. If you're new to the language you might want to
start by getting an idea of what the language is like, to get the most out of
Crawl.  If you're already familiar with other languages, and want to learn
Python quickly, we recommend `Learn Python The Hard Way`_.  If you're new to programming
and want to start with Python, take a look at `this list of Python resources
for non-programmers`_.

.. _Python: http://www.python.org
.. _this list of Python resources for non-programmers: http://wiki.python.org/moin/BeginnersGuide/NonProgrammers
.. _Learn Python The Hard Way: http://learnpythonthehardway.org/book/

Creating a project
==================

Before you start crawling, you will have set up a new Grapy project. Enter a
directory where you'd like to store your code and then run::

   mkdir tutorial
   mkdir tutorial/spiders
   touch tutorial/__init__.py
   touch tutorial/items.py
   touch tutorial/pipelines.py
   touch tutorial/middlewares.py
   touch tutorial/spiders/__init__.py
   touch config.py
   touch main.py

These are basically:

* ``config.py``: the project configuration file
* ``tutorial/``: the project's python module, you'll later import your code from
  here.
* ``tutorial/items.py``: the project's items file.
* ``tutorial/pipelines.py``: the project's pipelines file.
* ``tutorial/middlewares.py``: the project's middlewares file.
* ``tutorial/spiders/``: a directory where you'll later put your spiders.

Defining our Item
=================

`Item` are containers that will be loaded with the crawled data; they work
like simple python dicts but provide additional protecting against populating
undeclared fields, to prevent typos.

They are declared by creating an :class:`grapy.core.Item` class and defining
its attributes as :attr:`grapy.core.Item._fields` objects, like you will in an ORM
(don't worry if you're not familiar with ORMs, you will see that this is an
easy task).

We begin by modeling the item that we will use to hold the sites data obtained
from dmoz.org, as we want to capture the name, url and description of the
sites, we define fields for each of these three attributes. To do that, we edit
items.py, found in the ``tutorial`` directory. Our Item class looks like this::

    from grapy.core import Item

    class DmozItem(Item):
        _fields = [
            {'name': 'title', 'type': 'str'},
            {'name': 'link',  'type': 'str'},
            {'name': 'desc',  'type': 'str'}
        ]

This may seem complicated at first, but defining the item allows you to use other handy
components of Crawl that need to know how your item looks like.

Our first Spider
================

Spiders are user-written classes used to crawl information from a domain (or group
of domains).

They define an initial list of URLs to download, how to follow links, and how
to parse the contents of those pages to extract :ref:`items <topics-items>`.

To create a Spider, you must subclass :class:`grapy.core.BaseSpider`, and
define the three main, mandatory, attributes:

* :attr:`~grapy.core.BaseSpider.name`: identifies the Spider. It must be
  unique, that is, you can't set the same name for different Spiders.

* :attr:`~grapy.core.BaseSpider.start_urls`: is a list of URLs where the
  Spider will begin to grapy from.  So, the first pages downloaded will be those
  listed here. The subsequent URLs will be generated successively from data
  contained in the start URLs.

* :meth:`~grapy.core.BaseSpider.parse` is a method of the spider, which will
  be called with the downloaded :class:`~grapy.core.Response` object of each
  start URL. The response is passed to the method as the first and only
  argument.

  This method is responsible for parsing the response data and extracting
  grapyed data (as grapyed items) and more URLs to follow.

  The :meth:`~grapy.core.BaseSpider.parse` method is in charge of processing
  the response and returning crawled data (as :class:`~grapy.core.Item`
  objects) and more URLs to follow (as :class:`~grapy.core.Request` objects).

This is the code for our first Spider; save it in a file named
``dmoz_spider.py`` under the ``tutorial/spiders`` directory::

   from grapy.core import BaseSpider

   class DmozSpider(BaseSpider):
       name = "dmoz"
       start_urls = [
           "http://www.dmoz.org/Computers/Programming/Languages/Python/Books/",
           "http://www.dmoz.org/Computers/Programming/Languages/Python/Resources/"
       ]

       def parse(self, response):
           filename = response.url.split("/")[-2]
           open(filename, 'wb').write(response.content)


Crawling
========

To put our spider to work, go to the project's top level directory and edit ``main.py``::

    from grapy import engine
    from grapy.sched import Scheduler
    from tutorial.spiders.dmoz_spider import DmozSpider

    sched = Scheduler()
    engine.set_sched(sched)
    engine.set_spiders([DmozSpider()])

    engine.start()

then::

    python3 main.py

But more interesting, as our ``parse`` method instructs, two files have been
created: *Books* and *Resources*, with the content of both URLs.

What just happened under the hood?
==================================

Crawl creates :class:`grapy.core.Request` objects for each URL in the
``start_urls`` attribute of the Spider, and assigns them the ``parse`` method of
the spider as their callback function.

These Requests are scheduled, then executed, and
:class:`grapy.core.Response` objects are returned and then fed back to the
spider, through the :meth:`~grapy.core.BaseSpider.parse` method.

Extracting Items
================

There are several ways to extract data from web pages.
Scrapy use :attr:`~grapy.core.Response.soup` and
:meth:`~grapy.core.Response.select` base on `BeautifulSoup`_

Let's add this code to our spider::

   from grapy.core import BaseSpider

   class DmozSpider(BaseSpider):
       name = "dmoz"
       start_urls = [
           "http://www.dmoz.org/Computers/Programming/Languages/Python/Books/",
           "http://www.dmoz.org/Computers/Programming/Languages/Python/Resources/"
       ]

       def parse(self, response):
           for site in response.select('ul li'):
               elem = site.find('a')
               if elem:
                   title = elem.get_text()
                   link = elem.get('href')
                   desc = site.get_text()
                   print(title, link, desc)

Now try crawling the dmoz.org domain again and you'll see sites being printed
in your output, run::

   python3 main.py

Using our item
==============

:class:`~grapy.core.Item` objects are custom python dicts; you can access the
values of their fields (attributes of the class we defined earlier) using the
standard dict syntax like::

   >>> item = DmozItem()
   >>> item['title'] = 'Example title'
   >>> item['title']
   'Example title'
   >>> item.title
   'Example title'

Spiders are expected to return their grapyed data inside
:class:`~grapy.core.Item` objects. So, in order to return the data we've
grapyed so far, the final code for our Spider would be like this::

   from grapy.core import BaseSpider
   from tutorial.items import DmozItem

   class DmozSpider(BaseSpider):
       name = "dmoz"
       start_urls = [
           "http://www.dmoz.org/Computers/Programming/Languages/Python/Books/",
           "http://www.dmoz.org/Computers/Programming/Languages/Python/Resources/"
       ]

       def parse(self, response):
           items = []
           for site in response.select('ul li'):
               elem = site.find('a')
               if elem:
                   item = DmozItem()
                   title = elem.get_text()
                   link = elem.get('href')
                   desc = site.get_text()
                   print(title, link, desc)
                   items.append(item)

           return items

Next steps
==========

This tutorial covers only the basics of Crawl, but there's a lot of other
features not mentioned here.

.. _intro-install:

==================
Installation guide
==================

Pre-requisites
==============

The installation steps assume that you have the following things installed:

* `Python`_ 3.3
* `asyncio`_ Python 3 async library
* `aiohttp`_ http client/server for asyncio
* `BeautifulSoup`_ Beautiful Soup: We called him Tortoise because he taught us
* `aiogear`_ Gearman client/worker for asyncio
* `pip`_ or `easy_install`_ Python package managers
* `Gearman`_ Gearman Job Server

Installing Crawl
=================

To install using source::

    git clone ssh://gitlab@gitlab.widget-inc.com:65422/pinbot-grapy/grapy.git
    cd grapy
    python3 setup.py install

.. _Python: http://www.python.org
.. _asyncio: https://code.google.com/p/tulip/
.. _aiohttp: https://github.com/fafhrd91/aiohttp
.. _BeautifulSoup: http://www.crummy.com/software/BeautifulSoup/
.. _Gearman: http://gearman.org/
.. _aiogear: https://github.com/Lupino/aiogear
.. _pip: http://www.pip-installer.org/en/latest/installing.html
.. _easy_install: http://pypi.python.org/pypi/setuptools

.. _topics-spiders:

==================
Spider
==================

.. _topics-items:

==================
Item
==================

.. _topics-item-pipeline:

==================
Pipeline
==================

