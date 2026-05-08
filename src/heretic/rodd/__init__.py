"""
heretic.rodd — L2 Rödd, the voice layer of HERETIC.

Rödd is the body's voice faculty: the mouth (Tunga / TTS) and the ears (Hlust / STT).
v0.2 shipped Tunga; v0.3 adds Hlust — the four Hlust substrate modules are scaffolded
here and will be fully implemented by Forge in v0.3 Wave 2.

Tunga receives streaming text deltas from L1 Bifröst, segments them at sentence
boundaries, sends each segment to the ChatterBox TTS service for synthesis, and
plays the returned WAV audio through the configured output device.

Hlust captures spoken audio from the microphone, classifies frames via VAD,
and transcribes complete utterances via Whisper.cpp, yielding text that flows
to L1 Bifröst as user-role messages.

Public surface:

    Config:
        RoddConfig          — root config for the full Rödd layer
        RoddTtsConfig       — TTS (Tunga) config subtree
        RoddSttConfig       — STT (Hlust) config subtree

    Tunga orchestrator (TTS, implemented v0.2):
        Tunga               — text-stream-to-speech orchestrator

    Hlust orchestrator (STT, skeleton v0.3):
        Hlust               — speech-to-text orchestrator

    ChatterBox client (TTS):
        ChatterboxClient    — ABC for all TTS service clients
        ChatterboxHttpClient — httpx-based production client

    Playback backends (TTS):
        AudioPlayback               — ABC for all audio output backends
        SoundDeviceBackend          — primary: sounddevice library (optional dep)
        PlatformFallbackBackend     — fallback: OS-native (winsound / afplay / aplay)
        NullPlaybackBackend         — silent fallback; no crash

    Microphone backends (STT):
        MicrophoneCapture           — ABC for all mic capture backends
        SoundDeviceMicBackend       — primary: sounddevice at 16 kHz mono int16
        NullMicBackend              — silent fallback; no capture

    VAD backends (STT):
        VadDetector                 — ABC for all VAD backends
        WebRtcVadBackend            — primary: webrtcvad-wheels (BSD-3)
        EnergyThresholdBackend      — fallback: pure-Python RMS energy
        NullVadBackend              — silent fallback; never detects speech

    Whisper backends (STT):
        WhisperEngine               — ABC for all Whisper transcription backends
        PyWhisperCppBackend         — primary: pywhispercpp Python bindings (MIT)
        CliSubprocessBackend        — fallback: whisper-cli binary subprocess
        NullWhisperBackend          — silent fallback; returns empty string

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
        HlustError
        MicrophoneError
        MicrophoneBackendUnavailableError
        VadError
        VadBackendUnavailableError
        WhisperError
        WhisperBackendUnavailableError
        WhisperModelLoadError
        HlustConfigError

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
    HlustConfigError,
    HlustError,
    MicrophoneBackendUnavailableError,
    MicrophoneError,
    PlaybackBackendUnavailableError,
    PlaybackError,
    RoddError,
    TungaConfigError,
    VadBackendUnavailableError,
    VadError,
    WhisperBackendUnavailableError,
    WhisperError,
    WhisperModelLoadError,
)
from heretic.rodd.hlust import Hlust
from heretic.rodd.microphone import MicrophoneCapture, NullMicBackend, SoundDeviceMicBackend
from heretic.rodd.playback import AudioPlayback, NullPlaybackBackend, PlatformFallbackBackend, SoundDeviceBackend
from heretic.rodd.tunga import Tunga
from heretic.rodd.vad import EnergyThresholdBackend, NullVadBackend, VadDetector, WebRtcVadBackend
from heretic.rodd.whisper_engine import (
    CliSubprocessBackend,
    NullWhisperBackend,
    PyWhisperCppBackend,
    WhisperEngine,
)

__all__ = [
    # Config
    "RoddConfig",
    "RoddTtsConfig",
    "RoddSttConfig",
    # Tunga orchestrator (TTS)
    "Tunga",
    # Hlust orchestrator (STT)
    "Hlust",
    # ChatterBox client
    "ChatterboxClient",
    "ChatterboxHttpClient",
    # Playback backends (TTS)
    "AudioPlayback",
    "SoundDeviceBackend",
    "PlatformFallbackBackend",
    "NullPlaybackBackend",
    # Microphone backends (STT)
    "MicrophoneCapture",
    "SoundDeviceMicBackend",
    "NullMicBackend",
    # VAD backends (STT)
    "VadDetector",
    "WebRtcVadBackend",
    "EnergyThresholdBackend",
    "NullVadBackend",
    # Whisper backends (STT)
    "WhisperEngine",
    "PyWhisperCppBackend",
    "CliSubprocessBackend",
    "NullWhisperBackend",
    # Errors — TTS
    "RoddError",
    "ChatterboxError",
    "ChatterboxConnectionError",
    "ChatterboxAuthError",
    "ChatterboxTimeoutError",
    "ChatterboxApiError",
    "PlaybackError",
    "PlaybackBackendUnavailableError",
    "TungaConfigError",
    # Errors — STT
    "HlustError",
    "MicrophoneError",
    "MicrophoneBackendUnavailableError",
    "VadError",
    "VadBackendUnavailableError",
    "WhisperError",
    "WhisperBackendUnavailableError",
    "WhisperModelLoadError",
    "HlustConfigError",
]
