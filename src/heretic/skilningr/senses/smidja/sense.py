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

import json
import logging
from typing import Any, Callable

from heretic.skilningr.config_model import SmidjaConfig
from heretic.skilningr.senses.smidja.client import BrunhandHttpClient
from heretic.skilningr.senses.smidja.errors import SmidjaError
from heretic.skilningr.senses.smidja.tools import SMIDJA_TOOL_DEFINITIONS

logger = logging.getLogger(__name__)


class SmidjaSense:
    """L5.5 Smiðja sense — Brúarhönd remote-control tool surface.

    Registered in ToolDispatcher under the prefix "smidja". Routes any tool_call
    whose name starts with "smidja." to the appropriate BrunhandHttpClient method.

    Usage (Forge implements the bodies):

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
        raise NotImplementedError(
            "SmidjaSense.__init__ — Forge implements in Wave 2. "
            "Body: store config, client, logger, event_emitter. "
            "self._is_open = False."
        )

    @property
    def is_available(self) -> bool:
        """True if the sense is enabled in config AND the client session is open.

        ToolDispatcher checks this before calling dispatch_tool_call. If False,
        the dispatcher returns SENSE_UNAVAILABLE error immediately.

        Returns:
            True if config.enabled is True and client is open (post open()).
        """
        raise NotImplementedError(
            "SmidjaSense.is_available — Forge implements in Wave 2. "
            "Body: return self._config.enabled and self._is_open."
        )

    async def open(self) -> None:
        """Open the Brúarhönd HTTP client session and probe daemon health.

        Called at ceremony start (Kynding) when skilningr.smidja.enabled is True.
        If the daemon is unreachable, logs a warning and sets the sense to degraded
        (is_available = False) — the ceremony continues without Smiðja.

        Fault tolerance invariant: NEVER raise to the caller (Kynding loop).
        All exceptions are caught, logged, and result in is_available=False.
        """
        raise NotImplementedError(
            "SmidjaSense.open — Forge implements in Wave 2. "
            "Body: try: await self._client.open(); self._is_open = True. "
            "Except SmidjaError as e: log warning; self._is_open = False. "
            "Except Exception as e: log error; self._is_open = False."
        )

    async def close(self) -> None:
        """Close the HTTP client and release resources.

        Called at ceremony end (Slokna). Idempotent.
        """
        raise NotImplementedError(
            "SmidjaSense.close — Forge implements in Wave 2. "
            "Body: try: await self._client.close(). Finally: self._is_open = False."
        )

    @property
    def tool_definitions(self) -> list[dict]:
        """Return the list of OpenAI tool schemas for the Smiðja sense.

        ToolDispatcher calls this at TENGSL to build the tools array.
        Returns SMIDJA_TOOL_DEFINITIONS from tools.py — the immutable schema list.
        Only returns the definitions if the sense is enabled; empty list otherwise.

        Returns:
            List of OpenAI tool dicts. Empty list if not enabled.
        """
        raise NotImplementedError(
            "SmidjaSense.tool_definitions — Forge implements in Wave 2. "
            "Body: if not self._config.enabled: return []. "
            "return SMIDJA_TOOL_DEFINITIONS."
        )

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

        Tool routing table (all 6 tools):
            smidja.screenshot  -> client.screenshot(region)
            smidja.click       -> client.click(x, y, button, clicks, modifiers)
            smidja.type_text   -> client.type_text(text, interval)
            smidja.hotkey      -> client.hotkey(keys)
            smidja.vroid_open  -> client.vroid_open(project_path, wait_timeout_seconds)
            smidja.vroid_export-> client.vroid_export(output_path, overwrite, wait_timeout_seconds)

        For smidja.screenshot specifically: the raw PNG bytes from client.screenshot()
        are base64-encoded into a data URL string and placed in the tool_result content.
        This mirrors the format used by L3 Sjón (FrameEncoder) so the agent receives
        images consistently from both vision channels.
        """
        raise NotImplementedError(
            "SmidjaSense.dispatch_tool_call — Forge implements in Wave 2. "
            "Steps: "
            "1. Extract call_id, tool_name, args_str from tool_call. "
            "2. Parse args = json.loads(args_str or '{}'). "
            "3. If event_emitter: emit SenseToolCall(state=STARTED, ...). "
            "4. try: route by tool_name to the matching client method. "
            "5. Encode result: for screenshot encode PNG bytes as data URL; "
            "   for all others json.dumps the payload dict. "
            "6. If event_emitter: emit SenseToolCall(state=COMPLETED, ...). "
            "7. Return {'tool_call_id': call_id, 'role': 'tool', 'content': content}. "
            "8. Except SmidjaError: emit FAILED event; return error tool_result. "
            "9. Except Exception: log; emit FAILED event; return error tool_result. "
            "NEVER re-raise — the dispatcher and CLI turn loop must not crash."
        )
