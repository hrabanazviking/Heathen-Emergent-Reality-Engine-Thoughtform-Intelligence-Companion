"""
Placeholder tests — Hlust orchestrator (L2 Rödd STT).

All tests are skip-marked. Forge implements these in v0.3 Wave 2.

Coverage targets (Forge):
    - Hlust.__init__() marks unavailable when any Null backend is injected
    - Hlust.__init__() marks available when all three backends are real (mocked)
    - Hlust.is_available is False for NullMic
    - Hlust.is_available is False for NullVad
    - Hlust.is_available is False for NullWhisper
    - Hlust.is_available is True when all three backends are real
    - Hlust.capture_one_utterance() raises HlustConfigError when unavailable
    - Hlust.capture_one_utterance() raises HlustConfigError when closed
    - Hlust.capture_one_utterance() lazy-loads model on first call
    - Hlust.capture_one_utterance() returns transcript from mocked Whisper
    - Hlust.capture_one_utterance() stops mic stream on completion
    - Hlust.capture_one_utterance() stops mic stream on VAD timeout
    - Hlust.close() is idempotent
    - Hlust.open() with eager strategy calls engine.load_model()
    - Hlust.open() with lazy strategy does NOT call engine.load_model()
    - Full orchestration flow: mic frames -> VAD gate -> Whisper -> text (mocked)
"""

from __future__ import annotations

import logging

import pytest

from heretic.rodd.config_model import RoddConfig, RoddSttConfig
from heretic.rodd.errors import HlustConfigError
from heretic.rodd.hlust import Hlust
from heretic.rodd.microphone import NullMicBackend
from heretic.rodd.vad import NullVadBackend
from heretic.rodd.whisper_engine import NullWhisperBackend


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_null_hlust(config: RoddConfig | None = None) -> Hlust:
    """Return a Hlust instance with all Null backends (unavailable state)."""
    cfg = config or RoddConfig()
    log = logging.getLogger("test.hlust")
    mic = NullMicBackend(device="default", logger=log)
    vad = NullVadBackend(config=cfg.stt, logger=log)
    engine = NullWhisperBackend(config=cfg.stt, logger=log)
    return Hlust(config=cfg, mic=mic, vad=vad, engine=engine, logger=log)


# ---------------------------------------------------------------------------
# Availability detection
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_hlust_unavailable_with_null_mic() -> None:
    """Hlust is unavailable when mic is NullMicBackend."""
    hlust = _make_null_hlust()
    assert hlust.is_available is False


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_hlust_unavailable_with_null_vad() -> None:
    """Hlust is unavailable when VAD is NullVadBackend."""
    # Forge injects a real mock mic but keeps NullVadBackend.
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_hlust_unavailable_with_null_whisper() -> None:
    """Hlust is unavailable when engine is NullWhisperBackend."""
    # Forge injects real mock mic and vad but keeps NullWhisperBackend.
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
def test_hlust_available_with_all_real_backends(mocker) -> None:
    """Hlust is available when all three backends are real (non-Null) mocks."""
    pass


# ---------------------------------------------------------------------------
# capture_one_utterance() guard conditions
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
async def test_capture_raises_when_unavailable() -> None:
    """capture_one_utterance() raises HlustConfigError when Hlust is unavailable."""
    hlust = _make_null_hlust()
    with pytest.raises(HlustConfigError):
        await hlust.capture_one_utterance()


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
async def test_capture_raises_when_closed(mocker) -> None:
    """capture_one_utterance() raises HlustConfigError after close() is called."""
    pass


# ---------------------------------------------------------------------------
# Lazy model loading
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
async def test_capture_triggers_lazy_model_load(mocker) -> None:
    """capture_one_utterance() calls engine.load_model() on first invocation."""
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
async def test_open_eager_calls_load_model(mocker) -> None:
    """Hlust.open() calls engine.load_model() when load_strategy is 'eager'."""
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
async def test_open_lazy_does_not_call_load_model(mocker) -> None:
    """Hlust.open() does NOT call engine.load_model() when load_strategy is 'lazy'."""
    pass


# ---------------------------------------------------------------------------
# Close
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
async def test_close_idempotent() -> None:
    """Hlust.close() can be called multiple times without raising."""
    pass


# ---------------------------------------------------------------------------
# Full orchestration flow (mocked)
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
async def test_capture_one_utterance_returns_transcript(mocker) -> None:
    """Full capture flow: mic frames + VAD gate -> Whisper -> stripped text returned."""
    # Forge injects mocked mic (pushes synthetic frames), mocked VAD (signals
    # utterance complete after N frames), mocked Whisper (returns "hello world").
    # Assert capture_one_utterance() returns "hello world".
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
async def test_capture_stops_mic_on_completion(mocker) -> None:
    """Mic stream is stopped after utterance completion."""
    pass


@pytest.mark.skip(reason="Forge implements in v0.3 Wave 2")
async def test_capture_stops_mic_on_vad_timeout(mocker) -> None:
    """Mic stream is stopped when _MAX_UTTERANCE_FRAMES is reached without VAD completion."""
    pass
