# -*- coding: utf-8 -*-
import os
import sys
import urwid
import subprocess

from pyhn.config import Config


class ItemWidget(urwid.WidgetWrap):

    def __init__(self, story):
        self.story = story
        self.number = story.number
        self.title = story.title
        self.url = story.URL
        self.submitter = story.submitter
        self.comment_count = story.commentCount
        self.comments_url = story.commentsURL
        self.score = story.score
        self.publishedTime = story.publishedTime
        self.item = [
            ('fixed', 4, urwid.Padding(urwid.AttrWrap(
                urwid.Text("%s:" % self.number, align="right"), 'body', 'focus'))),
            urwid.AttrWrap(urwid.Text('%s' % self.title), 'body', 'focus'),
            ('fixed', 5, urwid.Padding(urwid.AttrWrap(
                urwid.Text(str(self.score), align="right"), 'body', 'focus'))),
            ('fixed', 8, urwid.Padding(urwid.AttrWrap(
                urwid.Text(str(self.comment_count), align="right"), 'body', 'focus'))),
        ]
        w = urwid.Columns(self.item, focus_column=1, dividechars=1)
        self.__super.__init__(w)

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key


class HNGui(object):
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.already_build = False
        self.which = "top"

        self.config = Config()
        self.palette = self.config.get_palette()

    def main(self):
        self.ui = urwid.raw_display.Screen()
        self.ui.register_palette(self.palette)
        self.build_interface()
        self.ui.run_wrapper(self.run)

    def build_interface(self):
        if self.cache_manager.is_outdated():
            self.cache_manager.refresh()

        self.stories = self.cache_manager.get_stories()
        self.update_stories(self.stories)
        self.header_content = [
                ('fixed', 4, urwid.Padding(urwid.AttrWrap(
                    urwid.Text(' N°'), 'header'))),
                urwid.AttrWrap(urwid.Text('TOP STORIES', align="center"), 'title'),
                ('fixed', 5, urwid.Padding(urwid.AttrWrap(
                    urwid.Text('SCORE'), 'header'))),
                ('fixed', 8, urwid.Padding(urwid.AttrWrap(
                    urwid.Text('COMMENTS'), 'header'))),            
            ]

        self.header = urwid.Columns(self.header_content, dividechars=1)
        self.footer = urwid.AttrMap(urwid.Text('Welcome in pyhn by socketubs (https://github.com/socketubs/pyhn)', align='center'), 'footer')

        self.view = urwid.Frame(urwid.AttrWrap(self.listbox, 'body'), header=self.header, footer=self.footer)
        self.loop = urwid.MainLoop(self.view, self.palette, screen=self.ui, unhandled_input=self.keystroke)
        self.already_build = True

    def set_help(self):
        msg = "J: Go next -- K: Go prev -- T: Top -- B: Best -- N: Newest -- R: Refresh -- Enter: Open link -- C: Open comments link -- ?, H: Help -- Q: Quit"
        self.view.set_footer(urwid.AttrWrap(urwid.Text(msg, align="center"), 'help'))

    def set_footer(self, msg):
        self.view.set_footer(urwid.AttrWrap(urwid.Text(msg), 'footer'))

    def set_header(self, msg):
        self.header_content[1] = urwid.AttrWrap(urwid.Text(msg, align="center"), 'title')
        self.view.set_header(urwid.Columns(self.header_content, dividechars=1))

    def keystroke(self, input):
        if input in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        elif input is 'enter':
            self.open_webbrowser(self.listbox.get_focus()[0].url)
        elif input in ('n', 'N'):
            self.set_footer('Retrieving newest stories...')
            if self.cache_manager.is_outdated('newest'):
                self.cache_manager.refresh('newest')
            stories = self.cache_manager.get_stories('newest')
            self.update_stories(stories)
            self.set_header('NEWEST STORIES')
            self.which = "newest"
        elif input in ('t', 'T'):
            self.set_footer('Retrieving top stories...')
            if self.cache_manager.is_outdated('top'):
                self.cache_manager.refresh('top')
            stories = self.cache_manager.get_stories('top')
            self.update_stories(stories)
            self.set_header('TOP STORIES')
            self.which = "top"
        elif input in ('b', 'B'):
            self.set_footer('Retrieving best stories...')
            if self.cache_manager.is_outdated('best'):
                self.cache_manager.refresh('best')
            stories = self.cache_manager.get_stories('best')
            self.update_stories(stories)
            self.set_header('BEST STORIES')
            self.which = "best"
        elif input in self.config.parser.get('keybindings', 'refresh').split(','):
            self.cache_manager.refresh(self.which)
            stories = self.cache_manager.get_stories(self.which)
            self.update_stories(stories)
        elif input in self.config.parser.get('keybindings', 'open_comments').split(','):
            self.open_webbrowser(self.listbox.get_focus()[0].comments_url)
        elif input in ('h', 'H', '?'):
            self.set_help()
        elif input in self.config.parser.get('keybindings', 'down').split(','):
            if self.listbox.focus_position - 1 in self.walker.positions():
                self.listbox.set_focus(self.walker.prev_position(self.listbox.focus_position))
        elif input in self.config.parser.get('keybindings', 'up').split(','):
            if self.listbox.focus_position + 1 in self.walker.positions():
                self.listbox.set_focus(self.walker.next_position(self.listbox.focus_position))
        elif input in self.config.parser.get('keybindings', 'reload_config').split(','):
            self.reload_config()
        elif input in self.config.parser.get('keybindings', 'page_up').split(','):
            self.listbox._keypress_page_up(self.ui.get_cols_rows())
        elif input in self.config.parser.get('keybindings', 'page_down').split(','):
            self.listbox._keypress_page_down(self.ui.get_cols_rows())

    def update_stories(self, stories):
        items = []
        for story in stories:
            items.append(ItemWidget(story))

        if self.already_build:
            self.walker[:] = items
            self.update()
        else:
            self.walker = urwid.SimpleListWalker(items)
            self.listbox = urwid.ListBox(self.walker)

    def open_webbrowser(self, url):
        python_bin = sys.executable
        browser_output = subprocess.Popen([python_bin, '-m', 'webbrowser', '-t', url],stdout=subprocess.PIPE,stderr=subprocess.PIPE)

    def update(self):
        focus = self.listbox.get_focus()[0]
        self.set_footer('submitted %s by %s' % (focus.publishedTime, focus.submitter))

    def reload_config(self):
        self.set_footer('Reloading configuration')
        self.config = Config()
        self.palette = self.config.get_palette()
        self.build_interface()
        self.loop.draw_screen()
        self.set_footer('Configuration file reloaded!')

        if self.config.parser.get('settings', 'cache') != self.cache_manager.cache_path:
            self.cache_manager.cache_path = self.config.parser.get('settings', 'cache')

    def run(self):
        urwid.connect_signal(self.walker, 'modified', self.update)

        try:
            self.loop.run()
        except KeyboardInterrupt:
            urwid.ExitMainLoop()
