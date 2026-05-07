"""
Tests for bifrost.tailscale — TailscaleAwareness and _detect_tailscale().

Covers: CGNAT range detection, endpoint resolution with various prefer/fallback
combinations, and the _detect_tailscale() detection logic.
"""

from __future__ import annotations

import ipaddress
from unittest import mock

import pytest

from heretic.bifrost.config_model import BifrostConfig, TailscaleOptions
from heretic.bifrost.errors import BifrostConnectionError
from heretic.bifrost.tailscale import TailscaleAwareness, _TAILSCALE_NETWORK, _detect_tailscale


# ---------------------------------------------------------------------------
# Tailscale CGNAT range constants
# ---------------------------------------------------------------------------

def test_tailscale_network_is_correct() -> None:
    """The Tailscale CGNAT range is 100.64.0.0/10."""
    assert str(_TAILSCALE_NETWORK) == "100.64.0.0/10"


def test_tailscale_address_in_range() -> None:
    """100.64.0.1 is in the Tailscale range."""
    assert ipaddress.ip_address("100.64.0.1") in _TAILSCALE_NETWORK


def test_tailscale_address_pi_hermes() -> None:
    """100.101.39.30 (Pi Hermes) is in the Tailscale CGNAT range."""
    assert ipaddress.ip_address("100.101.39.30") in _TAILSCALE_NETWORK


def test_non_tailscale_address_outside_range() -> None:
    """8.8.8.8 is NOT in the Tailscale range."""
    assert ipaddress.ip_address("8.8.8.8") not in _TAILSCALE_NETWORK


def test_localhost_outside_tailscale_range() -> None:
    """127.0.0.1 is NOT in the Tailscale range."""
    assert ipaddress.ip_address("127.0.0.1") not in _TAILSCALE_NETWORK


# ---------------------------------------------------------------------------
# TailscaleAwareness.is_tailscale_address
# ---------------------------------------------------------------------------

def test_is_tailscale_address_true_for_cgnat_ip() -> None:
    """is_tailscale_address returns True for a known Tailscale IP."""
    cfg = BifrostConfig(endpoint="http://100.101.39.30:8643/v1")
    ts = TailscaleAwareness(cfg)
    # Mock gethostbyname to return the IP directly (no DNS lookup)
    with mock.patch("socket.gethostbyname", return_value="100.101.39.30"):
        assert ts.is_tailscale_address("100.101.39.30") is True


def test_is_tailscale_address_false_for_public_ip() -> None:
    """is_tailscale_address returns False for a public IP."""
    cfg = BifrostConfig()
    ts = TailscaleAwareness(cfg)
    with mock.patch("socket.gethostbyname", return_value="8.8.8.8"):
        assert ts.is_tailscale_address("8.8.8.8") is False


def test_is_tailscale_address_false_on_dns_failure() -> None:
    """is_tailscale_address returns False (not raises) on DNS resolution failure."""
    import socket
    cfg = BifrostConfig()
    ts = TailscaleAwareness(cfg)
    with mock.patch("socket.gethostbyname", side_effect=socket.gaierror("no DNS")):
        assert ts.is_tailscale_address("nonexistent.host") is False


# ---------------------------------------------------------------------------
# TailscaleAwareness.resolve_endpoint
# ---------------------------------------------------------------------------

def _make_ts(
    endpoint: str = "http://100.101.39.30:8643/v1",
    prefer: bool = True,
    fallback: bool = True,
    active: bool = True,
) -> TailscaleAwareness:
    """Helper: build a TailscaleAwareness with mocked detection result."""
    cfg = BifrostConfig(
        endpoint=endpoint,
        tailscale=TailscaleOptions(prefer=prefer, fallback_to_direct=fallback),
    )
    ts = TailscaleAwareness(cfg)
    # Bypass actual detection — set cached result directly
    ts._tailscale_active = active
    return ts


def test_resolve_endpoint_prefer_active_returns_endpoint() -> None:
    """prefer=True + Tailscale active → return configured endpoint as-is."""
    ts = _make_ts(prefer=True, active=True)
    assert ts.resolve_endpoint() == "http://100.101.39.30:8643/v1"


def test_resolve_endpoint_prefer_inactive_fallback_true_returns_endpoint() -> None:
    """prefer=True + inactive + fallback_to_direct=True → return endpoint."""
    ts = _make_ts(prefer=True, active=False, fallback=True)
    assert ts.resolve_endpoint() == "http://100.101.39.30:8643/v1"


def test_resolve_endpoint_prefer_inactive_no_fallback_raises() -> None:
    """prefer=True + inactive + fallback_to_direct=False → BifrostConnectionError."""
    ts = _make_ts(prefer=True, active=False, fallback=False)
    with pytest.raises(BifrostConnectionError, match="Tailscale is not active"):
        ts.resolve_endpoint()


def test_resolve_endpoint_prefer_false_returns_direct() -> None:
    """prefer=False → return configured endpoint regardless of Tailscale state."""
    ts = _make_ts(prefer=False, active=False, fallback=False)
    assert ts.resolve_endpoint() == "http://100.101.39.30:8643/v1"


def test_resolve_endpoint_cloud_agent() -> None:
    """Cloud agents (prefer=False) get their URL returned unchanged."""
    ts = _make_ts(
        endpoint="https://api.openai.com/v1",
        prefer=False,
        active=False,
    )
    assert ts.resolve_endpoint() == "https://api.openai.com/v1"


# ---------------------------------------------------------------------------
# _detect_tailscale — mocked behaviour
# ---------------------------------------------------------------------------

def test_detect_tailscale_not_installed_returns_false() -> None:
    """If tailscale CLI is not on PATH, detection returns False."""
    with mock.patch("shutil.which", return_value=None):
        assert _detect_tailscale() is False


def test_detect_tailscale_cli_returns_zero_returns_true() -> None:
    """If tailscale status exits 0, Tailscale is active."""
    with mock.patch("shutil.which", return_value="/usr/bin/tailscale"), \
         mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0)
        assert _detect_tailscale() is True


def test_detect_tailscale_cli_returns_nonzero_falls_back() -> None:
    """If tailscale status exits non-zero, detect falls through to DNS probe."""
    import socket
    with mock.patch("shutil.which", return_value="/usr/bin/tailscale"), \
         mock.patch("subprocess.run") as mock_run, \
         mock.patch("socket.gethostbyname", side_effect=socket.gaierror):
        mock_run.return_value = mock.Mock(returncode=1)
        result = _detect_tailscale()
        assert result is False


def test_detect_tailscale_cli_timeout_falls_back_to_false() -> None:
    """If tailscale status times out, detection falls through and returns False."""
    import subprocess
    import socket
    with mock.patch("shutil.which", return_value="/usr/bin/tailscale"), \
         mock.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("tailscale", 2)), \
         mock.patch("socket.gethostbyname", side_effect=socket.gaierror):
        result = _detect_tailscale()
        assert result is False


# ---------------------------------------------------------------------------
# tailscale_active property (lazy evaluation / caching)
# ---------------------------------------------------------------------------

def test_tailscale_active_is_cached() -> None:
    """tailscale_active is evaluated lazily and cached on first access."""
    cfg = BifrostConfig()
    ts = TailscaleAwareness(cfg)
    call_count = [0]

    def fake_detect() -> bool:
        call_count[0] += 1
        return True

    with mock.patch("heretic.bifrost.tailscale._detect_tailscale", side_effect=fake_detect):
        _ = ts.tailscale_active
        _ = ts.tailscale_active
        _ = ts.tailscale_active

    # _detect_tailscale should only be called once (cache hit after first)
    assert call_count[0] == 1
