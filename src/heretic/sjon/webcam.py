"""
Webcam capture backends — L3 Sjón substrate (v0.5.2).

Defines the WebcamCaptureBackend abstract base class and two concrete
implementations:

- OpenCvBackend: primary backend using cv2.VideoCapture (opencv-python, Apache 2.0,
  cross-platform). Returns raw BGR bytes. Preferred when cv2 is importable.
- NullBackend: always-unavailable silent stub. Final fallback so the factory chain
  never returns None. Webcam paths degrade gracefully rather than crashing.

Factory:
    best_available(logger, config) selects the highest-priority available backend.

Selection order:
    1. OpenCvBackend — if cv2 is importable and VideoCapture probe succeeds.
    2. NullBackend — silent fallback; logs a warning.

Mirrors the MssBackend / NullBackend pattern in capture.py.

cv2 lifecycle notes (relevant to OpenCvBackend implementation):
    - cv2.VideoCapture(device_index) opens the capture device. This call may
      block briefly while the OS enumerates the device.
    - cap.isOpened() returns True when the device was successfully opened.
    - cap.read() returns (retval, frame) where retval is bool and frame is a
      numpy ndarray of shape (height, width, 3) in BGR channel order.
    - cap.release() closes the device and releases the OS handle. Must be called
      on close. Calling release() on an already-released cap is a safe no-op.
    - Device index 0 selects the first available camera. Higher indices select
      additional cameras. On some platforms (Linux V4L2) the index maps directly
      to /dev/video0, /dev/video1, etc.
    - On macOS (AVFoundation backend) and Windows (DirectShow/MSMF backend) the
      index is OS-enumerated and may not match physical device order.
    - Thread safety: cap.read() is NOT thread-safe; capture() uses a threading.Lock
      to serialise concurrent calls (matching MssBackend's _lock pattern).

Architectural decision: opencv-python is the [vision] optional extra, not a core dep.
``pip install heretic[vision]`` is required to activate cv2.
See pyproject.toml [vision] extra.

Ref: docs/architecture/LAYER_INTERFACES.md §L3 Sjón.
     src/heretic/sjon/capture.py (MssBackend — mirrored pattern).
     src/heretic/sjon/INTERFACE.md §Webcam capture.
"""

from __future__ import annotations

import abc
import logging
import threading
from typing import TYPE_CHECKING

from heretic.sjon.errors import (
    WebcamBackendUnavailableError,
    WebcamCaptureError,
)

if TYPE_CHECKING:
    from heretic.sjon.config_model import SjonWebcamConfig


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class WebcamCaptureBackend(abc.ABC):
    """Contract for all webcam capture backends.

    Implementations receive a SjonWebcamConfig and return raw image bytes
    (BGR channel order — the caller converts to the target format via Pillow
    or cv2.imencode before encoding to JPEG/PNG and then base64).

    Lifecycle:
        backend = WebcamCaptureBackend.best_available(logger, config)
        if not backend.available():
            # degrade gracefully — no webcam on this machine or cv2 absent
            ...
        backend.open()
        raw_bytes, width, height = backend.capture(device_index=0)
        backend.close()

    capture() is synchronous. Callers run it in a thread pool executor when
    they need non-blocking behaviour inside an async context (matching the
    MssBackend pattern in sjon.py).
    """

    @classmethod
    def best_available(
        cls,
        logger: logging.Logger,
        config: "SjonWebcamConfig",
    ) -> "WebcamCaptureBackend":
        """Return the best available webcam capture backend for the current environment.

        Selection order:
            1. OpenCvBackend — if cv2 is importable and available() returns True.
            2. NullBackend — silent fallback; logs a warning.

        No network access. No side effects beyond logging.

        Args:
            logger: Logger for backend selection diagnostics.
            config: SjonWebcamConfig driving device selection and dimensions.

        Returns:
            A WebcamCaptureBackend instance. Never None — NullBackend is the
            final fallback.
        """
        # Delegate to module-level factory (symmetry with capture.best_available).
        return best_available(logger, config)

    @abc.abstractmethod
    def available(self) -> bool:
        """Return True if this backend can successfully capture on the current machine.

        Must not raise. Must not make network calls. May probe the import system
        and the OS device list, but must be cheap to call — it is invoked during
        backend selection, not only at capture time.

        Returns:
            True if open() + capture() are expected to succeed on this machine.
            False if this backend cannot function (missing dep, no device, etc.).
        """

    @abc.abstractmethod
    def open(self) -> None:
        """Open the capture device and acquire OS resources.

        Must be called before capture(). Idempotent — a second open() on an
        already-open backend is a safe no-op.

        Raises:
            WebcamCaptureError: if the device cannot be opened (device absent,
                OS permission denied, index out of range).
            WebcamBackendUnavailableError: if cv2 is not installed.
        """

    @abc.abstractmethod
    def capture(self, device_index: int) -> tuple[bytes, int, int]:
        """Capture a single webcam frame and return raw image bytes.

        Args:
            device_index: The zero-based device index to capture from. Passed
                explicitly (rather than reading from config) so that future
                multi-camera support can call capture() on a single backend
                instance with different indices without re-opening.

        Returns:
            A tuple of (raw_bytes, width, height) where raw_bytes is raw BGR
            pixel data (3 channels, uint8), width and height are the actual
            captured frame dimensions in pixels.

        Raises:
            WebcamCaptureError: if the capture operation fails (device not open,
                read returned retval=False, frame is None or empty).
            WebcamBackendUnavailableError: if cv2 is not installed or the backend
                has not been opened.
        """

    @abc.abstractmethod
    def close(self) -> None:
        """Release the capture device and free OS resources.

        Must be idempotent. Must not raise. Called during ceremony shutdown
        (Slokna) and on graceful close of the Sjón orchestrator.

        After close(), capture() must raise WebcamCaptureError if called without
        a subsequent open().
        """


# ---------------------------------------------------------------------------
# OpenCvBackend
# ---------------------------------------------------------------------------

class OpenCvBackend(WebcamCaptureBackend):
    """Primary webcam capture backend using cv2.VideoCapture (opencv-python).

    opencv-python returns raw BGR pixel data as a numpy ndarray. This backend
    converts the ndarray to raw bytes (ndarray.tobytes()) so the rest of the
    pipeline (FrameEncoder or JPEG encode via cv2.imencode) operates on plain
    bytes — no numpy dependency in downstream modules.

    Cross-platform support (via opencv-python):
        - Windows: DirectShow (default) or MSMF backend.
        - macOS: AVFoundation backend.
        - Linux: V4L2 backend (/dev/videoN).
        - Raspberry Pi: V4L2 with camera module.

    Thread safety: capture() uses a per-instance threading.Lock to serialise
    concurrent calls. cv2.VideoCapture.read() is NOT thread-safe; the lock
    prevents data races when the Sjón orchestrator runs capture in an executor.

    Device lifecycle:
        - cv2.VideoCapture(device_index) is called lazily on first capture()
          (after open() sets the device_index), or eagerly if open() is called
          explicitly. The cap instance is reused across captures for efficiency.
        - cap.release() is called in close(), freeing the OS device handle.

    Ref: src/heretic/sjon/webcam.py module docstring for detailed cv2 lifecycle notes.
    """

    def __init__(
        self,
        config: "SjonWebcamConfig",
        logger: logging.Logger,
    ) -> None:
        """Initialise OpenCvBackend.

        Args:
            config: SjonWebcamConfig providing device_index and dimension limits.
            logger: Logger for capture diagnostics and device warnings.

        Note: Does NOT acquire any OS resource at init time. The cv2.VideoCapture
        instance is created lazily on first open() / capture() call.
        """
        self._config = config
        self._logger = logger
        # cv2.VideoCapture instance — None until open() or first capture().
        self._cap: object | None = None
        # threading.Lock serialises cv2.VideoCapture.read() calls.
        self._lock = threading.Lock()

    def available(self) -> bool:
        """Return True if cv2 is importable and a capture device is likely accessible.

        Probe order (cheap; no side effects beyond import attempt):
            1. Attempt to import cv2.
            2. If import fails -> return False (opencv-python not installed).
            3. Attempt a device probe: open VideoCapture(device_index), check
               isOpened(), release immediately. If the probe fails for any
               reason -> return False.
            4. Return True.

        Must not raise. Must not leave an open VideoCapture after return.

        Note: on some platforms (Linux V4L2) opening /dev/video0 briefly may
        cause a short delay (~100 ms). This is acceptable for the backend
        selection probe which runs once at ceremony start.
        """
        try:
            import cv2  # noqa: PLC0415 — lazy import; cv2 is optional
        except ImportError:
            self._logger.debug(
                "OpenCvBackend.available(): cv2 import failed — "
                "opencv-python not installed. Install heretic[vision]."
            )
            return False

        try:
            cap = cv2.VideoCapture(self._config.device_index)
            opened = cap.isOpened()
            cap.release()
            if not opened:
                self._logger.debug(
                    "OpenCvBackend.available(): VideoCapture(%d) did not open — "
                    "device absent or access denied.",
                    self._config.device_index,
                )
            return bool(opened)
        except Exception as exc:
            self._logger.debug(
                "OpenCvBackend.available(): device probe failed (%s) — returning False.", exc
            )
            return False

    def open(self) -> None:
        """Open cv2.VideoCapture for the configured device_index.

        cv2 lifecycle:
            cap = cv2.VideoCapture(self._config.device_index)
            if not cap.isOpened():
                raise WebcamCaptureError(...)

        The cap instance is stored in self._cap for reuse across capture() calls.
        Idempotent: if self._cap is already open (isOpened() == True), this is a no-op.

        Raises:
            WebcamCaptureError: if cv2.VideoCapture cannot open the device.
            WebcamBackendUnavailableError: if cv2 is not installed.
        """
        try:
            import cv2  # noqa: PLC0415
        except ImportError as exc:
            raise WebcamBackendUnavailableError(
                "opencv-python (cv2) is not installed. "
                "Install heretic[vision] to enable webcam capture."
            ) from exc

        with self._lock:
            # Idempotent: already open → no-op
            if self._cap is not None:
                try:
                    if self._cap.isOpened():  # type: ignore[union-attr]
                        self._logger.debug(
                            "OpenCvBackend.open(): already open — no-op."
                        )
                        return
                except Exception:
                    pass  # cap in an indeterminate state — re-open below

            cap = cv2.VideoCapture(self._config.device_index)
            if not cap.isOpened():
                cap.release()
                raise WebcamCaptureError(
                    f"OpenCvBackend.open(): cv2.VideoCapture({self._config.device_index}) "
                    f"did not open — device absent, index out of range, or OS denied access."
                )
            self._cap = cap
            self._logger.debug(
                "OpenCvBackend.open(): VideoCapture(%d) opened successfully.",
                self._config.device_index,
            )

    def capture(self, device_index: int) -> tuple[bytes, int, int]:
        """Capture one frame via cv2.VideoCapture.read().

        Reads one frame from the open VideoCapture instance.
        Returns raw RGB bytes (converted from OpenCV's native BGR).

        BGR→RGB conversion:
            OpenCV returns frames in BGR channel order. This method converts
            to RGB via cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) before returning
            raw bytes. Downstream callers (Pillow, vision API) expect RGB.

        cv2 lifecycle:
            retval, frame = self._cap.read()
            if not retval or frame is None:
                raise WebcamCaptureError(...)
            # frame shape: (height, width, 3) in BGR channel order
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width = rgb_frame.shape[:2]
            return rgb_frame.tobytes(), width, height

        Args:
            device_index: Zero-based device index. If it differs from the index
                used to open self._cap, a warning is logged and the existing cap
                is used (re-open on index change is a v0.5.x concern).

        Returns:
            (raw_rgb_bytes, width, height) — RGB channel order, 3 bytes/pixel.

        Raises:
            WebcamCaptureError: cap.read() returned retval=False or frame is None.
            WebcamBackendUnavailableError: cv2 not installed; or open() not called.
        """
        try:
            import cv2  # noqa: PLC0415
        except ImportError as exc:
            raise WebcamBackendUnavailableError(
                "opencv-python (cv2) is not installed. "
                "Install heretic[vision] to enable webcam capture."
            ) from exc

        with self._lock:
            if self._cap is None:
                raise WebcamBackendUnavailableError(
                    "OpenCvBackend.capture() called before open(). "
                    "Call open() first to acquire the device handle."
                )

            if device_index != self._config.device_index:
                self._logger.warning(
                    "OpenCvBackend.capture(): device_index=%d differs from configured %d. "
                    "Using existing cap (re-open on index change is v0.5.x). "
                    "Multi-camera is deferred.",
                    device_index, self._config.device_index,
                )

            ret, frame = self._cap.read()  # type: ignore[union-attr]
            if not ret or frame is None:
                raise WebcamCaptureError(
                    f"OpenCvBackend.capture(): cv2.VideoCapture.read() returned "
                    f"retval={ret!r} — device disconnected, permission revoked, or stream ended."
                )

            # Convert BGR→RGB (Cartographer invariant — cv2 returns BGR; Pillow + vision APIs expect RGB)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width = rgb_frame.shape[:2]
            return rgb_frame.tobytes(), width, height

    def close(self) -> None:
        """Release cv2.VideoCapture and free the OS device handle.

        cv2 lifecycle:
            if self._cap is not None:
                self._cap.release()
                self._cap = None

        Must be idempotent. Must not raise. Calling close() when already closed
        (self._cap is None) is a safe no-op.
        """
        with self._lock:
            if self._cap is not None:
                try:
                    self._cap.release()  # type: ignore[union-attr]
                except Exception as exc:
                    # Never raise from close() — log and swallow.
                    self._logger.debug(
                        "OpenCvBackend.close(): cap.release() raised (ignored): %s", exc
                    )
                finally:
                    self._cap = None
                self._logger.debug(
                    "OpenCvBackend.close(): VideoCapture released."
                )


# ---------------------------------------------------------------------------
# NullBackend
# ---------------------------------------------------------------------------

class WebcamNullBackend(WebcamCaptureBackend):
    """Always-unavailable silent stub backend for webcam capture.

    WebcamNullBackend exists so the factory chain always returns a backend
    instance rather than None. Code that calls best_available() and then checks
    available() will receive False and can degrade gracefully without handling None.

    capture() raises WebcamBackendUnavailableError to make misconfiguration visible —
    if code calls capture() without first checking available(), the error is explicit.

    Mirrors the NullBackend pattern in capture.py exactly.
    """

    def available(self) -> bool:
        """Always returns False — this backend cannot capture anything."""
        return False

    def open(self) -> None:
        """No-op — NullBackend holds no OS resources and cannot open a device."""

    def capture(self, device_index: int) -> tuple[bytes, int, int]:
        """Always raises WebcamBackendUnavailableError.

        This method should never be called in normal operation because code is
        expected to check available() before calling capture(). The error makes
        any incorrect usage immediately visible.

        Raises:
            WebcamBackendUnavailableError: always.
        """
        raise WebcamBackendUnavailableError(
            "WebcamNullBackend.capture() called — no webcam capture backend is available "
            "on this machine. Install heretic[vision] (opencv-python>=4.8) and ensure "
            "a capture device is present. Ref: src/heretic/sjon/INTERFACE.md §Webcam capture."
        )

    def close(self) -> None:
        """No-op — WebcamNullBackend holds no OS resources."""


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def best_available(
    logger: logging.Logger,
    config: "SjonWebcamConfig",
) -> WebcamCaptureBackend:
    """Select and return the best available webcam capture backend.

    Module-level factory function. Mirrors the capture.best_available() pattern.

    Selection order:
        1. OpenCvBackend — if cv2 is importable and OpenCvBackend.available() is True.
        2. WebcamNullBackend — always-unavailable fallback with warning.

    Note: OpenCvBackend.available() probes cv2 import and VideoCapture device open.
    If cv2 is absent or the device is unreachable the factory falls through to
    WebcamNullBackend, ensuring the chain never returns None.

    Args:
        logger: Logger for backend selection diagnostics.
        config: SjonWebcamConfig driving the backend probe and configuration.

    Returns:
        A WebcamCaptureBackend instance. Never None.
    """
    candidate = OpenCvBackend(config, logger)
    try:
        if candidate.available():
            logger.info(
                "OpenCvBackend selected for webcam capture (cv2 available, device %d accessible).",
                config.device_index,
            )
            return candidate
    except Exception as exc:
        logger.debug(
            "OpenCvBackend availability probe failed (%s) — falling back to WebcamNullBackend.",
            exc,
        )

    logger.warning(
        "No webcam capture backend available. "
        "Install heretic[vision] (pip install heretic[vision]) and ensure "
        "a webcam is connected. Sjón webcam capture will remain inactive."
    )
    return WebcamNullBackend()
