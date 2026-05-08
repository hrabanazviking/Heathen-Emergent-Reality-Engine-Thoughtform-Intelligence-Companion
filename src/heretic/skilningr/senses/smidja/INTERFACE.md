# Smiðja Sense Interface

**Last updated:** 2026-05-08 (v0.6.1 Forge dispatch scaffold — Rúnhild Svartdóttir)
**Scope:** L5.5 Smiðja — the workshop (`src/heretic/skilningr/senses/smidja/`)
**Owner:** Architect (Rúnhild Svartdóttir)
**Derives from:** `docs/architecture/LAYER_INTERFACES.md §L5 Skilningr`
               `docs/architecture/SENSE_CONTRACTS.md §Smiðja`
               `src/seidr_smidja/brunhand/daemon/INTERFACE.md` (Brúarhönd daemon API)
               `src/seidr_smidja/bridges/straumur/api.py` (Straumur REST API — authoritative)
**True Name:** Smiðja (L5.5) — "Forge/Workshop"; the body's hands that reach into the world.
**sense_id:** `smidja`
**SLO tier:** Cold (Brúarhönd: < 30 s p95) / Very Cold (Forge: 60–300 s per build — Blender renders)

---

## What This Sense Owns

- `SmidjaConfig` — Brúarhönd connection settings + `forge: ForgeConfig` sub-block.
- `ForgeConfig` — Straumur endpoint, optional token_env, timeout.
- `BrunhandHttpClient` — async httpx client for Brúarhönd daemon; bearer-token auth.
- `ForgeHttpClient` — async httpx client for Straumur REST bridge; optional bearer-token auth.
- `SmidjaSense` — orchestrator; holds both clients; dual-half lifecycle; routes by tool name prefix.
- `SMIDJA_TOOL_DEFINITIONS` — the locked set of 9 OpenAI tool schemas (6 Brúarhönd + 3 Forge).
- The Smiðja error hierarchy (re-exported from `heretic.skilningr.errors`).

---

## Dual-Half Architecture

The Smiðja sense has two independent halves:

| Half | Client | Daemon | Timeout | Auth |
|---|---|---|---|---|
| **Brúarhönd** (live GUI) | `BrunhandHttpClient` | Horfunarþjónn (port 8848) | 30 s default | Bearer token required |
| **Forge** (headless Blender) | `ForgeHttpClient` | Straumur REST (port 8765) | 120 s default | Optional (no auth on localhost) |

Each half opens and closes independently. If one daemon is unreachable, the other continues.
`SmidjaSense.is_available` is True if at least one half is open.
`SmidjaSense.brunhand_available` and `forge_available` report per-half state.

---

## The 6 Brúarhönd Tools (v0.6.0)

| Tool Name | Daemon Endpoint | Required Parameters | Notes |
|---|---|---|---|
| `smidja.screenshot` | `POST /v1/brunhand/screenshot` | none | `region` optional; returns PNG as base64 data URL |
| `smidja.click` | `POST /v1/brunhand/click` | `x`, `y` | optional: `button`, `clicks`, `modifiers` |
| `smidja.type_text` | `POST /v1/brunhand/type` | `text` | optional: `interval`; method name avoids Python builtin |
| `smidja.hotkey` | `POST /v1/brunhand/hotkey` | `keys` | keys is a list of PyAutoGUI key name strings |
| `smidja.vroid_open` | `POST /v1/brunhand/vroid/open_project` | `project_path` | path relative to daemon's project_root |
| `smidja.vroid_export` | `POST /v1/brunhand/vroid/export_vrm` | `output_path` | path relative to daemon's export_root |

---

## The 3 Forge Tools (v0.6.1)

Exposed only when `forge.enabled: true`. Forge implements method bodies in Wave 2.
In Wave 1 scaffold, calls return `SENSE_INTERNAL_ERROR` (NotImplementedError stub).

| Tool Name | Straumur Endpoint | Required Parameters | Notes |
|---|---|---|---|
| `smidja.forge_build_avatar` | `POST /v1/avatars` | `loom_spec` (object) | Slow — Blender render; returns session_id + vrm_path |
| `smidja.forge_get_avatar` | `GET /v1/avatars/{session_id}` | `avatar_id` (session_id string) | Returns full Annáll session record |
| `smidja.forge_inspect_avatar` | `POST /v1/inspect` | `avatar_id` (vrm_path string) | Gate compliance check; vrm_path must be within allow-listed dirs |

**IMPORTANT parameter naming:** Both `smidja.forge_get_avatar` and `smidja.forge_inspect_avatar`
expose their primary parameter as `avatar_id` in the tool schema. Internally:
- `forge_get_avatar.avatar_id` → passed as `session_id` to `ForgeHttpClient.get_avatar()`
- `forge_inspect_avatar.avatar_id` → passed as `vrm_path` to `ForgeHttpClient.inspect_avatar()`

This naming was chosen for agent UX consistency. The docstrings clarify the actual semantics.

---

## Tool Routing Rule

```
Tool action = everything after the first "." in the tool name.
  action.startswith("forge_")  →  ForgeHttpClient
  otherwise                    →  BrunhandHttpClient
```

Examples:
- `smidja.screenshot`          → BrunhandHttpClient (action = "screenshot")
- `smidja.forge_build_avatar`  → ForgeHttpClient    (action = "forge_build_avatar")

This rule is sealed. Changing it is a breaking change requiring a sense version bump.

---

## Tool Definitions Gating

`SmidjaSense.tool_definitions` returns:
- Brúarhönd tools (non-`forge_` actions) only when `SmidjaConfig.enabled` is True
- Forge tools (`forge_*` actions) only when `SmidjaConfig.forge.enabled` is True

Returning all 9 tools requires both halves enabled (Mode C).

---

## Authentication Invariants

### Brúarhönd half
1. `SmidjaConfig.token_env` stores the ENV VAR NAME, never the token itself.
2. `BrunhandHttpClient.__init__` resolves `os.environ[config.token_env]` ONCE.
3. Token is stored in `self._token` and injected as `Authorization: Bearer <token>` header.
4. Token MUST NOT appear in: repr, str, log lines, error messages, audit events.
5. `hmac.compare_digest` (constant-time) used for any local equality check.

### Forge half
1. Straumur does NOT require authentication on localhost (H-005 in api.py).
2. `ForgeConfig.token_env` is optional (default `None`).
3. When `None`, no `Authorization` header is sent.
4. When set, `ForgeHttpClient.__init__` resolves `os.environ[config.token_env]` ONCE.
5. Same redaction invariant applies: token value NEVER in logs, reprs, or error messages.

---

## Brúarhönd Request Envelope Invariant

Every POST to an authenticated Brúarhönd endpoint must include three envelope fields
(per `src/seidr_smidja/brunhand/daemon/INTERFACE.md §Shared Envelope`):

```json
{
    "request_id": "<uuid4>",
    "session_id": "<persisted per client lifetime>",
    "agent_id": "<config.host_name>"
}
```

`BrunhandHttpClient._build_envelope(primitive_params)` generates these automatically.
The agent does NOT supply them. Straumur (Forge) does NOT use a request envelope.

---

## Screenshot Format

`BrunhandHttpClient.screenshot()` returns raw PNG bytes decoded from `png_bytes_b64`.
`SmidjaSense.dispatch_tool_call()` re-encodes as a base64 data URL for the tool_result,
mirroring the format used by L3 Sjón (`FrameEncoder`).

Privacy invariant: screenshots are NOT cached or stored beyond the tool_result content.

---

## Forge Build Response Shape

`POST /v1/avatars` returns (HTTP 200 on success, HTTP 422 on failure):

```json
{
    "success": true,
    "request_id": "<uuid4>",
    "vrm_path": "<absolute path on Straumur host or null>",
    "render_paths": {"<view_name>": "<path>"},
    "compliance_passed": true | false | null,
    "session_id": "<uuid4>",
    "elapsed_seconds": 42.1,
    "errors": [{"stage": "<str>", "message": "<str>"}]
}
```

`session_id` is the Annáll session identifier — pass it to `GET /v1/avatars/{session_id}`
(via `smidja.forge_get_avatar`) to retrieve the full audit record.

---

## Capability Gating

Smiðja tools are injected into the agent's `tools` array only when:
1. The relevant half is enabled in heretic.yaml (`skilningr.smidja.enabled: true` for
   Brúarhönd; `skilningr.smidja.forge.enabled: true` for Forge)
2. `?tool_use` capability flag is True (agent supports OpenAI tool_use)
3. `SmidjaSense.is_available` is True (at least one half opened successfully)

---

## Error Model

### Brúarhönd-specific

| Condition | HTTP Status | Error Class | SENSE_CONTRACTS Code |
|---|---|---|---|
| Daemon unreachable | connection failure | `BrunhandUnreachableError` | `EXTERNAL_APP_UNAVAILABLE` |
| Request timeout | — (httpx timeout) | `BrunhandTimeoutError` | `SENSE_TIMEOUT` |
| Bearer token rejected | 401 | `BrunhandAuthError` | `PERMISSION_DENIED` |
| Concurrent session | 423 | `BrunhandSessionLockedError` | `SENSE_INTERNAL_ERROR` |

### Forge-specific

| Condition | HTTP Status | Error Class | SENSE_CONTRACTS Code |
|---|---|---|---|
| Straumur unreachable | connection failure | `ForgeUnreachableError` | `EXTERNAL_APP_UNAVAILABLE` |
| Request timeout | — (httpx timeout) | `ForgeTimeoutError` | `SENSE_TIMEOUT` |
| Invalid vrm_path / spec | 400 / 422 | `ForgeValidationError` | `INVALID_ARGUMENTS` |
| Wave 1 stub call | — | `NotImplementedError` | `SENSE_INTERNAL_ERROR` |

### Shared

| Condition | Error Class | SENSE_CONTRACTS Code |
|---|---|---|
| Half not open | `SenseUnavailableError` | `SENSE_UNAVAILABLE` |
| Unknown tool name | `ToolDispatchError` | `SENSE_INTERNAL_ERROR` |
| Invalid JSON args | `ToolDispatchError` | `INVALID_ARGUMENTS` |

All errors return a structured tool_result with error JSON — `dispatch_tool_call` NEVER raises.

---

## API Discrepancies vs TASK §4 — Brúarhönd Half

| TASK §4 (incorrect) | Actual endpoint (correct) |
|---|---|
| `POST /v1/brunhand/vroid-open` | `POST /v1/brunhand/vroid/open_project` |
| `POST /v1/brunhand/vroid-export` | `POST /v1/brunhand/vroid/export_vrm` |
| (not mentioned) screenshot returns raw bytes | screenshot returns `{"payload": {"png_bytes_b64": "..."}}` |
| (not mentioned) shared envelope required | Every POST requires `request_id`, `session_id`, `agent_id` |
| (table listed only 8 paths) | Real API has 14 endpoints (move, drag, scroll, find_window, etc.) |

## API Discrepancies vs TASK §4 — Forge (Straumur) Half

| TASK §4 (incorrect / imprecise) | Actual (from api.py — authoritative) |
|---|---|
| Health path `/health` | Actual path is `/v1/health` (lives under `/v1/`) |
| `GET /v1/avatars/{id}` returns avatar metadata | Returns full **Annáll session record** (session_id, events, summary) |
| Inspect takes `avatar_id` | Inspect takes `{"vrm_path": str, "targets": list[str] | null}` — NOT an id |
| Straumur requires bearer token | Straumur has NO auth on localhost (H-005); token_env is optional |
| Port unconfirmed | Default port confirmed as **8765** (SEIDR_STRAUMUR_PORT env or __main__ default) |

---

## Module Map

```
senses/smidja/
  __init__.py         — public re-exports: SmidjaSense, BrunhandHttpClient, ForgeHttpClient, SMIDJA_TOOL_DEFINITIONS
  INTERFACE.md        — this file
  client.py           — BrunhandHttpClient (Brúarhönd half — implemented v0.6)
  forge_client.py     — ForgeHttpClient (Forge half — Wave 2 stubs in v0.6.1)
  tools.py            — SMIDJA_TOOL_DEFINITIONS (9 schemas; locked)
  sense.py            — SmidjaSense (dual-half orchestrator)
  config_model.py     — SmidjaConfig + ForgeConfig (in heretic.skilningr.config_model)
  errors.py           — re-exports from heretic.skilningr.errors (Brúarhönd + Forge errors)
```

---

## What Callers Must Not Assume

- That `dispatch_tool_call` raises on failure — it always returns a dict.
- That the tool names will change — they are stable identifiers.
- That screenshots persist — bytes exist only for the duration of the call.
- That the daemon runs on localhost — `config.host` may be a Tailscale address.
- That `type_text` maps to an endpoint named `type_text` — it maps to `/v1/brunhand/type`.
- That Forge tools work immediately — `ForgeHttpClient` methods are Wave 2 stubs.
- That `forge_get_avatar.avatar_id` is an asset ID — it is the Annáll session_id.
- That `forge_inspect_avatar.avatar_id` is an ID — it is a server-side vrm_path.
- That Straumur requires auth — it does NOT on localhost; token is optional.

---

*Rúnhild Svartdóttir, Architect — 2026-05-08*
