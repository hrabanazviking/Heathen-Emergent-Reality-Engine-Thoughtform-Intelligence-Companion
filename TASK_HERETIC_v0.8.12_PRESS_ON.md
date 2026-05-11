# TASK — HERETIC v0.8.12 — element-targeted press (Innan Hurðar extension)

> **Started: 2026-05-11** (immediately after v0.8.11 sealed at `87c05e1`)
> **Codename:** NONE — fifteenth unnamed extension within Innan Hurðar.
> **Umbrella:** v0.8 *Opið Vef* — fifteenth slice.
> **Mode:** AUTONOMOUS. Twenty-third milestone in the autonomous arc.

---

## 1. Task scope

Add `leid.press_on(session_id, selector, key)`. The existing `press` (v0.8.4) dispatches a key to whatever element currently has focus via `page.keyboard.press(key)`. The new `press_on` targets the FIRST element matching a CSS selector, focuses it, then presses the key — using Playwright's `locator.first.press(key, timeout=...)`. This closes the symmetry with `click` (v0.8.2) and `type` (v0.8.2.1), both of which take a selector and act on the first match.

**New tool:**
- `leid.press_on(session_id, selector, key)` → `{selector, key, pressed, current_url, current_title}`

**New error class:**
- `LeidPressOnElementNotFoundError(LeidError)` — selector matched nothing within `browser_click_timeout_seconds`. Sibling to `LeidClickElementNotFoundError` and `LeidTypeElementNotFoundError`. Mapped to `INVALID_ARGUMENTS`.

**Why a new error class instead of reusing one of the existing two?** Same reason `LeidTypeElementNotFoundError` is distinct from `LeidClickElementNotFoundError` at v0.8.2.1 — the agent can tell which gesture's selector failed. press_on is its own gesture, with its own selector failure semantics.

---

## 2. Out of scope

| Capability | Slice | Reason |
|---|---|---|
| Multi-element press (press on every match) | v0.8.x | First-match convention is consistent with click/type |
| Press sequence (multiple keys in one call) | v0.8.x | Agent can call press_on multiple times if needed |
| Modifier-press without selector | v0.8.x | That's `press` (v0.8.4) — already exists |
| `force=True` to bypass actionability check | v0.8.x | Playwright's default actionability is right default |

---

## 3. Architectural decisions

| # | Decision | Choice |
|---|---|---|
| D-153 | New tool name | `leid.press_on` — distinguishes from `leid.press` (page-level) |
| D-154 | Selector semantics | First match via `page.locator(selector).first` (matches click/type at D-44/D-53) |
| D-155 | Timeout source | Reuses `browser_click_timeout_seconds` (matches D-54 — interactive actions share this bound) |
| D-156 | Error class | New `LeidPressOnElementNotFoundError` — sibling discipline (D-153 from v0.8.2.1) |
| D-157 | Error mapping | INVALID_ARGUMENTS (same as click/type element-not-found) |
| D-158 | Return shape | `{selector, key, pressed, current_url, current_title}` — selector + key both echoed for honesty |
| D-159 | Activity update | press_on counts as activity (matches B-22 / press / B-19 / type) |
| D-160 | Post-action URL/title | Read after press (press_on may trigger navigation, e.g. Enter on a submit button) |
| D-161 | LeidClient byte-untouched | D-14 honoured for the 16th consecutive milestone |
| D-162 | Config byte-untouched | No new config field; reuses browser_click_timeout_seconds |
| D-163 | New B-Invariant | B-30 |

---

## 4. New B-Invariant

| # | B-Invariant |
|---|---|
| B-30 | `press_on(session_id, selector, key)` calls `page.locator(selector).first.press(key, timeout=browser_click_timeout_seconds * 1000)`. PlaywrightTimeoutError on the locator press raises `LeidPressOnElementNotFoundError`; other PlaywrightError raises `LeidConnectionError`. On success, marks session activity and returns post-press URL + title. |

---

## 5. Test plan

New tests in `tests/test_leid_playwright_client.py` (TestPressOn class, ~6 tests):
- `test_press_on_success_calls_locator_first_press` — happy path; selector + key reach locator.first.press; result shape correct
- `test_press_on_session_not_found_raises` — unknown session_id
- `test_press_on_selector_not_found_raises_press_on_element_not_found_error` — PlaywrightTimeoutError → LeidPressOnElementNotFoundError
- `test_press_on_playwright_error_raises_connection_error` — non-timeout PlaywrightError → LeidConnectionError
- `test_press_on_marks_session_activity` — session.mark_activity() called on success
- `test_press_on_returns_post_action_url_and_title` — navigation triggered by press_on (e.g. Enter) reflects in current_url

New tests in `tests/test_leid_sense.py` (~3 tests):
- `test_leid_sense_press_on_tool_definition_present`
- `test_leid_sense_press_on_dispatch_calls_playwright_client_press_on`
- `test_leid_sense_press_on_element_not_found_returns_invalid_arguments`

---

## 6. Wave plan

| Wave | Role | Deliverable |
|---|---|---|
| 0 | Runa | TASK file |
| 1 | Skald (brief) | OPID_VEF §IX continuation |
| 2 | Cartographer | DATA_FLOW §4.12.2.16 |
| 3 | Architect | INTERFACE §12.18 + B-30 + new error class + tool registry entry |
| 4 | Forge | New press_on method + sense dispatch + ~6 client tests + ~3 sense tests |
| 5 | Auditor | AUDIT_v0.8.12 |
| 6 | Forge cleanup | If needed |
| 7 | Scribe | DEVLOG entry 37 |

---

## 7. Exit criteria — ALL MET 2026-05-11

- [x] New `press_on` method on PlaywrightLeidClient
- [x] New `LeidPressOnElementNotFoundError` error class + INVALID_ARGUMENTS mapping
- [x] New `leid.press_on` tool registry entry
- [x] Sense dispatch wired
- [x] B-30 added to INTERFACE
- [x] 9 new client tests (TestPressOn class)
- [x] 2 new sense dispatch tests (+ tool_definitions count + tool_names_locked covers press_on)
- [x] Cartographer + Auditor docs
- [x] DEVLOG entry 37
- [x] All pushed

---

## 8. SEAL — 2026-05-11

**Status:** SEALED. v0.8.12 PASSES SCRUTINY (0/0/0/0) — twelfth consecutive zero-findings audit.

**Final commits:**
- Wave 0–3 (Runa + Skald + Cartographer + Architect — folded): `0d9622d`
- Wave 4 (Forge): `32b3337`
- Wave 5 (Auditor, AUDIT_v0.8.12_PRESS_ON.md): pushed with Scribe seal
- Wave 7 (Scribe, DEVLOG entry 37 + this seal + memory refresh): final push

**Test surface delta:** 1620 → 1631 passing (+11), zero regressions, 11.38s.

**Invariants honoured:**
- D-14 (LeidClient byte-untouched) — 16th consecutive milestone
- D-130 (operator infrastructure unchanged; no new agent surface that could be confused with one)
- B-30 (locator.first.press primitive + error mapping) — newly established
- Sibling discipline (each gesture's selector failure has its own class) — third application

**Fifteenth unnamed extension within Innan Hurðar.** Five named dispositions; fifteen unnamed extensions. The body's interactive triad is complete: click, type, press_on.
