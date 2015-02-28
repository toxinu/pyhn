Pyhn
====

Hacker news in your terminal.

.. image:: https://raw.github.com/socketubs/pyhn/master/screenshot.png

Don't be worry about your IP. Pyhn is not aggresive, it uses cache.

Installation
------------

Using pip: ::

	pip install pyhn

Run it: ::

	pyhn

Arch Linux
~~~~~~~~~~

``pyhn`` is available in the AUR_.

Usage
-----

Use help for all key bindings:

* **h**, **?**: Print help popup

Configuration
-------------

By default, configuration file is in your ``$HOME/.pyhn/config``.
You can set key bindings, colors and more.

This is an example file: ::

  [keybindings]
  open_story_link = S,enter
  show_story_link = s
  open_comments_link = C
  show_comments_link = c
  open_user_link = U
  show_user_link = u
  up = j
  down = k
  page_up = ctrl d
  page_down = ctrl u
  first_story = g
  last_story = G
  refresh = r,R
  reload_config = ctrl r,ctrl R

  [settings]
  cache = /home/socketubs/.pyhn/cache
  cache_age = 5
  browser_cmd = __default__

  [colors]
  body = default||standout
  focus = black|light green|underline
  footer = black|light gray
  footer-error = dark red,bold|light gray
  header = dark gray,bold|white|
  title = dark red,bold|light gray
  help = black,bold|light gray

Settings
~~~~~~~~

* ``cache_age`` is a minute indicator which say to ``CacheManager`` when cache is outdated
* ``browser_cmd`` is a bash command which will be use to open links

Examples: ::

  browser_cmd = lynx __url__
  browser_cmd = __default__
  browser_cmd = w3m __url__
  browser_cmd = echo "[INFO] Open with w3m: __url__" >> /tmp/pyhn.log && w3m __url__

Key bindings
~~~~~~~~~~~~

You can set different key bindings for same action with a comma separator.
Take a look at ``urwid`` `input`_ manual.

Colors
~~~~~~

Colors options are designed like that: ``foreground|background|monochrome``.

**foreground**

* *colors*:  ‘default’ (use the terminal’s default foreground), ‘black’, ‘dark red’, ‘dark green’, ‘brown’, ‘dark blue’, ‘dark magenta’, ‘dark cyan’, ‘light gray’, ‘dark gray’, ‘light red’, ‘light green’, ‘yellow’, ‘light blue’, ‘light magenta’, ‘light cyan’, ‘white’
* *settings*: ‘bold’, ‘underline’, ‘blink’, ‘standout’

**background**

* *colors*: ‘default’ (use the terminal’s default background), ‘black’, ‘dark red’, ‘dark green’, ‘brown’, ‘dark blue’, ‘dark magenta’, ‘dark cyan’, ‘light gray’

**monochrome**

* *settings* : ‘bold’, ‘underline’, ‘blink’, ‘standout’

For more informations you can take a look at ``urwid`` `manual`_.

License
-------

License is `AGPL3`_. See `LICENSE`_.

.. _AUR: https://aur.archlinux.org/packages/pyhn/
.. _input: http://excess.org/urwid/docs/manual/userinput.html#keyboard-input
.. _manual: http://excess.org/urwid/docs/manual/displayattributes.html#foreground-and-background-settings
.. _AGPL3: http://www.gnu.org/licenses/agpl.html
.. _LICENSE: https://raw.github.com/socketubs/pyhn/master/LICENSE
