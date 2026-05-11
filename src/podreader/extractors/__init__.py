"""Extractor loading and dispatch."""

from podreader.extractors import npr, democracynow

BUILT_IN = {
    npr.name: npr,
    democracynow.name: democracynow,
}


def load_extractors():
    """Load built-in extractors. Returns dict of name -> module."""
    return dict(BUILT_IN)
