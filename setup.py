#!/usr/bin/env python
# coding: utf-8
import os
import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

packages = [
    'pyhn',
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


def get_version():
    VERSIONFILE = os.path.join('pyhn', '__init__.py')
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
    keywords="python hackernews hn terminal commandline",
    packages=packages,
    scripts=['scripts/pyhn'],
    install_requires=['urwid'],
    package_data={'': ['LICENSE'], 'pyhn.lib.requests': ['*.pem']},
    package_dir={'pyhn': 'pyhn'},
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4']
)
