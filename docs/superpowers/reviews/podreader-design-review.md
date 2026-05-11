# Design Review: Podreader

**Reviewer:** Gemini CLI
**Date:** 2026-05-10
**Status:** Completed

This review evaluates the **podreader** design spec (v2026-05-10) against the priorities outlined in the design review prompt.

---

## 1. Architectural Gaps

### Missing Error Cases
- **Transcription Failures:** The spec doesn't define what happens if `extract_transcript(html)` returns an empty string or fails due to a site layout change. There should be a `failed` or `needs-retry` state to distinguish from `unprocessed`.
- **Resource Constraints:** Whisper is resource-intensive. If audio is too long or disk is full during `cache/` download, the tool might crash mid-process, leaving `state.json` in an inconsistent state.
- **Dependency Missing:** Whisper requires `ffmpeg`. The tool should check for this early.

### State Management Robustness
- **Atomic Writes:** Since `state.json` and `config.toml` are the source of truth, the implementation **must** use a "write-to-temp-then-rename" pattern. A partial write during a crash would corrupt the entire subscription list and history.
- **Concurrent Access:** Even if "single user," an agent might trigger multiple `podreader process` calls in parallel. A simple file lock or atomic updates are recommended.

### Extractor Plugin Contract
- **Pagination/JS:** Some transcripts (e.g., Substack, some media sites) are paginated or require JS execution. The current `extract_transcript(html)` contract assumes a single static HTML page.
- **Auth:** There is no mechanism for extractors to access credentials (e.g., for premium feeds).

---

## 2. RSS Edge Cases

### GUIDs and Identification
- **Missing GUIDs:** If an entry lacks a GUID, the spec should explicitly fall back to a SHA-256 hash of `link + pubdate` to prevent duplicate "new" episodes on every fetch.
- **GUID Stability:** Some feeds change GUIDs when updating metadata. The system should handle (or ignore) such churn.

### Pagination and History
- **Historical Backfill:** `podreader fetch` currently only pulls what's in the current XML. If a feed has 1,000 episodes but the XML only shows 20, there's no way to reach the older ones. 
- **Enclosures:** If an episode has no enclosures (e.g., a "transcript only" or "announcement" entry), the Whisper fallback will fail. The `transcripts.py` logic needs a check for `enclosure` presence.

---

## 3. Extractor Design

### Context and Contract
- **Context Injection:** `get_transcript_url(entry)` should also receive the `feed_config` (to access per-feed settings) and perhaps the `feed` object itself for channel-level metadata.
- **Return Types:** `extract_transcript` should return a structured object (or at least `(text, metadata)`) to capture things like speaker labels if they are parsed from the HTML.

### Security
- **Dynamic Loading:** Loading from `~/.podreader/extractors/` using `importlib` is standard for Python CLI tools, but the tool should check file permissions (ensure they aren't world-writable) to prevent local privilege escalation.

---

## 4. Whisper Integration

### Subprocess vs. Library
- **Recommendation:** Use **subprocess** for Whisper.
- **Why:** Whisper (and its dependencies like `torch`) is heavy. Loading it as a library into the main CLI process will make every command (even `podreader list`) feel sluggish due to import overhead. Subprocess also isolates crashes and allows for easier memory cleanup.

### Cache Management
- **Retention Policy:** The spec mentions `cache/` for audio but no cleanup. A `max_cache_size_gb` or `auto_cleanup = true` setting is needed in `config.toml`.
- **GPU Config:** `config.toml` should allow specifying `device = "cuda" | "cpu" | "mps"`.

---

## 5. CLI Design

### Ambiguity and References
- **Match Resolution:** If `podreader process "The Oil Crisis"` matches two episodes, it should fail with an error listing the matches and their indexes/GUIDs, rather than picking the first one.
- **Index Stability:** "Index from list" is convenient but dangerous if the list order changes between commands. Indexes should be clearly ephemeral.

### Automation
- **Combined Step:** `podreader fetch --process` or `podreader fetch --all --process` is highly recommended for agentic workflows where "get everything new and ready" is a common task.
- **Read Formats:** `podreader read --format [text|json|srt]` is essential. Agents will likely want JSON containing the transcript + timestamps + episode metadata.

---

## 6. Missing Features

### Agent-Specific Needs
- **Search:** A `podreader search <query>` command that greps through saved transcripts is a high-value feature for agents looking for specific topics across their subscriptions.
- **Export:** A way to export a "bundle" for a specific episode (transcript + metadata + audio link) in a single JSON blob.

### Maintenance
- **Pruning:** `podreader purge --older-than 30d` to clean up old transcripts and state entries.

---

## 7. Scope and Implementation

### MVP Definition
1. Feed subscription and state tracking (with GUID fallback).
2. Basic extractor support (built-in only).
3. Whisper fallback (subprocess-based).
4. `read` command (stdout).

### Deferred
1. User-defined extractors (v1.1).
2. Advanced search (v1.2).
3. Auth-based extraction (v2.0).

---

## Summary of Concrete Fixes

1. **State:** Implement atomic JSON writes using `os.replace`.
2. **Identification:** Use `hash(link + title)` if `guid` is missing.
3. **Execution:** Move Whisper to a subprocess call.
4. **CLI:** Add `podreader fetch --process` for batching.
5. **Output:** Add `--format json` to `read` command.
