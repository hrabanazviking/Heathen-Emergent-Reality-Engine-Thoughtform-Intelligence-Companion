# TASK — HERETIC v0.8.5 — leid.go_back + leid.go_forward (Innan Hurðar extension)

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-10** (immediately after v0.8.4 leid.press sealed at `329a909`)
>
> **Codename:** **NONE** — eighth unnamed extension within Innan Hurðar.
>
> **Bundling note:** Two tools (go_back + go_forward) are bundled in this single milestone because they are **inverses sharing identical structure**. Splitting them into v0.8.5 + v0.8.6 would produce two near-duplicate task/audit/seal cycles for no benefit. Same disposition; same B-invariant; same return shape; one Forge implementation with a shared private helper.
>
> **Umbrella milestone:** v0.8 *Opið Vef* — eighth slice within the umbrella.
>
> **Mythic Engineering mode:** AUTONOMOUS. Sixteenth milestone in the autonomous arc.
>
> **STATUS — 2026-05-10:** **SHIPPED + AUDITED + SEALED.** All seven waves closed; Wave 6 cleanup skipped (Auditor returned **zero findings** — fifth consecutive in v0.8 umbrella).
>
> **Final HEAD:** `aeae4f8` (Auditor close) — final Scribe push will advance.
>
> **Test status:** Leid 222 + 2 skip (was 203 + 2 — `+19`). Full suite 1543 + 9 skip (was 1524 + 9). Zero regressions.
>
> **Auditor verdict:** PASSES SCRUTINY (0/0/0/0). Fifth consecutive zero-findings audit. **First bundled-pair milestone in v0.8 umbrella** shipped cleanly. See `docs/audit/AUDIT_v0.8.5_GO_BACK_FORWARD.md`.
>
> **DEVLOG:** Entry 30 — `docs/DEVLOG.md`.

---

## 1. Task scope

Add TWO paired tools — browser history navigation:

> **`leid.go_back(session_id) → {session_id, moved, previous_url, current_url, title}`** —
>
> Navigates the open session BACKWARD in the browser's history stack — equivalent to the user pressing the back button. Returns `moved: false` (NOT an error) when there is no history to go back to (the session is at its first page).

> **`leid.go_forward(session_id) → {session_id, moved, previous_url, current_url, title}`** —
>
> Navigates the open session FORWARD in the browser's history stack — equivalent to the user pressing the forward button. Returns `moved: false` when there is no history to go forward to (typical state after a fresh navigation that did not branch from history).

Both share identical:
- B-invariant (B-23)
- Return shape (with `moved` boolean)
- Failure-mode mapping (no new error classes)
- Implementation primitive (`page.go_back` / `page.go_forward` — both Playwright-native)
- Configuration reuse (`browser_navigation_timeout_seconds`, `browser_load_state`)

The httpx tools, render_url, screenshot, and the v0.8.2.x session tools are **unchanged**. v0.8.5 is purely additive.

---

## 2. Out of scope

| Capability                  | Slice    | Reason for deferral                                       |
|-----------------------------|----------|-----------------------------------------------------------|
| `leid.reload`               | v0.8.x   | Distinct primitive (`page.reload`); separate slice if needed |
| Final-URL allowlist re-check after history navigation | v0.8.x | Pre-existing concern across all browser tools (see D-92); v0.8.5 inherits the established posture |
| History-stack length introspection | v0.8.x | Playwright doesn't easily expose this; would need page.evaluate which violates B-10 |
| Direct go-to-N-entries-back | v0.8.x   | `page.go_back()` is single-step; multi-step would be agent-side iteration |

---

## 3. Architectural decisions

| #  | Decision | Choice | Rationale |
|----|---|---|---|
| D-88 | Primitives | `await session.page.go_back(wait_until=..., timeout=...)` and `await session.page.go_forward(wait_until=..., timeout=...)` | Playwright's canonical history-navigation primitives. Both return `Response | None` (None when no history entry exists in that direction) |
| D-89 | "No history" semantics | Returns `{moved: false, ...}` — **NOT an error** | Same divergence rationale as `query`'s D-72: history-nav is a probe-and-act primitive. Failing loudly when "already at the start" is bad UX — the agent's "go back if possible" intent is naturally expressed as a try-and-check |
| D-90 | Shared private helper | Implement `_go_history(session_id, direction: Literal["back", "forward"])` once; `go_back` and `go_forward` are thin wrappers | DRY without over-engineering — the two methods differ by one Playwright call |
| D-91 | Timeout + load_state | Reuses `browser_navigation_timeout_seconds` and `browser_load_state` (same as `open_session` and `navigate`) | History nav is functionally a navigation; same operator-controlled bounds. No new config fields |
| D-92 | URL allowlist gate | NOT applied to history nav — accepted limitation | The URLs in the history stack were already allowlist-checked when the body originally navigated to them. Re-checking would require a post-hoc check (after the page has already moved), which introduces unwind problems. This is consistent with the pre-existing "final-URL allowlist re-check after redirect" gap that applies to all browser tools and is already deferred. v0.8.5 does NOT widen the gap; it inherits the existing posture |
| D-93 | New error classes | NONE — reuses existing classes | LeidSessionExpiredError for unknown session_id; LeidTimeoutError / LeidConnectionError / LeidHttpError for navigation failures (mirrors navigate's mapping). No "no history" error class because that's not an error (D-89) |
| D-94 | Skald wave | NO new vision-doc addendum — eighth unnamed extension | Continuing the established pattern. Brief paragraph in OPID_VEF.md §IX continuation |
| D-95 | New B-Invariant | B-23 — shared invariant for go_back AND go_forward | Single invariant covers both methods because they share identical structure |
| D-96 | Scope of the bundle | go_back + go_forward ONLY; reload is NOT bundled | Reload is semantically distinct (re-fetch current page vs traverse history); mixing it would dilute the "history nav" framing |

---

## 4. New B-Invariant

| #    | B-Invariant |
|------|-----------|
| B-23 | `go_back()` and `go_forward()` enforce the same session/timeout discipline as `navigate()`: `evict_expired_sessions` runs first; unknown session_id raises `LeidSessionExpiredError`; `page.go_back()` / `page.go_forward()` is awaited with `wait_until=config.browser_load_state` and `timeout=config.browser_navigation_timeout_seconds * 1000`; on success (whether `moved: true` or `moved: false`), `session.last_activity_at` is updated. **DIVERGENCE from B-20**: when Playwright returns `None` (no history in that direction), the tool returns `{moved: false}` rather than raising — history nav is a probe-and-act primitive. **Inheritance**: HTTP 4xx/5xx during history navigation maps to `LeidHttpError` (same as navigate); navigation timeout maps to `LeidTimeoutError`; network error maps to `LeidConnectionError`. Cookies + localStorage persist across history nav (same as navigate — that's what a session is). |

B-1..B-22 continue to govern unchanged. The "no history is not an error" rule is the second deliberate divergence in the v0.8 umbrella (the first being B-21's `query` not-found semantics) — both are read-and-act primitives where "the thing isn't there" is information, not failure.

---

## 5. Test plan

Extend `tests/test_leid_playwright_client.py` with `TestGoBack` and `TestGoForward` classes. Many tests will be near-duplicates of each other; this is intentional — paired-tool tests should be structurally identical so a future Forge can verify symmetry by inspection.

For `TestGoBack` and `TestGoForward` each (~7 tests × 2 = 14):
- `test_go_back_unknown_session_raises_expired` / `test_go_forward_unknown_session_raises_expired` — B-16
- `test_go_back_calls_page_go_back` / `test_go_forward_calls_page_go_forward` — D-88
- `test_go_back_returns_moved_true_on_success` / `test_go_forward_returns_moved_true_on_success`
- `test_go_back_returns_moved_false_when_no_history` / `test_go_forward_returns_moved_false_when_no_history` — D-89 (Playwright returns None)
- `test_go_back_returns_previous_and_current_url` / `test_go_forward_returns_previous_and_current_url`
- `test_go_back_timeout_raises_leid_timeout` / `test_go_forward_timeout_raises_leid_timeout`
- `test_go_back_updates_last_activity` / `test_go_forward_updates_last_activity` — B-17 / B-23

Plus shared tests (~3):
- `test_go_back_does_not_call_page_evaluate` (one regression-guard suffices for both since they share the helper)
- `test_go_back_http_error_raises_leid_http_error` (covers shared error mapping)
- `test_go_back_network_error_raises_leid_connection_error` (covers shared error mapping)

`tests/test_leid_sense.py` (~2):
- `test_dispatch_go_back_routes_to_playwright_client`
- `test_dispatch_go_forward_routes_to_playwright_client`
- Update tool count check 12 → 14
- Update tool names locked check (add both)

Total new tests: ~19.

---

## 6. Wave plan

| Wave | Role | Deliverable |
|---|---|---|
| 0 | Runa (this file) | TASK file |
| 1 | Skald (very brief) | OPID_VEF.md §IX continuation paragraph (one paragraph covers both as a pair) |
| 2 | Cartographer | DATA_FLOW.md §4.12.2.9 — history-nav flow (single section covers both directions) |
| 3 | Architect | INTERFACE.md §12.11 + B-23 + 2 tool defs |
| 4 | Forge | _go_history helper + go_back + go_forward methods + sense routing + ~17 method tests + 2 dispatch tests |
| 5 | Auditor | AUDIT_v0.8.5_GO_BACK_FORWARD.md |
| 6 | Forge cleanup | If needed |
| 7 | Scribe | DEVLOG entry 30 + seal + memory refresh |

---

## 7. Exit criteria (all met; this milestone is SEALED)

- [x] `go_back()` and `go_forward()` methods on `PlaywrightLeidClient` — `79daaac`
- [x] Shared `_go_history()` private helper — `79daaac`
- [x] `leid.go_back` and `leid.go_forward` registered in `LEID_TOOL_DEFINITIONS` — `e1683b5`
- [x] `LeidSense._route` dispatches both — `79daaac`
- [x] No new error classes (D-93) — confirmed
- [x] No new config fields (D-91) — confirmed
- [x] B-23 added to INTERFACE.md §12.11 — `e1683b5`
- [x] All 203 existing leid tests pass unchanged — verified at `79daaac`
- [x] 17 new method tests passing — `79daaac`
- [x] 2 new dispatch tests passing — `79daaac`
- [x] `docs/cartography/DATA_FLOW.md` §4.12.2.9 exists (covers both directions) — `3421150`
- [x] `docs/vision/OPID_VEF.md` §IX continuation paragraph exists — `d6db4ee`
- [x] `docs/audit/AUDIT_v0.8.5_GO_BACK_FORWARD.md` PASSES SCRUTINY (0/0/0/0) — `aeae4f8`
- [x] DEVLOG entry 30 written — Wave 7 (this seal)
- [x] All commits pushed to `development` — final Scribe push closes
