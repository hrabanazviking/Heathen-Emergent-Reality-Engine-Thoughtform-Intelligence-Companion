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

Threading bridge (CRITICAL — do not bypass):
    The sounddevice mic callback fires on a C background thread managed by PortAudio.
    Asyncio primitives (asyncio.Queue, asyncio.Event) MUST NOT be touched from that
    thread.  The bridge pattern used here:

        self._loop  = asyncio.get_running_loop()  — captured in open()
        self._frame_queue = asyncio.Queue()        — created in open()

    The mic callback does:
        loop.call_soon_threadsafe(frame_queue.put_nowait, pcm_bytes)

    The capture loop awaits:
        frame = await frame_queue.get()

    This is the ONLY safe bridge between the PortAudio C thread and asyncio.

Lazy-load contract (C-Q-C1):
    WhisperEngine.load_model() is NOT called at Kynding. It is called on the first
    invocation of capture_one_utterance() when load_strategy is 'lazy' (default).
    When load_strategy is 'eager', the caller (lifecycle) calls
    await hlust.open() which in turn calls load_model().

Degraded mode:
    If any critical component is unavailable (NullMicBackend or NullWhisperBackend),
    Hlust sets self._available = False. capture_one_utterance() raises HlustConfigError
    so the caller (cli.py) falls back to stdin input. The ceremony never crashes.

    NullVadBackend does NOT make Hlust unavailable — it just means a fixed-window
    capture strategy is used.  The body can still listen without smart VAD.

Fault model:
    Any exception during a live capture cycle is caught, logged, and either:
    - Returned as empty string (for recoverable faults — mic stutter, VAD noise).
    - Re-raised as HlustError after cleanup (for fatal faults — device lost).
    The CLI treats empty string as "no input this turn" and continues.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import TYPE_CHECKING

from heretic.rodd.errors import (
    HlustConfigError,
    HlustError,
    WhisperError,
)
from heretic.rodd.microphone import NullMicBackend
from heretic.rodd.whisper_engine import NullWhisperBackend

if TYPE_CHECKING:
    from heretic.rodd.config_model import RoddConfig
    from heretic.rodd.microphone import MicrophoneCapture
    from heretic.rodd.vad import VadDetector
    from heretic.rodd.whisper_engine import WhisperEngine


# Maximum number of 30 ms frames we will accumulate before forcing utterance end.
# 1000 frames * 30 ms = 30 seconds.  This is a hard safety cap to prevent an
# infinite capture loop if VAD fails to detect end-of-speech in noisy environments.
_MAX_UTTERANCE_FRAMES: int = 1000


class Hlust:
    """Orchestrator — converts spoken audio into text.

    Hlust is stateful. A single instance is created per ceremony. It manages
    the microphone stream lifecycle, accumulates frames, gates on VAD, and
    calls Whisper for transcription.

    Thread safety: Hlust is NOT thread-safe. capture_one_utterance() must not
    be called concurrently from multiple asyncio tasks.

    Availability:
        - NullMicBackend  → self._available = False  (no mic, cannot capture)
        - NullWhisperBackend → self._available = False (no transcription)
        - NullVadBackend → still available (fixed-window capture works without VAD)
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
            vad: A VadDetector backend (already constructed). NullVadBackend is
                 tolerated — Hlust falls back to fixed-window capture in that case.
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

        # The asyncio event loop reference captured in open().
        # Needed by the mic callback to bridge frames from the PortAudio C thread.
        self._loop: asyncio.AbstractEventLoop | None = None

        # Frame queue: mic callback pushes bytes; capture loop awaits bytes.
        # Created in open() inside a running event loop.
        self._frame_queue: asyncio.Queue[bytes] | None = None

        # Track whether mic stream is currently active to support idempotent stop
        self._stream_active: bool = False

        # Determine availability: NullMicBackend or NullWhisperBackend → unavailable.
        # NullVadBackend is tolerated — it provides a fixed-window fallback.
        null_components = []
        if isinstance(mic, NullMicBackend):
            null_components.append("microphone")
        if isinstance(engine, NullWhisperBackend):
            null_components.append("Whisper engine")

        self._available: bool = len(null_components) == 0
        if not self._available:
            self._log.warning(
                "Hlust: unavailable — the following components have no real backend: %s. "
                "Voice input is disabled; CLI will use stdin fallback.",
                ", ".join(null_components),
            )

    @property
    def is_available(self) -> bool:
        """True if mic and Whisper backends are real (non-Null) and Hlust can capture."""
        return self._available

    @property
    def is_closed(self) -> bool:
        """True if close() has been called."""
        return self._closed

    async def open(self) -> None:
        """Prepare Hlust for utterance capture.

        Called at Kynding or before the first ceremony.

        Actions:
        1. Capture the running asyncio event loop reference (needed by the
           mic callback threading bridge).
        2. Create the asyncio.Queue for frame delivery.
        3. If load_strategy is 'eager': load the Whisper model now.

        If Hlust is unavailable (Null backends), this is a no-op.

        Never raises — faults are logged and stored. capture_one_utterance()
        will raise HlustConfigError if the system is not ready.
        """
        if not self._available or self._closed:
            return

        try:
            self._loop = asyncio.get_running_loop()
            self._frame_queue = asyncio.Queue()
            self._log.debug("Hlust: event loop captured, frame queue ready")

            if self._config.load_strategy == "eager":
                self._log.info("Hlust: eager load_strategy — loading Whisper model at Kynding")
                await self._ensure_model_loaded()

            self._log.info("Hlust: open complete (strategy=%r)", self._config.load_strategy)
        except Exception as exc:
            # open() must not propagate — log and mark unavailable
            self._log.warning("Hlust.open: failed during setup: %s", exc)
            self._available = False

    async def preload_model(self) -> None:
        """Eagerly load the Whisper model. Called by lifecycle at Kynding when configured.

        After this coroutine returns, self._engine.is_loaded is True.

        Raises:
            WhisperError: if model loading fails (propagated from WhisperEngine.load_model).
        """
        await self._ensure_model_loaded()
        self._log.info("Hlust: Whisper model preloaded (eager/explicit)")

    async def capture_one_utterance(self) -> str:
        """Capture one complete spoken utterance and return its transcript.

        This is the primary public interface for Hlust. The CLI calls this
        instead of stdin.readline() when STT is enabled and Hlust is available.

        Sequence:
            1. Guard checks (available, not closed).
            2. Lazy-load Whisper model if not yet loaded.
            3. Reset VAD state for a new utterance.
            4. Print '[listening...]' cue to stderr.
            5. Start the microphone stream with a frame callback that bridges
               frames from the PortAudio C thread to the asyncio frame queue.
            6. Accumulate frames from the queue; classify each via VAD.
            7. When VAD signals utterance complete (or _MAX_UTTERANCE_FRAMES reached),
               stop the stream.
            8. Concatenate accumulated frames.
            9. Print '[loading model...]' only if we had to lazy-load.
            10. Call engine.transcribe(audio_bytes, sample_rate=16000).
            11. Print '[heard: <transcript>]' to stderr for confirmation.
            12. Return the stripped transcript string.

        Returns:
            Transcribed text string, stripped of leading/trailing whitespace.
            Returns empty string on recoverable fault (mic stutter, no speech detected).

        Raises:
            HlustConfigError: if Hlust is unavailable (Null backends) or closed.
        """
        if not self._available:
            raise HlustConfigError(
                "Hlust.capture_one_utterance: Hlust is unavailable (no real mic/Whisper). "
                "The caller should fall back to stdin input."
            )
        if self._closed:
            raise HlustConfigError(
                "Hlust.capture_one_utterance: Hlust has been closed. Create a new instance."
            )

        # Ensure the frame queue and loop reference are initialised.
        # open() should have been called already, but guard defensively.
        if self._loop is None or self._frame_queue is None:
            self._loop = asyncio.get_running_loop()
            self._frame_queue = asyncio.Queue()

        try:
            return await self._capture_loop()
        except HlustConfigError:
            raise  # propagate guard errors unchanged
        except Exception as exc:
            # Recoverable fault — log, clean up, return empty string so CLI continues
            self._log.warning("Hlust.capture_one_utterance: fault during capture: %s", exc)
            self._stop_mic_safe()
            return ""

    async def _capture_loop(self) -> str:
        """Internal: execute the full capture → VAD → transcribe pipeline.

        Split from capture_one_utterance() for clarity and testability.
        Exceptions here propagate to capture_one_utterance()'s fault handler.
        """
        loop = self._loop
        frame_queue: asyncio.Queue[bytes] = self._frame_queue  # type: ignore[assignment]

        # Lazy-load Whisper model on first utterance if not already loaded.
        # We do this BEFORE opening the mic so the '[loading model...]' pause
        # does not affect the listening cue timing.
        if not self._model_loaded:
            print("[loading model...]", file=sys.stderr, flush=True)
            await self._ensure_model_loaded()

        # Reset VAD state for a clean utterance
        self._vad.reset()
        frames: list[bytes] = []

        print("[listening...]", file=sys.stderr, flush=True)

        # Build the mic frame callback.
        # CRITICAL: this callback fires on a PortAudio C background thread.
        # It MUST NOT touch asyncio primitives directly.
        # Bridge via loop.call_soon_threadsafe() — the ONLY safe crossing.
        def _frame_callback(pcm_bytes: bytes) -> None:
            # call_soon_threadsafe schedules the put_nowait coroutine on the
            # asyncio event loop thread, making the queue delivery thread-safe.
            loop.call_soon_threadsafe(frame_queue.put_nowait, pcm_bytes)

        # Start the mic stream
        self._mic.start_stream(_frame_callback)
        self._stream_active = True

        try:
            # Accumulate frames until VAD signals complete or hard cap reached
            while len(frames) < _MAX_UTTERANCE_FRAMES:
                try:
                    # Wait for the next frame with a generous timeout.
                    # If the mic stops pushing frames (device error), this prevents
                    # an infinite hang.
                    frame = await asyncio.wait_for(frame_queue.get(), timeout=5.0)
                except asyncio.TimeoutError:
                    # No frame arrived within 5 s — treat as utterance end (device stall)
                    self._log.debug("Hlust: frame timeout — ending utterance capture")
                    break

                frames.append(frame)

                # Classify frame via VAD and check for utterance end.
                # is_speech() updates VAD's internal state for utterance_complete().
                try:
                    self._vad.is_speech(frame)
                except Exception as vad_exc:
                    # VAD fault — log and continue; don't crash the capture
                    self._log.debug("Hlust: VAD is_speech error (ignored): %s", vad_exc)

                if self._vad.utterance_complete(frames):
                    self._log.debug(
                        "Hlust: VAD utterance_complete after %d frames (%d ms)",
                        len(frames),
                        len(frames) * 30,
                    )
                    break

            if len(frames) >= _MAX_UTTERANCE_FRAMES:
                self._log.warning(
                    "Hlust: hard cap reached (%d frames = %d s) — forcing utterance end",
                    _MAX_UTTERANCE_FRAMES,
                    _MAX_UTTERANCE_FRAMES * 30 // 1000,
                )

        finally:
            # Always stop the mic stream — even if an exception occurred above
            self._stop_mic_safe()

        if not frames:
            self._log.debug("Hlust: no frames accumulated — returning empty transcript")
            return ""

        # Concatenate all frames into a single audio buffer for Whisper
        audio = b"".join(frames)

        # Transcribe via Whisper engine
        try:
            transcript = await self._engine.transcribe(audio, sample_rate=16_000)
        except WhisperError as exc:
            self._log.warning("Hlust: transcription failed: %s", exc)
            return ""

        transcript = transcript.strip()
        print(f"[heard: {transcript}]", file=sys.stderr, flush=True)
        return transcript

    def _stop_mic_safe(self) -> None:
        """Stop the mic stream without raising. Idempotent."""
        if self._stream_active:
            try:
                self._mic.stop_stream()
            except Exception as exc:
                self._log.debug("Hlust: error stopping mic stream: %s", exc)
            finally:
                self._stream_active = False

    async def close(self) -> None:
        """Shut down Hlust cleanly. Safe to call multiple times (idempotent).

        Stops the microphone stream if running and releases resources.
        After close(), capture_one_utterance() raises HlustConfigError.

        Never raises.
        """
        if self._closed:
            return
        self._closed = True

        try:
            self._stop_mic_safe()
        except Exception as exc:
            self._log.debug("Hlust.close: error during mic stop: %s", exc)

        self._log.debug("Hlust: closed")

    async def _ensure_model_loaded(self) -> None:
        """Internal: load the Whisper model if not yet loaded (lazy strategy).

        Called by capture_one_utterance() before the first transcription and by
        open() when load_strategy is 'eager'.  Sets self._model_loaded = True on
        success.

        Raises:
            WhisperError / WhisperModelLoadError: if model loading fails.
        """
        if self._model_loaded:
            return
        await self._engine.load_model()
        self._model_loaded = True
        self._log.info("Hlust: Whisper model loaded (lazy)")
