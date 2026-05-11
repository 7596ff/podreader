# podreader

Podcast subscription and transcript management for AI agents. Subscribe to feeds, fetch episodes, get transcripts (from the web or via whisper), read them.

## Usage

```bash
podreader add https://feeds.npr.org/510310/podcast.xml --name npr-politics --extractor npr
podreader add https://www.democracynow.org/podcast.xml --name democracy-now --extractor democracynow
podreader add https://example.com/feed.xml --name my-podcast  # no extractor = whisper fallback

podreader fetch democracy-now --last 5          # fetch latest 5 episodes
podreader fetch npr-politics --last 1 --process # fetch and transcribe in one step
podreader process my-podcast "episode title"    # transcribe a specific episode
podreader read democracy-now "friday" --latest  # print transcript to stdout
podreader read npr-politics "oil" --format json # transcript + metadata as JSON
podreader mark democracy-now "friday" --latest  # mark as processed
podreader status                                # show what needs attention
podreader list                                  # show all feeds and counts
```

## Transcript Sources

**Web extractors** — for podcasts with published transcripts. Built-in extractors for:
- **NPR** — fetches from `npr.org/transcripts/`
- **Democracy Now** — multi-page fetch: index → segment URLs → combine

**Whisper fallback** — for everything else. Downloads the audio, runs OpenAI whisper as a subprocess, saves the transcript. Requires `ffmpeg` on PATH.

**Custom extractors** — write a Python file with two functions:
```python
name = "my-podcast"

def get_transcript_url(entry):
    """Given a feedparser entry, return the transcript URL or None."""
    ...

def extract_transcript(html):
    """Given the HTML of the transcript page, return plain text."""
    ...
```

Place in `~/.podreader/extractors/` (v1.1).

## Episode Pipeline

```
unprocessed → transcript-fetched → processed
                ↘ skipped (no audio/extractor)
                ↘ failed (error during processing)
```

`processed` is set by `podreader mark`. `skipped` and `failed` are set automatically. `failed` can be retried.

## Episode References

Episodes can be referenced by:
- **Title substring** — `podreader read my-feed "oil crisis"`
- **Index** — `podreader read my-feed 0` (oldest), `podreader read my-feed -1` (newest)
- **GUID** — exact match
- **`--latest` flag** — resolves ambiguous matches by picking the most recent

## Storage

Everything lives in `~/.podreader/`:
```
~/.podreader/
├── config.toml      # feed subscriptions
├── state.json       # episode status
├── transcripts/     # saved transcripts
└── cache/           # downloaded audio (temporary)
```

## Install

```bash
# Nix (includes whisper + ffmpeg)
nix build
nix run . -- status

# uv (whisper installed separately)
uv venv && uv pip install -e .
```

## Tests

```bash
uv run pytest
```

49 tests covering state management, config, episode matching, transcript fallback chain, and feed parsing.
