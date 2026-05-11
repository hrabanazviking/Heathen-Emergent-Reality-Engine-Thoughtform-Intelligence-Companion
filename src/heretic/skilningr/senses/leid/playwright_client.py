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
    LeidTypeElementNotFoundError,
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

    def _check_final_url_allowed(self, url: str, *, input_url: str = "") -> None:
        """Re-check *url* against the allowlist + HTTPS-only policy AFTER navigation.

        v0.8.10 — closes the deferred sandbox gap (B-28). Used by every
        navigation-completing call site to verify that ``page.url``
        AFTER navigation is still in the operator's allowlist. The body
        may have been redirected (server-side 3xx, JavaScript-driven
        client-side, etc.) to a non-allowlisted URL during the
        navigation; the operator's allowlist is unconditional and
        applies post-navigation as well as pre-navigation.

        Same logic as ``_validate_url`` but tailored for the post-
        navigation case: returns nothing (the URL has already been
        normalised by Playwright); raises with a message that names
        BOTH the input URL (what the agent asked for) and the final
        URL (where the page actually landed).

        Args:
            url:        The final URL to check (typically session.page.url
                        or the post-navigation page.url).
            input_url:  Optional. The URL the agent originally asked for,
                        used in the error message. If omitted, only the
                        final URL is named.

        Raises:
            UrlNotAllowedError: final URL not in allowlist OR uses HTTP
                                scheme when allow_http is False.
        """
        url_stripped = url.strip()
        # HTTPS-only enforcement (mirrors _validate_url's gate)
        if url_stripped.lower().startswith("http://") and not self._config.allow_http:
            raise UrlNotAllowedError(
                f"Navigation to {input_url!r} resulted in HTTP (non-TLS) URL "
                f"{url_stripped!r}. Set skilningr.leid.allow_http: true to "
                f"permit HTTP fetches. HTTPS is strongly recommended."
            )

        allowed, _result = url_matches_allowlist(
            url_stripped, self._config.url_allowlist_patterns
        )
        if not allowed:
            self._log.warning(
                "Leið final-URL allowlist rejection: input=%s final=%s",
                input_url, url_stripped,
            )
            if input_url:
                raise UrlNotAllowedError(
                    f"Navigation to {input_url!r} resulted in {url_stripped!r}, "
                    f"which is not in url_allowlist_patterns."
                )
            else:
                raise UrlNotAllowedError(
                    f"Final URL {url_stripped!r} is not in url_allowlist_patterns."
                )

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
            # B-27 (v0.8.9) — operator-controlled viewport propagated.
            context = await browser.new_context(
                user_agent=self._config.user_agent,
                viewport={
                    "width": self._config.browser_viewport_width,
                    "height": self._config.browser_viewport_height,
                },
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

            # B-28 (v0.8.10) — final-URL allowlist re-check. The page may
            # have redirected during navigation; the operator's allowlist
            # applies post-navigation as well as pre-navigation.
            self._check_final_url_allowed(page.url, input_url=normalised_url)

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
            # B-27 (v0.8.9) — operator-controlled viewport propagated.
            context = await browser.new_context(
                user_agent=self._config.user_agent,
                viewport={
                    "width": self._config.browser_viewport_width,
                    "height": self._config.browser_viewport_height,
                },
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

            # B-28 (v0.8.10) — final-URL allowlist re-check.
            self._check_final_url_allowed(page.url, input_url=normalised_url)

            # Stage 5 — capture the screenshot.
            # M-1 closure (v0.8.2): explicit Page.* exception typing —
            # network/page-level failures during page.screenshot() now
            # surface as LeidConnectionError, matching httpx's precision.
            # B-29 (v0.8.11): operator-controlled format + quality.
            screenshot_kwargs: dict[str, Any] = {
                "full_page": full_page,
                "type": self._config.browser_screenshot_format,
            }
            if self._config.browser_screenshot_format != "png":
                screenshot_kwargs["quality"] = (
                    self._config.browser_screenshot_jpeg_quality
                )
            try:
                png_bytes = await page.screenshot(**screenshot_kwargs)
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
            # B-29 (v0.8.11): reflect actual format used (was hardcoded "png")
            "image_format": self._config.browser_screenshot_format,
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
            # B-27 (v0.8.9) — operator-controlled viewport propagated.
            context = await browser.new_context(
                user_agent=self._config.user_agent,
                viewport={
                    "width": self._config.browser_viewport_width,
                    "height": self._config.browser_viewport_height,
                },
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

            # B-28 (v0.8.10) — final-URL allowlist re-check. Session is
            # NOT yet registered (was_registered is still False), so the
            # outer cleanup branch tears down the launched browser quartet.
            self._check_final_url_allowed(page.url, input_url=normalised_url)

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

    async def type(
        self, session_id: str, selector: str, text: str
    ) -> dict[str, Any]:
        """Fill the first element matching *selector* with *text*. (D-53, B-19)

        v0.8.2.1 — unnamed extension of Innan Hurðar; the second half of
        the interactive gesture begun with click. Uses Playwright's
        ``locator.fill`` primitive (not ``type``, which is keystroke-by-
        keystroke): waits for actionability, focuses the element, clears
        any existing value, sets the new value, and dispatches an
        ``input`` event. This is what agents almost always want for
        "set this field's value." HERETIC injects no JavaScript — the
        input event is dispatched by Playwright's fill primitive itself.

        Args:
            session_id: A session_id returned by a prior open_session call.
            selector:   CSS selector. The FIRST matching element is filled.
            text:       The text to set as the element's value. Empty string
                        is allowed (clears the field).

        Returns:
            dict with keys: selector, typed, current_url, current_title.

        Raises:
            LeidSessionExpiredError:        session_id unknown or evicted.
            LeidTypeElementNotFoundError:   selector matched nothing within
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
                f"Playwright disappeared between open_session and type: {exc}"
            ) from exc

        # D-54: reuse the click timeout config field — both are fast
        # interactive actions sharing the same operator-controlled bound.
        fill_timeout_ms = self._config.browser_click_timeout_seconds * 1000

        # D-53: locator.first.fill — clears + focuses + sets + input event.
        # D-55: TimeoutError → LeidTypeElementNotFoundError (selector wrong);
        #       other PlaywrightError → LeidConnectionError.
        locator = session.page.locator(selector).first
        try:
            await locator.fill(text, timeout=fill_timeout_ms)
        except PlaywrightTimeoutError as exc:
            raise LeidTypeElementNotFoundError(
                f"Selector {selector!r} matched no actionable input element "
                f"in session {session_id!r} within "
                f"{self._config.browser_click_timeout_seconds}s. Refine the "
                f"selector and retry. Underlying: {exc}"
            ) from exc
        except PlaywrightError as exc:
            raise LeidConnectionError(
                f"type({selector!r}) on session {session_id!r} failed at the "
                f"browser level: {exc}"
            ) from exc

        # B-17 / B-19 — successful type counts as activity.
        session.mark_activity()

        # D-57 — read post-fill URL and title (mirrors click D-44/D-49).
        current_url = session.page.url
        try:
            current_title = await session.page.title()
        except Exception:
            current_title = None

        self._log.debug(
            "Leið type: session=%s selector=%s text_len=%d -> url=%s",
            session_id, selector, len(text), current_url,
        )

        return {
            "selector": selector,
            "typed": True,
            "current_url": current_url,
            "current_title": current_title,
        }

    async def navigate(self, session_id: str, url: str) -> dict[str, Any]:
        """Navigate an open session to a new URL. (B-20, D-60..D-66)

        v0.8.2.2 — unnamed extension of Innan Hurðar; the body walks to a
        new room without leaving the building. The session keeps its
        identity, cookies, and localStorage; only the page URL changes.

        Order matters: ``_validate_url`` runs FIRST (B-12 — gate before
        any browser operation), THEN session lookup (B-16). An invalid URL
        fails loudly even if the session is also gone — the operator's
        allowlist gate is unconditional.

        On navigation failure the session stays open at whatever URL it
        had before the failed goto — the agent can retry or try a
        different navigate. The session is NOT closed on failure.

        Args:
            session_id: A session_id returned by a prior open_session call.
            url:        The new URL to navigate to. Must match
                        url_allowlist_patterns.

        Returns:
            dict with keys: session_id (unchanged, D-62), previous_url
            (D-64 — captured before goto), final_url (page.url after
            goto — may differ from the input on client-side redirect),
            title (page.title() or None on read failure).

        Raises:
            UrlNotAllowedError:        URL not in allowlist or HTTP rejected.
            LeidSessionExpiredError:   session_id unknown or evicted.
            LeidTimeoutError:          page.goto exceeded timeout.
            LeidHttpError:             navigation returned 4xx or 5xx status.
            LeidConnectionError:       network-level error during navigation.
        """
        # B-12 / B-20 — URL validation FIRST, BEFORE session resolution.
        # The operator's allowlist gate is unconditional; an invalid URL
        # must fail loudly regardless of session_id state.
        normalised_url = self._validate_url(url)

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
                f"Playwright disappeared between open_session and navigate: {exc}"
            ) from exc

        # D-64 — capture previous URL BEFORE goto.
        previous_url = session.page.url

        # D-65 — reuses navigation timeout config (same as open_session).
        navigation_timeout_ms = (
            self._config.browser_navigation_timeout_seconds * 1000
        )

        try:
            response = await session.page.goto(
                normalised_url,
                wait_until=self._config.browser_load_state,
                timeout=navigation_timeout_ms,
            )
        except PlaywrightTimeoutError as exc:
            # B-5 inherited — session NOT closed; agent can retry.
            raise LeidTimeoutError(
                f"navigate({normalised_url!r}) on session {session_id!r} "
                f"timed out after "
                f"{self._config.browser_navigation_timeout_seconds}s "
                f"(load_state={self._config.browser_load_state!r}): {exc}"
            ) from exc
        except PlaywrightError as exc:
            raise LeidConnectionError(
                f"navigate({normalised_url!r}) on session {session_id!r} "
                f"failed at the network layer: {exc}"
            ) from exc

        # Status check — same as open_session.
        if response is not None and response.status >= 400:
            raise LeidHttpError(
                f"HTTP {response.status} from {normalised_url!r} "
                f"during navigate on session {session_id!r}."
            )

        # B-28 (v0.8.10) — final-URL allowlist re-check. The session
        # has been compromised if the page landed on a non-allowlisted
        # URL; the only safe response is to terminate it (D-139).
        try:
            self._check_final_url_allowed(
                session.page.url, input_url=normalised_url
            )
        except UrlNotAllowedError:
            bad_url = session.page.url
            await manager.close_session(session_id)
            raise UrlNotAllowedError(
                f"Navigation to {normalised_url!r} on session "
                f"{session_id!r} resulted in {bad_url!r}, which is not "
                f"in url_allowlist_patterns. The session has been closed."
            )

        # B-17 / B-20 — successful navigation counts as activity.
        session.mark_activity()

        # D-49-style defensive title read.
        final_url = session.page.url
        try:
            title = await session.page.title()
        except Exception:
            title = None

        self._log.debug(
            "Leið navigate: session=%s prev=%s -> final=%s",
            session_id, previous_url, final_url,
        )

        return {
            "session_id": session_id,  # D-62 unchanged
            "previous_url": previous_url,  # D-64
            "final_url": final_url,
            "title": title,
        }

    async def query(
        self, session_id: str, selector: str, attribute: str = ""
    ) -> dict[str, Any]:
        """Read text or attribute of first element matching *selector*. (B-21, D-69..D-79)

        v0.8.3 — sixth unnamed extension within Innan Hurðar; the body's
        first eye inside the door (read-only).

        DELIBERATE divergence from click/type (D-72): a selector matching
        no elements is NOT a failure. Returns ``{found: False, count: 0,
        value: None}``. Read tools must support "looking to see if X
        exists" without forcing the agent to wrap the success case in
        try/except.

        Args:
            session_id: A session_id returned by a prior open_session call.
            selector:   CSS selector. Only the first match's value is
                        returned, but ``count`` reports total matches.
            attribute:  Optional. If empty (default), returns the element's
                        text content. If non-empty, returns the value of
                        that HTML attribute (None if attribute absent).

        Returns:
            dict with keys: session_id, selector, attribute, found, value, count.

        Raises:
            LeidSessionExpiredError:  session_id unknown or evicted.
            LeidConnectionError:      browser-level failure (page closed,
                                      process disconnect, etc.).
            (NO LeidQueryElementNotFoundError class — D-79.)
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
                f"Playwright disappeared between open_session and query: {exc}"
            ) from exc

        timeout_ms = self._config.browser_click_timeout_seconds * 1000  # D-75

        # Stage 4 — locator + count (always — gives us the cheap path for "no match")
        locator = session.page.locator(selector)
        try:
            count = await locator.count()
        except PlaywrightError as exc:
            raise LeidConnectionError(
                f"query({selector!r}) on session {session_id!r}: locator.count() "
                f"failed at the browser level: {exc}"
            ) from exc

        # Stage 5 — not-found early return (D-72)
        if count == 0:
            session.mark_activity()  # B-17 (still counts as activity)
            self._log.debug(
                "Leið query: session=%s selector=%r -> not found",
                session_id, selector,
            )
            return {
                "session_id": session_id,
                "selector": selector,
                "attribute": attribute,
                "found": False,
                "value": None,
                "count": 0,
            }

        # Stage 6 — extract from first match (D-69)
        first = locator.first
        try:
            if attribute == "":  # D-70 — default to text content
                value = await first.text_content(timeout=timeout_ms)
            else:  # D-71 — specific attribute
                value = await first.get_attribute(attribute, timeout=timeout_ms)
        except PlaywrightTimeoutError as exc:
            raise LeidConnectionError(
                f"query({selector!r}, attribute={attribute!r}) on session "
                f"{session_id!r} timed out during extraction after "
                f"{self._config.browser_click_timeout_seconds}s: {exc}"
            ) from exc
        except PlaywrightError as exc:
            raise LeidConnectionError(
                f"query({selector!r}, attribute={attribute!r}) on session "
                f"{session_id!r} failed at the browser level: {exc}"
            ) from exc

        # B-17 / B-21 — successful query counts as activity.
        session.mark_activity()

        self._log.debug(
            "Leið query: session=%s selector=%r attribute=%r -> count=%d, "
            "value_len=%s",
            session_id, selector, attribute, count,
            len(value) if isinstance(value, str) else "null",
        )

        return {
            "session_id": session_id,
            "selector": selector,
            "attribute": attribute,
            "found": True,
            "value": value,  # str OR None (when text_content / get_attribute returned None)
            "count": count,
        }

    async def press(self, session_id: str, key: str) -> dict[str, Any]:
        """Send a keyboard key to the open session's page. (B-22, D-80..D-87)

        v0.8.4 — seventh unnamed extension within Innan Hurðar. The body's
        keyboard finger. Page-level: ``page.keyboard.press(key)`` dispatches
        to whatever element currently has focus (typically established by a
        prior click or type).

        Playwright's key syntax is supported (D-81): single keys (``"Enter"``,
        ``"Tab"``, ``"Escape"``, ``"ArrowDown"``, ``"a"``, ``"F5"``) and
        modifier combinations (``"Control+A"``, ``"Shift+Tab"``,
        ``"Meta+S"``). HERETIC does not validate the key string — Playwright
        dispatches as best it can; unrecognized keys produce no event but
        do NOT raise (D-84).

        Args:
            session_id: A session_id returned by a prior open_session call.
            key:        The key or modifier+key combination to press, in
                        Playwright's syntax.

        Returns:
            dict with keys: session_id, key, pressed, current_url,
            current_title. ``current_url`` may differ from the pre-press URL
            if the press triggered navigation (e.g., Enter submitted a form).

        Raises:
            LeidSessionExpiredError:  session_id unknown or evicted.
            LeidConnectionError:      browser-level failure (page closed,
                                      process disconnect, etc.).
        """
        manager = self._get_or_create_session_manager()
        await manager.evict_expired_sessions()  # B-15
        session = await manager.get_session(session_id)  # B-16

        try:
            from playwright.async_api import (
                Error as PlaywrightError,  # type: ignore[import-not-found]
            )
        except ImportError as exc:
            raise LeidPlaywrightUnavailableError(
                f"Playwright disappeared between open_session and press: {exc}"
            ) from exc

        # D-80 / B-22 — page-level keyboard.press. No per-call timeout
        # available; Playwright applies its own internal default action
        # timeout (~30s).
        try:
            await session.page.keyboard.press(key)
        except PlaywrightError as exc:
            raise LeidConnectionError(
                f"press({key!r}) on session {session_id!r} failed at the "
                f"browser level: {exc}"
            ) from exc

        # B-17 / B-22 — successful press counts as activity.
        session.mark_activity()

        # D-85 — read post-press state. Press may have triggered navigation
        # (e.g., Enter submitted a form).
        current_url = session.page.url
        try:
            current_title = await session.page.title()
        except Exception:
            current_title = None

        self._log.debug(
            "Leið press: session=%s key=%r -> url=%s",
            session_id, key, current_url,
        )

        return {
            "session_id": session_id,
            "key": key,
            "pressed": True,
            "current_url": current_url,
            "current_title": current_title,
        }

    async def _go_history(
        self, session_id: str, direction: str
    ) -> dict[str, Any]:
        """Shared private helper for go_back / go_forward. (B-23, D-88..D-93)

        Both go_back and go_forward share identical structure differing
        only in the Playwright primitive used. This helper centralises
        the discipline; the public methods are thin wrappers (D-90).

        Args:
            session_id: A session_id from a prior open_session call.
            direction:  Either "back" or "forward". Selects which
                        Playwright primitive to call.

        Returns:
            dict with keys: session_id, moved, previous_url, current_url, title.

        Raises:
            LeidSessionExpiredError, LeidTimeoutError, LeidHttpError,
            LeidConnectionError.
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
                f"Playwright disappeared between open_session and "
                f"go_{direction}: {exc}"
            ) from exc

        # Capture previous URL BEFORE the history step (D-64 mirror).
        previous_url = session.page.url

        # Select the Playwright primitive (D-88, D-90).
        if direction == "back":
            primitive = session.page.go_back
        elif direction == "forward":
            primitive = session.page.go_forward
        else:
            # Defensive — this function is private and only called with
            # "back" or "forward", but be explicit.
            raise ValueError(
                f"_go_history: invalid direction {direction!r}; "
                f"expected 'back' or 'forward'."
            )

        navigation_timeout_ms = (
            self._config.browser_navigation_timeout_seconds * 1000
        )

        try:
            response = await primitive(
                wait_until=self._config.browser_load_state,
                timeout=navigation_timeout_ms,
            )
        except PlaywrightTimeoutError as exc:
            raise LeidTimeoutError(
                f"go_{direction} on session {session_id!r} timed out after "
                f"{self._config.browser_navigation_timeout_seconds}s "
                f"(load_state={self._config.browser_load_state!r}): {exc}"
            ) from exc
        except PlaywrightError as exc:
            raise LeidConnectionError(
                f"go_{direction} on session {session_id!r} failed at the "
                f"network layer: {exc}"
            ) from exc

        # D-89 — detect "no history in this direction".
        # Playwright returns None when there's no history entry.
        if response is None:
            session.mark_activity()  # B-17 (still counts as activity)
            # Read title defensively — page didn't move, but title can change
            try:
                title = await session.page.title()
            except Exception:
                title = None
            self._log.debug(
                "Leið go_%s: session=%s -> no history (moved: false)",
                direction, session_id,
            )
            return {
                "session_id": session_id,
                "moved": False,
                "previous_url": previous_url,
                "current_url": previous_url,  # didn't move
                "title": title,
            }

        # Status check on successful move.
        if response.status >= 400:
            raise LeidHttpError(
                f"HTTP {response.status} during go_{direction} on session "
                f"{session_id!r}."
            )

        # B-28 (v0.8.10) — final-URL allowlist re-check. The history nav
        # may have landed at a non-allowlisted URL (e.g., the original
        # destination redirected somewhere new since first navigated).
        # Stateful violation closes the session (D-139).
        try:
            self._check_final_url_allowed(
                session.page.url, input_url=f"<go_{direction} from {previous_url}>"
            )
        except UrlNotAllowedError:
            bad_url = session.page.url
            await manager.close_session(session_id)
            raise UrlNotAllowedError(
                f"go_{direction} on session {session_id!r} (from "
                f"{previous_url!r}) resulted in {bad_url!r}, which is "
                f"not in url_allowlist_patterns. The session has been closed."
            )

        # B-17 / B-23 — successful history nav counts as activity.
        session.mark_activity()

        final_url = session.page.url
        try:
            title = await session.page.title()
        except Exception:
            title = None

        self._log.debug(
            "Leið go_%s: session=%s prev=%s -> final=%s",
            direction, session_id, previous_url, final_url,
        )

        return {
            "session_id": session_id,
            "moved": True,
            "previous_url": previous_url,
            "current_url": final_url,
            "title": title,
        }

    async def go_back(self, session_id: str) -> dict[str, Any]:
        """Step backward in the session's browser history. (B-23, D-89)

        Returns ``{moved: false, ...}`` (NOT an error) when there's no
        history entry to go back to.

        See ``_go_history`` for the full contract.
        """
        return await self._go_history(session_id, "back")

    async def go_forward(self, session_id: str) -> dict[str, Any]:
        """Step forward in the session's browser history. (B-23, D-89)

        Returns ``{moved: false, ...}`` (NOT an error) when there's no
        history entry to go forward to (typical state after a fresh
        navigation that did not branch from history).

        See ``_go_history`` for the full contract.
        """
        return await self._go_history(session_id, "forward")

    async def session_render(self, session_id: str) -> dict[str, Any]:
        """Re-extract rendered text + title from the current session page. (B-24, D-97)

        v0.8.6 — ninth unnamed extension within Innan Hurðar; the in-session
        counterpart of v0.8.0's ``render_url``. Same primitives
        (``page.content()`` + ``_extract_text_from_html``); same B-6 size
        cap on rendered HTML byte size; same M-1 closure pattern around
        ``page.content``. Operates on the EXISTING session's page rather
        than launching a fresh browser — ~10-50x cheaper than render_url
        because no browser cold start is needed.

        Use after a click/type/press/navigate/history-step has changed
        what's on the page and you want to read the new state without
        closing and re-opening the session.

        Args:
            session_id: A session_id returned by a prior open_session call.

        Returns:
            dict with keys: session_id, current_url, text, title,
            source_size_bytes.

        Raises:
            LeidSessionExpiredError:    session_id unknown or evicted.
            LeidConnectionError:        browser-level failure.
            LeidResponseTooLargeError:  rendered HTML exceeds max_response_bytes.
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
                f"Playwright disappeared between open_session and "
                f"session_render: {exc}"
            ) from exc

        # D-101 — capture current URL at entry
        current_url = session.page.url

        # M-1 closure pattern (D-100): page.content wrapped with explicit
        # exception typing, mirroring v0.8.2's wrap of render_url's content.
        try:
            html = await session.page.content()
        except (PlaywrightTimeoutError, PlaywrightError) as exc:
            raise LeidConnectionError(
                f"session_render on session {session_id!r}: page.content() "
                f"failed at the browser level (page may have closed or "
                f"process disconnected): {exc}"
            ) from exc

        # B-6 inheritance — pre-cap on rendered HTML byte size
        rendered_size = len(html.encode("utf-8"))
        if rendered_size > self._config.max_response_bytes:
            self._log.warning(
                "Leið session_render: rendered HTML on session %s is %d "
                "bytes, exceeds max_response_bytes=%d — aborting before "
                "text extraction",
                session_id, rendered_size, self._config.max_response_bytes,
            )
            raise LeidResponseTooLargeError(
                f"Rendered HTML on session {session_id!r} is {rendered_size} "
                f"bytes, which exceeds max_response_bytes="
                f"{self._config.max_response_bytes}. Increase "
                f"LeidConfig.max_response_bytes or query smaller fragments "
                f"via leid.query."
            )

        # D-97 — reuse the v0.8.0 helper; no re-implementation
        text, title = _extract_text_from_html(html)

        # B-17 / B-24 — successful re-extract counts as activity
        session.mark_activity()

        self._log.debug(
            "Leið session_render: session=%s current_url=%s -> "
            "source_size=%d text_len=%d",
            session_id, current_url, rendered_size, len(text),
        )

        return {
            "session_id": session_id,
            "current_url": current_url,
            "text": text,
            "title": title,
            "source_size_bytes": rendered_size,
        }

    async def session_screenshot(self, session_id: str) -> dict[str, Any]:
        """Capture base64 PNG of the current session page. (B-24, D-98)

        v0.8.6 — paired with session_render; the in-session counterpart of
        v0.8.1's ``screenshot``. Same primitive (``page.screenshot``);
        same B-11 size cap on raw PNG bytes BEFORE base64 encoding; same
        M-1 closure pattern around ``page.screenshot``. Operates on the
        EXISTING session's page rather than launching a fresh browser
        — ~10x cheaper than screenshot because no browser cold start.

        Args:
            session_id: A session_id returned by a prior open_session call.

        Returns:
            dict with keys: session_id, current_url, image_base64,
            image_format, size_bytes, full_page.

        Raises:
            LeidSessionExpiredError:    session_id unknown or evicted.
            LeidConnectionError:        browser-level failure.
            LeidResponseTooLargeError:  raw PNG bytes exceed max_response_bytes.
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
                f"Playwright disappeared between open_session and "
                f"session_screenshot: {exc}"
            ) from exc

        # D-101 — capture current URL at entry
        current_url = session.page.url
        full_page = self._config.browser_screenshot_full_page  # D-98 reuse

        # M-1 closure pattern (D-100): page.screenshot wrapped with explicit
        # exception typing, mirroring v0.8.2's wrap of screenshot's primitive.
        # B-29 (v0.8.11): operator-controlled format + quality.
        screenshot_kwargs: dict[str, Any] = {
            "full_page": full_page,
            "type": self._config.browser_screenshot_format,
        }
        if self._config.browser_screenshot_format != "png":
            screenshot_kwargs["quality"] = (
                self._config.browser_screenshot_jpeg_quality
            )
        try:
            png_bytes = await session.page.screenshot(**screenshot_kwargs)
        except (PlaywrightTimeoutError, PlaywrightError) as exc:
            raise LeidConnectionError(
                f"session_screenshot on session {session_id!r}: "
                f"page.screenshot() failed at the browser level (page may "
                f"have closed or process disconnected): {exc}"
            ) from exc

        # B-11 inheritance — pre-cap on raw PNG bytes BEFORE base64
        png_size = len(png_bytes)
        if png_size > self._config.max_response_bytes:
            self._log.warning(
                "Leið session_screenshot: PNG on session %s is %d bytes, "
                "exceeds max_response_bytes=%d — aborting before base64",
                session_id, png_size, self._config.max_response_bytes,
            )
            raise LeidResponseTooLargeError(
                f"PNG screenshot on session {session_id!r} is {png_size} "
                f"bytes, which exceeds max_response_bytes="
                f"{self._config.max_response_bytes}. Increase "
                f"LeidConfig.max_response_bytes, or set "
                f"browser_screenshot_full_page: false to capture only "
                f"the viewport."
            )

        # Base64 encode (D-17 from v0.8.1) — ASCII-decode safe by definition
        image_base64 = base64.b64encode(png_bytes).decode("ascii")

        # B-17 / B-24 — successful re-shoot counts as activity
        session.mark_activity()

        self._log.debug(
            "Leið session_screenshot: session=%s current_url=%s -> "
            "png_size=%d full_page=%s",
            session_id, current_url, png_size, full_page,
        )

        return {
            "session_id": session_id,
            "current_url": current_url,
            "image_base64": image_base64,
            # B-29 (v0.8.11): reflect actual format used (was hardcoded "png")
            "image_format": self._config.browser_screenshot_format,
            "size_bytes": png_size,
            "full_page": full_page,
        }

    async def reload(self, session_id: str) -> dict[str, Any]:
        """Refresh the current page of an open session. (B-25, D-107)

        v0.8.7 — tenth unnamed extension within Innan Hurðar; the body's
        footstep in place. Re-fetches the current page through Playwright's
        ``page.reload()``. Cookies and localStorage persist (intrinsic
        to refresh semantics). The URL stays the same in normal cases (a
        server-side redirect on reload could change it).

        Args:
            session_id: A session_id from a prior open_session call.

        Returns:
            dict with keys: session_id, current_url, title.

        Raises:
            LeidSessionExpiredError, LeidTimeoutError, LeidHttpError,
            LeidConnectionError.
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
                f"Playwright disappeared between open_session and "
                f"reload: {exc}"
            ) from exc

        navigation_timeout_ms = (
            self._config.browser_navigation_timeout_seconds * 1000
        )

        # D-107 — page.reload returns Response | None
        try:
            response = await session.page.reload(
                wait_until=self._config.browser_load_state,
                timeout=navigation_timeout_ms,
            )
        except PlaywrightTimeoutError as exc:
            raise LeidTimeoutError(
                f"reload on session {session_id!r} timed out after "
                f"{self._config.browser_navigation_timeout_seconds}s "
                f"(load_state={self._config.browser_load_state!r}): {exc}"
            ) from exc
        except PlaywrightError as exc:
            raise LeidConnectionError(
                f"reload on session {session_id!r} failed at the "
                f"network layer: {exc}"
            ) from exc

        # Status check — only when response is non-None (data: URLs return None)
        if response is not None and response.status >= 400:
            raise LeidHttpError(
                f"HTTP {response.status} during reload on session "
                f"{session_id!r}."
            )

        # B-28 (v0.8.10) — final-URL allowlist re-check. The reload may
        # have been redirected somewhere new since the page was first
        # navigated to. Stateful violation closes the session (D-139).
        try:
            self._check_final_url_allowed(
                session.page.url, input_url=f"<reload of session {session_id}>"
            )
        except UrlNotAllowedError:
            bad_url = session.page.url
            await manager.close_session(session_id)
            raise UrlNotAllowedError(
                f"reload on session {session_id!r} resulted in {bad_url!r}, "
                f"which is not in url_allowlist_patterns. The session has "
                f"been closed."
            )

        # B-17 / B-25 — successful reload counts as activity
        session.mark_activity()

        # D-111 minimal shape — read post-reload state
        current_url = session.page.url
        try:
            title = await session.page.title()
        except Exception:
            title = None

        self._log.debug(
            "Leið reload: session=%s -> current_url=%s",
            session_id, current_url,
        )

        return {
            "session_id": session_id,
            "current_url": current_url,
            "title": title,
        }

    async def query_all(
        self, session_id: str, selector: str, attribute: str = ""
    ) -> dict[str, Any]:
        """Read text or attribute of ALL elements matching *selector*. (B-26, D-114..D-125)

        v0.8.8 — eleventh unnamed extension within Innan Hurðar; the
        multi-element follow-up to v0.8.3's single-match ``query``.
        Returns ALL matches as a list (in DOM order) up to a cardinality
        cap (``config.browser_query_max_matches``).

        Same DELIBERATE divergence as ``query`` (D-72 / D-117): empty
        result is NOT an error — returns ``{count: 0, values: []}``.
        Multi-element query is a probe-and-act primitive; the agent's
        natural "give me all matches" includes the success case of
        "there were zero."

        Args:
            session_id: A session_id from a prior open_session call.
            selector:   CSS selector. ALL matching elements (up to cap)
                        are extracted in DOM order.
            attribute:  Optional. If empty (default), returns each
                        element's text content. If non-empty, returns
                        the value of that HTML attribute (None if
                        attribute absent).

        Returns:
            dict with keys: session_id, selector, attribute, count, values.
            ``values`` is a list of strings or None (length == count).

        Raises:
            LeidSessionExpiredError:    session_id unknown or evicted.
            LeidConnectionError:        browser-level failure on count or
                                        per-element extraction.
            LeidResponseTooLargeError:  count > config.browser_query_max_matches.
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
                f"Playwright disappeared between open_session and "
                f"query_all: {exc}"
            ) from exc

        timeout_ms = self._config.browser_click_timeout_seconds * 1000  # D-122

        # Stage 4 — locator + count
        locator = session.page.locator(selector)
        try:
            count = await locator.count()
        except PlaywrightError as exc:
            raise LeidConnectionError(
                f"query_all({selector!r}) on session {session_id!r}: "
                f"locator.count() failed at the browser level: {exc}"
            ) from exc

        # Stage 5 — cardinality cap (B-26 NEW; D-116)
        max_matches = self._config.browser_query_max_matches
        if count > max_matches:
            self._log.warning(
                "Leið query_all: selector %r matched %d elements on session "
                "%s, exceeds browser_query_max_matches=%d — aborting before "
                "iteration",
                selector, count, session_id, max_matches,
            )
            raise LeidResponseTooLargeError(
                f"Selector {selector!r} matched {count} elements in session "
                f"{session_id!r}, which exceeds browser_query_max_matches="
                f"{max_matches}. Refine the selector to match fewer "
                f"elements, or raise LeidConfig.browser_query_max_matches "
                f"if your use case genuinely needs many matches."
            )

        # Stage 6 — empty-result early return (D-117)
        if count == 0:
            session.mark_activity()  # B-17 / B-26 (still counts)
            self._log.debug(
                "Leið query_all: session=%s selector=%r -> no matches",
                session_id, selector,
            )
            return {
                "session_id": session_id,
                "selector": selector,
                "attribute": attribute,
                "count": 0,
                "values": [],
            }

        # Stage 7 — iterate matches and extract (D-118)
        values: list[Any] = []
        for i in range(count):
            el = locator.nth(i)
            try:
                if attribute == "":  # D-120 default = text content
                    v = await el.text_content(timeout=timeout_ms)
                else:  # D-120 specific attribute
                    v = await el.get_attribute(attribute, timeout=timeout_ms)
            except PlaywrightTimeoutError as exc:
                raise LeidConnectionError(
                    f"query_all({selector!r}, attribute={attribute!r}) "
                    f"on session {session_id!r}: extraction at index {i} "
                    f"timed out after "
                    f"{self._config.browser_click_timeout_seconds}s: {exc}"
                ) from exc
            except PlaywrightError as exc:
                raise LeidConnectionError(
                    f"query_all({selector!r}, attribute={attribute!r}) "
                    f"on session {session_id!r}: extraction at index {i} "
                    f"failed at the browser level: {exc}"
                ) from exc
            values.append(v)

        # Stage 8 — activity update (B-17 / B-26)
        session.mark_activity()

        self._log.debug(
            "Leið query_all: session=%s selector=%r attribute=%r "
            "-> count=%d, values_len=%d",
            session_id, selector, attribute, count, len(values),
        )

        return {
            "session_id": session_id,
            "selector": selector,
            "attribute": attribute,
            "count": count,
            "values": values,
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
