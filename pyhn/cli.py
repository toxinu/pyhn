"""Console entry point for pyhn (the `pyhn` command)."""
import logging

from pyhn import gui
from pyhn.cachemanager import CacheManager
from pyhn.config import Config
from pyhn.logconfig import setup_logging


def main() -> None:
    config = Config()
    setup_logging(
        config.parser.get("settings", "log_path"),
        config.parser.get("settings", "log_level"))
    logging.getLogger(__name__).info("pyhn starting")

    cache_manager = CacheManager()
    hn_gui = gui.HNGui(cache_manager)
    hn_gui.main()


if __name__ == "__main__":
    main()
