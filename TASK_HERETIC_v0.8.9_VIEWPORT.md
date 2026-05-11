# TASK — HERETIC v0.8.9 — Configurable viewport (Innan Hurðar extension)

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-11** (immediately after v0.8.8 leid.query_all sealed at `b60343c`)
>
> **Codename:** **NONE** — twelfth unnamed extension within Innan Hurðar.
>
> **Umbrella milestone:** v0.8 *Opið Vef* — twelfth slice within the umbrella.
>
> **Mythic Engineering mode:** AUTONOMOUS. Twentieth milestone in the autonomous arc.
>
> **Notable departure:** This slice **modifies three existing methods** (`render_url`, `screenshot`, `open_session`) to pass viewport=... to `browser.new_context()`. The public agent-facing surface is unchanged — same tools, same parameters, same return shapes. Only the internal Playwright call gains a new kwarg, and operator-controlled viewport now propagates uniformly. A few existing tests that asserted `new_context.assert_awaited_once_with(user_agent=...)` need to be updated to also expect `viewport=...` in the call.
>
> **STATUS — 2026-05-11:** **SHIPPED + AUDITED + SEALED.** All seven waves closed; Wave 6 cleanup skipped (Auditor returned **zero findings** — ninth consecutive in v0.8 umbrella).
>
> **Final HEAD:** `6d46336` (Auditor close) — final Scribe push will advance.
>
> **Test status:** Leid 279 + 2 skip (was 269 + 2 — `+10`). Full suite **1600 + 9 skip** (was 1590 + 9). Suite has crossed 1600 tests. Zero regressions.
>
> **Auditor verdict:** PASSES SCRUTINY (0/0/0/0). Ninth consecutive zero-findings audit. **First substantive-modification slice in v0.8 umbrella** shipped cleanly with default-preserving discipline. See `docs/audit/AUDIT_v0.8.9_VIEWPORT.md`.
>
> **DEVLOG:** Entry 34 — `docs/DEVLOG.md`.

---

## 1. Task scope

Add operator-controlled viewport configuration:

> **Two new `LeidConfig` fields:**
>   - `browser_viewport_width: int = 1280` — viewport width in pixels
>   - `browser_viewport_height: int = 720` — viewport height in pixels
>
> **Three modification sites:**
>   - `PlaywrightLeidClient.render_url()` — passes viewport at new_context
>   - `PlaywrightLeidClient.screenshot()` — passes viewport at new_context
>   - `PlaywrightLeidClient.open_session()` — passes viewport at new_context (subsequent session tools inherit it)

Why this matters: many sites render differently at different viewport widths (mobile vs desktop vs ultrawide). Currently HERETIC uses Playwright's default 1280×720 — fine for most cases but operators with mobile-first scenarios or large dashboards need control. Defaults stay at Playwright's default values so existing operators see no behavior change.

The agent-facing tool surface is **unchanged**. No new tools, no new tool parameters, no new error classes. Only operators see the new config fields; agents never need to know about viewport.

---

## 2. Out of scope

| Capability                  | Slice    | Reason for deferral                                       |
|-----------------------------|----------|-----------------------------------------------------------|
| Per-call viewport override (agent-supplied) | v0.8.x | Operator-controlled is the right scope; agent-controlled would break the "agent doesn't manage browser internals" abstraction |
| Device emulation presets (e.g., iPhone, iPad) | v0.8.x | Distinct concern; would also include user_agent + touch settings |
| Mid-session viewport change | v0.8.x — `page.set_viewport_size` | Distinct primitive; would need its own tool. v0.8.9 is launch-time-only |
| Per-tool viewport override (e.g., screenshot at 1920 but session at 1280) | v0.8.x | Complexity not justified for v0.8.9 |

---

## 3. Architectural decisions

| #   | Decision | Choice | Rationale |
|-----|---|---|---|
| D-126 | Two fields, not one tuple | `browser_viewport_width: int` and `browser_viewport_height: int` | Simpler validation; flat field structure matches the rest of LeidConfig |
| D-127 | Defaults | 1280 × 720 (matches Playwright's default) | No behavior change for existing operators |
| D-128 | Validation | Both must be `> 0` (Playwright accepts 1+; operators with use cases below 100 are unusual but valid) | Minimal validation; trust the operator |
| D-129 | Application sites | All three browser-context-creating methods: render_url, screenshot, open_session | Operator's viewport choice should propagate uniformly across the body's browser usage |
| D-130 | Mid-session viewport | NOT changeable — viewport is set at session creation and persists through the session's life | Avoids agent-vs-operator config tension; matches the "viewport is operator-controlled, not agent-controlled" principle |
| D-131 | Test impact | Two existing `new_context.assert_awaited_once_with(user_agent=...)` tests need updates to also expect `viewport=...` in the call | Mechanical; the assertion shape gains one kwarg |
| D-132 | New error classes | NONE — config validation reuses ValueError (existing pattern) | Same shape as other LeidConfig fields |
| D-133 | Skald wave | NO new vision-doc addendum — twelfth unnamed extension | Continuing the established pattern. Brief paragraph in OPID_VEF.md §IX continuation |
| D-134 | New B-Invariant | B-27 — viewport is configured uniformly across all browser-context creations | Single new invariant covering the propagation discipline |

---

## 4. New B-Invariant

| #    | B-Invariant |
|------|-----------|
| B-27 | Every `browser.new_context(...)` call within `PlaywrightLeidClient` (in `render_url`, `screenshot`, `open_session`) passes `viewport={"width": config.browser_viewport_width, "height": config.browser_viewport_height}`. Operator-controlled viewport propagates uniformly across all browser-context creations. Once a context is created, its viewport persists for the life of that browser context (mid-session viewport change is out of scope per D-130). |

B-1..B-26 continue to govern unchanged.

---

## 5. New config fields

| Field                          | Type | Default | Validation | Purpose |
|--------------------------------|------|---------|------------|---------|
| `browser_viewport_width`       | int  | 1280    | `> 0`      | Viewport width in pixels for browser contexts |
| `browser_viewport_height`      | int  | 720     | `> 0`      | Viewport height in pixels for browser contexts |

---

## 6. Test plan

**New tests in `tests/test_leid_playwright_client.py`** (~3 + 3 = 6):

For each of the three modified methods:
- `test_render_url_passes_viewport_from_config`
- `test_screenshot_passes_viewport_from_config`
- `test_open_session_passes_viewport_from_config`

Each verifies `new_context` is called with `viewport={"width": ..., "height": ...}` matching the config.

**Existing tests to update (D-131):**
- `test_render_url_uses_configured_user_agent` — change assertion to include `viewport={"width": 1280, "height": 720}`
- `test_screenshot_uses_configured_user_agent` — same

**New tests in `tests/test_leid_sense.py`** (~4):
- `test_leid_config_browser_viewport_width_default_is_1280`
- `test_leid_config_browser_viewport_height_default_is_720`
- `test_leid_config_invalid_browser_viewport_width_raises`
- `test_leid_config_invalid_browser_viewport_height_raises`

---

## 7. Wave plan

| Wave | Role | Deliverable |
|---|---|---|
| 0 | Runa (this file) | TASK file |
| 1 | Skald (very brief) | OPID_VEF.md §IX continuation paragraph |
| 2 | Cartographer | DATA_FLOW.md §4.12.2.13 — viewport propagation note + B-27 |
| 3 | Architect | INTERFACE.md §12.15 + B-27 + 2 LeidConfig fields |
| 4 | Forge | Modify 3 methods in playwright_client.py (1-line each) + update 2 existing tests + 6 new tests + 4 config tests |
| 5 | Auditor | AUDIT_v0.8.9_VIEWPORT.md (verify uniform propagation; verify default-preservation; verify test updates are mechanical) |
| 6 | Forge cleanup | If needed |
| 7 | Scribe | DEVLOG entry 34 + seal + memory refresh |

---

## 8. Exit criteria (all met; this milestone is SEALED)

- [x] 2 new `LeidConfig` fields with __post_init__ validation — `a56c6e0`
- [x] `PlaywrightLeidClient.render_url()` passes viewport at new_context — `164fb0b`
- [x] `PlaywrightLeidClient.screenshot()` passes viewport at new_context — `164fb0b`
- [x] `PlaywrightLeidClient.open_session()` passes viewport at new_context — `164fb0b`
- [x] No new tools, no new error classes — confirmed
- [x] B-27 added to INTERFACE.md §12.15 — `a56c6e0`
- [x] All 269 existing leid tests pass (with 2 updated assertions; rest unchanged) — verified at `164fb0b`
- [x] 6 new viewport propagation tests passing (3 explicit + 3 default) — `164fb0b`
- [x] 4 new config validation tests passing — `164fb0b`
- [x] `docs/cartography/DATA_FLOW.md` §4.12.2.13 exists — `2134beb`
- [x] `docs/vision/OPID_VEF.md` §IX continuation paragraph exists — `1e244e9`
- [x] `docs/audit/AUDIT_v0.8.9_VIEWPORT.md` PASSES SCRUTINY (0/0/0/0) — `6d46336`
- [x] DEVLOG entry 34 written — Wave 7 (this seal)
- [x] All commits pushed to `development` — final Scribe push closes
