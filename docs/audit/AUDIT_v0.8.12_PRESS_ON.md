# AUDIT — v0.8.12 element-targeted press (Innan Hurðar extension)

**Auditor:** Sólrún Hvítmynd
**Date:** 2026-05-11
**Scope under audit:** v0.8.12 — new `leid.press_on(session_id, selector, key)` tool. Uses Playwright's `page.locator(selector).first.press(key, timeout=...)` primitive. New `LeidPressOnElementNotFoundError` class (sibling of click/type element-not-found classes); maps to `INVALID_ARGUMENTS`. New B-30 invariant.
**Mythic Engineering session:** AUTONOMOUS — Forge HEAD `32b3337` (post-implementation, pre-audit)
**Audit method:** Static review of `press_on()` against the v0.8.12 contract in `INTERFACE.md §12.18`. Symmetry verification with click (v0.8.2) and type (v0.8.2.1) — the three element-targeted interactive primitives. Error-class mapping verification. Sense-dispatch wiring verification. Tool-registry verification. LeidClient byte-untouched check (D-14). Test coverage check.
**Verdict:** **PASSES SCRUTINY** — 0 BLOCKER, 0 SERIOUS, 0 NOTABLE, 0 NIT (TWELFTH CONSECUTIVE zero-findings audit in the v0.8 umbrella).

---

## I. Method

The audit was conducted in eight passes:

1. **B-30 verification** — confirm `press_on` calls `page.locator(selector).first.press(key, timeout=browser_click_timeout_seconds * 1000)` with the correct error mapping.
2. **Symmetry with click and type** — confirm press_on follows the same shape (selector → first → action with timeout + element-not-found error class).
3. **Error-class hierarchy** — confirm `LeidPressOnElementNotFoundError` is sibling of `LeidClickElementNotFoundError` and `LeidTypeElementNotFoundError`; all three map to `INVALID_ARGUMENTS` in `_leid_error_code`.
4. **Distinction from `leid.press` (v0.8.4)** — confirm press_on does not collapse into press; the two have orthogonal use cases.
5. **Sense-dispatch wiring** — confirm `LeidSense.dispatch_tool_call` routes `leid.press_on` to `press_on()` with the three args.
6. **Tool-registry verification** — confirm `leid.press_on` is registered with the correct JSON Schema (required: session_id + selector + key; additionalProperties: false).
7. **D-14 LeidClient byte-untouched** — confirm `leid/client.py` unchanged.
8. **Test coverage** — confirm tests cover the happy path, both failure modes, modifier keys, activity update, post-action URL read, and B-10 (no page.evaluate).

---

## II. B-30 Verification

**Contract (INTERFACE.md §12.18):**
> `press_on(session_id, selector, key)` calls `page.locator(selector).first.press(key, timeout=browser_click_timeout_seconds * 1000)`. `PlaywrightTimeoutError` raises `LeidPressOnElementNotFoundError`; other `PlaywrightError` raises `LeidConnectionError`. On success, `session.mark_activity()` is invoked and the post-press URL + title are read and returned.

**Implementation (`playwright_client.py`):**

```python
press_timeout_ms = self._config.browser_click_timeout_seconds * 1000
locator = session.page.locator(selector).first
try:
    await locator.press(key, timeout=press_timeout_ms)
except PlaywrightTimeoutError as exc:
    raise LeidPressOnElementNotFoundError(...) from exc
except PlaywrightError as exc:
    raise LeidConnectionError(...) from exc

session.mark_activity()
current_url = session.page.url
try:
    current_title = await session.page.title()
except Exception:
    current_title = None
```

**Verified by inspection.** All five elements of B-30 are present:
- locator.first.press with key + timeout kwarg ✓
- PlaywrightTimeoutError → LeidPressOnElementNotFoundError ✓
- non-timeout PlaywrightError → LeidConnectionError ✓
- mark_activity on success ✓
- post-press URL + title read with defensive title ✓

**Verdict:** **PASS** — B-30 met.

---

## III. Symmetry with click and type

**The three interactive primitives share a single shape:**

| Tool | Primitive | Timeout | Element-not-found class | Activity update | Post-action read |
|---|---|---|---|---|---|
| `click` (v0.8.2) | `locator.first.click(timeout=...)` | `browser_click_timeout_seconds` | `LeidClickElementNotFoundError` | yes | url + title |
| `type` (v0.8.2.1) | `locator.first.fill(text, timeout=...)` | `browser_click_timeout_seconds` | `LeidTypeElementNotFoundError` | yes | url + title |
| `press_on` (v0.8.12) | `locator.first.press(key, timeout=...)` | `browser_click_timeout_seconds` | `LeidPressOnElementNotFoundError` | yes | url + title |

**Verified by side-by-side reading of all three methods.** The shape is identical down to the defensive title read pattern (`try: title() except Exception: None`). The Architect's discipline of "interactive actions share one operator bound" (D-54 → D-155) holds.

**Verdict:** **PASS** — Press_on completes the three-primitive symmetry.

---

## IV. Error-Class Hierarchy

**`heretic/skilningr/errors.py`** declares `LeidPressOnElementNotFoundError(LeidError)` with docstring explicitly noting sibling relationship and INVALID_ARGUMENTS mapping.

**`senses/leid/errors.py`** re-exports the new class alongside the other Leid errors.

**`senses/leid/sense.py::_leid_error_code()`** updated:

```python
if isinstance(
    exc,
    (
        LeidResponseTooLargeError,
        LeidClickElementNotFoundError,
        LeidTypeElementNotFoundError,
        LeidPressOnElementNotFoundError,
    ),
):
    return "INVALID_ARGUMENTS"
```

**Verified.** The new class joins the existing INVALID_ARGUMENTS tuple cleanly. The error code mapping is exhaustive at this layer; no other isinstance branch can swallow the new class because LeidError subclass identity is checked in declared order.

**Verdict:** **PASS** — Hierarchy is correct; mapping is correct.

---

## V. Distinction from leid.press (v0.8.4)

| Property | `leid.press` (v0.8.4) | `leid.press_on` (v0.8.12) |
|---|---|---|
| Primitive | `page.keyboard.press(key)` | `page.locator(selector).first.press(key, timeout=...)` |
| Focus model | Whatever element has focus | The matched element (focused by Playwright) |
| Selector arg | none | required |
| Timeout arg | none (Playwright default) | `browser_click_timeout_seconds * 1000` |
| On selector miss | n/a (no selector) | `LeidPressOnElementNotFoundError` |
| Use case | "press Enter after I just typed" | "press Space on this specific button" |

**Verified.** The two tools are clearly orthogonal: `press` is page-level (uses current focus), `press_on` is element-targeted (focuses the matched element first). The contract documents the distinction in INTERFACE §12.18 and the DATA_FLOW §4.12.2.16 symmetry table.

**Verdict:** **PASS** — No collapse; orthogonal use cases.

---

## VI. Sense-Dispatch Wiring

**`senses/leid/sense.py`** (dispatch branch added immediately after `leid.press` branch):

```python
if tool_name == "leid.press_on":
    if self._playwright_client is None:
        self._playwright_client = PlaywrightLeidClient(
            self._config, log=self._log
        )
    result = await self._playwright_client.press_on(
        session_id=args["session_id"],
        selector=args["selector"],
        key=args["key"],
    )
    return json.dumps(result)
```

**Verified.** The branch follows the established shape (lazy-init the Playwright client; await with kwargs from the parsed args dict; return JSON). KeyError on missing required args propagates through the dispatch's argument-extraction error handling.

**Verdict:** **PASS** — Dispatch is wired correctly.

---

## VII. Tool-Registry Verification

**`senses/leid/tools.py`** registers `leid.press_on` between `leid.press` and `leid.go_back`:

- name: `leid.press_on` ✓
- description: documents distinction from `leid.press`, the use case, the error semantics, and the surface (INVALID_ARGUMENTS on miss) ✓
- parameters: session_id + selector + key all required; additionalProperties: false ✓
- examples: cover modifier+key combos and CSS selector patterns ✓

**Tool count discipline:** The tool list header docstring updated to mention v0.8.12; the dispatch test counts updated from 18 → 19; the tool_names_locked test asserts `leid.press_on in names`.

**Verdict:** **PASS** — Registry entry is complete and correctly placed.

---

## VIII. D-14 LeidClient Byte-Untouched

Verified by `git diff c41cb9b..HEAD -- src/heretic/skilningr/senses/leid/client.py` — empty.

**Verdict:** **PASS** — D-14 holds for the 16th consecutive milestone.

---

## IX. Test Coverage

**Client tests (TestPressOn, 9 tests in `tests/test_leid_playwright_client.py`):**

1. `test_press_on_unknown_session_raises_expired` — B-16 boundary
2. `test_press_on_calls_locator_first_press` — D-154 / B-30 primitive
3. `test_press_on_passes_key_and_timeout` — kwarg propagation (D-155)
4. `test_press_on_timeout_raises_press_on_element_not_found` — B-30 timeout branch
5. `test_press_on_browser_error_raises_connection_error` — B-30 non-timeout branch
6. `test_press_on_returns_post_action_url_and_title` — D-160 return shape
7. `test_press_on_updates_last_activity` — D-159 / B-17 activity update
8. `test_press_on_does_not_call_page_evaluate` — B-10 inherited
9. `test_press_on_supports_modifier_keys` — D-153 inherited (modifier syntax)

**Helper extension:** `_install_fake_playwright` got a `press_side_effect` parameter and the fake locator's first now exposes a `press` AsyncMock. Failure-path coverage is symmetric with `click_side_effect` and `fill_side_effect`.

**Sense tests (in `tests/test_leid_sense.py`):**

1. `test_tool_definitions_when_enabled` — count 18 → 19
2. `test_tool_names_locked` — asserts `leid.press_on` in names
3. `test_dispatch_press_on_routes_to_playwright_client` — dispatch happy path with all three kwargs
4. `test_dispatch_press_on_element_not_found_returns_invalid_arguments` — D-157 error mapping verified at the dispatch boundary

**Full suite:** 1631 passed, 9 skipped (was 1620 → +11). Zero regressions. 11.38s.

**Coverage matrix:**

| Dimension | Covered |
|---|---|
| Happy path (primitive + kwargs) | yes |
| Selector-miss (B-30 timeout branch) | yes |
| Browser failure (B-30 non-timeout branch) | yes |
| Unknown session (B-16) | yes |
| Activity update (D-159) | yes |
| Post-action read (D-160) | yes |
| B-10 (no page.evaluate) | yes |
| Modifier keys | yes |
| Error code mapping at dispatch boundary (D-157) | yes |
| Tool registry surface (D-156 indirectly) | yes |
| Symmetry with click/type | implicit (shape match) |

**Verdict:** **PASS** — Coverage is complete.

---

## X. Findings

**BLOCKER:** 0
**SERIOUS:** 0
**NOTABLE:** 0
**NIT:** 0

**Twelfth consecutive zero-findings audit in the v0.8 umbrella.**

---

## XI. Verdict

**PASSES SCRUTINY.** v0.8.12 is a clean, additive refinement that:

- adds `press_on` as the third element-targeted interactive primitive, completing the symmetry with click and type;
- introduces a sibling error class (`LeidPressOnElementNotFoundError`) maintaining the discipline that each gesture's selector failure is distinguishable;
- maps the new class to `INVALID_ARGUMENTS` consistent with click and type;
- preserves D-14 (LeidClient byte-untouched, 16th consecutive milestone);
- preserves D-130 (operator infrastructure remains operator infrastructure; no new agent surface that could be confused with one);
- ships with exhaustive coverage at the client primitive, the sense dispatch, and the registry surface;
- is structurally orthogonal to `leid.press` (v0.8.4), with clear use-case separation.

The refinement is sealed and ready for DEVLOG.

— Sólrún Hvítmynd, 2026-05-11
