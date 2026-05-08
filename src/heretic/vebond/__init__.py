"""
heretic.vebond — L4 Vébond / Eldahús (the Summoning Circle)

The fire-room of HERETIC. This layer is the WebSocket IPC bridge between the
Python ceremony backend and the React frontend (Eldahús). It is purely
presentational from the ceremony's perspective: it receives state events from
all inner layers and emits user commands back into the lifecycle.

Layer position in the HERETIC stack:
    L0 Grunnr (foundation)
    L1 Bifrost (agent connection)
    L2 Rodd (voice)
    L3 Sjon (vision)
  > L4 Vebond (this layer — UI / IPC surface)
    L5 Skilningr (sense hub)

What this layer owns:
    - VebondConfig — WebSocket server + UI display configuration
    - EventBus — in-process pub/sub bus connecting inner layers to connected clients
    - WebSocketServer — FastAPI app with /ws and /health endpoints
    - Protocol schema — ProtocolEvent and ProtocolCommand typed models (pydantic v2)
    - Error hierarchy — VebondError and all subclasses

What this layer never controls:
    - Agent conversation content (L1 Bifrost)
    - Audio DSP or mic capture (L2 Rodd)
    - Screen capture (L3 Sjon)
    - MCP tool routing or sense subprocess lifecycle (L5 Skilningr)

Public API (re-exported below):
    VebondConfig          — import for configuration
    EventBus              — import for the event bus
    WebSocketServer       — import to start the IPC server
    ProtocolEvent         — import for the full event union type
    ProtocolCommand       — import for the full command union type
    CeremonyStateChanged  — import for the specific event model
    BifrostHealth
    TungaActivity
    HlustActivity
    AgentToken
    AgentTurnComplete
    ErrorEvent
    LightCommand
    ExtinguishCommand
    SendMessageCommand
    CancelTurnCommand
    ToggleSenseCommand
    VebondError           — import for the error hierarchy root
    VebondConfigError
    VebondBindError
    VebondAuthError
    ProtocolError
    MessageTooLargeError

Canonical reference: docs/architecture/LAYER_INTERFACES.md §L4 Vébond
IPC schema reference: docs/architecture/IPC_PROTOCOL.md
"""

from heretic.vebond.config_model import VebondConfig
from heretic.vebond.errors import (
    VebondError,
    VebondConfigError,
    VebondBindError,
    VebondAuthError,
    ProtocolError,
    MessageTooLargeError,
)
from heretic.vebond.serve import EventBus, WebSocketServer

# Protocol models — pydantic v2 required for these imports.
# If pydantic is not installed, importing heretic.vebond.protocol will raise
# ImportError with an install hint. We do NOT import protocol at __init__ level
# unconditionally to preserve the ability to import VebondConfig and errors
# without pydantic installed (e.g. in test environments that only test config).
# Callers that need the typed models import them explicitly from heretic.vebond.protocol.
try:
    from heretic.vebond.protocol import (
        ProtocolEvent,
        ProtocolCommand,
        CeremonyStateChanged,
        BifrostHealth,
        TungaActivity,
        HlustActivity,
        AgentToken,
        AgentTurnComplete,
        ErrorEvent,
        LightCommand,
        ExtinguishCommand,
        SendMessageCommand,
        CancelTurnCommand,
        ToggleSenseCommand,
    )
    _PROTOCOL_AVAILABLE = True
except ImportError:
    # pydantic not installed — config and error imports still work.
    # Any code that needs ProtocolEvent/ProtocolCommand must import from
    # heretic.vebond.protocol directly and handle the ImportError itself.
    _PROTOCOL_AVAILABLE = False


__all__ = [
    # Config
    "VebondConfig",
    # Server
    "EventBus",
    "WebSocketServer",
    # Errors
    "VebondError",
    "VebondConfigError",
    "VebondBindError",
    "VebondAuthError",
    "ProtocolError",
    "MessageTooLargeError",
    # Protocol (pydantic required)
    "ProtocolEvent",
    "ProtocolCommand",
    "CeremonyStateChanged",
    "BifrostHealth",
    "TungaActivity",
    "HlustActivity",
    "AgentToken",
    "AgentTurnComplete",
    "ErrorEvent",
    "LightCommand",
    "ExtinguishCommand",
    "SendMessageCommand",
    "CancelTurnCommand",
    "ToggleSenseCommand",
    "_PROTOCOL_AVAILABLE",
]
