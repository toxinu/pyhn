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

requires = [
    'requests==2.25.1',
    'beautifulsoup4==4.9.3',
    'urwid==2.1.2']

version = ''
with open('pyhn/__init__.py', 'r') as fd:
    version = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
        fd.read(), re.MULTILINE).group(1)

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
    author="toxinu",
    author_email="toxinu@gmail.com",
    url='https://github.com/toxinu/pyhn/',
    keywords="python hackernews hn terminal commandline",
    packages=['pyhn'],
    scripts=['scripts/pyhn'],
    install_requires=requires,
    package_data={'': ['LICENSE', 'NOTICE']},
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
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7']
)
