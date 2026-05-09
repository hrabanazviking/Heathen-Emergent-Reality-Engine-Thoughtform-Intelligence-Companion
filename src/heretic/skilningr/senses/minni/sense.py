"""
MinniSense — L5.1 Minni sense orchestrator.

MinniSense is the boundary between ToolDispatcher and MinniClient.
It owns:
    - Sense lifecycle (open/close)
    - Tool call routing (dispatch_tool_call routes to the MinniClient method)
    - Result encoding (success payloads and errors into OpenAI tool_result format)
    - Event emission (SenseToolCall events via optional event_emitter)

It does NOT own:
    - Filesystem I/O (MinniClient)
    - Sandbox validation (heretic.skilningr.sandbox)
    - Tool schema definitions (tools.py MINNI_TOOL_DEFINITIONS)
    - Config (MinniConfig, passed in from HereticConfig.skilningr.minni)
    - Agent message routing (ToolDispatcher)

LIFECYCLE:
    MinniSense is instantiated once per ceremony. open() verifies the client
    can operate (all allowed_roots exist and are accessible). close() is a no-op
    in v0.6.2 (no persistent connection to close). Both honour the Smiðja
    pattern: never raise to the caller; degrade gracefully.

Design:
    dispatch_tool_call NEVER raises — all errors return structured tool_result dicts.

Ref: docs/architecture/LAYER_INTERFACES.md §L5 Skilningr
     docs/architecture/SENSE_CONTRACTS.md §1 (lifecycle) §3 (error format)
     src/heretic/skilningr/senses/minni/INTERFACE.md
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any, Callable

from heretic.skilningr.config_model import MinniConfig
from heretic.skilningr.senses.minni.client import MinniClient
from heretic.skilningr.senses.minni.errors import MinniError
from heretic.skilningr.senses.minni.tools import MINNI_TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

# Valid tool names for routing — derived from MINNI_TOOL_DEFINITIONS at import time
_MINNI_TOOL_NAMES: frozenset[str] = frozenset(
    t["function"]["name"] for t in MINNI_TOOL_DEFINITIONS
)


class MinniSense:
    """L5.1 Minni sense — sandboxed filesystem tool surface.

    Registered in ToolDispatcher under the prefix "minni". Routes any tool_call
    whose name starts with "minni." to MinniClient.

    Usage:
        config = heretic_config.skilningr.minni
        client = MinniClient(config)
        sense  = MinniSense(config, client)
        await sense.open()
        result = await sense.dispatch_tool_call(tool_call_dict)
        await sense.close()
    """

    def __init__(
        self,
        config: MinniConfig,
        client: MinniClient,
        log: logging.Logger | None = None,
        event_emitter: Callable | None = None,
    ) -> None:
        """Initialise the Minni sense.

        Args:
            config:        MinniConfig from HereticConfig.skilningr.minni.
            client:        MinniClient — the sandboxed filesystem operator.
            log:           Optional logger instance.
            event_emitter: Optional callable for SenseToolCall IPC events.
                           Signature: event_emitter(event: SenseToolCall) -> None.
        """
        self._config = config
        self._client = client
        self._log = log if log is not None else logging.getLogger(__name__)
        self._event_emitter = event_emitter
        self._is_open: bool = False

    @property
    def is_available(self) -> bool:
        """True if the sense is enabled AND open.

        ToolDispatcher checks this before calling dispatch_tool_call.
        """
        return self._config.enabled and self._is_open

    async def open(self) -> None:
        """Open the Minni sense — verify sandbox roots are accessible.

        Called at ceremony start (Kynding). Does not raise — all exceptions
        are caught and logged; the ceremony continues with is_available=False
        if open fails.

        In v0.6.2 the client is a stub (NotImplementedError bodies). The sense
        is marked open if enabled=True, as the sandbox validation paths are
        testable even without Forge implementation.
        """
        if not self._config.enabled:
            self._is_open = False
            return

        try:
            # Forge Wave 2: client.open() will verify allowed_roots exist.
            # For now: sense opens successfully if enabled=True.
            self._is_open = True
            self._log.info(
                "Minni sense opened — %d allowed root(s) configured.",
                len(self._config.allowed_roots),
            )
        except Exception as exc:
            self._log.error(
                "Minni sense failed to open (unexpected): %s", exc, exc_info=True
            )
            self._is_open = False

    async def close(self) -> None:
        """Close the Minni sense and release any resources.

        Idempotent. No persistent connection to close in v0.6.2.
        """
        self._is_open = False

    @property
    def tool_definitions(self) -> list[dict]:
        """Return the OpenAI tool schemas when the sense is enabled.

        Returns:
            MINNI_TOOL_DEFINITIONS if config.enabled, else empty list.
        """
        return list(MINNI_TOOL_DEFINITIONS) if self._config.enabled else []

    async def dispatch_tool_call(self, tool_call: dict) -> dict:
        """Route a tool_call to the appropriate MinniClient method.

        NEVER raises. All errors are caught and returned as structured
        tool_result dicts with SENSE_CONTRACTS.md error JSON in content.

        Args:
            tool_call: OpenAI-format tool_call dict.

        Returns:
            OpenAI tool_result dict.
        """
        call_id: str = tool_call.get("id", "unknown")
        fn_block = tool_call.get("function", {})
        tool_name: str = fn_block.get("name", "")
        args_str: str = fn_block.get("arguments", "") or "{}"

        # Parse arguments
        try:
            args: dict[str, Any] = json.loads(args_str)
        except json.JSONDecodeError as exc:
            return _error_tool_result(
                call_id, tool_name, "INVALID_ARGUMENTS",
                f"Could not parse tool call arguments as JSON: {exc}",
            )

        t_start = time.monotonic()
        self._emit_event("started", call_id, tool_name, None, None)

        try:
            content = await self._route(tool_name, args)
            duration_ms = int((time.monotonic() - t_start) * 1000)
            self._emit_event("completed", call_id, tool_name, duration_ms, None)
            return {"tool_call_id": call_id, "role": "tool", "content": content}

        except MinniError as exc:
            duration_ms = int((time.monotonic() - t_start) * 1000)
            self._log.warning("Minni dispatch failed for %r: %s", tool_name, exc)
            self._emit_event("failed", call_id, tool_name, duration_ms, str(exc))
            return _error_tool_result(
                call_id, tool_name, _minni_error_code(exc), str(exc)
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - t_start) * 1000)
            self._log.error(
                "Minni dispatch raised unexpected error for %r: %s",
                tool_name, exc, exc_info=True,
            )
            self._emit_event("failed", call_id, tool_name, duration_ms, str(exc))
            return _error_tool_result(
                call_id, tool_name, "SENSE_INTERNAL_ERROR",
                f"Unexpected error during Minni tool dispatch: {type(exc).__name__}",
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _route(self, tool_name: str, args: dict[str, Any]) -> str:
        """Route a parsed tool call to the MinniClient method.

        Raises MinniError subclasses on failure.
        Raises ToolDispatchError for unknown tool names.
        """
        from heretic.skilningr.errors import ToolDispatchError

        if tool_name not in _MINNI_TOOL_NAMES:
            raise ToolDispatchError(
                f"Unknown Minni tool: {tool_name!r}. "
                f"Valid tools: {sorted(_MINNI_TOOL_NAMES)}"
            )

        if tool_name == "minni.read_file":
            result = self._client.read_file(path=args["path"])
            return json.dumps(result)

        if tool_name == "minni.write_file":
            result = self._client.write_file(
                path=args["path"],
                content=args["content"],
            )
            return json.dumps(result)

        if tool_name == "minni.list_directory":
            result = self._client.list_directory(
                path=args["path"],
                recurse=args.get("recurse", False),
            )
            return json.dumps(result)

        # Unreachable if _MINNI_TOOL_NAMES is kept in sync
        raise ToolDispatchError(
            f"Minni route fell through for {tool_name!r} — routing table out of sync."
        )

    def _emit_event(
        self,
        state: str,
        call_id: str,
        tool_name: str,
        duration_ms: int | None,
        error: str | None,
    ) -> None:
        """Emit a SenseToolCall IPC event via event_emitter if wired."""
        if self._event_emitter is None:
            return
        try:
            from heretic.vebond.protocol import SenseToolCall, SenseToolCallState
            sense_part = tool_name.split(".")[0] if "." in tool_name else tool_name
            event = SenseToolCall(
                state=SenseToolCallState(state),
                sense=sense_part,
                tool_name=tool_name,
                call_id=call_id,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                error=error,
            )
            self._event_emitter(event)
        except Exception as exc:
            self._log.warning("Minni: event emission failed (non-fatal): %s", exc)


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _error_tool_result(
    call_id: str,
    tool_name: str,
    code: str,
    message: str,
    detail: str = "",
) -> dict:
    """Build an OpenAI tool_result containing a SENSE_CONTRACTS.md error envelope."""
    sense = tool_name.split(".")[0] if "." in tool_name else tool_name
    payload: dict[str, Any] = {
        "error": True,
        "code": code,
        "message": message,
        "sense": sense,
        "tool": tool_name,
    }
    if detail:
        payload["detail"] = detail
    return {
        "tool_call_id": call_id,
        "role": "tool",
        "content": json.dumps(payload),
    }


def _minni_error_code(exc: MinniError) -> str:
    """Map a MinniError subclass to a SENSE_CONTRACTS.md error code string."""
    from heretic.skilningr.errors import (
        MinniFileNotFoundError,
        MinniFileTooLargeError,
        MinniPermissionError,
        MinniSandboxViolation,
    )
    if isinstance(exc, MinniSandboxViolation):
        return "PERMISSION_DENIED"
    if isinstance(exc, MinniPermissionError):
        return "PERMISSION_DENIED"
    if isinstance(exc, MinniFileNotFoundError):
        return "INVALID_ARGUMENTS"
    if isinstance(exc, MinniFileTooLargeError):
        return "INVALID_ARGUMENTS"
    return "SENSE_INTERNAL_ERROR"
