"""
Placeholder tests for LeidSense — L5.3 HTTP fetch sense orchestrator.

Ref: src/heretic/skilningr/senses/leid/sense.py
"""

from __future__ import annotations

import pytest

from heretic.skilningr.config_model import LeidConfig
from heretic.skilningr.senses.leid.client import LeidClient
from heretic.skilningr.senses.leid.sense import LeidSense
from heretic.skilningr.senses.leid.tools import LEID_TOOL_DEFINITIONS


class TestLeidConfig:

    def test_leid_config_defaults_disabled(self):
        """LeidConfig defaults to enabled=False."""
        config = LeidConfig()
        assert config.enabled is False

    def test_leid_config_default_patterns_empty(self):
        """LeidConfig default url_allowlist_patterns is empty."""
        config = LeidConfig()
        assert config.url_allowlist_patterns == []

    def test_leid_config_https_only_by_default(self):
        """LeidConfig defaults allow_http to False."""
        config = LeidConfig()
        assert config.allow_http is False

    def test_leid_config_invalid_timeout_raises(self):
        """timeout_seconds <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="timeout_seconds"):
            LeidConfig(timeout_seconds=0)

    def test_leid_config_invalid_response_bytes_raises(self):
        """max_response_bytes <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="max_response_bytes"):
            LeidConfig(max_response_bytes=0)

    def test_leid_config_invalid_redirects_raises(self):
        """max_redirects < 0 raises ValueError."""
        with pytest.raises(ValueError, match="max_redirects"):
            LeidConfig(max_redirects=-1)

    def test_leid_config_empty_user_agent_raises(self):
        """An empty user_agent raises ValueError."""
        with pytest.raises(ValueError, match="user_agent"):
            LeidConfig(user_agent="")

    def test_leid_config_wildcard_warns_when_enabled(self):
        """A '*' pattern in url_allowlist_patterns emits a warning when enabled=True."""
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            LeidConfig(enabled=True, url_allowlist_patterns=["*"])
        assert any("wildcard" in str(warning.message).lower()
                   or "unrestricted" in str(warning.message).lower()
                   for warning in w)


class TestLeidSenseLifecycle:

    @pytest.mark.asyncio
    async def test_sense_disabled_not_available(self):
        config = LeidConfig(enabled=False)
        client = LeidClient(config)
        sense = LeidSense(config, client)
        await sense.open()
        assert sense.is_available is False

    @pytest.mark.asyncio
    async def test_sense_enabled_is_available(self):
        config = LeidConfig(enabled=True, url_allowlist_patterns=["https://example.com/*"])
        client = LeidClient(config)
        sense = LeidSense(config, client)
        await sense.open()
        assert sense.is_available is True

    @pytest.mark.asyncio
    async def test_sense_close_marks_unavailable(self):
        config = LeidConfig(enabled=True, url_allowlist_patterns=["https://example.com/*"])
        client = LeidClient(config)
        sense = LeidSense(config, client)
        await sense.open()
        await sense.close()
        assert sense.is_available is False


class TestLeidSenseToolDefinitions:

    def test_tool_definitions_when_enabled(self):
        """tool_definitions returns 2 tools when enabled."""
        config = LeidConfig(enabled=True, url_allowlist_patterns=["https://example.com/*"])
        client = LeidClient(config)
        sense = LeidSense(config, client)
        assert len(sense.tool_definitions) == 2

    def test_tool_definitions_when_disabled(self):
        """tool_definitions returns empty list when disabled."""
        config = LeidConfig(enabled=False)
        client = LeidClient(config)
        sense = LeidSense(config, client)
        assert sense.tool_definitions == []

    def test_tool_names_locked(self):
        """The two Leið tool names are locked as specified."""
        names = {t["function"]["name"] for t in LEID_TOOL_DEFINITIONS}
        assert "leid.fetch_url" in names
        assert "leid.extract_text" in names


@pytest.mark.skip(reason="Wave 2 — LeidClient not yet implemented by Forge")
class TestLeidSenseDispatch:

    @pytest.mark.asyncio
    async def test_fetch_url_dispatches(self):
        pass

    @pytest.mark.asyncio
    async def test_extract_text_dispatches(self):
        pass
