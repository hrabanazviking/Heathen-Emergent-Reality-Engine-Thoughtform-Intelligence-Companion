# TASK — HERETIC v0.8.2 INNAN HURÐAR (Stateful Sessions + First Click)

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-10** (immediately after v0.8.1 *Mynd af Vegferð* sealed at `e653e25`)
>
> **Codename (Skald to seal at Wave 1):** *Innan Hurðar* — "inside the door." Where v0.8.0 and v0.8.1 had the body walking past the door and looking through, v0.8.2 has the body **crossing the threshold** and **staying** — keeping a session open across multiple actions, touching what is in front of it.
>
> **Umbrella milestone:** v0.8 *Opið Vef* — third slice within the umbrella, but this slice introduces a NEW DISPOSITION (statefulness), so it earns its own Skald codename in addition to staying under the umbrella name.
>
> **Mythic Engineering mode:** AUTONOMOUS. Volmarr offered hugs and "continue" — eleventh milestone in the autonomous arc that began 2026-05-09.

---

## 1. Task scope

Open the stateful-interaction sub-section of the v0.8 umbrella with FOUR new tools and a new infrastructural class:

> **Four new tools:**
>   1. `leid.open_session(url) → {session_id, final_url, title}` — opens a stateful browser session at the URL; the page stays alive until explicitly closed or until idle/absolute timeout.
>   2. `leid.session_status(session_id) → {state, url, title, opened_at, last_activity_at, age_seconds, idle_seconds}` — non-mutating health/status check on an open session.
>   3. `leid.click(session_id, selector) → {selector, clicked, current_url, current_title}` — clicks the first element matching the CSS selector inside the open session.
>   4. `leid.close_session(session_id) → {session_id, closed}` — closes the session, releases all browser resources.

> **One new infrastructural class:** `BrowserSessionManager` — owns the dictionary of open sessions, enforces concurrency caps and timeouts, performs idle-eviction and absolute-eviction.

This is the SMALLEST cohesive vertical slice that proves stateful sessions: open → click → close. Subsequent tools (`type`, `navigate-in-session`, `query`) follow in v0.8.2.1 / v0.8.2.2 / v0.8.3.

The httpx tools, `render_url`, and `screenshot` are **unchanged**. v0.8.2 is purely additive.

**Bonus payload:** **Audit M-1 from v0.8.1 CLOSED at this milestone.** Explicit `try/except (PlaywrightError, PlaywrightTimeoutError)` mapping added around all four `Page.*` call sites currently in use: `page.goto` (already typed via the v0.8.0/v0.8.1 wrappers), `page.content` (NEW typing — closes M-1 for render_url), `page.screenshot` (NEW typing — closes M-1 for screenshot), `page.click` (NEW typing — born already-correct at this milestone). The Auditor recommended bundling this into v0.8.2; that recommendation is honoured.

---

## 2. Out of scope (deferred to later v0.8.x slices)

| Capability                        | Slice    | Reason for deferral                                  |
|-----------------------------------|----------|------------------------------------------------------|
| `leid.type`                       | v0.8.2.1 | Distinct enough — input composition vs DOM activation; small focused slice |
| `leid.navigate` (in-session)      | v0.8.2.2 | Useful but not minimal-vertical — open_session already navigates once |
| `leid.query`                      | v0.8.3   | CSS selector + attribute extraction (different semantics from click) |
| `leid.session_render` (in-session HTML) | v0.8.x | Re-extract rendered text from a live session |
| `leid.session_screenshot` (in-session) | v0.8.x | Mid-session screenshot (vs the stateless v0.8.1 screenshot) |
| Multi-tab support                 | v0.8.x+  | Single page per session at v0.8.2                    |
| Wait-for-selector / wait-for-event | v0.8.x  | The agent can poll session_status; native waits later |
| Cookie persistence                | NEVER    | B-3 still holds: each SESSION uses a fresh context, no cookies survive close_session |

---

## 3. Architectural decisions (Architect to confirm at Wave 3)

### 3.1 Session lifecycle decisions

| #  | Decision | Choice | Rationale |
|----|---|---|---|
| D-26 | Session ID format | UUID4 hex string (32 chars), prefixed with `"leid-"` for log readability | Cryptographically unguessable; distinguishable from other session-shaped IDs |
| D-27 | Session storage | In-memory `dict[str, _LeidSession]` on `BrowserSessionManager` | Process-local; sessions naturally die with the process. No persistence — operator restart = sessions gone |
| D-28 | Concurrency cap | New `LeidConfig.browser_max_concurrent_sessions: int = 3` | Defensive default; opens too many Chromium processes is the foot-gun |
| D-29 | Idle timeout | New `LeidConfig.browser_session_idle_timeout_seconds: int = 300` (5 min) | Sessions with no activity for 5 minutes are evicted. Last-activity is updated on every successful tool call |
| D-30 | Absolute timeout | New `LeidConfig.browser_session_max_lifetime_seconds: int = 1800` (30 min) | Hard ceiling — even active sessions die after 30 minutes. Prevents indefinite resource holding |
| D-31 | Eviction trigger | Lazy-eviction at the start of every `open_session`, `session_status`, `click`, `close_session` call | No background task; the manager checks "are any sessions overdue?" on each call. Simpler than asyncio task scheduling; correctness is operator-perceivable (sessions visibly closed when next call happens) |
| D-32 | Eviction observability | When a session is evicted, the next call referencing its ID returns `LeidSessionExpiredError → SENSE_UNAVAILABLE`. The eviction itself logs at WARNING level | Agent learns its session is gone; operator sees the eviction in logs |
| D-33 | Cap-exceeded behaviour | `open_session` with N already-active sessions and N >= cap → `LeidSessionLimitError → SENSE_UNAVAILABLE` (NOT silently evicting oldest) | Explicit refusal is clearer than silent invalidation of agent state |
| D-34 | Session struct shape | Internal `_LeidSession` dataclass holding `session_id`, `pw`, `browser`, `context`, `page`, `created_at`, `last_activity_at` | Tracks everything needed for cleanup + status |
| D-35 | Thread safety | `BrowserSessionManager` uses `asyncio.Lock` for the dict mutations | Async-correct; protects against concurrent open/close interleaving |
| D-36 | Browser lifecycle (this slice) | Launch-per-SESSION (not per-call) — `open_session` calls `async_playwright().start()` + `chromium.launch` + `new_context` + `new_page` + `page.goto`; subsequent `click` calls reuse the page; `close_session` tears down all four | NEW lifecycle distinct from the launch-per-call pattern of `render_url` / `screenshot`. The render_url / screenshot lifecycle is unchanged |
| D-37 | Cleanup on cap reached | `open_session` failing for cap reason does NOT touch other sessions | No silent eviction; honest refusal |
| D-38 | Cleanup on idle/absolute eviction | Eviction calls the same nested `context.close()` → `browser.close()` → `pw.stop()` shape as render_url's `finally`, each defensively wrapped | Same B-7 cleanup discipline at session-close time |
| D-39 | Session shared across tools | All session tools (status, click, future type/navigate) reference the same session_id and operate on the same `_LeidSession.page` | The session IS the page; tools act on it |

### 3.2 Click decisions

| #  | Decision | Choice | Rationale |
|----|---|---|---|
| D-40 | Selector format | CSS selector (Playwright default) | Standard; familiar; supports common tag/class/ID/attribute patterns |
| D-41 | Element matching | `page.locator(selector).first.click()` — clicks the FIRST matching element | Deterministic for ambiguous selectors; agent can refine selector if multiple matches |
| D-42 | Click timeout | New `LeidConfig.browser_click_timeout_seconds: int = 10` (separate from goto timeout) | Click is a quick action; long timeout = bad UX. Separate from navigation timeout because semantically distinct |
| D-43 | Click failure mode | `playwright.async_api.TimeoutError` → `LeidClickElementNotFoundError → INVALID_ARGUMENTS`. `PlaywrightError` (other) → `LeidConnectionError` | The agent often supplies a wrong selector — INVALID_ARGUMENTS tells them "your selector failed", not "the network failed" |
| D-44 | Post-click state read | Return current `page.url` and `page.title()` after click — these may have changed if the click triggered navigation | Lets the agent know if it landed on a new page after click |
| D-45 | Click does NOT wait for navigation | No explicit `page.wait_for_load_state` after click | Click is the action; waiting is a separate concern (deferred to v0.8.x). Agent can re-call `session_status` if it suspects navigation |

### 3.3 M-1 closure decisions (deferred from v0.8.1)

| #  | Decision | Choice | Rationale |
|----|---|---|---|
| D-46 | Wrap `page.content()` in render_url | `try: html = await page.content(); except (PlaywrightError, PlaywrightTimeoutError): raise LeidConnectionError(...)` | Closes M-1 for render_url's content site |
| D-47 | Wrap `page.screenshot()` in screenshot | Same try/except shape; same `LeidConnectionError` raise | Closes M-1 for screenshot's capture site |
| D-48 | Wrap `page.click()` in click | Different mapping — TimeoutError → `LeidClickElementNotFoundError`; other PlaywrightError → `LeidConnectionError` | Born already-correct |
| D-49 | Wrap `page.title()` in click's post-state read | `try: title = await page.title(); except: title = None` (defensive — non-fatal) | Title-read failure should not fail the click |
| D-50 | Existing `page.goto` wrap (already correct) | Unchanged — TimeoutError → LeidTimeoutError; PlaywrightError → LeidConnectionError | Already typed correctly in v0.8.0/v0.8.1 |

### 3.4 Skald disposition decision

| #  | Decision | Choice | Rationale |
|----|---|---|---|
| D-51 | Codename for v0.8.2 | *Innan Hurðar* — "inside the door" — earns its own Skald name (vs the unnamed v0.8.1 extension) | This IS a new disposition: stateful presence vs stateless walk. The body's relationship to the page changes qualitatively. v0.8.1 was "second manner of reporting back from the same walk"; v0.8.2 is "first time the body stays" |
| D-52 | New vision file or addendum? | **Addendum** to OPID_VEF.md (§IX), not a new vision file | Still within the v0.8 umbrella; the new disposition deepens *Opið Vef* rather than replacing it. The pattern "name within addendum, not new file" continues from v0.8.1 |

---

## 4. Session lifecycle flow — proposed Cartographer sketch

```
Lifecycle 1 — open_session
  ┌─────────────────────────────────────────────────────┐
  │ agent → leid.open_session(url)                      │
  │   ↓                                                 │
  │ LeidSense._route → PlaywrightLeidClient.open_session│
  │   ↓                                                 │
  │ _validate_url (B-1: gate before launch)             │
  │   ↓                                                 │
  │ BrowserSessionManager._evict_expired_sessions       │
  │   ↓                                                 │
  │ Check active_count < browser_max_concurrent_sessions│
  │   │ (D-33: explicit refusal if cap reached)         │
  │   ↓                                                 │
  │ async_playwright().start()                          │
  │ chromium.launch(headless=True)                      │
  │ browser.new_context(user_agent=...)                 │
  │ context.new_page()                                  │
  │ page.goto(url, wait_until=..., timeout=...)         │
  │   ↓                                                 │
  │ session = _LeidSession(                             │
  │   session_id=uuid4().hex prefixed,                  │
  │   pw=pw, browser=browser, context=context, page=p,  │
  │   created_at=now, last_activity_at=now,             │
  │ )                                                   │
  │   ↓                                                 │
  │ manager._sessions[session_id] = session             │
  │   ↓                                                 │
  │ return {session_id, final_url=page.url, title}      │
  └─────────────────────────────────────────────────────┘

Lifecycle 2 — session_status (non-mutating)
  ┌─────────────────────────────────────────────────────┐
  │ _evict_expired_sessions                             │
  │ session = _sessions.get(session_id) or raise        │
  │ session.last_activity_at = now (this counts as       │
  │   activity — keeps the session alive)               │
  │ return {state, url, title, opened_at, last_activity_│
  │         at, age_seconds, idle_seconds}              │
  └─────────────────────────────────────────────────────┘

Lifecycle 3 — click
  ┌─────────────────────────────────────────────────────┐
  │ _evict_expired_sessions                             │
  │ session = _sessions.get(session_id) or raise        │
  │ try:                                                │
  │   await session.page.locator(selector).first.click( │
  │     timeout=browser_click_timeout_seconds * 1000)   │
  │ except PlaywrightTimeoutError:                      │
  │   raise LeidClickElementNotFoundError               │
  │ except PlaywrightError:                             │
  │   raise LeidConnectionError                         │
  │ session.last_activity_at = now                      │
  │ try: title = await session.page.title()             │
  │ except: title = None                                │
  │ return {selector, clicked: true, current_url,       │
  │         current_title}                              │
  └─────────────────────────────────────────────────────┘

Lifecycle 4 — close_session
  ┌─────────────────────────────────────────────────────┐
  │ session = _sessions.pop(session_id, None)           │
  │ if session is None:                                 │
  │   return {session_id, closed: false} (idempotent)   │
  │ try: await session.context.close()                  │
  │ try: await session.browser.close()                  │
  │ try: await session.pw.stop()                        │
  │ return {session_id, closed: true}                   │
  └─────────────────────────────────────────────────────┘

Eviction (lazy, on every call):
  For each session in _sessions:
    if (now - session.last_activity_at) > idle_timeout: evict
    elif (now - session.created_at) > max_lifetime: evict
  Eviction = same cleanup as close_session, plus log warning.
```

---

## 5. New B-Invariants (Architect to lock at Wave 3)

Additive over B-1..B-11. The B-1..B-11 govern the stateless tools (`render_url`, `screenshot`) and the URL gate; B-12..B-18 govern the session lifecycle.

| #    | B-Invariant |
|------|-----------|
| B-12 | `_validate_url()` is called at the start of `open_session()` BEFORE `async_playwright().start()`. A rejected URL never causes a session to be created or a browser process to spawn. |
| B-13 | `open_session()` checks `len(manager._sessions) < config.browser_max_concurrent_sessions` BEFORE attempting to launch. If at cap, raise `LeidSessionLimitError → SENSE_UNAVAILABLE`. No silent eviction of existing sessions. |
| B-14 | Each open session uses its OWN `pw`, `browser`, `context`, `page` quartet. No sharing of resources between sessions — each session can be torn down independently without affecting others. |
| B-15 | `_evict_expired_sessions()` is called at the START of `open_session()`, `session_status()`, `click()`, and `close_session()`. Eviction uses the same cleanup ordering as `close_session()`: context → browser → pw, each defensively wrapped. |
| B-16 | A `session_id` whose session has been evicted (or never existed) raises `LeidSessionExpiredError → SENSE_UNAVAILABLE` from any tool that references it (status, click, future type/navigate). `close_session` is the exception — it returns `{closed: false}` idempotently for an unknown session_id (allows the agent to safely re-issue close). |
| B-17 | After every successful session-affecting tool call (`status`, `click`, future `type`/`navigate`), `session.last_activity_at` is updated to the current monotonic time. Idle eviction is therefore relative to *real activity*, not just to `open_session` time. |
| B-18 | `close_session()` is idempotent: closing an already-closed or never-existed session_id returns `{closed: false}` and does NOT raise. Closing an active session returns `{closed: true}` and removes it from the manager dict before any cleanup begins (so a concurrent eviction sweep cannot double-clean). |

B-1..B-11 continue to govern `render_url` and `screenshot` unchanged. B-3 (no cookies persist between calls) is **strengthened** at the SESSION level: cookies persist *within* a session (they have to — that's what a session is), but each session's context is still fresh, and `close_session` discards all of them.

---

## 6. New error classes (Architect to add at Wave 3)

All subclass `LeidError` (existing parent), all map to specific SENSE_CONTRACTS codes:

| Class                            | Maps to                  | Raised when                                                  |
|----------------------------------|--------------------------|--------------------------------------------------------------|
| `LeidSessionLimitError`          | `SENSE_UNAVAILABLE`      | `open_session` called with cap already reached (B-13)       |
| `LeidSessionExpiredError`        | `SENSE_UNAVAILABLE`      | tool call references unknown / evicted session_id (B-16)    |
| `LeidClickElementNotFoundError`  | `INVALID_ARGUMENTS`      | `page.click(selector)` timed out — selector matched nothing |

Existing classes used as-is:
- `LeidConnectionError` for network errors during click + render_url/screenshot post-M-1 closures
- `LeidPlaywrightUnavailableError` for missing playwright package or chromium binary

---

## 7. Test plan — Forge writes; Auditor verifies

New file: `tests/test_leid_session_manager.py` for the BrowserSessionManager unit tests.
Extension to `tests/test_leid_playwright_client.py`: new `TestSession*` and `TestClick` classes.
Extension to `tests/test_leid_sense.py`: 4 new dispatch tests + 4 new config validation tests.

### 7.1 BrowserSessionManager unit tests (~12 tests)

| Test | Asserts |
|---|---|
| `test_manager_starts_empty` | `len(manager._sessions) == 0` |
| `test_manager_register_increments_count` | After registering one session, `len(manager._sessions) == 1` |
| `test_manager_get_returns_session_or_none` | get() with valid id returns session; with unknown id returns None |
| `test_manager_pop_removes_and_returns` | pop() returns the removed session; second pop returns None |
| `test_manager_evicts_idle_session` | Session with `last_activity_at` past idle timeout is removed; cleanup callbacks called |
| `test_manager_evicts_absolute_lifetime` | Session past max_lifetime is removed even if still active |
| `test_manager_does_not_evict_fresh_session` | Fresh session within both limits stays |
| `test_manager_eviction_does_not_disturb_other_sessions` | One expired, one fresh: only expired removed |
| `test_manager_at_cap_raises` | `check_capacity()` at cap raises `LeidSessionLimitError` |
| `test_manager_under_cap_passes` | check_capacity under cap returns silently |
| `test_manager_cleanup_callbacks_run_in_order` | Eviction calls context.close → browser.close → pw.stop |
| `test_manager_cleanup_callback_failure_does_not_block_others` | If context.close raises, browser.close + pw.stop still run |

### 7.2 PlaywrightLeidClient session tests (~16 tests in `TestOpenSession`, `TestSessionStatus`, `TestClick`, `TestCloseSession`)

| Test | Asserts |
|---|---|
| `test_open_session_validates_before_launch` | B-12 — invalid URL → no browser spawned |
| `test_open_session_returns_session_id_and_metadata` | Returns dict with session_id, final_url, title |
| `test_open_session_at_cap_raises_session_limit_error` | B-13 — N sessions open + N=cap → LeidSessionLimitError |
| `test_open_session_unavailable_when_playwright_missing` | B-2 still applies |
| `test_open_session_navigation_timeout_raises_leid_timeout` | B-5 still applies |
| `test_open_session_uses_fresh_context_per_session` | B-14 |
| `test_session_status_returns_metadata` | Status fields present |
| `test_session_status_unknown_id_raises_expired` | B-16 |
| `test_session_status_updates_last_activity` | B-17 |
| `test_click_clicks_first_matching_element` | D-41 |
| `test_click_unknown_session_raises_expired` | B-16 for click |
| `test_click_timeout_raises_element_not_found` | D-43 |
| `test_click_network_error_raises_leid_connection_error` | D-43 (other PlaywrightError branch) |
| `test_click_returns_current_url_and_title` | D-44 |
| `test_click_updates_last_activity` | B-17 for click |
| `test_close_session_returns_closed_true_for_active` | B-18 active path |
| `test_close_session_idempotent_for_unknown_id` | B-18 idempotent path — does NOT raise |
| `test_close_session_runs_cleanup_in_order` | context → browser → pw |

### 7.3 M-1 closure tests (closes Audit M-1 from v0.8.1)

| Test | Asserts |
|---|---|
| `test_render_url_page_content_exception_maps_to_connection_error` | D-46 — `page.content` raising PlaywrightError → LeidConnectionError |
| `test_screenshot_page_screenshot_exception_maps_to_connection_error` | D-47 — `page.screenshot` raising PlaywrightError → LeidConnectionError |

### 7.4 Sense dispatch tests (~4)

`test_dispatch_open_session_routes_to_playwright_client`
`test_dispatch_session_status_routes_to_playwright_client`
`test_dispatch_click_routes_to_playwright_client`
`test_dispatch_close_session_routes_to_playwright_client`

### 7.5 Config validation tests (~4)

`test_leid_config_invalid_browser_max_concurrent_sessions_raises`
`test_leid_config_invalid_browser_session_idle_timeout_raises`
`test_leid_config_invalid_browser_session_max_lifetime_raises`
`test_leid_config_invalid_browser_click_timeout_raises`

### 7.6 Existing tests must continue to pass

- 30 `test_leid_client.py` (httpx, untouched)
- 30 `test_leid_sense.py` (will grow by 8 — 4 dispatch + 4 config)
- 46 `test_leid_playwright_client.py` (+ 2 skipped) — render_url + screenshot tests UNCHANGED; new session/click tests appended

---

## 8. New / modified files (Forge inventory)

**New:**
- `src/heretic/skilningr/senses/leid/session_manager.py` — `BrowserSessionManager` + `_LeidSession`
- `tests/test_leid_session_manager.py`

**Modified (additive):**
- `src/heretic/skilningr/senses/leid/playwright_client.py` — 4 new methods (`open_session`, `session_status`, `click`, `close_session`); imports `BrowserSessionManager`; M-1 closures around `page.content` (in `render_url`) and `page.screenshot` (in `screenshot`)
  - **NOTE on D-23 from v0.8.1:** D-23 said "render_url byte-untouched at v0.8.1." That decision was scoped to v0.8.1 only. v0.8.2 explicitly closes M-1 by adding 1-line try/except wraps around `page.content` (in render_url) and `page.screenshot` (in screenshot). The Auditor explicitly invited this in M-1's recommendation. Behavior is preserved (same exception-class outputs); only the typing becomes explicit.
- `src/heretic/skilningr/senses/leid/sense.py` — `_route` adds 4 branches; `_leid_error_code` adds 3 new error class mappings
- `src/heretic/skilningr/senses/leid/tools.py` — append 4 tool definitions
- `src/heretic/skilningr/senses/leid/INTERFACE.md` — §12 contract addendum (B-12..B-18, session lifecycle, click contract)
- `src/heretic/skilningr/senses/leid/errors.py` — re-export 3 new classes
- `src/heretic/skilningr/errors.py` — define 3 new classes
- `src/heretic/skilningr/config_model.py` — 4 new LeidConfig fields + validation
- `docs/cartography/DATA_FLOW.md` — new §4.12.2.4
- `docs/vision/OPID_VEF.md` — §IX addendum
- `tests/test_leid_playwright_client.py` — 16 new session/click tests + 2 M-1 closure tests
- `tests/test_leid_sense.py` — 4 dispatch + 4 config validation

**Untouched (additive):**
- `src/heretic/skilningr/senses/leid/client.py` — v0.7.1 streaming, byte-identical (D-14)
- `PlaywrightLeidClient.__init__` — gains a `_session_manager` attribute (lazy init), but the constructor signature is unchanged; existing v0.8.0/v0.8.1 callers work unchanged

---

## 9. Wave plan

| Wave | Role | Deliverable |
|---|---|---|
| 0 | Runa | TASK file committed + pushed |
| 1 | Skald (brief) | OPID_VEF.md §IX addendum — *Innan Hurðar* |
| 2 | Cartographer | DATA_FLOW.md §4.12.2.4 — session lifecycle flow |
| 3 | Architect | INTERFACE.md §12 + LeidConfig fields + 3 error classes + 4 tool defs |
| 4 | Forge | session_manager.py + 4 methods on PlaywrightLeidClient + sense routing + tests + M-1 closures |
| 5 | Auditor | AUDIT_v0.8.2_INNAN_HURDAR.md — verify B-1..B-18 + L/render_url non-regression + M-1 closure verification |
| 6 | Forge cleanup | Address findings; skip if clean |
| 7 | Scribe | DEVLOG entry 25 + TASK seal + memory refresh + final push |

---

## 10. Exit criteria (this milestone is sealed when all are true)

- [ ] `BrowserSessionManager` class implemented with eviction logic
- [ ] 4 new methods on `PlaywrightLeidClient`: `open_session`, `session_status`, `click`, `close_session`
- [ ] 4 new tools registered in `LEID_TOOL_DEFINITIONS`
- [ ] `LeidSense._route` dispatches all 4 new tools
- [ ] 3 new error classes defined and re-exported
- [ ] 4 new `LeidConfig` fields (max_concurrent, idle_timeout, max_lifetime, click_timeout) with validation
- [ ] B-12..B-18 added to INTERFACE.md §12
- [ ] M-1 closure: `page.content` and `page.screenshot` exceptions explicitly typed
- [ ] All 26 existing playwright_client tests pass unchanged
- [ ] All 30 existing test_leid_sense tests pass unchanged
- [ ] All 30 existing test_leid_client tests pass unchanged
- [ ] At least 12 BrowserSessionManager unit tests passing
- [ ] At least 16 session/click integration tests passing
- [ ] 2 M-1 closure tests passing
- [ ] 4 dispatch tests passing
- [ ] 4 config validation tests passing
- [ ] `docs/cartography/DATA_FLOW.md` §4.12.2.4 exists
- [ ] `docs/vision/OPID_VEF.md` §IX addendum exists
- [ ] `docs/audit/AUDIT_v0.8.2_INNAN_HURDAR.md` PASSES SCRUTINY
- [ ] DEVLOG entry 25 written
- [ ] All commits pushed to `development`

---

*Task file authored by Runa Gridweaver Freyjasdottir, opening the third slice of v0.8 Opið Vef. The body now learns to stay inside the door, not just walk past it.*
