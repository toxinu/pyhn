# -*- coding: utf-8 -*-
import os
import sys
import urwid
import subprocess
import threading

from pyhn.config import Config
from pyhn.popup import Popup
from pyhn import __version__ as VERSION

class ItemWidget(urwid.WidgetWrap):
    """ Widget of listbox, represent each story """
    def __init__(self, story):
        self.story = story
        self.number = story.number
        self.title = story.title
        self.url = story.URL
        self.submitter = story.submitter
        self.submitter_url = story.submitterURL
        self.comment_count = story.commentCount
        self.comments_url = story.commentsURL
        self.score = story.score
        self.published_time = story.publishedTime

        if self.submitter == -1:
            self.submitter = "-"
            self.submitter_url = -1

        if self.score == -1:
            self.score = "-"

        if self.comment_count == -1:
            self.comment_count = "-"
            self.comments_url = -1

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
    """ The Pyhn Gui object """
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.already_build = False
        self.which = "top"

        self.config = Config()
        self.palette = self.config.get_palette()

    def main(self):
        """ Main Gui function which create Ui object, build interface and run the loop """
        self.ui = urwid.raw_display.Screen()
        self.ui.register_palette(self.palette)
        self.build_interface()
        self.ui.run_wrapper(self.run)

    def build_help(self):
        """ Fetch all key bindings and build help message """
        self.bindings = {}
        self.help_msg = []
        self.help_msg.append(urwid.AttrWrap(urwid.Text('\n Key bindings \n'), 'title'))
        self.help_msg.append(urwid.AttrWrap(urwid.Text(''), 'help'))
        for binding in self.config.parser.items('keybindings'):
            self.bindings[binding[0]] = binding[1]
            line = urwid.AttrWrap(urwid.Text(' %s: %s ' % (
                    binding[1],
                    binding[0].replace('_', ' '))), 'help')
            self.help_msg.append(line)
        self.help_msg.append(urwid.AttrWrap(urwid.Text(''), 'help'))
        self.help_msg.append(urwid.AttrWrap(urwid.Text(' Thanks for using Pyhn %s! ' % VERSION, align='center'), 'title'))
        self.help_msg.append(urwid.AttrWrap(urwid.Text(''), 'help'))
        self.help_msg.append(urwid.AttrWrap(urwid.Text(' Website: http://github.com/socketubs/pyhn '), 'help'))
        self.help_msg.append(urwid.AttrWrap(urwid.Text(' Author : socketubs '), 'help'))
        self.help_msg.append(urwid.AttrWrap(urwid.Text(''), 'help'))
        self.help_msg.append(urwid.AttrWrap(urwid.Text(''), 'help'))
        self.help_msg.append(urwid.AttrWrap(urwid.Text(''), 'help'))

        self.help = Popup(self.help_msg, ('help','help'), (0,1), self.view)

    def build_interface(self):
        """
        Build interface, refresh cache if needed, update stories listbox, create
        header, footer, view and the loop.
        """
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
        self.loop = urwid.MainLoop(
                self.view, self.palette,
                screen=self.ui, handle_mouse=False,
                unhandled_input=self.keystroke)

        self.build_help()
        self.already_build = True

    def set_help(self):
        """ Set help msg in footer """
        self.view.set_footer(urwid.AttrWrap(urwid.Text(self.help, align="center"), 'help'))

    def set_footer(self, msg):
        """ Set centered footer message """
        self.footer = urwid.AttrWrap(urwid.Text(msg), 'footer')
        self.view.set_footer(self.footer)

    def set_header(self, msg):
        """ Set header story message """
        self.header_content[1] = urwid.AttrWrap(urwid.Text(msg, align="center"), 'title')
        self.view.set_header(urwid.Columns(self.header_content, dividechars=1))

    def keystroke(self, input):
        """ All key bindings are computed here """
        # QUIT
        if input in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        # LINKS
        elif input in self.bindings['open_story_link'].split(','):
            self.open_webbrowser(self.listbox.get_focus()[0].url)
        elif input in self.bindings['show_story_link'].split(','):
            self.set_footer(self.listbox.get_focus()[0].url)
        elif input in self.bindings['open_comments_link'].split(','):
            if self.listbox.get_focus()[0].comments_url == -1:
                self.set_footer('No comments')
            else:
                self.open_webbrowser(self.listbox.get_focus()[0].comments_url)
        elif input in self.bindings['show_comments_link'].split(','):
            if self.listbox.get_focus()[0].comments_url == -1:
                self.set_footer('No comments')
            else:
                self.set_footer(self.listbox.get_focus()[0].comments_url)
        elif input in self.bindings['open_submitter_link'].split(','):
            if self.listbox.get_focus()[0].submitter_url == -1:
                self.set_footer('Anonymous submitter')
            else:
                self.open_webbrowser(self.listbox.get_focus()[0].submitter_url)
        elif input in self.bindings['show_submitter_link'].split(','):
            if self.listbox.get_focus()[0].submitter_url == -1:
                self.set_footer('Anonymous submitter')
            else:
                self.set_footer(self.listbox.get_focus()[0].submitter_url)
        # MOVEMENTS
        elif input in self.bindings['down'].split(','):
            if self.listbox.focus_position - 1 in self.walker.positions():
                self.listbox.set_focus(self.walker.prev_position(self.listbox.focus_position))
        elif input in self.bindings['up'].split(','):
            if self.listbox.focus_position + 1 in self.walker.positions():
                self.listbox.set_focus(self.walker.next_position(self.listbox.focus_position))
        elif input in self.bindings['page_up'].split(','):
            self.listbox._keypress_page_up(self.ui.get_cols_rows())
        elif input in self.bindings['page_down'].split(','):
            self.listbox._keypress_page_down(self.ui.get_cols_rows())
        elif input in self.bindings['first_story'].split(','):
            self.listbox.set_focus(self.walker.positions()[0])
        elif input in self.bindings['last_story'].split(','):
            self.listbox.set_focus(self.walker.positions()[-1])
        # STORIES
        elif input in ('n',):
            threading.Thread(None, self.async_refresher, None, ('newest','NEWEST STORIES'), {}).start()
        elif input in ('t',):
            threading.Thread(None, self.async_refresher, None, ('top','TOP STORIES'), {}).start()
        elif input in ('b',):
            self.set_footer('Syncing best stories...')
            threading.Thread(None, self.async_refresher, None, ('best','BEST STORIES'), {}).start()
        # OTHERS
        elif input in self.bindings['refresh'].split(','):
            threading.Thread(None, self.async_refresher, None, (), {}).start()
        elif input in self.bindings['reload_config'].split(','):
            self.reload_config()
        elif input in ('h', 'H', '?'):
            keys = True
            while True:
                if keys:
                    self.ui.draw_screen(self.ui.get_cols_rows(), self.help.render(self.ui.get_cols_rows(), True));
                    keys = self.ui.get_input()
                    if 'h' or 'H' or '?' or 'escape' in keys:
                        break

    def async_refresher(self, which=None, header=None):
        if which is None:
            which = self.which
        if self.cache_manager.is_outdated(which):
            self.cache_manager.refresh(which)
        stories = self.cache_manager.get_stories(which)
        self.update_stories(stories)
        if header is not None:
            self.set_header(header)
            self.which = which
        self.loop.draw_screen()

    def update_stories(self, stories):
        """ Reload listbox and walker with new stories """
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
        """ Handle url and open sub process with web browser """
        if self.config.parser.get('settings', 'browser_cmd') == "__default__":
            python_bin = sys.executable
            browser_output = subprocess.Popen([python_bin, '-m', 'webbrowser', '-t', url],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        else:
            cmd = self.config.parser.get('settings', 'browser_cmd')
            p = subprocess.Popen(cmd.replace('__url__', url), shell=True, close_fds=True)
            p.wait()

    def update(self):
        """ Update footer about focus story """
        focus = self.listbox.get_focus()[0]
        if focus.submitter == "":
            msg = "submitted %s" % focus.published_time
        else:
            msg = "submitted %s by %s" % (focus.published_time, focus.submitter)

        self.set_footer(msg)

    def reload_config(self):
        """
        Create new Config object, reload colors, refresh cache
        if needed and redraw screen.
        """
        self.set_footer('Reloading configuration')
        self.config = Config()
        self.build_help()
        self.palette = self.config.get_palette()
        self.build_interface()
        self.loop.draw_screen()
        self.set_footer('Configuration file reloaded!')

        if self.config.parser.get('settings', 'cache') != self.cache_manager.cache_path:
            self.cache_manager.cache_path = self.config.parser.get('settings', 'cache')

    def run(self):
        """ Run the loop """
        urwid.connect_signal(self.walker, 'modified', self.update)

        try:
            self.loop.run()
        except KeyboardInterrupt:
            urwid.ExitMainLoop()
