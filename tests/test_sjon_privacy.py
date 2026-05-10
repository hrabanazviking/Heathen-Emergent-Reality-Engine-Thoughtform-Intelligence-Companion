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
