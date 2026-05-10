# TASK — HERETIC v0.8.0 OPIÐ VEF (Foundational Slice)

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-10** (immediately after v0.6.3.1 Persistent Verkminni shipped + audited + sealed at `d2de175`)
>
> **Codename (Skald to seal at Wave 1):** *Fyrsta Vegferð á Vefnum* — "the first journey on the web." The body has stood in front of the web before — through Leið's httpx eyes — but it has only ever read what was already written on the surface. Now, for the first time, the body steps onto the road, lets the page run its scripts, lets the world render itself in front of the body's eyes, and reads what the world chose to show.
>
> **Umbrella milestone (per ROADMAP.md):** v0.8 *Opið Vef* — "the open web." This task opens the milestone with its first vertical slice (`v0.8.0`). Subsequent slices (v0.8.1 screenshot, v0.8.2 click+type, v0.8.3 query) follow.
>
> **Mythic Engineering mode:** AUTONOMOUS. Volmarr asleep / hands-off. All six roles run on this single milestone within one session. Operator-side dependency (Playwright + Chromium runtime install) is documented but optional; the sense degrades gracefully when absent — the existing v0.7.1 httpx tools continue to work unchanged.

---

## 1. Task scope

Open the v0.8 *Opið Vef* milestone with the smallest cohesive vertical slice that proves the new sub-faculty:

> **One new tool — `leid.render_url(url)`** — a stateless tool that:
>   1. Validates `url` against the existing `url_allowlist_patterns` (same gate as `leid.fetch_url`).
>   2. Launches a headless Chromium subprocess via Playwright.
>   3. Navigates to the URL.
>   4. Waits for the configured load state (default `domcontentloaded`).
>   5. Extracts the rendered text content and `<title>` from the post-JS DOM.
>   6. Closes the browser.
>   7. Returns a dict with `{url, final_url, text, title, source_size_bytes}`.

This is the JS-rendered analog of `leid.extract_text` — same shape, different transport. **Stateless: each call launches and disposes its own browser.** Stateful browsing (persistent page, click, type, query) belongs to v0.8.1+ and is explicitly out of scope here.

The existing v0.7.1 streaming-httpx tools (`leid.fetch_url`, `leid.extract_text`) are **unchanged**. v0.8.0 is purely additive at the sense surface.

---

## 2. Out of scope (deferred to later v0.8.x slices)

| Tool                | Slice    | Reason for deferral                                 |
|---------------------|----------|-----------------------------------------------------|
| `leid.screenshot`   | v0.8.1   | Image-bytes return path needs its own design pass (base64? Sjón frame buffer? size cap?) |
| `leid.click`        | v0.8.2   | Requires stateful session model (persistent page, session ID, lifetime)              |
| `leid.type`         | v0.8.2   | Same stateful-session prerequisite                                                   |
| `leid.query`        | v0.8.3   | CSS selector + extract-attributes design pass                                        |
| Multi-tab support   | v0.8.x+  | Single-tab only at v0.8.0–v0.8.3                                                     |
| Cookie persistence  | NEVER    | Manifesto: cookies remain stateless; same as L-5 invariant for httpx                 |
| Browser-process restart on crash | v0.8.x | v0.8.0 is launch-per-call; persistent-process lifecycle is a v0.8.2 concern  |
| Domain-distinct allow-list | v0.8.x | Reuses the existing URL allowlist for v0.8.0; refinement (allow http vs render) deferred |

---

## 3. Architectural decisions (Architect to confirm at Wave 3)

| # | Decision | Choice | Rationale |
|---|---|---|---|
| D-1 | Browser engine | **Playwright (Chromium)** | Roadmap Q13: "Playwright is preferred (broader browser support, better async architecture)." Apache-2.0 license. Async API matches existing httpx async pattern. |
| D-2 | Optional dep wiring | New `[browser]` extra in pyproject.toml: `playwright>=1.40` | Mirrors `[voice]`, `[vision]`, `[serve]`, `[mcp]` patterns. Keeps `pip install heretic` lightweight on headless installs that have no use for a browser. |
| D-3 | Runtime browser binary | Operator runs `playwright install chromium` after `pip install heretic[browser]` | Standard Playwright workflow. Cannot be auto-installed via pip alone. Document in TROUBLESHOOTING / install instructions. |
| D-4 | Sense-availability check | New `LeidPlaywrightUnavailableError` raised at sense-startup if `playwright` import fails or browser binary missing; sense reports `EXTERNAL_APP_UNAVAILABLE` for `leid.render_url` calls when unavailable, but `leid.fetch_url` and `leid.extract_text` continue to work normally. | Graceful partial-availability — same posture as Mímisbrunnr/libzim. |
| D-5 | Browser lifecycle | **Launch-per-call** at v0.8.0 (each `render_url` call: `async_playwright().start()` → launch → context → page → goto → extract → close → stop). | Stateless; matches the existing `LeidClient` per-request httpx pattern. Persistent-browser lifecycle is a v0.8.2 concern when click/type need a live page. |
| D-6 | Default load state | `domcontentloaded` (configurable to `load`, `networkidle`, `commit`) | DOMContentLoaded fires after HTML is parsed and synchronous scripts executed — best balance of "page is rendered enough to extract" vs "no waiting forever for trackers." |
| D-7 | URL allowlist gate | Reuse existing `sandbox.url_matches_allowlist()` BEFORE launching the browser | Same gate, applied earlier — no browser launches if the URL is rejected. Single source of allow-list truth. |
| D-8 | HTTPS-only policy | Reuse `allow_http: false` from LeidConfig | Browser tools inherit the same HTTP/HTTPS policy as httpx tools. No separate flag. |
| D-9 | Response size cap | Cap on **rendered text bytes** at the same `max_response_bytes` cap. Pre-cap on `page.content()` size before text extraction. | Honors the existing memory-bound contract. |
| D-10 | Cookie / state isolation | Each `render_url` call uses a **fresh `browser.new_context()` (private context)**. No cookies persist between calls. No localStorage carry-over. | Honors L-5 (no cookies stored) at the browser layer. |
| D-11 | Headless | Always headless at v0.8.0 (no `headless: false` config option) | No UI surface to argue about; visible-browser mode is operator-debug, not production, and can be added in a later slice if needed. |
| D-12 | User-Agent | Reuse the existing `LeidConfig.user_agent` field; pass to Chromium via `browser.new_context(user_agent=...)` | One UA across both transports — consistent server-side identification. |
| D-13 | Navigation timeout | New `LeidConfig.browser_navigation_timeout_seconds` (default 30) — separate from the httpx `timeout_seconds` because rendered pages legitimately take longer | Browser load times are intrinsically slower; conflating with httpx timeout would force a global increase. |
| D-14 | Method shape policy | The new `render_url()` method lives on a **new sibling class `PlaywrightLeidClient`**, not inside `LeidClient`. `LeidSense._route()` dispatches `leid.render_url` to the playwright client; httpx tools dispatch unchanged to `LeidClient`. | Keeps the v0.7.1 httpx code path **byte-untouched** — additive only, zero regression risk to the streaming work. |
| D-15 | License | Playwright is **Apache-2.0** (Microsoft). Confirm at scope entry; add to `THIRD_PARTY_NOTICES.md`. Chromium binary distributed under BSD-style + LGPL components — Playwright downloads it as a runtime artifact, not bundled in the wheel. | Roadmap Q13 license check satisfied; no GPL contamination. |

---

## 4. Browser-render flow — proposed Cartographer sketch

```
agent tool_call → leid.render_url(url)
                   │
                   ▼
            LeidSense._route → "leid.render_url" → PlaywrightLeidClient.render_url(url)
                   │
                   ▼
            _validate_url      ── allowlist + HTTPS-only gate (same as httpx)
                   │ (raises UrlNotAllowedError before any browser launch)
                   ▼
        availability check    ── if Playwright not importable / browser missing:
                                   raise LeidPlaywrightUnavailableError
                   │
                   ▼
       async_playwright().start() ── new playwright runtime (per call, D-5)
                   │
                   ▼
       browser = pw.chromium.launch(headless=True)
                   │
                   ▼
       context = browser.new_context(user_agent=..., viewport=...)   ── fresh, no cookies (D-10)
                   │
                   ▼
       page = context.new_page()
                   │
                   ▼
       page.goto(url, wait_until="domcontentloaded", timeout=...)   ── D-6, D-13
                   │
                   ├── timeout → LeidTimeoutError
                   ├── HTTP error / network → LeidConnectionError
                   ├── HTTP 4xx/5xx response.status → LeidHttpError
                   ▼
       html = await page.content()            ── post-JS rendered DOM as HTML string
                   │
                   ├── pre-cap: if len(html.encode("utf-8")) > max_response_bytes → LeidResponseTooLargeError
                   ▼
       text, title = _extract_text_from_html(html)   ── reuses existing stdlib HTMLParser
                   │
                   ▼
       await context.close()     ── disposes cookies, localStorage
       await browser.close()
       await pw.stop()           ── shuts down playwright runtime
                   │
                   ▼
       return { url, final_url=page.url, text, title, source_size_bytes }
```

The flow mirrors `extract_text`'s logical shape — but with Playwright as the transport rather than httpx — preserving the agent-facing contract style.

---

## 5. New B-invariants (browser-mode, Architect to lock at Wave 3)

Additive to the existing L-1..L-9. The L-invariants continue to govern httpx tools unchanged.

| # | B-Invariant |
|---|-----------|
| B-1 | `_validate_url()` is called BEFORE `async_playwright().start()`. No browser process spawns for a rejected URL. |
| B-2 | `LeidPlaywrightUnavailableError` is raised at `render_url()` entry if `playwright` import or `chromium.launch()` fails. The httpx tools (`fetch_url`, `extract_text`) continue to work unaffected. |
| B-3 | Each `render_url()` call uses `browser.new_context()` — cookies/localStorage are scoped to the call and discarded at `context.close()`. No state persists between calls. |
| B-4 | The browser is launched headless (no visible window). |
| B-5 | `page.goto(url, wait_until="domcontentloaded", timeout=browser_navigation_timeout_seconds * 1000)`. Timeout maps to `LeidTimeoutError`. |
| B-6 | After navigation: `len(page.content().encode("utf-8")) <= max_response_bytes`. If exceeded, raise `LeidResponseTooLargeError` BEFORE text extraction; close context+browser+pw cleanly during stack unwind. |
| B-7 | All three resources (`pw`, `browser`, `context`) are closed in `finally` blocks. A failure during navigation must not leak a browser process. |
| B-8 | The `User-Agent` header on every browser request matches `LeidConfig.user_agent` (passed via `new_context(user_agent=...)`). |
| B-9 | `allow_http: false` rejects `http://` URLs at `_validate_url()` before browser launch — same posture as httpx tools (B-1 includes this). |
| B-10 | Browser path: no JS code is supplied by the agent in v0.8.0. The page runs its own scripts during render; HERETIC injects nothing. |

---

## 6. Test plan — Forge writes; Auditor verifies

New file: `tests/test_leid_playwright_client.py`. All tests mock the Playwright API (no real Chromium spawned in CI). One smoke test marked `@pytest.mark.requires_playwright` exercises the real binary if installed.

| Test | Asserts |
|---|---|
| `test_render_url_validates_before_launch` | URL not in allowlist → `UrlNotAllowedError` raised; `async_playwright` mock never called. (B-1) |
| `test_render_url_unavailable_when_playwright_missing` | Mock `import playwright` to raise `ImportError`; `render_url()` raises `LeidPlaywrightUnavailableError`. (B-2) |
| `test_render_url_unavailable_when_browser_launch_fails` | Mock `chromium.launch()` to raise; `render_url()` raises `LeidPlaywrightUnavailableError`. (B-2) |
| `test_render_url_uses_fresh_context_per_call` | Two consecutive calls → `browser.new_context()` called twice, both contexts closed. (B-3) |
| `test_render_url_launches_headless` | `chromium.launch()` called with `headless=True`. (B-4) |
| `test_render_url_navigation_timeout_raises_leid_timeout` | Mock `page.goto()` to raise `playwright.async_api.TimeoutError` → `LeidTimeoutError`. (B-5) |
| `test_render_url_navigation_http_error_raises_leid_http_error` | Mock `page.goto()` to return response with `status >= 400` → `LeidHttpError` with status code in message. |
| `test_render_url_pre_cap_on_rendered_html_size` | `page.content()` returns 2 MiB string with `max_response_bytes=1 MiB` → `LeidResponseTooLargeError`. (B-6) |
| `test_render_url_pre_cap_under_threshold` | `page.content()` returns 100 KiB with `max_response_bytes=1 MiB` → success. |
| `test_render_url_returns_correct_shape` | Success returns `{url, final_url, text, title, source_size_bytes}` with correct keys + types. |
| `test_render_url_extracts_title_from_rendered_html` | HTML has `<title>Test Page</title>` → `title == "Test Page"`. |
| `test_render_url_extracts_text_from_rendered_html` | HTML has `<body><p>Hello</p></body>` → `text == "Hello"`. |
| `test_render_url_returns_final_url_after_redirect` | `page.url` differs from input URL → `final_url` reflects redirected URL. |
| `test_render_url_uses_configured_user_agent` | `new_context()` called with `user_agent=config.user_agent`. (B-8) |
| `test_render_url_rejects_http_when_allow_http_false` | `http://example.com` with `allow_http=false` → `UrlNotAllowedError`. (B-9) |
| `test_render_url_closes_all_resources_on_navigation_failure` | `page.goto()` raises → `context.close()`, `browser.close()`, `pw.stop()` all called. (B-7) |
| `test_render_url_closes_all_resources_on_size_cap_breach` | Pre-cap raised → context+browser+pw all cleaned up. (B-7) |
| **Existing tests must continue to pass:** `tests/test_leid_client.py` (30) and `tests/test_leid_sense.py` (20) — zero regression on the httpx path. |
| `test_leid_sense.py::test_dispatch_render_url_routes_to_playwright_client` | LeidSense routes `leid.render_url` to PlaywrightLeidClient; httpx client not touched. |
| `test_leid_sense.py::test_render_url_unavailable_returns_external_app_unavailable_code` | When PlaywrightLeidClient raises `LeidPlaywrightUnavailableError`, sense returns SENSE_CONTRACTS code `EXTERNAL_APP_UNAVAILABLE`. |
| `@pytest.mark.requires_playwright test_render_url_smoke_real_chromium` | Marked-skip unless playwright + chromium installed; renders `data:text/html,...` URL and checks text extraction. Default-skip in CI. |

---

## 7. New / modified files (Forge inventory)

**New:**
- `src/heretic/skilningr/senses/leid/playwright_client.py` — `PlaywrightLeidClient` with `render_url()`
- `src/heretic/skilningr/senses/leid/errors.py` — add `LeidPlaywrightUnavailableError` (additive; existing exceptions unchanged)
- `tests/test_leid_playwright_client.py` — new test file
- `docs/vision/OPID_VEF.md` — Wave 1 vision doc

**Modified (additive):**
- `src/heretic/skilningr/config_model.py` — `LeidConfig` gains `browser_navigation_timeout_seconds: int = 30` and `browser_load_state: str = "domcontentloaded"` fields
- `src/heretic/skilningr/senses/leid/sense.py` — `LeidSense.__init__` accepts optional `playwright_client`; `_route` adds `leid.render_url` branch; `_leid_error_code` adds `LeidPlaywrightUnavailableError → EXTERNAL_APP_UNAVAILABLE`
- `src/heretic/skilningr/senses/leid/tools.py` — append `leid.render_url` tool definition
- `src/heretic/skilningr/senses/leid/INTERFACE.md` — Wave 3 update with B-invariants
- `src/heretic/skilningr/errors.py` — re-export `LeidPlaywrightUnavailableError`
- `pyproject.toml` — add `[browser]` extra
- `THIRD_PARTY_NOTICES.md` — Playwright (Apache-2.0) entry
- `docs/cartography/DATA_FLOW.md` — Wave 2 §4.12.3 browser-render flow
- `tests/test_leid_sense.py` — two new dispatch tests (additive; existing 20 unchanged)

**Untouched (additive law):**
- `src/heretic/skilningr/senses/leid/client.py` — the v0.7.1 streaming code is **byte-identical** after this milestone. The new sub-faculty lives in `playwright_client.py`.

---

## 8. Wave plan (Mythic Engineering ritual — autonomous)

| Wave | Role | Deliverable |
|---|---|---|
| 0 | Runa (this file) | TASK_HERETIC_v0.8.0_OPID_VEF.md committed + pushed |
| 1 | Skald (Sigrún Ljósbrá) | `docs/vision/OPID_VEF.md` |
| 2 | Cartographer (Védis Eikleið) | `docs/cartography/DATA_FLOW.md` §4.12.3 |
| 3 | Architect (Rúnhild Svartdóttir) | `senses/leid/INTERFACE.md` browser-mode addendum + LeidConfig fields + tools.py append |
| 4 | Forge (Eldra Járnsdóttir) | `playwright_client.py` + `errors.py` addendum + sense.py routing + tests + pyproject extra + THIRD_PARTY_NOTICES |
| 5 | Auditor (Sólrún Hvítmynd) | `docs/audit/AUDIT_v0.8.0_OPID_VEF.md` — verify B-1..B-10 + L-invariant non-regression |
| 6 | Forge cleanup | Address audit findings (skip if clean) |
| 7 | Scribe (Eirwyn Rúnblóm) | DEVLOG entry 23 + this TASK file sealed + memory refresh + final push |

Each wave commits and pushes. Cumulative work is recoverable at any wave boundary if context is interrupted.

---

## 9. Exit criteria (this milestone is sealed when all are true)

- [ ] `playwright_client.py` exists with `PlaywrightLeidClient.render_url()` implementation
- [ ] `LeidPlaywrightUnavailableError` defined and re-exported
- [ ] `leid.render_url` registered in `LEID_TOOL_DEFINITIONS`
- [ ] `LeidSense._route` dispatches `leid.render_url` correctly
- [ ] `LeidConfig` has `browser_navigation_timeout_seconds` and `browser_load_state` fields
- [ ] `[browser]` extra in `pyproject.toml`
- [ ] `THIRD_PARTY_NOTICES.md` lists Playwright (Apache-2.0)
- [ ] `tests/test_leid_playwright_client.py` exists with all 17 mock-based tests passing
- [ ] `tests/test_leid_sense.py` has 2 new dispatch tests passing
- [ ] All 30 existing `test_leid_client.py` tests pass unchanged (no httpx regression)
- [ ] All 20 existing `test_leid_sense.py` tests pass unchanged
- [ ] `docs/vision/OPID_VEF.md` exists
- [ ] `docs/cartography/DATA_FLOW.md` §4.12.3 exists
- [ ] `senses/leid/INTERFACE.md` v0.8.0 addendum exists with B-1..B-10
- [ ] `docs/audit/AUDIT_v0.8.0_OPID_VEF.md` PASSES SCRUTINY (0 BLOCKER, 0 SERIOUS)
- [ ] DEVLOG entry 23 written
- [ ] All commits pushed to `development`

---

## 10. Rollback plan

The milestone is fully additive. To roll back:
1. Revert the wave commits in reverse order.
2. The v0.7.1 httpx code is byte-identical and survives any rollback intact.
3. Operators with `pip install heretic[browser]` installed will see `leid.render_url` disappear from the tool catalogue if v0.8.0 is reverted; existing scripts using `leid.fetch_url` or `leid.extract_text` are unaffected.

---

*Task file authored by Runa Gridweaver Freyjasdottir, opening the v0.8 Opið Vef milestone with its first vertical slice. The body has read what the world wrote in stone; now it learns to read what the world chooses to render.*
