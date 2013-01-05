# -*- coding: utf-8 -*-
import os
import pickle
import datetime

from pyhn.hnapi import HackerNewsAPI

cache_path = os.path.join(os.environ.get('HOME', './'), '.pyhn.cache')

class cacheManager(object):
	def __init__(self, path=cache_path):
		self.path = path
		self.api = HackerNewsAPI()

		if not os.path.exists(self.path):
			self.refresh()

	def is_outdated(self, which="top"):
		if not os.path.exists(self.path):
			return True

		cache = pickle.load(open(self.path))
		if not cache.get(which, False):
			return True

		cache_age = datetime.datetime.today() - cache[which]['date']
		if cache_age.seconds > 5*60:
			return True
		else:
			return False

	def refresh(self, which="top"):
		if which == "top":
			stories = self.api.getTopStories()
		elif which == "newest":
			stories = self.api.getNewestStories()
		elif which == "best":
			stories = self.api.getBestStories()
		else:
			raise Exception('Bad choice, can only refresh: top, newest and best stories')

		cache = {}
		if os.path.exists(self.path):
			cache = pickle.load(open(self.path))

		cache[which] = {'stories':stories, 'date':datetime.datetime.today()}
		pickle.dump(cache, open(self.path, 'w'))

	def get_stories(self, which="top"):
		cache = []
		if os.path.exists(self.path):
			cache = pickle.load(open(self.path))
	
		if not cache.get(which, False):
			return []
		else:
			return cache[which]['stories']