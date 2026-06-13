"""GUI construction + progressive-load tests: no screen, no event loop, no network.

HOME is redirected to tmp by the autouse conftest fixture, so Config() writes
under tmp_path/.pyhn.
"""
import types

import urwid

import pyhn.hnapi as hnapi
from pyhn.gui import CommentWidget, HNGui, ItemWidget, SkeletonWidget


def _story(**kw):
    s = hnapi.HackerNewsStory()
    s.number = kw.get("number", 1)
    s.title = kw.get("title", "Example story")
    s.url = kw.get("url", "https://example.com")
    s.domain = kw.get("domain", "https://example.com")
    s.submitter = kw.get("submitter", "alice")
    s.submitter_url = kw.get(
        "submitter_url", "https://news.ycombinator.com/user?id=alice")
    s.score = kw.get("score", 42)
    s.comment_count = kw.get("comment_count", 7)
    s.comments_url = kw.get(
        "comments_url", "https://news.ycombinator.com/item?id=1")
    s.published_time = kw.get("published_time", "1 hour ago")
    s.id = kw.get("id", 1)
    return s


# --- ItemWidget construction ------------------------------------------------

def test_itemwidget_constructs():
    # Regression: super().__init__ (was the removed urwid __super idiom).
    widget = ItemWidget(_story(), True, True, True)
    assert widget.selectable()


def test_itemwidget_title_stays_str():
    # Regression: title was double-encoded to bytes, crashing urwid 4.
    widget = ItemWidget(_story(title="Café — news"), True, True, True)
    assert isinstance(widget.title, str)
    assert widget.title == "Café — news"


def test_itemwidget_shows_domain():
    widget = ItemWidget(_story(domain="https://example.com"), False, False, False)
    plain, _ = widget.item[1].original_widget.get_text()
    assert "(example.com)" in plain


def test_itemwidget_hides_hn_self_domain():
    widget = ItemWidget(
        _story(domain="https://news.ycombinator.com"), False, False, False)
    plain, _ = widget.item[1].original_widget.get_text()
    assert "(" not in plain


def test_itemwidget_handles_none_fields():
    widget = ItemWidget(
        _story(number=None, submitter=None, score=None, comment_count=None),
        True, True, True)
    assert widget is not None


# --- progressive loading ----------------------------------------------------

class _DummyCache:
    """update path never touches the cache manager."""


def _prep_gui(cache):
    """An HNGui wired enough to exercise load paths without a screen."""
    gui = HNGui(cache)
    gui.already_build = True
    gui.walker = urwid.SimpleListWalker([])
    gui.listbox = urwid.ListBox(gui.walker)
    gui.loop = types.SimpleNamespace(draw_screen=lambda: None)
    gui.set_footer = lambda *a, **k: None
    gui.set_header = lambda *a, **k: None
    return gui


def test_set_then_append_items():
    gui = _prep_gui(_DummyCache())
    gui._set_items([_story(id=1)])
    gui._append_items([_story(id=2), _story(id=3)])
    assert [w.story.id for w in gui.walker] == [1, 2, 3]


def test_load_section_streams_all_chunks():
    class Cache:
        def is_outdated(self, which):
            return True

        def refresh_stream(self, which):
            yield [_story(id=1)]
            yield [_story(id=2), _story(id=3)]

    gui = _prep_gui(Cache())
    gui.load_section("top")
    assert [w.story.id for w in gui.walker] == [1, 2, 3]


def test_load_section_warm_cache_is_instant():
    class Cache:
        def is_outdated(self, which):
            return False

        def get_stories(self, which):
            return [_story(id=1), _story(id=2)]

    gui = _prep_gui(Cache())
    gui.load_section("top")
    assert [w.story.id for w in gui.walker] == [1, 2]


def test_skeleton_widget():
    sk = SkeletonWidget(True, True, True)
    assert sk.selectable() is False
    sk.set_frame("X")
    assert sk._spinner.text == "X"


def test_prefill_skeletons():
    gui = _prep_gui(_DummyCache())
    gui._prefill_skeletons(5)
    assert len(gui.walker) == 5
    assert all(isinstance(w, SkeletonWidget) for w in gui.walker)


def test_update_ignores_skeleton_and_empty_focus():
    # Regression: the 'modified' signal fires update() while the list holds
    # skeletons; focus is a SkeletonWidget (no .submitter) -> must not crash.
    gui = _prep_gui(_DummyCache())
    gui.update()                 # empty walker -> focus None
    gui._prefill_skeletons(3)
    gui.update()                 # focus is a SkeletonWidget
    # No assertion needed: the test passes if neither call raises.


def test_modified_signal_with_skeletons_does_not_crash():
    # Mirrors run(): the 'modified' signal calls update() on every walker
    # mutation, including when skeletons are inserted. This is the exact path
    # that crashed at startup.
    gui = _prep_gui(_DummyCache())
    urwid.connect_signal(gui.walker, "modified", gui.update)
    gui._prefill_skeletons(3)  # mutation -> modified -> update(); must not raise


def test_streaming_replaces_skeletons_in_place():
    class Cache:
        def is_outdated(self, which):
            return True

        def refresh_stream(self, which):
            yield [_story(id=1), _story(id=2), _story(id=3)]

    gui = _prep_gui(Cache())
    gui._prefill_skeletons(5)          # 5 placeholders up front
    gui.load_section("top")            # one 3-story chunk
    assert len(gui.walker) == 3        # leftover skeletons trimmed
    assert all(isinstance(w, ItemWidget) for w in gui.walker)
    assert [w.story.id for w in gui.walker] == [1, 2, 3]


def test_stale_load_aborts_midstream():
    holder = {}

    class Cache:
        def is_outdated(self, which):
            return True

        def refresh_stream(self, which):
            yield [_story(id=1)]
            holder["gui"]._load_gen += 1  # a newer load started
            yield [_story(id=2)]

    gui = _prep_gui(Cache())
    holder["gui"] = gui
    gui.load_section("top")
    # First chunk applied; second dropped because the load was superseded.
    assert [w.story.id for w in gui.walker] == [1]


# --- comments view ----------------------------------------------------------

def _comment(by="alice", text="hello", depth=0, deleted=False):
    return hnapi.HackerNewsComment(
        by=by, text=text, published_time="1 hour ago", depth=depth,
        deleted=deleted)


def test_comment_widget():
    w = CommentWidget(_comment(depth=2))
    assert w.selectable() is True


def test_comment_widget_focus_bar():
    w = CommentWidget(_comment(text="hello"))
    focused = [t.decode() for t in w.render((30,), focus=True).text]
    assert focused[0].startswith("│")          # content rows carry the bar
    assert not focused[-1].startswith("│")      # trailing divider row does not
    unfocused = [t.decode() for t in w.render((30,), focus=False).text]
    assert not any(line.startswith("│") for line in unfocused)


def test_comment_view_navigation():
    # Regression: a full-height selection bar must not break j/k navigation.
    gui = _prep_gui_with_view(_DummyCache())
    gui.bindings = dict(gui.config.parser.items("keybindings"))
    gui._mode = "comments"
    gui.walker = urwid.SimpleListWalker(
        [CommentWidget(_comment(by=b)) for b in "abc"])
    gui.listbox = urwid.ListBox(gui.walker)
    gui.ui = types.SimpleNamespace(get_cols_rows=lambda: (40, 10))
    gui.listbox.render((40, 10), focus=True)
    gui.keystroke("j")   # down (default binding)
    assert gui.listbox.focus_position == 1
    gui.keystroke("k")   # up
    assert gui.listbox.focus_position == 0


def _prep_gui_with_view(cache):
    """An HNGui with a real Frame view, for comment mode-switch tests."""
    gui = _prep_gui(cache)
    gui.view = urwid.Frame(urwid.AttrMap(gui.listbox, 'body'))
    gui.set_header = lambda *a, **k: None
    return gui


def test_open_comments_view_non_story_focus_noop():
    gui = _prep_gui_with_view(_DummyCache())
    gui._prefill_skeletons(2)          # focus is a SkeletonWidget
    gui.open_comments_view()
    assert gui._mode == "stories"


def test_load_comments_switches_mode_and_back():
    class API:
        def get_comments(self, story_id, max_comments=200):
            return [_comment(by="a", depth=0), _comment(by="b", depth=1)]

    class Cache:
        api = API()
        comments_limit = 50

    gui = _prep_gui_with_view(Cache())
    gui._set_items([_story(id=1)])     # one real story focused
    gui._load_comments(1, gui._load_gen)
    assert gui._mode == "comments"
    assert len(gui.walker) == 2
    assert all(isinstance(w, CommentWidget) for w in gui.walker)

    gui._close_comments()
    assert gui._mode == "stories"
    assert [w.story.id for w in gui.walker] == [1]


def test_load_comments_empty_stays_in_stories():
    class API:
        def get_comments(self, story_id, max_comments=200):
            return []

    class Cache:
        api = API()
        comments_limit = 50

    gui = _prep_gui_with_view(Cache())
    gui._set_items([_story(id=1)])
    gui._load_comments(1, gui._load_gen)
    assert gui._mode == "stories"


def test_stale_comment_load_aborts():
    class API:
        def get_comments(self, story_id, max_comments=200):
            return [_comment()]

    class Cache:
        api = API()
        comments_limit = 50

    gui = _prep_gui_with_view(Cache())
    gui._set_items([_story(id=1)])
    gui._load_gen += 1                 # simulate a newer load before this one
    gui._load_comments(1, gui._load_gen - 1)
    assert gui._mode == "stories"      # superseded -> no switch


def test_enter_opens_comments_not_browser():
    # Stale config (open_story_link='S,enter') must not also open the browser
    # when Enter is bound to comments.
    gui = _prep_gui_with_view(_DummyCache())
    gui._set_items([_story(id=1)])
    gui.bindings = dict(gui.config.parser.items("keybindings"))
    gui.bindings["open_story_link"] = "S,enter"
    gui.bindings["comments"] = "enter"
    opened, viewed = [], []
    gui.open_webbrowser = lambda url: opened.append(url)
    gui.open_comments_view = lambda: viewed.append(True)
    gui.keystroke("enter")
    assert opened == []        # browser NOT opened
    assert viewed == [True]    # comment view opened


def test_help_overlay_open_and_close():
    # Regression: Esc (and h/q) must dismiss the help popup. The old blocking
    # get_input() loop never resolved a lone Esc.
    gui = _prep_gui_with_view(_DummyCache())
    gui.build_help()
    gui.bindings = dict(gui.config.parser.items("keybindings"))

    gui.keystroke("h")
    assert gui._help_open is True
    assert gui.loop.widget is gui.help

    gui.keystroke("esc")
    assert gui._help_open is False
    assert gui.loop.widget is gui.view


def test_help_overlay_swallows_keys_until_closed():
    gui = _prep_gui_with_view(_DummyCache())
    gui.build_help()
    gui.bindings = dict(gui.config.parser.items("keybindings"))
    gui.keystroke("h")
    # A non-close key while help is open is ignored (no section load, no crash).
    spawned = []
    gui._spawn_load = lambda *a, **k: spawned.append(a)
    gui.keystroke("t")
    assert spawned == []
    assert gui._help_open is True
