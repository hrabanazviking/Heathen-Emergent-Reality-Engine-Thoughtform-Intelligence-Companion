"""
Audio playback backends — L2 Rödd Tunga substrate.

Defines the AudioPlayback abstract base class and three concrete backends:

- SoundDeviceBackend: primary cross-platform backend using the ``sounddevice``
  library (optional dependency — in [voice] extra). Preferred when available.
- PlatformFallbackBackend: secondary backend using OS-native commands when
  sounddevice is not installed (aplay/paplay/play on Linux, afplay on macOS,
  winsound on Windows).
- NullPlaybackBackend: silent fallback — no audio, no crash. Used when no
  backend is available so the ceremony can continue text-only without a hard
  dependency on working speakers.

Tunga selects the backend at init time via the static factory
AudioPlayback.best_available().

Architectural decision: sounddevice is the [voice] optional extra, not a core dep.
This means ``pip install heretic`` works on machines without speakers; only
``pip install heretic[voice]`` pulls in sounddevice. See pyproject.toml.
"""

from __future__ import annotations

import abc
import io
import logging
import os
import platform
import shutil
import subprocess
import tempfile
import wave
from typing import TYPE_CHECKING

from heretic.rodd.errors import PlaybackBackendUnavailableError, PlaybackError

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
            1. SoundDeviceBackend — if sounddevice is importable and device available.
            2. PlatformFallbackBackend — if a native OS player exists.
            3. NullPlaybackBackend — silent fallback; logs a warning.

        No network access. No side effects beyond logging.
        """
        sd_backend = SoundDeviceBackend(config, logger)
        if sd_backend.available():
            logger.info("AudioPlayback: selected SoundDeviceBackend (sounddevice library)")
            return sd_backend

        fallback_backend = PlatformFallbackBackend(config, logger)
        if fallback_backend.available():
            logger.info(
                "AudioPlayback: sounddevice not available — selected PlatformFallbackBackend "
                "(OS-native player: %s)",
                platform.system(),
            )
            return fallback_backend

        logger.warning(
            "AudioPlayback: no audio backend available on this machine. "
            "Tunga will run in text-only mode. "
            "Install heretic[voice] to enable sounddevice-based playback."
        )
        return NullPlaybackBackend(config, logger)

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
# sounddevice backend
# ---------------------------------------------------------------------------

class SoundDeviceBackend(AudioPlayback):
    """Primary audio playback backend using the ``sounddevice`` library.

    sounddevice is an optional dependency (``pip install heretic[voice]``).
    This backend is chosen automatically by AudioPlayback.best_available()
    when sounddevice is importable and a usable device is present.

    Reads WAV headers to extract samplerate and channel count, then feeds
    the audio data to sounddevice.play(). Uses the device specified in
    ``config.device`` (or the OS default when ``config.device == 'default'``).
    """

    def __init__(self, config: "RoddTtsConfig", logger: logging.Logger) -> None:
        self._config = config
        self._log = logger
        self._closed: bool = False

    def available(self) -> bool:
        """Return True if sounddevice AND numpy are importable and a usable output device exists.

        Both sounddevice and numpy are probed here because play() imports numpy at
        call time.  If numpy is absent, available() must return False so that
        degradation is detected at Kynding (construction) rather than mid-ceremony
        on the first audio chunk.

        Never raises — any exception causes a False return so the fallback chain
        proceeds without crashing the ceremony.

        Ref: docs/audit/AUDIT_v0.2_FIRST_VOICE.md S-2.
        """
        try:
            import numpy  # noqa: F401 — probe: play() needs this at call time
            import sounddevice as sd  # noqa: F401 — testing importability
            # Probe the configured output device to verify it exists
            device_arg = None if self._config.device == "default" else self._config.device
            sd.query_devices(device=device_arg, kind="output")
            return True
        except Exception:
            return False

    def play(self, wav_bytes: bytes) -> None:
        """Play WAV bytes via sounddevice — blocks until playback completes.

        Parses the WAV header to extract sample rate, channel count, and bit depth,
        converts the PCM data to a numpy array, and calls sounddevice.play() with
        blocking=True so this method returns only when audio finishes.

        Raises:
            PlaybackBackendUnavailableError: if sounddevice cannot be imported at call time.
            PlaybackError: on any sounddevice.PortAudioError or other playback failure.
        """
        try:
            import numpy as np
            import sounddevice as sd
        except ImportError as exc:
            raise PlaybackBackendUnavailableError(
                "sounddevice (or numpy) is not installed. "
                "Install heretic[voice] to enable sounddevice playback."
            ) from exc

        try:
            with wave.open(io.BytesIO(wav_bytes)) as wf:
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()
                raw_pcm = wf.readframes(n_frames)
        except Exception as exc:
            raise PlaybackError(f"Failed to parse WAV header: {exc}") from exc

        # Map sample width to numpy dtype
        dtype_map = {1: np.int8, 2: np.int16, 3: np.int32, 4: np.int32}
        dtype = dtype_map.get(sampwidth)
        if dtype is None:
            raise PlaybackError(
                f"Unsupported WAV sample width: {sampwidth} bytes. "
                "Expected 1, 2, or 4 bytes per sample."
            )

        try:
            data = np.frombuffer(raw_pcm, dtype=dtype)
            if n_channels > 1:
                data = data.reshape(-1, n_channels)
        except Exception as exc:
            raise PlaybackError(f"Failed to decode WAV PCM data: {exc}") from exc

        device_arg = None if self._config.device == "default" else self._config.device
        self._log.debug(
            "SoundDeviceBackend.play: %d frames, %d Hz, %d ch, device=%r",
            n_frames,
            framerate,
            n_channels,
            device_arg,
        )

        try:
            sd.play(data, samplerate=framerate, device=device_arg, blocking=True)
        except sd.PortAudioError as exc:
            raise PlaybackError(
                f"PortAudio error during playback: {exc}. "
                "Check that your audio device is connected and not in use."
            ) from exc
        except Exception as exc:
            raise PlaybackError(f"sounddevice playback failed: {exc}") from exc

    def close(self) -> None:
        """Stop any active playback and release sounddevice resources."""
        if self._closed:
            return
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass  # If sounddevice was never used, stop() is a no-op
        self._closed = True
        self._log.debug("SoundDeviceBackend: closed")


# ---------------------------------------------------------------------------
# Platform fallback backend
# ---------------------------------------------------------------------------

class PlatformFallbackBackend(AudioPlayback):
    """Fallback audio playback backend using OS-native commands.

    Used when sounddevice is not installed. Selects the appropriate
    native audio command for the current OS:
        - Windows: winsound.PlaySound (stdlib)
        - macOS:   afplay subprocess
        - Linux:   aplay subprocess, with paplay/play as further fallbacks

    WAV bytes are written to a named temporary file, played via the native
    command, then the temp file is removed in a finally block regardless of
    success or failure.

    Playback quality and latency are lower than SoundDeviceBackend.
    Users who need reliable voice output should install heretic[voice].
    """

    _PLATFORM: str = platform.system()
    """Cached OS identifier: 'Windows', 'Darwin', 'Linux'. Set at class definition time."""

    def __init__(self, config: "RoddTtsConfig", logger: logging.Logger) -> None:
        self._config = config
        self._log = logger
        self._closed: bool = False

    def available(self) -> bool:
        """Return True if the OS-native playback method is available on this machine.

        Never raises — returns False on any exception.
        """
        try:
            if self._PLATFORM == "Windows":
                import winsound  # noqa: F401
                return True
            if self._PLATFORM == "Darwin":
                return shutil.which("afplay") is not None
            if self._PLATFORM == "Linux":
                return (
                    shutil.which("aplay") is not None
                    or shutil.which("paplay") is not None
                    or shutil.which("play") is not None
                )
            return False
        except Exception:
            return False

    def play(self, wav_bytes: bytes) -> None:
        """Play WAV bytes using the OS-native audio command.

        Writes the audio to a temp file, invokes the platform command, and
        removes the temp file in a finally block whether or not playback succeeds.

        Raises:
            PlaybackBackendUnavailableError: if no native player is available.
            PlaybackError: on subprocess failure or OSError.
        """
        if not self.available():
            raise PlaybackBackendUnavailableError(
                f"No native audio player found on {self._PLATFORM!r}. "
                "Install heretic[voice] for sounddevice-based playback."
            )

        tmp_path = None
        try:
            # Write to a named temp file — delete=False so the OS player can open it
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(wav_bytes)
                tmp_path = tmp.name

            self._log.debug(
                "PlatformFallbackBackend.play: temp=%r size=%d platform=%s",
                tmp_path,
                len(wav_bytes),
                self._PLATFORM,
            )
            self._play_via_native(tmp_path)
        except (PlaybackError, PlaybackBackendUnavailableError):
            raise
        except Exception as exc:
            raise PlaybackError(
                f"Platform fallback playback failed ({self._PLATFORM}): {exc}"
            ) from exc
        finally:
            # Always remove the temp file — even if playback failed
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    def _play_via_native(self, wav_path: str) -> None:
        """Invoke the platform-appropriate audio player command.

        Raises:
            PlaybackError: on subprocess failure.
        """
        try:
            if self._PLATFORM == "Windows":
                import winsound
                winsound.PlaySound(wav_path, winsound.SND_FILENAME)
            elif self._PLATFORM == "Darwin":
                subprocess.run(["afplay", wav_path], check=True, capture_output=True)
            elif self._PLATFORM == "Linux":
                self._play_linux(wav_path)
            else:
                raise PlaybackBackendUnavailableError(
                    f"Unsupported platform for fallback playback: {self._PLATFORM!r}"
                )
        except (PlaybackError, PlaybackBackendUnavailableError):
            raise
        except subprocess.CalledProcessError as exc:
            raise PlaybackError(
                f"Audio command failed (exit {exc.returncode}): {exc.stderr!r}"
            ) from exc
        except Exception as exc:
            raise PlaybackError(
                f"Native audio playback error on {self._PLATFORM!r}: {exc}"
            ) from exc

    def _play_linux(self, wav_path: str) -> None:
        """Try aplay, then paplay, then play (sox) on Linux.

        Raises:
            PlaybackError: if all available commands fail.
        """
        for cmd in ("aplay", "paplay", "play"):
            if shutil.which(cmd) is not None:
                flags = ["-q"] if cmd == "aplay" else []
                try:
                    subprocess.run([cmd] + flags + [wav_path], check=True, capture_output=True)
                    return
                except subprocess.CalledProcessError as exc:
                    self._log.debug("Linux audio command %r failed: %s", cmd, exc)
                    continue
        raise PlaybackError(
            "All Linux audio commands (aplay, paplay, play) failed or are unavailable."
        )

    def close(self) -> None:
        """No persistent resources held — mark as closed."""
        self._closed = True
        self._log.debug("PlatformFallbackBackend: closed")


# ---------------------------------------------------------------------------
# Null backend — silent fallback for graceful degradation
# ---------------------------------------------------------------------------

class NullPlaybackBackend(AudioPlayback):
    """Silent no-op playback backend.

    Used when neither sounddevice nor any OS-native player is available.
    All operations succeed silently so the ceremony continues text-only
    without crashing. The Tunga orchestrator checks available() and enters
    degraded mode after construction, so play() should not normally be called —
    but it is safe if it is.
    """

    def __init__(self, config: "RoddTtsConfig", logger: logging.Logger) -> None:
        self._config = config
        self._log = logger
        self._closed: bool = False

    def available(self) -> bool:
        """Always returns False — this backend produces no audio."""
        return False

    def play(self, wav_bytes: bytes) -> None:
        """Silent no-op — does not play audio. Logs at DEBUG."""
        self._log.debug(
            "NullPlaybackBackend.play: discarding %d WAV bytes (no audio backend)",
            len(wav_bytes),
        )

    def close(self) -> None:
        """No-op close — marks as closed."""
        self._closed = True
        self._log.debug("NullPlaybackBackend: closed")
