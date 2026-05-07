"""
Tests for grunnr.config — HereticConfig and load_config().

Placeholder suite. Forge will implement real tests here covering:
    - load_config() with a minimal heretic.yaml in a tmp_path
    - load_config() with the $HERETIC_CONFIG env var override
    - load_config() with a malformed YAML → ConfigLoadError raised
    - load_config() with a missing file → ConfigLoadError raised
    - config_version mismatch → ConfigLoadError raised
    - All top-level True Name keys (grunnr/bifrost/rodd/sjon/vebond/skilningr) round-trip
    - ${ENV_VAR} references in api_key are expanded correctly
    - HereticConfig.default() returns a fully populated struct with correct defaults
    - BifrostConfig defaults match LAYER_INTERFACES.md reference block

Each test is currently marked skip so the suite stays green while the skeleton
awaits Forge implementation.
"""

from __future__ import annotations

import pytest

from heretic.grunnr.config import HereticConfig, ConfigLoadError


@pytest.mark.skip(reason="Forge will implement: load_config() not yet built")
def test_load_config_minimal_yaml(tmp_path: pytest.TempPathFactory) -> None:
    """load_config() returns a valid HereticConfig from a minimal heretic.yaml."""
    pass


@pytest.mark.skip(reason="Forge will implement: load_config() not yet built")
def test_load_config_missing_file_raises() -> None:
    """load_config() raises ConfigLoadError when heretic.yaml is absent."""
    pass


@pytest.mark.skip(reason="Forge will implement: load_config() not yet built")
def test_load_config_malformed_yaml_raises(tmp_path: pytest.TempPathFactory) -> None:
    """load_config() raises ConfigLoadError when heretic.yaml contains invalid YAML."""
    pass


@pytest.mark.skip(reason="Forge will implement: load_config() not yet built")
def test_config_version_mismatch_raises(tmp_path: pytest.TempPathFactory) -> None:
    """load_config() raises ConfigLoadError when config_version does not match."""
    pass


@pytest.mark.skip(reason="Forge will implement: load_config() not yet built")
def test_all_top_level_keys_round_trip(tmp_path: pytest.TempPathFactory) -> None:
    """heretic.yaml with all six True Name keys (grunnr/bifrost/rodd/sjon/vebond/skilningr)
    loads correctly and populates every sub-config."""
    pass


@pytest.mark.skip(reason="Forge will implement: load_config() not yet built")
def test_env_var_reference_expanded_in_api_key(
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """${HERETIC_AGENT_KEY} in bifrost.api_key is expanded from the environment."""
    pass


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
