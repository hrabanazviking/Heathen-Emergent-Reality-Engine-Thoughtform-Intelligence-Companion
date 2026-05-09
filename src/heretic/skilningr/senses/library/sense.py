"""
LibrarySense — L5.9 Library sense orchestrator (Mímisbrunnr).

LibrarySense is the boundary between ToolDispatcher and LibraryClient.
It owns:
    - Sense lifecycle (open/close)
    - Tool call routing (dispatch_tool_call routes to LibraryClient)
    - Result encoding (success payloads and errors into OpenAI tool_result)
    - Event emission (SenseToolCall events via optional event_emitter)

It does NOT own:
    - Corpus data (KeywordIndex, store — mimisbrunnr subpackage)
    - Tool schema definitions (tools.py LIBRARY_TOOL_DEFINITIONS)
    - Config (LibraryConfig, passed from HereticConfig.skilningr.library)
    - Agent message routing (ToolDispatcher)

LIFECYCLE:
    LibrarySense.open() resolves storage_path (via platformdirs if empty),
    calls ensure_storage_directory, and optionally rebuilds the keyword
    index if autoindex_on_open=True and the index does not yet exist.
    None of this raises to the caller — degraded state is logged and
    is_available returns False.

    dispatch_tool_call NEVER raises — all errors return structured
    tool_result dicts per SENSE_CONTRACTS.md §3.

Ref: docs/architecture/LAYER_INTERFACES.md §L5 Skilningr
     docs/architecture/SENSE_CONTRACTS.md §1 (lifecycle) §3 (error format)
     src/heretic/skilningr/senses/library/INTERFACE.md
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from heretic.skilningr.config_model import LibraryConfig
from heretic.skilningr.senses.library.errors import LibraryError
from heretic.skilningr.senses.library.tools import LIBRARY_TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

# Valid tool names for routing — derived from LIBRARY_TOOL_DEFINITIONS at import time
_LIBRARY_TOOL_NAMES: frozenset[str] = frozenset(
    t["function"]["name"] for t in LIBRARY_TOOL_DEFINITIONS
)


class LibrarySense:
    """L5.9 Library sense — Norse corpus access tool surface.

    Registered in ToolDispatcher under the prefix "library". Routes any
    tool_call whose name starts with "library." to LibraryClient.

    Usage:
        config = heretic_config.skilningr.library
        client = LibraryClient(config, data_dir)
        sense  = LibrarySense(config, client)
        await sense.open()
        result = await sense.dispatch_tool_call(tool_call_dict)
        await sense.close()
    """

    def __init__(
        self,
        config: LibraryConfig,
        client: Any,  # LibraryClient — typed Any to avoid circular import
        log: logging.Logger | None = None,
        event_emitter: Callable | None = None,
    ) -> None:
        """Initialise the Library sense.

        Args:
            config:        LibraryConfig from HereticConfig.skilningr.library.
            client:        LibraryClient — the corpus accessor.
            log:           Optional logger instance.
            event_emitter: Optional callable for SenseToolCall IPC events.
        """
        self._config = config
        self._client = client
        self._log = log if log is not None else logging.getLogger(__name__)
        self._event_emitter = event_emitter
        self._is_open: bool = False
        self._data_dir: Path | None = None

    @property
    def is_available(self) -> bool:
        """True if the sense is enabled AND open."""
        return self._config.enabled and self._is_open

    async def open(self) -> None:
        """Open the Library sense — resolve storage path and prepare index.

        Called at ceremony start (Kynding). Does not raise — all exceptions
        are caught and logged; the ceremony continues with is_available=False
        if open fails.

        Steps:
          1. If not enabled, return (is_open remains False).
          2. Resolve storage_path via platformdirs if config.storage_path is empty.
          3. Call ensure_storage_directory on the resolved path.
          4. If config.autoindex_on_open is True and no index file exists,
             attempt to build the keyword index (failures are warnings only).
          5. Set self._is_open = True.
        """
        if not self._config.enabled:
            self._is_open = False
            return

        try:
            # 1. Resolve the data directory
            data_dir = self._resolve_data_dir()
            self._data_dir = data_dir

            # 2. Ensure the directory exists
            from heretic.skilningr.mimisbrunnr.store import ensure_storage_directory
            ensure_storage_directory(data_dir)

            # 3. Optionally build the index on open
            if self._config.autoindex_on_open:
                index_path = data_dir / "keyword_index.jsonl"
                if not index_path.exists():
                    try:
                        from heretic.skilningr.mimisbrunnr.index import KeywordIndex
                        idx = KeywordIndex(data_dir)
                        idx.build(data_dir)
                        self._log.info(
                            "LibrarySense.open: keyword index built at %s", index_path
                        )
                    except Exception as exc:
                        # Index build failure is non-fatal — log and continue
                        self._log.warning(
                            "LibrarySense.open: autoindex failed (non-fatal): %s", exc
                        )

            self._is_open = True
            self._log.info("Library sense opened. data_dir=%s", data_dir)

        except Exception as exc:
            self._log.error(
                "Library sense failed to open: %s", exc, exc_info=True
            )
            self._is_open = False

    async def close(self) -> None:
        """Close the Library sense and release any resources.

        Idempotent. No persistent connection in v0.7.
        """
        self._is_open = False

    @property
    def tool_definitions(self) -> list[dict]:
        """Return the OpenAI tool schemas when the sense is enabled."""
        return list(LIBRARY_TOOL_DEFINITIONS) if self._config.enabled else []

    async def dispatch_tool_call(self, tool_call: dict) -> dict:
        """Route a tool_call to the appropriate LibraryClient method.

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

        except LibraryError as exc:
            duration_ms = int((time.monotonic() - t_start) * 1000)
            self._log.warning("Library dispatch failed for %r: %s", tool_name, exc)
            self._emit_event("failed", call_id, tool_name, duration_ms, str(exc))
            return _error_tool_result(
                call_id, tool_name, _library_error_code(exc), str(exc)
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - t_start) * 1000)
            self._log.error(
                "Library dispatch raised unexpected error for %r: %s",
                tool_name, exc, exc_info=True,
            )
            self._emit_event("failed", call_id, tool_name, duration_ms, str(exc))
            return _error_tool_result(
                call_id, tool_name, "SENSE_INTERNAL_ERROR",
                f"Unexpected error during Library tool dispatch: {type(exc).__name__}",
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_data_dir(self) -> Path:
        """Resolve the Mímisbrunnr data directory.

        If config.storage_path is set, expand ~ and use it.
        Otherwise, resolve via platformdirs.user_data_dir.

        Returns:
            Absolute Path to the data directory.
        """
        if self._config.storage_path:
            return Path(self._config.storage_path).expanduser().resolve()

        try:
            from platformdirs import user_data_dir
            base = Path(user_data_dir("heretic", appauthor=False))
        except ImportError:
            # Fallback if platformdirs not installed — should not happen
            base = Path.home() / ".local" / "share" / "heretic"

        return base / "library" / "mimisbrunnr"

    async def _route(self, tool_name: str, args: dict[str, Any]) -> str:
        """Route a parsed tool call to the LibraryClient method.

        Raises LibraryError subclasses on failure.
        Raises ToolDispatchError for unknown tool names.
        """
        from heretic.skilningr.errors import ToolDispatchError

        if tool_name not in _LIBRARY_TOOL_NAMES:
            raise ToolDispatchError(
                f"Unknown Library tool: {tool_name!r}. "
                f"Valid tools: {sorted(_LIBRARY_TOOL_NAMES)}"
            )

        if tool_name == "library.search":
            query = args.get("query", "")
            max_results = args.get("max_results", self._config.max_results)
            result = self._client.search(query, max_results=max_results)
            return json.dumps({"results": result, "count": len(result)})

        if tool_name == "library.get_text":
            source_id = args["source_id"]
            start_line = args.get("start_line", 1)
            num_lines = args.get("num_lines", 50)
            result = self._client.get_text(
                source_id,
                start_line=start_line,
                num_lines=num_lines,
            )
            return json.dumps(result)

        if tool_name == "library.list_sources":
            result = self._client.list_sources()
            return json.dumps({"sources": result})

        # Unreachable if _LIBRARY_TOOL_NAMES is kept in sync
        raise ToolDispatchError(
            f"Library route fell through for {tool_name!r} — routing table out of sync."
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
            self._log.warning("Library: event emission failed (non-fatal): %s", exc)


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


def _library_error_code(exc: LibraryError) -> str:
    """Map a LibraryError subclass to a SENSE_CONTRACTS.md error code string."""
    from heretic.skilningr.mimisbrunnr.errors import (
        ConsentRefused,
        IntegrityError,
        LibraryDownloadError,
        LibraryIndexError,
        ManifestError,
    )
    if isinstance(exc, ConsentRefused):
        return "PERMISSION_DENIED"
    if isinstance(exc, LibraryDownloadError):
        return "EXTERNAL_APP_UNAVAILABLE"
    if isinstance(exc, (IntegrityError, ManifestError, LibraryIndexError)):
        return "SENSE_INTERNAL_ERROR"
    return "SENSE_INTERNAL_ERROR"
