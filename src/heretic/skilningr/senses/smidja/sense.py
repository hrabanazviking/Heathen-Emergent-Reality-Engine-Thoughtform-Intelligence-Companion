"""
SmidjaSense — L5.5 Smiðja sense orchestrator.

SmidjaSense is the boundary between ToolDispatcher and BrunhandHttpClient.
It owns:
    - Lifecycle (open/close of the HTTP client)
    - Tool call routing (dispatch_tool_call routes by name to the right client method)
    - Result encoding (success payloads and errors into OpenAI tool_result format)
    - Event emission (SenseToolCall events via the optional event_emitter callback)

It does NOT own:
    - HTTP transport (BrunhandHttpClient)
    - Tool schema definitions (tools.py SMIDJA_TOOL_DEFINITIONS)
    - Config (SmidjaConfig, passed in from grunnr.config.HereticConfig.skilningr.smidja)
    - Agent message routing (ToolDispatcher)

Design:
    SmidjaSense is instantiated once per ceremony. ToolDispatcher holds a reference
    to it and calls dispatch_tool_call for every smidja.* tool_call from the agent.
    dispatch_tool_call NEVER raises — all errors return structured tool_result dicts.

Ref: docs/architecture/LAYER_INTERFACES.md §L5 Skilningr
     docs/architecture/SENSE_CONTRACTS.md §1 (lifecycle) §3 (error format)
     src/heretic/skilningr/senses/smidja/INTERFACE.md
"""

from __future__ import annotations

import base64
import json
import logging
import time
from datetime import datetime
from typing import Any, Callable

from heretic.skilningr.config_model import SmidjaConfig
from heretic.skilningr.senses.smidja.client import BrunhandHttpClient
from heretic.skilningr.senses.smidja.errors import SmidjaError
from heretic.skilningr.senses.smidja.tools import SMIDJA_TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

# Tool name → client method name mapping
_TOOL_TO_METHOD: dict[str, str] = {
    "smidja.screenshot": "screenshot",
    "smidja.click": "click",
    "smidja.type_text": "type_text",
    "smidja.hotkey": "hotkey",
    "smidja.vroid_open": "vroid_open",
    "smidja.vroid_export": "vroid_export",
}

# Tool name → argument key mapping (tool parameter name → client method kwarg name)
# Only needed where parameter names differ between tool schema and client method
_TOOL_ARG_MAP: dict[str, dict[str, str]] = {
    "smidja.vroid_open": {"project_path": "project_path"},
    "smidja.vroid_export": {"output_path": "output_path"},
}


class SmidjaSense:
    """L5.5 Smiðja sense — Brúarhönd remote-control tool surface.

    Registered in ToolDispatcher under the prefix "smidja". Routes any tool_call
    whose name starts with "smidja." to the appropriate BrunhandHttpClient method.

    Usage:
        config = heretic_config.skilningr.smidja
        client = BrunhandHttpClient(config, logger)
        sense  = SmidjaSense(config, client, logger, event_emitter=bus.publish)
        await sense.open()
        result = await sense.dispatch_tool_call(tool_call_dict)
        await sense.close()
    """

    def __init__(
        self,
        config: SmidjaConfig,
        client: BrunhandHttpClient,
        logger: logging.Logger | None = None,
        event_emitter: Callable | None = None,
    ) -> None:
        """Initialise the Smiðja sense.

        Args:
            config: SmidjaConfig from HereticConfig.skilningr.smidja.
            client: BrunhandHttpClient for the configured host. Must be
                    created before the sense but not yet opened.
            logger: Optional logger instance.
            event_emitter: Optional callable for emitting SenseToolCall IPC events.
                           Signature: event_emitter(event: SenseToolCall) -> None.
                           If None, events are not emitted (useful in tests and
                           when the IPC bus is not active).
        """
        self._config = config
        self._client = client
        self._log = logger if logger is not None else logging.getLogger(__name__)
        self._event_emitter = event_emitter
        self._is_open: bool = False

    @property
    def is_available(self) -> bool:
        """True if the sense is enabled in config AND the client session is open.

        ToolDispatcher checks this before calling dispatch_tool_call. If False,
        the dispatcher returns SENSE_UNAVAILABLE error immediately.

        Returns:
            True if config.enabled is True and client is open (post open()).
        """
        return self._config.enabled and self._is_open

    async def open(self) -> None:
        """Open the Brúarhönd HTTP client session and probe daemon health.

        Called at ceremony start (Kynding) when skilningr.smidja.enabled is True.
        If the daemon is unreachable, logs a warning and sets the sense to degraded
        (is_available = False) — the ceremony continues without Smiðja.

        Fault tolerance invariant: NEVER raise to the caller (Kynding loop).
        All exceptions are caught, logged, and result in is_available=False.
        """
        try:
            await self._client.open()
            self._is_open = True
            self._log.info("Smiðja sense opened — Brúarhönd hand is ready.")
        except SmidjaError as exc:
            self._log.warning(
                "Smiðja sense failed to open (SmidjaError) — ceremony continues "
                "without the hand: %s",
                exc,
            )
            self._is_open = False
        except Exception as exc:
            self._log.error(
                "Smiðja sense failed to open (unexpected error) — ceremony continues "
                "without the hand: %s",
                exc,
                exc_info=True,
            )
            self._is_open = False

    async def close(self) -> None:
        """Close the HTTP client and release resources.

        Called at ceremony end (Slokna). Idempotent.
        """
        try:
            await self._client.close()
        except Exception as exc:
            self._log.warning("Error while closing Smiðja client: %s", exc)
        finally:
            self._is_open = False

    @property
    def tool_definitions(self) -> list[dict]:
        """Return the list of OpenAI tool schemas for the Smiðja sense.

        ToolDispatcher calls this at TENGSL to build the tools array.
        Returns SMIDJA_TOOL_DEFINITIONS from tools.py — the immutable schema list.
        Only returns the definitions if the sense is enabled; empty list otherwise.

        Returns:
            List of OpenAI tool dicts. Empty list if not enabled.
        """
        if not self._config.enabled:
            return []
        return SMIDJA_TOOL_DEFINITIONS

    async def dispatch_tool_call(self, tool_call: dict) -> dict:
        """Route a tool_call to the appropriate BrunhandHttpClient method.

        This method NEVER raises. All errors are caught and returned as structured
        tool_result dicts with SENSE_CONTRACTS.md error JSON in the content field.

        Args:
            tool_call: OpenAI-format tool_call dict:
                {
                    "id": "<call_id>",
                    "type": "function",
                    "function": {
                        "name": "smidja.screenshot",
                        "arguments": '{"region": null}'
                    }
                }

        Returns:
            OpenAI tool_result dict:
                {"tool_call_id": "<id>", "role": "tool", "content": "<json>"}
            content is the success payload JSON or a SENSE_CONTRACTS.md error JSON.
        """
        # Extract call metadata
        call_id: str = tool_call.get("id", "unknown")
        fn_block = tool_call.get("function", {})
        tool_name: str = fn_block.get("name", "")
        args_str: str = fn_block.get("arguments", "") or "{}"

        # Parse arguments — treat invalid JSON as empty args
        try:
            args: dict[str, Any] = json.loads(args_str)
        except json.JSONDecodeError as exc:
            self._log.warning(
                "Smiðja dispatch: could not parse arguments JSON for %r: %s",
                tool_name, exc,
            )
            return _error_tool_result(
                call_id, tool_name,
                "INVALID_ARGUMENTS",
                f"Could not parse tool call arguments as JSON: {exc}",
            )

        # Emit STARTED event
        t_start = time.monotonic()
        self._emit_event(
            state="started",
            call_id=call_id,
            tool_name=tool_name,
            duration_ms=None,
            error=None,
        )

        try:
            content = await self._route(tool_name, args)
            duration_ms = int((time.monotonic() - t_start) * 1000)
            self._emit_event(
                state="completed",
                call_id=call_id,
                tool_name=tool_name,
                duration_ms=duration_ms,
                error=None,
            )
            return {
                "tool_call_id": call_id,
                "role": "tool",
                "content": content,
            }

        except SmidjaError as exc:
            duration_ms = int((time.monotonic() - t_start) * 1000)
            self._log.warning(
                "Smiðja dispatch failed for %r (SmidjaError): %s",
                tool_name, exc,
            )
            self._emit_event(
                state="failed",
                call_id=call_id,
                tool_name=tool_name,
                duration_ms=duration_ms,
                error=str(exc),
            )
            return _error_tool_result(
                call_id, tool_name,
                _smidja_error_code(exc),
                str(exc),
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - t_start) * 1000)
            self._log.error(
                "Smiðja dispatch raised unexpected error for %r: %s",
                tool_name, exc,
                exc_info=True,
            )
            self._emit_event(
                state="failed",
                call_id=call_id,
                tool_name=tool_name,
                duration_ms=duration_ms,
                error=str(exc),
            )
            return _error_tool_result(
                call_id, tool_name,
                "SENSE_INTERNAL_ERROR",
                f"Unexpected error during tool dispatch: {type(exc).__name__}",
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _route(self, tool_name: str, args: dict[str, Any]) -> str:
        """Route a parsed tool call to the correct BrunhandHttpClient method.

        Returns the tool result content as a JSON string (or data URL for screenshots).

        Raises:
            SmidjaError and subclasses on client-level failures.
            ValueError if tool_name is unknown.
        """
        if tool_name == "smidja.screenshot":
            region = args.get("region", None)
            png_bytes = await self._client.screenshot(region=region)
            # Re-encode raw PNG bytes as a data URL — mirrors L3 Sjón FrameEncoder format
            b64_str = base64.b64encode(png_bytes).decode("ascii")
            data_url = f"data:image/png;base64,{b64_str}"
            return json.dumps({"type": "image", "data_url": data_url})

        if tool_name == "smidja.click":
            result = await self._client.click(
                x=args["x"],
                y=args["y"],
                button=args.get("button", "left"),
                clicks=args.get("clicks", 1),
                modifiers=args.get("modifiers", []),
            )
            return json.dumps(result)

        if tool_name == "smidja.type_text":
            result = await self._client.type_text(
                text=args["text"],
                interval=args.get("interval", 0.05),
            )
            return json.dumps(result)

        if tool_name == "smidja.hotkey":
            result = await self._client.hotkey(keys=args["keys"])
            return json.dumps(result)

        if tool_name == "smidja.vroid_open":
            result = await self._client.vroid_open(
                project_path=args["project_path"],
                wait_timeout_seconds=args.get("wait_timeout_seconds", 60.0),
            )
            return json.dumps(result)

        if tool_name == "smidja.vroid_export":
            result = await self._client.vroid_export(
                output_path=args["output_path"],
                overwrite=args.get("overwrite", True),
                wait_timeout_seconds=args.get("wait_timeout_seconds", 120.0),
            )
            return json.dumps(result)

        # Unknown tool in the smidja.* namespace
        from heretic.skilningr.errors import ToolDispatchError
        raise ToolDispatchError(
            f"Unknown Smiðja tool: {tool_name!r}. "
            f"Valid tools: {list(_TOOL_TO_METHOD.keys())}"
        )

    def _emit_event(
        self,
        state: str,
        call_id: str,
        tool_name: str,
        duration_ms: int | None,
        error: str | None,
    ) -> None:
        """Emit a SenseToolCall IPC event via event_emitter if wired.

        If event_emitter is None (CLI mode, unit tests), this is a no-op.
        Any exception in the emitter is caught and logged — tool dispatch
        must never crash because event emission failed.
        """
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
            self._log.warning(
                "Smiðja: event emission failed (non-fatal): %s", exc
            )


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


def _smidja_error_code(exc: SmidjaError) -> str:
    """Map a SmidjaError subclass to a SENSE_CONTRACTS.md error code string."""
    from heretic.skilningr.senses.smidja.errors import (
        BrunhandAuthError,
        BrunhandSessionLockedError,
        BrunhandTimeoutError,
        BrunhandUnreachableError,
    )
    from heretic.skilningr.errors import ToolDispatchError, SenseUnavailableError

    if isinstance(exc, BrunhandAuthError):
        return "PERMISSION_DENIED"
    if isinstance(exc, BrunhandUnreachableError):
        return "EXTERNAL_APP_UNAVAILABLE"
    if isinstance(exc, BrunhandTimeoutError):
        return "SENSE_TIMEOUT"
    if isinstance(exc, BrunhandSessionLockedError):
        return "SENSE_INTERNAL_ERROR"
    if isinstance(exc, ToolDispatchError):
        return "SENSE_INTERNAL_ERROR"
    if isinstance(exc, SenseUnavailableError):
        return "SENSE_UNAVAILABLE"
    return "SENSE_INTERNAL_ERROR"
