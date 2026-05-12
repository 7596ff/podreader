"""Transcript fetching — extractor dispatch, whisper fallback, skip logic."""

import inspect
import os
import requests


def resolve_transcript(entry, feed_name, feed_config, extractors, data_dir):
    """
    Resolve a transcript for an episode. Returns (transcript_text, transcript_path) or raises.

    Fallback chain:
    1. Extractor (web fetch + extract)
    2. Whisper (download audio + faster-whisper transcribe)
    3. Skip (no enclosure, no extractor) — raises ValueError
    """
    extractor_name = feed_config.get("extractor")

    # Try extractor path
    if extractor_name and extractor_name in extractors:
        extractor = extractors[extractor_name]
        url = extractor.get_transcript_url(entry)
        if url is not None:
            response = requests.get(url)
            # Pass source_url if the extractor accepts it
            sig = inspect.signature(extractor.extract_transcript)
            if "source_url" in sig.parameters:
                text = extractor.extract_transcript(response.text, source_url=url)
            else:
                text = extractor.extract_transcript(response.text)
            path = _save_transcript(text, feed_name, entry, data_dir)
            return text, path

    # Try whisper path — need an audio enclosure
    enclosures = getattr(entry, "enclosures", [])
    if enclosures:
        audio_url = enclosures[0].get("href") if isinstance(enclosures[0], dict) else enclosures[0].href
        cache_dir = os.path.join(data_dir, "cache", feed_name)
        audio_path = download_audio(audio_url, cache_dir)
        model = feed_config.get("whisper_model", "base")
        text = run_whisper(audio_path, model=model)
        path = _save_transcript(text, feed_name, entry, data_dir)
        return text, path

    # No extractor worked and no enclosure — skip
    raise ValueError(f"Skip: no extractor and no audio enclosure for '{entry.title}'")


def _save_transcript(text, feed_name, entry, data_dir):
    """Save transcript text to disk. Returns the path."""
    from podreader.state import slugify, guid_or_fallback
    guid = guid_or_fallback(entry)
    # Use parsed date if available, fall back to raw
    pp = getattr(entry, "published_parsed", None)
    import time
    if pp and isinstance(pp, time.struct_time):
        pub_date = f"{pp.tm_year}-{pp.tm_mon:02d}-{pp.tm_mday:02d}"
    else:
        raw = getattr(entry, "published", "unknown")
        pub_date = str(raw)[:10] if raw else "unknown"
    slug = slugify(entry.title, pub_date, guid)
    transcript_dir = os.path.join(data_dir, "transcripts", feed_name)
    os.makedirs(transcript_dir, exist_ok=True)
    path = os.path.join(transcript_dir, f"{slug}.txt")
    with open(path, "w") as f:
        f.write(text)
    return path


def download_audio(url, cache_dir):
    """Download audio file to cache directory. Returns path to downloaded file."""
    os.makedirs(cache_dir, exist_ok=True)
    filename = url.split("/")[-1].split("?")[0] or "audio.mp3"
    path = os.path.join(cache_dir, filename)
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return path


def run_whisper(audio_path, model="base"):
    """Transcribe audio using faster-whisper. Returns transcript text."""
    from faster_whisper import WhisperModel

    whisper_model = WhisperModel(model, device="cpu", compute_type="int8")
    segments, _info = whisper_model.transcribe(audio_path)

    lines = []
    for segment in segments:
        lines.append(segment.text.strip())

    if not lines:
        raise RuntimeError(f"Whisper produced no output for {audio_path}")

    return "\n".join(lines)
