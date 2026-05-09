"""
SkepjaSense — L5.2 Skepja sense orchestrator.

SkepjaSense is the boundary between ToolDispatcher and SkepjaClient.
It owns:
    - Sense lifecycle (open/close)
    - Tool call routing (dispatch_tool_call routes to SkepjaClient methods)
    - Result encoding (success payloads and errors into OpenAI tool_result format)
    - Event emission (SenseToolCall events via optional event_emitter)

It does NOT own:
    - Subprocess execution (SkepjaClient)
    - Allowlist validation (heretic.skilningr.sandbox)
    - Tool schema definitions (tools.py SKEPJA_TOOL_DEFINITIONS)
    - Config (SkepjaConfig, passed from HereticConfig.skilningr.skepja)
    - Agent message routing (ToolDispatcher)

Design:
    dispatch_tool_call NEVER raises — all errors return structured tool_result dicts.

Ref: docs/architecture/LAYER_INTERFACES.md §L5 Skilningr
     docs/architecture/SENSE_CONTRACTS.md §1 (lifecycle) §3 (error format)
     src/heretic/skilningr/senses/skepja/INTERFACE.md
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any, Callable

from heretic.skilningr.config_model import SkepjaConfig
from heretic.skilningr.senses.skepja.client import SkepjaClient
from heretic.skilningr.senses.skepja.errors import SkepjaError
from heretic.skilningr.senses.skepja.tools import SKEPJA_TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

_SKEPJA_TOOL_NAMES: frozenset[str] = frozenset(
    t["function"]["name"] for t in SKEPJA_TOOL_DEFINITIONS
)


class SkepjaSense:
    """L5.2 Skepja sense — allowlisted terminal tool surface.

    Registered in ToolDispatcher under the prefix "skepja". Routes any
    tool_call whose name starts with "skepja." to SkepjaClient.

    Usage:
        config = heretic_config.skilningr.skepja
        client = SkepjaClient(config)
        sense  = SkepjaSense(config, client)
        await sense.open()
        result = await sense.dispatch_tool_call(tool_call_dict)
        await sense.close()
    """

    def __init__(
        self,
        config: SkepjaConfig,
        client: SkepjaClient,
        log: logging.Logger | None = None,
        event_emitter: Callable | None = None,
    ) -> None:
        self._config = config
        self._client = client
        self._log = log if log is not None else logging.getLogger(__name__)
        self._event_emitter = event_emitter
        self._is_open: bool = False

    @property
    def is_available(self) -> bool:
        """True if enabled AND open."""
        return self._config.enabled and self._is_open

    async def open(self) -> None:
        """Open the Skepja sense. Logs allowlist status. Never raises."""
        if not self._config.enabled:
            self._is_open = False
            return
        try:
            self._is_open = True
            allowlist_count = len(self._config.command_allowlist)
            if allowlist_count == 0:
                self._log.warning(
                    "Skepja sense opened but command_allowlist is EMPTY — "
                    "no commands will be permitted until entries are added."
                )
            else:
                self._log.info(
                    "Skepja sense opened — %d allowlisted command(s).", allowlist_count
                )
        except Exception as exc:
            self._log.error("Skepja sense failed to open: %s", exc, exc_info=True)
            self._is_open = False

    async def close(self) -> None:
        """Close the Skepja sense. No persistent subprocess to clean up."""
        self._is_open = False

    @property
    def tool_definitions(self) -> list[dict]:
        return list(SKEPJA_TOOL_DEFINITIONS) if self._config.enabled else []

    async def dispatch_tool_call(self, tool_call: dict) -> dict:
        """Route a tool_call to SkepjaClient. NEVER raises."""
        call_id: str = tool_call.get("id", "unknown")
        fn_block = tool_call.get("function", {})
        tool_name: str = fn_block.get("name", "")
        args_str: str = fn_block.get("arguments", "") or "{}"

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

        except SkepjaError as exc:
            duration_ms = int((time.monotonic() - t_start) * 1000)
            self._log.warning("Skepja dispatch failed for %r: %s", tool_name, exc)
            self._emit_event("failed", call_id, tool_name, duration_ms, str(exc))
            return _error_tool_result(
                call_id, tool_name, _skepja_error_code(exc), str(exc)
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - t_start) * 1000)
            self._log.error(
                "Skepja dispatch raised unexpected error for %r: %s",
                tool_name, exc, exc_info=True,
            )
            self._emit_event("failed", call_id, tool_name, duration_ms, str(exc))
            return _error_tool_result(
                call_id, tool_name, "SENSE_INTERNAL_ERROR",
                f"Unexpected error during Skepja tool dispatch: {type(exc).__name__}",
            )

    async def _route(self, tool_name: str, args: dict[str, Any]) -> str:
        from heretic.skilningr.errors import ToolDispatchError

        if tool_name not in _SKEPJA_TOOL_NAMES:
            raise ToolDispatchError(
                f"Unknown Skepja tool: {tool_name!r}. "
                f"Valid tools: {sorted(_SKEPJA_TOOL_NAMES)}"
            )

        if tool_name == "skepja.run_command":
            result = self._client.run_command(command=args["command"])
            return json.dumps(result)

        if tool_name == "skepja.get_working_directory":
            result = self._client.get_working_directory()
            return json.dumps(result)

        raise ToolDispatchError(
            f"Skepja route fell through for {tool_name!r} — routing table out of sync."
        )

    def _emit_event(
        self,
        state: str,
        call_id: str,
        tool_name: str,
        duration_ms: int | None,
        error: str | None,
    ) -> None:
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
            self._log.warning("Skepja: event emission failed (non-fatal): %s", exc)


def _error_tool_result(
    call_id: str,
    tool_name: str,
    code: str,
    message: str,
    detail: str = "",
) -> dict:
    sense = tool_name.split(".")[0] if "." in tool_name else tool_name
    payload: dict[str, Any] = {
        "error": True, "code": code, "message": message,
        "sense": sense, "tool": tool_name,
    }
    if detail:
        payload["detail"] = detail
    return {"tool_call_id": call_id, "role": "tool", "content": json.dumps(payload)}


def _skepja_error_code(exc: SkepjaError) -> str:
    from heretic.skilningr.errors import (
        CommandExecutionError,
        CommandNotAllowedError,
        CommandParseError,
        CommandTimeoutError,
    )
    if isinstance(exc, CommandNotAllowedError):
        return "PERMISSION_DENIED"
    if isinstance(exc, CommandParseError):
        return "INVALID_ARGUMENTS"
    if isinstance(exc, CommandTimeoutError):
        return "SENSE_TIMEOUT"
    if isinstance(exc, CommandExecutionError):
        return "SENSE_INTERNAL_ERROR"
    return "SENSE_INTERNAL_ERROR"
