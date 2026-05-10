# AUDIT — HERETIC v0.6.3 *Verkminni* (Deed-Memory for Smiðja)

**Date:** 2026-05-09
**Auditor:** Sólrún Hvítmynd (The Auditor for Vibe Coding)
**Subject:** v0.6.3 — Per-tool-call audit log for L5.5 Smiðja
**Subject HEAD at audit time:** `e997e32` (Architect+Forge merged Wave close)

---

## Verdict

**PASSES SCRUTINY — 0 BLOCKERS, 0 NOTABLE FINDINGS, 0 NITS.**

The three inherited Smiðja invariants (Smiðja-1: dispatch never raises; Smiðja-2: bearer token never logged; Smiðja-3: tool_result return shape unchanged) hold under the audit-hook extension. The five new v0.6.3 invariants V-1 through V-5 are verified by direct test evidence. The `_safe_audit` wrapper structurally preserves the dispatcher's never-raise property by catching every exception from the audit-write path. The audit log is what the Skald named: a *witness*, not a *gate*. No regression in the broader suite.

---

## What I Verified (Evidence Trail)

### V-1: Every dispatched tool call produces paired (started, completed/failed) audit entries

**Claim:** When `verkminni.enabled = True`, every tool call dispatched through SmidjaSense produces exactly two audit entries with the same `call_id` — one `started` and one `completed` OR `failed`.

**Evidence:**
- `test_success_records_started_and_completed`: a successful `smidja.click` produces `len(entries) == 2`, with `entries[0].state == "started"` and `entries[1].state == "completed"`. Both share the same `call_id` (the tool_call's id field). **Test passes.**
- `test_smidja_error_records_started_and_failed`: when `bc.click` raises `BrunhandUnreachableError`, the audit log still contains 2 entries — `started` followed by `failed` with the error string. **Test passes.**
- `test_unexpected_exception_records_started_and_failed`: when `bc.click` raises generic `RuntimeError`, the audit log still contains the paired entries. The `Exception` branch (lines ~422-453 in `sense.py`) properly calls `_safe_audit(state="failed", ...)`. **Test passes.**

**Code review:** dispatch_tool_call has exactly four exit points where audit hooks fire:
- Line ~377-385: `_safe_audit(state="started", ...)` after `t_start`
- Line ~393-400: `_safe_audit(state="completed", ...)` on success
- Line ~423-430: `_safe_audit(state="failed", ...)` in `SmidjaError` handler
- Lines ~462-470 + ~487-495: `_safe_audit(state="failed", ...)` in both branches of the generic `Exception` handler (SkilningrError vs unknown)

There is no exit path that produces only a `started` entry without a paired completion. **V-1 verified.**

### V-2: Audit-write failures CANNOT make dispatch_tool_call raise (witness, not gate)

**Claim:** Smiðja-1 (dispatch never raises) is preserved structurally even when AuditLog operations fail.

**Evidence:**
- `_safe_audit` in `sense.py` (lines ~530-560) wraps the entire audit-write path in `try/except Exception`. Any exception is caught, logged at warning, and the function returns normally — propagating nothing to the caller.
- `test_audit_write_failure_does_not_break_dispatch`: replaces `AuditLog.record` with a `MagicMock(side_effect=RuntimeError("audit broken"))`, then calls `dispatch_tool_call`. The test asserts:
  1. The dispatch returns a normal `tool_result` dict (not raising).
  2. The dispatch contains `tool_call_id`, `role`, and `content` keys.
- **Test passes.** The audit failures (which fire on every audit hook in this test — twice per call) do not propagate.

**Honest negative check:** I read `_safe_audit` for any path that could let an exception escape. There is exactly one `try` and exactly one `except Exception`. The `except` body calls `self._log.warning(...)` (which itself cannot raise — Python's logging module catches its own internal exceptions by default). No path inside the function body lies outside the `try`. **V-2 verified structurally.**

### V-3: Ring buffer evicts oldest at maxlen=depth (no unbounded memory growth)

**Claim:** `AuditLog` uses `collections.deque(maxlen=depth)`; recording the (depth+1)-th entry evicts the first.

**Evidence:**
- `test_ring_buffer_evicts_oldest`: records 5 entries into an `AuditLog(depth=3)`. Asserts `len(log) == 3` after, and the retained `call_id`s are `["c2", "c3", "c4"]` — the oldest two were evicted.
- **Test passes.**
- Code review: `self._buffer = deque(maxlen=depth)` at `verkminni.py:158`. `deque.append()` semantically pops the leftmost element when the deque is full. Python stdlib guarantee. **V-3 verified.**

### V-4: SmidjaSense.close() (SLOKNA) clears the audit log

**Claim:** Ceremony-scoped privacy — the audit log does not persist across ceremonies.

**Evidence:**
- `test_close_clears_audit_log`: dispatches a tool call (producing 2 entries), asserts the log has 2 entries, then calls `await sense.close()`, asserts `len(log) == 0`.
- **Test passes.**
- Code review: `sense.py:close()` at line ~290 has a new block:
  ```python
  try:
      self._audit_log.clear()
  except Exception as exc:
      self._log.warning("Verkminni: audit clear failed at close: %s", exc)
  ```
  Wrapped in try/except so a clear failure cannot break close (defensive parallel to V-2). **V-4 verified.**

### V-5: NullAuditLog opt-out — record() is a no-op

**Claim:** When `verkminni.enabled = False` (operator opt-out), the AuditLog is replaced with a `NullAuditLog` whose `record()` does nothing; the dispatch path is unchanged.

**Evidence:**
- `test_null_audit_log_records_nothing`: passes `NullAuditLog()` as the `audit_log` parameter; dispatches a successful `smidja.click`; asserts `len(null_log) == 0` and the dispatch result is normal.
- **Test passes.**
- Code review: `NullAuditLog` in `verkminni.py` has `record()` as a `pass` body. Same public shape as `AuditLog` (`record/entries/clear/__len__`), so the dispatcher's `_safe_audit → audit_log.record(entry)` call site needs no branching. The Open/Closed Principle is honoured: enabling/disabling Verkminni doesn't change the dispatch site. **V-5 verified.**

### V-Smiðja-1: Inherited — dispatch_tool_call NEVER raises

**Claim:** The pre-existing Smiðja-1 invariant is preserved by V-2.

**Evidence:** All 45 baseline `test_smidja_sense.py` tests pass unchanged at `e997e32`. The new audit hooks added paired `_safe_audit` calls but did not modify the existing `try/except` structure that catches all dispatch exceptions and converts them to error tool_results. **Verified by regression test pass + code review.**

### V-Smiðja-2: Inherited — bearer token never logged

**Claim:** Audit entries do not record the bearer token used to authenticate to Brúarhönd.

**Evidence:**
- The bearer token is stored in an environment variable (`token_env: BRUNHAND_TOKEN_HERETIC`) and fetched by `BrunhandHttpClient.open()` at request time — it is NEVER an argument to a tool call. The `args` dict received by `dispatch_tool_call` and forwarded to `_safe_audit` contains only the agent-supplied tool arguments (e.g. `{"x": 100, "y": 200}`).
- `args_json_for_audit = json.dumps(args, default=str)` at line ~358 of `sense.py` serialises only the args dict. The token is not in scope.
- **Verified by code review.**

### V-Smiðja-3: Inherited — tool_result return shape unchanged

**Claim:** The OpenAI tool_result dict returned by `dispatch_tool_call` is byte-equivalent to the v0.6.2 / v0.6.x version.

**Evidence:**
- All `test_dispatch_*` tests in `test_smidja_sense.py` (which assert the precise `tool_call_id`, `role`, `content` shape) pass unchanged.
- Audit hooks are *additive* — they record entries via `_safe_audit` without modifying the `return` statements.
- **Verified by regression pass.**

### V-6: Truncation policy is honoured

**Claim:** `arguments_json` and `error` are each capped at 500 characters with a `... (N more chars)` marker if longer.

**Evidence:**
- `test_short_text_unchanged`: `_truncate("hello") == "hello"`.
- `test_exact_cap_unchanged`: 500-char string returns identical.
- `test_one_over_cap_gets_marker`: 501-char string gets the marker.
- `test_long_text_truncated`: 1500-char string starts with the first 500 chars and contains `(1000 more chars)`.
- `test_build_entry_truncates_args` and `test_build_entry_truncates_error`: confirm `build_entry` applies the policy to both fields.
- **All tests pass.** V-6 verified.

### V-7: AuditEntry is frozen

**Claim:** `AuditEntry` cannot be mutated after construction; the record is immutable.

**Evidence:**
- `test_frozen_dataclass`: attempting `e.timestamp = "y"` raises `FrozenInstanceError` (caught as a generic `Exception` in the test).
- Code: `@dataclass(frozen=True)` decorator at `verkminni.py:107`. **V-7 verified.**

### V-8: Threading safety

**Claim:** `AuditLog.record()` and `entries()` are safe under concurrent calls.

**Evidence:** `AuditLog` uses a `threading.Lock` around all mutation and read operations. While the test suite does not exercise concurrent mutation (HERETIC is async-single-threaded for dispatch), the lock provides a structural safety net. The `with self._lock:` block at every method ensures atomicity. **Verified by code review.**

---

## Test Suite Status (post-Wave 4 close)

### Smiðja scope (the milestone surface)

| File | Tests | Status |
|---|---|---|
| `tests/test_smidja_verkminni.py` (NEW) | 28 | 28/28 passing |
| `tests/test_smidja_sense.py` | 45 (unchanged) | 45/45 passing |
| `tests/test_smidja_*` other | unchanged | passing |

### Broader suite

The 20 pre-existing environment failures (`fastapi` / `mcp` not installed) are byte-identical in stash diff. v0.6.3 introduced **zero** new regressions. Pass-count delta `+28` reflects the 28 new Verkminni tests cleanly.

---

## Cross-Document Consistency

- **TASK_HERETIC_v0.6.3_VERKMINNI.md §3** decision table — every choice (module location, AuditEntry shape, ring buffer via `deque(maxlen=N)`, threading lock, default depth 100, opt-in flag default `True`, hook integration sites, never-raise via try/except, truncation cap 500, public surface methods, SLOKNA cleanup) matches the implementation.
- **docs/cartography/DATA_FLOW.md §4.11.10** — the audit-hook flow diagram, the AuditEntry shape table, the AuditLog ring buffer semantics, the five Verkminni invariants V-1..V-5, the three inherited Smiðja-1/2/3, the heretic.yaml config block — all match the Python code. The default-ON rationale (observability is a security discipline) matches the v0.6.3 default.
- **src/heretic/skilningr/senses/smidja/verkminni.py** module docstring — names V-1..V-5 explicitly with the same numbering and language as TASK and DATA_FLOW. **Smiðja-1 / Smiðja-2 / Smiðja-3** also named explicitly as inherited.
- **docs/vision/VERKMINNI.md §V** — the Skald's "audit hook is non-load-bearing" framing matches the V-2 verification site (`_safe_audit` wraps all writes in try/except).

No contradictions between the four written sources and the code.

---

## What I Did NOT Find (Honest Negative Audit)

- **No path that records only a started entry without a completion.** The four exit points of dispatch_tool_call all call `_safe_audit(state="completed"|"failed", ...)`.
- **No exception escape from `_safe_audit`.** The single `try` block covers the entire audit-write path; the `except Exception` catches everything including `KeyboardInterrupt`-equivalents — actually, `Exception` does NOT catch `BaseException` like KeyboardInterrupt. **This is correct behaviour:** if the user hits Ctrl+C during an audit write, that should propagate up and terminate the ceremony, not be silently swallowed. Verkminni catches *errors*, not *signals*.
- **No bearer token in audit entries.** Token lives in env var, fetched at request time inside the client. Not an argument to dispatch_tool_call.
- **No mutable default in AuditLog.** `deque(maxlen=depth)` is constructed in `__init__`, not as a class-level mutable default.
- **No subtle off-by-one in `entries(limit=N)`.** The slice `list(self._buffer)[-limit:]` returns the last N entries when N < len, or all entries when N >= len (because the early-return path at the `if` covers that case).
- **No persistence to disk in v0.6.3.** No file I/O in `verkminni.py`. In-memory only, as designed.
- **No race between record() and entries().** Both methods acquire the same `threading.Lock`. A snapshot from `entries()` is consistent.
- **No leak of args containing screenshot bytes.** The `smidja.screenshot` tool returns bytes IN ITS RESULT, not in the args. The `args` dict for screenshot is typically `{}` or contains a small region spec — small payloads. Even if an operator constructed a malicious tool call with a large `args` dict, the 500-char truncation caps the audit entry size.

---

## Findings

**0 BLOCKER. 0 SERIOUS. 0 NOTABLE. 0 NIT.**

The Auditor records no further work for v0.6.3. The Forge does not need a Wave 6 cleanup pass. The Scribe may proceed to seal.

---

*Authored by Sólrún Hvítmynd, The Auditor for Vibe Coding, 2026-05-09. The next wave is the Scribe.*
