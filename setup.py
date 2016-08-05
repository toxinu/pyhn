#!/usr/bin/env python
# coding: utf-8
import os
import re
import sys

from codecs import open

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

packages = [
    'pyhn',
    'pyhn.lib',
    'pyhn.lib.requests',
    'pyhn.lib.requests.packages',
    'pyhn.lib.requests.packages.chardet',
    'pyhn.lib.requests.packages.urllib3',
    'pyhn.lib.requests.packages.urllib3.packages',
    'pyhn.lib.requests.packages.urllib3.contrib',
    'pyhn.lib.requests.packages.urllib3.util',
    'pyhn.lib.requests.packages.urllib3.packages.ssl_match_hostname',
    'pyhn.lib.bs4_py2',
    'pyhn.lib.bs4_py2.builder',
    'pyhn.lib.bs4_py3',
    'pyhn.lib.bs4_py3.builder']

requires = ['urwid==1.3.0']

version = ''
with open('pyhn/__init__.py', 'r') as fd:
    version = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

with open('README.rst', 'r', 'utf-8') as f:
    readme = f.read()

setup(
    name='pyhn',
    version=version,
    description='Hacker News in your terminal',
    long_description=readme,
    license=open("LICENSE").read(),
    author="Geoffrey Lehée",
    author_email="contact@toxi.nu",
    url='https://github.com/toxinu/pyhn/',
    keywords="python hackernews hn terminal commandline",
    packages=packages,
    scripts=['scripts/pyhn'],
    install_requires=requires,
    package_data={'': ['LICENSE', 'NOTICE'], 'pyhn.lib.requests': ['*.pem']},
    package_dir={'pyhn': 'pyhn'},
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4']
)
