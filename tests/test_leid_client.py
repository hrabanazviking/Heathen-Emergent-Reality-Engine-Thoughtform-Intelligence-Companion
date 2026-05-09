"""
Tests for LeidClient — sandboxed HTTP fetch operations.

Covers:
    - URL gateway (_validate_url): allowlist accept/reject, HTTPS-only default,
                                   HTTP allowed when configured
    - fetch_url: happy path, URL rejection, timeout, HTTP error (4xx/5xx),
                 response-too-large (raises LeidResponseTooLargeError), connection error, redirect error
    - extract_text: HTML stripping, title extraction, non-HTML passthrough

All HTTP calls are mocked via unittest.mock — no real network requests.

Ref: src/heretic/skilningr/senses/leid/client.py
     TASK_HERETIC_v0.6.2_MORE_SENSES.md §3
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from heretic.skilningr.config_model import LeidConfig
from heretic.skilningr.senses.leid.client import LeidClient, _extract_text_from_html
from heretic.skilningr.senses.leid.errors import (
    LeidConnectionError,
    LeidHttpError,
    LeidResponseTooLargeError,
    LeidTimeoutError,
    UrlNotAllowedError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_client(patterns: list[str] = None, **kwargs) -> LeidClient:
    """Return a LeidClient with the given URL allowlist patterns."""
    if patterns is None:
        patterns = ["https://example.com/*"]
    config = LeidConfig(url_allowlist_patterns=patterns, **kwargs)
    return LeidClient(config)


def make_mock_response(
    status_code: int = 200,
    content: bytes = b"<html><body>Hello</body></html>",
    content_type: str = "text/html; charset=utf-8",
) -> MagicMock:
    """Return a mock httpx.Response."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.content = content
    mock.text = content.decode("utf-8", errors="replace")
    # Use a MagicMock for headers so .get() can be configured
    headers_mock = MagicMock()
    headers_mock.get = lambda k, default="": (
        content_type if k == "content-type" else default
    )
    mock.headers = headers_mock
    return mock


# ---------------------------------------------------------------------------
# URL gateway — _validate_url
# ---------------------------------------------------------------------------

class TestLeidClientUrlGateway:

    def test_validate_url_accepted(self):
        """_validate_url accepts a URL matching an allowlist pattern."""
        client = make_client(["https://docs.python.org/*"])
        normalised = client._validate_url("https://docs.python.org/3/library/os.html")
        assert "docs.python.org" in normalised

    def test_validate_url_not_in_allowlist_raises(self):
        """_validate_url raises UrlNotAllowedError for non-matching URLs."""
        client = make_client(["https://docs.python.org/*"])
        with pytest.raises(UrlNotAllowedError):
            client._validate_url("https://evil.com/steal")

    def test_validate_http_rejected_when_https_only(self):
        """HTTP URL is rejected when allow_http=False (default)."""
        client = make_client(["http://example.com/*"], allow_http=False)
        with pytest.raises(UrlNotAllowedError, match="HTTP"):
            client._validate_url("http://example.com/page")

    def test_validate_http_accepted_when_allow_http(self):
        """HTTP URL is accepted when allow_http=True and pattern matches."""
        client = make_client(["http://example.com/*"], allow_http=True)
        normalised = client._validate_url("http://example.com/page")
        assert "example.com" in normalised

    def test_validate_url_scheme_normalised(self):
        """Uppercase HTTPS scheme is normalised before matching."""
        client = make_client(["https://docs.python.org/*"])
        normalised = client._validate_url("HTTPS://docs.python.org/3/")
        assert normalised.startswith("https://")

    def test_validate_url_empty_allowlist_raises(self):
        """_validate_url raises when allowlist is empty."""
        config = LeidConfig(url_allowlist_patterns=[])
        client = LeidClient(config)
        with pytest.raises(UrlNotAllowedError):
            client._validate_url("https://example.com/page")


# ---------------------------------------------------------------------------
# fetch_url
# ---------------------------------------------------------------------------

class TestLeidClientFetchUrl:

    @pytest.mark.asyncio
    async def test_fetch_url_success(self):
        """fetch_url returns structured result for a successful GET."""
        client = make_client(["https://example.com/*"])
        body_bytes = b"<html><body>Hello</body></html>"
        mock_response = make_mock_response(status_code=200, content=body_bytes)

        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_context):
            result = await client.fetch_url("https://example.com/page")

        assert result["status_code"] == 200
        assert "Hello" in result["body"]
        assert result["url"] == "https://example.com/page"
        # v0.6.2: no 'truncated' key — oversized bodies raise LeidResponseTooLargeError

    @pytest.mark.asyncio
    async def test_fetch_url_not_allowed_raises(self):
        """fetch_url raises UrlNotAllowedError for URLs not in allowlist."""
        client = make_client(["https://example.com/*"])
        with pytest.raises(UrlNotAllowedError):
            await client.fetch_url("https://evil.com/steal")

    @pytest.mark.asyncio
    async def test_fetch_url_timeout_raises(self):
        """fetch_url raises LeidTimeoutError on httpx timeout."""
        client = make_client(["https://example.com/*"])
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(
            side_effect=httpx.TimeoutException("timed out")
        )
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_context):
            with pytest.raises(LeidTimeoutError):
                await client.fetch_url("https://example.com/slow")

    @pytest.mark.asyncio
    async def test_fetch_url_http_error_raises(self):
        """fetch_url raises LeidHttpError for 4xx and 5xx responses."""
        client = make_client(["https://example.com/*"])
        mock_response = make_mock_response(status_code=404, content=b"Not Found")
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_context):
            with pytest.raises(LeidHttpError):
                await client.fetch_url("https://example.com/missing")

    @pytest.mark.asyncio
    async def test_fetch_url_response_too_large_raises(self):
        """fetch_url raises LeidResponseTooLargeError when body exceeds max_response_bytes.

        v0.6.2: full body is buffered then the size check fires. No partial
        content is returned — the agent receives a clear error instead of a
        silently truncated body. v0.6.2.1 will add streaming early termination.
        """
        config = LeidConfig(
            url_allowlist_patterns=["https://example.com/*"],
            max_response_bytes=10,
        )
        client = LeidClient(config)
        big_body = b"x" * 1000
        mock_response = make_mock_response(status_code=200, content=big_body)
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_context):
            with pytest.raises(LeidResponseTooLargeError) as exc_info:
                await client.fetch_url("https://example.com/big")

        # Error message must name the actual size and the cap
        assert "1000" in str(exc_info.value)
        assert "10" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_url_connection_error_raises(self):
        """fetch_url raises LeidConnectionError for httpx connect errors."""
        client = make_client(["https://example.com/*"])
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(
            side_effect=httpx.ConnectError("connection refused")
        )
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_context):
            with pytest.raises(LeidConnectionError):
                await client.fetch_url("https://example.com/down")

    @pytest.mark.asyncio
    async def test_fetch_url_too_many_redirects_raises(self):
        """fetch_url raises LeidConnectionError when redirect limit is exceeded."""
        client = make_client(["https://example.com/*"])
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(
            side_effect=httpx.TooManyRedirects("too many redirects")
        )
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_context):
            with pytest.raises(LeidConnectionError):
                await client.fetch_url("https://example.com/redirect-loop")


# ---------------------------------------------------------------------------
# extract_text
# ---------------------------------------------------------------------------

class TestLeidClientExtractText:

    @pytest.mark.asyncio
    async def test_extract_text_strips_html_tags(self):
        """extract_text strips HTML tags and returns plain text."""
        client = make_client(["https://example.com/*"])
        html_body = b"<html><head><title>My Page</title></head><body><p>Hello World</p></body></html>"
        mock_response = make_mock_response(status_code=200, content=html_body)
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_context):
            result = await client.extract_text("https://example.com/page")

        assert "Hello World" in result["text"]
        assert "<p>" not in result["text"]
        assert result["title"] == "My Page"
        assert result["url"] == "https://example.com/page"

    @pytest.mark.asyncio
    async def test_extract_text_non_html_returns_raw_body(self):
        """extract_text returns raw body for non-HTML content types."""
        client = make_client(["https://example.com/*"])
        plain_body = b"plain text content"
        mock_response = make_mock_response(
            status_code=200,
            content=plain_body,
            content_type="text/plain",
        )
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_context):
            result = await client.extract_text("https://example.com/text")

        assert "plain text content" in result["text"]
        assert result["title"] is None

    @pytest.mark.asyncio
    async def test_extract_text_url_not_allowed_raises(self):
        """extract_text raises UrlNotAllowedError for non-matching URLs."""
        client = make_client(["https://example.com/*"])
        with pytest.raises(UrlNotAllowedError):
            await client.extract_text("https://evil.com/page")

    @pytest.mark.asyncio
    async def test_extract_text_script_tags_excluded(self):
        """extract_text skips content inside <script> tags."""
        client = make_client(["https://example.com/*"])
        html_body = b"<html><body><script>alert('xss');</script><p>Clean</p></body></html>"
        mock_response = make_mock_response(status_code=200, content=html_body)
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_context):
            result = await client.extract_text("https://example.com/scripted")

        assert "alert" not in result["text"]
        assert "Clean" in result["text"]


# ---------------------------------------------------------------------------
# _extract_text_from_html (unit tests for the helper directly)
# ---------------------------------------------------------------------------

class TestExtractTextFromHtml:

    def test_strips_tags(self):
        """_extract_text_from_html strips HTML tags from content."""
        html = "<html><body><p>Hello <b>World</b></p></body></html>"
        text, title = _extract_text_from_html(html)
        assert "Hello" in text
        assert "World" in text
        assert "<b>" not in text

    def test_extracts_title(self):
        """_extract_text_from_html extracts the page title."""
        html = "<html><head><title>My Page</title></head><body><p>Content</p></body></html>"
        text, title = _extract_text_from_html(html)
        assert title == "My Page"

    def test_skips_script_content(self):
        """_extract_text_from_html skips content inside <script> tags."""
        html = "<html><body><script>secret_js();</script><p>Visible</p></body></html>"
        text, title = _extract_text_from_html(html)
        assert "secret_js" not in text
        assert "Visible" in text

    def test_skips_style_content(self):
        """_extract_text_from_html skips content inside <style> tags."""
        html = "<html><head><style>body { color: red; }</style></head><body><p>Text</p></body></html>"
        text, title = _extract_text_from_html(html)
        assert "color" not in text
        assert "Text" in text

    def test_empty_html_returns_empty(self):
        """_extract_text_from_html handles empty input gracefully."""
        text, title = _extract_text_from_html("")
        assert text == ""
        assert title is None
