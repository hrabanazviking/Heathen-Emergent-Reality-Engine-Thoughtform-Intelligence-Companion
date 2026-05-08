"""
Tests for heretic.sjon.capture — ScreenCaptureBackend, MssBackend, NullBackend, best_available.

All mss calls are mocked — tests must pass on headless machines without mss installed.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from heretic.sjon.config_model import SjonScreenConfig
from heretic.sjon.errors import (
    BackendUnavailableError,
    PermissionDeniedError,
    ScreenCaptureError,
)


# ---------------------------------------------------------------------------
# NullBackend
# ---------------------------------------------------------------------------

class TestNullBackend:
    def test_available_is_false(self) -> None:
        from heretic.sjon.capture import NullBackend
        backend = NullBackend()
        assert backend.available() is False

    def test_capture_raises_backend_unavailable(self) -> None:
        from heretic.sjon.capture import NullBackend
        backend = NullBackend()
        with pytest.raises(BackendUnavailableError):
            backend.capture()

    def test_close_is_noop(self) -> None:
        from heretic.sjon.capture import NullBackend
        backend = NullBackend()
        backend.close()  # must not raise

    def test_close_is_idempotent(self) -> None:
        from heretic.sjon.capture import NullBackend
        backend = NullBackend()
        backend.close()
        backend.close()  # second call also must not raise


# ---------------------------------------------------------------------------
# MssBackend.available()
# ---------------------------------------------------------------------------

class TestMssBackendAvailable:
    def test_available_false_when_mss_import_fails(self) -> None:
        """MssBackend.available() returns False when mss is not installed."""
        from heretic.sjon.capture import MssBackend

        cfg = SjonScreenConfig()
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)

        # Patch the import inside the available() method.
        with patch("builtins.__import__", side_effect=ImportError("mss not installed")):
            result = backend.available()

        assert result is False

    def test_available_true_when_mss_present(self) -> None:
        """MssBackend.available() returns True when mss + Pillow are available."""
        from heretic.sjon.capture import MssBackend

        cfg = SjonScreenConfig()
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)

        # Mock mss to simulate a successful probe.
        mock_mss_ctx = MagicMock()
        mock_mss_ctx.__enter__ = MagicMock(return_value=mock_mss_ctx)
        mock_mss_ctx.__exit__ = MagicMock(return_value=False)
        mock_mss_ctx.monitors = [
            {"left": 0, "top": 0, "width": 3840, "height": 2160},  # virtual all
            {"left": 0, "top": 0, "width": 1920, "height": 1080},  # primary
        ]

        mock_mss_module = MagicMock()
        mock_mss_module.mss.return_value = mock_mss_ctx

        mock_pil = MagicMock()

        with patch.dict("sys.modules", {"mss": mock_mss_module, "PIL": mock_pil, "PIL.Image": mock_pil}):
            result = backend.available()

        assert result is True

    def test_available_false_when_probe_raises(self) -> None:
        """MssBackend.available() returns False when the mss probe raises unexpectedly."""
        from heretic.sjon.capture import MssBackend

        cfg = SjonScreenConfig()
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)

        mock_mss_module = MagicMock()
        mock_mss_module.mss.side_effect = RuntimeError("probe error")
        mock_pil = MagicMock()

        with patch.dict("sys.modules", {"mss": mock_mss_module, "PIL": mock_pil, "PIL.Image": mock_pil}):
            result = backend.available()

        assert result is False

    def test_available_false_when_no_monitors(self) -> None:
        """MssBackend.available() returns False when mss reports an empty monitor list."""
        from heretic.sjon.capture import MssBackend

        cfg = SjonScreenConfig()
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)

        mock_mss_ctx = MagicMock()
        mock_mss_ctx.__enter__ = MagicMock(return_value=mock_mss_ctx)
        mock_mss_ctx.__exit__ = MagicMock(return_value=False)
        mock_mss_ctx.monitors = []  # empty — no monitors

        mock_mss_module = MagicMock()
        mock_mss_module.mss.return_value = mock_mss_ctx
        mock_pil = MagicMock()

        with patch.dict("sys.modules", {"mss": mock_mss_module, "PIL": mock_pil, "PIL.Image": mock_pil}):
            result = backend.available()

        assert result is False


# ---------------------------------------------------------------------------
# MssBackend.capture()
# ---------------------------------------------------------------------------

class TestMssBackendCapture:
    def _make_mock_mss_instance(self, width: int = 1920, height: int = 1080) -> MagicMock:
        """Build a mock mss instance that returns a synthetic BGRA frame."""
        bgra_size = width * height * 4
        fake_bgra = bytes(bgra_size)

        mock_sct_img = MagicMock()
        mock_sct_img.bgra = fake_bgra
        mock_sct_img.width = width
        mock_sct_img.height = height

        monitor_list = [
            {"left": 0, "top": 0, "width": 3840, "height": 2160},  # virtual
            {"left": 0, "top": 0, "width": width, "height": height},  # primary
        ]

        mock_instance = MagicMock()
        mock_instance.monitors = monitor_list
        mock_instance.grab.return_value = mock_sct_img
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        return mock_instance

    def test_capture_returns_bgra_bytes_and_dimensions(self) -> None:
        """capture() returns (bytes, width, height) on happy path."""
        from heretic.sjon.capture import MssBackend

        w, h = 1920, 1080
        cfg = SjonScreenConfig(monitor_index=0)
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)

        mock_mss_instance = self._make_mock_mss_instance(w, h)
        mock_mss_module = MagicMock()
        mock_mss_module.mss.return_value = mock_mss_instance
        mock_mss_module.exception = MagicMock()
        # Make ScreenShotError a real exception class so it can be caught
        mock_mss_module.exception.ScreenShotError = type(
            "ScreenShotError", (Exception,), {}
        )
        mock_mss_exception = mock_mss_module.exception

        with patch.dict("sys.modules", {
            "mss": mock_mss_module,
            "mss.exception": mock_mss_exception,
        }):
            raw, width, height = backend.capture()

        assert isinstance(raw, bytes)
        assert len(raw) == w * h * 4
        assert width == w
        assert height == h

    def test_capture_raises_screen_capture_error_on_mss_failure(self) -> None:
        """capture() raises ScreenCaptureError when mss raises ScreenShotError (non-permission)."""
        from heretic.sjon.capture import MssBackend

        cfg = SjonScreenConfig()
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)

        MockScreenShotError = type("ScreenShotError", (Exception,), {})

        mock_mss_instance = MagicMock()
        mock_mss_instance.monitors = [
            {"left": 0, "top": 0, "width": 3840, "height": 2160},
            {"left": 0, "top": 0, "width": 1920, "height": 1080},
        ]
        mock_mss_instance.grab.side_effect = MockScreenShotError("capture error")
        mock_mss_instance.__enter__ = MagicMock(return_value=mock_mss_instance)
        mock_mss_instance.__exit__ = MagicMock(return_value=False)

        mock_mss_module = MagicMock()
        mock_mss_module.mss.return_value = mock_mss_instance
        mock_mss_module.exception.ScreenShotError = MockScreenShotError

        with patch.dict("sys.modules", {
            "mss": mock_mss_module,
            "mss.exception": mock_mss_module.exception,
        }):
            with pytest.raises(ScreenCaptureError):
                backend.capture()

    def test_capture_raises_permission_denied_on_tcc_error(self) -> None:
        """capture() raises PermissionDeniedError when the error message mentions 'permission'."""
        from heretic.sjon.capture import MssBackend

        cfg = SjonScreenConfig()
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)

        MockScreenShotError = type("ScreenShotError", (Exception,), {})

        mock_mss_instance = MagicMock()
        mock_mss_instance.monitors = [
            {"left": 0, "top": 0, "width": 3840, "height": 2160},
            {"left": 0, "top": 0, "width": 1920, "height": 1080},
        ]
        mock_mss_instance.grab.side_effect = MockScreenShotError(
            "Permission denied: screen recording blocked by TCC"
        )
        mock_mss_instance.__enter__ = MagicMock(return_value=mock_mss_instance)
        mock_mss_instance.__exit__ = MagicMock(return_value=False)

        mock_mss_module = MagicMock()
        mock_mss_module.mss.return_value = mock_mss_instance
        mock_mss_module.exception.ScreenShotError = MockScreenShotError

        with patch.dict("sys.modules", {
            "mss": mock_mss_module,
            "mss.exception": mock_mss_module.exception,
        }):
            with pytest.raises(PermissionDeniedError):
                backend.capture()

    def test_capture_raises_backend_unavailable_when_mss_not_importable(self) -> None:
        """capture() raises BackendUnavailableError when mss cannot be imported at capture time."""
        from heretic.sjon.capture import MssBackend

        cfg = SjonScreenConfig()
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)

        # Simulate mss not installed at capture time.
        with patch("builtins.__import__", side_effect=ImportError("mss not installed")):
            with pytest.raises(BackendUnavailableError):
                backend.capture()

    def test_monitor_index_clamping(self) -> None:
        """capture() clamps out-of-range monitor_index to highest available with a warning."""
        from heretic.sjon.capture import MssBackend

        # monitor_index=9 but only 1 monitor available -> clamp to index 1 (primary)
        cfg = SjonScreenConfig(monitor_index=9)
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)

        w, h = 1920, 1080
        fake_bgra = bytes(w * h * 4)

        mock_sct_img = MagicMock()
        mock_sct_img.bgra = fake_bgra
        mock_sct_img.width = w
        mock_sct_img.height = h

        mock_instance = MagicMock()
        mock_instance.monitors = [
            {"left": 0, "top": 0, "width": 3840, "height": 2160},  # virtual
            {"left": 0, "top": 0, "width": w, "height": h},         # primary only
        ]
        mock_instance.grab.return_value = mock_sct_img
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)

        MockScreenShotError = type("ScreenShotError", (Exception,), {})
        mock_mss_module = MagicMock()
        mock_mss_module.mss.return_value = mock_instance
        mock_mss_module.exception.ScreenShotError = MockScreenShotError

        with patch.dict("sys.modules", {
            "mss": mock_mss_module,
            "mss.exception": mock_mss_module.exception,
        }):
            raw, width, height = backend.capture()

        # Clamped to primary — should succeed and return valid dimensions
        assert width == w
        assert height == h


# ---------------------------------------------------------------------------
# v0.5.1 placeholder tests — MssBackend.list_monitors
# Forge implements the logic; these stubs mark the scaffold complete.
# ---------------------------------------------------------------------------

class TestMssBackendListMonitors:
    """MssBackend.list_monitors() — v0.5.1. (Placeholders: Forge implements.)"""

    @pytest.mark.skip(
        reason="v0.5.1 placeholder — Forge implements: list_monitors returns mss.monitors list"
    )
    def test_list_monitors_returns_list_of_dicts(self) -> None:
        from heretic.sjon.capture import MssBackend
        cfg = SjonScreenConfig()
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)
        monitors = backend.list_monitors()
        assert isinstance(monitors, list)
        assert len(monitors) >= 1
        for m in monitors:
            assert "width" in m
            assert "height" in m

    @pytest.mark.skip(
        reason=(
            "v0.5.1 placeholder — Forge implements: list_monitors index 0 = composite virtual"
        )
    )
    def test_list_monitors_index_0_is_composite(self) -> None:
        from heretic.sjon.capture import MssBackend
        cfg = SjonScreenConfig()
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)
        monitors = backend.list_monitors()
        # Index 0 is the virtual all-monitors composite — width >= any individual screen
        assert monitors[0]["width"] >= max(m["width"] for m in monitors[1:] or [{"width": 0}])

    @pytest.mark.skip(
        reason=(
            "v0.5.1 placeholder — Forge implements: list_monitors raises "
            "BackendUnavailableError when mss not installed"
        )
    )
    def test_list_monitors_raises_when_mss_not_installed(self) -> None:
        from heretic.sjon.capture import MssBackend
        cfg = SjonScreenConfig()
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)
        with pytest.raises(BackendUnavailableError):
            backend.list_monitors()


# ---------------------------------------------------------------------------
# MssBackend.close()
# ---------------------------------------------------------------------------

class TestMssBackendClose:
    def test_close_before_capture_is_noop(self) -> None:
        """MssBackend.close() is a no-op when no mss instance has been created."""
        from heretic.sjon.capture import MssBackend

        cfg = SjonScreenConfig()
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)
        backend.close()  # must not raise

    def test_close_is_idempotent(self) -> None:
        """MssBackend.close() can be called multiple times without error."""
        from heretic.sjon.capture import MssBackend

        cfg = SjonScreenConfig()
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)
        backend.close()
        backend.close()  # second call also safe


# ---------------------------------------------------------------------------
# best_available() factory
# ---------------------------------------------------------------------------

class TestBestAvailable:
    def test_returns_null_backend_when_mss_unavailable(self) -> None:
        """best_available() returns NullBackend when MssBackend.available() is False."""
        from heretic.sjon.capture import best_available, NullBackend, MssBackend

        cfg = SjonScreenConfig()
        log = logging.getLogger("test")

        # Patch MssBackend.available to return False.
        with patch.object(MssBackend, "available", return_value=False):
            backend = best_available(log, cfg)

        assert isinstance(backend, NullBackend)

    def test_returns_mss_backend_when_available(self) -> None:
        """best_available() returns MssBackend when it reports available=True."""
        from heretic.sjon.capture import best_available, MssBackend

        cfg = SjonScreenConfig()
        log = logging.getLogger("test")

        with patch.object(MssBackend, "available", return_value=True):
            backend = best_available(log, cfg)

        assert isinstance(backend, MssBackend)

    def test_logs_warning_when_falling_back_to_null(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """best_available() logs a warning when falling back to NullBackend."""
        from heretic.sjon.capture import best_available, MssBackend

        cfg = SjonScreenConfig()
        log = logging.getLogger("test_best_available_warn")

        with patch.object(MssBackend, "available", return_value=False):
            with caplog.at_level(logging.WARNING, logger="test_best_available_warn"):
                best_available(log, cfg)

        assert any(
            "No screen capture backend available" in r.message or
            "vision" in r.message.lower()
            for r in caplog.records
        )
