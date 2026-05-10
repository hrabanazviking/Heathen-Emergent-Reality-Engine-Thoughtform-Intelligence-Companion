# TASK — HERETIC v0.6.3.1 Persistent Verkminni

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-09** (immediately after v0.7.3 sealed at `4a6e578`)
>
> **Codename:** none. v0.6.3.1 extends v0.6.3 *Verkminni* — same discipline (the body's deed-memory), now optionally persisted to disk at operator's explicit choice. Brief Skald wave only (addendum to VERKMINNI.md).
>
> **Mythic Engineering mode:** AUTONOMOUS continuation. EIGHTH milestone of the session — deliberately tight scope.

---

## 1. Task scope

Add an **opt-in persistent disk log** to v0.6.3 *Verkminni*. When the operator sets `skilningr.smidja.verkminni.persistent_log_path` to a writable path, every `AuditEntry` recorded by `AuditLog.record()` is **also** appended as a JSON line to that file.

**Default OFF.** Disk writes cross a real privacy threshold (the in-memory ring buffer is cleared at SLOKNA — V-4 in v0.6.3 — but a disk file persists indefinitely until the operator deletes it). Operators who want persistent audit records explicitly opt in by configuring a path. Operators who don't pay nothing — the in-memory ring buffer behaviour is byte-equivalent to v0.6.3 when no path is configured.

The disk-write path is **best-effort** and **non-load-bearing**: any I/O exception during the file write is caught, logged at warning, and the in-memory record proceeds normally. The audit log is a *witness, not a gate* — V-2 from v0.6.3 is preserved through the disk extension.

---

## 2. Current status — 2026-05-09

**Phase:** v0.6.3.1 **SHIPPED + AUDITED + SEALED.** All seven waves closed.

**HEAD (development) at audit close:** `236f569` (Auditor PASSES SCRUTINY)

**Test count after v0.6.3.1:** Smiðja verkminni 28 → 37 (+9). Smiðja total 82.

### v0.6.3.1 deliverables — all complete

- ✅ Wave 0 — TASK file at `e11dddf`
- ✅ Wave 1 — Skald (brief): `docs/vision/VERKMINNI.md §VIII` addendum at `c8be0e5`. No new codename.
- ✅ Wave 2 — Cartographer: `docs/cartography/DATA_FLOW.md §4.11.10.1` at `64ce538`
- ✅ Waves 3+4 — Architect+Forge merged: `AuditLog.disk_log_path` + 9 tests at `a8e6256`
- ✅ Wave 5 — Auditor: `docs/audit/AUDIT_v0.6.3.1_PERSISTENT_VERKMINNI.md` PASSES at `236f569`
- ⏭ Wave 6 — Forge cleanup (skipped; audit found nothing)
- ✅ Wave 7 — Scribe: DEVLOG entry 22, this TASK seal, memory refresh (final commit)

### What v0.6.3.1 does NOT add

- File rotation / size cap — out of scope; operator manages
- File compression — out of scope
- CLI command to read/query the file — v0.6.3.2 candidate
- Integration with Vébond UI — separate frontend milestone
- Forwarding entries to remote SIEM/syslog — out of scope
- Encrypted at rest — out of scope; operator's filesystem-level concern

---

## 3. Architectural decisions

| Decision | Choice | Rationale |
|---|---|---|
| Opt-in flag | `disk_log_path: Path \| None = None` parameter on `AuditLog.__init__` | Path-as-toggle (mirrors v0.5.3 `privacy_masks: list[]` pattern — emptiness IS the off-switch) |
| File format | JSONL — one JSON-encoded `AuditEntry` per line | Standard, parseable, append-friendly, no special tooling |
| Append semantics | Open in append mode (`"a"`) at every `record()` call | Survives crashes; no held file handle (better resilience than long-open) |
| Write failure handling | `try/except Exception` around the file write; log warning; proceed normally | V-2 witness-not-gate; matches v0.6.3 dispatch never-raise |
| Directory creation | `disk_log_path.parent.mkdir(parents=True, exist_ok=True)` on first write | Operator may configure a path whose parent doesn't exist yet |
| File line format | `json.dumps({timestamp, call_id, tool_name, arguments_json, state, duration_ms, error}) + "\n"` | Same shape as `AuditEntry` dataclass fields; truncation already applied by build_entry |
| Concurrency | Same `threading.Lock` that protects the in-memory deque | Disk write happens inside the lock to keep entry ordering consistent |
| Default | None / OFF | Privacy-first; operator opts in by configuring a path |
| Existing AuditLog state | When disk_log_path is None, behaviour is byte-equivalent to v0.6.3 | Backward compatibility preserved |

---

## 4. Privacy & integrity invariants (Auditor verification subjects)

The five v0.6.3 Verkminni invariants are inherited and must continue to hold:

| # | Inherited Invariant | v0.6.3.1 verification |
|---|---|---|
| V-1 | Every dispatched tool call produces paired (started, completed/failed) entries | Re-verify; disk write happens after in-memory record, doesn't change pairing |
| V-2 | Audit-write failures cannot make dispatch raise | EXTENDED: disk-write failures also cannot make dispatch raise |
| V-3 | Ring buffer evicts oldest at maxlen | Unchanged; in-memory buffer behaviour identical |
| V-4 | SLOKNA clears the in-memory log | Unchanged; the disk file is NOT cleared (operator's persistent record) |
| V-5 | NullAuditLog opt-out works | Unchanged; NullAuditLog never writes anywhere |
| Smiðja-1/2/3 | Inherited | Unchanged |

New v0.6.3.1 invariants:

| # | Invariant |
|---|-----------|
| **D-1** | When `disk_log_path is None`, behaviour is byte-equivalent to v0.6.3. No file is created; no disk I/O occurs. |
| **D-2** | When `disk_log_path` is set, every successful `record()` call results in exactly one new JSONL line in the file. The line is the JSON serialisation of the AuditEntry. |
| **D-3** | Disk write failures (OSError, PermissionError, file-system-full, parent directory missing after mkdir attempt) are caught and logged at warning. The in-memory record completes normally. The dispatch never raises. |
| **D-4** | The disk file is APPENDED to, not overwritten. Recording 100 entries with a fresh AuditLog and a pre-existing file produces a file with `pre_existing_lines + 100` lines. |
| **D-5** | The disk file is NOT cleared at SLOKNA. The persistent record outlives the ceremony — that's the point. |

---

## 5. Test plan

New tests in `tests/test_smidja_verkminni.py` (extension):

| Test | Asserts |
|---|---|
| `test_audit_log_default_no_disk_path` | `AuditLog()` (no disk_log_path) produces no file (D-1) |
| `test_audit_log_with_disk_path_appends_jsonl` | After 3 records, file has 3 JSONL lines parseable as JSON |
| `test_audit_log_with_disk_path_creates_parent_dir` | Path with non-existent parent → mkdir succeeds, file written |
| `test_audit_log_with_disk_path_appends_to_existing_file` | Pre-existing file with N lines + 5 new records → N+5 lines |
| `test_audit_log_disk_write_failure_does_not_raise` | Path is read-only → record() does not raise; warning logged |
| `test_audit_log_disk_write_failure_preserves_in_memory` | Path is read-only → in-memory entry still recorded normally |
| `test_audit_log_jsonl_format_matches_entry_fields` | Parsed JSONL line has all AuditEntry fields with correct types |
| `test_disk_path_not_cleared_at_slokna` | `SmidjaSense.close()` clears in-memory but NOT disk file (D-5) |
| `test_smidja_sense_passes_disk_path_to_audit_log` | Config `verkminni.persistent_log_path` is forwarded |

Existing 28 v0.6.3 verkminni tests + 45 smidja_sense tests must continue to pass unchanged — they don't pass a disk_log_path.

---

## 6. Mythic Engineering wave plan

### Wave 0 — TASK file (this commit)

### Wave 1 — Skald (brief)
- `docs/vision/VERKMINNI.md` §VIII addendum on operator-chosen persistence

### Wave 2 — Cartographer
- `docs/cartography/DATA_FLOW.md §4.11.10` addendum: disk-mirror best-effort write

### Wave 3+4 — Architect+Forge merged
- `AuditLog` accepts `disk_log_path` parameter
- `record()` appends JSONL line if path set; wraps in try/except (D-3)
- `SmidjaSense.__init__` reads `config.verkminni.persistent_log_path` (if SmidjaConfig is updated; otherwise just plumb through audit_log)
- 9 new tests
- INTERFACE.md update

### Wave 5 — Auditor
- `docs/audit/AUDIT_v0.6.3.1_PERSISTENT_VERKMINNI.md`
- Verify D-1..D-5 + V-1..V-5 inheritance
- Honest negative audit

### Wave 6 — Forge cleanup (only if Wave 5 raises items)

### Wave 7 — Scribe
- DEVLOG entry 22
- TASK seal
- Memory refresh

---

## 7. Forbidden moves

- ☒ Do **not** clear the disk file at SLOKNA. The point is persistence.
- ☒ Do **not** make disk-write failure raise into the dispatcher.
- ☒ Do **not** open a long-lived file handle. Open-append-close per record() — survives crashes better.
- ☒ Do **not** default disk_log_path to a sensible path. Explicit None means OFF; operator opts in.
- ☒ Do **not** introduce a new dependency.

---

## 8. Backlog forward (post-v0.6.3.1)

| Item | Notes |
|---|---|
| v0.6.3.2 CLI `heretic smidja log` | Reads the disk file from v0.6.3.1 |
| v0.6.3.x file rotation / size cap | Disk hygiene |
| v0.6.3.x JSON schema versioning | Future-proofing |
| v0.7.x parallel multi-source download | asyncio.gather over Endurdrykkr |
| **v0.8 Opið Vef** | Major roadmap successor |

---

*Authored by Runa Gridweaver Freyjasdottir, autonomous Mythic Engineering 2026-05-09. Next wave: Skald (brief).*
