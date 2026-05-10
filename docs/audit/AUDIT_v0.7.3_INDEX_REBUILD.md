# AUDIT — HERETIC v0.7.3 Mímisbrunnr Index Auto-Rebuild

**Date:** 2026-05-09
**Auditor:** Sólrún Hvítmynd (The Auditor for Vibe Coding)
**Subject:** v0.7.3 — KeywordIndex.search() auto-rebuild on missing/corrupt index
**Subject HEAD at audit time:** `c589e4d` (Architect+Forge merged Wave close)

---

## Verdict

**PASSES SCRUTINY — 0 BLOCKERS, 0 NOTABLE FINDINGS, 0 NITS.**

The auto-rebuild path is structurally sound: it fires only when the index is genuinely unusable (missing file, OSError on load, or zero entries after corrupt-line skipping); it preserves the actionable LibraryIndexError for the truly-unrecoverable case (no `.txt` source files); the auto-rebuilt index is byte-equivalent to a manually-built one. No new privacy or integrity invariants — this is a behaviour extension on the v0.7.2 *Endurdrykkr* lineage, not a new discipline. No regression in the broader Mímisbrunnr suite.

---

## What I Verified

### V-1: Auto-rebuild fires when index is missing
- `test_search_auto_rebuilds_when_index_missing`: source file exists, `keyword_index.jsonl` does not. After `idx.search("Odin")`, the index file is written to disk and hits are returned. **Test passes.**

### V-2: Auto-rebuild fires when index is empty (zero bytes)
- `test_search_auto_rebuilds_when_index_empty`: writes a zero-byte index file. `_load_index_from_disk` returns `[]`. The check `if loaded_entries:` is falsy → rebuild triggered. After search() the index has entries. **Test passes.**

### V-3: Auto-rebuild fires when every index line is malformed
- `test_search_auto_rebuilds_when_index_all_corrupt`: writes three garbage lines. `_load_index_from_disk` skips each with a warning and returns `[]`. Same falsy check triggers rebuild. **Test passes.**

### V-4: Actionable error preserved when truly unrecoverable
- `test_search_raises_when_no_txt_files_and_no_index`: empty `data_dir`. `_load_or_rebuild_cache` finds no index AND no source files; raises `LibraryIndexError` containing "No keyword index" and "library download". **Test passes — the v0.7 actionable message is preserved.**
- `test_search_raises_when_no_txt_files_and_corrupt_index`: corrupt index but no source files. Same fall-through to the rebuild path; same raise. **Test passes.**

### V-5: Auto-rebuild produces byte-equivalent output to manual build
- `test_auto_rebuild_index_equivalent_to_manual_build`: builds an index manually, captures entries; deletes the index file; constructs a fresh `KeywordIndex` instance and calls search() (auto-rebuilds); compares entries. **Same count, same source_id/line_number/content per entry, same ordering. Test passes.**

This is the load-bearing claim: auto-rebuild and manual rebuild are indistinguishable. They both call `self.build(self._data_dir)`, which is unchanged from v0.7. The only difference is the trigger.

### V-6: Logging is operator-visible
- `test_auto_rebuild_logs_warning_or_info`: captures logs at INFO level under the `heretic.skilningr.mimisbrunnr.index` logger; asserts at least one message contains "auto-build" or "auto-rebuild". **Test passes.**

The operator can trace why the rebuild happened (file missing vs. file corrupt vs. file empty) by reading the logs.

### V-7: Backward compatibility
- All 23 existing `test_mimisbrunnr_index.py` tests pass unchanged at HEAD `c589e4d`.
- The pre-existing test `test_search_raises_library_index_error_when_no_index` continues to pass because the substring "No keyword index" still appears in the new error message — the test uses `match="No keyword index"` (partial match), not exact equality.
- `search()` signature unchanged. `KeywordIndex.__init__` unchanged. `build()` unchanged.

### V-8: M-1..M-9 inherited from v0.7 / v0.7.2 unchanged
- v0.7 Mímisbrunnr invariants (consent gate first, atomic rename, SHA-256 verification, offline invariant) are not affected — `index.py` does not own any of those; downloader.py owns them and was not edited in v0.7.3.
- v0.7.2 Endurdrykkr invariants (M-7/M-8/M-9 around resumable downloads) are not affected — same reason.

---

## Test Suite Status

| File | Tests | Status |
|---|---|---|
| `tests/test_mimisbrunnr_index.py` | 23 (v0.7) + 7 (v0.7.3) = 30 | 30/30 passing |
| `tests/test_mimisbrunnr_downloader.py` | 24 | 24/24 passing |
| `tests/test_mimisbrunnr_*` other | unchanged | passing |
| **Mímisbrunnr total** | **152** | **all passing** |

The 20 pre-existing environment failures in the broader suite are unchanged.

---

## Cross-Document Consistency

- **TASK_HERETIC_v0.7.3_INDEX_REBUILD.md §3** decision table — matches the implementation.
- **docs/cartography/DATA_FLOW.md §4.14.2.1** — the decision-tree diagram matches `_load_or_rebuild_cache()` line by line.
- **docs/vision/ENDURDRYKKR.md §VIII** — Skald addendum correctly characterises v0.7.3 as continuity-extension to the index layer; no new discipline coined.
- **src/heretic/skilningr/mimisbrunnr/index.py** module changes are localised: `search()` body shortened from ~10 lines to 2; `_load_or_rebuild_cache()` added (~50 lines); `_load_index_from_disk()` unchanged.

No contradictions.

---

## Honest Negative Audit

- **No silent retry loop.** If `build()` itself fails (disk write error, etc.), the exception propagates — `_load_or_rebuild_cache` does not catch it. This is correct: a build failure is operator-visible.
- **No infinite loop on persistent corruption.** If `build()` succeeds but writes a corrupt file (e.g. disk-level corruption mid-write), the next `search()` would attempt to rebuild again. But because `build()` writes via `.heretic_tmp` + `os.replace`, partial-write corruption is structurally impossible.
- **No hidden state mutation.** `_load_or_rebuild_cache` only reads `self._data_dir` and writes `self._cache` (via `build()`). No other instance state is touched.
- **No race between cache check and load.** `KeywordIndex` is single-threaded by usage; the audit is not introducing concurrency.
- **No accidental rebuild when index is healthy.** The check is `if loaded_entries:` — a non-empty list is truthy; happy path returns immediately.
- **No leak of corruption details.** The WARNING log mentions "no usable entries (empty or all lines corrupt)" but does not expose the corrupt content itself, which could include truncated PII if the file got mangled.

---

## Findings

**0 BLOCKER. 0 SERIOUS. 0 NOTABLE. 0 NIT.**

The Auditor records no further work for v0.7.3. The Forge does not need a Wave 6 cleanup pass. The Scribe may proceed to seal.

---

*Authored by Sólrún Hvítmynd, The Auditor for Vibe Coding, 2026-05-09. The next wave is the Scribe.*
