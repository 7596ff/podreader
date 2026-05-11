"""RSS fetching and episode list management."""

import feedparser
from podreader.state import guid_or_fallback


def fetch_feed(url):
    """Fetch and parse an RSS feed. Returns a feedparser feed object."""
    return feedparser.parse(url)


def new_episodes(feed, existing_state):
    """Return episodes from feed that are not already in state. Handles missing guids."""
    episodes = []
    for entry in feed.entries:
        guid = guid_or_fallback(entry)
        if guid not in existing_state:
            episodes.append(entry)
    return episodes
