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


# ---------------------------------------------------------------------------
# Hlust STT errors (v0.3)
# ---------------------------------------------------------------------------

class HlustError(RoddError):
    """Base class for all Hlust (STT / ear) errors.

    Raised when any component of the STT pipeline — microphone capture, VAD,
    or Whisper transcription — encounters a fault.

    Recovery: caller (CLI) falls back to stdin input with a warning log.
    The ceremony must not crash on Hlust failure.
    """


class MicrophoneError(HlustError):
    """A microphone capture operation failed.

    Raised when the mic stream cannot be opened, a device is lost mid-capture,
    or the capture backend encounters an unrecoverable error.

    Maps to VOICE_DEVICE_UNAVAILABLE (mic side) from LAYER_INTERFACES.md §L2.
    """


class MicrophoneBackendUnavailableError(MicrophoneError):
    """No microphone backend is available on this platform.

    Raised when ``MicrophoneCapture.best_available()`` cannot find a working
    backend (sounddevice absent and no platform fallback). Hlust will be in
    unavailable state; CLI falls back to stdin.

    Maps to VOICE_DEVICE_UNAVAILABLE from LAYER_INTERFACES.md §L2.
    """


class VadError(HlustError):
    """A Voice Activity Detection operation failed.

    Raised when the VAD backend receives malformed audio (wrong frame length)
    or encounters an internal classification error.
    """


class VadBackendUnavailableError(VadError):
    """No VAD backend is available on this platform.

    Raised when neither webrtcvad-wheels nor EnergyThresholdBackend (always
    available) initialises successfully. In practice this should not happen
    because EnergyThresholdBackend has no deps — but the error is defined
    for completeness and defensive coding.
    """


class WhisperError(HlustError):
    """A Whisper transcription operation failed.

    Raised when the transcription backend returns an error, the audio is
    malformed, or the backend encounters an unexpected runtime fault.
    """


class WhisperBackendUnavailableError(WhisperError):
    """No Whisper backend is available on this machine.

    Raised when neither pywhispercpp nor the whisper-cli binary is available.
    Hlust will be in unavailable state; CLI falls back to stdin.
    """


class WhisperModelLoadError(WhisperError):
    """The Whisper GGML model could not be loaded.

    Raised when the model file is missing, corrupt, has an incompatible format,
    or the system does not have enough memory to load it.

    Maps to VOICE_STT_CRASH from LAYER_INTERFACES.md §L2.

    Attributes:
        model_path: The path that was attempted (relative; never absolute).
    """

    def __init__(self, message: str, model_path: str | None = None) -> None:
        super().__init__(message)
        self.model_path = model_path


class HlustConfigError(HlustError):
    """Hlust was initialised with an invalid config or in an unusable state.

    Raised by capture_one_utterance() when:
      - Hlust is marked unavailable (Null backends for mic, VAD, or Whisper).
      - Hlust has been closed.
      - The RoddSttConfig contains logically inconsistent values that prevent
        safe operation.

    Recovery: CLI disables voice input for this ceremony and falls back to stdin.
    """
