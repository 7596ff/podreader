# Podreader — Design Spec

A podcast subscription and transcript management tool for AI agents. Maintains feeds, tracks episode status through a pipeline, fetches or generates transcripts, and outputs them to stdout for agent consumption.

## Project Structure

```
podreader/
├── pyproject.toml
├── src/
│   └── podreader/
│       ├── __init__.py
│       ├── cli.py          # argument parsing, command dispatch
│       ├── feeds.py        # RSS fetching, feed management
│       ├── transcripts.py  # transcript fetching (web + whisper)
│       ├── state.py        # JSON state read/write
│       ├── config.py       # TOML config read/write
│       └── extractors/     # built-in extractors
│           ├── __init__.py
│           ├── npr.py
│           └── democracynow.py
└── tests/
    ├── test_feeds.py
    ├── test_transcripts.py
    ├── test_state.py
    └── test_extractors.py
```

## Storage

Everything lives in `~/.podreader/`:

```
~/.podreader/
├── config.toml          # feed subscriptions + settings
├── state.json           # episode status tracking
├── transcripts/         # saved transcripts, one per episode
│   ├── democracy-now/
│   │   └── 2026-05-08-friday.txt
│   └── npr-politics/
│       └── 2026-05-08-how-rising-oil-prices.txt
├── cache/               # temporary audio downloads
│   └── npr-politics/
│       └── 2026-05-08-how-rising-oil-prices.mp3
└── extractors/          # user-defined extractors (v1.1)
    └── my-podcast.py
```

## Config (`~/.podreader/config.toml`)

```toml
[settings]
whisper_model = "base"       # tiny, base, small, medium, large
max_cache_gb = 5             # auto-cleanup when cache exceeds this

[feeds.democracy-now]
url = "https://www.democracynow.org/podcast.xml"
extractor = "democracynow"

[feeds.npr-politics]
url = "https://feeds.npr.org/510310/podcast.xml"
extractor = "npr"

[feeds.ezra-klein]
url = "https://feeds.simplecast.com/82FI35Px"
# no extractor = whisper fallback
```

If a feed has an `extractor` field, podreader uses the named plugin to fetch transcripts from the web. If no extractor is specified, it falls back to downloading audio and running whisper.

## State (`~/.podreader/state.json`)

```json
{
  "democracy-now": {
    "tag:democracynow.org,2026-05-08:media/mp3podcast/428ae4": {
      "title": "Democracy Now! 2026-05-08 Friday",
      "status": "processed",
      "pub_date": "2026-05-08",
      "audio_url": "https://...",
      "transcript_path": "transcripts/democracy-now/2026-05-08-friday.txt"
    }
  }
}
```

- Episodes keyed by feed name → guid (unique, stable per episode)
- If an entry lacks a guid, fall back to `sha256(link + title)` as the key
- Transcript filenames are slugified from title + date + short hash of guid (human-readable on disk, collision-proof for same-day episodes with similar titles)
- Status pipeline: `unprocessed` → `transcript-fetched` → `processed`
- Terminal states: `skipped` (no enclosure and no extractor — cannot be processed) and `failed` (processing attempted but errored)
- `processed` is a user-set bit (via `podreader mark`). `skipped`, `failed`, and `transcript-fetched` are result-states of the processing engine. `status` command shows `unprocessed` and `failed` as actionable; `skipped` and `processed` as done.
- `fetch --process` commits state after each episode, not at the end of the batch (incremental persistence)
- All state writes use atomic write-to-temp-then-`os.replace` pattern to prevent corruption

## Extractor Plugin Interface

```python
# extractors/npr.py

name = "npr"  # matches config's extractor field

def get_transcript_url(entry):
    """Given a feedparser entry, return the transcript URL or None."""
    slug = entry.link.split("/")[4]
    return f"https://www.npr.org/transcripts/{slug}"

def extract_transcript(html):
    """Given the HTML of the transcript page, return plain text."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    # extract transcript text
    ...
```

**MVP:** Built-in extractors only (NPR, Democracy Now). User-defined extractors deferred to v1.1.

**Loading order (v1.1):**
1. Built-in extractors from `src/podreader/extractors/`
2. User extractors from `~/.podreader/extractors/`
3. User extractors override built-ins with the same `name`

**Contract:**
- `name`: string matching the `extractor` field in config
- `get_transcript_url(entry)`: takes a `feedparser` entry, returns a URL string or `None`
- `extract_transcript(html)`: takes raw HTML, returns plain text transcript
- If either function isn't defined, that step falls back to whisper

**Transcript flow:**
1. Has extractor? → `get_transcript_url()` → fetch the page → `extract_transcript()` → save
2. No extractor? → download audio enclosure → run whisper-timestamped as subprocess → save
3. No enclosure and no extractor? → mark as `skipped`

## Commands

```
podreader add <url> [--name NAME] [--extractor NAME]
```
Subscribe to a feed. Name is auto-derived from the RSS title if not given.

```
podreader list
```
Show all feeds with episode counts by status.

```
podreader fetch <feed> [--last N] [--process]
```
Pull the RSS feed, add new episodes to state as `unprocessed`. Default fetches all new episodes. `--process` immediately processes all fetched episodes (combined step for agentic workflows). State is committed after each episode, not at the end of the batch.

```
podreader process <feed> <episode>
```
Get the transcript — either via extractor or via whisper (run as subprocess to isolate crashes). Moves status from `unprocessed` to `transcript-fetched`. On failure, marks as `failed`. Checks for `ffmpeg` before attempting whisper path.

```
podreader read <feed> <episode> [--format text|json]
```
Output the transcript to stdout. `text` (default) outputs plain transcript. `json` outputs transcript + episode metadata (title, date, feed, audio URL).

```
podreader mark <feed> <episode>
```
Mark as `processed`.

```
podreader status [feed]
```
Summary of unprocessed and transcript-fetched episodes.

**Episode references:** Episodes can be referenced by guid, title substring, or index from `list`. Ambiguous matches fail with an error listing all matches and their indexes — never silently pick the first. `--latest` flag resolves ambiguity deterministically by picking the most recent match (agent-friendly).

## Known Limitations (MVP)

- **No historical backfill.** Only episodes present in the current RSS XML are fetchable. Most feeds expose 50-300 episodes.
- **No paginated or JS-rendered transcripts.** Extractors assume a single static HTML page.
- **No authenticated feeds or transcript sources.**
- **User-defined extractors deferred to v1.1.**

## Dependencies

- `feedparser` — RSS parsing
- `requests` — HTTP fetching
- `beautifulsoup4` — HTML transcript extraction
- `whisper-timestamped` — audio transcription with word-level timestamps (invoked as subprocess to isolate crashes from main process)
- `tomli-w` — TOML writing (reading via stdlib `tomllib`)

Runtime requirement: `ffmpeg` (checked before whisper transcription).

## TDD Targets

- **State management** — read/write JSON, atomic writes, status transitions (including `skipped` and `failed`), slug generation with hash, guid fallback
- **Config** — read/write TOML, feed CRUD, extractor resolution
- **Feed parsing** — RSS → episode list, deduplication against existing state, missing guid handling
- **Transcript fallback chain** — extractor → whisper → skip. The most brittle path; TDD focus here.
- **Transcript extraction** — HTML → text for built-in extractors (NPR, DN)
- **Episode matching** — guid, title substring, index resolution, ambiguous match errors, `--latest` resolution

TDD-skip:
- Whisper transcription (integration test, not unit)
- CLI formatting (manual/smoke testing)
- HTTP fetching (mock in tests)
