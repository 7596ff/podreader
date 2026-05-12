"""TOML config read/write for feed subscriptions and settings."""

import os
import tempfile
import tomllib
import tomli_w


DEFAULT_CONFIG = {
    "settings": {
        "whisper_model": "base",
        "max_cache_gb": 5,
    },
    "feeds": {},
}


def load_config(path):
    """Load config from TOML file. Returns default config if file doesn't exist."""
    if not os.path.exists(path):
        import copy
        return copy.deepcopy(DEFAULT_CONFIG)
    with open(path, "rb") as f:
        return tomllib.load(f)


def save_config(config, path):
    """Atomically write config to TOML file."""
    dir_name = os.path.dirname(path) or "."
    os.makedirs(dir_name, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            tomli_w.dump(config, f)
        os.replace(tmp_path, path)
    except:
        os.unlink(tmp_path)
        raise


def add_feed(config, name, url, extractor=None):
    """Add a feed to the config. Returns updated config."""
    if name in config["feeds"]:
        raise ValueError(f"Feed '{name}' already exists")
    feed = {"url": url}
    if extractor:
        feed["extractor"] = extractor
    config["feeds"][name] = feed
    return config


def remove_feed(config, name):
    """Remove a feed from the config. Returns updated config."""
    if name not in config["feeds"]:
        raise KeyError(f"Feed '{name}' not found")
    del config["feeds"][name]
    return config


def get_extractor_name(config, feed_name):
    """Return the extractor name for a feed, or None if not set."""
    if feed_name not in config["feeds"]:
        raise KeyError(f"Feed '{feed_name}' not found")
    return config["feeds"][feed_name].get("extractor")
