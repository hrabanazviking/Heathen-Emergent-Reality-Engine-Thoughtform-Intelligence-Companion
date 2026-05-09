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
    index if autoindex_on_open=True and the index is stale. None of this
    raises to the caller — degraded state is logged and is_available
    returns False.

    dispatch_tool_call NEVER raises — all errors return structured
    tool_result dicts per SENSE_CONTRACTS.md §3.

Ref: docs/architecture/LAYER_INTERFACES.md §L5 Skilningr
     docs/architecture/SENSE_CONTRACTS.md §1 (lifecycle) §3 (error format)
     src/heretic/skilningr/senses/library/INTERFACE.md
"""

from __future__ import annotations

import logging
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

    Usage (Forge implements bodies):
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
        client: Any,  # LibraryClient — typed Any to avoid circular import at scaffold
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

    @property
    def is_available(self) -> bool:
        """True if the sense is enabled AND open."""
        return self._config.enabled and self._is_open

    async def open(self) -> None:
        """Open the Library sense — resolve storage path and prepare index.

        Called at ceremony start (Kynding). Does not raise — all exceptions
        are caught and logged; the ceremony continues with is_available=False
        if open fails.

        Raises:
            NotImplementedError: Forge implements the body.
        """
        raise NotImplementedError(
            "LibrarySense.open is a Forge implementation target. "
            "Body: if not enabled, return; resolve storage_path via "
            "platformdirs if empty; call ensure_storage_directory; "
            "if autoindex_on_open and index stale, call KeywordIndex.build; "
            "set self._is_open = True."
        )

    async def close(self) -> None:
        """Close the Library sense and release any resources.

        Idempotent. No persistent connection in v0.7.

        Raises:
            NotImplementedError: Forge implements the body.
        """
        raise NotImplementedError(
            "LibrarySense.close is a Forge implementation target. "
            "Body: self._is_open = False."
        )

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

        Raises:
            NotImplementedError: Forge implements the body.
        """
        raise NotImplementedError(
            "LibrarySense.dispatch_tool_call is a Forge implementation target. "
            "Body mirrors MinniSense.dispatch_tool_call: parse args; route to "
            "client.search / client.get_text / client.list_sources; catch "
            "LibraryError; return structured tool_result dict."
        )
