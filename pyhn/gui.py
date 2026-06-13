from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import urwid

from pyhn import __version__
from pyhn.config import TRUE_WORDS, Config
from pyhn.poller import Poller
from pyhn.popup import Popup

if TYPE_CHECKING:
    from pyhn.cachemanager import CacheManager
    from pyhn.hnapi import HackerNewsComment, HackerNewsStory

log = logging.getLogger(__name__)


class ItemWidget(urwid.WidgetWrap):
    """ Widget of listbox, represent each story """
    def __init__(
        self,
        story: HackerNewsStory,
        show_published_time: bool,
        show_score: bool,
        show_comments: bool,
    ) -> None:
        self.story = story
        self.number = story.number
        self.title = story.title
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
            number_text = f'{self.number}:'

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
            comment_text = f'{self.comment_count}'

        # Title, with the source domain appended in a dim style (HN-like),
        # except for self/text posts that just link back to the item page.
        title_markup: list = [self.title]
        if self.domain and self.domain != 'news.ycombinator.com':
            title_markup.append(('domain', f'  ({self.domain})'))

        self.item = [
            ('fixed', 4, urwid.Padding(urwid.AttrMap(
                urwid.Text(number_text, align=number_align),
                'body', 'focus'))),
            urwid.AttrMap(
                urwid.Text(title_markup),
                {None: 'body'}, {None: 'focus'}),
        ]
        if self.show_published_time:
            self.item.append(
                ('fixed', 15, urwid.Padding(urwid.AttrMap(
                urwid.Text(str(self.published_time), align="right"), 'body', 'focus'))),
            )
        if self.show_score:
            self.item.append(
                ('fixed', 5, urwid.Padding(urwid.AttrMap(
                    urwid.Text(str(self.score), align="right"), 'body', 'focus'))),
            )
        if self.show_comments:
            self.item.append(
                ('fixed', 8, urwid.Padding(urwid.AttrMap(
                    urwid.Text(comment_text, align="right"),
                    'body', 'focus')))
            )
        w = urwid.Columns(self.item, focus_column=1, dividechars=1)
        super().__init__(w)

    def selectable(self) -> bool:
        return True

    def keypress(self, size: tuple[int, int], key: str) -> str | None:
        return key


class SkeletonWidget(urwid.WidgetWrap):
    """Dim placeholder row shown while a section streams in.

    Mirrors ItemWidget's column layout so replacing one causes no layout jump.
    The rank column shows an animated spinner; the rest are dim bars.
    """
    _BAR = "░" * 400  # light-shade blocks; cropped to the terminal width

    def __init__(
        self,
        show_published_time: bool,
        show_score: bool,
        show_comments: bool,
        spinner: str = "⠋",
    ) -> None:
        self._spinner = urwid.Text(spinner, align="center")
        # Spinner in the rank column, then a single dim bar that fills the
        # rest of the line (cropped to the terminal width by urwid).
        item: list = [
            ('fixed', 4, urwid.AttrMap(self._spinner, 'skeleton')),
            urwid.AttrMap(urwid.Text(self._BAR, wrap='clip'), 'skeleton'),
        ]
        super().__init__(urwid.Columns(item, focus_column=1, dividechars=1))

    def selectable(self) -> bool:
        # Non-selectable so focus skips placeholders and lands on real rows.
        return False

    def set_frame(self, char: str) -> None:
        self._spinner.set_text(char)


class CommentWidget(urwid.WidgetWrap):
    """One comment in the thread view, indented by its depth."""

    # Columns for the selection rule itself (bar + one gap before the text).
    _GUTTER = 2

    def __init__(self, comment: HackerNewsComment) -> None:
        author = comment.by or "[deleted]"
        meta = f"{author} · {comment.published_time}"
        pile = urwid.Pile([
            urwid.AttrMap(urwid.Text(meta), 'comment-meta'),
            urwid.Text(comment.text or ""),
            urwid.Divider(),
        ])
        # Plain body (selectable/navigable like any list row). The depth indent
        # and the left selection rule are drawn in render(), so the bar sits at
        # the comment's own left edge and moves with nesting.
        self._indent = 2 * comment.depth
        self._body = urwid.Padding(pile, right=1)
        super().__init__(self._body)

    def _inner_width(self, maxcol: int) -> int:
        return max(maxcol - self._indent - self._GUTTER, 1)

    def rows(self, size: tuple[int, ...], focus: bool = False) -> int:
        return int(self._body.rows((self._inner_width(size[0]),), focus))

    def render(self, size: tuple[int, ...], focus: bool = False) -> Any:
        inner = self._inner_width(size[0])
        body = self._body.render((inner,), focus)
        height = max(body.rows(), 1)
        # Bar covers the content rows but not the trailing Divider blank.
        content = max(height - 1, 1)
        char = "│" if focus else " "
        bar = urwid.Text(
            [('comment-bar', "\n".join([char] * content + [" "] * (height - content)))]
        ).render((1,))
        gap = urwid.Text("\n".join([" "] * height)).render((1,))

        parts = []
        if self._indent:
            pad = urwid.Text("\n".join([""] * height)).render((self._indent,))
            parts.append((pad, None, False, self._indent))
        parts += [
            (bar, None, False, 1),
            (gap, None, False, 1),
            (body, None, focus, inner),
        ]
        return urwid.CanvasJoin(parts)

    def selectable(self) -> bool:
        return True

    def keypress(self, size: tuple[int, int], key: str) -> str | None:
        return key


class HNGui:
    """ The Pyhn Gui object """
    SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    # Built lazily in _set_items()/build_interface(); declared here so the type
    # is known before those conditional assignments. urwid is treated as
    # untyped (see [tool.mypy] in pyproject.toml), so these are effectively Any.
    walker: urwid.SimpleListWalker
    listbox: urwid.ListBox

    def __init__(self, cache_manager: CacheManager) -> None:
        self.cache_manager = cache_manager
        self.already_build = False
        self.which = "top"
        # Bumped on every load request; a running load aborts if it no longer
        # matches, so rapid section switches don't interleave in the walker.
        # The lock makes each "check gen, then mutate walker" step atomic with
        # respect to a new load bumping the generation.
        self._load_gen = 0
        self._load_lock = threading.Lock()
        self._seen_ids: set = set()
        # "stories" list vs "comments" thread view.
        self._mode = "stories"
        self._help_open = False
        self._story_listbox: Any = None
        self._story_walker: Any = None
        self._story_header = "TOP STORIES"
        # Skeleton spinner animation state (driven on the loop thread).
        self._spinner_frame = 0
        self._anim_active = False
        self._redraw_pipe: Any = None  # set in build_interface (watch_pipe)
        # Assigned in build_interface / _set_items; declared for the type checker.
        self.walker: urwid.SimpleListWalker
        self.listbox: urwid.ListBox

        self.config = Config()
        self.poller = Poller(
            self, delay=int(
                self.config.parser.get('settings', 'refresh_interval')))
        self.palette = self.config.get_palette()
        self.show_comments = self.config.parser.get('interface', 'show_comments') in TRUE_WORDS
        self.show_score = self.config.parser.get('interface', 'show_score') in TRUE_WORDS
        self.show_published_time = self.config.parser.get(
            'interface', 'show_published_time') in TRUE_WORDS

    def main(self) -> None:
        """
        Main Gui function which create Ui object,
        build interface and run the loop
        """
        self.ui = urwid.raw_display.Screen()
        self.ui.register_palette(self.palette)
        self.build_interface()
        # MainLoop (created with screen=self.ui) manages the screen lifecycle;
        # the old Screen.run_wrapper() is deprecated and removed in urwid 5.
        self.run()

    def build_help(self) -> None:
        """ Fetch all key bindings and build help message """
        self.bindings = {}
        self.help_msg = []
        self.help_msg.append(
            urwid.AttrMap(urwid.Text('\n Key bindings \n'), 'title'))
        self.help_msg.append(urwid.AttrMap(urwid.Text(''), 'help'))
        for binding in self.config.parser.items('keybindings'):
            self.bindings[binding[0]] = binding[1]
            line = urwid.AttrMap(
                urwid.Text(
                    ' {}: {} '.format(binding[1], binding[0].replace('_', ' '))),
                'help')
            self.help_msg.append(line)
        self.help_msg.append(urwid.AttrMap(
            urwid.Text(' ctrl mouse-left: open story link'), 'help'))
        self.help_msg.append(urwid.AttrMap(urwid.Text(''), 'help'))
        self.help_msg.append(urwid.AttrMap(
            urwid.Text(
                f' Thanks for using Pyhn {__version__}! ', align='center'),
            'title'))
        self.help_msg.append(urwid.AttrMap(urwid.Text(''), 'help'))
        self.help_msg.append(
            urwid.AttrMap(urwid.Text(
                ' Author : toxinu'), 'help'))
        self.help_msg.append(urwid.AttrMap(
            urwid.Text(' Code   : https://github.com/toxinu/pyhn '),
            'help'))
        self.help_msg.append(urwid.AttrMap(
            urwid.Text(' Website: http://toxinu.github.io '),
            'help'))
        self.help_msg.append(urwid.AttrMap(urwid.Text(''), 'help'))
        self.help_msg.append(urwid.AttrMap(urwid.Text(''), 'help'))
        self.help_msg.append(urwid.AttrMap(urwid.Text(''), 'help'))

        self.help = Popup(self.help_msg, ('help', 'help'), (0, 1), self.view)

    def build_interface(self) -> None:
        """
        Build interface, refresh cache if needed, update stories listbox,
        create header, footer, view and the loop.
        """
        # Render whatever is cached instantly (often empty on first run); the
        # actual fetch is streamed in once the loop is live (see run()).
        self.stories = self.cache_manager.get_stories()
        self._set_items(self.stories)
        self.header_content = [
            ('fixed', 4, urwid.Padding(
                urwid.AttrMap(urwid.Text(' N°'), 'header'))),
            urwid.AttrMap(urwid.Text('TOP STORIES', align="center"), 'title'),
        ]
        if self.show_published_time:
            self.header_content.append(
                ('fixed', 15, urwid.Padding(
                urwid.AttrMap(urwid.Text('PUBLISHED TIME'), 'header'))),
            )
        if self.show_score:
            self.header_content.append(
                ('fixed', 5, urwid.Padding(
                urwid.AttrMap(urwid.Text('SCORE'), 'header'))),
            )
        if self.show_comments:
            self.header_content.append(
                ('fixed', 8, urwid.Padding(
                    urwid.AttrMap(urwid.Text('COMMENTS'), 'header')))
            )
        self.header = urwid.Columns(self.header_content, dividechars=1)
        self.footer = urwid.AttrMap(
            urwid.Text(
                'Welcome in pyhn by toxinu '
                '(https://github.com/toxinu/pyhn)', align='center'),
            'footer')

        self.view = urwid.Frame(
            urwid.AttrMap(
                self.listbox, 'body'), header=self.header, footer=self.footer)
        if not self.already_build:
            self.loop = urwid.MainLoop(
                self.view,
                self.palette,
                screen=self.ui,
                handle_mouse=True,
                unhandled_input=self.keystroke)
            # Background loads write to this pipe to request a redraw on the
            # loop thread (drawing directly from a worker thread is unsafe and
            # can hang until the next keypress).
            self._redraw_pipe = self.loop.watch_pipe(self._loop_redraw)
        else:
            # Rebuild (reload_config): reuse the existing loop and redraw pipe
            # so in-flight workers keep writing to a live fd; just swap in the
            # new view and palette.
            self.loop.widget = self.view
            self.ui.register_palette(self.palette)

        self.build_help()
        self.already_build = True

    def set_help(self) -> None:
        """ Set help msg in footer """
        self.view.set_footer(
            urwid.AttrMap(urwid.Text(self.help, align="center"), 'help'))

    def _open_help(self) -> None:
        """Show the help popup as the loop's top widget (Esc/h/q to close)."""
        self.loop.widget = self.help
        self._help_open = True
        self.loop.draw_screen()

    def _close_help(self) -> None:
        self.loop.widget = self.view
        self._help_open = False
        self.loop.draw_screen()

    def set_footer(self, msg: str, style: str = "normal") -> None:
        """ Set centered footer message """
        if style == "normal":
            self.footer = urwid.AttrMap(urwid.Text(msg), 'footer')
            self.view.set_footer(self.footer)
        elif style == "error":
            self.footer = urwid.AttrMap(urwid.Text(msg), 'footer-error')
            self.view.set_footer(self.footer)

    def set_header(self, msg: str) -> None:
        """ Set header story message """
        self.header_content[1] = urwid.AttrMap(
            urwid.Text(msg, align="center"), 'title')
        self.view.set_header(urwid.Columns(self.header_content, dividechars=1))

    def keystroke(self, input: str) -> None:
        """ All key bindings are computed here """
        log.debug("key=%r mode=%s which=%s", input, self._mode, self.which)
        # HELP OVERLAY: while open, any close key dismisses it; other keys
        # (e.g. up/down) are handled by the popup's own listbox.
        if self._help_open:
            if input in ('h', 'H', '?', 'esc', 'q', 'Q'):
                self._close_help()
            return

        # QUIT
        if input in ('q', 'Q'):
            self.exit(must_raise=True)

        # COMMENTS MODE: only navigation + back are active.
        if self._mode == "comments":
            if input in self.bindings['back'].split(','):
                self._close_comments()
            else:
                self._handle_movement(input)
            return

        # LINKS
        if input in self.bindings['open_comments_link'].split(','):
            if not self.listbox.focus.comments_url:
                self.set_footer('No comments')
            else:
                self.open_webbrowser(self.listbox.focus.comments_url)
        if input in self.bindings['show_comments_link'].split(','):
            if not self.listbox.focus.comments_url:
                self.set_footer('No comments')
            else:
                self.set_footer(self.listbox.focus.comments_url)
        if (input in self.bindings['open_story_link'].split(',')
                and input not in self.bindings['comments'].split(',')):
            # A key bound to both (e.g. a stale config with open_story_link=
            # 'S,enter') should only open comments, not also the browser.
            self.open_webbrowser(self.listbox.focus.url)
        if input in self.bindings['show_story_link'].split(','):
            self.set_footer(self.listbox.focus.url)
        if input in self.bindings['open_submitter_link'].split(','):
            if not self.listbox.focus.submitter_url:
                self.set_footer('No submitter')
            else:
                self.open_webbrowser(self.listbox.focus.submitter_url)
        if input in self.bindings['show_submitter_link'].split(','):
            if not self.listbox.focus.submitter_url:
                self.set_footer('No submitter')
            else:
                self.set_footer(self.listbox.focus.submitter_url)
        # MOVEMENTS
        self._handle_movement(input)
        # COMMENTS
        if input in self.bindings['comments'].split(','):
            self.open_comments_view()
        # STORIES
        if input in self.bindings['newest_stories'].split(','):
            self._spawn_load('newest', 'NEWEST STORIES')
        if input in self.bindings['top_stories'].split(','):
            self._spawn_load('top', 'TOP STORIES')
        if input in self.bindings['best_stories'].split(','):
            self._spawn_load('best', 'BEST STORIES')
        if input in self.bindings['show_stories'].split(','):
            self._spawn_load('show', 'SHOW STORIES')
        if input in self.bindings['show_newest_stories'].split(','):
            self._spawn_load('show_newest', 'SHOW NEWEST STORIES')
        if input in self.bindings['ask_stories'].split(','):
            self._spawn_load('ask', 'ASK STORIES')
        if input in self.bindings['jobs_stories'].split(','):
            self._spawn_load('jobs', 'JOBS STORIES')
        # OTHERS
        if input in self.bindings['refresh'].split(','):
            self._spawn_load(self.which, force=True)
        if input in self.bindings['reload_config'].split(','):
            self.reload_config()
        if input in ('h', 'H', '?'):
            self._open_help()
        # MOUSE
        if len(input) > 1 and input[0] == 'ctrl mouse release':
            self.open_webbrowser(self.listbox.focus.url)

    def _story_widget(self, story: HackerNewsStory) -> ItemWidget:
        """Build one ItemWidget, marking duplicate-id stories with '- '."""
        if story.id is not None and story.id in self._seen_ids:
            story.title = f"- {story.title}"
        self._seen_ids.add(story.id)
        return ItemWidget(
            story,
            self.show_published_time,
            self.show_score,
            self.show_comments)

    def _set_items(self, stories: list[HackerNewsStory]) -> None:
        """Replace the list with stories (or build the walker first time)."""
        self._seen_ids = set()
        items = [self._story_widget(s) for s in stories]
        if self.already_build:
            self.walker[:] = items
            self.update()
        else:
            self.walker = urwid.SimpleListWalker(items)
            self.listbox = urwid.ListBox(self.walker)

    def _append_items(self, stories: list[HackerNewsStory]) -> None:
        """Append more stories to the existing list (streaming)."""
        self.walker.extend([self._story_widget(s) for s in stories])

    def _loop_redraw(self, _data: bytes) -> bool:
        """watch_pipe callback: redraw on the loop thread. Keeps the pipe open."""
        self.loop.draw_screen()
        return True

    def _request_redraw(self) -> None:
        """Ask the loop to redraw — safe to call from a worker thread."""
        if self._redraw_pipe is not None:
            try:
                os.write(self._redraw_pipe, b"x")
            except OSError:
                log.exception("redraw pipe write failed")
        else:
            log.debug("redraw requested but no pipe (not in main loop)")

    def _handle_movement(self, input: str) -> None:
        """Navigation keys, shared by the stories and comments views."""
        if not self.walker.positions():
            return
        if input in self.bindings['up'].split(','):
            if self.listbox.focus_position - 1 in self.walker.positions():
                self.listbox.set_focus(
                    self.walker.prev_position(self.listbox.focus_position))
        if input in self.bindings['down'].split(','):
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

    def open_comments_view(self) -> None:
        """Open the in-app comment thread for the focused story."""
        focus = self.listbox.focus
        if not isinstance(focus, ItemWidget):
            self.set_footer('No comments')
            return
        story_id = focus.story.id
        if not focus.comments_url or story_id is None:
            self.set_footer('No comments')
            return
        with self._load_lock:
            self._load_gen += 1
            gen = self._load_gen
        self.set_header(f"COMMENTS: {focus.title}")
        self.set_footer('Loading comments...')
        self.loop.draw_screen()
        threading.Thread(
            target=self._load_comments,
            args=(story_id, gen),
            daemon=True).start()

    def _load_comments(self, story_id: int, gen: int) -> None:
        """Fetch and render a story's comments (background thread)."""
        log.debug("loading comments for story_id=%s", story_id)
        try:
            comments = self.cache_manager.api.get_comments(
                story_id, self.cache_manager.comments_limit)
        except Exception:
            # Worker-thread boundary: never let an error (network, or a pool
            # shutdown race on quit) escape as an uncaught traceback.
            log.exception("comment load failed for story_id=%s", story_id)
            if gen == self._load_gen:
                self.set_header(self._story_header)
                self.set_footer('Failed to load comments', style="error")
                self._request_redraw()
            return
        log.debug("fetched %d comments for story_id=%s", len(comments), story_id)
        if not comments:
            with self._load_lock:
                if gen != self._load_gen:
                    return
                self.set_header(self._story_header)
            self.set_footer('No comments')
            self._request_redraw()
            return
        rows = [CommentWidget(c) for c in comments]
        with self._load_lock:
            if gen != self._load_gen:
                log.debug("comment load superseded (gen changed)")
                return
            self._story_listbox = self.listbox
            self._story_walker = self.walker
            walker = urwid.SimpleListWalker(rows)
            self.walker = walker
            self.listbox = urwid.ListBox(walker)
            self.view.body = urwid.AttrMap(self.listbox, 'body')
            self._mode = "comments"
        self.set_footer(f"{len(comments)} comments - Esc to go back")
        log.debug("entered comments mode (%d rows)", len(comments))
        self._request_redraw()

    def _close_comments(self) -> None:
        """Return from the comment view to the story list."""
        if self._story_listbox is None:
            return
        self.listbox = self._story_listbox
        self.walker = self._story_walker
        self.view.body = urwid.AttrMap(self.listbox, 'body')
        self._mode = "stories"
        self.set_header(self._story_header)
        self.update()
        self.loop.draw_screen()

    def _prefill_skeletons(self, count: int) -> None:
        """Fill the list with `count` placeholder rows before streaming."""
        self._seen_ids = set()
        skeletons = [
            SkeletonWidget(
                self.show_published_time, self.show_score, self.show_comments)
            for _ in range(count)]
        if self.already_build:
            self.walker[:] = skeletons
        else:
            self.walker = urwid.SimpleListWalker(skeletons)
            self.listbox = urwid.ListBox(self.walker)

    def _start_anim(self) -> None:
        if self._anim_active:
            return
        self._anim_active = True
        self._spinner_frame = 0
        self.loop.set_alarm_in(0, self._animate)

    def _stop_anim(self) -> None:
        self._anim_active = False

    def _animate(self, loop: urwid.MainLoop, _data: object = None) -> None:
        """Advance the spinner on every pending skeleton row, then reschedule."""
        if not self._anim_active:
            return
        self._spinner_frame += 1
        frame = self._spinner_frame
        n = len(self.SPINNER)
        pending = False
        for i, widget in enumerate(list(self.walker)):
            if isinstance(widget, SkeletonWidget):
                pending = True
                widget.set_frame(self.SPINNER[(frame + i) % n])
        if not pending:
            self._anim_active = False
            return
        loop.draw_screen()
        loop.set_alarm_in(0.1, self._animate)

    def _spawn_load(
        self, which: str, header: str | None = None, force: bool = False,
    ) -> None:
        """Start (or restart) a background load, superseding any in flight.

        Must be called on the loop thread (prefill + animation touch urwid).
        """
        streaming = force or self.cache_manager.is_outdated(which)
        with self._load_lock:
            self._load_gen += 1
            gen = self._load_gen
            if streaming and getattr(self, "loop", None) is not None:
                if header is not None:
                    self.set_header(header)
                    self.which = which
                self._prefill_skeletons(self.cache_manager.expected_count())
                self._start_anim()
        log.debug(
            "spawn_load which=%s force=%s streaming=%s gen=%d",
            which, force, streaming, gen)
        threading.Thread(
            target=self.load_section,
            args=(which, header, force, gen),
            daemon=True).start()

    def refresh_current(self) -> None:
        """Force-refresh the current section (called from the poller thread)."""
        # Marshal onto the loop thread so prefill/animation are loop-safe.
        self.loop.set_alarm_in(
            0, lambda *_: self._spawn_load(self.which, force=True))

    def load_section(
        self, which: str, header: str | None = None,
        force: bool = False, gen: int = 0,
    ) -> None:
        """Load a section, streaming chunks into the list as they arrive.

        Replaces skeleton placeholders in place (length stays stable until the
        leftover trim) and aborts if a newer load supersedes this one. Each
        gen-check + walker mutation runs under _load_lock so a switch cannot
        land between them.
        """
        with self._load_lock:
            if gen != self._load_gen:
                return
            if header is not None:
                self.set_header(header)
                self._story_header = header
                self.which = which

        # Fresh cache: render instantly, no network, no skeleton.
        if not force and not self.cache_manager.is_outdated(which):
            stories = self.cache_manager.get_stories(which)
            with self._load_lock:
                if gen != self._load_gen:
                    return
                log.debug("load_section %s warm n=%d", which, len(stories))
                self._set_items(stories)
            self._request_redraw()
            return

        offset = 0
        try:
            for chunk in self.cache_manager.refresh_stream(which):
                with self._load_lock:
                    if gen != self._load_gen:
                        return  # superseded by a newer load
                    for i, story in enumerate(chunk):
                        widget = self._story_widget(story)
                        pos = offset + i
                        if pos < len(self.walker):
                            self.walker[pos] = widget
                        else:
                            self.walker.append(widget)
                    offset += len(chunk)
                self.set_footer(f"Loading {which}... {offset}")
                self._request_redraw()
        except Exception:
            # Worker-thread boundary (network error or pool shutdown on quit).
            log.exception("story load failed for which=%s", which)
            with self._load_lock:
                if gen != self._load_gen:
                    return
                self._stop_anim()
                del self.walker[offset:]
            self.set_footer(f"Failed to load {which} stories", style="error")
            self._request_redraw()
            return

        with self._load_lock:
            if gen != self._load_gen:
                return
            del self.walker[offset:]  # drop any leftover skeleton rows
            self._stop_anim()
        log.debug("load_section %s stream done n=%d", which, offset)
        self.set_footer(f"{which} stories ({offset})")
        self._request_redraw()

    def open_webbrowser(self, url: str) -> None:
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
                err = p.communicate()[1]
                self.set_footer(err.decode(errors="replace"), style="error")

    def update(self) -> None:
        """ Update footer about focus story """
        focus = self.listbox.focus
        # focus can be a SkeletonWidget (placeholder) or None (empty list);
        # only real stories have submitter/published_time to show.
        if not isinstance(focus, ItemWidget):
            return
        if not focus.submitter:
            msg = f"submitted {focus.published_time}"
        else:
            msg = f"submitted {focus.published_time} by {focus.submitter}"

        self.set_footer(msg)

    def reload_config(self) -> None:
        """Reload colours, key bindings and interface options, then redraw.

        Reuses the existing event loop and redraw pipe (build_interface only
        creates them once) so in-flight background loads stay valid.
        """
        self.config = Config()
        self.palette = self.config.get_palette()
        self.show_comments = self.config.parser.get(
            'interface', 'show_comments') in TRUE_WORDS
        self.show_score = self.config.parser.get(
            'interface', 'show_score') in TRUE_WORDS
        self.show_published_time = self.config.parser.get(
            'interface', 'show_published_time') in TRUE_WORDS
        self.build_interface()
        self.loop.draw_screen()
        self.set_footer('Configuration file reloaded!')

        if self.config.parser.get(
                'settings', 'cache') != self.cache_manager.cache_path:
            self.cache_manager.cache_path = self.config.parser.get(
                'settings', 'cache')

    def exit(self, must_raise: bool = False) -> None:
        self.poller.stop()
        self.poller.join()
        if must_raise:
            raise urwid.ExitMainLoop()
        urwid.ExitMainLoop()

    def run(self) -> None:
        urwid.connect_signal(self.walker, 'modified', self.update)
        # Start the first load once the screen is live, so the first page
        # streams in instead of blocking startup.
        self.loop.set_alarm_in(
            0, lambda *a: self._spawn_load('top', 'TOP STORIES'))

        try:
            self.poller.start()
            self.loop.run()
        except KeyboardInterrupt:
            self.exit()
        log.info("pyhn exiting")
