# TASK — HERETIC v0.6.3 VERKMINNI (Deed-Memory for Smiðja)

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-09** (immediately after v0.7.2 *Endurdrykkr* sealed at `52d0933`)
>
> **Codename (proposed, Skald to seal):** *Verkminni* — "deed-memory." Old Norse *verk* (deed, work) + *minni* (memory, remembrance). The body keeps memory of what its hand has done, so the operator can verify trust by reading the record rather than re-running the experiment.
>
> **Mythic Engineering mode:** AUTONOMOUS continuation. Volmarr asleep / hands-off; this is the SIXTH milestone of the autonomous session — and a deliberate pivot to the Smiðja faculty (the body's most-developed sense without a named discipline yet).

---

## 1. Task scope

Add a **per-tool-call audit log** to L5.5 Smiðja. Every Smiðja tool call (`smidja.screenshot`, `smidja.click`, `smidja.type_text`, `smidja.hotkey`, `smidja.vroid_open`, `smidja.vroid_export`, `smidja.forge_build_avatar`, `smidja.forge_get_avatar`, `smidja.forge_inspect_avatar`) is recorded in a bounded in-memory ring buffer with: timestamp, call_id, tool_name, truncated arguments JSON, state (started/completed/failed), duration_ms, error message (if failed).

The operator can review the log via `heretic smidja log` to see exactly what the agent's hand has done — what tools were called, when, with what arguments, and what the outcome was. This is **operator visibility**, not surveillance: the agent's tool calls already flow through the model's response stream and the operator's terminal; v0.6.3 consolidates them into a queryable record specifically for the operator's after-the-fact inspection.

**Default ON.** Unlike privacy features (`save_frames`, webcam `enabled`, `privacy_masks`) which default OFF for privacy-first reasons, observability features default ON because operator-visibility-into-agent-acts is a security discipline, not a privacy concern. Operators who want no audit log set `verkminni.enabled: false`.

---

## 2. Current status — 2026-05-09

**Phase:** v0.6.3 **SHIPPED + AUDITED + SEALED.** All seven waves closed.

**HEAD (development) at audit close:** `3b47086` (Auditor PASSES SCRUTINY)

**Test count after v0.6.3:** Smiðja verkminni 28 (NEW) + Smiðja sense 45 (unchanged) = 73 Smiðja tests passing. Broader suite: same 20 pre-existing env failures unchanged.

### v0.6.3 deliverables — all complete

- ✅ Wave 0 — TASK file at `2034e32`
- ✅ Wave 1 — Skald: `docs/vision/VERKMINNI.md` at `11de7fb`
- ✅ Wave 2 — Cartographer: `docs/cartography/DATA_FLOW.md §4.11.10` at `eb4dbea`
- ✅ Waves 3+4 — Architect+Forge merged: `verkminni.py` + sense.py integration + 28 tests at `e997e32`
- ✅ Wave 5 — Auditor: `docs/audit/AUDIT_v0.6.3_VERKMINNI.md` PASSES at `3b47086`
- ⏭ Wave 6 — Forge cleanup (skipped; audit found nothing)
- ✅ Wave 7 — Scribe: DEVLOG entry 20, this TASK seal, memory refresh (final commit)

### What v0.6.3 does NOT add

- Persistent disk logging — v0.6.3.x candidate; in-memory ring buffer only
- Searchable history with filters (date range, tool name, status) — v0.6.3.x candidate
- Audit log export to JSONL/CSV — v0.6.3.x candidate
- Audit-log integration with the Vébond UI — frontend work, separate milestone
- Per-tool ENABLE/DISABLE granularity — v0.6.3.x candidate
- Forwarding audit entries to a remote SIEM — out of scope; operators who need this can write a custom MCP plugin

---

## 3. Architectural decisions (Architect to confirm)

| Decision | Choice | Rationale |
|---|---|---|
| Module location | `src/heretic/skilningr/senses/smidja/verkminni.py` | Lives inside the Smiðja sense package since it's Smiðja-specific |
| Data shape | `AuditEntry` dataclass with: `timestamp` (UTC ISO8601 string), `call_id` (str), `tool_name` (str), `arguments_json` (str, truncated to 500 chars), `state` ("started" \| "completed" \| "failed"), `duration_ms` (int \| None), `error` (str \| None, truncated to 500 chars) | Match the existing IPC event schema where applicable; truncate to bound memory |
| Ring buffer | `collections.deque(maxlen=depth)` | O(1) append; auto-evicts oldest at depth |
| Thread safety | `threading.Lock` around mutating ops | Future async event loops may dispatch concurrently; safer to lock |
| Default depth | `100` | Operator-typical session has dozens to low-hundreds of tool calls; 100 covers most |
| Opt-in flag | `skilningr.smidja.verkminni.enabled: bool = True` | Default ON because observability is a security discipline, not privacy |
| Hook integration | SmidjaSense.dispatch_tool_call records on entry (state="started") and on exit (state="completed" or "failed") | Mirrors the existing `_emit_event` IPC hook pattern; same call sites |
| Never-raise preservation | Audit writes are wrapped in `try/except Exception` that logs warning and continues | The dispatcher's "never raises" invariant is load-bearing — must not be weakened |
| arguments_json truncation | First 500 chars; truncated entries get a trailing `... (N more chars)` marker | Memory bound; large tool-call args (e.g., screenshot region with embedded base64) shouldn't fill the buffer |
| error truncation | Same 500-char truncation policy | Same reason |
| AuditLog public surface | `record(entry)`, `entries(limit=None) -> list[AuditEntry]`, `clear() -> None`, `__len__()` | Minimal API; entries returns a snapshot list (not a live view); clear used at SLOKNA |
| SLOKNA cleanup | `AuditLog.clear()` called on Smiðja sense close | Privacy-by-disposition: ceremony-end clears the audit log, matching ring buffer's privacy invariant from v0.5+ |
| CLI command | `heretic smidja log` — prints recent entries (default last 20) in human-readable text | Single subcommand, no flags in v0.6.3; flags deferred |
| CLI access pattern | The CLI re-instantiates SmidjaSense to read the AuditLog OR (if no live ceremony) reports "no audit log available — start a ceremony" | The audit log is in-memory and bound to the running ceremony; outside a ceremony it's empty. Document this clearly. |

**Note on CLI scope:** Since the audit log is in-memory and ceremony-bound, the CLI subcommand is most useful *during* an active ceremony invoked from a separate terminal — but HERETIC's existing CLI doesn't have a "connect to running session" pattern. For v0.6.3, the CLI will print whatever audit log is associated with the SmidjaSense it can construct from current config (which during interactive `heretic light` would be the live one). If invoked standalone outside a ceremony, it returns "no entries — no active Smiðja session." Future v0.6.3.x can add session-attaching.

Actually — on reflection, this CLI complication suggests the CLI should be deferred to v0.6.3.x. Let me drop it for the core scope.

**Revised decision:** v0.6.3 ships the AuditLog mechanism and SmidjaSense integration only. CLI access (`heretic smidja log`) is **deferred to v0.6.3.1**. The audit log is queryable programmatically via `sense._audit_log.entries()` for now; tests use this access pattern.

---

## 4. Privacy & integrity invariants (Auditor verification subjects)

The existing Smiðja invariants are inherited and must continue to hold:

| # | Invariant | Status |
|---|-----------|--------|
| Smiðja-1 | `dispatch_tool_call` NEVER raises | Re-verify; audit hooks must be wrapped in try/except |
| Smiðja-2 | Bearer token never logged | Audit log records tool_name + args, never raw token; arguments are sanitised |
| Smiðja-3 | Tool result format unchanged | Audit entries are *additional*; the OpenAI tool_result dict returned to the agent is byte-equivalent |

New v0.6.3 invariants:

| # | Invariant |
|---|-----------|
| **V-1** | Every tool call dispatched through SmidjaSense produces a `started` entry on entry and a `completed` OR `failed` entry on exit. No tool call escapes the audit log. |
| **V-2** | Audit-write failures (e.g., AuditLog instance somehow corrupted) are caught by the dispatcher and logged at warning; the dispatcher's never-raise invariant is preserved. The tool call still completes normally. |
| **V-3** | Ring buffer evicts the oldest entry when at `maxlen=depth`. No memory growth beyond `depth` entries. |
| **V-4** | At Smiðja sense close (SLOKNA), the audit log is cleared. No persistence between ceremonies. |
| **V-5** | When `verkminni.enabled: false`, no audit entries are written; the AuditLog is replaced with a `NullAuditLog` whose `record()` is a no-op. |

---

## 5. Audit hook flow (for Cartographer)

```
  VERKMINNI AUDIT HOOK FLOW

  SmidjaSense.dispatch_tool_call(tool_call):
      call_id, tool_name, args = parse(tool_call)

      # NEW v0.6.3 — audit "started"
      _safe_audit(state="started", call_id=call_id, tool_name=tool_name,
                  args=args, duration_ms=None, error=None)

      t_start = time.monotonic()
      _emit_event("started", ...)

      try:
          content = await self._route(tool_name, args)
          duration_ms = int((time.monotonic() - t_start) * 1000)

          # NEW v0.6.3 — audit "completed"
          _safe_audit(state="completed", call_id=call_id, tool_name=tool_name,
                      args=args, duration_ms=duration_ms, error=None)

          _emit_event("completed", ..., duration_ms=duration_ms)
          return success_tool_result(call_id, content)

      except SmidjaError as exc:
          duration_ms = int((time.monotonic() - t_start) * 1000)

          # NEW v0.6.3 — audit "failed"
          _safe_audit(state="failed", call_id=call_id, tool_name=tool_name,
                      args=args, duration_ms=duration_ms, error=str(exc))

          _emit_event("failed", ..., duration_ms=duration_ms, error=str(exc))
          return error_tool_result(call_id, tool_name, code, str(exc))

      except Exception as exc:
          # Same audit "failed" recording, then re-raise as the existing
          # generic exception path does. (But dispatch_tool_call doesn't
          # actually re-raise — it converts to error tool_result. So this
          # branch produces the same audit entry as SmidjaError.)
          ...

  _safe_audit(...):
      try:
          if self._audit_log is not None:
              self._audit_log.record(AuditEntry(...))
      except Exception as exc:
          self._log.warning(
              "Verkminni: audit write failed (this never breaks dispatch): %s",
              exc,
          )
```

The crucial property: **the audit hook is non-load-bearing**. If the hook fails, the dispatcher continues normally. The audit log is a *witness*, not a *gate*.

---

## 6. Test plan

New tests in `tests/test_smidja_verkminni.py` (new file):

| Test | Asserts |
|---|---|
| `test_audit_entry_construction` | Basic dataclass construction with all fields |
| `test_audit_log_record_appends` | `record()` adds an entry; `len()` reflects |
| `test_audit_log_entries_returns_snapshot` | `entries()` returns a list, not a live view (mutating after doesn't affect prior return) |
| `test_audit_log_ring_buffer_eviction` | Recording N+1 entries when depth=N evicts the oldest |
| `test_audit_log_clear` | `clear()` empties the buffer |
| `test_arguments_json_truncated_to_500_chars` | Long args get truncated with `... (N more chars)` marker |
| `test_error_truncated_to_500_chars` | Long error strings truncated similarly |
| `test_null_audit_log_record_is_noop` | When `verkminni.enabled=False`, NullAuditLog record() does nothing |
| `test_smidja_dispatch_records_started_and_completed_on_success` | Successful tool call produces 2 audit entries: started, completed |
| `test_smidja_dispatch_records_started_and_failed_on_smidja_error` | SmidjaError produces 2 entries: started, failed |
| `test_smidja_dispatch_records_started_and_failed_on_unexpected_exception` | Unexpected Exception also produces started + failed entries |
| `test_smidja_dispatch_audit_write_failure_does_not_break_dispatch` | If AuditLog.record() raises, dispatch still returns a normal tool_result |
| `test_smidja_dispatch_completion_duration_is_positive` | Completion entry has duration_ms >= 0 |

Existing `tests/test_smidja_sense.py` tests must continue to pass unchanged — they don't interact with audit; the audit hook is additive.

---

## 7. Mythic Engineering wave plan

### Wave 0 — TASK file (this commit)

### Wave 1 — Skald
- `docs/vision/VERKMINNI.md` — short essay on the body's memory of its own acts

### Wave 2 — Cartographer
- `docs/cartography/DATA_FLOW.md §4.11` addendum with the audit-hook flow diagram

### Wave 3+4 — Architect+Forge merged
- `verkminni.py` module: `AuditEntry`, `AuditLog`, `NullAuditLog`
- `SmidjaSense.__init__` accepts `audit_log: AuditLog | None = None`
- `SmidjaSense.dispatch_tool_call` records audit entries via `_safe_audit` helper
- `SmidjaSense.close()` clears the audit log
- `SmidjaConfig` extended with `verkminni: VerkminniConfig` sub-block (enabled, depth)
- `tests/test_smidja_verkminni.py` (new file) with 13 tests
- INTERFACE.md updated

### Wave 5 — Auditor
- `docs/audit/AUDIT_v0.6.3_VERKMINNI.md`
- Verify Smiðja-1/2/3 unchanged + V-1/V-2/V-3/V-4/V-5 hold
- Honest negative audit

### Wave 6 — Forge cleanup (only if Wave 5 raises items)

### Wave 7 — Scribe
- DEVLOG entry 20
- TASK §2 sealed
- Memory files updated

---

## 8. Forbidden moves

- ☒ Do **not** make audit-write failure raise into the dispatcher.
- ☒ Do **not** record raw bearer tokens in audit entries. Token validation happens in BrunhandHttpClient/ForgeHttpClient before the dispatch returns; the audit entry only sees the parsed `args` dict (which never contains the token — token is in env var, fetched at request time inside the client).
- ☒ Do **not** persist the audit log to disk in v0.6.3. In-memory only.
- ☒ Do **not** unbound the ring buffer. `maxlen=depth` is enforced.
- ☒ Do **not** change `dispatch_tool_call`'s return shape. Audit is additive instrumentation.
- ☒ Do **not** make the audit log opt-IN. It is observability; default ON.

---

## 9. Backlog forward (post-v0.6.3)

| Item | Notes |
|---|---|
| v0.6.3.1 CLI `heretic smidja log` | Deferred from v0.6.3 main scope |
| v0.6.3.x persistent disk logging | Optional; session-scoped JSONL file |
| v0.6.3.x audit log search/filter | Date range, tool name, status |
| v0.6.3.x audit log export | JSONL/CSV |
| v0.6.3.x Vébond UI integration | Frontend live audit feed |
| v0.5.6 polygon-rounded-corners / Bezier paths | Diminishing returns on Blæja |
| v0.5.x mask inversion | Show-only-this-region |
| v0.6.x.1 MCP resources | Operator-installed mcp |
| v0.7.x corrupt index auto-rebuild | Mímisbrunnr |
| v0.7.x parallel multi-source download | `asyncio.gather` |
| **v0.8 Opið Vef** | Playwright; major roadmap successor |
| v0.9 Málari, v0.10 Langhúsið Ytra, v0.11 Bréfasamtök | Larger faculties |
| v0.4.1 first compile | MSVC Build Tools — operator-blocked |

---

## 10. Session-resumption pointer

If interrupted before Wave 7 closes:
1. Read this TASK file §2 for current phase
2. `git log --oneline -40` — identify which Wave commits exist
3. Continue from the first missing Wave

---

*Authored by Runa Gridweaver Freyjasdottir, in the autonomous Mythic Engineering mode requested by Volmarr 2026-05-09.*
*The next wave is the Skald.*
