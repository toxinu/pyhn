# -*- coding: utf-8 -*-
import os
import pickle
import datetime

from pyhn.hnapi import HackerNewsAPI
from pyhn.config import Config

class cacheManager(object):
	def __init__(self, cache_path=None):
		self.cache_path = cache_path
		if cache_path is None:
			self.config = Config()
			self.cache_path = self.config.parser.get('settings', 'cache')

		self.cache_age = int(self.config.parser.get('settings', 'cache_age'))
		self.api = HackerNewsAPI()

		if not os.path.exists(self.cache_path):
			self.refresh()

	def is_outdated(self, which="top"):
		if not os.path.exists(self.cache_path):
			return True

		cache = pickle.load(open(self.cache_path))
		if not cache.get(which, False):
			return True

		cache_age = datetime.datetime.today() - cache[which]['date']
		if cache_age.seconds > self.cache_age*60:
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
		if os.path.exists(self.cache_path):
			cache = pickle.load(open(self.cache_path))

		cache[which] = {'stories':stories, 'date':datetime.datetime.today()}
		pickle.dump(cache, open(self.cache_path, 'w'))

	def get_stories(self, which="top"):
		cache = []
		if os.path.exists(self.cache_path):
			cache = pickle.load(open(self.cache_path))
	
		if not cache.get(which, False):
			return []
		else:
			return cache[which]['stories']