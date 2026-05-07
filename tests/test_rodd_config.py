"""
Tests — heretic.rodd config_model (RoddTtsConfig, RoddSttConfig, RoddConfig).

Verifies defaults, validation ranges, and boundary conditions.
"""

from __future__ import annotations

import pytest

from heretic.rodd.config_model import RoddConfig, RoddSttConfig, RoddTtsConfig
from heretic.rodd.errors import TungaConfigError


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------

def test_rodd_tts_config_defaults() -> None:
    """RoddTtsConfig defaults match the LAYER_INTERFACES.md §L2 reference block."""
    cfg = RoddTtsConfig()
    assert cfg.enabled is True
    assert cfg.engine == "chatterbox"
    assert cfg.endpoint == "http://100.66.178.105:7851"
    assert cfg.voice_id == "default"
    assert cfg.model == "turbo"
    assert cfg.language_id == "en"
    assert cfg.temperature == 0.8
    assert cfg.exaggeration == 0.5
    assert cfg.cfg_weight == 1.0
    assert cfg.top_p == 0.95
    assert cfg.repetition_penalty == 1.2
    assert cfg.device == "default"
    assert cfg.speed == 1.0
    assert cfg.request_timeout_seconds == 30
    assert cfg.chunk_min_chars == 80
    assert ". " in cfg.sentence_terminators
    assert "! " in cfg.sentence_terminators
    assert "? " in cfg.sentence_terminators
    assert "\n\n" in cfg.sentence_terminators


def test_rodd_stt_config_defaults() -> None:
    """RoddSttConfig defaults match the LAYER_INTERFACES.md §L2 reference block."""
    cfg = RoddSttConfig()
    assert cfg.enabled is True
    assert cfg.engine == "whisper_cpp"
    assert cfg.model_path == "models/ggml-base.en.bin"
    assert cfg.device == "default"
    assert cfg.vad_threshold == 0.6
    assert cfg.language == "en"
    assert cfg.load_strategy == "lazy"


def test_rodd_config_wraps_both_halves() -> None:
    """RoddConfig.tts and RoddConfig.stt are the correct sub-config types."""
    cfg = RoddConfig()
    assert isinstance(cfg.tts, RoddTtsConfig)
    assert isinstance(cfg.stt, RoddSttConfig)


# ---------------------------------------------------------------------------
# Validation — empty endpoint
# ---------------------------------------------------------------------------

def test_rodd_tts_config_rejects_empty_endpoint() -> None:
    """RoddTtsConfig raises TungaConfigError when endpoint is empty string."""
    with pytest.raises(TungaConfigError, match="endpoint"):
        RoddTtsConfig(endpoint="")


# ---------------------------------------------------------------------------
# Validation — temperature range
# ---------------------------------------------------------------------------

def test_rodd_tts_config_rejects_temperature_below_minimum() -> None:
    """RoddTtsConfig raises TungaConfigError when temperature < 0.05."""
    with pytest.raises(TungaConfigError, match="temperature"):
        RoddTtsConfig(temperature=0.04)


def test_rodd_tts_config_rejects_temperature_above_maximum() -> None:
    """RoddTtsConfig raises TungaConfigError when temperature > 2.0."""
    with pytest.raises(TungaConfigError, match="temperature"):
        RoddTtsConfig(temperature=2.01)


def test_rodd_tts_config_accepts_temperature_at_min_boundary() -> None:
    """RoddTtsConfig does not raise when temperature == 0.05 (lower boundary)."""
    cfg = RoddTtsConfig(temperature=0.05)
    assert cfg.temperature == 0.05


def test_rodd_tts_config_accepts_temperature_at_max_boundary() -> None:
    """RoddTtsConfig does not raise when temperature == 2.0 (upper boundary)."""
    cfg = RoddTtsConfig(temperature=2.0)
    assert cfg.temperature == 2.0


# ---------------------------------------------------------------------------
# Validation — exaggeration range
# ---------------------------------------------------------------------------

def test_rodd_tts_config_rejects_exaggeration_out_of_range() -> None:
    """RoddTtsConfig raises TungaConfigError when exaggeration < 0.0 or > 2.0."""
    with pytest.raises(TungaConfigError, match="exaggeration"):
        RoddTtsConfig(exaggeration=-0.01)
    with pytest.raises(TungaConfigError, match="exaggeration"):
        RoddTtsConfig(exaggeration=2.01)


def test_rodd_tts_config_accepts_exaggeration_boundaries() -> None:
    """RoddTtsConfig accepts 0.0 and 2.0 for exaggeration."""
    RoddTtsConfig(exaggeration=0.0)
    RoddTtsConfig(exaggeration=2.0)


# ---------------------------------------------------------------------------
# Validation — cfg_weight range
# ---------------------------------------------------------------------------

def test_rodd_tts_config_rejects_cfg_weight_out_of_range() -> None:
    """RoddTtsConfig raises TungaConfigError when cfg_weight < 0.0 or > 2.0."""
    with pytest.raises(TungaConfigError, match="cfg_weight"):
        RoddTtsConfig(cfg_weight=-0.01)
    with pytest.raises(TungaConfigError, match="cfg_weight"):
        RoddTtsConfig(cfg_weight=2.01)


# ---------------------------------------------------------------------------
# Validation — repetition_penalty range
# ---------------------------------------------------------------------------

def test_rodd_tts_config_rejects_repetition_penalty_out_of_range() -> None:
    """RoddTtsConfig raises TungaConfigError when repetition_penalty < 0.1 or > 5.0."""
    with pytest.raises(TungaConfigError, match="repetition_penalty"):
        RoddTtsConfig(repetition_penalty=0.09)
    with pytest.raises(TungaConfigError, match="repetition_penalty"):
        RoddTtsConfig(repetition_penalty=5.01)


# ---------------------------------------------------------------------------
# Validation — chunk_min_chars
# ---------------------------------------------------------------------------

def test_rodd_tts_config_rejects_chunk_min_chars_zero() -> None:
    """RoddTtsConfig raises TungaConfigError when chunk_min_chars < 1."""
    with pytest.raises(TungaConfigError, match="chunk_min_chars"):
        RoddTtsConfig(chunk_min_chars=0)
    with pytest.raises(TungaConfigError, match="chunk_min_chars"):
        RoddTtsConfig(chunk_min_chars=-5)


def test_rodd_tts_config_accepts_chunk_min_chars_one() -> None:
    """RoddTtsConfig accepts chunk_min_chars=1 (minimum valid value)."""
    cfg = RoddTtsConfig(chunk_min_chars=1)
    assert cfg.chunk_min_chars == 1


# ---------------------------------------------------------------------------
# Boundary acceptance
# ---------------------------------------------------------------------------

def test_rodd_tts_config_accepts_all_valid_boundary_values() -> None:
    """RoddTtsConfig does not raise for all valid boundary values simultaneously."""
    cfg = RoddTtsConfig(
        endpoint="http://localhost:7851",
        temperature=0.05,
        exaggeration=0.0,
        cfg_weight=0.0,
        repetition_penalty=0.1,
        chunk_min_chars=1,
    )
    assert cfg.endpoint == "http://localhost:7851"


# ---------------------------------------------------------------------------
# Grunnr round-trip
# ---------------------------------------------------------------------------

def test_heretic_config_rodd_round_trip() -> None:
    """HereticConfig.rodd survives default construction with correct types."""
    from heretic.grunnr.config import HereticConfig
    cfg = HereticConfig.default()
    # grunnr.config has its own lightweight RoddConfig — just verify it is present
    assert hasattr(cfg, "rodd")
    assert hasattr(cfg.rodd, "tts")
    assert hasattr(cfg.rodd, "stt")
