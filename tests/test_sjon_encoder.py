"""
Placeholder tests for heretic.sjon.encoder.

These tests are skip-marked during the v0.5 scaffold phase. Forge implements
the full test suite in Wave 2 after the stubs in encoder.py are filled.

Coverage targets (Forge):
    - FrameEncoder.encode() returns bytes (PNG magic bytes: b'\\x89PNG')
    - FrameEncoder.encode() raises FrameEncodingError when Pillow is not installed
    - FrameEncoder.encode() converts BGRA pixel data to correct RGB PNG
    - FrameEncoder.resize_if_needed() does not resize when frame fits within limits
    - FrameEncoder.resize_if_needed() downscales proportionally when frame is too wide
    - FrameEncoder.resize_if_needed() downscales proportionally when frame is too tall
    - FrameEncoder.resize_if_needed() downscales by the minimum ratio (not width, not height)
    - FrameEncoder.to_data_url() produces a string starting with 'data:image/png;base64,'
    - FrameEncoder.to_data_url() round-trips correctly (decode base64 -> original PNG bytes)
    - FrameEncoder.encode_to_data_url() is equivalent to encode() then to_data_url()
    - FrameEncoder raises FrameEncodingError (not a PIL or other raw exception) on failure
"""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
def test_encoder_to_data_url_format() -> None:
    """to_data_url() output starts with the correct data URL prefix."""
    from heretic.sjon.encoder import FrameEncoder
    encoder = FrameEncoder(max_width=1280, max_height=720)
    # Minimal 1x1 white PNG (valid PNG bytes for testing round-trip)
    import base64
    import io
    try:
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (1, 1), color=(255, 255, 255)).save(buf, format="PNG")
        png_bytes = buf.getvalue()
    except ImportError:
        pytest.skip("Pillow not installed — cannot generate test PNG")
    data_url = encoder.to_data_url(png_bytes)
    assert data_url.startswith("data:image/png;base64,")


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
def test_encoder_resize_not_needed_when_small() -> None:
    """resize_if_needed() returns the image unchanged when it fits within limits."""
    from heretic.sjon.encoder import FrameEncoder
    encoder = FrameEncoder(max_width=1280, max_height=720)
    try:
        from PIL import Image
        img = Image.new("RGB", (640, 360))
    except ImportError:
        pytest.skip("Pillow not installed")
    result = encoder.resize_if_needed(img)
    assert result.size == (640, 360)


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
def test_encoder_resize_proportional_when_wide() -> None:
    """resize_if_needed() downscales proportionally when frame is wider than max_width."""
    from heretic.sjon.encoder import FrameEncoder
    encoder = FrameEncoder(max_width=1280, max_height=720)
    try:
        from PIL import Image
        # 2560x720 — double width, same height — should scale to 1280x360
        img = Image.new("RGB", (2560, 720))
    except ImportError:
        pytest.skip("Pillow not installed")
    result = encoder.resize_if_needed(img)
    assert result.size == (1280, 360)


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
def test_encoder_encode_raises_frame_encoding_error_when_pillow_absent(
    monkeypatch: pytest.MonkeyPatch,
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
