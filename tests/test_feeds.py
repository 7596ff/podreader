import os
import feedparser
import pytest
from podreader.feeds import new_episodes
from podreader.state import guid_or_fallback


def fixture_path():
    return os.path.join(os.path.dirname(__file__), "fixtures", "sample_feed.xml")


def parse_fixture():
    return feedparser.parse(fixture_path())


class TestNewEpisodes:
    def test_all_new_when_state_empty(self):
        feed = parse_fixture()
        episodes = new_episodes(feed, {})
        assert len(episodes) == 4

    def test_skips_already_known(self):
        feed = parse_fixture()
        existing = {"guid-001": {"title": "Episode One", "status": "processed"}}
        episodes = new_episodes(feed, existing)
        guids = [guid_or_fallback(ep) for ep in episodes]
        assert "guid-001" not in guids
        assert len(episodes) == 3

    def test_handles_missing_guid(self):
        feed = parse_fixture()
        episodes = new_episodes(feed, {})
        titles = [ep.title for ep in episodes]
        assert "Episode Three (No GUID)" in titles

    def test_includes_episodes_without_enclosure(self):
        feed = parse_fixture()
        episodes = new_episodes(feed, {})
        titles = [ep.title for ep in episodes]
        assert "Announcement (No Audio)" in titles
