"""
Placeholder tests for LibrarySense.

All test bodies that depend on Forge implementation are skipped.
Import-level tests (sense imports, tool_definitions shape) are live.

Covers:
    - LibrarySense import (live)
    - tool_definitions returns empty list when disabled (live, if sense.open stub allows)
    - open() raises NotImplementedError (scaffold placeholder — skip)
    - close() raises NotImplementedError (scaffold placeholder — skip)
    - dispatch_tool_call raises NotImplementedError (scaffold placeholder — skip)
    - is_available False when not open (live via property)

Ref: src/heretic/skilningr/senses/library/sense.py
"""

from __future__ import annotations

import pytest

from heretic.skilningr.config_model import LibraryConfig
from heretic.skilningr.senses.library.sense import LibrarySense
from heretic.skilningr.senses.library.tools import LIBRARY_TOOL_DEFINITIONS


class TestLibrarySenseImport:
    """Smoke tests — verify the sense imports and basic property behaviour."""

    def test_library_sense_importable(self) -> None:
        """LibrarySense must be importable from its canonical module."""
        assert LibrarySense is not None

    def test_tool_definitions_importable(self) -> None:
        """LIBRARY_TOOL_DEFINITIONS must be importable and non-empty."""
        assert len(LIBRARY_TOOL_DEFINITIONS) == 3

    def test_is_available_false_when_not_open(self) -> None:
        """is_available must be False before open() is called."""
        config = LibraryConfig(enabled=True)
        # client=None is acceptable at scaffold time — sense.open() is not called
        sense = LibrarySense(config, client=None)
        assert sense.is_available is False

    def test_is_available_false_when_disabled(self) -> None:
        """is_available must be False when enabled=False regardless of open state."""
        config = LibraryConfig(enabled=False)
        sense = LibrarySense(config, client=None)
        assert sense.is_available is False

    def test_tool_definitions_empty_when_disabled(self) -> None:
        """tool_definitions must return [] when sense is disabled."""
        config = LibraryConfig(enabled=False)
        sense = LibrarySense(config, client=None)
        assert sense.tool_definitions == []

    def test_tool_definitions_non_empty_when_enabled(self) -> None:
        """tool_definitions must return the 3 locked schemas when enabled."""
        config = LibraryConfig(enabled=True)
        sense = LibrarySense(config, client=None)
        defs = sense.tool_definitions
        assert len(defs) == 3
        names = {d["function"]["name"] for d in defs}
        assert names == {"library.search", "library.get_text", "library.list_sources"}


class TestLibrarySenseStubs:
    """Placeholder tests — unskip when Forge implements the bodies."""

    @pytest.mark.skip(reason="Forge implementation target — LibrarySense.open not yet implemented")
    async def test_open_sets_is_open(self) -> None:
        """open() must mark the sense as open when config.enabled=True."""
        from pathlib import Path
        import tempfile
        config = LibraryConfig(enabled=True)
        sense = LibrarySense(config, client=None)
        with tempfile.TemporaryDirectory() as d:
            await sense.open()
            assert sense.is_available is True

    @pytest.mark.skip(reason="Forge implementation target — LibrarySense.close not yet implemented")
    async def test_close_clears_is_open(self) -> None:
        """close() must mark the sense as not open."""
        config = LibraryConfig(enabled=True)
        sense = LibrarySense(config, client=None)
        await sense.close()
        assert sense.is_available is False

    @pytest.mark.skip(reason="Forge implementation target — LibrarySense.dispatch_tool_call not yet implemented")
    async def test_dispatch_unknown_tool_returns_error_result(self) -> None:
        """dispatch_tool_call must not raise for an unknown tool name."""
        config = LibraryConfig(enabled=True)
        sense = LibrarySense(config, client=None)
        tool_call = {
            "id": "call_001",
            "function": {"name": "library.nonexistent", "arguments": "{}"},
        }
        result = await sense.dispatch_tool_call(tool_call)
        assert result["tool_call_id"] == "call_001"
        assert result["role"] == "tool"
