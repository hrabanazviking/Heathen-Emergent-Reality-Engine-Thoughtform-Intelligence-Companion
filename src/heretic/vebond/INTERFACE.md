# Vebond Module Interface

**Last updated:** 2026-05-07
**Scope:** L4 Vebond / Eldahus — the Summoning Circle layer Python module (`src/heretic/vebond/`)
**Owner:** Architect (Runhild Svartdottir)
**Derives from:** `docs/architecture/LAYER_INTERFACES.md §L4 Vebond`
**Legend:** Owns = authoritative data owner; Never-controls = hard boundary.

---

## What Vebond Owns

- `VebondConfig` — complete typed configuration: UI display settings AND WebSocket server settings.
  This is the canonical definition; `heretic.grunnr.config.HereticConfig.vebond` imports from here.
- `EventBus` — in-process pub/sub bus connecting inner layers to all WebSocket clients.
  Backend layers call `EventBus.publish(event)`; WebSocketServer fans them out.
- `WebSocketServer` — FastAPI application with `/ws` (WebSocket IPC) and `/health` (REST) endpoints.
  Binds to `VebondConfig.ws_host:VebondConfig.ws_port` on start.
- IPC protocol schema — `ProtocolEvent` and `ProtocolCommand` pydantic v2 discriminated unions.
  Python-side mirror of `frontend/src/types/ipc.ts`.
- Error hierarchy — `VebondError` and all subclasses (see `errors.py`).

---

## What Vebond Exposes (Public API)

| Export | Module | Purpose |
|---|---|---|
| `VebondConfig` | `vebond.config_model` | Complete config struct — UI display + WS server. |
| `EventBus` | `vebond.serve` | In-process pub/sub for IPC events. |
| `WebSocketServer` | `vebond.serve` | FastAPI + uvicorn WS/REST server. |
| `ProtocolEvent` | `vebond.protocol` | Discriminated union of all S->C events. |
| `ProtocolCommand` | `vebond.protocol` | Discriminated union of all C->S commands. |
| `CeremonyStateChanged` | `vebond.protocol` | Lifecycle state transition event. |
| `BifrostHealth` | `vebond.protocol` | Bifrost connection state event. |
| `TungaActivity` | `vebond.protocol` | TTS voice-out state event. |
| `HlustActivity` | `vebond.protocol` | STT voice-in state event. |
| `AgentToken` | `vebond.protocol` | Streaming text token event. |
| `AgentTurnComplete` | `vebond.protocol` | Agent turn completion event. |
| `ErrorEvent` | `vebond.protocol` | Error/warning surface event. |
| `LightCommand` | `vebond.protocol` | Initiate ceremony command. |
| `ExtinguishCommand` | `vebond.protocol` | Shutdown ceremony command. |
| `SendMessageCommand` | `vebond.protocol` | User text input command. |
| `CancelTurnCommand` | `vebond.protocol` | Abort in-flight turn command. |
| `ToggleSenseCommand` | `vebond.protocol` | Sense toggle command (read-only in v0.4.0). |
| `VebondError` | `vebond.errors` | Root error for all vebond failures. |
| `VebondConfigError` | `vebond.errors` | Invalid VebondConfig value. |
| `VebondBindError` | `vebond.errors` | Could not bind WS server port. |
| `VebondAuthError` | `vebond.errors` | Reserved for v0.4.x token auth. |
| `ProtocolError` | `vebond.errors` | Malformed or unrecognized IPC message. |
| `MessageTooLargeError` | `vebond.errors` | Message exceeds max_message_size_bytes. |

All of the above are re-exported from `heretic.vebond` directly.

**pydantic dependency note:** `ProtocolEvent`, `ProtocolCommand`, and all event/command
models require `pydantic>=2.5` (part of `heretic[serve]`). `VebondConfig` and the error
classes do NOT require pydantic and are importable without the `[serve]` extra.

---

## What Vebond Must Never Control

- Agent conversation content — `text` in `SendMessageCommand` is injected into L1 Bifrost;
  Vebond never reads, interprets, or modifies it
- Audio DSP, mic capture, or audio playback (L2 Roed)
- Screen capture or frame injection (L3 Sjon)
- MCP tool routing or sense subprocess lifecycle (L5 Skilningr)
- Writing to `heretic.yaml` directly (deferred to L0 Grunnr via `update_config` command in v0.4.x)
- Network routing between HERETIC and the agent (L1 Bifrost owns that)

---

## Inputs

| Input | Source | Notes |
|---|---|---|
| `VebondConfig` | L0 Grunnr `load_config()` | Resolved and typed at Kynding. |
| `heretic::lifecycle::*` events | Holdvordur via EventBus | Drive `ceremony.state_changed` S->C events. |
| `bifrost::state(...)` | L1 Bifrost via EventBus | Drive `bifrost.health` S->C events. |
| `bifrost::agent_text_delta` | L1 Bifrost via EventBus | Drive `agent.token` S->C events. |
| `bifrost::agent_turn_end` | L1 Bifrost via EventBus | Drive `agent.turn_complete` S->C events. |
| `voice::speaking_start/end` | L2 Roed Tunga via EventBus | Drive `tunga.activity` S->C events. |
| `voice::error(...)` | L2 Roed via EventBus | Drive `error` S->C events (source="tunga"/"hlust"). |
| `hlust::state(...)` | L2 Roed Hlust via EventBus | Drive `hlust.activity` S->C events. |
| WebSocket messages from clients | Browser frontend | Parsed as `ProtocolCommand` and dispatched. |

---

## Outputs

### WebSocket events pushed to all connected clients (S->C)

| Event | Condition | Source layer |
|---|---|---|
| `ceremony.state_changed` | Lifecycle state transition | Holdvordur |
| `bifrost.health` | Bifrost connection state change | L1 Bifrost |
| `tunga.activity` | TTS voice-out state change | L2 Roed Tunga |
| `hlust.activity` | STT voice-in state change | L2 Roed Hlust |
| `agent.token` | Streaming text chunk received | L1 Bifrost |
| `agent.turn_complete` | Agent turn ended | L1 Bifrost |
| `error` | Any layer error worth surfacing | Any layer |

### Commands dispatched to inner layers (from client commands)

| Command | Dispatched to |
|---|---|
| `LightCommand` | Holdvordur — trigger OPENING / Bifrost probe |
| `ExtinguishCommand` | Holdvordur — trigger Slokna |
| `SendMessageCommand` | L1 Bifrost — inject user message; begin agent turn |
| `CancelTurnCommand` | L1 Bifrost — cancel in-flight streaming turn |
| `ToggleSenseCommand` | No-op in v0.4.0; L5 Skilningr target in v0.4.x |

---

## Config Keys

```yaml
vebond:
  # --- UI display settings ---
  theme: dark_norse                # dark_norse | (future: custom)
  show_frame_thumbnail: false      # show latest Sjon frame in layer-status panel
  show_agent_text_stream: true     # stream agent text tokens into chat panel
  ceremony_button_confirm: true    # require confirmation before Extinguish

  # --- WebSocket server settings ---
  ws_host: "127.0.0.1"            # bind address; loopback by default
  ws_port: 8642                   # WebSocket port; frontend proxy targets this
  allow_remote_bind: false        # gate for non-loopback ws_host (security)
  max_message_size_bytes: 1048576 # 1 MiB max incoming WS message size
  heartbeat_interval_seconds: 30  # WS ping interval
  connection_timeout_seconds: 60  # max idle time before server drops client
```

---

## Error Model

| Error | Condition | Recovery |
|---|---|---|
| `VebondConfigError` | Invalid `VebondConfig` field at construction | Fix `heretic.yaml`; restart |
| `VebondBindError` | Port in use or interface unavailable at startup | Change port; free conflicting process |
| `VebondAuthError` | (v0.4.x) Invalid client token | Surface in UI; no auto-retry |
| `ProtocolError` | Malformed or unrecognized WebSocket message | Send `error` event (warn); keep connection open |
| `MessageTooLargeError` | Message exceeds `max_message_size_bytes` | Send `error` event (warn); keep connection open |

---

## SLO Tier

**Hot** — the UI must reflect state changes (connection status, voice activity, lifecycle)
within 60 ms of event emission (per `LAYER_INTERFACES.md §L4`). The WebSocket event fan-out
path must not introduce latency above this threshold under normal operating conditions.

---

## Dependencies

The `vebond` package requires these Python packages to be installed (via `pip install heretic[serve]`):

```
fastapi>=0.110
uvicorn[standard]>=0.27
websockets>=12
pydantic>=2.5
```

`VebondConfig` and the error hierarchy have NO external dependencies beyond the Python
standard library — they are importable without `[serve]`.
