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

import base64
import logging
import uuid
from typing import Any

from heretic.skilningr.config_model import LeidConfig
from heretic.skilningr.sandbox import url_matches_allowlist
from heretic.skilningr.senses.leid.client import _extract_text_from_html
from heretic.skilningr.senses.leid.errors import (
    LeidClickElementNotFoundError,
    LeidConnectionError,
    LeidHttpError,
    LeidPlaywrightUnavailableError,
    LeidResponseTooLargeError,
    LeidSessionLimitError,
    LeidTimeoutError,
    UrlNotAllowedError,
)
from heretic.skilningr.senses.leid.session_manager import (
    BrowserSessionManager,
    _LeidSession,
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
        # v0.8.2 — lazy session manager for Innan Hurðar tools.
        # Constructed on first session-tool call; remains None for hosts
        # that only use the stateless tools (render_url, screenshot).
        self._session_manager: BrowserSessionManager | None = None

    def _get_or_create_session_manager(self) -> BrowserSessionManager:
        """Lazily construct the BrowserSessionManager on first session-tool call.

        Hosts that use only render_url / screenshot never construct a manager.
        Hosts that use any of the v0.8.2 session tools get a single manager
        bound to the same config.
        """
        if self._session_manager is None:
            self._session_manager = BrowserSessionManager(
                self._config, log=self._log
            )
        return self._session_manager

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

            # B-6 — pre-cap on rendered HTML BEFORE text extraction.
            # M-1 closure (v0.8.2): explicit Page.* exception typing —
            # network-level failures during page.content() now surface as
            # LeidConnectionError, matching httpx's network-error precision.
            try:
                html = await page.content()
            except (PlaywrightTimeoutError, PlaywrightError) as exc:
                raise LeidConnectionError(
                    f"page.content() for {normalised_url!r} failed at the "
                    f"browser level (page may have closed or process "
                    f"disconnected): {exc}"
                ) from exc
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

    async def screenshot(self, url: str) -> dict[str, Any]:
        """Navigate to *url* in headless Chromium and return a base64-PNG screenshot.

        v0.8.1 *Mynd af Vegferð* — second tool on the Opið Vef sub-faculty.
        Same launch-per-call browser lifecycle as ``render_url``; same B-1..B-10
        invariants. One additional invariant — B-11 — governs the image-data
        path: the size cap (``config.max_response_bytes``) applies to the **raw
        PNG bytes BEFORE base64 encoding**, NOT to the base64-expanded length.

        See module docstring for the full sandbox invariant list. Each call is
        fully stateless — a fresh browser context is created and disposed.

        Args:
            url: URL to screenshot. Must match url_allowlist_patterns.

        Returns:
            dict with keys:
                url (str):                 the validated URL passed in
                final_url (str):           page.url after navigation
                                           (may differ from url after redirect)
                image_base64 (str):        ASCII base64 encoding of the raw PNG
                image_format (str):        always "png" at v0.8.1
                size_bytes (int):          length of the raw PNG bytes
                                           (BEFORE base64 expansion — D-18)
                full_page (bool):          echo of config.browser_screenshot_full_page

        Raises:
            UrlNotAllowedError:             URL not in allowlist or HTTP rejected.
            LeidPlaywrightUnavailableError: playwright not installed OR chromium
                                            binary missing.
            LeidTimeoutError:               page.goto() exceeded
                                            browser_navigation_timeout_seconds.
            LeidHttpError:                  navigation returned 4xx or 5xx status.
            LeidConnectionError:            network-level error reached by Playwright.
            LeidResponseTooLargeError:      raw PNG bytes exceed max_response_bytes.
        """
        # B-1 — allowlist + HTTPS-only gate. Reuses the same _validate_url
        # method as render_url. A rejected URL never causes a browser launch.
        normalised_url = self._validate_url(url)

        # B-2 — defer the Playwright import to here.
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
                "Playwright is not installed. To enable leid.screenshot, run "
                "`pip install heretic[browser]` and then "
                "`playwright install chromium`. The httpx tools "
                "(leid.fetch_url, leid.extract_text) continue to work without "
                f"Playwright. Import error: {exc}"
            ) from exc

        full_page = self._config.browser_screenshot_full_page
        self._log.debug(
            "Leið screenshot: %s (timeout=%ds, max_bytes=%d, "
            "load_state=%r, full_page=%s)",
            normalised_url,
            self._config.browser_navigation_timeout_seconds,
            self._config.max_response_bytes,
            self._config.browser_load_state,
            full_page,
        )

        # B-7 — same nested cleanup pattern as render_url. Each resource is
        # closed in a `finally` block; each close itself is wrapped so a
        # failure in one cleanup does not block the others.
        pw = None
        browser = None
        context = None
        try:
            pw = await async_playwright().start()

            try:
                # B-4 — always headless
                browser = await pw.chromium.launch(headless=True)
            except Exception as exc:
                raise LeidPlaywrightUnavailableError(
                    "Chromium browser binary could not be launched. The most "
                    "common cause is that `playwright install chromium` has "
                    "not been run. Without the browser binary, leid.screenshot "
                    "cannot operate; the httpx tools are unaffected. "
                    f"Underlying error: {exc}"
                ) from exc

            # B-3 — fresh context per call. B-8 — user agent passed through.
            context = await browser.new_context(
                user_agent=self._config.user_agent,
            )
            page = await context.new_page()

            # B-5 — bounded navigation timeout. Identical mapping to render_url.
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
                raise LeidConnectionError(
                    f"Browser navigation to {normalised_url!r} failed at the "
                    f"network layer: {exc}"
                ) from exc

            # Same status-code check as render_url — None response (e.g. data:)
            # is allowed through to the screenshot step.
            if response is not None and response.status >= 400:
                raise LeidHttpError(
                    f"HTTP {response.status} from {normalised_url!r} "
                    f"(rendered via Playwright)."
                )

            # Stage 5 — capture the screenshot.
            # M-1 closure (v0.8.2): explicit Page.* exception typing —
            # network/page-level failures during page.screenshot() now
            # surface as LeidConnectionError, matching httpx's precision.
            try:
                png_bytes = await page.screenshot(
                    full_page=full_page,
                    type="png",
                )
            except (PlaywrightTimeoutError, PlaywrightError) as exc:
                raise LeidConnectionError(
                    f"page.screenshot() for {normalised_url!r} failed at the "
                    f"browser level (page may have closed or process "
                    f"disconnected): {exc}"
                ) from exc

            # B-11 — pre-cap on raw PNG byte size, BEFORE base64 encoding.
            # The base64 expansion (~33%) is avoided when the cap fires.
            png_size = len(png_bytes)
            if png_size > self._config.max_response_bytes:
                self._log.warning(
                    "Leið screenshot: PNG from %s is %d bytes, exceeds "
                    "max_response_bytes=%d — aborting before base64 encoding",
                    normalised_url,
                    png_size,
                    self._config.max_response_bytes,
                )
                raise LeidResponseTooLargeError(
                    f"PNG screenshot of {normalised_url!r} is {png_size} "
                    f"bytes, which exceeds max_response_bytes="
                    f"{self._config.max_response_bytes}. The page may be a "
                    f"large SPA. Increase LeidConfig.max_response_bytes, or "
                    f"set browser_screenshot_full_page: false to capture only "
                    f"the viewport instead."
                )

            # Stage 7 — base64 encode (D-17). ASCII-decode is safe because
            # base64 output is by definition ASCII-only.
            image_base64 = base64.b64encode(png_bytes).decode("ascii")
            final_url = page.url

        finally:
            # B-7 — close in reverse order, each wrapped defensively.
            if context is not None:
                try:
                    await context.close()
                except Exception as exc:
                    self._log.warning(
                        "Leið screenshot: context.close() raised "
                        "(non-fatal): %s",
                        exc,
                    )
            if browser is not None:
                try:
                    await browser.close()
                except Exception as exc:
                    self._log.warning(
                        "Leið screenshot: browser.close() raised "
                        "(non-fatal): %s",
                        exc,
                    )
            if pw is not None:
                try:
                    await pw.stop()
                except Exception as exc:
                    self._log.warning(
                        "Leið screenshot: playwright.stop() raised "
                        "(non-fatal): %s",
                        exc,
                    )

        self._log.debug(
            "Leið screenshot: %s -> final_url=%s, png_size=%d, "
            "base64_size=%d, full_page=%s",
            normalised_url,
            final_url,
            png_size,
            len(image_base64),
            full_page,
        )

        return {
            "url": normalised_url,
            "final_url": final_url,
            "image_base64": image_base64,
            "image_format": "png",
            "size_bytes": png_size,
            "full_page": full_page,
        }

    # ------------------------------------------------------------------
    # v0.8.2 Innan Hurðar — stateful session methods
    # ------------------------------------------------------------------

    async def open_session(self, url: str) -> dict[str, Any]:
        """Open a stateful browser session at *url* and return its session_id.

        v0.8.2 *Innan Hurðar* — stateful sub-disposition. Unlike render_url and
        screenshot (launch-per-call), open_session keeps the (pw, browser,
        context, page) quartet alive after returning, registered with the
        BrowserSessionManager under a UUID4-derived session_id. The agent
        uses the session_id for subsequent session_status/click/close_session
        calls.

        Lifecycle (D-36): launch-per-SESSION. The session lives until either:
          - leid.close_session(session_id) is called, OR
          - browser_session_idle_timeout_seconds passes with no activity, OR
          - browser_session_max_lifetime_seconds passes (hard ceiling).

        Args:
            url: URL to navigate to in the new session. Must match
                 url_allowlist_patterns.

        Returns:
            dict with keys:
                session_id (str):  prefixed UUID4 hex (e.g. "leid-abc...")
                final_url (str):   page.url after the navigation completes
                title (str):       page <title> after navigation

        Raises:
            UrlNotAllowedError:             URL not in allowlist or HTTP rejected.
            LeidPlaywrightUnavailableError: playwright not installed OR chromium
                                            binary missing.
            LeidSessionLimitError:          concurrent-sessions cap reached.
            LeidTimeoutError:               page.goto() exceeded
                                            browser_navigation_timeout_seconds.
            LeidHttpError:                  navigation returned 4xx or 5xx status.
            LeidConnectionError:            network-level error during navigation.
        """
        # B-12 — validate URL FIRST. No browser launches for a rejected URL.
        normalised_url = self._validate_url(url)

        # B-15 — lazy eviction of expired sessions before any new work.
        manager = self._get_or_create_session_manager()
        await manager.evict_expired_sessions()

        # B-13 — explicit refusal at cap. No silent eviction.
        await manager.check_capacity()

        # B-2 — defer playwright import; mirrors render_url / screenshot.
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
                "Playwright is not installed. To enable leid.open_session, run "
                "`pip install heretic[browser]` and then "
                "`playwright install chromium`. The httpx tools "
                "(leid.fetch_url, leid.extract_text) continue to work without "
                f"Playwright. Import error: {exc}"
            ) from exc

        self._log.debug(
            "Leið open_session: %s (timeout=%ds, load_state=%r, max_concurrent=%d)",
            normalised_url,
            self._config.browser_navigation_timeout_seconds,
            self._config.browser_load_state,
            self._config.browser_max_concurrent_sessions,
        )

        # Launch the (pw, browser, context, page) quartet. If ANY stage
        # fails BEFORE registration, we must clean up everything launched
        # so far (B-7-style) because the session is NOT yet known to the
        # manager — eviction won't catch it.
        #
        # was_registered tracks whether ownership has transferred to the
        # manager. Set to True only after register_session succeeds; if any
        # later code raises (it doesn't, but defensively), the cleanup
        # branch knows to leave the resources alone (the manager owns them).
        # (Auditor NOTABLE-1, Wave 6 closure: replaces the previous
        # introspection heuristic that walked _sessions.values() to decide.)
        pw = None
        browser = None
        context = None
        was_registered = False
        try:
            pw = await async_playwright().start()
            try:
                browser = await pw.chromium.launch(headless=True)  # B-4
            except Exception as exc:
                raise LeidPlaywrightUnavailableError(
                    "Chromium browser binary could not be launched. The most "
                    "common cause is that `playwright install chromium` has "
                    "not been run. Without the browser binary, leid.open_session "
                    "cannot operate; the httpx tools are unaffected. "
                    f"Underlying error: {exc}"
                ) from exc

            # Each session gets its own context (B-14, also strengthened B-3).
            context = await browser.new_context(
                user_agent=self._config.user_agent,
            )
            page = await context.new_page()

            try:
                response = await page.goto(
                    normalised_url,
                    wait_until=self._config.browser_load_state,
                    timeout=self._config.browser_navigation_timeout_seconds * 1000,
                )
            except PlaywrightTimeoutError as exc:
                raise LeidTimeoutError(
                    f"open_session navigation to {normalised_url!r} timed out "
                    f"after {self._config.browser_navigation_timeout_seconds}s "
                    f"(load_state={self._config.browser_load_state!r}): {exc}"
                ) from exc
            except PlaywrightError as exc:
                raise LeidConnectionError(
                    f"open_session navigation to {normalised_url!r} failed "
                    f"at the network layer: {exc}"
                ) from exc

            if response is not None and response.status >= 400:
                raise LeidHttpError(
                    f"HTTP {response.status} from {normalised_url!r} "
                    f"during open_session navigation."
                )

            # Read the title once; defensive against title-read failures.
            try:
                title = await page.title()
            except Exception:
                title = ""

            session_id = f"leid-{uuid.uuid4().hex}"
            session = _LeidSession(
                session_id=session_id,
                pw=pw,
                browser=browser,
                context=context,
                page=page,
            )

            # Register with the manager. Re-checks the cap under-lock; on
            # race-loss the registration raises LeidSessionLimitError and
            # the outer cleanup branch (was_registered=False) will tear
            # down the quartet.
            await manager.register_session(session)
            was_registered = True

            final_url = page.url

        except Exception:
            # Cleanup ONLY when the session was NOT registered. After
            # registration, ownership transferred to the manager — the
            # manager handles cleanup at close / eviction time.
            if not was_registered:
                if context is not None:
                    try:
                        await context.close()
                    except Exception:
                        pass
                if browser is not None:
                    try:
                        await browser.close()
                    except Exception:
                        pass
                if pw is not None:
                    try:
                        await pw.stop()
                    except Exception:
                        pass
            raise

        self._log.debug(
            "Leið open_session: %s -> session_id=%s, final_url=%s",
            normalised_url, session_id, final_url,
        )

        return {
            "session_id": session_id,
            "final_url": final_url,
            "title": title,
        }

    async def session_status(self, session_id: str) -> dict[str, Any]:
        """Non-mutating health/identity check on an open session. (B-16, B-17)

        Returns the session's current URL, title, lifetime metadata, and
        derived age/idle seconds. Counts as activity (resets idle timer).

        Args:
            session_id: A session_id returned by a prior open_session call.

        Returns:
            dict with keys: state, url, title, opened_at, last_activity_at,
                            age_seconds, idle_seconds.

        Raises:
            LeidSessionExpiredError: session_id unknown or evicted.
            LeidConnectionError:     page.title() raised at browser layer.
        """
        manager = self._get_or_create_session_manager()
        await manager.evict_expired_sessions()  # B-15
        session = await manager.get_session(session_id)  # B-16

        # B-2 — defer playwright import for the exception types used below.
        try:
            from playwright.async_api import (
                Error as PlaywrightError,  # type: ignore[import-not-found]
            )
            from playwright.async_api import (
                TimeoutError as PlaywrightTimeoutError,  # type: ignore[import-not-found]
            )
        except ImportError as exc:
            # Should never happen — if we have an active session we must have
            # imported playwright already to launch it. Defensive.
            raise LeidPlaywrightUnavailableError(
                f"Playwright disappeared between open_session and "
                f"session_status: {exc}"
            ) from exc

        try:
            url = session.page.url
            title = await session.page.title()
        except (PlaywrightTimeoutError, PlaywrightError) as exc:
            raise LeidConnectionError(
                f"session_status({session_id!r}) failed at the browser level: "
                f"{exc}"
            ) from exc

        import time as _time
        now = _time.monotonic()
        age = session.age_seconds(now)
        idle = session.idle_seconds(now)

        # B-17 — status counts as activity (resets idle).
        session.mark_activity()

        return {
            "state": "alive",
            "url": url,
            "title": title,
            "opened_at": session.created_at,
            "last_activity_at": session.last_activity_at,
            "age_seconds": age,
            "idle_seconds": idle,
        }

    async def click(self, session_id: str, selector: str) -> dict[str, Any]:
        """Click the first element matching *selector* in the open session. (D-41)

        v0.8.2's first interactive tool. The click may trigger navigation or
        any other in-page behaviour the page's own scripts implement.
        HERETIC injects no JavaScript (B-10 inherited).

        Args:
            session_id: A session_id returned by a prior open_session call.
            selector:   CSS selector. The FIRST matching element is clicked.

        Returns:
            dict with keys: selector, clicked, current_url, current_title.

        Raises:
            LeidSessionExpiredError:        session_id unknown or evicted.
            LeidClickElementNotFoundError:  selector matched nothing within
                                            browser_click_timeout_seconds.
            LeidConnectionError:            other Playwright error.
        """
        manager = self._get_or_create_session_manager()
        await manager.evict_expired_sessions()  # B-15
        session = await manager.get_session(session_id)  # B-16

        try:
            from playwright.async_api import (
                Error as PlaywrightError,  # type: ignore[import-not-found]
            )
            from playwright.async_api import (
                TimeoutError as PlaywrightTimeoutError,  # type: ignore[import-not-found]
            )
        except ImportError as exc:
            raise LeidPlaywrightUnavailableError(
                f"Playwright disappeared between open_session and click: {exc}"
            ) from exc

        click_timeout_ms = self._config.browser_click_timeout_seconds * 1000

        # D-41: locator.first.click for deterministic first-match behaviour.
        # D-43: TimeoutError → LeidClickElementNotFoundError (selector wrong);
        #       other PlaywrightError → LeidConnectionError (network/page issue).
        locator = session.page.locator(selector).first
        try:
            await locator.click(timeout=click_timeout_ms)
        except PlaywrightTimeoutError as exc:
            raise LeidClickElementNotFoundError(
                f"Selector {selector!r} matched no actionable element in "
                f"session {session_id!r} within "
                f"{self._config.browser_click_timeout_seconds}s. Refine the "
                f"selector and retry. Underlying: {exc}"
            ) from exc
        except PlaywrightError as exc:
            raise LeidConnectionError(
                f"click({selector!r}) on session {session_id!r} failed at the "
                f"browser level: {exc}"
            ) from exc

        # B-17 — successful click counts as activity.
        session.mark_activity()

        # D-44 — read post-click URL and title (may have changed due to nav).
        # D-49 — title-read failure is non-fatal.
        current_url = session.page.url
        try:
            current_title = await session.page.title()
        except Exception:
            current_title = None

        self._log.debug(
            "Leið click: session=%s selector=%s -> url=%s",
            session_id, selector, current_url,
        )

        return {
            "selector": selector,
            "clicked": True,
            "current_url": current_url,
            "current_title": current_title,
        }

    async def close_session(self, session_id: str) -> dict[str, Any]:
        """Close the session and release all browser resources. Idempotent. (B-18)

        Returns ``{closed: true}`` for an active session that was closed,
        ``{closed: false}`` for an unknown / already-closed / evicted
        session_id. Does NOT raise for unknown ids — agents can safely
        re-issue close after a failed earlier attempt.

        Args:
            session_id: The session_id to close.

        Returns:
            dict with keys: session_id, closed (bool).
        """
        manager = self._get_or_create_session_manager()
        # No eviction sweep here — close_session is the only path that
        # SHOULD always succeed regardless of session state. Eviction would
        # just be redundant work.
        was_closed = await manager.close_session(session_id)
        return {
            "session_id": session_id,
            "closed": was_closed,
        }
