# Leið Sense — Interface Contract

**Last updated:** 2026-05-11 (v0.8.11 JPEG/WebP screenshot output — Rúnhild Svartdóttir) | 2026-05-11 (v0.8.10 final-URL allowlist re-check) | 2026-05-11 (v0.8.9 configurable viewport) | 2026-05-11 (v0.8.8 query_all extension) | 2026-05-11 (v0.8.7 reload extension) | 2026-05-11 (v0.8.6 mid-session re-extract pair) | 2026-05-10 (v0.8.5 history nav extension) | 2026-05-10 (v0.8.4 press extension) | 2026-05-10 (v0.8.3 query extension) | 2026-05-10 (v0.8.2.2 navigate extension) | 2026-05-10 (v0.8.2.1 type extension) | 2026-05-10 (v0.8.2 *Innan Hurðar* stateful sessions + click) | 2026-05-10 (v0.8.1 *Mynd af Vegferð* screenshot) | 2026-05-10 (v0.8.0 *Opið Vef* browser-render) | 2026-05-09 (v0.7.1 *Straumr á Leið* streaming) | 2026-05-08 (v0.6.2 scaffold)
**Scope:** L5.3 Leið — sandboxed HTTP fetch sense (httpx) + browser-render sub-faculty (Playwright, opt-in)
**Authority:** Architect (Rúnhild Svartdóttir)

---

## 1. Identity

| Field       | Value                                          |
|-------------|------------------------------------------------|
| True Name   | Leið ("path" / "way")                          |
| sense_id    | `leid`                                         |
| Layer       | L5.3 Skilningr sense hub                       |
| Prefix      | `leid.*`                                       |
| Config key  | `skilningr.leid.*` in `heretic.yaml`           |
| Module      | `heretic.skilningr.senses.leid`                |
| Client (httpx) | `LeidClient` (httpx GET, URL allowlist) — answers `leid.fetch_url`, `leid.extract_text` |
| Client (browser, v0.8.0+, opt-in) | `PlaywrightLeidClient` (headless Chromium via Playwright) — answers `leid.render_url` |

---

## 2. Purpose

Leið gives the agent a road to the outside web — strictly bounded. It fetches
HTTP resources and extracts their text within an operator-defined URL allowlist.
No URL is reachable unless the operator explicitly permits a matching pattern.
An empty allowlist means the world is closed.

Leið's **httpx tools** (`leid.fetch_url`, `leid.extract_text`) do NOT execute JavaScript.
They do NOT follow links beyond the requested URL. They do NOT store or send
cookies. They do NOT support POST or any other write method. These are GET-only
since v0.6.2.

Leið's **browser tool** (`leid.render_url`, **v0.8.0+, opt-in via `pip install heretic[browser]`**)
launches a headless Chromium subprocess via Playwright and DOES allow the page's
own scripts to run before reading the rendered DOM. It uses a fresh browser
context per call — no cookies persist between calls, no localStorage carries
over, no state of any kind crosses call boundaries. HERETIC injects no
JavaScript of its own; only the page's scripts run, on the page itself. See §10
for the v0.8.0 browser-mode contract.

---

## 3. Sandbox Invariants (NON-NEGOTIABLE)

| # | Invariant |
|---|-----------|
| L-1 | `sandbox.url_matches_allowlist()` is called BEFORE any `httpx` request is made. No HTTP I/O precedes this check. |
| L-2 | `url_allowlist_patterns` defaults `[]` (empty). With an empty list, no URL is fetchable regardless of `enabled=True`. |
| L-3 | `enabled: false` by default. No outbound HTTP until explicitly enabled. |
| L-4 | HTTPS-only by default (`allow_http: false`). HTTP URLs are rejected unless `allow_http: true`. Even when allowed, HTTP is logged as a warning. |
| L-5 | No cookies stored, sent, or accepted at any time. |
| L-6 | No JavaScript execution. httpx is the transport; playwright/selenium = v0.8 Opið Vef. |
| L-7 | Response body is capped at `max_response_bytes` (default 1 MiB). **As of v0.7.1 the cap is enforced via streaming abort:** `httpx.AsyncClient.stream("GET", url)` + `aiter_bytes`; the `LeidResponseTooLargeError` is raised **mid-stream** as soon as the accumulator exceeds the cap. The connection is closed during stack unwind; remaining bytes never travel. Memory at moment of raise is bounded by `max_response_bytes + chunk_size` (default ~1.06 MiB). The agent receives a structured error, never partial content. |
| L-7a | When `Content-Length` header is present and already exceeds `max_response_bytes`, `LeidResponseTooLargeError` is raised before any chunk is read. Malformed `Content-Length` values are ignored (fall through to chunk loop). |
| L-8 | Redirects are followed up to `max_redirects` (default 5). Beyond that the request aborts with LeidConnectionError. |
| L-9 | The wildcard pattern `"*"` is logged as a security warning at ceremony start if present in `url_allowlist_patterns`. |

---

## 4. Tools

### 4.1 httpx tools (LOCKED at v0.6.2)

| Tool name          | Action              | Required params  | Optional params | Transport |
|--------------------|---------------------|------------------|-----------------|-----------|
| `leid.fetch_url`   | Raw HTTP GET        | `url` (string)   | —               | httpx     |
| `leid.extract_text`| GET + strip HTML    | `url` (string)   | —               | httpx     |

### 4.2 Stateless browser tools (added at v0.8.0+ — *Opið Vef*)

| Tool name          | Action                                          | Required params  | Optional params | Transport          | Added |
|--------------------|-------------------------------------------------|------------------|-----------------|--------------------|-------|
| `leid.render_url`  | Headless Chromium navigate + extract rendered text | `url` (string) | —               | Playwright (Chromium) | v0.8.0 |
| `leid.screenshot`  | Headless Chromium navigate + return base64 PNG of rendered page | `url` (string) | — | Playwright (Chromium) | v0.8.1 |

### 4.3 Stateful browser tools (added at v0.8.2 — *Innan Hurðar*)

| Tool name              | Action                                                              | Required params                          | Transport             | Added |
|------------------------|---------------------------------------------------------------------|------------------------------------------|-----------------------|-------|
| `leid.open_session`    | Open a stateful session at URL; page stays alive                    | `url` (string)                           | Playwright (Chromium) | v0.8.2 |
| `leid.session_status`  | Non-mutating health/identity check on an open session               | `session_id` (string)                    | Playwright (Chromium) | v0.8.2 |
| `leid.click`           | Click first element matching CSS selector inside open session       | `session_id`, `selector` (both strings)  | Playwright (Chromium) | v0.8.2 |
| `leid.type`            | Fill first element matching selector with the supplied text         | `session_id`, `selector`, `text` (all strings) | Playwright (Chromium) | v0.8.2.1 |
| `leid.navigate`        | Navigate an open session to a new URL (cookies + localStorage persist) | `session_id`, `url` (both strings)    | Playwright (Chromium) | v0.8.2.2 |
| `leid.query`           | Read text or attribute of first element matching CSS selector (read-only; not-found is not an error) | `session_id`, `selector` (req); `attribute` (opt) | Playwright (Chromium) | v0.8.3 |
| `leid.press`           | Send a keyboard key (Enter, Tab, Escape, modifier combos) at page-level focus | `session_id`, `key` (both strings) | Playwright (Chromium) | v0.8.4 |
| `leid.go_back`         | Step backward in the session's browser history; `moved: false` if at start | `session_id` (string) | Playwright (Chromium) | v0.8.5 |
| `leid.go_forward`      | Step forward in the session's browser history; `moved: false` if at end | `session_id` (string) | Playwright (Chromium) | v0.8.5 |
| `leid.session_render`  | Re-extract rendered text + title from the current session page (mid-session counterpart of leid.render_url) | `session_id` (string) | Playwright (Chromium) | v0.8.6 |
| `leid.session_screenshot` | Capture base64 PNG of the current session page (mid-session counterpart of leid.screenshot) | `session_id` (string) | Playwright (Chromium) | v0.8.6 |
| `leid.reload`          | Refresh the current page of an open session (re-fetch + re-render in place) | `session_id` (string) | Playwright (Chromium) | v0.8.7 |
| `leid.query_all`       | Read text or attribute of ALL elements matching CSS selector (read-only; bounded by browser_query_max_matches) | `session_id`, `selector` (req); `attribute` (opt) | Playwright (Chromium) | v0.8.8 |
| `leid.close_session`   | Close session and release all resources (idempotent for unknown id) | `session_id` (string)                    | Playwright (Chromium) | v0.8.2 |

**Availability:** the browser tools are registered in `LEID_TOOL_DEFINITIONS`
whenever `config.enabled: true`, but a tool call to either raises
`LeidPlaywrightUnavailableError → EXTERNAL_APP_UNAVAILABLE` if the operator has
not installed the `[browser]` extra (`pip install heretic[browser]`) and run
`playwright install chromium`. The httpx tools (`leid.fetch_url`,
`leid.extract_text`) work unaffected regardless.

---

## 5. Success Response Shapes

### leid.fetch_url
```json
{
  "url": "https://docs.python.org/3/library/os.html",
  "status_code": 200,
  "content_type": "text/html; charset=utf-8",
  "body": "<html>...",
  "size_bytes": 45678
}
```

> **Drift correction (v0.7.1):** Earlier sketches of this section showed `body_encoding`
> and `truncated` keys. The shipped v0.6.2 client returned neither (UTF-8 decode with
> `errors="replace"` is implicit; oversized bodies raise instead of truncating). The
> table above now matches the live `LeidClient.fetch_url` return shape. v0.7.1 does not
> change these keys.

### leid.extract_text
```json
{
  "url": "https://docs.python.org/3/library/os.html",
  "text": "os — Miscellaneous operating system interfaces...",
  "title": "os — Miscellaneous operating system interfaces — Python 3 documentation",
  "source_size_bytes": 45678
}
```

> **Drift correction (v0.7.1):** Earlier sketches showed `size_bytes` and `truncated`.
> The shipped client returns `source_size_bytes` (the bytes of the original HTML before
> tag-stripping) and no `truncated` key. v0.7.1 does not change these keys.

---

## 6. Failure Modes

| Condition                                  | Error class                | SENSE_CONTRACTS code      |
|--------------------------------------------|----------------------------|---------------------------|
| URL not in allowlist                       | `UrlNotAllowedError`       | `PERMISSION_DENIED`       |
| HTTP URL and `allow_http: false`           | `UrlNotAllowedError`       | `PERMISSION_DENIED`       |
| Request timed out                          | `LeidTimeoutError`         | `SENSE_TIMEOUT`           |
| Response exceeds `max_response_bytes`      | `LeidResponseTooLargeError`| `INVALID_ARGUMENTS`       |
| HTTP 4xx / 5xx status                      | `LeidHttpError`            | `SENSE_INTERNAL_ERROR`    |
| Network-level error (DNS, TCP, TLS)        | `LeidConnectionError`      | `EXTERNAL_APP_UNAVAILABLE`|
| Unknown tool name in `leid.*`              | `ToolDispatchError`        | `SENSE_INTERNAL_ERROR`    |
| Sense disabled or not open                 | `SenseUnavailableError`    | `SENSE_UNAVAILABLE`       |
| Playwright not installed / chromium missing (v0.8.0+ browser tools) | `LeidPlaywrightUnavailableError` | `EXTERNAL_APP_UNAVAILABLE` |
| Concurrent-session cap reached (v0.8.2 `leid.open_session`)   | `LeidSessionLimitError`     | `SENSE_UNAVAILABLE`       |
| Unknown / evicted session_id (v0.8.2 status/click/close)     | `LeidSessionExpiredError`   | `SENSE_UNAVAILABLE`       |
| Selector matched no element within click timeout (v0.8.2)    | `LeidClickElementNotFoundError` | `INVALID_ARGUMENTS`   |
| Selector matched no element within type timeout (v0.8.2.1)   | `LeidTypeElementNotFoundError`  | `INVALID_ARGUMENTS`   |

---

## 7. Configuration Reference

```yaml
skilningr:
  leid:
    enabled: false                        # opt-in
    url_allowlist_patterns: []            # empty = nothing fetchable; add patterns
      # - "https://docs.python.org/*"
      # - "https://en.wikipedia.org/*"
    timeout_seconds: 30
    max_redirects: 5
    max_response_bytes: 1048576           # 1 MB
    user_agent: "HERETIC/0.6.2 (heretic-summoning-circle)"
    allow_http: false                     # HTTPS-only by default

    # v0.8.0 Opið Vef — browser-render fields (apply to all browser tools)
    browser_navigation_timeout_seconds: 30   # max wall-clock for page.goto(); separate from httpx timeout
    browser_load_state: "domcontentloaded"   # one of: commit, domcontentloaded, load, networkidle

    # v0.8.1 Mynd af Vegferð — screenshot field (applies to leid.screenshot only)
    browser_screenshot_full_page: true       # true=capture full scrollable page; false=viewport only

    # v0.8.2 Innan Hurðar — session lifecycle + click fields
    browser_max_concurrent_sessions: 3            # hard cap; open_session at cap raises
    browser_session_idle_timeout_seconds: 300     # 5 min — evict on idle
    browser_session_max_lifetime_seconds: 1800    # 30 min — hard ceiling
    browser_click_timeout_seconds: 10             # max wall-clock for a single click

    # v0.8.8 query_all — cardinality cap on multi-element query
    browser_query_max_matches: 100                # hard cap; query_all > cap raises

    # v0.8.9 — configurable viewport (applied at all browser-context creations)
    browser_viewport_width: 1280                  # viewport width in pixels (>0)
    browser_viewport_height: 720                  # viewport height in pixels (>0)

    # v0.8.11 — screenshot format + quality (applied to screenshot tools)
    browser_screenshot_format: "png"              # one of: png, jpeg, webp
    browser_screenshot_jpeg_quality: 80           # 0..100; ignored when format=png
```

---

## 8. Forge Implementation Contract

### v0.7.1 (current — *Straumr á Leið* streaming)

- `fetch_url`:
  1. Call `_validate_url()` first (allowlist + HTTPS-only gate). No httpx call before this.
  2. Open `httpx.AsyncClient(follow_redirects=True, max_redirects=config.max_redirects, timeout=config.timeout_seconds, headers={"User-Agent": config.user_agent})`.
  3. Open `client.stream("GET", url)` as the response context.
  4. **Pre-cap on `Content-Length`**: if header is present and parses as `int` greater than `max_response_bytes`, raise `LeidResponseTooLargeError` immediately. Malformed values are ignored.
  5. **Status check**: if `response.status_code >= 400`, peek up to 500 bytes via a bounded `aiter_bytes` loop for the error-message tail, then raise `LeidHttpError`.
  6. **Streaming accumulator**: `acc = bytearray()`. Iterate `async for chunk in response.aiter_bytes(65536)`. Extend `acc`. After each extend, if `len(acc) > max_response_bytes`, raise `LeidResponseTooLargeError`.
  7. Decode `bytes(acc)` as UTF-8 with `errors="replace"`. Return dict with the five keys in §5.
  8. Map `httpx.TimeoutException` → `LeidTimeoutError`; `httpx.TooManyRedirects` → `LeidConnectionError`; `httpx.ConnectError` → `LeidConnectionError`; other `httpx.HTTPError` → `LeidConnectionError`.

- `extract_text`: call `fetch_url()` internally; if `content_type` contains `text/html` or `application/xhtml`, use `_TextExtractor` (stdlib `html.parser` subclass) to strip tags and capture title; otherwise return raw decoded body as text. No external HTML parser dependency.

### v0.6.2 (historical — buffer-then-check)

The v0.6.2 implementation read `response.content` (full materialisation) then checked
`len > max_response_bytes`. The exception class and surface contract were the same; the
mechanism was the difference. v0.7.1 replaces this in place; the v0.6.2 code path is
gone. The audit-deferred N-2 finding from `AUDIT_v0.6.2_MORE_SENSES.md` is closed by
v0.7.1.

### Method shape policy

The public surface (`fetch_url`, `extract_text`) is **unchanged** between v0.6.2 and
v0.7.1. No new methods, no new private helpers, no new config keys. The streaming
behaviour is hidden behind the same agent-facing contract. This was an explicit
Architect decision: a one-path replacement is cleaner than parallel buffer/streaming
modes when the v0.6.2 path was authored as a known-temporary placeholder.

The v0.8.0 *Opið Vef* addition does NOT modify `LeidClient`. The new browser-render
sub-faculty lives in a sibling class `PlaywrightLeidClient` with its own `render_url()`
method. `LeidSense._route` dispatches `leid.fetch_url` and `leid.extract_text` to
`LeidClient` (unchanged) and `leid.render_url` to `PlaywrightLeidClient`. This was an
explicit Architect decision (D-14): the v0.7.1 streaming path is byte-untouched and
zero-regression-risk; the new transport is purely additive.

---

## 10. Browser-mode contract (v0.8.0 — *Opið Vef*)

### 10.1 Sub-faculty identity

| Field            | Value                                                                     |
|------------------|---------------------------------------------------------------------------|
| Sub-faculty name | *Opið Vef* — "the open web"                                               |
| Tool             | `leid.render_url`                                                         |
| Module           | `heretic.skilningr.senses.leid.playwright_client`                         |
| Class            | `PlaywrightLeidClient`                                                    |
| Engine           | Chromium (headless) via Playwright (Microsoft, Apache-2.0)                |
| Optional dep     | `pip install heretic[browser]` + `playwright install chromium`            |
| Lifecycle        | Launch-per-call (D-5): each call spawns and disposes its own browser     |

### 10.2 B-Invariants (NON-NEGOTIABLE — additive over L-1..L-9)

The L-invariants from §3 continue to govern the httpx tools unchanged. The
B-invariants govern `leid.render_url`. Where an L and a B address the same
concern, B is a refinement, not a replacement.

| #   | B-Invariant |
|-----|-------------|
| B-1 | `_validate_url()` (allowlist + HTTPS-only gate) is called BEFORE `async_playwright().start()`. No browser process spawns for a rejected URL. |
| B-2 | `LeidPlaywrightUnavailableError` is raised at `render_url()` entry if `playwright` import or `chromium.launch()` fails. The httpx tools (`fetch_url`, `extract_text`) continue to dispatch unaffected. |
| B-3 | Each `render_url()` call uses `browser.new_context()` — cookies and localStorage are scoped to the call and discarded at `context.close()`. No state persists between calls. |
| B-4 | The browser is launched headless (`headless=True`). No visible window. |
| B-5 | `page.goto(url, wait_until=config.browser_load_state, timeout=config.browser_navigation_timeout_seconds * 1000)`. Playwright's `TimeoutError` maps to `LeidTimeoutError`. |
| B-6 | After navigation: `len(html.encode("utf-8")) <= config.max_response_bytes`. If exceeded, raise `LeidResponseTooLargeError` BEFORE text extraction; close context+browser+pw cleanly during stack unwind. |
| B-7 | All three resources (`pw`, `browser`, `context`) are closed in `finally` blocks. A failure during navigation must not leak a browser process. |
| B-8 | The `User-Agent` on every browser request matches `config.user_agent`, passed via `browser.new_context(user_agent=...)`. |
| B-9 | `allow_http: false` rejects `http://` URLs at `_validate_url()` before browser launch — same posture as httpx tools. |
| B-10 | HERETIC injects no JavaScript code into the page in v0.8.0. The page's own scripts run during render; that is the only script execution. No `page.evaluate(...)` from agent input. |

### 10.3 Success response shape

```json
{
  "url": "https://example.com/spa",
  "final_url": "https://example.com/spa#loaded",
  "text": "Welcome to the rendered SPA...",
  "title": "Example SPA — Home",
  "source_size_bytes": 24576
}
```

| Key                | Type   | Meaning                                                                     |
|--------------------|--------|-----------------------------------------------------------------------------|
| `url`              | string | The validated URL passed in (post normalisation; identical to input in most cases) |
| `final_url`        | string | `page.url` after navigation; differs from `url` when the page navigated itself during render (client-side redirect, hash change, etc.) |
| `text`             | string | Plain text extracted from rendered DOM via the same stdlib `_TextExtractor` as `extract_text` |
| `title`            | string \| null | `<title>` of the rendered DOM; `null` if absent                       |
| `source_size_bytes`| int    | UTF-8 byte length of `await page.content()` (the rendered HTML before tag stripping) |

### 10.4 Memory bound at the rendered-HTML cap

Unlike `leid.fetch_url` (which streams via `aiter_bytes` and aborts mid-stream
once the accumulator exceeds the cap), `leid.render_url` materialises the entire
rendered DOM as a single string via `await page.content()` BEFORE the cap is
checked. The worst-case memory at the moment of pre-cap raise is therefore
approximately:

```
len(html.encode("utf-8")) + Python string overhead
```

This is intentional: Playwright does not expose a streaming DOM read API. The
cap on `render_url` is a **token-budget bound** (preventing the agent from
receiving an enormous text payload), not a **memory bound** for the browser
process itself. Operators who need true streaming abort must use `leid.fetch_url`,
which retains the v0.7.1 streaming guarantees. This trade-off is documented at
DATA_FLOW.md §4.12.2.2.

### 10.5 Out of scope at v0.8.0

| Capability                 | Status            |
|----------------------------|-------------------|
| `leid.screenshot`          | v0.8.1 (separate slice) |
| `leid.click`, `leid.type`  | v0.8.2 (requires persistent-session model) |
| `leid.query`               | v0.8.3 (CSS selector + attribute extraction) |
| Multi-tab support          | v0.8.x+           |
| Persistent browser between calls | v0.8.2 (when click/type need a live page) |
| Cookie persistence         | NEVER (B-3 is permanent) |
| Visible browser mode       | Not planned (debug-only, may add later if needed) |

### 10.6 Forge implementation contract

- `PlaywrightLeidClient(config: LeidConfig, log: logging.Logger | None = None)`
  has a single public coroutine: `async def render_url(self, url: str) -> dict`.
- Imports of `playwright` are deferred to inside `render_url()` — the module
  import does NOT require playwright to be installed. This guarantees that
  modules importing `playwright_client` do not break on hosts without the
  `[browser]` extra.
- Allowlist + HTTPS-only validation reuses the existing `_validate_url()` logic
  (refactored into a shared helper or duplicated; Forge to choose the
  cleanest integration without modifying `LeidClient`).
- All three resources opened (`pw`, `browser`, `context`) are closed in nested
  `try/finally` blocks. The unwinding order is: `context.close()` →
  `browser.close()` → `pw.stop()`.
- Status-code check uses the `Response` object returned by `page.goto()`.
- Pre-cap on `len(html.encode("utf-8"))` BEFORE `_extract_text_from_html` is
  called. The extractor is the same one used by `LeidClient.extract_text`.
- The 17 mock-based tests in `tests/test_leid_playwright_client.py` exhaust the
  invariants. The `@pytest.mark.requires_playwright` smoke test exercises a
  real Chromium when the operator has installed it; it is default-skip in CI.

---

## 11. Browser-mode contract addendum (v0.8.1 — *Mynd af Vegferð*)

> **Added 2026-05-10 v0.8.1.** Adds `leid.screenshot` as a sibling method on
> `PlaywrightLeidClient`. Same lifecycle as `render_url`; one new invariant.

### 11.1 New tool

| Field    | Value                                                 |
|----------|-------------------------------------------------------|
| Tool     | `leid.screenshot`                                     |
| Method   | `PlaywrightLeidClient.screenshot(url: str) -> dict`   |
| Engine   | Chromium (headless) via Playwright (same as `render_url`) |

### 11.2 New B-Invariant

| #    | B-Invariant |
|------|-----------|
| B-11 | `screenshot()` enforces the same size cap as `render_url`, applied to the **raw PNG bytes BEFORE base64 encoding**. If `len(png_bytes) > config.max_response_bytes`, `LeidResponseTooLargeError` is raised BEFORE the `base64.b64encode` call. The B-7 cleanup invariant continues to hold: context/browser/pw all closed during stack unwind. |

B-1..B-10 from §10.2 govern `screenshot()` unchanged. B-10 in particular gains a regression-guard test at this milestone (`page.evaluate` is asserted not-called for both methods), closing Audit N-2 from `AUDIT_v0.8.0_OPID_VEF.md`.

### 11.3 Success response shape

```json
{
  "url": "https://example.com/dashboard",
  "final_url": "https://example.com/dashboard",
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "image_format": "png",
  "size_bytes": 45678,
  "full_page": true
}
```

| Key              | Type   | Meaning                                                         |
|------------------|--------|-----------------------------------------------------------------|
| `url`            | string | Validated URL passed in (post normalisation)                    |
| `final_url`      | string | `page.url` after navigation; differs on client-side redirect    |
| `image_base64`   | string | Base64-encoded PNG bytes (ASCII-safe)                           |
| `image_format`   | string | Always `"png"` at v0.8.1 (JPEG/WebP deferred)                   |
| `size_bytes`     | int    | Length of the **raw PNG bytes** (before base64 expansion)       |
| `full_page`      | bool   | Echo of `config.browser_screenshot_full_page` actually used     |

### 11.4 Why the cap is on raw PNG bytes, not base64 length

Base64 expands by approximately 4/3 (33% growth). Capping on the encoded length would force operators to set `max_response_bytes` 33% higher to allow the same actual image content, conflating *content size* with *transport encoding overhead*. The v0.8.1 contract caps on what the body actually fetched (PNG bytes), not on what the body re-encoded for the agent. This is consistent with how `render_url` caps on the UTF-8 byte length of `page.content()` (the rendered content), not on a downstream encoding step.

### 11.5 New configuration field

| Field                            | Type | Default | Meaning                                                |
|----------------------------------|------|---------|--------------------------------------------------------|
| `browser_screenshot_full_page`   | bool | `True`  | `True`: capture entire scrollable page. `False`: viewport only (1280x720 default). |

### 11.6 Out of scope at v0.8.1

| Capability                  | Status            |
|-----------------------------|-------------------|
| `leid.click`, `leid.type`   | v0.8.2            |
| `leid.query`                | v0.8.3            |
| Element/region screenshots  | v0.8.x+           |
| JPEG / WebP output formats  | v0.8.x+           |
| Configurable viewport size  | v0.8.x+           |
| Screenshot quality settings | v0.8.x+ (PNG is lossless; quality applies to JPEG only) |

### 11.7 Forge implementation contract

- `screenshot()` lives as a sibling method on `PlaywrightLeidClient`. The v0.8.0 `render_url()` is byte-untouched (Architect D-23: strict additive law honoured at v0.8.1; refactor question revisited at v0.8.2 if patterns coalesce).
- `_validate_url()` is reused from the existing v0.8.0 implementation.
- Resource cleanup uses the same `try/finally` shape as `render_url()`.
- `await page.screenshot(full_page=config.browser_screenshot_full_page, type="png")` returns `bytes`; the cap check then compares `len(png_bytes)` to `config.max_response_bytes`; on success `image_base64 = base64.b64encode(png_bytes).decode("ascii")`.
- Tests live in `tests/test_leid_playwright_client.py::TestScreenshot` and exhaust B-1..B-10 + the new B-11. Two B-10 regression-guard tests are added (`test_render_url_does_not_call_page_evaluate`, `test_screenshot_does_not_call_page_evaluate`) closing Audit N-2.

---

## 12. Stateful sessions + click contract (v0.8.2 — *Innan Hurðar*)

### 12.1 New sub-disposition

Where v0.8.0 (`render_url`) and v0.8.1 (`screenshot`) had the body do a single
stateless act per call, v0.8.2 introduces **stateful sessions**: the body opens
a session at a URL, the page stays alive, the agent issues one or more action
calls against the session, and eventually the agent closes the session. The
relationship to the page is qualitatively different — *visit* becomes
*presence*. This is a NEW DISPOSITION; the Skald codename is *Innan Hurðar*.

| Field            | Value                                                                |
|------------------|----------------------------------------------------------------------|
| Sub-disposition  | *Innan Hurðar* — "inside the door"                                   |
| Tools            | `leid.open_session`, `leid.session_status`, `leid.click`, `leid.close_session` |
| Module           | `heretic.skilningr.senses.leid.playwright_client` (new methods on `PlaywrightLeidClient`) + `heretic.skilningr.senses.leid.session_manager` (new) |
| New class        | `BrowserSessionManager` — owns the open sessions, enforces cap + lazy eviction |
| Lifecycle        | Launch-per-SESSION (NEW; distinct from launch-per-call of `render_url` / `screenshot`) |

### 12.2 New B-Invariants (additive over B-1..B-11)

| #    | B-Invariant |
|------|-----------|
| B-12 | `_validate_url()` is called at the start of `open_session()` BEFORE `async_playwright().start()`. A rejected URL never causes a session to be created or a browser process to spawn. |
| B-13 | `open_session()` checks `len(manager._sessions) < config.browser_max_concurrent_sessions` BEFORE attempting to launch. If at cap, raise `LeidSessionLimitError → SENSE_UNAVAILABLE`. **No silent eviction of existing sessions** — the agent's mental model of which sessions are alive remains correct. |
| B-14 | Each open session uses its OWN `pw`, `browser`, `context`, `page` quartet. No sharing of resources between sessions — each session can be torn down independently without affecting others. |
| B-15 | `_evict_expired_sessions()` is called at the START of `open_session()`, `session_status()`, `click()`, and `close_session()`. Eviction uses the same cleanup ordering as `close_session()`: context → browser → pw, each defensively wrapped. **Lazy** — no background task; correctness is operator-perceivable. |
| B-16 | A `session_id` whose session has been evicted (or never existed) raises `LeidSessionExpiredError → SENSE_UNAVAILABLE` from any tool that references it (status, click, future type/navigate). **`close_session` is the exception** — it returns `{closed: false}` idempotently for an unknown session_id (allows the agent to safely re-issue close). |
| B-17 | After every successful session-affecting tool call (`status`, `click`, future `type`/`navigate`), `session.last_activity_at` is updated to the current monotonic time. Idle eviction is therefore relative to *real activity*, not just to `open_session` time. |
| B-18 | `close_session()` is idempotent: closing an already-closed or never-existed session_id returns `{closed: false}` and does NOT raise. Closing an active session removes it from the manager dict BEFORE any cleanup begins (so a concurrent eviction sweep cannot double-clean), then runs cleanup, then returns `{closed: true}`. |

B-1..B-11 continue to govern `render_url` and `screenshot` unchanged. B-3 (no
cookies persist between calls) is **strengthened at the session boundary**:
cookies persist *within* a session (that is what a session is), but each
session's context is still fresh, and `close_session` discards all of them.

### 12.3 Audit M-1 closure (deferred from v0.8.1)

This milestone closes Auditor M-1 from `AUDIT_v0.8.1_MYND_AF_VEGFERD.md`.
Three additional `Page.*` call sites gain explicit exception typing:

| Call site                         | Method context  | Exception class on PlaywrightError | Exception class on PlaywrightTimeoutError |
|-----------------------------------|-----------------|------------------------------------|-------------------------------------------|
| `await page.content()`            | `render_url()`  | `LeidConnectionError`              | (not raised here in practice)             |
| `await page.screenshot()`         | `screenshot()`  | `LeidConnectionError`              | (not raised here in practice)             |
| `await locator.click()`           | `click()`       | `LeidConnectionError`              | `LeidClickElementNotFoundError`           |

The fourth `Page.*` site (`page.goto`) was already correctly typed in v0.8.0;
unchanged here. All four network-level browser failures now surface to the
agent with the same precision httpx failures already had.

### 12.4 Success response shapes

#### `leid.open_session`
```json
{
  "session_id": "leid-3f7c1b2e8a4d4f6e9b8c0d1e2f3a4b5c",
  "final_url": "https://example.com/dashboard",
  "title": "Example Dashboard"
}
```

#### `leid.session_status`
```json
{
  "state": "alive",
  "url": "https://example.com/dashboard",
  "title": "Example Dashboard",
  "opened_at": 1715379600.123,
  "last_activity_at": 1715379650.456,
  "age_seconds": 50.3,
  "idle_seconds": 0.0
}
```

`opened_at` and `last_activity_at` are monotonic-clock floats (`time.monotonic()`); `age_seconds` and `idle_seconds` are computed at call time relative to those.

#### `leid.click`
```json
{
  "selector": "button.submit",
  "clicked": true,
  "current_url": "https://example.com/dashboard/result",
  "current_title": "Result page"
}
```

`current_title` is `null` if the title read failed defensively (D-49).

#### `leid.close_session`
```json
{
  "session_id": "leid-3f7c1b2e8a4d4f6e9b8c0d1e2f3a4b5c",
  "closed": true
}
```

`closed: false` for an unknown / already-closed / evicted session_id (B-18 idempotency).

### 12.5 Out of scope at v0.8.2

| Capability                  | Status            |
|-----------------------------|-------------------|
| `leid.type` (form input)    | v0.8.2.1          |
| `leid.navigate` (in-session)| v0.8.2.2          |
| `leid.query` (CSS query)    | v0.8.3            |
| `leid.session_render` (re-extract HTML in session) | v0.8.x |
| `leid.session_screenshot`   | v0.8.x            |
| Multi-tab support           | v0.8.x+           |
| Wait-for-selector, wait-for-event | v0.8.x      |
| Cookie persistence across sessions | NEVER (B-3) |
| Session survival across operator restarts | NEVER (D-27 — process-local) |

### 12.6 Forge implementation contract

- `BrowserSessionManager` lives in a new module: `heretic.skilningr.senses.leid.session_manager`. It owns the dict `_sessions: dict[str, _LeidSession]`, an `asyncio.Lock` for mutations (D-35), and the eviction logic.
- `_LeidSession` is a private dataclass with: `session_id`, `pw`, `browser`, `context`, `page`, `created_at`, `last_activity_at`. Used internally only.
- `PlaywrightLeidClient` gains a private `_session_manager: BrowserSessionManager | None = None` attribute, lazily created on first session-tool call. The manager binds to the client's config.
- The four new methods (`open_session`, `session_status`, `click`, `close_session`) live as siblings of `render_url` and `screenshot` on `PlaywrightLeidClient`.
- Session ID format: `f"leid-{uuid.uuid4().hex}"` (D-26).
- Eviction triggers: `_session_manager._evict_expired_sessions()` is called at the start of every new method (D-31, B-15).
- `close_session` removes from dict BEFORE cleanup (B-18) so a concurrent eviction sweep cannot double-clean.
- Cleanup ordering on close + eviction: `context.close()` → `browser.close()` → `pw.stop()`, each defensively wrapped (same shape as render_url's `finally`).
- M-1 closure: 1-line `try/except (PlaywrightError, PlaywrightTimeoutError)` wraps added around `await page.content()` (in render_url) and `await page.screenshot()` (in screenshot), mapping to `LeidConnectionError`. The v0.8.0 `render_url()` and v0.8.1 `screenshot()` BEHAVIOR is preserved (same exception-class outputs); only the error TYPING becomes explicit.
- Tests live in `tests/test_leid_session_manager.py` (BrowserSessionManager unit tests) and `tests/test_leid_playwright_client.py::TestSession*` / `TestClick` (integration tests).

### 12.7 Type extension (v0.8.2.1 — unnamed within Innan Hurðar)

> **Added 2026-05-10 v0.8.2.1.** Adds `leid.type` as the second half of the
> interactive gesture begun with click. Unnamed extension — no new
> disposition, just the complementary tool the existing disposition
> implied. Same session, same locator pattern, same timeout discipline.

**New tool:** `leid.type(session_id, selector, text)` → `{selector, typed,
current_url, current_title}`.

**New B-Invariant:**

| #    | B-Invariant |
|------|-----------|
| B-19 | `type()` enforces the same session/cap/timeout discipline as `click()`: `evict_expired_sessions` runs first; unknown session_id raises `LeidSessionExpiredError`; `locator.fill` timeout maps to `LeidTypeElementNotFoundError` (D-55, sibling of B-relevant click class); other PlaywrightError maps to `LeidConnectionError`; on success, `session.last_activity_at` is updated. |

**New error class:** `LeidTypeElementNotFoundError → INVALID_ARGUMENTS`. Sibling of `LeidClickElementNotFoundError`; agent can distinguish click vs type selector failures.

**Implementation primitive:** `await session.page.locator(selector).first.fill(text, timeout=config.browser_click_timeout_seconds * 1000)`. Reuses the click timeout config field (D-54) — type and click are both fast interactive actions sharing the same operator-controlled bound. `locator.fill()` (not `type()`) is the canonical "set this field's value" Playwright primitive: it waits for actionability, focuses the element, clears existing value, sets the new value, and dispatches the `input` event. Keystroke-by-keystroke simulation is deferred to v0.8.x.

**Success response shape:**

```json
{
  "selector": "input[name='email']",
  "typed": true,
  "current_url": "https://example.com/login",
  "current_title": "Login"
}
```

**Out of scope at v0.8.2.1:**

| Capability                  | Status            |
|-----------------------------|-------------------|
| Keystroke simulation (page.type with delay) | v0.8.x — separate primitive for legacy JS frameworks |
| Special keys (Enter, Tab, Escape) | v0.8.x — separate `leid.press` primitive |
| Form submission             | not needed — agent uses `leid.click('button[type=submit]')` |
| Multi-element fill          | v0.8.x — current `.first.fill` is intentional D-56 |

### 12.8 Navigate extension (v0.8.2.2 — unnamed within Innan Hurðar)

> **Added 2026-05-10 v0.8.2.2.** Adds `leid.navigate` for in-session URL
> changes. Reuses the existing browser quartet (no new launch). Cookies +
> localStorage persist across navigation (D-63 — that's what a session
> IS). No new error classes (D-66 reuses existing ones).

**New tool:** `leid.navigate(session_id, url)` → `{session_id, previous_url, final_url, title}`.

**New B-Invariant:**

| #    | B-Invariant |
|------|-----------|
| B-20 | `navigate()` enforces the same URL-gate-then-session-resolve discipline as the rest of Innan Hurðar: `_validate_url` runs FIRST (B-12); then `evict_expired_sessions` (B-15); then `get_session` (B-16); then `page.goto` with the open_session navigation contract (B-5 timeout); on success, `session.last_activity_at` is updated (B-17); the session_id is unchanged (D-62). The session's cookie/localStorage state PERSISTS across the navigation (D-63 — that is what a session is). On navigation failure, the session is NOT closed — it stays open with whatever URL it had, ready for retry or different navigate. |

**Implementation primitive:** `await session.page.goto(url, wait_until=config.browser_load_state, timeout=config.browser_navigation_timeout_seconds * 1000)`. Reuses the same Playwright primitive as `open_session`'s navigation phase, on the EXISTING page rather than a freshly-created one.

**Success response shape:**

```json
{
  "session_id": "leid-3f7c1b2e8a4d4f6e9b8c0d1e2f3a4b5c",
  "previous_url": "https://example.com/login",
  "final_url": "https://example.com/dashboard",
  "title": "Dashboard"
}
```

`previous_url` is captured BEFORE the new goto so the agent has a coherent record of the navigation transition (D-64).

**Failure-mode reuse:** No new error classes. Maps identically to open_session's navigation phase:

| Condition                                        | Error class                | SENSE_CONTRACTS code      |
|--------------------------------------------------|----------------------------|---------------------------|
| URL not in allowlist (B-12)                      | `UrlNotAllowedError`       | `PERMISSION_DENIED`       |
| Unknown / evicted session_id (B-16)              | `LeidSessionExpiredError`  | `SENSE_UNAVAILABLE`       |
| Navigation timeout (B-5 inherited)               | `LeidTimeoutError`         | `SENSE_TIMEOUT`           |
| Navigation HTTP 4xx/5xx                          | `LeidHttpError`            | `SENSE_INTERNAL_ERROR`    |
| Navigation network error                          | `LeidConnectionError`      | `EXTERNAL_APP_UNAVAILABLE`|

**Distinct from open_session navigation phase:** `open_session` failure cleans up the just-launched browser quartet (because the session is not yet registered). `navigate` failure does NOT close the existing session — it stays open with whatever URL it had before the failed goto, ready for the agent to retry or try a different navigate. This is intentional: agents should not lose their entire session state because of a single failed navigation.

**Out of scope at v0.8.2.2:**

| Capability                  | Status            |
|-----------------------------|-------------------|
| `leid.go_back` / `go_forward` | v0.8.x — browser history navigation, distinct primitive |
| `leid.reload`               | v0.8.x — distinct primitive |
| Final-URL allowlist re-check after redirect | v0.8.x — pre-existing concern across all browser tools; v0.8.2.2 mirrors current behaviour |

### 12.9 Query extension (v0.8.3 — unnamed within Innan Hurðar)

> **Added 2026-05-10 v0.8.3.** Adds `leid.query` — the read-only sibling of
> click and type. Returns text or attribute of first matching element +
> total match count. **Deliberate error-semantic divergence**: not finding
> a match is NOT an error (D-72 / B-21). No new error classes (D-79).

**New tool:** `leid.query(session_id, selector, attribute="")` → `{session_id, selector, attribute, found, value, count}`.

**New B-Invariant:**

| #    | B-Invariant |
|------|-----------|
| B-21 | `query()` enforces the same session/timeout discipline as the rest of Innan Hurðar: `evict_expired_sessions` runs first; unknown session_id raises `LeidSessionExpiredError`; `locator.count()` and (if non-zero) `text_content()` / `get_attribute()` calls bounded by `browser_click_timeout_seconds`; on success, `session.last_activity_at` is updated. **DIVERGENCE from B-19 / D-43**: a selector matching no elements is NOT a failure — `query` returns `{found: false, count: 0, value: null}` because read operations must support "looking to see if X exists." |

**Implementation primitive:** `await session.page.locator(selector).count()` (always); then `await session.page.locator(selector).first.text_content(timeout=...)` OR `await session.page.locator(selector).first.get_attribute(attribute, timeout=...)` (only when `count > 0`). Reuses the click timeout config field (D-75).

**Success response shape:**

```json
{
  "session_id": "leid-3f7c1b2e8a4d4f6e9b8c0d1e2f3a4b5c",
  "selector": "h1.title",
  "attribute": "",
  "found": true,
  "value": "Welcome to the Dashboard",
  "count": 1
}
```

**Not-found response shape (NOT an error — agent receives a successful tool result):**

```json
{
  "session_id": "leid-3f7c1b2e8a4d4f6e9b8c0d1e2f3a4b5c",
  "selector": ".error-banner",
  "attribute": "",
  "found": false,
  "value": null,
  "count": 0
}
```

**Found-but-attribute-missing response shape (D-73 — useful diagnostic):**

```json
{
  "session_id": "leid-3f7c1b2e8a4d4f6e9b8c0d1e2f3a4b5c",
  "selector": "img.logo",
  "attribute": "data-tracking-id",
  "found": true,
  "value": null,
  "count": 1
}
```

The agent can distinguish "no element" (`found: false`, `count: 0`) from "element exists but attribute absent" (`found: true`, `value: null`). Likewise, `text_content()` returning None for an element with no text passes through as JSON null with `found: true`.

**Why "not found" is not an error (D-72 design rationale):**

Click and type are MUTATING actions — the agent expects them to succeed; a selector that matches nothing is a real failure that needs reporting. Query is a READ — the agent often calls it precisely to determine whether something is on the page (e.g., `query(session, ".alert-error")` to detect an error message; the success case is "no error message present"). Forcing exception handling on the success case would invert the semantics. So:

| Tool      | Selector matched nothing → |
|-----------|------------------|
| click     | `LeidClickElementNotFoundError → INVALID_ARGUMENTS` (B-19) |
| type      | `LeidTypeElementNotFoundError → INVALID_ARGUMENTS` (B-19) |
| **query** | **`{found: false, count: 0, value: null}` (D-72 / B-21)** |

**Failure-mode reuse:** No new error classes. The two genuine failure modes:

| Condition                                        | Error class                | SENSE_CONTRACTS code      |
|--------------------------------------------------|----------------------------|---------------------------|
| Unknown / evicted session_id (B-16)              | `LeidSessionExpiredError`  | `SENSE_UNAVAILABLE`       |
| Browser failure (page closed, process disconnect) | `LeidConnectionError`      | `EXTERNAL_APP_UNAVAILABLE`|

**Out of scope at v0.8.3:**

| Capability                  | Status            |
|-----------------------------|-------------------|
| Multi-element extraction (returning all matches as a list) | v0.8.x — first-match keeps shape consistent with click/type |
| XPath selectors             | v0.8.x — Playwright supports XPath; CSS suffices for v0.8.3 |
| Inner HTML extraction       | v0.8.x — text_content covers most needs; raw HTML is a different primitive |
| Element bounding-box / position | v0.8.x — geometric inspection is a separate concern |
| Visibility check            | v0.8.x — `found` conveys DOM presence; visibility is a refinement |

### 12.10 Press extension (v0.8.4 — unnamed within Innan Hurðar)

> **Added 2026-05-10 v0.8.4.** Adds `leid.press` — page-level keyboard key
> dispatch through Playwright's `page.keyboard.press()`. The body's
> keyboard finger; the canonical "press Enter to submit" or "press Escape
> to dismiss" primitive. No new error classes (D-84). No new config
> fields (D-83 reuses click timeout). One new B-invariant (B-22).

**New tool:** `leid.press(session_id, key)` → `{session_id, key, pressed, current_url, current_title}`.

**New B-Invariant:**

| #    | B-Invariant |
|------|-----------|
| B-22 | `press()` enforces the same session/activity discipline as the rest of Innan Hurðar interactive tools: `evict_expired_sessions` runs first; unknown session_id raises `LeidSessionExpiredError`; `page.keyboard.press(key)` is awaited (Playwright applies its own default action timeout — keyboard.press does not accept a per-call timeout); on success, `session.last_activity_at` is updated. |

**Implementation primitive:** `await session.page.keyboard.press(key)`. Page-level (D-80) — dispatches to whatever element currently has focus. Typical agent flow: `leid.click(selector)` or `leid.type(selector, text)` first to establish focus, then `leid.press("Enter")`.

**Key syntax (D-81):** Playwright's native syntax. Examples:
- Single keys: `"Enter"`, `"Tab"`, `"Escape"`, `"ArrowDown"`, `"a"`, `"F5"`, `"PageDown"`, `" "` (space)
- Modifier combinations: `"Control+A"`, `"Shift+Tab"`, `"Meta+S"`, `"Alt+F4"`

HERETIC does not validate the key string. Playwright dispatches as best it can; unrecognized keys produce no event but do NOT raise.

**Success response shape:**

```json
{
  "session_id": "leid-3f7c1b2e8a4d4f6e9b8c0d1e2f3a4b5c",
  "key": "Enter",
  "pressed": true,
  "current_url": "https://example.com/results?q=norse",
  "current_title": "Search Results"
}
```

`current_url` may differ from the pre-press URL when the press triggers navigation (e.g., Enter submitted a form).

**Failure-mode reuse:** No new error classes. The two genuine failure modes:

| Condition                                        | Error class                | SENSE_CONTRACTS code      |
|--------------------------------------------------|----------------------------|---------------------------|
| Unknown / evicted session_id (B-16)              | `LeidSessionExpiredError`  | `SENSE_UNAVAILABLE`       |
| Browser failure (page closed, process disconnect) | `LeidConnectionError`      | `EXTERNAL_APP_UNAVAILABLE`|

**Why no LeidPressKeyInvalidError?** Playwright accepts arbitrary key strings. Unrecognized keys produce no event — `pressed: true` is returned because the API call itself succeeded; the agent can verify the press had its intended effect by querying the page state afterward (via `leid.query` or `leid.session_status`). This matches Playwright's own permissive design.

**Out of scope at v0.8.4:**

| Capability                  | Status            |
|-----------------------------|-------------------|
| Element-targeted press (`locator.press`) | v0.8.x — agent achieves this via click(selector) then press(key); explicit element-press is a refinement |
| Text input via per-key sequences | v0.8.x — `leid.type` covers text via locator.fill |
| Mouse events (hover, double-click, drag) | v0.8.x — distinct primitives |
| Held keys / down-up sequences | v0.8.x — Playwright's `keyboard.down`/`up` primitives, distinct contract |

### 12.11 History navigation extension (v0.8.5 — paired tools, unnamed within Innan Hurðar)

> **Added 2026-05-10 v0.8.5.** Adds `leid.go_back` and `leid.go_forward`
> as a paired bundle — they share identical structure and one private
> helper. Browser history navigation through Playwright's `page.go_back`
> / `page.go_forward`. **Deliberate divergence**: "no history in this
> direction" returns `moved: false` rather than raising (D-89, same
> posture as v0.8.3 query's not-found). No new error classes (D-93). No
> new config fields (D-91 reuses navigation timeout).

**New tools (paired):**
- `leid.go_back(session_id)` → `{session_id, moved, previous_url, current_url, title}`
- `leid.go_forward(session_id)` → `{session_id, moved, previous_url, current_url, title}`

Both share identical contract; only the underlying Playwright primitive differs.

**New B-Invariant (covers both tools):**

| #    | B-Invariant |
|------|-----------|
| B-23 | `go_back()` and `go_forward()` enforce the same session/timeout discipline as `navigate()`: `evict_expired_sessions` runs first; unknown session_id raises `LeidSessionExpiredError`; `page.go_back()` / `page.go_forward()` is awaited with `wait_until=config.browser_load_state` and `timeout=config.browser_navigation_timeout_seconds * 1000`; on success (whether `moved: true` or `moved: false`), `session.last_activity_at` is updated. **DIVERGENCE from B-20**: when Playwright returns `None` (no history in that direction), the tool returns `{moved: false}` rather than raising — history nav is a probe-and-act primitive. Inheritance: HTTP 4xx/5xx during history navigation maps to `LeidHttpError`; navigation timeout maps to `LeidTimeoutError`; network error maps to `LeidConnectionError`. Cookies + localStorage persist across history nav (same as navigate). |

**Implementation primitive:** `await session.page.go_back(wait_until=..., timeout=...)` and `await session.page.go_forward(wait_until=..., timeout=...)`. Both return `Response | None` — None means no history entry exists in that direction.

**Success response shape (when moved):**

```json
{
  "session_id": "leid-3f7c1b2e8a4d4f6e9b8c0d1e2f3a4b5c",
  "moved": true,
  "previous_url": "https://example.com/dashboard",
  "current_url": "https://example.com/login",
  "title": "Login"
}
```

**Successful "no history" shape (NOT an error):**

```json
{
  "session_id": "leid-3f7c1b2e8a4d4f6e9b8c0d1e2f3a4b5c",
  "moved": false,
  "previous_url": "https://example.com/login",
  "current_url": "https://example.com/login",
  "title": "Login"
}
```

`previous_url == current_url` when `moved: false` because the page didn't actually move — the browser had nothing to go back/forward to. The agent can write `if not result["moved"]:` to detect this case.

**Why "no history" is not an error (D-89 design rationale):**

Same rationale as v0.8.3 query's D-72. History navigation is a probe-and-act primitive — the agent's natural intent is "go back if there's something to go back to." Failing loudly when the body is at the start of its session's history would be the wrong shape: the body is doing exactly what it was asked to do (go back as far as possible — which is zero steps). For comparison:

| Tool      | Probe-vs-action | "Nothing to act on" → |
|-----------|-----------------|------------------|
| navigate  | directed action | (n/a — agent supplies URL) |
| click     | directed action | `LeidClickElementNotFoundError → INVALID_ARGUMENTS` |
| type      | directed action | `LeidTypeElementNotFoundError → INVALID_ARGUMENTS` |
| **query** | **probe-and-act** | **`{found: false, count: 0, value: null}`** |
| **go_back / go_forward** | **probe-and-act** | **`{moved: false, ...}`** |

**URL allowlist gate (D-92 — accepted limitation):** History nav does NOT re-validate URLs against the allowlist. The URLs in the history stack were already allowlist-checked when the body originally navigated to them. Re-checking would require a post-hoc check (after the page has already moved), which introduces unwind problems. This is consistent with the pre-existing "final-URL allowlist re-check after redirect" gap that applies to all browser tools and is already deferred. v0.8.5 does NOT widen the gap; it inherits the existing posture.

**Failure-mode reuse:** No new error classes. Same mapping as `navigate`:

| Condition                                        | Error class                | SENSE_CONTRACTS code      |
|--------------------------------------------------|----------------------------|---------------------------|
| Unknown / evicted session_id (B-16)              | `LeidSessionExpiredError`  | `SENSE_UNAVAILABLE`       |
| Navigation timeout (B-5 inherited)               | `LeidTimeoutError`         | `SENSE_TIMEOUT`           |
| Navigation HTTP 4xx/5xx                          | `LeidHttpError`            | `SENSE_INTERNAL_ERROR`    |
| Navigation network error                          | `LeidConnectionError`      | `EXTERNAL_APP_UNAVAILABLE`|

**Out of scope at v0.8.5:**

| Capability                  | Status            |
|-----------------------------|-------------------|
| `leid.reload`               | v0.8.x — distinct primitive (page.reload); separate slice if needed |
| Multi-step go_back (e.g., go back 3 entries) | v0.8.x — agent-side iteration |
| History-stack length introspection | v0.8.x — Playwright doesn't easily expose this without page.evaluate (which violates B-10) |
| Final-URL allowlist re-check after history navigation | v0.8.x — pre-existing concern across all browser tools (D-92) |

### 12.12 Mid-session re-extract pair (v0.8.6 — paired tools, unnamed within Innan Hurðar)

> **Added 2026-05-11 v0.8.6.** Adds `leid.session_render` and
> `leid.session_screenshot` as a paired bundle — the in-session
> counterparts of v0.8.0's `leid.render_url` and v0.8.1's
> `leid.screenshot`. Same primitives (`page.content()` /
> `page.screenshot()`); same size-cap discipline (B-6 inherited /
> B-11 inherited); same M-1 closure pattern. Applied to a live
> session page rather than a freshly-launched one. **No new error
> classes** (D-103). **No new config fields** (D-102 — reuses
> max_response_bytes, browser_screenshot_full_page).

**New tools (paired):**
- `leid.session_render(session_id)` → `{session_id, current_url, text, title, source_size_bytes}`
- `leid.session_screenshot(session_id)` → `{session_id, current_url, image_base64, image_format, size_bytes, full_page}`

**New B-Invariant (covers both tools):**

| #    | B-Invariant |
|------|-----------|
| B-24 | `session_render()` and `session_screenshot()` enforce the same session/timeout discipline as the rest of Innan Hurðar interactive tools: `evict_expired_sessions` runs first; unknown session_id raises `LeidSessionExpiredError`; the underlying Playwright primitive (`page.content()` for session_render; `page.screenshot()` for session_screenshot) is wrapped with `try/except (PlaywrightError, PlaywrightTimeoutError) → LeidConnectionError` (D-100 — M-1 closure inheritance); the existing size caps from B-6 (rendered HTML byte size) and B-11 (raw PNG bytes before base64) apply unchanged; on success, `session.last_activity_at` is updated. |

**Implementation primitives:**
- `session_render`: `await session.page.content()` then `_extract_text_from_html(html)` (the same helper used by v0.8.0's `extract_text` and `render_url`).
- `session_screenshot`: `await session.page.screenshot(full_page=config.browser_screenshot_full_page, type="png")`, then `base64.b64encode(png_bytes).decode("ascii")`.

Both reuse the established Playwright primitives and helpers. No new helpers introduced.

**Success response shapes:**

`leid.session_render`:
```json
{
  "session_id": "leid-3f7c1b2e8a4d4f6e9b8c0d1e2f3a4b5c",
  "current_url": "https://example.com/dashboard",
  "text": "Welcome back. Your last login was at 14:32.",
  "title": "Dashboard",
  "source_size_bytes": 24576
}
```

`leid.session_screenshot`:
```json
{
  "session_id": "leid-3f7c1b2e8a4d4f6e9b8c0d1e2f3a4b5c",
  "current_url": "https://example.com/dashboard",
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "image_format": "png",
  "size_bytes": 45678,
  "full_page": true
}
```

`current_url` is captured at entry — reflects whatever page the session is on after any prior click / type / press / navigate / history-step. There is no separate `url` and `final_url` because, unlike `render_url` and `screenshot`, no input URL is supplied — the agent is asking about the current state, not about a navigation.

**Why these tools are needed (use cases):**
- After `leid.click(session, "button.submit")` triggers a single-page-app state change, `leid.session_render(session)` returns the post-click text without close+re-open
- After `leid.type` + `leid.press("Enter")` submits a search, `leid.session_screenshot(session)` captures the rendered results
- Periodic mid-flow re-extraction for "verify state after each step" agent loops
- SPAs where URL doesn't change but DOM does

**Cost vs stateless siblings:**

| Tool | Cost | Lifecycle |
|---|---|---|
| `leid.render_url` (v0.8.0) | ~500-3000 ms | launch+goto+content+teardown |
| `leid.session_render` (v0.8.6) | ~20-100 ms | content only (reuses session) |
| `leid.screenshot` (v0.8.1) | ~500-3000 ms | launch+goto+screenshot+teardown |
| `leid.session_screenshot` (v0.8.6) | ~50-300 ms | screenshot only (reuses session) |

Mid-session tools are 10-50x cheaper than their stateless siblings because they skip browser cold-start.

**Failure-mode reuse:** No new error classes.

| Condition                                        | Error class                | SENSE_CONTRACTS code      |
|--------------------------------------------------|----------------------------|---------------------------|
| Unknown / evicted session_id (B-16)              | `LeidSessionExpiredError`  | `SENSE_UNAVAILABLE`       |
| Browser failure (page closed, process disconnect) | `LeidConnectionError`      | `EXTERNAL_APP_UNAVAILABLE`|
| Rendered HTML > max_response_bytes (B-6 inherited) | `LeidResponseTooLargeError` | `INVALID_ARGUMENTS`     |
| Raw PNG bytes > max_response_bytes (B-11 inherited) | `LeidResponseTooLargeError` | `INVALID_ARGUMENTS`    |

**Out of scope at v0.8.6:**

| Capability                  | Status            |
|-----------------------------|-------------------|
| Element-scoped screenshot (`locator.screenshot`) | v0.8.x — distinct primitive |
| Inner HTML re-extraction (raw HTML, not stripped to text) | v0.8.x |
| Mid-session JPEG/WebP screenshot output | v0.8.x — PNG-only matches v0.8.1's posture |
| Mid-session viewport reconfiguration | v0.8.x — inherits the session's launch-time viewport |

### 12.13 Reload extension (v0.8.7 — unnamed within Innan Hurðar)

> **Added 2026-05-11 v0.8.7.** Adds `leid.reload` — refresh the current
> page of an open session through Playwright's `page.reload()`. Rounds
> out the motion vocabulary inside the door: navigate (forward to URL),
> go_back (history step back), go_forward (history step forward),
> reload (in place). No new error classes (D-110). No new config fields
> (D-108 reuses navigation timeout + load_state).

**New tool:** `leid.reload(session_id)` → `{session_id, current_url, title}`.

**New B-Invariant:**

| #    | B-Invariant |
|------|-----------|
| B-25 | `reload()` enforces the same session/timeout discipline as `navigate()` and history-nav: `evict_expired_sessions` runs first; unknown session_id raises `LeidSessionExpiredError`; `page.reload()` is awaited with `wait_until=config.browser_load_state` and `timeout=config.browser_navigation_timeout_seconds * 1000`; HTTP 4xx/5xx during reload maps to `LeidHttpError`; on success, `session.last_activity_at` is updated. Cookies + localStorage persist across reload — that's intrinsic to refresh semantics, not a new invariant. |

**Implementation primitive:** `await session.page.reload(wait_until=config.browser_load_state, timeout=config.browser_navigation_timeout_seconds * 1000)`. Returns `Response | None` — None in unusual cases (data: URLs that cannot be reloaded), treated as "no HTTP status to check" (same posture as navigate when response is None).

**Success response shape:**

```json
{
  "session_id": "leid-3f7c1b2e8a4d4f6e9b8c0d1e2f3a4b5c",
  "current_url": "https://example.com/dashboard",
  "title": "Dashboard"
}
```

Minimal shape (D-111). No `previous_url` because reload is in-place — previous and current URL are conceptually the same. No `moved` boolean because reload is not a probe-and-act primitive — either it succeeded or it failed.

**Failure-mode reuse:** No new error classes. Same mapping as `navigate`:

| Condition                                        | Error class                | SENSE_CONTRACTS code      |
|--------------------------------------------------|----------------------------|---------------------------|
| Unknown / evicted session_id (B-16)              | `LeidSessionExpiredError`  | `SENSE_UNAVAILABLE`       |
| Reload timeout (B-5 inherited)                   | `LeidTimeoutError`         | `SENSE_TIMEOUT`           |
| Reload HTTP 4xx/5xx                               | `LeidHttpError`            | `SENSE_INTERNAL_ERROR`    |
| Reload network error                              | `LeidConnectionError`      | `EXTERNAL_APP_UNAVAILABLE`|

**Why no URL allowlist re-check on reload:** D-109 — same posture as go_back/go_forward (D-92). The URL the body is at was already allowlist-checked when first navigated to. Reload is in-place — the URL doesn't change. This inherits the existing pre-existing-concern about final-URL allowlist re-check after redirect.

**Out of scope at v0.8.7:**

| Capability                  | Status            |
|-----------------------------|-------------------|
| Hard reload (skip cache) | v0.8.x — Playwright's reload accepts no `bypass_cache`; agent achieves this via `keyboard.press("Control+Shift+R")` instead |
| Reload-and-extract combined | v0.8.x — agent does `reload()` then `session_render()` |
| Final-URL allowlist re-check | v0.8.x — pre-existing concern across all browser tools |

### 12.14 Multi-element query extension (v0.8.8 — unnamed within Innan Hurðar)

> **Added 2026-05-11 v0.8.8.** Adds `leid.query_all` — multi-element
> follow-up to v0.8.3 single-match `query`. Returns ALL matches as a
> list (in DOM order) up to a new cardinality cap. Same probe-and-act
> posture as query: empty result is NOT an error. **First new
> LeidConfig field since v0.8.2** (`browser_query_max_matches`,
> default 100). No new error classes (D-123).

**New tool:** `leid.query_all(session_id, selector, attribute="")` → `{session_id, selector, attribute, count, values}`.

**New B-Invariant:**

| #    | B-Invariant |
|------|-----------|
| B-26 | `query_all()` enforces the same session/timeout discipline as `query()`: `evict_expired_sessions` runs first; unknown session_id raises `LeidSessionExpiredError`; `locator.count()` then `locator.nth(i).text_content()` / `.get_attribute()` (per i in 0..count) calls bounded by `browser_click_timeout_seconds`; on success, `session.last_activity_at` is updated. **NEW**: cardinality cap — when `count > config.browser_query_max_matches`, `LeidResponseTooLargeError` is raised BEFORE iteration. **DIVERGENCE inherited from B-21**: empty result (count=0) is NOT an error — returns `{count: 0, values: []}`. |

**Implementation primitive:** `await session.page.locator(selector).count()` always; then `await session.page.locator(selector).nth(i).text_content(timeout=...)` OR `.get_attribute(attribute, timeout=...)` for each `i in range(count)` (only when `0 < count <= browser_query_max_matches`). Reuses the click timeout (D-122).

**New config field:**

| Field                        | Type | Default | Meaning |
|------------------------------|------|---------|---------|
| `browser_query_max_matches`  | int  | 100     | Cardinality cap on `query_all`. Selectors matching more raise `LeidResponseTooLargeError`. Must be >= 1. |

**Success response shape (matches found):**

```json
{
  "session_id": "leid-3f7c1b2e8a4d4f6e9b8c0d1e2f3a4b5c",
  "selector": "article h2",
  "attribute": "",
  "count": 5,
  "values": [
    "First article title",
    "Second article title",
    "Third article title",
    "Fourth article title",
    "Fifth article title"
  ]
}
```

**Empty-result shape (NOT an error):**

```json
{
  "session_id": "leid-3f7c1b2e8a4d4f6e9b8c0d1e2f3a4b5c",
  "selector": ".error-message",
  "attribute": "",
  "count": 0,
  "values": []
}
```

`values` is always a list of length equal to `count`. Each element is a string OR `null` (None when the underlying `text_content()` or `get_attribute()` returned None — element exists but has no text or the requested attribute is absent).

**Cap-exceeded behaviour (D-116):**

```json
// LeidResponseTooLargeError → INVALID_ARGUMENTS
// "selector matched 542 elements, exceeds browser_query_max_matches=100; refine selector"
```

The cap fires BEFORE iteration begins — no partial work, no silent truncation. Honest feedback to the agent.

**Distinct from query:** `query` returns the FIRST match with `{found, value, count}`; `query_all` returns ALL matches (up to cap) with `{count, values}`. The agent picks based on intent:
- "Is there an error message?" → `query(".error-msg")` (binary check)
- "What's the first article title?" → `query("article h2")` (single read)
- "List all the article titles" → `query_all("article h2")` (enumeration)

**Failure-mode reuse:** No new error classes.

| Condition                                        | Error class                | SENSE_CONTRACTS code      |
|--------------------------------------------------|----------------------------|---------------------------|
| Unknown / evicted session_id (B-16)              | `LeidSessionExpiredError`  | `SENSE_UNAVAILABLE`       |
| count > browser_query_max_matches (B-26)         | `LeidResponseTooLargeError`| `INVALID_ARGUMENTS`       |
| Browser failure on count or extraction           | `LeidConnectionError`      | `EXTERNAL_APP_UNAVAILABLE`|

**Out of scope at v0.8.8:**

| Capability                  | Status            |
|-----------------------------|-------------------|
| Streaming/paginated query results | v0.8.x — cap-based bounding suffices |
| XPath multi-match           | v0.8.x — CSS suffices |
| Per-element bounding box    | v0.8.x — geometric inspection separate concern |
| Nested attribute reads (href + text in one call) | v0.8.x — agent calls twice |

### 12.15 Configurable viewport (v0.8.9 — unnamed within Innan Hurðar)

> **Added 2026-05-11 v0.8.9.** Operator-controlled viewport for all
> browser-mode tools. Adds two new `LeidConfig` fields
> (`browser_viewport_width`, `browser_viewport_height`) with defaults
> 1280×720 (matching Playwright's default — no behavior change for
> existing operators). Applied uniformly at three browser-context-
> creation sites (B-27): `render_url`, `screenshot`, `open_session`.
> Agent-facing tool surface unchanged. No new tools, no new error
> classes. **Not** a new tool — a behavior change to existing tools.

**New B-Invariant:**

| #    | B-Invariant |
|------|-----------|
| B-27 | Every `browser.new_context(...)` call within `PlaywrightLeidClient` (in `render_url`, `screenshot`, `open_session`) passes `viewport={"width": config.browser_viewport_width, "height": config.browser_viewport_height}`. Operator-controlled viewport propagates uniformly across all browser-context creations. Once a context is created, its viewport persists for the life of that browser context (mid-session viewport change is out of scope per D-130). |

**New config fields:**

| Field                          | Type | Default | Validation |
|--------------------------------|------|---------|------------|
| `browser_viewport_width`       | int  | 1280    | `> 0`      |
| `browser_viewport_height`      | int  | 720     | `> 0`      |

**Implementation:** each affected method's existing `browser.new_context(user_agent=config.user_agent)` call gains a `viewport={"width": config.browser_viewport_width, "height": config.browser_viewport_height}` kwarg. Same call shape; one new kwarg.

**Why operator-controlled, not agent-controlled (D-130):**

Agent-supplied viewport would let the agent ask for "show me this page at mobile width" — useful, but it would require the agent to reason about browser rendering details that are usually the operator's concern. Operator-controlled is the right scope: the operator picks the viewport their use case needs, and every agent using their HERETIC instance gets the same view.

Per-tool viewport override (e.g., screenshot at 1920 but session at 1280) is a candidate for v0.8.x if real use cases demand it.

**Why launch-time-only (D-130):**

Mid-session viewport change (`page.set_viewport_size`) is a distinct primitive and would need its own tool. v0.8.9 is launch-time only — the session's viewport is fixed at `open_session` and persists for the session's life. This matches the "viewport is operator infrastructure" principle: operators set it once, it stays set.

**Out of scope at v0.8.9:**

| Capability                  | Status            |
|-----------------------------|-------------------|
| Per-call viewport override (agent-supplied) | v0.8.x — would break agent-doesn't-manage-browser-internals abstraction |
| Device emulation presets (iPhone, iPad, etc.) | v0.8.x — distinct concern; would also include user_agent + touch settings |
| Mid-session viewport change | v0.8.x — `page.set_viewport_size`; distinct primitive |
| Per-tool viewport override (e.g., screenshot 1920, session 1280) | v0.8.x — complexity not justified for v0.8.9 |

### 12.16 Final-URL allowlist re-check (v0.8.10 — unnamed within Innan Hurðar)

> **Added 2026-05-11 v0.8.10.** Closes the long-deferred sandbox gap
> noted in every browser-tool audit since v0.6.2. Adds a
> post-navigation URL re-check at all 7 navigation-completing call
> sites (`render_url`, `screenshot`, `open_session`, `navigate`,
> `go_back`, `go_forward`, `reload`). **Stateful violations close
> the session** — the operator's allowlist is unconditional. NO new
> tools (D-145), NO new error classes (D-143 — reuses
> `UrlNotAllowedError`), NO new config fields (D-144).

**New B-Invariant:**

| #    | B-Invariant |
|------|-----------|
| B-28 | Every browser tool that completes a navigation re-checks `page.url` against `url_allowlist_patterns` and the HTTPS-only policy AFTER the navigation completes. If the final URL is NOT allowed, `UrlNotAllowedError` is raised. **For stateful tools that violate** (`navigate`, `go_back`, `go_forward`, `reload`): the session is closed (via `manager.close_session(session_id)`) BEFORE the raise. **For `open_session`**: the session is never registered (existing was_registered=False cleanup branch tears down the launched browser quartet). **For stateless tools** (`render_url`, `screenshot`): the existing `finally` cleanup handles teardown. |

**Implementation:** new private helper `_check_final_url_allowed(url)` on `PlaywrightLeidClient`. Reuses `sandbox.url_matches_allowlist` + the HTTPS-only policy logic from `_validate_url`. Same rules pre-flight and post-navigation; single source of truth.

**Failure handling — three patterns:**

| Tool category | Sites | What happens on violation |
|---|---|---|
| Stateless | `render_url`, `screenshot` | Raise `UrlNotAllowedError` — existing `finally` cleans up the launched browser quartet |
| Stateful (session not yet registered) | `open_session` | Raise `UrlNotAllowedError` — existing `was_registered=False` branch cleans up |
| Stateful (session already registered) | `navigate`, `go_back`, `go_forward`, `reload` | Call `manager.close_session(session_id)` to terminate the session, THEN raise `UrlNotAllowedError` |

**Why close the session on stateful violation (D-139):**

The session has landed on a not-allowlisted URL. The agent's next call (status, click, query, etc.) would operate on that page. The only safe response is to terminate the session.

Alternatives considered:
- **Leave session open**, rely on agent to call `close_session`. Rejected — the session is in a non-allowed state for as long as it lives; security must be enforced structurally, not advisedly.
- **Navigate the session BACK** to the previous URL. Rejected — the previous URL might also have led here through redirect; complex to reason about; brittle.

Chosen: close. Explicit, predictable, secure.

**Error message shape:**

For stateless tools:
> "Navigation to `<input_url>` resulted in `<final_url>`, which is not in url_allowlist_patterns."

For stateful tools (D-140):
> "Navigation to `<input_url>` on session `<session_id>` resulted in `<final_url>`, which is not in url_allowlist_patterns. The session has been closed."

**Closed concern:**

The deferred concern *"final-URL allowlist re-check after redirect — pre-existing concern across all browser tools"* — noted in the v0.8.5 audit (and in earlier audits implicitly via the deferred status of this gap) — is now CLOSED.

**Out of scope at v0.8.10:**

| Capability                  | Status            |
|-----------------------------|-------------------|
| Per-redirect URL re-check (intermediate URLs in chain) | v0.8.x — Playwright doesn't expose intermediate redirects without explicit request hooks; checking the FINAL URL catches the dangerous case |
| Per-tool toggle for the re-check | v0.8.x — sandbox security is unconditional; no opt-out |
| Detailed redirect chain in error message | v0.8.x — chain is invisible to us without request hooks |

### 12.17 JPEG/WebP screenshot output (v0.8.11 — unnamed within Innan Hurðar)

> **Added 2026-05-11 v0.8.11.** Operator-controlled screenshot format. Two new
> `LeidConfig` fields (`browser_screenshot_format`, `browser_screenshot_jpeg_quality`).
> Applied to both `screenshot` (stateless) and `session_screenshot` (stateful).
> Defaults preserve PNG behavior. NO new tools, NO new error classes (D-151).

**New B-Invariant:**

| # | B-Invariant |
|---|---|
| B-29 | `screenshot()` and `session_screenshot()` pass `type=config.browser_screenshot_format` to `page.screenshot()`. When format is `"jpeg"` or `"webp"`, `quality=config.browser_screenshot_jpeg_quality` is also passed; when format is `"png"`, `quality` is omitted (PNG is lossless). The `image_format` field in the return reflects the actual format used. |

**New config fields:**

| Field | Type | Default | Validation |
|---|---|---|---|
| `browser_screenshot_format` | str | `"png"` | one of `{"png", "jpeg", "webp"}` |
| `browser_screenshot_jpeg_quality` | int | `80` | 0..100 |

**Implementation pattern:**
```python
screenshot_kwargs = {"full_page": ..., "type": config.browser_screenshot_format}
if config.browser_screenshot_format != "png":
    screenshot_kwargs["quality"] = config.browser_screenshot_jpeg_quality
png_bytes = await page.screenshot(**screenshot_kwargs)
```

**Return shape:** `image_format` now reflects the actual format used (previously hardcoded `"png"`).

**Out of scope:**
- Per-call format override (agent-supplied) — operator-controlled is the right scope
- Per-tool format (screenshot=jpeg but session_screenshot=png) — complexity not justified
- Format auto-detection by content — out of scope
