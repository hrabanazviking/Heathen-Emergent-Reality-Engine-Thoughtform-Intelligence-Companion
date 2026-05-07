"""
Tests — heretic.rodd.playback (AudioPlayback backends).

All sounddevice and subprocess calls are mocked — no real speakers required.
Tests verify the backend selection chain, availability checks, WAV parsing,
platform dispatch, temp-file cleanup, and the NullPlaybackBackend no-op.
"""

from __future__ import annotations

import io
import struct
import wave
from unittest.mock import MagicMock, patch

import pytest

from heretic.rodd.config_model import RoddTtsConfig
from heretic.rodd.errors import PlaybackBackendUnavailableError, PlaybackError
from heretic.rodd.playback import (
    AudioPlayback,
    NullPlaybackBackend,
    PlatformFallbackBackend,
    SoundDeviceBackend,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(**kwargs) -> RoddTtsConfig:
    defaults = {"endpoint": "http://test:7851", "device": "default"}
    defaults.update(kwargs)
    return RoddTtsConfig(**defaults)


def _make_logger():
    import logging
    log = logging.getLogger("test.rodd.playback")
    log.setLevel(logging.CRITICAL)
    return log


def _make_wav_bytes() -> bytes:
    """Build a minimal valid 0.1s silent WAV file."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        n = 2205
        wf.writeframes(struct.pack(f"<{n}h", *([0] * n)))
    return buf.getvalue()


# ---------------------------------------------------------------------------
# AudioPlayback.best_available() factory
# ---------------------------------------------------------------------------

def test_best_available_returns_sounddevice_backend_when_importable() -> None:
    """best_available() returns SoundDeviceBackend when sounddevice can be imported."""
    config = _make_config()
    logger = _make_logger()
    with patch.object(SoundDeviceBackend, "available", return_value=True):
        backend = AudioPlayback.best_available(config, logger)
    assert isinstance(backend, SoundDeviceBackend)


def test_best_available_returns_fallback_when_sounddevice_unavailable() -> None:
    """best_available() returns PlatformFallbackBackend when sounddevice is unavailable."""
    config = _make_config()
    logger = _make_logger()
    with patch.object(SoundDeviceBackend, "available", return_value=False), \
         patch.object(PlatformFallbackBackend, "available", return_value=True):
        backend = AudioPlayback.best_available(config, logger)
    assert isinstance(backend, PlatformFallbackBackend)


def test_best_available_returns_null_when_no_backend_available() -> None:
    """best_available() returns NullPlaybackBackend when no backend is available."""
    config = _make_config()
    logger = _make_logger()
    with patch.object(SoundDeviceBackend, "available", return_value=False), \
         patch.object(PlatformFallbackBackend, "available", return_value=False):
        backend = AudioPlayback.best_available(config, logger)
    assert isinstance(backend, NullPlaybackBackend)


# ---------------------------------------------------------------------------
# SoundDeviceBackend.available()
# ---------------------------------------------------------------------------

def test_sounddevice_available_true_when_device_found() -> None:
    """SoundDeviceBackend.available() returns True when sounddevice and device are present."""
    config = _make_config(device="default")
    logger = _make_logger()
    backend = SoundDeviceBackend(config, logger)

    mock_sd = MagicMock()
    mock_sd.query_devices = MagicMock(return_value={"name": "Default", "max_output_channels": 2})
    with patch.dict("sys.modules", {"sounddevice": mock_sd}):
        result = backend.available()
    assert result is True


def test_sounddevice_available_false_when_import_fails() -> None:
    """SoundDeviceBackend.available() returns False when sounddevice raises ImportError."""
    config = _make_config()
    logger = _make_logger()
    backend = SoundDeviceBackend(config, logger)

    with patch("builtins.__import__", side_effect=lambda name, *a, **k: (_ for _ in ()).throw(ImportError("no sounddevice")) if name == "sounddevice" else __import__(name, *a, **k)):
        result = backend.available()
    assert result is False


def test_sounddevice_available_false_when_device_missing() -> None:
    """SoundDeviceBackend.available() returns False when device query raises."""
    config = _make_config(device="nonexistent_device")
    logger = _make_logger()
    backend = SoundDeviceBackend(config, logger)

    mock_sd = MagicMock()
    mock_sd.query_devices = MagicMock(side_effect=Exception("No such device"))
    with patch.dict("sys.modules", {"sounddevice": mock_sd}):
        result = backend.available()
    assert result is False


def test_sounddevice_available_never_raises() -> None:
    """SoundDeviceBackend.available() returns False (not raises) on any exception."""
    config = _make_config()
    logger = _make_logger()
    backend = SoundDeviceBackend(config, logger)

    with patch.dict("sys.modules", {"sounddevice": None}):
        # sys.modules with None entry causes AttributeError on attribute access
        try:
            result = backend.available()
            assert result is False
        except Exception as exc:
            pytest.fail(f"available() raised unexpectedly: {exc}")


# ---------------------------------------------------------------------------
# SoundDeviceBackend.play()
# ---------------------------------------------------------------------------

def test_sounddevice_play_calls_sounddevice_play() -> None:
    """SoundDeviceBackend.play() calls sounddevice.play with correct samplerate."""
    config = _make_config(device="default")
    logger = _make_logger()
    backend = SoundDeviceBackend(config, logger)
    wav_bytes = _make_wav_bytes()

    mock_sd = MagicMock()
    mock_np = MagicMock()
    # Simulate numpy frombuffer returning a mock array
    mock_array = MagicMock()
    mock_np.frombuffer = MagicMock(return_value=mock_array)
    mock_np.int16 = "int16"
    mock_np.int32 = "int32"
    mock_np.int8 = "int8"

    with patch.dict("sys.modules", {"sounddevice": mock_sd, "numpy": mock_np}):
        backend.play(wav_bytes)

    mock_sd.play.assert_called_once()
    call_kwargs = mock_sd.play.call_args
    # Verify samplerate was passed — 22050 is what _make_wav_bytes() sets
    assert call_kwargs.kwargs.get("samplerate") == 22050 or (
        len(call_kwargs.args) >= 2 and call_kwargs.args[1] == 22050
    )


def test_sounddevice_play_raises_playback_error_on_portaudio_error() -> None:
    """SoundDeviceBackend.play() raises PlaybackError on sounddevice.PortAudioError."""
    config = _make_config()
    logger = _make_logger()
    backend = SoundDeviceBackend(config, logger)
    wav_bytes = _make_wav_bytes()

    mock_sd = MagicMock()
    mock_sd.PortAudioError = Exception  # make PortAudioError catch as generic Exception
    mock_sd.play = MagicMock(side_effect=mock_sd.PortAudioError("device error"))
    mock_np = MagicMock()
    mock_array = MagicMock()
    mock_np.frombuffer = MagicMock(return_value=mock_array)
    mock_np.int16 = "int16"
    mock_np.int32 = "int32"
    mock_np.int8 = "int8"

    with patch.dict("sys.modules", {"sounddevice": mock_sd, "numpy": mock_np}):
        with pytest.raises(PlaybackError):
            backend.play(wav_bytes)


def test_sounddevice_close_calls_stop() -> None:
    """SoundDeviceBackend.close() calls sounddevice.stop()."""
    config = _make_config()
    logger = _make_logger()
    backend = SoundDeviceBackend(config, logger)

    mock_sd = MagicMock()
    with patch.dict("sys.modules", {"sounddevice": mock_sd}):
        backend.close()

    mock_sd.stop.assert_called_once()


# ---------------------------------------------------------------------------
# PlatformFallbackBackend.available()
# ---------------------------------------------------------------------------

def test_fallback_available_on_windows() -> None:
    """PlatformFallbackBackend.available() returns True on Windows when winsound importable."""
    config = _make_config()
    logger = _make_logger()

    mock_winsound = MagicMock()
    with patch.object(PlatformFallbackBackend, "_PLATFORM", "Windows"), \
         patch.dict("sys.modules", {"winsound": mock_winsound}):
        backend = PlatformFallbackBackend(config, logger)
        result = backend.available()
    assert result is True


def test_fallback_available_on_linux() -> None:
    """PlatformFallbackBackend.available() returns True on Linux when aplay is on PATH."""
    config = _make_config()
    logger = _make_logger()

    with patch.object(PlatformFallbackBackend, "_PLATFORM", "Linux"), \
         patch("shutil.which", side_effect=lambda cmd: "/usr/bin/aplay" if cmd == "aplay" else None):
        backend = PlatformFallbackBackend(config, logger)
        result = backend.available()
    assert result is True


def test_fallback_available_on_macos() -> None:
    """PlatformFallbackBackend.available() returns True on macOS when afplay is on PATH."""
    config = _make_config()
    logger = _make_logger()

    with patch.object(PlatformFallbackBackend, "_PLATFORM", "Darwin"), \
         patch("shutil.which", return_value="/usr/bin/afplay"):
        backend = PlatformFallbackBackend(config, logger)
        result = backend.available()
    assert result is True


def test_fallback_available_false_on_unknown_platform() -> None:
    """PlatformFallbackBackend.available() returns False on unsupported platforms."""
    config = _make_config()
    logger = _make_logger()

    with patch.object(PlatformFallbackBackend, "_PLATFORM", "FreeBSD"):
        backend = PlatformFallbackBackend(config, logger)
        result = backend.available()
    assert result is False


# ---------------------------------------------------------------------------
# PlatformFallbackBackend.play()
# ---------------------------------------------------------------------------

def test_fallback_play_creates_and_removes_temp_file_on_linux() -> None:
    """PlatformFallbackBackend.play() writes a temp file and deletes it after playback."""
    config = _make_config()
    logger = _make_logger()
    wav_bytes = _make_wav_bytes()

    created_paths: list[str] = []
    deleted_paths: list[str] = []

    class _FakeTempFile:
        name = "/tmp/fake_test.wav"
        def write(self, data): pass
        def __enter__(self): return self
        def __exit__(self, *a): pass

    import subprocess as _subprocess

    with patch.object(PlatformFallbackBackend, "_PLATFORM", "Linux"), \
         patch("shutil.which", return_value="/usr/bin/aplay"), \
         patch("tempfile.NamedTemporaryFile", return_value=_FakeTempFile()), \
         patch("os.path.exists", return_value=True), \
         patch("os.unlink") as mock_unlink, \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = _subprocess.CompletedProcess(args=[], returncode=0)
        backend = PlatformFallbackBackend(config, logger)
        backend.play(wav_bytes)

    mock_unlink.assert_called_once()


def test_fallback_play_removes_temp_file_on_failure() -> None:
    """PlatformFallbackBackend.play() removes the temp file even when the command fails."""
    import subprocess as _subprocess
    config = _make_config()
    logger = _make_logger()
    wav_bytes = _make_wav_bytes()

    class _FakeTempFile:
        name = "/tmp/fake_test_fail.wav"
        def write(self, data): pass
        def __enter__(self): return self
        def __exit__(self, *a): pass

    with patch.object(PlatformFallbackBackend, "_PLATFORM", "Linux"), \
         patch("shutil.which", return_value="/usr/bin/aplay"), \
         patch("tempfile.NamedTemporaryFile", return_value=_FakeTempFile()), \
         patch("os.path.exists", return_value=True), \
         patch("os.unlink") as mock_unlink, \
         patch("subprocess.run", side_effect=_subprocess.CalledProcessError(1, "aplay", stderr=b"fail")):
        backend = PlatformFallbackBackend(config, logger)
        with pytest.raises(PlaybackError):
            backend.play(wav_bytes)

    # Temp file must be removed even on failure
    mock_unlink.assert_called_once()


def test_fallback_play_raises_playback_error_on_subprocess_failure() -> None:
    """PlatformFallbackBackend.play() raises PlaybackError on CalledProcessError."""
    import subprocess as _subprocess
    config = _make_config()
    logger = _make_logger()
    wav_bytes = _make_wav_bytes()

    class _FakeTempFile:
        name = "/tmp/test_sub_fail.wav"
        def write(self, data): pass
        def __enter__(self): return self
        def __exit__(self, *a): pass

    with patch.object(PlatformFallbackBackend, "_PLATFORM", "Darwin"), \
         patch("shutil.which", return_value="/usr/bin/afplay"), \
         patch("tempfile.NamedTemporaryFile", return_value=_FakeTempFile()), \
         patch("os.path.exists", return_value=True), \
         patch("os.unlink"), \
         patch("subprocess.run", side_effect=_subprocess.CalledProcessError(1, "afplay", stderr=b"err")):
        backend = PlatformFallbackBackend(config, logger)
        with pytest.raises(PlaybackError):
            backend.play(wav_bytes)


def test_fallback_close_does_not_raise() -> None:
    """PlatformFallbackBackend.close() completes without raising."""
    config = _make_config()
    logger = _make_logger()
    backend = PlatformFallbackBackend(config, logger)
    backend.close()  # Should not raise
    assert backend._closed is True


# ---------------------------------------------------------------------------
# NullPlaybackBackend
# ---------------------------------------------------------------------------

def test_null_backend_available_returns_false() -> None:
    """NullPlaybackBackend.available() always returns False."""
    config = _make_config()
    logger = _make_logger()
    backend = NullPlaybackBackend(config, logger)
    assert backend.available() is False


def test_null_backend_play_does_not_raise() -> None:
    """NullPlaybackBackend.play() does not raise — it silently discards audio."""
    config = _make_config()
    logger = _make_logger()
    backend = NullPlaybackBackend(config, logger)
    wav_bytes = _make_wav_bytes()
    backend.play(wav_bytes)  # Should not raise


def test_null_backend_close_does_not_raise() -> None:
    """NullPlaybackBackend.close() completes without raising."""
    config = _make_config()
    logger = _make_logger()
    backend = NullPlaybackBackend(config, logger)
    backend.close()
    assert backend._closed is True
