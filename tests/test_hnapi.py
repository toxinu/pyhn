"""HackerNewsAPI tests against the Firebase JSON API.

No network: fetch_json is monkeypatched to serve canned items by URL.
"""
import pytest

from pyhn.hnapi import (
    HackerNewsAPI,
    HackerNewsStory,
    HackerNewsUser,
    HNException,
    _html_to_text,
    _relative_time,
)

# A small in-memory HN: id -> item payload.
ITEMS = {
    1: {"id": 1, "type": "story", "by": "alice", "time": 1175714200,
        "title": "First &amp; foremost", "url": "https://example.com/a",
        "score": 100, "descendants": 12},
    2: {"id": 2, "type": "story", "by": "bob", "time": 1175714200,
        "title": "Ask HN: no url here", "score": 5, "descendants": 3},  # text post
    3: {"id": 3, "type": "job", "by": "corp", "time": 1175714200,
        "title": "We are hiring", "url": "", "score": 1},  # job, empty url, no descendants
    4: {"id": 4, "type": "story", "deleted": True},  # filtered
    5: {"id": 5, "type": "story", "dead": True, "title": "spam"},  # filtered
}
TOP_IDS = [1, 2, 3, 4, 5]


def _api(monkeypatch, ids=TOP_IDS, items=ITEMS):
    api = HackerNewsAPI()

    def fake_fetch_json(url):
        if url.endswith("topstories.json"):
            return ids
        if "/item/" in url:
            item_id = int(url.split("/item/")[1].split(".json")[0])
            return items.get(item_id)
        raise AssertionError("unexpected url: " + url)

    monkeypatch.setattr(api, "fetch_json", fake_fetch_json)
    return api


def test_get_top_stories_ranks_and_fields(monkeypatch):
    stories = _api(monkeypatch).get_top_stories(extra_page=0)
    # ids 4 and 5 (deleted/dead) are dropped; ranks stay contiguous.
    assert [s.id for s in stories] == [1, 2, 3]
    assert [s.number for s in stories] == [1, 2, 3]
    first = stories[0]
    assert first.score == 100
    assert first.comment_count == 12
    assert first.submitter == "alice"
    assert first.submitter_url.endswith("user?id=alice")
    assert first.comments_url == "https://news.ycombinator.com/item?id=1"


def test_title_is_unescaped(monkeypatch):
    first = _api(monkeypatch).get_top_stories(extra_page=0)[0]
    assert first.title == "First & foremost"


def test_text_post_url_falls_back_to_comments(monkeypatch):
    ask = _api(monkeypatch).get_top_stories(extra_page=0)[1]
    assert ask.url == ask.comments_url == "https://news.ycombinator.com/item?id=2"


def test_job_empty_url_falls_back_to_comments(monkeypatch):
    job = _api(monkeypatch).get_top_stories(extra_page=0)[2]
    assert job.url == job.comments_url
    assert job.comment_count is None  # no descendants field


def test_extra_page_limits_item_count(monkeypatch):
    requested = []
    ids = list(range(1, 101))

    def fake(url):
        if url.endswith("topstories.json"):
            return ids
        item_id = int(url.split("/item/")[1].split(".json")[0])
        requested.append(item_id)
        return {"id": item_id, "title": "t", "time": 1175714200,
                "by": "x", "score": 1, "descendants": 0}

    api = HackerNewsAPI()
    monkeypatch.setattr(api, "fetch_json", fake)
    api.get_top_stories(extra_page=0)
    assert len(requested) == 30  # PAGE_SIZE * (0 + 1)


def test_unknown_section_raises(monkeypatch):
    api = _api(monkeypatch)
    with pytest.raises(ValueError):
        api._story_ids("nonsense")


def test_fetch_json_wraps_errors(monkeypatch):
    import pyhn.hnapi as hnapi

    def boom(*args, **kwargs):
        raise OSError("no network")

    monkeypatch.setattr(hnapi.requests, "get", boom)
    with pytest.raises(HNException):
        HackerNewsAPI().fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")


@pytest.mark.parametrize("delta_seconds,expected", [
    (5, "5 seconds ago"),
    (1, "1 second ago"),
    (60, "1 minute ago"),
    (180, "3 minutes ago"),
    (3600, "1 hour ago"),
    (7200, "2 hours ago"),
    (86400, "1 day ago"),
    (172800, "2 days ago"),
    (0, "just now"),
])
def test_relative_time(delta_seconds, expected):
    now = 2_000_000_000
    assert _relative_time(now - delta_seconds, now=now) == expected


def test_refresh_karma(monkeypatch):
    import pyhn.hnapi as hnapi
    monkeypatch.setattr(
        hnapi.HackerNewsAPI, "fetch_json",
        lambda self, url: {"id": "alice", "karma": 4242})
    user = HackerNewsUser("alice")
    assert user.karma == 4242


def test_refresh_karma_missing_raises(monkeypatch):
    import pyhn.hnapi as hnapi
    monkeypatch.setattr(
        hnapi.HackerNewsAPI, "fetch_json", lambda self, url: None)
    with pytest.raises(HNException):
        HackerNewsUser("ghost")


def test_story_dict_roundtrip(monkeypatch):
    story = _api(monkeypatch).get_top_stories(extra_page=0)[0]
    restored = HackerNewsStory.from_dict(story.to_dict())
    assert restored.to_dict() == story.to_dict()


def test_iter_stories_chunks(monkeypatch):
    # 100 valid ids, chunk_size 30 -> 30,30,30,10.
    ids = list(range(1, 101))

    def fake(url):
        if url.endswith("topstories.json"):
            return ids
        item_id = int(url.split("/item/")[1].split(".json")[0])
        return {"id": item_id, "title": "t", "time": 1175714200,
                "by": "x", "score": 1, "descendants": 0}

    api = HackerNewsAPI()
    monkeypatch.setattr(api, "fetch_json", fake)

    chunks = list(api.iter_stories("top", extra_page=3, chunk_size=30))
    assert [len(c) for c in chunks] == [30, 30, 30, 10]
    flat = [s for c in chunks for s in c]
    assert [s.number for s in flat] == list(range(1, 101))  # contiguous ranks


def test_collect_equals_iter_concat(monkeypatch):
    stories = _api(monkeypatch).get_top_stories(extra_page=0)
    api2 = _api(monkeypatch)
    flat = [s for c in api2.iter_stories("top", extra_page=0) for s in c]
    assert [s.id for s in stories] == [s.id for s in flat]


def test_html_to_text():
    assert _html_to_text("Hi &amp; <i>bye</i>") == "Hi & bye"
    assert _html_to_text("a<p>b") == "a\n\nb"
    assert _html_to_text('see <a href="http://x">link</a>') == "see link"
    assert _html_to_text("") == ""


# A small comment tree: story 100 has kids 200 (with child 300) and 201.
COMMENT_ITEMS = {
    100: {"id": 100, "type": "story", "kids": [200, 201]},
    200: {"id": 200, "type": "comment", "by": "alice", "time": 1175714200,
          "text": "top &amp; level", "kids": [300]},
    300: {"id": 300, "type": "comment", "by": "bob", "time": 1175714200,
          "text": "<p>reply"},
    201: {"id": 201, "type": "comment", "deleted": True, "time": 1175714200},
}


def _comment_api(monkeypatch, items=COMMENT_ITEMS):
    api = HackerNewsAPI()

    def fake(url):
        item_id = int(url.split("/item/")[1].split(".json")[0])
        return items.get(item_id)

    monkeypatch.setattr(api, "fetch_json", fake)
    return api


def test_get_comments_depth_and_order(monkeypatch):
    comments = _comment_api(monkeypatch).get_comments(100)
    assert [(c.by, c.depth) for c in comments] == [
        ("alice", 0), ("bob", 1), (None, 0)]
    assert comments[0].text == "top & level"
    assert comments[2].deleted is True
    assert comments[2].text == "[deleted]"


def test_get_comments_respects_cap(monkeypatch):
    comments = _comment_api(monkeypatch).get_comments(100, max_comments=1)
    assert len(comments) == 1
