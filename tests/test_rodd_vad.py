"""
Tests — VadDetector backends (L2 Rödd Hlust substrate).

The vad_threshold -> aggressiveness mapping is a key invariant tested here.
webrtcvad is mocked throughout — no real C extension required.
"""

from __future__ import annotations

import logging
import math
import struct
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

from heretic.rodd.config_model import RoddSttConfig
from heretic.rodd.errors import VadError
from heretic.rodd.microphone import FRAME_BYTES, FRAME_MS
from heretic.rodd.vad import (
    EnergyThresholdBackend,
    NullVadBackend,
    VadDetector,
    WebRtcVadBackend,
    _SILENCE_FRAMES,
    _MIN_SPEECH_FRAMES,
    _NULL_VAD_WINDOW_FRAMES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _silence_frame() -> bytes:
    """Return a FRAME_BYTES block of silence (all-zero int16 samples)."""
    return b"\x00" * FRAME_BYTES


def _loud_frame() -> bytes:
    """Return a FRAME_BYTES block with high-amplitude int16 samples (speech-like)."""
    # 480 samples of int16 value 20000 (near max amplitude)
    return struct.pack("<480h", *(20000 for _ in range(480)))


def _make_mock_webrtcvad(is_speech_return: bool = True) -> types.ModuleType:
    """Build a minimal mock webrtcvad module."""
    wv_mock = MagicMock()
    vad_instance = MagicMock()
    vad_instance.is_speech.return_value = is_speech_return
    wv_mock.Vad.return_value = vad_instance
    return wv_mock


# ---------------------------------------------------------------------------
# NullVadBackend — fixed-window fallback
# ---------------------------------------------------------------------------

def test_null_vad_always_available() -> None:
    """NullVadBackend.available() is always True."""
    assert NullVadBackend.available() is True


def test_null_vad_is_speech_always_true() -> None:
    """NullVadBackend.is_speech() always returns True (assumes speech)."""
    config = RoddSttConfig()
    vad = NullVadBackend(config=config, logger=logging.getLogger("test.null_vad"))
    assert vad.is_speech(_silence_frame()) is True
    assert vad.is_speech(_loud_frame()) is True


def test_null_vad_utterance_complete_false_before_window() -> None:
    """NullVadBackend.utterance_complete() returns False before the 3-second window."""
    config = RoddSttConfig()
    vad = NullVadBackend(config=config, logger=logging.getLogger("test.null_vad"))
    # 50 frames = 50 * 30 ms = 1500 ms < 3000 ms window
    frames = [_silence_frame()] * 50
    assert vad.utterance_complete(frames) is False


def test_null_vad_utterance_complete_true_at_window() -> None:
    """NullVadBackend.utterance_complete() returns True once 3-second window reached."""
    config = RoddSttConfig()
    vad = NullVadBackend(config=config, logger=logging.getLogger("test.null_vad"))
    # _NULL_VAD_WINDOW_FRAMES = 3000 / 30 = 100 frames
    frames = [_silence_frame()] * _NULL_VAD_WINDOW_FRAMES
    assert vad.utterance_complete(frames) is True


def test_null_vad_reset_is_noop() -> None:
    """NullVadBackend.reset() does not raise."""
    config = RoddSttConfig()
    vad = NullVadBackend(config=config, logger=logging.getLogger("test.null_vad"))
    vad.reset()  # must not raise


def test_null_vad_is_instance_of_vad_detector() -> None:
    """NullVadBackend is a valid VadDetector subclass."""
    config = RoddSttConfig()
    vad = NullVadBackend(config=config, logger=logging.getLogger("test.null_vad"))
    assert isinstance(vad, VadDetector)


# ---------------------------------------------------------------------------
# EnergyThresholdBackend — pure-Python fallback
# ---------------------------------------------------------------------------

def test_energy_threshold_always_available() -> None:
    """EnergyThresholdBackend.available() is always True (no external deps)."""
    assert EnergyThresholdBackend.available() is True


def test_energy_threshold_is_speech_silent_frame_is_false() -> None:
    """EnergyThresholdBackend classifies a silent frame (all zeros) as non-speech."""
    config = RoddSttConfig()
    vad = EnergyThresholdBackend(config=config, logger=logging.getLogger("test.energy_vad"))
    assert vad.is_speech(_silence_frame()) is False


def test_energy_threshold_is_speech_loud_frame_is_true() -> None:
    """EnergyThresholdBackend classifies a high-amplitude frame as speech."""
    config = RoddSttConfig(vad_threshold=0.0)  # lowest threshold = most sensitive
    vad = EnergyThresholdBackend(config=config, logger=logging.getLogger("test.energy_vad"))
    # Loud frame has RMS ~20000, threshold at vad_threshold=0.0 is ~300
    assert vad.is_speech(_loud_frame()) is True


def test_energy_threshold_speech_updates_speech_seen() -> None:
    """EnergyThresholdBackend sets _speech_seen=True after detecting speech."""
    config = RoddSttConfig(vad_threshold=0.0)
    vad = EnergyThresholdBackend(config=config, logger=logging.getLogger("test.energy_vad"))
    assert vad._speech_seen is False
    vad.is_speech(_loud_frame())
    assert vad._speech_seen is True


def test_energy_threshold_silence_increments_silence_count() -> None:
    """EnergyThresholdBackend increments _silence_count for silent frames."""
    config = RoddSttConfig()
    vad = EnergyThresholdBackend(config=config, logger=logging.getLogger("test.energy_vad"))
    vad.is_speech(_silence_frame())
    assert vad._silence_count == 1
    vad.is_speech(_silence_frame())
    assert vad._silence_count == 2


def test_energy_threshold_speech_resets_silence_count() -> None:
    """EnergyThresholdBackend resets _silence_count to 0 when speech detected."""
    config = RoddSttConfig(vad_threshold=0.0)
    vad = EnergyThresholdBackend(config=config, logger=logging.getLogger("test.energy_vad"))
    vad.is_speech(_silence_frame())
    vad.is_speech(_silence_frame())
    assert vad._silence_count == 2
    vad.is_speech(_loud_frame())
    assert vad._silence_count == 0


def test_energy_threshold_utterance_complete_after_silence_run() -> None:
    """EnergyThresholdBackend.utterance_complete() returns True after speech + silence run."""
    config = RoddSttConfig(vad_threshold=0.0)
    vad = EnergyThresholdBackend(config=config, logger=logging.getLogger("test.energy_vad"))

    # Inject speech first
    for _ in range(5):
        vad.is_speech(_loud_frame())
    assert vad._speech_seen is True

    # Now inject _SILENCE_FRAMES frames of silence
    frames: list[bytes] = []
    for _ in range(_SILENCE_FRAMES):
        frames.append(_silence_frame())
        vad.is_speech(_silence_frame())

    assert vad.utterance_complete(frames) is True


def test_energy_threshold_utterance_not_complete_before_silence_run() -> None:
    """EnergyThresholdBackend.utterance_complete() returns False before silence threshold."""
    config = RoddSttConfig(vad_threshold=0.0)
    vad = EnergyThresholdBackend(config=config, logger=logging.getLogger("test.energy_vad"))

    vad.is_speech(_loud_frame())  # one speech frame
    # Only 5 silence frames — well below threshold
    frames: list[bytes] = []
    for _ in range(5):
        frames.append(_silence_frame())
        vad.is_speech(_silence_frame())

    assert vad.utterance_complete(frames) is False


def test_energy_threshold_utterance_not_complete_without_speech() -> None:
    """EnergyThresholdBackend.utterance_complete() returns False without prior speech."""
    config = RoddSttConfig()
    vad = EnergyThresholdBackend(config=config, logger=logging.getLogger("test.energy_vad"))
    # Lots of silence with no preceding speech
    frames: list[bytes] = []
    for _ in range(_SILENCE_FRAMES + 10):
        frames.append(_silence_frame())
        vad.is_speech(_silence_frame())
    assert vad.utterance_complete(frames) is False


def test_energy_threshold_reset_clears_state() -> None:
    """EnergyThresholdBackend.reset() resets speech_seen and silence_count."""
    config = RoddSttConfig(vad_threshold=0.0)
    vad = EnergyThresholdBackend(config=config, logger=logging.getLogger("test.energy_vad"))
    vad.is_speech(_loud_frame())
    vad.is_speech(_silence_frame())
    assert vad._speech_seen is True
    assert vad._silence_count == 1
    vad.reset()
    assert vad._speech_seen is False
    assert vad._silence_count == 0


# ---------------------------------------------------------------------------
# WebRtcVadBackend — vad_threshold -> aggressiveness mapping (CRITICAL)
# ---------------------------------------------------------------------------

def _make_webrtcvad_backend(vad_threshold: float) -> WebRtcVadBackend:
    """Helper to build WebRtcVadBackend with given threshold."""
    config = RoddSttConfig(vad_threshold=vad_threshold)
    return WebRtcVadBackend(config=config, logger=logging.getLogger("test.webrtcvad"))


@pytest.mark.parametrize("threshold,expected_aggressiveness", [
    (0.0, 0),   # 0.0 * 3 = 0.0 -> round -> 0
    (0.1, 0),   # 0.1 * 3 = 0.3 -> round -> 0
    (0.2, 1),   # 0.2 * 3 = 0.6 -> round -> 1
    (0.33, 1),  # 0.33 * 3 = 0.99 -> round -> 1
    (0.5, 2),   # 0.5 * 3 = 1.5 -> round -> 2
    (0.6, 2),   # 0.6 * 3 = 1.8 -> round -> 2 (default config value)
    (0.67, 2),  # 0.67 * 3 = 2.01 -> round -> 2
    (0.8, 2),   # 0.8 * 3 = 2.4 -> round -> 2
    (0.85, 3),  # 0.85 * 3 = 2.55 -> round -> 3
    (1.0, 3),   # 1.0 * 3 = 3.0 -> round -> 3
])
def test_webrtcvad_aggressiveness_mapping(
    monkeypatch,
    threshold: float,
    expected_aggressiveness: int,
) -> None:
    """Cartographer-flagged mapping: vad_threshold * 3 rounded and clamped to [0,3]."""
    wv_mock = _make_mock_webrtcvad()
    monkeypatch.setitem(sys.modules, "webrtcvad", wv_mock)

    backend = _make_webrtcvad_backend(threshold)
    # Force lazy init to fire by calling is_speech
    backend.is_speech(_silence_frame())

    # Verify the Vad was constructed and set_mode called with correct aggressiveness
    wv_mock.Vad.assert_called_once()
    vad_instance = wv_mock.Vad.return_value
    vad_instance.set_mode.assert_called_once_with(expected_aggressiveness)


def test_webrtcvad_available_when_importable(monkeypatch) -> None:
    """WebRtcVadBackend.available() returns True when webrtcvad is importable."""
    wv_mock = _make_mock_webrtcvad()
    monkeypatch.setitem(sys.modules, "webrtcvad", wv_mock)
    assert WebRtcVadBackend.available() is True


def test_webrtcvad_available_false_on_import_error(monkeypatch) -> None:
    """WebRtcVadBackend.available() returns False on ImportError."""
    monkeypatch.setitem(sys.modules, "webrtcvad", None)
    assert WebRtcVadBackend.available() is False


def test_webrtcvad_is_speech_delegates_to_vad(monkeypatch) -> None:
    """WebRtcVadBackend.is_speech() returns True when webrtcvad returns True."""
    wv_mock = _make_mock_webrtcvad(is_speech_return=True)
    monkeypatch.setitem(sys.modules, "webrtcvad", wv_mock)

    backend = _make_webrtcvad_backend(0.6)
    result = backend.is_speech(_loud_frame())
    assert result is True


def test_webrtcvad_is_speech_returns_false_for_silence(monkeypatch) -> None:
    """WebRtcVadBackend.is_speech() returns False when webrtcvad returns False."""
    wv_mock = _make_mock_webrtcvad(is_speech_return=False)
    monkeypatch.setitem(sys.modules, "webrtcvad", wv_mock)

    backend = _make_webrtcvad_backend(0.6)
    result = backend.is_speech(_silence_frame())
    assert result is False


def test_webrtcvad_is_speech_bad_frame_raises_vad_error(monkeypatch) -> None:
    """WebRtcVadBackend.is_speech() raises VadError on wrong-length frame."""
    wv_mock = _make_mock_webrtcvad()
    monkeypatch.setitem(sys.modules, "webrtcvad", wv_mock)

    backend = _make_webrtcvad_backend(0.6)
    with pytest.raises(VadError, match="expected.*bytes"):
        backend.is_speech(b"\x00" * 100)  # Wrong length (100 bytes, not 960)


def test_webrtcvad_is_speech_passes_correct_sample_rate(monkeypatch) -> None:
    """WebRtcVadBackend.is_speech() calls vad.is_speech(frame, 16000)."""
    wv_mock = _make_mock_webrtcvad()
    monkeypatch.setitem(sys.modules, "webrtcvad", wv_mock)

    backend = _make_webrtcvad_backend(0.6)
    backend.is_speech(_loud_frame())

    vad_instance = wv_mock.Vad.return_value
    call_args = vad_instance.is_speech.call_args
    assert call_args.args[1] == 16_000


def test_webrtcvad_utterance_complete_after_silence_run(monkeypatch) -> None:
    """WebRtcVadBackend.utterance_complete() returns True after speech + silence run."""
    wv_mock = _make_mock_webrtcvad()
    monkeypatch.setitem(sys.modules, "webrtcvad", wv_mock)

    backend = _make_webrtcvad_backend(0.6)

    # Force _MIN_SPEECH_FRAMES of speech
    wv_mock.Vad.return_value.is_speech.return_value = True
    for _ in range(_MIN_SPEECH_FRAMES):
        backend.is_speech(_loud_frame())

    # Force _SILENCE_FRAMES of silence
    wv_mock.Vad.return_value.is_speech.return_value = False
    frames: list[bytes] = []
    for _ in range(_SILENCE_FRAMES):
        frames.append(_silence_frame())
        backend.is_speech(_silence_frame())

    assert backend.utterance_complete(frames) is True


def test_webrtcvad_utterance_not_complete_mid_utterance(monkeypatch) -> None:
    """WebRtcVadBackend.utterance_complete() returns False while speech is ongoing."""
    wv_mock = _make_mock_webrtcvad(is_speech_return=True)
    monkeypatch.setitem(sys.modules, "webrtcvad", wv_mock)

    backend = _make_webrtcvad_backend(0.6)
    frames: list[bytes] = []
    for _ in range(10):
        frames.append(_loud_frame())
        backend.is_speech(_loud_frame())

    assert backend.utterance_complete(frames) is False


def test_webrtcvad_reset_clears_state(monkeypatch) -> None:
    """WebRtcVadBackend.reset() resets speech and silence frame counters."""
    wv_mock = _make_mock_webrtcvad(is_speech_return=True)
    monkeypatch.setitem(sys.modules, "webrtcvad", wv_mock)

    backend = _make_webrtcvad_backend(0.6)
    for _ in range(5):
        backend.is_speech(_loud_frame())
    assert backend._speech_frames == 5

    backend.reset()
    assert backend._speech_frames == 0
    assert backend._silence_frames == 0


def test_webrtcvad_lazy_init(monkeypatch) -> None:
    """WebRtcVadBackend does not create the Vad instance until is_speech() is called."""
    wv_mock = _make_mock_webrtcvad()
    monkeypatch.setitem(sys.modules, "webrtcvad", wv_mock)

    backend = _make_webrtcvad_backend(0.6)
    # No call yet
    wv_mock.Vad.assert_not_called()
    # Now call is_speech to trigger lazy init
    backend.is_speech(_loud_frame())
    wv_mock.Vad.assert_called_once()


# ---------------------------------------------------------------------------
# best_available() factory
# ---------------------------------------------------------------------------

def test_vad_best_available_prefers_webrtcvad(monkeypatch) -> None:
    """best_available() returns WebRtcVadBackend when webrtcvad is present."""
    monkeypatch.setattr(WebRtcVadBackend, "available", classmethod(lambda cls: True))
    config = RoddSttConfig()
    logger = logging.getLogger("test.vad_factory")
    vad = VadDetector.best_available(config, logger)
    assert isinstance(vad, WebRtcVadBackend)


def test_vad_best_available_falls_back_to_energy(monkeypatch) -> None:
    """best_available() returns EnergyThresholdBackend when webrtcvad absent."""
    monkeypatch.setattr(WebRtcVadBackend, "available", classmethod(lambda cls: False))
    config = RoddSttConfig()
    logger = logging.getLogger("test.vad_factory")
    vad = VadDetector.best_available(config, logger)
    assert isinstance(vad, EnergyThresholdBackend)


def test_vad_best_available_never_raises(monkeypatch) -> None:
    """best_available() never raises regardless of backend availability."""
    monkeypatch.setattr(WebRtcVadBackend, "available", classmethod(lambda cls: False))
    monkeypatch.setattr(EnergyThresholdBackend, "available", classmethod(lambda cls: False))
    config = RoddSttConfig()
    logger = logging.getLogger("test.vad_factory")
    vad = VadDetector.best_available(config, logger)
    assert vad is not None
    assert isinstance(vad, NullVadBackend)
