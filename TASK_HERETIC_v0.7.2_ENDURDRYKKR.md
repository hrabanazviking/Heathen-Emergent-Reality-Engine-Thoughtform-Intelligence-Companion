# TASK — HERETIC v0.7.2 ENDURDRYKKR (Resumable Downloads for Mímisbrunnr)

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-09** (immediately after v0.5.5 *Mjúkblæja* sealed at `2fff370`)
>
> **Codename (proposed, Skald to seal):** *Endurdrykkr* — "the resumed drink." Old Norse compound *endur-* (again) + *drykkr* (drink). Continues the v0.7 Mímisbrunnr (Mímir's Well) metaphor: when a draught from the well is interrupted, the body picks up the same drink rather than starting over.
>
> **Mythic Engineering mode:** AUTONOMOUS continuation. Volmarr asleep / hands-off; this is the FIFTH milestone of the autonomous session — and a deliberate shift away from the *Blæja* axis to a different system (knowledge well, not sight).

---

## 1. Task scope

Add **resumable downloads** to `mimisbrunnr/downloader.py` via HTTP `Range` requests. When a download is interrupted (network error, host shutdown, ceremony Slokna mid-fetch), the partial bytes are preserved in `.heretic_tmp` and the next download attempt **resumes from the byte offset** rather than re-fetching from scratch.

Without resume, every interruption costs the operator the whole download. For Norse starter-pack files this is a few MB; for future v0.8 ZIM corpora (Wikipedia, Wiktionary) this could be tens to hundreds of GB. The asymmetry between successful and interrupted downloads becomes prohibitive at that scale.

The existing v0.7 Downloader already streams to `.heretic_tmp` and renames atomically on success. v0.7.2 changes the *failure recovery* path: on the next download attempt, instead of deleting the `.heretic_tmp` and starting over, we hash the existing partial bytes, send `Range: bytes=N-` to the server, and continue writing+hashing from offset N.

---

## 2. Current status — 2026-05-09

**Phase:** v0.7.2 **OPEN — wave plan published, no code written yet.**

**HEAD (development):** `2fff370` (v0.5.5 Scribe seal — parent of upcoming Wave 0 commit)

**Test count baseline:** Mímisbrunnr downloader tests at `tests/test_mimisbrunnr_downloader.py`. Sjón privacy 74 + encoder 24 + Sjón total 219 carried from v0.5.5.

### v0.7.2 deliverables — pending

- ☐ Skald — `docs/vision/ENDURDRYKKR.md` — short essay on continuity-of-draught
- ☐ Cartographer — `docs/cartography/DATA_FLOW.md §4.14.1` addendum: resume flow + 206/200 dispatch + SHA-256 continuation across the seam
- ☐ Architect+Forge — refactor `Downloader.download()` to detect existing `.heretic_tmp`, hash partial bytes, send Range request, handle 206 (Partial Content) vs 200 (server didn't honour Range) vs 416 (Range Not Satisfiable); update INTERFACE.md
- ☐ Forge — 12+ new tests covering: clean-slate download (existing v0.7 behaviour), resume from partial tmp, server returns 206 with Content-Range, server returns 200 (full body — restart), server returns 416 (delete tmp + retry full), partial sha256 verification, resumed sha256 matches manifest after seam
- ☐ Auditor — `docs/audit/AUDIT_v0.7.2_ENDURDRYKKR.md` — verifies (1) consent gate still runs first, (2) full-file SHA-256 matches manifest after resume, (3) safety size cap still applies across resumed bytes, (4) atomic rename only on full success, (5) tmp file preserved on interruption (NOT cleaned up on retry-able errors)
- ☐ Scribe — DEVLOG entry 19; TASK seal; memory refresh

### What v0.7.2 does NOT add

- Multi-source concurrent downloads (`asyncio.gather` over multiple sources) — out of scope; single-source sequential behaviour is preserved
- Bandwidth throttling — operator can use OS-level shaping if needed
- Mid-download checksum chunking (Merkle-style) — full-file SHA-256 is the only integrity check; matches manifest format
- Pause/resume UI controls — operator just hits the same `heretic library download <id>` command twice
- Server-driven content-encoding renegotiation — Range works with identity content-encoding only

---

## 3. Architectural decisions (Architect to confirm)

| Decision | Choice | Rationale |
|---|---|---|
| Resume detection | Check if `.heretic_tmp` exists at `dest_path.with_suffix(".heretic_tmp")` and has `size > 0` before any network call | Single source of truth; the existing tmp-file convention already exists |
| Partial-byte hashing | Hash all bytes of `.heretic_tmp` into the streaming SHA-256 hasher BEFORE issuing the Range request | The downloader's running SHA-256 must include partial bytes so the final digest matches the full-file hash |
| Range header | `Range: bytes=N-` (open-ended) where N = existing partial size | Standard HTTP/1.1 spec; servers either honour or 416 |
| Response status dispatch | `206` → resume (server confirmed range); `200` → restart (server returned full body — likely doesn't support Range); `416` → restart (Range Not Satisfiable) | Only 206 means "I am giving you bytes from offset N onwards" |
| 200-on-resume-attempt handling | Reset the hasher; truncate `.heretic_tmp`; treat as fresh download | The server is sending the full body, so we can't append it to the partial |
| 416 handling | Delete `.heretic_tmp`; raise an internal-only signal that triggers a fresh-start retry within the same `download()` call | Range was unsatisfiable (e.g. partial size > current file size — the source file has changed); start fresh |
| Append vs rewrite of tmp | Open `.heretic_tmp` in `"ab"` mode for resume; in `"wb"` for fresh-start; in `"wb"` for the post-200/416 restart inside the same call | Append preserves the existing partial bytes; truncating opens for the fresh path |
| Safety size cap | Counted across all bytes (resumed + new). Cap = `expected * 1.5` | Same semantic as v0.7 — total bytes received cannot exceed the cap regardless of whether they came in one connection or two |
| Atomic rename | Unchanged — `os.replace(tmp, dest)` only on successful SHA-256 verification | The contract is "either you get a complete file at dest or you get nothing" |
| Failure-mode tmp preservation | On `httpx.TransportError` / `httpx.TimeoutException` / `httpx.RequestError` / generic `OSError` during streaming: the `.heretic_tmp` is **preserved** so the next call can resume. On `IntegrityError` (cap exceeded or SHA-256 mismatch): the `.heretic_tmp` is **deleted** because the file is poisoned | Resume-able vs resume-not-able distinction. Network errors leave salvageable bytes; integrity errors mean the bytes themselves are wrong. |
| Logging | INFO log at start indicating "resuming from N bytes" when partial exists; INFO log at end indicating "wrote N+M bytes total" | Operator can see resume happened |
| Backward compatibility | Existing v0.7 Downloader.download() signature unchanged. New behaviour is automatic when `.heretic_tmp` exists with non-zero size | No new flags; resume is always tried; explicit "force fresh" is achieved by deleting `.heretic_tmp` manually |

---

## 4. Privacy & integrity invariants (Auditor verification subjects)

The v0.7 Mímisbrunnr invariants are inherited and must continue to hold:

| # | Invariant | v0.7 status | v0.7.2 verification |
|---|-----------|-------------|---------------------|
| M-1 | Consent gate runs FIRST, before any network activity | ✓ | Re-verify; resume detection runs after consent |
| M-2 | Atomic rename — `dest_path` only exists when complete and verified | ✓ | Re-verify; intermediate state stays in `.heretic_tmp` until SHA-256 verified |
| M-3 | SHA-256 verification gates the rename | ✓ | Extended: SHA-256 of full file (including resumed bytes) must match manifest |
| M-4 | Safety size cap aborts oversize responses | ✓ | Extended: cap counted across resumed + new bytes (cumulative) |
| M-5 | `LibraryClient` does not import httpx | ✓ | Unchanged — v0.7.2 only edits the existing httpx-importing module |
| M-6 | Offline invariant — sense reports NOT_AVAILABLE without network | ✓ | Unchanged |

New v0.7.2 invariants:

| # | Invariant |
|---|-----------|
| **M-7** | The full-file SHA-256 hash after resume equals the SHA-256 of the bytes that *would have been written* by a single uninterrupted download — i.e., partial-byte hashing across the seam preserves digest correctness. |
| **M-8** | On resume-able failure (network error during streaming), `.heretic_tmp` is preserved. On non-resume-able failure (SHA-256 mismatch, size cap exceeded), `.heretic_tmp` is deleted. The distinction is documented per failure-mode in the audit. |
| **M-9** | When a server returns 200 instead of the requested 206 (server doesn't support Range), the downloader resets the hasher, truncates the tmp file, and restarts the streaming write — without raising. The operator sees "resume attempted, server returned full body, downloading fresh" in the INFO log. |

---

## 5. Resume flow sketch (for Cartographer)

```
  ENDURDRYKKR — RESUME FLOW

  Step 1 — Consent gate (UNCHANGED)
    prompt_for_download(source, auto_yes=auto_yes)

  Step 2 — Resume detection
    tmp_path = dest_path.with_suffix(".heretic_tmp")
    if tmp_path.exists() and tmp_path.stat().st_size > 0:
        partial_size = tmp_path.stat().st_size
        # Hash existing partial bytes into hasher BEFORE network
        hasher = hashlib.sha256()
        with tmp_path.open("rb") as fh:
            while chunk := fh.read(_CHUNK_SIZE):
                hasher.update(chunk)
        total_bytes = partial_size
        request_headers = {"Range": f"bytes={partial_size}-"}
        log.info("Resuming download of %r from byte %d", source.id, partial_size)
        write_mode = "ab"   # APPEND — preserve partial bytes
    else:
        partial_size = 0
        hasher = hashlib.sha256()
        total_bytes = 0
        request_headers = {}
        write_mode = "wb"   # WRITE — fresh tmp file

  Step 3 — HTTP stream with optional Range header
    async with httpx.AsyncClient(...) as client:
        async with client.stream("GET", source.url, headers=request_headers) as response:
            # Step 3a — Status dispatch
            if response.status_code == 206:
                # Partial Content — server honoured Range; append to existing tmp
                pass
            elif response.status_code == 200:
                # Server returned full body — server didn't honour Range OR
                # we sent no Range. If partial_size > 0, this means the server
                # ignored our Range; reset and treat as fresh download.
                if partial_size > 0:
                    log.info(
                        "Resume requested but server returned 200; "
                        "restarting fresh download of %r", source.id,
                    )
                    hasher = hashlib.sha256()
                    total_bytes = 0
                    write_mode = "wb"
                # else: this is a normal fresh download
            elif response.status_code == 416:
                # Range Not Satisfiable — partial may be larger than the
                # current source file; delete tmp and retry as fresh
                tmp_path.unlink(missing_ok=True)
                hasher = hashlib.sha256()
                total_bytes = 0
                # NOTE: For v0.7.2 we re-raise here as a recoverable error;
                # the operator's next call will start fresh.
                raise LibraryDownloadError(
                    f"Range not satisfiable for {source.id!r}; partial "
                    "removed. Run download again to start fresh."
                )
            else:
                raise LibraryDownloadError(...)

            # Step 3b — Stream body, append/write to tmp, update hasher
            with tmp_path.open(write_mode) as fh:
                async for chunk in response.aiter_bytes(chunk_size=_CHUNK_SIZE):
                    total_bytes += len(chunk)
                    if total_bytes > size_cap:
                        # Same as v0.7: integrity error, delete tmp, raise
                        ...
                    hasher.update(chunk)
                    fh.write(chunk)

  Step 4 — SHA-256 verify (UNCHANGED)
    computed_sha256 = hasher.hexdigest()
    if source.sha256 is not None and computed_sha256 != source.sha256:
        # NON-RESUMABLE failure — delete tmp
        self._cleanup_tmp(tmp_path)
        raise IntegrityError(...)

  Step 5 — Atomic rename (UNCHANGED)
    os.replace(str(tmp_path), str(dest_path))
```

---

## 6. Test plan

New tests in `tests/test_mimisbrunnr_downloader.py`:

| Test | Asserts |
|---|---|
| `test_resume_detects_existing_tmp_and_sends_range` | When `.heretic_tmp` exists with size N, a Range header `bytes=N-` is sent in the request |
| `test_resume_206_appends_to_partial_tmp` | Server returns 206 with the remaining bytes; final file equals expected content |
| `test_resume_full_sha256_matches_after_seam` | SHA-256 of resumed file matches the SHA-256 of the equivalent uninterrupted full download |
| `test_resume_server_returns_200_restarts_fresh` | Server ignored Range and returned 200; partial tmp truncated; full body written; logs note the restart |
| `test_resume_server_returns_416_deletes_tmp_and_raises` | Range not satisfiable; tmp deleted; LibraryDownloadError raised with explanatory message |
| `test_no_resume_when_tmp_does_not_exist` | Fresh download — no Range header sent |
| `test_no_resume_when_tmp_is_empty` | Empty `.heretic_tmp` (zero bytes) is treated as no-tmp; fresh download |
| `test_resume_cumulative_size_cap_still_applies` | If resumed bytes + new bytes exceed the safety cap, IntegrityError raised; tmp deleted |
| `test_network_error_during_resume_preserves_tmp` | Transport error during the resumed stream leaves the tmp file intact (M-8) |
| `test_sha256_mismatch_after_resume_deletes_tmp` | Final SHA-256 mismatch after resume → tmp deleted (M-8) |
| `test_consent_gate_runs_before_resume_detection` | Consent refused → no tmp file inspection |
| `test_resume_then_full_dest_already_exists` | dest_path file exists already (full file present) — caller's responsibility, but if .heretic_tmp also exists, resume tries; verify clean behaviour |

Existing tests in `test_mimisbrunnr_downloader.py` must continue to pass unchanged — `.heretic_tmp` does not exist in their fixtures.

---

## 7. Mythic Engineering wave plan

### Wave 0 — TASK file (this commit)

### Wave 1 — Skald
- `docs/vision/ENDURDRYKKR.md` — short essay on continuity-of-draught

### Wave 2 — Cartographer
- `docs/cartography/DATA_FLOW.md §4.14.1` addendum with resume flow + 206/200/416 dispatch table

### Wave 3+4 — Architect+Forge merged (matches v0.5.4 / v0.5.5 pattern)
- Refactor `Downloader.download()` to add resume detection + partial-byte hashing + Range request + status dispatch
- INTERFACE.md update
- 12 new tests
- Run full Mímisbrunnr suite; confirm 0 regressions

### Wave 5 — Auditor
- `docs/audit/AUDIT_v0.7.2_ENDURDRYKKR.md`
- Verify M-1..M-9
- Honest negative audit

### Wave 6 — Forge cleanup (only if Wave 5 raises items)

### Wave 7 — Scribe
- DEVLOG entry 19
- TASK §2 sealed
- Memory files updated

---

## 8. Forbidden moves

- ☒ Do **not** change the `Downloader.download()` signature. Resume is automatic; no new `resume: bool` flag.
- ☒ Do **not** introduce a new dependency. httpx already supports Range via `headers=`.
- ☒ Do **not** delete `.heretic_tmp` on transport-level errors. Network errors must leave the partial file resumable.
- ☒ Do **not** weaken the SHA-256-mismatch path. Mismatch = tmp deleted (M-8).
- ☒ Do **not** weaken the consent-gate-first invariant. M-1 must hold.
- ☒ Do **not** break the offline invariant (M-5). Only the existing Downloader file gets the change.

---

## 9. Backlog forward (post-v0.7.2)

| Item | Notes |
|---|---|
| v0.7.x corrupt index auto-rebuild | If index is invalid, rebuild from sources without re-downloading |
| v0.7.x parallel multi-source download | `asyncio.gather` over a list of sources |
| v0.5.6 polygon-rounded-corners / Bezier paths | Diminishing returns on Blæja vocabulary |
| v0.5.x mask inversion | "show only this region; veil all else" |
| v0.5.x window-tracking masks | OS window enumeration |
| v0.6.x.1 MCP resources | mcp_server.py extension |
| v0.6.x Mode C Smiðja composition | Multi-step orchestration |
| **v0.8 Opið Vef** | Playwright; major roadmap successor |
| v0.9 Málari | Photopea editor |
| v0.10 Langhúsið Ytra | VRChat OSC + MindSpark |
| v0.11 Bréfasamtök | Email |
| v0.4.1 first compile | MSVC Build Tools — operator-blocked |

---

## 10. Session-resumption pointer

If interrupted before Wave 7 closes:
1. Read this TASK file §2 for current phase
2. `git log --oneline -35` — identify which Wave commits exist
3. Continue from the first missing Wave

---

*Authored by Runa Gridweaver Freyjasdottir, in the autonomous Mythic Engineering mode requested by Volmarr 2026-05-09.*
*The next wave is the Skald.*
