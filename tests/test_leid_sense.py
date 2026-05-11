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
    LeidClickElementNotFoundError,
    LeidConnectionError,
    LeidPlaywrightUnavailableError,
    LeidSessionExpiredError,
    LeidSessionLimitError,
    LeidTimeoutError,
    UrlNotAllowedError,
)
from heretic.skilningr.senses.leid.playwright_client import PlaywrightLeidClient
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

    # --- v0.8.0 Opið Vef — browser-render field validation (Auditor N-1) ---

    def test_leid_config_invalid_browser_navigation_timeout_raises(self):
        """browser_navigation_timeout_seconds <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="browser_navigation_timeout_seconds"):
            LeidConfig(browser_navigation_timeout_seconds=0)
        with pytest.raises(ValueError, match="browser_navigation_timeout_seconds"):
            LeidConfig(browser_navigation_timeout_seconds=-5)

    def test_leid_config_invalid_browser_load_state_raises(self):
        """browser_load_state outside the four allowed values raises ValueError."""
        with pytest.raises(ValueError, match="browser_load_state"):
            LeidConfig(browser_load_state="ready")  # not a Playwright state
        with pytest.raises(ValueError, match="browser_load_state"):
            LeidConfig(browser_load_state="")

    def test_leid_config_browser_load_state_accepts_all_four_valid_values(self):
        """All four documented browser_load_state values construct without error."""
        for state in ("commit", "domcontentloaded", "load", "networkidle"):
            cfg = LeidConfig(browser_load_state=state)
            assert cfg.browser_load_state == state

    def test_leid_config_browser_navigation_timeout_default(self):
        """browser_navigation_timeout_seconds defaults to 30."""
        cfg = LeidConfig()
        assert cfg.browser_navigation_timeout_seconds == 30

    def test_leid_config_browser_load_state_default_is_domcontentloaded(self):
        """browser_load_state defaults to 'domcontentloaded'."""
        cfg = LeidConfig()
        assert cfg.browser_load_state == "domcontentloaded"

    # --- v0.8.1 Mynd af Vegferð — screenshot field default ---

    def test_leid_config_browser_screenshot_full_page_default_is_true(self):
        """browser_screenshot_full_page defaults to True per D-20."""
        cfg = LeidConfig()
        assert cfg.browser_screenshot_full_page is True

    # --- v0.8.2 Innan Hurðar — session + click field validation ---

    def test_leid_config_invalid_browser_max_concurrent_sessions_raises(self):
        with pytest.raises(ValueError, match="browser_max_concurrent_sessions"):
            LeidConfig(browser_max_concurrent_sessions=0)
        with pytest.raises(ValueError, match="browser_max_concurrent_sessions"):
            LeidConfig(browser_max_concurrent_sessions=-1)

    def test_leid_config_invalid_browser_session_idle_timeout_raises(self):
        with pytest.raises(ValueError, match="browser_session_idle_timeout_seconds"):
            LeidConfig(browser_session_idle_timeout_seconds=0)

    def test_leid_config_invalid_browser_session_max_lifetime_raises(self):
        with pytest.raises(ValueError, match="browser_session_max_lifetime_seconds"):
            LeidConfig(browser_session_max_lifetime_seconds=0)

    def test_leid_config_max_lifetime_must_be_at_least_idle_timeout(self):
        """max_lifetime < idle_timeout is incoherent."""
        with pytest.raises(ValueError, match="incoherent"):
            LeidConfig(
                browser_session_idle_timeout_seconds=300,
                browser_session_max_lifetime_seconds=60,
            )

    def test_leid_config_invalid_browser_click_timeout_raises(self):
        with pytest.raises(ValueError, match="browser_click_timeout_seconds"):
            LeidConfig(browser_click_timeout_seconds=0)


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
        """tool_definitions returns 8 tools when enabled
        (v0.6.2: 2 + v0.8.0: 1 + v0.8.1: 1 + v0.8.2: 4)."""
        config = LeidConfig(enabled=True, url_allowlist_patterns=["https://example.com/*"])
        client = LeidClient(config)
        sense = LeidSense(config, client)
        assert len(sense.tool_definitions) == 8

    def test_tool_definitions_when_disabled(self):
        """tool_definitions returns empty list when disabled."""
        config = LeidConfig(enabled=False)
        client = LeidClient(config)
        sense = LeidSense(config, client)
        assert sense.tool_definitions == []

    def test_tool_names_locked(self):
        """All eight Leið tool names are locked as specified
        (v0.6.2: fetch_url, extract_text; v0.8.0: render_url;
         v0.8.1: screenshot; v0.8.2: open_session, session_status,
         click, close_session)."""
        names = {t["function"]["name"] for t in LEID_TOOL_DEFINITIONS}
        assert "leid.fetch_url" in names
        assert "leid.extract_text" in names
        assert "leid.render_url" in names
        assert "leid.screenshot" in names
        assert "leid.open_session" in names
        assert "leid.session_status" in names
        assert "leid.click" in names
        assert "leid.close_session" in names


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
        })
        sense = LeidSense(config, mock_client)
        await sense.open()
        tool_call = self._make_tool_call("leid.fetch_url", {"url": "https://example.com/page"})
        result = await sense.dispatch_tool_call(tool_call)
        assert result["role"] == "tool"
        parsed = json.loads(result["content"])
        assert parsed["status_code"] == 200
        # v0.6.2: no 'truncated' key — oversized bodies raise LeidResponseTooLargeError
        assert "truncated" not in parsed

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

    # -------------------------------------------------------------------
    # v0.8.0 Opið Vef — leid.render_url dispatch
    # -------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_dispatch_render_url_routes_to_playwright_client(self):
        """dispatch_tool_call routes leid.render_url to the injected
        PlaywrightLeidClient; the httpx LeidClient is NOT touched (D-14)."""
        config = LeidConfig(
            enabled=True,
            url_allowlist_patterns=["https://example.com/*"],
        )
        mock_client = MagicMock(spec=LeidClient)
        mock_client.fetch_url = AsyncMock(return_value={})  # should NOT be called
        mock_client.extract_text = AsyncMock(return_value={})  # should NOT be called

        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.render_url = AsyncMock(return_value={
            "url": "https://example.com/spa",
            "final_url": "https://example.com/spa",
            "text": "Rendered content",
            "title": "SPA",
            "source_size_bytes": 1234,
        })
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.render_url", {"url": "https://example.com/spa"}
        )
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])

        assert parsed["text"] == "Rendered content"
        assert parsed["title"] == "SPA"
        assert parsed["final_url"] == "https://example.com/spa"
        # The httpx client surface MUST NOT have been touched
        mock_client.fetch_url.assert_not_called()
        mock_client.extract_text.assert_not_called()
        mock_pw_client.render_url.assert_awaited_once_with(
            url="https://example.com/spa"
        )

    @pytest.mark.asyncio
    async def test_render_url_unavailable_returns_external_app_unavailable_code(self):
        """When PlaywrightLeidClient raises LeidPlaywrightUnavailableError, the
        sense returns SENSE_CONTRACTS code EXTERNAL_APP_UNAVAILABLE."""
        config = LeidConfig(
            enabled=True,
            url_allowlist_patterns=["https://example.com/*"],
        )
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.render_url = AsyncMock(
            side_effect=LeidPlaywrightUnavailableError(
                "Playwright is not installed."
            )
        )
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.render_url", {"url": "https://example.com/spa"}
        )
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["error"] is True
        assert parsed["code"] == "EXTERNAL_APP_UNAVAILABLE"

    # -------------------------------------------------------------------
    # v0.8.1 Mynd af Vegferð — leid.screenshot dispatch
    # -------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_dispatch_screenshot_routes_to_playwright_client(self):
        """dispatch_tool_call routes leid.screenshot to PlaywrightLeidClient.screenshot;
        the httpx LeidClient and PlaywrightLeidClient.render_url are NOT touched."""
        config = LeidConfig(
            enabled=True,
            url_allowlist_patterns=["https://example.com/*"],
        )
        mock_client = MagicMock(spec=LeidClient)
        mock_client.fetch_url = AsyncMock(return_value={})  # MUST NOT be called
        mock_client.extract_text = AsyncMock(return_value={})  # MUST NOT be called

        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.render_url = AsyncMock(return_value={})  # MUST NOT be called
        mock_pw_client.screenshot = AsyncMock(return_value={
            "url": "https://example.com/dash",
            "final_url": "https://example.com/dash",
            "image_base64": "iVBORw0KGgoAAAANSUhEUg==",
            "image_format": "png",
            "size_bytes": 28,
            "full_page": True,
        })
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.screenshot", {"url": "https://example.com/dash"}
        )
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])

        assert parsed["image_format"] == "png"
        assert parsed["size_bytes"] == 28
        assert parsed["full_page"] is True
        # Other surfaces MUST NOT have been touched
        mock_client.fetch_url.assert_not_called()
        mock_client.extract_text.assert_not_called()
        mock_pw_client.render_url.assert_not_called()
        mock_pw_client.screenshot.assert_awaited_once_with(
            url="https://example.com/dash"
        )

    @pytest.mark.asyncio
    async def test_screenshot_unavailable_returns_external_app_unavailable_code(self):
        """When PlaywrightLeidClient.screenshot raises LeidPlaywrightUnavailableError,
        the sense returns EXTERNAL_APP_UNAVAILABLE."""
        config = LeidConfig(
            enabled=True,
            url_allowlist_patterns=["https://example.com/*"],
        )
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.screenshot = AsyncMock(
            side_effect=LeidPlaywrightUnavailableError(
                "Playwright is not installed."
            )
        )
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.screenshot", {"url": "https://example.com/dash"}
        )
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["error"] is True
        assert parsed["code"] == "EXTERNAL_APP_UNAVAILABLE"

    # -------------------------------------------------------------------
    # v0.8.2 Innan Hurðar — session-tool dispatch
    # -------------------------------------------------------------------

    def _session_config(self) -> LeidConfig:
        return LeidConfig(
            enabled=True,
            url_allowlist_patterns=["https://example.com/*"],
        )

    @pytest.mark.asyncio
    async def test_dispatch_open_session_routes_to_playwright_client(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.open_session = AsyncMock(return_value={
            "session_id": "leid-deadbeef",
            "final_url": "https://example.com/page",
            "title": "Page",
        })
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.open_session", {"url": "https://example.com/page"}
        )
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["session_id"] == "leid-deadbeef"
        mock_pw_client.open_session.assert_awaited_once_with(
            url="https://example.com/page"
        )

    @pytest.mark.asyncio
    async def test_dispatch_session_status_routes_to_playwright_client(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.session_status = AsyncMock(return_value={
            "state": "alive",
            "url": "https://example.com/page",
            "title": "Page",
            "opened_at": 1.0,
            "last_activity_at": 1.5,
            "age_seconds": 0.5,
            "idle_seconds": 0.0,
        })
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.session_status", {"session_id": "leid-deadbeef"}
        )
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["state"] == "alive"
        mock_pw_client.session_status.assert_awaited_once_with(
            session_id="leid-deadbeef"
        )

    @pytest.mark.asyncio
    async def test_dispatch_click_routes_to_playwright_client(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.click = AsyncMock(return_value={
            "selector": "button",
            "clicked": True,
            "current_url": "https://example.com/landed",
            "current_title": "Landed",
        })
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.click",
            {"session_id": "leid-deadbeef", "selector": "button"},
        )
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["clicked"] is True
        mock_pw_client.click.assert_awaited_once_with(
            session_id="leid-deadbeef", selector="button"
        )

    @pytest.mark.asyncio
    async def test_dispatch_close_session_routes_to_playwright_client(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.close_session = AsyncMock(return_value={
            "session_id": "leid-deadbeef",
            "closed": True,
        })
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.close_session", {"session_id": "leid-deadbeef"}
        )
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["closed"] is True
        mock_pw_client.close_session.assert_awaited_once_with(
            session_id="leid-deadbeef"
        )

    # v0.8.2 — error code mappings for the new error classes

    @pytest.mark.asyncio
    async def test_session_limit_error_returns_sense_unavailable_code(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.open_session = AsyncMock(
            side_effect=LeidSessionLimitError("at cap")
        )
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        result = await sense.dispatch_tool_call(self._make_tool_call(
            "leid.open_session", {"url": "https://example.com/page"}
        ))
        parsed = json.loads(result["content"])
        assert parsed["code"] == "SENSE_UNAVAILABLE"

    @pytest.mark.asyncio
    async def test_session_expired_error_returns_sense_unavailable_code(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.session_status = AsyncMock(
            side_effect=LeidSessionExpiredError("expired")
        )
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        result = await sense.dispatch_tool_call(self._make_tool_call(
            "leid.session_status", {"session_id": "leid-gone"}
        ))
        parsed = json.loads(result["content"])
        assert parsed["code"] == "SENSE_UNAVAILABLE"

    @pytest.mark.asyncio
    async def test_click_element_not_found_returns_invalid_arguments_code(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.click = AsyncMock(
            side_effect=LeidClickElementNotFoundError("no match")
        )
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        result = await sense.dispatch_tool_call(self._make_tool_call(
            "leid.click",
            {"session_id": "leid-x", "selector": "#nope"},
        ))
        parsed = json.loads(result["content"])
        assert parsed["code"] == "INVALID_ARGUMENTS"
