"""
Placeholder tests for SkepjaSense — L5.2 terminal sense orchestrator.

Ref: src/heretic/skilningr/senses/skepja/sense.py
"""

from __future__ import annotations

import pytest

from heretic.skilningr.config_model import SkepjaConfig
from heretic.skilningr.senses.skepja.client import SkepjaClient
from heretic.skilningr.senses.skepja.sense import SkepjaSense
from heretic.skilningr.senses.skepja.tools import SKEPJA_TOOL_DEFINITIONS


class TestSkepjaConfig:

    def test_skepja_config_defaults_disabled(self):
        """SkepjaConfig defaults to enabled=False."""
        config = SkepjaConfig()
        assert config.enabled is False

    def test_skepja_config_default_allowlist_empty(self):
        """SkepjaConfig default command_allowlist is empty."""
        config = SkepjaConfig()
        assert config.command_allowlist == []

    def test_skepja_config_invalid_timeout_raises(self):
        """timeout_seconds <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="timeout_seconds"):
            SkepjaConfig(timeout_seconds=0)

    def test_skepja_config_invalid_output_bytes_raises(self):
        """max_output_bytes <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="max_output_bytes"):
            SkepjaConfig(max_output_bytes=-1)


class TestSkepjaSenseLifecycle:

    @pytest.mark.asyncio
    async def test_sense_disabled_not_available(self):
        """A disabled SkepjaSense is not available."""
        config = SkepjaConfig(enabled=False)
        client = SkepjaClient(config)
        sense = SkepjaSense(config, client)
        await sense.open()
        assert sense.is_available is False

    @pytest.mark.asyncio
    async def test_sense_enabled_is_available(self):
        """An enabled SkepjaSense is available after open."""
        config = SkepjaConfig(enabled=True)
        client = SkepjaClient(config)
        sense = SkepjaSense(config, client)
        await sense.open()
        assert sense.is_available is True

    @pytest.mark.asyncio
    async def test_sense_close_marks_unavailable(self):
        """Closing a SkepjaSense marks it unavailable."""
        config = SkepjaConfig(enabled=True)
        client = SkepjaClient(config)
        sense = SkepjaSense(config, client)
        await sense.open()
        await sense.close()
        assert sense.is_available is False


class TestSkepjaSenseToolDefinitions:

    def test_tool_definitions_when_enabled(self):
        """tool_definitions returns 2 tools when enabled."""
        config = SkepjaConfig(enabled=True)
        client = SkepjaClient(config)
        sense = SkepjaSense(config, client)
        assert len(sense.tool_definitions) == 2

    def test_tool_definitions_when_disabled(self):
        """tool_definitions returns empty list when disabled."""
        config = SkepjaConfig(enabled=False)
        client = SkepjaClient(config)
        sense = SkepjaSense(config, client)
        assert sense.tool_definitions == []

    def test_tool_names_locked(self):
        """The two Skepja tool names are locked as specified."""
        names = {t["function"]["name"] for t in SKEPJA_TOOL_DEFINITIONS}
        assert "skepja.run_command" in names
        assert "skepja.get_working_directory" in names


@pytest.mark.skip(reason="Wave 2 — SkepjaClient not yet implemented by Forge")
class TestSkepjaSenseDispatch:

    @pytest.mark.asyncio
    async def test_run_command_dispatches(self):
        pass

    @pytest.mark.asyncio
    async def test_get_working_directory_dispatches(self):
        pass
