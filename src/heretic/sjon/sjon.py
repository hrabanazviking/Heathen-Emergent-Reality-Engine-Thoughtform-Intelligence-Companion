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

Ref: docs/architecture/LAYER_INTERFACES.md §L3 Sjón.
    docs/TASK_HERETIC_v0.5_FIRST_SIGHT.md §5 (capture trigger model).
    docs/audit/AUDIT_v0.0_INITIAL_DOC_SET.md C-Q-C3 (frame format sealed).
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from heretic.sjon.errors import (
    BackendUnavailableError,
    FrameEncodingError,
    PermissionDeniedError,
    ScreenCaptureError,
    SjonError,
    ThrottleRejectedError,
)

if TYPE_CHECKING:
    from heretic.sjon.capture import ScreenCaptureBackend
    from heretic.sjon.config_model import SjonConfig
    from heretic.sjon.encoder import FrameEncoder


class Sjón:
    """Orchestrator for L3 Sjón (Vision).

    Coordinates capture backend + encoder + throttle guard to implement
    on-demand snapshot for the v0.5 milestone.

    Typical usage (after Forge implements the stubs):

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

    All async methods are NotImplementedError stubs in this scaffold.
    """

    def __init__(
        self,
        config: "SjonConfig",
        capture_backend: "ScreenCaptureBackend",
        encoder: "FrameEncoder",
        logger: logging.Logger | None = None,
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
        """
        self._config = config
        self._backend = capture_backend
        self._encoder = encoder
        self._logger = logger or logging.getLogger(__name__)

        # Throttle state — guards min_interval_ms.
        # Protected by _throttle_lock to ensure correctness under asyncio task
        # concurrency (not expected in normal use, but defensive).
        self._last_capture_ts: float = 0.0
        self._throttle_lock: asyncio.Lock | None = None
        # Forge: initialise _throttle_lock in an async context or lazily on first
        # snapshot() call (asyncio.Lock must be created in a running event loop).

    @property
    def is_available(self) -> bool:
        """True if the capture backend reports itself as available.

        This is a cheap, synchronous check — it does not attempt a capture.
        Callers should check this before calling snapshot() when they need to
        gate UI state or capability flag reporting.

        Returns:
            True if config.sjon.screen.enabled AND capture_backend.available().
        """
        raise NotImplementedError(
            "Sjón.is_available: "
            "return self._config.screen.enabled and self._backend.available(). "
            "Both conditions must be True. backend.available() must not raise."
        )

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

        Returns:
            A list of zero or one inline base64 PNG data URL strings.
            Empty list if: backend unavailable, throttled, permission denied,
            encoding error, or screen capture disabled in config.

        Contract: never raises. Log warnings for recoverable errors.
        """
        raise NotImplementedError(
            "Sjón.snapshot(): "
            "1. Check is_available — if False, return []. "
            "2. Ensure _throttle_lock is initialised (asyncio.Lock()). "
            "3. Acquire _throttle_lock. "
            "4. Check throttle: if (time.monotonic() - _last_capture_ts) * 1000 < "
            "   config.screen.min_interval_ms: release lock, return []. "
            "5. Run capture in executor: loop = asyncio.get_event_loop(); "
            "   raw, w, h = await loop.run_in_executor(None, self._backend.capture). "
            "6. Update _last_capture_ts = time.monotonic() (before releasing lock). "
            "7. Release _throttle_lock. "
            "8. Encode: data_url = self._encoder.encode_to_data_url(raw, w, h). "
            "9. Return [data_url]. "
            "10. Catch PermissionDeniedError -> warn + return []. "
            "    Catch ScreenCaptureError, BackendUnavailableError -> warn + return []. "
            "    Catch FrameEncodingError -> warn + return []. "
            "    Catch Exception -> warn + return [] (never propagate). "
            "All catches must log the error message at WARNING level."
        )

    async def close(self) -> None:
        """Release all resources held by Sjón (backend + encoder).

        Called during ceremony shutdown (Slokna) before the process exits.
        Must be idempotent. Must not raise.
        """
        raise NotImplementedError(
            "Sjón.close(): "
            "try: self._backend.close() — wrap with logged warning, do not raise. "
            "Clear _last_capture_ts = 0.0. "
            "Log info: 'Sjón closed.'"
        )
