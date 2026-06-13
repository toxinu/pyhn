from __future__ import annotations

from threading import Event, Thread
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyhn.gui import HNGui


class Poller(Thread):
    """Periodically refreshes the current section.

    Uses an Event so the wait is interruptible — stopping is instant instead of
    polling a counter every 100ms.
    """

    def __init__(self, gui: HNGui, delay: int = 5) -> None:
        if delay < 1:
            delay = 1
        self.gui = gui
        self.delay = delay
        self._stop_event = Event()
        super().__init__(daemon=True)

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        interval = self.delay * 60
        # wait() returns True if stopped, False on timeout -> time to refresh.
        while not self._stop_event.wait(interval):
            self.gui.refresh_current()
