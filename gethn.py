#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import pickle
import datetime
import time

from blessings import Terminal

t = Terminal()

debug = False
if len(sys.argv) == 2:
    debug = True

if sys.version < '3':
  import codecs
  def u(x):
    return codecs.unicode_escape_decode(x)[0]
else:
  def u(x):
    return x

def refreshCache():
    from hnapi import HackerNewsAPI
    hn = HackerNewsAPI()
    stories = hn.getTopStories()
    cache = {'date':datetime.datetime.today(),'stories':stories}
    pickle.dump(cache,open('hn.cache','w'))
    return stories

if os.path.exists('hn.cache'):
    cache = pickle.load(open('hn.cache'))
    stories = cache['stories']
    cacheAge = datetime.datetime.today() - cache['date']
    if cacheAge.seconds > 5*60:
        print(':: Refreshing HN cache')
        stories = refreshCache()
else:
    stories = refreshCache()

with t.fullscreen():
    lines = 0
    max_lines = t.height - 1
    for _id, s in enumerate(stories):
        # Counter
        if max_lines - lines < 5:
            footer_height = (max_lines - lines) - 1
            footer = '\n' * footer_height
            print(footer)
            more = False
            while not more:
                if debug:
                    print('!! Term height: %s' % t.height)
                    print('!! Footer height: %s' % footer_height)
                more = raw_input('More')
                if not more:
                    more = True
            lines = 0
            t.clear()

        if _id > 0 and lines > 0:
            lines += 1
            print('')
        header = '%s' % u(s.title)
        lines += 1
        if len(header) > t.width:
            lines += len(header)/t.width
        print(t.yellow(header))
        if len(s.URL) > t.width:
            lines += len(s.URL)/t.width
        lines += 1
        print(s.URL)

        # Score
        score = str(s.score) + " points "
        if s.score == -1:
            score = ""
        # Submitter
        submitter = "by " + s.submitter + " "
        if s.submitter == None:
            submitter = ""

        print('%s%s%s' % (score, submitter, s.publishedTime))
        lines += 1
        if debug:
            print('! Lines: %s' % lines)
