# TASK — HERETIC v0.5.4 MARGBLÆJA (Many-Shaped Veils)

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-09** (immediately after v0.5.3 *Blæja* sealed at `daf6258`)
>
> **Codename (proposed, Skald to seal):** *Margblæja* — "many-veiled" / the veil that speaks in many forms. The Norse compound *marg-* (many) + *blæja* (veil) names a single disposition with an expanded vocabulary, not a new disposition.
>
> **Mythic Engineering mode:** AUTONOMOUS continuation. Volmarr asleep / hands-off; this is the third milestone of the autonomous session.

---

## 1. Task scope

Extend the v0.5.3 *Blæja* privacy-mask layer with **non-rectangular shapes**:

1. **Circle** — defined by centre `(cx, cy)` and `radius`. Used to obscure round elements (a status indicator, a profile photo thumbnail, a circular video tile).
2. **Polygon** — defined by an ordered list of vertices `[(x1,y1), (x2,y2), ...]` with `>=3` points. Used to obscure irregular shapes (an angled window, a non-axis-aligned region, a diagonal strip).

The existing rectangular `PrivacyMaskRegion` is preserved unchanged as the simplest shape. All three shapes share the same three application modes (`blur`, `solid`, `pixelate`) and the same disposition: the mask runs inside `FrameEncoder.encode()` after PIL decode and before any leak path.

The shape vocabulary is unified through a `PrivacyMaskShape` Protocol. Both new dataclasses implement two methods — `bounding_box()` and `alpha_mask(w, h)` — alongside the same mode-and-mode-params surface. `apply_privacy_masks` dispatches via the Protocol so all three shapes flow through the same composite pipeline.

---

## 2. Current status — 2026-05-09

**Phase:** v0.5.4 **SHIPPED + AUDITED + SEALED.** All seven waves closed.

**HEAD (development) at audit close:** `9d09b68` (Auditor PASSES SCRUTINY)

**Test count after v0.5.4:** Sjón privacy 24 → 51 (+27 new Margblæja tests). Sjón total 169 → 196. No regressions.

### v0.5.4 deliverables — all complete

- ✅ Wave 0 — `chore: open v0.5.4 ...` at `045524d`
- ✅ Wave 1 — Skald: `docs/vision/MARGBLAEJA.md` at `0080687`
- ✅ Wave 2 — Cartographer: `docs/cartography/DATA_FLOW.md §4.10.14.1` at `06d5627`
- ✅ Waves 3+4a — Architect+Forge merged: Protocol + 2 new dataclasses + apply refactor at `c49bdcd`
- ✅ Wave 4b — Forge: 27 tests + INTERFACE.md + P-8 truth correction at `6f66237`
- ✅ Wave 5 — Auditor: `docs/audit/AUDIT_v0.5.4_MARGBLAEJA.md` PASSES at `9d09b68`
- ⏭ Wave 6 — Forge cleanup (skipped; audit found nothing to remediate)
- ✅ Wave 7 — Scribe: DEVLOG entry 17, this TASK seal, memory refresh (final commit)

### What v0.5.4 does NOT add

- Animated shapes (a region whose path drifts each frame) — out of scope
- Bezier-curve shapes — v0.5.5+
- Window-tracking masks (mask follows a moving window) — v0.6+
- Frontend shape-picker UI — operator edits `heretic.yaml` directly
- Mask groups / unions / intersections — operator can stack regions for compound coverage

---

## 3. Architectural decisions (Architect to confirm at Wave 3)

| Decision | Choice | Rationale |
|---|---|---|
| Shape unification | `PrivacyMaskShape` typing.Protocol with two methods + mode field | Structural typing keeps the three shapes decoupled while sharing the Protocol contract; no inheritance / dataclass collision |
| `bounding_box()` | Returns `(x, y, w, h)` of the **smallest axis-aligned rectangle containing the shape** | Lets `apply_privacy_masks` reuse the v0.5.3 clamp logic unchanged |
| `alpha_mask(w, h)` | Returns a Pillow `"L"` mode image of size `(w, h)` with shape interior = 255, exterior = 0 | The composite step pastes the *modified crop* over the *original crop* using this alpha mask; outside the shape, the original pixels are preserved |
| Composite primitive | `Image.composite(modified_crop, original_crop, alpha_mask)` then paste back at clamped (x, y) | Pillow primitive; pixel-exact; honoured by every mode (blur, solid, pixelate) uniformly |
| Mode application | Unchanged — applied to the **bounding-box crop** before composite | Same code path as v0.5.3 rectangle; the alpha mask carves out the shape from the modified crop |
| Backward compatibility | `PrivacyMaskRegion` (rectangle) gains `bounding_box()` and `alpha_mask(w, h)` methods. `alpha_mask` for rectangle returns a fully-opaque `"L"` image — the composite is a no-op outside the rectangle case (which is exactly the existing v0.5.3 behaviour). | Existing tests pass unchanged |
| Circle field shape | `PrivacyMaskCircle(cx, cy, radius, mode, blur_radius?, solid_color?, pixelate_factor?)` | Centre-and-radius is the natural circle representation |
| Polygon field shape | `PrivacyMaskPolygon(points: list[tuple[int, int]], mode, ...)` | Operator authors a list of (x, y) vertices in source pixel space |
| Polygon validation | `len(points) >= 3`; each point a 2-tuple of non-negative ints; ints validated by `__post_init__` | Less than 3 vertices is not a polygon; non-int coords are operator typo |
| Circle validation | `cx, cy >= 0`; `radius >= 1` | Standard |
| `bounding_box` for circle | `(cx - radius, cy - radius, 2*radius, 2*radius)` clamped at apply time | Exact bounding box of a disc |
| `bounding_box` for polygon | `(min_x, min_y, max_x - min_x, max_y - min_y)` from vertex coords; `+1` width/height to include max edge pixels | Standard axis-aligned bounding box |
| Type hint of `privacy_masks` | `list[PrivacyMaskShape]` | Protocol-typed; `PrivacyMaskRegion` / `PrivacyMaskCircle` / `PrivacyMaskPolygon` all satisfy it |
| Apply pipeline | `for shape in masks: bbox = shape.bounding_box(); clamp; crop; modified = apply_mode(crop, shape); alpha = shape.alpha_mask(w_eff, h_eff); composited = Image.composite(modified, crop, alpha); paste` | Single uniform pipeline; mode and shape are orthogonal |
| Fail-safe | Same as v0.5.3 — on any Pillow exception during apply, fall back to SOLID-fill of the **bounding box** | Conservative: better to over-mask than under-mask |

---

## 4. Privacy invariants (Auditor verification subjects)

The six v0.5.3 invariants P-1..P-6 are inherited and must continue to hold:

| # | Invariant | v0.5.3 status | v0.5.4 verification |
|---|-----------|---------------|---------------------|
| P-1 | Unmasked frame bytes never reach disk | ✓ verified | Re-verify across all three shapes |
| P-2 | Unmasked frame bytes never reach the agent | ✓ verified | Re-verify across all three shapes |
| P-3 | `privacy_masks` defaults to `[]` (opt-in) | ✓ verified | Unchanged (config field is the same) |
| P-4 | Coordinates in source pixel space; clamp silent | ✓ verified | Re-verify for circle bbox (cx-radius can be negative pre-clamp) and polygon bbox |
| P-5 | Zero-area regions rejected at config time | ✓ verified | Extend: circle radius < 1 raises; polygon < 3 points raises |
| P-6 | Existing privacy invariants preserved | ✓ verified | Unchanged |

New v0.5.4 invariants:

| # | Invariant |
|---|-----------|
| **P-7** | The alpha-mask composite step preserves shape boundaries pixel-exactly. A pixel outside the shape but inside the bounding box must be unchanged; a pixel inside the shape must equal the modified-crop pixel. |
| **P-8** | A polygon with co-linear or coincident vertices is a degenerate but valid polygon — Pillow handles it (renders empty region); apply continues; debug log fires once for "degenerate polygon" via the same one-time clamp-log throttle. |
| **P-9** | A circle whose bounding box is wholly off-frame is a no-op (same semantics as the equivalent rectangle case). |

---

## 5. Composite pipeline sketch (Cartographer + Forge)

```
  MARGBLÆJA — APPLY ONE SHAPE (rectangle / circle / polygon — one path)

  shape.bounding_box() → (bx, by, bw, bh)             # source coords
  clamp to image bounds → (x_eff, y_eff, w_eff, h_eff)
  if w_eff <= 0 or h_eff <= 0: log clamp once, skip

  crop_original = image.crop((x_eff, y_eff, x_eff+w_eff, y_eff+h_eff))
  modified      = apply_mode(crop_original, shape)    # blur / solid / pixelate

  alpha = shape.alpha_mask(w_eff, h_eff)              # "L" mode; in-shape=255

  composited = Image.composite(modified, crop_original, alpha)
                # for each pixel:
                #   if alpha[p] == 255: composited[p] = modified[p]
                #   if alpha[p] ==   0: composited[p] = crop_original[p]
                #   between:           linear blend by alpha (anti-aliased edge)

  image.paste(composited, (x_eff, y_eff))
```

The crucial property: **the alpha-mask preserves shape boundaries**. A pixel outside the shape but inside the bounding box keeps its original value (it was in `crop_original`, not in `modified`). The body veils only what the operator drew.

---

## 6. Test plan — Forge writes; Auditor verifies

New tests in `tests/test_sjon_privacy.py` (extension):

| Test | Asserts |
|---|---|
| `test_circle_interior_masked_solid` | A pixel at the centre of a solid-mode circle is the mask colour |
| `test_circle_exterior_unchanged` | A pixel inside the bounding box but outside the circle radius is unchanged |
| `test_circle_corner_unchanged` | The four corners of the circle's bounding box are unchanged (they're outside the disc) |
| `test_circle_blur_reduces_variance` | A blur-mode circle reduces variance at the centre but not outside |
| `test_circle_partially_off_frame_clamps` | Circle with `cx - radius < 0` clamps; visible disc-portion is masked |
| `test_circle_wholly_off_frame_is_noop` | Circle entirely outside image → no change |
| `test_polygon_triangle_solid` | A 3-vertex triangle with solid mode masks interior |
| `test_polygon_exterior_unchanged` | Pixel outside the polygon's interior (but inside bbox) is unchanged |
| `test_polygon_5_vertex_pentagon` | A more complex polygon still masks correctly |
| `test_polygon_partially_off_frame` | Polygon vertices off-frame are clamped; visible portion masked |
| `test_polygon_invalid_too_few_points_raises` | `PrivacyMaskPolygon(points=[(0,0), (10,10)])` raises ValueError |
| `test_polygon_invalid_non_int_raises` | A point `(0, "10")` raises ValueError |
| `test_circle_invalid_zero_radius_raises` | `PrivacyMaskCircle(radius=0)` raises ValueError |
| `test_circle_invalid_negative_radius_raises` | Negative radius raises |
| `test_mixed_shape_list_all_applied` | A list with one Region + one Circle + one Polygon: all three regions masked correctly |
| `test_rectangle_alpha_mask_is_fully_opaque` | `PrivacyMaskRegion.alpha_mask(w,h)` returns an L image with all pixels == 255 (verifying backward compat) |

Integration test extension in `tests/test_sjon_encoder.py`:

| Test | Asserts |
|---|---|
| `test_encoder_applies_circle_mask_through_full_pipeline` | A circle mask survives encode + resize end-to-end |

Existing 24 v0.5.3 privacy tests + 3 v0.5.3 encoder integration tests must continue to pass without modification.

---

## 7. Mythic Engineering wave plan

### Wave 0 — TASK file (this commit)

### Wave 1 — Skald
- `docs/vision/MARGBLAEJA.md` — what it means for a disposition to grow more expressive
- Brief — this is an extension, not a new philosophy

### Wave 2 — Cartographer
- `docs/cartography/DATA_FLOW.md §4.10.14` addendum: shape Protocol + composite pipeline; one-pipeline-three-shapes diagram

### Wave 3 — Architect
- `PrivacyMaskShape` Protocol declared in `privacy.py`
- `PrivacyMaskCircle` and `PrivacyMaskPolygon` dataclasses with construction-time validation
- Existing `PrivacyMaskRegion` gains `bounding_box()` and `alpha_mask(w, h)` methods
- INTERFACE.md updated: shape table, Protocol contract, three concrete classes
- Function signatures of new methods sealed (NotImplementedError bodies; Forge fills)

### Wave 4 — Forge
- Implement `bounding_box()` and `alpha_mask(w, h)` on all three shapes
- Refactor `apply_privacy_masks` to use the Protocol-dispatched pipeline
- Add 16+ new tests covering all paths above
- Extend `tests/test_sjon_encoder.py` with 1 integration test for circle through full encode+resize
- Run full Sjón suite; confirm 0 regressions

### Wave 5 — Auditor
- `docs/audit/AUDIT_v0.5.4_MARGBLAEJA.md`
- Verify all 6 carried-over invariants + 3 new (P-7, P-8, P-9)
- Verify backward compatibility — rectangle path unchanged in observable behaviour
- Honest negative audit — no leak path missed

### Wave 6 — Forge cleanup (only if Wave 5 raises items)

### Wave 7 — Scribe
- DEVLOG entry 17
- TASK §2 sealed
- `project_heretic_status.md` updated; `MEMORY.md` quick-facts refreshed

---

## 8. Forbidden moves

- ☒ Do **not** rename `PrivacyMaskRegion`. The name is used in INTERFACE.md, DATA_FLOW.md, the v0.5.3 audit, the v0.5.3 DEVLOG entry, and existing test code. Renaming would be a subtractive change.
- ☒ Do **not** change `PrivacyMaskRegion`'s field set. Adding methods is fine; changing fields is not.
- ☒ Do **not** introduce a new dependency. Pillow already supplies `ImageDraw.Draw` for circle and polygon rasterisation.
- ☒ Do **not** make the new shapes inherit from `PrivacyMaskRegion`. They are *peers* under the Protocol, not subtypes of the rectangle.
- ☒ Do **not** silently let a polygon with < 3 points pass. Validate at construction.
- ☒ Do **not** dilute P-1..P-6 in the alpha-mask composite. Outside the shape, the original pixel must remain — the composite mathematics must preserve that.

---

## 9. Backlog forward (post-v0.5.4)

| Item | Requires | Notes |
|---|---|---|
| v0.5.5 bezier mask paths | Pillow ImageDraw.Path | Curved shapes |
| v0.5.x window-tracking masks | OS window enumeration | Mask follows a named window |
| v0.5.x frontend mask-picker UI | Frontend dev | Visual region drawing in Eldahús |
| v0.5.3 webcam sub-badge | Frontend only | Carried X-1 NIT from v0.5.2 |
| v0.6.x.1 MCP resources | mcp_server.py extension | `resources/*` file hosting |
| v0.6.x Mode C Smiðja composition | No external gate | Multi-step Brúarhönd + Forge |
| **v0.8 Opið Vef** | Playwright | Full browser sense |
| v0.9 Málari | Playwright (v0.8) | Photopea editor |
| v0.10 Langhúsið Ytra | OSC + MindSpark | VRChat embodiment |
| v0.11 Bréfasamtök | aiosmtplib + aioimaplib | Email |
| v0.4.1 first compile | MSVC Build Tools | Operator-blocked |

The natural successor in roadmap order is **v0.8 Opið Vef** — the full Playwright browser sense.

---

## 10. Session-resumption pointer

If interrupted before Wave 7 closes, resume by:
1. Read this TASK file §2 for current phase
2. `git log --oneline -25` — identify which Wave commits exist
3. Continue from the first missing Wave

---

*Authored by Runa Gridweaver Freyjasdottir, in the autonomous Mythic Engineering mode requested by Volmarr 2026-05-09.*
*The next wave is the Skald.*
