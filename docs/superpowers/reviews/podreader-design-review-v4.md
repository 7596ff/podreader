# Design Review v4: Podreader (Final Polish)

**Reviewer:** Gemini CLI
**Date:** 2026-05-10
**Status:** Final Approval

The v4 spec and Roadmap now incorporate the refined pipeline logic, orphan cache management, and storage evolution path recommended in the v3 review. The architecture is mature, deterministic, and specifically hardened for the resource-intensive nature of audio transcription and the autonomy requirements of AI agents.

---

## 1. Resolution of Refined Architectural Points

- **Status Pipeline Clarity:** Fixed. The spec now explicitly distinguishes between **Result States** (`transcript-fetched`, `skipped`, `failed`) and the **User Bit** (`processed`). This clarifies the `status` command logic (identifying actionable vs. done work) and prevents the tool from nagging users about "unprocessable" (`skipped`) episodes.
- **Orphan Cache Management:** Added to v1.1. The "startup sanity check" is the correct approach to ensure that failed or killed Whisper processes don't permanently leak disk space in `~/.podreader/cache/`.
- **Storage Evolution:** Added to v1.2. The plan to migrate from `.txt` to JSON-formatted transcripts acknowledges the need for richer metadata (speaker labels, timestamps) while keeping the MVP simple.

---

## 2. Final Critical Observations

### A. The "Guid Fallback" Consistency
The spec uses `sha256(link + title)` when a GUID is missing.
- **Edge Case:** If a podcast feed updates an episode's title (e.g., "The Oil Crisis [Fixed Audio]") and lacks a GUID, the `sha256` will change. 
- **The Result:** The episode will be treated as "new" and fetched again. 
- **Mitigation:** This is a known risk in RSS processing without GUIDs. For an MVP, `link + title` is the best heuristic, but the implementation should document this behavior for feeds with poor metadata hygiene.

### B. Dependency Management: `whisper-timestamped`
The spec relies on `whisper-timestamped` as a subprocess.
- **Maintenance Risk:** `whisper-timestamped` is a wrapper. If it breaks or falls behind the main `openai-whisper` package, the tool's core value (timestamps) is at risk.
- **Strategy:** The `transcripts.py` module should be written with a clean abstraction for "Transcriber," making it easy to swap the subprocess command if we migrate to `faster-whisper` or another engine in v2.0.

### C. The `list` vs `status` Command Overlap
- **Observation:** `podreader list` shows "counts by status," while `podreader status` shows a "summary of unprocessed and transcript-fetched."
- **Critique:** There is significant overlap here. In a CLI, users (and agents) might find it confusing whether they want `list` or `status`.
- **Refinement:** Ensure `list` remains high-level (feed health/counts) and `status` is actionable (what episodes need attention right now).

---

## 3. Implementation Checklist (Ready for TDD)

1.  **Atomicity:** Use `tempfile.NamedTemporaryFile` + `os.replace` for all JSON/TOML writes.
2.  **Isolation:** Use `subprocess.run` with a timeout and resource limits for Whisper.
3.  **Ambiguity:** Implement the `--latest` flag as a simple sort-by-date (or index) filter on the results of the substring match.
4.  **Resilience:** The "Fallback Chain" test suite should cover:
    - [ ] `extractor` succeeds.
    - [ ] `extractor` fails -> Whisper fallback.
    - [ ] No `extractor` -> Whisper fallback.
    - [ ] Whisper fails -> `failed` state.
    - [ ] No enclosure/extractor -> `skipped` state.

---

## Final Verdict
The **Podreader v4** design is theoretically sound and practically robust. It avoids the "heavy import" trap, handles the fragility of web-scraping/ML, and provides a clear API for automation.

**Implementation can begin immediately.**
