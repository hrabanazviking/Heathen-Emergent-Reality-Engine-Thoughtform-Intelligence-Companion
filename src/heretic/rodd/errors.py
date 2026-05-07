"""
Rodd error hierarchy — L2 Rödd voice layer exceptions.

All Rodd errors derive from RoddError. Callers should catch the base class for
broad fault tolerance, or catch specific subclasses for targeted recovery.

Error taxonomy mirrors the VOICE_* codes defined in LAYER_INTERFACES.md §L2 Rödd
and the error model described in rodd/INTERFACE.md.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

class RoddError(Exception):
    """Base class for all L2 Rödd voice layer errors.

    Catch this to handle any Rodd fault without distinguishing origin.
    All subclasses carry a human-readable message describing the fault condition.
    """


# ---------------------------------------------------------------------------
# ChatterBox TTS client errors
# ---------------------------------------------------------------------------

class ChatterboxError(RoddError):
    """Base class for all ChatterBox TTS service errors.

    Raised when communication with the ChatterBox HTTP service fails
    or returns an unexpected response.
    """


class ChatterboxConnectionError(ChatterboxError):
    """ChatterBox endpoint is unreachable.

    Maps to VOICE_TTS_UNREACHABLE from LAYER_INTERFACES.md §L2.
    Raised when the HTTP transport cannot establish a connection — e.g.
    the Pi is offline, network is down, or the service is not running.

    Recovery: emit voice::error, fall back to text-only output.
    """


class ChatterboxAuthError(ChatterboxError):
    """ChatterBox returned HTTP 401 or 403.

    Raised when the service rejects the request due to authentication.
    In v0.2 ChatterBox has no auth, so this guards against future credential
    additions without code changes.

    Recovery: surface in log; do not retry automatically.
    """


class ChatterboxTimeoutError(ChatterboxError):
    """ChatterBox did not respond within the configured timeout.

    Raised when the HTTP request to /v1/audio/speech exceeds
    ``rodd.tts.request_timeout_seconds``.

    Recovery: log warning; discard or queue the pending speech chunk per config.
    """


class ChatterboxApiError(ChatterboxError):
    """ChatterBox returned an unexpected HTTP status or malformed response body.

    Raised when the service is reachable but responds with a non-200 status
    not covered by ChatterboxAuthError, or when the response body cannot be
    interpreted as valid WAV audio.

    Attributes:
        status_code: HTTP status code received (or None if not applicable).
        detail: Raw detail from the response body when available.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        detail: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


# ---------------------------------------------------------------------------
# Playback errors
# ---------------------------------------------------------------------------

class PlaybackError(RoddError):
    """Base class for all audio playback errors.

    Raised when the selected audio backend cannot play WAV audio to the
    configured output device.
    """


class PlaybackBackendUnavailableError(PlaybackError):
    """No suitable audio playback backend is available on this platform.

    Raised when ``SoundDeviceBackend.available()`` returns False AND the
    ``PlatformFallbackBackend`` also reports itself unavailable — meaning
    HERETIC has no path to produce audio on the current machine.

    Maps to VOICE_DEVICE_UNAVAILABLE from LAYER_INTERFACES.md §L2.

    Recovery: disable TTS output for this ceremony; log clear warning so
    the operator knows to install sounddevice or check device availability.
    """


# ---------------------------------------------------------------------------
# Configuration errors
# ---------------------------------------------------------------------------

class TungaConfigError(RoddError):
    """Tunga was initialised with an invalid or incomplete RoddConfig.

    Raised by Tunga.__init__() during __post_init__ validation when required
    fields are missing, out-of-range, or logically inconsistent (e.g.
    ``rodd.tts.enabled: true`` but no endpoint configured).

    Recovery: abort Tunga initialisation; lifecycle must catch this and
    disable the voice-out capability flag without crashing the ceremony.
    """
