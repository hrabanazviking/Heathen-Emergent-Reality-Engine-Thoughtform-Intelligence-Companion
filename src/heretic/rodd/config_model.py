"""
Rodd config model — dataclasses mirroring the ``rodd:`` YAML subtree.

RoddConfig, RoddTtsConfig, and RoddSttConfig are populated by Grunnr's config
loader from the ``rodd:`` section of heretic.yaml. They are also re-exported
from ``heretic.grunnr.config.HereticConfig.rodd`` so callers do not need to
import from both modules.

The canonical type definitions live here (in the rodd package) to keep L2
self-contained; Grunnr's config.py imports RoddConfig, RoddTtsConfig, and
RoddSttConfig from this module.

All defaults match the reference block in LAYER_INTERFACES.md §L2 Rödd.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from heretic.rodd.errors import TungaConfigError


# ---------------------------------------------------------------------------
# RoddTtsConfig — Tunga (mouth / TTS) half
# ---------------------------------------------------------------------------

@dataclass
class RoddTtsConfig:
    """TTS settings — the Tunga (tongue) half of L2 Rödd.

    Mirrors the ``rodd.tts:`` YAML block documented in LAYER_INTERFACES.md §L2.

    All path fields are relative — never absolute. Endpoint is a URL string that
    may reference a Tailscale IP or hostname; resolution is done at runtime by
    ChatterboxHttpClient.
    """

    enabled: bool = True
    """Whether TTS output is active. When False, Tunga exits silently on feed_chunk()."""

    engine: str = "chatterbox"
    """TTS backend: ``chatterbox`` (default) | ``openai_compat`` (future)."""

    endpoint: str = "http://100.66.178.105:7851"
    """ChatterBox service base URL (Pi endpoint). Never hardcoded absolute path."""

    voice_id: str = "default"
    """Voice identifier sent to ChatterBox. ``default`` = built-in ChatterBox voice."""

    voice_prompt_path: str | None = None
    """Optional path to a .wav voice prompt file (relative to heretic data dir).
    Must be >= 5 s for the ``turbo`` model. None = use ChatterBox default voice.
    v0.2: ships as None; user may configure later."""

    model: str = "turbo"
    """ChatterBox model variant: ``turbo`` | ``tts`` | ``multilingual``.
    ``turbo`` is the v0.2 default — lowest latency, always-warm."""

    language_id: str = "en"
    """BCP-47 language code. Only used by the ``multilingual`` model."""

    exaggeration: float = 0.5
    """Emotional exaggeration factor. Range: 0.0–2.0."""

    cfg_weight: float = 1.0
    """CFG guidance weight. Range: 0.0–2.0. Only used by the ``tts`` model."""

    temperature: float = 0.8
    """Sampling temperature. Range: 0.05–2.0. Default per ChatterBox API spec."""

    top_p: float = 0.95
    """Nucleus sampling cutoff. Range: 0.0–1.0."""

    repetition_penalty: float = 1.2
    """Repetition penalty. Range: 0.1–5.0. Default per ChatterBox API spec."""

    device: str = "default"
    """Audio output device name or ``default`` (OS default speaker)."""

    speed: float = 1.0
    """Playback speed multiplier (applied by the playback backend, not ChatterBox)."""

    request_timeout_seconds: int = 30
    """HTTP timeout for /v1/audio/speech requests. Raise ChatterboxTimeoutError on breach."""

    chunk_min_chars: int = 80
    """Minimum accumulated characters before flushing a sentence-boundary chunk to TTS.
    Prevents single-word audio requests (jarring); balances latency vs. naturalness.
    Set per v0.2 architectural decision in TASK_HERETIC_v0.2_FIRST_VOICE.md §4."""

    sentence_terminators: tuple[str, ...] = field(
        default_factory=lambda: (". ", "! ", "? ", "\n\n")
    )
    """Substrings that mark a sentence boundary for streaming chunking."""

    def __post_init__(self) -> None:
        """Validate field ranges. Raises TungaConfigError on any violation."""
        if not self.endpoint:
            raise TungaConfigError(
                "rodd.tts.endpoint must be a non-empty URL string. "
                "Set it in heretic.yaml under rodd.tts.endpoint."
            )
        if not (0.05 <= self.temperature <= 2.0):
            raise TungaConfigError(
                f"rodd.tts.temperature must be between 0.05 and 2.0, got {self.temperature}."
            )
        if not (0.0 <= self.exaggeration <= 2.0):
            raise TungaConfigError(
                f"rodd.tts.exaggeration must be between 0.0 and 2.0, got {self.exaggeration}."
            )
        if not (0.0 <= self.cfg_weight <= 2.0):
            raise TungaConfigError(
                f"rodd.tts.cfg_weight must be between 0.0 and 2.0, got {self.cfg_weight}."
            )
        if not (0.1 <= self.repetition_penalty <= 5.0):
            raise TungaConfigError(
                f"rodd.tts.repetition_penalty must be between 0.1 and 5.0, "
                f"got {self.repetition_penalty}."
            )
        if self.chunk_min_chars < 1:
            raise TungaConfigError(
                f"rodd.tts.chunk_min_chars must be >= 1, got {self.chunk_min_chars}."
            )


# ---------------------------------------------------------------------------
# RoddSttConfig — Hlust (ear / STT) half
# ---------------------------------------------------------------------------

@dataclass
class RoddSttConfig:
    """STT settings — the Hlust (ear) half of L2 Rödd.

    Mirrors the ``rodd.stt:`` YAML block documented in LAYER_INTERFACES.md §L2.
    Hlust is implemented in v0.3; these fields are declared now so heretic.yaml
    can carry the full ``rodd:`` block without parse errors.

    All path fields are relative — never absolute.
    """

    enabled: bool = True
    """Whether STT input is active. When False, Hlust does not start."""

    engine: str = "whisper_cpp"
    """STT backend: ``whisper_cpp`` (default) | future backends."""

    model_path: str = "models/ggml-base.en.bin"
    """Path to the Whisper GGML model file, relative to the HERETIC data directory."""

    device: str = "default"
    """Microphone device name or ``default`` (OS default mic)."""

    vad_threshold: float = 0.6
    """Voice Activity Detection confidence threshold. Range: 0.0–1.0."""

    language: str = "en"
    """BCP-47 language code for transcription."""

    load_strategy: str = "lazy"
    """``lazy`` = load model on first utterance; ``eager`` = load at Kynding."""


# ---------------------------------------------------------------------------
# RoddConfig — root for L2 Rödd
# ---------------------------------------------------------------------------

@dataclass
class RoddConfig:
    """L2 Rödd — complete voice layer settings.

    Contains both halves — Tunga (TTS out) and Hlust (STT in). Each half is
    independently operable: TTS can be enabled while STT is disabled and vice-versa.

    Consumed by Tunga.__init__() and (in v0.3) Hlust.__init__().
    """

    tts: RoddTtsConfig = field(default_factory=RoddTtsConfig)
    """Tunga (mouth) settings."""

    stt: RoddSttConfig = field(default_factory=RoddSttConfig)
    """Hlust (ear) settings."""
