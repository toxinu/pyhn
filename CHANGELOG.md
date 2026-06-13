# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Modernization and bug-fix pass: runs on current Python and urwid, with a test
suite plus ruff and mypy checks.

### Fixed

- **Launch crash on urwid 4**: `ItemWidget` used the removed `self.__super`
  idiom. Replaced with `super().__init__()`.
- **`get_ask_stories` crash** (`a`): called int attr as a function instead of
  `fetch_html`.
- **`open_comments` crash** (`C`): the `show_comments` bool flag shadowed the
  `show_comments()` method. Removed the dead method and `on_comments` state.
- **`None` id crash in `get_stories`**: `id < 0` failed on `None`; now checks
  `id is None`. Dropped an adjacent no-op line.
- **Title double-encoding**: titles encoded `utf-8` then `latin` broke urwid 4;
  now kept as `str` throughout.
- **`refresh_karma`**: `if karma is not '':` (identity check) changed to `!=`.
- **Inverted up/down nav**: handlers were swapped and defaults non-vim. Fixed to
  `up=k`/`down=j` (existing configs may need their up/down lines swapped).
- **`fetch_html` silent `None`**: now raises `HNException` with chaining instead
  of returning `None` on error.
- **Background loads now repaint reliably**: worker threads request a redraw via
  `watch_pipe` (drawing from a thread could otherwise hang until the next
  keypress — e.g. comments stuck on "Loading…"). Load failures now show an error
  instead of hanging.
- **urwid `run_wrapper` deprecation**: dropped the redundant legacy screen call;
  `MainLoop.run()` manages the screen (urwid-5 ready).

### Changed

- **Data source: HTML scraping → official HN Firebase API.** Replaced the
  BeautifulSoup scraper with the JSON API; items fetched concurrently. Removes
  the whole parse-bug class; `show_newest` now aliases Show HN (no API list).
- **Packaging: setup.py → pyproject.toml** (PEP 621). `pyhn` console entry point
  replaces `scripts/pyhn`; ruff + mypy config consolidated into pyproject.
- **Cache: pickle → JSON** (human-readable, no unpickle code-exec risk). Legacy
  caches auto-rebuilt; added `HackerNewsStory.to_dict`/`from_dict`; `with` handles.
- **urwid `AttrWrap` → `AttrMap`** (29 sites), clearing all urwid 4 deprecation
  warnings.
- **bs4 `findAll` → `find_all`**, clearing deprecation warnings.
- Renamed `HackerNewsAPI.get_source` → `fetch_html`.
- Dropped Python 2: removed `PY3` blocks, import fallbacks, `u''`, `object` bases,
  `%`-formatting.
- Baseline raised to Python 3.10 (setup.py, requirements, tox `py310`–`py314`).
- Unpinned deps: `requests>=2.31`, `beautifulsoup4>=4.12`, `urwid>=2.6` (→ 4.x).
- Added type hints across the package; mypy now enforces `disallow_untyped_defs`.
- `Poller` waits on a `threading.Event` instead of a 100ms busy-loop — instant,
  idle-free shutdown.
- Default `extra_page` raised 2 → 3 (~120 stories loaded per section).
- `open_story_link` default is now `S` only (Enter opens the comment thread).
  Existing configs keep `S,enter` — edit the line if Enter should not open the URL.

### Added

- **File logging**: diagnostics written to a configurable log file (`log_path`,
  `log_level` under `[settings]`; default `~/.pyhn/pyhn.log` at WARNING). The
  story/comment load paths log progress and failures.
- **Progressive story loading**: the first page renders as soon as it arrives,
  then remaining pages stream in and append live. Startup no longer scales with
  `extra_page`. Applies to startup, section switches, and refresh; rapid switches
  are guarded against interleaving. Fresh cache still renders instantly.
- **In-app threaded comments**: Enter on a story opens an indented, scrollable
  comment thread fetched from the HN API (HTML converted to plain text); Escape
  returns to the list. New `comments`/`back` keybindings and `comment-meta` colour.
  Bounded by `comments_limit` (default 50, configurable) so the load stays fast —
  breadth-first, so top-level comments fill first.
- **Source domain next to titles**: each story shows its site (e.g.
  `(example.com)`) after the title in a dim `domain` style (configurable);
  hidden for self/text posts. Matches HN's own layout.
- **Skeleton loading rows**: while a section streams, the list fills with dim
  placeholder rows and a braille spinner waving down the rank column; rows
  resolve to real stories top-down and leftover placeholders vanish when done.
  New `skeleton` palette colour (configurable).
- **Test suite** (pytest/tox): parser, config, JSON cache round-trip, and GUI
  construction tests. 30 tests, no network.
- **ruff** (`ruff.toml`, py310, `E/F/I/UP/B`) and **mypy** (`mypy.ini` + tox env).

### Removed

- **beautifulsoup4 dependency** — no longer needed after the API migration.
- Dead `HackerNewsStory.get_comments()` (defunct appspot endpoint).
- Scratch scripts `tests/get_comments.py`, `tests/treesample.py`,
  `tests/comments.data`.
