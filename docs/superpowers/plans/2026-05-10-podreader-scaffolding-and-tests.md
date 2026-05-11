# Podreader — Scaffolding & Tests

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up the project structure and write all failing tests for podreader's TDD targets. No implementation — just red.

**Architecture:** Python package with `uv`, pytest for testing. Tests cover state management, config, episode matching, and the transcript fallback chain. All tests should fail for the right reasons (missing logic, not import errors).

**Tech Stack:** Python 3.11+, uv, pytest, feedparser (test fixtures only)

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/podreader/__init__.py`
- Create: `src/podreader/state.py`
- Create: `src/podreader/config.py`
- Create: `src/podreader/feeds.py`
- Create: `src/podreader/transcripts.py`
- Create: `src/podreader/cli.py`
- Create: `src/podreader/extractors/__init__.py`
- Create: `src/podreader/extractors/npr.py`
- Create: `src/podreader/extractors/democracynow.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "podreader"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "feedparser",
    "requests",
    "beautifulsoup4",
    "tomli-w",
]

[project.optional-dependencies]
whisper = ["whisper-timestamped"]

[project.scripts]
podreader = "podreader.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/podreader"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create module stubs**

```python
# src/podreader/__init__.py
```

```python
# src/podreader/state.py
"""Episode state management — JSON read/write, status transitions, slug generation."""

import hashlib
import json
import os
import re
import tempfile


def load_state(path):
    """Load state from JSON file. Returns empty dict if file doesn't exist."""
    raise NotImplementedError


def save_state(state, path):
    """Atomically write state to JSON file using write-to-temp + os.replace."""
    raise NotImplementedError


def slugify(title, pub_date, guid):
    """Generate a collision-proof filename slug from title + date + short hash of guid."""
    raise NotImplementedError


def guid_or_fallback(entry):
    """Return the entry's guid, or sha256(link + title) if missing."""
    raise NotImplementedError


def transition_status(current, target):
    """Validate and return a status transition. Raises ValueError if invalid."""
    raise NotImplementedError
```

```python
# src/podreader/config.py
"""TOML config read/write for feed subscriptions and settings."""

import tomllib
import tomli_w


def load_config(path):
    """Load config from TOML file. Returns default config if file doesn't exist."""
    raise NotImplementedError


def save_config(config, path):
    """Atomically write config to TOML file."""
    raise NotImplementedError


def add_feed(config, name, url, extractor=None):
    """Add a feed to the config. Returns updated config."""
    raise NotImplementedError


def remove_feed(config, name):
    """Remove a feed from the config. Returns updated config."""
    raise NotImplementedError


def get_extractor_name(config, feed_name):
    """Return the extractor name for a feed, or None if not set."""
    raise NotImplementedError
```

```python
# src/podreader/feeds.py
"""RSS fetching and episode list management."""


def fetch_feed(url):
    """Fetch and parse an RSS feed. Returns a feedparser feed object."""
    raise NotImplementedError


def new_episodes(feed, existing_state):
    """Return episodes from feed that are not already in state. Handles missing guids."""
    raise NotImplementedError
```

```python
# src/podreader/transcripts.py
"""Transcript fetching — extractor dispatch, whisper fallback, skip logic."""


def resolve_transcript(entry, feed_name, feed_config, extractors, data_dir):
    """
    Resolve a transcript for an episode. Returns (transcript_text, transcript_path) or raises.

    Fallback chain:
    1. Extractor (web fetch + extract)
    2. Whisper (download audio + subprocess transcribe)
    3. Skip (no enclosure, no extractor)
    """
    raise NotImplementedError


def run_whisper(audio_path, model="base"):
    """Run whisper-timestamped as subprocess. Returns transcript text."""
    raise NotImplementedError
```

```python
# src/podreader/cli.py
"""CLI argument parsing and command dispatch."""


def main():
    print("podreader: not yet implemented")
```

```python
# src/podreader/extractors/__init__.py
"""Extractor loading and dispatch."""


def load_extractors():
    """Load built-in extractors. Returns dict of name -> module."""
    raise NotImplementedError
```

```python
# src/podreader/extractors/npr.py
"""NPR transcript extractor."""

name = "npr"


def get_transcript_url(entry):
    raise NotImplementedError


def extract_transcript(html):
    raise NotImplementedError
```

```python
# src/podreader/extractors/democracynow.py
"""Democracy Now transcript extractor."""

name = "democracynow"


def get_transcript_url(entry):
    raise NotImplementedError


def extract_transcript(html):
    raise NotImplementedError
```

- [ ] **Step 3: Initialize with uv and verify**

```bash
cd ~/podreader
uv venv
uv pip install -e ".[whisper]"
uv run python -c "import podreader; print('ok')"
```

Expected: prints `ok`.

- [ ] **Step 4: Verify pytest runs**

```bash
cd ~/podreader && uv run pytest --co
```

Expected: "no tests ran" (no test files yet).

---

### Task 2: State Management Tests

**Files:**
- Create: `tests/test_state.py`

- [ ] **Step 1: Write tests for state read/write and atomic saves**

```python
# tests/test_state.py
import json
import os
import pytest
from podreader.state import (
    load_state,
    save_state,
    slugify,
    guid_or_fallback,
    transition_status,
)


class TestLoadState:
    def test_load_existing_state(self, tmp_path):
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({
            "my-feed": {
                "guid-123": {
                    "title": "Episode One",
                    "status": "unprocessed",
                    "pub_date": "2026-05-10",
                }
            }
        }))
        state = load_state(str(state_file))
        assert "my-feed" in state
        assert state["my-feed"]["guid-123"]["title"] == "Episode One"

    def test_load_missing_file_returns_empty(self, tmp_path):
        state = load_state(str(tmp_path / "nonexistent.json"))
        assert state == {}


class TestSaveState:
    def test_save_and_reload(self, tmp_path):
        state_file = tmp_path / "state.json"
        state = {"feed": {"guid": {"title": "Ep", "status": "unprocessed"}}}
        save_state(state, str(state_file))
        loaded = load_state(str(state_file))
        assert loaded == state

    def test_atomic_write_does_not_corrupt_on_existing(self, tmp_path):
        state_file = tmp_path / "state.json"
        original = {"feed": {"guid": {"title": "Original", "status": "processed"}}}
        save_state(original, str(state_file))
        # Save again — should not leave partial writes
        updated = {"feed": {"guid": {"title": "Updated", "status": "processed"}}}
        save_state(updated, str(state_file))
        loaded = load_state(str(state_file))
        assert loaded["feed"]["guid"]["title"] == "Updated"


class TestSlugify:
    def test_basic_slug(self):
        slug = slugify("Friday Headlines", "2026-05-09", "abc123")
        assert "friday-headlines" in slug
        assert "2026-05-09" in slug
        # Short hash of guid should be present
        assert len(slug) > len("2026-05-09-friday-headlines")

    def test_special_characters_removed(self):
        slug = slugify("What's Next? (Part 1)", "2026-05-09", "xyz")
        assert "?" not in slug
        assert "'" not in slug
        assert "(" not in slug

    def test_same_title_different_guid_different_slug(self):
        slug1 = slugify("Daily News", "2026-05-09", "guid-aaa")
        slug2 = slugify("Daily News", "2026-05-09", "guid-bbb")
        assert slug1 != slug2


class TestGuidOrFallback:
    def test_entry_with_guid(self):
        class Entry:
            id = "real-guid-123"
            link = "https://example.com/ep1"
            title = "Episode One"
        result = guid_or_fallback(Entry())
        assert result == "real-guid-123"

    def test_entry_without_guid_uses_hash(self):
        class Entry:
            id = None
            link = "https://example.com/ep1"
            title = "Episode One"
        result = guid_or_fallback(Entry())
        assert len(result) == 64  # sha256 hex digest

    def test_fallback_is_deterministic(self):
        class Entry:
            id = None
            link = "https://example.com/ep1"
            title = "Episode One"
        r1 = guid_or_fallback(Entry())
        r2 = guid_or_fallback(Entry())
        assert r1 == r2

    def test_different_entries_different_fallbacks(self):
        class Entry1:
            id = None
            link = "https://example.com/ep1"
            title = "Episode One"
        class Entry2:
            id = None
            link = "https://example.com/ep2"
            title = "Episode Two"
        assert guid_or_fallback(Entry1()) != guid_or_fallback(Entry2())


class TestTransitionStatus:
    def test_unprocessed_to_transcript_fetched(self):
        assert transition_status("unprocessed", "transcript-fetched") == "transcript-fetched"

    def test_transcript_fetched_to_processed(self):
        assert transition_status("transcript-fetched", "processed") == "processed"

    def test_unprocessed_to_skipped(self):
        assert transition_status("unprocessed", "skipped") == "skipped"

    def test_unprocessed_to_failed(self):
        assert transition_status("unprocessed", "failed") == "failed"

    def test_invalid_transition_raises(self):
        with pytest.raises(ValueError):
            transition_status("processed", "unprocessed")

    def test_skipped_is_terminal(self):
        with pytest.raises(ValueError):
            transition_status("skipped", "transcript-fetched")

    def test_failed_can_retry(self):
        assert transition_status("failed", "unprocessed") == "unprocessed"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/podreader && uv run pytest tests/test_state.py -v
```

Expected: All tests FAIL with `NotImplementedError`.

---

### Task 3: Config Tests

**Files:**
- Create: `tests/test_config.py`

- [ ] **Step 1: Write tests for config read/write and feed management**

```python
# tests/test_config.py
import pytest
from podreader.config import (
    load_config,
    save_config,
    add_feed,
    remove_feed,
    get_extractor_name,
)


class TestLoadConfig:
    def test_load_existing_config(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[settings]
whisper_model = "base"
max_cache_gb = 5

[feeds.my-feed]
url = "https://example.com/feed.xml"
extractor = "npr"
""")
        config = load_config(str(config_file))
        assert config["settings"]["whisper_model"] == "base"
        assert config["feeds"]["my-feed"]["url"] == "https://example.com/feed.xml"

    def test_load_missing_file_returns_defaults(self, tmp_path):
        config = load_config(str(tmp_path / "nonexistent.toml"))
        assert "settings" in config
        assert "feeds" in config
        assert config["feeds"] == {}


class TestSaveConfig:
    def test_save_and_reload(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config = {
            "settings": {"whisper_model": "base", "max_cache_gb": 5},
            "feeds": {"test": {"url": "https://example.com/feed.xml"}},
        }
        save_config(config, str(config_file))
        loaded = load_config(str(config_file))
        assert loaded["feeds"]["test"]["url"] == "https://example.com/feed.xml"


class TestAddFeed:
    def test_add_feed_basic(self):
        config = {"settings": {}, "feeds": {}}
        config = add_feed(config, "my-pod", "https://example.com/feed.xml")
        assert "my-pod" in config["feeds"]
        assert config["feeds"]["my-pod"]["url"] == "https://example.com/feed.xml"

    def test_add_feed_with_extractor(self):
        config = {"settings": {}, "feeds": {}}
        config = add_feed(config, "npr-news", "https://feeds.npr.org/feed.xml", extractor="npr")
        assert config["feeds"]["npr-news"]["extractor"] == "npr"

    def test_add_duplicate_raises(self):
        config = {"settings": {}, "feeds": {"my-pod": {"url": "https://example.com"}}}
        with pytest.raises(ValueError):
            add_feed(config, "my-pod", "https://other.com")


class TestRemoveFeed:
    def test_remove_existing(self):
        config = {"settings": {}, "feeds": {"my-pod": {"url": "https://example.com"}}}
        config = remove_feed(config, "my-pod")
        assert "my-pod" not in config["feeds"]

    def test_remove_nonexistent_raises(self):
        config = {"settings": {}, "feeds": {}}
        with pytest.raises(KeyError):
            remove_feed(config, "nope")


class TestGetExtractorName:
    def test_feed_with_extractor(self):
        config = {"feeds": {"npr": {"url": "...", "extractor": "npr"}}}
        assert get_extractor_name(config, "npr") == "npr"

    def test_feed_without_extractor(self):
        config = {"feeds": {"pod": {"url": "..."}}}
        assert get_extractor_name(config, "pod") is None

    def test_nonexistent_feed_raises(self):
        config = {"feeds": {}}
        with pytest.raises(KeyError):
            get_extractor_name(config, "nope")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/podreader && uv run pytest tests/test_config.py -v
```

Expected: All tests FAIL with `NotImplementedError`.

---

### Task 4: Episode Matching Tests

**Files:**
- Create: `tests/test_matching.py`
- Create: `src/podreader/matching.py`

- [ ] **Step 1: Create matching module stub**

```python
# src/podreader/matching.py
"""Episode matching — resolve episode references by guid, title substring, or index."""


def resolve_episode(feed_state, reference, latest=False):
    """
    Resolve an episode reference against feed state.

    reference can be:
    - A guid (exact match)
    - A title substring (fuzzy match)
    - An integer index

    Returns the guid of the matched episode.
    Raises ValueError on no match or ambiguous match (unless latest=True).
    """
    raise NotImplementedError
```

- [ ] **Step 2: Write matching tests**

```python
# tests/test_matching.py
import pytest
from podreader.matching import resolve_episode

FEED_STATE = {
    "guid-aaa": {
        "title": "Monday Headlines",
        "status": "unprocessed",
        "pub_date": "2026-05-05",
    },
    "guid-bbb": {
        "title": "Tuesday Headlines",
        "status": "transcript-fetched",
        "pub_date": "2026-05-06",
    },
    "guid-ccc": {
        "title": "Wednesday Headlines",
        "status": "processed",
        "pub_date": "2026-05-07",
    },
    "guid-ddd": {
        "title": "The Oil Crisis",
        "status": "unprocessed",
        "pub_date": "2026-05-08",
    },
    "guid-eee": {
        "title": "The Oil Crisis: Part 2",
        "status": "unprocessed",
        "pub_date": "2026-05-09",
    },
}


class TestResolveByGuid:
    def test_exact_guid_match(self):
        assert resolve_episode(FEED_STATE, "guid-aaa") == "guid-aaa"

    def test_nonexistent_guid_raises(self):
        with pytest.raises(ValueError):
            resolve_episode(FEED_STATE, "guid-zzz")


class TestResolveByTitle:
    def test_unique_substring_match(self):
        assert resolve_episode(FEED_STATE, "Monday") == "guid-aaa"

    def test_case_insensitive(self):
        assert resolve_episode(FEED_STATE, "monday") == "guid-aaa"

    def test_ambiguous_match_raises(self):
        with pytest.raises(ValueError, match="Ambiguous"):
            resolve_episode(FEED_STATE, "Oil Crisis")

    def test_ambiguous_with_latest_picks_most_recent(self):
        result = resolve_episode(FEED_STATE, "Oil Crisis", latest=True)
        assert result == "guid-eee"  # 2026-05-09 is more recent

    def test_no_match_raises(self):
        with pytest.raises(ValueError):
            resolve_episode(FEED_STATE, "xyzzy nonexistent")


class TestResolveByIndex:
    def test_index_zero(self):
        result = resolve_episode(FEED_STATE, "0")
        # Index 0 should return the first episode (sorted by date)
        assert result == "guid-aaa"

    def test_index_last(self):
        result = resolve_episode(FEED_STATE, "4")
        assert result == "guid-eee"

    def test_index_out_of_range_raises(self):
        with pytest.raises(ValueError):
            resolve_episode(FEED_STATE, "99")

    def test_negative_index(self):
        result = resolve_episode(FEED_STATE, "-1")
        assert result == "guid-eee"  # latest
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd ~/podreader && uv run pytest tests/test_matching.py -v
```

Expected: All tests FAIL with `NotImplementedError`.

---

### Task 5: Transcript Fallback Chain Tests

**Files:**
- Create: `tests/test_transcripts.py`

- [ ] **Step 1: Write fallback chain tests**

```python
# tests/test_transcripts.py
import pytest
from unittest.mock import MagicMock, patch
from podreader.transcripts import resolve_transcript


def make_entry(title="Test Episode", link="https://example.com/ep1",
               audio_url="https://example.com/ep1.mp3", has_enclosure=True):
    entry = MagicMock()
    entry.title = title
    entry.link = link
    if has_enclosure:
        entry.enclosures = [{"href": audio_url, "type": "audio/mpeg"}]
    else:
        entry.enclosures = []
    return entry


def make_extractor(url="https://example.com/transcript", text="Transcript text here."):
    extractor = MagicMock()
    extractor.get_transcript_url = MagicMock(return_value=url)
    extractor.extract_transcript = MagicMock(return_value=text)
    return extractor


class TestFallbackChain:
    def test_extractor_succeeds(self, tmp_path):
        entry = make_entry()
        extractor = make_extractor()
        extractors = {"test-extractor": extractor}
        feed_config = {"extractor": "test-extractor"}

        text, path = resolve_transcript(
            entry, "test-feed", feed_config, extractors, str(tmp_path)
        )
        assert text == "Transcript text here."
        assert path is not None
        extractor.get_transcript_url.assert_called_once_with(entry)
        extractor.extract_transcript.assert_called_once()

    def test_extractor_returns_none_falls_back_to_whisper(self, tmp_path):
        entry = make_entry()
        extractor = make_extractor()
        extractor.get_transcript_url.return_value = None
        extractors = {"test-extractor": extractor}
        feed_config = {"extractor": "test-extractor"}

        with patch("podreader.transcripts.run_whisper", return_value="Whisper output") as mock_whisper:
            with patch("podreader.transcripts.download_audio", return_value=str(tmp_path / "audio.mp3")):
                text, path = resolve_transcript(
                    entry, "test-feed", feed_config, extractors, str(tmp_path)
                )
        assert text == "Whisper output"
        mock_whisper.assert_called_once()

    def test_no_extractor_uses_whisper(self, tmp_path):
        entry = make_entry()
        extractors = {}
        feed_config = {}  # no extractor field

        with patch("podreader.transcripts.run_whisper", return_value="Whisper output") as mock_whisper:
            with patch("podreader.transcripts.download_audio", return_value=str(tmp_path / "audio.mp3")):
                text, path = resolve_transcript(
                    entry, "test-feed", feed_config, extractors, str(tmp_path)
                )
        assert text == "Whisper output"

    def test_whisper_fails_raises(self, tmp_path):
        entry = make_entry()
        extractors = {}
        feed_config = {}

        with patch("podreader.transcripts.run_whisper", side_effect=RuntimeError("Whisper crashed")):
            with patch("podreader.transcripts.download_audio", return_value=str(tmp_path / "audio.mp3")):
                with pytest.raises(RuntimeError, match="Whisper crashed"):
                    resolve_transcript(
                        entry, "test-feed", feed_config, extractors, str(tmp_path)
                    )

    def test_no_enclosure_no_extractor_raises_skip(self, tmp_path):
        entry = make_entry(has_enclosure=False)
        extractors = {}
        feed_config = {}

        with pytest.raises(ValueError, match="[Ss]kip"):
            resolve_transcript(
                entry, "test-feed", feed_config, extractors, str(tmp_path)
            )
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/podreader && uv run pytest tests/test_transcripts.py -v
```

Expected: All tests FAIL with `NotImplementedError`.

---

### Task 6: Feed Parsing Tests

**Files:**
- Create: `tests/test_feeds.py`
- Create: `tests/fixtures/sample_feed.xml`

- [ ] **Step 1: Create a test RSS fixture**

```xml
<!-- tests/fixtures/sample_feed.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Podcast</title>
    <item>
      <title>Episode One</title>
      <link>https://example.com/ep1</link>
      <guid>guid-001</guid>
      <pubDate>Mon, 05 May 2026 12:00:00 +0000</pubDate>
      <enclosure url="https://example.com/ep1.mp3" type="audio/mpeg" length="1000000"/>
    </item>
    <item>
      <title>Episode Two</title>
      <link>https://example.com/ep2</link>
      <guid>guid-002</guid>
      <pubDate>Tue, 06 May 2026 12:00:00 +0000</pubDate>
      <enclosure url="https://example.com/ep2.mp3" type="audio/mpeg" length="2000000"/>
    </item>
    <item>
      <title>Episode Three (No GUID)</title>
      <link>https://example.com/ep3</link>
      <pubDate>Wed, 07 May 2026 12:00:00 +0000</pubDate>
      <enclosure url="https://example.com/ep3.mp3" type="audio/mpeg" length="3000000"/>
    </item>
    <item>
      <title>Announcement (No Audio)</title>
      <link>https://example.com/announce</link>
      <guid>guid-004</guid>
      <pubDate>Thu, 08 May 2026 12:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>
```

- [ ] **Step 2: Write feed parsing tests**

```python
# tests/test_feeds.py
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
        # Episode Three has no guid — should still be included with a fallback key
        titles = [ep.title for ep in episodes]
        assert "Episode Three (No GUID)" in titles

    def test_includes_episodes_without_enclosure(self):
        feed = parse_fixture()
        episodes = new_episodes(feed, {})
        titles = [ep.title for ep in episodes]
        assert "Announcement (No Audio)" in titles
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd ~/podreader && uv run pytest tests/test_feeds.py -v
```

Expected: All tests FAIL with `NotImplementedError`.

---

### Task 7: Commit Everything

- [ ] **Step 1: Stage and commit**

```bash
cd ~/podreader
git add -A
git commit -m "scaffold and tests: project structure, state, config, matching, transcripts, feeds — all red"
```
