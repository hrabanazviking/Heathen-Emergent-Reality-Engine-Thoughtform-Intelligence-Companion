"""
Tests for heretic.sjon.encoder — FrameEncoder.

All Pillow calls use real Pillow if installed, with a fallback mock path
so tests can also run in envs without Pillow (they will skip gracefully).
"""

from __future__ import annotations

import base64
import io
import logging
from unittest.mock import MagicMock, patch

import pytest


def _pillow_available() -> bool:
    try:
        from PIL import Image  # noqa: F401
        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# to_data_url — pure stdlib, always works
# ---------------------------------------------------------------------------

class TestToDataUrl:
    def test_produces_correct_prefix(self) -> None:
        from heretic.sjon.encoder import FrameEncoder
        encoder = FrameEncoder()
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        data_url = encoder.to_data_url(fake_png)
        assert data_url.startswith("data:image/png;base64,")

    def test_base64_encodes_payload(self) -> None:
        from heretic.sjon.encoder import FrameEncoder
        encoder = FrameEncoder()
        fake_png = b"hello png"
        data_url = encoder.to_data_url(fake_png)
        prefix = "data:image/png;base64,"
        encoded_part = data_url[len(prefix):]
        decoded = base64.standard_b64decode(encoded_part)
        assert decoded == fake_png

    def test_empty_bytes_produces_valid_data_url(self) -> None:
        from heretic.sjon.encoder import FrameEncoder
        encoder = FrameEncoder()
        data_url = encoder.to_data_url(b"")
        assert data_url == "data:image/png;base64,"

    def test_output_is_ascii(self) -> None:
        from heretic.sjon.encoder import FrameEncoder
        encoder = FrameEncoder()
        fake_png = bytes(range(256))  # all byte values
        data_url = encoder.to_data_url(fake_png)
        # Must be pure ASCII — safe to embed in JSON
        data_url.encode("ascii")  # raises if non-ASCII


# ---------------------------------------------------------------------------
# resize_if_needed — requires Pillow
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _pillow_available(), reason="Pillow not installed")
class TestResizeIfNeeded:
    def test_no_resize_when_within_bounds(self) -> None:
        from PIL import Image
        from heretic.sjon.encoder import FrameEncoder

        encoder = FrameEncoder(max_width=1280, max_height=720)
        img = Image.new("RGB", (640, 360))
        result = encoder.resize_if_needed(img)
        # Small image — returned unchanged (same size)
        assert result.size == (640, 360)

    def test_no_resize_at_exact_boundary(self) -> None:
        from PIL import Image
        from heretic.sjon.encoder import FrameEncoder

        encoder = FrameEncoder(max_width=1280, max_height=720)
        img = Image.new("RGB", (1280, 720))
        result = encoder.resize_if_needed(img)
        assert result.size == (1280, 720)

    def test_downscales_oversized_width(self) -> None:
        from PIL import Image
        from heretic.sjon.encoder import FrameEncoder

        encoder = FrameEncoder(max_width=640, max_height=480)
        img = Image.new("RGB", (1920, 1080))
        result = encoder.resize_if_needed(img)
        w, h = result.size
        assert w <= 640
        assert h <= 480

    def test_downscales_oversized_height(self) -> None:
        from PIL import Image
        from heretic.sjon.encoder import FrameEncoder

        encoder = FrameEncoder(max_width=3000, max_height=360)
        img = Image.new("RGB", (1920, 1080))
        result = encoder.resize_if_needed(img)
        _w, h = result.size
        assert h <= 360

    def test_aspect_ratio_preserved(self) -> None:
        from PIL import Image
        from heretic.sjon.encoder import FrameEncoder

        encoder = FrameEncoder(max_width=480, max_height=270)
        img = Image.new("RGB", (1920, 1080))  # 16:9
        result = encoder.resize_if_needed(img)
        w, h = result.size
        # Aspect ratio should be 16:9 (within 1 pixel rounding)
        assert abs(w / h - 16 / 9) < 0.02

    def test_resize_proportional_when_wide(self) -> None:
        """resize_if_needed() downscales proportionally when frame is wider than max_width."""
        from PIL import Image
        from heretic.sjon.encoder import FrameEncoder

        encoder = FrameEncoder(max_width=1280, max_height=720)
        # 2560x720 — double width, same height — should scale to 1280x360
        img = Image.new("RGB", (2560, 720))
        result = encoder.resize_if_needed(img)
        assert result.size == (1280, 360)


# ---------------------------------------------------------------------------
# encode() — requires Pillow; tests BGRX channel path
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _pillow_available(), reason="Pillow not installed")
class TestFrameEncoderEncode:
    def _make_bgra_bytes(self, width: int, height: int) -> bytes:
        """Create a synthetic BGRA byte sequence for testing."""
        # Simple gradient: B=x%256, G=y%256, R=0, A=255
        result = bytearray()
        for y in range(height):
            for x in range(width):
                result.extend([x % 256, y % 256, 0, 255])
        return bytes(result)

    def test_encode_returns_png_bytes(self) -> None:
        from heretic.sjon.encoder import FrameEncoder
        encoder = FrameEncoder(max_width=64, max_height=64)
        w, h = 32, 32
        bgra = self._make_bgra_bytes(w, h)
        png = encoder.encode(bgra, w, h, "BGRA")
        # PNG magic bytes
        assert png[:8] == b"\x89PNG\r\n\x1a\n"

    def test_encode_bgra_to_rgb_produces_valid_image(self) -> None:
        from PIL import Image
        from heretic.sjon.encoder import FrameEncoder
        encoder = FrameEncoder(max_width=64, max_height=64)
        w, h = 16, 16
        bgra = self._make_bgra_bytes(w, h)
        png = encoder.encode(bgra, w, h, "BGRA")
        # Verify round-trip via Pillow: PNG decodes to an image of correct size
        img = Image.open(io.BytesIO(png))
        assert img.size == (w, h)
        assert img.mode == "RGB"

    def test_encode_downscales_when_oversized(self) -> None:
        from PIL import Image
        from heretic.sjon.encoder import FrameEncoder
        encoder = FrameEncoder(max_width=8, max_height=8)
        w, h = 32, 32
        bgra = self._make_bgra_bytes(w, h)
        png = encoder.encode(bgra, w, h, "BGRA")
        img = Image.open(io.BytesIO(png))
        assert img.size[0] <= 8
        assert img.size[1] <= 8

    def test_encode_raises_frame_encoding_error_on_bad_input(self) -> None:
        from heretic.sjon.errors import FrameEncodingError
        from heretic.sjon.encoder import FrameEncoder
        encoder = FrameEncoder(max_width=64, max_height=64)
        # Wrong dimensions — too few bytes for a 100x100 BGRA image
        with pytest.raises(FrameEncodingError):
            encoder.encode(b"\x00\x01\x02\x03", 100, 100, "BGRA")

    def test_encode_to_data_url_convenience_method(self) -> None:
        from heretic.sjon.encoder import FrameEncoder
        encoder = FrameEncoder(max_width=64, max_height=64)
        w, h = 8, 8
        bgra = bytes(w * h * 4)
        data_url = encoder.encode_to_data_url(bgra, w, h, "BGRA")
        assert data_url.startswith("data:image/png;base64,")

    def test_encode_to_data_url_equivalent_to_encode_then_to_data_url(self) -> None:
        from heretic.sjon.encoder import FrameEncoder
        encoder = FrameEncoder(max_width=64, max_height=64)
        w, h = 8, 8
        bgra = bytes(w * h * 4)
        via_convenience = encoder.encode_to_data_url(bgra, w, h, "BGRA")
        via_two_steps = encoder.to_data_url(encoder.encode(bgra, w, h, "BGRA"))
        assert via_convenience == via_two_steps


# ---------------------------------------------------------------------------
# encode() with Pillow mocked — for envs without Pillow
# ---------------------------------------------------------------------------

class TestFrameEncoderImportError:
    def test_encode_raises_frame_encoding_error_when_pillow_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """encode() raises FrameEncodingError (not ImportError) when Pillow is not installed."""
        import builtins
        real_import = builtins.__import__

        def mock_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "PIL" or name.startswith("PIL."):
                raise ImportError("Pillow not installed")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        from heretic.sjon.encoder import FrameEncoder
        from heretic.sjon.errors import FrameEncodingError
        encoder = FrameEncoder()
        with pytest.raises(FrameEncodingError):
            encoder.encode(b"\x00" * 4, width=1, height=1, pixel_format="BGRA")

    def test_to_data_url_works_without_pillow(self) -> None:
        """to_data_url() only uses stdlib base64 — works regardless of Pillow."""
        from heretic.sjon.encoder import FrameEncoder
        encoder = FrameEncoder()
        result = encoder.to_data_url(b"\x89PNG")
        assert result.startswith("data:image/png;base64,")


# ---------------------------------------------------------------------------
# encode() override parameters — verify override dims are honoured
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _pillow_available(), reason="Pillow not installed")
class TestFrameEncoderEncodeOverride:
    """Verify the max_width_override / max_height_override keyword arguments.

    These are used by the Sjón oversize-retry path (S-1 fix) to force a lower
    resolution cap without constructing a second encoder instance.
    """

    def _make_bgra_bytes(self, width: int, height: int) -> bytes:
        """Synthetic BGRA frame: B=x%256, G=y%256, R=0, A=255."""
        result = bytearray()
        for y in range(height):
            for x in range(width):
                result.extend([x % 256, y % 256, 0, 255])
        return bytes(result)

    def test_encode_uses_configured_max_when_no_override(self) -> None:
        """Without override kwargs, encode() respects self._max_width/_max_height."""
        from PIL import Image
        from heretic.sjon.encoder import FrameEncoder

        # Encoder capped at 16x16; source is 32x32 — must be downscaled.
        encoder = FrameEncoder(max_width=16, max_height=16)
        bgra = self._make_bgra_bytes(32, 32)
        png = encoder.encode(bgra, 32, 32, "BGRA")
        img = Image.open(io.BytesIO(png))
        # Output must be within the configured cap.
        assert img.size[0] <= 16
        assert img.size[1] <= 16

    def test_encode_uses_override_when_provided(self) -> None:
        """When override kwargs are supplied, encode() respects them over self._max_*.

        Encoder is configured with max 64x64, but override forces 8x8.
        Source is 32x32, which fits within 64x64 but NOT within 8x8.
        Override must win — output must be within 8x8.
        """
        from PIL import Image
        from heretic.sjon.encoder import FrameEncoder

        encoder = FrameEncoder(max_width=64, max_height=64)
        bgra = self._make_bgra_bytes(32, 32)
        png = encoder.encode(
            bgra,
            32,
            32,
            "BGRA",
            max_width_override=8,
            max_height_override=8,
        )
        img = Image.open(io.BytesIO(png))
        # Override dims must win over the encoder's configured 64x64.
        assert img.size[0] <= 8
        assert img.size[1] <= 8

    def test_encode_override_independent_of_configured_max(self) -> None:
        """Override dims are fully independent from the encoder's configured max.

        Two encoders with different configured maxes, both called with the same
        override — should produce identically-sized output (the override wins for
        both). This confirms the override is not combined with self._max_* in any
        way (no min(), no max(), just a straight replacement).
        """
        from PIL import Image
        from heretic.sjon.encoder import FrameEncoder

        bgra = self._make_bgra_bytes(64, 64)

        encoder_a = FrameEncoder(max_width=256, max_height=256)
        encoder_b = FrameEncoder(max_width=16, max_height=16)

        png_a = encoder_a.encode(bgra, 64, 64, "BGRA", max_width_override=32, max_height_override=32)
        png_b = encoder_b.encode(bgra, 64, 64, "BGRA", max_width_override=32, max_height_override=32)

        img_a = Image.open(io.BytesIO(png_a))
        img_b = Image.open(io.BytesIO(png_b))

        # Both must be within the override cap.
        assert img_a.size[0] <= 32 and img_a.size[1] <= 32
        assert img_b.size[0] <= 32 and img_b.size[1] <= 32
        # Both must produce the same output dimensions (override is the only cap in play).
        assert img_a.size == img_b.size
