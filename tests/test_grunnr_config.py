"""
Tests for grunnr.config — HereticConfig and load_config().

Covers: loading, missing files, malformed YAML, version mismatch,
recursive merge with defaults, env var expansion, and round-trip for all
six top-level True Name keys.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from heretic.grunnr.config import (
    HereticConfig,
    ConfigLoadError,
    SUPPORTED_CONFIG_VERSION,
    load_config,
)


# ---------------------------------------------------------------------------
# HereticConfig.default() structural tests
# ---------------------------------------------------------------------------

def test_default_config_is_valid() -> None:
    """HereticConfig.default() returns without raising and has correct top-level structure."""
    cfg = HereticConfig.default()
    assert cfg.grunnr is not None
    assert cfg.bifrost is not None
    assert cfg.rodd is not None
    assert cfg.sjon is not None
    assert cfg.vebond is not None
    assert cfg.skilningr is not None


def test_bifrost_default_max_tokens() -> None:
    """BifrostConfig defaults to max_tokens=127000 per RULES.AI.md."""
    cfg = HereticConfig.default()
    assert cfg.bifrost.max_tokens == 127000


def test_grunnr_default_log_level() -> None:
    """GrunnrConfig defaults to log_level='info'."""
    cfg = HereticConfig.default()
    assert cfg.grunnr.log_level == "info"


def test_grunnr_default_config_version() -> None:
    """GrunnrConfig.config_version defaults to the supported version."""
    cfg = HereticConfig.default()
    assert cfg.grunnr.config_version == SUPPORTED_CONFIG_VERSION


def test_bifrost_default_stream_true() -> None:
    """BifrostConfig defaults to stream=True — SSE streaming is preferred."""
    cfg = HereticConfig.default()
    assert cfg.bifrost.stream is True


def test_tailscale_default_prefer_true() -> None:
    """Tailscale defaults to prefer=True."""
    cfg = HereticConfig.default()
    assert cfg.bifrost.tailscale.prefer is True


def test_sjon_default_save_frames_false() -> None:
    """Screen save_frames defaults to False — opt-in only, never auto-saves."""
    cfg = HereticConfig.default()
    assert cfg.sjon.screen.save_frames is False


# ---------------------------------------------------------------------------
# load_config() — file not found
# ---------------------------------------------------------------------------

def test_load_config_missing_file_raises(tmp_path: Path) -> None:
    """load_config() raises ConfigLoadError when the file does not exist."""
    missing = tmp_path / "does_not_exist.yaml"
    with pytest.raises(ConfigLoadError, match="Cannot find"):
        load_config(str(missing))


# ---------------------------------------------------------------------------
# load_config() — malformed YAML
# ---------------------------------------------------------------------------

def test_load_config_malformed_yaml_raises(tmp_path: Path) -> None:
    """load_config() raises ConfigLoadError when heretic.yaml contains invalid YAML."""
    bad = tmp_path / "heretic.yaml"
    bad.write_text(": this: is: broken yaml:\n  bad\n  - [", encoding="utf-8")
    with pytest.raises(ConfigLoadError):
        load_config(str(bad))


# ---------------------------------------------------------------------------
# load_config() — empty file
# ---------------------------------------------------------------------------

def test_load_config_empty_file_returns_defaults(tmp_path: Path) -> None:
    """An empty heretic.yaml (null document) returns a default config."""
    empty = tmp_path / "heretic.yaml"
    empty.write_text("", encoding="utf-8")
    cfg = load_config(str(empty))
    assert cfg.grunnr.log_level == "info"
    assert cfg.bifrost.max_tokens == 127000


# ---------------------------------------------------------------------------
# load_config() — minimal valid YAML
# ---------------------------------------------------------------------------

def test_load_config_minimal_yaml(tmp_path: Path) -> None:
    """load_config() returns a valid HereticConfig from a minimal heretic.yaml."""
    config_file = tmp_path / "heretic.yaml"
    config_file.write_text(
        "grunnr:\n  log_level: debug\n  config_version: \"1\"\n",
        encoding="utf-8",
    )
    cfg = load_config(str(config_file))
    assert cfg.grunnr.log_level == "debug"
    # Unspecified fields retain defaults
    assert cfg.bifrost.max_tokens == 127000


# ---------------------------------------------------------------------------
# load_config() — version mismatch
# ---------------------------------------------------------------------------

def test_config_version_mismatch_raises(tmp_path: Path) -> None:
    """load_config() raises ConfigLoadError when config_version does not match."""
    config_file = tmp_path / "heretic.yaml"
    config_file.write_text(
        "grunnr:\n  config_version: \"999\"\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigLoadError, match="config_version"):
        load_config(str(config_file))


# ---------------------------------------------------------------------------
# load_config() — all six True Name keys round-trip
# ---------------------------------------------------------------------------

def test_all_top_level_keys_round_trip(tmp_path: Path) -> None:
    """heretic.yaml with all six True Name keys populates every sub-config."""
    config_file = tmp_path / "heretic.yaml"
    config_file.write_text(
        """
grunnr:
  log_level: warn
  config_version: "1"
bifrost:
  model: my-model
  max_tokens: 99999
rodd:
  stt:
    enabled: false
sjon:
  screen:
    width: 640
vebond:
  theme: dark_norse
skilningr:
  filesystem:
    enabled: true
""",
        encoding="utf-8",
    )
    cfg = load_config(str(config_file))
    assert cfg.grunnr.log_level == "warn"
    assert cfg.bifrost.model == "my-model"
    assert cfg.bifrost.max_tokens == 99999
    assert cfg.rodd.stt.enabled is False
    assert cfg.sjon.screen.width == 640
    assert cfg.vebond.theme == "dark_norse"
    assert cfg.skilningr.filesystem.enabled is True


# ---------------------------------------------------------------------------
# load_config() — nested merge preserves defaults for unspecified subkeys
# ---------------------------------------------------------------------------

def test_partial_bifrost_block_preserves_defaults(tmp_path: Path) -> None:
    """Specifying only some bifrost keys leaves others at their defaults."""
    config_file = tmp_path / "heretic.yaml"
    config_file.write_text(
        "grunnr:\n  config_version: \"1\"\nbifrost:\n  model: test-model\n",
        encoding="utf-8",
    )
    cfg = load_config(str(config_file))
    assert cfg.bifrost.model == "test-model"
    assert cfg.bifrost.stream is True          # default preserved
    assert cfg.bifrost.max_tokens == 127000    # default preserved


# ---------------------------------------------------------------------------
# load_config() — env var expansion in api_key
# ---------------------------------------------------------------------------

def test_env_var_reference_expanded_in_api_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """${HERETIC_AGENT_KEY} in bifrost.api_key is expanded from the environment."""
    monkeypatch.setenv("HERETIC_AGENT_KEY", "super-secret-token")
    config_file = tmp_path / "heretic.yaml"
    config_file.write_text(
        'grunnr:\n  config_version: "1"\nbifrost:\n  api_key: "${HERETIC_AGENT_KEY}"\n',
        encoding="utf-8",
    )
    cfg = load_config(str(config_file))
    assert cfg.bifrost.api_key == "super-secret-token"


def test_env_var_unset_warns_and_uses_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing env var substitutes empty string and logs a warning (does not raise)."""
    monkeypatch.delenv("HERETIC_AGENT_KEY", raising=False)
    config_file = tmp_path / "heretic.yaml"
    config_file.write_text(
        'grunnr:\n  config_version: "1"\nbifrost:\n  api_key: "${HERETIC_AGENT_KEY}"\n',
        encoding="utf-8",
    )
    # Should not raise — warn and substitute empty string
    cfg = load_config(str(config_file))
    assert cfg.bifrost.api_key == ""


# ---------------------------------------------------------------------------
# load_config() — HERETIC_CONFIG env var override
# ---------------------------------------------------------------------------

def test_heretic_config_env_var_overrides_search(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When $HERETIC_CONFIG is set, load_config() uses that file."""
    config_file = tmp_path / "custom_heretic.yaml"
    config_file.write_text(
        "grunnr:\n  config_version: \"1\"\n  log_level: error\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HERETIC_CONFIG", str(config_file))
    cfg = load_config()  # no explicit path
    assert cfg.grunnr.log_level == "error"


# ---------------------------------------------------------------------------
# N-3 — BifrostConfig field parity guard
# ---------------------------------------------------------------------------

def test_bifrost_config_field_parity() -> None:
    """Both BifrostConfig dataclasses must have identical field names until they are merged.

    Two BifrostConfig dataclasses exist — one in grunnr.config (used by the config
    loader) and one in bifrost.config_model (used by the client). A manual bridge in
    cli.py copies all fields from the former to the latter at ceremony start.

    If a field is added to one class and not the other, the bridge silently passes
    the default value rather than the user's configured value — a runtime defect with
    no error signal. This test is the tripwire.

    The 'tailscale' field is intentionally typed differently (TailscaleConfig vs
    TailscaleOptions — two local wrappers with identical structure). The test guards
    field *names* only for the top-level BifrostConfig, then verifies the tailscale
    wrapper fields separately to catch sub-field drift.

    Ref: docs/audit/AUDIT_v0.1_FIRST_COMMUNION.md N-3.
    """
    from dataclasses import fields
    from heretic.grunnr.config import (
        BifrostConfig as GrunnrBifrostConfig,
        TailscaleConfig,
    )
    from heretic.bifrost.config_model import (
        BifrostConfig as BifrostBifrostConfig,
        TailscaleOptions,
    )

    grunnr_field_names = {f.name for f in fields(GrunnrBifrostConfig)}
    bifrost_field_names = {f.name for f in fields(BifrostBifrostConfig)}

    assert grunnr_field_names == bifrost_field_names, (
        "BifrostConfig field names drifted between grunnr.config and "
        "bifrost.config_model. The cli.py bridge silently drops any field that "
        "exists in one class but not the other.\n"
        f"Only in grunnr: {sorted(grunnr_field_names - bifrost_field_names)}\n"
        f"Only in bifrost: {sorted(bifrost_field_names - grunnr_field_names)}\n"
        "Add the missing field to both classes before committing."
    )

    # Verify that the non-tailscale fields also have identical type annotations.
    # The 'tailscale' field intentionally differs in its local wrapper class name
    # (TailscaleConfig vs TailscaleOptions) — both wrappers are structurally
    # identical. We guard that separately below.
    grunnr_types = {
        f.name: f.type
        for f in fields(GrunnrBifrostConfig)
        if f.name != "tailscale"
    }
    bifrost_types = {
        f.name: f.type
        for f in fields(BifrostBifrostConfig)
        if f.name != "tailscale"
    }
    assert grunnr_types == bifrost_types, (
        "BifrostConfig field types drifted (excluding the intentionally-named "
        "'tailscale' field).\n"
        f"Grunnr types: {sorted(grunnr_types.items())}\n"
        f"Bifrost types: {sorted(bifrost_types.items())}\n"
    )

    # Guard the tailscale wrapper sub-fields — both wrappers must be structurally
    # identical even though they carry different local class names.
    grunnr_ts_names = {f.name for f in fields(TailscaleConfig)}
    bifrost_ts_names = {f.name for f in fields(TailscaleOptions)}
    assert grunnr_ts_names == bifrost_ts_names, (
        "Tailscale wrapper fields drifted between TailscaleConfig (grunnr.config) "
        "and TailscaleOptions (bifrost.config_model).\n"
        f"Only in TailscaleConfig: {sorted(grunnr_ts_names - bifrost_ts_names)}\n"
        f"Only in TailscaleOptions: {sorted(bifrost_ts_names - grunnr_ts_names)}\n"
    )

    grunnr_ts_types = {f.name: f.type for f in fields(TailscaleConfig)}
    bifrost_ts_types = {f.name: f.type for f in fields(TailscaleOptions)}
    assert grunnr_ts_types == bifrost_ts_types, (
        "Tailscale wrapper field types drifted.\n"
        f"TailscaleConfig: {sorted(grunnr_ts_types.items())}\n"
        f"TailscaleOptions: {sorted(bifrost_ts_types.items())}\n"
    )


# ---------------------------------------------------------------------------
# S-1 — RoddTtsConfig consolidation guard
# ---------------------------------------------------------------------------

def test_rodd_tts_config_is_canonical() -> None:
    """grunnr.config re-exports the canonical RoddTtsConfig from rodd.config_model.

    After the S-1 consolidation (AUDIT_v0.2_FIRST_VOICE.md S-1), grunnr.config
    no longer defines its own RoddTtsConfig stub.  It imports and re-exports the
    canonical class from heretic.rodd.config_model.  This test is the tripwire:
    if the import is ever accidentally replaced with a local stub again, the
    identity check fails immediately.
    """
    from heretic.grunnr.config import RoddTtsConfig as GrunnrRoddTtsConfig
    from heretic.rodd.config_model import RoddTtsConfig as RoddRoddTtsConfig

    assert GrunnrRoddTtsConfig is RoddRoddTtsConfig, (
        "grunnr.config.RoddTtsConfig is NOT the same object as "
        "rodd.config_model.RoddTtsConfig. The S-1 consolidation has drifted — "
        "grunnr.config must re-export the canonical class, not define its own stub."
    )


def test_rodd_tts_config_yaml_round_trip(tmp_path: Path) -> None:
    """Operator-set synthesis fields in heretic.yaml reach HereticConfig.rodd.tts.

    Reproduces the S-1 bug: the old 6-field grunnr stub silently dropped
    temperature, model, chunk_min_chars and other synthesis fields.  After
    consolidation, every field in heretic.yaml should flow through to the
    typed config without being discarded.

    Ref: docs/audit/AUDIT_v0.2_FIRST_VOICE.md S-1.
    """
    config_file = tmp_path / "heretic.yaml"
    config_file.write_text(
        """
grunnr:
  config_version: "1"
rodd:
  tts:
    temperature: 1.5
    model: tts
    chunk_min_chars: 120
    exaggeration: 1.2
    repetition_penalty: 1.8
""",
        encoding="utf-8",
    )
    cfg = load_config(str(config_file))

    assert cfg.rodd.tts.temperature == 1.5, (
        f"temperature not loaded from heretic.yaml — got {cfg.rodd.tts.temperature}"
    )
    assert cfg.rodd.tts.model == "tts", (
        f"model not loaded from heretic.yaml — got {cfg.rodd.tts.model}"
    )
    assert cfg.rodd.tts.chunk_min_chars == 120, (
        f"chunk_min_chars not loaded from heretic.yaml — got {cfg.rodd.tts.chunk_min_chars}"
    )
    assert cfg.rodd.tts.exaggeration == 1.2, (
        f"exaggeration not loaded from heretic.yaml — got {cfg.rodd.tts.exaggeration}"
    )
    assert cfg.rodd.tts.repetition_penalty == 1.8, (
        f"repetition_penalty not loaded from heretic.yaml — got {cfg.rodd.tts.repetition_penalty}"
    )
