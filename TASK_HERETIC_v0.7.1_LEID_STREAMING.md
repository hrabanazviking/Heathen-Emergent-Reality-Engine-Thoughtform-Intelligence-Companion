# TASK — HERETIC v0.7.1 LEID STREAMING

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-09** (immediately after v0.7 Mímisbrunnr shipped + audited + cleaned at `27568cd`)
>
> **Codename (proposed, Skald to seal):** *Straumr í Brunni* — "the stream within the well." The river does not need to fill the cup before it can be tasted; the body learns to drink as the water flows.
>
> **Mythic Engineering mode:** AUTONOMOUS. Volmarr asleep / hands-off. All six roles run on this single milestone within one session. No operator-side blockers anticipated.

---

## 1. Task scope

Close audit-deferred finding **N-2** from `docs/audit/AUDIT_v0.6.2_MORE_SENSES.md`:

> *"Leid response cap is a post-download buffer slice, not a streaming abort. `response.content` reads the entire body into memory before the size check runs. A streaming implementation (httpx `aiter_bytes`) would be the correct fix in v0.6.2.1."*

Replace the buffer-then-check pattern in `src/heretic/skilningr/senses/leid/client.py:284-298` with **true streaming via `httpx.AsyncClient.stream()` + `aiter_bytes`** — the connection is closed and `LeidResponseTooLargeError` is raised **as soon as accumulated bytes exceed `max_response_bytes`**, not after the full body is materialised in memory.

The error class `LeidResponseTooLargeError` and its existing semantics are preserved. The error text continues to name the cap and (when known) the actual size. The agent-facing contract does not change.

---

## 2. Current status — 2026-05-09

**Phase:** v0.7.1 **OPEN — wave plan published, no code written yet.**

**HEAD (development):** `9fadbf4` (parent of upcoming Wave 0 task-file commit)

**Test count baseline (before this milestone):** Python **1231** passed + 7 skipped + 91 frontend = **1329 total. 0 failures. 0 open findings.**

### v0.7.1 deliverables — pending

- ☐ Skald — name sealed in `docs/vision/` (or in this TASK §3 if no separate vision file)
- ☐ Cartographer — `docs/cartography/DATA_FLOW.md` Leið HTTP fetch sub-section updated to show streaming flow + early-termination cut
- ☐ Architect — `INTERFACE.md` for `senses/leid/` updated; method shape decided (single `fetch_url` with internal streaming, OR a new private `_stream_into_body` helper); signature of public surface unchanged
- ☐ Forge — `client.py` `fetch_url` rewritten to use `client.stream("GET", url)` + `aiter_bytes(chunk_size=...)`; accumulator raises mid-stream
- ☐ Forge — tests added: streaming early-termination, mid-stream raise position, backpressure-safe accumulator, byte-exact boundary at the cap
- ☐ Auditor — `docs/audit/AUDIT_v0.7.1_LEID_STREAMING.md` written; verifies no regression, verifies real early termination (not just rearranged buffering), confirms invariants intact
- ☐ Scribe — `docs/DEVLOG.md` entry 15; this TASK sealed; `project_heretic_status.md` memory updated; `MEMORY.md` quick-facts line refreshed

### What v0.7.1 does NOT add

- New tools or new sense methods (the public agent-facing surface is unchanged).
- Streaming for `extract_text` directly — it routes through `fetch_url` and inherits the new behaviour automatically.
- Resumable downloads, range requests, or partial-content semantics.
- A new config flag — streaming is the only path; the buffer path is replaced, not coexisting (the v0.6.2 path was a known limitation, not a feature to preserve).

### Why "replaced, not coexisting"

The additive-only law applies to **fixes that risk losing prior work** (data, decisions, semantics). Replacing a known-limitation buffer path with the proper streaming path that satisfies the *same* contract is not subtractive — the contract is preserved, only the internal implementation moves to the correct mechanism. The N-2 audit finding explicitly authorised this in writing: *"A streaming implementation (httpx `aiter_bytes`) would be the correct fix in v0.6.2.1."* The buffer path was authored as a placeholder pending exactly this milestone. Removing the placeholder is not undoing prior craft; it is fulfilling its written intent.

---

## 3. Architectural decisions (Architect to confirm at Wave 3)

| Decision | Choice | Rationale |
|---|---|---|
| Streaming primitive | `httpx.AsyncClient.stream("GET", url)` async-context-manager + `response.aiter_bytes(chunk_size=...)` | Canonical httpx streaming idiom; closes connection on exit; naturally interruptible by `break` or `raise` mid-iteration |
| Chunk size | `65536` (64 KiB) | Standard for HTTP body streaming; balances syscall overhead with early-termination latency at small caps |
| Accumulator | `bytearray` extended per chunk | Mutable, O(1) extend; no list-of-bytes overhead; `bytes(accumulator)` only at success exit |
| Cap-exceeded behaviour | Mid-stream `raise LeidResponseTooLargeError` as soon as `len(accumulator) > max_response_bytes` | True early termination; the `async with` exit closes the connection during stack unwind |
| Cap message — known actual size? | When the chunk that pushed us over is the last one, "actual size" reads naturally; otherwise message says `"exceeds max_response_bytes={cap}; aborted at first chunk past cap"` | Honest about what the streamed code can know; no fabricated full-size number |
| Status-code check | Still happens before any body iteration | The 4xx/5xx HTTP status check uses `response.status_code` from headers — `client.stream` exposes this immediately after entering the context |
| Error-status response.text reading | Within `client.stream`, `response.text` requires a prior read; we use `await response.aread()` (bounded by a small read cap, e.g. first 500 bytes via aiter_bytes) for the truncated error message | Keeps the existing 4xx/5xx error format alive without buffering the full error body |
| Header-based pre-cap check | Optional — if `Content-Length` header is present and already exceeds `max_response_bytes`, raise immediately before any body iteration | Saves a network round of 64 KiB; cleanly handled by the same exception class |
| Existing public surface | Unchanged: `fetch_url(url) -> dict` returns the same five keys; `extract_text(url) -> dict` returns the same four keys | Agent contract preserved |

---

## 4. Streaming flow — proposed Cartographer sketch

```
agent tool_call → leid.fetch_url(url)
                   │
                   ▼
            _validate_url      ── allowlist + HTTPS-only gate
                   │
                   ▼
       async with httpx.AsyncClient(...) as client
           │
           ▼
    async with client.stream("GET", url) as response
           │
           ├── response.status_code >= 400 ──→ aread() truncated → LeidHttpError
           │
           ├── Content-Length > cap (if known) ──→ LeidResponseTooLargeError
           │
           ▼
      acc = bytearray()
      async for chunk in response.aiter_bytes(65536):
          acc.extend(chunk)
          if len(acc) > max_response_bytes:
              raise LeidResponseTooLargeError(...)   ── stream closes on unwind
           │
           ▼
      return { url, status_code, content_type, body=acc.decode(...), size_bytes=len(acc) }
```

The shape is the **same outer flow** as v0.6.2; only the body-reading interior changes. The `LeidResponseTooLargeError` raise site moves from "after full content read" to "as soon as accumulator exceeds cap." Test expectations on the raise itself remain valid because the same exception class is raised with a similar message.

---

## 5. Test plan — Forge writes; Auditor verifies

New tests in `tests/test_leid_client.py`:

| Test | Asserts |
|---|---|
| `test_fetch_url_streams_without_full_buffer` | Mock the response so `aiter_bytes` yields chunks; verify accumulator never holds more than `max_response_bytes + chunk_size` bytes at the moment of raise |
| `test_fetch_url_aborts_mid_stream_when_cap_exceeded` | Mock to yield 4 chunks of 4 KiB each with `max_response_bytes=10000`; assert raise after 3rd chunk (12 KiB > 10 KiB), not after all 4 |
| `test_fetch_url_content_length_pre_cap_header` | Mock response with `Content-Length: 99999` and `max_response_bytes=1000`; assert immediate raise without iterating chunks |
| `test_fetch_url_byte_exact_boundary` | `max_response_bytes=10`, chunks `[b"xxxxxxxxxx", b"x"]` (10 + 1); assert success on first chunk path NOT raised at the boundary, raise only after the second chunk arrives |
| `test_fetch_url_status_check_runs_before_streaming` | Mock 404 response; assert `LeidHttpError` raised without entering `aiter_bytes` loop |
| `test_fetch_url_streaming_success_under_cap` | Stream of 3 chunks totalling 5 KiB with `max_response_bytes=1_000_000`; assert success and correct `size_bytes` |

Existing tests that must continue to pass:
- `test_fetch_url_success` (basic GET)
- `test_fetch_url_not_allowed_raises` (allowlist gate)
- `test_fetch_url_timeout_raises` (timeout handling)
- `test_fetch_url_http_error_raises` (4xx)
- `test_fetch_url_response_too_large_raises` (the cap *is* still enforced)
- `test_fetch_url_connection_error_raises`
- `test_fetch_url_too_many_redirects_raises`
- All `extract_text_*` tests (route through `fetch_url`)

The existing `test_fetch_url_response_too_large_raises` test mock structure (a single response object with full `.content`) needs updating to a streaming mock. **This is mock surgery, not contract breakage**: the test still asserts the same exception class with the same key error-message substrings.

---

## 6. Mythic Engineering wave plan

### Wave 0 — TASK file open (this commit)
- Write this TASK file
- `git add`, commit with message starting `chore: open v0.7.1 ...`, push to `development`
- **No other code changes in this commit**

### Wave 1 — Skald (sole)
- Name the milestone (proposed: *Straumr í Brunni*); confirm or reframe
- Optional: short vision passage, only if it would change naming or framing

### Wave 2 — Cartographer (sole)
- Update `docs/cartography/DATA_FLOW.md` Leið subsection §4.X with the streaming flow diagram
- Note the cap-exceeded raise position shift; preserve any §16 cross-refs

### Wave 3 — Architect (sole)
- Confirm decision table in §3 above (or revise)
- Update `src/heretic/skilningr/senses/leid/INTERFACE.md` to document streaming as the canonical body-read path; remove the "v0.6.2.1+" deferred note
- Optionally: scaffold helper signatures (no logic) so Forge has a clean target

### Wave 4 — Forge (sole)
- Replace body-read interior of `fetch_url` per the streaming sketch
- Update module-level docstring (the multi-line at lines 1–37) to reflect streaming as the actual behaviour
- Update `fetch_url` docstring (lines 202–233) likewise
- Add the 6 new tests in `tests/test_leid_client.py`
- Update `test_fetch_url_response_too_large_raises` mock to streaming structure
- Run full pytest; fix any unrelated drift caught
- Confirm 1231 → 1237+ Python tests passing

### Wave 5 — Auditor (sole)
- Write `docs/audit/AUDIT_v0.7.1_LEID_STREAMING.md`
- Verify the 6 invariants from §1 of the existing v0.6.2 audit still hold
- Verify N-2 is genuinely closed: read the post-Wave-4 `client.py`, confirm no `response.content` materialisation, confirm `aiter_bytes` is the body path
- Verify regression: no other test newly fails or skips
- If any concern: open a remediation list (additive — never delete Forge's code)

### Wave 6 — Forge cleanup (only if Wave 5 raises items)
- Address each Auditor concern; never delete or rename existing tests; only add or correct

### Wave 7 — Scribe (sole)
- DEVLOG entry 15
- This TASK §2 status updated to **SHIPPED + AUDITED + CLEANED**
- `project_heretic_status.md` memory file updated
- `MEMORY.md` quick-facts line refreshed
- Final commit + push

---

## 7. Invariants to preserve (Auditor's checklist source)

From `docs/audit/AUDIT_v0.6.2_MORE_SENSES.md` and `client.py` module docstring:

1. **Allowlist gate runs BEFORE any httpx call.** `_validate_url` must remain the first action in `fetch_url`.
2. **HTTPS-only by default.** `allow_http: false` must reject `http://` URLs at the gate.
3. **GET only.** No other HTTP methods.
4. **No cookies.** `httpx.AsyncClient` cookies not configured.
5. **No JS execution.** httpx only — Playwright/selenium remain a future-version (v0.8) concern.
6. **`max_response_bytes` honoured.** Now enforced via streaming abort, not post-hoc slicing. The agent never sees partial content; only structured error.
7. **No live network calls in tests.** All httpx calls mocked.
8. **Sandbox seam routing unchanged.** All path/command/URL validation still routes through `skilningr/sandbox.py`.
9. **Privacy-first default.** Sense remains `enabled: false` by default.
10. **Sense dispatch never raises.** `LeidSense.dispatch_tool_call` continues to catch all exceptions and return structured tool_results.

---

## 8. Forbidden moves

- ☒ Do **not** add a new config flag for streaming — there is one path now.
- ☒ Do **not** silently truncate a response and return partial content. The contract is "raise or full success."
- ☒ Do **not** change the `LeidResponseTooLargeError` class shape.
- ☒ Do **not** touch the URL allowlist, HTTPS-only gate, or `_validate_url` logic.
- ☒ Do **not** introduce live network calls in tests, ever.
- ☒ Do **not** delete the v0.6.2 audit file or rewrite its history of N-2; v0.7.1's audit references and closes it.

---

## 9. Backlog forward (post-v0.7.1)

| Item | Requires | Notes |
|---|---|---|
| v0.5.3 frontend webcam sub-badge | Frontend only | Carried X-1 NIT from v0.5.2 |
| v0.5.3 privacy masks | Python + Pillow | Blur regions before frame send |
| v0.6.x.1 MCP resources | Small extension of mcp_server.py | File-resource hosting via MCP `resources/*` |
| v0.6.x Mode C Smiðja composition | No external gate | Explicit Brúarhönd+Forge orchestration |
| **v0.8 Opið Vef** | Playwright | Full browser navigation Leið — clicks, JS pages, screenshots |
| v0.9 Málari | Playwright (v0.8) | Photopea image editor sense, depends on v0.8 transport |
| v0.10 Langhúsið Ytra | OSC + MindSpark | VRChat embodiment |
| v0.11 Bréfasamtök | aiosmtplib + aioimaplib | Email sense |
| v0.4.1 first compile | MSVC Build Tools | Tauri wrap blocked on operator install |

The natural successor to v0.7.1 in the canonical roadmap is **v0.8 Opið Vef** — the full-browser Leið with Playwright, which subsumes the current httpx-only Leið and unlocks v0.9 Hönd (Photopea) downstream.

---

## 10. Session-resumption pointer

If this session is interrupted before Wave 7 closes, resume by:

1. Read this TASK file §2 for current phase
2. Read `git log --oneline -20` to identify which Wave commits exist
3. Continue from the first Wave whose commit is missing
4. The task tracker (`TaskList`) preserves wave state within the session; if rebuilt, re-create from §6

---

*Authored by Runa Gridweaver Freyjasdottir, in the autonomous Mythic Engineering mode requested by Volmarr 2026-05-09.*
*The next wave is the Skald.*
