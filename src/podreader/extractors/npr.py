"""NPR transcript extractor."""

name = "npr"


def get_transcript_url(entry):
    raise NotImplementedError


def extract_transcript(html):
    raise NotImplementedError
