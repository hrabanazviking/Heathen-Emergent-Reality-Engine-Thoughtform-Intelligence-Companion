"""
Placeholder tests — MicrophoneCapture backends (L2 Rödd Hlust substrate).

All tests are skip-marked. Forge implements these in v0.3 Wave 2.

Coverage targets (Forge):
    - SoundDeviceMicBackend.available() returns True when sounddevice is importable
    - SoundDeviceMicBackend.available() returns False when sounddevice is absent (mocked)
    - SoundDeviceMicBackend.start_stream() pushes FRAME_BYTES-sized frames to callback
    - SoundDeviceMicBackend.stop_stream() cleanly stops the stream without raising
    - SoundDeviceMicBackend.stop_stream() is idempotent (safe to call twice)
    - NullMicBackend.available() always returns True
    - NullMicBackend.start_stream() is a no-op (callback is never called)
    - NullMicBackend.stop_stream() is a no-op
    - MicrophoneCapture.best_available() returns SoundDeviceMicBackend when sounddevice present
    - MicrophoneCapture.best_available() returns NullMicBackend when sounddevice absent
    - Frame format invariant: each callback receives exactly FRAME_BYTES (960) bytes
"""

from __future__ import annotations

import pytest

from heretic.rodd.microphone import (
    FRAME_BYTES,
    FRAME_MS,
    FRAME_SAMPLES,
    MicrophoneCapture,
    NullMicBackend,
    SAMPLE_RATE,
    SoundDeviceMicBackend,
)


# ---------------------------------------------------------------------------
# NullMicBackend — always available; no capture
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_null_mic_backend_always_available() -> None:
    """NullMicBackend.available() is always True regardless of platform."""
    assert NullMicBackend.available() is True


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_null_mic_start_stream_noop(caplog) -> None:
    """NullMicBackend.start_stream() does not invoke the callback."""
    import logging
    received: list[bytes] = []
    logger = logging.getLogger("test.null_mic")
    mic = NullMicBackend(device="default", logger=logger)
    mic.start_stream(callback=received.append)
    assert received == []


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_null_mic_stop_stream_noop() -> None:
    """NullMicBackend.stop_stream() does not raise even if stream was never started."""
    import logging
    logger = logging.getLogger("test.null_mic")
    mic = NullMicBackend(device="default", logger=logger)
    mic.stop_stream()  # must not raise


# ---------------------------------------------------------------------------
# Frame format constants
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_frame_format_constants_locked() -> None:
    """Frame format constants match the Architect's locked invariant."""
    assert SAMPLE_RATE == 16_000
    assert FRAME_MS == 30
    assert FRAME_SAMPLES == 480
    assert FRAME_BYTES == 960


# ---------------------------------------------------------------------------
# SoundDeviceMicBackend — probed by Forge with mocked sounddevice
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_sounddevice_mic_available_when_sounddevice_importable(monkeypatch) -> None:
    """SoundDeviceMicBackend.available() returns True when sounddevice is importable."""
    # Forge mocks sounddevice import and query_devices to simulate availability.
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_sounddevice_mic_available_false_when_import_fails(monkeypatch) -> None:
    """SoundDeviceMicBackend.available() returns False on ImportError."""
    # Forge patches importlib/builtins.__import__ to raise ImportError for sounddevice.
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_sounddevice_mic_start_pushes_frame_bytes(monkeypatch) -> None:
    """SoundDeviceMicBackend.start_stream() callback receives exactly FRAME_BYTES bytes."""
    # Forge mocks sounddevice.RawInputStream to invoke callback with synthetic frames.
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_sounddevice_mic_stop_stream_idempotent(monkeypatch) -> None:
    """SoundDeviceMicBackend.stop_stream() can be called twice without raising."""
    pass


# ---------------------------------------------------------------------------
# best_available() factory
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_best_available_returns_sounddevice_when_available(monkeypatch) -> None:
    """best_available() returns SoundDeviceMicBackend when sounddevice is present."""
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_best_available_returns_null_when_sounddevice_absent(monkeypatch) -> None:
    """best_available() returns NullMicBackend when sounddevice is absent."""
    pass
