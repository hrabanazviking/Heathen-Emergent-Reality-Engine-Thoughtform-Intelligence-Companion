# TASK — HERETIC v0.5.5 MJÚKBLÆJA (Soft-Curved Veils)

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-09** (immediately after v0.5.4 *Margblæja* sealed at `e13407c`)
>
> **Codename (proposed, Skald to seal):** *Mjúkblæja* — "soft veil." Old Norse *mjúkr* (soft, smooth, gentle) + *blæja* (veil). The cloth that has learned to take soft shapes — round corners, curved edges, ellipses — to fit modern UI elements that are rarely sharp-cornered.
>
> **Mythic Engineering mode:** AUTONOMOUS continuation. Volmarr asleep / hands-off; this is the FOURTH milestone of the autonomous session.

---

## 1. Task scope

Extend the v0.5.4 *Margblæja* shape vocabulary with **two new soft-curved shapes**:

1. **Rounded rectangle** — defined by axis-aligned `(x, y, w, h)` plus `corner_radius`. Universal modern-UI primitive: every contemporary chat window, code editor, browser tab, and dialog has rounded corners. Veiling a rounded chat window with a sharp rectangle wastes pixels (covers more than the window) and signals the wrong shape (sharp where the source was soft).
2. **Ellipse** — defined by centre `(cx, cy)` and **two distinct radii** `(rx, ry)`. Strictly more general than the v0.5.4 `PrivacyMaskCircle` (which constrains `rx == ry == radius`). Useful for oval-shaped UI elements: pill-shaped buttons, status bars, thumbnail crops with non-square aspect ratios.

Both shapes implement the existing `PrivacyMaskShape` Protocol — same `bounding_box()` + `alpha_mask(w, h)` contract as the three v0.5.4 shapes. The unified apply pipeline picks them up automatically. The Architect's "one pipeline, three shapes" claim from v0.5.4 becomes "**one pipeline, five shapes**" — proving by extension that the abstraction holds.

The existing rectangle, circle, polygon shapes are unchanged. The codebase grows by two dataclasses + their two Protocol methods + validation, not by any pipeline branching.

---

## 2. Current status — 2026-05-09

**Phase:** v0.5.5 **OPEN — wave plan published, no code written yet.**

**HEAD (development):** `e13407c` (v0.5.4 Scribe seal — parent of upcoming Wave 0 commit)

**Test count baseline (before this milestone):** Sjón scope **196** on full-extras host (post-Margblæja). Privacy file: **51** tests. Encoder: **24** tests including 3 Blæja integration.

### v0.5.5 deliverables — pending

- ☐ Skald — `docs/vision/MJUKBLAEJA.md` — modern UI is rounded; the body's vocabulary should match
- ☐ Cartographer — `docs/cartography/DATA_FLOW.md §4.10.14.1` addendum: rounded_rectangle + ellipse shape formulas + Pillow primitives
- ☐ Architect+Forge — two new dataclasses (`PrivacyMaskRoundedRectangle`, `PrivacyMaskEllipse`) with Protocol method bodies; INTERFACE.md updated
- ☐ Forge — 14+ new tests; existing 51 privacy tests + 24 encoder tests must pass unchanged
- ☐ Auditor — `docs/audit/AUDIT_v0.5.5_MJUKBLAEJA.md` — verifies P-1..P-9 still hold for the two new shapes
- ☐ Scribe — DEVLOG entry 18; TASK seal; memory refresh

### What v0.5.5 does NOT add

- Bezier-curve / freeform paths — that remains v0.5.6+
- Polygon with rounded corners — different Pillow primitive; v0.5.6+
- Animated shapes — out of scope (and probably never sensible)
- Shape inversion / "show only this region" — v0.5.x
- Frontend shape-picker UI — v0.5.x frontend dev

---

## 3. Architectural decisions (Architect to confirm)

| Decision | Choice | Rationale |
|---|---|---|
| RoundedRectangle field shape | `(x, y, w, h, corner_radius)` | Standard CSS-style rounded-rectangle parameters; matches operator's mental model from CSS / design tools |
| `corner_radius` semantics | A single integer applied to all four corners | Pillow's `rounded_rectangle` takes a single radius; per-corner radii would require a custom alpha-mask painter — out of scope for v0.5.5 |
| `corner_radius` validation | `>= 0` (zero = sharp rectangle, valid degenerate case) | Allows operator to set 0 explicitly without raising; the resulting alpha mask is identical to a regular rectangle. |
| `corner_radius` upper bound | clamped at apply time to `min(w, h) // 2` | A radius larger than half the shorter side would produce overlapping corner arcs; clamping ensures Pillow's rasteriser receives a valid value. Operator does not see an error; the rendered shape is the largest-valid rounded rect. |
| RoundedRectangle bbox | `(x, y, w, h)` — same as the underlying rectangle | The corner curves are *inside* the bbox |
| RoundedRectangle alpha_mask | `Image.new("L", (w, h), 0)` + `ImageDraw.rounded_rectangle((0, 0, w-1, h-1), radius=R, fill=255)` | Pillow's built-in primitive. Available since Pillow 8.2.0 (we pin >=10). |
| Ellipse field shape | `(cx, cy, rx, ry)` | Two distinct radii — Circle's generalisation. `PrivacyMaskCircle(cx, cy, r)` is *not* a subtype; both are independent shapes that satisfy the Protocol. |
| Ellipse validation | `cx, cy >= 0`; `rx, ry >= 1` | Mirror of Circle's validation, generalised to two radii |
| Ellipse bbox | `(cx - rx, cy - ry, 2*rx, 2*ry)` | Standard axis-aligned ellipse bounding box |
| Ellipse alpha_mask | `Image.new("L", (w, h), 0)` + `ImageDraw.ellipse((0, 0, w-1, h-1), fill=255)` | Same primitive Circle uses; `w` and `h` differ when `rx != ry` |
| Mode + mode-param surface | Same as all other shapes (mode, blur_radius, solid_color, pixelate_factor) | Reuses `_validate_shared_shape_fields` helper from v0.5.4 |
| Type union of `privacy_masks` | Still `list[PrivacyMaskShape]` (Protocol-typed) | Both new shapes satisfy the Protocol structurally; no config-type change |
| YAML loader extension | Out of scope for v0.5.5 implementation — operator constructs Python objects directly in tests / programmatic config until a YAML loader extension lands | Operator-side YAML schema is a separate concern; the dataclasses are the contract |

---

## 4. Privacy invariants (Auditor verification subjects)

All nine invariants from v0.5.3 + v0.5.4 are inherited and must continue to hold. v0.5.5 adds none — the shape extension does not change the structural property that the mask runs upstream of every leak path. Each new shape simply provides its own bounding box and alpha mask; the apply pipeline is unchanged.

| # | Invariant | v0.5.3 | v0.5.4 | v0.5.5 |
|---|-----------|--------|--------|--------|
| P-1 | No unmasked bytes to disk | ✓ | ✓ | ✓ (re-verify across all 5 shapes) |
| P-2 | No unmasked bytes to agent | ✓ | ✓ | ✓ (re-verify) |
| P-3 | Opt-in default `[]` | ✓ | ✓ | ✓ (config field unchanged) |
| P-4 | Source-pixel coords; silent clamp | ✓ | ✓ | ✓ (re-verify for ellipse with rx != ry; rounded rect with corner_radius > w/2) |
| P-5 | Zero-area rejected at config time | ✓ | ✓ | Extended: `rx < 1` raises; `ry < 1` raises; `corner_radius < 0` raises. RoundedRectangle reuses x/y/w/h validation. |
| P-6 | Existing privacy invariants preserved | ✓ | ✓ | ✓ |
| P-7 | Alpha-mask boundary preservation | — | ✓ | ✓ (rounded-rect corner pixel outside the curve must be unchanged; non-circular ellipse exterior must be unchanged) |
| P-8 | Degenerate construction graceful | — | ✓ | Extended: corner_radius=0 is a valid degenerate case (rounded rect == sharp rect); rx==ry on Ellipse is a valid degenerate case (ellipse == circle) — both render correctly |
| P-9 | Off-frame bbox no-op | — | ✓ | ✓ (re-verify for rounded rect + ellipse) |

---

## 5. Test plan

New tests in `tests/test_sjon_privacy.py` (extension):

| Test | Asserts |
|---|---|
| `test_rounded_rectangle_is_shape` | `isinstance(_, PrivacyMaskShape)` |
| `test_rounded_rectangle_default_construction` | basic construction with corner_radius |
| `test_rounded_rectangle_zero_corner_radius_succeeds` | corner_radius=0 is valid (sharp rect) |
| `test_rounded_rectangle_negative_corner_radius_raises` | corner_radius=-1 raises ValueError |
| `test_rounded_rectangle_zero_width_raises` | w=0 raises (inherited rectangle rule) |
| `test_rounded_rectangle_solid_interior` | A pixel near the centre is the mask colour |
| `test_rounded_rectangle_corner_outside_curve_unchanged` | A pixel in the absolute corner of the bbox (within corner_radius of the corner) is unchanged — outside the rounded curve. P-7. |
| `test_rounded_rectangle_corner_radius_clamped_to_half` | corner_radius larger than half the shorter side is clamped at apply time without raising |
| `test_rounded_rectangle_off_frame_noop` | Wholly off-frame is no-op |
| `test_ellipse_is_shape` | `isinstance(_, PrivacyMaskShape)` |
| `test_ellipse_default_construction` | basic construction with distinct rx, ry |
| `test_ellipse_zero_rx_raises` | rx=0 raises |
| `test_ellipse_zero_ry_raises` | ry=0 raises |
| `test_ellipse_solid_interior` | Pixel at centre is mask colour |
| `test_ellipse_bbox_corner_unchanged` | Bbox corner is outside the ellipse — must be unchanged. P-7. |
| `test_ellipse_with_equal_radii_acts_like_circle` | rx == ry produces a circular alpha mask (degenerate case = circle) |
| `test_mixed_five_shape_list_all_applied` | List with rect + circle + polygon + rounded_rect + ellipse: all five regions masked correctly in one apply call |

Existing 51 v0.5.3+v0.5.4 privacy tests + 24 encoder tests must pass unchanged.

---

## 6. Mythic Engineering wave plan

### Wave 0 — TASK file (this commit)

### Wave 1 — Skald
- `docs/vision/MJUKBLAEJA.md` — short essay on modern UI rounded corners

### Wave 2 — Cartographer
- `docs/cartography/DATA_FLOW.md §4.10.14.1` addendum with the two new shapes' formulas

### Wave 3+4 — Architect+Forge merged (matches v0.5.4 pattern)
- `PrivacyMaskRoundedRectangle` dataclass + Protocol methods
- `PrivacyMaskEllipse` dataclass + Protocol methods
- INTERFACE.md update
- 17 new tests
- Run full Sjón suite; confirm 0 regressions

### Wave 5 — Auditor
- `docs/audit/AUDIT_v0.5.5_MJUKBLAEJA.md`
- Verify all 9 inherited invariants still hold
- Honest negative audit

### Wave 6 — Forge cleanup (only if Wave 5 raises items)

### Wave 7 — Scribe
- DEVLOG entry 18
- TASK §2 sealed
- Memory files updated

---

## 7. Forbidden moves

- ☒ Do **not** rename or modify existing shape classes. RoundedRectangle is NOT a subtype of Region. Ellipse is NOT a subtype of Circle. They are peers under the Protocol.
- ☒ Do **not** introduce new dependencies. Pillow's `rounded_rectangle` and `ellipse` are already available.
- ☒ Do **not** silently coerce a negative corner_radius to 0. Validate at construction.
- ☒ Do **not** branch the apply pipeline by shape kind. The Protocol absorbs each new shape via `bounding_box` + `alpha_mask` only.
- ☒ Do **not** weaken P-7 boundary preservation. Rounded-rect corners must leave bbox-corner pixels unchanged.

---

## 8. Backlog forward (post-v0.5.5)

| Item | Notes |
|---|---|
| v0.5.6 polygon-with-rounded-corners | Custom alpha-mask painter (no direct Pillow primitive) |
| v0.5.6 Bezier paths | Pillow ImageDraw.Path (newer Pillow versions) |
| v0.5.x mask inversion | "show only this region; veil all else" — useful for IDE-only mode |
| v0.5.x window-tracking masks | OS window enumeration |
| v0.5.x frontend mask-picker UI | Frontend dev |
| v0.6.x.1 MCP resources | mcp_server.py extension |
| v0.6.x Mode C Smiðja composition | Multi-step orchestration |
| **v0.8 Opið Vef** | Playwright; major roadmap successor |
| v0.9 Málari | Photopea editor (depends on v0.8) |
| v0.10 Langhúsið Ytra | VRChat OSC + MindSpark |
| v0.11 Bréfasamtök | Email |
| v0.4.1 first compile | MSVC Build Tools — operator-blocked |

---

## 9. Session-resumption pointer

If interrupted before Wave 7 closes, resume by:
1. Read this TASK file §2 for current phase
2. `git log --oneline -30` — identify which Wave commits exist
3. Continue from the first missing Wave

---

*Authored by Runa Gridweaver Freyjasdottir, in the autonomous Mythic Engineering mode requested by Volmarr 2026-05-09.*
*The next wave is the Skald.*
