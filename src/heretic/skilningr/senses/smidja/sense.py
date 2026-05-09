"""
SmidjaSense — L5.5 Smiðja sense orchestrator.

SmidjaSense is the boundary between ToolDispatcher and both HTTP clients.
It owns:
    - Dual-half lifecycle (open/close of BOTH BrunhandHttpClient and ForgeHttpClient)
    - Tool call routing (dispatch_tool_call routes to the correct client by prefix)
    - Result encoding (success payloads and errors into OpenAI tool_result format)
    - Event emission (SenseToolCall events via the optional event_emitter callback)

It does NOT own:
    - HTTP transport (BrunhandHttpClient, ForgeHttpClient)
    - Tool schema definitions (tools.py SMIDJA_TOOL_DEFINITIONS)
    - Config (SmidjaConfig, passed in from grunnr.config.HereticConfig.skilningr.smidja)
    - Agent message routing (ToolDispatcher)

DUAL-HALF ARCHITECTURE (v0.6.1):
    SmidjaSense holds both _brunhand_client (BrunhandHttpClient) and
    _forge_client (ForgeHttpClient) as separate attributes. Each half opens and
    closes independently. If one half is unreachable, the other continues working.

    State tracking:
        _brunhand_open: bool — True when Brúarhönd client opened successfully
        _forge_open: bool    — True when Forge client opened successfully

ROUTING RULE (sealed — do not change without a sense version bump):
    Tool name action = everything after the first "." in the tool name.
    Tools whose action does NOT start with "forge_" → BrunhandHttpClient.
    Tools whose action DOES start with "forge_" → ForgeHttpClient.

    Examples:
        "smidja.screenshot"          → BrunhandHttpClient  (action = "screenshot")
        "smidja.click"               → BrunhandHttpClient  (action = "click")
        "smidja.forge_build_avatar"  → ForgeHttpClient     (action = "forge_build_avatar")
        "smidja.forge_get_avatar"    → ForgeHttpClient     (action = "forge_get_avatar")

TOOL DEFINITIONS GATING:
    tool_definitions returns only tools whose half is enabled:
        - Brúarhönd tools only if SmidjaConfig.enabled is True
        - Forge tools only if SmidjaConfig.forge.enabled is True

LIFECYCLE:
    SmidjaSense is instantiated once per ceremony. Both clients must be created
    and passed at construction time (but not yet opened). open() probes both
    health endpoints; close() closes both halves; all errors are silently
    degraded to is_available = False for that half.

Design:
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
from heretic.skilningr.senses.smidja.errors import ForgeError, SmidjaError
from heretic.skilningr.senses.smidja.forge_client import ForgeHttpClient
from heretic.skilningr.senses.smidja.tools import SMIDJA_TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

# Tool name → client method name mapping (Brúarhönd half)
_BRUNHAND_TOOL_TO_METHOD: dict[str, str] = {
    "smidja.screenshot": "screenshot",
    "smidja.click": "click",
    "smidja.type_text": "type_text",
    "smidja.hotkey": "hotkey",
    "smidja.vroid_open": "vroid_open",
    "smidja.vroid_export": "vroid_export",
}

# Forge tool names (actions starting with "forge_") — for routing only
# Full schema locked in tools.py SMIDJA_TOOL_DEFINITIONS
_FORGE_TOOL_NAMES: frozenset[str] = frozenset({
    "smidja.forge_build_avatar",
    "smidja.forge_get_avatar",
    "smidja.forge_inspect_avatar",
})


class SmidjaSense:
    """L5.5 Smiðja sense — dual-half tool surface (Brúarhönd + Forge).

    Registered in ToolDispatcher under the prefix "smidja". Routes any tool_call
    whose name starts with "smidja." to the appropriate client:
        - "smidja.forge_*" tools → ForgeHttpClient (headless Blender pipeline)
        - All other "smidja.*" tools → BrunhandHttpClient (live GUI control)

    Both halves open and close independently. If the Forge daemon is unreachable,
    Brúarhönd tools still work, and vice versa.

    Usage:
        config          = heretic_config.skilningr.smidja
        brunhand_client = BrunhandHttpClient(config, logger)
        forge_client    = ForgeHttpClient(config.forge, logger)
        sense           = SmidjaSense(config, brunhand_client, forge_client, logger)
        await sense.open()
        result = await sense.dispatch_tool_call(tool_call_dict)
        await sense.close()
    """

    def __init__(
        self,
        config: SmidjaConfig,
        client: BrunhandHttpClient,
        forge_client: ForgeHttpClient,
        logger: logging.Logger | None = None,
        event_emitter: Callable | None = None,
    ) -> None:
        """Initialise the Smiðja sense with both halves.

        Args:
            config: SmidjaConfig from HereticConfig.skilningr.smidja.
                    The Forge sub-config is at config.forge (ForgeConfig).
            client: BrunhandHttpClient for the configured Brúarhönd host.
                    Must be created before the sense but not yet opened.
            forge_client: ForgeHttpClient for the Straumur REST bridge.
                          Must be created before the sense but not yet opened.
            logger: Optional logger instance.
            event_emitter: Optional callable for emitting SenseToolCall IPC events.
                           Signature: event_emitter(event: SenseToolCall) -> None.
                           If None, events are not emitted (useful in tests and
                           when the IPC bus is not active).
        """
        self._config = config
        self._client = client                   # Brúarhönd half
        self._brunhand_client: BrunhandHttpClient = client  # alias for clarity
        self._forge_client: ForgeHttpClient = forge_client  # Forge half
        self._log = logger if logger is not None else logging.getLogger(__name__)
        self._event_emitter = event_emitter
        # Independent per-half open state
        self._brunhand_open: bool = False
        self._forge_open: bool = False

    @property
    def _is_open(self) -> bool:
        """True if either half is open (backwards compat with callers that check _is_open)."""
        return self._brunhand_open or self._forge_open

    @property
    def is_available(self) -> bool:
        """True if at least one half is enabled AND open.

        ToolDispatcher checks this before calling dispatch_tool_call. If False,
        the dispatcher returns SENSE_UNAVAILABLE error immediately.

        Note: each half's individual availability is checked inside _route.
        A call to a Forge tool still returns a structured error if only Brúarhönd
        is open; the sense as a whole remains "available" as long as one half is.

        Returns:
            True if (config.enabled and brunhand_open) or (config.forge.enabled and forge_open).
        """
        brunhand_available = self._config.enabled and self._brunhand_open
        forge_available = self._config.forge.enabled and self._forge_open
        return brunhand_available or forge_available

    @property
    def brunhand_available(self) -> bool:
        """True if the Brúarhönd half is enabled AND open."""
        return self._config.enabled and self._brunhand_open

    @property
    def forge_available(self) -> bool:
        """True if the Forge half is enabled AND open."""
        return self._config.forge.enabled and self._forge_open

    async def open(self) -> None:
        """Open both halves independently and probe each daemon's health.

        Called at ceremony start (Kynding). Each half opens independently:
        - If Brúarhönd is enabled, probes /v1/brunhand/health; failure → _brunhand_open=False
        - If Forge is enabled, probes /v1/health (Straumur); failure → _forge_open=False

        Fault tolerance invariant: NEVER raise to the caller (Kynding loop).
        All exceptions are caught and logged; the ceremony continues with whatever
        halves are successfully opened.

        NOTE: The Forge half currently raises NotImplementedError (Wave 2 stub).
        This is caught and treated as a degraded-open (forge_open=False) — the
        ceremony continues with Brúarhönd only until Forge implements.
        """
        # --- Brúarhönd half ---
        if self._config.enabled:
            try:
                await self._brunhand_client.open()
                self._brunhand_open = True
                self._log.info("Smiðja sense (Brúarhönd half) opened — hand is ready.")
            except SmidjaError as exc:
                self._log.warning(
                    "Smiðja Brúarhönd half failed to open (SmidjaError) — "
                    "ceremony continues without Brúarhönd: %s",
                    exc,
                )
                self._brunhand_open = False
            except Exception as exc:
                self._log.error(
                    "Smiðja Brúarhönd half failed to open (unexpected) — "
                    "ceremony continues without Brúarhönd: %s",
                    exc,
                    exc_info=True,
                )
                self._brunhand_open = False
        else:
            self._brunhand_open = False

        # --- Forge half ---
        if self._config.forge.enabled:
            try:
                await self._forge_client.open()
                self._forge_open = True
                self._log.info("Smiðja sense (Forge half) opened — headless pipeline ready.")
            except NotImplementedError:
                # ForgeHttpClient.open() is a Wave 2 stub — degrade gracefully
                self._log.info(
                    "Smiðja Forge half is a Wave 2 stub (NotImplementedError) — "
                    "Forge tools unavailable until ForgeHttpClient is implemented."
                )
                self._forge_open = False
            except ForgeError as exc:
                self._log.warning(
                    "Smiðja Forge half failed to open (ForgeError) — "
                    "ceremony continues without Forge: %s",
                    exc,
                )
                self._forge_open = False
            except SmidjaError as exc:
                self._log.warning(
                    "Smiðja Forge half failed to open (SmidjaError) — "
                    "ceremony continues without Forge: %s",
                    exc,
                )
                self._forge_open = False
            except Exception as exc:
                self._log.error(
                    "Smiðja Forge half failed to open (unexpected) — "
                    "ceremony continues without Forge: %s",
                    exc,
                    exc_info=True,
                )
                self._forge_open = False
        else:
            self._forge_open = False

    async def close(self) -> None:
        """Close both halves and release resources.

        Called at ceremony end (Slokna). Idempotent. Both halves are closed
        regardless of whether they were open. Errors in one half do not prevent
        the other from closing.
        """
        # --- Brúarhönd half ---
        try:
            await self._brunhand_client.close()
        except NotImplementedError:
            pass  # stub — nothing to close
        except Exception as exc:
            self._log.warning("Error closing Smiðja Brúarhönd half: %s", exc)
        finally:
            self._brunhand_open = False

        # --- Forge half ---
        try:
            await self._forge_client.close()
        except NotImplementedError:
            pass  # stub — nothing to close
        except Exception as exc:
            self._log.warning("Error closing Smiðja Forge half: %s", exc)
        finally:
            self._forge_open = False

    @property
    def tool_definitions(self) -> list[dict]:
        """Return the OpenAI tool schemas for enabled halves of the Smiðja sense.

        ToolDispatcher calls this at TENGSL to build the tools array.
        Returns the relevant subset of SMIDJA_TOOL_DEFINITIONS:
            - Brúarhönd tools (smidja.screenshot etc.) if config.enabled is True
            - Forge tools (smidja.forge_*) if config.forge.enabled is True

        Both halves may be enabled simultaneously (Mode C).
        Either half may be enabled independently.

        Returns:
            List of OpenAI tool dicts. Empty list if neither half is enabled.
        """
        result: list[dict] = []
        if self._config.enabled:
            result.extend(
                t for t in SMIDJA_TOOL_DEFINITIONS
                if not t["function"]["name"].split(".", 1)[1].startswith("forge_")
            )
        if self._config.forge.enabled:
            result.extend(
                t for t in SMIDJA_TOOL_DEFINITIONS
                if t["function"]["name"].split(".", 1)[1].startswith("forge_")
            )
        return result

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
            # SmidjaError covers BrunhandError, ForgeError and their subclasses.
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
            # Check for SkilningrError subclasses (e.g. SenseUnavailableError,
            # ToolDispatchError) which are not SmidjaError but carry known error codes.
            from heretic.skilningr.errors import SkilningrError
            if isinstance(exc, SkilningrError):
                self._log.warning(
                    "Smiðja dispatch failed for %r (SkilningrError): %s",
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
                    _skilningr_error_code(exc),
                    str(exc),
                )
            # Truly unexpected error — log as error, return generic SENSE_INTERNAL_ERROR
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
        """Route a parsed tool call to the correct client method.

        ROUTING RULE (sealed):
            The action is everything after the first "." in the tool name.
            If the action starts with "forge_" → ForgeHttpClient.
            Otherwise → BrunhandHttpClient.

        Returns the tool result content as a JSON string (or data URL for screenshots).

        Raises:
            SmidjaError and subclasses on client-level failures.
            ForgeError and subclasses on Forge client failures.
            ToolDispatchError if tool_name is unknown or its half is unavailable.
        """
        # Determine which half owns this tool call
        action = tool_name.split(".", 1)[1] if "." in tool_name else tool_name
        is_forge_tool = action.startswith("forge_")

        if is_forge_tool:
            return await self._route_forge(tool_name, action, args)
        else:
            return await self._route_brunhand(tool_name, args)

    async def _route_brunhand(self, tool_name: str, args: dict[str, Any]) -> str:
        """Route a tool call to BrunhandHttpClient.

        Raises ToolDispatchError if the Brúarhönd half is not open or the tool
        name is unrecognized. All SmidjaError subclasses propagate to the caller
        (dispatch_tool_call catches them).
        """
        from heretic.skilningr.errors import SenseUnavailableError, ToolDispatchError

        if not self._brunhand_open:
            raise SenseUnavailableError(
                f"Smiðja Brúarhönd half is not open — cannot dispatch {tool_name!r}. "
                f"Ensure skilningr.smidja.enabled: true and the daemon is reachable."
            )

        if tool_name == "smidja.screenshot":
            region = args.get("region", None)
            png_bytes = await self._brunhand_client.screenshot(region=region)
            # Re-encode raw PNG bytes as a data URL — mirrors L3 Sjón FrameEncoder format
            b64_str = base64.b64encode(png_bytes).decode("ascii")
            data_url = f"data:image/png;base64,{b64_str}"
            return json.dumps({"type": "image", "data_url": data_url})

        if tool_name == "smidja.click":
            result = await self._brunhand_client.click(
                x=args["x"],
                y=args["y"],
                button=args.get("button", "left"),
                clicks=args.get("clicks", 1),
                modifiers=args.get("modifiers", []),
            )
            return json.dumps(result)

        if tool_name == "smidja.type_text":
            result = await self._brunhand_client.type_text(
                text=args["text"],
                interval=args.get("interval", 0.05),
            )
            return json.dumps(result)

        if tool_name == "smidja.hotkey":
            result = await self._brunhand_client.hotkey(keys=args["keys"])
            return json.dumps(result)

        if tool_name == "smidja.vroid_open":
            result = await self._brunhand_client.vroid_open(
                project_path=args["project_path"],
                wait_timeout_seconds=args.get("wait_timeout_seconds", 60.0),
            )
            return json.dumps(result)

        if tool_name == "smidja.vroid_export":
            result = await self._brunhand_client.vroid_export(
                output_path=args["output_path"],
                overwrite=args.get("overwrite", True),
                wait_timeout_seconds=args.get("wait_timeout_seconds", 120.0),
            )
            return json.dumps(result)

        # Unknown Brúarhönd tool in the smidja.* namespace
        raise ToolDispatchError(
            f"Unknown Smiðja Brúarhönd tool: {tool_name!r}. "
            f"Valid Brúarhönd tools: {list(_BRUNHAND_TOOL_TO_METHOD.keys())}"
        )

    async def _route_forge(self, tool_name: str, action: str, args: dict[str, Any]) -> str:
        """Route a tool call to ForgeHttpClient.

        Raises ToolDispatchError if the Forge half is not open or the tool name
        is unrecognized. ForgeError subclasses propagate to the caller
        (dispatch_tool_call catches them via SmidjaError).

        Parameter mapping (tool schema uses "avatar_id" for both get and inspect):
            smidja.forge_build_avatar   → forge_client.build_avatar(loom_spec=args["loom_spec"])
            smidja.forge_get_avatar     → forge_client.get_avatar(session_id=args["avatar_id"])
            smidja.forge_inspect_avatar → forge_client.inspect_avatar(vrm_path=args["avatar_id"],
                                             targets=args.get("targets"))

        The tool schema exposes "avatar_id" for UX consistency; the mapping to the
        correct ForgeHttpClient parameter (session_id / vrm_path) is done here.
        See INTERFACE.md §"IMPORTANT parameter naming".
        """
        from heretic.skilningr.errors import SenseUnavailableError, ToolDispatchError

        if not self._forge_open:
            raise SenseUnavailableError(
                f"Smiðja Forge half is not open — cannot dispatch {tool_name!r}. "
                f"Ensure skilningr.smidja.forge.enabled: true and Straumur is running."
            )

        if tool_name not in _FORGE_TOOL_NAMES:
            raise ToolDispatchError(
                f"Unknown Smiðja Forge tool: {tool_name!r}. "
                f"Valid Forge tools: {sorted(_FORGE_TOOL_NAMES)}"
            )

        # Route to the correct ForgeHttpClient method
        if tool_name == "smidja.forge_build_avatar":
            result = await self._forge_client.build_avatar(
                loom_spec=args["loom_spec"],
            )
            return json.dumps(result)

        if tool_name == "smidja.forge_get_avatar":
            # Tool param "avatar_id" is the Annáll session_id
            result = await self._forge_client.get_avatar(
                session_id=args["avatar_id"],
            )
            return json.dumps(result)

        if tool_name == "smidja.forge_inspect_avatar":
            # Tool param "avatar_id" is actually the server-side vrm_path
            result = await self._forge_client.inspect_avatar(
                vrm_path=args["avatar_id"],
                targets=args.get("targets"),
            )
            return json.dumps(result)

        # Unreachable if _FORGE_TOOL_NAMES is kept in sync, but guard anyway
        raise ToolDispatchError(
            f"Forge route fell through for {tool_name!r} — this is a bug. "
            f"_FORGE_TOOL_NAMES and _route_forge dispatch table are out of sync."
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
    """Map a SmidjaError subclass to a SENSE_CONTRACTS.md error code string.

    Covers both Brúarhönd errors and Forge errors (all subclass SmidjaError).
    """
    from heretic.skilningr.senses.smidja.errors import (
        BrunhandAuthError,
        BrunhandSessionLockedError,
        BrunhandTimeoutError,
        BrunhandUnreachableError,
        ForgeTimeoutError,
        ForgeUnreachableError,
        ForgeValidationError,
    )
    from heretic.skilningr.errors import SenseUnavailableError, ToolDispatchError

    # Brúarhönd errors
    if isinstance(exc, BrunhandAuthError):
        return "PERMISSION_DENIED"
    if isinstance(exc, BrunhandUnreachableError):
        return "EXTERNAL_APP_UNAVAILABLE"
    if isinstance(exc, BrunhandTimeoutError):
        return "SENSE_TIMEOUT"
    if isinstance(exc, BrunhandSessionLockedError):
        return "SENSE_INTERNAL_ERROR"

    # Forge errors
    if isinstance(exc, ForgeUnreachableError):
        return "EXTERNAL_APP_UNAVAILABLE"
    if isinstance(exc, ForgeTimeoutError):
        return "SENSE_TIMEOUT"
    if isinstance(exc, ForgeValidationError):
        return "INVALID_ARGUMENTS"

    # Dispatcher-level errors
    if isinstance(exc, ToolDispatchError):
        return "SENSE_INTERNAL_ERROR"
    if isinstance(exc, SenseUnavailableError):
        return "SENSE_UNAVAILABLE"
    return "SENSE_INTERNAL_ERROR"


def _skilningr_error_code(exc: Exception) -> str:
    """Map any SkilningrError subclass to a SENSE_CONTRACTS.md error code string.

    Used for SkilningrError instances that are NOT SmidjaError (e.g.
    SenseUnavailableError, ToolDispatchError raised from routing helpers).
    Falls back to _smidja_error_code if the exception is also a SmidjaError.
    """
    from heretic.skilningr.errors import SenseUnavailableError, ToolDispatchError
    if isinstance(exc, SmidjaError):
        return _smidja_error_code(exc)
    if isinstance(exc, SenseUnavailableError):
        return "SENSE_UNAVAILABLE"
    if isinstance(exc, ToolDispatchError):
        return "SENSE_INTERNAL_ERROR"
    return "SENSE_INTERNAL_ERROR"
