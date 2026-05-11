# TASK — HERETIC v0.8.10 — Final-URL allowlist re-check (Innan Hurðar extension)

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-11** (immediately after v0.8.9 configurable viewport sealed at `8737724`)
>
> **Codename:** **NONE** — thirteenth unnamed extension within Innan Hurðar.
>
> **Umbrella milestone:** v0.8 *Opið Vef* — thirteenth slice within the umbrella.
>
> **Mythic Engineering mode:** AUTONOMOUS. Twenty-first milestone in the autonomous arc.
>
> **Notable departure:** This slice **closes a real sandbox gap** that has been deferred since v0.6.2 and re-flagged in every browser-tool audit since. The agent-facing tool surface is unchanged in shape; the sandbox enforcement gains absolute discipline. **Stateful tools that violate**: the session is auto-closed, a security-grade enforcement of the operator's allowlist.

---

## 1. Task scope

Close the deferred concern that has been carried forward through every browser-tool audit:

> **Currently:** every browser tool validates the INPUT URL against `url_allowlist_patterns` BEFORE navigation. This catches direct attempts to fetch non-allowlisted URLs.
>
> **Gap:** if an allowlisted URL responds with a 3xx redirect to a non-allowlisted URL (or a JavaScript-driven client-side navigation, or any other in-page mechanism that changes `page.url`), the body lands on the non-allowlisted URL without the operator's allowlist being re-checked. The agent then operates on a page the operator never permitted.
>
> **v0.8.10 closes this:** every navigation-completing call (whether stateless or stateful) checks `page.url` AFTER the navigation against the same allowlist + HTTPS-only policy. If the final URL is not allowed, raise `UrlNotAllowedError` (existing class). For STATEFUL tools, the session is auto-closed before the raise — the agent loses the session, but the alternative (the body sitting on a non-allowlisted page until the next call) is unacceptable.

**Seven modification sites:**
1. `render_url` — after `page.goto`, before content extraction
2. `screenshot` — after `page.goto`, before screenshot capture
3. `open_session` — after `page.goto`, before session registration
4. `navigate` — after `page.goto`, before activity update
5. `go_back` (via `_go_history`) — after history nav, before activity update
6. `go_forward` (via `_go_history`) — after history nav, before activity update
7. `reload` — after `page.reload`, before activity update

**The agent-facing tool surface is unchanged.** No new tools, no new tool parameters, no new return shapes. Only the sandbox enforcement gains the missing tooth.

---

## 2. Out of scope

| Capability                  | Slice    | Reason for deferral                                       |
|-----------------------------|----------|-----------------------------------------------------------|
| Per-redirect URL re-check   | v0.8.x  | Playwright doesn't expose intermediate redirect URLs without explicit `request` event hooks; checking the FINAL URL catches the dangerous case |
| Allowlist diff between input and final URL | v0.8.x | The agent doesn't need this; either both are allowed or the navigation is refused |
| Per-tool toggle for the re-check | v0.8.x | The check is unconditional — sandbox security shouldn't be opt-out |
| Detailed redirect chain in error message | v0.8.x | The error names input URL and final URL; the chain between them is invisible to us |

---

## 3. Architectural decisions

| #   | Decision | Choice | Rationale |
|-----|---|---|---|
| D-135 | Check primitive | New private helper `_check_final_url_allowed(url)` — same logic as `_validate_url` but called AFTER navigation | Single source of truth for the check; reuses existing sandbox.url_matches_allowlist + HTTPS-only logic |
| D-136 | Failure class | Reuse `UrlNotAllowedError` (existing class from v0.6.2) | Same semantic — URL not in allowlist; agents that handle the pre-flight check already handle this class |
| D-137 | Stateless tools (render_url, screenshot) | Raise after final-URL check fails. Cleanup is automatic via existing `finally` blocks (B-7) | No special handling needed |
| D-138 | open_session | Raise after final-URL check fails (BEFORE registering the session). The launched browser quartet is cleaned up via the existing was_registered=False branch | Session never gets registered; agent never receives a session_id for a violation |
| D-139 | Stateful navigation tools (navigate, go_back, go_forward, reload) | Auto-close the session BEFORE raising. The session has been compromised (page is on a not-allowlisted URL); the only safe action is to terminate it | Security-grade enforcement: the operator's allowlist is unconditional |
| D-140 | Error message | Names both the INPUT URL (what the agent asked for) and the FINAL URL (where the page actually landed). Notes "session has been closed" for stateful violations | Diagnostic information without exposing the full redirect chain |
| D-141 | New B-Invariant | B-28 — every navigation-completing call re-checks page.url against the allowlist; stateful violations close the session before raising | Single new invariant covers the discipline at all 7 sites |
| D-142 | Skald wave | NO new vision-doc addendum — thirteenth unnamed extension | Continuing the established pattern. Brief paragraph in OPID_VEF.md §IX continuation |
| D-143 | New error classes | NONE (D-136 reuses UrlNotAllowedError) | Same shape as v0.6.2 sandbox |
| D-144 | New config fields | NONE | The check is unconditional; no operator opt-out |
| D-145 | Test impact | Each of 7 sites needs at least one "final URL not allowed" test; stateful tools also test "session is closed after violation" | Substantial test count growth (7 + ~5 stateful-close assertions) |

---

## 4. New B-Invariant

| #    | B-Invariant |
|------|-----------|
| B-28 | Every browser tool that completes a navigation (whether stateless or stateful) re-checks `page.url` against `url_allowlist_patterns` and the HTTPS-only policy AFTER the navigation completes. If the final URL is NOT allowed, `UrlNotAllowedError` is raised. **For stateful tools that violate** (`navigate`, `go_back`, `go_forward`, `reload`): the session is closed (via `manager.close_session(session_id)`) BEFORE the raise — the operator's allowlist is unconditional and a session that has landed on a non-allowlisted URL is terminated as a security measure. **For `open_session`**: the session is never registered (the existing was_registered=False cleanup branch tears down the launched browser quartet). **For stateless tools** (`render_url`, `screenshot`): the existing `finally` cleanup handles teardown. |

B-1..B-27 continue to govern unchanged. **B-28 closes the deferred concern noted in the v0.8.5 audit and earlier ("final-URL allowlist re-check after redirect — pre-existing concern across all browser tools").**

---

## 5. Test plan

**New tests in `tests/test_leid_playwright_client.py`** (~9 tests):

For each affected method:
- `test_render_url_raises_when_final_url_not_allowed` — server-side redirect to evil.com → raise (cleanup auto)
- `test_screenshot_raises_when_final_url_not_allowed` — same
- `test_open_session_raises_when_final_url_not_allowed_and_no_session_registered` — verify session_id is NOT returned and manager._sessions is empty
- `test_navigate_raises_and_closes_session_when_final_url_not_allowed`
- `test_go_back_raises_and_closes_session_when_final_url_not_allowed`
- `test_go_forward_raises_and_closes_session_when_final_url_not_allowed`
- `test_reload_raises_and_closes_session_when_final_url_not_allowed`

Plus shared cross-cutting:
- `test_render_url_does_not_raise_when_final_url_matches_allowlist` — happy path verification (final URL is in allowlist)
- `test_navigate_session_remains_usable_when_final_url_matches_allowlist` — happy path verification

`tests/test_leid_sense.py` — NO new tests needed (no new tools, no new error code mapping; existing UrlNotAllowedError → PERMISSION_DENIED handles the new error path).

---

## 6. Wave plan

| Wave | Role | Deliverable |
|---|---|---|
| 0 | Runa (this file) | TASK file |
| 1 | Skald (very brief) | OPID_VEF.md §IX continuation paragraph |
| 2 | Cartographer | DATA_FLOW.md §4.12.2.14 — final-URL re-check flow + B-28 |
| 3 | Architect | INTERFACE.md §12.16 + B-28 |
| 4 | Forge | New `_check_final_url_allowed()` helper + 7 modification sites + ~9 new tests |
| 5 | Auditor | AUDIT_v0.8.10_FINAL_URL_ALLOWLIST.md (verify uniform application; verify session-close-on-violation; verify NO regression on happy paths) |
| 6 | Forge cleanup | If needed |
| 7 | Scribe | DEVLOG entry 35 + seal + memory refresh |

---

## 7. Exit criteria

- [ ] New private helper `_check_final_url_allowed(url)` on `PlaywrightLeidClient`
- [ ] All 7 navigation-completing call sites apply the check
- [ ] Stateful violations call `manager.close_session(session_id)` before raising
- [ ] No new tools (verified by tool count check unchanged)
- [ ] No new error classes (D-143 — reuses UrlNotAllowedError)
- [ ] No new config fields (D-144)
- [ ] B-28 added to INTERFACE.md §12.16
- [ ] All 279 existing leid tests pass unchanged
- [ ] At least 9 new violation tests passing
- [ ] At least 2 new happy-path verification tests passing
- [ ] `docs/cartography/DATA_FLOW.md` §4.12.2.14 exists
- [ ] `docs/vision/OPID_VEF.md` §IX continuation paragraph exists
- [ ] `docs/audit/AUDIT_v0.8.10_FINAL_URL_ALLOWLIST.md` PASSES SCRUTINY
- [ ] DEVLOG entry 35 written
- [ ] All commits pushed to `development`
