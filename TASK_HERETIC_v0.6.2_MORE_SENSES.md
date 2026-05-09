# TASK — HERETIC v0.6.2 MORE SENSES

> **Operational task resumption file** — per Volmarr's session-resume protocol.

> **Started: 2026-05-08** (immediately after v0.6.1 Forge Dispatch shipped + audited + cleaned at `7e63556`)

> **Mode: extension milestone.** Three new L5 Skilningr senses on the substrate v0.6 shipped: filesystem, terminal, browser. Slim wave plan: no Skald. Privacy + sandbox are the cross-cutting invariants.

---

## 1. Task scope

The Smiðja sense (v0.6 + v0.6.1) is the workshop. v0.6.2 adds three NEW sibling senses to L5 Skilningr — each with its own tool surface, each opening alongside Smiðja but independently:

| Sense | True Name | Purpose | Tools (v0.6.2 minimum) |
|---|---|---|---|
| **Minni** | "memory" | filesystem reads/writes within a sandboxed root | `minni.read_file`, `minni.write_file`, `minni.list_directory` |
| **Skepja** | "shaping" | shell command execution within an allowlisted set | `skepja.run_command`, `skepja.get_working_directory` |
| **Leið** | "path/way" | HTTP fetch + text extraction (no headless browser yet) | `leid.fetch_url`, `leid.extract_text` |

These names are pulled from the early NAMING.md ferment (v0.0). v0.6.2 activates them as concrete senses. Skilningr now hosts FOUR senses: Smiðja (v0.6 + v0.6.1), Minni, Skepja, Leið (v0.6.2). Each opens independently per the dual-half pattern Forge established for Smiðja.

What v0.6.2 does NOT add:
- Headless browser (Leið uses httpx-only; playwright/selenium = v0.6.2.x)
- Filesystem watch / inotify (read-only point-in-time only)
- Persistent shell session (each `skepja.run_command` is a fresh subprocess)
- Network interception / proxy
- More than these three senses (per scope tightness — additional senses = v0.6.x)

---

## 2. Current status — 2026-05-08 — SHIPPED + AUDITED + CLEANED

**Phase:** v0.6.2 COMPLETE. HEAD: `6a027f3`. Python 943 passed + 7 skipped + 91 frontend = **1041 tests. 0 open findings.**

### v0.6.2 deliverables
- DONE `src/heretic/skilningr/senses/minni/` — filesystem sense complete; sandbox-validated file ops; atomic write; symlink escape blocked via Path.resolve()
- DONE `src/heretic/skilningr/senses/skepja/` — terminal sense complete; subprocess with command_allowlist; shell=False invariant; env isolation (inherit_env=False default)
- DONE `src/heretic/skilningr/senses/leid/` — HTTP fetch sense complete; URL allowlist; HTTPS-only default; stdlib html.parser; LeidResponseTooLargeError now raised (Wave 3 N-1 fix)
- DONE `src/heretic/skilningr/sandbox.py` — shared validation primitives (path/command/URL); corrected symlink docstring (S-1 Wave 3 fix)
- DONE `SkilningrConfig` extended with MinniConfig + SkepjaConfig + LeidConfig typed fields
- DONE `ToolDispatcher` registration: 4 senses register; 16 tools available when all open
- DONE CLI: all three senses init at TENGSL, each in independent try/except; disabled by default
- DONE 134 new Python tests (7 new files); 809 → 943 Python; 5 symlink tests (N-3 Wave 3 fix)
- DONE `docs/cartography/DATA_FLOW.md §4.12–§4.12.3` — four new sections + §16 rewritten as Four Senses Diagram
- DONE `heretic.example.yaml` — three new commented sense sub-blocks

### Audit arc (PASS WITH CONCERNS, 0 blockers — all findings closed)

| Finding | Severity | Resolution |
|---|---|---|
| S-1: symlink docstrings lied about mechanism | SERIOUS | CLOSED at `6a027f3` — docstrings corrected; mechanism now described accurately |
| N-1: LeidResponseTooLargeError dead code | NOTABLE | CLOSED at `6a027f3` — class now imported and raised; honest note about buffer-then-raise limitation |
| N-2: full-buffer-pre-cap | NOTABLE | DEFERRED — comment added in client.py naming N-2 and pointing to v0.6.2.1 backlog |
| N-3: no symlink test | NOTABLE | CLOSED at `6a027f3` — 5 new symlink tests; Windows-skip via pytest.mark.skipif |

### Wave plan (complete with commit hashes)

| Wave | Commit(s) | Role | Content |
|---|---|---|---|
| Task open | `bfca031` | Runa (Scribe) | Task file created |
| Wave 1 — Cartographer | `ec9c2a3` | Cartographer | DATA_FLOW.md §4.12 + sandbox invariant doc |
| Wave 1 — Architect | `b5e5ca8` | Architect | sandbox.py + 3 sense subpackages + IPC bridge |
| Wave 2 — Forge | `f235cda` | Forge | sandbox primitives + Minni client/sense/tests |
| Wave 2 — Forge | `6e594cc` | Forge | Skepja terminal sense implementation |
| Wave 2 — Forge | `88d3ab9` | Forge | Leið HTTP fetch sense implementation |
| Wave 2 — Forge | `b1be21a` | Forge | CLI TENGSL wiring for all three new senses |
| Audit | `a685b35` | Auditor | AUDIT_v0.6.2_MORE_SENSES.md — PASS WITH CONCERNS |
| Wave 3 — Forge | `6a027f3` | Forge | S-1 docstring fix + N-1 raise the dead + N-3 symlink tests |
| Scribe close | (this session) | Scribe | DEVLOG entry 12 + TASK seal + memory refresh |

---

## 3. Sandbox + privacy invariants (CRITICAL — varies per sense)

### Minni (filesystem)
- `enabled: false` default (opt-in)
- `allowed_roots: list[str]` — default `["~/heretic_workspace"]` only; agent CANNOT read/write outside these roots
- Every read_file / write_file path is resolved + verified to be within an allowed root before the operation runs
- write_file refuses to overwrite outside allowed roots even if path resolves there via symlink (no symlink-follow during validation)
- Path traversal blocked: `../`, absolute paths outside allowed roots, etc.
- File size limits: read_file max 1MB default; write_file max 1MB default
- No execute permissions touched by Minni

### Skepja (terminal)
- `enabled: false` default
- `command_allowlist: list[str]` — default `[]` (empty = nothing runs); operator must explicitly add commands
- `working_directory: str` — default `~/heretic_workspace`; commands run only there
- Every run_command call: command's first token must be in allowlist OR full command must match an allowed pattern
- Subprocess never inherits HERETIC's environment unless `inherit_env: true` (default false)
- Subprocess timeout: 60s default
- Output truncation: stdout/stderr capped at 64KB to prevent token-blowup
- No shell injection: subprocess.run with `shell=False`; commands are split via shlex.split

### Leið (HTTP fetch)
- `enabled: false` default
- `url_allowlist_patterns: list[str]` — default `[]` (nothing fetchable); operator adds patterns like `https://docs.python.org/*` or `*` for unrestricted (with explicit warning logged)
- Every fetch_url call: URL must match at least one allowlist pattern OR match wildcard
- Max response size: 1MB default; truncate beyond
- User-Agent: `HERETIC/0.6.2 (heretic-summoning-circle)`
- No cookies, no redirects beyond N=5 default, no JS execution
- HTTPS preferred; HTTP allowed but logged as warning
- Timeout: 30s default

These are cross-cutting; Architect's INTERFACE.md per sense must surface them clearly.

---

## 4. Architectural decisions

| Decision | Choice | Rationale |
|---|---|---|
| Three senses in one milestone | YES — share the Skilningr substrate; tight scope per sense | Avoid trickle-effect of singleton milestones; share infra |
| Sense layout | Each sense is its own subpackage `senses/<name>/` mirroring Smiðja's layout | Predictable; ToolDispatcher registers each independently |
| filesystem transport | LOCAL Python pathlib/io | No network; lowest risk; pure stdlib |
| terminal transport | LOCAL subprocess.run (shell=False) | Stdlib; explicit command allowlist; no shell injection |
| HTTP fetch transport | LOCAL httpx (already a dep) | Reuse; URL allowlist gates outbound traffic |
| Default disabled | All three senses default `enabled: false` | Privacy-first; explicit opt-in per sense |
| Shared sandbox primitives | `_path_within_allowed_roots()` helper in `skilningr/sandbox.py` | Reuse across senses; one implementation |
| Tool naming | `minni.<action>`, `skepja.<action>`, `leid.<action>` | Two-part per A-2 sealed convention |
| Failure mode | Sandbox violation → ToolDispatchError with explanatory tool_result; never raise to CLI | Per RULES.AI fault tolerance |
| Skald essay | NO — extension milestone; the body's senses already named in vision cycle | Three new senses don't change the philosophical frame |

---

## 5. Roadmap slot

> **v0.6.2 — More Senses** — filesystem + terminal + browser substrate — L5 Skilningr extension — 2 wk

### v0.6.2 exit criteria
- 4 senses (Smiðja, Minni, Skepja, Leið) registered with ToolDispatcher when enabled
- ~10 new tools available to the agent (3 minni + 2 skepja + 2 leið + Smiðja's existing 9)
- Each sense opens independently; failure of one does not affect others
- Sandbox invariants honored under test (path traversal blocked, command allowlist enforced, URL allowlist enforced)
- Configurable via `heretic.yaml` `skilningr.minni.*` / `skepja.*` / `leid.*` keys
- Test count ≥854 Python; total ≥945
- Audit verdict PASS or PASS WITH CONCERNS, no blockers

---

## 6. Mythic Engineering wave plan (slim)

### Wave 1 — parallel
- **Cartographer**: extend `docs/cartography/DATA_FLOW.md §4.12` with three new sub-sections (§4.12 Minni filesystem flow, §4.12.1 Skepja terminal flow, §4.12.2 Leið HTTP fetch flow); update §16 component diagram with three new sense modules; document each sense's failure modes (path traversal, command not allowed, URL not allowed, timeout, oversize response, etc.)
- **Architect**: scaffold the three senses; create `skilningr/sandbox.py` (shared path/command/URL validation primitives); update SkilningrConfig with three new sub-blocks; update SENSE_CONTRACTS.md if needed; update IPC_PROTOCOL.md naming bridge with new sense names; SMIDJA_TOOL_DEFINITIONS gets 7 sibling tool def lists in their own files; update INTERFACE.md per sense; placeholder tests

### Wave 2
- **Forge**: implement minni/client.py (sandbox-validated file ops), skepja/client.py (subprocess wrapper with allowlist enforcement + timeout + output cap), leid/client.py (httpx GET with URL allowlist + size cap + redirect limit); each sense.py orchestrator routes its tools; ToolDispatcher.register_sense for each in CLI init; full tests including sandbox-violation paths
- **Auditor**: AUDIT_v0.6.2_MORE_SENSES.md; verify ALL sandbox invariants tested under malicious input (path traversal, allowlist bypass, oversize, timeout); verify each sense degrades independently; verify defaults are safe (all disabled by default)

### Wave 3 — cleanup if needed

### Close-out
- **Scribe**: DEVLOG entry 12 + TASK update + memory refresh

---

## 7. Files to be created/extended

```
src/heretic/skilningr/
  sandbox.py            NEW — shared validation primitives (path/command/URL)
  config_model.py       extend — MinniConfig + SkepjaConfig + LeidConfig + SkilningrConfig.minni/skepja/leid fields
  errors.py             extend — sense-specific errors (FilesystemError, SandboxViolation, CommandNotAllowed, UrlNotAllowed, etc.)
  senses/
    minni/
      __init__.py
      INTERFACE.md
      config_model.py
      errors.py
      client.py         filesystem ops with sandbox validation
      tools.py          3 tool definitions
      sense.py          MinniSense orchestrator
    skepja/
      (same layout)
    leid/
      (same layout)
tests/
  test_sandbox.py       NEW — shared primitive tests
  test_minni_client.py  NEW
  test_minni_sense.py   NEW
  test_skepja_client.py NEW
  test_skepja_sense.py  NEW
  test_leid_client.py   NEW
  test_leid_sense.py    NEW
  test_skilningr_dispatcher.py extend — multi-sense routing tests
heretic.example.yaml    extend — three new commented sub-blocks
docs/cartography/DATA_FLOW.md extend — §4.12 (three new sub-sections)
docs/architecture/IPC_PROTOCOL.md extend — naming bridge new entries
```

---

## 8. Operational rules (carried)

- Privacy-first: all three senses default disabled
- Sandbox invariants verified by tests under malicious input
- No emoji
- Type hints; PEP 8
- Bearer token from env var (where applicable; n/a for these three since no remote service)
- Cross-platform (especially terminal — Windows cmd vs Unix shell semantics differ)

---

## 9. Backlog forward
- v0.5.3 frontend Sjón webcam sub-badge (carry from v0.5.2)
- v0.5.x periodic webcam, multi-camera, privacy masks
- v0.6.2.1 Leið streaming via aiter_bytes: early termination at size cap,
  replacing v0.6.2's full-buffer-then-check pattern; avoids materialising
  oversized bodies in memory; adds true "connection closed early" behaviour
  that the LeidResponseTooLargeError docstring anticipates.
- v0.6.2.1 headless browser (Leið via playwright)
- v0.6.x native MCP server hosting (instead of OpenAI tool_use)
- v0.7 Mímisbrunnr starter pack — NEXT after v0.6.2
- v0.4.1 first compile (awaits operator linker install)

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-08.*
*v0.6.2 — when the workshop's neighbors open: the library, the kitchen, and the road.*
