"""
Client for the official Hacker News API.

Hacker News publishes a versioned, public JSON API hosted on Firebase:
https://github.com/HackerNews/API

This module wraps it and exposes story/user objects to the rest of pyhn. The
public surface (HackerNewsAPI.get_*_stories, the HackerNewsStory fields,
HackerNewsUser) is kept stable so the cache and GUI layers are unaffected.
"""
from __future__ import annotations

import html
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from typing import Any

import requests

API_BASE = "https://hacker-news.firebaseio.com/v0"
ITEM_BASE = "https://news.ycombinator.com/item?id="
USER_BASE = "https://news.ycombinator.com/user?id="

# Stories per "page", matching the historical HN front-page size. extra_page
# multiplies this (extra_page=2 -> 90 stories), preserving the old semantics.
PAGE_SIZE = 30
# Concurrency for per-item lookups (the API has no batch endpoint).
MAX_WORKERS = 16
# Per-request timeout (seconds) so a stalled connection can't hang forever.
REQUEST_TIMEOUT = 10

HEADERS = {
    'User-Agent': (
        "Pyhn (Hacker news command line client) - "
        "https://github.com/toxinu/pyhn")}

# Maps a pyhn "which" value to the API's story-list endpoint. The API has no
# "show newest" list, so show_newest aliases to showstories.
LIST_ENDPOINTS = {
    "top": "topstories",
    "newest": "newstories",
    "best": "beststories",
    "ask": "askstories",
    "show": "showstories",
    "show_newest": "showstories",
    "jobs": "jobstories",
}


class HNException(Exception):
    """
    HNException is exactly the same as a plain Python Exception.

    The HNException class exists solely so that you can identify
    errors that come from HN as opposed to from your application.
    """
    pass


def _relative_time(epoch: int, now: float | None = None) -> str:
    """Render a Unix timestamp as a relative string, e.g. '2 hours ago'."""
    if now is None:
        now = time.time()
    delta = int(now - epoch)
    if delta < 0:
        delta = 0

    for unit, seconds in (
            ("day", 86400), ("hour", 3600), ("minute", 60), ("second", 1)):
        if delta >= seconds:
            value = delta // seconds
            plural = "s" if value != 1 else ""
            return f"{value} {unit}{plural} ago"
    return "just now"


class _TextExtractor(HTMLParser):
    """Collects plain text from HN comment HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "p":
            self.parts.append("\n\n")
        elif tag == "br":
            self.parts.append("\n")
        elif tag == "li":
            self.parts.append("\n- ")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def get_text(self) -> str:
        return "".join(self.parts).strip()


def _html_to_text(raw: str) -> str:
    """Convert HN comment HTML to readable plain text."""
    if not raw:
        return ""
    parser = _TextExtractor()
    parser.feed(raw)
    return parser.get_text()


class HackerNewsAPI:
    """Fetches stories and users from the official Hacker News API."""

    def fetch_json(self, url: str) -> Any:
        """GET a URL and return the decoded JSON body."""
        try:
            r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        except Exception as exc:
            raise HNException(
                "Error getting data from " + url +
                ". Your internet connection may have something "
                "funny going on, or you could be behind a proxy.") from exc
        if not r:
            raise HNException(
                f"Empty or error response ({r.status_code}) from {url}")
        return r.json()

    def _story_ids(self, which: str) -> list[int]:
        """Return the ordered story ids for a 'which' section."""
        endpoint = LIST_ENDPOINTS.get(which)
        if endpoint is None:
            valid = ", ".join(sorted(LIST_ENDPOINTS))
            raise ValueError(f"Bad value: one of {valid}")
        ids = self.fetch_json(f"{API_BASE}/{endpoint}.json")
        return ids or []

    def _fetch_item(self, item_id: int) -> dict | None:
        """Fetch a single item; None if it has no body."""
        return self.fetch_json(f"{API_BASE}/item/{item_id}.json")

    def _build_story(self, item: dict | None, rank: int) -> HackerNewsStory | None:
        """Turn an API item into a HackerNewsStory, or None to skip it."""
        if not item or item.get('deleted') or item.get('dead'):
            return None

        story = HackerNewsStory()
        story.id = item.get('id')
        story.number = rank
        story.title = html.unescape(item.get('title') or "")
        story.score = item.get('score')
        story.comment_count = item.get('descendants')
        story.published_time = _relative_time(item['time']) if item.get('time') else ""

        story.comments_url = f"{ITEM_BASE}{story.id}"
        # Jobs send url:"" and Ask/text posts omit it; fall back to the item page.
        story.url = item.get('url') or story.comments_url
        story.domain = story.url

        story.submitter = item.get('by')
        if story.submitter:
            story.submitter_url = f"{USER_BASE}{story.submitter}"
        else:
            story.submitter_url = None
        return story

    def iter_stories(
        self,
        which: str,
        extra_page: int = 1,
        chunk_size: int = PAGE_SIZE,
    ) -> Iterator[list[HackerNewsStory]]:
        """Yield stories in chunks, fetching each chunk's items concurrently.

        Lets callers render the first page before the whole batch arrives.
        Ranks are assigned sequentially across chunks (filtered items skipped).
        """
        count = PAGE_SIZE * (extra_page + 1)
        ids = self._story_ids(which)[:count]
        rank = 1
        for start in range(0, len(ids), chunk_size):
            batch = ids[start:start + chunk_size]
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
                items = list(pool.map(self._fetch_item, batch))
            chunk = []
            for item in items:
                story = self._build_story(item, rank)
                if story is not None:
                    chunk.append(story)
                    rank += 1
            yield chunk

    def _collect(self, which: str, extra_page: int) -> list[HackerNewsStory]:
        """Fetch the first N ids for 'which' and build all stories."""
        return [
            story
            for chunk in self.iter_stories(which, extra_page)
            for story in chunk]

    def get_top_stories(self, extra_page: int = 1) -> list[HackerNewsStory]:
        return self._collect("top", extra_page)

    def get_newest_stories(self, extra_page: int = 1) -> list[HackerNewsStory]:
        return self._collect("newest", extra_page)

    def get_best_stories(self, extra_page: int = 1) -> list[HackerNewsStory]:
        return self._collect("best", extra_page)

    def get_show_stories(self, extra_page: int = 1) -> list[HackerNewsStory]:
        return self._collect("show", extra_page)

    def get_show_newest_stories(self, extra_page: int = 1) -> list[HackerNewsStory]:
        return self._collect("show_newest", extra_page)

    def get_ask_stories(self, extra_page: int = 1) -> list[HackerNewsStory]:
        return self._collect("ask", extra_page)

    def get_jobs_stories(self, extra_page: int = 1) -> list[HackerNewsStory]:
        return self._collect("jobs", extra_page)

    def get_comments(
        self, item_id: int, max_comments: int = 50,
    ) -> list[HackerNewsComment]:
        """Fetch a story's comment tree, flattened depth-first with depth tags.

        Items are fetched breadth-first, one whole level at a time and fully
        concurrent, so a large thread is a handful of parallel batches rather
        than hundreds of serial round-trips. Display order is then a cheap
        depth-first walk over the items already in memory.
        """
        root = self._fetch_item(item_id)
        if not root:
            return []

        items: dict[int, dict] = {}
        frontier = list(root.get('kids', []))
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            while frontier and len(items) < max_comments:
                batch = frontier[:max_comments - len(items)]
                next_frontier: list[int] = []
                for cid, item in zip(
                        batch, pool.map(self._fetch_item, batch), strict=False):
                    if not item:
                        continue
                    items[cid] = item
                    next_frontier.extend(item.get('kids', []))
                frontier = next_frontier

        out: list[HackerNewsComment] = []

        def walk(kid_ids: list[int], depth: int) -> None:
            for cid in kid_ids:
                if len(out) >= max_comments:
                    return
                item = items.get(cid)
                if not item:
                    continue
                deleted = bool(item.get('deleted') or item.get('dead'))
                out.append(HackerNewsComment(
                    by=item.get('by'),
                    text="[deleted]" if deleted else _html_to_text(
                        item.get('text', '')),
                    published_time=(
                        _relative_time(item['time']) if item.get('time') else ""),
                    depth=depth,
                    deleted=deleted))
                walk(item.get('kids', []), depth + 1)

        walk(root.get('kids', []), 0)
        return out


class HackerNewsComment:
    """A single comment in a story's thread."""

    def __init__(
        self,
        by: str | None,
        text: str,
        published_time: str,
        depth: int,
        deleted: bool = False,
    ) -> None:
        self.by = by
        self.text = text
        self.published_time = published_time
        self.depth = depth
        self.deleted = deleted


class HackerNewsStory:
    """
    A class representing a story on Hacker News.
    """
    id: int | None = None            # The Hacker News ID of a story.
    number: int | str | None = None  # What rank the story is on HN.
    title: str = ""                  # The title of the story.
    domain: str = ""                 # The website the story is from.
    url: str = ""                    # The URL of the story.
    score: int | str | None = None   # Current score of the story.
    submitter: str | None = ""       # The person that submitted the story.
    submitter_url: str | None = None  # The submitter's user page.
    comment_count: int | None = None  # How many comments the story has.
    comments_url: str | None = ""     # The HN link for commenting.
    published_time: str | None = ""   # The time since story was published

    # Fields persisted to / restored from the JSON cache.
    _FIELDS = (
        "id", "number", "title", "domain", "url", "score", "submitter",
        "submitter_url", "comment_count", "comments_url", "published_time")

    def to_dict(self) -> dict:
        """Serialize to a plain dict for JSON storage."""
        return {field: getattr(self, field) for field in self._FIELDS}

    @classmethod
    def from_dict(cls, data: dict) -> HackerNewsStory:
        """Rebuild a story from a cached dict."""
        story = cls()
        for field in cls._FIELDS:
            setattr(story, field, data.get(field))
        return story

    def print_details(self) -> None:
        """
        Prints details of the story.
        """
        print(f"{self.number}: {self.title}")
        print(f"URL: {self.url}")
        print(f"domain: {self.domain}")
        print(f"score: {self.score} points")
        print(f"submitted by: {self.submitter}")
        print(f"since {self.published_time}")
        print(f"of comments: {self.comment_count}")
        print(f"'discuss' URL: {self.comments_url}")
        print(f"HN ID: {self.id}")
        print(" ")


class HackerNewsUser:
    """
    A class representing a user on Hacker News.
    """
    # Default value. I don't think anyone really has -10000 karma.
    karma: int = -10000
    name: str = ""  # The user's HN username.
    user_page_url: str = ""  # The URL of the user's 'user' page.
    threads_page_url: str = ""  # The URL of the user's 'threads' page.

    def __init__(self, username: str) -> None:
        """
        Constructor for the user class.
        """
        self.name = username
        self.user_page_url = USER_BASE + self.name
        self.threads_page_url = (
            f"https://news.ycombinator.com/threads?id={self.name}")
        self.refresh_karma()

    def refresh_karma(self) -> None:
        """Fetch the user's karma from the API."""
        data = HackerNewsAPI().fetch_json(f"{API_BASE}/user/{self.name}.json")
        if not data or 'karma' not in data:
            raise HNException("Error getting karma for user " + self.name)
        self.karma = int(data['karma'])
