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
    - No cookies stored, sent, or accepted (stateless).
    - No JavaScript execution (httpx only; playwright = v0.6.2.1+).
    - Response body is truncated at LeidConfig.max_response_bytes.
    - Redirects followed up to LeidConfig.max_redirects (default 5).
    - Custom User-Agent: LeidConfig.user_agent.

The httpx client is created fresh per-request in the Wave 2 implementation
(no persistent httpx.AsyncClient across calls — simpler lifecycle, no
connection reuse issues). Forge Wave 2 may upgrade to a shared client if
connection reuse becomes important.

Ref: src/heretic/skilningr/senses/leid/INTERFACE.md
     src/heretic/skilningr/sandbox.py (url_matches_allowlist)
     TASK_HERETIC_v0.6.2_MORE_SENSES.md §3 (Leið sandbox invariants)
"""

from __future__ import annotations

import logging
from typing import Any

from heretic.skilningr.config_model import LeidConfig
from heretic.skilningr.sandbox import url_matches_allowlist
from heretic.skilningr.senses.leid.errors import UrlNotAllowedError

logger = logging.getLogger(__name__)


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

    async def fetch_url(self, url: str) -> dict[str, Any]:
        """Fetch the raw content of a URL via HTTP GET.

        Args:
            url: URL to fetch. Must match url_allowlist_patterns.

        Returns:
            dict with keys:
                url (str): normalised URL fetched
                status_code (int): HTTP response status code
                content_type (str): Content-Type header value
                body (str): response body as UTF-8 string (or base64 for binary)
                body_encoding (str): "utf-8" or "base64"
                size_bytes (int): actual bytes in body before encoding
                truncated (bool): True if body was truncated to max_response_bytes

        Raises:
            UrlNotAllowedError: URL not in allowlist or HTTP rejected.
            LeidTimeoutError: request timed out.
            LeidResponseTooLargeError: response exceeds max_response_bytes.
            LeidHttpError: 4xx or 5xx response.
            LeidConnectionError: network-level error.
        """
        raise NotImplementedError(
            "LeidClient.fetch_url: Forge implements this in Wave 2 of v0.6.2."
        )

    async def extract_text(self, url: str) -> dict[str, Any]:
        """Fetch a URL and extract its plain text content.

        Fetches the URL (same constraints as fetch_url) and strips HTML tags
        to return readable text. For non-HTML responses, returns the raw body.

        Args:
            url: URL to fetch and extract text from. Must match allowlist.

        Returns:
            dict with keys:
                url (str): normalised URL fetched
                text (str): extracted plain text content
                title (str | None): page title if HTML and detectable
                size_bytes (int): size of original response body
                truncated (bool): True if content was truncated

        Raises:
            UrlNotAllowedError: URL not in allowlist or HTTP rejected.
            LeidTimeoutError: request timed out.
            LeidResponseTooLargeError: response exceeds max_response_bytes.
            LeidHttpError: 4xx or 5xx response.
            LeidConnectionError: network-level error.
        """
        raise NotImplementedError(
            "LeidClient.extract_text: Forge implements this in Wave 2 of v0.6.2."
        )
