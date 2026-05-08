# Smiðja Sense Interface

**Last updated:** 2026-05-08 (v0.6 scaffold — Rúnhild Svartdóttir)
**Scope:** L5.5 Smiðja — the first hand (`src/heretic/skilningr/senses/smidja/`)
**Owner:** Architect (Rúnhild Svartdóttir)
**Derives from:** `docs/architecture/LAYER_INTERFACES.md §L5 Skilningr`
               `docs/architecture/SENSE_CONTRACTS.md §Smiðja`
               `src/seidr_smidja/brunhand/daemon/INTERFACE.md` (Brúarhönd daemon API)
**True Name:** Smiðja (L5.5) — "Forge"; the body's hand that reaches into the world.
**sense_id:** `smidja`
**SLO tier:** Cold — tool calls involve a round-trip to the Brúarhönd daemon; < 30 s p95.

---

## What This Sense Owns

- `SmidjaConfig` — connection settings for the Brúarhönd daemon host.
- `BrunhandHttpClient` — async httpx client; owns the bearer-token session and all HTTP calls.
- `SmidjaSense` — orchestrator; registered in ToolDispatcher under prefix "smidja".
- `SMIDJA_TOOL_DEFINITIONS` — the locked set of 6 OpenAI tool schemas for this sense.
- The Smiðja error hierarchy (re-exported from `heretic.skilningr.errors`).

---

## The 6 Tools (v0.6.0)

Tool transport: OpenAI tool_use format (not MCP stdio). Per TASK §3 architectural decision.
Tool names follow the two-part `smidja.<action>` format per SENSE_CONTRACTS.md §2.

| Tool Name | Daemon Endpoint | Required Parameters | Notes |
|---|---|---|---|
| `smidja.screenshot` | `POST /v1/brunhand/screenshot` | none | `region` is optional; returns PNG as base64 data URL |
| `smidja.click` | `POST /v1/brunhand/click` | `x`, `y` | optional: `button`, `clicks`, `modifiers` |
| `smidja.type_text` | `POST /v1/brunhand/type` | `text` | optional: `interval`; method name avoids Python builtin |
| `smidja.hotkey` | `POST /v1/brunhand/hotkey` | `keys` | keys is a list of PyAutoGUI key name strings |
| `smidja.vroid_open` | `POST /v1/brunhand/vroid/open_project` | `project_path` | path relative to daemon's project_root |
| `smidja.vroid_export` | `POST /v1/brunhand/vroid/export_vrm` | `output_path` | path relative to daemon's export_root |

**Names are stable identifiers.** Renaming any tool name is a breaking change requiring
a sense version bump (per SENSE_CONTRACTS.md §2, rule 4).

---

## Authentication Invariant

1. `SmidjaConfig.token_env` stores the ENV VAR NAME, never the token itself.
2. `BrunhandHttpClient.__init__` resolves `os.environ[config.token_env]` ONCE.
3. The token is stored in `self._token` and injected as `Authorization: Bearer <token>` header.
4. The token MUST NOT appear in: repr, str, log lines, error messages, audit events.
   Log lines that reference the auth header use `[REDACTED]`.
5. `hmac.compare_digest` (constant-time) is used for any local equality check.
   httpx constructs the header value directly; HERETIC does not write it manually.

---

## Request Envelope Invariant

Every POST to an authenticated daemon endpoint must include three envelope fields
(per `src/seidr_smidja/brunhand/daemon/INTERFACE.md §Shared Envelope`):

```json
{
    "request_id": "<uuid4>",
    "session_id": "<persisted per client lifetime>",
    "agent_id": "<config.host_name>"
}
```

`BrunhandHttpClient._build_envelope(primitive_params)` generates these automatically.
The agent does NOT supply them in its tool call arguments.

---

## Screenshot Format

`BrunhandHttpClient.screenshot()` returns raw PNG bytes (decoded from the daemon's
`png_bytes_b64` base64 JSON field). `SmidjaSense.dispatch_tool_call()` re-encodes
these bytes as a base64 data URL for the tool_result content, mirroring the format
used by L3 Sjón (`FrameEncoder`). This ensures the agent receives images consistently
from both vision channels.

Privacy invariant: screenshots are NOT cached or stored beyond the tool_result content.
The in-memory bytes exist only for the duration of the dispatch call.

---

## Capability Gating

Smiðja tools are injected into the agent's `tools` array only when:
1. `skilningr.smidja.enabled: true` in heretic.yaml
2. `?tool_use` capability flag is True (agent supports OpenAI tool_use)
3. `SmidjaSense.is_available` is True (client opened successfully)

The CLI turn loop checks these at TENGSL before calling `ToolDispatcher.all_tool_definitions()`.

---

## Error Model (Smiðja-specific)

| Condition | HTTP Status | Error Class | SENSE_CONTRACTS Code |
|---|---|---|---|
| Daemon unreachable | connection failure | `BrunhandUnreachableError` | `EXTERNAL_APP_UNAVAILABLE` |
| Request timeout | — (httpx timeout) | `BrunhandTimeoutError` | `SENSE_TIMEOUT` |
| Bearer token rejected | 401 | `BrunhandAuthError` | `PERMISSION_DENIED` |
| Concurrent session | 423 | `BrunhandSessionLockedError` | `SENSE_INTERNAL_ERROR` |
| VRoid not running | 200 success=false | (checked in payload) | `EXTERNAL_APP_UNAVAILABLE` |
| Sense not open | — | `SenseUnavailableError` | `SENSE_UNAVAILABLE` |

All errors return a structured tool_result with error JSON (never a raised exception to Bifröst).

---

## API Discrepancies vs TASK §4

TASK §4 contained an incomplete/partially incorrect Brúarhönd endpoint table.
The following discrepancies are documented here as the authoritative correction.
The code uses the ACTUAL API from `src/seidr_smidja/brunhand/daemon/INTERFACE.md`.

| TASK §4 (incorrect) | Actual endpoint (correct) |
|---|---|
| `POST /v1/brunhand/vroid-open` | `POST /v1/brunhand/vroid/open_project` |
| `POST /v1/brunhand/vroid-export` | `POST /v1/brunhand/vroid/export_vrm` |
| (not mentioned) screenshot returns raw bytes | screenshot returns `{"payload": {"png_bytes_b64": "..."}}` |
| (not mentioned) shared envelope required | Every POST requires `request_id`, `session_id`, `agent_id` |
| (table listed only 8 paths) | Real API has 14 endpoints (move, drag, scroll, find_window, wait_for_window, vroid/save_project also exist) |

v0.6.1+ candidates from the real API surface not in v0.6.0 scope:
- `smidja.find_window` → `POST /v1/brunhand/find_window`
- `smidja.wait_for_window` → `POST /v1/brunhand/wait_for_window`
- `smidja.save_project` → `POST /v1/brunhand/vroid/save_project`
- `smidja.move` → `POST /v1/brunhand/move`
- `smidja.drag` → `POST /v1/brunhand/drag`
- `smidja.scroll` → `POST /v1/brunhand/scroll`

---

## Module Map

```
senses/smidja/
  __init__.py    — public re-exports: SmidjaSense, BrunhandHttpClient, SMIDJA_TOOL_DEFINITIONS
  INTERFACE.md   — this file
  client.py      — BrunhandHttpClient (Forge Wave 2 implements bodies)
  tools.py       — SMIDJA_TOOL_DEFINITIONS (6 schemas; locked; tests run immediately)
  sense.py       — SmidjaSense (Forge Wave 2 implements bodies)
  errors.py      — re-exports from heretic.skilningr.errors
```

---

## What Callers Must Not Assume

- That `dispatch_tool_call` raises on failure — it always returns a dict.
- That the tool names will change — they are stable identifiers.
- That screenshots persist — bytes exist only for the duration of the call.
- That the daemon runs on localhost — `config.host` may be a Tailscale address.
- That `type_text` maps to an endpoint named `type_text` — it maps to `/v1/brunhand/type`.

---

*Rúnhild Svartdóttir, Architect — 2026-05-08*
