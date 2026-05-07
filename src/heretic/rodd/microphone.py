"""
Microphone capture backends — L2 Rödd Hlust substrate.

Defines the MicrophoneCapture abstract base class and three concrete backends:

- SoundDeviceMicBackend: primary cross-platform backend using ``sounddevice``
  (optional dep — in [voice] extra). Streams 16 kHz mono int16 frames at 30 ms
  intervals, the format native to both webrtcvad and Whisper.
- NullMicBackend: silent fallback — no capture, no crash. When no backend is
  available, Hlust enters stdin fallback mode rather than halting the ceremony.

Hlust selects the backend at init time via ``MicrophoneCapture.best_available()``.

Frame contract (shared invariant with VadDetector and WhisperEngine):
    sample_rate : 16 000 Hz
    channels    : 1 (mono)
    dtype       : int16
    frame_ms    : 30 ms  =>  480 samples  =>  960 bytes per frame

This contract is locked in by the Architect; see rodd/INTERFACE.md §Hlust.
"""

from __future__ import annotations

import abc
import logging
from typing import Callable


# ---------------------------------------------------------------------------
# Frame format constants (locked by Architect — do not change without INTERFACE.md revision)
# ---------------------------------------------------------------------------

SAMPLE_RATE: int = 16_000
"""Whisper-native and webrtcvad-compatible sample rate."""

CHANNELS: int = 1
"""Mono capture — Whisper operates on mono audio."""

FRAME_MS: int = 30
"""webrtcvad supports only 10, 20, or 30 ms frames. 30 ms is chosen for balance."""

FRAME_SAMPLES: int = SAMPLE_RATE * FRAME_MS // 1000
"""Number of samples per frame: 480."""

FRAME_BYTES: int = FRAME_SAMPLES * 2
"""Bytes per frame (int16 = 2 bytes/sample): 960."""


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class MicrophoneCapture(abc.ABC):
    """Contract for all microphone capture backends.

    Implementations open a system audio input stream and push 30 ms int16 frames
    to the registered callback. All capture runs on a background thread; the
    callback is invoked from that thread — implementors must document any
    thread-safety implications.

    Lifecycle:
        mic = MicrophoneCapture.best_available(config_device, logger)
        mic.start_stream(callback)          # begins pushing frames
        ...                                 # callback receives bytes objects
        mic.stop_stream()                   # stops capture cleanly
    """

    @classmethod
    @abc.abstractmethod
    def available(cls) -> bool:
        """Return True if this backend can be instantiated on the current platform.

        Probes required dependencies without raising. A False return means the
        backend should not be selected; ``best_available()`` skips it.
        """

    @abc.abstractmethod
    def start_stream(self, callback: Callable[[bytes], None]) -> None:
        """Open the audio input stream and begin pushing 30 ms int16 frames to callback.

        Each call to callback receives exactly FRAME_BYTES (960) bytes of raw
        int16 PCM audio at SAMPLE_RATE (16 kHz), mono.

        The stream runs on a background thread. The callback is invoked from
        that thread; it must be fast (< 1 ms) to avoid frame drops.

        Args:
            callback: Callable accepting one bytes argument — one 30 ms frame.

        Raises:
            MicrophoneError: if the audio device cannot be opened.
            MicrophoneBackendUnavailableError: if the backend is not available.
        """

    @abc.abstractmethod
    def stop_stream(self) -> None:
        """Stop the capture stream cleanly.

        Blocks until the background capture thread has exited. Safe to call even
        if ``start_stream()`` was never called or already stopped.

        Never raises.
        """

    @staticmethod
    def best_available(
        device: str,
        logger: logging.Logger,
    ) -> "MicrophoneCapture":
        """Factory: return the best available MicrophoneCapture for this machine.

        Preference order:
            1. SoundDeviceMicBackend  — requires sounddevice (in [voice] extra)
            2. NullMicBackend         — always available; no capture

        Args:
            device: Device name or ``"default"`` from ``rodd.stt.device``.
            logger: Logger instance from grunnr.logger.get_logger.

        Returns:
            A MicrophoneCapture instance. Never raises — returns NullMicBackend
            if no real backend is available so the ceremony can continue text-only.
        """
        if SoundDeviceMicBackend.available():
            logger.debug("MicrophoneCapture.best_available: selecting SoundDeviceMicBackend")
            return SoundDeviceMicBackend(device=device, logger=logger)

        logger.warning(
            "MicrophoneCapture.best_available: no real mic backend available "
            "(is sounddevice installed? try: pip install heretic[voice]). "
            "Falling back to NullMicBackend — Hlust will use stdin input."
        )
        return NullMicBackend(device=device, logger=logger)


# ---------------------------------------------------------------------------
# SoundDeviceMicBackend — primary backend
# ---------------------------------------------------------------------------

class SoundDeviceMicBackend(MicrophoneCapture):
    """Primary microphone backend using the sounddevice library.

    Captures 16 kHz mono int16 audio in 30 ms frames and pushes each frame to
    the registered callback. sounddevice is an optional dep (``heretic[voice]``);
    ``available()`` returns False if the import fails so the factory degrades
    gracefully.

    Cross-platform: Windows (WASAPI/DirectSound), macOS (CoreAudio), Linux (ALSA/PulseAudio/JACK).
    """

    def __init__(self, device: str, logger: logging.Logger) -> None:
        """Initialise the backend.

        Args:
            device: OS device name or ``"default"``. Passed to sounddevice
                    at stream open time, not at construction.
            logger: Logger instance.
        """
        self._device = device
        self._log = logger
        self._stream: object | None = None  # sounddevice.RawInputStream at runtime

    @classmethod
    def available(cls) -> bool:
        """Return True if sounddevice can be imported and an input device exists."""
        raise NotImplementedError(
            "Forge will implement: probe `import sounddevice` and "
            "`sounddevice.query_devices(kind='input')` without raising. "
            "Return False on ImportError or no-device PortAudioError."
        )

    def start_stream(self, callback: Callable[[bytes], None]) -> None:
        """Open a sounddevice.RawInputStream and register the frame callback.

        Forge will implement: construct RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=FRAME_SAMPLES,
            device=self._device if self._device != 'default' else None,
            dtype='int16',
            channels=CHANNELS,
            callback=<adapter that extracts bytes and calls the user callback>,
        ), call stream.start(), store as self._stream.
        """
        raise NotImplementedError(
            "Forge will implement: open sounddevice.RawInputStream at 16 kHz mono int16, "
            "30 ms blocksize (480 samples), call start(), store stream handle."
        )

    def stop_stream(self) -> None:
        """Stop and close the sounddevice stream.

        Forge will implement: call self._stream.stop() then self._stream.close(),
        set self._stream = None, log at DEBUG. Handle None stream safely.
        """
        raise NotImplementedError(
            "Forge will implement: stop and close the sounddevice stream; "
            "set self._stream = None; never raise."
        )


# ---------------------------------------------------------------------------
# NullMicBackend — silent fallback
# ---------------------------------------------------------------------------

class NullMicBackend(MicrophoneCapture):
    """No-op microphone backend. Always available; never captures audio.

    Used when no real backend is available so Hlust can continue to exist
    without crashing. ``start_stream()`` is a no-op; ``stop_stream()`` is a no-op.
    Hlust detects the Null backend and falls back to stdin input.
    """

    def __init__(self, device: str, logger: logging.Logger) -> None:
        self._device = device
        self._log = logger

    @classmethod
    def available(cls) -> bool:
        """Always True — the null backend is always available."""
        return True

    def start_stream(self, callback: Callable[[bytes], None]) -> None:
        """No-op — NullMicBackend does not capture audio."""
        self._log.debug("NullMicBackend.start_stream: no-op (no real mic backend available)")

    def stop_stream(self) -> None:
        """No-op."""
        self._log.debug("NullMicBackend.stop_stream: no-op")
