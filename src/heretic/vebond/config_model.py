"""
Vébond config model — typed configuration for the L4 WebSocket server layer.

This module is the canonical definition of VebondConfig. It is imported by
heretic.grunnr.config.HereticConfig so that all vebond settings live in one
place and are self-contained within the vebond package.

heretic.grunnr.config has no reverse dependency on heretic.vebond beyond this
import — the direction is safe and introduces no circular dependency.

Config keys mirror the vebond: YAML block in LAYER_INTERFACES.md §L4.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VebondConfig:
    """L4 Vébond — complete configuration: both UI display and WebSocket server.

    All keys correspond to the vebond: YAML block documented in
    docs/architecture/LAYER_INTERFACES.md §L4 Vébond.

    This dataclass is the single authoritative definition. heretic.grunnr.config
    imports and re-exports it so that HereticConfig.vebond carries the full schema.

    Fields are split by concern:
        - UI display settings (theme, frame thumbnail, etc.)
        - WebSocket server settings (ws_host, ws_port, etc.)

    The two concerns coexist in one struct because they share one YAML block
    (vebond:) and one owner (L4 Vébond). Splitting into two sub-dataclasses would
    create unnecessary nesting in heretic.yaml for what is already a coherent unit.
    """

    # ------------------------------------------------------------------
    # UI display settings (operator-facing; existed before v0.4)
    # ------------------------------------------------------------------

    theme: str = "dark_norse"
    """Visual theme identifier. dark_norse is the only supported value in v0.4.
    Future: custom theme support deferred to v0.5+."""

    show_frame_thumbnail: bool = False
    """Show latest Sjón frame as a thumbnail in the UI layer-status panel.
    Off by default — opt-in to avoid screen burn and privacy concerns."""

    show_agent_text_stream: bool = True
    """Stream agent text tokens into the chat panel as they arrive.
    If False, only completed turns are displayed."""

    ceremony_button_confirm: bool = True
    """Require a confirmation step before Extinguish is accepted.
    Prevents accidental ceremony termination."""

    # ------------------------------------------------------------------
    # WebSocket server settings (new in v0.4)
    # ------------------------------------------------------------------

    ws_host: str = "127.0.0.1"
    """Host address to bind the WebSocket server.

    Default is 127.0.0.1 (loopback only). The browser frontend and Tauri WebView
    both run on the same machine and connect over localhost — no external bind
    is needed or safe for v0.4.

    To bind to all interfaces (e.g. for remote dev tooling) set allow_remote_bind:
    true AND explicitly override this to 0.0.0.0. Both conditions are required;
    allow_remote_bind alone does not change the bind address.

    Never bind to 0.0.0.0 without understanding the security implications."""

    ws_port: int = 8642
    """TCP port for the WebSocket server.

    8642 is the HERETIC Vébond port by convention. The frontend vite.config.ts
    proxy targets this port by default. Set vebond.ws_port in heretic.yaml to
    override if 8642 is occupied."""

    allow_remote_bind: bool = False
    """Gate that must be explicitly set true before a non-loopback ws_host is
    accepted. Serves as a double-confirmation that the operator understands they
    are exposing the IPC surface to the network.

    In v0.4.0 the IPC surface has no authentication — it is designed for
    localhost-only use (Tauri WebView as the sole client). Enabling remote bind
    without adding auth (planned for v0.4.x) is a security concern. The operator
    must set this true AND set ws_host to a non-loopback address; otherwise
    VebondConfig.__post_init__ raises VebondConfigError."""

    max_message_size_bytes: int = 1_048_576
    """Maximum raw WebSocket message size in bytes (default 1 MiB).

    Messages larger than this limit are rejected with a MessageTooLargeError.
    Prevents oversized payloads from consuming excessive memory or causing
    denial-of-service conditions. Operators expecting large tool result payloads
    may increase this, but should do so deliberately."""

    heartbeat_interval_seconds: int = 30
    """Interval between WebSocket heartbeat pings from server to client.

    The server sends a ping frame every N seconds on idle connections. If the
    client does not pong within connection_timeout_seconds, the connection is
    considered dead and cleaned up."""

    connection_timeout_seconds: int = 60
    """Maximum seconds a connected client may be silent (no pong received) before
    the server drops the connection.

    This is distinct from the Bifröst heartbeat — this governs the WebSocket
    transport layer between browser and Python backend, not the agent connection."""

    def __post_init__(self) -> None:
        """Validate config values on construction.

        Raises:
            VebondConfigError: if any invariant is violated.
        """
        # Import here to avoid circular reference at module load time.
        # errors.py does not import config_model.py.
        from heretic.vebond.errors import VebondConfigError

        if self.ws_port < 1 or self.ws_port > 65535:
            raise VebondConfigError(
                f"vebond.ws_port must be in range 1-65535; got {self.ws_port}"
            )

        loopback_prefixes = ("127.", "::1", "localhost")
        is_loopback = any(self.ws_host.startswith(p) for p in loopback_prefixes)
        if not is_loopback and not self.allow_remote_bind:
            raise VebondConfigError(
                f"vebond.ws_host is set to {self.ws_host!r} (non-loopback) but "
                f"vebond.allow_remote_bind is False. "
                f"To bind the WebSocket server to a non-loopback address you must "
                f"explicitly set vebond.allow_remote_bind: true in heretic.yaml. "
                f"See docs/architecture/IPC_PROTOCOL.md §Authentication for context."
            )

        if self.max_message_size_bytes < 1024:
            raise VebondConfigError(
                f"vebond.max_message_size_bytes must be at least 1024 bytes; "
                f"got {self.max_message_size_bytes}"
            )

        if self.heartbeat_interval_seconds < 1:
            raise VebondConfigError(
                f"vebond.heartbeat_interval_seconds must be >= 1; "
                f"got {self.heartbeat_interval_seconds}"
            )

        if self.connection_timeout_seconds < self.heartbeat_interval_seconds:
            raise VebondConfigError(
                f"vebond.connection_timeout_seconds ({self.connection_timeout_seconds}) "
                f"must be >= heartbeat_interval_seconds ({self.heartbeat_interval_seconds}). "
                f"A connection cannot time out faster than it is expected to heartbeat."
            )
