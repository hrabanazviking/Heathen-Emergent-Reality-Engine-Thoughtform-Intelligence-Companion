# TASK — HERETIC v0.8.8 — leid.query_all (Innan Hurðar extension)

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-11** (immediately after v0.8.7 leid.reload sealed at `3807e9e`)
>
> **Codename:** **NONE** — eleventh unnamed extension within Innan Hurðar.
>
> **Umbrella milestone:** v0.8 *Opið Vef* — eleventh slice within the umbrella.
>
> **Mythic Engineering mode:** AUTONOMOUS. Nineteenth milestone in the autonomous arc.
>
> **Notable departure:** This slice introduces the **first new LeidConfig field since v0.8.2** (`browser_query_max_matches`). The five-consecutive-milestone config-and-errors-stability streak (v0.8.3 → v0.8.7) ends here, honestly — multi-match query genuinely needs a cardinality cap to bound the result list.

---

## 1. Task scope

Add ONE new tool — multi-element query, natural follow-up to v0.8.3:

> **`leid.query_all(session_id, selector, attribute="") → {session_id, selector, attribute, count, values}`** —
>
> Returns ALL matching elements' text content (or specified attribute) as a list, in DOM order. Where `leid.query` returns just the first match (consistent with the body's other interactive primitives that operate on `.first`), `leid.query_all` returns the whole set — useful for "give me all the article titles" or "list all the navigation links" or "what does each error message say?"

Bounded by a new `LeidConfig.browser_query_max_matches` (default 100). If the selector matches more than the cap, `LeidResponseTooLargeError` is raised — the agent gets honest feedback that their selector is too broad. The same "not found is not an error" posture (D-72) applies: count=0 returns `{count: 0, values: []}` (empty list), NOT an exception.

The httpx tools, render_url, screenshot, the v0.8.2.x session tools, and v0.8.5/v0.8.6/v0.8.7 paired/single tools are **unchanged**. v0.8.8 is purely additive.

---

## 2. Out of scope

| Capability                  | Slice    | Reason for deferral                                       |
|-----------------------------|----------|-----------------------------------------------------------|
| Streaming/paginated query results | v0.8.x | Cap-based bounding is enough for v0.8.8; pagination is a separate primitive |
| XPath multi-match           | v0.8.x   | CSS suffices for v0.8.8 |
| Per-element bounding box / position | v0.8.x | Geometric inspection is a separate concern |
| Nested attribute reads (e.g., href + text in one call) | v0.8.x | Single-attribute keeps the API simple; agent calls twice if both needed |

---

## 3. Architectural decisions

| #  | Decision | Choice | Rationale |
|----|---|---|---|
| D-114 | Match cardinality | ALL matches up to cap (D-117) | The point of query_all is enumeration; first-match is what query already does |
| D-115 | Cap field | NEW `LeidConfig.browser_query_max_matches: int = 100` | Cardinality cap, distinct from byte-size cap. Default 100 is the most-agents-want-this-many threshold; operators with bigger needs raise it |
| D-116 | Cap-exceeded behaviour | When `count > browser_query_max_matches`, raise `LeidResponseTooLargeError` BEFORE iterating the matches | Reuses the existing too-large error class; honest feedback that the selector is too broad. No silent truncation |
| D-117 | Empty-result behaviour | `{count: 0, values: []}` — NOT an error | Same posture as v0.8.3 query's D-72. Multi-element query is a probe-and-act primitive |
| D-118 | Iteration primitive | `locator.nth(i).text_content(...)` or `.get_attribute(...)` for i in range(count) | Standard Playwright multi-element pattern |
| D-119 | Order | DOM order (Playwright's natural iteration order) | Predictable; matches user intuition |
| D-120 | Attribute parameter | Optional, defaults to `""` (text content) — same shape as v0.8.3 query | Symmetry with single-match query; agent learns one parameter, not two |
| D-121 | Return shape | `{session_id, selector, attribute, count, values}` — no `found` field (multi-element doesn't need binary semantic) | Distinct from query's `{found, value, count}` shape; honest about what each tool gives back |
| D-122 | Timeout per element | Each text_content / get_attribute call uses `browser_click_timeout_seconds` (D-75 reuse) | Same per-element bound as single-match query |
| D-123 | New error classes | NONE — reuses LeidSessionExpiredError, LeidConnectionError, LeidResponseTooLargeError | Same failure surface as query + the new cardinality cap raises the existing too-large class |
| D-124 | Skald wave | NO new vision-doc addendum — eleventh unnamed extension | Continuing the established pattern |
| D-125 | New B-Invariant | B-26 — query_all respects same session/timeout discipline as query, plus the new cardinality cap | Single new invariant |

---

## 4. New B-Invariant

| #    | B-Invariant |
|------|-----------|
| B-26 | `query_all()` enforces the same session/timeout discipline as `query()`: `evict_expired_sessions` runs first; unknown session_id raises `LeidSessionExpiredError`; `locator.count()` then `locator.nth(i).text_content()` / `.get_attribute()` (per i in 0..count) calls bounded by `browser_click_timeout_seconds`; on success, `session.last_activity_at` is updated. **NEW**: cardinality cap — when `count > config.browser_query_max_matches`, `LeidResponseTooLargeError` is raised BEFORE iteration. **DIVERGENCE inherited from B-21**: empty result (count=0) is NOT an error — returns `{count: 0, values: []}`. |

B-1..B-25 continue to govern unchanged.

---

## 5. New config field validation

`LeidConfig.browser_query_max_matches: int = 100` — must be `>= 1` (at minimum 1 match could fit; less is incoherent). `__post_init__` validates this.

---

## 6. Test plan

Extend `tests/test_leid_playwright_client.py` with `TestQueryAll` class (~12 tests):

- `test_query_all_unknown_session_raises_expired` — B-16
- `test_query_all_returns_empty_list_when_no_match` — D-117 / B-26 divergence
- `test_query_all_returns_single_match_as_one_element_list` — single match in a list
- `test_query_all_returns_all_matches_in_dom_order` — D-114, D-119
- `test_query_all_returns_attribute_values` — D-120 (attribute path)
- `test_query_all_returns_text_when_attribute_omitted` — D-120 (default text path)
- `test_query_all_includes_null_for_missing_attributes` — element exists, attribute absent → None in list
- `test_query_all_cap_exceeded_raises_too_large` — D-116 (count > cap)
- `test_query_all_cap_edge_succeeds_at_exact_cap` — count == cap → succeeds
- `test_query_all_count_failure_raises_connection_error` — locator.count error
- `test_query_all_extraction_failure_raises_connection_error` — text_content/get_attribute error
- `test_query_all_updates_last_activity_on_found` — B-17 / B-26
- `test_query_all_updates_last_activity_on_empty` — B-17 / B-26 also on empty path
- `test_query_all_does_not_call_page_evaluate` — B-10 inherited

`tests/test_leid_sense.py` (~3):
- `test_dispatch_query_all_routes_to_playwright_client`
- `test_dispatch_query_all_passes_attribute_when_provided`
- `test_leid_config_invalid_browser_query_max_matches_raises` (config validation)
- `test_leid_config_browser_query_max_matches_default_is_100`
- Update tool count check 17 → 18
- Update tool names locked check

---

## 7. Wave plan

| Wave | Role | Deliverable |
|---|---|---|
| 0 | Runa (this file) | TASK file |
| 1 | Skald (very brief) | OPID_VEF.md §IX continuation paragraph |
| 2 | Cartographer | DATA_FLOW.md §4.12.2.12 — query_all flow + B-26 |
| 3 | Architect | INTERFACE.md §12.14 + B-26 + LeidConfig field + 1 tool def |
| 4 | Forge | query_all() method + sense routing + ~13 method tests + 2 dispatch + 2 config validation |
| 5 | Auditor | AUDIT_v0.8.8_QUERY_ALL.md |
| 6 | Forge cleanup | If needed |
| 7 | Scribe | DEVLOG entry 33 + seal + memory refresh |

---

## 8. Exit criteria

- [ ] `query_all()` method on `PlaywrightLeidClient`
- [ ] `leid.query_all` registered in `LEID_TOOL_DEFINITIONS` with `attribute` optional
- [ ] `LeidSense._route` dispatches `leid.query_all`
- [ ] No new error classes (D-123)
- [ ] NEW config field `browser_query_max_matches: int = 100` with __post_init__ validation
- [ ] B-26 added to INTERFACE.md §12.14
- [ ] All 251 existing leid tests pass unchanged
- [ ] At least 12 new method tests passing
- [ ] 2 new dispatch tests passing
- [ ] 2 new config validation tests passing
- [ ] `docs/cartography/DATA_FLOW.md` §4.12.2.12 exists
- [ ] `docs/vision/OPID_VEF.md` §IX continuation paragraph exists
- [ ] `docs/audit/AUDIT_v0.8.8_QUERY_ALL.md` PASSES SCRUTINY
- [ ] DEVLOG entry 33 written
- [ ] All commits pushed to `development`
