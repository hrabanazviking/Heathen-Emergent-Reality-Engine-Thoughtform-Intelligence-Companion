# TASK — HERETIC v0.8.7 — leid.reload (Innan Hurðar extension)

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-11** (immediately after v0.8.6 session re-extract pair sealed at `b9389c6`)
>
> **Codename:** **NONE** — tenth unnamed extension within Innan Hurðar.
>
> **Umbrella milestone:** v0.8 *Opið Vef* — tenth slice within the umbrella.
>
> **Mythic Engineering mode:** AUTONOMOUS. Eighteenth milestone in the autonomous arc.

---

## 1. Task scope

Add ONE new tool — refresh the current session page:

> **`leid.reload(session_id) → {session_id, current_url, title}`** —
>
> Refreshes the current page of an open session — equivalent to the user pressing F5 or the browser's reload button. The session's identity, cookies, and localStorage all survive the reload (within-session state IS the point). The page's URL stays the same (in normal cases) but its content is re-fetched from the server. Same wait_until + timeout config as `navigate`. Reuses navigation timeout + load state.

This rounds out the motion vocabulary inside the door:

| Motion tool | Direction |
|---|---|
| `leid.navigate(url)` | Forward to a new URL |
| `leid.go_back()` | Back one step in history |
| `leid.go_forward()` | Forward one step in history |
| **`leid.reload()`** | **In place — re-fetch current page** |

The httpx tools, render_url, screenshot, the v0.8.2.x session tools, and the v0.8.5/v0.8.6 paired tools are **unchanged**. v0.8.7 is purely additive.

---

## 2. Out of scope

| Capability                  | Slice    | Reason for deferral                                       |
|-----------------------------|----------|-----------------------------------------------------------|
| Hard reload (skip cache)    | v0.8.x   | Playwright's reload accepts no `bypass_cache` parameter — that's a `keyboard.press("Control+Shift+R")` pattern instead |
| Reload-and-extract combined | v0.8.x   | Agent achieves this via `reload()` then `session_render()` — no need for a fused primitive |
| Final-URL allowlist re-check | v0.8.x  | Pre-existing concern across all browser tools |

---

## 3. Architectural decisions

| #  | Decision | Choice | Rationale |
|----|---|---|---|
| D-107 | Primitive | `await session.page.reload(wait_until=..., timeout=...)` | Playwright's canonical reload primitive. Returns `Response | None` (None in unusual cases like data: URLs that cannot be reloaded; treated as "no HTTP status to check") |
| D-108 | Timeout + load_state | Reuses `browser_navigation_timeout_seconds` + `browser_load_state` | Reload is functionally a navigation (re-fetch + render); same operator-controlled bounds. No new config fields |
| D-109 | URL allowlist gate | NOT applied (no URL parameter) | Same posture as go_back/go_forward (D-92): the URL the body is at was already allowlist-checked when first navigated to. Reload is in-place — the URL doesn't change |
| D-110 | New error classes | NONE — reuses existing classes | LeidSessionExpiredError, LeidTimeoutError, LeidConnectionError, LeidHttpError. Same mapping as navigate / go_back / go_forward |
| D-111 | Return shape | `{session_id, current_url, title}` — minimal | No `previous_url` because reload is in-place (previous and current URL are conceptually the same). No `moved` because reload is not a probe-and-act primitive — either it succeeded or it failed |
| D-112 | Skald wave | NO new vision-doc addendum — tenth unnamed extension | Continuing the established pattern. Brief paragraph in OPID_VEF.md §IX continuation |
| D-113 | New B-Invariant | B-25 — reload respects same session/timeout/activity discipline as navigate | Single new invariant; reuses prior infrastructure |

---

## 4. New B-Invariant

| #    | B-Invariant |
|------|-----------|
| B-25 | `reload()` enforces the same session/timeout discipline as `navigate()` and history-nav: `evict_expired_sessions` runs first; unknown session_id raises `LeidSessionExpiredError`; `page.reload()` is awaited with `wait_until=config.browser_load_state` and `timeout=config.browser_navigation_timeout_seconds * 1000`; HTTP 4xx/5xx during reload maps to `LeidHttpError`; on success, `session.last_activity_at` is updated. Cookies + localStorage persist across reload — that's intrinsic to refresh semantics, not a new invariant. |

B-1..B-24 continue to govern unchanged.

---

## 5. Test plan

Extend `tests/test_leid_playwright_client.py` with `TestReload` class (~9 tests):

- `test_reload_unknown_session_raises_expired` — B-16
- `test_reload_calls_page_reload_with_load_state_and_timeout` — D-107
- `test_reload_returns_current_url_and_title` — D-111
- `test_reload_returns_session_id_unchanged` — session identity preserved
- `test_reload_handles_none_response` — D-107 None response (no HTTP check)
- `test_reload_timeout_raises_leid_timeout` — B-5 inherited via B-25
- `test_reload_http_error_raises_leid_http_error` — D-110
- `test_reload_network_error_raises_leid_connection_error` — D-110
- `test_reload_updates_last_activity` — B-17 / B-25
- `test_reload_does_not_call_page_evaluate` — B-10 inherited

`tests/test_leid_sense.py`:
- `test_dispatch_reload_routes_to_playwright_client` — routing
- Update tool count check 16 → 17
- Update tool names locked check

---

## 6. Wave plan

| Wave | Role | Deliverable |
|---|---|---|
| 0 | Runa (this file) | TASK file |
| 1 | Skald (very brief) | OPID_VEF.md §IX continuation paragraph |
| 2 | Cartographer | DATA_FLOW.md §4.12.2.11 — reload flow |
| 3 | Architect | INTERFACE.md §12.13 + B-25 + 1 tool def |
| 4 | Forge | reload() method + sense routing + 10 method tests + 1 dispatch test |
| 5 | Auditor | AUDIT_v0.8.7_RELOAD.md |
| 6 | Forge cleanup | If needed |
| 7 | Scribe | DEVLOG entry 32 + seal + memory refresh |

---

## 7. Exit criteria

- [ ] `reload()` method on `PlaywrightLeidClient`
- [ ] `leid.reload` registered in `LEID_TOOL_DEFINITIONS`
- [ ] `LeidSense._route` dispatches `leid.reload`
- [ ] No new error classes (D-110)
- [ ] No new config fields (D-108)
- [ ] B-25 added to INTERFACE.md §12.13
- [ ] All 240 existing leid tests pass unchanged
- [ ] At least 9 new method tests passing
- [ ] 1 new dispatch test passing
- [ ] `docs/cartography/DATA_FLOW.md` §4.12.2.11 exists
- [ ] `docs/vision/OPID_VEF.md` §IX continuation paragraph exists
- [ ] `docs/audit/AUDIT_v0.8.7_RELOAD.md` PASSES SCRUTINY
- [ ] DEVLOG entry 32 written
- [ ] All commits pushed to `development`
