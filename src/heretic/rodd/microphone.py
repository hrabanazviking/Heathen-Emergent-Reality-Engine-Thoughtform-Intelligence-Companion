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

Threading note: The sounddevice callback fires on a C background thread managed
by PortAudio, NOT on the asyncio event loop thread.  Hlust bridges frames back to
asyncio via ``loop.call_soon_threadsafe``.  The callback registered with
start_stream() will be called from that C thread; it MUST be fast and MUST NOT
touch asyncio primitives directly.
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
        mic = MicrophoneCapture.best_available(device, logger)
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

    Threading: sounddevice's RawInputStream invokes the PortAudio callback from a
    C background thread.  The user callback registered with start_stream() is wrapped
    in a lightweight adapter that converts the numpy buffer to plain bytes before
    forwarding — this keeps the user callback free of numpy dependencies and ensures
    the bytes copy happens before any asyncio handoff.
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
        """Return True if sounddevice can be imported and an input device exists.

        Two conditions must both hold:
        1. ``import sounddevice`` succeeds (library installed).
        2. At least one input device is present per sounddevice.query_devices().
           Returns False if PortAudio reports no input devices.
        Never raises — all exceptions are swallowed and return False.
        """
        try:
            import sounddevice as sd  # noqa: F401

            # Check that at least one input device is available.
            # query_devices() returns a DeviceList; each entry has 'max_input_channels'.
            devices = sd.query_devices()
            if not hasattr(devices, "__iter__"):
                # Single device returned as a dict-like object
                devices = [devices]
            for dev in devices:
                try:
                    if dev.get("max_input_channels", 0) > 0:
                        return True
                except (AttributeError, TypeError):
                    # Some entries may not support .get(); skip gracefully
                    continue
            return False
        except Exception:
            # ImportError, PortAudioError, or anything else — backend unavailable
            return False

    def start_stream(self, callback: Callable[[bytes], None]) -> None:
        """Open a sounddevice.RawInputStream and register the frame callback.

        Opens the stream with:
            samplerate  = SAMPLE_RATE (16 000 Hz)
            blocksize   = FRAME_SAMPLES (480 samples = 30 ms)
            channels    = CHANNELS (1 — mono)
            dtype       = 'int16'
            device      = self._device unless 'default' (then use PortAudio default)

        The internal PortAudio callback converts the incoming numpy buffer to a
        plain bytes copy (to avoid retaining a reference to the PortAudio-owned
        buffer) and forwards it to the user callback.

        Args:
            callback: Receives exactly FRAME_BYTES (960) bytes per call.

        Raises:
            MicrophoneError: on PortAudio failure or device open error.
        """
        from heretic.rodd.errors import MicrophoneError

        try:
            import sounddevice as sd

            # Resolve 'default' to None so sounddevice uses the OS default input.
            device_arg = None if self._device == "default" else self._device

            def _sd_callback(indata: object, frames: int, time_info: object, status: object) -> None:
                # indata is a numpy array (FRAME_SAMPLES, CHANNELS) of int16.
                # We copy to bytes immediately — do NOT retain indata reference
                # beyond this callback frame because PortAudio recycles its buffer.
                if status:
                    self._log.debug("SoundDeviceMicBackend: status=%s", status)
                try:
                    # Convert numpy array to raw bytes (int16 little-endian)
                    pcm_bytes = bytes(indata)
                    callback(pcm_bytes)
                except Exception as exc:
                    # Never raise from the PortAudio C callback thread — just log.
                    self._log.debug("SoundDeviceMicBackend: callback error: %s", exc)

            stream = sd.RawInputStream(
                samplerate=SAMPLE_RATE,
                blocksize=FRAME_SAMPLES,
                device=device_arg,
                dtype="int16",
                channels=CHANNELS,
                callback=_sd_callback,
            )
            stream.start()
            self._stream = stream
            self._log.debug(
                "SoundDeviceMicBackend: stream started (device=%r, rate=%d, blocksize=%d)",
                self._device,
                SAMPLE_RATE,
                FRAME_SAMPLES,
            )
        except Exception as exc:
            raise MicrophoneError(
                f"SoundDeviceMicBackend.start_stream failed: {exc}"
            ) from exc

    def stop_stream(self) -> None:
        """Stop and close the sounddevice stream cleanly.

        Calls stream.stop() then stream.close(). Idempotent — safe to call
        when the stream was never started or already closed. Never raises.
        """
        if self._stream is None:
            return
        try:
            self._stream.stop()
            self._stream.close()
            self._log.debug("SoundDeviceMicBackend: stream stopped and closed")
        except Exception as exc:
            # Log but swallow — stop_stream() must never raise (RULES.AI fault tolerance)
            self._log.debug("SoundDeviceMicBackend.stop_stream: error during close: %s", exc)
        finally:
            self._stream = None


# ---------------------------------------------------------------------------
# NullMicBackend — silent fallback
# ---------------------------------------------------------------------------

class NullMicBackend(MicrophoneCapture):
    """No-op microphone backend. Always available; never captures audio.

    Used when no real backend is available so Hlust can continue to exist
    without crashing. ``start_stream()`` is a no-op; ``stop_stream()`` is a no-op.
    Hlust detects the Null backend via isinstance() and falls back to stdin input.
    """

    def __init__(self, device: str, logger: logging.Logger) -> None:
        self._device = device
        self._log = logger

    @classmethod
    def available(cls) -> bool:
        """NullMicBackend reports itself unavailable to prevent factory selection.

        The factory will only pick NullMicBackend as a last resort because it
        explicitly returns False — best_available() falls through to it only
        when no real backend returns True.

        Note: this is intentionally False (not True) so the factory can use the
        conventional "try each in order, pick first True" pattern.  NullMicBackend
        is appended directly to the fallback chain in best_available(), not selected
        via available().
        """
        return False

    def start_stream(self, callback: Callable[[bytes], None]) -> None:
        """No-op — NullMicBackend does not capture audio."""
        self._log.debug("NullMicBackend.start_stream: no-op (no real mic backend available)")

    def stop_stream(self) -> None:
        """No-op."""
        self._log.debug("NullMicBackend.stop_stream: no-op")
