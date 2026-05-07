"""
Hlust — the ear of HERETIC. L2 Rödd STT orchestrator.

Hlust receives spoken audio from the microphone, passes 30 ms frames through VAD
to detect utterance boundaries, and transcribes complete utterances via Whisper.
The resulting text string flows to L1 Bifröst as a user-role message
(voice::transcript event).

Architecture:
    OS microphone
        -> MicrophoneCapture.start_stream(frame_callback)
           -> 30 ms int16 frames (960 bytes each)
           -> VadDetector.is_speech(frame)           -- speech / silence classifier
              -> accumulate speech frames in buffer
           -> VadDetector.utterance_complete(frames)  -- end-of-utterance gate
              -> WhisperEngine.transcribe(concat_bytes, sample_rate=16000)
                 -> transcript text
                    -> returned from capture_one_utterance()
                       -> L1 Bifröst (caller responsibility)

Lazy-load contract (C-Q-C1):
    WhisperEngine.load_model() is NOT called at Kynding. It is called on the first
    invocation of capture_one_utterance() when load_strategy is 'lazy' (default).
    When load_strategy is 'eager', the caller (lifecycle) calls
    await hlust.preload_model() at Kynding.

Degraded mode:
    If any component is unavailable (NullMicBackend, NullVadBackend,
    NullWhisperBackend), Hlust sets self._available = False. capture_one_utterance()
    then raises HlustConfigError so the caller (cli.py) falls back to stdin input
    with a user-visible warning. The ceremony never crashes.

Fault model:
    Any exception from the mic, VAD, or Whisper layer during a live capture cycle
    is caught, logged, and re-raised as HlustError (or a subclass). The caller is
    responsible for the stdin fallback decision.

NOTE: capture_one_utterance() is async def. CLI callers must await it.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from heretic.rodd.errors import (
    HlustConfigError,
    HlustError,
    MicrophoneError,
    VadError,
    WhisperError,
)
from heretic.rodd.microphone import NullMicBackend
from heretic.rodd.vad import NullVadBackend
from heretic.rodd.whisper_engine import NullWhisperBackend

if TYPE_CHECKING:
    from heretic.rodd.config_model import RoddConfig
    from heretic.rodd.microphone import MicrophoneCapture
    from heretic.rodd.vad import VadDetector
    from heretic.rodd.whisper_engine import WhisperEngine


# Maximum duration we will wait for a complete utterance before giving up.
# This prevents an infinite capture loop when VAD fails to detect end-of-speech.
# Default: 15 seconds (500 frames at 30 ms). Configurable in a future config field.
_MAX_UTTERANCE_FRAMES: int = 500


class Hlust:
    """Orchestrator — converts spoken audio into text.

    Hlust is stateful. A single instance is created per ceremony. It manages
    the microphone stream lifecycle, accumulates frames, gates on VAD, and
    calls Whisper for transcription.

    Thread safety: Hlust is NOT thread-safe. capture_one_utterance() must not
    be called concurrently from multiple asyncio tasks.

    Availability: if any critical component is a Null backend, self._available
    is False and capture_one_utterance() raises HlustConfigError immediately.
    The caller should then fall back to stdin input.
    """

    def __init__(
        self,
        config: "RoddConfig",
        mic: "MicrophoneCapture",
        vad: "VadDetector",
        engine: "WhisperEngine",
        logger: logging.Logger,
    ) -> None:
        """Initialise Hlust.

        Stores config and dependencies. Does NOT call mic.start_stream() or
        engine.load_model() here — those are deferred to open() and the first
        capture_one_utterance() call respectively.

        Args:
            config: Full RoddConfig. Hlust reads ``config.stt`` for its settings.
            mic: A MicrophoneCapture backend (already constructed). If it is a
                 NullMicBackend, Hlust marks itself unavailable.
            vad: A VadDetector backend (already constructed). If it is a
                 NullVadBackend, Hlust marks itself unavailable.
            engine: A WhisperEngine backend (already constructed). If it is a
                    NullWhisperBackend, Hlust marks itself unavailable.
            logger: Logger instance from grunnr.logger.get_logger.
        """
        self._config = config.stt
        self._mic = mic
        self._vad = vad
        self._engine = engine
        self._log = logger
        self._closed: bool = False
        self._model_loaded: bool = False

        # Detect Null backends — any Null means no real STT available
        null_components = []
        if isinstance(mic, NullMicBackend):
            null_components.append("microphone")
        if isinstance(vad, NullVadBackend):
            null_components.append("VAD")
        if isinstance(engine, NullWhisperBackend):
            null_components.append("Whisper engine")

        self._available: bool = len(null_components) == 0
        if not self._available:
            self._log.warning(
                "Hlust: unavailable — the following components have no real backend: %s. "
                "Voice input is disabled; CLI will use stdin fallback.",
                ", ".join(null_components),
            )

        # asyncio.Event used to signal frame arrival from the mic callback thread
        # to the asyncio capture loop. Forge will initialise this inside open()
        # after the event loop is running.
        self._frame_event: asyncio.Event | None = None
        self._frame_buffer: list[bytes] = []

    @property
    def is_available(self) -> bool:
        """True if all three backends are real (non-Null) and Hlust can capture."""
        return self._available

    @property
    def is_closed(self) -> bool:
        """True if close() has been called."""
        return self._closed

    async def open(self) -> None:
        """Prepare Hlust for utterance capture.

        Called at Kynding or before the first ceremony. When load_strategy is
        'eager', loads the Whisper model here. When 'lazy' (default), defers
        model loading to the first capture_one_utterance() call.

        If Hlust is unavailable (Null backends), this is a no-op.

        Never raises — faults are logged and stored; capture_one_utterance()
        will raise HlustConfigError if the system is not ready.
        """
        if not self._available or self._closed:
            return

        # Forge will implement:
        # 1. Initialise self._frame_event = asyncio.Event() (must be inside a running loop)
        # 2. If self._config.load_strategy == 'eager': await self._load_model()
        raise NotImplementedError(
            "Forge will implement: initialise self._frame_event = asyncio.Event(); "
            "if config.load_strategy == 'eager', await self._load_model(); "
            "log readiness at INFO level."
        )

    async def preload_model(self) -> None:
        """Eagerly load the Whisper model. Called by lifecycle at Kynding when configured.

        Equivalent to forcing model loading before the first utterance.
        After this coroutine returns, self._engine.is_loaded is True.

        Raises:
            WhisperError: if model loading fails (propagated from WhisperEngine.load_model).
        """
        raise NotImplementedError(
            "Forge will implement: await self._engine.load_model(), "
            "set self._model_loaded = True, log at INFO."
        )

    async def capture_one_utterance(self) -> str:
        """Capture one complete spoken utterance and return its transcript.

        This is the primary public interface for Hlust. The CLI calls this
        instead of stdin.readline() when STT is enabled and Hlust is available.

        Sequence:
            1. Lazy-load Whisper model if not yet loaded (first call).
            2. Reset VAD state for a new utterance.
            3. Start the microphone stream, pushing frames to an internal buffer.
            4. Accumulate frames; classify each via VAD.
            5. When VAD signals utterance complete (or _MAX_UTTERANCE_FRAMES reached),
               stop the stream.
            6. Concatenate accumulated speech frames.
            7. Call engine.transcribe(audio_bytes, sample_rate=16000).
            8. Return the stripped transcript string.

        Returns:
            Transcribed text string, stripped of leading/trailing whitespace.
            May be empty if the audio contained no recognisable speech.

        Raises:
            HlustConfigError: if Hlust is unavailable (Null backends) or closed.
            MicrophoneError: if mic stream cannot be opened.
            VadError: if VAD classification fails.
            WhisperError: if transcription fails.
            HlustError: for any other Hlust-level fault.

        Never raises generic Exception — all exceptions are wrapped in an Hlust subclass.
        """
        if not self._available:
            raise HlustConfigError(
                "Hlust.capture_one_utterance: Hlust is unavailable (no real mic/VAD/Whisper). "
                "The caller should fall back to stdin input."
            )
        if self._closed:
            raise HlustConfigError(
                "Hlust.capture_one_utterance: Hlust has been closed. Create a new instance."
            )

        # Forge will implement the full capture loop:
        # 1. await self._ensure_model_loaded()
        # 2. self._vad.reset(); self._frame_buffer.clear()
        # 3. loop = asyncio.get_running_loop()
        # 4. Define frame_callback(frame: bytes) that appends to self._frame_buffer
        #    and calls loop.call_soon_threadsafe(self._frame_event.set)
        # 5. self._mic.start_stream(frame_callback)
        # 6. while len(self._frame_buffer) < _MAX_UTTERANCE_FRAMES:
        #        await self._frame_event.wait(); self._frame_event.clear()
        #        frame = self._frame_buffer[-1]  # process latest frame
        #        vad.is_speech(frame)
        #        if vad.utterance_complete(self._frame_buffer): break
        # 7. self._mic.stop_stream()
        # 8. audio = b"".join(self._frame_buffer)
        # 9. text = await self._engine.transcribe(audio, sample_rate=16000)
        # 10. return text.strip()
        raise NotImplementedError(
            "Forge will implement: lazy model load, VAD reset, mic stream open, "
            "asyncio frame accumulation loop with VAD gating, "
            "mic stop, Whisper transcription, return stripped text."
        )

    async def close(self) -> None:
        """Shut down Hlust cleanly. Safe to call multiple times.

        Stops the microphone stream if running and releases any resources.
        After close(), capture_one_utterance() raises HlustConfigError.

        Never raises.
        """
        if self._closed:
            return
        self._closed = True

        # Forge will implement: self._mic.stop_stream() in a try/except,
        # log any error at DEBUG, log INFO on clean shutdown.
        raise NotImplementedError(
            "Forge will implement: try self._mic.stop_stream(), "
            "catch and log any exception at DEBUG, log 'Hlust: closed' at DEBUG."
        )

    async def _ensure_model_loaded(self) -> None:
        """Internal — load the Whisper model if not yet loaded (lazy strategy).

        Called by capture_one_utterance() before the first transcription.
        Sets self._model_loaded = True on success.

        Raises:
            WhisperError: if model loading fails.
        """
        if self._model_loaded:
            return
        # Forge will implement: await self._engine.load_model(),
        # self._model_loaded = True, log at INFO "Hlust: Whisper model loaded (lazy)".
        raise NotImplementedError(
            "Forge will implement: await self._engine.load_model(); "
            "set self._model_loaded = True; log INFO 'Hlust: Whisper model loaded (lazy)'."
        )
