# AUDIT — HERETIC v0.7.2 *Endurdrykkr* (Resumable Downloads)

**Date:** 2026-05-09
**Auditor:** Sólrún Hvítmynd (The Auditor for Vibe Coding)
**Subject:** v0.7.2 — Resumable downloads for `mimisbrunnr/downloader.py`
**Subject HEAD at audit time:** `6b7aad4` (Architect+Forge merged Wave close)

---

## Verdict

**PASSES SCRUTINY — 0 BLOCKERS, 0 NOTABLE FINDINGS, 0 NITS.**

The six v0.7 Mímisbrunnr invariants M-1 through M-6 are inherited and continue to hold. The three new v0.7.2 invariants M-7 (full SHA-256 across the seam), M-8 (resumable vs non-resumable failure tmp disposition), and M-9 (200-on-resume graceful restart) are verified by direct test evidence. Resume is automatic (no new flag); fresh-download behaviour for the no-tmp case is byte-equivalent to v0.7. The resumable/non-resumable disposition table is internally consistent and protects the operator from drinking poisoned partials. No regression in the broader suite.

---

## What I Verified (Evidence Trail)

### V-1: M-1 inherited unchanged — consent gate runs FIRST

**Claim:** `prompt_for_download(source, auto_yes=auto_yes)` is called before any disk inspection or network activity.

**Evidence:**
- `downloader.py:122` — `prompt_for_download` is the first executable statement inside `download()`, before the `tmp_path` declaration on line 132 and certainly before the resume-detection block (line 144 onwards).
- Test `test_consent_runs_before_resume_detection` patches `prompt_for_download` to raise `ConsentRefused` and asserts that the pre-existing `.heretic_tmp` file is unchanged. **Test passes.** Consent ran before tmp inspection.

**Status:** VERIFIED.

### V-2: M-2 inherited — atomic rename only on success

**Claim:** `dest_path` only exists when SHA-256 verification has passed.

**Evidence:** `os.replace(str(tmp_path), str(dest_path))` is called only after the SHA-256 verification block (line ~330), unchanged from v0.7. Resume does not move this seam — partial bytes live in `.heretic_tmp` until the full file is verified, exactly as before.

**Status:** VERIFIED.

### V-3: M-3 inherited — SHA-256 mismatch raises and deletes tmp

**Claim:** When the manifest's `sha256` is set and the computed digest does not match, `IntegrityError` is raised and `.heretic_tmp` is deleted.

**Evidence:**
- `_cleanup_tmp(tmp_path)` is called at line ~325 immediately before the `IntegrityError` raise on SHA mismatch.
- Test `test_sha256_mismatch_after_resume_deletes_tmp` constructs a resume scenario where the final SHA-256 does not match the manifest hash, asserts `IntegrityError` is raised AND `.heretic_tmp` is deleted (not preserved). **Test passes.** Non-resumable failure correctly disposes of the poisoned partial.

**Status:** VERIFIED.

### V-4: M-4 inherited — safety size cap aborts oversize responses (cumulative across seam)

**Claim:** Cumulative bytes received cannot exceed `expected * 1.5`, regardless of whether bytes came in one connection or two.

**Evidence:**
- `total_bytes` is initialised to `partial_size` (the existing tmp's size) at the resume-detection block. The streaming-body loop adds new chunk sizes to this counter, so the cap check is genuinely cumulative.
- Test `test_size_cap_counts_resumed_plus_new_bytes`: 100-byte expected source (cap = 150 bytes); pre-fills tmp with 140 bytes; server returns 50 more bytes (total = 190 > 150). Asserts `IntegrityError` is raised AND `.heretic_tmp` is deleted. **Test passes.**

**Status:** VERIFIED.

### V-5: M-5 inherited — offline invariant preserved

**Claim:** `LibraryClient` does not import httpx; only `Downloader` does.

**Evidence:** v0.7.2 only edits `mimisbrunnr/downloader.py` and `tests/test_mimisbrunnr_downloader.py`. No other module gains an httpx import. The v0.7 architectural rule that the Downloader is the *single* httpx-importing module is unchanged.

**Status:** VERIFIED.

### V-6: M-6 inherited — sense remains opt-in / library defaults disabled

**Claim:** Library sense's enabled-default behaviour is unchanged.

**Evidence:** v0.7.2 only changes the body of `Downloader.download()`. The sense's config dataclass and the `LibrarySense.dispatch_tool_call` flow are not edited.

**Status:** VERIFIED.

### V-7: NEW — full-file SHA-256 correctness across the resume seam

**Claim:** When a download is interrupted at byte N and resumed, the final SHA-256 hash equals the SHA-256 of the bytes that would have been written by a single uninterrupted download.

**Evidence:** This is the load-bearing invariant of v0.7.2. The mechanism is: the partial bytes already on disk are fed into `hashlib.sha256()` BEFORE the network call, then new chunks are fed into the same hasher object as they arrive. The final `hasher.hexdigest()` consumes the same bytes in the same order as a single uninterrupted call would.

- Test `test_resume_full_sha256_matches_after_seam`: pre-fills tmp with the first quarter of `sample_content`; server returns 206 with the remaining three-quarters; asserts the returned hash equals `sample_content_sha256` (the hash of the full content). **Test passes.** M-7 verified.
- Reading the implementation: `hasher = hashlib.sha256()` (line ~138); the partial-read loop at lines 154-159 calls `hasher.update(chunk)` on each chunk read from `.heretic_tmp`; the streaming-write loop at line ~298 calls `hasher.update(chunk)` on each new chunk from the response. The two loops feed the same hasher in the order: partial bytes first, then new bytes. This is the only correct order.

**Status:** VERIFIED.

### V-8: NEW — resumable vs non-resumable failure disposition

**Claim:** Network-level errors preserve `.heretic_tmp` for the next call's resume; integrity errors delete it because the partial bytes are poisoned.

**Evidence:**

**Non-resumable failures (tmp DELETED):**
- `IntegrityError` (size-cap exceeded): `_cleanup_tmp(tmp_path)` called before raise (line ~289). Confirmed by `test_size_cap_counts_resumed_plus_new_bytes`.
- `IntegrityError` (SHA mismatch): `_cleanup_tmp(tmp_path)` called before raise (line ~325). Confirmed by `test_sha256_mismatch_after_resume_deletes_tmp`.
- 416 Range Not Satisfiable: `_cleanup_tmp(tmp_path)` called before raise (line ~226). Confirmed by `test_server_returns_416_deletes_tmp_and_raises`.

**Resumable failures (tmp PRESERVED):**
- `httpx.TransportError`: no `_cleanup_tmp` call in the except branch (lines ~351-356). Confirmed by `test_network_error_during_resume_preserves_tmp` — pre-fills tmp with N bytes, raises TransportError at stream creation, asserts tmp file still exists with the same N bytes.
- `httpx.TimeoutException`: same — no `_cleanup_tmp`.
- `httpx.RequestError`: same.
- `httpx.HTTPStatusError`: same.
- Generic `Exception` (line ~378): the message says "Partial file (if any) preserved at {tmp_path}" — no `_cleanup_tmp` call. (The v0.7 code DID call `_cleanup_tmp` here; v0.7.2 changed that to align with the resumable-failure principle.)

This is the M-8 contract the Skald named: *recoverable interruptions are forgiven; poisoned partials are dropped*.

**Status:** VERIFIED.

### V-9: NEW — 200-on-resume graceful restart

**Claim:** When a Range request is sent but the server returns 200 (full body), the downloader resets the hasher, truncates the tmp file, and continues without raising.

**Evidence:**
- Status dispatch block at line ~196-219: when `response.status_code == 200` AND `partial_size > 0` (i.e., we asked for a Range), the code resets `hasher = hashlib.sha256()`, `total_bytes = 0`, and sets `write_mode = "wb"` (which truncates on next file open).
- Test `test_server_returns_200_on_resume_request_restarts_fresh`: pre-fills tmp with deliberately *wrong* content (`b"this is wrong partial content"`); server returns 200 with the correct full body; asserts the final SHA-256 matches the full-content hash (the wrong partial was discarded). **Test passes.**

The behaviour is exactly what M-9 promises: the body did not raise; it accepted the world's actual answer (200 with full body) and produced a correct file.

**Status:** VERIFIED.

### V-10: Backward compatibility — fresh download path unchanged

**Claim:** When no `.heretic_tmp` exists, the download flow is byte-equivalent to v0.7.

**Evidence:**
- Test `test_no_resume_when_tmp_does_not_exist`: no tmp file pre-created; asserts no `Range` header is sent and the download completes normally.
- Test `test_no_resume_when_tmp_is_empty`: empty (zero-byte) tmp file pre-created; asserts treated as "no tmp" — no Range header, normal fresh download.
- All 13 v0.7 baseline downloader tests continue to pass unchanged at HEAD `6b7aad4`. None was modified for v0.7.2 — they all assumed no pre-existing tmp file in their fixtures, and that's still correct.

**Status:** VERIFIED.

### V-11: Test integrity

**Claim:** The 11 new tests assert real properties, not mocked tautologies.

**Evidence:**
- Tests construct real `LibrarySource` dataclasses, real synthetic content bytes, real mock responses with explicit chunk control via `_make_mock_streaming_response`.
- Tests inspect actual disk state (`tmp_file.exists()`, `tmp_file.stat().st_size`, `tmp_file.read_bytes()`) and the actual `Range` header captured via the new `_make_capturing_client` helper.
- The SHA-256 verification test (`test_resume_full_sha256_matches_after_seam`) compares the runtime-computed digest against `hashlib.sha256(sample_content).hexdigest()` — the canonical full-content digest. There is no way to satisfy this assertion without the partial-byte-hashing mechanism actually working end-to-end.

**Status:** VERIFIED.

### V-12: No new dependency

**Claim:** v0.7.2 introduces no new pip / runtime dependency.

**Evidence:** `pyproject.toml` not edited (`git diff --stat 2fff370..6b7aad4 pyproject.toml` returns nothing). httpx already supports the `headers=` kwarg on `client.stream()`.

**Status:** VERIFIED.

---

## Test Suite Status (post-Wave 4 close)

### Mímisbrunnr scope (the milestone surface)

| File | Tests | Status |
|---|---|---|
| `tests/test_mimisbrunnr_downloader.py` | 13 (v0.7) + 11 (v0.7.2) = 24 | 24/24 passing |
| `tests/test_mimisbrunnr_index.py` | unchanged | passing |
| `tests/test_mimisbrunnr_store.py` | unchanged | passing |
| `tests/test_mimisbrunnr_consent.py` | unchanged | passing |
| `tests/test_mimisbrunnr_manifest.py` | unchanged | passing |
| `tests/test_library_*` | unchanged | passing |

### Broader suite

The 20 pre-existing environment failures (`fastapi` / `mcp` not installed) are byte-identical in stash diff. v0.7.2 introduced **zero** new regressions. Pass-count delta `+23` reflects 11 new v0.7.2 tests + 12 collection-variance recoveries that are unrelated to the milestone surface.

---

## Cross-Document Consistency

- **TASK_HERETIC_v0.7.2_ENDURDRYKKR.md §3** decision table — every choice (Range header format, write-mode dispatch, status-code dispatch table, failure-mode tmp disposition) matches the implementation.
- **docs/cartography/DATA_FLOW.md §4.14.1.1** — the resume-flow diagram, the HTTP status disposition table, and the resumable-vs-non-resumable failure table all match the Python code's actual control flow.
- **docs/vision/ENDURDRYKKR.md §III, §V** — the Skald's "five statuses" essay (206 / 200 / 416 / 4xx-5xx / network blink) and the resumable/non-resumable distinction match the implementation behaviour.
- **src/heretic/skilningr/mimisbrunnr/downloader.py** — module docstring's ENDURDRYKKR section names M-7/M-8/M-9 explicitly; the implementation honours each.

No contradictions between the four written sources and the code.

---

## What I Did NOT Find (Honest Negative Audit)

- **No silent bypass on consent failure.** The consent gate is the first executable statement; tmp inspection is downstream.
- **No silent SHA-256 corruption.** The partial bytes are read in the same chunk size used for the streaming write — no buffer-misalignment bugs.
- **No leftover hash state on the 200-restart path.** `hasher = hashlib.sha256()` reassignment creates a fresh hasher object; the Python garbage collector reclaims the old one. The restart truly starts from zero state.
- **No race between consent and tmp inspection.** Both run synchronously inside the `download()` async coroutine before any `await`.
- **No new mutable global.** All state lives in local variables of `download()`.
- **No subtle off-by-one in Range header.** `f"bytes={partial_size}-"` requests bytes from offset `partial_size` (inclusive). The server responds with bytes [partial_size, end-of-file], which is exactly the bytes we don't already have.
- **No accidental tmp-deletion on 4xx.** The except branches for `httpx.HTTPStatusError` (which would catch a 4xx if raised by httpx itself) do NOT call `_cleanup_tmp` — preserving the partial for resume. This is correct M-8 behaviour for 4xx (other than 416, which is dispatched explicitly upstream).

---

## Findings

**0 BLOCKER. 0 SERIOUS. 0 NOTABLE. 0 NIT.**

The Auditor records no further work for v0.7.2. The Forge does not need a Wave 6 cleanup pass. The Scribe may proceed to seal.

---

*Authored by Sólrún Hvítmynd, The Auditor for Vibe Coding, 2026-05-09. The next wave is the Scribe.*
