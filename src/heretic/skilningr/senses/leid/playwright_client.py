"""
PlaywrightLeidClient — browser-render sub-faculty for the Leið sense.

This module implements the v0.8.0 *Opið Vef* sub-faculty: a sandboxed,
headless-Chromium browser-render path for the agent's `leid.render_url` tool.

It exists alongside `LeidClient` (httpx GET) and does NOT modify it. The
v0.7.1 streaming-httpx code path is byte-untouched. `LeidSense` dispatches
`leid.fetch_url` and `leid.extract_text` to `LeidClient` and `leid.render_url`
to `PlaywrightLeidClient`.

SANDBOX INVARIANTS (B-1 .. B-10) — DO NOT WEAKEN:

    B-1  _validate_url() runs BEFORE async_playwright().start(). No browser
         process spawns for a rejected URL.
    B-2  LeidPlaywrightUnavailableError is raised at render_url() entry if
         (a) the playwright package cannot be imported, OR (b) chromium
         fails to launch (typically: operator did not run
         `playwright install chromium`). The httpx tools (fetch_url,
         extract_text) on LeidClient continue to dispatch unaffected.
    B-3  Each render_url() call uses browser.new_context() — a fresh,
         isolated context. Cookies and localStorage discarded at
         context.close(). NO state crosses call boundaries.
    B-4  The browser is launched headless=True. No visible window.
    B-5  page.goto(url, wait_until=config.browser_load_state,
         timeout=config.browser_navigation_timeout_seconds * 1000).
         Playwright's TimeoutError → LeidTimeoutError.
    B-6  After navigation: len(html.encode("utf-8")) <= max_response_bytes.
         Exceeded → LeidResponseTooLargeError BEFORE text extraction;
         context+browser+pw closed cleanly during stack unwind.
    B-7  All three resources (pw, browser, context) closed in nested
         `finally` blocks. A failure during navigation cannot leak a
         browser process.
    B-8  User-Agent on every browser request matches config.user_agent
         (passed via browser.new_context(user_agent=...)).
    B-9  allow_http: false rejects http:// URLs at _validate_url() before
         browser launch — same posture as httpx tools.
    B-10 HERETIC injects no JavaScript code into the page in v0.8.0.
         The page's own scripts run during render; that is the only
         script execution. No page.evaluate(...) from agent input.

Memory bound at the cap:
    Unlike fetch_url (streaming aiter_bytes with mid-stream abort), render_url
    materialises the full rendered DOM as a single string via
    `await page.content()` BEFORE the cap is checked. The cap is therefore a
    token-budget bound (preventing the agent from receiving an enormous text
    payload), NOT a memory bound for the browser process. Operators who need
    true streaming abort must use leid.fetch_url instead. See
    docs/cartography/DATA_FLOW.md §4.12.2.2 for the full trade-off discussion.

Lifecycle: launch-per-call (D-5).
    Each render_url() call:
        1. starts its own playwright runtime
        2. launches its own browser
        3. opens its own browser context (fresh cookie jar, fresh localStorage)
        4. opens its own page
        5. tears all four down before returning

    Stateful browsing (persistent page, click, type, query) is deferred to
    v0.8.2 / v0.8.3. v0.8.0 is stateless by design.

Ref: src/heretic/skilningr/senses/leid/INTERFACE.md §10
     docs/cartography/DATA_FLOW.md §4.12.2.2
     docs/vision/OPID_VEF.md
     TASK_HERETIC_v0.8.0_OPID_VEF.md
"""

from __future__ import annotations

import logging
from typing import Any

from heretic.skilningr.config_model import LeidConfig
from heretic.skilningr.sandbox import url_matches_allowlist
from heretic.skilningr.senses.leid.client import _extract_text_from_html
from heretic.skilningr.senses.leid.errors import (
    LeidConnectionError,
    LeidHttpError,
    LeidPlaywrightUnavailableError,
    LeidResponseTooLargeError,
    LeidTimeoutError,
    UrlNotAllowedError,
)

logger = logging.getLogger(__name__)


class PlaywrightLeidClient:
    """Sandboxed headless-Chromium fetch client for the Leið Opið Vef sub-faculty.

    Answers the `leid.render_url` tool only. The httpx tools (`leid.fetch_url`,
    `leid.extract_text`) continue to be answered by `LeidClient`.

    Usage:
        config = heretic_config.skilningr.leid
        client = PlaywrightLeidClient(config)
        result = await client.render_url("https://example-spa.com/dashboard")
    """

    def __init__(
        self,
        config: LeidConfig,
        log: logging.Logger | None = None,
    ) -> None:
        """Initialise the Playwright Leið client.

        Args:
            config: LeidConfig — URL allowlist, user agent, size cap, browser
                    timeout, browser load state.
            log:    Optional logger. Defaults to module logger.

        Note: This constructor does NOT import playwright. Import is deferred
        to render_url() so that hosts without `pip install heretic[browser]`
        can still import this module without ImportError. B-2 only triggers
        on actual call to render_url().
        """
        self._config = config
        self._log = log if log is not None else logging.getLogger(__name__)

    def _validate_url(self, url: str) -> str:
        """Validate that *url* matches the allowlist and return the normalised URL.

        Also enforces the HTTPS-only policy when allow_http is False.
        Identical contract to LeidClient._validate_url. B-1 / B-9 honoured.

        Args:
            url: The candidate URL string from the agent tool call.

        Returns:
            Normalised URL string (scheme lowercase, netloc lowercase).

        Raises:
            UrlNotAllowedError: URL does not match any allowlist pattern.
            UrlNotAllowedError: URL uses HTTP scheme and allow_http is False.
        """
        url_stripped = url.strip()
        # B-9 — HTTPS-only enforcement
        if url_stripped.lower().startswith("http://") and not self._config.allow_http:
            raise UrlNotAllowedError(
                f"HTTP (non-TLS) URL rejected: {url!r}. "
                f"Set skilningr.leid.allow_http: true to permit HTTP fetches. "
                f"HTTPS is strongly recommended."
            )

        allowed, result = url_matches_allowlist(
            url_stripped, self._config.url_allowlist_patterns
        )
        if not allowed:
            self._log.warning("Leið Opið Vef URL allowlist rejection: %s", result)
            raise UrlNotAllowedError(f"URL not permitted: {result}")

        # Log HTTP warning even when allowed
        if url_stripped.lower().startswith("http://"):
            self._log.warning(
                "Leið Opið Vef: rendering HTTP (non-TLS) URL — content is "
                "unencrypted: %s",
                url_stripped,
            )

        return result  # type: ignore[return-value]

    async def render_url(self, url: str) -> dict[str, Any]:
        """Navigate to *url* in headless Chromium and extract rendered text + title.

        See module docstring for full sandbox invariants B-1 .. B-10. Each call
        is fully stateless — a fresh browser context is created and disposed.

        Args:
            url: URL to render. Must match url_allowlist_patterns.

        Returns:
            dict with keys:
                url (str):                 the validated URL passed in
                final_url (str):           page.url after navigation
                                           (may differ from url after redirect)
                text (str):                plain text from rendered DOM
                title (str | None):        <title> of rendered DOM
                source_size_bytes (int):   UTF-8 byte length of the rendered HTML

        Raises:
            UrlNotAllowedError:             URL not in allowlist or HTTP rejected.
            LeidPlaywrightUnavailableError: playwright not installed OR chromium
                                            binary missing.
            LeidTimeoutError:               page.goto() exceeded
                                            browser_navigation_timeout_seconds.
            LeidHttpError:                  navigation returned 4xx or 5xx status.
            LeidConnectionError:            network-level error reached by Playwright.
            LeidResponseTooLargeError:      rendered HTML exceeds max_response_bytes.
        """
        # B-1 — validate URL BEFORE any Playwright operation. A rejected URL
        # NEVER causes a browser process to spawn.
        normalised_url = self._validate_url(url)

        # B-2 — defer the Playwright import to here. Hosts without the
        # [browser] extra installed must still be able to import this module.
        try:
            from playwright.async_api import (
                Error as PlaywrightError,  # type: ignore[import-not-found]
            )
            from playwright.async_api import (
                TimeoutError as PlaywrightTimeoutError,  # type: ignore[import-not-found]
            )
            from playwright.async_api import (
                async_playwright,  # type: ignore[import-not-found]
            )
        except ImportError as exc:
            raise LeidPlaywrightUnavailableError(
                "Playwright is not installed. To enable leid.render_url, run "
                "`pip install heretic[browser]` and then "
                "`playwright install chromium`. The httpx tools "
                "(leid.fetch_url, leid.extract_text) continue to work without "
                f"Playwright. Import error: {exc}"
            ) from exc

        self._log.debug(
            "Leið render_url: %s (timeout=%ds, max_bytes=%d, load_state=%r)",
            normalised_url,
            self._config.browser_navigation_timeout_seconds,
            self._config.max_response_bytes,
            self._config.browser_load_state,
        )

        # B-7 — nested try/finally for full resource cleanup. Even if any
        # stage raises, the runtime / browser / context already opened
        # are torn down in reverse order.
        pw = None
        browser = None
        context = None
        try:
            pw = await async_playwright().start()

            # B-2 (continued) — chromium binary must be available
            try:
                # B-4 — always headless
                browser = await pw.chromium.launch(headless=True)
            except Exception as exc:
                # The most common cause is that the operator has not run
                # `playwright install chromium`. Translate to the same
                # availability error the agent already understands.
                raise LeidPlaywrightUnavailableError(
                    "Chromium browser binary could not be launched. The most "
                    "common cause is that `playwright install chromium` has "
                    "not been run. Without the browser binary, leid.render_url "
                    "cannot operate; the httpx tools are unaffected. "
                    f"Underlying error: {exc}"
                ) from exc

            # B-3 — fresh context per call. No cookies persist between calls.
            # B-8 — user agent passed through.
            context = await browser.new_context(
                user_agent=self._config.user_agent,
            )
            page = await context.new_page()

            # B-5 — bounded navigation timeout
            try:
                response = await page.goto(
                    normalised_url,
                    wait_until=self._config.browser_load_state,
                    timeout=self._config.browser_navigation_timeout_seconds * 1000,
                )
            except PlaywrightTimeoutError as exc:
                raise LeidTimeoutError(
                    f"Browser navigation to {normalised_url!r} timed out after "
                    f"{self._config.browser_navigation_timeout_seconds}s "
                    f"(load_state={self._config.browser_load_state!r}): {exc}"
                ) from exc
            except PlaywrightError as exc:
                # Network-level errors (DNS, TLS, refused, etc.) surface as
                # the generic playwright Error. Translate to the same
                # connection-error shape as the httpx path.
                raise LeidConnectionError(
                    f"Browser navigation to {normalised_url!r} failed at the "
                    f"network layer: {exc}"
                ) from exc

            # Status-code check. response is None for some special navigations
            # (e.g. data: URLs, downloads); treat None as "no HTTP status to check"
            # and continue to the content read.
            if response is not None and response.status >= 400:
                raise LeidHttpError(
                    f"HTTP {response.status} from {normalised_url!r} "
                    f"(rendered via Playwright)."
                )

            # B-6 — pre-cap on rendered HTML BEFORE text extraction
            html = await page.content()
            rendered_size = len(html.encode("utf-8"))
            if rendered_size > self._config.max_response_bytes:
                self._log.warning(
                    "Leið render_url: rendered HTML from %s is %d bytes, "
                    "exceeds max_response_bytes=%d — aborting before text "
                    "extraction",
                    normalised_url,
                    rendered_size,
                    self._config.max_response_bytes,
                )
                raise LeidResponseTooLargeError(
                    f"Rendered HTML from {normalised_url!r} is {rendered_size} "
                    f"bytes, which exceeds max_response_bytes="
                    f"{self._config.max_response_bytes}. The page may be a "
                    f"large SPA. Increase LeidConfig.max_response_bytes or "
                    f"prefer leid.fetch_url for static fetches."
                )

            text, title = _extract_text_from_html(html)
            final_url = page.url

        finally:
            # B-7 — close in reverse order. Each close is wrapped so a
            # failure in one cleanup does not block the others.
            if context is not None:
                try:
                    await context.close()
                except Exception as exc:
                    self._log.warning(
                        "Leið render_url: context.close() raised "
                        "(non-fatal): %s",
                        exc,
                    )
            if browser is not None:
                try:
                    await browser.close()
                except Exception as exc:
                    self._log.warning(
                        "Leið render_url: browser.close() raised "
                        "(non-fatal): %s",
                        exc,
                    )
            if pw is not None:
                try:
                    await pw.stop()
                except Exception as exc:
                    self._log.warning(
                        "Leið render_url: playwright.stop() raised "
                        "(non-fatal): %s",
                        exc,
                    )

        self._log.debug(
            "Leið render_url: %s -> final_url=%s, source_size=%d, "
            "text_len=%d",
            normalised_url,
            final_url,
            rendered_size,
            len(text),
        )

        return {
            "url": normalised_url,
            "final_url": final_url,
            "text": text,
            "title": title,
            "source_size_bytes": rendered_size,
        }
