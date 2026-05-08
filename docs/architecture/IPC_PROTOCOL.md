# HERETIC — IPC Protocol (L4 Vebond WebSocket Schema)

**Last updated:** 2026-05-08 (v0.5 scaffold — Rúnhild Svartdóttir: added §3.8 sjon.activity event; extended §8 naming bridge with sjon.activity row and §8.3 vision::frame internal note; added SjonActivityState shared value type to §2) | 2026-05-07 (revised: audit N-1 + N-3 remediation — Rúnhild Svartdóttir)
**Scope:** The canonical typed schema for all WebSocket messages exchanged between
the Python backend (L4 Vebond) and the React frontend (Eldahus). This file is the
**single source of truth**. Both implementation files derive from it — any discrepancy
between this document and the code is a bug in the code.

**Authority:** Architect (Runhild Svartdottir)

**Implementation files that mirror this schema:**
- `src/heretic/vebond/protocol.py` — Python / pydantic v2 models
- `frontend/src/types/ipc.ts` — TypeScript discriminated unions

**Related:**
- `docs/architecture/LAYER_INTERFACES.md §L4 Vebond` — layer ownership contract
- `docs/architecture/CEREMONY.md` — lifecycle states the UI must reflect
- `src/heretic/vebond/config_model.py` — VebondConfig (host, port, auth gate)

**Legend:**
- `S->C` — server to client (backend pushes state)
- `C->S` — client to server (frontend sends user actions)
- All `timestamp` fields: ISO 8601 UTC, format `2026-05-07T14:32:00.000Z`

---

## 1. Transport

**Protocol:** WebSocket (RFC 6455)
**Default URL:** `ws://127.0.0.1:8642/ws`
**Configurable via:** `vebond.ws_host` and `vebond.ws_port` in `heretic.yaml`

**Serialization:** JSON text frames. All messages are UTF-8 JSON objects with a
required `type` string field that acts as a discriminator.

**REST health endpoint:** `GET http://127.0.0.1:8642/health`
Returns the following JSON object with HTTP 200 when the server is up:

```json
{
  "status": "ok",
  "version": "<heretic version string>",
  "lifecycle_state": "<current LifecycleState wire value>"
}
```

Fields:
- `status`: always `"ok"` when the server responds to this endpoint.
- `version`: the running `heretic.__version__` string (e.g. `"0.1.0.dev0"`).
- `lifecycle_state`: the current ceremony lifecycle state as a wire-format string,
  using the same LifecycleState values defined in §2 (e.g. `"hvild"`, `"kynding"`,
  `"tengsl"`). See CEREMONY.md §1 for the full mapping from internal enum to
  wire-format string. Tauri sidecar health checks should inspect this field to
  determine whether a ceremony is already active before attempting to connect.

Used by monitoring, CI, and Tauri sidecar health checks.

### 1.1 Message size

Incoming messages (C->S) exceeding `vebond.max_message_size_bytes` (default 1 MiB)
are rejected. The server sends an `error` event (level='warn') and keeps the connection
open — a single oversized message is not fatal.

### 1.2 Heartbeat

The server sends a WebSocket ping frame every `vebond.heartbeat_interval_seconds`
(default 30 s). If no pong is received within `vebond.connection_timeout_seconds`
(default 60 s), the server drops the connection and cleans up its state.

### 1.3 Authentication

**v0.4.0:** Localhost only. No authentication. The browser frontend and (in v0.4.1)
the Tauri WebView are the sole clients — both run on the same machine. No token is
required or checked.

**Non-loopback binding:** Requires `vebond.allow_remote_bind: true` in heretic.yaml.
The operator is responsible for network-level security when binding to non-loopback
addresses. `VebondAuthError` is reserved for v0.4.x token authentication.

---

## 2. Shared Value Types

These string literal sets are used as field types across multiple messages.

```
LifecycleState: "hvild" | "kynding" | "tengsl" | "samraedur" | "slokna"
              | "recovering" | "config_error"

  Maps to CEREMONY.md states:
    hvild        — Hvild (rest; process not running)
    kynding      — Kynding (kindling; encompasses READY and OPENING sub-states)
    tengsl       — Tengsl (bonds; Bifrost open, spirit present)
    samraedur    — Samraedur (communion; active turns)
    slokna       — Slokna (extinguish; draining and shutdown)
    recovering   — RECOVERING (reconnecting mid-Samraedur; sub-state of Tengsl/Samraedur)
    config_error — CONFIG_ERROR (heretic.yaml invalid; terminal state)

  L4 Vebond display rules (per CEREMONY.md §8):
    READY sub-state        -> show as "kynding"
    OPENING sub-state      -> show as "kynding" (fire rising)
    RECOVERING sub-state   -> show as "recovering" (flickering modifier)
    EXTINGUISHED sub-state -> show as "slokna" transitioning to "hvild"
    CONFIG_ERROR           -> distinct error state; not a True Name phase

BifrostStatus:  "open" | "closed" | "opening" | "failed"
TungaState:     "idle" | "synthesizing" | "speaking" | "failed"
HlustState:     "idle" | "loading" | "listening" | "transcribing" | "failed"
SjonState:      "idle" | "capturing" | "encoding" | "failed"
  Emitted as the `state` field of sjon.activity events (§3.8).
    idle      — no capture in progress; Sjón available and waiting
    capturing — MssBackend.capture() executing in a thread pool executor
    encoding  — FrameEncoder converting raw bytes to PNG and base64
    failed    — last capture or encode attempt failed; recovers on next snapshot()
ErrorLevel:     "warn" | "error"
```

---

## 3. Events — Server to Client (S->C)

The server pushes events to all connected clients via the EventBus. Events are
JSON text frames. All events have a `type` string field for discrimination.

---

### 3.1 `ceremony.state_changed`

Emitted when the ceremony lifecycle state transitions. The frontend uses this to
update the Summoning Circle visual state, enable/disable ceremony controls, and
drive the lifecycle pulse animation.

**Direction:** S->C
**Emitted by:** Holdvordur (Lifecycle state machine) via EventBus
**Frequency:** Once per state transition

```json
{
  "type": "ceremony.state_changed",
  "from_state": "<LifecycleState>",
  "to_state": "<LifecycleState>",
  "timestamp": "<ISO 8601 UTC>"
}
```

**Field notes:**
- `from_state`: the state being left
- `to_state`: the state being entered
- `timestamp`: when the transition occurred (server clock)

**Frontend response:**
- Update Summoning Circle ring color and animation based on `to_state`
- Enable/disable LightButton (enabled in kynding), ExtinguishButton (enabled in tengsl/samraedur)
- Update lifecycle label in status panel

---

### 3.2 `bifrost.health`

Emitted when the L1 Bifrost connection state changes (DISCONNECTED, CONNECTING,
CONNECTED, RECOVERING, ERROR). The frontend uses this to update the connection
indicator and the Bifrost entry in the layer-status panel.

**Direction:** S->C
**Emitted by:** L1 Bifrost on every connection state machine transition
**Frequency:** On each Bifrost state change

```json
{
  "type": "bifrost.health",
  "status": "<BifrostStatus>",
  "endpoint": "<agent endpoint URL>",
  "latency_ms": <integer or null>
}
```

**Field notes:**
- `endpoint`: the agent URL being targeted. Never includes auth tokens.
- `latency_ms`: round-trip latency of the last successful capability probe, in ms.
  `null` if no probe has completed or the connection is not open.

**Frontend response:**
- Update LayerStatusItem for Bifrost (healthy = open, degraded = failed)
- Update ConnectionIndicator if bifrost.status is used as a proxy for overall health

---

### 3.3 `tunga.activity`

Emitted when the Tunga (TTS / voice-out) state changes. The frontend animates the
Mal-green voice-out indicator in response.

**Direction:** S->C
**Emitted by:** L2 Roed Tunga on state transitions
**Frequency:** On each Tunga state change

```json
{
  "type": "tunga.activity",
  "state": "<TungaState>"
}
```

**Frontend response:**
- "speaking" -> animate Mal-green outward bloom (agent is speaking)
- "synthesizing" -> dim pulse (generating audio)
- "idle" -> indicator returns to resting state
- "failed" -> LayerStatusItem shows degraded

---

### 3.4 `hlust.activity`

Emitted when the Hlust (STT / voice-in) state changes. The frontend animates the
Mal-green voice-in indicator and displays the listening waveform.

**Direction:** S->C
**Emitted by:** L2 Roed Hlust on state transitions
**Frequency:** On each Hlust state change; also emitted periodically while listening
with updated `level_db`

```json
{
  "type": "hlust.activity",
  "state": "<HlustState>",
  "level_db": <float or null>
}
```

**Field notes:**
- `level_db`: current mic input level in dBFS. Range: -infinity to 0.0 (0.0 = max signal).
  `null` when not actively capturing.
  Used to drive the voice-level waveform visualisation (animate-listen).

**Frontend response:**
- "listening" -> animate inward pull (animate-listen) per AESTHETIC.md
- "transcribing" -> brief transition animation
- "idle" -> indicator returns to resting state
- ChatInput shows voice-cue indicator when state is "listening" or "transcribing"

---

### 3.8 `sjon.activity`

Emitted when the Sjón (Vision / screen capture) state changes during a snapshot.
The frontend uses this to animate the Sjón-glow blue accent in LayerStatusPanel,
mirroring the pattern of `tunga.activity` and `hlust.activity`.

**Direction:** S->C
**Emitted by:** L3 Sjón orchestrator (`sjon.sjon.Sjón`) via EventBus at capture milestones
**Frequency:** At each capture lifecycle transition during snapshot() — not during idle periods

```json
{
  "type": "sjon.activity",
  "state": "<SjonState>",
  "timestamp": "<ISO 8601 UTC>"
}
```

**Field notes:**
- `state`: current state of the Sjón capture pipeline (SjonState — see §2).
- `timestamp`: UTC ISO 8601 timestamp of the state transition.

**Frontend response:**
- "capturing" -> dim blue pulse begins (MssBackend executing)
- "encoding" -> brief transition animation (Pillow encoding)
- "idle" -> Sjón-glow blue accent returns to resting state
- "failed" -> LayerStatusPanel Sjón row shows degraded indicator

**Implementation references:**
- Python model: `heretic.vebond.protocol.SjonActivity`
- TypeScript mirror: `frontend/src/types/ipc.ts` (to be added by Forge — v0.5 Wave 2)

---

### 3.5 `agent.token`

Emitted for each streaming text token received from the agent. The frontend
appends `text_delta` to the current assistant message in the chat history as
tokens arrive.

**Direction:** S->C
**Emitted by:** L1 Bifrost on each `bifrost::agent_text_delta` event
**Frequency:** High — one per streaming chunk from the agent (may be many per second)

```json
{
  "type": "agent.token",
  "role": "assistant",
  "text_delta": "<text fragment>",
  "sequence_id": <integer>
}
```

**Field notes:**
- `text_delta`: the text fragment in this chunk. May be a single character, a word,
  or multiple words depending on the agent's streaming granularity.
- `sequence_id`: monotonically increasing integer per turn, starting at 0 for each
  new agent turn. The frontend can detect dropped messages by checking for gaps.
- `role`: always "assistant" in v0.4. Future: may include "tool_result" deltas.

**Note:** The `turn_id` field is carried implicitly — the frontend tracks it as
`activeTurnId` in the store, set when the first token of a new turn arrives and
cleared on `agent.turn_complete`. If explicit turn_id tagging is needed, it will be
added in v0.4.x.

**Frontend response:**
- Append `text_delta` to the current streaming ChatMessage in chatHistory
- Show streaming cursor while `sequence_id` increments
- Do NOT commit the message as complete until `agent.turn_complete` arrives

---

### 3.6 `agent.turn_complete`

Emitted when the agent finishes generating a response for one turn. The frontend
finalizes the current message, enables ChatInput, and stops the streaming cursor.

**Direction:** S->C
**Emitted by:** L1 Bifrost on `bifrost::agent_turn_end`
**Frequency:** Once per agent turn

```json
{
  "type": "agent.turn_complete",
  "turn_id": "<unique turn identifier>",
  "finish_reason": "<finish reason string>"
}
```

**Field notes:**
- `turn_id`: unique identifier for this turn (generated by the backend per turn).
  Used in `CancelTurnCommand` to target an in-flight turn.
- `finish_reason`: why the turn ended:
  - `"stop"` — natural end of generation
  - `"length"` — max_tokens reached (per `bifrost.max_tokens` in heretic.yaml)
  - `"tool_calls"` — agent issued tool calls (handled internally; not normally surfaced)
  - `"cancelled"` — turn was cancelled by a `CancelTurnCommand`
  - `"error"` — turn ended due to a Bifrost error

**Frontend response:**
- Set streaming=false on the active ChatMessage
- Clear activeTurnId
- Enable ChatInput
- If finish_reason is "error": show an ErrorEvent toast (the `error` event should
  arrive separately with details)

---

### 3.7 `error`

Emitted when any layer encounters an error worth surfacing to the user. The frontend
displays these as toast notifications per AESTHETIC.md error-tone motion pattern.

**Direction:** S->C
**Emitted by:** Any layer via EventBus.publish()
**Frequency:** On error conditions; not during normal operation

```json
{
  "type": "error",
  "level": "<ErrorLevel>",
  "source": "<layer or module name>",
  "message": "<human-readable description>"
}
```

**Field notes:**
- `level`: "warn" — ceremony continues, informational; "error" — may require user action
- `source`: which layer emitted the error. Examples: "bifrost", "tunga", "hlust",
  "vebond", "lifecycle", "hlust.vad", "tunga.chatterbox"
- `message`: user-intelligible description. NOT a Python traceback. NOT an internal
  error code. Should read naturally to a non-technical user.

**Frontend response (per AESTHETIC.md):**
- Show toast notification with `animate-error-once` (single slow pulse, not repeating)
- "warn" level: auto-dismiss after 6 seconds
- "error" level: remain until manually dismissed
- Route `source` to the appropriate LayerStatusItem to update its health indicator

---

## 4. Commands — Client to Server (C->S)

The frontend sends commands as JSON text frames. All commands have a `type` string
field. The server deserializes using the ProtocolCommand discriminated union.

Invalid commands (malformed JSON, missing required fields, unknown type) result in
an `error` event (level='warn') pushed back to the sending client. The server does
not close the connection for a single bad command.

---

### 4.1 `light`

Initiate the Kynding -> Tengsl ceremony sequence (Light the Candle).

**Direction:** C->S
**Valid states:** Must be sent when lifecycleState is "kynding" or "hvild"
**Expected response events:** `ceremony.state_changed` (to "kynding" with OPENING
sub-state), `bifrost.health` (status="opening"), then `ceremony.state_changed`
(to "tengsl" on success, or to "kynding" on failure), `bifrost.health` (open or failed)

```json
{
  "type": "light"
}
```

**Backend behavior:**
1. Transition lifecycle to OPENING
2. Initiate L1 Bifrost capability probe (see `AGENT_AGNOSTIC_PROTOCOL.md §5.1`)
3. On probe success: transition to Tengsl, emit `ceremony.state_changed`
4. On probe failure: transition back to READY (kynding), emit `error` + `ceremony.state_changed`

---

### 4.2 `extinguish`

Initiate the Slokna shutdown sequence (Extinguish the Candle).

**Direction:** C->S
**Valid states:** tengsl, samraedur, recovering
**Expected response events:** `ceremony.state_changed` (slokna), then
`ceremony.state_changed` (kynding or hvild)

```json
{
  "type": "extinguish"
}
```

**Frontend responsibility:** If `vebond.ceremony_button_confirm: true` (default),
the frontend must show a confirmation dialog before sending this command. The backend
does not perform a second confirmation.

**Backend behavior:**
1. Transition lifecycle to SLOKNA
2. Stop accepting new user inputs from L2 Roed
3. Drain in-flight turns and tool calls (`bifrost.drain_timeout_seconds`)
4. Close Bifrost, stop Roed and Sjon
5. Zero session state; transition to EXTINGUISHED then READY (or HVILD if app closes)

---

### 4.3 `send_message`

Send a user text message into the active Samraedur turn loop.

**Direction:** C->S
**Valid states:** samraedur, tengsl (before first turn)
**Expected response events:** `agent.token` (N times), `agent.turn_complete`

```json
{
  "type": "send_message",
  "text": "<user message>"
}
```

**Field notes:**
- `text`: non-empty string. Backend strips leading/trailing whitespace. An empty or
  whitespace-only `text` results in an `error` event (level='warn'); the command is ignored.

**Backend behavior:**
1. Validate lifecycle state (samraedur or tengsl); reject otherwise
2. Validate text is non-empty after stripping
3. Inject as a user-role message into the Bifrost message array
4. Begin agent turn; emit `agent.token` events for each streaming chunk
5. Emit `agent.turn_complete` when the turn ends

---

### 4.4 `cancel_turn`

Abort an in-flight agent turn.

**Direction:** C->S
**Valid states:** samraedur (while `activeTurnId` is non-null)
**Expected response events:** `agent.turn_complete` with `finish_reason="cancelled"`
(if cancellation succeeds), or `error` (level='warn') if no matching turn is in flight

```json
{
  "type": "cancel_turn",
  "turn_id": "<turn identifier>"
}
```

**Field notes:**
- `turn_id`: the value from the `turn_id` field on `agent.turn_complete` events for
  the current turn. The frontend tracks this as `activeTurnId` in the store.

**Backend behavior:**
1. Look up the in-flight turn by `turn_id`
2. If found: cancel the streaming HTTP request; emit `agent.turn_complete` (cancelled)
3. If not found (already complete): emit `error` (level='warn'); no-op

---

### 4.5 `toggle_sense`

Toggle a sense (Hlust, Tunga, Sjon, etc.) on or off.

**Direction:** C->S
**Valid states:** any
**v0.4.0 status:** RECEIVED BUT NOT ACTED UPON

```json
{
  "type": "toggle_sense",
  "sense_id": "<sense identifier>",
  "enabled": <boolean>
}
```

**Field notes:**
- `sense_id` valid values: `"hlust"`, `"tunga"`, `"sjon_screen"`, `"sjon_webcam"`,
  `"filesystem"`, `"terminal"`, `"browser"`, `"photopea"`, `"blender"`, `"vrchat"`,
  `"agentmail"`, `"library"`
- Unknown `sense_id` results in `error` (level='warn')

**v0.4.0 behavior:** The backend receives this command and emits:
```json
{
  "type": "error",
  "level": "warn",
  "source": "vebond",
  "message": "Sense toggles are read-only in v0.4.0. Restart the ceremony with the updated heretic.yaml to change sense configuration."
}
```

**v0.4.x behavior:** The command will trigger a heretic.yaml key update and hot-reload
of the affected sense subprocess, without requiring a ceremony restart.

---

## 5. Connection Lifecycle

### 5.1 New connection

1. Client opens WebSocket to `ws://127.0.0.1:8642/ws`
2. Server accepts and adds to connected clients
3. Server immediately pushes the current ceremony state snapshot:
   - `ceremony.state_changed` with `from_state` = current state, `to_state` = current state
   - `bifrost.health` with current Bifrost status
   - `tunga.activity` with current Tunga state
   - `hlust.activity` with current Hlust state
   - `sjon.activity` with current Sjón state (added in v0.5)
   This lets the client initialize its UI to the correct state without waiting for
   the next transition event.
4. Client begins reading events and may send commands immediately

### 5.2 Disconnection

If the client disconnects (browser tab closed, network failure, or `disconnect()` call):
1. Server removes the client from connected clients
2. Server cancels any fan-out tasks for that connection
3. No event is emitted to other clients — client loss is transparent
4. The ceremony continues uninterrupted

If the server stops (process killed, `server.stop()` called during Slokna):
1. Server sends a WebSocket close frame (code 1001 Going Away) to all connected clients
2. Clients receive `onclose` and should update connectionStatus to "disconnected"

### 5.3 Multiple clients

The server supports multiple simultaneous WebSocket connections. All events are
broadcast to all connected clients. Commands from any client are processed equally.
In v0.4.0 there is no client distinction or access control — all clients share the
same ceremony state. v0.4.x may add client identity for multi-operator scenarios.

---

## 6. Error Handling Summary

| Condition | Server behavior | Client sees |
|---|---|---|
| Malformed JSON (C->S) | Send error event (warn), keep connection | error event |
| Unknown `type` field (C->S) | Send error event (warn), keep connection | error event |
| Oversized message (C->S) | Send error event (warn), keep connection | error event |
| Command in wrong lifecycle state | Send error event (warn), keep connection | error event |
| Empty `text` in `send_message` | Send error event (warn), discard | error event |
| Backend layer error | Emit error event to all clients | error event |
| Bifrost connection lost | Emit bifrost.health + ceremony.state_changed (recovering) | both events |
| Server stops (Slokna) | WS close frame (1001) to all clients | onclose |
| Client disconnect | Remove from connected set; no broadcast | none |

---

## 7. TypeScript / Python Schema Symmetry

The discriminated union pattern is identical on both sides:

**Python (pydantic v2):**
```python
ProtocolEvent = Annotated[
    Union[CeremonyStateChanged, BifrostHealth, ...],
    Field(discriminator="type"),
]
```

**TypeScript:**
```typescript
export type ProtocolEvent =
  | CeremonyStateChanged
  | BifrostHealth
  | ...;
// Narrowing: if (isCeremonyStateChanged(event)) { event.to_state ... }
```

The `type` field value strings are identical in both languages. A message valid in
Python will deserialize correctly in TypeScript and vice versa. Changes to either
representation must be propagated to both simultaneously. This file (IPC_PROTOCOL.md)
is the authority that governs both.

---

## 8. Naming Bridge — Internal Bus vs Wire Protocol

**Cross-reference:** This section bridges two authoritative but distinct vocabularies.
- `docs/architecture/LAYER_INTERFACES.md §L4 Vébond` is authoritative for the
  **internal event-bus contract** — the names used inside the Python process when
  modules communicate through the EventBus or Lifecycle machine.
- This file (`IPC_PROTOCOL.md`) is authoritative for the **wire-protocol contract** —
  the JSON `type` strings that cross the WebSocket boundary between the Python backend
  and the React frontend.

A developer reading only LAYER_INTERFACES.md cannot trace `open_bifrost` to its wire
counterpart without reading `cli.py`. This section makes the mapping explicit.

The mapping is **informational**. It does not extend the authority of either document
into the other's domain. If a wire `type` value conflicts with what appears here, the
relevant authoritative document governs.

### 8.1 Command mapping (C->S: frontend sends, backend handles)

| Internal-bus name (LAYER_INTERFACES.md §L4 Outputs) | Wire `type` (IPC_PROTOCOL.md §4) | Direction | Section |
|---|---|---|---|
| `heretic::ui::command::open_bifrost` | `light` | C->S | §4.1 |
| `heretic::ui::command::close_bifrost` | `extinguish` | C->S | §4.2 |
| `heretic::ui::command::toggle_sense(sense_id, enabled)` | `toggle_sense` | C->S | §4.5 |
| `heretic::ui::command::toggle_voice_in(enabled)` | — internal only, not exposed in v0.4.0 | — | — |
| `heretic::ui::command::toggle_voice_out(enabled)` | — internal only, not exposed in v0.4.0 | — | — |
| `heretic::ui::command::update_config(key, value)` | — internal only, not exposed in v0.4.0 | — | — |

Notes on internal-only commands:
- `toggle_voice_in` / `toggle_voice_out`: voice-layer toggles are not yet surfaced as
  discrete wire commands in v0.4.0. Voice configuration is set via `heretic.yaml` at
  startup. These will be mapped to wire commands in v0.4.x when hot-reload is wired.
- `update_config`: surface-level config changes are routed internally to L0 Grunnr and
  are not exposed as a wire command in v0.4.0. No `update_config` wire type exists.

The `send_message` and `cancel_turn` commands (§4.3, §4.4) have no named internal-bus
counterpart in LAYER_INTERFACES.md §L4 — they are originate-at-the-wire commands
generated by the frontend user action, with no internal-bus equivalent.

### 8.2 Event mapping (S->C: backend pushes, frontend receives)

| Internal-bus / lifecycle source (LAYER_INTERFACES.md §L4 Inputs) | Wire `type` (IPC_PROTOCOL.md §3) | Direction | Section |
|---|---|---|---|
| `heretic::lifecycle::*` transitions → `_on_lifecycle_state_change` | `ceremony.state_changed` | S->C | §3.1 |
| `bifrost::state` transitions (open, failed, closed, recovering) | `bifrost.health` | S->C | §3.2 |
| `voice::speaking_start` / `voice::speaking_end` (Tunga state change) | `tunga.activity` | S->C | §3.3 |
| `voice::listening_start` / `voice::transcribing` (Hlust state change) | `hlust.activity` | S->C | §3.4 |
| `bifrost::agent_text_delta` chunks | `agent.token` | S->C | §3.5 |
| `bifrost::agent_turn_end` | `agent.turn_complete` | S->C | §3.6 |
| Any layer error via `EventBus.publish(ErrorEvent)` | `error` | S->C | §3.7 |
| `heretic::ui::state_update(full_state_snapshot)` | — internal only; snapshot delivered as 4 separate events on WS connect (§5.1) | — | §5.1 |
| `sense_hub::sense_healthy(sense_id)` / `sense_hub::sense_degraded(sense_id)` | — internal only, not exposed as a discrete wire event in v0.4.0 | — | — |
| `vision::frame(base64_png, timestamp, source)` (Sjón capture output) | — internal only; frame is not exposed as a raw wire event. The frame bytes are injected directly into the Bifröst message payload as `image_url` content (see AGENT_AGNOSTIC_PROTOCOL.md §2.1 and §8 item 7). The `sjon.activity` wire event (§3.8) communicates capture *state* only — not the frame itself. | — | §3.8 |
| Sjón capture state transitions (internal SjonActivityState enum) | `sjon.activity` | S->C | §3.8 |

Notes on internal-only events:
- `heretic::ui::state_update`: LAYER_INTERFACES.md describes this as the authoritative
  UI state snapshot. On the wire it is decomposed into four individual events sent on
  every new WebSocket connection (§5.1): `ceremony.state_changed`, `bifrost.health`,
  `tunga.activity`, `hlust.activity`. There is no single `state_update` wire event type.
- `sense_hub::sense_healthy` / `sense_hub::sense_degraded`: Sense health changes are
  delivered to the UI only as `error` events (level="warn") from the relevant source
  in v0.4.0. A discrete `sense.health` wire event is planned for v0.4.x when
  Skilningr (L5) is wired.
- `vision::frame`: Vision frame thumbnails are not exposed over the WebSocket in v0.4.0.

### 8.3 Implementation anchor

The mapping above is implemented in `src/heretic/cli.py:_async_serve`. Specifically:
- `_state_map` (cli.py ~line 467) maps internal `LifecycleState` enum values to
  wire-format `LifecycleState` strings used in `ceremony.state_changed` events.
- `command_handlers` dict (cli.py ~line 746) maps wire `type` strings (`"light"`,
  `"extinguish"`, `"send_message"`, `"cancel_turn"`, `"toggle_sense"`) to their
  handler functions.

If the implementation diverges from this table, the implementation must be updated to
match — this document is the authority for intended behavior.

---

## 9. Version and Compatibility

**v0.4.0:** This schema is first released. All fields are REQUIRED unless marked
"or null" or given a default value. The server sets `Content-Type` on the health
endpoint response but does not set a protocol version header on the WebSocket
connection in v0.4.0.

**v0.4.x:** Will add:
- ToggleSenseCommand functional implementation
- Turn-level `turn_id` tagging on AgentToken events
- Optional bearer token authentication (`VebondAuthError`)
- Protocol version negotiation header on connect

**Schema change policy:** Additive changes (new optional fields, new event types)
are backward-compatible. Removing fields or changing `type` string values is a
breaking change requiring a version bump and migration guide.
