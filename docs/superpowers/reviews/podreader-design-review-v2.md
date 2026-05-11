# Design Review v2: Podreader (Critical Evaluation)

**Reviewer:** Gemini CLI
**Date:** 2026-05-10
**Status:** Under Revision

While the v2 spec addresses several surface-level concerns (atomic writes, GUID fallbacks, combined CLI flags), it introduces several structural contradictions and logical gaps that would likely cause failure in a production-agent environment.

---

## 1. The "Lazy Import" Fallacy
The spec attempts to solve the Whisper performance issue with "lazy-imported [whisper-timestamped], only loaded when whisper path is used." 

- **The Contradiction:** This solves the *startup* time for `list` or `status`, but it fails the **Process Integrity** requirement. Whisper (via `torch`) can consume 2GB+ of RAM and utilize 100% of a GPU/CPU. If Whisper is lazy-loaded into the main `podreader` process, a transcription crash (OOM, driver error, Segfault) kills the entire CLI process.
- **The Gap:** The spec claims "All state writes use atomic write-to-temp." If the process segfaults during a Whisper run inside the main process, any pending state changes for *other* episodes fetched in that same `fetch --process` run are lost.
- **Critical Fix:** Revert to the **subprocess** recommendation. Isolate the heavy, unstable ML stack from the lightweight state-management CLI.

## 2. The "Unprocessable" Loop
The spec states: *"No enclosure and no extractor? → skip with warning."*

- **The Contradiction:** If an episode is "skipped," what is its `status`?
    - If it stays `unprocessed`, every subsequent `podreader fetch --process` will re-attempt to download/transcribe the "no-enclosure" episode, resulting in a permanent warning loop.
    - If it moves to `processed` (or a new `skipped` status), this isn't defined in the **Status Pipeline** (`unprocessed` → `transcript-fetched` → `processed`).
- **The Gap:** The pipeline is too linear. It lacks an "ignored" or "failed" terminal state for episodes that *cannot* be processed (e.g., text-only announcements in a podcast feed).

## 3. Atomic Integrity vs. Batch Processing
The spec adds `podreader fetch --process` for agentic workflows.

- **The Contradiction:** Podcasting is a long-tail task (transcription takes minutes/hours). If `fetch --process` pulls 10 episodes and transcribes them sequentially:
    - **Scenario A (Batch Update):** State is saved at the end. A crash at episode 9 loses 2 hours of work.
    - **Scenario B (Incremental Update):** State is saved after each episode. This is better, but the spec doesn't explicitly define this behavior, and "atomic write-to-temp" doesn't protect against the *user* or *agent* seeing an inconsistent state if they run `podreader status` in another terminal during the hours-long batch.
- **Critical Fix:** Define "Incremental Persistence." State must be committed immediately after each successful `transcript-fetched` transition.

## 4. Unique Keys vs. Colliding Paths
- **The Logic Gap:** The spec correctly identifies that GUIDs (or SHA256 fallbacks) are the unique keys in `state.json`. However, it also states: *"Transcript filenames are slugified from title + date."*
- **The Contradiction:** It is common for "Daily" podcasts to release a "Part 1" and "Part 2" or a "Correction" with the same title and date. 
    - `Key A`: `hash(title + date + link_1)`
    - `Key B`: `hash(title + date + link_2)`
    - **Both attempt to write to:** `transcripts/feed/2026-05-10-title.txt`.
    - One will overwrite the other, or the atomic write will fail. The `state.json` will point to a file that doesn't match the record.
- **Critical Fix:** The `transcript_path` must include a portion of the unique key (e.g., `title-date-HASH.txt`) to ensure file-system uniqueness matches state-uniqueness.

## 5. Ambiguity vs. Agent Autonomy
- **The UX Contradiction:** *"Ambiguous matches fail with an error listing all matches... never silently pick the first."*
- **The Problem:** For a human, this is great. For an AI agent running in a loop, this is a **deadlock**. If an agent says `podreader read "The Crisis"`, and it matches two episodes, the agent's script fails.
- **Critical Fix:** Add a `--latest` or `--first` flag, or allow referencing by `-1` (latest). Agents need a deterministic way to resolve ambiguity without human intervention.

## 6. Dependency Confusion
- **Minor Contradiction:** The `TDD Targets` include *"Extractor loading — built-in discovery, dispatch"*, but the `MVP` section says *"User-defined extractors deferred to v1.1."* 
- If there are only 2 built-in extractors, "discovery" is over-engineered for the MVP. Focus TDD on the **fallback logic** (Extractor -> None -> Enclosure -> Whisper), which is currently the most brittle part of the design.

---

### Summary of Required v3 Changes:
1. **Isolate Whisper:** Move from "lazy import" to a true subprocess call (`python -m whisper...` or a dedicated entry point).
2. **Terminal Failure State:** Add `skipped` or `failed` to the status pipeline.
3. **Collision-Proof Paths:** Include GUID/Hash in the filename.
4. **Agent-Friendly Selection:** Add a mechanism to "pick latest" on ambiguity.
5. **Incremental Commit:** Explicitly state that `fetch --process` commits state per-episode.
