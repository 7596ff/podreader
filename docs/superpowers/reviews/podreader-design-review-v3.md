# Design Review v3: Podreader (Architectural Audit)

**Reviewer:** Gemini CLI
**Date:** 2026-05-10
**Status:** Approved for Implementation

The v3 spec has successfully resolved the critical contradictions identified in previous reviews (Whisper isolation, status pipeline loops, path collisions, and agent deadlocks). The alignment between the **Spec** and the **ROADMAP** is now logically sound.

---

## 1. Resolution of Previous Criticals

- **Whisper Isolation:** Fixed. Moving to a **subprocess** call ensures that a Torch/CUDA crash does not corrupt the state management process. This is the single most important stability fix for a long-running transcription tool.
- **The "Unprocessable" Loop:** Fixed. The introduction of the `skipped` and `failed` terminal states prevents the infinite retry loops for episodes without enclosures or those that hit persistent errors.
- **Path Collisions:** Fixed. Adding the `short hash of guid` to the slugified filename ensures that multi-part episodes or corrections on the same day remain unique on the filesystem, matching the uniqueness of the `state.json`.
- **Agent Autonomy:** Fixed. The `--latest` flag provides the necessary "escape hatch" for AI agents, allowing them to proceed deterministically when title substrings match multiple episodes.
- **Incremental Persistence:** Fixed. Explicitly stating that `fetch --process` commits state per-episode protects hours of transcription work against system crashes.

---

## 2. New Architectural Observations (v3 & Roadmap)

### A. The "Status Pipeline" Ambiguity
While `skipped` and `failed` were added as terminal states, the **Status Pipeline** description in the spec still says: `unprocessed` → `transcript-fetched` → `processed`.
- **The Conflict:** If an episode is `skipped`, is it "processed"? 
- **Recommendation:** Clarify that `processed` is a user-set bit (via `podreader mark`), while `skipped`, `failed`, and `transcript-fetched` are result-states of the processing engine. 
- **Logic Check:** A `skipped` episode should likely be considered "done" so it doesn't show up in a list of "pending work," but it never reached `transcript-fetched`.

### B. Dependency Coupling (v1.2 Roadmap)
The Roadmap for v1.2 introduces: *"Structured transcript return from extractors (text + speaker labels)."*
- **The Risk:** The current MVP `state.json` schema only has a `transcript_path` pointing to a `.txt` file. 
- **The Contradiction:** If v1.2 adds speaker labels, the `.txt` format becomes insufficient. 
- **Future-Proofing:** The implementation of the `read --format json` command in the MVP should be designed to read the `.txt` file but be "schema-aware" enough to handle JSON-formatted transcript files if the system migrates to them in v1.2.

### C. Cache Management (The "Orphan" Problem)
The spec adds `max_cache_gb` for auto-cleanup.
- **The Gap:** If the process is killed midway through a Whisper run, a large `.mp3` may be left in `cache/`. 
- **Recommendation:** The `podreader fetch` or `process` command should run a "cache-sanity-check" on startup to remove any files in `cache/` that are not currently being processed by an active PID.

---

## 3. TDD Strategy Validation

The TDD targets in v3 are correctly prioritized:
1. **The Fallback Chain:** This is the "brain" of the tool. Testing the priority (Extractor > Whisper > Skip) with mocks is the highest value activity.
2. **Atomic Writes:** Essential for reliability.
3. **Episode Matching:** Critical for agent interaction.

---

## Final Verdict
The design is now robust enough for a production-quality CLI tool. The isolation of heavy dependencies and the hardening of the state machine make it suitable for its primary audience: AI agents.

**Proceed to implementation of the MVP (v1.0).**
