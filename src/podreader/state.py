"""Episode state management — JSON read/write, status transitions, slug generation."""

import hashlib
import json
import os
import re
import tempfile


# Valid status transitions: {current_status: {allowed_targets}}
VALID_TRANSITIONS = {
    "unprocessed": {"transcript-fetched", "skipped", "failed"},
    "transcript-fetched": {"processed"},
    "failed": {"unprocessed"},  # retry
    # processed and skipped are terminal
}


def load_state(path):
    """Load state from JSON file. Returns empty dict if file doesn't exist."""
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def save_state(state, path):
    """Atomically write state to JSON file using write-to-temp + os.replace."""
    dir_name = os.path.dirname(path) or "."
    os.makedirs(dir_name, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp_path, path)
    except:
        os.unlink(tmp_path)
        raise


def slugify(title, pub_date, guid):
    """Generate a collision-proof filename slug from title + date + short hash of guid."""
    # Clean title: lowercase, replace non-alphanumeric with hyphens, collapse multiples
    clean = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    # Short hash of guid for collision-proofing
    short_hash = hashlib.sha256(guid.encode()).hexdigest()[:8]
    return f"{pub_date}-{clean}-{short_hash}"


def guid_or_fallback(entry):
    """Return the entry's guid, or sha256(link + title) if missing."""
    guid = getattr(entry, "id", None)
    if guid and isinstance(guid, str):
        return guid
    # Fallback: hash of link + title
    link = getattr(entry, "link", "")
    title = getattr(entry, "title", "")
    return hashlib.sha256(f"{link}{title}".encode()).hexdigest()


def transition_status(current, target):
    """Validate and return a status transition. Raises ValueError if invalid."""
    allowed = VALID_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise ValueError(
            f"Invalid status transition: {current} → {target}. "
            f"Allowed from {current}: {allowed or 'none (terminal state)'}"
        )
    return target
