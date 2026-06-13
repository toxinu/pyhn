import pytest


@pytest.fixture(autouse=True)
def isolated_home(monkeypatch, tmp_path):
    """Keep Config() and the cache out of the real ~/.pyhn during tests."""
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path
