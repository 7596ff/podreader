"""RSS fetching and episode list management."""


def fetch_feed(url):
    """Fetch and parse an RSS feed. Returns a feedparser feed object."""
    raise NotImplementedError


def new_episodes(feed, existing_state):
    """Return episodes from feed that are not already in state. Handles missing guids."""
    raise NotImplementedError
