from __future__ import annotations

import datetime
import json
import os
from collections.abc import Iterator

from pyhn import hnapi
from pyhn.config import Config
from pyhn.hnapi import HackerNewsAPI, HackerNewsStory


class CacheManager:
    def __init__(self, cache_path: str | None = None) -> None:
        self.config = Config()
        if cache_path is None:
            cache_path = self.config.parser.get('settings', 'cache')
        self.cache_path: str = cache_path

        self.cache_age = int(self.config.parser.get('settings', 'cache_age'))
        self.extra_page = int(self.config.parser.get('settings', 'extra_page'))
        self.comments_limit = int(
            self.config.parser.get('settings', 'comments_limit'))
        self.api = HackerNewsAPI()
        # Note: construction does not fetch. Callers load lazily (the GUI
        # streams the first section once its event loop is running).

    def expected_count(self) -> int:
        """Approximate number of stories a full load will produce.

        Used by the GUI to size the skeleton placeholder list.
        """
        return hnapi.PAGE_SIZE * (self.extra_page + 1)

    def _load(self) -> dict:
        """Read the JSON cache, returning {} on missing or unreadable file.

        An unreadable file includes a legacy pickle cache from older
        versions; it is simply treated as empty and rebuilt on refresh.
        """
        if not os.path.exists(self.cache_path):
            return {}
        try:
            with open(self.cache_path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError, UnicodeDecodeError):
            return {}

    def is_outdated(self, which: str = "top") -> bool:
        cache = self._load()
        entry = cache.get(which)
        if not entry:
            return True

        cached_at = datetime.datetime.fromisoformat(entry['date'])
        cache_age = datetime.datetime.today() - cached_at
        return cache_age.total_seconds() > self.cache_age * 60

    def refresh_stream(
        self, which: str = "top",
    ) -> Iterator[list[HackerNewsStory]]:
        """Fetch a section in chunks, yielding each as it arrives.

        Accumulates all chunks and writes the full section to the JSON cache
        once the stream is exhausted, so the on-disk cache stays a complete
        snapshot.
        """
        collected: list[HackerNewsStory] = []
        for chunk in self.api.iter_stories(which, extra_page=self.extra_page):
            collected.extend(chunk)
            yield chunk

        cache = self._load()
        cache[which] = {
            'stories': [story.to_dict() for story in collected],
            'date': datetime.datetime.today().isoformat()}
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f)

    def refresh(self, which: str = "top") -> None:
        """Fully refresh a section's cache (drains refresh_stream)."""
        for _ in self.refresh_stream(which):
            pass

    def get_stories(self, which: str = "top") -> list[HackerNewsStory]:
        entry = self._load().get(which)
        if not entry:
            return []
        return [HackerNewsStory.from_dict(d) for d in entry['stories']]
