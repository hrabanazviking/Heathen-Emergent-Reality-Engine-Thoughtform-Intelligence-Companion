"""
heretic.rodd — L2 Rödd, the voice layer of HERETIC.

Rödd is the body's voice faculty: the mouth (Tunga / TTS) and the ears (Hlust / STT).
In v0.2 only Tunga is implemented; Hlust follows in v0.3.

Tunga receives streaming text deltas from L1 Bifröst, segments them at sentence
boundaries, sends each segment to the ChatterBox TTS service for synthesis, and
plays the returned WAV audio through the configured output device.

Public surface:

    Config:
        RoddConfig          — root config for the full Rödd layer
        RoddTtsConfig       — TTS (Tunga) config subtree
        RoddSttConfig       — STT (Hlust) config subtree (fields ready; impl in v0.3)

    Orchestrator:
        Tunga               — text-stream-to-speech orchestrator

    ChatterBox client:
        ChatterboxClient    — ABC for all TTS service clients
        ChatterboxHttpClient — httpx-based production client

    Playback backends:
        AudioPlayback               — ABC for all audio output backends
        SoundDeviceBackend          — primary: sounddevice library (optional dep)
        PlatformFallbackBackend     — fallback: OS-native (winsound / afplay / aplay)

    Errors:
        RoddError
        ChatterboxError
        ChatterboxConnectionError
        ChatterboxAuthError
        ChatterboxTimeoutError
        ChatterboxApiError
        PlaybackError
        PlaybackBackendUnavailableError
        TungaConfigError

Authority: LAYER_INTERFACES.md §L2 Rödd, SENSE_CONTRACTS.md, rodd/INTERFACE.md
"""

from __future__ import annotations

from heretic.rodd.chatterbox import ChatterboxClient, ChatterboxHttpClient
from heretic.rodd.config_model import RoddConfig, RoddSttConfig, RoddTtsConfig
from heretic.rodd.errors import (
    ChatterboxApiError,
    ChatterboxAuthError,
    ChatterboxConnectionError,
    ChatterboxError,
    ChatterboxTimeoutError,
    PlaybackBackendUnavailableError,
    PlaybackError,
    RoddError,
    TungaConfigError,
)
from heretic.rodd.playback import AudioPlayback, PlatformFallbackBackend, SoundDeviceBackend
from heretic.rodd.tunga import Tunga

__all__ = [
    # Config
    "RoddConfig",
    "RoddTtsConfig",
    "RoddSttConfig",
    # Orchestrator
    "Tunga",
    # ChatterBox client
    "ChatterboxClient",
    "ChatterboxHttpClient",
    # Playback backends
    "AudioPlayback",
    "SoundDeviceBackend",
    "PlatformFallbackBackend",
    # Errors
    "RoddError",
    "ChatterboxError",
    "ChatterboxConnectionError",
    "ChatterboxAuthError",
    "ChatterboxTimeoutError",
    "ChatterboxApiError",
    "PlaybackError",
    "PlaybackBackendUnavailableError",
    "TungaConfigError",
]
