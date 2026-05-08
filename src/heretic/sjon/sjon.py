"""
Sjón orchestrator — L3 Sjón (Vision).

The Sjón class coordinates screen capture (ScreenCaptureBackend), frame
encoding (FrameEncoder), and the throttle guard to implement on-demand
snapshot delivery for v0.5.

Capture trigger model (v0.5 — on-demand only):
    When the user sends a message AND config.sjon.screen.enabled AND
    capability flag ?vision_in is confirmed, the turn loop calls snapshot().
    snapshot() returns a list of data URL strings (one per frame, currently
    always zero or one). The caller attaches these to the user-role message
    as image_url content blocks.

    Periodic interval capture (interval_ms) is NOT active in v0.5 — the field
    is reserved for v0.5.x. The ring buffer (buffer_depth) is also v0.5.x.

Throttle:
    No two captures may occur within min_interval_ms of each other. If snapshot()
    is called within this window, it returns an empty list silently (no error).
    ThrottleRejectedError is available if callers need to distinguish throttle from
    unavailability, but snapshot() itself swallows it and returns [].

Failure model:
    If capture fails (backend unavailable, permission denied, encoding error),
    snapshot() logs a warning and returns []. The ceremony continues without
    a frame. snapshot() NEVER raises — the turn loop may call it unconditionally.

Event emitter:
    The optional event_emitter callable is invoked with SjonActivity pydantic
    models at each capture milestone (capturing, encoding, idle, failed).
    The CLI wires this to None; vebond/serve.py wires it to the EventBus.
    When event_emitter is None, events are simply not emitted (tests + CLI).

Privacy invariant:
    snapshot() NEVER writes raw bytes or PNG frames to disk.
    Only in-memory buffers are used. The returned data URL string may be
    large (base64 PNG), but it is held only in the returned list and the
    message payload — never persisted.

Ref: docs/architecture/LAYER_INTERFACES.md §L3 Sjón.
    docs/TASK_HERETIC_v0.5_FIRST_SIGHT.md §5 (capture trigger model).
    docs/audit/AUDIT_v0.0_INITIAL_DOC_SET.md C-Q-C3 (frame format sealed).
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from typing import TYPE_CHECKING, Callable, Optional

from heretic.sjon.errors import (
    BackendUnavailableError,
    FrameEncodingError,
    PermissionDeniedError,
    ScreenCaptureError,
    SjonError,
)

if TYPE_CHECKING:
    from heretic.sjon.capture import ScreenCaptureBackend
    from heretic.sjon.config_model import SjonConfig
    from heretic.sjon.encoder import FrameEncoder

# Oversize frame threshold: if the PNG exceeds this, we retry at half resolution.
# 4 MB is a generous upper bound — normal 1280x720 PNGs are ~0.3-1.2 MB.
_OVERSIZE_BYTES = 4 * 1024 * 1024


class Sjón:
    """Orchestrator for L3 Sjón (Vision).

    Coordinates capture backend + encoder + throttle guard to implement
    on-demand snapshot for the v0.5 milestone.

    Typical usage:

        backend = best_available(logger, config.sjon.screen)
        encoder = FrameEncoder(
            max_width=config.sjon.screen.max_width,
            max_height=config.sjon.screen.max_height,
            logger=logger,
        )
        sjon = Sjón(config=config.sjon, capture_backend=backend,
                    encoder=encoder, logger=logger)

        # In the turn loop:
        data_urls = await sjon.snapshot()
        # data_urls is [] (unavailable/throttled/error) or ["data:image/png;base64,..."]
    """

    def __init__(
        self,
        config: "SjonConfig",
        capture_backend: "ScreenCaptureBackend",
        encoder: "FrameEncoder",
        logger: logging.Logger | None = None,
        event_emitter: Optional[Callable] = None,
    ) -> None:
        """Initialise the Sjón orchestrator.

        Args:
            config: SjonConfig (screen + webcam sub-configs).
            capture_backend: An instantiated ScreenCaptureBackend. The Sjón
                orchestrator does NOT create the backend — the caller selects
                it via best_available() or provides a test double. This keeps
                the orchestrator testable without mocking module-level imports.
            encoder: An instantiated FrameEncoder. Same injection rationale.
            logger: Logger for capture/encode diagnostics and throttle warnings.
            event_emitter: Optional callable invoked with SjonActivity instances
                at each capture milestone. None = events not emitted (CLI mode).
                vebond/serve.py wires this to EventBus.publish().
        """
        self._config = config
        self._backend = capture_backend
        self._encoder = encoder
        self._logger = logger or logging.getLogger(__name__)
        self._event_emitter = event_emitter

        # Throttle state — guards min_interval_ms.
        # _throttle_lock is initialised lazily on first snapshot() call so that
        # it is always created inside a running event loop (asyncio.Lock requirement).
        self._last_capture_ts: float = 0.0
        self._throttle_lock: Optional[asyncio.Lock] = None

        # Ring buffer — holds the most recent `buffer_depth` data URL strings.
        # deque(maxlen=N) gives O(1) append with automatic oldest-evict on overflow.
        # Used only in continuous mode (v0.5.1+); always present so recent_frames()
        # can be called safely in on-demand mode (returns []).
        self._buffer: deque[str] = deque(maxlen=config.screen.buffer_depth)

        # Continuous capture task slot — populated by start_continuous_capture(),
        # cleared by stop_continuous_capture(). None in on-demand mode.
        self._continuous_task: Optional[asyncio.Task] = None  # type: ignore[type-arg]

        # Buffer lock — lazily created inside the event loop (same pattern as
        # _throttle_lock). Serialises reads/writes to _buffer from concurrent callers.
        self._buffer_lock: Optional[asyncio.Lock] = None

    def _get_lock(self) -> asyncio.Lock:
        """Lazily initialise the throttle asyncio.Lock.

        asyncio.Lock must be created inside a running event loop. We defer
        creation to the first snapshot() call to avoid issues when the Sjón
        instance is created outside an async context (e.g., in synchronous tests).
        """
        if self._throttle_lock is None:
            self._throttle_lock = asyncio.Lock()
        return self._throttle_lock

    def _get_buffer_lock(self) -> asyncio.Lock:
        """Lazily initialise the ring-buffer asyncio.Lock.

        Same lazy-init pattern as _get_lock() — must be created inside a running
        event loop. Used to serialise reads and appends to self._buffer across
        the continuous-capture task and any concurrent recent_frames() caller.
        """
        if self._buffer_lock is None:
            self._buffer_lock = asyncio.Lock()
        return self._buffer_lock

    def _emit(self, state: str) -> None:
        """Emit a SjonActivity event via the event_emitter, if one is configured.

        Swallows all errors — event emission must never crash the capture pipeline.

        Args:
            state: One of "idle", "capturing", "encoding", "failed".
        """
        if self._event_emitter is None:
            return
        try:
            from datetime import datetime
            from heretic.vebond.protocol import SjonActivity, SjonActivityState
            state_enum = SjonActivityState(state)
            event = SjonActivity(state=state_enum, timestamp=datetime.utcnow())
            self._event_emitter(event)
        except Exception as exc:
            # Never let event emission crash the capture pipeline.
            self._logger.debug("Sjón event emission failed (ignored): %s", exc)

    @property
    def is_available(self) -> bool:
        """True if the capture backend reports itself as available.

        Both conditions must be true:
            1. config.sjon.screen.enabled is True (operator has enabled screen capture).
            2. capture_backend.available() is True (OS + deps are present).

        This is a cheap, synchronous check — it does not attempt a capture.
        Callers should check this before calling snapshot() when they need to
        gate UI state or capability flag reporting.

        Returns:
            True if screen capture is both configured and operationally possible.
        """
        return self._config.screen.enabled and self._backend.available()

    async def snapshot(self) -> list[str]:
        """Capture one screen frame on demand and return it as a data URL list.

        This is the primary interface for the v0.5 turn loop. The caller:
            1. Calls snapshot() before building the user message.
            2. If the returned list is non-empty, attaches the data URLs as
               image_url content blocks in the user message.
            3. If the list is empty, sends the message without image content.

        snapshot() NEVER raises. All errors are logged as warnings and the
        empty list is returned. This ensures the turn loop can call it
        unconditionally without guarding against exceptions.

        Throttle: if the time since the last successful capture is less than
        config.sjon.screen.min_interval_ms, the call returns [] immediately
        with a debug-level log (not a warning — throttling is expected behaviour,
        not an error).

        Oversize guard (F-4): if the encoded PNG exceeds 4 MB, we retry with
        half the configured max resolution. If the retry is still oversized,
        we log a warning and return [] rather than sending an enormous payload.

        Returns:
            A list of zero or one inline base64 PNG data URL strings.
            Empty list if: backend unavailable, throttled, permission denied,
            encoding error, or screen capture disabled in config.

        Contract: never raises. Logs warnings for recoverable errors.

        Privacy: never writes bytes to disk. Only in-memory processing.
        """
        # Gate 1: availability check (sync, cheap).
        if not self.is_available:
            return []

        lock = self._get_lock()

        try:
            async with lock:
                # Gate 2: throttle check.
                now = time.monotonic()
                elapsed_ms = (now - self._last_capture_ts) * 1000.0
                if elapsed_ms < self._config.screen.min_interval_ms:
                    self._logger.debug(
                        "Sjón snapshot throttled: %.0fms since last capture "
                        "(min_interval_ms=%d). Returning empty.",
                        elapsed_ms, self._config.screen.min_interval_ms,
                    )
                    return []

                # Emit: capturing state.
                self._emit("capturing")

                # Run the blocking capture in a thread pool executor so we do not
                # block the asyncio event loop during the GDI/Quartz/X11 grab call.
                monitor_index = self._config.screen.monitor_index
                loop = asyncio.get_event_loop()
                try:
                    raw_bgra, w, h = await loop.run_in_executor(
                        None,
                        lambda: self._backend.capture(),
                    )
                except PermissionDeniedError as exc:
                    self._logger.warning(
                        "Sjón snapshot failed — OS denied screen capture permission: %s. "
                        "Grant Screen Recording permission and restart the ceremony.", exc
                    )
                    self._emit("failed")
                    return []
                except (ScreenCaptureError, BackendUnavailableError, SjonError) as exc:
                    self._logger.warning(
                        "Sjón snapshot failed — capture error: %s", exc
                    )
                    self._emit("failed")
                    return []

                # Update throttle timestamp immediately after successful capture.
                self._last_capture_ts = time.monotonic()

                # Emit: encoding state.
                self._emit("encoding")

                # Encode in a thread pool executor (Pillow resize + PNG encode can be slow
                # for large frames — keep the event loop free).
                max_w = self._config.screen.max_width
                max_h = self._config.screen.max_height
                try:
                    png_bytes = await loop.run_in_executor(
                        None,
                        lambda: self._encoder.encode(raw_bgra, w, h),
                    )
                except FrameEncodingError as exc:
                    self._logger.warning(
                        "Sjón snapshot failed — encoding error: %s", exc
                    )
                    self._emit("failed")
                    return []

                # Oversize guard (F-4): retry at half resolution if PNG is too large.
                # We use the injected encoder directly with halved max dimensions,
                # so the retry goes through the same encoder instance (testable via mocks).
                if len(png_bytes) > _OVERSIZE_BYTES:
                    self._logger.warning(
                        "Sjón snapshot: encoded PNG is %.1f MB (threshold %.1f MB). "
                        "Retrying at half resolution.",
                        len(png_bytes) / 1024 / 1024,
                        _OVERSIZE_BYTES / 1024 / 1024,
                    )
                    half_w = max_w // 2
                    half_h = max_h // 2
                    try:
                        png_bytes = await loop.run_in_executor(
                            None,
                            lambda: self._encoder.encode(
                                raw_bgra,
                                w,
                                h,
                                max_width_override=half_w,
                                max_height_override=half_h,
                            ),
                        )
                    except FrameEncodingError as exc:
                        self._logger.warning(
                            "Sjón snapshot: half-resolution retry also failed: %s. "
                            "Dropping frame.", exc
                        )
                        self._emit("failed")
                        return []

                    if len(png_bytes) > _OVERSIZE_BYTES:
                        self._logger.warning(
                            "Sjón snapshot: half-resolution PNG still %.1f MB. "
                            "Dropping frame to protect token budget.",
                            len(png_bytes) / 1024 / 1024,
                        )
                        self._emit("failed")
                        return []

                # Convert to data URL — pure Python / stdlib, no blocking I/O.
                data_url = self._encoder.to_data_url(png_bytes)

                # Emit: idle (capture + encode complete, frame ready).
                self._emit("idle")

                self._logger.debug(
                    "Sjón snapshot complete: %dx%d source, PNG %d bytes, data_url %d chars.",
                    w, h, len(png_bytes), len(data_url),
                )
                return [data_url]

        except asyncio.CancelledError:
            # Let CancelledError propagate — it is not a capture failure.
            self._emit("failed")
            raise
        except Exception as exc:
            # Catch-all: snapshot() must never propagate to the turn loop.
            self._logger.warning(
                "Sjón snapshot failed unexpectedly (turn continues without frame): %s",
                exc, exc_info=True,
            )
            self._emit("failed")
            return []

    async def start_continuous_capture(self) -> None:
        """Start the background periodic capture task (v0.5.1).

        Raises:
            NotImplementedError: Forge will implement this method.

        Forge implementation notes:
            - Create an asyncio.Task that loops with asyncio.sleep(interval_ms/1000)
              between iterations.
            - Each iteration: call snapshot() (captures + encodes); if a data URL is
              returned, append it to self._buffer under self._get_buffer_lock().
            - Backpressure-skip: if the previous iteration's capture is still in flight
              (detected via an in-flight flag), skip the current tick rather than queuing.
            - Throttle is still enforced: snapshot() already enforces min_interval_ms.
            - Emit SjonActivity(state=CONTINUOUS_RUNNING) after the task starts.
            - Store the task in self._continuous_task for cancellation by
              stop_continuous_capture().
            - Idempotent: if a task is already running, log a warning and return.
        """
        raise NotImplementedError(
            "Forge will implement: background asyncio.Task that loops with "
            "asyncio.sleep(interval_ms/1000), calls capture+encode via snapshot(), "
            "appends data URLs to self._buffer under _get_buffer_lock(); "
            "backpressure-skip if previous tick is still in flight; "
            "throttle still enforced via snapshot(); "
            "emits SjonActivity CONTINUOUS_RUNNING on start; "
            "stores task in self._continuous_task; idempotent."
        )

    async def stop_continuous_capture(self) -> None:
        """Stop the background periodic capture task cleanly (v0.5.1).

        Raises:
            NotImplementedError: Forge will implement this method.

        Forge implementation notes:
            - Cancel self._continuous_task if it is not None.
            - Await the task with asyncio.shield or try/except CancelledError so that
              the task is fully finished before this coroutine returns.
            - Set self._continuous_task = None.
            - Emit SjonActivity(state=CONTINUOUS_STOPPED).
            - Idempotent: if no task is running, return without error.
        """
        raise NotImplementedError(
            "Forge will implement: cancel self._continuous_task; await task completion; "
            "set self._continuous_task = None; emit SjonActivity CONTINUOUS_STOPPED; "
            "idempotent (no-op if no task running)."
        )

    def recent_frames(self, n: int | None = None) -> list[str]:
        """Return the most recent N data URL strings from the ring buffer (v0.5.1).

        Raises:
            NotImplementedError: Forge will implement this method.

        Forge implementation notes:
            - If n is None, return all frames currently in self._buffer (oldest first).
            - If n is specified, return the last n frames (most-recently appended),
              oldest first within the returned slice.
            - This method is synchronous — callers in the turn loop do not need to
              await it. Buffer access is guarded by self._get_buffer_lock() in async
              contexts; this sync accessor takes a snapshot of the deque safely via
              list(self._buffer) (thread-safe for reads; asyncio.Lock prevents
              concurrent modification in the event loop).
            - Returns [] if the buffer is empty or continuous mode has never run.

        Args:
            n: Maximum number of frames to return. None = return all buffered frames.

        Returns:
            List of inline base64 PNG data URL strings, ordered oldest-to-newest.
        """
        raise NotImplementedError(
            "Forge will implement: return list(self._buffer)[-n:] if n else "
            "list(self._buffer); ordered oldest-to-newest; returns [] if buffer empty."
        )

    async def close(self) -> None:
        """Release all resources held by Sjón (backend + encoder).

        Called during ceremony shutdown (Slokna) before the process exits.
        Must be idempotent. Must not raise.

        v0.5.1 additions: cancels the continuous capture task if one is running
        (privacy invariant — no frames may persist past Slokna); clears self._buffer.
        """
        # Stop continuous capture task if running (v0.5.1 — Forge wires this in Wave 2).
        # Until Forge implements stop_continuous_capture(), we cancel the task slot
        # directly to satisfy the privacy invariant: no frames persist past close().
        if self._continuous_task is not None and not self._continuous_task.done():
            self._continuous_task.cancel()
            try:
                await self._continuous_task
            except (asyncio.CancelledError, Exception) as exc:
                self._logger.debug(
                    "Sjón.close(): continuous task cancelled (expected): %s", exc
                )
            self._continuous_task = None

        # Clear ring buffer — privacy invariant: buffered frames must not persist
        # past ceremony end (Slokna). Ref: TASK_HERETIC_v0.5.1_PERIODIC_SIGHT §7.
        self._buffer.clear()

        try:
            self._backend.close()
        except Exception as exc:
            self._logger.warning(
                "Sjón.close(): error closing capture backend (ignored): %s", exc
            )
        self._last_capture_ts = 0.0
        self._logger.info("Sjón closed.")
