"""
Screen capture backends — L3 Sjón substrate.

Defines the ScreenCaptureBackend abstract base class and three concrete
implementations:

- MssBackend: primary cross-platform backend using the ``mss`` library
  (optional dependency — in [vision] extra). MIT licensed, lightweight,
  returns raw BGRA bytes. Preferred when available.
- NullBackend: always-unavailable silent stub. Used as a sentinel so that
  the factory chain always returns a backend instance, never None. Ceremonies
  that cannot capture degrade gracefully rather than crashing.

Factory:
    best_available(logger, config) selects the highest-priority available backend.

Selection order:
    1. MssBackend — if mss is importable and screen access is possible.
    2. NullBackend — silent fallback; logs a warning.

Mirrors the AudioPlayback / ScreenCaptureBackend pattern from rodd.playback.

Architectural decision: mss is the [vision] optional extra, not a core dep.
``pip install heretic`` works on headless machines; only
``pip install heretic[vision]`` pulls in mss and Pillow.
See pyproject.toml [vision] extra.

Ref: docs/architecture/LAYER_INTERFACES.md §L3 Sjón.
"""

from __future__ import annotations

import abc
import logging
from typing import TYPE_CHECKING

from heretic.sjon.errors import BackendUnavailableError, ScreenCaptureError

if TYPE_CHECKING:
    from heretic.sjon.config_model import SjonScreenConfig


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class ScreenCaptureBackend(abc.ABC):
    """Contract for all screen capture backends.

    Implementations receive a SjonScreenConfig and return raw image bytes
    (BGRA or BGR depending on the backend — the FrameEncoder normalises the
    format before PNG encoding).

    Lifecycle:
        backend = ScreenCaptureBackend.best_available(logger, config)
        if not backend.available():
            # degrade gracefully — no screen capture on this machine
            ...
        raw_bytes, width, height = backend.capture()
        backend.close()

    The capture() method is synchronous. Callers run it in a thread pool
    executor when they need non-blocking behaviour inside an async context.
    """

    @classmethod
    def best_available(
        cls,
        logger: logging.Logger,
        config: "SjonScreenConfig",
    ) -> "ScreenCaptureBackend":
        """Return the best available screen capture backend for the current environment.

        Selection order:
            1. MssBackend — if mss is importable and available() returns True.
            2. NullBackend — silent fallback; logs a warning.

        No network access. No side effects beyond logging.

        Args:
            logger: Logger for backend selection diagnostics.
            config: SjonScreenConfig driving monitor selection and crop.

        Returns:
            A ScreenCaptureBackend instance. Never None — NullBackend is the
            final fallback.
        """
        raise NotImplementedError(
            "ScreenCaptureBackend.best_available() must be implemented. "
            "Forge implements the full selection chain in this classmethod."
        )

    @abc.abstractmethod
    def available(self) -> bool:
        """Return True if this backend can successfully capture on the current machine.

        Must not raise. Must not make network calls. May probe the import system
        and the OS screen capture permission, but must be cheap to call — it is
        invoked during backend selection, not only at capture time.

        Returns:
            True if capture() is expected to succeed on this machine.
            False if this backend cannot function (missing dep, no permission, etc.).
        """

    @abc.abstractmethod
    def capture(self) -> tuple[bytes, int, int]:
        """Capture a single screen frame and return raw image bytes.

        Returns:
            A tuple of (raw_bytes, width, height) where raw_bytes is the raw
            pixel data (format depends on backend — BGRA for mss), width and
            height are the actual captured dimensions in pixels.

        Raises:
            ScreenCaptureError: if the capture operation fails for any reason
                other than permission denial.
            PermissionDeniedError: if the OS denies screen capture permission
                at capture time (as opposed to at available() probe time).
            BackendUnavailableError: if the backend is no longer available
                at capture time (e.g., device was disconnected).
        """

    @abc.abstractmethod
    def close(self) -> None:
        """Release any OS resources held by this backend.

        Must be idempotent. Must not raise. Called during ceremony shutdown
        (Slokna) and on graceful close of the Sjón orchestrator.
        """


# ---------------------------------------------------------------------------
# MssBackend
# ---------------------------------------------------------------------------

class MssBackend(ScreenCaptureBackend):
    """Primary screen capture backend using the ``mss`` library (MIT, cross-platform).

    mss returns raw BGRA pixel data. The FrameEncoder (encoder.py) converts
    BGRA to RGB before PNG encoding.

    Cross-platform support:
        - Windows: GDI capture
        - macOS: Quartz capture (requires Screen Recording permission in macOS Privacy)
        - Linux: X11 or XRandR capture (requires DISPLAY environment variable)

    This backend is selected only when ``mss`` is importable (in the [vision] extra).

    All methods are NotImplementedError stubs — Forge implements the full mss API
    integration. The stub messages describe what each method must do.

    Ref: docs/TASK_HERETIC_v0.5_FIRST_SIGHT.md §3 (mss decision).
    """

    def __init__(
        self,
        config: "SjonScreenConfig",
        logger: logging.Logger,
    ) -> None:
        """Initialise MssBackend.

        Args:
            config: SjonScreenConfig providing monitor_index and crop settings.
            logger: Logger for capture diagnostics and warnings.

        Note: Does NOT acquire any OS resource at init time. The mss context
        manager is created per-capture (or kept open across captures — Forge decides
        based on mss lifecycle docs).
        """
        self._config = config
        self._logger = logger
        self._mss_instance: object | None = None  # type: ignore[assignment]
        # Forge: replace object with mss.MssBase when mss is imported.

    def available(self) -> bool:
        """Return True if mss is importable and basic screen access is possible.

        Probe order (no side effects beyond import attempt):
            1. Attempt to import mss.
            2. If import fails -> return False (dep not installed).
            3. Attempt a cheap probe (e.g. mss.mss().__enter__() and immediately close).
               If the probe raises a PermissionError or mss-specific exception -> return False.
            4. Return True.

        Must not raise. Must not leave an open mss instance.
        """
        raise NotImplementedError(
            "MssBackend.available(): import mss; attempt a lightweight probe to "
            "confirm the OS allows screen capture; return True/False without raising. "
            "Catch mss.exception.ScreenShotError, PermissionError, and ImportError."
        )

    def capture(self) -> tuple[bytes, int, int]:
        """Capture one frame using mss.

        Implementation contract:
            - Use self._config.monitor_index to select the monitor.
            - If monitor_index is out of range, clamp to the highest available and warn.
            - If self._config.crop is set, apply the sub-region to the mss grab call.
            - Return (raw_bgra_bytes, width, height).
            - Raise PermissionDeniedError on macOS TCC denial (mss raises ScreenShotError
              with 'permission' in the message on macOS 10.15+).
            - Raise ScreenCaptureError on any other mss failure.

        Returns:
            (raw_bytes, width, height) — BGRA pixel data + frame dimensions.

        Raises:
            PermissionDeniedError: OS denied screen capture permission.
            ScreenCaptureError: any other capture failure (device error, mss crash, etc.).
            BackendUnavailableError: mss is no longer importable or initializable.
        """
        raise NotImplementedError(
            "MssBackend.capture(): use mss.mss() context manager; call grab() with "
            "the configured monitor and optional crop region; return "
            "(bytes(sct_img.bgra), sct_img.width, sct_img.height). "
            "Wrap mss.exception.ScreenShotError -> ScreenCaptureError. "
            "Detect permission denial from macOS TCC error message."
        )

    def close(self) -> None:
        """Close the mss context manager if one is held open, releasing OS resources.

        Must be idempotent. Must not raise.
        """
        raise NotImplementedError(
            "MssBackend.close(): if self._mss_instance is not None, call its "
            "__exit__() or .close() method (check mss API). Set to None afterward. "
            "Wrap any exception with a logged warning — do not propagate."
        )


# ---------------------------------------------------------------------------
# NullBackend
# ---------------------------------------------------------------------------

class NullBackend(ScreenCaptureBackend):
    """Always-unavailable silent stub backend.

    NullBackend exists so that the factory chain always returns a backend
    instance rather than None. Code that calls best_available() and then
    checks available() will receive False from NullBackend and can degrade
    gracefully without needing to handle a None backend.

    capture() raises BackendUnavailableError to make misconfiguration visible —
    if code calls capture() on a NullBackend without first checking available(),
    the error message is explicit.
    """

    def available(self) -> bool:
        """Always returns False — this backend cannot capture anything."""
        return False

    def capture(self) -> tuple[bytes, int, int]:
        """Always raises BackendUnavailableError.

        This method should never be called in normal operation because code
        is expected to check available() before calling capture(). The error
        makes any incorrect usage immediately visible.

        Raises:
            BackendUnavailableError: always.
        """
        raise BackendUnavailableError(
            "NullBackend.capture() called — no screen capture backend is available "
            "on this machine. Install the [vision] extra (mss + Pillow) and ensure "
            "screen recording permission is granted. Ref: LAYER_INTERFACES.md §L3."
        )

    def close(self) -> None:
        """No-op — NullBackend holds no OS resources."""


# ---------------------------------------------------------------------------
# Factory (full implementation deferred to Forge)
# ---------------------------------------------------------------------------

def best_available(
    logger: logging.Logger,
    config: "SjonScreenConfig",
) -> ScreenCaptureBackend:
    """Select and return the best available screen capture backend.

    Module-level factory function. Mirrors AudioPlayback.best_available() from
    rodd.playback but as a standalone function (not a classmethod) for clarity.

    Selection order:
        1. MssBackend — if mss is importable and MssBackend.available() is True.
        2. NullBackend — always-unavailable fallback with warning.

    Args:
        logger: Logger for backend selection diagnostics.
        config: SjonScreenConfig driving the backend probe and configuration.

    Returns:
        A ScreenCaptureBackend instance. Never None.
    """
    raise NotImplementedError(
        "best_available(): instantiate MssBackend(config, logger); if backend.available() "
        "return it with an info log. Otherwise log a warning explaining mss is not installed "
        "or screen permission is denied. Return NullBackend() as the final fallback. "
        "This mirrors AudioPlayback.best_available() in rodd/playback.py."
    )
