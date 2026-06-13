"""File logging for pyhn.

The TUI owns the terminal, so diagnostics go to a log file (path + level are
configurable under [settings] in ~/.pyhn/config). Modules log via
``logging.getLogger(__name__)``; those propagate to the "pyhn" logger configured
here.
"""
from __future__ import annotations

import logging

_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_logging(path: str, level: str) -> logging.Logger:
    """Configure the 'pyhn' logger to write to `path` at `level`.

    Idempotent: re-calling does not stack handlers.
    """
    logger = logging.getLogger("pyhn")
    logger.setLevel(getattr(logging, str(level).upper(), logging.WARNING))
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        handler = logging.FileHandler(path, encoding="utf-8")
        handler.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(handler)
    return logger
