Pyhn
====

Hacker news in your terminal.

.. image:: https://dl.dropbox.com/s/swxcq2uk797309c/Screenshot%20at%202013-01-05%2018%3A38%3A59.png

Don't be worry about your IP. Pyhn is not aggresive, it uses cache.

Installation
------------

Using pip: ::

	pip install pyhn

Run it: ::

	pyhn

Usage
-----

* **h**, **?**: Print help in footer
* **j**: Go next story
* **k**: Go prev story
* **t**: Show top stories
* **b**: Show best stories
* **n**: Show newest stories
* **r**: Refresh view
* **Enter**: Open selected story in new web browser tab
* **c**: Open selected story comments page in new web browser tab
* **q**, **Escape**: Quit pyhn

Configuration
-------------

By default, configuration file is in your ``$HOME/.pyhn/confi``.
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
	
	[colors]
	body = default||standout
	focus = black|light green|underline
	footer = black|light gray
	header = dark gray,bold|white|
	title = dark red,bold|light gray
	help = black,bold|light gray

Settings
~~~~~~~~

``cache_age`` is a minute indicator which say to ``CacheManager`` when cache is outdated.

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

For more informations you can take a loot at ``urwid`` `manual`_.

License
-------

License is `AGPL3`_. See `LICENSE`_.

.. _input: http://excess.org/urwid/docs/manual/userinput.html#keyboard-input
.. _manual: http://excess.org/urwid/docs/manual/displayattributes.html#foreground-and-background-settings
.. _AGPL3: http://www.gnu.org/licenses/agpl.html
.. _LICENSE: https://raw.github.com/socketubs/pyhn/master/LICENSE
