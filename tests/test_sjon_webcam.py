"""
Tests for L3 Sjón webcam support — v0.5.2 (Forge Wave 2).

All placeholder skip-marks replaced with real implementations.
OpenCvBackend, snapshot_webcam(), and _encode_webcam_frame are fully implemented.

Test inventory:
    NullBackend:
        1. test_null_backend_available_false
        2. test_null_backend_open_is_noop
        3. test_null_backend_close_is_noop
        4. test_null_backend_capture_raises
        5. test_null_backend_capture_raises_is_webcam_capture_error
    SjonWebcamConfig defaults + validation: (tests 6–22, existing, unchanged)
    Factory:
        23. test_factory_returns_webcam_null_backend_when_cv2_absent
        24. test_factory_never_returns_none
    OpenCvBackend:
        25. test_opencvbackend_available_true_when_cv2_and_device_present
        26. test_opencvbackend_available_false_when_cv2_absent
        27. test_opencvbackend_available_false_when_device_not_opened
        28. test_opencvbackend_available_does_not_leave_cap_open
        29. test_opencvbackend_open_sets_cap
        30. test_opencvbackend_open_idempotent
        31. test_opencvbackend_open_raises_when_device_not_opened
        32. test_opencvbackend_open_raises_when_cv2_absent
        33. test_opencvbackend_close_releases_cap_idempotent
        34. test_opencvbackend_capture_returns_rgb_bytes
        35. test_opencvbackend_capture_bgr_to_rgb_conversion
        36. test_opencvbackend_capture_raises_on_read_failure
        37. test_opencvbackend_capture_raises_before_open
    Sjón.snapshot_webcam():
        38. test_snapshot_webcam_disabled_returns_empty
        39. test_snapshot_webcam_no_backend_returns_empty
        40. test_snapshot_webcam_unavailable_backend_returns_empty
        41. test_snapshot_webcam_returns_jpeg_data_url
        42. test_snapshot_webcam_returns_png_data_url
        43. test_snapshot_webcam_respects_max_dimensions
        44. test_snapshot_webcam_never_raises_on_capture_error
        45. test_snapshot_webcam_never_raises_on_encode_error

Ref: TASK_HERETIC_v0.5.2_WEBCAM.md §Wave 2.
     src/heretic/sjon/webcam.py (OpenCvBackend implementation).
     src/heretic/sjon/sjon.py (snapshot_webcam + _encode_webcam_frame).
"""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import MagicMock, patch

import pytest

from heretic.sjon.config_model import SjonWebcamConfig
from heretic.sjon.errors import WebcamBackendUnavailableError, WebcamCaptureError
from heretic.sjon.webcam import WebcamNullBackend, best_available


# ---------------------------------------------------------------------------
# NullBackend behaviour — these tests are NOT skipped; the NullBackend is fully
# scaffolded and should pass without Forge Wave 2 work.
# ---------------------------------------------------------------------------

class TestWebcamNullBackend:
    """NullBackend is fully scaffolded; these tests run without skip."""

    def test_null_backend_available_false(self) -> None:
        """WebcamNullBackend.available() must always return False."""
        backend = WebcamNullBackend()
        assert backend.available() is False

    def test_null_backend_open_is_noop(self) -> None:
        """WebcamNullBackend.open() must not raise."""
        backend = WebcamNullBackend()
        backend.open()  # Must not raise.

    def test_null_backend_close_is_noop(self) -> None:
        """WebcamNullBackend.close() must not raise, even when called twice."""
        backend = WebcamNullBackend()
        backend.close()
        backend.close()  # Idempotent.

    def test_null_backend_capture_raises(self) -> None:
        """WebcamNullBackend.capture() must raise WebcamBackendUnavailableError."""
        backend = WebcamNullBackend()
        with pytest.raises(WebcamBackendUnavailableError):
            backend.capture(device_index=0)

    def test_null_backend_capture_raises_is_webcam_capture_error(self) -> None:
        """WebcamBackendUnavailableError must be a subclass of WebcamCaptureError."""
        backend = WebcamNullBackend()
        with pytest.raises(WebcamCaptureError):
            backend.capture(device_index=0)


# ---------------------------------------------------------------------------
# SjonWebcamConfig validation — these tests run without skip; the config is
# fully implemented.
# ---------------------------------------------------------------------------

class TestSjonWebcamConfigDefaults:
    """Config field defaults and basic construction."""

    def test_default_enabled_false(self) -> None:
        """enabled must default to False — strongest consent gate."""
        cfg = SjonWebcamConfig()
        assert cfg.enabled is False

    def test_default_device_index(self) -> None:
        """device_index must default to 0."""
        cfg = SjonWebcamConfig()
        assert cfg.device_index == 0

    def test_default_max_width(self) -> None:
        cfg = SjonWebcamConfig()
        assert cfg.max_width == 1280

    def test_default_max_height(self) -> None:
        cfg = SjonWebcamConfig()
        assert cfg.max_height == 720

    def test_default_format_jpeg(self) -> None:
        cfg = SjonWebcamConfig()
        assert cfg.format == "jpeg"

    def test_default_jpeg_quality(self) -> None:
        cfg = SjonWebcamConfig()
        assert cfg.jpeg_quality == 85

    def test_default_attach_policy_screen_only(self) -> None:
        """attach_policy must default to screen_only for backward compatibility."""
        cfg = SjonWebcamConfig()
        assert cfg.attach_policy == "screen_only"


class TestSjonWebcamConfigValidation:
    """Field range validation in __post_init__."""

    def test_jpeg_quality_too_low_raises(self) -> None:
        with pytest.raises(ValueError, match="jpeg_quality"):
            SjonWebcamConfig(jpeg_quality=0)

    def test_jpeg_quality_too_high_raises(self) -> None:
        with pytest.raises(ValueError, match="jpeg_quality"):
            SjonWebcamConfig(jpeg_quality=101)

    def test_jpeg_quality_boundary_low_valid(self) -> None:
        cfg = SjonWebcamConfig(jpeg_quality=1)
        assert cfg.jpeg_quality == 1

    def test_jpeg_quality_boundary_high_valid(self) -> None:
        cfg = SjonWebcamConfig(jpeg_quality=100)
        assert cfg.jpeg_quality == 100

    def test_invalid_format_raises(self) -> None:
        with pytest.raises(ValueError, match="format"):
            SjonWebcamConfig(format="gif")  # type: ignore[arg-type]

    def test_valid_format_png(self) -> None:
        cfg = SjonWebcamConfig(format="png")
        assert cfg.format == "png"

    def test_invalid_attach_policy_raises(self) -> None:
        with pytest.raises(ValueError, match="attach_policy"):
            SjonWebcamConfig(attach_policy="all_buffered")  # type: ignore[arg-type]

    def test_valid_attach_policy_alongside(self) -> None:
        cfg = SjonWebcamConfig(attach_policy="alongside")
        assert cfg.attach_policy == "alongside"

    def test_valid_attach_policy_webcam_only(self) -> None:
        cfg = SjonWebcamConfig(attach_policy="webcam_only")
        assert cfg.attach_policy == "webcam_only"

    def test_valid_attach_policy_alternate(self) -> None:
        cfg = SjonWebcamConfig(attach_policy="alternate")
        assert cfg.attach_policy == "alternate"

    def test_max_width_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="max_width"):
            SjonWebcamConfig(max_width=0)

    def test_max_height_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="max_height"):
            SjonWebcamConfig(max_height=0)

    def test_device_index_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="device_index"):
            SjonWebcamConfig(device_index=-1)

    def test_enabled_true_logs_privacy_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """enabled=True must emit a WARNING to keep physical-presence capture visible."""
        with caplog.at_level(logging.WARNING, logger="heretic.sjon.config_model"):
            SjonWebcamConfig(enabled=True)
        assert any("physical presence" in r.message.lower() or "privacy" in r.message.lower()
                   for r in caplog.records), (
            "Expected a privacy warning when enabled=True. "
            "SjonWebcamConfig.__post_init__ must call _LOG.warning() when enabled is True."
        )


# ---------------------------------------------------------------------------
# Factory tests — partial; best_available() falls through to NullBackend
# because OpenCvBackend.available() raises NotImplementedError at this stage.
# ---------------------------------------------------------------------------

class TestBestAvailableFactory:
    """Factory behaviour — cv2 absent means NullBackend; cv2+device present means OpenCvBackend."""

    def test_factory_returns_webcam_null_backend_when_cv2_absent(self) -> None:
        """When cv2 is not importable, best_available() returns WebcamNullBackend."""
        logger = logging.getLogger("test.factory")
        cfg = SjonWebcamConfig()
        # Patch cv2 import to fail so available() returns False
        with patch.dict("sys.modules", {"cv2": None}):
            backend = best_available(logger, cfg)
        assert isinstance(backend, WebcamNullBackend)

    def test_factory_never_returns_none(self) -> None:
        """Factory must always return a backend instance, never None."""
        logger = logging.getLogger("test.factory")
        cfg = SjonWebcamConfig()
        # Ensure factory returns something even when cv2 absent
        with patch.dict("sys.modules", {"cv2": None}):
            backend = best_available(logger, cfg)
        assert backend is not None

    def test_factory_returns_opencvbackend_when_cv2_and_device_present(self) -> None:
        """When cv2 is importable and device opens, factory returns OpenCvBackend."""
        from heretic.sjon.webcam import OpenCvBackend
        logger = logging.getLogger("test.factory")
        cfg = SjonWebcamConfig()

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True

        mock_cv2 = MagicMock()
        mock_cv2.VideoCapture.return_value = mock_cap

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            backend = best_available(logger, cfg)

        assert isinstance(backend, OpenCvBackend)


# ---------------------------------------------------------------------------
# OpenCvBackend — available(), open(), capture(), close()
# ---------------------------------------------------------------------------

class TestOpenCvBackendAvailable:
    """OpenCvBackend.available() probe logic."""

    def test_available_true_when_cv2_and_device_present(self) -> None:
        """available() returns True when cv2 imports and VideoCapture opens."""
        from heretic.sjon.webcam import OpenCvBackend

        logger = logging.getLogger("test")
        cfg = SjonWebcamConfig(device_index=0)
        backend = OpenCvBackend(cfg, logger)

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cv2 = MagicMock()
        mock_cv2.VideoCapture.return_value = mock_cap

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            result = backend.available()

        assert result is True
        # Device probe must release the cap after checking — not leave it open
        mock_cap.release.assert_called_once()

    def test_available_false_when_cv2_absent(self) -> None:
        """available() returns False when cv2 is not importable."""
        from heretic.sjon.webcam import OpenCvBackend

        logger = logging.getLogger("test")
        cfg = SjonWebcamConfig(device_index=0)
        backend = OpenCvBackend(cfg, logger)

        with patch.dict("sys.modules", {"cv2": None}):
            result = backend.available()

        assert result is False

    def test_available_false_when_device_not_opened(self) -> None:
        """available() returns False when cv2 imports but VideoCapture.isOpened() is False."""
        from heretic.sjon.webcam import OpenCvBackend

        logger = logging.getLogger("test")
        cfg = SjonWebcamConfig(device_index=99)
        backend = OpenCvBackend(cfg, logger)

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cv2 = MagicMock()
        mock_cv2.VideoCapture.return_value = mock_cap

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            result = backend.available()

        assert result is False

    def test_available_does_not_raise_on_exception(self) -> None:
        """available() must never raise even if VideoCapture blows up."""
        from heretic.sjon.webcam import OpenCvBackend

        logger = logging.getLogger("test")
        cfg = SjonWebcamConfig(device_index=0)
        backend = OpenCvBackend(cfg, logger)

        mock_cv2 = MagicMock()
        mock_cv2.VideoCapture.side_effect = OSError("device exploded")

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            result = backend.available()

        assert result is False


class TestOpenCvBackendLifecycle:
    """open(), close() lifecycle tests."""

    def _make_backend_with_mock_cv2(
        self, device_index: int = 0
    ) -> "tuple[OpenCvBackend, MagicMock, MagicMock]":
        """Return (backend, mock_cv2, mock_cap) with a happily-opening mock cap."""
        from heretic.sjon.webcam import OpenCvBackend

        logger = logging.getLogger("test")
        cfg = SjonWebcamConfig(device_index=device_index)
        backend = OpenCvBackend(cfg, logger)

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cv2 = MagicMock()
        mock_cv2.VideoCapture.return_value = mock_cap
        return backend, mock_cv2, mock_cap

    def test_open_sets_cap(self) -> None:
        """open() stores the VideoCapture instance in _cap."""
        backend, mock_cv2, mock_cap = self._make_backend_with_mock_cv2()

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            backend.open()

        assert backend._cap is mock_cap

    def test_open_idempotent(self) -> None:
        """Calling open() twice does not re-open the device."""
        backend, mock_cv2, mock_cap = self._make_backend_with_mock_cv2()

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            backend.open()
            backend.open()  # second call must be a no-op

        # VideoCapture constructor called only once
        assert mock_cv2.VideoCapture.call_count == 1

    def test_open_raises_when_device_not_opened(self) -> None:
        """open() raises WebcamCaptureError when VideoCapture.isOpened() is False."""
        from heretic.sjon.webcam import OpenCvBackend

        logger = logging.getLogger("test")
        cfg = SjonWebcamConfig(device_index=99)
        backend = OpenCvBackend(cfg, logger)

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cv2 = MagicMock()
        mock_cv2.VideoCapture.return_value = mock_cap

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            with pytest.raises(WebcamCaptureError):
                backend.open()

    def test_open_raises_when_cv2_absent(self) -> None:
        """open() raises WebcamBackendUnavailableError when cv2 not installed."""
        from heretic.sjon.webcam import OpenCvBackend

        logger = logging.getLogger("test")
        cfg = SjonWebcamConfig()
        backend = OpenCvBackend(cfg, logger)

        with patch.dict("sys.modules", {"cv2": None}):
            with pytest.raises(WebcamBackendUnavailableError):
                backend.open()

    def test_close_releases_cap_idempotent(self) -> None:
        """close() releases cap and is a no-op when called again."""
        backend, mock_cv2, mock_cap = self._make_backend_with_mock_cv2()

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            backend.open()
            backend.close()

        mock_cap.release.assert_called_once()
        assert backend._cap is None

        # Second close() must not raise
        backend.close()
        assert backend._cap is None


class TestOpenCvBackendCapture:
    """capture() — happy path, BGR→RGB conversion, failure modes."""

    def test_capture_returns_rgb_bytes_and_dimensions(self) -> None:
        """capture() returns (rgb_bytes, width, height) on a happy-path read."""
        import numpy as np
        from heretic.sjon.webcam import OpenCvBackend

        logger = logging.getLogger("test")
        cfg = SjonWebcamConfig(device_index=0)
        backend = OpenCvBackend(cfg, logger)

        # 4×4 BGR frame
        fake_bgr = np.zeros((4, 4, 3), dtype=np.uint8)
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, fake_bgr)

        mock_cv2 = MagicMock()
        mock_cv2.VideoCapture.return_value = mock_cap
        # cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) — return an RGB ndarray
        fake_rgb = np.zeros((4, 4, 3), dtype=np.uint8)
        mock_cv2.cvtColor.return_value = fake_rgb
        mock_cv2.COLOR_BGR2RGB = 4  # dummy int constant

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            backend.open()
            raw_bytes, width, height = backend.capture(device_index=0)

        assert isinstance(raw_bytes, bytes)
        assert width == 4
        assert height == 4
        assert len(raw_bytes) == 4 * 4 * 3  # 3 bytes per pixel

    def test_capture_converts_bgr_to_rgb(self) -> None:
        """BGR→RGB conversion must be applied: cv2.cvtColor called with COLOR_BGR2RGB.

        This is the Cartographer-flagged invariant: cv2 returns BGR;
        downstream callers (Pillow, vision APIs) expect RGB. The conversion
        must happen in capture(), before bytes are returned.
        """
        import numpy as np
        from heretic.sjon.webcam import OpenCvBackend

        logger = logging.getLogger("test")
        cfg = SjonWebcamConfig(device_index=0)
        backend = OpenCvBackend(cfg, logger)

        # Synthesise a frame where B≠R so channel order is observable.
        # BGR: pixel (0,0) has B=200, G=100, R=50
        fake_bgr = np.zeros((2, 2, 3), dtype=np.uint8)
        fake_bgr[0, 0] = [200, 100, 50]  # BGR

        # Expected RGB after conversion: R=50, G=100, B=200
        fake_rgb = np.zeros((2, 2, 3), dtype=np.uint8)
        fake_rgb[0, 0] = [50, 100, 200]  # RGB (reversed channels)

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, fake_bgr)

        mock_cv2 = MagicMock()
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.cvtColor.return_value = fake_rgb
        mock_cv2.COLOR_BGR2RGB = 4

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            backend.open()
            raw_bytes, w, h = backend.capture(device_index=0)

        # Verify cv2.cvtColor was called — this is the conversion gate
        assert mock_cv2.cvtColor.called
        call_args = mock_cv2.cvtColor.call_args
        assert call_args[0][1] == mock_cv2.COLOR_BGR2RGB

        # Verify pixel byte order: first pixel in returned bytes = RGB=[50,100,200]
        assert raw_bytes[0] == 50   # R
        assert raw_bytes[1] == 100  # G
        assert raw_bytes[2] == 200  # B

    def test_capture_raises_on_read_failure(self) -> None:
        """capture() raises WebcamCaptureError when cap.read() returns retval=False."""
        import numpy as np
        from heretic.sjon.webcam import OpenCvBackend

        logger = logging.getLogger("test")
        cfg = SjonWebcamConfig(device_index=0)
        backend = OpenCvBackend(cfg, logger)

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (False, None)  # retval=False → device disconnected

        mock_cv2 = MagicMock()
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.COLOR_BGR2RGB = 4

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            backend.open()
            with pytest.raises(WebcamCaptureError):
                backend.capture(device_index=0)

    def test_capture_raises_before_open(self) -> None:
        """capture() raises WebcamBackendUnavailableError when open() has not been called."""
        from heretic.sjon.webcam import OpenCvBackend

        logger = logging.getLogger("test")
        cfg = SjonWebcamConfig()
        backend = OpenCvBackend(cfg, logger)

        mock_cv2 = MagicMock()
        mock_cv2.COLOR_BGR2RGB = 4

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            with pytest.raises(WebcamBackendUnavailableError):
                backend.capture(device_index=0)


# ---------------------------------------------------------------------------
# Sjón.snapshot_webcam() — orchestrator-level tests
# ---------------------------------------------------------------------------

def _make_sjon_with_webcam(
    webcam_cfg: SjonWebcamConfig | None = None,
    webcam_backend_available: bool = True,
    capture_result: tuple[bytes, int, int] | None = None,
    capture_raises: Exception | None = None,
) -> "Sjón":
    """Build a minimal Sjón instance with a mocked webcam backend for testing.

    The screen backend and encoder are also mocked — these tests focus purely
    on the webcam path.
    """
    from heretic.sjon.sjon import Sjón
    from heretic.sjon.config_model import SjonConfig, SjonScreenConfig

    if webcam_cfg is None:
        webcam_cfg = SjonWebcamConfig(enabled=True)

    screen_cfg = SjonScreenConfig(enabled=False)
    cfg = SjonConfig(screen=screen_cfg, webcam=webcam_cfg)

    logger = logging.getLogger("test.sjon")

    # Mock screen backend + encoder (not used in webcam tests)
    mock_screen_backend = MagicMock()
    mock_screen_backend.available.return_value = False
    mock_encoder = MagicMock()

    sjon = Sjón(
        config=cfg,
        capture_backend=mock_screen_backend,
        encoder=mock_encoder,
        logger=logger,
    )

    # Build mock webcam backend
    mock_webcam = MagicMock()
    mock_webcam.available.return_value = webcam_backend_available

    if capture_raises is not None:
        mock_webcam.capture.side_effect = capture_raises
    elif capture_result is not None:
        mock_webcam.capture.return_value = capture_result
    else:
        # Default: tiny 2x2 black frame (RGB bytes)
        import numpy as np
        frame = np.zeros((2, 2, 3), dtype=np.uint8)
        mock_webcam.capture.return_value = (frame.tobytes(), 2, 2)

    sjon._webcam_backend = mock_webcam
    return sjon


class TestSjonSnapshotWebcam:
    """snapshot_webcam() contract tests."""

    @pytest.mark.asyncio
    async def test_disabled_returns_empty(self) -> None:
        """snapshot_webcam() returns [] when webcam.enabled is False."""
        sjon = _make_sjon_with_webcam(
            webcam_cfg=SjonWebcamConfig(enabled=False),
        )
        result = await sjon.snapshot_webcam()
        assert result == []

    @pytest.mark.asyncio
    async def test_no_backend_returns_empty(self) -> None:
        """snapshot_webcam() returns [] when _webcam_backend is None."""
        from heretic.sjon.sjon import Sjón
        from heretic.sjon.config_model import SjonConfig, SjonScreenConfig

        cfg = SjonConfig(
            screen=SjonScreenConfig(enabled=False),
            webcam=SjonWebcamConfig(enabled=True),
        )
        mock_backend = MagicMock()
        mock_backend.available.return_value = False
        sjon = Sjón(
            config=cfg,
            capture_backend=mock_backend,
            encoder=MagicMock(),
            logger=logging.getLogger("test"),
        )
        # _webcam_backend is None by default
        result = await sjon.snapshot_webcam()
        assert result == []

    @pytest.mark.asyncio
    async def test_unavailable_backend_returns_empty(self) -> None:
        """snapshot_webcam() returns [] when backend.available() is False."""
        sjon = _make_sjon_with_webcam(webcam_backend_available=False)
        result = await sjon.snapshot_webcam()
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_jpeg_data_url(self) -> None:
        """snapshot_webcam() returns 'data:image/jpeg;base64,...' when format=jpeg."""
        import numpy as np

        frame = np.zeros((8, 8, 3), dtype=np.uint8)
        rgb_bytes = frame.tobytes()

        sjon = _make_sjon_with_webcam(
            webcam_cfg=SjonWebcamConfig(enabled=True, format="jpeg", jpeg_quality=85),
            capture_result=(rgb_bytes, 8, 8),
        )
        result = await sjon.snapshot_webcam()

        assert len(result) == 1
        assert result[0].startswith("data:image/jpeg;base64,")

    @pytest.mark.asyncio
    async def test_returns_png_data_url(self) -> None:
        """snapshot_webcam() returns 'data:image/png;base64,...' when format=png."""
        import numpy as np

        frame = np.zeros((8, 8, 3), dtype=np.uint8)
        rgb_bytes = frame.tobytes()

        sjon = _make_sjon_with_webcam(
            webcam_cfg=SjonWebcamConfig(enabled=True, format="png"),
            capture_result=(rgb_bytes, 8, 8),
        )
        result = await sjon.snapshot_webcam()

        assert len(result) == 1
        assert result[0].startswith("data:image/png;base64,")

    @pytest.mark.asyncio
    async def test_respects_max_dimensions(self) -> None:
        """_encode_webcam_frame resizes down to fit max_width x max_height."""
        import base64
        import io
        import numpy as np
        from PIL import Image

        # 64x64 source frame, max 32x32 → should be resized down
        frame = np.zeros((64, 64, 3), dtype=np.uint8)
        rgb_bytes = frame.tobytes()

        sjon = _make_sjon_with_webcam(
            webcam_cfg=SjonWebcamConfig(
                enabled=True, format="png", max_width=32, max_height=32
            ),
            capture_result=(rgb_bytes, 64, 64),
        )
        result = await sjon.snapshot_webcam()

        assert len(result) == 1
        # Decode and verify dimensions were constrained
        data_b64 = result[0].split(",", 1)[1]
        img = Image.open(io.BytesIO(base64.b64decode(data_b64)))
        assert img.width <= 32
        assert img.height <= 32

    @pytest.mark.asyncio
    async def test_never_raises_on_capture_error(self) -> None:
        """snapshot_webcam() returns [] when capture raises WebcamCaptureError; never propagates."""
        sjon = _make_sjon_with_webcam(
            capture_raises=WebcamCaptureError("device read failed"),
        )
        result = await sjon.snapshot_webcam()
        assert result == []

    @pytest.mark.asyncio
    async def test_never_raises_on_generic_error(self) -> None:
        """snapshot_webcam() returns [] even when an unexpected error occurs; never propagates."""
        sjon = _make_sjon_with_webcam(
            capture_raises=RuntimeError("unexpected hardware fault"),
        )
        result = await sjon.snapshot_webcam()
        assert result == []
