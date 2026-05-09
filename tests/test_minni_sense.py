"""
Placeholder tests for MinniSense — L5.1 filesystem sense orchestrator.

These tests verify sense lifecycle and dispatch routing. Client implementation
is a Wave 2 Forge task — client method calls raise NotImplementedError until
then.

Ref: src/heretic/skilningr/senses/minni/sense.py
     TASK_HERETIC_v0.6.2_MORE_SENSES.md
"""

from __future__ import annotations

import pytest

from heretic.skilningr.config_model import MinniConfig
from heretic.skilningr.senses.minni.client import MinniClient
from heretic.skilningr.senses.minni.sense import MinniSense
from heretic.skilningr.senses.minni.tools import MINNI_TOOL_DEFINITIONS


class TestMinniSenseConfig:

    def test_minni_config_defaults_disabled(self):
        """MinniConfig defaults to enabled=False."""
        config = MinniConfig()
        assert config.enabled is False

    def test_minni_config_default_roots(self):
        """MinniConfig default allowed_roots contains the workspace path."""
        config = MinniConfig()
        assert len(config.allowed_roots) >= 1
        assert any("heretic_workspace" in r for r in config.allowed_roots)

    def test_minni_config_invalid_read_bytes_raises(self):
        """max_read_bytes <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="max_read_bytes"):
            MinniConfig(max_read_bytes=0)

    def test_minni_config_invalid_write_bytes_raises(self):
        """max_write_bytes <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="max_write_bytes"):
            MinniConfig(max_write_bytes=-1)


class TestMinniSenseLifecycle:

    @pytest.mark.asyncio
    async def test_sense_disabled_not_available(self):
        """A disabled MinniSense is not available."""
        config = MinniConfig(enabled=False)
        client = MinniClient(config)
        sense = MinniSense(config, client)
        await sense.open()
        assert sense.is_available is False

    @pytest.mark.asyncio
    async def test_sense_enabled_is_available(self):
        """An enabled MinniSense is available after open."""
        config = MinniConfig(enabled=True)
        client = MinniClient(config)
        sense = MinniSense(config, client)
        await sense.open()
        assert sense.is_available is True

    @pytest.mark.asyncio
    async def test_sense_close_marks_unavailable(self):
        """Closing a MinniSense marks it unavailable."""
        config = MinniConfig(enabled=True)
        client = MinniClient(config)
        sense = MinniSense(config, client)
        await sense.open()
        await sense.close()
        assert sense.is_available is False


class TestMinniSenseToolDefinitions:

    def test_tool_definitions_when_enabled(self):
        """tool_definitions returns 3 tools when enabled."""
        config = MinniConfig(enabled=True)
        client = MinniClient(config)
        sense = MinniSense(config, client)
        defs = sense.tool_definitions
        assert len(defs) == 3

    def test_tool_definitions_when_disabled(self):
        """tool_definitions returns empty list when disabled."""
        config = MinniConfig(enabled=False)
        client = MinniClient(config)
        sense = MinniSense(config, client)
        defs = sense.tool_definitions
        assert defs == []

    def test_tool_names_locked(self):
        """The three Minni tool names are locked as specified."""
        names = {t["function"]["name"] for t in MINNI_TOOL_DEFINITIONS}
        assert "minni.read_file" in names
        assert "minni.write_file" in names
        assert "minni.list_directory" in names


@pytest.mark.skip(reason="Wave 2 — MinniClient not yet implemented by Forge")
class TestMinniSenseDispatch:

    @pytest.mark.asyncio
    async def test_read_file_dispatch(self, tmp_path):
        """read_file dispatches to client and returns structured result."""
        pass

    @pytest.mark.asyncio
    async def test_write_file_dispatch(self, tmp_path):
        """write_file dispatches to client and returns structured result."""
        pass

    @pytest.mark.asyncio
    async def test_list_directory_dispatch(self, tmp_path):
        """list_directory dispatches to client and returns structured result."""
        pass
