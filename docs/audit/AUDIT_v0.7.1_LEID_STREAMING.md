# AUDIT — HERETIC v0.7.1 *Straumr á Leið* (Leið Streaming)

**Date:** 2026-05-09
**Auditor:** Sólrún Hvítmynd (The Auditor for Vibe Coding)
**Subject:** v0.7.1 — Leið streaming abort via httpx.AsyncClient.stream + aiter_bytes
**Subject HEAD at audit time:** `f3baf65` (Forge Wave 4 close)
**Closes audit-deferred finding:** N-2 from `docs/audit/AUDIT_v0.6.2_MORE_SENSES.md`

---

## Verdict

**PASSES SCRUTINY — 0 BLOCKERS, 0 NOTABLE FINDINGS, 0 NITS.**

The N-2 deferral is closed honestly and completely. The streaming pattern is real (not rearranged buffering). All ten invariants in `TASK_HERETIC_v0.7.1_LEID_STREAMING.md §7` hold under the post-Wave-4 code. No regressions in the leid suite. No new test failures in the broader suite that did not pre-exist this milestone.

---

## What I Verified (Evidence Trail)

### V-1: The full-buffer pattern is genuinely gone

**Claim:** v0.7.1 replaces `response.content` materialisation with streaming.

**Evidence:** `grep -nE "response\.content|response\.text|response\.aread"` against `src/heretic/skilningr/senses/leid/client.py` returns **zero matches**. The only body-read primitive remaining is `response.aiter_bytes(...)` at lines 306 and 324, called inside the `client.stream("GET", normalised_url)` async-context-manager. The httpx full-buffer attributes are not referenced anywhere in the file — not in source code, not in error paths, not in fallback branches.

**Status:** VERIFIED.

### V-2: The streaming abort is real (not rearranged buffering)

**Claim:** The cap raise fires inside the chunk loop and the connection closes during stack unwind.

**Evidence:** The Forge `tests/test_leid_client.py::TestLeidClientStreaming::test_aborts_mid_stream_when_cap_exceeded` is the load-bearing test for this claim. It sets `max_response_bytes=10_000` and configures the mock response with **four** 4 KiB chunks. The test instruments `aiter_bytes` to record which chunk indices are yielded. After the third chunk (12 KiB total > 10 KiB cap), the raise must fire and the fourth chunk must never be yielded. The test asserts `chunks_yielded == [0, 1, 2]` — strict on the value `[0, 1, 2]`, not a loose `<= 3`. The test passes. Streaming abort is real.

A second-line check: the raise occurs inside the inner `async with client.stream(...)` block. Python language semantics guarantee that on `raise`, the stream context's `__aexit__` runs during stack unwind. The `__aexit__` of `httpx.AsyncClient.stream` cancels the response and closes the underlying connection (this is documented httpx behaviour and verified against httpx source for the version pinned in `pyproject.toml`). No additional bytes are pulled.

**Status:** VERIFIED.

### V-3: Memory at moment of raise is bounded

**Claim:** The accumulator never exceeds `max_response_bytes + chunk_size` at the moment the raise fires.

**Evidence:** The implementation extends the bytearray, then checks. The chunk that pushes the accumulator past the cap is the last one appended. With default `_STREAM_CHUNK_SIZE = 65_536` and default `max_response_bytes = 1_048_576`, the upper bound at raise time is 1_114_112 bytes (~1.06 MiB). The implementation honours this directly by ordering: extend, then compare. The `test_byte_exact_boundary_plus_one_raises` test confirms the comparison is strictly `len(acc) > max_bytes` — not `>=` — so a body exactly at the cap succeeds and a body one byte over raises.

The Skald passage at `docs/vision/STRAUMR_A_LEID.md §III` describes this disposition; the code satisfies it.

**Status:** VERIFIED.

### V-4: Allowlist + HTTPS-only gate runs BEFORE any httpx call

**Claim (TASK §7 invariant 1):** `_validate_url` is the first action in `fetch_url`.

**Evidence:** `client.py:261` is the first line inside `fetch_url`'s body after the docstring. It calls `self._validate_url(url)`. `httpx.AsyncClient` is not opened until line 274. `client.stream("GET", ...)` is not opened until line 280. There is no early-return path or short-circuit between these. The ordering is preserved exactly as in v0.6.2.

The gate's own invariants (HTTPS-only at line 184; allowlist match via `sandbox.url_matches_allowlist` at line 191) are unchanged from v0.6.2 because `_validate_url` itself was not edited in v0.7.1. Diff confirms.

**Status:** VERIFIED.

### V-5: GET-only invariant

**Claim (TASK §7 invariant 3):** No HTTP method other than GET.

**Evidence:** `grep` for `client.stream` finds exactly one call: `client.stream("GET", normalised_url)` at line 280. No `client.post`, `client.put`, `client.delete`, `client.request` calls exist. No method-name parameterisation. The string `"GET"` is hard-coded.

**Status:** VERIFIED.

### V-6: No cookies

**Claim (TASK §7 invariant 4):** `httpx.AsyncClient` is constructed without cookie support.

**Evidence:** Lines 274–279 construct `httpx.AsyncClient(timeout=..., max_redirects=..., headers=..., follow_redirects=True)`. No `cookies=` argument. httpx's default for the `cookies` parameter is `None`, which means no persistent cookie jar. Set-Cookie response headers are not stored; subsequent requests do not send cookies. This is identical to the v0.6.2 construction.

**Status:** VERIFIED.

### V-7: No JS execution; httpx is the transport

**Claim (TASK §7 invariant 5):** No browser engine.

**Evidence:** Imports at top of `client.py` show only `httpx` for transport. No `playwright`, `selenium`, `pyppeteer` references. The `_TextExtractor` is the stdlib `html.parser.HTMLParser` subclass. JS-rendered pages still return near-empty text — this is the same documented limit as v0.6.2; v0.7.1 does not move this boundary. The deferred-note language has been correctly updated from "v0.6.2.1+" to "v0.8 Opið Vef" in module docstring.

**Status:** VERIFIED.

### V-8: max_response_bytes is honoured under the new mechanism

**Claim (TASK §7 invariant 6):** Cap enforced via streaming abort. Agent never sees partial content.

**Evidence:** Three test cases hold the line:
- `test_fetch_url_response_too_large_raises` — basic cap breach raises `LeidResponseTooLargeError`
- `test_byte_exact_boundary_succeeds_at_cap` — exactly at cap is success
- `test_byte_exact_boundary_plus_one_raises` — one byte over raises

On the success path, `fetch_url` returns the standard 5-key dict. On the failure path, the exception propagates and `LeidSense.dispatch_tool_call` (in `sense.py`, unchanged in v0.7.1) catches it and returns a structured tool_result. **No partial content is ever returned to the agent.** The error tool_result names `max_response_bytes` for operator diagnosis.

**Status:** VERIFIED.

### V-9: Test code does not make live network calls

**Claim (TASK §7 invariant 7):** All httpx calls mocked.

**Evidence:** `tests/test_leid_client.py` imports `httpx` only for exception-class symbols (`httpx.TimeoutException`, `httpx.ConnectError`, `httpx.TooManyRedirects`). No `httpx.AsyncClient(...)` construction in test code; all production AsyncClient usage is patched via `with patch("httpx.AsyncClient", return_value=outer_ctx)`. Test helpers `make_streaming_response` and `make_streaming_mock_client` produce MagicMock + AsyncMock objects only.

Search for live-call patterns in tests: `grep -n "httpx\.\(AsyncClient\|Client\|get\|post\)" tests/test_leid_client.py` returns only the symbol-import context. Confirmed clean.

**Status:** VERIFIED.

### V-10: Sandbox seam routing unchanged

**Claim (TASK §7 invariant 8):** All path/command/URL validation still routes through `skilningr/sandbox.py`.

**Evidence:** `client.py:59` imports `url_matches_allowlist` from `heretic.skilningr.sandbox`. `client.py:191` calls it from inside `_validate_url`. No alternative sandbox utility was added. No bypass path exists in `fetch_url`. The streaming change is internal to the body-read step (after the gate); it did not introduce any new surface that requires sandbox checks.

**Status:** VERIFIED.

### V-11: Privacy-first default preserved

**Claim (TASK §7 invariant 9):** Sense remains `enabled: false` by default.

**Evidence:** Not touched by v0.7.1. `SkilningrLeidConfig.enabled` default remains `False` in `config_model.py`. v0.7.1 changes are scoped to `client.py` body-read internals; config defaults were not edited. Memory inspection of `LeidSense.dispatch_tool_call` (in `sense.py`) confirms the dispatch-never-raises invariant is unchanged: any `LeidError` subclass — including `LeidResponseTooLargeError` raised from streaming — is caught by the same try/except and converted to a structured tool_result.

**Status:** VERIFIED.

### V-12: Sense dispatch never raises (still)

**Claim (TASK §7 invariant 10):** `LeidSense.dispatch_tool_call` continues to catch all exceptions.

**Evidence:** `sense.py` (in `senses/leid/`) was not edited by v0.7.1. The streaming change in `client.py` raises the same exception class `LeidResponseTooLargeError` at the same level (i.e., `LeidClient.fetch_url` propagates it; `LeidSense.dispatch_tool_call` catches it). The test file `test_leid_sense.py` was not edited by v0.7.1 and its 20 tests still pass post-Wave-4 (Forge run).

**Status:** VERIFIED.

---

## Test Suite Status (post-Wave 4)

### Leið scope (the milestone surface)

| File | Tests | Status |
|---|---|---|
| `tests/test_leid_client.py` | 30 (was 22; +8 streaming) | 30/30 passing |
| `tests/test_leid_sense.py` | 20 (unchanged) | 20/20 passing |
| **Leið total** | **50** | **50/50 passing** |

### Broader suite

A focused run on the local laptop reveals that 20 unrelated tests fail because of **missing optional environment dependencies** (`fastapi`, `mcp`, equivalent of `[serve]`/`[mcp]` extras not installed in this dev environment). Diffing the failure list against the pre-v0.7.1 stash baseline shows the lists are **byte-identical** — i.e., v0.7.1 introduced **zero new failures** in the broader suite. The 20 pre-existing failures will pass once `pip install heretic[serve,mcp]` is run; they are documented elsewhere as environment-only and out of scope for this audit.

The Auditor records this fact for the Scribe so that no future memory inflates 1231 → arbitrary numbers as if the broader suite had drifted under v0.7.1. It did not.

---

## Cross-Document Consistency

- **TASK_HERETIC_v0.7.1_LEID_STREAMING.md** §3 decision table — every choice (chunk_size 65536, bytearray accumulator, mid-stream raise, Content-Length pre-cap, status check before body) is reflected verbatim in the implementation. No silent drift between TASK and code.
- **docs/cartography/DATA_FLOW.md §4.12.2.1** — the streaming flow sketch matches the implementation step for step. The memory bound stated in the cartography (`max_response_bytes + chunk_size`) is exactly what the code achieves.
- **src/heretic/skilningr/senses/leid/INTERFACE.md** §8 (v0.7.1 Forge Implementation Contract) — the eight-step contract enumerated by the Architect is followed in `fetch_url` body order.
- **docs/vision/STRAUMR_A_LEID.md** §III — the Skald's prose ("the body raises its hand. The streaming context unwinds. The connection is closed.") is satisfied by the actual `async with` exit semantics.

No contradictions between the four written sources and the code.

---

## What I Did NOT Find (Honest Negative Audit)

To prevent the audit from being a self-congratulatory ritual, I list what I actively looked for and did not find:

- **No silent `response.content` fallback.** I grepped. Zero matches.
- **No "if streaming fails, fall back to buffer" branch.** I read the full `fetch_url` body. There is no such branch.
- **No new private state on `LeidClient`.** Only two new class constants (`_STREAM_CHUNK_SIZE`, `_ERROR_PEEK_BYTES`). Both are integers; both are immutable; neither holds a connection or a buffer.
- **No leak of internal mock state across tests.** The new test helpers construct fresh MagicMock objects per test. Pytest test isolation is preserved.
- **No new dependency.** `pyproject.toml` was not edited. httpx is the same version. No `pyproject` changes for v0.7.1.

---

## N-2 Closure Statement

`docs/audit/AUDIT_v0.6.2_MORE_SENSES.md §N-2` was opened on 2026-05-08 with severity NOTABLE. The finding's prescribed fix was: *"A streaming implementation (httpx aiter_bytes) would be the correct fix in v0.6.2.1."* (The version label slipped from "v0.6.2.1" to "v0.7.1" between authoring; the substance of the prescribed fix is unchanged.)

The fix has now been delivered. The `response.content` materialisation is gone. The `aiter_bytes` accumulator is in place. The mid-stream `LeidResponseTooLargeError` raise is verified by `test_aborts_mid_stream_when_cap_exceeded`. The Content-Length pre-cap that was *not* prescribed but that the Architect added is verified by `test_content_length_pre_cap_aborts_before_any_chunk`.

**N-2 is closed at HEAD `f3baf65`. The audit trail records both the writing of the deferral and the keeping of the promise.**

---

## Findings

**0 BLOCKER. 0 SERIOUS. 0 NOTABLE. 0 NIT.**

The Auditor records no further work for v0.7.1. The Forge does not need a Wave 6 cleanup pass. The Scribe may proceed to seal.

---

*Authored by Sólrún Hvítmynd, The Auditor for Vibe Coding, 2026-05-09. The next wave is the Scribe.*
