"""
Bifröst Tailscale awareness — detect and prefer Tailscale routing.

Tailscale is the trusted network fabric of this ecosystem. The Pi running Hermes
is at ``100.101.39.30:8643/v1`` on the Tailscale mesh. HERETIC prefers Tailscale
routing when available and falls back to the raw endpoint URL when it is not.

TailscaleAwareness does not manage the Tailscale daemon — that is external software
the user installs. It only:
    1. Detects whether Tailscale is active on this machine.
    2. Determines whether the configured agent endpoint is a Tailscale address.
    3. Optionally resolves the preferred endpoint URL for a given config.

Ref:
    docs/architecture/LAYER_INTERFACES.md §L1 Bifröst — Config keys (tailscale: block)
    docs/architecture/ARCHITECTURE.md §8 Technology Stack — Tailscale
"""

from __future__ import annotations

import ipaddress
import shutil
import socket
import subprocess
from typing import Optional

from heretic.bifrost.config_model import BifrostConfig
from heretic.bifrost.errors import BifrostConnectionError

# Tailscale address space: 100.64.0.0/10
# This is the CGNAT range Tailscale uses for its mesh addresses.
_TAILSCALE_NETWORK = ipaddress.ip_network("100.64.0.0/10")


class TailscaleAwareness:
    """Detects Tailscale presence and resolves preferred agent endpoints.

    Instantiated once by BifrostClient during Kynding. The results are cached
    for the duration of the ceremony — Tailscale state is not expected to change
    while a ceremony is active (RECOVERING handles the case where it does drop).
    """

    def __init__(self, config: BifrostConfig) -> None:
        self._config = config
        self._tailscale_active: Optional[bool] = None  # None = not yet checked

    @property
    def tailscale_active(self) -> bool:
        """Return True if Tailscale appears to be active on this machine.

        Lazily evaluated on first access. Cached thereafter.

        Forge will implement the actual detection: check for the Tailscale socket,
        attempt to enumerate network interfaces for 100.64.0.0/10 addresses, or
        call ``tailscale status`` as a subprocess.
        """
        if self._tailscale_active is None:
            self._tailscale_active = _detect_tailscale()
        return self._tailscale_active

    def resolve_endpoint(self) -> str:
        """Return the best endpoint URL given current Tailscale state and config.

        Logic per AGENT_AGNOSTIC_PROTOCOL.md §4.1:
            - prefer=True  + Tailscale active  → use configured endpoint (Tailscale route)
            - prefer=True  + Tailscale inactive + fallback_to_direct=True → use endpoint directly
            - prefer=True  + Tailscale inactive + fallback_to_direct=False → raise
            - prefer=False → return configured endpoint directly (bypass Tailscale logic)

        Returns:
            The resolved endpoint URL string — always derived from config, never hardcoded.

        Raises:
            BifrostConnectionError: if Tailscale is required but not available.
        """
        endpoint = self._config.endpoint
        prefer = self._config.tailscale.prefer
        fallback = self._config.tailscale.fallback_to_direct

        if not prefer:
            # User explicitly opted out of Tailscale routing — use endpoint directly
            return endpoint

        if self.tailscale_active:
            return endpoint

        # Tailscale is not active
        if fallback:
            return endpoint

        raise BifrostConnectionError(
            f"Tailscale is not active and fallback_to_direct is disabled. "
            f"Cannot reach agent at {endpoint!r}. "
            f"Start Tailscale or set bifrost.tailscale.fallback_to_direct: true."
        )

    def is_tailscale_address(self, host: str) -> bool:
        """Return True if ``host`` resolves to a Tailscale (100.64.0.0/10) address.

        Args:
            host: A hostname or IP string from the endpoint URL.

        Returns:
            True if the IP is in the 100.64.0.0/10 range; False otherwise.
            Returns False (not raises) if host cannot be resolved.
        """
        try:
            ip_str = socket.gethostbyname(host)
            ip = ipaddress.ip_address(ip_str)
            return ip in _TAILSCALE_NETWORK
        except (socket.gaierror, ValueError):
            return False


def _detect_tailscale() -> bool:
    """Detect whether Tailscale is running on the local machine.

    Best-effort check — false negatives are possible on unusual configurations,
    but any exception returns False rather than crashing.

    Strategy:
        1. Check if the ``tailscale`` CLI binary is on PATH (shutil.which).
           If not found, Tailscale is almost certainly not installed → return False.
        2. If found, call ``tailscale status --json`` with a 2-second timeout
           to see if the daemon is actually running.
        3. Fall back to checking local sockets for a 100.64.0.0/10 address via
           socket.gethostbyname("100.100.100.100") as a Tailscale magic DNS probe.

    Returns:
        True if Tailscale appears active; False on any detection failure.
    """
    # Step 1: Is the CLI even installed?
    if shutil.which("tailscale") is None:
        return False

    # Step 2: Call `tailscale status` — non-zero exit means daemon is not running
    try:
        result = subprocess.run(
            ["tailscale", "status"],
            capture_output=True,
            timeout=2,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        # TimeoutExpired: daemon is hung or not responding
        # OSError/FileNotFoundError: CLI found by shutil.which but exec failed
        pass

    # Step 3: Probe Tailscale magic DNS as a last resort
    # 100.100.100.100 is Tailscale's own DNS resolver; resolving it means TS is up
    try:
        socket.setdefaulttimeout(1)
        socket.gethostbyname("100.100.100.100")
        return True
    except (socket.gaierror, OSError):
        return False
    finally:
        socket.setdefaulttimeout(None)
