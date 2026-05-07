"""
Voice Activity Detection backends — L2 Rödd Hlust substrate.

Defines the VadDetector abstract base class and three concrete backends:

- WebRtcVadBackend: primary VAD using webrtcvad-wheels (BSD-3, prebuilt). Operates on
  16 kHz mono int16 frames at exactly 30 ms (960 bytes). Aggressive-mode aggressiveness
  is configurable via the vad_threshold config field (see below).
- EnergyThresholdBackend: fallback VAD using RMS energy computation — zero deps,
  always available. Less accurate in noisy environments; use only when webrtcvad
  is unavailable.
- NullVadBackend: silent fallback — never detects speech; used when the ceremony
  must run without any VAD capability (unusual; Hlust falls back to stdin).

Hlust selects the backend at init time via ``VadDetector.best_available()``.

Utterance-completion model:
    VadDetector.utterance_complete(frames) returns True when a sufficient run of
    trailing non-speech frames has been observed after an initial speech-containing
    run. The required silence count is derived from the config threshold but the
    exact implementation is Forge's responsibility.

Frame contract (matches microphone.py FRAME_BYTES invariant):
    sample_rate : 16 000 Hz
    dtype       : int16 (raw bytes, not numpy arrays)
    frame_bytes : 960 bytes per call to is_speech()
"""

from __future__ import annotations

import abc
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from heretic.rodd.config_model import RoddSttConfig


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class VadDetector(abc.ABC):
    """Contract for all Voice Activity Detection backends.

    Implementations classify individual 30 ms frames as speech or non-speech,
    and accumulate frame history to decide when an utterance is complete.

    Lifecycle (used by Hlust orchestrator):
        vad = VadDetector.best_available(config, logger)
        vad.reset()
        while capturing:
            frame = <960 bytes from MicrophoneCapture callback>
            if vad.is_speech(frame):
                ...buffer accumulation...
            if vad.utterance_complete(accumulated_frames):
                transcript = whisper.transcribe(concat(accumulated_frames), ...)
                break
    """

    @classmethod
    @abc.abstractmethod
    def available(cls) -> bool:
        """Return True if this backend can be instantiated on the current platform.

        Probes required dependencies without raising.
        """

    @abc.abstractmethod
    def is_speech(self, frame: bytes) -> bool:
        """Classify one 30 ms frame as speech or non-speech.

        Args:
            frame: Exactly 960 bytes of 16 kHz mono int16 PCM audio.

        Returns:
            True if the frame contains speech energy above the configured threshold.

        Raises:
            VadError: if the frame is malformed (wrong length or corrupt audio).
        """

    @abc.abstractmethod
    def utterance_complete(self, frames: list[bytes]) -> bool:
        """Return True when the frame sequence indicates the utterance has ended.

        Inspects the tail of ``frames`` for a run of consecutive non-speech frames
        long enough to conclude the speaker has paused. The required silence length
        is derived from the config (typically 600–800 ms = 20–27 frames at 30 ms).

        Args:
            frames: All frames accumulated since last reset(), including silence.

        Returns:
            True when trailing silence exceeds the configured end-of-utterance threshold.
        """

    @abc.abstractmethod
    def reset(self) -> None:
        """Reset internal state for a new utterance.

        Called by Hlust before each new capture cycle. Clears any frame-history
        state accumulated from a previous utterance.
        """

    @staticmethod
    def best_available(
        config: "RoddSttConfig",
        logger: logging.Logger,
    ) -> "VadDetector":
        """Factory: return the best available VadDetector for this machine.

        Preference order:
            1. WebRtcVadBackend       — requires webrtcvad-wheels (in [voice] extra)
            2. EnergyThresholdBackend — pure Python; always available
            3. NullVadBackend         — no detection; Hlust falls back to stdin

        Args:
            config: RoddSttConfig from heretic.yaml. Carries vad_threshold.
            logger: Logger instance from grunnr.logger.get_logger.

        Returns:
            A VadDetector instance. Never raises.
        """
        if WebRtcVadBackend.available():
            logger.debug("VadDetector.best_available: selecting WebRtcVadBackend")
            return WebRtcVadBackend(config=config, logger=logger)

        logger.warning(
            "VadDetector.best_available: webrtcvad-wheels not available "
            "(try: pip install heretic[voice]). "
            "Falling back to EnergyThresholdBackend."
        )
        if EnergyThresholdBackend.available():
            return EnergyThresholdBackend(config=config, logger=logger)

        logger.warning(
            "VadDetector.best_available: EnergyThresholdBackend also unavailable. "
            "Using NullVadBackend — Hlust will not detect speech."
        )
        return NullVadBackend(config=config, logger=logger)


# ---------------------------------------------------------------------------
# WebRtcVadBackend — primary backend
# ---------------------------------------------------------------------------

class WebRtcVadBackend(VadDetector):
    """Primary VAD backend using the webrtcvad-wheels library (BSD-3).

    Wraps webrtcvad.Vad, which implements Google's WebRTC VAD — a small,
    fast, non-ML classifier operating on 30 ms frames at 16 kHz. Four
    aggressiveness modes (0–3) control sensitivity; HERETIC maps the
    float ``vad_threshold`` (0.0–1.0) to an integer mode.

    Threshold-to-mode mapping (Forge decides exact boundaries):
        0.0–0.25  => mode 0 (least aggressive — more liberal)
        0.25–0.5  => mode 1
        0.5–0.75  => mode 2
        0.75–1.0  => mode 3 (most aggressive — suppresses more noise)

    The default ``vad_threshold: 0.6`` maps to mode 2.
    """

    def __init__(self, config: "RoddSttConfig", logger: logging.Logger) -> None:
        """Initialise the WebRTC VAD.

        Args:
            config: RoddSttConfig; reads vad_threshold.
            logger: Logger instance.
        """
        self._config = config
        self._log = logger
        self._vad: object | None = None  # webrtcvad.Vad at runtime

    @classmethod
    def available(cls) -> bool:
        """Return True if webrtcvad can be imported."""
        raise NotImplementedError(
            "Forge will implement: attempt `import webrtcvad` and return True/False. "
            "Never raise — catch ImportError and return False."
        )

    def is_speech(self, frame: bytes) -> bool:
        """Classify one 30 ms frame via webrtcvad.Vad.is_speech().

        Forge will implement: call self._vad.is_speech(frame, SAMPLE_RATE).
        Raise VadError on malformed frame (wrong length). Lazy-init self._vad
        on first call if not yet constructed.
        """
        raise NotImplementedError(
            "Forge will implement: lazy-init webrtcvad.Vad(mode), "
            "call .is_speech(frame, 16000), raise VadError on bad frame length."
        )

    def utterance_complete(self, frames: list[bytes]) -> bool:
        """Return True after sufficient trailing silence (config-driven).

        Forge will implement: inspect the tail of frames, count consecutive
        non-speech frames (via is_speech()), return True when the count exceeds
        the silence threshold (derived from vad_threshold: ~20 frames = 600 ms).
        Requires that at least one speech frame was seen before the silence run.
        """
        raise NotImplementedError(
            "Forge will implement: count trailing non-speech frames in `frames`; "
            "return True when silence_frame_count >= silence_threshold AND at least "
            "one speech frame preceded the silence. Threshold ~600 ms = 20 frames."
        )

    def reset(self) -> None:
        """Reset internal utterance state.

        Forge will implement: clear any per-utterance counters or frame history.
        The webrtcvad.Vad object itself is stateless per-frame, so this may be
        a no-op unless EnergyThresholdBackend-style history is mirrored here.
        """
        raise NotImplementedError(
            "Forge will implement: reset any per-utterance state counters."
        )


# ---------------------------------------------------------------------------
# EnergyThresholdBackend — pure-Python fallback
# ---------------------------------------------------------------------------

class EnergyThresholdBackend(VadDetector):
    """Fallback VAD using root-mean-square energy computation.

    Zero dependencies — uses only the Python standard library. Computes the
    RMS amplitude of each 30 ms frame and compares it to a fixed energy
    threshold derived from the config. Less accurate than webrtcvad in real-world
    conditions (fans, breathing, ambient noise) but guarantees basic VAD when
    webrtcvad-wheels is not installed.

    The ``vad_threshold`` config value (0.0–1.0) is mapped to an internal RMS
    threshold by Forge at implementation time (exact mapping is an implementation
    concern, not an architectural one — Forge has latitude to calibrate).
    """

    def __init__(self, config: "RoddSttConfig", logger: logging.Logger) -> None:
        self._config = config
        self._log = logger
        self._speech_seen: bool = False
        self._silence_count: int = 0

    @classmethod
    def available(cls) -> bool:
        """Always True — EnergyThresholdBackend has no external deps."""
        return True

    def is_speech(self, frame: bytes) -> bool:
        """Classify frame by RMS energy.

        Forge will implement: unpack frame as 16-bit signed integers, compute
        RMS, compare to threshold derived from vad_threshold config.
        Track and update self._speech_seen and self._silence_count.
        """
        raise NotImplementedError(
            "Forge will implement: unpack int16 samples from frame bytes, "
            "compute RMS, compare to energy threshold derived from config.vad_threshold. "
            "Update self._speech_seen and self._silence_count."
        )

    def utterance_complete(self, frames: list[bytes]) -> bool:
        """Return True after self._speech_seen and sufficient trailing silence.

        Forge will implement: return True when self._speech_seen is True AND
        self._silence_count exceeds the silence threshold (~600 ms = 20 frames).
        """
        raise NotImplementedError(
            "Forge will implement: return True when speech_seen and silence_count "
            "exceeds the end-of-utterance threshold (~20 frames at 30 ms = 600 ms)."
        )

    def reset(self) -> None:
        """Reset per-utterance state."""
        self._speech_seen = False
        self._silence_count = 0
        self._log.debug("EnergyThresholdBackend.reset: utterance state cleared")


# ---------------------------------------------------------------------------
# NullVadBackend — silent fallback
# ---------------------------------------------------------------------------

class NullVadBackend(VadDetector):
    """No-op VAD. Never detects speech. Always reports utterance incomplete.

    Used as a last resort when neither webrtcvad nor energy detection is available.
    Hlust detects the Null backend and falls back to stdin input for the ceremony.
    """

    def __init__(self, config: "RoddSttConfig", logger: logging.Logger) -> None:
        self._config = config
        self._log = logger

    @classmethod
    def available(cls) -> bool:
        """Always True."""
        return True

    def is_speech(self, frame: bytes) -> bool:
        """Always returns False."""
        return False

    def utterance_complete(self, frames: list[bytes]) -> bool:
        """Always returns False — the Null backend never completes an utterance."""
        return False

    def reset(self) -> None:
        """No-op."""
