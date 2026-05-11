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
