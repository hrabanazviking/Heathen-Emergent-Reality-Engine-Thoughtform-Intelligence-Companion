"""
Tests for LibrarySense — L5.9 Library sense orchestrator.

Covers:
    - LibrarySense import (live)
    - tool_definitions returns empty list when disabled (live)
    - tool_definitions returns 3 schemas when enabled (live)
    - is_available False before open() (live)
    - is_available False when disabled (live)
    - open() sets is_open when enabled
    - open() does not raise when enabled=False
    - close() clears is_open
    - close() is idempotent
    - dispatch_tool_call routes library.search to client.search
    - dispatch_tool_call routes library.get_text to client.get_text
    - dispatch_tool_call routes library.list_sources to client.list_sources
    - dispatch_tool_call returns error result for unknown tool name
    - dispatch_tool_call returns error result for invalid JSON args
    - dispatch_tool_call NEVER raises — always returns dict
    - dispatch_tool_call catches LibraryError and returns error result

Ref: src/heretic/skilningr/senses/library/sense.py
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio

from heretic.skilningr.config_model import LibraryConfig
from heretic.skilningr.senses.library.errors import LibraryError
from heretic.skilningr.senses.library.sense import LibrarySense
from heretic.skilningr.senses.library.tools import LIBRARY_TOOL_DEFINITIONS


# ---------------------------------------------------------------------------
# Mock client factory
# ---------------------------------------------------------------------------

def _make_mock_client(
    search_result=None,
    get_text_result=None,
    list_sources_result=None,
):
    """Build a MagicMock LibraryClient with preconfigured return values."""
    client = MagicMock()
    client.search.return_value = search_result if search_result is not None else []
    client.get_text.return_value = get_text_result if get_text_result is not None else {
        "source_id": "prose_edda_brodeur",
        "start_line": 1,
        "num_lines": 2,
        "text": "Odin spoke.\nThor listened.",
        "total_lines_in_file": 5,
    }
    client.list_sources.return_value = list_sources_result if list_sources_result is not None else []
    return client


# ---------------------------------------------------------------------------
# Import-level / property tests
# ---------------------------------------------------------------------------

class TestLibrarySenseImport:
    """Smoke tests — verify the sense imports and basic property behaviour."""

    def test_library_sense_importable(self) -> None:
        assert LibrarySense is not None

    def test_tool_definitions_importable(self) -> None:
        assert len(LIBRARY_TOOL_DEFINITIONS) == 3

    def test_is_available_false_when_not_open(self) -> None:
        config = LibraryConfig(enabled=True)
        sense = LibrarySense(config, client=None)
        assert sense.is_available is False

    def test_is_available_false_when_disabled(self) -> None:
        config = LibraryConfig(enabled=False)
        sense = LibrarySense(config, client=None)
        assert sense.is_available is False

    def test_tool_definitions_empty_when_disabled(self) -> None:
        config = LibraryConfig(enabled=False)
        sense = LibrarySense(config, client=None)
        assert sense.tool_definitions == []

    def test_tool_definitions_non_empty_when_enabled(self) -> None:
        config = LibraryConfig(enabled=True)
        sense = LibrarySense(config, client=None)
        defs = sense.tool_definitions
        assert len(defs) == 3
        names = {d["function"]["name"] for d in defs}
        assert names == {"library.search", "library.get_text", "library.list_sources"}


# ---------------------------------------------------------------------------
# open() / close()
# ---------------------------------------------------------------------------

class TestLibrarySenseLifecycle:
    """Tests for sense open/close lifecycle."""

    @pytest.mark.asyncio
    async def test_open_sets_is_open_when_enabled(self, tmp_path: Path) -> None:
        config = LibraryConfig(enabled=True, storage_path=str(tmp_path))
        sense = LibrarySense(config, client=_make_mock_client())
        await sense.open()
        assert sense.is_available is True

    @pytest.mark.asyncio
    async def test_open_does_not_set_is_open_when_disabled(
        self, tmp_path: Path
    ) -> None:
        config = LibraryConfig(enabled=False, storage_path=str(tmp_path))
        sense = LibrarySense(config, client=None)
        await sense.open()
        assert sense.is_available is False

    @pytest.mark.asyncio
    async def test_close_clears_is_open(self, tmp_path: Path) -> None:
        config = LibraryConfig(enabled=True, storage_path=str(tmp_path))
        sense = LibrarySense(config, client=_make_mock_client())
        await sense.open()
        assert sense.is_available is True
        await sense.close()
        assert sense.is_available is False

    @pytest.mark.asyncio
    async def test_close_idempotent(self, tmp_path: Path) -> None:
        config = LibraryConfig(enabled=True, storage_path=str(tmp_path))
        sense = LibrarySense(config, client=_make_mock_client())
        await sense.close()
        await sense.close()  # second call must not raise
        assert sense.is_available is False

    @pytest.mark.asyncio
    async def test_open_does_not_raise_on_storage_error(self) -> None:
        """open() must not raise even if storage_path is invalid."""
        config = LibraryConfig(
            enabled=True,
            storage_path="/nonexistent/path/that/cannot/exist/xyzabc"
        )
        sense = LibrarySense(config, client=_make_mock_client())
        # Must not raise
        await sense.open()
        # is_available may be True or False depending on mkdir success;
        # on Windows readonly dirs this might fail, but it must not crash


# ---------------------------------------------------------------------------
# dispatch_tool_call — routing
# ---------------------------------------------------------------------------

class TestLibrarySenseDispatch:
    """Tests for dispatch_tool_call routing and error handling."""

    @pytest.mark.asyncio
    async def test_dispatch_search_routes_to_client_search(
        self, tmp_path: Path
    ) -> None:
        search_result = [
            {"source_id": "prose_edda_brodeur", "line_number": 1,
             "context_text": "Odin spoke.", "match_position": 0}
        ]
        mock_client = _make_mock_client(search_result=search_result)
        config = LibraryConfig(enabled=True, storage_path=str(tmp_path))
        sense = LibrarySense(config, mock_client)
        await sense.open()

        tool_call = {
            "id": "call_001",
            "function": {
                "name": "library.search",
                "arguments": json.dumps({"query": "Odin", "max_results": 5}),
            },
        }
        result = await sense.dispatch_tool_call(tool_call)
        assert result["tool_call_id"] == "call_001"
        assert result["role"] == "tool"
        mock_client.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_get_text_routes_to_client_get_text(
        self, tmp_path: Path
    ) -> None:
        mock_client = _make_mock_client()
        config = LibraryConfig(enabled=True, storage_path=str(tmp_path))
        sense = LibrarySense(config, mock_client)
        await sense.open()

        tool_call = {
            "id": "call_002",
            "function": {
                "name": "library.get_text",
                "arguments": json.dumps({
                    "source_id": "prose_edda_brodeur",
                    "start_line": 1,
                    "num_lines": 10,
                }),
            },
        }
        result = await sense.dispatch_tool_call(tool_call)
        assert result["tool_call_id"] == "call_002"
        mock_client.get_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_list_sources_routes_to_client_list_sources(
        self, tmp_path: Path
    ) -> None:
        list_result = [{"id": "prose_edda_brodeur", "downloaded": False}]
        mock_client = _make_mock_client(list_sources_result=list_result)
        config = LibraryConfig(enabled=True, storage_path=str(tmp_path))
        sense = LibrarySense(config, mock_client)
        await sense.open()

        tool_call = {
            "id": "call_003",
            "function": {
                "name": "library.list_sources",
                "arguments": "{}",
            },
        }
        result = await sense.dispatch_tool_call(tool_call)
        assert result["tool_call_id"] == "call_003"
        mock_client.list_sources.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_unknown_tool_returns_error_result(
        self, tmp_path: Path
    ) -> None:
        config = LibraryConfig(enabled=True, storage_path=str(tmp_path))
        sense = LibrarySense(config, client=_make_mock_client())
        await sense.open()

        tool_call = {
            "id": "call_bad",
            "function": {"name": "library.nonexistent", "arguments": "{}"},
        }
        result = await sense.dispatch_tool_call(tool_call)
        assert result["tool_call_id"] == "call_bad"
        assert result["role"] == "tool"
        content = json.loads(result["content"])
        assert content["error"] is True

    @pytest.mark.asyncio
    async def test_dispatch_invalid_json_args_returns_error(
        self, tmp_path: Path
    ) -> None:
        config = LibraryConfig(enabled=True, storage_path=str(tmp_path))
        sense = LibrarySense(config, client=_make_mock_client())
        await sense.open()

        tool_call = {
            "id": "call_broken",
            "function": {
                "name": "library.search",
                "arguments": "not valid json {{{",
            },
        }
        result = await sense.dispatch_tool_call(tool_call)
        assert result["tool_call_id"] == "call_broken"
        content = json.loads(result["content"])
        assert content["error"] is True
        assert "INVALID_ARGUMENTS" in content["code"]

    @pytest.mark.asyncio
    async def test_dispatch_never_raises_on_library_error(
        self, tmp_path: Path
    ) -> None:
        """dispatch_tool_call must never raise even when client raises LibraryError."""
        mock_client = MagicMock()
        mock_client.search.side_effect = LibraryError("index not built")
        config = LibraryConfig(enabled=True, storage_path=str(tmp_path))
        sense = LibrarySense(config, mock_client)
        await sense.open()

        tool_call = {
            "id": "call_err",
            "function": {
                "name": "library.search",
                "arguments": json.dumps({"query": "Odin"}),
            },
        }
        # Must not raise
        result = await sense.dispatch_tool_call(tool_call)
        assert result["role"] == "tool"
        content = json.loads(result["content"])
        assert content["error"] is True

    @pytest.mark.asyncio
    async def test_dispatch_never_raises_on_unexpected_exception(
        self, tmp_path: Path
    ) -> None:
        """dispatch_tool_call must not raise even on RuntimeError from client."""
        mock_client = MagicMock()
        mock_client.search.side_effect = RuntimeError("unexpected boom")
        config = LibraryConfig(enabled=True, storage_path=str(tmp_path))
        sense = LibrarySense(config, mock_client)
        await sense.open()

        tool_call = {
            "id": "call_boom",
            "function": {
                "name": "library.search",
                "arguments": json.dumps({"query": "Odin"}),
            },
        }
        result = await sense.dispatch_tool_call(tool_call)
        assert result["role"] == "tool"
        content = json.loads(result["content"])
        assert content["error"] is True

    @pytest.mark.asyncio
    async def test_dispatch_search_result_content_is_json(
        self, tmp_path: Path
    ) -> None:
        mock_client = _make_mock_client(search_result=[])
        config = LibraryConfig(enabled=True, storage_path=str(tmp_path))
        sense = LibrarySense(config, mock_client)
        await sense.open()

        tool_call = {
            "id": "call_json",
            "function": {
                "name": "library.search",
                "arguments": json.dumps({"query": "Odin"}),
            },
        }
        result = await sense.dispatch_tool_call(tool_call)
        # content must be valid JSON string
        parsed = json.loads(result["content"])
        assert "results" in parsed or "error" in parsed
