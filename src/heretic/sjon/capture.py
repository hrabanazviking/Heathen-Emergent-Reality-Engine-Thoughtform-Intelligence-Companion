"""
Screen capture backends — L3 Sjón substrate.

Defines the ScreenCaptureBackend abstract base class and two concrete
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
import threading
from typing import TYPE_CHECKING

from heretic.sjon.errors import (
    BackendUnavailableError,
    PermissionDeniedError,
    ScreenCaptureError,
)

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
        # Delegate to the module-level factory for symmetry with rodd.playback
        return best_available(logger, config)

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
    BGRA to RGB before PNG encoding using Pillow's "BGRX" raw decoder mode
    (BGRX = BGR with ignored alpha byte, which is exactly BGRA without the alpha).

    Cross-platform support:
        - Windows: GDI capture
        - macOS: Quartz capture (requires Screen Recording permission in macOS Privacy)
        - Linux: X11 or XRandR capture (requires DISPLAY environment variable)

    This backend is selected only when ``mss`` is importable (in the [vision] extra).

    Thread safety: capture() uses a per-instance lock to serialise concurrent calls.
    The mss instance is created lazily on first capture and reused across calls
    to avoid the overhead of creating a new context for every frame.

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

        Note: Does NOT acquire any OS resource at init time. The mss instance
        is created lazily on the first capture() call.
        """
        self._config = config
        self._logger = logger
        self._mss_instance: object | None = None
        # Lock guards the lazy mss instance and serialises capture() calls.
        # Both threading.Lock (for sync tests) and asyncio contexts are safe
        # because capture() is always called from run_in_executor (a thread).
        self._lock = threading.Lock()

    def available(self) -> bool:
        """Return True if mss is importable and basic screen access is possible.

        Probe order (no side effects beyond import attempt):
            1. Attempt to import mss and PIL.
            2. If import fails -> return False (dep not installed).
            3. Attempt a cheap probe: open mss.mss() context, read monitors,
               confirm at least one monitor is present, close context.
               If the probe raises any exception -> return False.
            4. Return True.

        Must not raise. Must not leave an open mss instance after return.
        """
        try:
            import mss  # noqa: F401
            from PIL import Image  # noqa: F401
            # Probe: verify mss can enumerate monitors without crashing.
            # mss.mss() returns a context-manager-capable instance.
            # We open, read monitors, and close immediately.
            with mss.mss() as sct:
                monitors = sct.monitors
                # monitors[0] is the "all monitors" virtual — always present.
                # monitors[1+] are individual screens. No real monitors -> degraded.
                if not monitors or len(monitors) < 1:
                    self._logger.warning(
                        "MssBackend.available(): mss reports no monitors — backend unavailable."
                    )
                    return False
            return True
        except ImportError:
            self._logger.debug(
                "MssBackend.available(): mss or Pillow not installed — backend unavailable. "
                "Install heretic[vision] to enable screen capture."
            )
            return False
        except Exception as exc:
            self._logger.debug(
                "MssBackend.available(): probe failed (%s) — backend unavailable.", exc
            )
            return False

    def capture(self) -> tuple[bytes, int, int]:
        """Capture one frame using mss.

        Implementation contract:
            - Use self._config.monitor_index to select the monitor.
              mss.monitors[0] = "all monitors" virtual; mss.monitors[1+] = individual.
              The config's monitor_index 0 maps to the primary screen (mss index 1).
            - If monitor_index is out of range, clamp to the highest available and warn.
            - If self._config.crop is set, apply the sub-region to the mss grab call.
            - Returns (raw_bgra_bytes, width, height).
            - Raises PermissionDeniedError on macOS TCC denial (mss raises ScreenShotError
              with 'permission' in the message on macOS 10.15+).
            - Raises ScreenCaptureError on any other mss failure.

        Returns:
            (raw_bytes, width, height) — BGRA pixel data + frame dimensions.

        Raises:
            PermissionDeniedError: OS denied screen capture permission.
            ScreenCaptureError: any other capture failure.
            BackendUnavailableError: mss is not importable.
        """
        try:
            import mss
            import mss.exception
        except ImportError as exc:
            raise BackendUnavailableError(
                "mss is not installed. Install heretic[vision]."
            ) from exc

        with self._lock:
            try:
                # Lazy-init mss instance — reuse across captures for efficiency.
                if self._mss_instance is None:
                    self._mss_instance = mss.mss().__enter__()

                sct = self._mss_instance

                # monitors[0] = virtual "all monitors" bounding box.
                # monitors[1] = primary monitor.
                # config.monitor_index is 0-based where 0 = primary (mss index 1).
                monitors = sct.monitors
                # Map config index -> mss index: config 0 -> mss 1 (primary)
                mss_index = self._config.monitor_index + 1
                max_mss_index = len(monitors) - 1  # last real monitor index

                if mss_index > max_mss_index:
                    self._logger.warning(
                        "MssBackend.capture(): monitor_index %d out of range "
                        "(max %d). Clamping to primary monitor.",
                        self._config.monitor_index, max_mss_index - 1,
                    )
                    mss_index = 1 if max_mss_index >= 1 else 0

                monitor = monitors[mss_index]

                # Apply crop if configured.
                if self._config.crop is not None:
                    c = self._config.crop
                    grab_region = {
                        "left":   monitor["left"] + c.get("x", 0),
                        "top":    monitor["top"] + c.get("y", 0),
                        "width":  c.get("w", monitor["width"]),
                        "height": c.get("h", monitor["height"]),
                    }
                else:
                    grab_region = monitor

                sct_img = sct.grab(grab_region)
                # mss returns BGRA raw bytes in sct_img.bgra; dimensions in .width/.height
                raw_bgra = bytes(sct_img.bgra)
                return raw_bgra, sct_img.width, sct_img.height

            except mss.exception.ScreenShotError as exc:
                # Check for macOS TCC permission denial in the error message.
                msg = str(exc).lower()
                if "permission" in msg or "tcc" in msg or "access denied" in msg:
                    raise PermissionDeniedError(
                        f"OS denied screen capture permission: {exc}. "
                        "On macOS: grant Screen Recording in System Privacy settings. "
                        "On Windows: check UIPI policy."
                    ) from exc
                raise ScreenCaptureError(
                    f"mss ScreenShotError during capture: {exc}"
                ) from exc
            except (PermissionDeniedError, ScreenCaptureError, BackendUnavailableError):
                raise  # re-raise typed errors as-is
            except Exception as exc:
                raise ScreenCaptureError(
                    f"Unexpected error during screen capture: {exc}"
                ) from exc

    def list_monitors(self) -> list[dict]:
        """Return the list of monitors reported by mss (v0.5.1).

        Raises:
            NotImplementedError: Forge will implement this method.

        Forge implementation notes:
            - Open a fresh mss.mss() context (do NOT reuse self._mss_instance to
              avoid interference with ongoing capture() calls).
            - Read sct.monitors and return it as a list of plain dicts.
            - mss.monitors[0]: virtual all-monitors composite bounding box.
            - mss.monitors[1+]: individual physical screens.
            - Each dict has at minimum: {"top": int, "left": int,
              "width": int, "height": int}.
            - If mss is not installed, raise BackendUnavailableError.
            - If the probe fails for any other reason, raise ScreenCaptureError.
            - This method is synchronous (mirrors capture()) — callers run it in
              a thread pool executor if they need non-blocking behaviour.

        Returns:
            List of monitor geometry dicts. Index 0 = composite virtual monitor;
            indices 1+ = individual physical monitors.

        Raises:
            BackendUnavailableError: mss is not installed.
            ScreenCaptureError: mss failed to enumerate monitors.
        """
        raise NotImplementedError(
            "Forge will implement: open fresh mss.mss() context; return sct.monitors "
            "as list[dict]; index 0 = all-monitors composite; 1+ = individual screens; "
            "raise BackendUnavailableError if mss not installed; "
            "raise ScreenCaptureError on any other failure."
        )

    def close(self) -> None:
        """Close the mss context manager if one is held open, releasing OS resources.

        Must be idempotent. Must not raise.
        """
        with self._lock:
            if self._mss_instance is not None:
                try:
                    # mss.MssBase supports __exit__ for context-manager close.
                    # We entered it manually in capture(), so we must exit manually.
                    self._mss_instance.__exit__(None, None, None)
                except Exception as exc:
                    self._logger.warning(
                        "MssBackend.close(): error closing mss instance (ignored): %s", exc
                    )
                finally:
                    self._mss_instance = None
        self._logger.debug("MssBackend closed.")


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
# Factory
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
    candidate = MssBackend(config, logger)
    if candidate.available():
        logger.info(
            "MssBackend selected for screen capture (mss + Pillow available)."
        )
        return candidate

    # mss not available or permission denied — fall back to NullBackend.
    logger.warning(
        "No screen capture backend available. "
        "Install heretic[vision] (pip install heretic[vision]) and ensure "
        "screen recording permission is granted. "
        "Sjón will remain inactive for this ceremony."
    )
    return NullBackend()
