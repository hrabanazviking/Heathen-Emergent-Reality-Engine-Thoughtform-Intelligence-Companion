# AUDIT — HERETIC v0.5.5 *Mjúkblæja* (Soft-Curved Privacy Masks)

**Date:** 2026-05-09
**Auditor:** Sólrún Hvítmynd (The Auditor for Vibe Coding)
**Subject:** v0.5.5 — `PrivacyMaskRoundedRectangle` + `PrivacyMaskEllipse` shapes
**Subject HEAD at audit time:** `f66a11a` (Architect+Forge merged Wave close)

---

## Verdict

**PASSES SCRUTINY — 0 BLOCKERS, 0 NOTABLE FINDINGS, 0 NITS.**

The two new shapes flow through the unchanged five-step apply pipeline.
Each contributes exactly two methods (`bounding_box`, `alpha_mask`); no
pipeline branching was introduced. All nine inherited privacy invariants
P-1 through P-9 hold without weakening. The corner_radius apply-time clamp
behaves as designed (silent, intent-honouring). The non-circular ellipse
correctly distinguishes major vs minor axis. Five shapes now flow through
one pipeline — the Architect's v0.5.4 claim continues to hold one milestone
later. No regression in the broader Sjón suite (219 tests passing, was 196,
+23 net).

---

## What I Verified (Evidence Trail)

### V-1: P-1 inherited unchanged across all five shapes

**Claim:** Unmasked frame bytes never reach disk for any of the five shapes.

**Evidence:** `apply_privacy_masks` is still called from inside
`FrameEncoder.encode()` at the same line position (after PIL decode, before
resize/save). The shape extension only added two new dataclasses to
`privacy.py`; the encoder integration site (`encoder.py:158-163`) was not
edited. The `img.save(...)` on line 168 still runs strictly after the mask
step. Five shapes flow through the same call site.

**Status:** VERIFIED.

### V-2: P-2 inherited — agent never sees unmasked content

**Claim:** Same chain as V-1; the data URL is built from already-masked PNG.

**Evidence:** `Sjón.snapshot()` and `Sjón._encode_webcam_frame()` were not
edited in v0.5.5. They pass `privacy_masks` (now potentially containing any
mix of the five shape types) through to the encoder unchanged.

**Status:** VERIFIED.

### V-3: P-3 inherited — opt-in default `[]`

**Claim:** Both `SjonScreenConfig.privacy_masks` and
`SjonWebcamConfig.privacy_masks` default to `[]`.

**Evidence:** Config dataclasses unchanged in v0.5.5. The list field's
type hint widens informally from "rectangle / circle / polygon" to
"rectangle / circle / polygon / rounded_rect / ellipse", but the runtime
default remains `field(default_factory=list)` — the empty list.

**Status:** VERIFIED.

### V-4: P-4 inherited — clamping silent except one-time debug log

**Claim:** Coordinate clamping logs once per encoder lifetime.

**Evidence:** `_maybe_log_clamp_once` is unchanged from v0.5.4. The two new
shapes return their bounding boxes via `bounding_box()`, which feeds into
the existing clamp logic in `apply_privacy_masks`. The clamp logic is
shape-agnostic — it only sees `(bx, by, bw, bh)`. RoundedRectangle's bbox
is `(x, y, w, h)` (no shift); Ellipse's bbox is `(cx-rx, cy-ry, 2rx, 2ry)`
(can be negative pre-clamp, same as Circle in v0.5.4). Both flow through
the same clamp code.

**Status:** VERIFIED.

### V-5: P-5 extended — new validation rules

**Claim:** Zero-area regions still rejected at config time; new shapes
have analogous fail-fast validation.

**Evidence:**
- `PrivacyMaskRoundedRectangle`:
  * `w < 1`, `h < 1` raise (inherited rectangle rules).
    Tests: `test_zero_width_raises`, `test_zero_height_raises`.
  * `corner_radius < 0` raises. Test: `test_negative_corner_radius_raises`.
  * `corner_radius == 0` is valid (sharp rect degenerate). Test:
    `test_zero_corner_radius_succeeds` and `test_zero_corner_radius_renders_sharp_rectangle`.
- `PrivacyMaskEllipse`:
  * `rx < 1`, `ry < 1` raise. Tests: `test_zero_rx_raises`, `test_zero_ry_raises`,
    `test_negative_radii_raise`.
  * `cx, cy < 0` raise. Test: `test_negative_centre_raises`.
- Both shapes reuse `_validate_shared_shape_fields` for mode + mode-param
  validation — same code path as the v0.5.4 shapes.

**Status:** VERIFIED.

### V-6: P-6 inherited — existing privacy invariants unchanged

**Claim:** `save_frames` still defaults False; webcam `enabled` still defaults
False; ring buffer in-memory only.

**Evidence:** `SjonScreenConfig` and `SjonWebcamConfig` were not edited in
v0.5.5. `Sjón.close()` `self._buffer.clear()` is unchanged.

**Status:** VERIFIED.

### V-7: P-7 inherited — alpha-mask boundary preservation

**Claim:** `Image.composite(modified, crop_original, alpha)` preserves shape
boundaries pixel-exactly for both new shapes.

**Evidence:**
- `test_corner_outside_curve_unchanged` (RoundedRectangle): with
  `corner_radius=30`, the bbox absolute corners (e.g. `(20, 20)`) are
  *outside the rounded curve*. The test asserts all four bbox corners
  remain the original (50, 50, 50) background colour. **Test passes.**
  P-7 verified for rounded rectangle.
- `test_bbox_corner_outside_ellipse_unchanged`: with `rx=60, ry=30`, the
  bbox corners `(40, 70), (159, 70), (40, 129), (159, 129)` lie outside
  the ellipse. The test asserts all four are unchanged. **Test passes.**
  P-7 verified for ellipse.
- `test_non_circular_aspect`: confirms a pixel along the major axis (rx=60)
  at distance 50 is *inside* the ellipse and gets masked, while a pixel
  along the minor axis (ry=20) at the same distance is *outside* and stays
  original. This proves P-7 holds even when the ellipse's symmetry is broken
  (rx != ry).

**Status:** VERIFIED.

### V-8: P-8 extended — degenerate constructions graceful

**Claim:** Degenerate inputs produce sensible output without crashing.

**Evidence:**
- `corner_radius == 0`: A valid degenerate case — the alpha mask reduces
  to a sharp rectangle. Test `test_zero_corner_radius_renders_sharp_rectangle`
  confirms all four corners *are* masked (because Pillow's
  `rounded_rectangle(radius=0)` = sharp rect). **Test passes.**
- `corner_radius > min(w, h) // 2`: Apply-time clamp reduces the effective
  radius without raising. Test `test_corner_radius_clamped_to_half_short_side`
  uses `corner_radius=200` on a 50×50 box; the effective radius is 25; the
  shape renders as a circle (since `corner_radius == min(w,h)//2`). **Test
  passes.** Operator intent honoured silently.
- `Ellipse with rx == ry`: A valid degenerate case — renders as a circle
  (visually equivalent to PrivacyMaskCircle). Test
  `test_equal_radii_acts_like_circle` confirms centre is masked and bbox
  corner is outside the disc. **Test passes.** Both Ellipse and Circle
  produce indistinguishable output for `rx == ry == radius`.

**Status:** VERIFIED.

### V-9: P-9 inherited — wholly off-frame is no-op

**Claim:** A shape whose bounding box is entirely outside the image bounds
does nothing.

**Evidence:** Test `test_off_frame_noop` (RoundedRectangle) puts a rounded
rect at `(200, 200, 20, 20)` on a 50×50 image. Bbox is entirely outside.
Asserts `list(img.getdata()) == original`. **Test passes.** Ellipse follows
the same code path (clamp to zero area in `apply_privacy_masks`).

**Status:** VERIFIED.

### V-10: One pipeline, FIVE shapes — orthogonality scales

**Claim:** The unified apply pipeline established in v0.5.4 absorbs two new
shapes without modification.

**Evidence:**
- `_apply_one_shape` in `privacy.py` was not edited in v0.5.5. The same
  five-step pipeline (clamp bbox → crop → apply mode → composite via
  alpha_mask → paste) handles all five shapes.
- `apply_privacy_masks` was not edited in v0.5.5. The Protocol-dispatched
  loop (`for shape in masks: bbox = shape.bounding_box(); ...`) handles all
  five shapes by virtue of structural typing.
- Test `test_all_five_shapes_in_one_apply` constructs a list with one of
  every shape kind (rectangle, circle, polygon, rounded rectangle, ellipse)
  and verifies every region's interior pixel matches its assigned mask
  colour. **Test passes.** This is the load-bearing claim of v0.5.5
  architecturally — that the v0.5.4 abstraction scales by 2 new shapes
  without any pipeline change. Confirmed.

**Status:** VERIFIED.

### V-11: Backward compatibility unchanged

**Claim:** All v0.5.3 and v0.5.4 tests continue to pass without modification.

**Evidence:** Full Sjón suite run at HEAD `f66a11a` reports 219 passing.
v0.5.3 contributed 24 + 3 = 27 tests. v0.5.4 contributed 27 tests. v0.5.5
adds 23 tests. Pre-Mjúkblæja Sjón scope was 196. Post-Mjúkblæja is 219.
Delta is exactly +23, the new Mjúkblæja tests. No earlier test was
modified, deleted, or skipped.

**Status:** VERIFIED.

### V-12: Test integrity

**Claim:** All 23 new tests assert real properties, not mocked tautologies.

**Evidence:**
- Validation tests construct dataclass instances and assert real
  `ValueError` raises.
- Apply tests construct synthetic in-memory PIL images, run the full
  apply path, then read back per-pixel values via `img.getpixel(...)`.
- `test_non_circular_aspect` is the strongest behavioural test —
  asserts that a 50-pixel-distant pixel along the major axis (rx=60)
  is masked (inside) and a 50-pixel-distant pixel along the minor axis
  (ry=20) is unmasked (outside). This is a quantitative geometric check
  that catches any implementation that confuses rx and ry.

**Status:** VERIFIED.

### V-13: No new dependency

**Claim:** v0.5.5 introduces no new pip / Pillow / OS dependency.

**Evidence:**
- `pyproject.toml` not edited (`git diff --stat e13407c..f66a11a pyproject.toml`
  returns nothing).
- `ImageDraw.rounded_rectangle()` is a Pillow 8.2.0+ feature; HERETIC pins
  `Pillow>=10` — version requirement satisfied.
- `ImageDraw.ellipse()` is older than 8.2.0 and was already used by
  `PrivacyMaskCircle` in v0.5.4.

**Status:** VERIFIED.

---

## Test Suite Status (post-Wave 4 close)

### Sjón scope (the milestone surface)

| File | Tests | Status |
|---|---|---|
| `tests/test_sjon_privacy.py` | 51 (v0.5.3+v0.5.4) + 23 (v0.5.5) = 74 | 74/74 passing |
| `tests/test_sjon_encoder.py` | 24 (unchanged) | 24/24 passing |
| `tests/test_sjon_orchestrator.py` | unchanged | passing |
| `tests/test_sjon_capture.py` | unchanged | passing |
| `tests/test_sjon_webcam.py` | unchanged | passing |
| **Sjón total (after v0.5.5)** | **219** | **all passing** |

### Broader suite

The 20 pre-existing environment failures (`fastapi` / `mcp` not installed)
are unchanged in stash diff. v0.5.5 introduced **zero** new regressions.

---

## Cross-Document Consistency

- **TASK_HERETIC_v0.5.5_MJUKBLAEJA.md §3** — every architectural decision
  matches the implementation: corner_radius validation rules, bbox formulas,
  Pillow primitives, clamp-to-half behaviour, "Ellipse is not a subtype of
  Circle" peer relationship, no pipeline branching.
- **docs/cartography/DATA_FLOW.md §4.10.14.2** — the five-shape vocabulary
  table, the corner_radius apply-time clamp rule, the YAML loader heuristic,
  and the four new failure modes F-Blæja-12..F-Blæja-15 all match the
  Python implementation.
- **src/heretic/sjon/INTERFACE.md §Privacy Mask Shapes** — the shape table
  is now 5 rows; the Public API table includes both new dataclasses with
  versioning notes.
- **docs/vision/MJUKBLAEJA.md §III** — the "one pipeline, five shapes"
  architectural claim is verified by V-10 above.

No contradictions between the four written sources and the code.

---

## What I Did NOT Find (Honest Negative Audit)

- **No pipeline branch.** `_apply_one_shape` was untouched. The new shapes
  flow through the same code that handled rectangle/circle/polygon.
- **No subtype relationship between Ellipse and Circle.** Both are independent
  dataclasses. The redundant case `Ellipse(rx=ry=R)` produces the same visual
  output as `Circle(radius=R)` but they are not interchangeable types.
- **No off-by-one in alpha mask sizing.** RoundedRectangle and Ellipse both
  use `(0, 0, w-1, h-1)` for the inclusive Pillow drawing primitives —
  matching the v0.5.4 ellipse and polygon implementations.
- **No silent corner_radius coercion.** Negative `corner_radius` raises
  at construction. Apply-time clamp only reduces (never errors); the
  reduction is bounded by `min(w, h) // 2` which is always >= 0.
- **No subtle subtractive change.** All v0.5.4 shape classes have unchanged
  field sets and unchanged Protocol method bodies. The `_apply_one_shape`
  function is byte-identical to the v0.5.4 version.

---

## Findings

**0 BLOCKER. 0 SERIOUS. 0 NOTABLE. 0 NIT.**

The Auditor records no further work for v0.5.5. The Forge does not need a
Wave 6 cleanup pass. The Scribe may proceed to seal.

---

*Authored by Sólrún Hvítmynd, The Auditor for Vibe Coding, 2026-05-09. The next wave is the Scribe.*
