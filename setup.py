#!/usr/bin/env python
# coding: utf-8

import os
import sys
import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_version():
    VERSIONFILE = 'pyhn/__init__.py'
    initfile_lines = open(VERSIONFILE, 'rt').readlines()
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    for line in initfile_lines:
        mo = re.search(VSRE, line, re.M)
        if mo:
            return mo.group(1)
    raise RuntimeError('Unable to find version string in %s.' % (VERSIONFILE,))

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

setup(
    name='pyhn',
    version=get_version(),
    description='Hacker News in your terminal',
    long_description=open('README.rst').read(),
    license=open("LICENSE").read(),
    author="Geoffrey Lehée",
    author_email="hello@socketubs.org",
    url='https://github.com/socketubs/pyhn/',
    keywords="python hackernews hn",
    packages=['pyhn'],
    scripts=['scripts/pyhn'],
    install_requires=['urwid', 'beautifulsoup4', 'isit'],
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3']
)
