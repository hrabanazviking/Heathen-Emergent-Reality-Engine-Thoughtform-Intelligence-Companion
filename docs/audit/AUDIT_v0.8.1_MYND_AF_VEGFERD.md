# AUDIT — v0.8.1 Mynd af Vegferð (Second slice within v0.8 Opið Vef)

**Auditor:** Sólrún Hvítmynd
**Date:** 2026-05-10
**Scope under audit:** v0.8.1 *Mynd af Vegferð* — `PlaywrightLeidClient.screenshot()` + `leid.screenshot` dispatch + B-11 invariant + B-10 regression-guards (closing N-2 from v0.8.0)
**Mythic Engineering session:** AUTONOMOUS — Forge HEAD `59fbd72` (post-implementation, pre-audit)
**Audit method:** Static review of the new `screenshot()` method against the v0.8.1 contract in `INTERFACE.md §11`. Verification that B-1..B-10 from v0.8.0 still hold for the new method (full inheritance) and that the new B-11 (pre-cap on raw PNG bytes) is enforced before base64 encoding. Byte-diff verification of the v0.7.1 streaming code path AND the v0.8.0 `render_url()` method (both must be untouched). Verification that the deferred N-2 from v0.8.0 is now closed.
**Verdict:** **PASSES SCRUTINY** — 0 BLOCKER, 0 SERIOUS, 0 NOTABLE, 1 NIT.

---

## I. Method

The audit was conducted in five passes:

1. **B-11 verification** — the new invariant traced from contract to implementation to test.
2. **B-1..B-10 inheritance verification** — confirm each invariant from v0.8.0 still holds for `screenshot()`.
3. **N-2 closure verification** — confirm the two new B-10 regression-guard tests assert what the Auditor recommended at v0.8.0 close.
4. **L + render_url non-regression** — confirm both `LeidClient` (v0.7.1 streaming) and `PlaywrightLeidClient.render_url()` (v0.8.0) are byte-identical.
5. **Resource-leak boundary probing** — exercise screenshot's failure paths and confirm `pw.stop()`, `browser.close()`, `context.close()` all run.

---

## II. B-11 Verification (the new invariant)

**Contract (INTERFACE.md §11.2):**
> `screenshot()` enforces the same size cap as `render_url`, applied to the **raw PNG bytes BEFORE base64 encoding**. If `len(png_bytes) > config.max_response_bytes`, `LeidResponseTooLargeError` is raised BEFORE the `base64.b64encode` call.

**Implementation (`playwright_client.py`):**

```python
png_bytes = await page.screenshot(full_page=full_page, type="png")

# B-11 — pre-cap on raw PNG byte size, BEFORE base64 encoding.
png_size = len(png_bytes)
if png_size > self._config.max_response_bytes:
    self._log.warning(...)
    raise LeidResponseTooLargeError(...)

# Stage 7 — base64 encode (D-17).
image_base64 = base64.b64encode(png_bytes).decode("ascii")
```

**Statement order verified:** the cap check is on line N+2 after `page.screenshot()` returns, and the `base64.b64encode` call is on line N+5+ (after the conditional raise). The raise occurs **before** any base64 work happens.

**Test:** `test_screenshot_pre_cap_on_png_bytes` — supplies a 2 MiB PNG with `max_response_bytes=1 MiB` and asserts `LeidResponseTooLargeError` is raised. The corresponding success-path test (`test_screenshot_pre_cap_under_threshold`) confirms a 1 KiB PNG passes the cap and returns successfully with `size_bytes == len(png_bytes)`.

**Cleanup-on-raise:** `test_screenshot_closes_resources_on_size_cap_breach` confirms `context.close()`, `browser.close()`, `pw.stop()` all run when B-11 fires. B-7 inheritance is therefore verified for the new failure path.

**Verdict:** **PASS** — B-11 is correctly placed, correctly enforced, correctly cleaned-up-after, and correctly tested.

---

## III. B-1..B-10 Inheritance Verification

The invariants from v0.8.0 §10.2 must continue to hold for `screenshot()`. Each is traced to its enforcing test in the new `TestScreenshot*` classes.

| #    | Invariant                                            | Implementation site (screenshot)                                                          | Test                                                              |
|------|------------------------------------------------------|-------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| B-1  | Validation before browser launch                     | First line of `screenshot()`: `normalised_url = self._validate_url(url)`                  | `test_screenshot_validates_before_launch`                         |
| B-2  | Unavailable when playwright/chromium missing         | Same `try/except ImportError` + `try/except` around `chromium.launch`                     | `test_screenshot_unavailable_when_playwright_missing`, `_when_browser_launch_fails` |
| B-3  | Fresh `new_context` per call                         | Same `context = await browser.new_context(user_agent=...)`                                | `test_screenshot_uses_fresh_context_per_call`                     |
| B-4  | Always headless                                      | Same `pw.chromium.launch(headless=True)`                                                  | `test_screenshot_launches_headless`                               |
| B-5  | Bounded navigation timeout → `LeidTimeoutError`      | Same `page.goto(..., timeout=config.browser_navigation_timeout_seconds * 1000)` + try/except `PlaywrightTimeoutError` | `test_screenshot_navigation_timeout_raises_leid_timeout`        |
| B-6  | (Render-only — N/A for screenshot; B-11 is the analog) | —                                                                                       | (B-11 covers the equivalent for screenshot)                       |
| B-7  | All resources closed in `finally`                    | Same nested `finally` with three conditional close blocks                                  | `test_screenshot_closes_resources_on_navigation_failure`, `_on_size_cap_breach` |
| B-8  | User-Agent passed to context                         | Same `new_context(user_agent=self._config.user_agent)`                                    | `test_screenshot_uses_configured_user_agent`                      |
| B-9  | `allow_http: false` rejects http://                  | Reuses the same `_validate_url` method (single source of truth)                            | `test_screenshot_rejects_http_when_allow_http_false`              |
| B-10 | No JavaScript injection                              | No `page.evaluate(...)` call anywhere in `screenshot()` (full file inspected)              | **`test_screenshot_does_not_call_page_evaluate`** (NEW, closes N-2) |

**Verdict:** **PASS** — every B-invariant from v0.8.0 is honoured by the new method, with explicit test coverage for each.

---

## IV. N-2 Closure (Audit-deferred from v0.8.0)

**Auditor recommendation at v0.8.0 close (`AUDIT_v0.8.0_OPID_VEF.md` §VI N-2):**
> Add a test that mocks `page.evaluate` and asserts `page.evaluate.assert_not_called()` after a successful `render_url()`. Defer to v0.8.x or v0.8.0.1 — needs richer page-mock infrastructure that may cleanly belong with the screenshot/click work.

**v0.8.1 closure (in `tests/test_leid_playwright_client.py::TestB10NoJavaScriptInjection`):**

```python
async def test_render_url_does_not_call_page_evaluate(self, fake_playwright):
    _, _, _, page_mock, _ = fake_playwright()
    client = make_client(["https://example.com/*"])
    await client.render_url("https://example.com/page")
    page_mock.evaluate.assert_not_called()

async def test_screenshot_does_not_call_page_evaluate(self, fake_playwright):
    _, _, _, page_mock, _ = fake_playwright()
    client = make_client(["https://example.com/*"])
    await client.screenshot("https://example.com/page")
    page_mock.evaluate.assert_not_called()
```

The `page_mock` factory in `_install_fake_playwright` was extended with `page_mock.evaluate = AsyncMock(return_value=None)`, which is the regression-guard mock surface. Both tests pass; both methods exercised end-to-end with the fake Playwright never observing a `page.evaluate` call.

**A future contributor adding `page.evaluate(agent_input)` to either method will fail these tests at CI** — exactly the regression-guard the v0.8.0 Auditor requested.

**Verdict:** **N-2 CLOSED.** The recommendation is satisfied as recommended (bundled with screenshot's mock infrastructure, not retrofitted in isolation).

---

## V. L + render_url Non-Regression

| Concern | Result |
|---|---|
| `LeidClient` source byte-identity | **VERIFIED.** `git diff 59fbd72 -- src/heretic/skilningr/senses/leid/client.py` returns empty. v0.7.1 streaming code intact |
| `PlaywrightLeidClient.render_url()` byte-identity | **VERIFIED.** The diff against `playwright_client.py` adds: (a) `import base64` line at top, (b) `screenshot()` method appended after `render_url()`. The `render_url()` method body is byte-identical to v0.8.0 (`73cbaac` → `59fbd72`) |
| `test_leid_client.py` 30 tests | **30/30 pass unchanged** |
| `test_leid_playwright_client.py` original 26 + 1 skip | **26/26 pass unchanged + 1 skip preserved** |
| `test_leid_sense.py` original 27 | **27/27 pass unchanged** (count check 3 → 4 was the only deliberate change; 27 → 30 added 3 new tests) |
| Tool-definition count change | Intentional: 3 → 4 (added `leid.screenshot`). Existing three definitions unchanged |
| `LeidConfig` backward compat | New field `browser_screenshot_full_page: bool = True` has a default; existing constructors continue to work unchanged |
| Verdict | **PASS** — D-23 (strict additive law for v0.8.1) honoured for `render_url`; D-14 from v0.8.0 still honoured for `LeidClient`. Two layers of preservation discipline maintained |

---

## VI. Resource-Leak Boundary Probing

The new `screenshot()` method's failure paths exercised:

| Failure | Resources cleaned? | Test |
|---|---|---|
| `page.goto` raises `PlaywrightError` (network) | `context.close()` ✓, `browser.close()` ✓, `pw.stop()` ✓ | `test_screenshot_closes_resources_on_navigation_failure` |
| `page.goto` raises `PlaywrightTimeoutError` | (Same `finally` shape — verified by code-path inspection; no separate explicit test, but the cleanup code is identical to the navigation-failure case which IS tested) | (covered by code-path identity) |
| HTTP 4xx/5xx → `LeidHttpError` | (Same `finally` shape — verified by code-path inspection) | (covered by code-path identity) |
| B-11 fires (PNG too large) | `context.close()` ✓, `browser.close()` ✓, `pw.stop()` ✓ | `test_screenshot_closes_resources_on_size_cap_breach` |
| `chromium.launch` fails | `pw.stop()` ✓ (browser & context skipped because they were never set) | (inherited from v0.8.0 N-2 cleanup pattern; same nested-conditional structure) |

**Verdict:** **PASS** — no resource leak found in any failure path.

---

## VII. Findings

### BLOCKER — none

### SERIOUS — none

### NOTABLE — none

### NIT

#### M-1: `page.screenshot()` and `page.content()` exceptions are not explicitly typed

The `screenshot()` method catches `PlaywrightTimeoutError` and `PlaywrightError` only around `page.goto()`. If `page.screenshot()` itself raises (e.g., browser process disconnected mid-call, page closed unexpectedly), the exception propagates as the raw underlying type and is caught by `LeidSense._route`'s generic `Exception` clause, surfacing to the agent as `SENSE_INTERNAL_ERROR` — which is the catch-all code, not a more specific `EXTERNAL_APP_UNAVAILABLE`.

The same pattern exists in `render_url()` for `await page.content()` — this gap was carried over from v0.8.0 and is not specific to v0.8.1. The Auditor flags it now to record the consistency.

**Recommendation:** Add a `try/except (PlaywrightError, PlaywrightTimeoutError)` around the `page.screenshot()` call AND the `page.content()` call in `render_url()`, mapping each to `LeidConnectionError`. This brings the failure surface in line with what the agent expects: a connection-level error from the browser is conceptually identical to a connection-level error from httpx, and both should surface as `EXTERNAL_APP_UNAVAILABLE` so the agent can apply the same retry/degrade policy.

This is a NIT, not a defect: the current behaviour is graceful (the `LeidSense._route` catch-all ensures dispatch never raises), and the cleanup `finally` block still runs. Only the agent-facing error code is suboptimal.

**Auditor recommends DEFERRING to v0.8.2** — the persistent-session model that v0.8.2 introduces will surface more browser-state exceptions (e.g., `PageClosedError` on click after navigation), so a single Forge pass at v0.8.2 can comprehensively map all `Page.*` exceptions to the appropriate `Leid*` classes for click, type, screenshot, content, and goto in one coordinated sweep.

---

## VIII. Verdict

**PASSES SCRUTINY** — the v0.8.1 *Mynd af Vegferð* slice is fit for milestone close.

| Severity | Count |
|---|---|
| BLOCKER | 0 |
| SERIOUS | 0 |
| NOTABLE | 0 |
| NIT | 1 (M-1 — exception typing for page.screenshot/page.content; deferred to v0.8.2) |

**Wins this milestone:**
- v0.8.0's Auditor recommendation N-2 is closed cleanly (with the better timing the Auditor recommended at v0.8.0 close).
- B-11 placed correctly: pre-cap on raw PNG before base64. Memory wasted on the encoded form is avoided when the cap fires.
- Strict additive law honoured: `LeidClient` byte-untouched (D-14 from v0.8.0 still holds); `render_url()` byte-untouched (D-23 from v0.8.1 honoured).
- B-10 now has explicit regression-guard coverage for both browser methods. Future contributors who add `page.evaluate(agent_input)` will fail these tests, not silently violate the invariant.

---

## IX. Notes for the Scribe

When sealing this milestone (Wave 7), the DEVLOG entry should record:

1. v0.8.1 *Mynd af Vegferð* is the **second slice** within the v0.8 *Opið Vef* umbrella.
2. **Pattern continues:** Like *Opið Vef* itself, *Mynd af Vegferð* extends a faculty without a new sense-level codename. The umbrella name v0.8 *Opið Vef* still does the work; only an addendum to the existing vision doc is added (no new vision file).
3. **Closes deferred N-2 from v0.8.0** — the Auditor's suggested timing was honoured.
4. The httpx code path AND the v0.8.0 render_url path are both byte-untouched.
5. Test growth: leid scope 83 + 1 skip → **106 + 2 skip** (+23 + 1); full suite 1404 + 8 → **1427 + 9** (+23 + 1).

Threads carried forward:
- v0.8.2 (`leid.click`, `leid.type`) — natural next slice; will need persistent-page session model
- v0.8.3 (`leid.query`) — CSS selector / attribute extraction
- M-1 — bundle exception-typing fix into v0.8.2 (Auditor's explicit recommendation)

---

*Audit authored by Sólrún Hvítmynd, Auditor for Vibe Coding, 2026-05-10.*
*The portrait is faithful, the cap is honest about content not transport, the body still injects no foreign script. The deferred regression-guard from the prior audit is now in place — the body's discipline is now testable, not only believable. The milestone passes.*
