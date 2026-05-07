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
import socket
from typing import Optional

from heretic.bifrost.config_model import BifrostConfig

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

        Logic:
            - If tailscale.prefer is True and Tailscale is active: return the
              configured endpoint as-is (it may already be a Tailscale address).
            - If tailscale.prefer is True and Tailscale is inactive:
              - If tailscale.fallback_to_direct is True: return configured endpoint.
              - Else: raise BifrostConnectionError explaining Tailscale is required.
            - If tailscale.prefer is False: return configured endpoint directly.

        Returns:
            The resolved endpoint URL string (never hardcoded; derived from config).

        Raises:
            NotImplementedError: Forge will implement the full routing logic.
        """
        raise NotImplementedError(
            "Forge will implement: TailscaleAwareness.resolve_endpoint — "
            "apply prefer/fallback logic from BifrostConfig.tailscale, "
            "raise BifrostConnectionError if Tailscale is required but absent, "
            "return the selected endpoint URL string."
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
    """Attempt to detect whether Tailscale is running on the local machine.

    This is a best-effort check. A positive result means Tailscale appears to be
    active. A negative result may be a false negative on unusual configurations.

    Strategy (Forge will implement the full version):
        1. Check if any local network interface has a 100.64.x.x address.
        2. If not detectable via interfaces, attempt to call ``tailscale status``
           as a subprocess with a short timeout.
        3. Return False on any exception — do not crash on detection failure.

    Returns:
        True if Tailscale appears active; False otherwise.
    """
    raise NotImplementedError(
        "Forge will implement: tailscale._detect_tailscale — "
        "enumerate network interfaces (psutil or socket) for 100.64.0.0/10 addresses, "
        "OR subprocess-call 'tailscale status' with timeout=2s, "
        "return True if detected, False on any failure."
    )
