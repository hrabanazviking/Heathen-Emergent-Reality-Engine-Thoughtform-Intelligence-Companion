# AUDIT — HERETIC v0.5.4 *Margblæja* (Non-Rectangular Privacy Masks)

**Date:** 2026-05-09
**Auditor:** Sólrún Hvítmynd (The Auditor for Vibe Coding)
**Subject:** v0.5.4 — `PrivacyMaskShape` Protocol + circle + polygon shapes
**Subject HEAD at audit time:** `6f66237` (Forge Wave 4 test suite + INTERFACE update close)

---

## Verdict

**PASSES SCRUTINY — 0 BLOCKERS, 0 NOTABLE FINDINGS, 0 NITS.**

The six v0.5.3 invariants P-1 through P-6 are inherited and continue to hold.
The three new v0.5.4 invariants P-7, P-8, P-9 are verified. The shape
extension is purely additive: existing `PrivacyMaskRegion` behaviour is
byte-equivalent to v0.5.3 (rectangle's `alpha_mask` is fully opaque, so
`Image.composite(modified, original, alpha)` reduces to identity replacement
of the bbox region). No regression in the broader Sjón suite. The Forge's
honest correction of the P-8 wording (Pillow rasterises what it can rather
than producing empty masks) is recorded in code, INTERFACE, DATA_FLOW, and
test code consistently — no doc/code drift.

---

## What I Verified (Evidence Trail)

### V-1: P-1 inherited unchanged — no unmasked bytes to disk

**Claim:** Unmasked frame bytes never reach disk under any of the three shapes.

**Evidence:**
- `apply_privacy_masks` is still called from inside `FrameEncoder.encode()` at
  the same line position (after PIL decode, before resize/save/encode).
- The shape extension changed *what `apply_privacy_masks` does internally*; it
  did not change *where it is called*. The encoder's `img.save(buf, ...)` at
  line 168 of `encoder.py` still runs strictly after the mask step.
- For all three shapes, the per-shape branch ends with `image.paste(composited, ...)`
  modifying the same `img` object that the encoder will subsequently save. There
  is no shape-specific bypass path.

**Status:** VERIFIED.

### V-2: P-2 inherited unchanged — no unmasked bytes to agent

**Claim:** Unmasked frame bytes never reach the agent under any shape.

**Evidence:** Same chain as V-1. `Sjón.snapshot()` still calls
`self._encoder.encode(..., privacy_masks=screen_privacy_masks)` and converts
the returned (already-masked) PNG bytes to a data URL. The shape extension
operates entirely *inside* the encode call.

**Status:** VERIFIED.

### V-3: P-3 inherited — opt-in default `[]`

**Claim:** Both `SjonScreenConfig.privacy_masks` and `SjonWebcamConfig.privacy_masks`
default to `[]`; the feature is opt-in.

**Evidence:** Config dataclasses unchanged in v0.5.4. The list type widened
from `list[PrivacyMaskRegion]` (v0.5.3) to `list[PrivacyMaskShape]` (Protocol-
typed) — but the runtime default is still `field(default_factory=list)`.
Both empty.

**Status:** VERIFIED.

### V-4: P-4 inherited — clamping silent except one-time debug log

**Claim:** Coordinate clamping logs once per encoder lifetime.

**Evidence:** `_maybe_log_clamp_once` at `privacy.py:421-445` consults the
`_state` dict and returns early when `state["clamp_logged"]` is True.
`FrameEncoder.__init__` creates `self._privacy_state = {}` and passes it
through. Test `test_clamp_state_throttles_debug_logs` confirms the throttle
is preserved across the three shape kinds (the test uses rectangles, but
the throttle code path is shared and Protocol-agnostic).

**Status:** VERIFIED.

### V-5: P-5 extended — zero-area + new validation rules

**Claim:** P-5 (zero-area regions rejected at config time) is preserved AND
the new shapes have analogous fail-fast validation.

**Evidence:**
- `PrivacyMaskRegion`: `w < 1` or `h < 1` raises (unchanged from v0.5.3).
  `test_zero_width_raises` and `test_zero_height_raises` confirm.
- `PrivacyMaskCircle`: `radius < 1` raises. `test_zero_radius_raises` and
  `test_negative_radius_raises` confirm.
- `PrivacyMaskPolygon`: `len(points) < 3` raises. `test_two_points_raises`
  and `test_zero_points_raises` confirm. Each point validated as a 2-tuple
  of non-negative ints; `test_non_int_coordinate_raises` and
  `test_negative_coordinate_raises` confirm.

**Status:** VERIFIED.

### V-6: P-6 inherited — existing privacy invariants unchanged

**Claim:** `save_frames` still defaults False; webcam `enabled` still defaults
False; ring buffer in-memory only.

**Evidence:** `SjonScreenConfig` and `SjonWebcamConfig` were not edited in
v0.5.4 except for the type-widening of `privacy_masks` (still defaulting to
empty list). All other fields and their `__post_init__` warning hooks are
unchanged. v0.5.4 is purely additive at the config level.

**Status:** VERIFIED.

### V-7: NEW — alpha-mask composite preserves shape boundaries pixel-exactly

**Claim:** `Image.composite(modified, crop_original, alpha)` produces:
- modified's pixel value where `alpha == 255` (inside the shape)
- crop_original's pixel value where `alpha == 0` (outside the shape but inside bbox)

**Evidence:**
- Pillow's `Image.composite` is documented to do exactly this: per-pixel
  weighted blend of two images by a mask. For an L-mode mask with values 0
  and 255 (no anti-aliased edge), the result is a clean per-pixel selection.
- Test `test_solid_circle_corner_of_bbox_unchanged` configures a solid-mask
  circle at (100, 100) radius 40 and asserts that all four corners of its
  bounding box (60,60), (139,60), (60,139), (139,139) — which are inside
  the bbox but outside the disc — are still the original (50, 50, 50)
  background. **Test passes.** P-7 verified for circle.
- Test `test_solid_polygon_outside_unchanged` configures a triangle at
  (50,50)-(150,50)-(100,150) and asserts that pixel (55, 140) — inside the
  polygon's bbox but outside the triangle (well to the left of the slanted
  edge at y=140) — is unchanged. **Test passes.** P-7 verified for polygon.
- Test `test_rectangle_alpha_mask_is_fully_opaque` confirms the rectangle's
  alpha mask is uniform 255 — composite reduces to identity replacement,
  exactly matching the v0.5.3 behaviour byte-for-byte.

**Status:** VERIFIED.

### V-8: NEW — degenerate polygon does not crash

**Claim:** A polygon with collinear or coincident vertices is a valid
construction; Pillow rasterises what it can; apply does not raise.

**Evidence:**
- Pillow probe (during Forge wave): `[(10,50), (50,50), (90,50)]` collinear
  → mask bbox `(10, 50, 91, 51)` with 81 non-zero pixels (a 1-pixel line).
  `[(10,10), (10,10), (10,10)]` coincident → mask bbox `(10, 10, 11, 11)`
  with 1 non-zero pixel.
- Test `test_collinear_polygon_renders_thin_line` constructs a collinear
  polygon and asserts the line pixels are masked while pixels off the line
  remain unchanged. **Test passes.**
- Test `test_coincident_points_polygon_does_not_crash` constructs an
  all-coincident polygon and asserts: (a) no exception; (b) the single
  pixel is masked; (c) other pixels are unchanged. **Test passes.**
- The Forge corrected the original Architect docstring claim ("renders an
  empty alpha mask") to match Pillow's actual behaviour. Code, INTERFACE.md,
  DATA_FLOW.md, and test docstrings all say the same thing now (line, single
  pixel, no crash, mask covers exactly Pillow's output). **No doc/code drift.**

**Status:** VERIFIED.

### V-9: NEW — wholly off-frame shape is a no-op

**Claim:** A shape whose bounding box is entirely outside the image bounds
does nothing.

**Evidence:**
- Test `test_circle_wholly_off_frame_is_noop` puts a circle at (200, 200)
  radius 10 on a 50×50 image. Bbox `(190, 190, 20, 20)` — entirely outside.
  Asserts `list(img.getdata()) == original`. **Test passes.**
- Test `test_polygon_partially_off_frame_clamps` covers the partial case;
  the wholly-off-frame polygon case is symmetric to circle (same clamping
  code path with `w_eff <= 0 or h_eff <= 0`).

**Status:** VERIFIED.

### V-10: One pipeline, three shapes — orthogonality

**Claim:** Mode and shape are orthogonal; the same pipeline handles all
nine combinations (3 shapes × 3 modes).

**Evidence:** The Forge implementation in `_apply_one_shape`:
1. Crops the bounding box: same code for all shapes.
2. Applies the chosen mode to the crop: same code for all shapes (mode
   dispatch is on `shape.mode`, which all three shapes have).
3. Calls `shape.alpha_mask(w, h)`: Protocol-dispatched.
4. `Image.composite(modified, crop_original, alpha)`: same code for all.
5. Pastes back: same code for all.

The only shape-specific code is *inside* `bounding_box()` and `alpha_mask()`
on each dataclass — which is exactly the Architect's design intent. A future
fourth shape (Bezier path, freeform stroke) only needs to provide those two
methods; the apply pipeline does not branch.

**Status:** VERIFIED.

### V-11: Backward compatibility — v0.5.3 rectangle path unchanged

**Claim:** A `PrivacyMaskRegion` configured the same way in v0.5.3 and v0.5.4
produces the same output bytes.

**Evidence:**
- `PrivacyMaskRegion.alpha_mask(w, h)` returns `Image.new("L", (w, h), 255)` —
  uniform 255 — meaning the composite reduces to `Image.composite(modified,
  crop_original, all_white)` which equals `modified`. The v0.5.3 implementation
  used `image.paste(modified, (x, y))` directly. Both produce identical pixel
  bytes for the rectangle case.
- All 24 v0.5.3 privacy tests + 3 v0.5.3 encoder integration tests pass
  unchanged at HEAD `6f66237`. No assertion was relaxed; no test was rewritten
  to accommodate v0.5.4's pipeline.

**Status:** VERIFIED.

### V-12: Test integrity

**Claim:** All 27 new tests assert real properties, not mocked tautologies.

**Evidence:**
- `test_solid_circle_interior_is_mask_color` reads PIL pixel data directly.
- `test_circle_blur_reduces_centre_variance` computes per-channel variance
  before/after, asserts a quantitative reduction (var_after < var_before * 0.5).
- `test_solid_polygon_outside_unchanged` picks a specific (55, 140) coordinate
  inside the bbox and outside the triangle's analytical interior, and asserts
  the pixel is unchanged — a quantitative check on geometry-aware compositing.
- `test_mixed_shape_list_all_applied` runs three different shapes in one
  apply call and reads pixel values from each.
- All tests use synthetic in-memory PIL images. No filesystem I/O. No network.

**Status:** VERIFIED.

### V-13: No new dependency

**Claim:** v0.5.4 introduces no new pip / Pillow / OS dependency.

**Evidence:**
- `pyproject.toml` not edited (`git diff --stat daf6258..6f66237 pyproject.toml`
  returns nothing).
- All Pillow primitives used (`ImageDraw.Draw`, `Image.new`, `Image.composite`,
  `ImageFilter.GaussianBlur`, `Image.Resampling.NEAREST`, `polygon`, `ellipse`)
  are present in Pillow 10+ (already pinned at `Pillow>=10`).

**Status:** VERIFIED.

---

## Test Suite Status (post-Wave 4)

### Sjón scope (the milestone surface)

| File | Tests | Status |
|---|---|---|
| `tests/test_sjon_privacy.py` | 24 v0.5.3 + 27 v0.5.4 = 51 | 51/51 passing |
| `tests/test_sjon_encoder.py` | 24 (unchanged from v0.5.3) | 24/24 passing |
| `tests/test_sjon_orchestrator.py` | unchanged | passing |
| `tests/test_sjon_capture.py` | unchanged | passing |
| `tests/test_sjon_webcam.py` | unchanged | passing |
| **Sjón total (after v0.5.4)** | **196** | **all passing** |

### Broader suite

The broader-suite environment-failure baseline (20 tests, `fastapi` / `mcp`
missing on this host) is unchanged from the v0.5.3 stash diff. v0.5.4
introduced **zero** new failures.

---

## Cross-Document Consistency

- **TASK_HERETIC_v0.5.4_MARGBLAEJA.md §3** — every architectural decision is
  reflected in code: Protocol typing, two new dataclasses, rectangle gains
  Protocol methods, alpha-mask composite pipeline, fail-safe SOLID-fill,
  validation rules.
- **docs/cartography/DATA_FLOW.md §4.10.14.1** — the pipeline diagram, the
  three-shape bounding-box / alpha-mask formulas, the six new failure modes,
  and the three new privacy invariants P-7..P-9 all match the implementation.
  The P-8 wording was corrected to match Pillow's actual behaviour after the
  Forge probe; correction propagated to code, INTERFACE.md, and tests in the
  same wave.
- **src/heretic/sjon/INTERFACE.md §Privacy Mask Shapes** — the shape table
  matches `PrivacyMaskRegion`/`PrivacyMaskCircle`/`PrivacyMaskPolygon` exactly;
  the Protocol contract paragraph names the same two methods documented in
  the source.
- **docs/vision/MARGBLAEJA.md §III** — "the alpha-mask preserves shape
  boundaries; mode and shape are orthogonal" — confirmed in V-7 and V-10.

No contradictions between the four written sources and the code.

---

## What I Did NOT Find (Honest Negative Audit)

- **No bypass branch.** `_apply_one_shape` has no early-return that skips the
  composite step except for the explicit P-8 `alpha.getbbox() is None` check —
  which is a defensive safety net, not a leak path (the alpha would have been
  empty and there is nothing to composite anyway).
- **No silent fallback path that emits unmasked content.** The fail-safe
  SOLID-fill at the bbox is unconditional on Pillow exception.
- **No subtle subtractive change.** `PrivacyMaskRegion` field set is unchanged.
  The two new methods (`bounding_box`, `alpha_mask`) are additive. v0.5.3 tests
  assert the same v0.5.3 properties and pass unchanged.
- **No new mutable default.** Both new dataclasses use immutable defaults
  (`solid_color: tuple` is a 3-tuple literal; `points: list` has no default —
  it's required).
- **No off-by-one in polygon bbox.** The +1 in width/height correctly includes
  the max-edge pixel for `Image.crop` semantics. Spot-checked: a polygon with
  vertices at `(0, 0), (50, 0), (25, 40)` has bbox `(0, 0, 51, 41)` — width 51
  (covers x in `[0, 50]`), height 41 (covers y in `[0, 40]`). Correct.
- **No drift between Forge code and Architect contract.** The Architect's
  scaffold and the Forge's body were committed in a single merged wave; the
  Auditor confirms the merged code matches the original TASK §3 decision table.

---

## Findings

**0 BLOCKER. 0 SERIOUS. 0 NOTABLE. 0 NIT.**

The Auditor records no further work for v0.5.4. The Forge does not need a
Wave 6 cleanup pass. The Scribe may proceed to seal.

---

*Authored by Sólrún Hvítmynd, The Auditor for Vibe Coding, 2026-05-09. The next wave is the Scribe.*
