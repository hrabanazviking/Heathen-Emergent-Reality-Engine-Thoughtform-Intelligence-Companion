# TASK — HERETIC v0.7.3 Mímisbrunnr Index Auto-Rebuild

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-09** (immediately after v0.6.3 *Verkminni* sealed at `bd48dd1`)
>
> **Codename:** none. v0.7.3 is an extension to v0.7.2 *Endurdrykkr* — same disposition (continuity), now applied to the keyword index in addition to the source download. The Skald has explicitly declined to coin a new name; this milestone rides on Endurdrykkr's framing. Brief Skald wave only.
>
> **Mythic Engineering mode:** AUTONOMOUS continuation. SEVENTH milestone of the session — and a deliberate small, focused, resilience-plumbing scope to avoid the diminishing-returns zone the entry-20 DEVLOG named.

---

## 1. Task scope

When `KeywordIndex.search()` is called and the on-disk `keyword_index.jsonl` is **missing** or **unreadable** or **empty after corrupt-line skipping**, the index is automatically **rebuilt from source files** (the `*.txt` files in the same data directory) before serving the query — instead of raising `LibraryIndexError`.

Operator pain solved: a corrupt or missing index file currently fails every library query with a message that points to `heretic library rebuild-index`. The operator has to manually run that command. v0.7.3 makes that recovery automatic when `.txt` source files are present (which they always are if any source has been downloaded).

If no `.txt` source files exist either (no source has been downloaded), the auto-rebuild fails — and the operator gets the same actionable error they get today, pointing them to `heretic library download`.

---

## 2. Current status — 2026-05-09

**Phase:** v0.7.3 **SHIPPED + AUDITED + SEALED.** All seven waves closed.

**HEAD (development) at audit close:** `290670c` (Auditor PASSES SCRUTINY)

**Test count after v0.7.3:** Mímisbrunnr index 23 → 30 (+7 new). Full Mímisbrunnr 152 passing.

### v0.7.3 deliverables — all complete

- ✅ Wave 0 — TASK file at `46fb8c4`
- ✅ Wave 1 — Skald (brief): `docs/vision/ENDURDRYKKR.md §VIII` addendum at `1dc1fad`. No new codename.
- ✅ Wave 2 — Cartographer: `docs/cartography/DATA_FLOW.md §4.14.2.1` at `e54d6b7`
- ✅ Waves 3+4 — Architect+Forge merged: `_load_or_rebuild_cache()` + 7 tests at `c589e4d`
- ✅ Wave 5 — Auditor: `docs/audit/AUDIT_v0.7.3_INDEX_REBUILD.md` PASSES at `290670c`
- ⏭ Wave 6 — Forge cleanup (skipped; audit found nothing)
- ✅ Wave 7 — Scribe: DEVLOG entry 21, this TASK seal, memory refresh (final commit)

### What v0.7.3 does NOT add

- Mtime-based staleness detection (rebuild when source files are newer than index) — out of scope; can be added later
- Index versioning / schema migration — out of scope
- Partial rebuild (only the affected source) — out of scope; full rebuild is fine for v0.7.3 (small corpora)
- New CLI command — `heretic library rebuild-index` already exists; v0.7.3 just makes it not strictly necessary

---

## 3. Architectural decisions

| Decision | Choice | Rationale |
|---|---|---|
| Auto-rebuild trigger | `KeywordIndex.search()` calls `_load_or_rebuild_cache()`; rebuild fires when index file is missing OR `_load_index_from_disk()` returns an empty list | Two failure modes (missing file, all-corrupt content) handled uniformly |
| Fallback to manual error | If auto-rebuild itself fails (no `.txt` source files), `LibraryIndexError` is raised with the same actionable message the operator gets today | Behaviour-preserving for the truly-unrecoverable case |
| Logging | INFO log on auto-rebuild trigger; WARNING log when load failed before rebuild | Operator can trace why the rebuild happened |
| In-memory cache | After auto-rebuild, `self._cache` holds the freshly built entries (set by `build()` on success) | Cache populated; no second disk read |
| Backward compatibility | `search()` signature unchanged; callers that previously caught `LibraryIndexError` for missing index continue to work — they just won't see that error when source files are present | Pure addition of a recovery path |
| Manual `rebuild-index` CLI | Unchanged. Still useful when operator wants to force a rebuild (e.g. after editing source files manually) | Additive, not subtractive |

---

## 4. Test plan

New tests in `tests/test_mimisbrunnr_index.py` (extension):

| Test | Asserts |
|---|---|
| `test_search_auto_rebuilds_when_index_missing` | data_dir has .txt files but no keyword_index.jsonl → search() builds the index and returns hits |
| `test_search_auto_rebuilds_when_index_empty` | data_dir has .txt files and a zero-byte keyword_index.jsonl → search() rebuilds |
| `test_search_auto_rebuilds_when_index_all_corrupt` | data_dir has .txt files and a keyword_index.jsonl whose every line is malformed JSON → search() rebuilds |
| `test_search_raises_when_no_txt_files_and_no_index` | Empty data_dir → search() raises LibraryIndexError with the correct actionable message |
| `test_search_raises_when_no_txt_files_and_corrupt_index` | data_dir has only corrupt index, no .txt files → raises (auto-rebuild can't proceed) |
| `test_auto_rebuild_index_is_equivalent_to_manual_build` | Compare auto-rebuild output to a manually-built index over the same corpus — same entry count, same ordering |
| `test_auto_rebuild_logs_at_info_or_warning` | Logging fires when rebuild is triggered |

Existing `test_mimisbrunnr_index.py` tests must continue to pass — they use a manually-built index, which is the happy path that does NOT trigger auto-rebuild.

---

## 5. Mythic Engineering wave plan

### Wave 0 — TASK file (this commit)

### Wave 1 — Skald (brief)
- Short 1-paragraph addendum in `docs/vision/ENDURDRYKKR.md` extending the disposition

### Wave 2 — Cartographer
- `docs/cartography/DATA_FLOW.md §4.14.2` addendum: index auto-rebuild path

### Wave 3+4 — Architect+Forge merged
- `_load_or_rebuild_cache` helper in index.py
- `search()` refactor to call it
- 7 new tests

### Wave 5 — Auditor
- `docs/audit/AUDIT_v0.7.3_INDEX_REBUILD.md` — verify auto-rebuild correctness + actionable-error preservation

### Wave 6 — Forge cleanup (only if Wave 5 raises items)

### Wave 7 — Scribe
- DEVLOG entry 21
- TASK seal
- Memory refresh

---

## 6. Forbidden moves

- ☒ Do **not** delete the `heretic library rebuild-index` CLI command. Manual rebuild remains useful.
- ☒ Do **not** trigger auto-rebuild when the index loaded successfully with at least one valid entry. Auto-rebuild is for the failure path only.
- ☒ Do **not** swallow the actionable error when no .txt files exist. The operator must still be told to download.
- ☒ Do **not** introduce a new dependency.

---

## 7. Backlog forward

- v0.7.x mtime-based staleness detection — rebuild when source files are newer than index
- v0.7.x parallel multi-source download — `asyncio.gather` over Endurdrykkr-resumed downloads
- v0.6.3.1 CLI `heretic smidja log` — deferred from v0.6.3
- v0.5.6 polygon-rounded-corners / Bezier — diminishing returns on Blæja
- **v0.8 Opið Vef** — natural roadmap successor; major new faculty

---

*Authored by Runa Gridweaver Freyjasdottir, in the autonomous Mythic Engineering mode 2026-05-09.*
*The next wave is the Skald (brief).*
