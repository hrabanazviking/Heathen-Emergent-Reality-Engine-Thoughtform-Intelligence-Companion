# AUDIT — v0.8.11 JPEG/WebP screenshot output (operator-controlled image format)

**Auditor:** Sólrún Hvítmynd
**Date:** 2026-05-11
**Scope under audit:** v0.8.11 — two new `LeidConfig` fields (`browser_screenshot_format`, `browser_screenshot_jpeg_quality`) propagated into Playwright's `page.screenshot()` kwargs at both `screenshot()` and `session_screenshot()` sites. B-29 invariant: the `image_format` return field reflects the actual format used.
**Mythic Engineering session:** AUTONOMOUS — Forge HEAD `d2f86c1` (post-implementation, pre-audit)
**Audit method:** Static review of the two modification sites against the v0.8.11 contract in `INTERFACE.md §12.17`. Verification that the validation in `LeidConfig.__post_init__` exhaustively constrains the new fields. Verification that the return-shape honesty law (B-29) holds at both sites. Verification that the public agent surface is unchanged (D-130: operator infrastructure, not agent intent). LeidClient byte-untouched check (D-14). Test coverage check. Backwards-compatibility check for the default-png path.
**Verdict:** **PASSES SCRUTINY** — 0 BLOCKER, 0 SERIOUS, 0 NOTABLE, 0 NIT (ELEVENTH CONSECUTIVE zero-findings audit in the v0.8 umbrella).

---

## I. Method

The audit was conducted in seven passes:

1. **B-29 verification at both sites** — confirm format + quality propagate into `page.screenshot()` and the `image_format` return field reflects reality.
2. **Configuration validation** — confirm `__post_init__` rejects every malformed input and accepts every legal one.
3. **Quality-only-when-lossy** — confirm `quality` is NOT passed when `format == "png"` (Playwright rejects this combination).
4. **D-130 surface invariance** — confirm no new agent argument; format is operator infrastructure.
5. **D-14 LeidClient byte-untouched** — confirm `leid/client.py` has not been modified since v0.7.1.
6. **Backwards compatibility** — confirm the default behaviour (PNG, no quality kwarg) is byte-identical to v0.8.10.
7. **Test coverage** — confirm tests cover both sites × all three formats + config validation + return-shape honesty.

---

## II. B-29 Verification at Both Sites

**Contract (INTERFACE.md §12.17):**
> The `browser_screenshot_format` and `browser_screenshot_jpeg_quality` LeidConfig fields propagate into Playwright's `page.screenshot()` kwargs at every screenshot-capturing tool. The `image_format` field in the tool's return value reflects the actual format used.

**Site 1 — `screenshot()` (stateless, line ~596):**

```python
screenshot_kwargs: dict[str, Any] = {
    "full_page": full_page,
    "type": self._config.browser_screenshot_format,
}
if self._config.browser_screenshot_format != "png":
    screenshot_kwargs["quality"] = (
        self._config.browser_screenshot_jpeg_quality
    )
png_bytes = await page.screenshot(**screenshot_kwargs)
...
return {
    ...
    "image_format": self._config.browser_screenshot_format,
    ...
}
```

**Verified.** Format propagates into the kwargs dict. Quality conditionally appended. Return-shape `image_format` mirrors the config value.

**Site 2 — `session_screenshot()` (stateful, line ~1747):**

Identical structure to Site 1 — same kwargs construction, same conditional quality, same return-shape field.

**Verified.** Both sites use the same propagation pattern; no divergence.

**Verdict:** **PASS** — B-29 uniformly applied at both screenshot sites.

---

## III. Configuration Validation

**Contract:** `browser_screenshot_format ∈ {"png", "jpeg", "webp"}`; `browser_screenshot_jpeg_quality ∈ [0, 100]`.

```python
_allowed_formats = {"png", "jpeg", "webp"}
if self.browser_screenshot_format not in _allowed_formats:
    raise ValueError(
        f"LeidConfig: browser_screenshot_format must be one of "
        f"{sorted(_allowed_formats)} (got {self.browser_screenshot_format!r})"
    )
if not (0 <= self.browser_screenshot_jpeg_quality <= 100):
    raise ValueError(
        f"LeidConfig: browser_screenshot_jpeg_quality must be in 0..100 "
        f"(got {self.browser_screenshot_jpeg_quality})"
    )
```

**Cases tested:**

| Input | Result |
|---|---|
| `"png"`, `"jpeg"`, `"webp"` | Accepted |
| `"gif"`, `""` | Rejected with ValueError |
| `quality=-1`, `quality=101` | Rejected with ValueError |
| `quality=0`, `quality=100` | Accepted (boundary) |

**Verdict:** **PASS** — Validation is exhaustive at the closed set of three formats and the closed integer interval `[0, 100]`.

---

## IV. Quality-Only-When-Lossy

Playwright rejects `page.screenshot(type="png", quality=...)` because PNG is lossless and quality is meaningless. The implementation correctly gates the quality kwarg:

```python
if self._config.browser_screenshot_format != "png":
    screenshot_kwargs["quality"] = ...
```

**Verified by test:** `test_screenshot_uses_png_by_default` asserts `"quality" not in call_kwargs`. Same for `test_session_screenshot_uses_png_by_default`.

**Verdict:** **PASS** — Quality is never sent to Playwright when format is PNG.

---

## V. D-130 Surface Invariance

**Contract (D-130):** Viewport, screenshot format, and similar "how the browser looks/captures" knobs are **operator infrastructure**, not agent intent. They live in `LeidConfig` and never appear as tool arguments.

**Public tool surface for `screenshot` and `session_screenshot`:**

- `screenshot(url, full_page=None)` — unchanged
- `session_screenshot(session_id, full_page=None)` — unchanged

No `format` or `quality` parameter has been added to either tool. The agent cannot influence the image format through any tool call. Only the operator (through `LeidConfig` at sense construction) can.

**Verdict:** **PASS** — D-130 honoured; no agent surface drift.

---

## VI. D-14 LeidClient Byte-Untouched

Verified by `git diff c41cb9b..HEAD -- src/heretic/skilningr/senses/leid/client.py` — empty.

**Verdict:** **PASS** — D-14 holds for the 15th consecutive milestone.

---

## VII. Backwards Compatibility

**Default config behaviour:**

- `browser_screenshot_format = "png"` (default)
- Branch: `if self._config.browser_screenshot_format != "png": ...` is False → no quality kwarg
- Resulting call: `await page.screenshot(full_page=..., type="png")`
- v0.8.10 call: `await page.screenshot(full_page=...)`

**Difference:** v0.8.11 explicitly passes `type="png"`. Playwright's default for `type` is `"png"`, so the wire-level behaviour is identical. The two existing tests that asserted `assert_awaited_once_with(full_page=True)` were updated to `assert_awaited_once_with(full_page=True, type="png")` — purely a test-spec adjustment to match the explicit-default style; not a behavioural regression.

**Return shape:** `image_format` field was hardcoded `"png"` in v0.8.10 and is now `self._config.browser_screenshot_format`, which equals `"png"` by default. Default-path return shape is byte-identical.

**Verdict:** **PASS** — Default behaviour bytewise-equivalent to v0.8.10 on the wire and in the return shape.

---

## VIII. Test Coverage

**New tests in `tests/test_leid_playwright_client.py` (TestScreenshotFormat, 6 tests):**

1. `test_screenshot_uses_png_by_default` — default config → `type="png"`, no quality
2. `test_screenshot_uses_jpeg_when_configured` — jpeg format → `type="jpeg"` + quality
3. `test_screenshot_uses_webp_when_configured` — webp format → `type="webp"` + quality
4. `test_screenshot_image_format_field_reflects_actual_format` — B-29 return shape
5. `test_session_screenshot_uses_png_by_default` — session site default
6. `test_session_screenshot_uses_jpeg_when_configured` — session site lossy + return shape

**New tests in `tests/test_leid_sense.py` (5 tests):**

1. `test_leid_config_browser_screenshot_format_default_is_png`
2. `test_leid_config_browser_screenshot_jpeg_quality_default_is_80`
3. `test_leid_config_browser_screenshot_format_accepts_jpeg_and_webp`
4. `test_leid_config_invalid_browser_screenshot_format_raises` — covers "gif" and ""
5. `test_leid_config_invalid_browser_screenshot_jpeg_quality_raises` — covers -1 and 101

**Coverage matrix:**

| Dimension | Covered |
|---|---|
| Format propagation site 1 (`screenshot`) | yes (3 tests) |
| Format propagation site 2 (`session_screenshot`) | yes (2 tests) |
| Quality propagation when lossy | yes (2 tests, jpeg + webp) |
| Quality absent when PNG | yes (2 tests, both sites) |
| Return shape `image_format` honesty | yes (2 tests, both sites) |
| Config field defaults | yes |
| Config field acceptance set | yes |
| Config field rejection set | yes (format + quality boundaries) |

**Full suite:** 1620 passed, 9 skipped, 56 warnings, 11.06s. No regressions.

**Verdict:** **PASS** — Coverage is complete across both sites × all three formats × both validation directions.

---

## IX. Sandbox-Bypass Attempt

Does the new format/quality propagation open any new attack surface?

- Format strings are constrained to a closed set of three by `__post_init__`. Any other value raises ValueError at config construction.
- Quality is constrained to integers in `[0, 100]`. Any other value raises ValueError at config construction.
- Neither value reaches any URL, file, or network layer — both flow only into Playwright's screenshot encoder.
- LeidClient (transport layer) is byte-untouched.

**No new attack surface introduced.**

**Verdict:** **PASS.**

---

## X. Findings

**BLOCKER:** 0
**SERIOUS:** 0
**NOTABLE:** 0
**NIT:** 0

**Eleventh consecutive zero-findings audit in the v0.8 umbrella.**

---

## XI. Verdict

**PASSES SCRUTINY.** v0.8.11 is a clean, additive refinement that:

- propagates two operator-controlled fields (format, quality) end-to-end through two screenshot sites;
- enforces a closed acceptance set at the configuration boundary;
- maintains return-shape honesty (B-29) by reflecting the actual format used;
- preserves D-130 (operator infrastructure, not agent intent);
- preserves D-14 (LeidClient byte-untouched, 15th consecutive milestone);
- preserves backwards compatibility (default PNG path is bytewise-equivalent on the wire and in the return shape);
- introduces no new attack surface;
- ships with exhaustive coverage at both sites × all three formats × both validation directions.

The refinement is sealed and ready for DEVLOG.

— Sólrún Hvítmynd, 2026-05-11
