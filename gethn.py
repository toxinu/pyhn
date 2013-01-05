#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gui
from cachemanager import cacheManager

cachemanager = cacheManager()
hn_gui = gui.HNGui(cachemanager)
hn_gui.main()