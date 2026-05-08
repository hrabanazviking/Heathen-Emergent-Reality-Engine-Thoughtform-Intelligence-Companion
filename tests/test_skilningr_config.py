"""
Placeholder tests — Skilningr config model.

These tests are marked skip until Forge Wave 2 implements the business logic.
The test file establishes the specification: each test body documents exactly
what invariant Forge must make true.

Ref: src/heretic/skilningr/config_model.py
     docs/architecture/LAYER_INTERFACES.md §L5 Skilningr
"""

import os
import warnings

import pytest

from heretic.skilningr.config_model import SkilningrConfig, SmidjaConfig


# ---------------------------------------------------------------------------
# SmidjaConfig construction
# ---------------------------------------------------------------------------

def test_smidja_config_default_values():
    """SmidjaConfig defaults: enabled=False, host=127.0.0.1, port=8848,
    token_env=BRUNHAND_TOKEN_HERETIC, require_https=True, host_name=default."""
    cfg = SmidjaConfig()
    assert cfg.enabled is False
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 8848
    assert cfg.token_env == "BRUNHAND_TOKEN_HERETIC"
    assert cfg.request_timeout_seconds == 30
    assert cfg.require_https is True
    assert cfg.host_name == "default"


def test_smidja_config_invalid_token_env_raises():
    """SmidjaConfig.__post_init__ raises ValueError if token_env is not a valid
    env var name (lowercase, spaces, or starting with a digit)."""
    with pytest.raises(ValueError, match="valid environment variable name"):
        SmidjaConfig(token_env="not-valid")


def test_smidja_config_invalid_token_env_lowercase_raises():
    """Lowercase names are not valid POSIX env var names per [A-Z_][A-Z0-9_]*."""
    with pytest.raises(ValueError, match="valid environment variable name"):
        SmidjaConfig(token_env="brunhand_token")


def test_smidja_config_port_out_of_range_raises():
    """SmidjaConfig raises ValueError for port=0 (below valid range 1-65535)."""
    with pytest.raises(ValueError, match="valid range"):
        SmidjaConfig(port=0)


def test_smidja_config_port_max_boundary():
    """Port 65535 is within range; must not raise."""
    cfg = SmidjaConfig(port=65535)
    assert cfg.port == 65535


def test_smidja_config_timeout_zero_raises():
    """request_timeout_seconds=0 must raise ValueError."""
    with pytest.raises(ValueError, match="must be > 0"):
        SmidjaConfig(request_timeout_seconds=0)


def test_smidja_config_enabled_missing_env_warns(monkeypatch):
    """If enabled=True and the token env var is unset, a UserWarning is emitted
    at construction time but NO exception is raised (allows CI without tokens)."""
    monkeypatch.delenv("BRUNHAND_TOKEN_HERETIC", raising=False)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        cfg = SmidjaConfig(enabled=True)  # should warn, not raise
    assert cfg.enabled is True
    assert any("BRUNHAND_TOKEN_HERETIC" in str(warning.message) for warning in w)


def test_smidja_config_enabled_with_token_no_warn(monkeypatch):
    """If enabled=True and the token env var IS set, no warning is emitted."""
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "secret-token-value")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        SmidjaConfig(enabled=True)
    smidja_warns = [x for x in w if "BRUNHAND_TOKEN" in str(x.message)]
    assert len(smidja_warns) == 0


# ---------------------------------------------------------------------------
# SkilningrConfig construction
# ---------------------------------------------------------------------------

def test_skilningr_config_has_smidja_field():
    """SkilningrConfig must have a smidja field of type SmidjaConfig."""
    cfg = SkilningrConfig()
    assert isinstance(cfg.smidja, SmidjaConfig)


def test_skilningr_config_smidja_disabled_by_default():
    """The smidja sense must default to disabled."""
    cfg = SkilningrConfig()
    assert cfg.smidja.enabled is False


def test_skilningr_config_other_senses_have_enabled_key():
    """Future sense stubs (filesystem, terminal, etc.) must have an 'enabled' key."""
    cfg = SkilningrConfig()
    for sense_id in ("filesystem", "terminal", "browser", "photopea", "vrchat", "agentmail", "library"):
        stub = getattr(cfg, sense_id, None)
        assert stub is not None, f"SkilningrConfig missing sense: {sense_id}"
        if isinstance(stub, dict):
            assert "enabled" in stub
        else:
            assert hasattr(stub, "enabled")
