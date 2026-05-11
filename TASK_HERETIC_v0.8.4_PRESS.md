# TASK — HERETIC v0.8.4 — leid.press (Innan Hurðar extension)

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-10** (immediately after v0.8.3 leid.query sealed at `9636cec`)
>
> **Codename:** **NONE** — seventh unnamed extension within Innan Hurðar. The body's keyboard finger; same disposition as click/type/query.
>
> **Umbrella milestone:** v0.8 *Opið Vef* — seventh slice within the umbrella.
>
> **Mythic Engineering mode:** AUTONOMOUS. Fifteenth milestone in the autonomous arc.

---

## 1. Task scope

Add ONE new tool — page-level keyboard input:

> **`leid.press(session_id, key) → {session_id, key, pressed, current_url, current_title}`** —
>
> Sends a keyboard key event to the open session's page. Common usage: after `leid.type` fills a search box, call `leid.press(session_id, "Enter")` to submit. Or `leid.press(session_id, "Escape")` to dismiss a modal. Or `leid.press(session_id, "Tab")` to move focus to the next field.

The press is **page-level** — it goes through Playwright's `page.keyboard.press(key)`, which dispatches to whatever element currently has focus. For "press Enter on this specific element," the agent's idiom is:
1. `leid.click(session_id, selector)` — focus the element
2. `leid.press(session_id, "Enter")` — press

(Or for many cases, just `leid.type` followed by `leid.press("Enter")` works because `type` leaves focus on the filled element.)

Playwright's key syntax is supported: single keys (`"Enter"`, `"Tab"`, `"Escape"`, `"ArrowDown"`, `"a"`, `"F5"`, etc.) and modifier combinations (`"Control+A"`, `"Shift+Tab"`, `"Meta+S"`). Per Playwright documentation.

The httpx tools, render_url, screenshot, and the v0.8.2.x session tools are **unchanged**. v0.8.4 is purely additive.

---

## 2. Out of scope

| Capability                  | Slice    | Reason for deferral                                       |
|-----------------------------|----------|-----------------------------------------------------------|
| Element-targeted press (locator.press) | v0.8.x | Agent achieves this via click(selector) then press(key); explicit element-press is a refinement |
| Text input via key sequences | v0.8.x  | leid.type covers text input via locator.fill; per-keystroke typing is a different primitive |
| Mouse events (hover, double-click, drag) | v0.8.x | Distinct primitives; press is keyboard-only |
| Held keys / key combinations beyond Playwright's "+"-syntax | v0.8.x | Playwright's syntax covers virtually all real agent needs |

---

## 3. Architectural decisions

| #  | Decision | Choice | Rationale |
|----|---|---|---|
| D-80 | Primitive | `await session.page.keyboard.press(key)` | Playwright's canonical page-level keyboard primitive. Dispatches to whatever element has focus |
| D-81 | Key syntax | Playwright's native syntax (single keys + Modifier+Key combinations) | Standard; well-documented; no need to invent a new vocabulary |
| D-82 | Focus model | NOT explicitly managed by HERETIC | The agent's intent is "press X"; whether focus is on the element they want is the agent's responsibility (typically established by a prior click or type) |
| D-83 | Timeout | Reuses `LeidConfig.browser_click_timeout_seconds` | Press is a fast interactive action; same operator-controlled bound. No new config field |
| D-84 | New error class | NONE | Reuses LeidConnectionError for genuine browser failures and LeidSessionExpiredError for session issues. Playwright's keyboard.press does NOT raise on "key was unrecognized" or similar — invalid keys produce no event and return successfully (consistent with Playwright's design). So no LeidPressKeyInvalidError needed |
| D-85 | Post-press state read | Read `page.url` and `page.title()` after press (mirrors click D-44/D-49) | Lets the agent know if the press triggered navigation (e.g., Enter submitted a form) |
| D-86 | Skald wave | NO new vision-doc addendum — seventh unnamed extension | Continuing the established pattern. Brief paragraph in OPID_VEF.md §IX continuation if anything |
| D-87 | New B-Invariant | B-22 — press respects same session/timeout/activity discipline as click/type | Single new invariant; reuses prior infrastructure |

---

## 4. New B-Invariant

| #    | B-Invariant |
|------|-----------|
| B-22 | `press()` enforces the same session/activity discipline as the rest of Innan Hurðar interactive tools: `evict_expired_sessions` runs first; unknown session_id raises `LeidSessionExpiredError`; `page.keyboard.press(key)` is awaited (Playwright applies its own default action timeout — Playwright does NOT accept a per-call timeout for keyboard.press); on success, `session.last_activity_at` is updated. |

B-1..B-21 continue to govern unchanged. Note the small discipline gap: `keyboard.press` does not accept a Python-level timeout argument (Playwright applies its own internal default action timeout of 30 seconds). This is acceptable — keyboard input is essentially synchronous; a 30-second bound is fine for the rare pathological case where the page is unresponsive.

---

## 5. Test plan

Extend `tests/test_leid_playwright_client.py` with `TestPress` class.

| Test | Asserts |
|---|---|
| `test_press_unknown_session_raises_expired` | B-16 |
| `test_press_calls_keyboard_press_with_key` | D-80 — page.keyboard.press is called with the supplied key |
| `test_press_returns_pressed_true_on_success` | result has `pressed: true` |
| `test_press_returns_current_url_and_title` | D-85 — post-press state read |
| `test_press_returns_session_id_unchanged` | session_id in result matches input |
| `test_press_browser_error_raises_leid_connection_error` | D-84 — PlaywrightError → LeidConnectionError |
| `test_press_updates_last_activity` | B-17 / B-22 |
| `test_press_does_not_call_page_evaluate` | B-10 inherited |
| `test_press_supports_modifier_keys` | D-81 — "Control+A" syntax accepted |

`tests/test_leid_sense.py`:
| `test_dispatch_press_routes_to_playwright_client` | Routing |
| Update tool count check 11 → 12 |
| Update tool names locked check |

---

## 6. Wave plan

| Wave | Role | Deliverable |
|---|---|---|
| 0 | Runa (this file) | TASK file |
| 1 | Skald (very brief) | OPID_VEF.md §IX continuation paragraph |
| 2 | Cartographer | DATA_FLOW.md §4.12.2.8 — press flow |
| 3 | Architect | INTERFACE.md §12.10 + B-22 + 1 tool def |
| 4 | Forge | press() method + sense routing + 9 new tests + 1 dispatch test |
| 5 | Auditor | AUDIT_v0.8.4_PRESS.md |
| 6 | Forge cleanup | If needed |
| 7 | Scribe | DEVLOG entry 29 + seal + memory refresh |

---

## 7. Exit criteria

- [ ] `press()` method on `PlaywrightLeidClient`
- [ ] `leid.press` registered in `LEID_TOOL_DEFINITIONS`
- [ ] `LeidSense._route` dispatches `leid.press`
- [ ] No new error classes (D-84)
- [ ] No new config fields (D-83)
- [ ] B-22 added to INTERFACE.md §12.10
- [ ] All 193 existing leid tests pass unchanged
- [ ] At least 9 new press tests passing
- [ ] 1 new dispatch test passing
- [ ] `docs/cartography/DATA_FLOW.md` §4.12.2.8 exists
- [ ] `docs/vision/OPID_VEF.md` §IX continuation paragraph exists
- [ ] `docs/audit/AUDIT_v0.8.4_PRESS.md` PASSES SCRUTINY
- [ ] DEVLOG entry 29 written
- [ ] All commits pushed to `development`
