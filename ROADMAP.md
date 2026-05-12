# Podreader Roadmap

## v1.0 (MVP) ✓
- [x] Feed subscription and state tracking
- [x] Built-in extractors (NPR, Democracy Now)
- [x] Whisper fallback via openai-whisper (subprocess, crash-isolated)
- [x] Atomic state writes (`os.replace`)
- [x] Incremental persistence (`fetch --process` commits per-episode)
- [x] GUID fallback (`sha256(link + title)`) for feeds without guids
- [x] Collision-proof transcript filenames (title + date + short hash)
- [x] `skipped` and `failed` terminal states in the pipeline
- [x] `fetch --process` combined step
- [x] `read --format json` output
- [x] Episode matching by guid, title substring, or index
- [x] `--latest` flag for agent-friendly ambiguity resolution
- [x] Cache size limit (`max_cache_gb` config)

## v1.1
- [ ] Show episode duration in `list` and `status` output (from RSS enclosure/itunes:duration)
- [ ] `fetch --first N` to grab oldest episodes
- [x] User-defined extractor plugins (`~/.podreader/extractors/`)
- [ ] `podreader search <query>` across saved transcripts
- [ ] `podreader purge --older-than <days>` cleanup command
- [x] `podreader remove <feed>` unsubscribe
- [ ] Orphan cache cleanup: startup sanity check removes cache files not being processed by an active PID

## v1.2
- [ ] `read --format srt` output with timestamps
- [ ] Extractor context injection (feed config, previous episode state)
- [ ] Structured transcript return from extractors (text + speaker labels)
- [ ] Migrate transcript storage from `.txt` to JSON-formatted files (text + speaker labels + timestamps) — `read --format json` becomes native rather than wrapping `.txt`

## v2.0
- [ ] Authenticated feeds and transcript sources
- [ ] Paginated / JS-rendered transcript support
- [ ] Historical backfill via podcast catalog APIs
- [ ] GPU device configuration for whisper
