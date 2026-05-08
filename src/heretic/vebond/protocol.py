"""
Vébond IPC protocol schema — typed Python representations of every WebSocket
event and command in the HERETIC L4 protocol.

Design decision: pydantic v2 (not plain dataclasses).

Rationale:
    - Discriminated unions with Annotated + Literal type fields give us clean
      deserialization: json.loads() + model_validate() in one call, with the
      'type' discriminator selecting the correct concrete model automatically.
    - pydantic v2's model_dump(mode='json') produces JSON-ready dicts without
      custom serialization code — necessary for the server to push events to the
      browser via WebSocket.
    - The TypeScript types in frontend/src/types/ipc.ts mirror this schema exactly.
      pydantic's discriminated union pattern (on a 'type' Literal field) maps
      directly to TypeScript discriminated unions on the same field name, giving
      clean symmetry without a code-generation step.
    - The alternative (plain dataclasses + manual JSON) would require hand-writing
      the same validation logic that pydantic provides. For an IPC boundary that
      carries structured data in both directions, pydantic is the right choice.

If pydantic is not installed (it is an optional [serve] dep), importing this
module will fail with a clear ImportError. Forge must ensure pydantic is installed
before instantiating the server.

Canonical reference: docs/architecture/IPC_PROTOCOL.md — that file is the
source of truth for the schema. This module implements it. Any discrepancy
between this module and IPC_PROTOCOL.md is a bug in this module.

Direction conventions (mirroring IPC_PROTOCOL.md):
    Events:   server -> client (backend pushes state to frontend)
    Commands: client -> server (frontend sends user actions to backend)
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Literal, Optional, Union

try:
    from pydantic import BaseModel, Field
except ImportError as _pydantic_missing:
    raise ImportError(
        "pydantic>=2.5 is required for heretic.vebond.protocol. "
        "Install it with: pip install heretic[serve]"
    ) from _pydantic_missing


# ==============================================================================
# Shared value types
# ==============================================================================

LifecycleStateStr = Literal[
    "hvild",       # Hvíld — rest; process not running or in Hvíld
    "kynding",     # Kynding — kindling; startup and READY/OPENING sub-states
    "tengsl",      # Tengsl — bonds; Bifröst open, spirit present
    "samraedur",   # Samræður — communion; active turns
    "slokna",      # Slokna — extinguish; drain and shutdown
    "recovering",  # RECOVERING — reconnecting mid-Samræður
    "config_error", # CONFIG_ERROR — terminal state; heretic.yaml invalid
]
"""All lifecycle states the UI must be able to display.

Includes both public ceremonial states (True Names) and the sub-states exposed
in the WebSocket protocol for UI granularity (recovering, config_error).
See CEREMONY.md §8 for the full public vs sub-state mapping.
"""

BifrostStatusStr = Literal["open", "closed", "opening", "failed"]

TungaStateStr = Literal["idle", "synthesizing", "speaking", "failed"]

HlustStateStr = Literal["idle", "loading", "listening", "transcribing", "failed"]

ErrorLevelStr = Literal["warn", "error"]


# ==============================================================================
# Server -> Client Events
# ==============================================================================

class CeremonyStateChanged(BaseModel):
    """Emitted when the ceremony lifecycle state transitions.

    The frontend uses this to update the Summoning Circle visual state,
    enable/disable controls, and update the lifecycle pulse animation.

    Direction: server -> client
    Emitted by: Holdvörðr (Lifecycle state machine) via EventBus
    """

    type: Literal["ceremony.state_changed"] = "ceremony.state_changed"
    from_state: LifecycleStateStr
    to_state: LifecycleStateStr
    timestamp: str
    """ISO 8601 UTC timestamp of the transition. Format: '2026-05-07T14:32:00.000Z'"""


class BifrostHealth(BaseModel):
    """Emitted when the L1 Bifröst connection state changes.

    The frontend uses this to update the connection indicator and
    the Bifröst entry in the layer-status panel.

    Direction: server -> client
    Emitted by: L1 Bifröst on every state transition of its connection state machine
    """

    type: Literal["bifrost.health"] = "bifrost.health"
    status: BifrostStatusStr
    endpoint: str
    """The agent endpoint URL being targeted. Never includes auth tokens."""
    latency_ms: Optional[int] = None
    """Round-trip latency of the last successful capability probe, in milliseconds.
    None if no probe has completed or the connection is not open."""


class TungaActivity(BaseModel):
    """Emitted when the Tunga (TTS / voice-out) state changes.

    The frontend uses this to animate the Mál-green voice-out indicator.

    Direction: server -> client
    Emitted by: L2 Rödd Tunga on state transitions
    """

    type: Literal["tunga.activity"] = "tunga.activity"
    state: TungaStateStr


class HlustActivity(BaseModel):
    """Emitted when the Hlust (STT / voice-in) state changes.

    The frontend uses this to animate the Mál-green voice-in indicator
    and display the listening/transcribing waveform.

    Direction: server -> client
    Emitted by: L2 Rödd Hlust on state transitions
    """

    type: Literal["hlust.activity"] = "hlust.activity"
    state: HlustStateStr
    level_db: Optional[float] = None
    """Current microphone input level in dBFS. None when not actively capturing.
    Range: -inf to 0.0 dBFS (0.0 is max signal, negative is quieter).
    Used to drive the voice-level waveform visualisation in the UI."""


class AgentToken(BaseModel):
    """Emitted for each streaming text token received from the agent.

    The frontend appends text_delta to the current assistant message in the
    chat history as tokens arrive. sequence_id is monotonically increasing per
    turn and allows the frontend to detect dropped messages.

    Direction: server -> client
    Emitted by: L1 Bifröst on each bifrost::agent_text_delta event
    """

    type: Literal["agent.token"] = "agent.token"
    role: Literal["assistant"] = "assistant"
    text_delta: str
    """The text fragment received in this streaming chunk. May be a single character,
    a word, or multiple words depending on the agent's streaming granularity."""
    sequence_id: int
    """Monotonically increasing integer per turn. Starts at 0 for each new agent turn.
    Allows the frontend to detect out-of-order or dropped token events."""


class AgentTurnComplete(BaseModel):
    """Emitted when the agent finishes generating a response for one turn.

    The frontend uses this to finalize the current message (stop the streaming
    cursor), enable the ChatInput, and potentially trigger TTS completion.

    Direction: server -> client
    Emitted by: L1 Bifröst on bifrost::agent_turn_end
    """

    type: Literal["agent.turn_complete"] = "agent.turn_complete"
    turn_id: str
    """Unique identifier for this turn. Generated by the backend per turn.
    The same turn_id used in AgentToken events for this turn and in any
    CancelTurnCommand issued by the client."""
    finish_reason: str
    """Why the turn ended. Mirrors OpenAI finish_reason values:
    'stop' — natural end of generation
    'length' — max_tokens reached
    'tool_calls' — agent issued tool calls (handled internally; not normally surfaced)
    'cancelled' — turn was cancelled by a CancelTurnCommand
    'error' — turn ended due to a Bifröst error"""


class SjonActivityState(str, Enum):
    """State values for the Sjón (Vision / screen capture) activity indicator.

    Maps to the capture lifecycle of L3 Sjón at capture milestones.
    The frontend uses this to animate the Sjón-glow blue accent in LayerStatusPanel.

    Wire value: the string value of each member (lowercase — e.g. "idle").
    """
    IDLE = "idle"
    """No capture in progress. Sjón is available and waiting for the next snapshot() call."""
    CAPTURING = "capturing"
    """MssBackend.capture() is executing (in a thread pool executor)."""
    ENCODING = "encoding"
    """FrameEncoder is converting raw bytes to PNG and base64."""
    FAILED = "failed"
    """The last capture or encode attempt failed. Sjón will retry on the next snapshot() call."""


class SjonActivity(BaseModel):
    """Emitted when the Sjón (Vision / screen capture) state changes.

    The frontend uses this to animate the Sjón-glow blue accent in the
    LayerStatusPanel, mirroring the pattern of tunga.activity / hlust.activity.

    Capture milestones that trigger emission:
        - idle:      after close() or after a failed attempt recovers
        - capturing: immediately before backend.capture() is called
        - encoding:  immediately after capture() returns, before encoder runs
        - failed:    when ScreenCaptureError, FrameEncodingError, or any
                     unrecoverable exception occurs during snapshot()

    Direction: S->C (server to client)
    Emitted by: L3 Sjón orchestrator (sjon.sjon.Sjón) via EventBus
    Frequency: at each capture milestone during snapshot(); not during idle periods

    Ref: docs/architecture/IPC_PROTOCOL.md §3 (event catalogue).
         docs/architecture/LAYER_INTERFACES.md §L3 Sjón.
    """

    type: Literal["sjon.activity"] = "sjon.activity"
    state: SjonActivityState
    """Current state of the Sjón capture pipeline."""
    timestamp: datetime
    """UTC datetime of the state transition. Use datetime.utcnow() at emission time.
    Serialised by pydantic as ISO 8601 UTC string in model_dump_json()."""


class ErrorEvent(BaseModel):
    """Emitted when any layer encounters an error worth surfacing to the user.

    'warn' level errors are informational — the ceremony continues. 'error' level
    errors indicate a failure that may require user action.

    The frontend displays these as toast notifications per the AESTHETIC.md
    error-tone motion pattern: a single slow pulse, not repeating.

    Direction: server -> client
    Emitted by: any layer via EventBus.publish()
    """

    type: Literal["error"] = "error"
    level: ErrorLevelStr
    source: str
    """Layer or module that emitted the error. Examples: 'bifrost', 'tunga', 'hlust',
    'vebond', 'lifecycle'. Used to route the error to the correct status indicator."""
    message: str
    """Human-readable description of the error. Must be user-intelligible —
    not a Python traceback or raw exception repr."""


# ------------------------------------------------------------------
# ProtocolEvent: the discriminated union of all server->client events.
# The 'type' field is the discriminator.
# ------------------------------------------------------------------

ProtocolEvent = Annotated[
    Union[
        CeremonyStateChanged,
        BifrostHealth,
        TungaActivity,
        HlustActivity,
        SjonActivity,
        AgentToken,
        AgentTurnComplete,
        ErrorEvent,
    ],
    Field(discriminator="type"),
]
"""Discriminated union of all events the server may push to the client.

Deserialize from JSON with:
    from pydantic import TypeAdapter
    _EVENT_ADAPTER = TypeAdapter(ProtocolEvent)
    event = _EVENT_ADAPTER.validate_python(json.loads(raw_message))

Serialize to JSON with:
    event_model.model_dump_json()
"""


# ==============================================================================
# Client -> Server Commands
# ==============================================================================

class LightCommand(BaseModel):
    """Initiate the Kynding -> Tengsl ceremony sequence (Light the Candle).

    The backend responds by:
        1. Transitioning lifecycle from READY to OPENING
        2. Opening L1 Bifröst (capability probe)
        3. On success: transitioning to Tengsl, emitting CeremonyStateChanged
        4. On failure: returning to READY, emitting ErrorEvent

    Direction: client -> server
    Expected response events: CeremonyStateChanged (OPENING), CeremonyStateChanged
    (tengsl on success OR kynding on failure), BifrostHealth
    """

    type: Literal["light"] = "light"


class ExtinguishCommand(BaseModel):
    """Initiate the Slokna shutdown sequence (Extinguish the Candle).

    The backend responds by:
        1. Transitioning lifecycle to SLOKNA
        2. Draining in-flight turns and tool calls (bifrost.drain_timeout_seconds)
        3. Closing Bifröst and stopping voice/vision layers
        4. Emitting CeremonyStateChanged (slokna) then CeremonyStateChanged (kynding/hvild)

    If ceremony_button_confirm is true in VebondConfig, the frontend must already
    have shown a confirmation dialog before sending this command. The backend does
    not perform a second confirmation — that is the frontend's responsibility.

    Direction: client -> server
    """

    type: Literal["extinguish"] = "extinguish"


class SendMessageCommand(BaseModel):
    """Send a user text message into the active Samræður turn loop.

    The backend injects the text as a user-role message and begins a new agent
    turn. While the turn is in progress, the backend emits AgentToken events
    for each streaming text chunk, followed by AgentTurnComplete.

    Only valid while lifecycle is Samræður (or Tengsl before first turn).
    Sending in other states results in an ErrorEvent (level='warn').

    Direction: client -> server
    Expected response events: AgentToken (N times), AgentTurnComplete
    """

    type: Literal["send_message"] = "send_message"
    text: str
    """The user's message text. Must be non-empty after stripping whitespace.
    The backend strips leading/trailing whitespace before injecting into the
    message array. Empty messages are rejected with an ErrorEvent (level='warn')."""


class CancelTurnCommand(BaseModel):
    """Abort an in-flight agent turn.

    The backend attempts to cancel the streaming HTTP request for the identified
    turn. If the turn has already completed, this is a no-op. The backend emits
    AgentTurnComplete with finish_reason='cancelled' if cancellation succeeds.

    Direction: client -> server
    """

    type: Literal["cancel_turn"] = "cancel_turn"
    turn_id: str
    """The turn_id from the AgentToken events for the turn to cancel.
    If no turn with this ID is in flight, the backend emits ErrorEvent (level='warn')."""


class ToggleSenseCommand(BaseModel):
    """Toggle a sense (Hlust, Tunga, Sjón, etc.) on or off.

    In v0.4.0 this command is RECEIVED but NOT acted upon — sense toggles affect
    config at the heretic.yaml level and require a ceremony restart to take effect.
    The backend emits an ErrorEvent (level='warn') explaining this limitation.

    In v0.4.x this command will rewrite the relevant heretic.yaml key and
    hot-reload the sense subprocess.

    Direction: client -> server
    Note: read-only in v0.4.0; functional in v0.4.x.
    """

    type: Literal["toggle_sense"] = "toggle_sense"
    sense_id: str
    """Sense identifier. Valid values: 'hlust', 'tunga', 'sjon_screen', 'sjon_webcam',
    'filesystem', 'terminal', 'browser', 'photopea', 'blender', 'vrchat',
    'agentmail', 'library'. Unknown sense_id results in ErrorEvent (level='warn')."""
    enabled: bool
    """True to enable, False to disable."""


# ------------------------------------------------------------------
# ProtocolCommand: the discriminated union of all client->server commands.
# ------------------------------------------------------------------

ProtocolCommand = Annotated[
    Union[
        LightCommand,
        ExtinguishCommand,
        SendMessageCommand,
        CancelTurnCommand,
        ToggleSenseCommand,
    ],
    Field(discriminator="type"),
]
"""Discriminated union of all commands the client may send to the server.

Deserialize from JSON with:
    from pydantic import TypeAdapter
    _COMMAND_ADAPTER = TypeAdapter(ProtocolCommand)
    command = _COMMAND_ADAPTER.validate_python(json.loads(raw_message))
"""
