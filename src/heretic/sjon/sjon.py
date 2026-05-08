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
import base64
import io
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
    from heretic.sjon.config_model import SjonConfig, SjonWebcamConfig
    from heretic.sjon.encoder import FrameEncoder
    from heretic.sjon.webcam import WebcamCaptureBackend

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

        # Webcam backend slot (v0.5.2 — scaffold).
        # None until Forge Wave 2 wires best_available(webcam) into __init__ or
        # a future set_webcam_backend() call. snapshot_webcam() checks for None
        # and raises NotImplementedError when the backend is not yet injected.
        # Forge Wave 2 will either add webcam_backend as a constructor parameter
        # (matching the capture_backend injection pattern) or lazy-init it here.
        self._webcam_backend: Optional["WebcamCaptureBackend"] = None

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

        Spawns an asyncio.Task that loops at config.screen.interval_ms, captures one
        frame per tick, encodes it, and appends the resulting data URL to the ring buffer.

        Backpressure: if the previous tick's capture+encode is still in flight, the
        current tick is SKIPPED (not queued) so we never pile up outstanding captures
        under system load.

        Throttle: snapshot() enforces min_interval_ms even inside the continuous loop,
        guarding against the edge case where interval_ms < min_interval_ms.

        Idempotent: a second call while a task is already running logs a debug message
        and returns without spawning a second task.

        Emits SjonActivity(state=CONTINUOUS_RUNNING) once the task is scheduled.
        """
        if self._continuous_task is not None and not self._continuous_task.done():
            self._logger.debug(
                "Sjon.start_continuous_capture(): task already running — no-op."
            )
            return

        self._logger.info(
            "Sjon: starting continuous capture (interval_ms=%d, buffer_depth=%d).",
            self._config.screen.interval_ms,
            self._config.screen.buffer_depth,
        )
        self._continuous_task = asyncio.create_task(self._continuous_loop())
        self._emit("continuous_running")

    async def _continuous_loop(self) -> None:
        """Background continuous capture loop — runs at interval_ms per tick.

        Lifecycle:
            - Sleeps for interval_ms at the start of each iteration so the first
              capture fires after one interval (not immediately at start).
            - On each tick: checks backpressure, captures + encodes, pushes to buffer.
            - On capture or encode failure: logs a warning and emits FAILED for that
              tick, then continues the loop (never crashes).
            - On asyncio.CancelledError: exits cleanly (task was stopped).

        Privacy: data URLs are written only to self._buffer (in-memory deque).
                 They are never written to disk. Buffer is cleared on close().
        """
        _capture_in_flight: bool = False
        _last_buffer_full_emitted: bool = False

        interval_s = self._config.screen.interval_ms / 1000.0

        try:
            while True:
                await asyncio.sleep(interval_s)

                # Backpressure check: skip this tick if previous capture still running.
                # Prevents capture queuing under sustained system load.
                if _capture_in_flight:
                    self._logger.debug(
                        "Sjon continuous loop: backpressure skip (previous capture in flight)."
                    )
                    continue

                _capture_in_flight = True
                try:
                    # snapshot() enforces min_interval_ms throttle and never raises.
                    # It returns [] on throttle, error, or unavailability — all safe.
                    urls = await self.snapshot()
                    if urls:
                        # Push to ring buffer under lock for write ordering.
                        lock = self._get_buffer_lock()
                        async with lock:
                            # Check if we're about to fill the buffer.
                            at_capacity = len(self._buffer) >= self._buffer.maxlen  # type: ignore[arg-type]
                            self._buffer.append(urls[0])
                            # Emit BUFFER_FULL once per fill cycle to avoid event flooding.
                            if at_capacity and not _last_buffer_full_emitted:
                                self._emit("buffer_full")
                                _last_buffer_full_emitted = True
                            elif not at_capacity:
                                # Reset the flag once the buffer has room again.
                                _last_buffer_full_emitted = False
                    else:
                        # snapshot() returned [] — capture failed or was throttled.
                        # snapshot() already emitted FAILED if it was a capture error.
                        self._logger.debug(
                            "Sjon continuous loop: snapshot returned empty (throttled or failed)."
                        )
                finally:
                    _capture_in_flight = False

        except asyncio.CancelledError:
            # Clean exit — stop_continuous_capture() cancelled us.
            self._logger.debug("Sjon continuous loop: cancelled cleanly.")
            raise
        except Exception as exc:
            # Unexpected error in the loop itself — log and let the loop die.
            # The ceremony continues; the eye goes dark but does not crash the process.
            self._logger.warning(
                "Sjon continuous loop: unexpected error (loop terminated): %s", exc, exc_info=True
            )

    async def stop_continuous_capture(self) -> None:
        """Stop the background periodic capture task cleanly (v0.5.1).

        Cancels self._continuous_task, awaits its completion (absorbing CancelledError),
        then sets the slot to None and emits CONTINUOUS_STOPPED.

        Idempotent: a call when no task is running is a safe no-op.
        """
        if self._continuous_task is None:
            return

        task = self._continuous_task
        if not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception) as exc:
                self._logger.debug(
                    "Sjon.stop_continuous_capture(): task finished (expected): %s", exc
                )

        self._continuous_task = None
        self._emit("continuous_stopped")
        self._logger.info("Sjon: continuous capture stopped.")

    def recent_frames(self, n: int | None = None) -> list[str]:
        """Return the most recent N data URL strings from the ring buffer (v0.5.1).

        Synchronous read — takes a snapshot of the deque contents which is safe because:
        - The deque is only appended to from within the asyncio event loop's continuous
          task, which cannot run concurrently with a synchronous call.
        - The buffer lock guards WRITE ordering between the continuous task and any
          future concurrent async writers; this sync reader just needs the snapshot.

        Ordering: oldest frame first, most recent frame last (natural deque order).

        Args:
            n: Maximum number of frames to return.
               None -> return all frames currently in the buffer.
               0    -> return [] (defensive; None vs 0 ambiguity guard).
               > buffer_depth -> returns up to buffer contents with no padding.

        Returns:
            List of inline base64 PNG data URL strings. Empty list if buffer is empty
            or continuous mode has never run.
        """
        if n == 0:
            return []
        snapshot = list(self._buffer)
        if n is None:
            return snapshot
        # Return last n frames (most recently appended), preserving oldest-first order.
        return snapshot[-n:] if len(snapshot) > n else snapshot

    async def close(self) -> None:
        """Release all resources held by Sjón (backend + encoder).

        Called during ceremony shutdown (Slokna) before the process exits.
        Must be idempotent. Must not raise.

        v0.5.1: delegates continuous task teardown to stop_continuous_capture()
        (which emits CONTINUOUS_STOPPED and awaits full cancellation), then clears
        the ring buffer to satisfy the privacy invariant: no frames persist past Slokna.

        Privacy invariant: buffered frames are NEVER written to disk; they live in
        self._buffer (a deque) and are explicitly cleared here at ceremony end.
        Ref: TASK_HERETIC_v0.5.1_PERIODIC_SIGHT §7.
        """
        # Stop continuous capture task cleanly via the named method.
        # stop_continuous_capture() is idempotent — safe to call when no task running.
        try:
            await self.stop_continuous_capture()
        except Exception as exc:
            self._logger.warning(
                "Sjon.close(): error stopping continuous task (ignored): %s", exc
            )

        # Clear ring buffer — privacy invariant: buffered frames must not persist
        # past ceremony end (Slokna). Ref: TASK_HERETIC_v0.5.1_PERIODIC_SIGHT §7.
        self._buffer.clear()

        try:
            self._backend.close()
        except Exception as exc:
            self._logger.warning(
                "Sjon.close(): error closing capture backend (ignored): %s", exc
            )
        self._last_capture_ts = 0.0
        self._logger.info("Sjon closed.")

    # ---------------------------------------------------------------------------
    # Webcam snapshot (v0.5.2 — implemented by Forge Wave 2)
    # ---------------------------------------------------------------------------

    async def snapshot_webcam(self) -> list[str]:
        """Capture one webcam frame on demand and return it as a data URL list (v0.5.2).

        This is the webcam parallel of snapshot() for the v0.5.2 on-demand model.
        Mirrors snapshot()'s contract exactly:
            - Returns a list of zero or one data URL strings.
            - NEVER raises — all errors are caught and [] is returned.
            - Does not write frames to disk.
            - Respects sjon.webcam.enabled; returns [] immediately when disabled.

        Data URL format:
            When sjon.webcam.format is "jpeg":
                "data:image/jpeg;base64,<encoded_jpeg>"
            When sjon.webcam.format is "png":
                "data:image/png;base64,<encoded_png>"

        attach_policy governs how the caller combines this list with the screen
        snapshot list. snapshot_webcam() itself is unaware of attach_policy — it
        captures and returns. The CLI / Bifröst turn loop applies the policy.

        Returns:
            A list of zero or one inline base64 data URL strings (JPEG or PNG per config).
            Empty list if: webcam disabled, backend unavailable, capture error, encode error.

        Contract: never raises. Logs warnings for recoverable errors.

        Privacy: never writes webcam frames to disk. Physical-presence capture —
        only proceed when sjon.webcam.enabled is explicitly True (operator opt-in).

        Ref: src/heretic/sjon/INTERFACE.md §Webcam capture.
             TASK_HERETIC_v0.5.2_WEBCAM.md §Wave 2.
        """
        try:
            # Gate 1: operator opt-in check.
            if not self._config.webcam.enabled:
                return []

            # Gate 2: backend availability check.
            if self._webcam_backend is None or not self._webcam_backend.available():
                return []

            # Run the blocking cv2.VideoCapture.read() in a thread pool executor
            # to keep the asyncio event loop free during device I/O.
            loop = asyncio.get_event_loop()
            device_index = self._config.webcam.device_index
            rgb_bytes, w, h = await loop.run_in_executor(
                None,
                lambda: self._webcam_backend.capture(device_index),  # type: ignore[union-attr]
            )

            # Encode the raw RGB frame to JPEG or PNG → base64 data URL.
            # Runs in executor too — Pillow encode can be slow for large frames.
            webcam_cfg = self._config.webcam
            encoded_bytes, mime_type = await loop.run_in_executor(
                None,
                lambda: self._encode_webcam_frame(rgb_bytes, w, h, webcam_cfg),
            )

            data_url = (
                f"data:{mime_type};base64,"
                + base64.b64encode(encoded_bytes).decode("ascii")
            )

            self._logger.debug(
                "Sjón webcam snapshot: %dx%d source, %s %d bytes, data_url %d chars.",
                w, h, mime_type, len(encoded_bytes), len(data_url),
            )
            return [data_url]

        except asyncio.CancelledError:
            # Let CancelledError propagate — not a capture failure.
            raise
        except Exception as exc:
            # Catch-all: snapshot_webcam() must never propagate to the turn loop.
            self._logger.warning(
                "Sjón webcam snapshot failed (turn continues without webcam frame): %s",
                exc, exc_info=True,
            )
            return []

    @staticmethod
    def _encode_webcam_frame(
        rgb_bytes: bytes,
        width: int,
        height: int,
        webcam_cfg: "SjonWebcamConfig",
    ) -> tuple[bytes, str]:
        """Encode raw RGB frame bytes to JPEG or PNG, resized to fit max dimensions.

        This is a pure synchronous helper intended to run in a thread pool executor.
        Uses Pillow for resize + encode, matching the FrameEncoder path for screen capture.

        BGR→RGB conversion has already been applied by OpenCvBackend.capture().
        This method receives clean RGB bytes.

        Args:
            rgb_bytes: Raw RGB pixel data (3 bytes/pixel, row-major), width×height.
            width:     Frame width in pixels.
            height:    Frame height in pixels.
            webcam_cfg: SjonWebcamConfig providing max_width, max_height, format, jpeg_quality.

        Returns:
            (encoded_bytes, mime_type) where mime_type is "image/jpeg" or "image/png".

        Raises:
            Any Pillow error on encode failure — callers must wrap in try/except.
        """
        from PIL import Image  # noqa: PLC0415 — Pillow is [vision] optional dep

        # Reconstruct PIL Image from raw RGB bytes.
        img = Image.frombytes("RGB", (width, height), rgb_bytes)

        # Resize to fit within max dimensions, preserving aspect ratio.
        max_w = webcam_cfg.max_width
        max_h = webcam_cfg.max_height
        if img.width > max_w or img.height > max_h:
            img.thumbnail((max_w, max_h), Image.LANCZOS)

        # Encode to JPEG or PNG.
        buf = io.BytesIO()
        if webcam_cfg.format == "jpeg":
            img.save(buf, "JPEG", quality=webcam_cfg.jpeg_quality, optimize=True)
            mime_type = "image/jpeg"
        else:
            img.save(buf, "PNG")
            mime_type = "image/png"

        return buf.getvalue(), mime_type
