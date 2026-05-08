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

    Usage (Forge implements the bodies):

        dispatcher = ToolDispatcher()
        dispatcher.register_sense("smidja", smidja_sense)
        result = await dispatcher.dispatch(tool_call_dict)

    The sense object registered here must expose:
        async def dispatch_tool_call(tool_call: dict) -> dict

    The dispatcher routes by tool-name prefix — the part before the first dot.
    A tool named "smidja.screenshot" is routed to the sense registered under "smidja".
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
        raise NotImplementedError(
            "ToolDispatcher.register_sense — Forge implements this in Wave 2. "
            "Body: validate prefix (no dots, non-empty), then store in self._senses[prefix]."
        )

    def unregister_sense(self, prefix: str) -> None:
        """Remove a sense from the registry. No-op if prefix is not registered.

        Used when a sense subprocess dies and is being restarted — it is removed
        from the routing table until it is healthy again.
        """
        raise NotImplementedError(
            "ToolDispatcher.unregister_sense — Forge implements in Wave 2. "
            "Body: self._senses.pop(prefix, None)."
        )

    @property
    def registered_prefixes(self) -> list[str]:
        """Return all currently-registered sense_id prefixes."""
        raise NotImplementedError(
            "ToolDispatcher.registered_prefixes — Forge implements in Wave 2. "
            "Body: return list(self._senses.keys())."
        )

    def all_tool_definitions(self) -> list[dict]:
        """Aggregate and return OpenAI tool schemas from all registered senses.

        Called by the CLI turn loop at TENGSL to build the tools array passed
        to BifrostClient.send_message().

        Returns:
            Flat list of OpenAI tool dicts ({type, function: {name, description, parameters}})
            from every registered sense in registration order.
        """
        raise NotImplementedError(
            "ToolDispatcher.all_tool_definitions — Forge implements in Wave 2. "
            "Body: iterate self._senses.values(), call sense.tool_definitions, "
            "extend into a flat list, return it."
        )

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

        The returned content string is always valid JSON. On success it is the
        sense's response payload. On failure it is the SENSE_CONTRACTS.md error
        envelope:
            {
                "error": true,
                "code": "<ERROR_CODE>",
                "message": "<human-readable>",
                "sense": "<sense_id>",
                "tool": "<tool_name>",
                "detail": "<optional>"
            }
        """
        raise NotImplementedError(
            "ToolDispatcher.dispatch — Forge implements in Wave 2. "
            "Steps: "
            "1. Extract call_id = tool_call.get('id') or generate one. "
            "2. Extract tool_name = tool_call['function']['name']. "
            "3. Split prefix = tool_name.split('.')[0]. "
            "4. If prefix not in self._senses: return _error_result(call_id, tool_name, "
            "   'TOOL_NOT_FOUND', f'No sense registered for prefix: {prefix}'). "
            "5. sense = self._senses[prefix]. "
            "6. If not sense.is_available: return _error_result(call_id, tool_name, "
            "   'SENSE_UNAVAILABLE', 'Sense is not available'). "
            "7. Try: result = await sense.dispatch_tool_call(tool_call). "
            "8. Catch SkilningrError and Exception: return _error_result. "
            "9. Wrap result in tool_result envelope and return."
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

    error_payload = {
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
