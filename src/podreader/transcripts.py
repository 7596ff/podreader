"""Transcript fetching — extractor dispatch, whisper fallback, skip logic."""

import os
import subprocess
import requests


def resolve_transcript(entry, feed_name, feed_config, extractors, data_dir):
    """
    Resolve a transcript for an episode. Returns (transcript_text, transcript_path) or raises.

    Fallback chain:
    1. Extractor (web fetch + extract)
    2. Whisper (download audio + subprocess transcribe)
    3. Skip (no enclosure, no extractor) — raises ValueError
    """
    extractor_name = feed_config.get("extractor")

    # Try extractor path
    if extractor_name and extractor_name in extractors:
        extractor = extractors[extractor_name]
        url = extractor.get_transcript_url(entry)
        if url is not None:
            response = requests.get(url)
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
    pub_date = getattr(entry, "published", "unknown")
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
    """Run whisper-timestamped as subprocess. Returns transcript text."""
    result = subprocess.run(
        [
            "python", "-m", "whisper_timestamped",
            audio_path,
            "--model", model,
            "--output_format", "txt",
            "--output_dir", os.path.dirname(audio_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Whisper failed: {result.stderr}")

    # Read the output txt file
    txt_path = os.path.splitext(audio_path)[0] + ".txt"
    with open(txt_path, "r") as f:
        return f.read()
