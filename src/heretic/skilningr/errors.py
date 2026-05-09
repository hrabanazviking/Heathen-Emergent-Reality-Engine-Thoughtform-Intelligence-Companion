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


class ForgeServerError(ForgeError):
    """HTTP 5xx response from the Straumur REST bridge — Blender render or pipeline
    failure on the Forge (Seidr-Smidja) side.

    This is a more specific subclass of ForgeError that distinguishes a server-side
    failure (pipeline crash, render error, Blender exception) from an unreachable
    host or a client validation error.

    Raised by ForgeHttpClient._handle_response when response.status_code >= 500.

    Forge should translate this to SENSE_CONTRACTS.md code SENSE_INTERNAL_ERROR.
    Ref: docs/cartography/DATA_FLOW.md §4.11.9 F-4
    """


# ---------------------------------------------------------------------------
# Minni-specific errors (filesystem sense) [v0.6.2]
# ---------------------------------------------------------------------------

class MinniError(SkilningrError):
    """Root error for the Minni sense — local filesystem read/write.

    All errors raised within Minni are subclasses of this. Callers catching
    SkilningrError also catch MinniError. All MinniError subclasses are caught
    at the MinniSense dispatch boundary and translated into structured
    tool_result error dicts — they are never re-raised to L1 Bifröst.

    Corresponds to SENSE_CONTRACTS.md sense: "minni".
    """


class MinniSandboxViolation(MinniError):
    """A path submitted to Minni lies outside all configured allowed_roots.

    This covers path traversal (../), absolute paths to system locations,
    symlink targets that escape the sandbox, and paths that resolve to outside
    every entry in MinniConfig.allowed_roots.

    Forge should translate this to SENSE_CONTRACTS.md code PERMISSION_DENIED.
    """


class MinniFileNotFoundError(MinniError):
    """The requested file or directory does not exist at the validated path.

    Raised by Minni read_file and list_directory when the target is absent.
    Distinct from a sandbox violation — the path IS within allowed_roots, but
    the filesystem object does not exist.

    Forge should translate this to SENSE_CONTRACTS.md code INVALID_ARGUMENTS.
    """


class MinniFileTooLargeError(MinniError):
    """A file operation was refused because the file or content exceeds the
    configured size limit (MinniConfig.max_read_bytes or max_write_bytes).

    Raised before any I/O begins so that no partial read/write occurs.

    Forge should translate this to SENSE_CONTRACTS.md code INVALID_ARGUMENTS.
    """


class MinniPermissionError(MinniError):
    """The OS refused a filesystem operation due to permission restrictions.

    Raised when PermissionError / OSError is caught from pathlib operations
    after sandbox validation has already passed. The path is within allowed_roots
    but the OS user running HERETIC lacks the necessary permissions.

    Forge should translate this to SENSE_CONTRACTS.md code PERMISSION_DENIED.
    """


# ---------------------------------------------------------------------------
# Skepja-specific errors (terminal sense) [v0.6.2]
# ---------------------------------------------------------------------------

class SkepjaError(SkilningrError):
    """Root error for the Skepja sense — sandboxed shell command execution.

    All errors raised within Skepja are subclasses of this. Callers catching
    SkilningrError also catch SkepjaError. All SkepjaError subclasses are caught
    at the SkepjaSense dispatch boundary and translated into structured
    tool_result error dicts — they are never re-raised to L1 Bifröst.

    Corresponds to SENSE_CONTRACTS.md sense: "skepja".
    """


class CommandNotAllowedError(SkepjaError):
    """The requested command's executable is not in the operator allowlist.

    Raised when sandbox.command_in_allowlist() returns False. The command was
    rejected before any subprocess was spawned — no execution occurred.

    Forge should translate this to SENSE_CONTRACTS.md code PERMISSION_DENIED.
    """


class CommandParseError(SkepjaError):
    """The command string could not be parsed by shlex.split().

    Raised when the command string contains malformed shell quoting or other
    syntax that shlex rejects. No execution occurred.

    Forge should translate this to SENSE_CONTRACTS.md code INVALID_ARGUMENTS.
    """


class CommandTimeoutError(SkepjaError):
    """A subprocess invocation timed out before completing.

    The subprocess was started but did not finish within SkepjaConfig.timeout_seconds.
    The process is terminated after timeout. Partial output up to the timeout
    may be available in the error detail.

    Forge should translate this to SENSE_CONTRACTS.md code SENSE_TIMEOUT.
    """


class CommandExecutionError(SkepjaError):
    """A subprocess completed but returned a non-zero exit code.

    Raised when subprocess.run() completes (not a timeout) and the exit code
    indicates failure. The error detail includes the exit code, stdout, and stderr
    up to the configured max_output_bytes cap.

    Forge should translate this to SENSE_CONTRACTS.md code SENSE_INTERNAL_ERROR.
    """


# ---------------------------------------------------------------------------
# Leið-specific errors (HTTP fetch sense) [v0.6.2]
# ---------------------------------------------------------------------------

class LeidError(SkilningrError):
    """Root error for the Leið sense — sandboxed HTTP fetch.

    All errors raised within Leið are subclasses of this. Callers catching
    SkilningrError also catch LeidError. All LeidError subclasses are caught
    at the LeidSense dispatch boundary and translated into structured
    tool_result error dicts — they are never re-raised to L1 Bifröst.

    Corresponds to SENSE_CONTRACTS.md sense: "leid".
    """


class UrlNotAllowedError(LeidError):
    """The requested URL does not match any pattern in url_allowlist_patterns.

    Raised when sandbox.url_matches_allowlist() returns False. No HTTP request
    was sent — the URL was rejected at the allowlist gate.

    Forge should translate this to SENSE_CONTRACTS.md code PERMISSION_DENIED.
    """


class LeidTimeoutError(LeidError):
    """An HTTP request timed out before a response was received.

    The connection or response did not complete within LeidConfig.timeout_seconds.
    The remote host may still be processing the request.

    Forge should translate this to SENSE_CONTRACTS.md code SENSE_TIMEOUT.
    """


class LeidResponseTooLargeError(LeidError):
    """The HTTP response body exceeds LeidConfig.max_response_bytes.

    Raised when the response Content-Length header or streaming body size
    exceeds the configured cap. The connection is closed immediately; no
    partial content is returned to the agent.

    Forge should translate this to SENSE_CONTRACTS.md code INVALID_ARGUMENTS.
    """


class LeidHttpError(LeidError):
    """The HTTP response carried a 4xx or 5xx status code.

    Raised by the Leið client when the fetch succeeds at the transport level
    but the server indicates an application-level failure. The status code and
    response body (truncated to max_response_bytes) are available in the detail.

    Forge should translate 4xx to INVALID_ARGUMENTS and 5xx to SENSE_INTERNAL_ERROR.
    """


class LeidConnectionError(LeidError):
    """A network-level error prevented the HTTP request from being sent or received.

    Covers DNS resolution failure, TCP connection refused, TLS handshake failure,
    and any other transport-level error that is not a timeout. The underlying
    exception message is included in the error detail.

    Forge should translate this to SENSE_CONTRACTS.md code EXTERNAL_APP_UNAVAILABLE.
    """
