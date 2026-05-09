"""
Tests for LeidSense — L5.3 HTTP fetch sense orchestrator.

Covers:
    - Config validation
    - Sense lifecycle (open/close/is_available)
    - Tool definitions
    - dispatch_tool_call routing (mocked client)
    - Error handling (UrlNotAllowedError, LeidTimeoutError, etc.)
    - JSON argument errors

Ref: src/heretic/skilningr/senses/leid/sense.py
     TASK_HERETIC_v0.6.2_MORE_SENSES.md
"""

from __future__ import annotations

import json
import warnings
from unittest.mock import AsyncMock, MagicMock

import pytest

from heretic.skilningr.config_model import LeidConfig
from heretic.skilningr.senses.leid.client import LeidClient
from heretic.skilningr.senses.leid.errors import (
    LeidConnectionError,
    LeidTimeoutError,
    UrlNotAllowedError,
)
from heretic.skilningr.senses.leid.sense import LeidSense
from heretic.skilningr.senses.leid.tools import LEID_TOOL_DEFINITIONS


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

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
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            LeidConfig(enabled=True, url_allowlist_patterns=["*"])
        assert any(
            "wildcard" in str(warning.message).lower()
            or "unrestricted" in str(warning.message).lower()
            for warning in w
        )


# ---------------------------------------------------------------------------
# Sense lifecycle
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# dispatch_tool_call — routing and error handling (mocked client)
# ---------------------------------------------------------------------------

class TestLeidSenseDispatch:

    def _make_tool_call(self, name: str, args: dict) -> dict:
        return {
            "id": "call_l01",
            "function": {
                "name": name,
                "arguments": json.dumps(args),
            },
        }

    @pytest.mark.asyncio
    async def test_fetch_url_dispatch_success(self):
        """dispatch_tool_call routes leid.fetch_url and returns result."""
        config = LeidConfig(
            enabled=True,
            url_allowlist_patterns=["https://example.com/*"],
        )
        mock_client = MagicMock(spec=LeidClient)
        mock_client.fetch_url = AsyncMock(return_value={
            "url": "https://example.com/page",
            "status_code": 200,
            "content_type": "text/html",
            "body": "<html><body>Hello</body></html>",
            "size_bytes": 30,
            "truncated": False,
        })
        sense = LeidSense(config, mock_client)
        await sense.open()
        tool_call = self._make_tool_call("leid.fetch_url", {"url": "https://example.com/page"})
        result = await sense.dispatch_tool_call(tool_call)
        assert result["role"] == "tool"
        parsed = json.loads(result["content"])
        assert parsed["status_code"] == 200
        assert parsed["truncated"] is False

    @pytest.mark.asyncio
    async def test_extract_text_dispatch_success(self):
        """dispatch_tool_call routes leid.extract_text and returns result."""
        config = LeidConfig(
            enabled=True,
            url_allowlist_patterns=["https://example.com/*"],
        )
        mock_client = MagicMock(spec=LeidClient)
        mock_client.extract_text = AsyncMock(return_value={
            "url": "https://example.com/page",
            "text": "Hello World",
            "title": "Example",
            "source_size_bytes": 100,
            "truncated": False,
        })
        sense = LeidSense(config, mock_client)
        await sense.open()
        tool_call = self._make_tool_call("leid.extract_text", {"url": "https://example.com/page"})
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["text"] == "Hello World"
        assert parsed["title"] == "Example"

    @pytest.mark.asyncio
    async def test_url_not_allowed_returns_error_result(self):
        """dispatch_tool_call returns error tool_result on UrlNotAllowedError."""
        config = LeidConfig(
            enabled=True,
            url_allowlist_patterns=["https://example.com/*"],
        )
        mock_client = MagicMock(spec=LeidClient)
        mock_client.fetch_url = AsyncMock(side_effect=UrlNotAllowedError("not allowed"))
        sense = LeidSense(config, mock_client)
        await sense.open()
        tool_call = self._make_tool_call("leid.fetch_url", {"url": "https://evil.com/steal"})
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["error"] is True
        assert parsed["code"] == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_leid_timeout_returns_error_result(self):
        """dispatch_tool_call returns error tool_result on LeidTimeoutError."""
        config = LeidConfig(
            enabled=True,
            url_allowlist_patterns=["https://example.com/*"],
        )
        mock_client = MagicMock(spec=LeidClient)
        mock_client.fetch_url = AsyncMock(side_effect=LeidTimeoutError("timeout"))
        sense = LeidSense(config, mock_client)
        await sense.open()
        tool_call = self._make_tool_call("leid.fetch_url", {"url": "https://example.com/slow"})
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["error"] is True
        assert parsed["code"] == "SENSE_TIMEOUT"

    @pytest.mark.asyncio
    async def test_connection_error_returns_error_result(self):
        """dispatch_tool_call returns error tool_result on LeidConnectionError."""
        config = LeidConfig(
            enabled=True,
            url_allowlist_patterns=["https://example.com/*"],
        )
        mock_client = MagicMock(spec=LeidClient)
        mock_client.fetch_url = AsyncMock(side_effect=LeidConnectionError("refused"))
        sense = LeidSense(config, mock_client)
        await sense.open()
        tool_call = self._make_tool_call("leid.fetch_url", {"url": "https://example.com/down"})
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["error"] is True
        assert parsed["code"] == "EXTERNAL_APP_UNAVAILABLE"

    @pytest.mark.asyncio
    async def test_invalid_json_args_returns_error_result(self):
        """dispatch_tool_call returns error result when arguments are invalid JSON."""
        config = LeidConfig(enabled=True, url_allowlist_patterns=["*"])
        mock_client = MagicMock(spec=LeidClient)
        sense = LeidSense(config, mock_client)
        await sense.open()
        bad_call = {
            "id": "call_bad",
            "function": {"name": "leid.fetch_url", "arguments": "{bad json"},
        }
        result = await sense.dispatch_tool_call(bad_call)
        parsed = json.loads(result["content"])
        assert parsed["error"] is True
        assert parsed["code"] == "INVALID_ARGUMENTS"
