"""
Bifröst config model — dataclass mirroring the ``bifrost:`` YAML subtree.

This module defines the BifrostConfig dataclass that is populated by Grunnr's
config loader from the ``bifrost:`` section of heretic.yaml.

BifrostConfig is also re-exported from ``heretic.grunnr.config.HereticConfig.bifrost``
so callers do not need to import it separately from both modules. The canonical type
definition lives here (in the bifrost package) to keep L1 self-contained; Grunnr's
config.py imports it from here.

All default values match the reference config block in LAYER_INTERFACES.md §L1.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TailscaleOptions:
    """Tailscale routing options inside the bifrost: block."""
    prefer: bool = True
    """Prefer Tailscale 100.64.0.0/10 routes when resolving the agent endpoint."""

    fallback_to_direct: bool = True
    """Fall back to the raw endpoint URL if Tailscale is not reachable."""


@dataclass
class BifrostConfig:
    """L1 Bifröst connection settings.

    Mirrors the ``bifrost:`` YAML block in heretic.yaml.
    All defaults match the reference block in LAYER_INTERFACES.md §L1.

    The api_key field holds an ${ENV_VAR} reference string. Grunnr's
    paths.resolve_env_var() expands it at runtime — never stored plaintext.
    """
    endpoint: str = "http://100.101.39.30:8643/v1"
    """OpenAI-compatible agent base URL."""

    api_key: str = "${HERETIC_AGENT_KEY}"
    """Env-var reference. Resolved by paths.resolve_env_var() before use."""

    model: str = "coding"
    """Model name sent in every /v1/chat/completions request body."""

    timeout_seconds: int = 30
    """Seconds to wait for an agent response before BIFROST_TIMEOUT."""

    stream_timeout_seconds: int = 120
    """Seconds to wait for a streaming response to complete."""

    connect_timeout_seconds: int = 15
    """Seconds for the capability probe before BIFROST_PROBE_TIMEOUT."""

    max_retries: int = 3
    """Retry attempts for reconnection (RECOVERING state)."""

    backoff_seconds: list[int] = field(default_factory=lambda: [2, 5, 15])
    """Wait durations before retry 1, 2, 3. Length must equal max_retries."""

    heartbeat_interval_seconds: int = 30
    """How often to send a keepalive probe to the agent."""

    heartbeat_miss_threshold: int = 3
    """Consecutive missed heartbeats before entering RECOVERING."""

    heartbeat_enabled: bool = True
    """Disable for cloud agents to avoid billing on keepalive pings."""

    stream: bool = True
    """Enable SSE streaming responses."""

    max_tokens: int = 127000
    """Per RULES.AI.md: keep token settings high."""

    max_parallel_tool_calls: int = 4
    """Maximum concurrent tool calls dispatched to L5 Skilningr per turn."""

    max_tool_call_rounds: int = 20
    """Maximum tool-call rounds before the turn is considered stuck and aborted."""

    drain_timeout_seconds: int = 10
    """Slokna drain window: in-flight tool calls are allowed this many seconds."""

    input_queue_depth: int = 10
    """Maximum queued voice/text inputs while a turn is in progress."""

    inject_context_on_connect: bool = False
    """If True, inject a system message at ceremony start announcing available senses."""

    tailscale: TailscaleOptions = field(default_factory=TailscaleOptions)
    """Tailscale routing preferences."""

    vision_in: bool = True
    """If True and ?vision_in capability confirmed, inject frames into agent turns."""
