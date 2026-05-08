# Bifröst Module Interface

**Last updated:** 2026-05-07
**Scope:** L1 Bifröst — the Agent Connection layer Python module (`src/heretic/bifrost/`)
**Owner:** Architect (Rúnhild Svartdóttir)
**Derives from:** `docs/architecture/LAYER_INTERFACES.md §L1 Bifröst`
**Legend:** Owns = authoritative data owner; Never-controls = hard boundary.

---

## What Bifröst Owns

- Agent endpoint URL and resolved Bearer token
- Connection state (DISCONNECTED → CONNECTING → CONNECTED → RECOVERING)
- Retry logic and exponential backoff (max_retries, backoff_seconds)
- Heartbeat management and miss threshold detection
- In-ceremony message queue (session-only; zeroed on Slokna)
- Tool call dispatch routing: receives `bifrost::tool_call` → routes to L5 Skilningr
- Capability flag registry for the current ceremony (`?tool_use`, `?vision_in`, `?streaming`)
- Tailscale-aware endpoint resolution (`TailscaleAwareness`)

## What Bifröst Exposes (Public API)

| Export | Module | Purpose |
|---|---|---|
| `BifrostClient` | `bifrost.client` | ABC — the stable contract for all agent connection implementations. |
| `OpenAICompatClient` | `bifrost.client` | Default implementation: OpenAI Chat Completions + SSE + tools array. |
| `BifrostConfig` | `bifrost.config_model` | Typed config struct for the `bifrost:` YAML subtree. |
| `TailscaleAwareness` | `bifrost.tailscale` | Detects Tailscale and resolves preferred endpoint URLs. |
| `BifrostError` | `bifrost.errors` | Root error; all Bifröst errors are subclasses. |
| `BifrostConnectionError` | `bifrost.errors` | Endpoint unreachable (BIFROST_UNREACHABLE). |
| `BifrostAuthError` | `bifrost.errors` | Token rejected (BIFROST_AUTH_FAILED). |
| `BifrostTimeoutError` | `bifrost.errors` | Response timeout (BIFROST_TIMEOUT). |
| `BifrostProbeError` | `bifrost.errors` | Capability probe failed (BIFROST_PROBE_FAILED). |
| `BifrostToolCallUnknownError` | `bifrost.errors` | Agent called unregistered tool. |
| `BifrostProtocolError` | `bifrost.errors` | Malformed agent response. |

## What Bifröst Must Never Control

- Agent memory, persona, or conversation history persistence
- System prompt contents (injected by Holdvörðr, not Bifröst)
- What tool calls actually do (that is L5 Skilningr's domain)
- Voice capture, TTS playback, or screen frame capture (those are L2/L3)
- UI rendering or event display (that is L4 Vébond)

## Inputs

| Input | Source | Notes |
|---|---|---|
| `BifrostConfig` | L0 Grunnr `load_config()` | Resolved and typed at Kynding |
| `voice::transcript(text, timestamp, confidence)` | L2 Rödd | Injected as user-role messages |
| `vision::frame(base64_png, timestamp, source)` | L3 Sjón | Injected when `?vision_in` capability is confirmed |
| `sense_hub::tool_result(call_id, result)` | L5 Skilningr | Returned after a tool call dispatched by Bifröst |
| `heretic::ui::command::open_bifrost` | L4 Vébond | Triggers OPENING phase |
| `heretic::ui::command::close_bifrost` | L4 Vébond | Triggers Slokna drain |
| `heretic::lifecycle::shutdown` | L0 Grunnr | Forces clean close |

## Outputs (events emitted)

| Event | Consumer | Notes |
|---|---|---|
| `bifrost::state(DISCONNECTED\|CONNECTING\|CONNECTED\|RECOVERING\|ERROR)` | L4 Vébond | UI connection indicator |
| `bifrost::agent_turn_start` | L4 Vébond | Turn indicator animation |
| `bifrost::agent_turn_end` | L4 Vébond | Turn indicator reset |
| `bifrost::tool_call(call_id, tool_name, args)` | L5 Skilningr | Dispatched tool call |
| `bifrost::agent_text_delta(text)` | L2 Rödd (Tunga), L4 Vébond | Streaming text chunk |
| `bifrost::error(code, message)` | L4 Vébond | Error toast notification |

## Error Model

| Code | Condition | Recovery |
|---|---|---|
| `BIFROST_AUTH_FAILED` | HTTP 401/403 from agent | Surface in UI; no auto-retry; user must fix key |
| `BIFROST_TIMEOUT` | No response in `timeout_seconds` | Retry per `max_retries` / `backoff_seconds` |
| `BIFROST_UNREACHABLE` | Tailscale/network down | Offer UI retry button; try fallback_to_direct |
| `BIFROST_PROBE_FAILED` | Capability probe timeout | Continue with conservative defaults (all flags False) |
| `BIFROST_TOOL_CALL_UNKNOWN` | Agent calls unregistered tool | Return `tool_error(tool_not_found)` to agent; do not crash |
| `BIFROST_PROTOCOL_ERROR` | Malformed response | Log full response at DEBUG; abort turn; emit error event |

## Capability Flags

Populated after a successful `open()` / capability probe:

| Flag | Meaning |
|---|---|
| `?tool_use` | Agent supports `tools` array + `tool_calls` / `tool` role message format |
| `?vision_in` | Agent can receive `image_url` content in user messages |
| `?streaming` | Agent supports SSE streaming via `stream: true` |

Conservative defaults if probe fails: all flags `False`.

## Invariants

1. `BifrostClient` is the only type that speaks to the agent endpoint. No other module
   makes HTTP calls to the agent URL.
2. The `api_key` value in `BifrostConfig` must be resolved (env var expanded) before
   being passed to `OpenAICompatClient`. Raw `${ENV_VAR}` strings must never reach
   an HTTP header.
3. Session state (message queue, capability flags, Tailscale connection state) is
   zeroed when `close()` returns. The client instance is not reused after `close()`.
4. Tool calls use the `tools` array format — the deprecated `functions` key is never
   sent.

## What Callers Must Not Assume

- That a `BifrostClient` instance can be reused after `close()`.
- That `send_message()` is reentrant — one turn at a time; queuing is Holdvörðr's job.
- That capability flags are stable across ceremonies — they are re-probed on every `open()`.
- That Tailscale is always available — `fallback_to_direct` exists for this reason.
