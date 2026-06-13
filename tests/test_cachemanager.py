"""CacheManager tests: no network, cache round-trips through JSON.

HOME is redirected to a tmp dir by the autouse conftest fixture, so Config()
and the cache live under tmp_path/.pyhn.
"""
import datetime
import json

import pyhn.hnapi as hnapi
from pyhn.cachemanager import CacheManager


def _fake_stories(start=1000, n=3):
    stories = []
    for i in range(n):
        s = hnapi.HackerNewsStory()
        s.number = i + 1
        s.title = f"Story {i + 1}"
        s.id = start + i
        stories.append(s)
    return stories


def _patch_iter(monkeypatch, chunks):
    """Make HackerNewsAPI.iter_stories yield the given chunks."""
    def fake_iter(self, which, extra_page=1, chunk_size=30):
        yield from chunks
    monkeypatch.setattr(hnapi.HackerNewsAPI, "iter_stories", fake_iter)


def test_refresh_and_get_stories(monkeypatch):
    _patch_iter(monkeypatch, [_fake_stories()])
    manager = CacheManager()
    manager.refresh("top")
    stories = manager.get_stories("top")
    assert [s.title for s in stories] == ["Story 1", "Story 2", "Story 3"]


def test_expected_count(monkeypatch):
    _patch_iter(monkeypatch, [_fake_stories()])
    manager = CacheManager()
    # extra_page defaults to 3 -> PAGE_SIZE * 4.
    assert manager.expected_count() == hnapi.PAGE_SIZE * 4


def test_init_does_not_fetch(monkeypatch):
    calls = []

    def fake_iter(self, which, extra_page=1, chunk_size=30):
        calls.append(which)
        yield _fake_stories()

    monkeypatch.setattr(hnapi.HackerNewsAPI, "iter_stories", fake_iter)
    manager = CacheManager()  # must not fetch on construction
    assert calls == []
    assert manager.get_stories("top") == []


def test_refresh_stream_yields_chunks_and_writes_cache(monkeypatch):
    chunks = [_fake_stories(1000, 2), _fake_stories(2000, 2)]
    _patch_iter(monkeypatch, chunks)
    manager = CacheManager()

    seen = list(manager.refresh_stream("top"))
    assert [len(c) for c in seen] == [2, 2]
    # Full section persisted to JSON.
    with open(manager.cache_path, encoding="utf-8") as f:
        raw = json.load(f)
    assert len(raw["top"]["stories"]) == 4


def test_is_outdated_multiday_age(monkeypatch):
    # Regression: timedelta.seconds (vs total_seconds) ignored the days part,
    # so a cache aged just over a day looked fresh.
    _patch_iter(monkeypatch, [_fake_stories()])
    manager = CacheManager()
    manager.refresh("top")
    with open(manager.cache_path, encoding="utf-8") as f:
        cache = json.load(f)
    old = datetime.datetime.today() - datetime.timedelta(days=1, seconds=30)
    cache["top"]["date"] = old.isoformat()
    with open(manager.cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f)
    assert manager.is_outdated("top") is True


def test_is_outdated_fresh_then_unknown(monkeypatch):
    _patch_iter(monkeypatch, [_fake_stories()])
    manager = CacheManager()
    manager.refresh("top")
    assert manager.is_outdated("top") is False
    assert manager.is_outdated("best") is True


def test_get_stories_unknown_section_empty(monkeypatch):
    _patch_iter(monkeypatch, [_fake_stories()])
    manager = CacheManager()
    assert manager.get_stories("ask") == []


def test_cache_file_is_valid_json(monkeypatch):
    _patch_iter(monkeypatch, [_fake_stories()])
    manager = CacheManager()
    manager.refresh("top")
    with open(manager.cache_path, encoding="utf-8") as f:
        raw = json.load(f)
    assert "top" in raw
    assert raw["top"]["stories"][0]["title"] == "Story 1"


def test_stories_roundtrip_preserves_fields(monkeypatch):
    _patch_iter(monkeypatch, [_fake_stories()])
    manager = CacheManager()
    manager.refresh("top")
    restored = manager.get_stories("top")
    assert all(isinstance(s, hnapi.HackerNewsStory) for s in restored)
    assert [s.id for s in restored] == [1000, 1001, 1002]
    assert [s.number for s in restored] == [1, 2, 3]


def test_legacy_or_corrupt_cache_treated_as_empty(monkeypatch):
    _patch_iter(monkeypatch, [_fake_stories()])
    manager = CacheManager()
    manager.refresh("top")
    with open(manager.cache_path, "wb") as f:
        f.write(b"\x80\x04\x95not-json-pickle-bytes")
    assert manager.get_stories("top") == []
    assert manager.is_outdated("top") is True
