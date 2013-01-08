# -*- coding: utf-8 -*-
import urwid


class Popup(urwid.WidgetWrap):
    """
    Creates a popup menu on top of another BoxWidget.

    Attributes:

    selected -- Contains the item the user has selected by pressing <RETURN>,
                or None if nothing has been selected.
    """

    selected = None

    def __init__(self, menu_list, attr, pos, body):
        """
        menu_list -- a list of strings with the menu entries
        attr -- a tuple (background, active_item) of attributes
        pos -- a tuple (x, y), position of the menu widget
        body -- widget displayed beneath the message widget
        """

        content = [w for w in menu_list]

        # Calculate width and height of the menu widget:
        height = len(menu_list)
        width = 0
        for entry in menu_list:
            if len(entry.original_widget.text) > width:
                width = len(entry.original_widget.text)

        # Create the ListBox widget and put it on top of body:
        self._listbox = urwid.AttrWrap(urwid.ListBox(content), attr[0])
        overlay = urwid.Overlay(self._listbox, body, 'center',
                                width + 2, 'middle', height)

        urwid.WidgetWrap.__init__(self, overlay)

    def keypress(self, size, key):
        """
        <RETURN> key selects an item, other keys will be passed to
        the ListBox widget.
        """

        if key == "enter":
            (widget, foo) = self._listbox.get_focus()
            (text, foo) = widget.get_text()
            self.selected = text[1:]  # Get rid of the leading space...
        else:
            return self._listbox.keypress(size, key)
