"""
Bifröst error hierarchy.

All errors raised by L1 Bifröst are subclasses of BifrostError. This hierarchy lets
callers catch just BifrostError when they do not care about the specific cause, or
catch a leaf class when they need to handle one case specially (e.g., surface a
BIFROST_AUTH_FAILED message in the UI without retrying).

Error code constants match the codes documented in LAYER_INTERFACES.md §L1 Error model:
    BIFROST_AUTH_FAILED
    BIFROST_TIMEOUT
    BIFROST_UNREACHABLE
    BIFROST_PROBE_FAILED
    BIFROST_TOOL_CALL_UNKNOWN
    BIFROST_PROTOCOL_ERROR

Ref:
    docs/architecture/LAYER_INTERFACES.md §L1 Bifröst — Error model
"""

from __future__ import annotations

from typing import Optional


class BifrostError(RuntimeError):
    """Root of the Bifröst error hierarchy.

    All errors from L1 Bifröst are instances of this class or its subclasses.
    Carries an optional ``code`` string that maps to the BIFROST_* constants
    in LAYER_INTERFACES.md.
    """

    def __init__(self, message: str, code: Optional[str] = None) -> None:
        super().__init__(message)
        self.code = code


class BifrostConnectionError(BifrostError):
    """The agent endpoint is unreachable or the connection was lost.

    Corresponds to BIFROST_UNREACHABLE in LAYER_INTERFACES.md.
    Raised when Tailscale is not active or the HTTP connection is refused.
    The Lifecycle transitions to RECOVERING on this error.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, code="BIFROST_UNREACHABLE")


class BifrostAuthError(BifrostError):
    """The agent rejected the Bearer token (HTTP 401 or 403).

    Corresponds to BIFROST_AUTH_FAILED in LAYER_INTERFACES.md.
    Not retried automatically — the user must correct their API key.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, code="BIFROST_AUTH_FAILED")


class BifrostTimeoutError(BifrostError):
    """The agent did not respond within the configured timeout.

    Corresponds to BIFROST_TIMEOUT in LAYER_INTERFACES.md.
    Retried per the bifrost.max_retries policy.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, code="BIFROST_TIMEOUT")


class BifrostProbeError(BifrostError):
    """The capability probe did not complete within connect_timeout_seconds.

    Corresponds to BIFROST_PROBE_FAILED in LAYER_INTERFACES.md.
    On probe failure, HERETIC continues with conservative capability defaults:
    ?tool_use = False, ?vision_in = False, ?streaming = False.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, code="BIFROST_PROBE_FAILED")


class BifrostToolCallUnknownError(BifrostError):
    """The agent called a tool that is not in the active tool registry.

    Corresponds to BIFROST_TOOL_CALL_UNKNOWN in LAYER_INTERFACES.md.
    A tool_error with code 'tool_not_found' is returned to the agent.
    HERETIC does not crash — the turn continues with the error result.
    """

    def __init__(self, tool_name: str) -> None:
        super().__init__(
            f"Agent called unknown tool: {tool_name!r}. "
            f"Tool is not registered in the active sense hub.",
            code="BIFROST_TOOL_CALL_UNKNOWN",
        )
        self.tool_name = tool_name


class BifrostProtocolError(BifrostError):
    """The agent response was malformed and could not be parsed.

    Corresponds to BIFROST_PROTOCOL_ERROR in LAYER_INTERFACES.md.
    The full response is logged at DEBUG level. The current turn is aborted.
    """

    def __init__(self, message: str, raw_response: Optional[str] = None) -> None:
        super().__init__(message, code="BIFROST_PROTOCOL_ERROR")
        self.raw_response = raw_response
