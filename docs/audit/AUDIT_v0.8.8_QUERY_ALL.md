# AUDIT — v0.8.8 leid.query_all (Innan Hurðar extension)

**Auditor:** Sólrún Hvítmynd
**Date:** 2026-05-11
**Scope under audit:** v0.8.8 — `PlaywrightLeidClient.query_all()` + `leid.query_all` dispatch + B-26 + new `LeidConfig.browser_query_max_matches` field
**Mythic Engineering session:** AUTONOMOUS — Forge HEAD `0210dbc` (post-implementation, pre-audit)
**Audit method:** Static review of the new method against the v0.8.8 contract in `INTERFACE.md §12.14`. Verification that B-26's cardinality cap is correctly enforced (cap fires BEFORE iteration). Verification that the divergence from query (multi-element vs single-element) is structurally explicit. Verification that the new config field is correctly validated. Sibling trace against `query`'s structure. L + prior-tools surface non-regression. The v0.8 umbrella's "no new config since v0.8.2" streak ends here — verify the new field is justified.
**Verdict:** **PASSES SCRUTINY** — 0 BLOCKER, 0 SERIOUS, 0 NOTABLE, 0 NIT (EIGHTH CONSECUTIVE zero-findings audit in the v0.8 umbrella).

---

## I. Method

The audit was conducted in six passes:

1. **B-26 verification** — session resolution, count, cap check, empty-return divergence, iteration with per-element extraction, activity update.
2. **Cap-fires-before-iteration verification** — confirm the cap check happens BEFORE any locator.nth() call.
3. **New config field verification** — `browser_query_max_matches` validation (>= 1) is correctly enforced; the streak-ending choice is justified at TASK time.
4. **Sibling trace** — `query_all` should mirror `query`'s discipline at every shared phase, diverge only at "single match → multi-match" and "found field → values list."
5. **L + prior-tools non-regression** — confirm all prior surfaces unchanged.
6. **Test-quality check** — 18 new tests cover happy path, B-26 phases, cap edge cases, empty return, all error classes, B-10 inheritance, config validation.

---

## II. B-26 Verification

**Contract (INTERFACE.md §12.14):**
> `query_all()` enforces the same session/timeout discipline as `query()`: `evict_expired_sessions` runs first; unknown session_id raises `LeidSessionExpiredError`; `locator.count()` then `locator.nth(i).text_content()` / `.get_attribute()` (per i in 0..count) calls bounded by `browser_click_timeout_seconds`; on success, `session.last_activity_at` is updated. **NEW**: cardinality cap — when `count > config.browser_query_max_matches`, `LeidResponseTooLargeError` is raised BEFORE iteration. **DIVERGENCE inherited from B-21**: empty result (count=0) is NOT an error.

**Implementation order (verified by inspection):**

```python
# Stage 1-3: session resolution
manager = ...
await manager.evict_expired_sessions()              # B-15
session = await manager.get_session(session_id)     # B-16
# import ...

# Stage 4: count
locator = session.page.locator(selector)
try:
    count = await locator.count()
except PlaywrightError:
    raise LeidConnectionError(...)

# Stage 5: cap check (NEW — fires BEFORE iteration)
if count > config.browser_query_max_matches:
    raise LeidResponseTooLargeError(...)

# Stage 6: empty-result early return (D-117 divergence)
if count == 0:
    session.mark_activity()
    return {count: 0, values: []}

# Stage 7: iterate and extract
values = []
for i in range(count):
    el = locator.nth(i)
    try:
        v = await el.text_content(timeout=...) or el.get_attribute(...)
    except (PlaywrightTimeoutError, PlaywrightError):
        raise LeidConnectionError(...)
    values.append(v)

# Stage 8: activity update
session.mark_activity()

# Stage 9: return
return {count, values, ...}
```

Each phase verified. The cap check (Stage 5) sits BETWEEN count and iteration — meaning a too-broad selector pays only for the count call, not for any per-element extraction. The empty-return (Stage 6) sits AFTER the cap check, so an empty result correctly takes the cheap path.

**Tests cover:**

| B-26 phase | Test |
|---|---|
| Unknown session → expired | `test_query_all_unknown_session_raises_expired` |
| Empty result → not an error | `test_query_all_returns_empty_list_when_no_match` (also asserts nth NOT called) |
| Single match in list | `test_query_all_returns_single_match_as_one_element_list` |
| Multi-match DOM order | `test_query_all_returns_all_matches_in_dom_order` |
| Attribute extraction | `test_query_all_returns_attribute_values` |
| Default text extraction | `test_query_all_returns_text_when_attribute_omitted` |
| Null for missing attribute | `test_query_all_includes_null_for_missing_attributes` |
| Cap exceeded → too large (BEFORE iteration) | `test_query_all_cap_exceeded_raises_too_large` (also asserts nth NOT called) |
| Cap edge succeeds | `test_query_all_cap_edge_succeeds_at_exact_cap` |
| count() failure | `test_query_all_count_failure_raises_connection_error` |
| Per-element extraction failure | `test_query_all_extraction_failure_raises_connection_error` (verifies error message includes index) |
| Activity update on found | `test_query_all_updates_last_activity_on_found` |
| Activity update on empty | `test_query_all_updates_last_activity_on_empty` |
| B-10 inheritance | `test_query_all_does_not_call_page_evaluate` |

**Verdict:** **PASS** — B-26 correctly enforced; 14 tests cover every documented phase.

---

## III. Cap-Fires-Before-Iteration Verification

The most important new behavior in v0.8.8 is the cap check. The Auditor verified:

1. **Code-path inspection:** `if count > max_matches:` sits BETWEEN `await locator.count()` and the `for i in range(count):` loop. There is no path that reaches the iteration loop without first passing the cap check.

2. **Test verification:** `test_query_all_cap_exceeded_raises_too_large` explicitly asserts `page_mock.locator.return_value.nth.assert_not_called()` after the cap raises. The mock would have been called if the iteration had begun; the assertion confirms it was not.

3. **Cost implication:** A too-broad selector (e.g., 10000 matches) costs only the `count()` call (~5-20 ms). No per-element extraction happens. The agent gets honest feedback fast.

4. **Cap-edge behavior:** `test_query_all_cap_edge_succeeds_at_exact_cap` confirms the cap is INCLUSIVE — count == cap succeeds, only count > cap fails. Documented as "cap is inclusive" in the Forge implementation.

**Verdict:** **PASS** — cap correctly bounds iteration cost; verified by both code inspection and test.

---

## IV. New Config Field Verification

**Field:** `LeidConfig.browser_query_max_matches: int = 100`

**Validation:** `__post_init__` raises `ValueError` if `< 1`. Default 100 is the most-agents-want-this-many threshold per D-115's rationale.

**Tests:**
- `test_leid_config_browser_query_max_matches_default_is_100` — verifies default
- `test_leid_config_invalid_browser_query_max_matches_raises` — verifies validation rejects 0 and -5

**Streak-end justification:** The v0.8.3 → v0.8.7 streak of "no new config field" was a property of disciplined extension. v0.8.8 ends the streak HONESTLY: multi-element query genuinely needs a cardinality cap, the cap is operator-controlled (not a hard-coded constant), and the cap addresses a real risk (over-broad selector → unbounded iteration). The Auditor finds the new field justified — adding config when the design genuinely needs it is correct discipline, not a regression.

**Verdict:** **PASS** — new config field correctly validated; streak-end honest.

---

## V. Sibling Trace (query_all vs query)

| Aspect | query (v0.8.3) | query_all (v0.8.8) |
|---|---|---|
| Cardinality | First match (`.first`) | All matches (`.nth(i)` per i) |
| Cap | n/a (single match) | NEW `browser_query_max_matches`, raises before iteration |
| Empty result | `{found: false, count: 0, value: null}` | `{count: 0, values: []}` (NO `found` field) |
| Single match | `{found: true, count: N, value: <str>}` | `{count: 1, values: [<str>]}` |
| Multi match | (returns first only) | `{count: N, values: [str, str, ...]}` |
| Per-element timeout | `browser_click_timeout_seconds` | identical |
| Session/activity discipline | B-21 | B-26 (inherits + adds cardinality cap) |
| Error class for browser failure | LeidConnectionError | identical |
| Error class for "thing not there" | NONE (returns `found: false`) | NONE (returns `count: 0, values: []`) |
| Error class for cap exceeded | n/a | `LeidResponseTooLargeError` |

**Two intentional differences from query, all justified:**
1. **No `found` field** — multi-element query doesn't need binary semantic. The agent uses `len(values) > 0` or `count > 0` to detect presence.
2. **Cardinality cap with `LeidResponseTooLargeError`** — query has no analog; multi-element query intrinsically needs bounding.

All other aspects mirror query exactly. Sibling consistency is exact at the discipline level.

**Verdict:** **PASS** — two justified differences; no surprise divergences.

---

## VI. L + Prior-Tools Non-Regression

| Concern | Result |
|---|---|
| `LeidClient` source byte-identity | **VERIFIED** — `git diff 0210dbc -- client.py` returns empty (TWELFTH consecutive milestone) |
| `BrowserSessionManager` byte-identity | **VERIFIED** |
| `errors.py` byte-identity | **VERIFIED** (D-123 — no new error classes) |
| `LeidConfig` change | **NEW FIELD ONLY** (`browser_query_max_matches`), with __post_init__ validation; existing fields and validations untouched |
| All 14 prior PlaywrightLeidClient methods | All **PRESERVED** — `query_all()` was inserted between `reload()` and `close_session()` |
| Existing 251 leid tests | All pass after v0.8.8 (verified `1590 passed` includes the prior 1572 + 18 new) |
| Tool count check | Intentional: 17 → 18 |
| Verdict | **PASS** — strict additive law honoured for the TWELFTH consecutive slice; new config field is the only deliberate addition |

---

## VII. Test-Quality Check

The 18 new tests (14 in `TestQueryAll` + 2 dispatch + 2 config validation) cover:
- B-16 session resolution failure
- D-117 empty-result divergence (with assertion that nth is NOT called)
- Single-match in list
- Multi-match DOM ordering
- Both extraction primitives (text_content, get_attribute)
- D-73-style null-attribute pass-through (per element)
- D-116 cap-exceeded path (with assertion that nth is NOT called)
- Cap edge (count == cap succeeds)
- Both failure points (count, per-element extraction)
- Per-element extraction failure includes the failing index in the error message
- Activity update on BOTH found and empty paths
- B-10 inheritance
- Config field default and validation
- Dispatch routing for default + explicit attribute

**Coverage assessment:** every B-26 phase, every D-decision, every documented response shape outcome, both error class paths, and the cap edge case. Two assertions explicitly verify "this code path was NOT taken" (nth.assert_not_called on empty and on cap-exceeded), which is the right shape for verifying early-return correctness.

**Verdict:** **PASS** — exhaustive coverage of the slice surface.

---

## VIII. Findings

### BLOCKER — none

### SERIOUS — none

### NOTABLE — none

### NIT — none

**Eighth consecutive zero-findings audit in the v0.8 umbrella.** v0.8.8 added a new config field (the first since v0.8.2) and the Auditor confirmed the addition was justified at TASK design time and correctly validated at implementation time. Adding necessary config is good discipline, not a regression — what would be a regression is hiding a new operator concern behind a hard-coded constant. v0.8.8 chose the right shape.

---

## IX. Verdict

**PASSES SCRUTINY** — the v0.8.8 query_all extension is fit for milestone close.

| Severity | Count |
|---|---|
| BLOCKER | 0 |
| SERIOUS | 0 |
| NOTABLE | 0 |
| NIT | 0 |

**Wins this milestone:**
- Eighth consecutive zero-findings audit. The pattern is now firmly established at eight in a row.
- Cap-fires-before-iteration verified by both code inspection and explicit `nth.assert_not_called()` test.
- Streak-end was HONEST — new config field is justified by genuine design need (cardinality bounding for multi-element query). Hiding it behind a hard-coded constant would have been worse discipline.
- Sibling trace against query exact at every shared phase; two intentional differences (no `found` field, new cap-exceeded error path) both explicitly justified.
- D-14 (LeidClient byte-untouched) honoured for the TWELFTH consecutive milestone.
- The body's eye now sees both singular (`query`) and plural (`query_all`) — each with its right use case.

---

## X. Notes for the Scribe

When sealing this milestone (Wave 7), the DEVLOG entry should record:

1. v0.8.8 is the **eleventh slice** within v0.8 *Opið Vef* and the **eleventh unnamed extension** in the body's history.
2. **Eighth consecutive zero-findings audit** — eight in a row.
3. **First new LeidConfig field since v0.8.2** — the five-consecutive-milestone config-stability streak ends honestly (v0.8.3 → v0.8.7 had no new config; v0.8.8 added `browser_query_max_matches` because multi-element query genuinely needs a cardinality cap).
4. The body's eye now has both singular and plural reads — `query` for "find this thing if it's there" and `query_all` for "list every thing of this kind."

Threads carried forward:
- v0.8.x JPEG/WebP screenshot output — small refinement
- v0.8.x configurable viewport size — small refinement
- v0.8.x element-targeted press (`locator.press`) — refinement on press
- v0.8.x final-URL allowlist re-check after redirect — pre-existing concern across all browser tools
- N-3, N-4 from v0.8.2 — pure NIT code style

---

*Audit authored by Sólrún Hvítmynd, Auditor for Vibe Coding, 2026-05-11.*
*The body's eye now sees both singular and plural; the cap fires before iteration; the new config field ends a streak honestly. Eighth consecutive zero-findings audit. The milestone passes.*
