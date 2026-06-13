"""Smoke tests: every module imports and Config instantiates on this Python."""
import importlib

import pytest

MODULES = [
    "pyhn",
    "pyhn.config",
    "pyhn.hnapi",
    "pyhn.cachemanager",
    "pyhn.poller",
    "pyhn.popup",
    "pyhn.gui",
    "pyhn.cli",
]


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name):
    assert importlib.import_module(name) is not None


def test_config_instantiates(tmp_path):
    from pyhn.config import Config

    config = Config(config_dir=str(tmp_path))
    assert config.parser is not None
