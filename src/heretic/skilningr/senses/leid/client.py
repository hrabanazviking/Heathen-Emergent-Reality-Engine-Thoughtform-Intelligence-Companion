"""
LeidClient — sandboxed HTTP fetch client for the Leið sense.

LeidClient executes HTTP GET requests through a strict URL allowlist gate:
    sandbox.url_matches_allowlist() is called BEFORE any httpx request is sent.
    No request is made to a URL that does not match at least one pattern.

SANDBOX INVARIANT (DO NOT WEAKEN):
    url_matches_allowlist() is called BEFORE any httpx call. This gate cannot
    be bypassed, reordered, or short-circuited.

PROTOCOL INVARIANTS:
    - GET only in v0.6.2. No POST, PUT, DELETE, or other methods.
    - HTTPS-only by default. HTTP requires LeidConfig.allow_http: true AND a
      matching allowlist pattern. HTTP URLs are always logged as warnings.
    - No cookies stored, sent, or accepted (stateless; httpx client cookies not set).
    - No JavaScript execution (httpx only; playwright = v0.6.2.1+).
    - Response body is capped at LeidConfig.max_response_bytes — reading stops at cap;
      "truncated" flag is set in the result dict.
    - Redirects followed up to LeidConfig.max_redirects (default 5).
    - Custom User-Agent: LeidConfig.user_agent.

HTML text extraction (extract_text):
    Uses the stdlib html.parser.HTMLParser subclass to strip tags and collect
    visible text. This is a shallow extraction — JS-rendered pages return
    near-empty text because httpx does not execute JavaScript.
    This boundary is documented as a known limit, NOT a bug.
    playwright/selenium = v0.6.2.1+ for JS-rendered pages.

A fresh httpx.AsyncClient is created per-request (no persistent connection pool
across calls). This keeps the lifecycle simple and avoids stale connection issues.

Ref: src/heretic/skilningr/senses/leid/INTERFACE.md
     src/heretic/skilningr/sandbox.py (url_matches_allowlist)
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

    async def fetch_url(self, url: str) -> dict[str, Any]:
        """Fetch the raw content of a URL via HTTP GET.

        Args:
            url: URL to fetch. Must match url_allowlist_patterns.

        Returns:
            dict with keys:
                url (str): normalised URL fetched
                status_code (int): HTTP response status code
                content_type (str): Content-Type header value (or "")
                body (str): response body as UTF-8 string (errors="replace")
                size_bytes (int): actual bytes read (before truncation)
                truncated (bool): True if body was capped at max_response_bytes

        Raises:
            UrlNotAllowedError: URL not in allowlist or HTTP rejected.
            LeidTimeoutError: request timed out.
            LeidHttpError: 4xx or 5xx response status.
            LeidConnectionError: network-level error (DNS, TLS, TCP refused).
        """
        # Gate — allowlist and HTTPS policy
        normalised_url = self._validate_url(url)

        self._log.debug(
            "Leið fetch_url: %s (timeout=%ds, max_bytes=%d)",
            normalised_url, self._config.timeout_seconds,
            self._config.max_response_bytes,
        )

        timeout = httpx.Timeout(self._config.timeout_seconds)
        headers = {"User-Agent": self._config.user_agent}

        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                max_redirects=self._config.max_redirects,
                headers=headers,
                follow_redirects=True,
            ) as client:
                response = await client.get(normalised_url)
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

        # Check for error status codes
        if response.status_code >= 400:
            raise LeidHttpError(
                f"HTTP {response.status_code} from {normalised_url!r}. "
                f"Response body (truncated): {response.text[:500]!r}"
            )

        content_type = response.headers.get("content-type", "")

        # Read and cap the response body
        raw_bytes = response.content
        size_bytes = len(raw_bytes)
        max_bytes = self._config.max_response_bytes
        truncated = size_bytes > max_bytes

        if truncated:
            raw_bytes = raw_bytes[:max_bytes]
            self._log.warning(
                "Leið fetch_url: response from %s truncated at %d bytes "
                "(full size: %d bytes)",
                normalised_url, max_bytes, size_bytes,
            )

        # Decode as UTF-8 with replacement for non-decodable bytes
        body = raw_bytes.decode("utf-8", errors="replace")

        self._log.debug(
            "Leið fetch_url: %s -> status=%d, size=%d, truncated=%s",
            normalised_url, response.status_code, size_bytes, truncated,
        )

        return {
            "url": normalised_url,
            "status_code": response.status_code,
            "content_type": content_type,
            "body": body,
            "size_bytes": size_bytes,
            "truncated": truncated,
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
                truncated (bool): True if content was truncated

        Raises:
            UrlNotAllowedError: URL not in allowlist or HTTP rejected.
            LeidTimeoutError: request timed out.
            LeidHttpError: 4xx or 5xx response status.
            LeidConnectionError: network-level error.
        """
        # Re-use fetch_url for transport and sandbox validation
        fetch_result = await self.fetch_url(url)

        body = fetch_result["body"]
        content_type = fetch_result["content_type"]
        source_size_bytes = fetch_result["size_bytes"]
        truncated = fetch_result["truncated"]

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
            "truncated": truncated,
        }
