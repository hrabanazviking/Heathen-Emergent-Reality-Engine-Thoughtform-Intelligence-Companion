"""
Tests — MicrophoneCapture backends (L2 Rödd Hlust substrate).

Tests use unittest.mock to avoid requiring real sounddevice installation.
All sounddevice interactions are patched at the module level.
"""

from __future__ import annotations

import logging
import sys
import types
from unittest.mock import MagicMock, patch, call

import pytest

from heretic.rodd.microphone import (
    CHANNELS,
    FRAME_BYTES,
    FRAME_MS,
    FRAME_SAMPLES,
    MicrophoneCapture,
    NullMicBackend,
    SAMPLE_RATE,
    SoundDeviceMicBackend,
)


# ---------------------------------------------------------------------------
# Frame format constants — locked invariant
# ---------------------------------------------------------------------------

def test_frame_format_constants_locked() -> None:
    """Frame format constants match the Architect's locked invariant."""
    assert SAMPLE_RATE == 16_000
    assert CHANNELS == 1
    assert FRAME_MS == 30
    assert FRAME_SAMPLES == 480
    assert FRAME_BYTES == 960


def test_frame_samples_derived_correctly() -> None:
    """FRAME_SAMPLES equals SAMPLE_RATE * FRAME_MS // 1000."""
    assert FRAME_SAMPLES == SAMPLE_RATE * FRAME_MS // 1000


def test_frame_bytes_is_two_bytes_per_sample() -> None:
    """FRAME_BYTES equals FRAME_SAMPLES * 2 (int16 = 2 bytes per sample)."""
    assert FRAME_BYTES == FRAME_SAMPLES * 2


# ---------------------------------------------------------------------------
# NullMicBackend — always available; no capture
# ---------------------------------------------------------------------------

def test_null_mic_backend_available_is_false() -> None:
    """NullMicBackend.available() returns False so factory doesn't auto-select it."""
    # NullMicBackend returns False from available() — best_available() appends it
    # as an explicit fallback, not via the available() probe.
    assert NullMicBackend.available() is False


def test_null_mic_start_stream_noop() -> None:
    """NullMicBackend.start_stream() does not invoke the callback."""
    received: list[bytes] = []
    logger = logging.getLogger("test.null_mic")
    mic = NullMicBackend(device="default", logger=logger)
    mic.start_stream(callback=received.append)
    assert received == []


def test_null_mic_stop_stream_noop() -> None:
    """NullMicBackend.stop_stream() does not raise even if stream was never started."""
    logger = logging.getLogger("test.null_mic")
    mic = NullMicBackend(device="default", logger=logger)
    mic.stop_stream()  # must not raise


def test_null_mic_stop_stream_after_start() -> None:
    """NullMicBackend.stop_stream() does not raise after start_stream()."""
    logger = logging.getLogger("test.null_mic")
    mic = NullMicBackend(device="default", logger=logger)
    mic.start_stream(callback=lambda _: None)
    mic.stop_stream()  # must not raise


def test_null_mic_is_instance_of_microphone_capture() -> None:
    """NullMicBackend is a valid MicrophoneCapture subclass."""
    logger = logging.getLogger("test.null_mic")
    mic = NullMicBackend(device="default", logger=logger)
    assert isinstance(mic, MicrophoneCapture)


# ---------------------------------------------------------------------------
# SoundDeviceMicBackend — probed with mocked sounddevice
# ---------------------------------------------------------------------------

def _make_mock_sounddevice(has_input_device: bool = True) -> types.ModuleType:
    """Build a minimal mock sounddevice module for testing."""
    sd_mock = MagicMock()
    if has_input_device:
        # A device list with one input device
        device_info = {"max_input_channels": 1, "name": "Mock Microphone"}
        sd_mock.query_devices.return_value = [device_info]
    else:
        # A device list with no input channels
        device_info = {"max_input_channels": 0, "name": "Mock Speaker"}
        sd_mock.query_devices.return_value = [device_info]
    return sd_mock


def test_sounddevice_mic_available_when_sounddevice_importable(monkeypatch) -> None:
    """SoundDeviceMicBackend.available() returns True when sounddevice is importable with input device."""
    sd_mock = _make_mock_sounddevice(has_input_device=True)
    # Patch sys.modules so 'import sounddevice' returns our mock
    monkeypatch.setitem(sys.modules, "sounddevice", sd_mock)
    assert SoundDeviceMicBackend.available() is True


def test_sounddevice_mic_available_false_when_import_fails(monkeypatch) -> None:
    """SoundDeviceMicBackend.available() returns False when sounddevice is not installed."""
    # Remove sounddevice from sys.modules to simulate ImportError
    monkeypatch.delitem(sys.modules, "sounddevice", raising=False)
    # Patch builtins __import__ via sys.modules manipulation:
    # the simplest approach is to set sys.modules['sounddevice'] to None,
    # which causes ImportError when imported.
    monkeypatch.setitem(sys.modules, "sounddevice", None)
    assert SoundDeviceMicBackend.available() is False


def test_sounddevice_mic_available_false_when_no_input_device(monkeypatch) -> None:
    """SoundDeviceMicBackend.available() returns False when no input device found."""
    sd_mock = _make_mock_sounddevice(has_input_device=False)
    monkeypatch.setitem(sys.modules, "sounddevice", sd_mock)
    assert SoundDeviceMicBackend.available() is False


def test_sounddevice_mic_available_false_when_query_raises(monkeypatch) -> None:
    """SoundDeviceMicBackend.available() returns False when query_devices() raises."""
    sd_mock = MagicMock()
    sd_mock.query_devices.side_effect = Exception("PortAudio error")
    monkeypatch.setitem(sys.modules, "sounddevice", sd_mock)
    assert SoundDeviceMicBackend.available() is False


def test_sounddevice_mic_start_stream_opens_raw_input_stream(monkeypatch) -> None:
    """SoundDeviceMicBackend.start_stream() opens RawInputStream with correct params."""
    sd_mock = _make_mock_sounddevice()
    mock_stream = MagicMock()
    sd_mock.RawInputStream.return_value = mock_stream
    monkeypatch.setitem(sys.modules, "sounddevice", sd_mock)

    logger = logging.getLogger("test.sd_mic")
    mic = SoundDeviceMicBackend(device="default", logger=logger)
    mic.start_stream(callback=lambda _: None)

    # Verify RawInputStream was constructed with correct parameters
    sd_mock.RawInputStream.assert_called_once()
    call_kwargs = sd_mock.RawInputStream.call_args.kwargs
    assert call_kwargs["samplerate"] == SAMPLE_RATE
    assert call_kwargs["blocksize"] == FRAME_SAMPLES
    assert call_kwargs["channels"] == CHANNELS
    assert call_kwargs["dtype"] == "int16"
    # device=None for 'default'
    assert call_kwargs["device"] is None
    # Stream should be started
    mock_stream.start.assert_called_once()


def test_sounddevice_mic_start_stream_named_device(monkeypatch) -> None:
    """SoundDeviceMicBackend passes named device to RawInputStream (not None)."""
    sd_mock = _make_mock_sounddevice()
    mock_stream = MagicMock()
    sd_mock.RawInputStream.return_value = mock_stream
    monkeypatch.setitem(sys.modules, "sounddevice", sd_mock)

    logger = logging.getLogger("test.sd_mic")
    mic = SoundDeviceMicBackend(device="Built-in Microphone", logger=logger)
    mic.start_stream(callback=lambda _: None)

    call_kwargs = sd_mock.RawInputStream.call_args.kwargs
    assert call_kwargs["device"] == "Built-in Microphone"


def test_sounddevice_mic_stop_stream_closes_cleanly(monkeypatch) -> None:
    """SoundDeviceMicBackend.stop_stream() calls stream.stop() then stream.close()."""
    sd_mock = _make_mock_sounddevice()
    mock_stream = MagicMock()
    sd_mock.RawInputStream.return_value = mock_stream
    monkeypatch.setitem(sys.modules, "sounddevice", sd_mock)

    logger = logging.getLogger("test.sd_mic")
    mic = SoundDeviceMicBackend(device="default", logger=logger)
    mic.start_stream(callback=lambda _: None)
    mic.stop_stream()

    mock_stream.stop.assert_called_once()
    mock_stream.close.assert_called_once()


def test_sounddevice_mic_stop_stream_idempotent(monkeypatch) -> None:
    """SoundDeviceMicBackend.stop_stream() can be called twice without raising."""
    sd_mock = _make_mock_sounddevice()
    mock_stream = MagicMock()
    sd_mock.RawInputStream.return_value = mock_stream
    monkeypatch.setitem(sys.modules, "sounddevice", sd_mock)

    logger = logging.getLogger("test.sd_mic")
    mic = SoundDeviceMicBackend(device="default", logger=logger)
    mic.start_stream(callback=lambda _: None)
    mic.stop_stream()
    mic.stop_stream()  # second call must not raise

    # stop/close called only once (stream set to None after first stop)
    mock_stream.stop.assert_called_once()
    mock_stream.close.assert_called_once()


def test_sounddevice_mic_stop_before_start_is_safe(monkeypatch) -> None:
    """SoundDeviceMicBackend.stop_stream() before start_stream() does not raise."""
    sd_mock = _make_mock_sounddevice()
    monkeypatch.setitem(sys.modules, "sounddevice", sd_mock)

    logger = logging.getLogger("test.sd_mic")
    mic = SoundDeviceMicBackend(device="default", logger=logger)
    mic.stop_stream()  # should be a no-op


def test_sounddevice_mic_callback_receives_frame_bytes(monkeypatch) -> None:
    """The sd callback adapter converts numpy-like buffer to bytes and forwards to user callback."""
    import asyncio

    sd_mock = _make_mock_sounddevice()
    captured_frames: list[bytes] = []
    captured_callback_ref: list = []

    # When RawInputStream is constructed, save the callback reference
    def _fake_raw_input_stream(**kwargs):
        captured_callback_ref.append(kwargs["callback"])
        stream_mock = MagicMock()
        return stream_mock

    sd_mock.RawInputStream.side_effect = _fake_raw_input_stream
    monkeypatch.setitem(sys.modules, "sounddevice", sd_mock)

    logger = logging.getLogger("test.sd_mic_cb")
    mic = SoundDeviceMicBackend(device="default", logger=logger)
    mic.start_stream(callback=captured_frames.append)

    # Simulate a PortAudio callback invocation with FRAME_BYTES of synthetic audio
    assert len(captured_callback_ref) == 1
    sd_callback = captured_callback_ref[0]

    # Create a bytearray-like object (simulating numpy array)
    fake_frame = bytearray(FRAME_BYTES)  # 960 bytes of silence
    sd_callback(fake_frame, FRAME_SAMPLES, None, None)

    assert len(captured_frames) == 1
    assert len(captured_frames[0]) == FRAME_BYTES


# ---------------------------------------------------------------------------
# best_available() factory
# ---------------------------------------------------------------------------

def test_best_available_returns_sounddevice_when_available(monkeypatch) -> None:
    """best_available() returns SoundDeviceMicBackend when sounddevice is present."""
    monkeypatch.setattr(SoundDeviceMicBackend, "available", classmethod(lambda cls: True))
    logger = logging.getLogger("test.best_available")
    mic = MicrophoneCapture.best_available("default", logger)
    assert isinstance(mic, SoundDeviceMicBackend)


def test_best_available_returns_null_when_sounddevice_absent(monkeypatch) -> None:
    """best_available() returns NullMicBackend when sounddevice is absent."""
    monkeypatch.setattr(SoundDeviceMicBackend, "available", classmethod(lambda cls: False))
    logger = logging.getLogger("test.best_available")
    mic = MicrophoneCapture.best_available("default", logger)
    assert isinstance(mic, NullMicBackend)


def test_best_available_never_raises(monkeypatch) -> None:
    """best_available() never raises regardless of what available() returns."""
    monkeypatch.setattr(SoundDeviceMicBackend, "available", classmethod(lambda cls: False))
    logger = logging.getLogger("test.best_available")
    # Must not raise
    mic = MicrophoneCapture.best_available("default", logger)
    assert mic is not None
