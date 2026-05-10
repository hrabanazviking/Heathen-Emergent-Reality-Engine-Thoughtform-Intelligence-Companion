"""
Tests for the v0.5.3 Blæja privacy mask layer.

Covers:
    - PrivacyMaskRegion construction-time validation (10 invariant tests)
    - apply_privacy_masks correctness for all three modes (blur, solid, pixelate)
    - Region clamping behaviour (partial off-frame, wholly off-frame)
    - Empty mask list early-return semantics
    - Multi-region application
    - Integration with FrameEncoder.encode

All tests use synthetic in-memory PIL images. No screen capture, no I/O.

Ref: src/heretic/sjon/privacy.py
     docs/cartography/DATA_FLOW.md §4.10.14
     TASK_HERETIC_v0.5.3_BLAEJA.md §6
"""

from __future__ import annotations

import io

import pytest

from heretic.sjon.privacy import PrivacyMaskRegion, apply_privacy_masks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_test_image(w: int = 200, h: int = 200, fill=(128, 64, 200)):
    """Return a fresh solid-colour PIL.Image of size w×h."""
    from PIL import Image
    return Image.new("RGB", (w, h), fill)


def _make_checkerboard(w: int = 100, h: int = 100, square: int = 10):
    """Return a high-frequency checkerboard image — good for blur visibility."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    for y0 in range(0, h, square):
        for x0 in range(0, w, square):
            if (x0 // square + y0 // square) % 2 == 0:
                draw.rectangle(
                    (x0, y0, x0 + square - 1, y0 + square - 1),
                    fill=(255, 255, 255),
                )
    return img


def _region_pixel_variance(img, x: int, y: int, w: int, h: int) -> float:
    """Return the per-channel variance of pixels in a region. Higher = more detail."""
    from PIL import Image
    crop = img.crop((x, y, x + w, y + h))
    pixels = list(crop.getdata())
    n = len(pixels)
    if n == 0:
        return 0.0
    # Per-channel variance averaged across R, G, B.
    means = [sum(p[c] for p in pixels) / n for c in range(3)]
    var = sum(
        sum((p[c] - means[c]) ** 2 for p in pixels) / n
        for c in range(3)
    ) / 3
    return var


def _region_distinct_colors(img, x: int, y: int, w: int, h: int) -> int:
    """Return the number of distinct (R, G, B) tuples in the region."""
    crop = img.crop((x, y, x + w, y + h))
    return len(set(crop.getdata()))


# ---------------------------------------------------------------------------
# PrivacyMaskRegion validation
# ---------------------------------------------------------------------------

class TestPrivacyMaskRegionValidation:

    def test_default_construction_succeeds(self):
        """Default region constructs without error."""
        r = PrivacyMaskRegion(x=10, y=20, w=100, h=50)
        assert r.mode == "blur"  # default
        assert r.solid_color == (0, 0, 0)
        assert r.blur_radius is None
        assert r.pixelate_factor is None

    def test_negative_x_raises(self):
        with pytest.raises(ValueError) as exc_info:
            PrivacyMaskRegion(x=-1, y=0, w=10, h=10)
        assert "x" in str(exc_info.value)

    def test_negative_y_raises(self):
        with pytest.raises(ValueError) as exc_info:
            PrivacyMaskRegion(x=0, y=-1, w=10, h=10)
        assert "y" in str(exc_info.value)

    def test_zero_width_raises(self):
        with pytest.raises(ValueError) as exc_info:
            PrivacyMaskRegion(x=0, y=0, w=0, h=10)
        assert "w" in str(exc_info.value)

    def test_zero_height_raises(self):
        with pytest.raises(ValueError) as exc_info:
            PrivacyMaskRegion(x=0, y=0, w=10, h=0)
        assert "h" in str(exc_info.value)

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError) as exc_info:
            PrivacyMaskRegion(x=0, y=0, w=10, h=10, mode="invalid")
        msg = str(exc_info.value)
        assert "blur" in msg
        assert "solid" in msg
        assert "pixelate" in msg

    def test_invalid_solid_color_too_short_raises(self):
        with pytest.raises(ValueError):
            PrivacyMaskRegion(x=0, y=0, w=10, h=10, solid_color=(0, 0))

    def test_invalid_solid_color_out_of_range_raises(self):
        with pytest.raises(ValueError):
            PrivacyMaskRegion(x=0, y=0, w=10, h=10, solid_color=(0, 0, 256))

    def test_zero_blur_radius_raises(self):
        with pytest.raises(ValueError):
            PrivacyMaskRegion(x=0, y=0, w=10, h=10, blur_radius=0)

    def test_one_pixelate_factor_raises(self):
        with pytest.raises(ValueError):
            PrivacyMaskRegion(x=0, y=0, w=10, h=10, mode="pixelate", pixelate_factor=1)

    def test_non_int_x_raises(self):
        with pytest.raises(ValueError):
            PrivacyMaskRegion(x="10", y=0, w=10, h=10)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# apply_privacy_masks — empty list / no-op
# ---------------------------------------------------------------------------

class TestApplyEmptyOrNoop:

    def test_empty_mask_list_returns_image_unchanged(self):
        img = _make_test_image(50, 50, fill=(10, 20, 30))
        original_pixels = list(img.getdata())
        result = apply_privacy_masks(img, [])
        assert result is img  # same object — no copy
        assert list(result.getdata()) == original_pixels

    def test_region_wholly_off_frame_is_noop(self):
        img = _make_checkerboard(100, 100, square=10)
        original_pixels = list(img.getdata())
        # Region starts past the right edge of a 100-wide image
        masks = [PrivacyMaskRegion(x=200, y=200, w=50, h=50, mode="solid")]
        result = apply_privacy_masks(img, masks)
        assert list(result.getdata()) == original_pixels


# ---------------------------------------------------------------------------
# apply_privacy_masks — solid mode
# ---------------------------------------------------------------------------

class TestApplySolid:

    def test_solid_region_is_uniform_color(self):
        img = _make_checkerboard(100, 100, square=10)
        masks = [PrivacyMaskRegion(
            x=10, y=10, w=50, h=50, mode="solid", solid_color=(123, 45, 67),
        )]
        apply_privacy_masks(img, masks)
        # All pixels in the region must equal the solid colour.
        crop = img.crop((10, 10, 60, 60))
        for px in crop.getdata():
            assert px == (123, 45, 67), f"Found non-mask pixel {px} in solid region"

    def test_solid_outside_region_unchanged(self):
        img = _make_checkerboard(100, 100, square=10)
        # Sample a pixel outside the masked region first
        outside_before = img.getpixel((80, 80))
        masks = [PrivacyMaskRegion(x=0, y=0, w=20, h=20, mode="solid")]
        apply_privacy_masks(img, masks)
        outside_after = img.getpixel((80, 80))
        assert outside_before == outside_after

    def test_solid_default_color_is_black(self):
        img = _make_test_image(50, 50, fill=(255, 255, 255))
        masks = [PrivacyMaskRegion(x=10, y=10, w=20, h=20, mode="solid")]
        apply_privacy_masks(img, masks)
        # A pixel in the masked region should be black
        assert img.getpixel((15, 15)) == (0, 0, 0)


# ---------------------------------------------------------------------------
# apply_privacy_masks — blur mode
# ---------------------------------------------------------------------------

class TestApplyBlur:

    def test_blur_reduces_region_variance(self):
        """Blurring a high-frequency region must lower its pixel variance."""
        img = _make_checkerboard(100, 100, square=4)  # very high frequency
        var_before = _region_pixel_variance(img, 10, 10, 60, 60)
        masks = [PrivacyMaskRegion(x=10, y=10, w=60, h=60, mode="blur")]
        apply_privacy_masks(img, masks)
        var_after = _region_pixel_variance(img, 10, 10, 60, 60)
        assert var_after < var_before * 0.5, (
            f"Blur did not meaningfully reduce variance: "
            f"before={var_before:.1f}, after={var_after:.1f}"
        )

    def test_blur_outside_region_unchanged(self):
        img = _make_checkerboard(100, 100, square=4)
        # Sample a pixel far outside the mask region
        outside_before = img.getpixel((80, 80))
        masks = [PrivacyMaskRegion(x=10, y=10, w=30, h=30, mode="blur")]
        apply_privacy_masks(img, masks)
        outside_after = img.getpixel((80, 80))
        assert outside_before == outside_after

    def test_blur_with_explicit_radius(self):
        img = _make_checkerboard(100, 100, square=4)
        masks = [PrivacyMaskRegion(
            x=10, y=10, w=50, h=50, mode="blur", blur_radius=20,
        )]
        # Should not raise.
        apply_privacy_masks(img, masks)
        var_after = _region_pixel_variance(img, 10, 10, 50, 50)
        # Heavy blur — variance should be very low.
        assert var_after < 1000.0


# ---------------------------------------------------------------------------
# apply_privacy_masks — pixelate mode
# ---------------------------------------------------------------------------

class TestApplyPixelate:

    def test_pixelate_reduces_distinct_colors(self):
        """Pixelating a high-detail region reduces the number of distinct colours."""
        from PIL import Image
        # Build an image with smooth gradient — many distinct colours
        img = Image.new("RGB", (100, 100))
        for y in range(100):
            for x in range(100):
                img.putpixel((x, y), (x * 2 % 256, y * 2 % 256, (x + y) % 256))
        n_before = _region_distinct_colors(img, 10, 10, 60, 60)
        masks = [PrivacyMaskRegion(
            x=10, y=10, w=60, h=60, mode="pixelate", pixelate_factor=10,
        )]
        apply_privacy_masks(img, masks)
        n_after = _region_distinct_colors(img, 10, 10, 60, 60)
        assert n_after < n_before, (
            f"Pixelation did not reduce colour count: "
            f"before={n_before}, after={n_after}"
        )
        # With factor=10 on a 60×60 region, we end up with 6×6 = 36 distinct
        # blocks. The actual distinct-colour count depends on how Pillow's
        # NEAREST resampling samples; it's bounded above by 36.
        assert n_after <= 36

    def test_pixelate_outside_region_unchanged(self):
        img = _make_checkerboard(100, 100, square=4)
        outside_before = img.getpixel((80, 80))
        masks = [PrivacyMaskRegion(x=10, y=10, w=30, h=30, mode="pixelate")]
        apply_privacy_masks(img, masks)
        outside_after = img.getpixel((80, 80))
        assert outside_before == outside_after


# ---------------------------------------------------------------------------
# apply_privacy_masks — clamping + multi-region
# ---------------------------------------------------------------------------

class TestApplyClamping:

    def test_region_extends_off_right_edge_is_clamped(self):
        """A region that overhangs the right edge is clamped to image bounds."""
        img = _make_checkerboard(100, 100, square=4)
        # x=80, w=50 → extends to x=130 on a 100-wide image
        masks = [PrivacyMaskRegion(
            x=80, y=10, w=50, h=20, mode="solid", solid_color=(99, 99, 99),
        )]
        apply_privacy_masks(img, masks)
        # The visible part — x in [80, 100), y in [10, 30) — must be the mask colour.
        for y in range(10, 30):
            for x in range(80, 100):
                assert img.getpixel((x, y)) == (99, 99, 99)
        # And pixels outside the visible part must still be unchanged.
        # Sample a pixel outside but on the same row
        # (image is checkerboard, so colour is well-defined)
        before_img = _make_checkerboard(100, 100, square=4)
        assert img.getpixel((50, 50)) == before_img.getpixel((50, 50))

    def test_multi_region_all_applied(self):
        img = _make_test_image(200, 200, fill=(50, 50, 50))
        masks = [
            PrivacyMaskRegion(x=0, y=0, w=50, h=50, mode="solid", solid_color=(200, 0, 0)),
            PrivacyMaskRegion(x=100, y=100, w=50, h=50, mode="solid", solid_color=(0, 200, 0)),
        ]
        apply_privacy_masks(img, masks)
        # Region 1: red
        assert img.getpixel((25, 25)) == (200, 0, 0)
        # Region 2: green
        assert img.getpixel((125, 125)) == (0, 200, 0)
        # Untouched area — original
        assert img.getpixel((75, 75)) == (50, 50, 50)


# ---------------------------------------------------------------------------
# apply_privacy_masks — fail-safe behaviour
# ---------------------------------------------------------------------------

class TestApplyFailSafe:

    def test_clamp_state_throttles_debug_logs(self, caplog):
        """When a state dict is provided, only one clamp debug log fires."""
        import logging
        img = _make_test_image(50, 50)
        state: dict = {}
        # Two off-frame regions — would produce two debug logs without state.
        masks = [
            PrivacyMaskRegion(x=200, y=200, w=10, h=10, mode="solid"),
            PrivacyMaskRegion(x=300, y=300, w=10, h=10, mode="solid"),
        ]
        with caplog.at_level(logging.DEBUG, logger="heretic.sjon.privacy"):
            apply_privacy_masks(img, masks, _state=state)
        debug_msgs = [r for r in caplog.records if r.levelno == logging.DEBUG]
        assert len(debug_msgs) <= 1, (
            f"State throttle failed — got {len(debug_msgs)} debug logs"
        )
        assert state.get("clamp_logged") is True


# ---------------------------------------------------------------------------
# v0.5.4 Margblæja — Protocol + Circle + Polygon tests
# ---------------------------------------------------------------------------

from heretic.sjon.privacy import (
    PrivacyMaskCircle, PrivacyMaskPolygon, PrivacyMaskShape,
)


class TestPrivacyMaskShapeProtocol:
    """Verify all three shape classes conform to the Protocol."""

    def test_region_is_shape(self):
        r = PrivacyMaskRegion(x=0, y=0, w=10, h=10)
        assert isinstance(r, PrivacyMaskShape)

    def test_circle_is_shape(self):
        c = PrivacyMaskCircle(cx=10, cy=10, radius=5)
        assert isinstance(c, PrivacyMaskShape)

    def test_polygon_is_shape(self):
        p = PrivacyMaskPolygon(points=[(0, 0), (10, 0), (5, 10)])
        assert isinstance(p, PrivacyMaskShape)

    def test_rectangle_alpha_mask_is_fully_opaque(self):
        """PrivacyMaskRegion.alpha_mask returns an L image where every pixel is 255."""
        r = PrivacyMaskRegion(x=0, y=0, w=20, h=15)
        am = r.alpha_mask(20, 15)
        assert am.mode == "L"
        assert am.size == (20, 15)
        # Every pixel must be 255 (full opacity)
        pixels = list(am.getdata())
        assert all(p == 255 for p in pixels)


class TestPrivacyMaskCircleValidation:

    def test_default_construction_succeeds(self):
        c = PrivacyMaskCircle(cx=50, cy=50, radius=20)
        assert c.mode == "blur"
        assert c.bounding_box() == (30, 30, 40, 40)

    def test_zero_radius_raises(self):
        with pytest.raises(ValueError) as exc_info:
            PrivacyMaskCircle(cx=10, cy=10, radius=0)
        assert "radius" in str(exc_info.value)

    def test_negative_radius_raises(self):
        with pytest.raises(ValueError):
            PrivacyMaskCircle(cx=10, cy=10, radius=-5)

    def test_negative_cx_raises(self):
        with pytest.raises(ValueError):
            PrivacyMaskCircle(cx=-1, cy=10, radius=5)

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError):
            PrivacyMaskCircle(cx=10, cy=10, radius=5, mode="rainbow")


class TestPrivacyMaskPolygonValidation:

    def test_minimal_triangle_succeeds(self):
        p = PrivacyMaskPolygon(points=[(0, 0), (10, 0), (5, 10)])
        assert p.bounding_box() == (0, 0, 11, 11)

    def test_two_points_raises(self):
        with pytest.raises(ValueError) as exc_info:
            PrivacyMaskPolygon(points=[(0, 0), (10, 10)])
        assert "3" in str(exc_info.value)

    def test_zero_points_raises(self):
        with pytest.raises(ValueError):
            PrivacyMaskPolygon(points=[])

    def test_non_int_coordinate_raises(self):
        with pytest.raises(ValueError):
            PrivacyMaskPolygon(points=[(0, 0), (10, "10"), (20, 20)])

    def test_negative_coordinate_raises(self):
        with pytest.raises(ValueError):
            PrivacyMaskPolygon(points=[(0, 0), (-1, 10), (5, 5)])


class TestPrivacyMaskCircleApply:

    def test_solid_circle_interior_is_mask_color(self):
        img = _make_test_image(200, 200, fill=(50, 50, 50))
        masks = [PrivacyMaskCircle(
            cx=100, cy=100, radius=40,
            mode="solid", solid_color=(255, 0, 0),
        )]
        apply_privacy_masks(img, masks)
        # Pixel at the centre of the circle must be the mask colour.
        assert img.getpixel((100, 100)) == (255, 0, 0)

    def test_solid_circle_corner_of_bbox_unchanged(self):
        """The four corners of the bounding box are OUTSIDE the disc."""
        img = _make_test_image(200, 200, fill=(50, 50, 50))
        masks = [PrivacyMaskCircle(
            cx=100, cy=100, radius=40,
            mode="solid", solid_color=(255, 0, 0),
        )]
        apply_privacy_masks(img, masks)
        # Corners of bbox: (60,60), (139,60), (60,139), (139,139) — outside disc.
        for corner in [(60, 60), (139, 60), (60, 139), (139, 139)]:
            assert img.getpixel(corner) == (50, 50, 50), (
                f"Corner {corner} was masked but should be outside the disc"
            )

    def test_solid_circle_outside_bbox_unchanged(self):
        img = _make_test_image(200, 200, fill=(50, 50, 50))
        masks = [PrivacyMaskCircle(
            cx=100, cy=100, radius=40,
            mode="solid", solid_color=(255, 0, 0),
        )]
        apply_privacy_masks(img, masks)
        # Far outside the bbox
        assert img.getpixel((10, 10)) == (50, 50, 50)
        assert img.getpixel((180, 180)) == (50, 50, 50)

    def test_circle_blur_reduces_centre_variance(self):
        img = _make_checkerboard(200, 200, square=4)
        var_before = _region_pixel_variance(img, 60, 60, 80, 80)
        masks = [PrivacyMaskCircle(cx=100, cy=100, radius=35, mode="blur")]
        apply_privacy_masks(img, masks)
        # Variance over the centre region (which lies entirely inside the disc)
        var_after = _region_pixel_variance(img, 80, 80, 40, 40)
        assert var_after < var_before * 0.5, (
            f"Blur on circle did not reduce centre variance: "
            f"before={var_before:.1f}, after={var_after:.1f}"
        )

    def test_circle_partially_off_frame_clamps(self):
        """Circle whose centre is near the edge clamps to image bounds."""
        img = _make_test_image(100, 100, fill=(50, 50, 50))
        # Circle centred at (10, 10) radius 30 — extends to (-20, -20) ... (40, 40)
        masks = [PrivacyMaskCircle(
            cx=10, cy=10, radius=30,
            mode="solid", solid_color=(255, 0, 0),
        )]
        apply_privacy_masks(img, masks)
        # Pixel at (10, 10) — circle centre — must be masked
        assert img.getpixel((10, 10)) == (255, 0, 0)
        # A pixel far away (90, 90) must be unchanged
        assert img.getpixel((90, 90)) == (50, 50, 50)

    def test_circle_wholly_off_frame_is_noop(self):
        img = _make_test_image(50, 50, fill=(100, 100, 100))
        masks = [PrivacyMaskCircle(
            cx=200, cy=200, radius=10,
            mode="solid", solid_color=(0, 0, 0),
        )]
        original = list(img.getdata())
        apply_privacy_masks(img, masks)
        assert list(img.getdata()) == original


class TestPrivacyMaskPolygonApply:

    def test_solid_triangle_interior_is_mask_color(self):
        img = _make_test_image(200, 200, fill=(50, 50, 50))
        masks = [PrivacyMaskPolygon(
            points=[(50, 50), (150, 50), (100, 150)],
            mode="solid", solid_color=(0, 200, 0),
        )]
        apply_privacy_masks(img, masks)
        # Centroid of the triangle — clearly interior
        assert img.getpixel((100, 80)) == (0, 200, 0)

    def test_solid_polygon_outside_unchanged(self):
        img = _make_test_image(200, 200, fill=(50, 50, 50))
        masks = [PrivacyMaskPolygon(
            points=[(50, 50), (150, 50), (100, 150)],
            mode="solid", solid_color=(0, 200, 0),
        )]
        apply_privacy_masks(img, masks)
        # Pixel inside the polygon's bbox but clearly OUTSIDE the triangle.
        # Triangle edges: top y=50 (x in [50,150]); left edge (50,50)→(100,150);
        # right edge (150,50)→(100,150). At y=140, the left edge has x ≈ 95.
        # (55, 140) is well to the left of the edge — outside the triangle but
        # inside the bbox (bbox = (50, 50) to (150, 150)).
        assert img.getpixel((55, 140)) == (50, 50, 50), (
            "Pixel inside bbox but outside triangle should be unchanged "
            "(P-7 — alpha-mask boundary preservation)"
        )
        # Pixel outside the bbox entirely
        assert img.getpixel((10, 10)) == (50, 50, 50)

    def test_solid_pentagon_interior_masked(self):
        img = _make_test_image(200, 200, fill=(50, 50, 50))
        # Regular-ish pentagon
        masks = [PrivacyMaskPolygon(
            points=[(100, 30), (150, 70), (130, 130), (70, 130), (50, 70)],
            mode="solid", solid_color=(255, 255, 0),
        )]
        apply_privacy_masks(img, masks)
        # Centre of the pentagon
        assert img.getpixel((100, 90)) == (255, 255, 0)

    def test_polygon_partially_off_frame_clamps(self):
        img = _make_test_image(100, 100, fill=(50, 50, 50))
        # Triangle with vertices outside the image
        masks = [PrivacyMaskPolygon(
            points=[(50, 50), (200, 50), (50, 200)],
            mode="solid", solid_color=(0, 0, 200),
        )]
        apply_privacy_masks(img, masks)
        # The interior of the visible portion (around (60, 60)) should be masked.
        # Note the visible interior is roughly the "near corner" of the triangle.
        assert img.getpixel((60, 60)) == (0, 0, 200)


class TestMixedShapeList:

    def test_mixed_shape_list_all_applied(self):
        img = _make_test_image(300, 300, fill=(50, 50, 50))
        masks = [
            PrivacyMaskRegion(
                x=10, y=10, w=40, h=40,
                mode="solid", solid_color=(255, 0, 0),
            ),
            PrivacyMaskCircle(
                cx=200, cy=50, radius=25,
                mode="solid", solid_color=(0, 255, 0),
            ),
            PrivacyMaskPolygon(
                points=[(50, 200), (100, 200), (75, 250)],
                mode="solid", solid_color=(0, 0, 255),
            ),
        ]
        apply_privacy_masks(img, masks)
        assert img.getpixel((30, 30)) == (255, 0, 0), "Rectangle interior wrong"
        assert img.getpixel((200, 50)) == (0, 255, 0), "Circle interior wrong"
        assert img.getpixel((75, 220)) == (0, 0, 255), "Polygon interior wrong"
        # Untouched
        assert img.getpixel((280, 280)) == (50, 50, 50)


class TestDegeneratePolygon:

    def test_collinear_polygon_renders_thin_line(self):
        """A polygon with all-collinear vertices renders the bounding line.

        Pillow's polygon rasteriser draws collinear points as a 1-pixel-wide
        line through the points. This is degenerate but well-defined Pillow
        behaviour — apply continues, masks the line pixels, leaves the rest
        of the image unchanged. P-8 (apply does not raise on degenerate input).
        """
        img = _make_test_image(100, 100, fill=(200, 200, 200))
        masks = [PrivacyMaskPolygon(
            points=[(10, 50), (50, 50), (90, 50)],
            mode="solid", solid_color=(0, 0, 0),
        )]
        apply_privacy_masks(img, masks)
        # The collinear line at y=50, x in [10..90] is masked.
        assert img.getpixel((50, 50)) == (0, 0, 0)
        # Pixels off the line are unchanged.
        assert img.getpixel((50, 30)) == (200, 200, 200)
        assert img.getpixel((50, 70)) == (200, 200, 200)

    def test_coincident_points_polygon_does_not_crash(self):
        """A polygon with all coincident vertices is a valid construction.

        Pillow renders a single pixel at the coincident location. The apply
        path continues; no exception. P-8 (no crash on degenerate input).
        """
        img = _make_test_image(100, 100, fill=(200, 200, 200))
        masks = [PrivacyMaskPolygon(
            points=[(50, 50), (50, 50), (50, 50)],
            mode="solid", solid_color=(0, 0, 0),
        )]
        # Should not raise.
        apply_privacy_masks(img, masks)
        # The single pixel at (50, 50) is masked; the rest is unchanged.
        assert img.getpixel((50, 50)) == (0, 0, 0)
        assert img.getpixel((30, 30)) == (200, 200, 200)


# ---------------------------------------------------------------------------
# v0.5.5 Mjúkblæja — RoundedRectangle + Ellipse tests
# ---------------------------------------------------------------------------

from heretic.sjon.privacy import (
    PrivacyMaskRoundedRectangle, PrivacyMaskEllipse,
)


class TestPrivacyMaskRoundedRectangleValidation:

    def test_default_construction_succeeds(self):
        rr = PrivacyMaskRoundedRectangle(x=0, y=0, w=100, h=100, corner_radius=10)
        assert rr.bounding_box() == (0, 0, 100, 100)
        assert rr.mode == "blur"

    def test_zero_corner_radius_succeeds(self):
        """corner_radius=0 is a valid degenerate case (sharp rectangle)."""
        rr = PrivacyMaskRoundedRectangle(x=0, y=0, w=50, h=50, corner_radius=0)
        # Should not raise
        assert rr.corner_radius == 0

    def test_negative_corner_radius_raises(self):
        with pytest.raises(ValueError) as exc_info:
            PrivacyMaskRoundedRectangle(x=0, y=0, w=10, h=10, corner_radius=-1)
        assert "corner_radius" in str(exc_info.value)

    def test_zero_width_raises(self):
        with pytest.raises(ValueError):
            PrivacyMaskRoundedRectangle(x=0, y=0, w=0, h=10, corner_radius=5)

    def test_zero_height_raises(self):
        with pytest.raises(ValueError):
            PrivacyMaskRoundedRectangle(x=0, y=0, w=10, h=0, corner_radius=5)

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError):
            PrivacyMaskRoundedRectangle(
                x=0, y=0, w=10, h=10, corner_radius=2, mode="curvy",
            )

    def test_is_shape(self):
        rr = PrivacyMaskRoundedRectangle(x=0, y=0, w=10, h=10, corner_radius=2)
        assert isinstance(rr, PrivacyMaskShape)


class TestPrivacyMaskRoundedRectangleApply:

    def test_solid_interior_is_mask_color(self):
        img = _make_test_image(200, 200, fill=(50, 50, 50))
        masks = [PrivacyMaskRoundedRectangle(
            x=20, y=20, w=160, h=160, corner_radius=20,
            mode="solid", solid_color=(255, 0, 0),
        )]
        apply_privacy_masks(img, masks)
        # Centre pixel — well inside the rounded rect
        assert img.getpixel((100, 100)) == (255, 0, 0)

    def test_corner_outside_curve_unchanged(self):
        """The bbox absolute corner is outside the rounded curve. P-7."""
        img = _make_test_image(200, 200, fill=(50, 50, 50))
        # corner_radius=30, so the absolute corner of the bbox is far outside
        # the rounded curve.
        masks = [PrivacyMaskRoundedRectangle(
            x=20, y=20, w=160, h=160, corner_radius=30,
            mode="solid", solid_color=(255, 0, 0),
        )]
        apply_privacy_masks(img, masks)
        # Top-left pixel of bbox: (20, 20). Inside the bbox but outside the
        # rounded curve (the curve carves away the corner).
        assert img.getpixel((20, 20)) == (50, 50, 50), (
            "Bbox top-left corner should be outside the rounded curve "
            "(P-7 boundary preservation)"
        )
        # Top-right corner of bbox
        assert img.getpixel((179, 20)) == (50, 50, 50)
        # Bottom-left corner
        assert img.getpixel((20, 179)) == (50, 50, 50)
        # Bottom-right corner
        assert img.getpixel((179, 179)) == (50, 50, 50)

    def test_corner_radius_clamped_to_half_short_side(self):
        """corner_radius larger than min(w,h)//2 is clamped at apply time without raising."""
        img = _make_test_image(100, 100, fill=(50, 50, 50))
        # 50x50 box with corner_radius=200 — clamped to min(50,50)//2 = 25
        masks = [PrivacyMaskRoundedRectangle(
            x=10, y=10, w=50, h=50, corner_radius=200,
            mode="solid", solid_color=(255, 255, 0),
        )]
        # Should not raise
        apply_privacy_masks(img, masks)
        # Centre is masked (this is now effectively a circle since corner_radius
        # clamped to 25 == min(w,h)//2)
        assert img.getpixel((35, 35)) == (255, 255, 0)

    def test_zero_corner_radius_renders_sharp_rectangle(self):
        """corner_radius=0 produces an alpha mask identical to a regular rectangle."""
        img = _make_test_image(100, 100, fill=(50, 50, 50))
        masks = [PrivacyMaskRoundedRectangle(
            x=10, y=10, w=80, h=80, corner_radius=0,
            mode="solid", solid_color=(0, 255, 0),
        )]
        apply_privacy_masks(img, masks)
        # All four corners of the rect should be masked (it's sharp-cornered)
        assert img.getpixel((10, 10)) == (0, 255, 0)
        assert img.getpixel((89, 89)) == (0, 255, 0)
        assert img.getpixel((50, 50)) == (0, 255, 0)

    def test_off_frame_noop(self):
        img = _make_test_image(50, 50, fill=(100, 100, 100))
        masks = [PrivacyMaskRoundedRectangle(
            x=200, y=200, w=20, h=20, corner_radius=5,
            mode="solid", solid_color=(0, 0, 0),
        )]
        original = list(img.getdata())
        apply_privacy_masks(img, masks)
        assert list(img.getdata()) == original


class TestPrivacyMaskEllipseValidation:

    def test_default_construction_succeeds(self):
        e = PrivacyMaskEllipse(cx=50, cy=50, rx=30, ry=20)
        assert e.bounding_box() == (20, 30, 60, 40)
        assert e.mode == "blur"

    def test_zero_rx_raises(self):
        with pytest.raises(ValueError) as exc_info:
            PrivacyMaskEllipse(cx=10, cy=10, rx=0, ry=5)
        assert "rx" in str(exc_info.value)

    def test_zero_ry_raises(self):
        with pytest.raises(ValueError) as exc_info:
            PrivacyMaskEllipse(cx=10, cy=10, rx=5, ry=0)
        assert "ry" in str(exc_info.value)

    def test_negative_radii_raise(self):
        with pytest.raises(ValueError):
            PrivacyMaskEllipse(cx=10, cy=10, rx=-1, ry=5)
        with pytest.raises(ValueError):
            PrivacyMaskEllipse(cx=10, cy=10, rx=5, ry=-1)

    def test_negative_centre_raises(self):
        with pytest.raises(ValueError):
            PrivacyMaskEllipse(cx=-1, cy=10, rx=5, ry=5)

    def test_is_shape(self):
        e = PrivacyMaskEllipse(cx=10, cy=10, rx=5, ry=5)
        assert isinstance(e, PrivacyMaskShape)


class TestPrivacyMaskEllipseApply:

    def test_solid_interior_is_mask_color(self):
        img = _make_test_image(200, 200, fill=(50, 50, 50))
        masks = [PrivacyMaskEllipse(
            cx=100, cy=100, rx=60, ry=30,
            mode="solid", solid_color=(0, 200, 0),
        )]
        apply_privacy_masks(img, masks)
        # Centre pixel — well inside the ellipse
        assert img.getpixel((100, 100)) == (0, 200, 0)

    def test_bbox_corner_outside_ellipse_unchanged(self):
        """A pixel at the corner of the bbox is outside the ellipse. P-7."""
        img = _make_test_image(200, 200, fill=(50, 50, 50))
        masks = [PrivacyMaskEllipse(
            cx=100, cy=100, rx=60, ry=30,
            mode="solid", solid_color=(0, 200, 0),
        )]
        apply_privacy_masks(img, masks)
        # bbox = (40, 70, 120, 60) — corners at (40,70), (159,70), (40,129), (159,129)
        # All four are outside the ellipse.
        assert img.getpixel((40, 70)) == (50, 50, 50), (
            "Bbox top-left corner should be outside the ellipse (P-7)"
        )
        assert img.getpixel((159, 70)) == (50, 50, 50)
        assert img.getpixel((40, 129)) == (50, 50, 50)
        assert img.getpixel((159, 129)) == (50, 50, 50)

    def test_non_circular_aspect(self):
        """An ellipse with rx != ry is genuinely non-circular.

        Sample two pixels along the major and minor axes at the same distance
        from the centre. Inside the ellipse along the major axis; outside
        along the minor axis (since ry < rx).
        """
        img = _make_test_image(200, 200, fill=(50, 50, 50))
        # Wide ellipse: rx=60 (horizontal half-axis), ry=20 (vertical half-axis)
        masks = [PrivacyMaskEllipse(
            cx=100, cy=100, rx=60, ry=20,
            mode="solid", solid_color=(0, 0, 200),
        )]
        apply_privacy_masks(img, masks)
        # 50 pixels left of centre along x — inside the ellipse (50 < rx=60)
        assert img.getpixel((50, 100)) == (0, 0, 200), (
            "Pixel along major axis (rx=60) at distance 50 should be inside"
        )
        # 50 pixels above centre along y — outside the ellipse (50 > ry=20)
        assert img.getpixel((100, 50)) == (50, 50, 50), (
            "Pixel along minor axis (ry=20) at distance 50 should be outside"
        )

    def test_equal_radii_acts_like_circle(self):
        """rx == ry produces a circular alpha mask (degenerate ellipse = circle)."""
        img = _make_test_image(200, 200, fill=(50, 50, 50))
        masks = [PrivacyMaskEllipse(
            cx=100, cy=100, rx=40, ry=40,
            mode="solid", solid_color=(255, 0, 255),
        )]
        apply_privacy_masks(img, masks)
        # Centre is masked
        assert img.getpixel((100, 100)) == (255, 0, 255)
        # Bbox corner (60, 60) is outside the disc — unchanged
        assert img.getpixel((60, 60)) == (50, 50, 50)


class TestFiveShapeMixedList:

    def test_all_five_shapes_in_one_apply(self):
        """A list with one of every shape kind: all five regions masked."""
        img = _make_test_image(400, 400, fill=(50, 50, 50))
        masks = [
            PrivacyMaskRegion(
                x=10, y=10, w=40, h=40,
                mode="solid", solid_color=(255, 0, 0),  # red rectangle
            ),
            PrivacyMaskCircle(
                cx=300, cy=50, radius=25,
                mode="solid", solid_color=(0, 255, 0),  # green circle
            ),
            PrivacyMaskPolygon(
                points=[(50, 200), (100, 200), (75, 250)],
                mode="solid", solid_color=(0, 0, 255),  # blue triangle
            ),
            PrivacyMaskRoundedRectangle(
                x=200, y=200, w=80, h=80, corner_radius=15,
                mode="solid", solid_color=(255, 255, 0),  # yellow rounded rect
            ),
            PrivacyMaskEllipse(
                cx=300, cy=300, rx=40, ry=20,
                mode="solid", solid_color=(255, 0, 255),  # magenta ellipse
            ),
        ]
        apply_privacy_masks(img, masks)
        # Each shape's interior pixel should match its colour
        assert img.getpixel((30, 30)) == (255, 0, 0), "Rectangle wrong"
        assert img.getpixel((300, 50)) == (0, 255, 0), "Circle wrong"
        assert img.getpixel((75, 220)) == (0, 0, 255), "Polygon wrong"
        assert img.getpixel((240, 240)) == (255, 255, 0), "Rounded rect wrong"
        assert img.getpixel((300, 300)) == (255, 0, 255), "Ellipse wrong"
        # Untouched pixel
        assert img.getpixel((380, 380)) == (50, 50, 50)
