"""Tests for the remove command — config, state, and file cleanup."""

import os
import json
from podreader.config import load_config, save_config, add_feed
from podreader.state import load_state, save_state


def setup_feed(data_dir, feed_name="test-feed", url="https://example.com/feed.xml"):
    """Set up a feed with config, state, transcripts, and cache."""
    os.makedirs(data_dir, exist_ok=True)

    # Config
    config_path = os.path.join(data_dir, "config.toml")
    config = load_config(config_path)
    config = add_feed(config, feed_name, url)
    save_config(config, config_path)

    # State
    state_path = os.path.join(data_dir, "state.json")
    state = load_state(state_path)
    state[feed_name] = [
        {"guid": "ep1", "title": "Episode 1", "status": "processed", "transcript_path": "t.txt"},
    ]
    save_state(state, state_path)

    # Transcripts
    transcript_dir = os.path.join(data_dir, "transcripts", feed_name)
    os.makedirs(transcript_dir, exist_ok=True)
    with open(os.path.join(transcript_dir, "ep1.txt"), "w") as f:
        f.write("transcript text")

    # Cache
    cache_dir = os.path.join(data_dir, "cache", feed_name)
    os.makedirs(cache_dir, exist_ok=True)
    with open(os.path.join(cache_dir, "audio.mp3"), "w") as f:
        f.write("fake audio")

    return config_path, state_path


def test_remove_cleans_everything(tmp_path, monkeypatch):
    """Remove should delete config entry, state, transcripts, and cache."""
    data_dir = str(tmp_path)
    config_path, state_path = setup_feed(data_dir)

    # Patch DATA_DIR
    import podreader.cli as cli
    monkeypatch.setattr(cli, "DATA_DIR", data_dir)

    import argparse
    args = argparse.Namespace(feed="test-feed", keep_data=False)
    cli.cmd_remove(args)

    # Config should not have the feed
    config = load_config(config_path)
    assert "test-feed" not in config["feeds"]

    # State should not have the feed
    state = load_state(state_path)
    assert "test-feed" not in state

    # Transcripts should be gone
    assert not os.path.exists(os.path.join(data_dir, "transcripts", "test-feed"))

    # Cache should be gone
    assert not os.path.exists(os.path.join(data_dir, "cache", "test-feed"))


def test_remove_keep_data(tmp_path, monkeypatch):
    """Remove with --keep-data should only remove config entry."""
    data_dir = str(tmp_path)
    config_path, state_path = setup_feed(data_dir)

    import podreader.cli as cli
    monkeypatch.setattr(cli, "DATA_DIR", data_dir)

    import argparse
    args = argparse.Namespace(feed="test-feed", keep_data=True)
    cli.cmd_remove(args)

    # Config should not have the feed
    config = load_config(config_path)
    assert "test-feed" not in config["feeds"]

    # State should still exist
    state = load_state(state_path)
    assert "test-feed" in state

    # Transcripts should still exist
    assert os.path.exists(os.path.join(data_dir, "transcripts", "test-feed"))


def test_remove_nonexistent_raises(tmp_path, monkeypatch):
    """Remove a feed that doesn't exist should raise."""
    data_dir = str(tmp_path)
    config_path = os.path.join(data_dir, "config.toml")
    config = load_config(config_path)
    save_config(config, config_path)

    import podreader.cli as cli
    monkeypatch.setattr(cli, "DATA_DIR", data_dir)

    import argparse
    import pytest
    args = argparse.Namespace(feed="nonexistent", keep_data=False)
    with pytest.raises(KeyError):
        cli.cmd_remove(args)
