#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
from hnapi import HackerNewsAPI

hn = HackerNewsAPI()
stories = hn.getTopStories()

story = stories[0]
if not os.path.exists('comments.data'):
    comments = story.getComments()
    open('comments.data', 'w').write(json.dumps(comments))
else:
    comments = json.load(open('comments.data'))

