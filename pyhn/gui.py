# -*- coding: utf-8 -*-
import sys
import urwid
import subprocess
import threading

from pyhn.popup import Popup
from pyhn.poller import Poller
from pyhn.config import Config, FALSE_WORDS, TRUE_WORDS
from pyhn import __version__

PY3 = False
if sys.version_info.major == 3:
    PY3 = True

if PY3:
    from urllib.parse import urlparse
else:
    from urlparse import urlparse


class ItemWidget(urwid.WidgetWrap):
    """ Widget of listbox, represent each story """
    def __init__(self, story, show_published_time, show_score, show_comments):
        self.story = story
        self.number = story.number
        self.title = story.title.encode('utf-8')
        self.url = story.url
        self.domain = urlparse(story.domain).netloc
        self.submitter = story.submitter
        self.submitter_url = story.submitter_url
        self.comment_count = story.comment_count
        self.comments_url = story.comments_url
        self.score = story.score
        self.published_time = story.published_time
        self.show_published_time = show_published_time
        self.show_score = show_score
        self.show_comments = show_comments

        if self.number is None:
            number_text = '-'
            number_align = 'center'
            self.number = '-'
        else:
            number_align = 'right'
            number_text = '%s:' % self.number

        if self.submitter is None:
            self.submitter = None
            self.submitter_url = None

        if self.score is None:
            self.score = "-"

        if self.comment_count is None:
            comment_text = '-'
            self.comment_count = None
            self.comments_url = None
        else:
            comment_text = '%s' % self.comment_count

        title = self.title
        try:
            title = title.encode('latin')
        except:
            pass

        self.item = [
            ('fixed', 4, urwid.Padding(urwid.AttrWrap(
                urwid.Text(number_text, align=number_align),
                'body', 'focus'))),
            urwid.AttrWrap(
                urwid.Text(title), 'body', 'focus'),
        ]
        if self.show_published_time:
            self.item.append(
                ('fixed', 15, urwid.Padding(urwid.AttrWrap(
                urwid.Text(str(self.published_time), align="right"), 'body', 'focus'))),
            )
        if self.show_score:
            self.item.append(
                ('fixed', 5, urwid.Padding(urwid.AttrWrap(
                    urwid.Text(str(self.score), align="right"), 'body', 'focus'))),
            )
        if self.show_comments:
            self.item.append(
                ('fixed', 8, urwid.Padding(urwid.AttrWrap(
                    urwid.Text(comment_text, align="right"),
                    'body', 'focus')))
            )
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
        self.on_comments = False
        self.which = "top"

        self.config = Config()
        self.poller = Poller(
            self, delay=int(
                self.config.parser.get('settings', 'refresh_interval')))
        self.palette = self.config.get_palette()
        self.show_comments = self.config.parser.get('interface', 'show_comments') in TRUE_WORDS
        self.show_score = self.config.parser.get('interface', 'show_score') in TRUE_WORDS
        self.show_published_time = self.config.parser.get(
            'interface', 'show_published_time') in TRUE_WORDS

    def main(self):
        """
        Main Gui function which create Ui object,
        build interface and run the loop
        """
        self.ui = urwid.raw_display.Screen()
        self.ui.register_palette(self.palette)
        self.build_interface()
        self.ui.run_wrapper(self.run)

    def build_help(self):
        """ Fetch all key bindings and build help message """
        self.bindings = {}
        self.help_msg = []
        self.help_msg.append(
            urwid.AttrWrap(urwid.Text('\n Key bindings \n'), 'title'))
        self.help_msg.append(urwid.AttrWrap(urwid.Text(''), 'help'))
        for binding in self.config.parser.items('keybindings'):
            self.bindings[binding[0]] = binding[1]
            line = urwid.AttrWrap(
                urwid.Text(
                    ' %s: %s ' % (binding[1], binding[0].replace('_', ' '))),
                'help')
            self.help_msg.append(line)
        self.help_msg.append(urwid.AttrWrap(
            urwid.Text(' ctrl mouse-left: open story link'), 'help'))
        self.help_msg.append(urwid.AttrWrap(urwid.Text(''), 'help'))
        self.help_msg.append(urwid.AttrWrap(
            urwid.Text(
                ' Thanks for using Pyhn %s! ' % __version__, align='center'),
            'title'))
        self.help_msg.append(urwid.AttrWrap(urwid.Text(''), 'help'))
        self.help_msg.append(
            urwid.AttrWrap(urwid.Text(
                ' Author : toxinu'), 'help'))
        self.help_msg.append(urwid.AttrWrap(
            urwid.Text(' Code   : https://github.com/toxinu/pyhn '),
            'help'))
        self.help_msg.append(urwid.AttrWrap(
            urwid.Text(' Website: http://toxinu.github.io '),
            'help'))
        self.help_msg.append(urwid.AttrWrap(urwid.Text(''), 'help'))
        self.help_msg.append(urwid.AttrWrap(urwid.Text(''), 'help'))
        self.help_msg.append(urwid.AttrWrap(urwid.Text(''), 'help'))

        self.help = Popup(self.help_msg, ('help', 'help'), (0, 1), self.view)

    def build_interface(self):
        """
        Build interface, refresh cache if needed, update stories listbox,
        create header, footer, view and the loop.
        """
        if self.cache_manager.is_outdated():
            self.cache_manager.refresh()

        self.stories = self.cache_manager.get_stories()
        self.update_stories(self.stories)
        self.header_content = [
            ('fixed', 4, urwid.Padding(
                urwid.AttrWrap(urwid.Text(' N°'), 'header'))),
            urwid.AttrWrap(urwid.Text('TOP STORIES', align="center"), 'title'),
        ]
        if self.show_published_time:
            self.header_content.append(
                ('fixed', 15, urwid.Padding(
                urwid.AttrWrap(urwid.Text('PUBLISHED TIME'), 'header'))),
            )
        if self.show_score:
            self.header_content.append(
                ('fixed', 5, urwid.Padding(
                urwid.AttrWrap(urwid.Text('SCORE'), 'header'))),
            )
        if self.show_comments:
            self.header_content.append(
                ('fixed', 8, urwid.Padding(
                    urwid.AttrWrap(urwid.Text('COMMENTS'), 'header')))
            )
        self.header = urwid.Columns(self.header_content, dividechars=1)
        self.footer = urwid.AttrMap(
            urwid.Text(
                'Welcome in pyhn by toxinu '
                '(https://github.com/toxinu/pyhn)', align='center'),
            'footer')

        self.view = urwid.Frame(
            urwid.AttrWrap(
                self.listbox, 'body'), header=self.header, footer=self.footer)
        self.loop = urwid.MainLoop(
            self.view,
            self.palette,
            screen=self.ui,
            handle_mouse=True,
            unhandled_input=self.keystroke)

        self.build_help()
        self.already_build = True

    def set_help(self):
        """ Set help msg in footer """
        self.view.set_footer(
            urwid.AttrWrap(urwid.Text(self.help, align="center"), 'help'))

    def set_footer(self, msg, style="normal"):
        """ Set centered footer message """
        if style == "normal":
            self.footer = urwid.AttrWrap(urwid.Text(msg), 'footer')
            self.view.set_footer(self.footer)
        elif style == "error":
            self.footer = urwid.AttrWrap(urwid.Text(msg), 'footer-error')
            self.view.set_footer(self.footer)

    def set_header(self, msg):
        """ Set header story message """
        self.header_content[1] = urwid.AttrWrap(
            urwid.Text(msg, align="center"), 'title')
        self.view.set_header(urwid.Columns(self.header_content, dividechars=1))

    def keystroke(self, input):
        """ All key bindings are computed here """
        # QUIT
        if input in ('q', 'Q'):
            self.exit(must_raise=True)
        # LINKS
        if input in self.bindings['open_comments_link'].split(','):
            if not self.listbox.get_focus()[0].comments_url:
                self.set_footer('No comments')
            else:
                if not self.on_comments:
                    self.show_comments(self.listbox.get_focus()[0])
                    self.on_comments = True
                else:
                    self.update_stories(
                        self.cache_manager.get_stories(self.which))
                    self.on_comments = False
                self.open_webbrowser(self.listbox.get_focus()[0].comments_url)
        if input in self.bindings['show_comments_link'].split(','):
            if not self.listbox.get_focus()[0].comments_url:
                self.set_footer('No comments')
            else:
                self.set_footer(self.listbox.get_focus()[0].comments_url)
        if input in self.bindings['open_story_link'].split(','):
            self.open_webbrowser(self.listbox.get_focus()[0].url)
        if input in self.bindings['show_story_link'].split(','):
            self.set_footer(self.listbox.get_focus()[0].url)
        if input in self.bindings['open_submitter_link'].split(','):
            if not self.listbox.get_focus()[0].submitter_url:
                self.set_footer('No submitter')
            else:
                self.open_webbrowser(self.listbox.get_focus()[0].submitter_url)
        if input in self.bindings['show_submitter_link'].split(','):
            if not self.listbox.get_focus()[0].submitter_url:
                self.set_footer('No submitter')
            else:
                self.set_footer(self.listbox.get_focus()[0].submitter_url)
        # MOVEMENTS
        if input in self.bindings['down'].split(','):
            if self.listbox.focus_position - 1 in self.walker.positions():
                self.listbox.set_focus(
                    self.walker.prev_position(self.listbox.focus_position))
        if input in self.bindings['up'].split(','):
            if self.listbox.focus_position + 1 in self.walker.positions():
                self.listbox.set_focus(
                    self.walker.next_position(self.listbox.focus_position))
        if input in self.bindings['page_up'].split(','):
            self.listbox._keypress_page_up(self.ui.get_cols_rows())
        if input in self.bindings['page_down'].split(','):
            self.listbox._keypress_page_down(self.ui.get_cols_rows())
        if input in self.bindings['first_story'].split(','):
            self.listbox.set_focus(self.walker.positions()[0])
        if input in self.bindings['last_story'].split(','):
            self.listbox.set_focus(self.walker.positions()[-1])
        # STORIES
        if input in self.bindings['newest_stories'].split(','):
            self.set_footer('Syncing newest stories...')
            threading.Thread(
                None,
                self.async_refresher,
                None,
                ('newest', 'NEWEST STORIES'),
                {}).start()
        if input in self.bindings['top_stories'].split(','):
            self.set_footer('Syncing top stories...')
            threading.Thread(
                None, self.async_refresher,
                None, ('top', 'TOP STORIES'), {}).start()
        if input in self.bindings['best_stories'].split(','):
            self.set_footer('Syncing best stories...')
            threading.Thread(
                None, self.async_refresher,
                None, ('best', 'BEST STORIES'), {}).start()
        if input in self.bindings['show_stories'].split(','):
            self.set_footer('Syncing show stories...')
            threading.Thread(
                None, self.async_refresher,
                None, ('show', 'SHOW STORIES'), {}).start()
        if input in self.bindings['show_newest_stories'].split(','):
            self.set_footer('Syncing show newest stories...')
            threading.Thread(
                None,
                self.async_refresher,
                None,
                ('show_newest', 'SHOW NEWEST STORIES'),
                {}).start()
        if input in self.bindings['ask_stories'].split(','):
            self.set_footer('Syncing ask stories...')
            threading.Thread(
                None, self.async_refresher,
                None, ('ask', 'ASK STORIES'), {}).start()
        if input in self.bindings['jobs_stories'].split(','):
            self.set_footer('Syncing jobs stories...')
            threading.Thread(
                None, self.async_refresher,
                None, ('jobs', 'JOBS STORIES'), {}).start()
        # OTHERS
        if input in self.bindings['refresh'].split(','):
            self.set_footer('Refreshing new stories...')
            threading.Thread(
                None, self.async_refresher, None, (), {'force': True}).start()
        if input in self.bindings['reload_config'].split(','):
            self.reload_config()
        if input in ('h', 'H', '?'):
            keys = True
            while True:
                if keys:
                    self.ui.draw_screen(
                        self.ui.get_cols_rows(),
                        self.help.render(self.ui.get_cols_rows(), True))
                    keys = self.ui.get_input()
                    if 'h' or 'H' or '?' or 'escape' in keys:
                        break
        # MOUSE
        if len(input) > 1 and input[0] == 'ctrl mouse release':
            self.open_webbrowser(self.listbox.get_focus()[0].url)

    def async_refresher(self, which=None, header=None, force=False):
        if which is None:
            which = self.which
        if self.cache_manager.is_outdated(which) or force:
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
        item_ids = []
        for story in stories:
            if story.id is not None and story.id in item_ids:
                story.title = "- %s" % story.title
                items.append(ItemWidget(
                    story,
                    self.show_published_time,
                    self.show_score,
                    self.show_comments))
            else:
                items.append(ItemWidget(
                    story,
                    self.show_published_time,
                    self.show_score,
                    self.show_comments))
            item_ids.append(story.id)

        if self.already_build:
            self.walker[:] = items
            self.update()
        else:
            self.walker = urwid.SimpleListWalker(items)
            self.listbox = urwid.ListBox(self.walker)

    def show_comments(self, story):
        pass

    def open_webbrowser(self, url):
        """ Handle url and open sub process with web browser """
        if self.config.parser.get('settings', 'browser_cmd') == "__default__":
            python_bin = sys.executable
            subprocess.Popen(
                [python_bin, '-m', 'webbrowser', '-t', url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        else:
            cmd = self.config.parser.get('settings', 'browser_cmd')
            try:
                p = subprocess.Popen(
                    cmd.replace('__url__', url),
                    shell=True,
                    close_fds=True,
                    stderr=subprocess.PIPE)

                returncode = p.wait()
            except KeyboardInterrupt:
                stderr = "User keyboard interrupt detected!"
                self.set_footer(stderr, style="error")
                return
            if returncode > 0:
                stderr = p.communicate()[1]
                self.set_footer("%s" % stderr, style="error")

    def update(self):
        """ Update footer about focus story """
        focus = self.listbox.get_focus()[0]
        if not focus.submitter:
            msg = "submitted %s" % focus.published_time
        else:
            msg = "submitted %s by %s" % (
                focus.published_time, focus.submitter)

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

        if self.config.parser.get(
                'settings', 'cache') != self.cache_manager.cache_path:
            self.cache_manager.cache_path = self.config.parser.get(
                'settings', 'cache')

    def exit(self, must_raise=False):
        self.poller.is_running = False
        self.poller.join()
        if must_raise:
            raise urwid.ExitMainLoop()
        urwid.ExitMainLoop()

    def run(self):
        urwid.connect_signal(self.walker, 'modified', self.update)

        try:
            self.poller.start()
            self.loop.run()
        except KeyboardInterrupt:
            self.exit()
        print('Exiting... Bye!')
