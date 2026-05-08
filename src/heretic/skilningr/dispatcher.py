"""
ToolDispatcher — routes incoming agent tool_calls to the registered sense.

The dispatcher is the single routing seam between L1 Bifröst (which receives
tool_call events from the agent) and L5 Skilningr's sense implementations.

Design:
    - Senses register under a string prefix (their sense_id, e.g. "smidja").
    - dispatch() receives an OpenAI-format tool_call dict (with "name" and "arguments")
      and routes it to the matching sense by prefix.
    - ALL dispatch failures are caught here and returned as tool_result error JSON.
      The dispatcher NEVER raises to its caller (Bifröst / CLI turn loop).
    - The result format is OpenAI tool_result format:
        {"tool_call_id": "...", "role": "tool", "content": "<json string>"}

Ref: TASK_HERETIC_v0.6_HANDS_AT_FORGE.md §3
     docs/architecture/LAYER_INTERFACES.md §L5 Skilningr
     docs/architecture/SENSE_CONTRACTS.md §3 (error format)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from heretic.skilningr.errors import (
    SenseUnavailableError,
    SkilningrError,
    ToolDispatchError,
)

logger = logging.getLogger(__name__)


class ToolDispatcher:
    """Routes OpenAI-format tool calls to registered sense handlers.

    Usage:
        dispatcher = ToolDispatcher()
        dispatcher.register_sense("smidja", smidja_sense)
        result = await dispatcher.dispatch(tool_call_dict)

    The sense object registered here must expose:
        async def dispatch_tool_call(tool_call: dict) -> dict
        property is_available -> bool
        property tool_definitions -> list[dict]
    """

    def __init__(self) -> None:
        # Maps sense_id prefix → sense object (duck-typed; must have dispatch_tool_call)
        self._senses: dict[str, Any] = {}

    def register_sense(self, prefix: str, sense: Any) -> None:
        """Register a sense under its sense_id prefix.

        Args:
            prefix: The sense_id (e.g. "smidja"). Must match the first component
                    of every tool name this sense exposes. No dots permitted.
            sense: Any object that exposes async dispatch_tool_call(tool_call: dict) -> dict.
                   The dispatcher does NOT validate this at registration time; duck-typed.

        Raises:
            ValueError: if prefix is empty or contains a dot.
        """
        if not prefix:
            raise ValueError(
                "ToolDispatcher.register_sense: prefix must be a non-empty string."
            )
        if "." in prefix:
            raise ValueError(
                f"ToolDispatcher.register_sense: prefix {prefix!r} must not contain "
                f"a dot. Prefixes are the top-level sense_id (e.g. 'smidja'), not "
                f"a full tool name."
            )
        self._senses[prefix] = sense
        logger.debug("ToolDispatcher: registered sense prefix %r", prefix)

    def unregister_sense(self, prefix: str) -> None:
        """Remove a sense from the registry. No-op if prefix is not registered.

        Used when a sense subprocess dies and is being restarted — it is removed
        from the routing table until it is healthy again.
        """
        self._senses.pop(prefix, None)
        logger.debug("ToolDispatcher: unregistered sense prefix %r", prefix)

    @property
    def registered_prefixes(self) -> list[str]:
        """Return all currently-registered sense_id prefixes."""
        return list(self._senses.keys())

    def all_tool_definitions(self) -> list[dict]:
        """Aggregate and return OpenAI tool schemas from all registered senses.

        Called by the CLI turn loop at TENGSL to build the tools array passed
        to BifrostClient.send_message().

        Returns:
            Flat list of OpenAI tool dicts ({type, function: {name, description, parameters}})
            from every registered sense in registration order.
        """
        definitions: list[dict] = []
        for sense in self._senses.values():
            try:
                defs = sense.tool_definitions
                if defs:
                    definitions.extend(defs)
            except Exception as exc:
                logger.warning(
                    "ToolDispatcher: could not retrieve tool_definitions from sense: %s",
                    exc,
                )
        return definitions

    async def dispatch(self, tool_call: dict) -> dict:
        """Route a tool call to the matching sense and return a tool_result dict.

        This method NEVER raises. All errors are caught and returned as a structured
        tool_result with error JSON in the content field.

        Args:
            tool_call: OpenAI-format tool_call dict:
                {
                    "id": "<call_id>",
                    "type": "function",
                    "function": {
                        "name": "smidja.screenshot",
                        "arguments": '{"region": null}'  # JSON string
                    }
                }

        Returns:
            OpenAI tool_result dict:
                {
                    "tool_call_id": "<call_id>",
                    "role": "tool",
                    "content": "<json string>"  # success payload OR error JSON
                }
        """
        # Extract the call_id and tool_name safely
        call_id: str = tool_call.get("id", "unknown")
        fn_block = tool_call.get("function", {})
        tool_name: str = fn_block.get("name", "")

        if not tool_name:
            return _error_result(
                call_id, "(unknown)", "TOOL_NOT_FOUND",
                "Tool call is missing function.name field."
            )

        # Route by prefix — the part before the first dot
        prefix = tool_name.split(".")[0]

        if prefix not in self._senses:
            logger.warning(
                "ToolDispatcher: no sense registered for prefix %r (tool: %r)",
                prefix, tool_name,
            )
            return _error_result(
                call_id, tool_name, "TOOL_NOT_FOUND",
                f"No sense registered for tool prefix: {prefix!r}. "
                f"Registered prefixes: {self.registered_prefixes}",
            )

        sense = self._senses[prefix]

        # Check availability — sense may be disabled or not yet opened
        try:
            available = sense.is_available
        except Exception as exc:
            logger.warning(
                "ToolDispatcher: could not check is_available for sense %r: %s",
                prefix, exc,
            )
            available = False

        if not available:
            return _error_result(
                call_id, tool_name, "SENSE_UNAVAILABLE",
                f"Sense {prefix!r} is not available (disabled or not opened).",
                sense=prefix,
            )

        # Dispatch to the sense — dispatch_tool_call must never raise
        try:
            result = await sense.dispatch_tool_call(tool_call)
            return result
        except Exception as exc:
            # If sense.dispatch_tool_call violated its never-raise contract, catch here
            logger.error(
                "ToolDispatcher: sense %r violated never-raise contract: %s",
                prefix, exc,
                exc_info=True,
            )
            return _error_result(
                call_id, tool_name, "SENSE_INTERNAL_ERROR",
                f"Sense {prefix!r} raised an unexpected error: {type(exc).__name__}",
                sense=prefix,
                detail=str(exc),
            )


def _error_result(
    call_id: str,
    tool_name: str,
    code: str,
    message: str,
    sense: str = "",
    detail: str = "",
) -> dict:
    """Build an OpenAI tool_result dict containing a SENSE_CONTRACTS.md error envelope.

    This is a module-level helper so Forge can call it from both ToolDispatcher.dispatch
    and from sense-level error handlers that need to construct a consistent error result.

    Args:
        call_id: The tool_call id to echo back (tool_call_id field).
        tool_name: The fully-qualified tool name that failed.
        code: SENSE_CONTRACTS.md error code string.
        message: Human-readable error description.
        sense: sense_id that produced the error (derived from tool_name prefix if absent).
        detail: Optional technical detail (exception repr, OS error, etc.).

    Returns:
        OpenAI tool_result dict ready to append to the messages array.
    """
    if not sense and "." in tool_name:
        sense = tool_name.split(".")[0]

    error_payload: dict[str, Any] = {
        "error": True,
        "code": code,
        "message": message,
        "sense": sense,
        "tool": tool_name,
    }
    if detail:
        error_payload["detail"] = detail

    return {
        "tool_call_id": call_id,
        "role": "tool",
        "content": json.dumps(error_payload),
    }
