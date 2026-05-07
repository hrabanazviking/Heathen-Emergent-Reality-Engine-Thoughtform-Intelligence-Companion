"""
Placeholder tests — VadDetector backends (L2 Rödd Hlust substrate).

All tests are skip-marked. Forge implements these in v0.3 Wave 2.

Coverage targets (Forge):
    - WebRtcVadBackend.available() returns True when webrtcvad importable
    - WebRtcVadBackend.available() returns False on ImportError (mocked)
    - WebRtcVadBackend.is_speech() returns True on a synthetic speech frame
    - WebRtcVadBackend.is_speech() returns False on a silent frame
    - WebRtcVadBackend.is_speech() raises VadError on wrong-length frame
    - WebRtcVadBackend.utterance_complete() returns False mid-utterance
    - WebRtcVadBackend.utterance_complete() returns True after sufficient silence
    - WebRtcVadBackend.reset() clears per-utterance state
    - EnergyThresholdBackend.available() is always True
    - EnergyThresholdBackend.is_speech() classifies by RMS energy
    - EnergyThresholdBackend.utterance_complete() triggers after silence threshold
    - EnergyThresholdBackend.reset() clears speech_seen and silence_count
    - NullVadBackend.available() is always True
    - NullVadBackend.is_speech() always returns False
    - NullVadBackend.utterance_complete() always returns False
    - VadDetector.best_available() preference order: webrtcvad > energy > null
"""

from __future__ import annotations

import pytest

from heretic.rodd.config_model import RoddSttConfig
from heretic.rodd.vad import (
    EnergyThresholdBackend,
    NullVadBackend,
    VadDetector,
    WebRtcVadBackend,
)
from heretic.rodd.microphone import FRAME_BYTES


# ---------------------------------------------------------------------------
# NullVadBackend — silent fallback
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_null_vad_always_available() -> None:
    """NullVadBackend.available() is always True."""
    assert NullVadBackend.available() is True


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_null_vad_is_speech_always_false() -> None:
    """NullVadBackend.is_speech() always returns False regardless of frame content."""
    import logging
    config = RoddSttConfig()
    vad = NullVadBackend(config=config, logger=logging.getLogger("test.null_vad"))
    silence = b"\x00" * FRAME_BYTES
    assert vad.is_speech(silence) is False


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_null_vad_utterance_complete_always_false() -> None:
    """NullVadBackend.utterance_complete() always returns False."""
    import logging
    config = RoddSttConfig()
    vad = NullVadBackend(config=config, logger=logging.getLogger("test.null_vad"))
    frames = [b"\x00" * FRAME_BYTES] * 30
    assert vad.utterance_complete(frames) is False


# ---------------------------------------------------------------------------
# EnergyThresholdBackend — pure-Python fallback
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_energy_threshold_always_available() -> None:
    """EnergyThresholdBackend.available() is always True (no external deps)."""
    assert EnergyThresholdBackend.available() is True


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_energy_threshold_is_speech_silent_frame() -> None:
    """EnergyThresholdBackend classifies a silent frame (all zeros) as non-speech."""
    import logging
    config = RoddSttConfig()
    vad = EnergyThresholdBackend(config=config, logger=logging.getLogger("test.energy_vad"))
    silence = b"\x00" * FRAME_BYTES
    assert vad.is_speech(silence) is False


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_energy_threshold_is_speech_loud_frame() -> None:
    """EnergyThresholdBackend classifies a high-amplitude frame as speech."""
    # Forge synthesises a frame with high-amplitude int16 values.
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_energy_threshold_utterance_complete_after_silence() -> None:
    """EnergyThresholdBackend.utterance_complete() returns True after speech + silence run."""
    # Forge constructs a frame sequence: N speech frames then 25 silence frames.
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_energy_threshold_reset_clears_state() -> None:
    """EnergyThresholdBackend.reset() resets speech_seen and silence_count."""
    import logging
    config = RoddSttConfig()
    vad = EnergyThresholdBackend(config=config, logger=logging.getLogger("test.energy_vad"))
    # After any classification:
    vad.reset()
    assert vad._speech_seen is False
    assert vad._silence_count == 0


# ---------------------------------------------------------------------------
# WebRtcVadBackend — probed by Forge with mocked webrtcvad
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_webrtcvad_available_when_importable(monkeypatch) -> None:
    """WebRtcVadBackend.available() returns True when webrtcvad is importable."""
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_webrtcvad_available_false_on_import_error(monkeypatch) -> None:
    """WebRtcVadBackend.available() returns False on ImportError."""
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_webrtcvad_is_speech_bad_frame_raises_vad_error() -> None:
    """WebRtcVadBackend.is_speech() raises VadError on a frame with wrong byte length."""
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_webrtcvad_utterance_complete_after_silence_run(monkeypatch) -> None:
    """WebRtcVadBackend.utterance_complete() triggers after ~600 ms of silence."""
    pass


# ---------------------------------------------------------------------------
# best_available() factory
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_vad_best_available_prefers_webrtcvad(monkeypatch) -> None:
    """best_available() returns WebRtcVadBackend when webrtcvad is present."""
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_vad_best_available_falls_back_to_energy(monkeypatch) -> None:
    """best_available() returns EnergyThresholdBackend when webrtcvad absent."""
    pass
