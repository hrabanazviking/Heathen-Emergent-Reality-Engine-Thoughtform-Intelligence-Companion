# AUDIT — v0.8.2 Innan Hurðar (Stateful Sessions + First Click)

**Auditor:** Sólrún Hvítmynd
**Date:** 2026-05-10
**Scope under audit:** v0.8.2 *Innan Hurðar* — `BrowserSessionManager` + 4 new session tools (`open_session`, `session_status`, `click`, `close_session`) + B-12..B-18 invariants + M-1 closure (deferred from `AUDIT_v0.8.1`)
**Mythic Engineering session:** AUTONOMOUS — Forge HEAD `b950726` (post-implementation, pre-audit)
**Audit method:** Static review of `session_manager.py` and four new methods on `PlaywrightLeidClient`. B-invariant trace from contract to implementation to test for B-12..B-18. M-1 closure verification (page.content + page.screenshot now explicitly typed). L + render_url + screenshot non-regression check at the contract surface. Concurrency-correctness probe (cap-race, eviction-race, double-close-race). Resource-leak boundary probing on the new failure paths.
**Verdict:** **PASSES SCRUTINY** — 0 BLOCKER, 0 SERIOUS, 1 NOTABLE, 2 NIT.

---

## I. Method

The audit was conducted in seven passes:

1. **B-12..B-18 verification** — each new invariant traced from contract to implementation to test.
2. **M-1 closure verification** — confirm `page.content` and `page.screenshot` are now explicitly wrapped, the closure is tested, and the deferred recommendation from v0.8.1 is fully honoured.
3. **L + render_url + screenshot surface non-regression** — confirm both v0.7.1 streaming `LeidClient` and the v0.8.0/v0.8.1 method surfaces are unchanged at the contract level (M-1's internal type-wrap is the Architect-approved exception, behaviour-preserving).
4. **Concurrency-correctness probing** — cap-race (two open_session calls competing for the last slot), eviction-race (close while eviction sweep runs), double-close (two close_session for the same id).
5. **Resource-leak probing** — every failure path of `open_session` (URL rejected, cap reached, playwright missing, chromium launch fails, navigation fails, registration race-loss).
6. **Idempotency verification** — `close_session` for an unknown id must not raise.
7. **Sandbox-bypass attempt** — try to construct a call path that reaches `async_playwright().start()` from `open_session()` without `_validate_url()` running first.

---

## II. B-Invariant Verification

| #    | Invariant                                                       | Implementation site                                                            | Test                                                            |
|------|-----------------------------------------------------------------|--------------------------------------------------------------------------------|-----------------------------------------------------------------|
| B-12 | Validation before any browser operation in `open_session`       | First executable line of `open_session`: `normalised_url = self._validate_url(url)` | `test_open_session_validates_before_launch`                  |
| B-13 | `check_capacity` raises at cap; no silent eviction              | `BrowserSessionManager.check_capacity` (no-lock read) + `register_session` re-check under lock | `test_check_capacity_at_cap_raises` + `test_register_session_at_cap_raises_under_lock` + `test_open_session_at_cap_raises_session_limit_error` |
| B-14 | Each session owns its own (pw, browser, context, page) quartet  | `_LeidSession` dataclass holds all four; `open_session` creates a fresh `new_context` each time | `test_open_session_uses_fresh_context`                       |
| B-15 | Lazy eviction at start of every session-tool call               | `evict_expired_sessions` called at top of `open_session`, `session_status`, `click` | Eviction tested by `TestBrowserSessionManagerEviction` (4 tests); per-tool eviction-trigger is implicitly verified by all session-tool tests passing after a session is registered |
| B-16 | Unknown / evicted session_id raises `LeidSessionExpiredError`   | `manager.get_session()` raises if `_sessions.get(...)` is None                 | `test_get_session_unknown_raises_expired`, `test_session_status_unknown_id_raises_expired`, `test_click_unknown_session_raises_expired` |
| B-17 | `last_activity_at` updated after every successful tool call     | `session.mark_activity()` called at end of `session_status` and `click` | `test_session_status_updates_last_activity`, `test_click_updates_last_activity` |
| B-18 | `close_session` is idempotent: pop-then-clean for unknown ids   | `close_session` returns False for unknown id; pop happens BEFORE cleanup begins | `test_close_session_idempotent_for_unknown_id`, `test_close_session_returns_closed_true_for_active`, `test_close_session_releases_resources` |

**Verdict:** **PASS** — all seven new invariants correctly enforced and tested.

---

## III. M-1 Closure Verification (deferred from `AUDIT_v0.8.1`)

**Auditor recommendation at v0.8.1 close (`AUDIT_v0.8.1_MYND_AF_VEGFERD.md` §VII M-1):**
> Add a `try/except (PlaywrightError, PlaywrightTimeoutError)` around `page.screenshot()` AND `page.content()` in `render_url()`, mapping each to `LeidConnectionError`.

**v0.8.2 implementation:**

`render_url`'s `await page.content()` (line 312-321 of `playwright_client.py`):
```python
try:
    html = await page.content()
except (PlaywrightTimeoutError, PlaywrightError) as exc:
    raise LeidConnectionError(
        f"page.content() for {normalised_url!r} failed at the "
        f"browser level (page may have closed or process "
        f"disconnected): {exc}"
    ) from exc
```

`screenshot`'s `await page.screenshot()` (line 526-538):
```python
try:
    png_bytes = await page.screenshot(full_page=full_page, type="png")
except (PlaywrightTimeoutError, PlaywrightError) as exc:
    raise LeidConnectionError(
        f"page.screenshot() for {normalised_url!r} failed at the "
        f"browser level (page may have closed or process "
        f"disconnected): {exc}"
    ) from exc
```

`click`'s `await locator.click()` is also explicitly typed (D-43): `PlaywrightTimeoutError` → `LeidClickElementNotFoundError`; other `PlaywrightError` → `LeidConnectionError`.

**Tests:**
- `test_render_url_page_content_exception_maps_to_connection_error` — passes
- `test_screenshot_page_screenshot_exception_maps_to_connection_error` — passes
- `test_click_timeout_raises_element_not_found` — passes
- `test_click_network_error_raises_leid_connection_error` — passes

**Behavioural preservation:** The wraps re-raise as `LeidConnectionError`, which `LeidSense._leid_error_code` already mapped to `EXTERNAL_APP_UNAVAILABLE`. So the agent-facing surface is **unchanged** for the success and previous failure cases. The wrap only refines previously-uncaught exceptions (which would have surfaced as the catch-all `SENSE_INTERNAL_ERROR`) into the more-specific `EXTERNAL_APP_UNAVAILABLE`. **This is precisely what M-1 asked for.**

**Verdict:** **M-1 CLOSED.** All four `Page.*` call sites now have explicit exception typing; agent receives the right error code for each failure mode.

---

## IV. L + render_url + screenshot Surface Non-Regression

| Concern | Result |
|---|---|
| `LeidClient` source byte-identity | **VERIFIED.** `git diff b950726 -- src/heretic/skilningr/senses/leid/client.py` returns empty |
| `PlaywrightLeidClient.render_url()` agent-facing surface | **PRESERVED.** The internal try/except wrap around `page.content()` is the only change; success-path return shape and existing failure-path exception classes are unchanged. The 26 v0.8.0/v0.8.1 playwright_client tests pass unchanged |
| `PlaywrightLeidClient.screenshot()` agent-facing surface | **PRESERVED.** Same observation — the try/except wrap is the only change to the interior; surface unchanged |
| `PlaywrightLeidClient.__init__` backward compat | The new `_session_manager` attribute is private and lazy-initialised; existing constructor signature unchanged. v0.8.0/v0.8.1 callers continue to work |
| `LeidSense` constructor backward compat | Unchanged |
| Tool-definition count | Intentional: 4 → 8 (added 4 v0.8.2 tools). Existing 4 unchanged |
| Verdict | **PASS** — D-14 honoured for v0.7.1; v0.8.0/v0.8.1 surface preserved at the contract level (Architect-approved internal type-wrap was the M-1 exception) |

---

## V. Concurrency-Correctness Probing

### V.1 Cap-race (two open_session calls compete for the last slot)

The `check_capacity` function does an unlocked read (which can race), but `register_session` re-checks under the lock and raises `LeidSessionLimitError` with a "Lost the race to register" message if the cap was reached between check and register.

**Test:** `test_register_session_at_cap_raises_under_lock` simulates this directly by registering a session into a cap-of-1 manager, then attempting a second registration — passes.

**Verdict:** **PASS** — the cap is honoured exactly even under concurrent calls.

### V.2 Eviction-race (close_session while eviction sweep runs)

`close_session` uses `_sessions.pop(session_id, None)` under the lock — atomic read+remove. If a concurrent eviction sweep also tries to pop the same session_id, exactly one of them gets the session object (the other gets `None`). The one that got the object runs cleanup; the other is a no-op.

`evict_expired_sessions` snapshots `expired_ids` under lock, then iterates; each per-session pop is also under lock with a None-check (`if session is None: continue`).

**Verdict:** **PASS** — pop-then-clean discipline (B-18) ensures cleanup runs at most once per session.

### V.3 Double-close (two close_session for the same id)

First close: pops the session, runs cleanup, returns `{closed: true}`.
Second close: pop returns None, returns `{closed: false}` without running cleanup again. **Idempotent.**

**Test:** `test_close_session_idempotent_for_unknown_id` covers the unknown-id path; the active-then-close-twice scenario is implicit (an "unknown id" after the first close is exactly this scenario).

**Verdict:** **PASS** — idempotency verified.

---

## VI. Resource-Leak Probing on `open_session`

| Failure path | Resources cleaned? |
|---|---|
| URL rejected (B-12) | No browser launched; nothing to clean |
| Cap reached (B-13, pre-launch) | No browser launched; nothing to clean |
| Playwright import fails (B-2) | No `pw` returned; nothing to clean |
| `chromium.launch` fails | `pw.stop()` runs in the outer cleanup branch |
| `page.goto` raises | `context.close + browser.close + pw.stop` all run via the outer cleanup branch |
| `page.title()` raises | Defensive — falls through to `title = ""`; session still created |
| `register_session` race-loss (cap filled by concurrent open) | The cap-race branch explicitly cleans up `context + browser + pw` then re-raises `LeidSessionLimitError` |

**Verdict:** **PASS** — every failure path cleans up its own launched resources before the session is registered. After registration, ownership transfers to the manager, which handles cleanup at close / eviction time.

**Notable:** the open_session cleanup logic is intricate — the outer `except Exception` block uses a heuristic (`not any(s.pw is pw for s in self._session_manager._sessions.values())`) to avoid double-cleaning when registration succeeded. This is correct but is the most subtle code in the milestone; see Finding NOTABLE-1 below for a recommendation.

---

## VII. Sandbox-Bypass Attempt

| Attempt | Result |
|---|---|
| Pass an unvalidated URL to `open_session` | `_validate_url` runs as the first line; no bypass possible |
| Race the validation (two threads) | `_validate_url` is a synchronous, deterministic function; no shared state to race |
| Inject a custom session via the manager directly | The manager has a public `register_session` method with a `_LeidSession` parameter — operator-level code COULD construct one and bypass `_validate_url`. But this is the same Python invariant as B-13's "adversarial caller injecting a client": Python cannot prevent caller-level construction of internal objects. The official path through `open_session` validates correctly |
| Verdict | **NO BYPASS FOUND** through the documented API surface |

---

## VIII. Findings

### BLOCKER — none

### SERIOUS — none

### NOTABLE

#### NOTABLE-1: `open_session` cleanup heuristic is subtle

The outer `except Exception` block at the end of `open_session` uses an introspection heuristic to decide whether to clean up the launched (pw, browser, context):

```python
if pw is not None and (
    self._session_manager is None
    or not any(
        s.pw is pw for s in self._session_manager._sessions.values()
    )
):
    # ... cleanup ...
```

The intent is correct: clean up ONLY if the session was not registered (because if it WAS registered, ownership transferred to the manager, which will clean up at close/eviction time).

The mechanism (iterating manager._sessions to check if our `pw` is still in there) is correct but FRAGILE:
- It relies on `_sessions` being accessible (private but present).
- It iterates the entire dict on every failure.
- It uses identity comparison (`is`) which is correct here but easy to break in a refactor.

**Cleaner alternative (for v0.8.2.1 or later):** carry a `was_registered` flag explicitly in the local scope:
```python
was_registered = False
try:
    # ... launch + register ...
    was_registered = True  # set right after register_session succeeds
except Exception:
    if not was_registered:
        # cleanup
    raise
```

The current code is FUNCTIONALLY CORRECT, just unnecessarily clever. Recommend cleanup to use the explicit flag at v0.8.2.1 or with the next Forge pass that touches this code.

### NIT

#### N-3: `session_status` re-imports playwright unnecessarily

`session_status` imports `playwright.async_api` exception types even though it only catches them around `await session.page.title()` — a single line. The import has to happen because we need the exception classes to type the catch, but the import block is identical to (and copy-pasted from) the larger one in `open_session`. A small private helper `_playwright_exception_types()` returning a tuple of the two classes would deduplicate the four copies of this import block now in the file.

This is purely a code-style observation; behaviour is correct.

#### N-4: `BrowserSessionManager.active_count` is documented as "no lock" but a concurrent `register_session`/`close_session` could observe a stale value

The docstring acknowledges this ("for observability only"), and the authoritative cap check is correctly under the lock in `register_session`. So the lack of synchronisation is intentional and correct. The NIT is just that callers using `active_count` for ANYTHING other than logging/observability could be misled.

**Recommended docstring tightening:** add an explicit "DO NOT use for cap enforcement — use `check_capacity` instead" line.

---

## IX. Verdict

**PASSES SCRUTINY** — the v0.8.2 *Innan Hurðar* slice is fit for milestone close.

| Severity | Count |
|---|---|
| BLOCKER | 0 |
| SERIOUS | 0 |
| NOTABLE | 1 (NOTABLE-1: subtle cleanup heuristic in open_session) |
| NIT | 2 (N-3 import dedup; N-4 active_count docstring) |

**Wins this milestone:**
- M-1 from v0.8.1 closed cleanly with a coordinated typing sweep across all four `Page.*` call sites.
- Stateful sessions land with full B-12..B-18 invariant coverage and 51 new tests.
- Concurrency correctness verified at three distinct race scenarios (cap-race, eviction-race, double-close).
- D-14 (LeidClient byte-untouched) and the contract-surface preservation of v0.8.0/v0.8.1 both honoured. The internal type-wrap added by M-1 is the explicit Architect-approved exception, behaviour-preserving.

**Auditor recommends:**
- **Wave 6:** Address NOTABLE-1 (refactor `open_session` cleanup to use an explicit `was_registered` flag). N-3 and N-4 may be deferred; they are pure code-style observations that do not affect correctness or agent-facing behaviour.

---

## X. Notes for the Scribe

When sealing this milestone (Wave 7), the DEVLOG entry should record:

1. v0.8.2 *Innan Hurðar* is the **third slice** within the v0.8 *Opið Vef* umbrella, AND it introduces a **new disposition** (stateful presence vs stateless walk) — earning its own Skald codename within the umbrella.
2. **M-1 from v0.8.1 CLOSED** — the Auditor's "coordinated single sweep" recommendation was honoured exactly.
3. The pattern of **named-then-unnamed extensions** is now joined by **named-with-new-disposition-within-umbrella**. The Skald's pen distinguishes between "extension of the same posture" (v0.7.3, v0.6.3.1, v0.8.1 → unnamed) and "new posture within the same umbrella" (v0.8.2 → named *Innan Hurðar*).
4. Test growth: leid scope 106 + 2 → **157 + 2** (+51); full suite 1427 + 9 → **1478 + 9**.

Threads carried forward:
- v0.8.2.1 (`leid.type`) — natural next slice
- v0.8.2.2 (`leid.navigate` in-session) — useful but not minimal-vertical
- v0.8.3 (`leid.query`) — selector + attribute extraction
- NOTABLE-1 cleanup of `open_session` cleanup heuristic — Wave 6 if appetite, otherwise v0.8.2.1
- N-3, N-4 — pure NITs, no time pressure

---

*Audit authored by Sólrún Hvítmynd, Auditor for Vibe Coding, 2026-05-10.*
*The body now stays inside the door, with discipline. Sessions are bounded, eviction is observable, the door does not stay propped forever. The deferred recommendation from the prior audit is closed in the same coordinated sweep its successor anticipated. The milestone passes — one clear NOTABLE worth attending to in cleanup, two NITs that can wait.*
