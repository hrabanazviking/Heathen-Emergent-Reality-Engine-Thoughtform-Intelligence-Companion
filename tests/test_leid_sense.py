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
    LeidTypeElementNotFoundError,
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

    # --- v0.8.8 query_all — cardinality cap field validation ---

    def test_leid_config_browser_query_max_matches_default_is_100(self):
        """browser_query_max_matches defaults to 100 per D-115."""
        cfg = LeidConfig()
        assert cfg.browser_query_max_matches == 100

    def test_leid_config_invalid_browser_query_max_matches_raises(self):
        """browser_query_max_matches < 1 raises ValueError."""
        with pytest.raises(ValueError, match="browser_query_max_matches"):
            LeidConfig(browser_query_max_matches=0)
        with pytest.raises(ValueError, match="browser_query_max_matches"):
            LeidConfig(browser_query_max_matches=-5)

    # --- v0.8.9 — viewport field validation ---

    def test_leid_config_browser_viewport_width_default_is_1280(self):
        """browser_viewport_width defaults to 1280 (Playwright's default)."""
        cfg = LeidConfig()
        assert cfg.browser_viewport_width == 1280

    def test_leid_config_browser_viewport_height_default_is_720(self):
        """browser_viewport_height defaults to 720 (Playwright's default)."""
        cfg = LeidConfig()
        assert cfg.browser_viewport_height == 720

    def test_leid_config_invalid_browser_viewport_width_raises(self):
        """browser_viewport_width <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="browser_viewport_width"):
            LeidConfig(browser_viewport_width=0)
        with pytest.raises(ValueError, match="browser_viewport_width"):
            LeidConfig(browser_viewport_width=-100)

    def test_leid_config_invalid_browser_viewport_height_raises(self):
        """browser_viewport_height <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="browser_viewport_height"):
            LeidConfig(browser_viewport_height=0)
        with pytest.raises(ValueError, match="browser_viewport_height"):
            LeidConfig(browser_viewport_height=-50)

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
        """tool_definitions returns 18 tools when enabled
        (v0.6.2: 2 + v0.8.0: 1 + v0.8.1: 1 + v0.8.2: 4 + v0.8.2.1: 1 +
         v0.8.2.2: 1 + v0.8.3: 1 + v0.8.4: 1 + v0.8.5: 2 + v0.8.6: 2 +
         v0.8.7: 1 + v0.8.8: 1)."""
        config = LeidConfig(enabled=True, url_allowlist_patterns=["https://example.com/*"])
        client = LeidClient(config)
        sense = LeidSense(config, client)
        assert len(sense.tool_definitions) == 18

    def test_tool_definitions_when_disabled(self):
        """tool_definitions returns empty list when disabled."""
        config = LeidConfig(enabled=False)
        client = LeidClient(config)
        sense = LeidSense(config, client)
        assert sense.tool_definitions == []

    def test_tool_names_locked(self):
        """All eighteen Leið tool names are locked as specified
        (v0.6.2: fetch_url, extract_text; v0.8.0: render_url;
         v0.8.1: screenshot; v0.8.2: open_session, session_status, click,
         close_session; v0.8.2.1: type; v0.8.2.2: navigate; v0.8.3: query;
         v0.8.4: press; v0.8.5: go_back, go_forward; v0.8.6: session_render,
         session_screenshot; v0.8.7: reload; v0.8.8: query_all)."""
        names = {t["function"]["name"] for t in LEID_TOOL_DEFINITIONS}
        assert "leid.fetch_url" in names
        assert "leid.extract_text" in names
        assert "leid.render_url" in names
        assert "leid.screenshot" in names
        assert "leid.open_session" in names
        assert "leid.session_status" in names
        assert "leid.click" in names
        assert "leid.type" in names
        assert "leid.navigate" in names
        assert "leid.query" in names
        assert "leid.press" in names
        assert "leid.go_back" in names
        assert "leid.go_forward" in names
        assert "leid.session_render" in names
        assert "leid.session_screenshot" in names
        assert "leid.reload" in names
        assert "leid.query_all" in names
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

    # -------------------------------------------------------------------
    # v0.8.2.1 — leid.type dispatch + error code
    # -------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_dispatch_type_routes_to_playwright_client(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.type = AsyncMock(return_value={
            "selector": "input",
            "typed": True,
            "current_url": "https://example.com/form",
            "current_title": "Form",
        })
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.type",
            {
                "session_id": "leid-x",
                "selector": "input",
                "text": "hello world",
            },
        )
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["typed"] is True
        mock_pw_client.type.assert_awaited_once_with(
            session_id="leid-x", selector="input", text="hello world"
        )

    @pytest.mark.asyncio
    async def test_type_element_not_found_returns_invalid_arguments_code(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.type = AsyncMock(
            side_effect=LeidTypeElementNotFoundError("no input matched")
        )
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        result = await sense.dispatch_tool_call(self._make_tool_call(
            "leid.type",
            {"session_id": "leid-x", "selector": "#nope", "text": "x"},
        ))
        parsed = json.loads(result["content"])
        assert parsed["code"] == "INVALID_ARGUMENTS"

    # -------------------------------------------------------------------
    # v0.8.2.2 — leid.navigate dispatch
    # -------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_dispatch_navigate_routes_to_playwright_client(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.navigate = AsyncMock(return_value={
            "session_id": "leid-x",
            "previous_url": "https://example.com/login",
            "final_url": "https://example.com/dashboard",
            "title": "Dashboard",
        })
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.navigate",
            {
                "session_id": "leid-x",
                "url": "https://example.com/dashboard",
            },
        )
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["previous_url"] == "https://example.com/login"
        assert parsed["final_url"] == "https://example.com/dashboard"
        mock_pw_client.navigate.assert_awaited_once_with(
            session_id="leid-x", url="https://example.com/dashboard"
        )

    # -------------------------------------------------------------------
    # v0.8.3 — leid.query dispatch
    # -------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_dispatch_query_routes_to_playwright_client(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.query = AsyncMock(return_value={
            "session_id": "leid-x",
            "selector": "h1",
            "attribute": "",
            "found": True,
            "value": "Heading",
            "count": 1,
        })
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.query",
            {"session_id": "leid-x", "selector": "h1"},  # attribute omitted
        )
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["found"] is True
        assert parsed["value"] == "Heading"
        # When attribute omitted, dispatcher passes empty string
        mock_pw_client.query.assert_awaited_once_with(
            session_id="leid-x", selector="h1", attribute=""
        )

    @pytest.mark.asyncio
    async def test_dispatch_query_passes_attribute_when_provided(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.query = AsyncMock(return_value={
            "session_id": "leid-x",
            "selector": "a",
            "attribute": "href",
            "found": True,
            "value": "https://example.com",
            "count": 1,
        })
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.query",
            {"session_id": "leid-x", "selector": "a", "attribute": "href"},
        )
        await sense.dispatch_tool_call(tool_call)
        mock_pw_client.query.assert_awaited_once_with(
            session_id="leid-x", selector="a", attribute="href"
        )

    # -------------------------------------------------------------------
    # v0.8.4 — leid.press dispatch
    # -------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_dispatch_press_routes_to_playwright_client(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.press = AsyncMock(return_value={
            "session_id": "leid-x",
            "key": "Enter",
            "pressed": True,
            "current_url": "https://example.com/results",
            "current_title": "Results",
        })
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.press",
            {"session_id": "leid-x", "key": "Enter"},
        )
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["pressed"] is True
        assert parsed["key"] == "Enter"
        mock_pw_client.press.assert_awaited_once_with(
            session_id="leid-x", key="Enter"
        )

    # -------------------------------------------------------------------
    # v0.8.5 — leid.go_back + leid.go_forward dispatch (paired)
    # -------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_dispatch_go_back_routes_to_playwright_client(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.go_back = AsyncMock(return_value={
            "session_id": "leid-x",
            "moved": True,
            "previous_url": "https://example.com/page2",
            "current_url": "https://example.com/page1",
            "title": "Page 1",
        })
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.go_back", {"session_id": "leid-x"}
        )
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["moved"] is True
        assert parsed["current_url"] == "https://example.com/page1"
        mock_pw_client.go_back.assert_awaited_once_with(session_id="leid-x")

    @pytest.mark.asyncio
    async def test_dispatch_go_forward_routes_to_playwright_client(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.go_forward = AsyncMock(return_value={
            "session_id": "leid-x",
            "moved": False,
            "previous_url": "https://example.com/page2",
            "current_url": "https://example.com/page2",
            "title": "Page 2",
        })
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.go_forward", {"session_id": "leid-x"}
        )
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        # Verifies the moved=false case is routed correctly (NOT an error)
        assert parsed["moved"] is False
        mock_pw_client.go_forward.assert_awaited_once_with(session_id="leid-x")

    # -------------------------------------------------------------------
    # v0.8.6 — leid.session_render + leid.session_screenshot dispatch
    # -------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_dispatch_session_render_routes_to_playwright_client(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.session_render = AsyncMock(return_value={
            "session_id": "leid-x",
            "current_url": "https://example.com/dashboard",
            "text": "Welcome back",
            "title": "Dashboard",
            "source_size_bytes": 1234,
        })
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.session_render", {"session_id": "leid-x"}
        )
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["text"] == "Welcome back"
        assert parsed["current_url"] == "https://example.com/dashboard"
        mock_pw_client.session_render.assert_awaited_once_with(
            session_id="leid-x"
        )

    @pytest.mark.asyncio
    async def test_dispatch_session_screenshot_routes_to_playwright_client(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.session_screenshot = AsyncMock(return_value={
            "session_id": "leid-x",
            "current_url": "https://example.com/results",
            "image_base64": "iVBORw0KGgoAAA==",
            "image_format": "png",
            "size_bytes": 12,
            "full_page": True,
        })
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.session_screenshot", {"session_id": "leid-x"}
        )
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["image_format"] == "png"
        assert parsed["full_page"] is True
        mock_pw_client.session_screenshot.assert_awaited_once_with(
            session_id="leid-x"
        )

    # -------------------------------------------------------------------
    # v0.8.7 — leid.reload dispatch
    # -------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_dispatch_reload_routes_to_playwright_client(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.reload = AsyncMock(return_value={
            "session_id": "leid-x",
            "current_url": "https://example.com/dashboard",
            "title": "Dashboard",
        })
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.reload", {"session_id": "leid-x"}
        )
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["current_url"] == "https://example.com/dashboard"
        assert parsed["title"] == "Dashboard"
        mock_pw_client.reload.assert_awaited_once_with(session_id="leid-x")

    # -------------------------------------------------------------------
    # v0.8.8 — leid.query_all dispatch
    # -------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_dispatch_query_all_routes_to_playwright_client(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.query_all = AsyncMock(return_value={
            "session_id": "leid-x",
            "selector": "article h2",
            "attribute": "",
            "count": 3,
            "values": ["Title A", "Title B", "Title C"],
        })
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.query_all", {"session_id": "leid-x", "selector": "article h2"},
        )
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["count"] == 3
        assert parsed["values"] == ["Title A", "Title B", "Title C"]
        # When attribute omitted, dispatcher passes empty string
        mock_pw_client.query_all.assert_awaited_once_with(
            session_id="leid-x", selector="article h2", attribute=""
        )

    @pytest.mark.asyncio
    async def test_dispatch_query_all_passes_attribute_when_provided(self):
        config = self._session_config()
        mock_client = MagicMock(spec=LeidClient)
        mock_pw_client = MagicMock(spec=PlaywrightLeidClient)
        mock_pw_client.query_all = AsyncMock(return_value={
            "session_id": "leid-x",
            "selector": "a.nav",
            "attribute": "href",
            "count": 2,
            "values": ["/about", "/contact"],
        })
        sense = LeidSense(config, mock_client, playwright_client=mock_pw_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "leid.query_all",
            {"session_id": "leid-x", "selector": "a.nav", "attribute": "href"},
        )
        await sense.dispatch_tool_call(tool_call)
        mock_pw_client.query_all.assert_awaited_once_with(
            session_id="leid-x", selector="a.nav", attribute="href"
        )
