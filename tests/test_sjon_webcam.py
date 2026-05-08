"""
Placeholder tests for L3 Sjón webcam support — v0.5.2 pre-stage scaffold.

All tests are marked pytest.mark.skip with an explicit reason pointing to
Forge Wave 2. This file declares the contract surface that the Forge will
validate once OpenCvBackend and snapshot_webcam() are implemented.

Test inventory:
    1. test_webcam_null_backend_available — NullBackend.available() always False.
    2. test_webcam_null_backend_capture_raises — NullBackend.capture() raises WebcamBackendUnavailableError.
    3. test_factory_falls_back_to_null_when_cv2_absent — best_available() returns NullBackend when cv2 not installed.
    4. test_webcam_config_defaults — SjonWebcamConfig field defaults are correct.
    5. test_webcam_config_validation_jpeg_quality — out-of-range jpeg_quality raises ValueError.
    6. test_webcam_config_validation_attach_policy — invalid attach_policy raises ValueError.
    7. test_webcam_config_validation_format — invalid format raises ValueError.
    8. test_webcam_config_validation_dimensions — max_width/max_height < 1 raises ValueError.
    9. test_webcam_config_enabled_true_logs_warning — enabled=True logs a privacy warning.
   10. test_opencvbackend_available_probe_happy_path — (Forge Wave 2) available() True when cv2+device present.
   11. test_opencvbackend_capture_happy_path — (Forge Wave 2) capture() returns (bytes, width, height).
   12. test_opencvbackend_capture_format_jpeg — (Forge Wave 2) snapshot_webcam() returns data:image/jpeg URL.
   13. test_opencvbackend_capture_format_png — (Forge Wave 2) snapshot_webcam() returns data:image/png URL.
   14. test_snapshot_webcam_attach_policy_screen_only — snapshot_webcam() returns [] when attach_policy screen_only.
   15. test_snapshot_webcam_disabled_returns_empty — snapshot_webcam() returns [] when webcam.enabled False.
   16. test_snapshot_webcam_never_raises — snapshot_webcam() returns [] even if capture explodes.

Ref: TASK_HERETIC_v0.5.2_WEBCAM.md §Wave 2 (Forge implements OpenCvBackend + snapshot_webcam).
     src/heretic/sjon/webcam.py (WebcamCaptureBackend ABC + OpenCvBackend skeleton).
     src/heretic/sjon/errors.py (WebcamCaptureError, WebcamBackendUnavailableError).
"""

from __future__ import annotations

import logging

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
    """Factory behaviour before Forge Wave 2 implements OpenCvBackend.available()."""

    def test_factory_returns_webcam_null_backend_when_cv2_absent(self) -> None:
        """When OpenCvBackend.available() raises NotImplementedError (pre-Wave-2),
        best_available() must return WebcamNullBackend."""
        logger = logging.getLogger("test.factory")
        cfg = SjonWebcamConfig()
        backend = best_available(logger, cfg)
        # At the pre-stage, available() raises NotImplementedError, so we
        # always expect NullBackend from the factory.
        assert isinstance(backend, WebcamNullBackend)

    def test_factory_never_returns_none(self) -> None:
        """Factory must always return a backend instance, never None."""
        logger = logging.getLogger("test.factory")
        cfg = SjonWebcamConfig()
        backend = best_available(logger, cfg)
        assert backend is not None


# ---------------------------------------------------------------------------
# OpenCvBackend skeleton — skipped until Forge Wave 2 implements available(),
# open(), capture(), close().
# ---------------------------------------------------------------------------

@pytest.mark.skip(
    reason="OpenCvBackend.available() raises NotImplementedError — Forge Wave 2 implements it. "
           "Ref: TASK_HERETIC_v0.5.2_WEBCAM.md §Wave 2."
)
def test_opencvbackend_available_probe_happy_path() -> None:
    """(Forge Wave 2) OpenCvBackend.available() returns True when cv2 and device 0 are present."""
    from unittest.mock import MagicMock, patch

    from heretic.sjon.webcam import OpenCvBackend

    logger = logging.getLogger("test")
    cfg = SjonWebcamConfig(device_index=0)
    backend = OpenCvBackend(cfg, logger)

    # Forge should mock cv2.VideoCapture such that isOpened() returns True.
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True

    with patch("cv2.VideoCapture", return_value=mock_cap):
        result = backend.available()

    assert result is True


@pytest.mark.skip(
    reason="OpenCvBackend.capture() raises NotImplementedError — Forge Wave 2 implements it. "
           "Ref: TASK_HERETIC_v0.5.2_WEBCAM.md §Wave 2."
)
def test_opencvbackend_capture_happy_path() -> None:
    """(Forge Wave 2) OpenCvBackend.capture() returns (bytes, width, height) on success."""
    import numpy as np
    from unittest.mock import MagicMock, patch

    from heretic.sjon.webcam import OpenCvBackend

    logger = logging.getLogger("test")
    cfg = SjonWebcamConfig(device_index=0)
    backend = OpenCvBackend(cfg, logger)

    # Synthesise a 4x4 BGR frame (small enough to be fast in tests).
    fake_frame = np.zeros((4, 4, 3), dtype=np.uint8)
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, fake_frame)

    with patch("cv2.VideoCapture", return_value=mock_cap):
        backend.open()
        raw_bytes, width, height = backend.capture(device_index=0)

    assert isinstance(raw_bytes, bytes)
    assert len(raw_bytes) == 4 * 4 * 3  # 4x4 BGR
    assert width == 4
    assert height == 4


@pytest.mark.skip(
    reason="Sjón.snapshot_webcam() raises NotImplementedError — Forge Wave 2 implements it. "
           "Ref: TASK_HERETIC_v0.5.2_WEBCAM.md §Wave 2."
)
async def test_snapshot_webcam_returns_jpeg_data_url() -> None:
    """(Forge Wave 2) snapshot_webcam() returns 'data:image/jpeg;base64,...' when format=jpeg."""
    # Forge will implement this test using a mocked OpenCvBackend that returns a
    # real 4x4 frame, and verify the returned data URL prefix.
    raise NotImplementedError(
        "Forge Wave 2: inject a mocked OpenCvBackend and assert "
        "data_url.startswith('data:image/jpeg;base64,')"
    )


@pytest.mark.skip(
    reason="Sjón.snapshot_webcam() raises NotImplementedError — Forge Wave 2 implements it. "
           "Ref: TASK_HERETIC_v0.5.2_WEBCAM.md §Wave 2."
)
async def test_snapshot_webcam_returns_png_data_url() -> None:
    """(Forge Wave 2) snapshot_webcam() returns 'data:image/png;base64,...' when format=png."""
    raise NotImplementedError(
        "Forge Wave 2: inject a mocked OpenCvBackend with format=png and assert "
        "data_url.startswith('data:image/png;base64,')"
    )


@pytest.mark.skip(
    reason="Sjón.snapshot_webcam() raises NotImplementedError — Forge Wave 2 implements it. "
           "Ref: TASK_HERETIC_v0.5.2_WEBCAM.md §Wave 2."
)
async def test_snapshot_webcam_screen_only_policy_returns_empty() -> None:
    """(Forge Wave 2) snapshot_webcam() returns [] when attach_policy='screen_only'."""
    raise NotImplementedError(
        "Forge Wave 2: even with webcam.enabled=True, if attach_policy='screen_only', "
        "snapshot_webcam() must return []. Assert result == []."
    )


@pytest.mark.skip(
    reason="Sjón.snapshot_webcam() raises NotImplementedError — Forge Wave 2 implements it. "
           "Ref: TASK_HERETIC_v0.5.2_WEBCAM.md §Wave 2."
)
async def test_snapshot_webcam_disabled_returns_empty() -> None:
    """(Forge Wave 2) snapshot_webcam() returns [] when webcam.enabled is False."""
    raise NotImplementedError(
        "Forge Wave 2: with webcam.enabled=False, snapshot_webcam() must return []. "
        "Assert result == []."
    )


@pytest.mark.skip(
    reason="Sjón.snapshot_webcam() raises NotImplementedError — Forge Wave 2 implements it. "
           "Ref: TASK_HERETIC_v0.5.2_WEBCAM.md §Wave 2."
)
async def test_snapshot_webcam_never_raises_on_capture_error() -> None:
    """(Forge Wave 2) snapshot_webcam() returns [] when capture raises; never propagates."""
    raise NotImplementedError(
        "Forge Wave 2: inject a mocked OpenCvBackend.capture() that raises WebcamCaptureError, "
        "call snapshot_webcam(), assert result == [] and no exception propagates."
    )
