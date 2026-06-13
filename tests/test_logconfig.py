"""Logging setup tests."""
import logging

from pyhn.logconfig import setup_logging


def test_setup_logging_writes_to_path(tmp_path):
    path = str(tmp_path / "pyhn.log")
    logger = setup_logging(path, "DEBUG")
    logger.debug("hello from test")
    for handler in logger.handlers:
        handler.flush()
    with open(path, encoding="utf-8") as f:
        assert "hello from test" in f.read()


def test_setup_logging_level_parsed(tmp_path):
    logger = setup_logging(str(tmp_path / "a.log"), "error")
    assert logger.level == logging.ERROR


def test_setup_logging_idempotent(tmp_path):
    path = str(tmp_path / "b.log")
    logger = setup_logging(path, "INFO")
    before = len(logger.handlers)
    setup_logging(path, "INFO")
    assert len(logger.handlers) == before  # no duplicate handler
