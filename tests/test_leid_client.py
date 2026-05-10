"""
Tests for LeidClient — sandboxed HTTP fetch operations.

Covers:
    - URL gateway (_validate_url): allowlist accept/reject, HTTPS-only default,
                                   HTTP allowed when configured
    - fetch_url: happy path, URL rejection, timeout, HTTP error (4xx/5xx),
                 response-too-large (raises LeidResponseTooLargeError), connection error, redirect error
    - fetch_url v0.7.1 streaming: mid-stream abort, Content-Length pre-cap,
                 byte-exact boundary, status-check-before-body, accumulator
                 memory bound
    - extract_text: HTML stripping, title extraction, non-HTML passthrough

All HTTP calls are mocked via unittest.mock — no real network requests.

Ref: src/heretic/skilningr/senses/leid/client.py
     TASK_HERETIC_v0.6.2_MORE_SENSES.md §3
     TASK_HERETIC_v0.7.1_LEID_STREAMING.md (Straumr á Leið)
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


def make_streaming_response(
    status_code: int = 200,
    chunks: list[bytes] | None = None,
    content_type: str = "text/html; charset=utf-8",
    content_length: str | None = None,
) -> MagicMock:
    """Return a mock httpx.Response shaped for the streaming code path.

    Supplies an async aiter_bytes that yields the given chunks. The chunk
    list mirrors what httpx would yield from a real network read.
    """
    if chunks is None:
        chunks = [b"<html><body>Hello</body></html>"]

    mock = MagicMock()
    mock.status_code = status_code

    headers: dict[str, str] = {"content-type": content_type}
    if content_length is not None:
        headers["content-length"] = content_length
    headers_mock = MagicMock()
    headers_mock.get = lambda k, default=None: headers.get(k.lower(), default)
    mock.headers = headers_mock

    async def _aiter_bytes(chunk_size: int = 65536):
        for chunk in chunks:
            yield chunk

    mock.aiter_bytes = _aiter_bytes
    return mock


def make_streaming_mock_client(
    response: MagicMock | None = None,
    *,
    stream_side_effect: BaseException | None = None,
) -> tuple[MagicMock, MagicMock]:
    """Return (mock_async_client_ctx, mock_async_client_instance).

    The async-client context manager wraps the instance whose `.stream()`
    returns the per-response inner context manager.
    """
    inner_ctx = MagicMock()
    if stream_side_effect is not None:
        inner_ctx.__aenter__ = AsyncMock(side_effect=stream_side_effect)
    else:
        inner_ctx.__aenter__ = AsyncMock(
            return_value=response if response is not None
            else make_streaming_response()
        )
    inner_ctx.__aexit__ = AsyncMock(return_value=None)

    instance = MagicMock()
    # client.stream() is a sync call returning an async context manager
    instance.stream = MagicMock(return_value=inner_ctx)

    outer_ctx = MagicMock()
    outer_ctx.__aenter__ = AsyncMock(return_value=instance)
    outer_ctx.__aexit__ = AsyncMock(return_value=None)
    return outer_ctx, instance


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
        response = make_streaming_response(
            status_code=200, chunks=[body_bytes],
        )
        outer_ctx, _ = make_streaming_mock_client(response)

        with patch("httpx.AsyncClient", return_value=outer_ctx):
            result = await client.fetch_url("https://example.com/page")

        assert result["status_code"] == 200
        assert "Hello" in result["body"]
        assert result["url"] == "https://example.com/page"
        assert result["size_bytes"] == len(body_bytes)
        assert "truncated" not in result  # v0.7.1: success returns no truncated key

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
        outer_ctx, _ = make_streaming_mock_client(
            stream_side_effect=httpx.TimeoutException("timed out"),
        )

        with patch("httpx.AsyncClient", return_value=outer_ctx):
            with pytest.raises(LeidTimeoutError):
                await client.fetch_url("https://example.com/slow")

    @pytest.mark.asyncio
    async def test_fetch_url_http_error_raises(self):
        """fetch_url raises LeidHttpError for 4xx and 5xx responses."""
        client = make_client(["https://example.com/*"])
        response = make_streaming_response(
            status_code=404, chunks=[b"Not Found"],
        )
        outer_ctx, _ = make_streaming_mock_client(response)

        with patch("httpx.AsyncClient", return_value=outer_ctx):
            with pytest.raises(LeidHttpError) as exc_info:
                await client.fetch_url("https://example.com/missing")

        assert "404" in str(exc_info.value)
        assert "Not Found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_url_response_too_large_raises(self):
        """fetch_url raises LeidResponseTooLargeError on cap breach.

        v0.7.1 Straumr á Leið: streaming abort. The accumulator is checked
        after each chunk extend; raise fires as soon as the cap is breached.
        Agent receives a structured error, never partial content.
        """
        config = LeidConfig(
            url_allowlist_patterns=["https://example.com/*"],
            max_response_bytes=10,
        )
        client = LeidClient(config)
        # 1000-byte body delivered as a single chunk — cap=10 raises after
        # the very first extend, before any further bytes arrive.
        big_body = b"x" * 1000
        response = make_streaming_response(
            status_code=200, chunks=[big_body],
        )
        outer_ctx, _ = make_streaming_mock_client(response)

        with patch("httpx.AsyncClient", return_value=outer_ctx):
            with pytest.raises(LeidResponseTooLargeError) as exc_info:
                await client.fetch_url("https://example.com/big")

        # Error message must name both the streamed size and the cap
        msg = str(exc_info.value)
        assert "1000" in msg
        assert "10" in msg

    @pytest.mark.asyncio
    async def test_fetch_url_connection_error_raises(self):
        """fetch_url raises LeidConnectionError for httpx connect errors."""
        client = make_client(["https://example.com/*"])
        outer_ctx, _ = make_streaming_mock_client(
            stream_side_effect=httpx.ConnectError("connection refused"),
        )

        with patch("httpx.AsyncClient", return_value=outer_ctx):
            with pytest.raises(LeidConnectionError):
                await client.fetch_url("https://example.com/down")

    @pytest.mark.asyncio
    async def test_fetch_url_too_many_redirects_raises(self):
        """fetch_url raises LeidConnectionError when redirect limit is exceeded."""
        client = make_client(["https://example.com/*"])
        outer_ctx, _ = make_streaming_mock_client(
            stream_side_effect=httpx.TooManyRedirects("too many redirects"),
        )

        with patch("httpx.AsyncClient", return_value=outer_ctx):
            with pytest.raises(LeidConnectionError):
                await client.fetch_url("https://example.com/redirect-loop")


# ---------------------------------------------------------------------------
# fetch_url v0.7.1 streaming-specific tests (Straumr á Leið)
# ---------------------------------------------------------------------------

class TestLeidClientStreaming:
    """Streaming-specific tests added with v0.7.1.

    Verifies the contract documented in
    docs/cartography/DATA_FLOW.md §4.12.2.1 (Straumr á Leið).
    """

    @pytest.mark.asyncio
    async def test_aborts_mid_stream_when_cap_exceeded(self):
        """Stream abort fires after the chunk that breaches the cap, not after all chunks.

        Setup: 4 chunks of 4 KiB each (16 KiB total) with max_response_bytes=10000.
        After chunk 3 (12 KiB) the accumulator exceeds the cap; raise must fire
        there. Chunk 4 must never be requested.
        """
        config = LeidConfig(
            url_allowlist_patterns=["https://example.com/*"],
            max_response_bytes=10_000,
        )
        client = LeidClient(config)

        chunk = b"x" * 4096
        chunks_yielded: list[int] = []

        async def _instrumented_aiter(chunk_size: int = 65536):
            for i, c in enumerate([chunk, chunk, chunk, chunk]):
                chunks_yielded.append(i)
                yield c

        response = make_streaming_response(status_code=200)
        response.aiter_bytes = _instrumented_aiter
        outer_ctx, _ = make_streaming_mock_client(response)

        with patch("httpx.AsyncClient", return_value=outer_ctx):
            with pytest.raises(LeidResponseTooLargeError):
                await client.fetch_url("https://example.com/big")

        # Three chunks reached: 0, 1, 2 push us to 12 KiB > 10 KiB cap.
        # The 4th chunk (index 3) must NEVER be yielded.
        assert chunks_yielded == [0, 1, 2], (
            f"Stream did not abort early — yielded {chunks_yielded}; "
            "expected only [0, 1, 2] before raise"
        )

    @pytest.mark.asyncio
    async def test_content_length_pre_cap_aborts_before_any_chunk(self):
        """Content-Length larger than cap raises before any chunk is read.

        The header-based pre-cap saves even the first chunk fetch. The
        aiter_bytes generator must not be entered.
        """
        config = LeidConfig(
            url_allowlist_patterns=["https://example.com/*"],
            max_response_bytes=1_000,
        )
        client = LeidClient(config)

        chunks_yielded: list[int] = []

        async def _instrumented_aiter(chunk_size: int = 65536):
            chunks_yielded.append(0)
            yield b"x"

        response = make_streaming_response(
            status_code=200, content_length="99999",
        )
        response.aiter_bytes = _instrumented_aiter
        outer_ctx, _ = make_streaming_mock_client(response)

        with patch("httpx.AsyncClient", return_value=outer_ctx):
            with pytest.raises(LeidResponseTooLargeError) as exc_info:
                await client.fetch_url("https://example.com/declared-big")

        assert chunks_yielded == [], (
            "Content-Length pre-cap failed — aiter_bytes was entered when "
            "the declared length already exceeded the cap"
        )
        assert "99999" in str(exc_info.value)
        assert "1000" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_malformed_content_length_falls_through_to_chunk_loop(self):
        """A non-numeric Content-Length is ignored; streaming proceeds normally."""
        client = make_client(["https://example.com/*"])
        response = make_streaming_response(
            status_code=200,
            chunks=[b"hello world"],
            content_length="not-a-number",
        )
        outer_ctx, _ = make_streaming_mock_client(response)

        with patch("httpx.AsyncClient", return_value=outer_ctx):
            result = await client.fetch_url("https://example.com/page")

        assert result["status_code"] == 200
        assert "hello world" in result["body"]

    @pytest.mark.asyncio
    async def test_byte_exact_boundary_succeeds_at_cap(self):
        """A response exactly equal to max_response_bytes succeeds.

        The cap is exclusive on the upper side: len(acc) > max_bytes raises.
        len(acc) == max_bytes is success.
        """
        config = LeidConfig(
            url_allowlist_patterns=["https://example.com/*"],
            max_response_bytes=10,
        )
        client = LeidClient(config)
        # Exactly 10 bytes — boundary success
        response = make_streaming_response(
            status_code=200, chunks=[b"xxxxxxxxxx"],
        )
        outer_ctx, _ = make_streaming_mock_client(response)

        with patch("httpx.AsyncClient", return_value=outer_ctx):
            result = await client.fetch_url("https://example.com/exact")

        assert result["size_bytes"] == 10
        assert result["body"] == "xxxxxxxxxx"

    @pytest.mark.asyncio
    async def test_byte_exact_boundary_plus_one_raises(self):
        """A response exactly one byte over the cap raises.

        Confirms the cap is strict at len(acc) > max_bytes.
        """
        config = LeidConfig(
            url_allowlist_patterns=["https://example.com/*"],
            max_response_bytes=10,
        )
        client = LeidClient(config)
        response = make_streaming_response(
            status_code=200, chunks=[b"xxxxxxxxxxX"],  # 11 bytes
        )
        outer_ctx, _ = make_streaming_mock_client(response)

        with patch("httpx.AsyncClient", return_value=outer_ctx):
            with pytest.raises(LeidResponseTooLargeError):
                await client.fetch_url("https://example.com/over")

    @pytest.mark.asyncio
    async def test_status_check_runs_before_body_accumulation(self):
        """4xx/5xx raise before the body accumulator is built.

        For a 404 response, the body is read only as a bounded peek (≤500
        bytes) for the diagnostic message. The full body accumulator path
        is never reached.
        """
        client = make_client(["https://example.com/*"])
        response = make_streaming_response(
            status_code=500,
            chunks=[b"internal server error pancake batter on fire"],
        )
        outer_ctx, _ = make_streaming_mock_client(response)

        with patch("httpx.AsyncClient", return_value=outer_ctx):
            with pytest.raises(LeidHttpError) as exc_info:
                await client.fetch_url("https://example.com/oops")

        msg = str(exc_info.value)
        assert "500" in msg
        # The diagnostic peek includes some of the error body
        assert "pancake" in msg or "internal server error" in msg

    @pytest.mark.asyncio
    async def test_multi_chunk_success_under_cap(self):
        """Multiple chunks under the cap accumulate correctly into body."""
        config = LeidConfig(
            url_allowlist_patterns=["https://example.com/*"],
            max_response_bytes=1_000_000,
        )
        client = LeidClient(config)
        chunks = [b"first chunk ", b"second chunk ", b"third chunk"]
        expected = b"".join(chunks)
        response = make_streaming_response(status_code=200, chunks=chunks)
        outer_ctx, _ = make_streaming_mock_client(response)

        with patch("httpx.AsyncClient", return_value=outer_ctx):
            result = await client.fetch_url("https://example.com/multi")

        assert result["size_bytes"] == len(expected)
        assert result["body"] == expected.decode("utf-8")

    @pytest.mark.asyncio
    async def test_error_peek_is_bounded_for_giant_4xx_body(self):
        """A 4xx response with a giant body still yields a small error message.

        The bounded error peek must not accumulate the full body. With
        a 200 KiB error body, the peek must stay under a small bound.
        """
        client = make_client(["https://example.com/*"])
        # 200 KiB error body delivered in 1-KiB chunks
        big_chunk = b"E" * 1024
        chunks = [big_chunk] * 200
        response = make_streaming_response(status_code=403, chunks=chunks)
        outer_ctx, _ = make_streaming_mock_client(response)

        with patch("httpx.AsyncClient", return_value=outer_ctx):
            with pytest.raises(LeidHttpError) as exc_info:
                await client.fetch_url("https://example.com/forbidden")

        msg = str(exc_info.value)
        assert "403" in msg
        # Diagnostic peek is hard-bounded by _ERROR_PEEK_BYTES (500). The
        # full message includes the f-string boilerplate, so a generous
        # upper bound (5 KiB) is still wildly less than the 200 KiB body.
        assert len(msg) < 5_000, (
            f"Error message length {len(msg)} suggests the peek leaked "
            "the full 200 KiB error body — peek bound is broken"
        )


# ---------------------------------------------------------------------------
# extract_text
# ---------------------------------------------------------------------------

class TestLeidClientExtractText:

    @pytest.mark.asyncio
    async def test_extract_text_strips_html_tags(self):
        """extract_text strips HTML tags and returns plain text."""
        client = make_client(["https://example.com/*"])
        html_body = b"<html><head><title>My Page</title></head><body><p>Hello World</p></body></html>"
        response = make_streaming_response(
            status_code=200, chunks=[html_body],
        )
        outer_ctx, _ = make_streaming_mock_client(response)

        with patch("httpx.AsyncClient", return_value=outer_ctx):
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
        response = make_streaming_response(
            status_code=200,
            chunks=[plain_body],
            content_type="text/plain",
        )
        outer_ctx, _ = make_streaming_mock_client(response)

        with patch("httpx.AsyncClient", return_value=outer_ctx):
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
        response = make_streaming_response(
            status_code=200, chunks=[html_body],
        )
        outer_ctx, _ = make_streaming_mock_client(response)

        with patch("httpx.AsyncClient", return_value=outer_ctx):
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
