"""
LeidSense — L5.3 Leið sense orchestrator.

LeidSense is the boundary between ToolDispatcher and LeidClient.
It owns:
    - Sense lifecycle (open/close)
    - Tool call routing (dispatch_tool_call routes to LeidClient methods)
    - Result encoding (success payloads and errors into OpenAI tool_result format)
    - Event emission (SenseToolCall events via optional event_emitter)

It does NOT own:
    - HTTP transport (LeidClient)
    - URL validation (heretic.skilningr.sandbox)
    - Tool schema definitions (tools.py LEID_TOOL_DEFINITIONS)
    - Config (LeidConfig, passed from HereticConfig.skilningr.leid)
    - Agent message routing (ToolDispatcher)

Design:
    dispatch_tool_call NEVER raises — all errors return structured tool_result dicts.

Ref: docs/architecture/LAYER_INTERFACES.md §L5 Skilningr
     docs/architecture/SENSE_CONTRACTS.md §1 (lifecycle) §3 (error format)
     src/heretic/skilningr/senses/leid/INTERFACE.md
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any, Callable

from heretic.skilningr.config_model import LeidConfig
from heretic.skilningr.senses.leid.client import LeidClient
from heretic.skilningr.senses.leid.errors import LeidError
from heretic.skilningr.senses.leid.playwright_client import PlaywrightLeidClient
from heretic.skilningr.senses.leid.tools import LEID_TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

_LEID_TOOL_NAMES: frozenset[str] = frozenset(
    t["function"]["name"] for t in LEID_TOOL_DEFINITIONS
)


class LeidSense:
    """L5.3 Leið sense — URL-allowlisted HTTP fetch tool surface.

    Registered in ToolDispatcher under the prefix "leid". Routes any tool_call
    whose name starts with "leid." to LeidClient.

    Usage:
        config = heretic_config.skilningr.leid
        client = LeidClient(config)
        sense  = LeidSense(config, client)
        await sense.open()
        result = await sense.dispatch_tool_call(tool_call_dict)
        await sense.close()
    """

    def __init__(
        self,
        config: LeidConfig,
        client: LeidClient,
        log: logging.Logger | None = None,
        event_emitter: Callable | None = None,
        playwright_client: PlaywrightLeidClient | None = None,
    ) -> None:
        """Construct the Leið sense.

        Args:
            config: LeidConfig — URL allowlist + browser timeouts + size cap.
            client: LeidClient — answers leid.fetch_url and leid.extract_text.
            log:    Optional logger.
            event_emitter: Optional callback for SenseToolCall events.
            playwright_client: Optional PlaywrightLeidClient — answers
                leid.render_url (v0.8.0 Opið Vef). When None, the sense
                lazily constructs one on first leid.render_url dispatch
                using the same config; the import of the playwright Python
                package is then deferred to the first actual call (B-2).
        """
        self._config = config
        self._client = client
        self._log = log if log is not None else logging.getLogger(__name__)
        self._event_emitter = event_emitter
        self._is_open: bool = False
        self._playwright_client: PlaywrightLeidClient | None = playwright_client

    @property
    def is_available(self) -> bool:
        """True if enabled AND open."""
        return self._config.enabled and self._is_open

    async def open(self) -> None:
        """Open the Leið sense. Logs allowlist status. Never raises."""
        if not self._config.enabled:
            self._is_open = False
            return
        try:
            self._is_open = True
            pattern_count = len(self._config.url_allowlist_patterns)
            if pattern_count == 0:
                self._log.warning(
                    "Leið sense opened but url_allowlist_patterns is EMPTY — "
                    "no URLs will be fetchable until patterns are added."
                )
            elif "*" in self._config.url_allowlist_patterns:
                self._log.warning(
                    "Leið sense opened with unrestricted wildcard '*' in "
                    "url_allowlist_patterns — ALL URLs are fetchable. "
                    "Restrict to specific patterns in production."
                )
            else:
                self._log.info(
                    "Leið sense opened — %d URL pattern(s) in allowlist.", pattern_count
                )
        except Exception as exc:
            self._log.error("Leið sense failed to open: %s", exc, exc_info=True)
            self._is_open = False

    async def close(self) -> None:
        """Close the Leið sense. No persistent HTTP client to close in v0.6.2."""
        self._is_open = False

    @property
    def tool_definitions(self) -> list[dict]:
        return list(LEID_TOOL_DEFINITIONS) if self._config.enabled else []

    async def dispatch_tool_call(self, tool_call: dict) -> dict:
        """Route a tool_call to LeidClient. NEVER raises."""
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

        except LeidError as exc:
            duration_ms = int((time.monotonic() - t_start) * 1000)
            self._log.warning("Leið dispatch failed for %r: %s", tool_name, exc)
            self._emit_event("failed", call_id, tool_name, duration_ms, str(exc))
            return _error_tool_result(
                call_id, tool_name, _leid_error_code(exc), str(exc)
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - t_start) * 1000)
            self._log.error(
                "Leið dispatch raised unexpected error for %r: %s",
                tool_name, exc, exc_info=True,
            )
            self._emit_event("failed", call_id, tool_name, duration_ms, str(exc))
            return _error_tool_result(
                call_id, tool_name, "SENSE_INTERNAL_ERROR",
                f"Unexpected error during Leið tool dispatch: {type(exc).__name__}",
            )

    async def _route(self, tool_name: str, args: dict[str, Any]) -> str:
        from heretic.skilningr.errors import ToolDispatchError

        if tool_name not in _LEID_TOOL_NAMES:
            raise ToolDispatchError(
                f"Unknown Leið tool: {tool_name!r}. "
                f"Valid tools: {sorted(_LEID_TOOL_NAMES)}"
            )

        if tool_name == "leid.fetch_url":
            result = await self._client.fetch_url(url=args["url"])
            return json.dumps(result)

        if tool_name == "leid.extract_text":
            result = await self._client.extract_text(url=args["url"])
            return json.dumps(result)

        if tool_name == "leid.render_url":
            # v0.8.0 Opið Vef — browser-render sub-faculty.
            # Lazily construct PlaywrightLeidClient if it was not injected.
            # The playwright import only happens inside render_url() itself
            # (B-2), so this lazy construction is safe on hosts without the
            # [browser] extra installed.
            if self._playwright_client is None:
                self._playwright_client = PlaywrightLeidClient(
                    self._config, log=self._log
                )
            result = await self._playwright_client.render_url(url=args["url"])
            return json.dumps(result)

        if tool_name == "leid.screenshot":
            # v0.8.1 Mynd af Vegferð — sibling browser tool. Same lazy
            # construction posture; same playwright import deferral.
            if self._playwright_client is None:
                self._playwright_client = PlaywrightLeidClient(
                    self._config, log=self._log
                )
            result = await self._playwright_client.screenshot(url=args["url"])
            return json.dumps(result)

        # v0.8.2 Innan Hurðar — stateful session tools. Same lazy client
        # construction; the BrowserSessionManager is internally lazy too.
        if tool_name == "leid.open_session":
            if self._playwright_client is None:
                self._playwright_client = PlaywrightLeidClient(
                    self._config, log=self._log
                )
            result = await self._playwright_client.open_session(url=args["url"])
            return json.dumps(result)

        if tool_name == "leid.session_status":
            if self._playwright_client is None:
                self._playwright_client = PlaywrightLeidClient(
                    self._config, log=self._log
                )
            result = await self._playwright_client.session_status(
                session_id=args["session_id"]
            )
            return json.dumps(result)

        if tool_name == "leid.click":
            if self._playwright_client is None:
                self._playwright_client = PlaywrightLeidClient(
                    self._config, log=self._log
                )
            result = await self._playwright_client.click(
                session_id=args["session_id"],
                selector=args["selector"],
            )
            return json.dumps(result)

        if tool_name == "leid.type":
            # v0.8.2.1 — unnamed extension within Innan Hurðar (the second
            # half of the interactive gesture).
            if self._playwright_client is None:
                self._playwright_client = PlaywrightLeidClient(
                    self._config, log=self._log
                )
            result = await self._playwright_client.type(
                session_id=args["session_id"],
                selector=args["selector"],
                text=args["text"],
            )
            return json.dumps(result)

        if tool_name == "leid.navigate":
            # v0.8.2.2 — unnamed extension within Innan Hurðar (the body
            # walks to a new room without leaving the building).
            if self._playwright_client is None:
                self._playwright_client = PlaywrightLeidClient(
                    self._config, log=self._log
                )
            result = await self._playwright_client.navigate(
                session_id=args["session_id"],
                url=args["url"],
            )
            return json.dumps(result)

        if tool_name == "leid.query":
            # v0.8.3 — sixth unnamed extension within Innan Hurðar (the
            # body's first eye inside the door — read-only).
            # attribute is optional; defaults to "" which means text content.
            if self._playwright_client is None:
                self._playwright_client = PlaywrightLeidClient(
                    self._config, log=self._log
                )
            result = await self._playwright_client.query(
                session_id=args["session_id"],
                selector=args["selector"],
                attribute=args.get("attribute", ""),
            )
            return json.dumps(result)

        if tool_name == "leid.press":
            # v0.8.4 — seventh unnamed extension within Innan Hurðar (the
            # body's keyboard finger). Page-level key dispatch.
            if self._playwright_client is None:
                self._playwright_client = PlaywrightLeidClient(
                    self._config, log=self._log
                )
            result = await self._playwright_client.press(
                session_id=args["session_id"],
                key=args["key"],
            )
            return json.dumps(result)

        if tool_name == "leid.close_session":
            if self._playwright_client is None:
                self._playwright_client = PlaywrightLeidClient(
                    self._config, log=self._log
                )
            result = await self._playwright_client.close_session(
                session_id=args["session_id"]
            )
            return json.dumps(result)

        raise ToolDispatchError(
            f"Leið route fell through for {tool_name!r} — routing table out of sync."
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
            self._log.warning("Leið: event emission failed (non-fatal): %s", exc)


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


def _leid_error_code(exc: LeidError) -> str:
    from heretic.skilningr.errors import (
        LeidClickElementNotFoundError,
        LeidConnectionError,
        LeidHttpError,
        LeidPlaywrightUnavailableError,
        LeidResponseTooLargeError,
        LeidSessionExpiredError,
        LeidSessionLimitError,
        LeidTimeoutError,
        LeidTypeElementNotFoundError,
        UrlNotAllowedError,
    )
    if isinstance(exc, UrlNotAllowedError):
        return "PERMISSION_DENIED"
    if isinstance(exc, LeidTimeoutError):
        return "SENSE_TIMEOUT"
    if isinstance(
        exc,
        (
            LeidResponseTooLargeError,
            LeidClickElementNotFoundError,
            LeidTypeElementNotFoundError,
        ),
    ):
        # v0.8.2 / v0.8.2.1 — agent-actionable errors (cap exceeded,
        # selector wrong on click or type).
        return "INVALID_ARGUMENTS"
    if isinstance(exc, LeidHttpError):
        return "SENSE_INTERNAL_ERROR"
    if isinstance(exc, LeidPlaywrightUnavailableError):
        # v0.8.0 Opið Vef — Playwright not installed or chromium missing.
        # Surfaces to the agent as the same code as a network-level error,
        # so the agent treats it as a transient/recoverable unavailability.
        return "EXTERNAL_APP_UNAVAILABLE"
    if isinstance(exc, (LeidSessionLimitError, LeidSessionExpiredError)):
        # v0.8.2 — session unavailable (cap reached or session evicted/unknown).
        return "SENSE_UNAVAILABLE"
    if isinstance(exc, LeidConnectionError):
        return "EXTERNAL_APP_UNAVAILABLE"
    return "SENSE_INTERNAL_ERROR"
