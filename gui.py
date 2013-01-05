#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urwid
import webbrowser

class ItemWidget(urwid.WidgetWrap):

    def __init__(self, story):
        self.story = story
        self.number = story.number
        self.title = story.title
        self.url = story.URL
        self.submitter = story.submitter
        self.comment_count = story.commentCount
        self.score = story.score
        self.publishedTime = story.publishedTime
        self.item = [
            ('fixed', 4, urwid.Padding(urwid.AttrWrap(
                urwid.Text("%s:" % self.number, align="right"), 'body', 'focus'))),
            urwid.AttrWrap(urwid.Text('%s' % self.title), 'body', 'focus'),
            ('fixed', 5, urwid.Padding(urwid.AttrWrap(
                urwid.Text(str(self.score), align="right"), 'body','focus'))),
            ('fixed', 8, urwid.Padding(urwid.AttrWrap(
                urwid.Text(str(self.comment_count), align="right"), 'body','focus'))),
        ]
        w = urwid.Columns(self.item, focus_column=1, dividechars=1)
        self.__super.__init__(w)

    def selectable (self):
        return True

    def keypress(self, size, key):
        return key

class HNGui(object):
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.already_build = False
        self.which = "top"

        self.palette = [
            ('body','default', '', 'standout'),
            ('focus','black', 'light green', 'underline'),
            ('footer','black', 'light gray'),
            ('header','dark gray,bold', 'white'),
            ('title','dark red,bold', 'white', '')
        ]

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
        self.footer = urwid.AttrMap(urwid.Text('Welcome in hn_cli by socketubs (http://socketubs.net)'), 'footer')

        self.view = urwid.Frame(urwid.AttrWrap(self.listbox, 'body'), header=self.header, footer=self.footer)
        self.loop = urwid.MainLoop(self.view, self.palette, screen=self.ui, unhandled_input=self.keystroke)
        self.already_build = True

    def set_footer(self, msg):
        self.view.set_footer(urwid.AttrWrap(urwid.Text(msg), 'footer'))

    def set_header(self, msg):
        self.header_content[1] = urwid.AttrWrap(urwid.Text(msg), 'title')
        self.view.set_header(urwid.Columns(self.header_content, dividechars=1))

    def keystroke(self, input):
        if input in ('q', 'Q'):
            raise urwid.ExitMainLoop()

        if input is 'enter':
            focus = self.listbox.get_focus()[0].title
            webbrowser.open(self.listbox.get_focus()[0].url, autoraise=False)

        if input in ('n', 'N'):
            self.set_footer('Retrieving newest stories...')
            if self.cache_manager.is_outdated('newest'):
                self.cache_manager.refresh('newest')
            stories = self.cache_manager.get_stories('newest')
            self.update_stories(stories)
            self.set_header('NEWEST STORIES')
            self.which = "newest"

        if input in ('t', 'T'):
            self.set_footer('Retrieving top stories...')
            if self.cache_manager.is_outdated('top'):
                self.cache_manager.refresh('top')
            stories = self.cache_manager.get_stories('top')
            self.update_stories(stories)
            self.set_header('TOP STORIES')
            self.which = "top"

        if input in ('b', 'B'):
            self.set_footer('Retrieving best stories...')
            if self.cache_manager.is_outdated('best'):
                self.cache_manager.refresh('best')
            stories = self.cache_manager.get_stories('best')
            self.update_stories(stories)
            self.set_header('BEST STORIES')
            self.which = "best"

        if input is 'r':
            self.cache_manager.refresh(self.which)
            stories = self.cache_manager.get_stories(self.which)
            self.update_stories(stories)

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

    def update(self):
        focus = self.listbox.get_focus()[0]
        self.set_footer('submitted %s by %s' % (focus.publishedTime, focus.submitter))

    def run(self):
        urwid.connect_signal(self.walker, 'modified', self.update)

        try:
            self.loop.run()
        except KeyboardInterrupt:
            urwid.ExitMainLoop()