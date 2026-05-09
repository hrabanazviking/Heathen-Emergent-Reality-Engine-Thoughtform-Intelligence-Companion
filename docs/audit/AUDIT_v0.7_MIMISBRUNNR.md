# AUDIT — v0.7 Mímisbrunnr (First Drink at the Well)

**Date:** 2026-05-08
**Auditor:** Sólrún Hvítmynd
**Scope:** Commits `0f33ea6` + `4d13e86` + `f5d13e4` (Forge Wave 2 implementation) and preceding scaffold commits `499f1a4` (Architect) + `20cc2f0` (Cartographer)
**Branch:** development
**Environment:** Python 3.10, Windows 11, PowerShell

## Commands run

```
python -m pytest tests/test_mimisbrunnr_manifest.py tests/test_mimisbrunnr_store.py
    tests/test_mimisbrunnr_consent.py tests/test_mimisbrunnr_downloader.py
    tests/test_mimisbrunnr_index.py tests/test_library_client.py
    tests/test_library_tools.py tests/test_library_sense.py
    tests/test_cli_library.py -v --tb=short
→ 219 passed in 1.06s

python -m pytest --tb=short -q
→ 1231 passed, 7 skipped, 48 warnings in 6.87s

npm --prefix frontend run build   (tsc + vite)
→ ✓ built in 1.12s — zero tsc errors, zero build errors

npx --prefix frontend tsc --noEmit
→ clean (zero output)

python -m heretic library --help
python -m heretic library list
python -m heretic version
→ all clean

Grep: import httpx — mimisbrunnr/ + senses/library/
Python runtime probe: vars() of mimisbrunnr.__init__, client, sense modules
python -c "from heretic.skilningr.config_model import LibraryConfig; print(LibraryConfig().enabled)"
→ False
```

---

## Summary verdict

**PASSES SCRUTINY** — with one mandatory close-out item for the Scribe (L-1, serious) and one notable finding (S-1).

All privacy invariants hold structurally. All atomic-write paths are correct. All error paths clean up temp files. The offline invariant is architecturally enforced and verified at runtime. Tests are real, not tautological. The full suite passes.

---

## Finding table

| ID | Severity | Location | Claim | Result |
|----|----------|----------|-------|--------|
| P-1 | — | `config_model.py:722` | `LibraryConfig.enabled = False` | **VERIFIED** |
| P-2 | — | `downloader.py:109` | consent called before network | **VERIFIED** |
| P-3 | — | `downloader.py:212-221` | mismatch → IntegrityError + tmp deleted | **VERIFIED** |
| P-4 | — | `store.py:58,78-83` | traversal rejection via `^[a-z0-9_]+$` | **VERIFIED** |
| P-5 | — | `client.py` (grep + runtime) | zero httpx references in LibraryClient | **VERIFIED** |
| P-6 | — | grep across both subpackages | only `downloader.py:47` imports httpx | **VERIFIED** |
| A-1 | — | `downloader.py:115,236` | `.heretic_tmp` → `os.replace` | **VERIFIED** |
| A-2 | — | `store.py:223,230` | manifest `.heretic_tmp` → `os.replace` | **VERIFIED** |
| A-3 | — | `index.py:141,191` | index JSONL `.heretic_tmp` → `os.replace` | **VERIFIED** |
| T-1 | — | runtime vars() probe | httpx not in client/sense/mimisbrunnr.__init__ globals | **VERIFIED** |
| T-2 | — | `store.py:58` + test parametrize | 11 unsafe ids tested; regex rejects all | **VERIFIED** |
| T-3 | — | `downloader.py:109,212` | consent first; SHA-256 streaming via hashlib.sha256() | **VERIFIED** |
| T-4 | — | `tools.py` + test suite | 3 tools; `type:function`; two-part names; additionalProperties:False | **VERIFIED** |
| F-1 | — | `downloader.py:178-194` | network failures → LibraryDownloadError; tmp cleaned | **VERIFIED** |
| F-2 | — | `downloader.py:213-221` | SHA-256 mismatch → IntegrityError + tmp deleted + log | **VERIFIED** |
| F-3 | — | `client.py:174-180` | source not downloaded → LibraryError (no crash) | **VERIFIED** |
| F-4 | — | `index.py:235-237` | empty query → `[]` (no error) | **VERIFIED** |
| F-5 | — | `store.py:78-83` | traversal attempt → ValueError before path construction | **VERIFIED** |
| F-6 | — | `downloader.py:109` + test | ConsentRefused propagates; httpx never called | **VERIFIED** |
| F-7 | — | `index.py:150-160` | file read I/O error → warning + skip source (graceful) | **VERIFIED** |
| L-1 | **SERIOUS** | `THIRD_PARTY_NOTICES.md` | 5 Norse starter pack sources need named attributions | **ABSENT** |
| S-1 | **NOTABLE** | `manifest.py:136-186` | All 5 SHA-256 hashes are `None` — placeholder not filled | **OPEN** |
| S-2 | nit | `downloader.py:149` | explicit `fh.close()` before `_cleanup_tmp` inside size-cap path | **NOTED** |

---

## Detailed findings

### L-1 — SERIOUS — THIRD_PARTY_NOTICES.md missing 5 source-specific entries

**Claim (TASK §7):** "THIRD_PARTY_NOTICES.md updated with all 5 source attributions" is listed as a v0.7 exit criterion.

**Evidence:** `THIRD_PARTY_NOTICES.md` §"Corpus Data Attribution" contains only a generic Project Gutenberg template block (lines 284–299). There are no named entries for the five specific texts: Prose Edda (Brodeur), Poetic Edda (Bellows), Heimskringla (Laing), Volsunga Saga (Morris/Magnusson), Saga of Erik the Red (Sephton).

The template block explicitly states: *"At ship time, only entries for corpora that the user has actually downloaded should appear in a running installation's THIRD_PARTY_NOTICES.md."* This policy is reasonable for user-installed corpora, but the v0.7 exit criterion required the Scribe to add them. TASK §5 close-out delegates this to the Scribe role.

**Required action (Scribe):** Add five explicit source entries under the L5.9 / Corpus Data attribution section. Each entry should carry: title, URL, translator, year of translation, Project Gutenberg item number, license statement (public domain, PG License), and confirm that these are the five ids in `NORSE_STARTER_PACK`. This is the Scribe's DEVLOG 14 close-out task.

**This is not a code defect** — it is a documentation gap at the close-out boundary. The code correctly attributes sources in `manifest.py` comments; the human-readable NOTICES file simply has not yet been updated by the Scribe as the wave plan required.

---

### S-1 — NOTABLE — All 5 SHA-256 hashes remain `None` in the manifest

**Location:** `src/heretic/skilningr/mimisbrunnr/manifest.py:136,149,162,174,186`

**Evidence (verbatim from manifest.py):**
```python
sha256=None,  # PLACEHOLDER — Forge fills after first verified download
```
All five sources carry this comment. The manifest docstring at line 35 states:
> "SHA-256 hashes are PLACEHOLDER (None) until Forge computes them from the first successful download. They must be filled before v0.7 release."

**Impact:** When `sha256 is None`, `Downloader.download` skips the integrity check and only logs the computed hash. This is documented design — but it means v0.7 ships with no integrity verification for any download until a real download has been run and the hashes recorded. An operator who follows the CLI flow today receives no tamper protection on first download.

**This is not a blocker** — the design explicitly accommodates the None state and logs the hash for the operator to record. However, the hashes should be filled before v0.7 is tagged as a release. This is the Scribe / Forge close-out step stated in the task file. Until filled, integrity verification is a no-op.

**Required action (Forge):** Execute `heretic library download <id> --yes` for each source in a clean environment, capture the logged SHA-256 from each, and update `manifest.py` with the real hashes. Then re-run the audit.

---

### S-2 — NIT — Explicit `fh.close()` before `_cleanup_tmp` in size-cap path

**Location:** `src/heretic/skilningr/mimisbrunnr/downloader.py:149-151`

```python
fh.close()
self._cleanup_tmp(tmp_path)
raise IntegrityError(...)
```

The explicit `fh.close()` is correct — it flushes and releases the file handle before `_cleanup_tmp` attempts deletion (important on Windows where open file handles block `unlink`). The `with tmp_path.open("wb") as fh:` block's `__exit__` will call `close()` a second time as the `IntegrityError` propagates out; this second close on an already-closed `io.BufferedWriter` is a CPython no-op (verified by probe). The pattern is correct on Windows and POSIX alike.

This is a nit only to document the pattern as intentional, not accidentally redundant.

---

## Privacy invariants — full assessment

### P-1: LibraryConfig.enabled defaults False
Verified. `config_model.py:722` declares `enabled: bool = False`. Runtime probe:
```
python -c "from heretic.skilningr.config_model import LibraryConfig; print(LibraryConfig().enabled)"
→ False
```

### P-2: Per-source consent enforced before network
Verified. `downloader.py:109` calls `prompt_for_download(source, auto_yes=auto_yes)` as the first statement in `download()`, before the `httpx.AsyncClient` context manager at line 124. Test `test_consent_refused_propagates_before_network_call` patches `httpx.AsyncClient` with `side_effect=AssertionError` and verifies it is never reached when `ConsentRefused` is raised. **PASSES.**

### P-3: SHA-256 mismatch raises IntegrityError and deletes tmp
Verified. `downloader.py:213-221`: on mismatch, `_cleanup_tmp(tmp_path)` is called, then `IntegrityError` raised. Tests `test_sha256_mismatch_raises_integrity_error`, `test_sha256_mismatch_does_not_write_final_file`, and `test_sha256_mismatch_cleans_up_heretic_tmp` all pass.

### P-4: Storage path validation rejects unsafe source_ids
Verified. `store.py:58`: `_SOURCE_ID_PATTERN = re.compile(r"^[a-z0-9_]+$")`. `_validate_source_id` is called by both `resolve_source_path` and `update_local_manifest` before any path construction. Test `TestResolveSourcePathUnsafe` parametrizes 11 bad ids including `../etc/passwd`, `prose/edda`, `PROSE_EDDA`, empty string, null byte — all correctly raise `ValueError`. **PASSES.**

### P-5: LibraryClient.search/get_text/list_sources make no network calls
Verified by three independent checks:
1. Grep: `import httpx` in `senses/library/` → zero matches (only a docstring comment)
2. Runtime vars() probe: no `httpx` module object in `client` module globals
3. Test `TestOfflineInvariant::test_client_module_does_not_import_httpx` passes

### P-6: Offline invariant structurally enforced — only downloader.py imports httpx
Verified. Grep across all of `mimisbrunnr/` and `senses/library/`:
- `mimisbrunnr/downloader.py:47` — `import httpx` — CORRECT
- All other files — only docstring references to httpx, zero actual imports

The `mimisbrunnr/__init__.py` imports `Downloader` from `downloader.py`, which causes `httpx` to be loaded into `sys.modules` on `import heretic.skilningr.mimisbrunnr`. However, `httpx` does not appear as a named attribute in `mimisbrunnr.__init__.__dict__` — the runtime vars() probe confirmed this. The offline invariant is preserved: no module outside `downloader.py` can call `httpx` through an imported name.

---

## Atomic write invariants — full assessment

### A-1: Downloader — `.heretic_tmp` → `os.replace`
Verified. `downloader.py:115`: `tmp_path = dest_path.with_suffix(".heretic_tmp")`. All writes go to `tmp_path`. On success: `os.replace(str(tmp_path), str(dest_path))` at line 236. On any failure: `_cleanup_tmp(tmp_path)` is called before raising. On size-cap abort: explicit `fh.close()` then `_cleanup_tmp` then raise (line 149-151). `os.replace` is atomic on Windows (replaces atomically within the same volume). **PASSES.**

### A-2: store.update_local_manifest — `.heretic_tmp` → `os.replace`
Verified. `store.py:223-230`: `tmp_path = manifest_path.with_suffix(".heretic_tmp")`. Write to `tmp_path`, then `os.replace`. On OSError: `tmp_path.unlink(missing_ok=True)` in the except block. Test `test_no_heretic_tmp_left_on_disk_after_success` confirms no `.heretic_tmp` remains. **PASSES.**

### A-3: KeywordIndex.build — JSONL atomic write
Verified. `index.py:141`: `tmp_path = index_path.with_suffix(".heretic_tmp")`. All JSONL lines written to `tmp_path`. On success: `os.replace(str(tmp_path), str(index_path))` at line 191. On OSError during write: `tmp_path.unlink(missing_ok=True)` then `LibraryIndexError`. Test `test_build_no_heretic_tmp_left_on_disk` confirms clean state. **PASSES.**

---

## Tool schema correctness (T-4)

Three tools defined in `tools.py`:

| Tool | type | name format | required params | additionalProperties |
|------|------|-------------|-----------------|----------------------|
| library.search | function | two-part ✓ | ["query"] ✓ | False ✓ |
| library.get_text | function | two-part ✓ | ["source_id"] ✓ | False ✓ |
| library.list_sources | function | two-part ✓ | [] ✓ | False ✓ |

All 11 tool schema tests pass. Schema conforms to OpenAI tool_use spec.

---

## Downloader — Architect's highest-risk module

All risk points verified:
- **SHA-256 streaming:** `hashlib.sha256()` at line 120; `hasher.update(chunk)` per chunk at line 160; `hexdigest()` after loop at line 210. Streaming — no full-content load.
- **Size cap:** `size_cap = int(source.expected_size_bytes * 1.5)` at line 114. Guard at line 148: `if total_bytes > size_cap` — checked per chunk before write and hash update. Abort path: `fh.close()`, `_cleanup_tmp`, `IntegrityError`.
- **Cleanup on all error paths:** Verified for (a) size cap, (b) SHA-256 mismatch, (c) HTTP non-200, (d) `httpx.HTTPStatusError`, (e) `httpx.TransportError`, (f) `httpx.TimeoutException`, (g) `httpx.RequestError`, (h) bare `Exception`. Each handler calls `_cleanup_tmp` before raising.
- **Atomic os.replace:** Line 236. Windows-safe — `os.replace` is atomic on NTFS within the same volume.
- **Consent first:** Line 109. Before any `async with httpx.AsyncClient`.

**Test coverage for Downloader:** 13 tests across 4 classes. All pass.

---

## Failure modes

| Mode | Handling | Test |
|------|----------|------|
| F-1: network fail | `LibraryDownloadError`; tmp cleaned | `test_transport_error_raises_library_download_error` ✓ |
| F-2: SHA-256 mismatch | `IntegrityError`; tmp deleted; logged | `test_sha256_mismatch_*` (3 tests) ✓ |
| F-3: source not on disk | `LibraryError("not been downloaded")` | `test_get_text_raises_for_undownloaded_source` ✓ |
| F-4: index empty / no index | `[]` for empty query; `LibraryIndexError` for no-index | `test_search_raises_library_index_error_when_no_index` ✓ |
| F-5: traversal attempt | `ValueError` at store entry point | `test_unsafe_id_raises_value_error` (11 params) ✓ |
| F-6: consent refused | `ConsentRefused`; no network call | `test_consent_refused_propagates_before_network_call` ✓ |
| F-7: corpus I/O error during index build | warning + skip source | `index.py:155-160` — graceful skip, no test for this specific path |

**Gap noted for F-7:** No test exercises the `except OSError` path in `KeywordIndex.build()` (lines 155-160) where a `.txt` file exists but is unreadable. The code is correct (logs warning, continues), but the failure path lacks a dedicated test. Severity: nit.

---

## CLI smoke

```
python -m heretic library --help   → clean; shows list/download/remove/rebuild-index subcommands
python -m heretic library list     → clean; shows all 5 sources, 0/5 downloaded, data_dir resolved
python -m heretic version          → 0.1.0.dev0 (clean)
```

Windows path in `heretic library list`: `C:\Users\volma\AppData\Local\heretic\library\mimisbrunnr` — correct platformdirs resolution via `user_data_dir("heretic")`.

---

## Test count

| Suite | Tests | Result |
|-------|-------|--------|
| v0.7 new: mimisbrunnr + library (all 9 files) | 219 | 219 passed |
| Full suite (Python) | 1238 | 1231 passed, 7 skipped |
| Frontend (tsc + vite build) | — | clean |

Net new tests vs. baseline (1012 + 7 skipped): +219 Python tests. Target was ≥1042; actual is 1231. Exit criterion met.

---

## Cross-platform assessment

- `os.replace` — atomic on NTFS (Windows) and POSIX (Linux/macOS). Windows: replaces atomically within the same volume; source and dest are in the same `data_dir`. **VERIFIED safe.**
- `platformdirs.user_data_dir("heretic")` — resolves to `%APPDATA%\Local\heretic` on Windows, `~/.local/share/heretic` on Linux, `~/Library/Application Support/heretic` on macOS. Verified correct on Windows via CLI smoke.
- Path construction: `data_dir / f"{source_id}.txt"` — `pathlib.Path` handles separators cross-platform.
- `Path.with_suffix(".heretic_tmp")` — POSIX and Windows compatible. Verified via probe.

---

## License attribution (L-1 detail)

`THIRD_PARTY_NOTICES.md` contains (line 284):
> *"Corpus Data Attribution (L5.9 Mímisbrunnr — downloaded by user) — The following corpus entries are added automatically when a user downloads a library source… At ship time, only entries for corpora that the user has actually downloaded should appear."*

This policy creates an ambiguity: the ship-time file for the HERETIC repository should name the five sources in the starter pack, since they are bundled in the manifest. They are not user-chosen — they are the curated set. The five specific sources — Prose Edda (Brodeur, 1916, PG #18947), Poetic Edda (Bellows, 1923, PG #73533), Heimskringla (Laing, 1844, PG #598), Volsunga Saga (Morris/Magnusson, 1888, PG #1152), Saga of Erik the Red (Sephton, 1880, PG #17946) — require named entries.

**Scribe action required for close-out:** Add five named entries under §"Corpus Data Attribution (L5.9 Mímisbrunnr)". Update the `Last updated` field to 2026-05-08.

---

## Unverified claims

One claim from the v0.7 exit criteria remains **unverifiable until real downloads run:**

> "Operator can `heretic library download prose_edda --yes` and SHA-256 verifies; file lands in correct path."

This cannot be verified without a real network call. The code path is correct and all logic is tested via mocked httpx. The actual SHA-256 values in the manifest are `None`. Until those are filled from a real download, the integrity gate is a no-op. This is a known pre-release state documented in the manifest comments, not a hidden defect.

---

## Verdict

**PASSES SCRUTINY** — with two named items before release tag:

1. **L-1 (Serious — Scribe):** Add five named Project Gutenberg source entries to `THIRD_PARTY_NOTICES.md`.
2. **S-1 (Notable — Forge):** Fill all five `sha256` placeholders in `manifest.py` from a real download run before the v0.7 release tag.

No blockers. No regressions. No invariant violations. The well holds its waters. The offline invariant is structurally unbreakable. The consent gate fires first, every time.

---

*The well must hold its waters in the dark — even when no one is drinking.*
*Sólrún Hvítmynd, 2026-05-08*
