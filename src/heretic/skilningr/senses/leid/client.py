"""
LeidClient — sandboxed HTTP fetch client for the Leið sense.

LeidClient executes HTTP GET requests through a strict URL allowlist gate:
    sandbox.url_matches_allowlist() is called BEFORE any httpx request is sent.
    No request is made to a URL that does not match at least one pattern.

SANDBOX INVARIANT (DO NOT WEAKEN):
    url_matches_allowlist() is called BEFORE any httpx call. This gate cannot
    be bypassed, reordered, or short-circuited.

PROTOCOL INVARIANTS:
    - GET only. No POST, PUT, DELETE, or other methods.
    - HTTPS-only by default. HTTP requires LeidConfig.allow_http: true AND a
      matching allowlist pattern. HTTP URLs are always logged as warnings.
    - No cookies stored, sent, or accepted (stateless; httpx client cookies not set).
    - No JavaScript execution (httpx only; playwright/selenium = v0.8 Opið Vef).
    - Response body is capped at LeidConfig.max_response_bytes — enforced via
      streaming abort (httpx.AsyncClient.stream + aiter_bytes). When the
      accumulator exceeds the cap, LeidResponseTooLargeError is raised mid-stream;
      the connection closes during stack unwind; remaining bytes never travel.
      Memory at moment of raise is bounded by max_response_bytes + chunk_size
      (default ~1.06 MiB). Agent receives a structured error, never partial content.
    - Content-Length pre-cap: if the response carries a Content-Length header
      that already exceeds the cap, LeidResponseTooLargeError is raised before
      any chunk is read. Malformed Content-Length values are ignored.
    - 4xx/5xx status check runs before body accumulation. The error-message tail
      is read via a bounded peek (max ~500 bytes) so a giant 4xx body cannot
      blow memory.
    - Redirects followed up to LeidConfig.max_redirects (default 5).
    - Custom User-Agent: LeidConfig.user_agent.

HTML text extraction (extract_text):
    Uses the stdlib html.parser.HTMLParser subclass to strip tags and collect
    visible text. This is a shallow extraction — JS-rendered pages return
    near-empty text because httpx does not execute JavaScript.
    This boundary is documented as a known limit, NOT a bug.
    playwright/selenium = v0.8 Opið Vef for JS-rendered pages.

A fresh httpx.AsyncClient is created per-request (no persistent connection pool
across calls). This keeps the lifecycle simple and avoids stale connection issues.

Ref: src/heretic/skilningr/senses/leid/INTERFACE.md
     src/heretic/skilningr/sandbox.py (url_matches_allowlist)
     TASK_HERETIC_v0.7.1_LEID_STREAMING.md (Straumr á Leið — streaming abort)
     TASK_HERETIC_v0.6.2_MORE_SENSES.md §3 (Leið sandbox invariants)
"""

from __future__ import annotations

import logging
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

import httpx

from heretic.skilningr.config_model import LeidConfig
from heretic.skilningr.sandbox import url_matches_allowlist
from heretic.skilningr.senses.leid.errors import (
    LeidConnectionError,
    LeidHttpError,
    LeidResponseTooLargeError,
    LeidTimeoutError,
    UrlNotAllowedError,
)

logger = logging.getLogger(__name__)


class _TextExtractor(HTMLParser):
    """Minimal stdlib HTML tag stripper.

    Collects visible text content, skipping script and style element bodies.
    Also captures the page <title> when present.

    Known boundary: JS-rendered content will not be present because httpx
    does not execute JavaScript. This is documented, not a bug.
    playwright = v0.6.2.1+ for JS pages.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._text_parts: list[str] = []
        self._skip_content = False
        self._in_title = False
        self._title_parts: list[str] = []
        self._skip_tags = frozenset({"script", "style", "head"})

    def handle_starttag(self, tag: str, attrs: list) -> None:
        tag_lower = tag.lower()
        if tag_lower in self._skip_tags:
            self._skip_content = True
        if tag_lower == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower in self._skip_tags:
            self._skip_content = False
        if tag_lower == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)
        elif not self._skip_content:
            stripped = data.strip()
            if stripped:
                self._text_parts.append(stripped)

    @property
    def text(self) -> str:
        return "\n".join(self._text_parts)

    @property
    def title(self) -> str | None:
        joined = "".join(self._title_parts).strip()
        return joined if joined else None


def _extract_text_from_html(html_body: str) -> tuple[str, str | None]:
    """Parse HTML with stdlib HTMLParser and return (text, title).

    Args:
        html_body: Raw HTML content string.

    Returns:
        Tuple of (plain_text, page_title_or_None).
    """
    extractor = _TextExtractor()
    try:
        extractor.feed(html_body)
        extractor.close()
    except Exception:
        # HTMLParser can raise on malformed HTML — return raw body as fallback
        return html_body, None
    return extractor.text, extractor.title


class LeidClient:
    """Sandboxed HTTP fetch client for the Leið sense.

    All fetch operations enforce the url_allowlist_patterns via
    sandbox.url_matches_allowlist() before any HTTP request is sent.

    Usage:
        client = LeidClient(config)
        result = await client.fetch_url("https://docs.python.org/3/")
        text   = await client.extract_text("https://docs.python.org/3/")
    """

    def __init__(
        self,
        config: LeidConfig,
        log: logging.Logger | None = None,
    ) -> None:
        """Initialise the Leið client.

        Args:
            config: LeidConfig — URL allowlist, timeouts, size caps, HTTP policy.
            log:    Optional logger. Defaults to module logger.
        """
        self._config = config
        self._log = log if log is not None else logging.getLogger(__name__)

    def _validate_url(self, url: str) -> str:
        """Validate that *url* matches the allowlist and return the normalised URL.

        Also enforces the HTTPS-only policy when allow_http is False.

        Args:
            url: The candidate URL string from the agent tool call.

        Returns:
            Normalised URL string (scheme lowercase, netloc lowercase).

        Raises:
            UrlNotAllowedError: URL does not match any allowlist pattern.
            UrlNotAllowedError: URL uses HTTP scheme and allow_http is False.
        """
        # Scheme check: reject http:// when allow_http is False
        url_stripped = url.strip()
        if url_stripped.lower().startswith("http://") and not self._config.allow_http:
            raise UrlNotAllowedError(
                f"HTTP (non-TLS) URL rejected: {url!r}. "
                f"Set skilningr.leid.allow_http: true to permit HTTP fetches. "
                f"HTTPS is strongly recommended."
            )

        allowed, result = url_matches_allowlist(url_stripped, self._config.url_allowlist_patterns)
        if not allowed:
            self._log.warning("Leið URL allowlist rejection: %s", result)
            raise UrlNotAllowedError(
                f"URL not permitted: {result}"
            )

        # Log HTTP warning even when allowed
        if url_stripped.lower().startswith("http://"):
            self._log.warning(
                "Leið: fetching HTTP (non-TLS) URL — content is unencrypted: %s",
                url_stripped,
            )

        return result  # type: ignore[return-value]

    def _is_html_content_type(self, content_type: str) -> bool:
        """Return True if the Content-Type header indicates HTML."""
        ct_lower = content_type.lower()
        return "text/html" in ct_lower or "application/xhtml" in ct_lower

    # Default chunk size for streaming reads. 64 KiB balances syscall
    # overhead against early-termination latency at small response caps.
    _STREAM_CHUNK_SIZE: int = 65536

    # Bounded peek for 4xx/5xx error-body tail. Keeps a giant error response
    # from blowing memory while still giving the agent a useful diagnostic.
    _ERROR_PEEK_BYTES: int = 500

    async def fetch_url(self, url: str) -> dict[str, Any]:
        """Fetch the raw content of a URL via HTTP GET (streaming).

        Size-cap behaviour (v0.7.1 Straumr á Leið — streaming abort):
            The body is read chunk-by-chunk via httpx.AsyncClient.stream() +
            aiter_bytes(). Each chunk extends a bytearray accumulator. After
            each extend, if the accumulator length exceeds
            LeidConfig.max_response_bytes, LeidResponseTooLargeError is
            raised immediately. The streaming context unwinds; the connection
            closes; remaining bytes are not transferred.

            Memory at moment of raise is bounded by
                max_response_bytes + _STREAM_CHUNK_SIZE
            because the chunk that pushes the accumulator past the cap is
            appended before the comparison.

            If the response carries a Content-Length header that already
            exceeds the cap, LeidResponseTooLargeError is raised before any
            chunk is read. Malformed Content-Length values are ignored
            (fall through to the chunk loop).

        Args:
            url: URL to fetch. Must match url_allowlist_patterns.

        Returns:
            dict with keys:
                url (str): normalised URL fetched
                status_code (int): HTTP response status code
                content_type (str): Content-Type header value (or "")
                body (str): response body as UTF-8 string (errors="replace")
                size_bytes (int): actual bytes read

        Raises:
            UrlNotAllowedError: URL not in allowlist or HTTP rejected.
            LeidTimeoutError: request timed out.
            LeidHttpError: 4xx or 5xx response status.
            LeidConnectionError: network-level error (DNS, TLS, TCP refused).
            LeidResponseTooLargeError: response body exceeds max_response_bytes
                (raised mid-stream as soon as the cap is breached).
        """
        # Gate — allowlist and HTTPS policy. Runs BEFORE any httpx call.
        normalised_url = self._validate_url(url)

        self._log.debug(
            "Leið fetch_url: %s (timeout=%ds, max_bytes=%d, stream_chunk=%d)",
            normalised_url, self._config.timeout_seconds,
            self._config.max_response_bytes, self._STREAM_CHUNK_SIZE,
        )

        timeout = httpx.Timeout(self._config.timeout_seconds)
        headers = {"User-Agent": self._config.user_agent}
        max_bytes = self._config.max_response_bytes

        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                max_redirects=self._config.max_redirects,
                headers=headers,
                follow_redirects=True,
            ) as client:
                async with client.stream("GET", normalised_url) as response:
                    # Pre-cap on Content-Length when present and well-formed.
                    cl_header = response.headers.get("content-length")
                    if cl_header is not None:
                        try:
                            declared = int(cl_header)
                        except ValueError:
                            declared = None
                        if declared is not None and declared > max_bytes:
                            self._log.warning(
                                "Leið fetch_url: Content-Length %d exceeds "
                                "max_response_bytes=%d for %s — aborting "
                                "before body read",
                                declared, max_bytes, normalised_url,
                            )
                            raise LeidResponseTooLargeError(
                                f"Response from {normalised_url!r} declares "
                                f"Content-Length {declared} bytes, which exceeds "
                                f"max_response_bytes={max_bytes}. Aborted before "
                                f"body read. Increase LeidConfig.max_response_bytes "
                                f"or fetch a smaller resource."
                            )

                    # 4xx/5xx status check runs before body accumulation.
                    if response.status_code >= 400:
                        error_acc = bytearray()
                        async for chunk in response.aiter_bytes(
                            self._STREAM_CHUNK_SIZE
                        ):
                            error_acc.extend(chunk)
                            if len(error_acc) >= self._ERROR_PEEK_BYTES:
                                break
                        peek = bytes(error_acc[: self._ERROR_PEEK_BYTES])
                        peek_str = peek.decode("utf-8", errors="replace")
                        raise LeidHttpError(
                            f"HTTP {response.status_code} from "
                            f"{normalised_url!r}. Response body (truncated): "
                            f"{peek_str!r}"
                        )

                    content_type = response.headers.get("content-type", "")

                    # Streaming accumulator with mid-stream cap enforcement.
                    acc = bytearray()
                    async for chunk in response.aiter_bytes(
                        self._STREAM_CHUNK_SIZE
                    ):
                        acc.extend(chunk)
                        if len(acc) > max_bytes:
                            self._log.warning(
                                "Leið fetch_url: streamed %d bytes from %s, "
                                "exceeds max_response_bytes=%d — aborting "
                                "stream and raising LeidResponseTooLargeError",
                                len(acc), normalised_url, max_bytes,
                            )
                            raise LeidResponseTooLargeError(
                                f"Response from {normalised_url!r} exceeds "
                                f"max_response_bytes={max_bytes}; streamed "
                                f"{len(acc)} bytes before abort. Increase "
                                f"LeidConfig.max_response_bytes or fetch a "
                                f"smaller resource."
                            )
                    size_bytes = len(acc)
                    body = bytes(acc).decode("utf-8", errors="replace")
                    status_code = response.status_code
        except httpx.TimeoutException as exc:
            raise LeidTimeoutError(
                f"Request to {normalised_url!r} timed out after "
                f"{self._config.timeout_seconds}s: {exc}"
            ) from exc
        except httpx.TooManyRedirects as exc:
            raise LeidConnectionError(
                f"Too many redirects fetching {normalised_url!r} "
                f"(max_redirects={self._config.max_redirects}): {exc}"
            ) from exc
        except httpx.ConnectError as exc:
            raise LeidConnectionError(
                f"Connection error fetching {normalised_url!r}: {exc}"
            ) from exc
        except httpx.HTTPError as exc:
            raise LeidConnectionError(
                f"HTTP transport error fetching {normalised_url!r}: {exc}"
            ) from exc

        self._log.debug(
            "Leið fetch_url: %s -> status=%d, size=%d",
            normalised_url, status_code, size_bytes,
        )

        return {
            "url": normalised_url,
            "status_code": status_code,
            "content_type": content_type,
            "body": body,
            "size_bytes": size_bytes,
        }

    async def extract_text(self, url: str) -> dict[str, Any]:
        """Fetch a URL and extract its plain text content.

        Fetches the URL (same constraints as fetch_url) and strips HTML tags
        to return readable text. For non-HTML responses, returns the raw body.

        Known boundary: JS-rendered pages return near-empty text because httpx
        does not execute JavaScript. This is a documented limit, not a bug.
        playwright/selenium = v0.6.2.1+ for JS pages.

        Args:
            url: URL to fetch and extract text from. Must match allowlist.

        Returns:
            dict with keys:
                url (str): normalised URL fetched
                text (str): extracted plain text content
                title (str | None): page title if HTML and detectable
                source_size_bytes (int): size of original response body in bytes

        Raises:
            UrlNotAllowedError: URL not in allowlist or HTTP rejected.
            LeidTimeoutError: request timed out.
            LeidHttpError: 4xx or 5xx response status.
            LeidConnectionError: network-level error.
            LeidResponseTooLargeError: response body exceeds max_response_bytes.
        """
        # Re-use fetch_url for transport and sandbox validation.
        # LeidResponseTooLargeError propagates unmodified if body exceeds cap.
        fetch_result = await self.fetch_url(url)

        body = fetch_result["body"]
        content_type = fetch_result["content_type"]
        source_size_bytes = fetch_result["size_bytes"]

        # Extract text from HTML if applicable; return raw body otherwise
        if self._is_html_content_type(content_type):
            text, title = _extract_text_from_html(body)
        else:
            # Non-HTML — return the body as-is (already UTF-8 decoded)
            text = body
            title = None

        self._log.debug(
            "Leið extract_text: %s -> %d chars of text extracted",
            fetch_result["url"], len(text),
        )

        return {
            "url": fetch_result["url"],
            "text": text,
            "title": title,
            "source_size_bytes": source_size_bytes,
        }
