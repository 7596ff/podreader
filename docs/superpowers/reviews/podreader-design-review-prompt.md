# Podreader Design Review Prompt

Paste the spec below into Gemini or another reviewer, followed by this prompt:

---

You are reviewing a design spec for **podreader**, a Python CLI tool that manages podcast subscriptions and transcripts for AI agents. The tool fetches RSS feeds, tracks episode status through a pipeline (`unprocessed` → `transcript-fetched` → `processed`), and either fetches web transcripts via per-feed Python plugin extractors or generates them via whisper from audio.

Please review the spec with the following priorities:

## 1. Architectural Gaps
- Are there missing error cases? (feed offline, transcript page changed, whisper fails, audio too long, disk full)
- Is the state management robust? (concurrent access not a concern — single user — but corruption, partial writes, missing keys)
- Does the extractor plugin interface have enough information to handle real-world podcasts? Are there common podcast transcript patterns that would break this contract?

## 2. RSS Edge Cases
- What happens with feeds that use non-standard guid formats, or feeds without guids at all?
- Pagination — some feeds only expose the last N episodes. How should podreader handle historical episodes?
- Feeds with multiple enclosures per episode, or episodes without enclosures?
- Character encoding issues in feed titles and descriptions?

## 3. Extractor Design
- Is the two-function contract (`get_transcript_url` + `extract_transcript`) sufficient? Are there transcript sources that would need a different pattern (e.g., API-based transcripts, paginated transcripts, transcripts behind authentication)?
- Should the extractor receive more context than just the feedparser entry? (e.g., feed-level config, previous episode state)
- Is dynamic module loading from `~/.podreader/extractors/` secure enough for a single-user tool?

## 4. Whisper Integration
- Should whisper run in a subprocess or as a library? Tradeoffs for each.
- Audio file management — when should cache be cleaned? Should there be a cache size limit?
- Should the tool support GPU acceleration configuration?
- `whisper-timestamped` vs base `openai-whisper` — is the timestamp feature worth the dependency?

## 5. CLI Design
- Is the episode reference system (guid, title substring, index) clear enough? What happens on ambiguous matches?
- Should `fetch` and `process` be combinable into one step? (`podreader fetch --process`)
- Should `read` support outputting in different formats (plain text, JSON with metadata, SRT)?

## 6. Missing Features
- Is anything obviously missing for an agent-facing tool? Think about what an AI agent needs that a human podcast listener wouldn't.
- Should there be a `podreader search` command for finding episodes across feeds?
- Cleanup commands — remove old episodes, purge cache, unsubscribe?

## 7. Scope
- Is this too much for a single implementation cycle? If so, what should be deferred?
- What's the minimum viable version that would be useful?

Please be specific. Cite the spec when pointing out issues. Suggest concrete fixes, not vague concerns.
