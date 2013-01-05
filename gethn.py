#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import pickle
import datetime

import gui

cache_path = os.path.join(os.environ.get('HOME', './'), '.hn.cache')

def refreshCache():
    from hnapi import HackerNewsAPI
    print('==> Refreshing HN cache')
    hn = HackerNewsAPI()
    stories = hn.getTopStories()
    cache = {'date':datetime.datetime.today(),'stories':stories}
    pickle.dump(cache, open(cache_path, 'w'))
    return stories

if os.path.exists(cache_path):
    cache = pickle.load(open(cache_path))
    stories = cache['stories']
    cacheAge = datetime.datetime.today() - cache['date']
    if cacheAge.seconds > 5*60:
        stories = refreshCache()
else:
    stories = refreshCache()

gui.render(stories)