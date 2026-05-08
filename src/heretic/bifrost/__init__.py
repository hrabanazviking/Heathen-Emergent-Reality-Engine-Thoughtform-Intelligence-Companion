"""
L1 Bifröst — the Agent Connection.

Old Norse *Bifröst*: the shimmering bridge of the gods — the only passage between
Ásgarðr and Midgard. Here: the Tailscale-aware OpenAI-compatible connection layer,
the bridge between the remote spirit and the local body.

Bifröst is the one and only seam between HERETIC and the inhabiting agent. No other
layer speaks directly to the agent endpoint. All agent communication flows through
the BifrostClient interface defined here.

Bifröst owns:
    - Agent endpoint URL and Bearer token
    - Connection state machine (DISCONNECTED → CONNECTING → CONNECTED → RECOVERING)
    - Retry logic and exponential backoff
    - Heartbeat management
    - Message queue (session-only; zeroed on Slokna)
    - Tool call dispatch routing toward L5 Skilningr
    - Capability flag registry for the current ceremony

Bifröst never controls:
    - Agent memory or persona
    - System prompt contents (that is the ceremony's concern, injected at first turn)
    - What senses actually do when a tool call arrives
    - Voice/vision data streams (it receives them as inputs, does not generate them)

Ref:
    docs/NAMING.md §Layers — Bifröst
    docs/architecture/LAYER_INTERFACES.md §L1 Bifröst
    docs/architecture/AGENT_AGNOSTIC_PROTOCOL.md
"""

from __future__ import annotations

from heretic.bifrost.client import BifrostClient, OpenAICompatClient
from heretic.bifrost.config_model import BifrostConfig
from heretic.bifrost.errors import (
    BifrostError,
    BifrostConnectionError,
    BifrostAuthError,
    BifrostTimeoutError,
)
from heretic.bifrost.tailscale import TailscaleAwareness

__all__ = [
    "BifrostClient",
    "OpenAICompatClient",
    "BifrostConfig",
    "BifrostError",
    "BifrostConnectionError",
    "BifrostAuthError",
    "BifrostTimeoutError",
    "TailscaleAwareness",
]
