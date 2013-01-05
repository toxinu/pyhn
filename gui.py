#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urwid
import webbrowser

class ItemWidget (urwid.WidgetWrap):

    def __init__ (self, story):
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

def render(stories):

    palette = [
        ('body','default', '', 'standout'),
        ('focus','black', 'light green', 'underline'),
        ('footer','black', 'light gray'),
        ('header','dark gray,bold', 'white'),
    ]

    def keystroke(input):
        if input in ('q', 'Q'):
            raise urwid.ExitMainLoop()

        if input is 'enter':
            focus = listbox.get_focus()[0].title
            webbrowser.open(listbox.get_focus()[0].url, autoraise=False)

    items = []
    for story in stories:
        items.append(ItemWidget(story))

    walker = urwid.SimpleListWalker(items)
    listbox = urwid.ListBox(walker)
    header_content = [
            ('fixed', 4, urwid.Padding(urwid.AttrWrap(
                urwid.Text(' N°'), 'header'))),
            urwid.AttrWrap(urwid.Text('TOP STORIES'), 'header'),
            ('fixed', 5, urwid.Padding(urwid.AttrWrap(
                urwid.Text('SCORE'), 'header'))),
            ('fixed', 8, urwid.Padding(urwid.AttrWrap(
                urwid.Text('COMMENTS'), 'header'))),            
        ]

    header = urwid.Columns(header_content, dividechars=1)
    footer = urwid.AttrMap(urwid.Text('Welcome in hn_cli by socketubs (http://socketubs.net)'), 'footer')

    view = urwid.Frame(urwid.AttrWrap(listbox, 'body'), header=header, footer=footer)

    def update():
        focus = listbox.get_focus()[0]
        view.set_footer(urwid.AttrWrap(urwid.Text(
                'submitted %s by %s' % (focus.publishedTime, focus.submitter)), 'footer'))

    loop = urwid.MainLoop(view, palette, unhandled_input=keystroke)
    urwid.connect_signal(walker, 'modified', update)
    try:
        loop.run()
    except KeyboardInterrupt:
        urwid.ExitMainLoop()