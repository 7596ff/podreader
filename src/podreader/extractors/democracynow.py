"""Democracy Now transcript extractor."""

name = "democracynow"


def get_transcript_url(entry):
    raise NotImplementedError


def extract_transcript(html):
    raise NotImplementedError
