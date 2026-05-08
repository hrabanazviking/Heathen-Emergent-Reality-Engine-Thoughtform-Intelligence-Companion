"""
Placeholder tests for heretic.sjon.capture.

These tests are skip-marked during the v0.5 scaffold phase. Forge implements
the full test suite in Wave 2 after the stubs in capture.py are filled.

Coverage targets (Forge):
    - NullBackend.available() returns False
    - NullBackend.capture() raises BackendUnavailableError
    - NullBackend.close() is a no-op (no raise)
    - MssBackend.available() returns False when mss is not importable (mock importlib)
    - MssBackend.available() returns False when OS denies screen capture permission
    - MssBackend.capture() returns (bytes, int, int) on success (mock mss)
    - MssBackend.capture() raises PermissionDeniedError on macOS TCC denial
    - MssBackend.capture() raises ScreenCaptureError on mss internal error
    - MssBackend.close() releases mss instance without raising
    - best_available() returns NullBackend when mss is not importable
    - best_available() returns MssBackend when mss is importable and available
    - best_available() logs a warning when falling back to NullBackend
    - monitor_index out-of-range is clamped with a warning (not a crash)
"""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
def test_null_backend_available_is_false() -> None:
    """NullBackend.available() always returns False."""
    from heretic.sjon.capture import NullBackend
    backend = NullBackend()
    assert backend.available() is False


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
def test_null_backend_capture_raises() -> None:
    """NullBackend.capture() raises BackendUnavailableError with a clear message."""
    from heretic.sjon.capture import NullBackend
    from heretic.sjon.errors import BackendUnavailableError
    backend = NullBackend()
    with pytest.raises(BackendUnavailableError):
        backend.capture()


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
def test_null_backend_close_is_noop() -> None:
    """NullBackend.close() does not raise."""
    from heretic.sjon.capture import NullBackend
    backend = NullBackend()
    backend.close()  # must not raise


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
def test_mss_backend_available_false_when_mss_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    """MssBackend.available() returns False when mss is not installed."""
    import builtins
    real_import = builtins.__import__

    def mock_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "mss":
            raise ImportError("mss not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    from heretic.sjon.capture import MssBackend
    from heretic.sjon.config_model import SjonScreenConfig
    import logging
    backend = MssBackend(SjonScreenConfig(), logging.getLogger("test"))
    assert backend.available() is False


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
def test_best_available_returns_null_when_mss_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """best_available() returns NullBackend when mss is not importable."""
    from heretic.sjon.capture import NullBackend
    # Forge: mock MssBackend.available() to return False; assert result is NullBackend
    pass
