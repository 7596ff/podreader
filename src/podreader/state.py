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
