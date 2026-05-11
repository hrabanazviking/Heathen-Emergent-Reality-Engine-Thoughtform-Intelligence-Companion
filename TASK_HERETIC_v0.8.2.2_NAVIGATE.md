# TASK — HERETIC v0.8.2.2 — leid.navigate (Innan Hurðar extension)

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-10** (immediately after v0.8.2.1 leid.type sealed at `c1897d5`)
>
> **Codename:** **NONE** — fifth unnamed extension. Same Innan Hurðar disposition; the body, already inside one room, walks to a new room without leaving the building.
>
> **Umbrella milestone:** v0.8 *Opið Vef* — fifth slice within the umbrella.
>
> **Mythic Engineering mode:** AUTONOMOUS. Thirteenth milestone in the autonomous arc that began 2026-05-09.
>
> **STATUS — 2026-05-10:** **SHIPPED + AUDITED + SEALED.** All seven waves closed; Wave 6 cleanup skipped (Auditor returned **zero findings** — second consecutive in v0.8 umbrella).
>
> **Final HEAD:** `898a4d3` (Auditor close) — final Scribe push will advance.
>
> **Test status:** Leid 179 + 2 skip (was 167 + 2 — `+12`). Full suite **1500 + 9 skip** (was 1488 + 9). Suite has crossed 1500 tests. Zero regressions.
>
> **Auditor verdict:** PASSES SCRUTINY (0/0/0/0). Second consecutive zero-findings audit. See `docs/audit/AUDIT_v0.8.2.2_NAVIGATE.md`.
>
> **DEVLOG:** Entry 27 — `docs/DEVLOG.md`.

---

## 1. Task scope

Add ONE new tool to the Innan Hurðar interactive disposition:

> **`leid.navigate(session_id, url) → {session_id, previous_url, final_url, title}`** —
>
> Navigates an existing open session to a new URL. The session's identity, cookies, and localStorage all survive the navigation (within-session state IS the point). Validates the new URL against `url_allowlist_patterns` (B-12 inherited). Uses the same `wait_until` and timeout config as `open_session`. Returns the previous URL so the agent has a coherent record of the navigation.

Behaviour mirrors `open_session`'s navigation phase, but reuses the existing session's `(pw, browser, context, page)` quartet rather than launching a new one. No new resources allocated; no concurrency-cap interaction; no eviction-by-cap.

The httpx tools, render_url, screenshot, and the v0.8.2 + v0.8.2.1 session tools are **unchanged**. v0.8.2.2 is purely additive.

---

## 2. Out of scope

| Capability                  | Slice    | Reason for deferral                                       |
|-----------------------------|----------|-----------------------------------------------------------|
| `leid.session_render`       | v0.8.x  | Re-extracting rendered text mid-session — separate slice |
| `leid.session_screenshot`   | v0.8.x  | Mid-session screenshot — separate slice                   |
| `leid.go_back` / `go_forward` | v0.8.x | Browser history navigation — distinct primitive           |
| `leid.reload`               | v0.8.x  | Reload current page — distinct primitive                  |
| Final-URL allowlist re-check after redirect | v0.8.x | Pre-existing concern across all browser tools; v0.8.2.2 mirrors current behaviour |

---

## 3. Architectural decisions

| #  | Decision | Choice | Rationale |
|----|---|---|---|
| D-60 | Primitive | `await session.page.goto(url, wait_until=..., timeout=...)` — same as open_session navigation | Stateful navigation reuses the same Playwright primitive; only the lifecycle is different (no launch, no teardown) |
| D-61 | URL validation | Reuses `_validate_url` (allowlist + HTTPS-only) | Single source of truth — every URL the body visits in any tool goes through the same gate |
| D-62 | Session identity | session_id UNCHANGED by navigation | The session is the browser context, not the page URL. Agents that store the session_id keep using it |
| D-63 | Cookie + localStorage state | PERSISTS across navigation (that's what a session IS) | B-3 already strengthened at the session boundary in v0.8.2; this is a confirmation, not a new invariant |
| D-64 | previous_url field | Capture `session.page.url` BEFORE the new goto, return as `previous_url` | Lets the agent reason about navigation history without polling session_status |
| D-65 | Timeout config | Reuses `LeidConfig.browser_navigation_timeout_seconds` (same field as open_session) | Open and navigate are the same operation lifecycle-wise |
| D-66 | Error mapping | TimeoutError → LeidTimeoutError; PlaywrightError → LeidConnectionError; status >= 400 → LeidHttpError; same as open_session navigation phase | Reuses existing classes; no new error classes needed |
| D-67 | Skald wave | NO new vision-doc addendum — pure unnamed extension within Innan Hurðar | Continuing the v0.8.2.1 precedent. Brief paragraph in OPID_VEF.md §IX continuation if anything |
| D-68 | New B-Invariant | B-20 — navigate respects same URL gate (B-12), session resolution (B-16), activity update (B-17), cleanup discipline as open_session | Single new invariant; reuses prior invariants |

---

## 4. New B-Invariant

| #    | B-Invariant |
|------|-----------|
| B-20 | `navigate()` enforces the same URL-gate-then-session-resolve discipline as the rest of Innan Hurðar: `_validate_url` runs FIRST (B-12 — gate before any browser op); then `evict_expired_sessions`; then `get_session` (B-16 — unknown id raises); then `page.goto` with the open_session navigation contract (B-5 timeout); on success, `session.last_activity_at` is updated (B-17); the session_id is unchanged (D-62). The session's cookie/localStorage state PERSISTS across the navigation (D-63 — that is what a session is). |

B-1..B-19 continue to govern unchanged. The session_id stays valid before, during (briefly between goto failure and cleanup), and after a successful navigate.

---

## 5. Test plan

Extend `tests/test_leid_playwright_client.py` with `TestNavigate` class.

| Test | Asserts |
|---|---|
| `test_navigate_validates_url_before_session_lookup` | B-12 — invalid URL raises BEFORE session_id is even looked up |
| `test_navigate_unknown_session_raises_expired` | B-16 |
| `test_navigate_calls_page_goto_with_new_url` | D-60 — page.goto is called with the new URL |
| `test_navigate_returns_previous_and_final_url` | D-64 — result has previous_url + final_url |
| `test_navigate_returns_session_id_unchanged` | D-62 — session_id in result matches input |
| `test_navigate_timeout_raises_leid_timeout` | B-5 — TimeoutError → LeidTimeoutError |
| `test_navigate_network_error_raises_leid_connection_error` | D-66 |
| `test_navigate_http_error_raises_leid_http_error` | D-66 |
| `test_navigate_updates_last_activity` | B-17 / B-20 |
| `test_navigate_does_not_call_page_evaluate` | B-10 inherited |
| `test_navigate_rejects_http_when_allow_http_false` | B-9 / B-12 |

`tests/test_leid_sense.py`:
| `test_dispatch_navigate_routes_to_playwright_client` | Routing |
| Update tool count check 9 → 10 |
| Update tool names locked check |

---

## 6. Wave plan

| Wave | Role | Deliverable |
|---|---|---|
| 0 | Runa (this file) | TASK file |
| 1 | Skald (very brief) | OPID_VEF.md §IX continuation paragraph (no new section) |
| 2 | Cartographer | DATA_FLOW.md §4.12.2.6 — navigate flow |
| 3 | Architect | INTERFACE.md §12.8 + B-20 + 1 tool def |
| 4 | Forge | navigate() method + sense routing + 11 new tests + 1 dispatch test |
| 5 | Auditor | AUDIT_v0.8.2.2_NAVIGATE.md |
| 6 | Forge cleanup | If needed |
| 7 | Scribe | DEVLOG entry 27 + seal + memory refresh |

---

## 7. Exit criteria (all met; this milestone is SEALED)

- [x] `navigate()` method on `PlaywrightLeidClient` — `5caabe8`
- [x] `leid.navigate` registered in `LEID_TOOL_DEFINITIONS` — `16a87cd`
- [x] `LeidSense._route` dispatches `leid.navigate` — `5caabe8`
- [x] No new error classes (reuses 5 existing ones) — confirmed
- [x] B-20 added to INTERFACE.md §12.8 — `16a87cd`
- [x] All 167 existing leid tests pass unchanged — verified at `5caabe8`
- [x] 11 new navigate tests passing — `5caabe8`
- [x] 1 new dispatch test passing — `5caabe8`
- [x] `docs/cartography/DATA_FLOW.md` §4.12.2.6 exists — `9c1ad75`
- [x] `docs/vision/OPID_VEF.md` §IX continuation paragraph exists — `63867fe`
- [x] `docs/audit/AUDIT_v0.8.2.2_NAVIGATE.md` PASSES SCRUTINY (0/0/0/0) — `898a4d3`
- [x] DEVLOG entry 27 written — Wave 7 (this seal)
- [x] All commits pushed to `development` — final Scribe push closes
