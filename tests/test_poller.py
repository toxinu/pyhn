"""Poller tests: the Event-based wait stops promptly."""
from pyhn.poller import Poller


class _GuiStub:
    def __init__(self):
        self.calls = 0

    def refresh_current(self):
        self.calls += 1


def test_poller_stops_immediately():
    # delay=1 -> 60s interval; stop() must interrupt the wait at once.
    poller = Poller(_GuiStub(), delay=1)
    poller.start()
    poller.stop()
    poller.join(timeout=2)
    assert not poller.is_alive()


def test_poller_clamps_delay():
    assert Poller(_GuiStub(), delay=0).delay == 1
