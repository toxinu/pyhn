# -*- coding: utf-8 -*-
import os

try:
    from configparser import SafeConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser


class Config(object):
    def __init__(self, config_dir=None, config_file=None):
        self.config_dir = config_dir
        self.config_file = config_file

        if config_dir is None:
            self.config_dir = os.path.join(os.environ.get('HOME', './'), '.pyhn')
        if config_file is None:
            self.config_file = "config"

        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        self.config_path = os.path.join(self.config_dir, self.config_file)

        self.parser = SafeConfigParser()
        self.read()

    def read(self):
        self.parser.read(self.config_path)

        # Keybindings
        if not self.parser.has_section('keybindings'):
            self.parser.add_section('keybindings')

        if not self.parser.has_option('keybindings', 'page_up'):
            self.parser.set('keybindings', 'page_up', 'ctrl u')
        if not self.parser.has_option('keybindings', 'page_down'):
            self.parser.set('keybindings', 'page_down', 'ctrl d')
        if not self.parser.has_option('keybindings', 'up'):
            self.parser.set('keybindings', 'up', 'j')
        if not self.parser.has_option('keybindings', 'down'):
            self.parser.set('keybindings', 'down', 'k')
        if not self.parser.has_option('keybindings', 'refresh'):
            self.parser.set('keybindings', 'refresh', 'r,R')
        if not self.parser.has_option('keybindings', 'open_comments'):
            self.parser.set('keybindings', 'open_comments', 'c,C')
        if not self.parser.has_option('keybindings', 'reload_config'):
            self.parser.set('keybindings', 'reload_config', 'ctrl r,ctrl R')

        # Paths
        if not self.parser.has_section('settings'):
            self.parser.add_section('settings')

        if not self.parser.has_option('settings', 'cache'):
            self.parser.set('settings', 'cache', os.path.join(os.environ.get('HOME', './'), '.pyhn', 'cache'))
        if not self.parser.has_option('settings', 'cache_age'):
            self.parser.set('settings', 'cache_age', "5")

        # Colors
        if not self.parser.has_section('colors'):
            self.parser.add_section('colors')

        if not self.parser.has_option('colors', 'body'):
            self.parser.set('colors', 'body', 'default||standout')
        if not self.parser.has_option('colors', 'focus'):
            self.parser.set('colors', 'focus', 'black|light green|underline')
        if not self.parser.has_option('colors', 'footer'):
            self.parser.set('colors', 'footer', 'black|light gray')
        if not self.parser.has_option('colors', 'header'):
            self.parser.set('colors', 'header', 'dark gray,bold|white|')
        if not self.parser.has_option('colors', 'title'):
            self.parser.set('colors', 'title', 'dark red,bold|light gray')
        if not self.parser.has_option('colors', 'help'):
            self.parser.set('colors', 'help', 'black,bold|light gray')

        if not os.path.exists(self.config_path):
            self.parser.write(open(self.config_path, 'w'))

    def get_palette(self):
        palette = []
        for item in self.parser.items('colors'):
            name = item[0]
            settings = item[1]
            foreground = ""
            background = ""
            monochrome = ""
            if len(settings.split('|')) == 3:
                foreground = settings.split('|')[0]
                background = settings.split('|')[1]
                monochrome = settings.split('|')[2]
            elif len(settings.split('|')) == 2:
                foreground = settings.split('|')[0]
                background = settings.split('|')[1]
            elif len(settings.split('|')) == 1:
                foreground = settings.split('|')[0]

            palette.append((name, foreground, background, monochrome))
        return palette
