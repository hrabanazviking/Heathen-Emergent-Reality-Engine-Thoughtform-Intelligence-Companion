# Leið Sense — Interface Contract

**Last updated:** 2026-05-10 (v0.8.1 *Mynd af Vegferð* screenshot addendum — Rúnhild Svartdóttir) | 2026-05-10 (v0.8.0 *Opið Vef* browser-render addendum) | 2026-05-09 (v0.7.1 *Straumr á Leið* streaming addendum) | 2026-05-08 (v0.6.2 scaffold)
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

### 4.2 Browser tools (added at v0.8.0+ — *Opið Vef*)

| Tool name          | Action                                          | Required params  | Optional params | Transport          | Added |
|--------------------|-------------------------------------------------|------------------|-----------------|--------------------|-------|
| `leid.render_url`  | Headless Chromium navigate + extract rendered text | `url` (string) | —               | Playwright (Chromium) | v0.8.0 |
| `leid.screenshot`  | Headless Chromium navigate + return base64 PNG of rendered page | `url` (string) | — | Playwright (Chromium) | v0.8.1 |

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
| Playwright not installed / chromium missing (v0.8.0 `leid.render_url` only) | `LeidPlaywrightUnavailableError` | `EXTERNAL_APP_UNAVAILABLE` |

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
