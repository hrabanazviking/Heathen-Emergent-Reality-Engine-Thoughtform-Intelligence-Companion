"""
Audio playback backends — L2 Rödd Tunga substrate.

Defines the AudioPlayback abstract base class and two concrete backend skeletons:

- SoundDeviceBackend: primary cross-platform backend using the ``sounddevice``
  library (optional dependency — in [voice] extra). Preferred when available.
- PlatformFallbackBackend: secondary backend using OS-native commands when
  sounddevice is not installed (aplay on Linux, afplay on macOS, winsound on Windows).

Tunga selects the backend at init time via the static factory AudioPlayback.best_available().
Forge (Eldra Járnsdóttir) will implement all method bodies.

Architectural decision: sounddevice is the [voice] optional extra, not a core dep.
This means ``pip install heretic`` works on machines without speakers; only
``pip install heretic[voice]`` pulls in sounddevice. See pyproject.toml.
"""

from __future__ import annotations

import abc
import io
import logging
import platform
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from heretic.rodd.config_model import RoddTtsConfig


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class AudioPlayback(abc.ABC):
    """Contract for all audio playback backends.

    Implementations receive raw WAV bytes and play them to the configured
    output device. All methods are synchronous; callers run them in a thread
    pool executor if they need non-blocking behaviour.

    Lifecycle:
        playback = AudioPlayback.best_available(config, logger)
        if not playback.available():
            # degrade gracefully — no audio on this machine
            ...
        playback.play(wav_bytes)
        playback.close()
    """

    @classmethod
    def best_available(
        cls,
        config: "RoddTtsConfig",
        logger: logging.Logger,
    ) -> "AudioPlayback":
        """Return the best available playback backend for the current environment.

        Selection order:
            1. SoundDeviceBackend — if sounddevice is importable.
            2. PlatformFallbackBackend — otherwise.

        Forge will implement:
        - Try ``import sounddevice`` inside a try/except ImportError.
        - Return SoundDeviceBackend(config, logger) on success.
        - Return PlatformFallbackBackend(config, logger) on ImportError.
        - Log which backend was selected at INFO level.
        """
        raise NotImplementedError(
            "Forge will implement: try importing sounddevice, return SoundDeviceBackend "
            "if available, else return PlatformFallbackBackend. Log the selection."
        )

    @abc.abstractmethod
    def play(self, wav_bytes: bytes) -> None:
        """Play WAV audio to the configured output device.

        This method is synchronous and blocks until playback is complete.
        Callers that need non-blocking behaviour must run this in a thread pool.

        Args:
            wav_bytes: Raw WAV audio data as returned by ChatterboxHttpClient.synthesize().

        Raises:
            PlaybackError: if playback fails for any reason.
            PlaybackBackendUnavailableError: if the backend is not available
                on this platform (available() returns False).
        """

    @abc.abstractmethod
    def available(self) -> bool:
        """Return True if this backend can produce audio on the current machine.

        Must not raise — returns False on any error determining availability.
        Used by Tunga to decide whether to activate voice-out or degrade to text-only.
        """

    @abc.abstractmethod
    def close(self) -> None:
        """Release any resources held by the backend.

        Safe to call even if the backend was never used or is not available.
        After close(), this instance must not be used for playback.
        """


# ---------------------------------------------------------------------------
# sounddevice backend skeleton
# ---------------------------------------------------------------------------

class SoundDeviceBackend(AudioPlayback):
    """Primary audio playback backend using the ``sounddevice`` library.

    sounddevice is an optional dependency (``pip install heretic[voice]``).
    This backend is chosen automatically by AudioPlayback.best_available()
    when sounddevice is importable.

    Reads WAV headers to extract samplerate and channel count, then feeds
    the audio data to sounddevice.play(). Uses the device specified in
    ``config.device`` (or the OS default when ``config.device == 'default'``).
    """

    def __init__(self, config: "RoddTtsConfig", logger: logging.Logger) -> None:
        """Initialise from config.

        Args:
            config: RoddTtsConfig. Only device and speed fields are used.
            logger: Logger for diagnostics.
        """
        self._config = config
        self._log = logger
        self._closed: bool = False

    def available(self) -> bool:
        """Return True if sounddevice is importable and a usable output device exists.

        Forge will implement:
        - Try ``import sounddevice as sd``.
        - Try ``sd.query_devices(device=..., kind='output')`` for the configured device.
        - Return True if both succeed, False otherwise.
        - Never raise — catch all exceptions and return False.
        """
        raise NotImplementedError(
            "Forge will implement: import sounddevice, query_devices for the configured "
            "output device, return True/False without raising."
        )

    def play(self, wav_bytes: bytes) -> None:
        """Play WAV bytes via sounddevice.

        Forge will implement:
        - Parse WAV headers using wave.open(io.BytesIO(wav_bytes)) to extract
          samplerate, sampwidth (bit depth), and nchannels.
        - Convert raw PCM data to a numpy array with dtype matching sampwidth:
            sampwidth 2 → np.int16; sampwidth 4 → np.int32.
        - Call sounddevice.play(data, samplerate=..., device=..., blocking=True).
        - Apply self._config.speed if != 1.0 via librosa.resample or a simple
          sample-rate trick (divide samplerate by speed).
        - Raise PlaybackError on sounddevice.PortAudioError.
        - Raise PlaybackBackendUnavailableError if sounddevice is not importable
          at call time (defensive — should not happen if available() was checked).
        - Log play start and duration at DEBUG level.
        """
        raise NotImplementedError(
            "Forge will implement: parse WAV with wave.open, extract PCM as numpy array, "
            "call sounddevice.play(data, samplerate, device, blocking=True), "
            "apply speed factor, raise PlaybackError on PortAudioError."
        )

    def close(self) -> None:
        """Release sounddevice resources.

        Forge will implement:
        - Call sounddevice.stop() if any playback is in progress.
        - Set self._closed = True.
        - Log at DEBUG.
        """
        raise NotImplementedError(
            "Forge will implement: call sounddevice.stop() if playing, set self._closed = True."
        )


# ---------------------------------------------------------------------------
# Platform fallback backend skeleton
# ---------------------------------------------------------------------------

class PlatformFallbackBackend(AudioPlayback):
    """Fallback audio playback backend using OS-native commands.

    Used when sounddevice is not installed. Selects the appropriate
    native audio command for the current OS:
        - Windows: winsound.PlaySound (stdlib)
        - macOS:   afplay subprocess
        - Linux:   aplay subprocess

    WAV bytes are written to a temporary file, played via the native command,
    then the temp file is removed. This approach ensures cross-platform
    compatibility without requiring any optional dependencies.

    Note: playback quality and latency are lower than SoundDeviceBackend.
    Users who need reliable voice output should install heretic[voice].
    """

    _PLATFORM: str = platform.system()
    """Cached OS identifier: 'Windows', 'Darwin', 'Linux'. Set at class definition time."""

    def __init__(self, config: "RoddTtsConfig", logger: logging.Logger) -> None:
        """Initialise from config.

        Args:
            config: RoddTtsConfig. Only device is used (where the OS supports it).
            logger: Logger for diagnostics.
        """
        self._config = config
        self._log = logger
        self._closed: bool = False

    def available(self) -> bool:
        """Return True if the OS-native playback method is available.

        Forge will implement:
        - Windows: try ``import winsound``; return True if succeeds.
        - macOS: check ``shutil.which('afplay') is not None``.
        - Linux: check ``shutil.which('aplay') is not None``.
        - Other OS: return False.
        - Never raise.
        """
        raise NotImplementedError(
            "Forge will implement: platform-specific availability check — "
            "Windows: import winsound; macOS: which(afplay); Linux: which(aplay). "
            "Return True/False without raising."
        )

    def play(self, wav_bytes: bytes) -> None:
        """Play WAV bytes using the OS-native audio command.

        Forge will implement:
        - Write wav_bytes to a named temporary file (suffix='.wav') using
          tempfile.NamedTemporaryFile(delete=False, suffix='.wav').
        - Platform dispatch:
            Windows: winsound.PlaySound(tmp_path, winsound.SND_FILENAME)
            macOS:   subprocess.run(['afplay', tmp_path], check=True)
            Linux:   subprocess.run(['aplay', tmp_path], check=True)
        - Remove the temp file in a finally block (cleanup always runs).
        - Raise PlaybackError on subprocess.CalledProcessError or OSError.
        - Raise PlaybackBackendUnavailableError if no native method is present.
        - Log at DEBUG (platform, file size, duration_ms).
        """
        raise NotImplementedError(
            "Forge will implement: write WAV to temp file, dispatch to OS-native player "
            "(winsound/afplay/aplay), remove temp file in finally, raise PlaybackError on failure."
        )

    def close(self) -> None:
        """No persistent resources to release for this backend.

        Forge will implement:
        - Set self._closed = True.
        - Log at DEBUG.
        """
        raise NotImplementedError(
            "Forge will implement: set self._closed = True, log at DEBUG. "
            "No persistent resources to release for this backend."
        )
