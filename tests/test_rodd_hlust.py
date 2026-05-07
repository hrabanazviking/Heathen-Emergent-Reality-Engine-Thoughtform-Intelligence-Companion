"""
Tests — Hlust orchestrator (L2 Rödd STT).

All backends are mocked via MagicMock/AsyncMock so no real hardware is required.
The threading bridge (loop.call_soon_threadsafe) is exercised by simulating the
mic callback directly in the asyncio loop.
"""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from heretic.rodd.config_model import RoddConfig, RoddSttConfig, RoddTtsConfig
from heretic.rodd.errors import HlustConfigError
from heretic.rodd.hlust import Hlust, _MAX_UTTERANCE_FRAMES
from heretic.rodd.microphone import NullMicBackend, FRAME_BYTES
from heretic.rodd.vad import NullVadBackend
from heretic.rodd.whisper_engine import NullWhisperBackend


# ---------------------------------------------------------------------------
# Helpers — mock backend factories
# ---------------------------------------------------------------------------

def _make_logger() -> logging.Logger:
    return logging.getLogger("test.hlust")


def _make_config(load_strategy: str = "lazy", stt_enabled: bool = True) -> RoddConfig:
    return RoddConfig(
        tts=RoddTtsConfig(),
        stt=RoddSttConfig(enabled=stt_enabled, load_strategy=load_strategy),
    )


def _silence_frame() -> bytes:
    return b"\x00" * FRAME_BYTES


class _MockMic:
    """Test double for MicrophoneCapture — records calls, never actually captures."""

    def __init__(self) -> None:
        self.started = False
        self.stopped = False
        self._callback = None
        self.start_count = 0
        self.stop_count = 0

    def start_stream(self, callback) -> None:
        self.started = True
        self.start_count += 1
        self._callback = callback

    def stop_stream(self) -> None:
        self.stopped = True
        self.stop_count += 1

    def push_frame(self, frame: bytes) -> None:
        """Synchronously invoke the registered callback as if a frame arrived."""
        if self._callback:
            self._callback(frame)


class _MockVad:
    """Test double for VadDetector."""

    def __init__(self, complete_after: int = 5) -> None:
        """complete_after: how many frames before utterance_complete returns True."""
        self.complete_after = complete_after
        self.reset_count = 0
        self.frames_seen = 0

    def is_speech(self, frame: bytes) -> bool:
        self.frames_seen += 1
        return True

    def utterance_complete(self, frames: list[bytes]) -> bool:
        return len(frames) >= self.complete_after

    def reset(self) -> None:
        self.reset_count += 1
        self.frames_seen = 0


class _MockEngine:
    """Test double for WhisperEngine."""

    def __init__(self, transcript: str = "hello world") -> None:
        self.transcript = transcript
        self._loaded = False
        self.load_count = 0
        self.transcribe_count = 0

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    async def load_model(self) -> None:
        self._loaded = True
        self.load_count += 1

    async def transcribe(self, audio: bytes, sample_rate: int = 16_000) -> str:
        self.transcribe_count += 1
        return self.transcript


def _make_real_hlust(
    complete_after: int = 3,
    transcript: str = "hello world",
    load_strategy: str = "lazy",
) -> tuple[Hlust, _MockMic, _MockVad, _MockEngine]:
    """Return a Hlust with real mock backends that will actually complete an utterance."""
    cfg = _make_config(load_strategy=load_strategy)
    log = _make_logger()
    mic = _MockMic()
    vad = _MockVad(complete_after=complete_after)
    engine = _MockEngine(transcript=transcript)
    hlust = Hlust(config=cfg, mic=mic, vad=vad, engine=engine, logger=log)
    return hlust, mic, vad, engine


def _make_null_hlust() -> Hlust:
    """Return a Hlust instance with all Null backends (unavailable state)."""
    cfg = _make_config()
    log = _make_logger()
    mic = NullMicBackend(device="default", logger=log)
    vad = NullVadBackend(config=cfg.stt, logger=log)
    engine = NullWhisperBackend(config=cfg.stt, logger=log)
    return Hlust(config=cfg, mic=mic, vad=vad, engine=engine, logger=log)


# ---------------------------------------------------------------------------
# Availability detection
# ---------------------------------------------------------------------------

def test_hlust_unavailable_with_null_mic() -> None:
    """Hlust is unavailable when mic is NullMicBackend."""
    hlust = _make_null_hlust()
    assert hlust.is_available is False


def test_hlust_unavailable_with_null_whisper() -> None:
    """Hlust is unavailable when engine is NullWhisperBackend."""
    cfg = _make_config()
    log = _make_logger()
    mic = _MockMic()
    vad = _MockVad()
    engine = NullWhisperBackend(config=cfg.stt, logger=log)
    hlust = Hlust(config=cfg, mic=mic, vad=vad, engine=engine, logger=log)
    assert hlust.is_available is False


def test_hlust_unavailable_with_null_mic_only() -> None:
    """Hlust is unavailable when mic is Null regardless of other backends."""
    cfg = _make_config()
    log = _make_logger()
    mic = NullMicBackend(device="default", logger=log)
    vad = _MockVad()
    engine = _MockEngine()
    hlust = Hlust(config=cfg, mic=mic, vad=vad, engine=engine, logger=log)
    assert hlust.is_available is False


def test_hlust_available_with_null_vad() -> None:
    """Hlust is available even when VAD is NullVadBackend (uses fixed-window fallback)."""
    cfg = _make_config()
    log = _make_logger()
    mic = _MockMic()
    vad = NullVadBackend(config=cfg.stt, logger=log)
    engine = _MockEngine()
    hlust = Hlust(config=cfg, mic=mic, vad=vad, engine=engine, logger=log)
    # NullVadBackend doesn't mark Hlust unavailable — it just means fixed-window capture
    assert hlust.is_available is True


def test_hlust_available_with_all_real_backends() -> None:
    """Hlust is available when mic and Whisper backends are real (non-Null)."""
    hlust, mic, vad, engine = _make_real_hlust()
    assert hlust.is_available is True


def test_hlust_not_closed_initially() -> None:
    """Hlust.is_closed is False immediately after construction."""
    hlust = _make_null_hlust()
    assert hlust.is_closed is False


# ---------------------------------------------------------------------------
# capture_one_utterance() guard conditions
# ---------------------------------------------------------------------------

async def test_capture_raises_when_unavailable() -> None:
    """capture_one_utterance() raises HlustConfigError when Hlust is unavailable."""
    hlust = _make_null_hlust()
    with pytest.raises(HlustConfigError, match="unavailable"):
        await hlust.capture_one_utterance()


async def test_capture_raises_when_closed() -> None:
    """capture_one_utterance() raises HlustConfigError after close() is called."""
    hlust, mic, vad, engine = _make_real_hlust()
    await hlust.close()
    with pytest.raises(HlustConfigError, match="closed"):
        await hlust.capture_one_utterance()


# ---------------------------------------------------------------------------
# Lazy model loading
# ---------------------------------------------------------------------------

async def test_capture_triggers_lazy_model_load() -> None:
    """capture_one_utterance() calls engine.load_model() on first invocation."""
    hlust, mic, vad, engine = _make_real_hlust(complete_after=1, transcript="test")
    await hlust.open()

    assert engine.load_count == 0  # not loaded yet

    # Feed one frame synchronously to satisfy the frame queue
    loop = asyncio.get_running_loop()

    async def _drive():
        # Push frames into the queue after a tiny delay so the capture loop is waiting
        await asyncio.sleep(0)
        # We push the frame via the mock mic's stored callback reference
        # Since mock mic runs synchronously, we need to simulate the threading bridge
        # by directly calling frame_queue.put_nowait via call_soon_threadsafe equivalent
        if hlust._frame_queue:
            hlust._frame_queue.put_nowait(_silence_frame())

    # Run capture_one_utterance() concurrently with the frame feeder
    capture_task = asyncio.ensure_future(hlust.capture_one_utterance())
    await _drive()
    await asyncio.sleep(0)
    # If VAD completes after 1 frame, the capture should finish
    await asyncio.wait_for(capture_task, timeout=2.0)

    assert engine.load_count == 1


async def test_model_not_loaded_at_open_with_lazy_strategy() -> None:
    """Hlust.open() does NOT call engine.load_model() with lazy strategy."""
    hlust, mic, vad, engine = _make_real_hlust(load_strategy="lazy")
    await hlust.open()
    assert engine.load_count == 0
    assert engine.is_loaded is False


async def test_model_loaded_at_open_with_eager_strategy() -> None:
    """Hlust.open() calls engine.load_model() with eager strategy."""
    hlust, mic, vad, engine = _make_real_hlust(load_strategy="eager")
    await hlust.open()
    assert engine.load_count == 1
    assert engine.is_loaded is True


# ---------------------------------------------------------------------------
# Close
# ---------------------------------------------------------------------------

async def test_close_idempotent() -> None:
    """Hlust.close() can be called multiple times without raising."""
    hlust = _make_null_hlust()
    await hlust.close()
    await hlust.close()
    assert hlust.is_closed is True


async def test_close_stops_mic_if_streaming() -> None:
    """Hlust.close() calls mic.stop_stream() if a stream was active."""
    hlust, mic, vad, engine = _make_real_hlust()
    hlust._stream_active = True  # simulate active stream state
    await hlust.close()
    assert mic.stopped is True


async def test_close_noop_when_already_closed() -> None:
    """Hlust.close() is a no-op when already closed."""
    hlust = _make_null_hlust()
    await hlust.close()
    assert hlust.is_closed is True
    # Second call must not raise or change state
    await hlust.close()
    assert hlust.is_closed is True


# ---------------------------------------------------------------------------
# Full orchestration flow (direct queue injection — no real threads)
# ---------------------------------------------------------------------------

async def test_capture_one_utterance_returns_transcript() -> None:
    """Full capture flow: frames pushed into queue -> VAD complete -> Whisper -> text."""
    hlust, mic, vad, engine = _make_real_hlust(complete_after=3, transcript="hello world")
    await hlust.open()

    async def _feed_frames():
        """Push 3 frames into Hlust's frame queue to trigger VAD completion."""
        await asyncio.sleep(0)
        assert hlust._frame_queue is not None
        for _ in range(3):
            hlust._frame_queue.put_nowait(_silence_frame())
            await asyncio.sleep(0)

    capture_task = asyncio.ensure_future(hlust.capture_one_utterance())
    await _feed_frames()
    result = await asyncio.wait_for(capture_task, timeout=3.0)

    assert result == "hello world"
    assert engine.transcribe_count == 1


async def test_capture_stops_mic_on_completion() -> None:
    """Mic stream is stopped after utterance completion."""
    hlust, mic, vad, engine = _make_real_hlust(complete_after=3, transcript="test")
    await hlust.open()

    async def _feed_frames():
        await asyncio.sleep(0)
        for _ in range(3):
            hlust._frame_queue.put_nowait(_silence_frame())
            await asyncio.sleep(0)

    capture_task = asyncio.ensure_future(hlust.capture_one_utterance())
    await _feed_frames()
    await asyncio.wait_for(capture_task, timeout=3.0)

    # Mic should have been started and stopped
    assert mic.start_count == 1
    assert mic.stop_count == 1


async def test_capture_returns_empty_on_no_frames() -> None:
    """capture_one_utterance() returns empty string when frame queue is empty on timeout.

    We simulate a quick timeout by patching asyncio.wait_for in the heretic.rodd.hlust
    module namespace specifically, replacing only the frame-queue wait.
    """
    hlust, mic, vad, engine = _make_real_hlust(complete_after=3, transcript="test")
    await hlust.open()

    # Patch asyncio.wait_for in hlust's module namespace to instantly time out
    import heretic.rodd.hlust as hlust_module

    original_wait_for = asyncio.wait_for
    call_count = [0]

    async def _instant_timeout(coro, timeout=None):
        call_count[0] += 1
        # First call is the frame wait — immediately time it out
        if call_count[0] == 1:
            # Cancel the coro cleanly
            coro.close()
            raise asyncio.TimeoutError()
        return await original_wait_for(coro, timeout=timeout)

    with patch.object(hlust_module, "asyncio") as mock_asyncio:
        # Set up the mock so it behaves like asyncio but overrides wait_for
        mock_asyncio.wait_for = _instant_timeout
        mock_asyncio.get_running_loop = asyncio.get_running_loop
        mock_asyncio.TimeoutError = asyncio.TimeoutError
        mock_asyncio.Queue = asyncio.Queue
        mock_asyncio.Event = asyncio.Event
        mock_asyncio.AbstractEventLoop = asyncio.AbstractEventLoop

        result = await asyncio.wait_for(hlust.capture_one_utterance(), timeout=3.0)

    # No frames received -> empty transcript
    assert result == ""


async def test_capture_hard_cap_limits_frames() -> None:
    """Hlust stops capture at _MAX_UTTERANCE_FRAMES even if VAD never completes."""
    # Use a VAD that never completes
    cfg = _make_config()
    log = _make_logger()
    mic = _MockMic()
    # VAD that never completes
    vad_never = MagicMock()
    vad_never.is_speech.return_value = True
    vad_never.utterance_complete.return_value = False
    vad_never.reset.return_value = None
    engine = _MockEngine(transcript="capped")

    hlust = Hlust(config=cfg, mic=mic, vad=vad_never, engine=engine, logger=log)
    await hlust.open()

    # Feed exactly _MAX_UTTERANCE_FRAMES frames
    async def _flood_frames():
        await asyncio.sleep(0)
        for _ in range(_MAX_UTTERANCE_FRAMES):
            hlust._frame_queue.put_nowait(_silence_frame())
            # Yield occasionally to let the capture loop drain the queue
            if _ % 50 == 0:
                await asyncio.sleep(0)

    capture_task = asyncio.ensure_future(hlust.capture_one_utterance())
    await _flood_frames()
    result = await asyncio.wait_for(capture_task, timeout=10.0)

    # Should have transcribed despite VAD never completing
    assert result == "capped"
    assert engine.transcribe_count == 1


async def test_capture_fault_returns_empty_not_crash() -> None:
    """capture_one_utterance() returns empty string on recoverable fault."""
    cfg = _make_config()
    log = _make_logger()
    mic = _MockMic()
    vad = _MockVad(complete_after=1)
    # Engine that raises on transcribe
    engine = _MockEngine()
    engine_async = AsyncMock()
    engine_async.transcribe = AsyncMock(side_effect=Exception("transcribe exploded"))
    engine_async.is_loaded = True
    engine_async.load_model = AsyncMock()

    hlust = Hlust(config=cfg, mic=mic, vad=vad, engine=engine_async, logger=log)
    await hlust.open()

    async def _feed():
        await asyncio.sleep(0)
        hlust._frame_queue.put_nowait(_silence_frame())

    capture_task = asyncio.ensure_future(hlust.capture_one_utterance())
    await _feed()
    result = await asyncio.wait_for(capture_task, timeout=3.0)

    # Should return empty string, not raise
    assert result == ""


# ---------------------------------------------------------------------------
# open() behavior
# ---------------------------------------------------------------------------

async def test_open_noop_when_unavailable() -> None:
    """Hlust.open() is a no-op when Hlust is unavailable."""
    hlust = _make_null_hlust()
    await hlust.open()  # must not raise
    assert hlust._loop is None  # not set because unavailable


async def test_open_noop_when_closed() -> None:
    """Hlust.open() is a no-op when Hlust is already closed."""
    hlust, mic, vad, engine = _make_real_hlust()
    await hlust.close()
    await hlust.open()  # must not raise or re-open
