"""
Sjón error hierarchy — L3 Sjón (Vision).

All Sjón-related failures are subclasses of SjonError. Callers who need to
catch any Sjón failure can catch SjonError; callers who need finer granularity
can catch the specific subclass.

Error taxonomy (mirrors the thiserror-style hierarchy used in rodd.errors):

    SjonError                          # root — catch-all for any Sjón failure
        ScreenCaptureError             # failure during screen capture operation
            PermissionDeniedError      # OS denied screen capture permission
        BackendUnavailableError        # no screen capture backend available on this machine
        FrameEncodingError             # failure during frame encoding (resize/PNG/base64)
        ThrottleRejectedError          # snapshot rejected — within min_interval_ms window
        WebcamCaptureError             # failure during webcam capture operation (v0.5.2)
            WebcamBackendUnavailableError  # no webcam backend available / cv2 absent

Ref: docs/architecture/LAYER_INTERFACES.md §L3 Sjón Error model.
     src/heretic/sjon/INTERFACE.md §Webcam capture (v0.5.2).
"""

from __future__ import annotations


class SjonError(Exception):
    """Root error for all L3 Sjón (Vision) failures.

    Raised when something in the Sjón layer fails in a way that cannot be
    handled internally. Callers (the ceremony turn loop, the CLI) must catch
    this and degrade gracefully — the ceremony must continue without vision
    rather than crashing.

    Ref: LAYER_INTERFACES.md §L3 Error model: if Sjón fails, continue
    the ceremony without a frame; log a warning; do not abort.
    """


class ScreenCaptureError(SjonError):
    """Raised when the screen capture operation itself fails.

    This covers failures after a working backend has been selected — i.e., the
    backend is available but the capture call returned an error. Includes OS
    errors that occur mid-capture.

    Distinct from BackendUnavailableError (no backend present at all) and
    PermissionDeniedError (OS permission check failed).
    """


class PermissionDeniedError(ScreenCaptureError):
    """Raised when the OS denies screen capture permission.

    Maps to VISION_PERMISSION_DENIED in LAYER_INTERFACES.md §L3 Error model.

    Recovery: capability flag ?vision_screen (internal-bus) becomes False.
    Sjón disables itself for the ceremony; the turn loop continues without frames.
    The user must grant screen recording permission (macOS Privacy, Wayland portal,
    Windows UIPI policy) and restart the ceremony.
    """


class BackendUnavailableError(SjonError):
    """Raised when no capture backend is available on this machine.

    Occurs when all backends in the selection chain (MssBackend, NullBackend)
    cannot provide a functional capture surface. The NullBackend always reports
    itself as unavailable — this error surfaces when even the factory chain
    exhausts without finding a working backend.

    Maps to the condition where ?vision_screen (internal-bus) is False because
    no backend can satisfy a capture request.
    """


class FrameEncodingError(SjonError):
    """Raised when frame encoding fails after successful capture.

    Covers failures in the FrameEncoder: resize errors, Pillow import failures,
    PNG encoding errors, and base64 encoding errors.

    When this error occurs the raw captured bytes are discarded and the turn
    continues without a frame. The error is logged as a warning, not a crash.
    """


class ThrottleRejectedError(SjonError):
    """Raised when a snapshot() call is rejected by the throttle guard.

    The Sjón orchestrator enforces a minimum interval (min_interval_ms) between
    captures to prevent rapid-fire screen capture spam. When a snapshot() is
    requested within the throttle window, ThrottleRejectedError is raised.

    Callers should treat this as a soft rejection — continue without a frame
    for this turn. The error does NOT indicate a backend failure.
    """


# ---------------------------------------------------------------------------
# Webcam errors (v0.5.2)
# ---------------------------------------------------------------------------

class WebcamCaptureError(SjonError):
    """Raised when a webcam capture operation fails (v0.5.2).

    This covers failures after a working backend has been selected — i.e., the
    backend is available and open() succeeded, but the capture call (cv2.VideoCapture
    .read()) returned retval=False or a None/empty frame.

    Distinct from WebcamBackendUnavailableError (no backend/cv2 present at all).

    Recovery: log warning; skip webcam frame for this turn; retry on next
    snapshot_webcam() call. The ceremony continues without a webcam frame.
    """


class WebcamBackendUnavailableError(WebcamCaptureError):
    """Raised when no webcam capture backend is available on this machine (v0.5.2).

    Occurs when:
        - opencv-python (cv2) is not installed (heretic[vision] not installed).
        - The WebcamNullBackend.capture() is called directly (misconfiguration guard).
        - OpenCvBackend.capture() is called before open() is called.
        - The device at device_index is absent or inaccessible.

    Recovery: capability flag ?vision_webcam (internal-bus) becomes False.
    Sjón webcam capture disables itself for the ceremony; the turn loop continues
    with screen-only frames (or no frames if screen is also unavailable).
    The user must install cv2 and/or connect a webcam and restart the ceremony.
    """
