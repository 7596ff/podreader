"""Transcript fetching — extractor dispatch, whisper fallback, skip logic."""


def resolve_transcript(entry, feed_name, feed_config, extractors, data_dir):
    """
    Resolve a transcript for an episode. Returns (transcript_text, transcript_path) or raises.

    Fallback chain:
    1. Extractor (web fetch + extract)
    2. Whisper (download audio + subprocess transcribe)
    3. Skip (no enclosure, no extractor)
    """
    raise NotImplementedError


def download_audio(url, cache_dir):
    """Download audio file to cache directory. Returns path to downloaded file."""
    raise NotImplementedError


def run_whisper(audio_path, model="base"):
    """Run whisper-timestamped as subprocess. Returns transcript text."""
    raise NotImplementedError
