# Podreader Roadmap

## v1.0 (MVP)
- Feed subscription and state tracking
- Built-in extractors (NPR, Democracy Now)
- Whisper fallback via whisper-timestamped (subprocess, crash-isolated)
- Atomic state writes (`os.replace`)
- Incremental persistence (`fetch --process` commits per-episode)
- GUID fallback (`sha256(link + title)`) for feeds without guids
- Collision-proof transcript filenames (title + date + short hash)
- `skipped` and `failed` terminal states in the pipeline
- `fetch --process` combined step
- `read --format json` output
- Episode matching by guid, title substring, or index
- `--latest` flag for agent-friendly ambiguity resolution
- Cache size limit (`max_cache_gb` config)

## v1.1
- User-defined extractor plugins (`~/.podreader/extractors/`)
- `podreader search <query>` across saved transcripts
- `podreader purge --older-than <days>` cleanup command
- `podreader remove <feed>` unsubscribe
- Orphan cache cleanup: startup sanity check removes cache files not being processed by an active PID

## v1.2
- `read --format srt` output with timestamps
- Extractor context injection (feed config, previous episode state)
- Structured transcript return from extractors (text + speaker labels)
- Migrate transcript storage from `.txt` to JSON-formatted files (text + speaker labels + timestamps) — `read --format json` becomes native rather than wrapping `.txt`

## v2.0
- Authenticated feeds and transcript sources
- Paginated / JS-rendered transcript support
- Historical backfill via podcast catalog APIs
- GPU device configuration for whisper
