# AUDIT — v0.8.0 Opið Vef (Foundational Slice)

**Auditor:** Sólrún Hvítmynd
**Date:** 2026-05-10
**Scope under audit:** v0.8.0 *Opið Vef* — `PlaywrightLeidClient` + `leid.render_url` dispatch + B-1..B-10 invariants
**Mythic Engineering session:** AUTONOMOUS — Forge HEAD `73cbaac` (post-implementation, pre-audit)
**Audit method:** Static review of `playwright_client.py` and modified `sense.py` against the contract in `INTERFACE.md §10` and the wave-design TASK file. Mock-based test suite verification. Byte-diff verification of the v0.7.1 streaming code path. Boundary-condition probing on the new B-invariants.
**Verdict:** **PASSES SCRUTINY** — 0 BLOCKER, 0 SERIOUS, 0 NOTABLE, 2 NIT.

---

## I. Method

The audit was conducted in five passes:

1. **B-invariant verification** — each of B-1 through B-10 traced from contract to implementation to test.
2. **L-invariant non-regression** — confirm the v0.7.1 streaming-httpx path (`LeidClient`) is byte-identical and all 30 streaming tests still pass.
3. **Resource-leak boundary probing** — exercise every failure path and confirm `pw.stop()`, `browser.close()`, `context.close()` all run.
4. **Sandbox-bypass attempt** — try to construct call paths that reach `async_playwright().start()` without `_validate_url()` running first.
5. **Configuration boundary probing** — confirm `__post_init__` rejects out-of-range values for the two new fields.

---

## II. B-Invariant Verification (per the v0.8.0 contract)

Each invariant is traced from the INTERFACE.md §10 contract through the
implementation to its enforcing test.

### B-1 — Validation runs before any browser operation

| Aspect | Result |
|---|---|
| Contract location | `INTERFACE.md §10.2 B-1` |
| Implementation | `playwright_client.py:184` — `normalised_url = self._validate_url(url)` is the FIRST executable line in `render_url()`, before any `try: from playwright...` |
| Test | `test_render_url_validates_before_launch` — asserts `async_playwright_mock.assert_not_called()` after a rejected URL |
| Verdict | **PASS** — verified by code path inspection and test |

### B-2 — Availability error on missing playwright OR chromium

| Aspect | Result |
|---|---|
| Implementation (import) | `playwright_client.py:198-217` — `try: from playwright.async_api import ...` / `except ImportError → raise LeidPlaywrightUnavailableError` |
| Implementation (launch) | `playwright_client.py:230-241` — `try: browser = await pw.chromium.launch(headless=True)` / `except Exception → raise LeidPlaywrightUnavailableError` |
| Tests | `test_render_url_unavailable_when_playwright_missing` (uses `no_playwright` fixture), `test_render_url_unavailable_when_browser_launch_fails` |
| Httpx isolation | `LeidClient.fetch_url` and `extract_text` paths verified untouched (D-14); 30 `test_leid_client.py` tests pass unchanged |
| Verdict | **PASS** — both failure modes raise the documented exception class; httpx tools unaffected |

### B-3 — Fresh context per call, no state crosses calls

| Aspect | Result |
|---|---|
| Implementation | `playwright_client.py:240` — `context = await browser.new_context(user_agent=...)`. The browser itself is also new per call (D-5: launch-per-call), so even if `new_context` were skipped, no state could persist. **Stronger than the invariant requires.** |
| Test | `test_render_url_uses_fresh_context_per_call` — two consecutive calls confirmed to result in two `new_context` awaits and two `context.close` awaits |
| Verdict | **PASS** — verified at both the contract level (per-call context) and the implementation-strength level (per-call browser) |

### B-4 — Always headless

| Aspect | Result |
|---|---|
| Implementation | `playwright_client.py:230` — `browser = await pw.chromium.launch(headless=True)` (literal `True`, not config-derived) |
| Test | `test_render_url_launches_headless` — asserts `chromium.launch.assert_awaited_once_with(headless=True)` |
| Verdict | **PASS** — no config option exists to make the browser visible; future visible-mode would require an explicit code change |

### B-5 — Bounded navigation timeout

| Aspect | Result |
|---|---|
| Implementation | `playwright_client.py:246-251` — `page.goto(url, wait_until=config.browser_load_state, timeout=config.browser_navigation_timeout_seconds * 1000)`. Playwright `TimeoutError` → `LeidTimeoutError` (line 252-258) |
| Tests | `test_render_url_navigation_timeout_raises_leid_timeout`, `test_render_url_passes_browser_load_state`, `test_render_url_passes_browser_navigation_timeout` |
| Verdict | **PASS** — both the timeout value and the load-state value are passed correctly; timeout maps to the correct exception class |

### B-6 — Pre-cap on rendered HTML size before text extraction

| Aspect | Result |
|---|---|
| Implementation | `playwright_client.py:273-291` — `html = await page.content()` → `rendered_size = len(html.encode("utf-8"))` → `if rendered_size > self._config.max_response_bytes: raise LeidResponseTooLargeError(...)`. The `_extract_text_from_html(html)` call is on line 293, AFTER the cap check |
| Trade-off | Documented in `INTERFACE.md §10.4` and `DATA_FLOW.md §4.12.2.2`: the cap is a token-budget bound, not a memory bound for the browser process. Operators needing true streaming abort use `leid.fetch_url` |
| Tests | `test_render_url_pre_cap_on_rendered_html_size` (2 MiB rejected against 1 MiB cap), `test_render_url_pre_cap_under_threshold` (under-cap success) |
| Verdict | **PASS** — pre-cap order is correct; the trade-off is honestly documented in two places |

### B-7 — All three resources closed in `finally`

| Aspect | Result |
|---|---|
| Implementation | `playwright_client.py:295-322` — single outer `try` with the entire navigate/extract block, then `finally:` containing three conditional close blocks (`if context is not None`, `if browser is not None`, `if pw is not None`) each individually wrapped in `try/except` so a failure in one cleanup does not block the others |
| Tests | `test_render_url_closes_all_resources_on_navigation_failure` (page.goto raises), `test_render_url_closes_all_resources_on_size_cap_breach` (pre-cap raises), `test_render_url_closes_resources_when_launch_fails` (chromium.launch raises) |
| Verdict | **PASS** — three distinct failure modes verified; each cleanup is itself defensive |

### B-8 — User-Agent passed to browser context

| Aspect | Result |
|---|---|
| Implementation | `playwright_client.py:240` — `context = await browser.new_context(user_agent=self._config.user_agent)` |
| Test | `test_render_url_uses_configured_user_agent` — asserts `browser_mock.new_context.assert_awaited_once_with(user_agent="HERETIC/0.8.0 (test-agent)")` |
| Verdict | **PASS** — single source of truth for user agent across both transports (httpx and Playwright) |

### B-9 — `allow_http: false` rejects http:// before browser launch

| Aspect | Result |
|---|---|
| Implementation | `playwright_client.py:131-138` — identical scheme-check logic to `LeidClient._validate_url` |
| Test | `test_render_url_rejects_http_when_allow_http_false` |
| Verdict | **PASS** — the gate is identical to the httpx path; same logic applied at an earlier point |

### B-10 — No JavaScript injection by HERETIC

| Aspect | Result |
|---|---|
| Implementation | `playwright_client.py` — full file inspected. The only Playwright surface used is: `async_playwright().start()`, `chromium.launch()`, `new_context()`, `new_page()`, `page.goto()`, `page.content()`, `context.close()`, `browser.close()`, `pw.stop()`. None of these inject script. There are NO calls to `page.evaluate`, `page.add_init_script`, `page.add_script_tag`, `page.expose_function`, or any other Playwright code-injection API |
| Test | No explicit test asserts "no `page.evaluate` is called" because the production code path never calls it; a regression would be a code change, not a runtime path |
| Verdict | **PASS WITH NIT** — see N-2 below |

---

## III. L-Invariant Non-Regression (the v0.7.1 streaming path)

| Concern | Result |
|---|---|
| `client.py` source byte-identity | **VERIFIED.** `git diff 4c817e2..HEAD -- src/heretic/skilningr/senses/leid/client.py` returns empty. The v0.7.1 streaming code is untouched |
| `test_leid_client.py` 30 tests | **30/30 pass unchanged.** No test was edited, no test failed |
| `LeidClient` import path | Still `from heretic.skilningr.senses.leid.client import LeidClient` |
| `LeidSense` constructor backward compat | The new `playwright_client` param is keyword-only with default `None` — existing callers (e.g., `LeidSense(config, client)`) continue to work unchanged. Verified by 20 unchanged `test_leid_sense.py` tests passing |
| Tool-definition count change | Intentional: 2 → 3 (added `leid.render_url`). Only the count assertion was updated; the existing two definitions are byte-identical |
| Verdict | **PASS** — zero regression on the v0.7.1 work |

---

## IV. Sandbox-Bypass Attempt

The auditor attempted to construct a call path that reaches `async_playwright().start()` without `_validate_url()` running first.

| Attempt | Result |
|---|---|
| Pass an unvalidated URL | `_validate_url(url)` is called on line 184 of `render_url()`, which is the FIRST executable statement. There is no public method that calls Playwright without going through `render_url()` first |
| Bypass via injected client | The `playwright_client` parameter to `LeidSense.__init__` accepts an arbitrary `PlaywrightLeidClient`-shaped object. An adversarial caller injecting a client whose `render_url` does not validate would bypass the gate — but this is a Python invariant, not a HERETIC invariant. The official `PlaywrightLeidClient.render_url` does validate; a custom impl is the operator's responsibility |
| Bypass via direct module import | `playwright_client.py` exports only `PlaywrightLeidClient`. There is no module-level helper that would launch a browser without validation |
| Verdict | **NO BYPASS FOUND.** The gate is structurally enforced by the order of statements in `render_url()` |

---

## V. Configuration Boundary Probing

| Field | Validation | Test |
|---|---|---|
| `browser_navigation_timeout_seconds` | `__post_init__`: raises `ValueError` if `<= 0` | **NO DIRECT TEST** — see N-1 below |
| `browser_load_state` | `__post_init__`: raises `ValueError` if not in `{"commit", "domcontentloaded", "load", "networkidle"}` | **NO DIRECT TEST** — see N-1 below |
| Verdict | The `__post_init__` validation logic is correct on inspection, but no test asserts the specific error messages |

---

## VI. Findings

### BLOCKER — none

### SERIOUS — none

### NOTABLE — none

### NIT

#### N-1: Two new LeidConfig fields lack direct config-validation tests

The `__post_init__` validation for the two new fields (`browser_navigation_timeout_seconds <= 0` and `browser_load_state not in {valid set}`) is correct on inspection but is not directly exercised by the existing `TestLeidConfig` test class. The existing pattern (`test_leid_config_invalid_timeout_raises`, `test_leid_config_invalid_response_bytes_raises`, etc.) suggests two parallel tests would belong:

- `test_leid_config_invalid_browser_navigation_timeout_raises`
- `test_leid_config_invalid_browser_load_state_raises`

This is a NIT, not a defect: the validation logic is in place and is byte-correct; only the test coverage of the validation logic is missing. Forge cleanup (Wave 6) is invited but not required.

**Recommended fix:** Add two tests in `tests/test_leid_sense.py::TestLeidConfig`. Defer to v0.8.0.1 if the Forge prefers not to touch this milestone post-audit.

#### N-2: B-10 (no JS injection) lacks a regression-guard test

The B-10 invariant ("HERETIC injects no JavaScript code into the page in v0.8.0") is currently held by the absence of `page.evaluate(...)`-style calls in `playwright_client.py`. A future contributor who adds `page.evaluate(agent_provided_string)` would silently violate B-10 with no test failure.

**Recommended fix:** Add a test that mocks `page.evaluate` and asserts `page.evaluate.assert_not_called()` after a successful `render_url()`. This is a defensive regression-guard, not a behavioural change.

This is a NIT for the same reason as N-1: the production code is correct now; the gap is in the regression-guard test coverage.

---

## VII. Verdict

**PASSES SCRUTINY** — the v0.8.0 *Opið Vef* foundational slice is fit for its sealed milestone close.

| Severity | Count |
|---|---|
| BLOCKER | 0 |
| SERIOUS | 0 |
| NOTABLE | 0 |
| NIT | 2 (N-1 config validation tests, N-2 B-10 regression-guard test) |

The two NITs are recommendations for additional defensive test coverage, NOT defects in the production code. They MAY be addressed at Forge Wave 6 if the milestone is to ship with maximum coverage; they MAY be deferred to a v0.8.0.1 follow-up if the milestone is to ship with the boundary clean and the recommendations queued.

The Auditor recommends **closing N-1 in Wave 6 (cheap, ~10 lines of test) and DEFERRING N-2 to v0.8.x or v0.8.0.1** (the regression-guard test requires more careful mock construction and may cleanly belong with the screenshot/click work that will share the page mock infrastructure).

---

## VIII. Notes for the Scribe

When sealing this milestone (Wave 7), the DEVLOG entry should record:

1. v0.8.0 *Opið Vef* opens the umbrella v0.8 milestone.
2. The roadmap milestone v0.8 is NOT yet fully sealed — only the foundational slice closes here. Subsequent slices: v0.8.1 (`screenshot`), v0.8.2 (`click`+`type`), v0.8.3 (`query`).
3. **Pattern continues:** *Opið Vef* is the third instance of "deepening an existing faculty without a new identity codename" — like Endurdrykkr extending into v0.7.3 (index-layer) and Verkminni extending into v0.6.3.1 (disk-mirror), Leið now extends into Playwright-render at v0.8.0 without a new sense-level codename. The umbrella name *Opið Vef* belongs to v0.8 the milestone, not to a new sense.
4. The v0.7.1 streaming code is byte-untouched; D-14 honoured.

---

*Audit authored by Sólrún Hvítmynd, Auditor for Vibe Coding, 2026-05-10.*
*The body's second pair of eyes opens cleanly. The gate is honoured at the threshold; the cookies do not survive their call; the browser does not leak. Two small recommendations queued for the cleanup hand. The milestone passes.*
