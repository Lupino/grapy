try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

packages = [
    'grapy',
    'grapy.core',
]

requires = ['asyncio', 'aiohttp', 'beautifulsoup4', 'requests']

setup(
    name='grapy',
    version='0.1.9',
    description='Grapy, a fast high-level screen scraping and web crawling framework for Python 3.3 or later base on asyncio.',
    author='Li Meng Jun',
    author_email='lmjubuntu@gmail.com',
    url='https://github.com/Lupino/grapy',
    packages=packages,
    package_dir={'grapy': 'grapy'},
    include_package_data=True,
    install_requires=requires,
)
