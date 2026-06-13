# Pyhn

Hacker News in your terminal.

![Pyhn screenshot](https://raw.githubusercontent.com/toxinu/pyhn/master/screenshot.png)

Pyhn reads from the official [Hacker News API](https://github.com/HackerNews/API)
(the public, read-only JSON API hosted on Firebase), so there is no HTML
scraping. Results are cached locally, and each section is fetched concurrently
and streamed into the list as it arrives, so the first page shows up almost
immediately.

## Features

- **Official Hacker News API** (no scraping)
- **Progressive, streaming load** with skeleton placeholders
- **Concurrent item fetching**
- **Local cache manager**
- Top, Newest, Best, Ask, Show, Show Newest and Jobs stories
- Customize all the colors
- Customize all the keybindings
- Default vim-like keybindings
- Auto refresh support
- Plays nice with tmux and screen (over ssh too!)
- Open stories in your web browser
- Mouse support
- Python 3.10+
- MIT license

## Installation

Pyhn requires Python 3.10 or newer. It is a command-line app, so the
recommended installs put it in an isolated environment on your `PATH`.

With [uv](https://docs.astral.sh/uv/) (recommended):

```
uv tool install pyhn
```

With [pipx](https://pipx.pypa.io):

```
pipx install pyhn
```


`pyhn` is available in the [AUR](https://aur.archlinux.org/packages/pyhn/).

## Usage

Use help for all key bindings:

- **h**, **?**: Print help popup

## Configuration

By default, the configuration file is in `$HOME/.pyhn/config`. It is created
with the defaults below on first run; you can set key bindings, colors and more.

This is an example file:

```ini
[keybindings]
page_up = ctrl u
page_down = ctrl d
first_story = g
last_story = G
up = k
down = j
refresh = r
show_comments_link = c
open_comments_link = C
show_story_link = s
open_story_link = S,enter
show_submitter_link = u
open_submitter_link = U
reload_config = ctrl R
newest_stories = n
top_stories = t
best_stories = b
show_stories = d
show_newest_stories = D
ask_stories = a
jobs_stories = J

[interface]
show_score = true
show_comments = true
show_published_time = false

[settings]
extra_page = 3
cache = /home/youruser/.pyhn/cache
cache_age = 5
browser_cmd = __default__
# Refresh interval in minutes (default: 5, minimum: 1)
refresh_interval = 5

[colors]
body = default||standout
focus = yellow,bold||underline
footer = black|light gray
footer-error = dark red,bold|light gray
header = dark gray,bold|white|
title = dark red,bold|light gray
help = black|dark cyan|standout
skeleton = dark gray|default
domain = dark blue|default
```

### Settings

- `extra_page` how many extra pages of stories to load (30 stories per page)
- `cache_age` minutes after which `CacheManager` considers the cache outdated
- `browser_cmd` command used to open links (`__url__` is replaced by the link)
- `refresh_interval` minutes between auto refreshes (minimum 1)

The `[interface]` section toggles the optional score, comment-count and
published-time columns.

Examples:

```
browser_cmd = lynx __url__
browser_cmd = __default__
browser_cmd = w3m __url__
browser_cmd = echo "[INFO] Open with w3m: __url__" >> /tmp/pyhn.log && w3m __url__
```

### Key bindings

You can set different key bindings for the same action with a comma separator.
Take a look at the `urwid` [input](https://urwid.org/manual/userinput.html#keyboard-input)
manual.

### Colors

Color options are written as `foreground|background|monochrome`. The background
and monochrome parts are optional (e.g. `yellow,bold||underline` leaves the
background at the terminal default).

**foreground**

- *colors*: 'default' (use the terminal's default foreground), 'black', 'dark red', 'dark green', 'brown', 'dark blue', 'dark magenta', 'dark cyan', 'light gray', 'dark gray', 'light red', 'light green', 'yellow', 'light blue', 'light magenta', 'light cyan', 'white'
- *settings*: 'bold', 'underline', 'blink', 'standout'

**background**

- *colors*: 'default' (use the terminal's default background), 'black', 'dark red', 'dark green', 'brown', 'dark blue', 'dark magenta', 'dark cyan', 'light gray'

**monochrome**

- *settings*: 'bold', 'underline', 'blink', 'standout'

For more information take a look at the `urwid`
[manual](https://urwid.org/manual/displayattributes.html#foreground-and-background-settings).

## License

License is [MIT](https://opensource.org/licenses/MIT). See
[LICENSE](https://raw.githubusercontent.com/toxinu/pyhn/master/LICENSE).
