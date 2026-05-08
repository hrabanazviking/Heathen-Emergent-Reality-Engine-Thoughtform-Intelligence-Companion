"""
Skilningr error hierarchy.

All errors that cross the Skilningr boundary are subclasses of SkilningrError.
Callers may catch SkilningrError to handle any Skilningr failure, or catch the
specific subclass when finer-grained handling is needed.

Design rule: these errors are NEVER propagated to the agent as Python exceptions.
They are caught at the dispatch boundary and translated into a tool_result with
error JSON per SENSE_CONTRACTS.md §3.

Ref: docs/architecture/LAYER_INTERFACES.md §L5 Skilningr
     docs/architecture/SENSE_CONTRACTS.md §3 Error Taxonomy
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

class SkilningrError(Exception):
    """Root error for the entire Skilningr sense hub layer.

    All errors raised within Skilningr are subclasses of this. Callers who want
    to catch any Skilningr failure without distinguishing the cause should catch
    this class.
    """


# ---------------------------------------------------------------------------
# Dispatcher-level errors
# ---------------------------------------------------------------------------

class SenseUnavailableError(SkilningrError):
    """The requested sense is disabled, not registered, or its client is down.

    Corresponds to SENSE_CONTRACTS.md error code: SENSE_UNAVAILABLE.
    The dispatcher returns a structured error tool_result — does not re-raise.
    """


class ToolDispatchError(SkilningrError):
    """A tool call could not be dispatched: unknown tool name, routing failure,
    malformed arguments, or an unclassified dispatch error.

    Corresponds to SENSE_CONTRACTS.md error code: SENSE_INTERNAL_ERROR when
    the cause is unknown, or INVALID_ARGUMENTS when arguments are malformed.
    """


class AuthError(SkilningrError):
    """Bearer token is missing, malformed, or was rejected by the remote daemon.

    Corresponds to HTTP 401 from the Brúarhönd daemon. This error is raised
    internally and is translated into a structured tool_result error by the
    dispatcher — it is never surfaced as a Python exception to L1 Bifröst.
    """


# ---------------------------------------------------------------------------
# Smiðja-specific errors (Brúarhönd HTTP client)
# ---------------------------------------------------------------------------

class SmidjaError(SkilningrError):
    """Root error for the Smiðja sense and its Brúarhönd HTTP client.

    Subclass of SkilningrError so callers catching SkilningrError also catch
    all Smiðja failures. Subclass this for Brúarhönd-specific failure modes.
    """


class BrunhandUnreachableError(SmidjaError):
    """The Brúarhönd daemon host is not reachable at the configured address:port.

    Possible causes: daemon not running, Tailscale down, wrong IP/hostname,
    firewall blocking the port.

    Forge should translate this to SENSE_CONTRACTS.md code EXTERNAL_APP_UNAVAILABLE
    in the tool_result error JSON.
    """


class BrunhandTimeoutError(SmidjaError):
    """A request to the Brúarhönd daemon timed out.

    The request was sent but no response arrived within request_timeout_seconds
    (configured in SmidjaConfig). The daemon may still be executing the primitive.

    Forge should translate this to SENSE_CONTRACTS.md code SENSE_TIMEOUT.
    """


class BrunhandAuthError(SmidjaError):
    """Bearer token was rejected by the Brúarhönd daemon (HTTP 401).

    The token stored in the env var named by SmidjaConfig.token_env is invalid
    or does not match the daemon's expected token.

    Distinct from AuthError (which is the Skilningr-level auth error); this is
    specifically the HTTP-layer rejection from the daemon.

    Forge should translate this to SENSE_CONTRACTS.md code PERMISSION_DENIED.
    """


class BrunhandSessionLockedError(SmidjaError):
    """The Brúarhönd daemon returned HTTP 423 — an active session is in progress.

    The daemon accepts only one concurrent session. A second connection attempt
    while a session is active returns 423. The client should surface this to the
    agent as a structured tool error rather than retrying immediately.

    Forge should translate this to a SENSE_INTERNAL_ERROR with a clear message.
    """


# ---------------------------------------------------------------------------
# Smiðja-specific errors (Forge / Straumur HTTP client)
# ---------------------------------------------------------------------------

class ForgeError(SmidjaError):
    """Root error for the Forge half of the Smiðja sense (ForgeHttpClient / Straumur).

    Subclass of SmidjaError so callers catching SmidjaError also catch all
    Forge failures. All ForgeError subclasses are caught at the SmidjaSense
    dispatch boundary and translated into structured tool_result error dicts —
    they are never re-raised to L1 Bifröst.

    The Forge half wraps Seidr-Smidja's Straumur REST bridge (headless Blender
    pipeline). It is architecturally independent from Brúarhönd: both halves
    live under the Smiðja sense but open, close, and fail independently.
    """


class ForgeUnreachableError(ForgeError):
    """The Seidr-Smidja Straumur REST bridge is not reachable at the configured endpoint.

    Possible causes: Seidr-Smidja not running, wrong endpoint URL, firewall.
    Default Straumur port: 8765 (localhost-only by default).

    Forge should translate this to SENSE_CONTRACTS.md code EXTERNAL_APP_UNAVAILABLE.
    """


class ForgeTimeoutError(ForgeError):
    """A request to the Straumur REST bridge timed out.

    The request was sent but no response arrived within ForgeConfig.request_timeout_seconds
    (default 120 s — Blender renders are slow). The Straumur server may still be
    processing the build.

    Forge should translate this to SENSE_CONTRACTS.md code SENSE_TIMEOUT.
    """


class ForgeValidationError(ForgeError):
    """The Straumur server rejected the request body (HTTP 422) or the
    ForgeHttpClient detected an invalid argument before sending.

    Common causes:
        - loom_spec missing required fields (base_asset_id, etc.)
        - vrm_path submitted to inspect is outside allow-listed roots (H-004)
        - vrm_path extension is not .vrm

    Forge should translate this to SENSE_CONTRACTS.md code INVALID_ARGUMENTS.
    """
