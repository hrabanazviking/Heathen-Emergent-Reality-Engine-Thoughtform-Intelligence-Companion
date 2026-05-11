# TASK — HERETIC v0.8.3 — leid.query (Innan Hurðar extension)

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-10** (immediately after v0.8.2.2 leid.navigate sealed at `b1ae5d1`)
>
> **Codename:** **NONE** — sixth unnamed extension. Same Innan Hurðar disposition (presence inside an open session); the body looks at what is in front of it without touching.
>
> **Umbrella milestone:** v0.8 *Opið Vef* — sixth slice within the umbrella.
>
> **Mythic Engineering mode:** AUTONOMOUS. Fourteenth milestone in the autonomous arc that began 2026-05-09.

---

## 1. Task scope

Add ONE new tool — the read-only sibling of click and type:

> **`leid.query(session_id, selector, attribute="") → {session_id, selector, attribute, found, value, count}`** —
>
> Inspects the DOM of an open session: extracts the text content (or a specified HTML attribute) of the FIRST element matching the CSS selector. Returns a count of total matches so the agent knows whether to refine the selector. **Not finding a matching element is NOT an error** — `found: false` with `value: null` is the natural read-result for "this thing is not on the page." This is a deliberate divergence from click/type (which raise `Leid*ElementNotFoundError` because mutating actions must succeed).

Use cases:
- "Is the user logged in?" → `query(session_id, ".user-name")` → `found: true` if so
- "What's the URL of the first article?" → `query(session_id, "article a", attribute="href")`
- "How many search results?" → `query(session_id, ".result")` → check `count`
- "What does this error message say?" → `query(session_id, ".alert-error")`

The httpx tools, render_url, screenshot, and the v0.8.2 / v0.8.2.1 / v0.8.2.2 session tools are **unchanged**. v0.8.3 is purely additive.

---

## 2. Out of scope

| Capability                  | Slice    | Reason for deferral                                       |
|-----------------------------|----------|-----------------------------------------------------------|
| Multi-element extraction (`.all()` returning a list) | v0.8.x | First-match keeps shape consistent with click/type; multi-element can be its own slice if needed |
| XPath selectors             | v0.8.x   | Playwright supports XPath but most agents use CSS; not a v0.8.3 concern |
| Inner HTML extraction       | v0.8.x   | text_content covers most needs; raw HTML is a different primitive |
| Element bounding-box / position | v0.8.x | Geometric inspection is a separate concern |
| Element visibility check    | v0.8.x   | `found` already conveys "matched in DOM"; visibility is a refinement |

---

## 3. Architectural decisions

| #  | Decision | Choice | Rationale |
|----|---|---|---|
| D-69 | Match cardinality | First match (`.first`) — same as click/type/screenshot/render_url's locator pattern | Consistent across the body's interactive faculty; a v0.8.x extension can add multi-match if agent feedback demands it |
| D-70 | Default extraction | `text_content()` when `attribute=""` (or omitted) | The agent's most common need is "what does this element say?" |
| D-71 | Attribute extraction | `get_attribute(name)` when `attribute` is non-empty | Standard DOM attribute read; returns None if attribute absent (passed through as JSON null) |
| D-72 | "Not found" semantics | `found: false`, `value: null`, `count: 0` — **NOT an error** | DELIBERATE divergence from click/type. Read tools must support "looking to see if X exists" without forcing exception handling on the agent |
| D-73 | "Found but no attribute" semantics | `found: true`, `value: null` | Distinguishes "no element" (count=0, value=null) from "element exists but attribute absent" (count>=1, value=null). Useful diagnostic information |
| D-74 | Count semantics | Total matches via `locator.count()` | Tells the agent if the selector is over- or under-specific; helps with refinement |
| D-75 | Timeout | Reuses `LeidConfig.browser_click_timeout_seconds` | Read operations are fast interactive actions; same operator-controlled bound. No new config field |
| D-76 | Whitespace handling | Pass-through (no strip, no normalize) | Honest about what the DOM contained; agents can normalize if they need |
| D-77 | Skald wave | NO new vision-doc addendum — sixth unnamed extension within Innan Hurðar | Continuing the established pattern. Brief paragraph in OPID_VEF.md §IX continuation if anything — the body looking is still the body being inside the door |
| D-78 | New B-Invariant | B-21 — query respects same session/timeout/activity discipline as click/type, with the divergence that "selector matched nothing" is a successful return rather than an error | Single new invariant; reuses prior infrastructure |
| D-79 | Error mapping | LeidConnectionError for genuine browser failures (page closed, etc.); LeidSessionExpiredError for unknown session_id; **NO LeidQueryElementNotFoundError class** because not-found is not an error | D-72's consequence — different semantic class than click/type |

---

## 4. New B-Invariant

| #    | B-Invariant |
|------|-----------|
| B-21 | `query()` enforces the same session/timeout discipline as the rest of Innan Hurðar: `evict_expired_sessions` runs first; unknown session_id raises `LeidSessionExpiredError`; `locator.count()` and (if non-zero) `text_content()` / `get_attribute()` calls bounded by `browser_click_timeout_seconds`; on success, `session.last_activity_at` is updated. **DIVERGENCE from B-19/D-43**: a selector matching no elements is NOT a failure — `query` returns `{found: false, count: 0, value: null}` because read operations must support "looking to see if X exists." |

B-1..B-20 continue to govern unchanged. The "found: false is not an error" rule is the first deliberate divergence in error semantics within the v0.8 umbrella; it is documented as such.

---

## 5. Test plan

Extend `tests/test_leid_playwright_client.py` with `TestQuery` class.

| Test | Asserts |
|---|---|
| `test_query_unknown_session_raises_expired` | B-16 |
| `test_query_returns_text_content_for_first_match` | D-69 / D-70 — text from first match |
| `test_query_returns_attribute_when_specified` | D-71 — get_attribute path |
| `test_query_returns_count_of_total_matches` | D-74 |
| `test_query_returns_not_found_when_no_match` | D-72 — `{found: false, count: 0, value: null}`; NO exception |
| `test_query_returns_found_true_with_null_value_when_attribute_missing` | D-73 |
| `test_query_browser_error_raises_leid_connection_error` | D-79 — page.locator failures map cleanly |
| `test_query_updates_last_activity` | B-17 / B-21 |
| `test_query_does_not_call_page_evaluate` | B-10 inherited |
| `test_query_passes_timeout_to_locator_calls` | D-75 |

`tests/test_leid_sense.py`:
| `test_dispatch_query_routes_to_playwright_client` | Routing |
| Update tool count check 10 → 11 |
| Update tool names locked check |

---

## 6. Wave plan

| Wave | Role | Deliverable |
|---|---|---|
| 0 | Runa (this file) | TASK file |
| 1 | Skald (very brief) | OPID_VEF.md §IX continuation paragraph — "the body looks but does not touch" |
| 2 | Cartographer | DATA_FLOW.md §4.12.2.7 — query flow |
| 3 | Architect | INTERFACE.md §12.9 + B-21 + 1 tool def (with optional `attribute` param) |
| 4 | Forge | query() method + sense routing + 10 new tests + 1 dispatch test |
| 5 | Auditor | AUDIT_v0.8.3_QUERY.md |
| 6 | Forge cleanup | If needed |
| 7 | Scribe | DEVLOG entry 28 + seal + memory refresh |

---

## 7. Exit criteria

- [ ] `query()` method on `PlaywrightLeidClient`
- [ ] `leid.query` registered in `LEID_TOOL_DEFINITIONS` with `attribute` as optional parameter
- [ ] `LeidSense._route` dispatches `leid.query`
- [ ] No new error classes (D-79)
- [ ] B-21 added to INTERFACE.md §12.9
- [ ] All 179 existing leid tests pass unchanged
- [ ] At least 10 new query tests passing
- [ ] 1 new dispatch test passing
- [ ] `docs/cartography/DATA_FLOW.md` §4.12.2.7 exists
- [ ] `docs/vision/OPID_VEF.md` §IX continuation paragraph exists
- [ ] `docs/audit/AUDIT_v0.8.3_QUERY.md` PASSES SCRUTINY
- [ ] DEVLOG entry 28 written
- [ ] All commits pushed to `development`
