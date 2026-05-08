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
# v0.5.1 tests — MssBackend.list_monitors + capture mapping asymmetry
# ---------------------------------------------------------------------------

class TestMssBackendListMonitors:
    """MssBackend.list_monitors() — v0.5.1 real tests."""

    def _make_mock_mss_context(
        self, monitor_list: list[dict] | None = None
    ) -> tuple[MagicMock, MagicMock]:
        """Return (mock_mss_module, mock_sct) with a given monitor list."""
        if monitor_list is None:
            monitor_list = [
                {"left": 0, "top": 0, "width": 3840, "height": 2160},  # virtual composite
                {"left": 0, "top": 0, "width": 1920, "height": 1080},  # primary
            ]
        mock_sct = MagicMock()
        mock_sct.monitors = monitor_list
        mock_sct.__enter__ = MagicMock(return_value=mock_sct)
        mock_sct.__exit__ = MagicMock(return_value=False)

        mock_mss_module = MagicMock()
        mock_mss_module.mss.return_value = mock_sct
        return mock_mss_module, mock_sct

    def test_list_monitors_returns_list_of_dicts(self) -> None:
        """list_monitors() returns a list of dicts with width/height keys."""
        from heretic.sjon.capture import MssBackend

        cfg = SjonScreenConfig()
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)

        mock_mss_module, _ = self._make_mock_mss_context()
        with patch.dict("sys.modules", {"mss": mock_mss_module}):
            monitors = backend.list_monitors()

        assert isinstance(monitors, list)
        assert len(monitors) == 2
        for m in monitors:
            assert isinstance(m, dict)
            assert "width" in m
            assert "height" in m
            assert "left" in m
            assert "top" in m

    def test_list_monitors_index_0_is_composite(self) -> None:
        """list_monitors()[0] is the virtual all-monitors composite (width >= any individual)."""
        from heretic.sjon.capture import MssBackend

        cfg = SjonScreenConfig()
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)

        monitor_list = [
            {"left": 0, "top": 0, "width": 3840, "height": 2160},  # virtual composite
            {"left": 0, "top": 0, "width": 1920, "height": 1080},  # screen 1
            {"left": 1920, "top": 0, "width": 1920, "height": 1080},  # screen 2
        ]
        mock_mss_module, _ = self._make_mock_mss_context(monitor_list)
        with patch.dict("sys.modules", {"mss": mock_mss_module}):
            monitors = backend.list_monitors()

        # Index 0 must have width >= max of individual screens
        individual_widths = [m["width"] for m in monitors[1:]]
        assert monitors[0]["width"] >= max(individual_widths)

    def test_list_monitors_raises_when_mss_not_installed(self) -> None:
        """list_monitors() raises BackendUnavailableError when mss cannot be imported."""
        from heretic.sjon.capture import MssBackend

        cfg = SjonScreenConfig()
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)

        with patch("builtins.__import__", side_effect=ImportError("mss not installed")):
            with pytest.raises(BackendUnavailableError):
                backend.list_monitors()

    def test_list_monitors_raises_screen_capture_error_on_mss_failure(self) -> None:
        """list_monitors() raises ScreenCaptureError when mss.mss() raises unexpectedly."""
        from heretic.sjon.capture import MssBackend

        cfg = SjonScreenConfig()
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)

        mock_mss_module = MagicMock()
        mock_mss_module.mss.side_effect = RuntimeError("display not available")
        with patch.dict("sys.modules", {"mss": mock_mss_module}):
            with pytest.raises(ScreenCaptureError):
                backend.list_monitors()

    def test_list_monitors_opens_fresh_context_not_reusing_instance(self) -> None:
        """list_monitors() opens its own fresh mss context, never reuses capture's instance."""
        from heretic.sjon.capture import MssBackend

        cfg = SjonScreenConfig()
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)

        # Pre-populate _mss_instance to verify list_monitors ignores it.
        backend._mss_instance = MagicMock()

        mock_mss_module, mock_sct = self._make_mock_mss_context()
        with patch.dict("sys.modules", {"mss": mock_mss_module}):
            monitors = backend.list_monitors()

        # The fresh context was opened (mss.mss() called once)
        mock_mss_module.mss.assert_called_once()
        # The pre-existing _mss_instance was not touched
        assert backend._mss_instance is not None  # still the pre-populated mock


class TestMssMonitorIndexMappingAsymmetry:
    """v0.5.1 mapping asymmetry: continuous vs on-demand monitor index resolution."""

    def _make_backend_with_mss(
        self,
        monitor_index: int = 0,
        continuous: bool = False,
        monitor_list: list[dict] | None = None,
    ) -> tuple["MssBackend", MagicMock, MagicMock]:
        """Build MssBackend + mock mss capturing the grab call."""
        from heretic.sjon.capture import MssBackend

        if monitor_list is None:
            monitor_list = [
                {"left": 0, "top": 0, "width": 3840, "height": 2160},   # virtual index 0
                {"left": 0, "top": 0, "width": 1920, "height": 1080},   # primary index 1
                {"left": 1920, "top": 0, "width": 1920, "height": 1080}, # secondary index 2
            ]

        cfg = SjonScreenConfig(monitor_index=monitor_index, continuous=continuous)
        log = logging.getLogger("test")
        backend = MssBackend(cfg, log)

        mock_sct_img = MagicMock()
        mock_sct_img.bgra = bytes(1920 * 1080 * 4)
        mock_sct_img.width = 1920
        mock_sct_img.height = 1080

        mock_instance = MagicMock()
        mock_instance.monitors = monitor_list
        mock_instance.grab.return_value = mock_sct_img
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)

        MockSSE = type("ScreenShotError", (Exception,), {})
        mock_mss_module = MagicMock()
        mock_mss_module.mss.return_value = mock_instance
        mock_mss_module.exception.ScreenShotError = MockSSE

        return backend, mock_instance, mock_mss_module

    def test_capture_continuous_index_0_uses_mss_0_composite(self) -> None:
        """In continuous mode with monitor_index=0, grab is called with monitors[0] (composite)."""
        backend, mock_instance, mock_mss_module = self._make_backend_with_mss(
            monitor_index=0, continuous=True
        )
        expected_monitor = mock_instance.monitors[0]  # composite virtual

        with patch.dict("sys.modules", {
            "mss": mock_mss_module,
            "mss.exception": mock_mss_module.exception,
        }):
            backend.capture()

        mock_instance.grab.assert_called_once_with(expected_monitor)

    def test_capture_on_demand_index_0_uses_mss_1_primary(self) -> None:
        """In on-demand mode with monitor_index=0, grab is called with monitors[1] (primary)."""
        backend, mock_instance, mock_mss_module = self._make_backend_with_mss(
            monitor_index=0, continuous=False
        )
        expected_monitor = mock_instance.monitors[1]  # primary single monitor

        with patch.dict("sys.modules", {
            "mss": mock_mss_module,
            "mss.exception": mock_mss_module.exception,
        }):
            backend.capture()

        mock_instance.grab.assert_called_once_with(expected_monitor)

    def test_capture_index_n_passes_through_in_both_modes(self) -> None:
        """monitor_index=2 maps to mss index 2 in both continuous and on-demand modes."""
        for continuous in (True, False):
            backend, mock_instance, mock_mss_module = self._make_backend_with_mss(
                monitor_index=2, continuous=continuous
            )
            mock_instance.grab.reset_mock()
            expected_monitor = mock_instance.monitors[2]

            with patch.dict("sys.modules", {
                "mss": mock_mss_module,
                "mss.exception": mock_mss_module.exception,
            }):
                backend.capture()

            mock_instance.grab.assert_called_once_with(expected_monitor)


class TestResolveMonitorIndex:
    """Unit tests for the _resolve_mss_monitor_index helper function."""

    def test_continuous_true_index_0_returns_0(self) -> None:
        from heretic.sjon.capture import _resolve_mss_monitor_index
        assert _resolve_mss_monitor_index(continuous=True, config_index=0) == 0

    def test_continuous_false_index_0_returns_1(self) -> None:
        from heretic.sjon.capture import _resolve_mss_monitor_index
        assert _resolve_mss_monitor_index(continuous=False, config_index=0) == 1

    def test_index_1_returns_1_regardless_of_mode(self) -> None:
        from heretic.sjon.capture import _resolve_mss_monitor_index
        assert _resolve_mss_monitor_index(continuous=True, config_index=1) == 1
        assert _resolve_mss_monitor_index(continuous=False, config_index=1) == 1

    def test_index_2_returns_2_regardless_of_mode(self) -> None:
        from heretic.sjon.capture import _resolve_mss_monitor_index
        assert _resolve_mss_monitor_index(continuous=True, config_index=2) == 2
        assert _resolve_mss_monitor_index(continuous=False, config_index=2) == 2


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
