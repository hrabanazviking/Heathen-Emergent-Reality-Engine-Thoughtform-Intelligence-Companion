"""
Voice Activity Detection backends — L2 Rödd Hlust substrate.

Defines the VadDetector abstract base class and three concrete backends:

- WebRtcVadBackend: primary VAD using webrtcvad-wheels (BSD-3, prebuilt). Operates on
  16 kHz mono int16 frames at exactly 30 ms (960 bytes). Aggressiveness is derived
  from the vad_threshold config field — see the mapping note below.
- EnergyThresholdBackend: fallback VAD using RMS energy computation — zero deps,
  always available. Less accurate in noisy environments; use only when webrtcvad
  is unavailable.
- NullVadBackend: fixed-window fallback — assumes all frames are speech, triggers
  utterance end after a hard 3-second cap. Used as a last-resort when neither
  webrtcvad nor energy detection is reliable.

Hlust selects the backend at init time via ``VadDetector.best_available()``.

--- vad_threshold → webrtcvad aggressiveness mapping ---

The HERETIC config field ``rodd.stt.vad_threshold`` is a float in [0.0, 1.0].
WebRTC VAD's ``set_mode()`` accepts an integer in [0, 3] (aggressiveness):
    0 = least aggressive (allows more liberal speech classification, lower false-neg)
    3 = most aggressive (filters more noise, higher false-neg rate)

Mapping applied by WebRtcVadBackend:
    aggressiveness = max(0, min(3, round(vad_threshold * 3)))

Examples:
    vad_threshold=0.0  -> aggressiveness=0
    vad_threshold=0.33 -> aggressiveness=1
    vad_threshold=0.5  -> aggressiveness=2  (default 0.6 also maps to 2)
    vad_threshold=0.67 -> aggressiveness=2
    vad_threshold=1.0  -> aggressiveness=3

The Cartographer flagged this impedance mismatch (DATA_FLOW.md §4.7.5); this
mapping resolves it cleanly with no loss of precision at the config layer.

Frame contract (matches microphone.py FRAME_BYTES invariant):
    sample_rate : 16 000 Hz
    dtype       : int16 (raw bytes, not numpy arrays)
    frame_bytes : 960 bytes per call to is_speech()
"""

from __future__ import annotations

import abc
import logging
import struct
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from heretic.rodd.config_model import RoddSttConfig

from heretic.rodd.microphone import FRAME_BYTES, FRAME_MS

# ---------------------------------------------------------------------------
# Silence threshold constants
# ---------------------------------------------------------------------------

# 800 ms of trailing silence = 800 / 30 = ~26.7 frames → 27 frames (rounded up).
# This is the number of consecutive non-speech frames required to conclude that
# the user has finished speaking.  Derived from the frame duration constant so
# it remains correct if FRAME_MS is ever changed.
_SILENCE_THRESHOLD_MS: int = 800
_SILENCE_FRAMES: int = math.ceil(_SILENCE_THRESHOLD_MS / FRAME_MS)  # 27

# Minimum number of speech frames required before we start counting silence.
# Prevents instant utterance-complete on leading silence at the start of capture.
_MIN_SPEECH_FRAMES: int = 3


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
        is _SILENCE_FRAMES (27 frames = ~800 ms at 30 ms/frame).

        Args:
            frames: All frames accumulated since last reset(), including silence.

        Returns:
            True when trailing silence exceeds the configured end-of-utterance threshold
            AND at least _MIN_SPEECH_FRAMES speech frames were observed first.
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
    float ``vad_threshold`` (0.0–1.0) to an integer mode using:

        aggressiveness = max(0, min(3, round(vad_threshold * 3)))

    This ensures:
        vad_threshold=0.0  -> mode 0 (least aggressive)
        vad_threshold=0.5  -> mode 2 (default config=0.6 also maps here)
        vad_threshold=1.0  -> mode 3 (most aggressive)

    The webrtcvad.Vad object itself is stateless per-frame; per-utterance
    state (speech count, silence count) is tracked in this wrapper.
    """

    def __init__(self, config: "RoddSttConfig", logger: logging.Logger) -> None:
        """Initialise the WebRTC VAD.

        Args:
            config: RoddSttConfig; reads vad_threshold.
            logger: Logger instance.
        """
        self._config = config
        self._log = logger
        self._vad: object | None = None  # webrtcvad.Vad at runtime (lazy init)
        self._speech_frames: int = 0
        self._silence_frames: int = 0

    @classmethod
    def available(cls) -> bool:
        """Return True if webrtcvad can be imported.

        Never raises — catches ImportError and returns False.
        """
        try:
            import webrtcvad  # noqa: F401
            return True
        except ImportError:
            return False

    def _get_vad(self) -> object:
        """Lazy-initialise and return the webrtcvad.Vad instance.

        Maps vad_threshold (0.0–1.0) to webrtcvad aggressiveness (0–3):
            aggressiveness = max(0, min(3, round(vad_threshold * 3)))
        """
        if self._vad is None:
            import webrtcvad
            # Cartographer-flagged impedance mismatch resolution:
            # vad_threshold is a float [0,1]; webrtcvad expects int [0,3].
            aggressiveness = max(0, min(3, round(self._config.vad_threshold * 3)))
            self._log.debug(
                "WebRtcVadBackend: vad_threshold=%.2f -> aggressiveness=%d",
                self._config.vad_threshold,
                aggressiveness,
            )
            vad = webrtcvad.Vad()
            vad.set_mode(aggressiveness)
            self._vad = vad
        return self._vad

    def is_speech(self, frame: bytes) -> bool:
        """Classify one 30 ms frame via webrtcvad.Vad.is_speech().

        Args:
            frame: Exactly FRAME_BYTES (960) bytes of 16 kHz mono int16 PCM.

        Returns:
            True if webrtcvad classifies the frame as containing speech.

        Raises:
            VadError: if the frame has the wrong byte length.
        """
        from heretic.rodd.errors import VadError

        if len(frame) != FRAME_BYTES:
            raise VadError(
                f"WebRtcVadBackend.is_speech: expected {FRAME_BYTES} bytes, "
                f"got {len(frame)}. Frame must be exactly 30 ms of 16 kHz int16 mono audio."
            )
        try:
            vad = self._get_vad()
            result: bool = vad.is_speech(frame, 16_000)
            # Update internal state for utterance_complete() tracking
            if result:
                self._speech_frames += 1
                self._silence_frames = 0
            else:
                self._silence_frames += 1
            return result
        except Exception as exc:
            from heretic.rodd.errors import VadError as VE
            raise VE(f"WebRtcVadBackend.is_speech error: {exc}") from exc

    def utterance_complete(self, frames: list[bytes]) -> bool:
        """Return True after sufficient trailing silence following at least some speech.

        Uses the internally-tracked speech and silence counters maintained by
        is_speech() rather than re-classifying the frame list. This avoids
        redundant classification work.

        Requires:
            - At least _MIN_SPEECH_FRAMES speech frames were observed.
            - The current trailing silence run exceeds _SILENCE_FRAMES (~800 ms).

        Args:
            frames: Accumulated frames (used only for fallback length check; state
                    is maintained in is_speech() tracking counters).

        Returns:
            True when the utterance appears complete.
        """
        return (
            self._speech_frames >= _MIN_SPEECH_FRAMES
            and self._silence_frames >= _SILENCE_FRAMES
        )

    def reset(self) -> None:
        """Reset per-utterance tracking state.

        Clears speech and silence frame counters. The webrtcvad.Vad object
        itself is stateless and is retained across utterances (no re-init needed).
        """
        self._speech_frames = 0
        self._silence_frames = 0
        self._log.debug("WebRtcVadBackend.reset: utterance state cleared")


# ---------------------------------------------------------------------------
# EnergyThresholdBackend — pure-Python fallback
# ---------------------------------------------------------------------------

class EnergyThresholdBackend(VadDetector):
    """Fallback VAD using root-mean-square energy computation.

    Zero dependencies — uses only the Python standard library. Computes the
    RMS amplitude of each 30 ms frame and compares it to a threshold derived
    from the config. Less accurate than webrtcvad in real-world conditions
    (fans, breathing, ambient noise) but guarantees basic VAD when
    webrtcvad-wheels is not installed.

    RMS threshold derivation from vad_threshold (0.0–1.0):
        rms_threshold = 300 + round(vad_threshold * 1500)

    This maps:
        vad_threshold=0.0 -> rms_threshold=300  (very sensitive, picks up quiet speech)
        vad_threshold=0.5 -> rms_threshold=1050 (moderate; filters fan noise)
        vad_threshold=1.0 -> rms_threshold=1800 (suppresses most ambient noise)

    Typical quiet ambient noise RMS: 50–200. Typical speech RMS: 800–3000.
    The scale gives practical dynamic range without requiring calibration.
    """

    def __init__(self, config: "RoddSttConfig", logger: logging.Logger) -> None:
        self._config = config
        self._log = logger
        self._speech_seen: bool = False
        self._silence_count: int = 0
        # Derive threshold once at init for efficiency
        self._rms_threshold: float = 300.0 + round(config.vad_threshold * 1500)

    @classmethod
    def available(cls) -> bool:
        """Always True — EnergyThresholdBackend has no external deps."""
        return True

    def is_speech(self, frame: bytes) -> bool:
        """Classify frame by RMS energy against the configured threshold.

        Unpacks the frame as signed 16-bit little-endian samples, computes RMS,
        and compares to the config-derived threshold.  Updates self._speech_seen
        and self._silence_count for utterance_complete() decisions.

        Args:
            frame: FRAME_BYTES (960) bytes of int16 PCM audio.

        Returns:
            True if RMS exceeds the configured energy threshold.
        """
        # Unpack all FRAME_SAMPLES (480) int16 samples from the frame bytes.
        # struct.unpack is used (stdlib-only, no numpy dep) for cross-platform compat.
        n_samples = len(frame) // 2
        if n_samples == 0:
            self._silence_count += 1
            return False

        samples = struct.unpack(f"<{n_samples}h", frame[:n_samples * 2])
        # RMS = sqrt(mean(sample^2))
        mean_sq = sum(s * s for s in samples) / n_samples
        rms = math.sqrt(mean_sq)

        speech = rms > self._rms_threshold
        if speech:
            self._speech_seen = True
            self._silence_count = 0
        else:
            self._silence_count += 1

        return speech

    def utterance_complete(self, frames: list[bytes]) -> bool:
        """Return True after speech has been observed and trailing silence exceeds threshold.

        Requires:
            - self._speech_seen is True (at least one speech frame was classified).
            - self._silence_count exceeds _SILENCE_FRAMES (~800 ms of trailing silence).

        Args:
            frames: Accumulated frames (not re-classified; uses internal state).

        Returns:
            True when the utterance appears complete.
        """
        return self._speech_seen and self._silence_count >= _SILENCE_FRAMES

    def reset(self) -> None:
        """Reset per-utterance state."""
        self._speech_seen = False
        self._silence_count = 0
        self._log.debug("EnergyThresholdBackend.reset: utterance state cleared")


# ---------------------------------------------------------------------------
# NullVadBackend — fixed-window fallback
# ---------------------------------------------------------------------------

# Fixed-window capture duration in milliseconds.  When neither WebRTC VAD nor
# energy-threshold VAD is available, Hlust falls back to capturing a fixed window
# of audio before transcribing.  3 seconds is long enough for a typical voice command.
_NULL_VAD_WINDOW_MS: int = 3000
_NULL_VAD_WINDOW_FRAMES: int = _NULL_VAD_WINDOW_MS // FRAME_MS  # 100 frames


class NullVadBackend(VadDetector):
    """Fixed-window VAD fallback. Assumes all frames contain speech.

    When no real VAD is available, Hlust needs a way to know when an utterance
    has ended without analysis.  This backend assumes every frame is speech and
    triggers utterance_complete() after a fixed 3-second window.

    This is a last-resort path — the Hlust is_available check will also be False
    (because mic or Whisper will be Null), so this backend should almost never
    run in practice.  It is present for completeness and defensive coding.
    """

    def __init__(self, config: "RoddSttConfig", logger: logging.Logger) -> None:
        self._config = config
        self._log = logger

    @classmethod
    def available(cls) -> bool:
        """Always True."""
        return True

    def is_speech(self, frame: bytes) -> bool:
        """Always returns True — NullVadBackend assumes all audio is speech."""
        return True

    def utterance_complete(self, frames: list[bytes]) -> bool:
        """Return True after the fixed 3-second window has elapsed.

        Args:
            frames: Accumulated frames. Length is compared to the fixed-window cap.

        Returns:
            True when len(frames) * FRAME_MS >= _NULL_VAD_WINDOW_MS (3000 ms).
        """
        return len(frames) >= _NULL_VAD_WINDOW_FRAMES

    def reset(self) -> None:
        """No-op — NullVadBackend has no per-utterance state."""
