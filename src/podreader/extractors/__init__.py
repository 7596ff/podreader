"""Extractor loading and dispatch."""

import importlib.util
import os
import sys

from podreader.extractors import npr, democracynow

BUILT_IN = {
    npr.name: npr,
    democracynow.name: democracynow,
}


def load_extractors(user_dir=None):
    """Load built-in extractors, then overlay user-defined ones from user_dir.

    User extractors are .py files with a `name` attribute and
    `get_transcript_url(entry)` and `extract_transcript(html)` functions.
    User extractors override built-ins if they share a name.
    """
    extractors = dict(BUILT_IN)

    if user_dir is None:
        user_dir = os.path.expanduser("~/.podreader/extractors")

    if not os.path.isdir(user_dir):
        return extractors

    for filename in sorted(os.listdir(user_dir)):
        if not filename.endswith(".py") or filename.startswith("_"):
            continue

        filepath = os.path.join(user_dir, filename)
        module_name = f"podreader_user_extractor_{filename[:-3]}"

        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception as e:
            # Syntax errors, import errors, etc — skip silently
            continue

        if not hasattr(mod, "name"):
            continue

        extractors[mod.name] = mod

    return extractors
