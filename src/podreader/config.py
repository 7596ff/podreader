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
