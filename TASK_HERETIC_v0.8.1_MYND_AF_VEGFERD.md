# TASK — HERETIC v0.8.1 MYND AF VEGFERÐ

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-10** (immediately after v0.8.0 *Opið Vef* sealed at `85ca9d2`)
>
> **Codename (Skald to seal at Wave 1, brief addendum):** *Mynd af Vegferð* — "image of the journey." The body now walks the road *and* keeps a portrait of what it saw. The text the body extracted in v0.8.0 told the agent what the page said; the screenshot tells the agent what the page *looked like*.
>
> **Umbrella milestone:** v0.8 *Opið Vef* — second slice within the umbrella. Like *Opið Vef* itself, *Mynd af Vegferð* is a **manner**, not a new identity — Leið remains Leið; the screenshot is a new posture for the same eyes that learned to walk in v0.8.0.
>
> **Mythic Engineering mode:** AUTONOMOUS. Volmarr asleep / hands-off. All seven roles run on this single milestone within one session.

---

## 1. Task scope

Add the second tool to the Opið Vef sub-faculty:

> **One new tool — `leid.screenshot(url)`** — a stateless tool that:
>   1. Validates `url` against `url_allowlist_patterns` (same gate as `render_url`).
>   2. Launches a headless Chromium subprocess via Playwright.
>   3. Navigates to the URL with the configured load state.
>   4. Captures a PNG screenshot of the rendered page (`full_page` configurable).
>   5. Pre-caps the raw PNG bytes against `max_response_bytes`.
>   6. Encodes the PNG bytes as base64.
>   7. Closes the browser context and runtime.
>   8. Returns a dict with `{url, final_url, image_base64, image_format, size_bytes, full_page}`.

The lifecycle mirrors `render_url` — same B-1..B-10 invariants apply. One new invariant (B-11) governs the image-data path. Implementation lives in the same `PlaywrightLeidClient` class as a sibling method.

The httpx tools and `render_url` are **unchanged**. v0.8.1 is purely additive.

---

## 2. Out of scope (deferred to later v0.8.x slices)

| Capability                  | Slice    | Reason for deferral                                      |
|-----------------------------|----------|----------------------------------------------------------|
| `leid.click`, `leid.type`   | v0.8.2   | Requires persistent-session model (live page across calls) |
| `leid.query`                | v0.8.3   | CSS selector + attribute extraction                       |
| Region/element screenshots  | v0.8.x+  | Single-page, full-page or viewport only at v0.8.1         |
| JPEG / WebP output          | v0.8.x+  | PNG only at v0.8.1                                        |
| Screenshot quality config   | v0.8.x+  | Default Playwright PNG quality                            |
| Persistent browser between calls | v0.8.2 | Forced by stateful tools                                  |
| Visible-window mode         | not planned | Same as v0.8.0 — debug only, not production           |

---

## 3. Architectural decisions (Architect to confirm at Wave 3)

| #  | Decision | Choice | Rationale |
|----|---|---|---|
| D-16 | Image format | **PNG** (Playwright default) | Lossless, broad agent compatibility; smaller for screenshots than JPEG when content is text-heavy |
| D-17 | Encoding for return | **base64 string** in `image_base64` field | Standard agent-tool convention for binary; JSON-safe; the agent can store/re-emit without further encoding |
| D-18 | Size cap target | Raw PNG bytes (BEFORE base64 encoding) checked against `max_response_bytes` | Honest about actual content size; the base64 expansion (~33%) is a transport detail, not a content-size question |
| D-19 | New error class? | Reuse `LeidResponseTooLargeError` | Same semantic — content from the page exceeded the operator-configured cap. Adding a parallel class for image-vs-text would fragment the error surface for no benefit |
| D-20 | Full-page vs viewport | New `LeidConfig.browser_screenshot_full_page: bool = True` | `full_page=True` is what users almost always want for "show me the page" semantics; viewport-only is an opt-out for cases where the SPA's full page is enormous |
| D-21 | Viewport size at v0.8.1 | Playwright default (1280x720) | Configurable viewport deferred to v0.8.x; not needed for the foundational screenshot slice |
| D-22 | Browser lifecycle | Launch-per-call (D-5), same as `render_url` | Stateless; the persistent-session question moves to v0.8.2 with click/type |
| D-23 | Refactor question | **Leave `render_url` byte-untouched.** `screenshot` duplicates the lifecycle scaffolding inline. | Strict additive law (RULES.AI). The cost of ~30 lines of duplication is small; the cost of refactoring v0.8.0's audited code at v0.8.1 is real (re-audit risk). If a third stateful method arrives at v0.8.2, the refactor case becomes stronger and can be revisited then with a wider mandate |
| D-24 | B-11 — image cap | Raw PNG bytes > `max_response_bytes` raises `LeidResponseTooLargeError` BEFORE base64 encoding; resources still cleaned up via the same `finally` block | Honors the same disposition as B-6 — the body knows what is too heavy before it asks anyone else to carry it |
| D-25 | Bundle Audit N-2 closure | Add the B-10 regression-guard test (`page.evaluate` not called by either render_url or screenshot) at Wave 4 alongside the new tests | Page-mock infrastructure expands at this slice; Auditor recommended deferring to "v0.8.x or v0.8.0.1" — v0.8.1 satisfies the recommendation cleanly |

---

## 4. Screenshot flow — proposed Cartographer sketch

```
agent tool_call → leid.screenshot(url)
                   │
                   ▼
            LeidSense._route → "leid.screenshot" → PlaywrightLeidClient.screenshot(url)
                   │
                   ▼
            _validate_url      ── allowlist + HTTPS-only gate (same as render_url)
                   │ (raises UrlNotAllowedError before any browser launch)
                   ▼
        availability check    ── playwright import + chromium launch (B-2)
                   │
                   ▼
       async_playwright().start() → chromium.launch(headless=True)
                   │
                   ▼
       browser.new_context(user_agent=...)   ── fresh, no cookies (B-3, B-8)
                   │
                   ▼
       page.goto(url, wait_until=config.browser_load_state, timeout=...)
                   │
                   ├── timeout → LeidTimeoutError                      (B-5)
                   ├── network → LeidConnectionError
                   ├── 4xx/5xx → LeidHttpError
                   ▼
       png_bytes = await page.screenshot(
           full_page=config.browser_screenshot_full_page,              (D-20)
           type="png",                                                 (D-16)
       )
                   │
                   ├── B-11 pre-cap: if len(png_bytes) > max_response_bytes
                   │                  → LeidResponseTooLargeError (D-24)
                   ▼
       image_base64 = base64.b64encode(png_bytes).decode("ascii")     (D-17)
       final_url    = page.url
                   │
                   ▼
       finally: context.close() → browser.close() → pw.stop()        (B-7)
                   │
                   ▼
       return {
         "url": validated_url,
         "final_url": final_url,
         "image_base64": image_base64,
         "image_format": "png",
         "size_bytes": len(png_bytes),
         "full_page": config.browser_screenshot_full_page,
       }
```

---

## 5. New B-invariant (browser-mode, Architect to lock at Wave 3)

| #    | B-Invariant |
|------|-----------|
| B-11 | `screenshot()` enforces the SAME size cap as `render_url`, applied to the **raw PNG bytes BEFORE base64 encoding**. If `len(png_bytes) > config.max_response_bytes`, `LeidResponseTooLargeError` is raised BEFORE base64 encoding; context+browser+pw closed cleanly during stack unwind (B-7 still applies). |

B-1..B-10 from v0.8.0 continue to govern both `render_url` and `screenshot` unchanged. B-10 in particular ("HERETIC injects no JavaScript") gains a regression-guard test at this milestone (closing Auditor N-2 from `AUDIT_v0.8.0_OPID_VEF.md`).

---

## 6. Test plan — Forge writes; Auditor verifies

New tests in `tests/test_leid_playwright_client.py` (new test class `TestScreenshot`, parallel to `TestRenderUrl*`):

| Test | Asserts |
|---|---|
| `test_screenshot_validates_before_launch` | URL not in allowlist → UrlNotAllowedError; no browser launched. (B-1 for screenshot) |
| `test_screenshot_unavailable_when_playwright_missing` | Playwright import fails → LeidPlaywrightUnavailableError. (B-2) |
| `test_screenshot_unavailable_when_browser_launch_fails` | `chromium.launch` raises → LeidPlaywrightUnavailableError. (B-2) |
| `test_screenshot_uses_fresh_context_per_call` | Two calls → two new_context, two close. (B-3) |
| `test_screenshot_launches_headless` | `chromium.launch(headless=True)`. (B-4) |
| `test_screenshot_navigation_timeout_raises_leid_timeout` | `page.goto` Timeout → LeidTimeoutError. (B-5) |
| `test_screenshot_http_error_raises_leid_http_error` | response.status >= 400 → LeidHttpError. |
| `test_screenshot_pre_cap_on_png_bytes` | PNG larger than `max_response_bytes` → LeidResponseTooLargeError BEFORE base64 encoding. (B-11) |
| `test_screenshot_pre_cap_under_threshold` | PNG within cap → success. |
| `test_screenshot_returns_correct_shape` | `{url, final_url, image_base64, image_format, size_bytes, full_page}`. |
| `test_screenshot_image_base64_decodes_to_original_png` | base64.decode(result["image_base64"]) == raw PNG bytes returned by mocked `page.screenshot`. (D-17) |
| `test_screenshot_full_page_true_passed_to_playwright` | `page.screenshot.assert_awaited_once_with(full_page=True, type="png")` when config sets True. |
| `test_screenshot_full_page_false_passed_to_playwright` | Same with False. |
| `test_screenshot_uses_configured_user_agent` | `new_context(user_agent=config.user_agent)`. (B-8) |
| `test_screenshot_rejects_http_when_allow_http_false` | http:// rejected. (B-9) |
| `test_screenshot_closes_resources_on_navigation_failure` | All three resources closed on `page.goto` raise. (B-7) |
| `test_screenshot_closes_resources_on_size_cap_breach` | All three closed on B-11 raise. (B-7) |
| **B-10 regression-guard (closes Audit N-2):** `test_render_url_does_not_call_page_evaluate` | After successful `render_url`, `page.evaluate` mock was never called. (B-10) |
| **B-10 regression-guard:** `test_screenshot_does_not_call_page_evaluate` | After successful `screenshot`, `page.evaluate` mock was never called. (B-10) |
| **Sense dispatch:** `test_dispatch_screenshot_routes_to_playwright_client` | `leid.screenshot` dispatched to PlaywrightLeidClient.screenshot; httpx client untouched. |
| **Sense dispatch:** `test_screenshot_unavailable_returns_external_app_unavailable_code` | LeidPlaywrightUnavailableError → EXTERNAL_APP_UNAVAILABLE code. |
| **Config validation:** `test_leid_config_browser_screenshot_full_page_default` | Default value is True. |
| `@pytest.mark.requires_playwright test_screenshot_smoke_real_chromium` | Default-skip; renders data: URL and asserts result["image_base64"] decodes to non-empty PNG bytes. |

| **Existing tests must continue to pass:** test_leid_client.py 30, test_leid_sense.py 27, test_leid_playwright_client.py 26 (+ 1 skip). |

---

## 7. New / modified files (Forge inventory)

**New:** none. All v0.8.1 work goes into existing files.

**Modified (additive):**
- `src/heretic/skilningr/senses/leid/playwright_client.py` — new `screenshot()` method on `PlaywrightLeidClient`; imports `base64` from stdlib
- `src/heretic/skilningr/senses/leid/sense.py` — `_route` adds `leid.screenshot` branch
- `src/heretic/skilningr/senses/leid/tools.py` — append `leid.screenshot` tool definition
- `src/heretic/skilningr/senses/leid/INTERFACE.md` — §10 addendum: B-11; tool table row; return shape
- `src/heretic/skilningr/config_model.py` — `LeidConfig.browser_screenshot_full_page: bool = True`
- `docs/cartography/DATA_FLOW.md` — new §4.12.2.3 — screenshot flow
- `docs/vision/OPID_VEF.md` — §VIII addendum (Skald brief, no new vision doc)
- `tests/test_leid_playwright_client.py` — `TestScreenshot` class + B-10 regression-guard tests for both methods
- `tests/test_leid_sense.py` — 2 new dispatch tests + 1 new config-default test

**Untouched (additive law D-23):**
- `src/heretic/skilningr/senses/leid/client.py` — v0.7.1 streaming-httpx code, byte-identical
- `PlaywrightLeidClient.render_url()` — v0.8.0 method, byte-identical
- `PlaywrightLeidClient.__init__` and `_validate_url` — shared with screenshot, no modification needed

---

## 8. Wave plan

| Wave | Role | Deliverable |
|---|---|---|
| 0 | Runa (this file) | TASK_HERETIC_v0.8.1_MYND_AF_VEGFERD.md committed + pushed |
| 1 | Skald (Sigrún Ljósbrá) — brief | `docs/vision/OPID_VEF.md` §VIII addendum (no new vision doc) |
| 2 | Cartographer (Védis Eikleið) | `docs/cartography/DATA_FLOW.md` §4.12.2.3 |
| 3 | Architect (Rúnhild Svartdóttir) | INTERFACE.md §10 addendum (B-11) + LeidConfig field + tool def |
| 4 | Forge (Eldra Járnsdóttir) | `screenshot()` method + sense routing + 22 new tests + 2 B-10 regression-guard tests + 1 config test |
| 5 | Auditor (Sólrún Hvítmynd) | `docs/audit/AUDIT_v0.8.1_MYND_AF_VEGFERD.md` — verify B-1..B-11 + L-invariant non-regression + N-2 closure verification |
| 6 | Forge cleanup | Address findings (skip if clean) |
| 7 | Scribe (Eirwyn Rúnblóm) | DEVLOG entry 24 + this TASK file sealed + memory refresh + final push |

---

## 9. Exit criteria (this milestone is sealed when all are true)

- [ ] `screenshot()` method implemented on `PlaywrightLeidClient`
- [ ] `leid.screenshot` registered in `LEID_TOOL_DEFINITIONS`
- [ ] `LeidSense._route` dispatches `leid.screenshot`
- [ ] `LeidConfig.browser_screenshot_full_page` field added with default True and __post_init__ accepts bool
- [ ] B-11 invariant added to INTERFACE.md §10
- [ ] All 26 existing playwright_client tests pass unchanged
- [ ] All 27 existing test_leid_sense tests pass unchanged
- [ ] All 30 existing test_leid_client tests pass unchanged
- [ ] At least 18 new screenshot tests passing
- [ ] 2 new B-10 regression-guard tests passing (closes Audit N-2 from v0.8.0)
- [ ] 2 new sense dispatch tests passing
- [ ] 1 new config default test passing
- [ ] `docs/cartography/DATA_FLOW.md` §4.12.2.3 exists
- [ ] `docs/vision/OPID_VEF.md` §VIII addendum exists
- [ ] `docs/audit/AUDIT_v0.8.1_MYND_AF_VEGFERD.md` PASSES SCRUTINY (0 BLOCKER, 0 SERIOUS)
- [ ] DEVLOG entry 24 written
- [ ] All commits pushed to `development`

---

*Task file authored by Runa Gridweaver Freyjasdottir, opening the second slice of v0.8 Opið Vef. The body now keeps a portrait of every road it walks.*
