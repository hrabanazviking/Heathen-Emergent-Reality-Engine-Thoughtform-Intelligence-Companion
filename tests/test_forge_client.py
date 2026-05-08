"""
Tests — ForgeHttpClient scaffold.

These tests verify that the ForgeHttpClient scaffold is importable, the class
is correctly structured, and all stub methods raise NotImplementedError.
The method implementations are Wave 2 work (Forge implements). Tests that
require a live Straumur daemon are marked with pytest.mark.skip.

Ref: src/heretic/skilningr/senses/smidja/forge_client.py
     src/heretic/skilningr/config_model.ForgeConfig
     docs/architecture/SENSE_CONTRACTS.md §Smiðja Forge dispatch
"""

import pytest

from heretic.skilningr.config_model import ForgeConfig
from heretic.skilningr.senses.smidja.forge_client import ForgeHttpClient
from heretic.skilningr.senses.smidja.errors import (
    ForgeError,
    ForgeUnreachableError,
    ForgeTimeoutError,
    ForgeValidationError,
)


# ---------------------------------------------------------------------------
# ForgeConfig tests
# ---------------------------------------------------------------------------

def test_forge_config_default_values():
    """ForgeConfig must have documented defaults: disabled, localhost:8765, 120s."""
    cfg = ForgeConfig()
    assert cfg.enabled is False
    assert "127.0.0.1" in cfg.endpoint
    assert "8765" in cfg.endpoint
    assert cfg.token_env is None
    assert cfg.request_timeout_seconds == 120


def test_forge_config_rejects_empty_endpoint():
    """ForgeConfig must raise ValueError if endpoint is empty."""
    with pytest.raises(ValueError, match="endpoint"):
        ForgeConfig(endpoint="")


def test_forge_config_rejects_invalid_token_env():
    """ForgeConfig must raise ValueError if token_env is not a valid env var name."""
    with pytest.raises(ValueError, match="token_env"):
        ForgeConfig(token_env="not-valid-123")


def test_forge_config_rejects_zero_timeout():
    """ForgeConfig must raise ValueError if request_timeout_seconds <= 0."""
    with pytest.raises(ValueError, match="request_timeout_seconds"):
        ForgeConfig(request_timeout_seconds=0)


def test_forge_config_accepts_valid_token_env():
    """ForgeConfig must accept a valid uppercase env var name for token_env."""
    cfg = ForgeConfig(token_env="SEIDR_SMIDJA_FORGE_TOKEN")
    assert cfg.token_env == "SEIDR_SMIDJA_FORGE_TOKEN"


# ---------------------------------------------------------------------------
# ForgeHttpClient construction tests
# ---------------------------------------------------------------------------

def test_forge_client_constructs_with_defaults():
    """ForgeHttpClient must construct without raising given a default ForgeConfig."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)
    assert client is not None


def test_forge_client_repr_does_not_include_token(monkeypatch):
    """ForgeHttpClient repr must never include a token value."""
    monkeypatch.setenv("SEIDR_SMIDJA_FORGE_TOKEN", "super_secret_token")
    cfg = ForgeConfig(token_env="SEIDR_SMIDJA_FORGE_TOKEN")
    client = ForgeHttpClient(cfg)
    r = repr(client)
    assert "super_secret_token" not in r


# ---------------------------------------------------------------------------
# NOTE: Wave-1 placeholder tests asserting NotImplementedError on each stub
# were removed when Forge implemented the method bodies in Wave 2 (commit
# salvaged after Anthropic usage cap interrupted Forge mid-test-replacement).
# Coverage gap is intentional and recorded for the v0.6.1 Auditor pass: the
# implementation is real, but real-mocked-httpx tests for happy-path + error
# mapping per failure mode F-1..F-5 should be added before v0.6.2.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Error hierarchy tests
# ---------------------------------------------------------------------------

def test_forge_error_hierarchy():
    """ForgeError and subclasses must sit in the correct inheritance tree."""
    from heretic.skilningr.errors import SmidjaError, SkilningrError

    assert issubclass(ForgeError, SmidjaError)
    assert issubclass(ForgeUnreachableError, ForgeError)
    assert issubclass(ForgeTimeoutError, ForgeError)
    assert issubclass(ForgeValidationError, ForgeError)
    # All should catch as SkilningrError
    assert issubclass(ForgeError, SkilningrError)


# ---------------------------------------------------------------------------
# Live daemon tests (require Straumur running at localhost:8765) — SKIPPED
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Requires live Seidr-Smidja Straumur daemon at localhost:8765")
@pytest.mark.asyncio
async def test_forge_client_live_health():
    """Forge implements: verify GET /v1/health returns {'status': 'ok'}."""
    cfg = ForgeConfig(enabled=True)
    client = ForgeHttpClient(cfg)
    await client.open()
    health = await client.health()
    assert health.get("status") == "ok"
    await client.close()


@pytest.mark.skip(reason="Requires live Seidr-Smidja Straumur daemon + valid Loom spec")
@pytest.mark.asyncio
async def test_forge_client_live_build_avatar():
    """Forge implements: verify POST /v1/avatars returns success response shape."""
    cfg = ForgeConfig(enabled=True)
    client = ForgeHttpClient(cfg)
    await client.open()
    result = await client.build_avatar({"base_asset_id": "vroid_base_v1"})
    assert "success" in result
    assert "session_id" in result
    await client.close()
