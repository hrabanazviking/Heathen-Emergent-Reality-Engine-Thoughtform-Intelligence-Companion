"""
Tunga — the tongue of HERETIC. L2 Rödd TTS orchestrator.

Tunga receives streaming text deltas from L1 Bifröst (bifrost::agent_text_delta),
accumulates them into sentence-boundary chunks, sends each chunk to ChatterBox
for synthesis, and plays the returned WAV bytes via the selected AudioPlayback backend.

Architecture:
    L1 Bifröst (text stream)
        -> await tunga.feed_chunk(text_delta)
           -> internal buffer accumulation
           -> sentence-boundary detection (chunk_min_chars + sentence_terminators)
           -> await _speak_chunk(chunk_text)
              -> await client.synthesize(chunk_text) -> bytes
              -> loop.run_in_executor(playback.play(wav_bytes))
                 -> speakers

Serialization:
    An asyncio.Lock (_speak_lock) ensures only one synthesis + playback pair runs
    at a time. Chunks arrive in order from Bifröst; they speak in order. The lock
    is acquired before synthesize() and released after play() finishes.

Fault model:
    If ChatterBox is unreachable at open() time, or playback fails at init,
    Tunga sets self._degraded = True. Subsequent feed_chunk()/flush() calls
    are no-ops. The ceremony continues text-only. This honours the Law of
    Fault Tolerance from RULES.AI.md.

    If synthesis or playback fail on a specific chunk after a successful open(),
    Tunga increments a consecutive-failure counter. After 3 consecutive failures
    it enters permanent degraded mode (DATA_FLOW.md §4.6.2).

NOTE: feed_chunk() and flush() are async def. CLI callers must await them.
The skeleton declared them as sync; Forge changes the signature per the Architect's
guidance in tunga.py: "NOTE TO FORGE: This method may need to become async def."
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from heretic.rodd.errors import ChatterboxError, PlaybackError, TungaConfigError

if TYPE_CHECKING:
    from heretic.rodd.chatterbox import ChatterboxClient
    from heretic.rodd.config_model import RoddConfig
    from heretic.rodd.playback import AudioPlayback


# Number of consecutive chunk failures before Tunga permanently degrades
_MAX_CONSECUTIVE_FAILURES: int = 3


class Tunga:
    """Orchestrator — converts streaming text into spoken audio.

    Tunga is stateful. A single instance is created per ceremony and reused
    across all agent turns. It maintains an internal text buffer and flushes
    it as sentence-boundary chunks accumulate above ``chunk_min_chars``.

    Thread safety: Tunga is NOT thread-safe. All calls to feed_chunk(), flush(),
    and close() must come from the same asyncio task. The internal _speak_lock
    serialises synthesis + playback so chunks always speak in order.

    Degraded mode: if self._degraded is True, feed_chunk() and flush() are no-ops
    that log at DEBUG. Degraded mode is entered when:
      - playback.available() is False at construction time
      - client.open() raises ChatterboxError
      - 3 consecutive chunk synthesis/playback failures occur mid-ceremony
    Degraded mode cannot be exited during a ceremony.
    """

    def __init__(
        self,
        config: "RoddConfig",
        client: "ChatterboxClient",
        playback: "AudioPlayback",
        logger: logging.Logger,
    ) -> None:
        """Initialise Tunga.

        Stores config, client, playback, and logger. Checks playback availability;
        enters degraded mode if not available. Does NOT call client.open() here —
        open() is an async operation called via Tunga.open() below.

        Args:
            config: Full RoddConfig. Tunga reads ``config.tts`` for its settings.
            client: A ChatterboxClient instance (not yet open). Tunga calls
                    open() when Tunga.open() is called.
            playback: An AudioPlayback backend (already constructed). If
                      ``playback.available()`` is False, Tunga enters degraded mode.
            logger: Logger instance from grunnr.logger.get_logger.

        Raises:
            TungaConfigError: if config.tts is invalid (propagated from RoddTtsConfig).
        """
        # config.tts is already validated by RoddTtsConfig.__post_init__; if we reach here
        # the config is valid. Store the TTS sub-config for easy access.
        self._config = config.tts
        self._client = client
        self._playback = playback
        self._log = logger
        self._buffer: str = ""
        self._degraded: bool = False
        self._closed: bool = False
        self._consecutive_failures: int = 0
        # Serialises synthesis + playback — one chunk in flight at a time
        self._speak_lock: asyncio.Lock = asyncio.Lock()

        # Check playback availability at construction time
        if not self._playback.available():
            self._degraded = True
            self._log.warning(
                "Tunga: no audio playback backend available — entering text-only mode. "
                "Voice output is disabled for this ceremony. "
                "Install heretic[voice] or check your audio device."
            )

    @property
    def is_degraded(self) -> bool:
        """True if Tunga is operating in text-only fallback mode (no audio output)."""
        return self._degraded

    @property
    def is_closed(self) -> bool:
        """True if close() has been called. A closed Tunga must not be used."""
        return self._closed

    async def open(self) -> None:
        """Open the ChatterBox client connection.

        Called at Kynding/Tengsl to verify ChatterBox is reachable before the
        ceremony begins. If the connection fails, Tunga enters degraded mode so
        the ceremony proceeds text-only rather than crashing.
        """
        if self._degraded or self._closed:
            return

        try:
            await self._client.open()
            self._log.info(
                "Tunga: open — endpoint=%s model=%s device=%s",
                self._config.endpoint,
                self._config.model,
                self._config.device,
            )
        except ChatterboxError as exc:
            self._degraded = True
            self._log.warning(
                "Tunga: ChatterBox unreachable at %r — entering text-only mode. "
                "The ceremony will continue without voice. Detail: %s",
                self._config.endpoint,
                exc,
            )
        except Exception as exc:
            # Unexpected error during open — degrade rather than crash
            self._degraded = True
            self._log.warning(
                "Tunga: unexpected error during client.open() — entering text-only mode: %s",
                exc,
            )

    async def feed_chunk(self, text_delta: str) -> None:
        """Accept a streaming text delta and speak any complete sentence chunks.

        Called by Holdvörðr for every ``bifrost::agent_text_delta`` event.
        Accumulates text in the internal buffer; flushes sentence chunks once
        the buffer exceeds ``chunk_min_chars`` AND contains a sentence terminator.

        The sentence chunking algorithm:
        1. Append text_delta to the buffer.
        2. If len(buffer) >= chunk_min_chars, scan for the LAST occurrence of any
           sentence terminator in the buffer.
        3. If found: extract buffer[:terminator_end] as a chunk, retain the rest.
        4. Call _speak_chunk(chunk) for the extracted text.
        5. If no terminator or buffer too short: keep accumulating.

        This is async — await it from the CLI response loop.

        Never raises. All errors are logged and handled internally.
        """
        if self._degraded or self._closed:
            self._log.debug("Tunga.feed_chunk: no-op (degraded=%s, closed=%s)", self._degraded, self._closed)
            return

        self._buffer += text_delta

        # Only attempt a boundary flush once we've built up enough text
        if len(self._buffer) < self._config.chunk_min_chars:
            return

        # Find the last sentence terminator in the accumulated buffer.
        # Using the LAST occurrence keeps larger chunks together, which gives
        # ChatterBox more context and produces more natural-sounding speech.
        last_boundary_end = -1
        for terminator in self._config.sentence_terminators:
            idx = self._buffer.rfind(terminator)
            if idx != -1:
                candidate_end = idx + len(terminator)
                if candidate_end > last_boundary_end:
                    last_boundary_end = candidate_end

        if last_boundary_end == -1:
            # No sentence boundary found — keep accumulating
            return

        chunk = self._buffer[:last_boundary_end]
        self._buffer = self._buffer[last_boundary_end:]

        await self._speak_chunk(chunk)

    async def flush(self) -> None:
        """Force-speak any text remaining in the buffer at end-of-stream.

        Called by Holdvörðr after the agent turn ends. Speaks whatever remains
        in the buffer regardless of chunk_min_chars or sentence boundaries.
        This ensures the last sentence fragment is always spoken.

        Never raises. All errors are logged and handled internally.
        """
        if self._degraded or self._closed:
            self._log.debug("Tunga.flush: no-op (degraded=%s, closed=%s)", self._degraded, self._closed)
            return

        remaining = self._buffer.strip()
        if not remaining:
            self._log.debug("Tunga.flush: buffer is empty — nothing to speak")
            self._buffer = ""
            return

        self._log.debug("Tunga.flush: flushing %d buffered chars", len(remaining))
        self._buffer = ""
        await self._speak_chunk(remaining)

    async def close(self) -> None:
        """Shut down Tunga cleanly. Safe to call multiple times.

        Flushes the buffer, closes the ChatterBox HTTP session and the playback backend.
        Sets self._closed = True. After close(), feed_chunk() and flush() are no-ops.

        Never raises.
        """
        if self._closed:
            return
        self._closed = True

        # Flush any remaining speech before closing (the agent's parting words)
        if not self._degraded and self._buffer.strip():
            try:
                await self._speak_chunk(self._buffer.strip())
            except Exception as exc:
                self._log.debug("Tunga.close: error during final flush: %s", exc)
        self._buffer = ""

        # Close client (async)
        try:
            await self._client.close()
        except Exception as exc:
            self._log.debug("Tunga.close: error closing client: %s", exc)

        # Close playback (sync)
        try:
            self._playback.close()
        except Exception as exc:
            self._log.debug("Tunga.close: error closing playback: %s", exc)

        self._log.debug("Tunga: closed")

    async def _speak_chunk(self, text: str) -> None:
        """Synthesise and play one text chunk. Internal — not part of the public API.

        Acquires _speak_lock so only one synthesis + playback pair runs at a time,
        guaranteeing in-order audio output even when multiple chunks are flushed
        in rapid succession.

        Fault tolerance: on ChatterboxError or PlaybackError, logs a WARNING and
        increments the consecutive failure counter. After _MAX_CONSECUTIVE_FAILURES
        consecutive failures, sets self._degraded = True and stops attempting synthesis
        for the rest of the ceremony (DATA_FLOW.md §4.6.2).

        Never raises.
        """
        text = text.strip()
        if not text:
            return

        self._log.debug(
            "Tunga._speak_chunk: len=%d preview=%r",
            len(text),
            text[:60],
        )

        async with self._speak_lock:
            if self._degraded:
                # May have degraded while waiting for the lock
                return
            try:
                wav_bytes = await self._client.synthesize(text)
            except ChatterboxError as exc:
                self._consecutive_failures += 1
                self._log.warning(
                    "Tunga: synthesis failed for chunk (len=%d): %s "
                    "[consecutive_failures=%d/%d]",
                    len(text),
                    exc,
                    self._consecutive_failures,
                    _MAX_CONSECUTIVE_FAILURES,
                )
                if self._consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
                    self._degraded = True
                    self._log.warning(
                        "Tunga: %d consecutive synthesis failures — "
                        "entering permanent text-only mode for this ceremony "
                        "(voice::error VOICE_TTS_UNREACHABLE)",
                        _MAX_CONSECUTIVE_FAILURES,
                    )
                return
            except Exception as exc:
                self._consecutive_failures += 1
                self._log.warning(
                    "Tunga: unexpected synthesis error for chunk (len=%d): %s",
                    len(text),
                    exc,
                )
                if self._consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
                    self._degraded = True
                return

            # Synthesis succeeded — reset consecutive failure count
            self._consecutive_failures = 0

            # Run blocking playback in a thread-pool executor so we don't block
            # the asyncio event loop while speakers emit audio.
            loop = asyncio.get_running_loop()  # get_event_loop() deprecated in 3.10+
            try:
                await loop.run_in_executor(None, self._playback.play, wav_bytes)
            except PlaybackError as exc:
                self._log.warning(
                    "Tunga: playback failed for chunk (len=%d): %s",
                    len(text),
                    exc,
                )
                # Playback failure is less severe than synthesis failure; we don't
                # increment consecutive_failures here — ChatterBox is still reachable.
                # If the device is truly gone, available() will return False on next check.
            except Exception as exc:
                self._log.warning(
                    "Tunga: unexpected playback error for chunk (len=%d): %s",
                    len(text),
                    exc,
                )
