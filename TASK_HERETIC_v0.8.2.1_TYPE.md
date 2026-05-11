# TASK — HERETIC v0.8.2.1 — leid.type (Innan Hurðar extension)

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-10** (immediately after v0.8.2 *Innan Hurðar* sealed at `3066074`)
>
> **Codename:** **NONE** — this is an **unnamed extension** of the v0.8.2 *Innan Hurðar* disposition. The body is not learning a new posture; it is gaining the second half of the interactive gesture it began in v0.8.2 (clicking) — typing. The Skald reserves new names for new dispositions; this is the same disposition with a complementary tool.
>
> **Umbrella milestone:** v0.8 *Opið Vef* — fourth slice within the umbrella. Within v0.8.2's *Innan Hurðar* sub-disposition.
>
> **Mythic Engineering mode:** AUTONOMOUS. Twelfth milestone in the autonomous arc that began 2026-05-09.

---

## 1. Task scope

Add ONE new tool to the Innan Hurðar interactive disposition:

> **`leid.type(session_id, selector, text) → {selector, typed, current_url, current_title}`** —
>
> Fills the first element matching the CSS selector in the open session with the supplied text. Uses Playwright's `locator.fill()` (D-53), which clears the field, focuses it, sets the value, and triggers an `input` event. The agent's "type X into Y" intent is satisfied by the most reliable cross-browser primitive Playwright offers.

Behaviour mirrors `leid.click`:
- Same session_id resolution (B-16)
- Same lazy-eviction-at-call-start (B-15)
- Same activity-update on success (B-17)
- Same `current_url` + `current_title` post-state read (D-44 reused)
- Same Page.* exception typing (D-48 sibling): `PlaywrightTimeoutError` → `LeidTypeElementNotFoundError → INVALID_ARGUMENTS`; other `PlaywrightError` → `LeidConnectionError → EXTERNAL_APP_UNAVAILABLE`

The httpx tools, render_url, screenshot, and the v0.8.2 session tools are **unchanged**. v0.8.2.1 is purely additive.

---

## 2. Out of scope

| Capability                  | Slice    | Reason for deferral                                       |
|-----------------------------|----------|-----------------------------------------------------------|
| Keystroke simulation (`page.type` with delay) | v0.8.x | `locator.fill` covers the canonical use case — most agents want "set this field's value", not keystroke-by-keystroke simulation |
| Special keys (Enter, Tab, etc.) | v0.8.x | Separate primitive (`locator.press`); cleaner as its own tool |
| Form submission              | v0.8.x  | Submit is usually `leid.click('button[type=submit]')` — already supported |
| Navigation in-session        | v0.8.2.2 | Different concern — moving the session to a new URL |
| Selector query / attribute extraction | v0.8.3 | Separate slice |

---

## 3. Architectural decisions

| #  | Decision | Choice | Rationale |
|----|---|---|---|
| D-53 | Type primitive | **`page.locator(selector).first.fill(text, timeout=...)`** | `fill` clears + focuses + sets + dispatches `input` event — what agents want for "set this field's value." Better than `type` (keystroke-by-keystroke) for the canonical case |
| D-54 | Timeout | Reuses `LeidConfig.browser_click_timeout_seconds` (single config field for all interactive operations) | Type and click are both "fast interactive actions"; conflating their timeouts is the right level of granularity. Avoids field proliferation |
| D-55 | New error class | `LeidTypeElementNotFoundError` (sibling to `LeidClickElementNotFoundError`) | Distinct class so the agent can tell selector failures on click apart from selector failures on type — even though both map to `INVALID_ARGUMENTS` |
| D-56 | Selector matching | First match (`.first.fill`) — same as click (D-41) | Deterministic; consistent with click |
| D-57 | Post-fill state read | Read `page.url` and `page.title()` after fill (mirrors click D-44/D-49) | Allows the agent to detect if filling triggered navigation (rare but possible via JS handlers) |
| D-58 | Skald wave | NO new vision-doc addendum — pure unnamed extension within Innan Hurðar | The Skald's pen reserves new codenames for new dispositions. v0.8.2.1 is the same disposition (interactive presence within an open session) with a complementary tool. Following the v0.7.3 / v0.6.3.1 unnamed-extension precedent. The DEVLOG entry IS the documentation of this slice |
| D-59 | Sense routing | One new branch in `LeidSense._route` for `leid.type`; one new error mapping in `_leid_error_code` for `LeidTypeElementNotFoundError → INVALID_ARGUMENTS` | Same shape as click |

---

## 4. New B-Invariant

| #    | B-Invariant |
|------|-----------|
| B-19 | `type()` enforces the same session/cap/timeout discipline as `click()`: `evict_expired_sessions` runs first; unknown session_id raises `LeidSessionExpiredError`; `locator.fill` timeout maps to `LeidTypeElementNotFoundError`; other PlaywrightError maps to `LeidConnectionError`; on success, `session.last_activity_at` is updated. |

B-1..B-18 from v0.8.0/v0.8.1/v0.8.2 continue to govern unchanged. B-10 (no JS injection) holds — `locator.fill` does not let the agent supply JavaScript.

---

## 5. Test plan

Extend `tests/test_leid_playwright_client.py` with `TestType` class. Extend the `_install_fake_playwright` helper to mock `locator.first.fill`.

| Test | Asserts |
|---|---|
| `test_type_fills_first_matching_element` | D-53 — page.locator(selector).first.fill is the call path |
| `test_type_unknown_session_raises_expired` | B-16 applies to type |
| `test_type_timeout_raises_element_not_found` | D-55 — TimeoutError → LeidTypeElementNotFoundError |
| `test_type_network_error_raises_leid_connection_error` | D-55 (other branch) |
| `test_type_returns_current_url_and_title` | D-57 — result has post-fill url + title |
| `test_type_updates_last_activity` | B-17 / B-19 |
| `test_type_passes_text_to_fill` | text parameter reaches locator.fill |
| `test_type_does_not_call_page_evaluate` | B-10 inherited |

`tests/test_leid_sense.py`:
| `test_dispatch_type_routes_to_playwright_client` | new dispatch test |
| `test_type_element_not_found_returns_invalid_arguments_code` | error code mapping |
| Update tool count check 8 → 9 |
| Update tool names locked check |

Existing tests must continue to pass (157 + 2 skip → 165 + 2 skip after v0.8.2.1).

---

## 6. Wave plan (smaller; standard 7 waves)

| Wave | Role | Deliverable |
|---|---|---|
| 0 | Runa (this file) | TASK file |
| 1 | Skald (very brief) | OPID_VEF.md §IX in-section continuation paragraph (NO new section, NO new codename) |
| 2 | Cartographer | DATA_FLOW.md §4.12.2.5 — type flow (small) |
| 3 | Architect | INTERFACE.md §12 addendum (B-19) + 1 new error class + 1 tool def |
| 4 | Forge | type method + sense routing + 8 new tests + 2 sense dispatch tests |
| 5 | Auditor | AUDIT_v0.8.2.1_TYPE.md |
| 6 | Forge cleanup | If needed |
| 7 | Scribe | DEVLOG entry 26 + seal + memory refresh |

---

## 7. Exit criteria

- [ ] `type()` method on `PlaywrightLeidClient`
- [ ] `leid.type` registered in `LEID_TOOL_DEFINITIONS`
- [ ] `LeidSense._route` dispatches `leid.type`
- [ ] `LeidTypeElementNotFoundError` defined + re-exported + mapped to `INVALID_ARGUMENTS`
- [ ] B-19 added to INTERFACE.md §12
- [ ] All 157 existing leid tests pass unchanged
- [ ] At least 8 new type tests passing
- [ ] 2 new dispatch / error-code tests passing
- [ ] `docs/cartography/DATA_FLOW.md` §4.12.2.5 exists
- [ ] `docs/vision/OPID_VEF.md` §IX continuation paragraph exists
- [ ] `docs/audit/AUDIT_v0.8.2.1_TYPE.md` PASSES SCRUTINY
- [ ] DEVLOG entry 26 written
- [ ] All commits pushed to `development`
