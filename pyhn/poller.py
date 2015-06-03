# -*- coding: utf-8 -*-
from time import sleep
from threading import Thread


class Poller(Thread):
    def __init__(self, gui, delay=5):
        if delay < 1:
            delay = 1

        self.gui = gui
        self.delay = delay
        self.is_running = True
        self.counter = 0
        super(Poller, self).__init__()

    def run(self):
        while self.is_running:
            sleep(0.1)
            self.counter += 0.1
            if self.counter >= self.delay * 60:
                self.gui.async_refresher(force=True)
                self.counter = 0
