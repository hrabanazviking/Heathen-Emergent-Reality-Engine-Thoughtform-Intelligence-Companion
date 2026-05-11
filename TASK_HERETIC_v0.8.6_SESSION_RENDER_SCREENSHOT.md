# TASK — HERETIC v0.8.6 — session_render + session_screenshot (Innan Hurðar extension)

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-11** (immediately after v0.8.5 history pair sealed at `7db363e`)
>
> **Codename:** **NONE** — ninth unnamed extension within Innan Hurðar.
>
> **Bundling note:** Like v0.8.5, two tools are bundled in one milestone because they share strong structural symmetry. session_render and session_screenshot are the mid-session counterparts of the existing stateless `leid.render_url` and `leid.screenshot` tools — same content extraction primitives (`page.content()` / `page.screenshot()`), same size-cap discipline, same B-10 inheritance, applied now to an existing open session's page instead of a freshly-launched one.
>
> **Umbrella milestone:** v0.8 *Opið Vef* — ninth slice within the umbrella.
>
> **Mythic Engineering mode:** AUTONOMOUS. Seventeenth milestone in the autonomous arc.
>
> **STATUS — 2026-05-11:** **SHIPPED + AUDITED + SEALED.** All seven waves closed; Wave 6 cleanup skipped (Auditor returned **zero findings** — sixth consecutive in v0.8 umbrella).
>
> **Final HEAD:** `062d061` (Auditor close) — final Scribe push will advance.
>
> **Test status:** Leid 240 + 2 skip (was 222 + 2 — `+18`). Full suite 1561 + 9 skip (was 1543 + 9). Zero regressions.
>
> **Auditor verdict:** PASSES SCRUTINY (0/0/0/0). Sixth consecutive zero-findings audit. **Second bundled-pair milestone in v0.8 umbrella** shipped cleanly. See `docs/audit/AUDIT_v0.8.6_SESSION_RENDER_SCREENSHOT.md`.
>
> **DEVLOG:** Entry 31 — `docs/DEVLOG.md`.

---

## 1. Task scope

Add TWO paired tools — mid-session re-extraction primitives:

> **`leid.session_render(session_id) → {session_id, current_url, text, title, source_size_bytes}`** —
>
> The in-session counterpart of v0.8.0's `leid.render_url`. Re-extracts the rendered text and title from the current page of an open session. Uses Playwright's `await page.content()` on the existing session page. Same B-6 size-cap discipline (pre-cap on rendered HTML byte size before text extraction).

> **`leid.session_screenshot(session_id) → {session_id, current_url, image_base64, image_format, size_bytes, full_page}`** —
>
> The in-session counterpart of v0.8.1's `leid.screenshot`. Captures a PNG of the current page of an open session. Uses Playwright's `await page.screenshot()` on the existing session page. Same B-11 size-cap discipline (pre-cap on raw PNG bytes before base64 encoding).

**Use cases:**
- After `click` triggers a single-page-app state change, `session_render` returns the post-click text without closing and re-opening
- After `type` + `press("Enter")` submits a search, `session_screenshot` captures the rendered results page
- Periodic mid-flow re-extraction for "verify state after each step" agent loops

The httpx tools, the v0.8.0/v0.8.1 stateless render_url / screenshot, and the v0.8.2.x session tools are **unchanged**. v0.8.6 is purely additive.

---

## 2. Out of scope

| Capability                  | Slice    | Reason for deferral                                       |
|-----------------------------|----------|-----------------------------------------------------------|
| Element-scoped screenshot (`locator.screenshot`) | v0.8.x | Distinct primitive; agent can navigate/click into the element first |
| Inner HTML re-extraction    | v0.8.x   | text_content covers most needs; raw HTML is a different primitive |
| Mid-session JPEG/WebP output | v0.8.x  | PNG-only at v0.8.6 (matches v0.8.1's posture) |
| Mid-session viewport configuration | v0.8.x | Inherits the session's launch-time viewport |

---

## 3. Architectural decisions

| #  | Decision | Choice | Rationale |
|----|---|---|---|
| D-97 | Render primitive | `await session.page.content()` then `_extract_text_from_html(html)` (same helper as render_url) | Re-use, don't re-write. The v0.8.0 helper is already tested |
| D-98 | Screenshot primitive | `await session.page.screenshot(full_page=config.browser_screenshot_full_page, type="png")` (mirrors v0.8.1 D-16 / D-20) | Same Playwright primitive; same config field for full_page |
| D-99 | Size-cap inheritance | session_render uses B-6's cap on rendered HTML byte size; session_screenshot uses B-11's cap on raw PNG bytes before base64 | Existing invariants apply unchanged — both already operate on a `page.content` or `page.screenshot` result |
| D-100 | M-1 closure inheritance | Both tools wrap their primitives in `try/except (PlaywrightError, PlaywrightTimeoutError)` mapping to `LeidConnectionError`, mirroring the v0.8.2 M-1 closure applied to render_url and screenshot | Pattern is established; reuses the explicit-typing discipline added at v0.8.2 |
| D-101 | Return shape | session_render returns `{session_id, current_url, text, title, source_size_bytes}` (mirrors render_url's `{url, final_url, text, title, source_size_bytes}` but with `current_url` instead of `url`+`final_url` since they're identical in-session); session_screenshot returns `{session_id, current_url, image_base64, image_format, size_bytes, full_page}` | Schema reflects that in-session re-extract has no "input URL distinct from final URL" — it's just "current URL" |
| D-102 | No new config | Reuses `max_response_bytes`, `browser_screenshot_full_page`, `browser_navigation_timeout_seconds` | All existing — session re-extract is functionally identical to the stateless tools |
| D-103 | No new error classes | Reuses LeidSessionExpiredError, LeidConnectionError, LeidResponseTooLargeError | Same failure surface as stateless siblings |
| D-104 | Skald wave | NO new vision-doc addendum — ninth unnamed extension | Continuing the established pattern |
| D-105 | New B-Invariant | B-24 — both tools enforce the same in-session discipline (session resolution + activity update) plus the existing B-6 / B-11 size caps from their stateless siblings | Single new invariant; reuses prior infrastructure |
| D-106 | Bundling | Both tools in one milestone (like v0.8.5) | Second bundled-pair milestone. They share session-resolution discipline, activity-update discipline, and M-1 closure pattern. Splitting would produce two near-duplicate audit cycles |

---

## 4. New B-Invariant

| #    | B-Invariant |
|------|-----------|
| B-24 | `session_render()` and `session_screenshot()` enforce the same session/timeout discipline as the rest of Innan Hurðar interactive tools: `evict_expired_sessions` runs first; unknown session_id raises `LeidSessionExpiredError`; the underlying Playwright primitive (`page.content()` for session_render; `page.screenshot()` for session_screenshot) is wrapped with `try/except (PlaywrightError, PlaywrightTimeoutError) → LeidConnectionError` (D-100 — M-1 closure inheritance); the existing size caps from B-6 (rendered HTML) and B-11 (raw PNG bytes before base64) apply unchanged; on success, `session.last_activity_at` is updated. |

B-1..B-23 continue to govern unchanged. B-6 and B-11 are explicitly inherited rather than restated — the size caps belong to the underlying primitives, not to the launch-vs-session lifecycle.

---

## 5. Test plan

Extend `tests/test_leid_playwright_client.py` with `TestSessionRender` and `TestSessionScreenshot` classes. Tests will be more numerous than v0.8.5 because the two tools diverge more (text vs binary, different size-cap units, different return shapes).

For `TestSessionRender` (~7 tests):
- `test_session_render_unknown_session_raises_expired` — B-16
- `test_session_render_calls_page_content` — D-97 (primitive call)
- `test_session_render_returns_text_and_title` — return shape
- `test_session_render_returns_current_url` — D-101
- `test_session_render_pre_cap_on_rendered_html` — B-6 inheritance
- `test_session_render_page_content_error_maps_to_connection_error` — D-100 / M-1
- `test_session_render_updates_last_activity` — B-17 / B-24

For `TestSessionScreenshot` (~7 tests):
- `test_session_screenshot_unknown_session_raises_expired` — B-16
- `test_session_screenshot_calls_page_screenshot_with_full_page_config` — D-98
- `test_session_screenshot_returns_base64_png` — return shape
- `test_session_screenshot_returns_current_url` — D-101
- `test_session_screenshot_pre_cap_on_png_bytes` — B-11 inheritance
- `test_session_screenshot_page_screenshot_error_maps_to_connection_error` — D-100 / M-1
- `test_session_screenshot_updates_last_activity` — B-17 / B-24

Shared (~2):
- `test_session_render_does_not_call_page_evaluate` — B-10 inheritance (one regression-guard per direction is enough)
- `test_session_screenshot_does_not_call_page_evaluate` — same

`tests/test_leid_sense.py` (~2):
- `test_dispatch_session_render_routes_to_playwright_client`
- `test_dispatch_session_screenshot_routes_to_playwright_client`
- Update tool count check 14 → 16
- Update tool names locked check

Total new tests: ~18.

---

## 6. Wave plan

| Wave | Role | Deliverable |
|---|---|---|
| 0 | Runa (this file) | TASK file |
| 1 | Skald (very brief) | OPID_VEF.md §IX continuation paragraph (one paragraph for the pair) |
| 2 | Cartographer | DATA_FLOW.md §4.12.2.10 — mid-session re-extract flow (one section covers both) |
| 3 | Architect | INTERFACE.md §12.12 + B-24 + 2 tool defs |
| 4 | Forge | session_render + session_screenshot methods + sense routing + ~16 method tests + 2 dispatch tests |
| 5 | Auditor | AUDIT_v0.8.6_SESSION_RENDER_SCREENSHOT.md |
| 6 | Forge cleanup | If needed |
| 7 | Scribe | DEVLOG entry 31 + seal + memory refresh |

---

## 7. Exit criteria (all met; this milestone is SEALED)

- [x] `session_render()` and `session_screenshot()` methods on `PlaywrightLeidClient` — `0f8bbb3`
- [x] `leid.session_render` and `leid.session_screenshot` registered in `LEID_TOOL_DEFINITIONS` — `c91d1bb`
- [x] `LeidSense._route` dispatches both — `0f8bbb3`
- [x] No new error classes (D-103) — confirmed
- [x] No new config fields (D-102) — confirmed
- [x] B-24 added to INTERFACE.md §12.12 — `c91d1bb`
- [x] M-1 closure pattern applied to both — `0f8bbb3`
- [x] All 222 existing leid tests pass unchanged — verified at `0f8bbb3`
- [x] 16 new method tests passing — `0f8bbb3`
- [x] 2 new dispatch tests passing — `0f8bbb3`
- [x] `docs/cartography/DATA_FLOW.md` §4.12.2.10 exists (covers both tools) — `af6427a`
- [x] `docs/vision/OPID_VEF.md` §IX continuation paragraph exists — `c6de401`
- [x] `docs/audit/AUDIT_v0.8.6_SESSION_RENDER_SCREENSHOT.md` PASSES SCRUTINY (0/0/0/0) — `062d061`
- [x] DEVLOG entry 31 written — Wave 7 (this seal)
- [x] All commits pushed to `development` — final Scribe push closes
