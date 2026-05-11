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
        updated = {"feed": {"guid": {"title": "Updated", "status": "processed"}}}
        save_state(updated, str(state_file))
        loaded = load_state(str(state_file))
        assert loaded["feed"]["guid"]["title"] == "Updated"


class TestSlugify:
    def test_basic_slug(self):
        slug = slugify("Friday Headlines", "2026-05-09", "abc123")
        assert "friday-headlines" in slug
        assert "2026-05-09" in slug
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
