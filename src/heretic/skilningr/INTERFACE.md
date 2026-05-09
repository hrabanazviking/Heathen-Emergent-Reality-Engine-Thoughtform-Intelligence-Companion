# Skilningr Module Interface

**Last updated:** 2026-05-08 (v0.6 scaffold — Rúnhild Svartdóttir)
**Scope:** L5 Skilningr — the sense hub layer Python module (`src/heretic/skilningr/`)
**Owner:** Architect (Rúnhild Svartdóttir)
**Derives from:** `docs/architecture/LAYER_INTERFACES.md §L5 Skilningr`
**Legend:** Owns = authoritative data owner; Never-controls = hard boundary.
**SLO tier:** Warm — tool call dispatch < 100 ms overhead (most time is in the sense subprocess or HTTP round-trip).

---

## What Skilningr Owns

- `SkilningrConfig`, `SmidjaConfig` — the canonical typed config structs.
  Authoritative definitions in `config_model.py`; `heretic.grunnr.config.HereticConfig.skilningr`
  imports from here (Approach B — mirror of rodd, sjon, vebond consolidation pattern).
- `ToolDispatcher` — routes OpenAI-format tool_call dicts to registered senses by prefix.
- `SkilningrError` and all error subclasses — the complete Skilningr error hierarchy.
- The sense subpackage namespace under `senses/`.

In v0.6.0 one sense is live: Smiðja (`senses/smidja/`). Future senses add subpackages here.

---

## What Skilningr Exposes (Public API)

All of the following are re-exported from `heretic.skilningr` directly.

| Export | Module | Purpose |
|---|---|---|
| `SkilningrConfig` | `config_model` | Root config: smidja + future sense sub-configs. |
| `SmidjaConfig` | `config_model` | Smiðja/Brúarhönd connection settings. Canonical definition. |
| `ToolDispatcher` | `dispatcher` | Routes tool_calls to registered senses. |
| `SmidjaSense` | `senses/smidja` | L5.5 Brúarhönd remote-control sense orchestrator. |
| `BrunhandHttpClient` | `senses/smidja` | Async HTTP client for the Horfunarþjónn daemon. |
| `SMIDJA_TOOL_DEFINITIONS` | `senses/smidja` | 6 OpenAI tool schemas for Brúarhönd v0.1. |
| `SkilningrError` | `errors` | Root error. Catch this for any Skilningr failure. |
| `SenseUnavailableError` | `errors` | Sense is disabled or client is down. |
| `ToolDispatchError` | `errors` | Tool call could not be routed (unknown name, malformed args). |
| `AuthError` | `errors` | Skilningr-level auth error (generic). |
| `SmidjaError` | `errors` | Root for all Smiðja/Brúarhönd errors. |
| `BrunhandUnreachableError` | `errors` | Daemon host not reachable. |
| `BrunhandTimeoutError` | `errors` | Request to daemon timed out. |
| `BrunhandAuthError` | `errors` | Bearer token rejected (HTTP 401). |
| `BrunhandSessionLockedError` | `errors` | Daemon busy with another session (HTTP 423). |

---

## What Skilningr Must Never Control

- Agent conversation content or message history — L1 Bifröst's domain.
- When tool schemas are injected into agent messages — the CLI turn loop decides (at TENGSL).
- Config file loading — Skilningr receives a typed `SkilningrConfig`; it never reads heretic.yaml.
- UI rendering or status event display — L4 Vébond. Skilningr emits `SenseToolCall` IPC events
  via EventBus; Vébond consumes them. Skilningr does not write to the WebSocket directly.
- Sense implementations — what a sense actually does is the sense's responsibility.
- Screenshot caching beyond the in-memory tool_result — no persistent frame storage.

---

## Inputs

| Input | Source | Notes |
|---|---|---|
| `SkilningrConfig` | L0 Grunnr `load_config()` | Resolved at Kynding; passed to ToolDispatcher and senses. |
| `tool_call` dict (OpenAI format) | L1 Bifröst / CLI | Routed through ToolDispatcher.dispatch(). |
| `enabled` flag per sense | `SkilningrConfig` | Determines which senses are active at TENGSL. |

---

## Outputs

| Output | Target | Notes |
|---|---|---|
| `tool_result` dict (OpenAI format) | L1 Bifröst / CLI | `{"tool_call_id": ..., "role": "tool", "content": "<json>"}` |
| `SenseToolCall` IPC event | L4 Vébond via EventBus | Emitted at STARTED / COMPLETED / FAILED per tool call. |
| Tool schema list | L1 Bifröst via CLI | `ToolDispatcher.all_tool_definitions()` called at TENGSL. |

---

## Tool Dispatch Lifecycle

```
CLI / Bifröst turn loop
        |
        | tool_call dict (from agent streaming response)
        v
 ToolDispatcher.dispatch()
        |
        | prefix = tool_name.split('.')[0]  # e.g. "smidja"
        | sense = self._senses[prefix]
        v
 SmidjaSense.dispatch_tool_call()
        |
        | emit SenseToolCall(state=STARTED)
        | route by tool_name to BrunhandHttpClient method
        v
 BrunhandHttpClient.<method>()
        |
        | POST /v1/brunhand/<endpoint>  (Bearer auth)
        v
 Brúarhönd daemon (Horfunarþjónn)
        |
        | response (200 JSON or error envelope)
        v
 BrunhandHttpClient — decode response
        |
        v
 SmidjaSense — encode result as tool_result content
        | emit SenseToolCall(state=COMPLETED or FAILED)
        v
 ToolDispatcher — return tool_result dict
        |
        v
 CLI / Bifröst — append tool_result to messages array
        | if agent has more tool_calls: loop
        | else: agent generates final text response
```

---

## Tool Naming Contract

All tool names follow the two-part format: `<sense_id>.<action_name>`
No `sense.` prefix. See `docs/architecture/SENSE_CONTRACTS.md §2` for the full
canonical spec (sealed at v0.0 audit A-2).

Smiðja tool names locked at v0.6.0:
- `smidja.screenshot`
- `smidja.click`
- `smidja.type_text`
- `smidja.hotkey`
- `smidja.vroid_open`
- `smidja.vroid_export`

---

## Auth Invariant (DO NOT BREAK)

`SmidjaConfig.token_env` holds an environment variable NAME, never the token value.
`BrunhandHttpClient.__init__` resolves the token from `os.environ[config.token_env]` ONCE.
The token is never logged, repr'd, serialised to disk, or echoed in any response.
Any log line that references the auth header uses `[REDACTED]`.

---

## Capability Gating

Smiðja tools are only injected into the agent's `tools` array when ALL of the following are true:
1. `skilningr.smidja.enabled: true` in heretic.yaml
2. The agent's capability probe returned `?tool_use = true` (per `AGENT_AGNOSTIC_PROTOCOL.md`)
3. `SmidjaSense.is_available` is True (client session opened successfully at TENGSL)

If any condition is False, the Smiðja tools are silently excluded from the tools array.
The agent receives no error — it simply does not know the tools exist.

---

## Error Model

All errors are caught at the `ToolDispatcher.dispatch()` boundary and translated into
tool_result dicts with structured error JSON. No exception escapes to L1 Bifröst.

| Error class | SENSE_CONTRACTS code | When |
|---|---|---|
| `SenseUnavailableError` | `SENSE_UNAVAILABLE` | Sense disabled or client not open |
| `ToolDispatchError` | `SENSE_INTERNAL_ERROR` | Unknown tool, routing failure |
| `BrunhandUnreachableError` | `EXTERNAL_APP_UNAVAILABLE` | Daemon not reachable |
| `BrunhandTimeoutError` | `SENSE_TIMEOUT` | Request timed out |
| `BrunhandAuthError` | `PERMISSION_DENIED` | Bearer token rejected |
| `BrunhandSessionLockedError` | `SENSE_INTERNAL_ERROR` | Daemon busy (HTTP 423) |
| Any other exception | `SENSE_INTERNAL_ERROR` | Unexpected error; logged |

---

## Config Keys

```yaml
skilningr:
  smidja:
    enabled: false
    host: 127.0.0.1
    port: 8848
    token_env: BRUNHAND_TOKEN_HERETIC
    request_timeout_seconds: 30
    require_https: true
    host_name: default
```

Full reference: `heretic.example.yaml §L5 Skilningr smidja block`

---

## MCP Server  [v0.6.x]

HERETIC's sense hub can also be reached via the Model Context Protocol transport,
in addition to (or instead of) the OpenAI tool_call path.

**The same dispatcher.  The same sandboxes.  The same auth invariants.**
The MCP server is an alternative connection transport, not a separate capability surface.

### McpServer class (`mcp_server.py`)

| Method | State | Notes |
|---|---|---|
| `__init__(config, dispatcher, logger)` | Live | Constructs `mcp.server.lowlevel.Server` instance. |
| `start(transport)` | NotImplementedError | Forge implements: register handlers + open transport. |
| `handle_initialize()` | NotImplementedError | Forge implements if custom init-time logic needed. |
| `handle_tools_list()` | NotImplementedError | Forge implements: calls dispatcher + convert_to_mcp_tool. |
| `handle_tools_call(name, args)` | NotImplementedError | Forge implements: dispatch + encode as TextContent. |

### convert_to_mcp_tool (module-level pure function)

```python
convert_to_mcp_tool(openai_tool: dict) -> dict
```

Translates one OpenAI `{"type": "function", "function": {...}}` schema to
`{"name": ..., "description": ..., "inputSchema": ...}` for `mcp.types.Tool(**result)`.
Raises `ValueError`/`TypeError` on malformed input.  Fully implemented.

### McpServerConfig (`config_model.py`)

```yaml
skilningr:
  mcp_server:
    enabled: false          # opt-in
    transport: stdio        # stdio | http
    host: 127.0.0.1         # http only
    port: 8643              # http only
    allow_remote_bind: false # http + non-loopback gate
    request_timeout_seconds: 60
```

Invariants:
- Non-loopback `host` with `transport: http` requires `allow_remote_bind: true`.
- `transport` must be `"stdio"` or `"http"`.
- `port` must be 1–65535.
- `request_timeout_seconds` must be > 0.

### MCP SDK API (mcp==1.27.0, verified 2026-05-08)

```python
# list_tools handler registration:
@mcp_lowlevel_server.list_tools()
async def handler() -> list[mcp.types.Tool]: ...

# call_tool handler registration:
@mcp_lowlevel_server.call_tool()
async def handler(name: str, arguments: dict) -> list[mcp.types.TextContent]: ...

# stdio transport:
async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
    init_opts = server.create_initialization_options()
    await server.run(read_stream, write_stream, init_opts)

# http transport:
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
manager = StreamableHTTPSessionManager(mcp_lowlevel_server)
# Mount manager.handle at "/" in a Starlette app; run with uvicorn.
```

### Error hierarchy additions (v0.6.x)

| Error class | Parent | When |
|---|---|---|
| `McpServerError` | `SkilningrError` | Root for all MCP server failures |
| `TransportError` | `McpServerError` | stdio stream failure; http port conflict |
| `ProtocolError` | `McpServerError` | MCP application-layer violation |
| `McpAuthError` | `McpServerError` | http bearer token rejected |

### CLI command

```
heretic mcp [--transport stdio|http] [--config PATH]
```

Stub raises `NotImplementedError`.  Forge implements full body.

---

## Module Map

```
src/heretic/skilningr/
  __init__.py        — public re-exports
  INTERFACE.md       — this file
  config_model.py    — SkilningrConfig, SmidjaConfig, McpServerConfig (canonical defs)
  errors.py          — complete error hierarchy (incl. McpServerError tree)
  dispatcher.py      — ToolDispatcher (Forge Wave 2)
  mcp_server.py      — McpServer class + convert_to_mcp_tool (v0.6.x scaffold)
  senses/
    __init__.py
    smidja/
      __init__.py
      INTERFACE.md   — Smiðja sense contract (this sense's seam)
      client.py      — BrunhandHttpClient (Forge Wave 2)
      tools.py       — SMIDJA_TOOL_DEFINITIONS (locked; 6 tools)
      sense.py       — SmidjaSense (Forge Wave 2)
      errors.py      — re-exports from skilningr/errors.py
```

---

*Rúnhild Svartdóttir, Architect — 2026-05-08 (v0.6.x MCP server scaffold)*
