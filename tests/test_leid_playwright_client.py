"""
Tests for PlaywrightLeidClient — Leið Opið Vef browser-render sub-faculty (v0.8.0).

Covers:
    - URL gateway (_validate_url): same allowlist + HTTPS-only rules as LeidClient
                                   (B-1, B-9 honoured)
    - render_url: B-1 .. B-10 invariants
        - validation runs before any Playwright operation
        - LeidPlaywrightUnavailableError when playwright import fails
        - LeidPlaywrightUnavailableError when chromium.launch fails
        - fresh new_context per call (no state crosses calls)
        - launches headless=True
        - timeout maps to LeidTimeoutError
        - HTTP 4xx/5xx maps to LeidHttpError
        - rendered HTML > max_response_bytes raises LeidResponseTooLargeError
                                                 BEFORE text extraction
        - all three resources (pw, browser, context) closed even on failure
        - user_agent passed through to new_context
        - http:// rejected when allow_http: false
    - return shape: {url, final_url, text, title, source_size_bytes}

All tests mock the playwright API by injecting a fake module into sys.modules.
No real Chromium is spawned. The single smoke test marked
``@pytest.mark.requires_playwright`` exercises the real binary if installed; it
is default-skip in CI.

Ref: src/heretic/skilningr/senses/leid/playwright_client.py
     src/heretic/skilningr/senses/leid/INTERFACE.md §10
     TASK_HERETIC_v0.8.0_OPID_VEF.md §6 (Test plan)
"""

from __future__ import annotations

import sys
import types
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from heretic.skilningr.config_model import LeidConfig
from heretic.skilningr.senses.leid.errors import (
    LeidConnectionError,
    LeidHttpError,
    LeidPlaywrightUnavailableError,
    LeidResponseTooLargeError,
    LeidTimeoutError,
    UrlNotAllowedError,
)
from heretic.skilningr.senses.leid.playwright_client import PlaywrightLeidClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_client(
    patterns: list[str] | None = None, **kwargs: Any
) -> PlaywrightLeidClient:
    """Return a PlaywrightLeidClient with the given URL allowlist patterns."""
    if patterns is None:
        patterns = ["https://example.com/*"]
    config = LeidConfig(url_allowlist_patterns=patterns, **kwargs)
    return PlaywrightLeidClient(config)


class _FakePlaywrightTimeoutError(Exception):
    """Stand-in for playwright.async_api.TimeoutError."""


class _FakePlaywrightError(Exception):
    """Stand-in for playwright.async_api.Error (network-level)."""


def _install_fake_playwright(
    *,
    launch_side_effect: BaseException | None = None,
    goto_side_effect: BaseException | None = None,
    page_content: str = "<html><head><title>Hi</title></head><body>Hello</body></html>",
    page_url: str = "https://example.com/page",
    response_status: int = 200,
    response_is_none: bool = False,
    screenshot_bytes: bytes = b"\x89PNG\r\n\x1a\n_fake_png_payload_",
) -> tuple[MagicMock, MagicMock, MagicMock, MagicMock, MagicMock]:
    """Install a fake `playwright.async_api` module in ``sys.modules``.

    Returns the mocks (start_mock, browser_mock, context_mock, page_mock, response_mock)
    so individual tests can assert call shape (e.g. headless=True, user_agent=...).
    """
    # Build the page mock first (innermost)
    page_mock = MagicMock()
    page_mock.url = page_url
    page_mock.content = AsyncMock(return_value=page_content)
    page_mock.screenshot = AsyncMock(return_value=screenshot_bytes)
    # B-10 regression-guard: page.evaluate is mocked but never called by
    # production code. Tests assert assert_not_called() after each method.
    page_mock.evaluate = AsyncMock(return_value=None)
    response_mock = MagicMock()
    response_mock.status = response_status
    if response_is_none:
        page_mock.goto = AsyncMock(return_value=None)
    elif goto_side_effect is not None:
        page_mock.goto = AsyncMock(side_effect=goto_side_effect)
    else:
        page_mock.goto = AsyncMock(return_value=response_mock)

    # Build the context mock
    context_mock = MagicMock()
    context_mock.new_page = AsyncMock(return_value=page_mock)
    context_mock.close = AsyncMock(return_value=None)

    # Build the browser mock
    browser_mock = MagicMock()
    browser_mock.new_context = AsyncMock(return_value=context_mock)
    browser_mock.close = AsyncMock(return_value=None)

    # Build the chromium-launcher mock
    chromium_mock = MagicMock()
    if launch_side_effect is not None:
        chromium_mock.launch = AsyncMock(side_effect=launch_side_effect)
    else:
        chromium_mock.launch = AsyncMock(return_value=browser_mock)

    # Build the playwright runtime mock
    pw_runtime_mock = MagicMock()
    pw_runtime_mock.chromium = chromium_mock
    pw_runtime_mock.stop = AsyncMock(return_value=None)

    # async_playwright() returns an object whose .start() returns the runtime.
    start_factory_mock = MagicMock()
    start_factory_mock.start = AsyncMock(return_value=pw_runtime_mock)
    async_playwright_mock = MagicMock(return_value=start_factory_mock)

    # Build the fake module
    fake_module = types.ModuleType("playwright.async_api")
    fake_module.async_playwright = async_playwright_mock
    fake_module.TimeoutError = _FakePlaywrightTimeoutError
    fake_module.Error = _FakePlaywrightError

    parent_module = types.ModuleType("playwright")
    parent_module.async_api = fake_module  # type: ignore[attr-defined]

    sys.modules["playwright"] = parent_module
    sys.modules["playwright.async_api"] = fake_module

    return (
        async_playwright_mock,
        browser_mock,
        context_mock,
        page_mock,
        response_mock,
    )


def _uninstall_fake_playwright() -> None:
    sys.modules.pop("playwright.async_api", None)
    sys.modules.pop("playwright", None)


@pytest.fixture
def fake_playwright():
    """Fixture: install fake playwright before the test, remove after."""
    yield _install_fake_playwright
    _uninstall_fake_playwright()


@pytest.fixture
def no_playwright():
    """Fixture: ensure playwright is NOT importable during the test."""
    saved_pw = sys.modules.pop("playwright", None)
    saved_pw_async = sys.modules.pop("playwright.async_api", None)
    # Inject a sentinel that will raise ImportError on attribute access
    # for `from playwright.async_api import async_playwright`.
    # The simplest way: make the parent module exist but the submodule
    # attribute access fail. But the cleanest approach is to insert a
    # finder that refuses these imports for the duration of the test.

    class _RefusingFinder:
        def find_module(self, name, path=None):
            if name == "playwright" or name.startswith("playwright."):
                return self
            return None

        def load_module(self, name):
            raise ImportError(f"playwright is not installed (test fixture)")

    finder = _RefusingFinder()
    sys.meta_path.insert(0, finder)
    yield
    sys.meta_path.remove(finder)
    if saved_pw is not None:
        sys.modules["playwright"] = saved_pw
    if saved_pw_async is not None:
        sys.modules["playwright.async_api"] = saved_pw_async


# ---------------------------------------------------------------------------
# URL gateway — _validate_url (B-1, B-9)
# ---------------------------------------------------------------------------

class TestPlaywrightLeidClientUrlGateway:

    def test_validate_url_accepted(self):
        client = make_client(["https://docs.python.org/*"])
        normalised = client._validate_url("https://docs.python.org/3/library/os.html")
        assert "docs.python.org" in normalised

    def test_validate_url_not_in_allowlist_raises(self):
        client = make_client(["https://docs.python.org/*"])
        with pytest.raises(UrlNotAllowedError):
            client._validate_url("https://evil.com/steal")

    def test_validate_http_rejected_when_https_only(self):
        client = make_client(["http://example.com/*"], allow_http=False)
        with pytest.raises(UrlNotAllowedError, match="HTTP"):
            client._validate_url("http://example.com/page")

    def test_validate_http_accepted_when_allow_http(self):
        client = make_client(["http://example.com/*"], allow_http=True)
        normalised = client._validate_url("http://example.com/page")
        assert "example.com" in normalised


# ---------------------------------------------------------------------------
# render_url — B-1: validation BEFORE any browser operation
# ---------------------------------------------------------------------------

class TestRenderUrlValidationBeforeLaunch:

    @pytest.mark.asyncio
    async def test_render_url_validates_before_launch(self, fake_playwright):
        """B-1: URL not in allowlist → UrlNotAllowedError; async_playwright
        factory NEVER called."""
        async_playwright_mock, *_ = fake_playwright()
        client = make_client(["https://docs.python.org/*"])

        with pytest.raises(UrlNotAllowedError):
            await client.render_url("https://evil.com/page")

        async_playwright_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_render_url_rejects_http_when_allow_http_false(self, fake_playwright):
        """B-9: http:// URL with allow_http=false → UrlNotAllowedError;
        no browser launched."""
        async_playwright_mock, *_ = fake_playwright()
        client = make_client(["http://example.com/*"], allow_http=False)

        with pytest.raises(UrlNotAllowedError, match="HTTP"):
            await client.render_url("http://example.com/page")

        async_playwright_mock.assert_not_called()


# ---------------------------------------------------------------------------
# render_url — B-2: availability errors
# ---------------------------------------------------------------------------

class TestRenderUrlAvailability:

    @pytest.mark.asyncio
    async def test_render_url_unavailable_when_playwright_missing(
        self, no_playwright
    ):
        """B-2: import of playwright fails → LeidPlaywrightUnavailableError."""
        client = make_client(["https://example.com/*"])
        with pytest.raises(LeidPlaywrightUnavailableError, match="not installed"):
            await client.render_url("https://example.com/page")

    @pytest.mark.asyncio
    async def test_render_url_unavailable_when_browser_launch_fails(
        self, fake_playwright
    ):
        """B-2: chromium.launch raises → LeidPlaywrightUnavailableError."""
        async_playwright_mock, *_ = fake_playwright(
            launch_side_effect=RuntimeError("Executable doesn't exist")
        )
        client = make_client(["https://example.com/*"])

        with pytest.raises(LeidPlaywrightUnavailableError, match="Chromium"):
            await client.render_url("https://example.com/page")


# ---------------------------------------------------------------------------
# render_url — B-3, B-4, B-8: lifecycle and per-call isolation
# ---------------------------------------------------------------------------

class TestRenderUrlLifecycle:

    @pytest.mark.asyncio
    async def test_render_url_uses_fresh_context_per_call(self, fake_playwright):
        """B-3: two consecutive calls open two contexts; both closed."""
        # First call
        _, browser_mock1, context_mock1, *_ = fake_playwright()
        client = make_client(["https://example.com/*"])
        await client.render_url("https://example.com/page1")
        assert browser_mock1.new_context.await_count == 1
        assert context_mock1.close.await_count == 1
        _uninstall_fake_playwright()

        # Second call (fresh fake)
        _, browser_mock2, context_mock2, *_ = _install_fake_playwright()
        try:
            await client.render_url("https://example.com/page2")
            assert browser_mock2.new_context.await_count == 1
            assert context_mock2.close.await_count == 1
        finally:
            _uninstall_fake_playwright()

    @pytest.mark.asyncio
    async def test_render_url_launches_headless(self, fake_playwright):
        """B-4: chromium.launch called with headless=True."""
        _, browser_mock, *_ = fake_playwright()
        # We need access to the chromium.launch call args, not browser.
        # Re-fetch the runtime via sys.modules to inspect it.
        chromium_launch = sys.modules["playwright.async_api"].async_playwright().start  # type: ignore[attr-defined]
        # simpler approach: patch chromium.launch on the runtime returned by
        # async_playwright().start() — but the helper already wires it. We
        # check the call args:
        client = make_client(["https://example.com/*"])
        await client.render_url("https://example.com/page")

        # Inspect launch call via the parent factory chain:
        async_pw = sys.modules["playwright.async_api"].async_playwright  # type: ignore[attr-defined]
        # The mock has been called; we walk to .return_value.start to get the
        # runtime mock that was returned via AsyncMock.
        start_factory = async_pw.return_value
        # start was called and returned the pw_runtime_mock
        pw_runtime = start_factory.start.return_value
        chromium = pw_runtime.chromium
        chromium.launch.assert_awaited_once_with(headless=True)

    @pytest.mark.asyncio
    async def test_render_url_uses_configured_user_agent(self, fake_playwright):
        """B-8: new_context called with user_agent=config.user_agent."""
        _, browser_mock, *_ = fake_playwright()
        client = make_client(
            ["https://example.com/*"],
            user_agent="HERETIC/0.8.0 (test-agent)",
        )
        await client.render_url("https://example.com/page")
        browser_mock.new_context.assert_awaited_once_with(
            user_agent="HERETIC/0.8.0 (test-agent)"
        )


# ---------------------------------------------------------------------------
# render_url — B-5: navigation timeout
# ---------------------------------------------------------------------------

class TestRenderUrlTimeout:

    @pytest.mark.asyncio
    async def test_render_url_navigation_timeout_raises_leid_timeout(
        self, fake_playwright
    ):
        """B-5: page.goto TimeoutError → LeidTimeoutError."""
        fake_playwright(
            goto_side_effect=_FakePlaywrightTimeoutError("Navigation timeout 30000ms")
        )
        client = make_client(["https://example.com/*"])
        with pytest.raises(LeidTimeoutError, match="timed out"):
            await client.render_url("https://example.com/page")

    @pytest.mark.asyncio
    async def test_render_url_passes_browser_load_state(self, fake_playwright):
        """page.goto is called with wait_until=config.browser_load_state."""
        _, _, _, page_mock, _ = fake_playwright()
        client = make_client(
            ["https://example.com/*"],
            browser_load_state="networkidle",
        )
        await client.render_url("https://example.com/page")
        # First positional arg is the url; kwargs include wait_until + timeout
        call_kwargs = page_mock.goto.await_args.kwargs
        assert call_kwargs["wait_until"] == "networkidle"

    @pytest.mark.asyncio
    async def test_render_url_passes_browser_navigation_timeout(self, fake_playwright):
        """page.goto timeout is browser_navigation_timeout_seconds * 1000 (ms)."""
        _, _, _, page_mock, _ = fake_playwright()
        client = make_client(
            ["https://example.com/*"],
            browser_navigation_timeout_seconds=15,
        )
        await client.render_url("https://example.com/page")
        call_kwargs = page_mock.goto.await_args.kwargs
        assert call_kwargs["timeout"] == 15000


# ---------------------------------------------------------------------------
# render_url — HTTP error and network error mapping
# ---------------------------------------------------------------------------

class TestRenderUrlNavigationErrors:

    @pytest.mark.asyncio
    async def test_render_url_http_error_raises_leid_http_error(
        self, fake_playwright
    ):
        """4xx/5xx response status → LeidHttpError with status code in message."""
        fake_playwright(response_status=503)
        client = make_client(["https://example.com/*"])
        with pytest.raises(LeidHttpError, match="503"):
            await client.render_url("https://example.com/page")

    @pytest.mark.asyncio
    async def test_render_url_network_error_raises_leid_connection_error(
        self, fake_playwright
    ):
        """playwright.async_api.Error (network-level) → LeidConnectionError."""
        fake_playwright(
            goto_side_effect=_FakePlaywrightError("net::ERR_NAME_NOT_RESOLVED")
        )
        client = make_client(["https://example.com/*"])
        with pytest.raises(LeidConnectionError, match="network layer"):
            await client.render_url("https://example.com/page")

    @pytest.mark.asyncio
    async def test_render_url_handles_none_response(self, fake_playwright):
        """page.goto returns None (e.g. data: URL) → no HTTP check; success."""
        fake_playwright(response_is_none=True)
        client = make_client(["https://example.com/*"])
        result = await client.render_url("https://example.com/page")
        assert result["text"] == "Hello"


# ---------------------------------------------------------------------------
# render_url — B-6: rendered-HTML pre-cap
# ---------------------------------------------------------------------------

class TestRenderUrlSizeCap:

    @pytest.mark.asyncio
    async def test_render_url_pre_cap_on_rendered_html_size(self, fake_playwright):
        """B-6: rendered HTML > max_response_bytes → LeidResponseTooLargeError."""
        large_html = "<html><body>" + ("x" * 2_000_000) + "</body></html>"
        fake_playwright(page_content=large_html)
        client = make_client(
            ["https://example.com/*"],
            max_response_bytes=1_048_576,  # 1 MB
        )
        with pytest.raises(LeidResponseTooLargeError, match="exceeds max_response_bytes"):
            await client.render_url("https://example.com/page")

    @pytest.mark.asyncio
    async def test_render_url_pre_cap_under_threshold(self, fake_playwright):
        """Under-cap render succeeds and returns expected fields."""
        small_html = "<html><head><title>Small</title></head><body>Tiny</body></html>"
        fake_playwright(page_content=small_html)
        client = make_client(
            ["https://example.com/*"],
            max_response_bytes=1_048_576,
        )
        result = await client.render_url("https://example.com/page")
        assert result["title"] == "Small"
        assert result["text"] == "Tiny"


# ---------------------------------------------------------------------------
# render_url — return shape
# ---------------------------------------------------------------------------

class TestRenderUrlReturnShape:

    @pytest.mark.asyncio
    async def test_render_url_returns_correct_shape(self, fake_playwright):
        """Success returns {url, final_url, text, title, source_size_bytes}."""
        html = "<html><head><title>Test Page</title></head><body><p>Body</p></body></html>"
        fake_playwright(page_content=html, page_url="https://example.com/final")
        client = make_client(["https://example.com/*"])
        result = await client.render_url("https://example.com/page")

        assert set(result.keys()) == {
            "url",
            "final_url",
            "text",
            "title",
            "source_size_bytes",
        }
        assert result["url"] == "https://example.com/page"
        assert result["final_url"] == "https://example.com/final"
        assert result["title"] == "Test Page"
        assert "Body" in result["text"]
        assert result["source_size_bytes"] == len(html.encode("utf-8"))

    @pytest.mark.asyncio
    async def test_render_url_extracts_title_from_rendered_html(
        self, fake_playwright
    ):
        """<title> is extracted into result['title']."""
        html = "<html><head><title>Norse Mythology</title></head><body>Odin</body></html>"
        fake_playwright(page_content=html)
        client = make_client(["https://example.com/*"])
        result = await client.render_url("https://example.com/page")
        assert result["title"] == "Norse Mythology"

    @pytest.mark.asyncio
    async def test_render_url_extracts_text_from_rendered_html(
        self, fake_playwright
    ):
        """Body text is stripped of tags and returned in result['text']."""
        html = "<html><body><p>Hello</p><p>World</p></body></html>"
        fake_playwright(page_content=html)
        client = make_client(["https://example.com/*"])
        result = await client.render_url("https://example.com/page")
        assert "Hello" in result["text"]
        assert "World" in result["text"]
        assert "<p>" not in result["text"]

    @pytest.mark.asyncio
    async def test_render_url_returns_final_url_after_redirect(
        self, fake_playwright
    ):
        """When page.url differs from input, final_url reflects the post-redirect URL."""
        fake_playwright(page_url="https://example.com/redirected")
        client = make_client(["https://example.com/*"])
        result = await client.render_url("https://example.com/page")
        assert result["final_url"] == "https://example.com/redirected"
        assert result["url"] == "https://example.com/page"


# ---------------------------------------------------------------------------
# render_url — B-7: resource cleanup on every failure
# ---------------------------------------------------------------------------

class TestRenderUrlResourceCleanup:

    @pytest.mark.asyncio
    async def test_render_url_closes_all_resources_on_navigation_failure(
        self, fake_playwright
    ):
        """B-7: page.goto raises → context.close, browser.close, pw.stop all called."""
        _, browser_mock, context_mock, _, _ = fake_playwright(
            goto_side_effect=_FakePlaywrightError("network layer")
        )
        client = make_client(["https://example.com/*"])
        with pytest.raises(LeidConnectionError):
            await client.render_url("https://example.com/page")

        assert context_mock.close.await_count == 1
        assert browser_mock.close.await_count == 1
        # Verify pw.stop was called via the runtime mock
        pw_runtime = sys.modules[
            "playwright.async_api"
        ].async_playwright.return_value.start.return_value  # type: ignore[attr-defined]
        assert pw_runtime.stop.await_count == 1

    @pytest.mark.asyncio
    async def test_render_url_closes_all_resources_on_size_cap_breach(
        self, fake_playwright
    ):
        """B-7: pre-cap raise → all three resources still closed."""
        large_html = "<html>" + ("x" * 2_000_000) + "</html>"
        _, browser_mock, context_mock, _, _ = fake_playwright(page_content=large_html)
        client = make_client(
            ["https://example.com/*"],
            max_response_bytes=1_048_576,
        )
        with pytest.raises(LeidResponseTooLargeError):
            await client.render_url("https://example.com/page")

        assert context_mock.close.await_count == 1
        assert browser_mock.close.await_count == 1
        pw_runtime = sys.modules[
            "playwright.async_api"
        ].async_playwright.return_value.start.return_value  # type: ignore[attr-defined]
        assert pw_runtime.stop.await_count == 1

    @pytest.mark.asyncio
    async def test_render_url_closes_resources_when_launch_fails(
        self, fake_playwright
    ):
        """B-7: chromium.launch fails → pw.stop still called; no leaks."""
        fake_playwright(
            launch_side_effect=RuntimeError("binary missing"),
        )
        client = make_client(["https://example.com/*"])
        with pytest.raises(LeidPlaywrightUnavailableError):
            await client.render_url("https://example.com/page")

        pw_runtime = sys.modules[
            "playwright.async_api"
        ].async_playwright.return_value.start.return_value  # type: ignore[attr-defined]
        # The runtime started, then launch failed; pw.stop still in finally.
        assert pw_runtime.stop.await_count == 1


# ---------------------------------------------------------------------------
# v0.8.1 Mynd af Vegferð — screenshot tests
# ---------------------------------------------------------------------------

class TestScreenshotValidationBeforeLaunch:
    """B-1, B-9 for screenshot — validation runs before any browser operation."""

    @pytest.mark.asyncio
    async def test_screenshot_validates_before_launch(self, fake_playwright):
        """B-1: URL not in allowlist → UrlNotAllowedError; no browser launched."""
        async_playwright_mock, *_ = fake_playwright()
        client = make_client(["https://docs.python.org/*"])
        with pytest.raises(UrlNotAllowedError):
            await client.screenshot("https://evil.com/page")
        async_playwright_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_screenshot_rejects_http_when_allow_http_false(self, fake_playwright):
        """B-9: http:// URL with allow_http=false → UrlNotAllowedError; no browser."""
        async_playwright_mock, *_ = fake_playwright()
        client = make_client(["http://example.com/*"], allow_http=False)
        with pytest.raises(UrlNotAllowedError, match="HTTP"):
            await client.screenshot("http://example.com/page")
        async_playwright_mock.assert_not_called()


class TestScreenshotAvailability:
    """B-2 for screenshot — availability errors."""

    @pytest.mark.asyncio
    async def test_screenshot_unavailable_when_playwright_missing(self, no_playwright):
        client = make_client(["https://example.com/*"])
        with pytest.raises(LeidPlaywrightUnavailableError, match="not installed"):
            await client.screenshot("https://example.com/page")

    @pytest.mark.asyncio
    async def test_screenshot_unavailable_when_browser_launch_fails(
        self, fake_playwright
    ):
        fake_playwright(launch_side_effect=RuntimeError("Executable doesn't exist"))
        client = make_client(["https://example.com/*"])
        with pytest.raises(LeidPlaywrightUnavailableError, match="Chromium"):
            await client.screenshot("https://example.com/page")


class TestScreenshotLifecycle:
    """B-3, B-4, B-8 for screenshot — context isolation, headless, user agent."""

    @pytest.mark.asyncio
    async def test_screenshot_uses_fresh_context_per_call(self, fake_playwright):
        """B-3: two consecutive calls open two contexts; both closed."""
        _, browser_mock1, context_mock1, *_ = fake_playwright()
        client = make_client(["https://example.com/*"])
        await client.screenshot("https://example.com/page1")
        assert browser_mock1.new_context.await_count == 1
        assert context_mock1.close.await_count == 1
        _uninstall_fake_playwright()

        _, browser_mock2, context_mock2, *_ = _install_fake_playwright()
        try:
            await client.screenshot("https://example.com/page2")
            assert browser_mock2.new_context.await_count == 1
            assert context_mock2.close.await_count == 1
        finally:
            _uninstall_fake_playwright()

    @pytest.mark.asyncio
    async def test_screenshot_launches_headless(self, fake_playwright):
        """B-4: chromium.launch called with headless=True."""
        fake_playwright()
        client = make_client(["https://example.com/*"])
        await client.screenshot("https://example.com/page")
        async_pw = sys.modules["playwright.async_api"].async_playwright  # type: ignore[attr-defined]
        chromium = async_pw.return_value.start.return_value.chromium
        chromium.launch.assert_awaited_once_with(headless=True)

    @pytest.mark.asyncio
    async def test_screenshot_uses_configured_user_agent(self, fake_playwright):
        """B-8: new_context called with user_agent=config.user_agent."""
        _, browser_mock, *_ = fake_playwright()
        client = make_client(
            ["https://example.com/*"],
            user_agent="HERETIC/0.8.1 (test-agent)",
        )
        await client.screenshot("https://example.com/page")
        browser_mock.new_context.assert_awaited_once_with(
            user_agent="HERETIC/0.8.1 (test-agent)"
        )


class TestScreenshotNavigationErrors:
    """B-5 timeout, HTTP error, network error mapping for screenshot."""

    @pytest.mark.asyncio
    async def test_screenshot_navigation_timeout_raises_leid_timeout(
        self, fake_playwright
    ):
        fake_playwright(
            goto_side_effect=_FakePlaywrightTimeoutError("Navigation timeout 30000ms")
        )
        client = make_client(["https://example.com/*"])
        with pytest.raises(LeidTimeoutError, match="timed out"):
            await client.screenshot("https://example.com/page")

    @pytest.mark.asyncio
    async def test_screenshot_http_error_raises_leid_http_error(self, fake_playwright):
        fake_playwright(response_status=502)
        client = make_client(["https://example.com/*"])
        with pytest.raises(LeidHttpError, match="502"):
            await client.screenshot("https://example.com/page")

    @pytest.mark.asyncio
    async def test_screenshot_network_error_raises_leid_connection_error(
        self, fake_playwright
    ):
        fake_playwright(
            goto_side_effect=_FakePlaywrightError("net::ERR_NAME_NOT_RESOLVED")
        )
        client = make_client(["https://example.com/*"])
        with pytest.raises(LeidConnectionError, match="network layer"):
            await client.screenshot("https://example.com/page")


class TestScreenshotSizeCap:
    """B-11 for screenshot — pre-cap on raw PNG bytes BEFORE base64."""

    @pytest.mark.asyncio
    async def test_screenshot_pre_cap_on_png_bytes(self, fake_playwright):
        """B-11: PNG larger than max_response_bytes → LeidResponseTooLargeError
        BEFORE base64 encoding step."""
        large_png = b"\x89PNG\r\n\x1a\n" + (b"x" * 2_000_000)
        fake_playwright(screenshot_bytes=large_png)
        client = make_client(
            ["https://example.com/*"],
            max_response_bytes=1_048_576,
        )
        with pytest.raises(
            LeidResponseTooLargeError, match="exceeds max_response_bytes"
        ):
            await client.screenshot("https://example.com/page")

    @pytest.mark.asyncio
    async def test_screenshot_pre_cap_under_threshold(self, fake_playwright):
        """Under-cap PNG succeeds and returns expected fields."""
        small_png = b"\x89PNG\r\n\x1a\n" + (b"x" * 1024)
        fake_playwright(screenshot_bytes=small_png)
        client = make_client(
            ["https://example.com/*"],
            max_response_bytes=1_048_576,
        )
        result = await client.screenshot("https://example.com/page")
        assert result["size_bytes"] == len(small_png)


class TestScreenshotReturnShape:
    """Return shape conforms to v0.8.1 contract."""

    @pytest.mark.asyncio
    async def test_screenshot_returns_correct_shape(self, fake_playwright):
        png = b"\x89PNG\r\n\x1a\n_test_payload_"
        fake_playwright(screenshot_bytes=png, page_url="https://example.com/final")
        client = make_client(["https://example.com/*"])
        result = await client.screenshot("https://example.com/page")

        assert set(result.keys()) == {
            "url",
            "final_url",
            "image_base64",
            "image_format",
            "size_bytes",
            "full_page",
        }
        assert result["url"] == "https://example.com/page"
        assert result["final_url"] == "https://example.com/final"
        assert result["image_format"] == "png"
        assert result["size_bytes"] == len(png)
        assert result["full_page"] is True  # config default

    @pytest.mark.asyncio
    async def test_screenshot_image_base64_decodes_to_original_png(
        self, fake_playwright
    ):
        """D-17: result['image_base64'] decodes to the exact bytes returned by
        page.screenshot."""
        import base64 as _b64
        png = b"\x89PNG\r\n\x1a\n_round_trip_payload_with_unique_marker_"
        fake_playwright(screenshot_bytes=png)
        client = make_client(["https://example.com/*"])
        result = await client.screenshot("https://example.com/page")
        decoded = _b64.b64decode(result["image_base64"])
        assert decoded == png

    @pytest.mark.asyncio
    async def test_screenshot_full_page_true_passed_to_playwright(
        self, fake_playwright
    ):
        """D-20: when config sets full_page=True, page.screenshot called with it."""
        _, _, _, page_mock, _ = fake_playwright()
        client = make_client(
            ["https://example.com/*"],
            browser_screenshot_full_page=True,
        )
        await client.screenshot("https://example.com/page")
        page_mock.screenshot.assert_awaited_once_with(full_page=True, type="png")

    @pytest.mark.asyncio
    async def test_screenshot_full_page_false_passed_to_playwright(
        self, fake_playwright
    ):
        """D-20: when config sets full_page=False, page.screenshot called with it."""
        _, _, _, page_mock, _ = fake_playwright()
        client = make_client(
            ["https://example.com/*"],
            browser_screenshot_full_page=False,
        )
        await client.screenshot("https://example.com/page")
        page_mock.screenshot.assert_awaited_once_with(full_page=False, type="png")


class TestScreenshotResourceCleanup:
    """B-7 for screenshot — all three resources closed even on failure."""

    @pytest.mark.asyncio
    async def test_screenshot_closes_resources_on_navigation_failure(
        self, fake_playwright
    ):
        _, browser_mock, context_mock, _, _ = fake_playwright(
            goto_side_effect=_FakePlaywrightError("network layer")
        )
        client = make_client(["https://example.com/*"])
        with pytest.raises(LeidConnectionError):
            await client.screenshot("https://example.com/page")

        assert context_mock.close.await_count == 1
        assert browser_mock.close.await_count == 1
        pw_runtime = sys.modules[
            "playwright.async_api"
        ].async_playwright.return_value.start.return_value  # type: ignore[attr-defined]
        assert pw_runtime.stop.await_count == 1

    @pytest.mark.asyncio
    async def test_screenshot_closes_resources_on_size_cap_breach(self, fake_playwright):
        large_png = b"\x89PNG" + (b"x" * 2_000_000)
        _, browser_mock, context_mock, _, _ = fake_playwright(
            screenshot_bytes=large_png,
        )
        client = make_client(
            ["https://example.com/*"],
            max_response_bytes=1_048_576,
        )
        with pytest.raises(LeidResponseTooLargeError):
            await client.screenshot("https://example.com/page")

        assert context_mock.close.await_count == 1
        assert browser_mock.close.await_count == 1
        pw_runtime = sys.modules[
            "playwright.async_api"
        ].async_playwright.return_value.start.return_value  # type: ignore[attr-defined]
        assert pw_runtime.stop.await_count == 1


# ---------------------------------------------------------------------------
# B-10 regression guards (closes Audit N-2 from AUDIT_v0.8.0_OPID_VEF.md)
# ---------------------------------------------------------------------------

class TestB10NoJavaScriptInjection:
    """B-10: HERETIC injects no JavaScript code into the page in v0.8.0+.

    These regression-guard tests assert that ``page.evaluate`` is NEVER called
    by either ``render_url`` or ``screenshot``. A future contributor who adds
    ``page.evaluate(agent_input)`` to either method would silently violate
    B-10; these tests turn that into a test failure.

    Closes Auditor recommendation N-2 from AUDIT_v0.8.0_OPID_VEF.md, which
    deferred this test to v0.8.x when richer page-mock infrastructure
    (the screenshot mock chain) became available.
    """

    @pytest.mark.asyncio
    async def test_render_url_does_not_call_page_evaluate(self, fake_playwright):
        """B-10: after a successful render_url, page.evaluate was never called."""
        _, _, _, page_mock, _ = fake_playwright()
        client = make_client(["https://example.com/*"])
        await client.render_url("https://example.com/page")
        page_mock.evaluate.assert_not_called()

    @pytest.mark.asyncio
    async def test_screenshot_does_not_call_page_evaluate(self, fake_playwright):
        """B-10: after a successful screenshot, page.evaluate was never called."""
        _, _, _, page_mock, _ = fake_playwright()
        client = make_client(["https://example.com/*"])
        await client.screenshot("https://example.com/page")
        page_mock.evaluate.assert_not_called()


# ---------------------------------------------------------------------------
# Smoke test — real Chromium (default-skip)
# ---------------------------------------------------------------------------

@pytest.mark.requires_playwright
@pytest.mark.asyncio
async def test_render_url_smoke_real_chromium():
    """Smoke test exercising real Playwright + Chromium.

    Default-skip in CI. Requires:
        pip install heretic[browser]
        playwright install chromium

    Renders a data: URL (no network) and asserts text extraction works.
    """
    pytest.importorskip("playwright")
    # Allowlist must match data: URLs by being a wildcard for this smoke test.
    client = make_client(["data:*"], allow_http=True)
    data_url = (
        "data:text/html,"
        "<html><head><title>Smoke</title></head><body><p>Hi</p></body></html>"
    )
    result = await client.render_url(data_url)
    assert result["title"] == "Smoke"
    assert "Hi" in result["text"]


@pytest.mark.requires_playwright
@pytest.mark.asyncio
async def test_screenshot_smoke_real_chromium():
    """Smoke test for v0.8.1 screenshot exercising real Playwright + Chromium.

    Default-skip in CI. Renders a data: URL and asserts the result['image_base64']
    decodes to non-empty PNG bytes starting with the canonical PNG signature.
    """
    import base64 as _b64
    pytest.importorskip("playwright")
    client = make_client(["data:*"], allow_http=True)
    data_url = (
        "data:text/html,"
        "<html><head><title>SmokeShot</title></head><body><p>Hi</p></body></html>"
    )
    result = await client.screenshot(data_url)
    assert result["image_format"] == "png"
    assert result["size_bytes"] > 0
    decoded = _b64.b64decode(result["image_base64"])
    # PNG signature: 89 50 4E 47 0D 0A 1A 0A
    assert decoded.startswith(b"\x89PNG\r\n\x1a\n")
