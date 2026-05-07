"""
Tunga — the tongue of HERETIC. L2 Rödd TTS orchestrator.

Tunga receives streaming text deltas from L1 Bifröst (bifrost::agent_text_delta),
accumulates them into sentence-boundary chunks, sends each chunk to ChatterBox
for synthesis, and plays the returned WAV bytes via the selected AudioPlayback backend.

Architecture:
    L1 Bifröst (text stream)
        -> Tunga.feed_chunk(text_delta)
           -> internal buffer accumulation
           -> sentence-boundary detection (chunk_min_chars + sentence_terminators)
           -> ChatterboxClient.synthesize(chunk_text) -> bytes
           -> AudioPlayback.play(wav_bytes)

Fault model:
    If ChatterBox is unreachable or playback fails, Tunga degrades to text-only
    mode. It logs a warning and does not raise to the caller. The ceremony continues
    uninterrupted. This is the Law of Fault Tolerance from RULES.AI.md.

Forge (Eldra Járnsdóttir) implements all method bodies. The skeleton declares the
full public interface, private attribute layout, and detailed docstrings so Forge
has a complete implementation target.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from heretic.rodd.chatterbox import ChatterboxClient
    from heretic.rodd.config_model import RoddConfig
    from heretic.rodd.playback import AudioPlayback


class Tunga:
    """Orchestrator — converts streaming text into spoken audio.

    Tunga is stateful. A single instance is created per ceremony and reused
    across all agent turns. It maintains an internal text buffer and flushes
    it as sentence-boundary chunks accumulate above ``chunk_min_chars``.

    Thread safety: Tunga is NOT thread-safe. All calls to feed_chunk(), flush(),
    and close() must come from the same thread or asyncio task. Callers that
    dispatch from multiple tasks must add their own synchronization.

    Degraded mode: if self._degraded is True, feed_chunk() and flush() are no-ops
    that log at DEBUG. Degraded mode is entered when ChatterBox is unreachable or
    the playback backend is unavailable, and cannot be exited during a ceremony.
    """

    def __init__(
        self,
        config: "RoddConfig",
        client: "ChatterboxClient",
        playback: "AudioPlayback",
        logger: logging.Logger,
    ) -> None:
        """Initialise Tunga. Validates config; enters degraded mode if appropriate.

        Args:
            config: Full RoddConfig. Tunga reads ``config.tts`` for its settings.
            client: A ChatterboxClient instance (open or not yet open). Tunga calls
                    open() during its own initialisation if the client is not open.
            playback: An AudioPlayback backend (already constructed; Tunga does not
                      own construction). If ``playback.available()`` is False, Tunga
                      enters degraded mode immediately.
            logger: Logger instance from grunnr.logger.get_logger.

        Post-construction invariants (Forge must uphold):
            - self._config is set to config.tts (the TTS sub-config, not the full RoddConfig).
            - self._client is the provided ChatterboxClient.
            - self._playback is the provided AudioPlayback.
            - self._log is the logger.
            - self._buffer is an empty string.
            - self._degraded is False unless playback.available() is False.
            - self._closed is False.

        Raises:
            TungaConfigError: if config.tts is invalid (caught from RoddTtsConfig.__post_init__).
        """
        # These assignments are acceptable in the skeleton — no NotImplementedError needed
        # because they are trivial attribute initialisation, not business logic.
        self._config = config.tts
        self._client = client
        self._playback = playback
        self._log = logger
        self._buffer: str = ""
        self._degraded: bool = False
        self._closed: bool = False

        # Forge will complete init:
        # 1. Check playback.available(). If False: self._degraded = True; log WARNING.
        # 2. If not degraded: call client.open() (handle ChatterboxError → set degraded).
        # 3. Log init result at INFO: endpoint, model, backend, degraded status.
        # Do not raise on degradation — the ceremony must continue.
        raise NotImplementedError(
            "Forge will implement: check playback.available() → degrade if False; "
            "call client.open() → degrade on ChatterboxError; "
            "log init result at INFO without raising."
        )

    @property
    def is_degraded(self) -> bool:
        """True if Tunga is operating in text-only fallback mode (no audio output)."""
        return self._degraded

    @property
    def is_closed(self) -> bool:
        """True if close() has been called. A closed Tunga must not be used."""
        return self._closed

    def feed_chunk(self, text_delta: str) -> None:
        """Accept a streaming text delta and speak any complete sentence chunks.

        Called by Holdvörðr for every ``bifrost::agent_text_delta`` event.
        Accumulates text in the internal buffer; flushes complete sentence chunks
        once the buffer exceeds ``chunk_min_chars`` AND contains a sentence terminator.

        Forge will implement:
        - Guard: if self._degraded or self._closed: log at DEBUG; return immediately.
        - Append text_delta to self._buffer.
        - Check if len(self._buffer) >= self._config.chunk_min_chars.
        - If yes: find the LAST occurrence of any sentence terminator in self._buffer.
        - If a terminator is found: extract self._buffer[:terminator_end] as a chunk;
          retain self._buffer[terminator_end:] as the new buffer.
        - Call self._speak_chunk(chunk_text) for the extracted text.
        - If no terminator found yet: leave the buffer unchanged (keep accumulating).

        Args:
            text_delta: A partial text string from the agent's streaming response.

        Raises:
            Never raises. All errors are logged and handled internally.
        """
        raise NotImplementedError(
            "Forge will implement: guard on degraded/closed; append delta to buffer; "
            "detect sentence boundary when buffer >= chunk_min_chars; "
            "extract chunk up to last terminator; call self._speak_chunk(chunk); "
            "retain remainder in buffer. Never raise."
        )

    def flush(self) -> None:
        """Force-speak any text remaining in the buffer at end-of-stream.

        Called by Holdvörðr after the agent turn ends (bifrost::agent_turn_end).
        Flushes whatever is in self._buffer regardless of chunk_min_chars or
        sentence boundary detection. This ensures the last sentence fragment
        is spoken even if it does not end with a terminator.

        Forge will implement:
        - Guard: if self._degraded or self._closed: return immediately.
        - If self._buffer is non-empty (strip check): call self._speak_chunk(self._buffer).
        - Clear self._buffer to empty string.
        - Log flush at DEBUG (chars flushed).

        Raises:
            Never raises. All errors are logged and handled internally.
        """
        raise NotImplementedError(
            "Forge will implement: guard on degraded/closed; speak any remaining buffer "
            "via self._speak_chunk(); clear buffer; log at DEBUG. Never raise."
        )

    def close(self) -> None:
        """Shut down Tunga cleanly. Safe to call multiple times.

        Closes the ChatterboxClient HTTP session and the playback backend.
        Sets self._closed = True. After close(), feed_chunk() and flush() are no-ops.

        Forge will implement:
        - Guard: if self._closed: return immediately.
        - self._closed = True.
        - Try: call self._client.close() (async-aware: Forge must handle the async context).
        - Try: call self._playback.close().
        - Log close at DEBUG.
        - All exceptions during close are caught and logged — never raised.

        Raises:
            Never raises.
        """
        raise NotImplementedError(
            "Forge will implement: guard on self._closed; set self._closed = True; "
            "close client and playback (catching all exceptions); log at DEBUG. Never raise."
        )

    def _speak_chunk(self, text: str) -> None:
        """Synthesise and play one text chunk. Internal — not part of the public API.

        Forge will implement:
        - Strip the text; if empty after strip: return immediately.
        - Log the chunk at DEBUG (first 60 chars, total length).
        - Call bytes = await self._client.synthesize(text.strip(), ...) using config defaults.
          (Forge must decide: either make Tunga fully async, or run the coroutine in
           asyncio.get_event_loop().run_until_complete() if called from sync context.
           Preferred: make Tunga async; feed_chunk and flush become async methods.)
        - Call self._playback.play(bytes).
        - On ChatterboxError: log WARNING; set self._degraded = True; return.
        - On PlaybackError: log WARNING; set self._degraded = True; return.
        - On any other Exception: log ERROR; set self._degraded = True; return.
        - Never raise.

        NOTE TO FORGE: This method may need to become ``async def _speak_chunk``. If
        Tunga is made fully async, feed_chunk() and flush() become ``async def`` too,
        and Holdvörðr must await them. This is the preferred design — update the public
        signatures in tunga.py and INTERFACE.md when you implement.
        """
        raise NotImplementedError(
            "Forge will implement: strip text; log chunk; call client.synthesize() "
            "(consider making async); call playback.play(); on any error: log WARNING, "
            "set self._degraded = True, return without raising."
        )
