"""
Vébond error hierarchy — all errors raised by the L4 WebSocket server layer.

Error taxonomy:
    VebondError                  — root; all vebond errors are subclasses
      VebondConfigError          — invalid VebondConfig value at construction
      VebondBindError            — could not bind the WebSocket server to the configured address
      VebondAuthError            — authentication failure (reserved for v0.4.x token auth)
      ProtocolError              — malformed or unrecognised IPC message received
        MessageTooLargeError     — incoming message exceeds max_message_size_bytes

All error classes carry a human-readable message. No error class stores secrets
(tokens, keys) in its attributes — those are logged at the call site if needed.
"""

from __future__ import annotations


class VebondError(Exception):
    """Root error for all L4 Vébond / WebSocket server failures.

    Catch this class to handle any vebond error uniformly. Catch a specific
    subclass for finer-grained handling. Never raise VebondError directly;
    always raise a concrete subclass so that callers can distinguish root cause.
    """


class VebondConfigError(VebondError):
    """Raised when VebondConfig contains an invalid or inconsistent value.

    This is raised in VebondConfig.__post_init__ before the server starts.
    It signals that the operator's heretic.yaml vebond: block needs correction.

    Example conditions:
        - ws_port outside 1-65535
        - non-loopback ws_host without allow_remote_bind: true
        - max_message_size_bytes < 1024
        - connection_timeout_seconds < heartbeat_interval_seconds
    """


class VebondBindError(VebondError):
    """Raised when the WebSocket server cannot bind to the configured address.

    This is a runtime error — config may be valid but the port is already in use,
    or the host interface does not exist on this machine, or OS permissions prevent
    the bind (e.g. port < 1024 without elevated privileges on Linux).

    Forge should map this to a user-visible error message suggesting to change
    vebond.ws_port in heretic.yaml or free the conflicting port.
    """


class VebondAuthError(VebondError):
    """Reserved for v0.4.x token authentication.

    In v0.4.0 the WebSocket server is localhost-only with no auth layer.
    This class exists so that v0.4.x can add bearer token validation without
    changing the error hierarchy. Forge should raise this when a connecting
    client presents an invalid or missing token (once auth is implemented).
    """


class ProtocolError(VebondError):
    """Raised when a received IPC message cannot be decoded or is structurally invalid.

    This covers:
        - JSON parse failure on the raw WebSocket message
        - Missing required fields (e.g. no 'type' discriminator)
        - Unknown 'type' value that matches no known ProtocolCommand variant

    On receiving a ProtocolError, the server should:
        1. Log the raw message at debug level (not info — could contain user text)
        2. Send an error event back to the client with level='warn'
        3. Continue serving; do not close the connection for a single bad message
    """


class MessageTooLargeError(ProtocolError):
    """Raised when an incoming WebSocket message exceeds max_message_size_bytes.

    Carries the actual size so it can be included in the error response.
    The server should reject the message and send an error event, but keep the
    connection open — oversized messages are a client bug, not a fatal condition.
    """

    def __init__(self, actual_bytes: int, limit_bytes: int) -> None:
        self.actual_bytes = actual_bytes
        self.limit_bytes = limit_bytes
        super().__init__(
            f"WebSocket message too large: {actual_bytes} bytes exceeds "
            f"limit of {limit_bytes} bytes. "
            f"Adjust vebond.max_message_size_bytes in heretic.yaml if this is intentional."
        )
