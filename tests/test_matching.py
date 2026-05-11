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
