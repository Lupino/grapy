try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

packages = [
    'grapy',
    'grapy.core',
]

requires = ['asyncio', 'aiohttp', 'beautifulsoup4']

setup(
    name='grapy',
    version='0.1.5',
    description='a scrapy like model',
    author='Li Meng Jun',
    author_email='lmjubuntu@gmail.com',
    url='http://lupino.me',
    packages=packages,
    package_dir={'grapy': 'grapy'},
    include_package_data=True,
    install_requires=requires,
)
