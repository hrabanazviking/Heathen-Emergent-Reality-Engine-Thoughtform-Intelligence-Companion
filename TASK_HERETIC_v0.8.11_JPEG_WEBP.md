# TASK — HERETIC v0.8.11 — JPEG/WebP screenshot output (Innan Hurðar extension)

> **Started: 2026-05-11** (immediately after v0.8.10 sealed at `d380e46`)
> **Codename:** NONE — fourteenth unnamed extension within Innan Hurðar.
> **Umbrella:** v0.8 *Opið Vef* — fourteenth slice.
> **Mode:** AUTONOMOUS. Twenty-second milestone in the autonomous arc.

---

## 1. Task scope

Add operator-controlled screenshot format. Currently both `screenshot` (v0.8.1) and `session_screenshot` (v0.8.6) produce PNG. Add support for JPEG and WebP via two new config fields:

- `browser_screenshot_format: str = "png"` — one of `"png" | "jpeg" | "webp"`
- `browser_screenshot_jpeg_quality: int = 80` — quality 0-100; passed to Playwright when format is jpeg or webp; ignored for png

**Modification sites:**
- `PlaywrightLeidClient.screenshot()` — `page.screenshot(type=config.browser_screenshot_format, quality=... if applicable)`
- `PlaywrightLeidClient.session_screenshot()` — same

**Return shape:** `image_format` field now reflects the actual format used (was hardcoded `"png"`).

No new tools, no new error classes, no agent-facing change (format is operator infrastructure).

---

## 2. Out of scope

| Capability | Slice | Reason |
|---|---|---|
| Per-call format override (agent-supplied) | v0.8.x | Operator-controlled is right scope |
| Per-tool format (screenshot=jpeg but session_screenshot=png) | v0.8.x | Complexity not justified |
| Format auto-detection by content | v0.8.x | Out of scope; operator picks |

---

## 3. Architectural decisions

| # | Decision | Choice |
|---|---|---|
| D-146 | Field types | str for format, int for quality |
| D-147 | Defaults | "png" + 80 — PNG matches existing behavior |
| D-148 | Validation | format in {"png", "jpeg", "webp"}; quality 0-100 |
| D-149 | Quality applies | Only to jpeg/webp — png ignores. Pass quality kwarg conditionally |
| D-150 | New B-Invariant | B-29 — format + quality propagated uniformly to both screenshot methods; quality omitted from call kwargs when format == "png" |
| D-151 | No new error classes | Config validation reuses ValueError |
| D-152 | Test impact | Existing screenshot tests assert `type="png"`; update mechanically to read from config defaults |

---

## 4. New B-Invariant

| # | B-Invariant |
|---|---|
| B-29 | `screenshot()` and `session_screenshot()` pass `type=config.browser_screenshot_format` to `page.screenshot()`. When format is `"jpeg"` or `"webp"`, `quality=config.browser_screenshot_jpeg_quality` is also passed; when format is `"png"`, `quality` is omitted from the call (Playwright's lossless PNG doesn't accept it). The `image_format` field in the return reflects the actual format used. |

---

## 5. Test plan

Existing tests to update:
- `test_screenshot_full_page_true_passed_to_playwright` — assertion includes `type` from config default
- `test_screenshot_full_page_false_passed_to_playwright` — same
- `test_session_screenshot_calls_page_screenshot_with_full_page_config` — same

New tests (~6 in TestScreenshotFormat class):
- `test_screenshot_uses_png_by_default`
- `test_screenshot_uses_jpeg_when_configured` (with quality)
- `test_screenshot_uses_webp_when_configured` (with quality)
- `test_session_screenshot_uses_png_by_default`
- `test_session_screenshot_uses_jpeg_when_configured`
- `test_image_format_field_reflects_actual_format`

New config validation tests (~4 in test_leid_sense.py):
- default tests + invalid format/quality raise tests

---

## 6. Wave plan

| Wave | Role | Deliverable |
|---|---|---|
| 0 | Runa | TASK file |
| 1 | Skald (brief) | OPID_VEF §IX continuation |
| 2 | Cartographer | DATA_FLOW §4.12.2.15 |
| 3 | Architect | INTERFACE §12.17 + B-29 + 2 LeidConfig fields |
| 4 | Forge | Modify 2 methods + update 3 existing tests + ~6 new tests + ~4 config tests |
| 5 | Auditor | AUDIT_v0.8.11 |
| 6 | Forge cleanup | If needed |
| 7 | Scribe | DEVLOG entry 36 |

---

## 7. Exit criteria

- [ ] 2 new LeidConfig fields with validation
- [ ] screenshot + session_screenshot pass format from config
- [ ] quality kwarg conditionally passed (omitted for png)
- [ ] image_format return field reflects actual format
- [ ] B-29 added to INTERFACE
- [ ] All existing leid tests pass (with 3 updated assertions)
- [ ] At least 6 new format propagation tests
- [ ] At least 4 new config validation tests
- [ ] Cartographer + Auditor docs
- [ ] DEVLOG entry 36
- [ ] All pushed
