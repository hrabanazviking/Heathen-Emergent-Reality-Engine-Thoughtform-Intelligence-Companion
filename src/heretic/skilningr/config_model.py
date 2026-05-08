"""
Skilningr config model — SkilningrConfig, SmidjaConfig, and ForgeConfig.

This module owns the authoritative Python type definitions for the L5 Skilningr
sense hub configuration and all currently-defined sense sub-configs. The pattern
follows Approach B (mirror of heretic.rodd.config_model and heretic.sjon.config_model):
the canonical definitions live here; heretic.grunnr.config imports them.

Config keys documented in:
    docs/architecture/LAYER_INTERFACES.md §L5 Skilningr

Auth invariant (DO NOT BREAK):
    SmidjaConfig stores the ENV VAR NAME (token_env), never the token value itself.
    The token is resolved from the environment once at BrunhandHttpClient init time.
    It must never appear in config files, log lines, or config repr strings.

ForgeConfig (v0.6.1):
    Straumur (the Seidr-Smidja REST bridge for headless Blender builds) does NOT
    require a bearer token on localhost. token_env is optional (default None).
    If set, ForgeHttpClient will pass it as Authorization: Bearer. If None, no
    auth header is sent — matching Straumur's H-005 localhost-only default.

Ref: TASK_HERETIC_v0.6_HANDS_AT_FORGE.md §3 (architectural decisions)
     TASK_HERETIC_v0.6.1_FORGE_DISPATCH.md §3 (Forge architectural decisions)
     src/seidr_smidja/brunhand/daemon/INTERFACE.md (Brúarhönd daemon API contract)
     src/seidr_smidja/bridges/straumur/api.py (Straumur REST bridge — authoritative)
"""

from __future__ import annotations

import os
import re
import warnings
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_ENV_VAR_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")
"""Valid POSIX / Windows env var name: starts with letter or underscore,
contains only uppercase letters, digits, and underscores."""


def _is_valid_env_var_name(name: str) -> bool:
    """Return True if name is a syntactically valid environment variable name."""
    return bool(_ENV_VAR_PATTERN.match(name))


# ---------------------------------------------------------------------------
# L5.5 Smiðja — Forge (Straumur) config  [v0.6.1]
# ---------------------------------------------------------------------------

@dataclass
class ForgeConfig:
    """Configuration for the Forge half of the Smiðja sense.

    The Forge half wraps Seidr-Smidja's Straumur REST bridge — the headless
    Blender pipeline for programmatic VRM avatar building. It is architecturally
    independent from Brúarhönd: both halves live under the Smiðja sense but
    open, close, and fail independently.

    Straumur defaults to localhost-only binding (127.0.0.1:8765) with NO
    bearer-token authentication. token_env is therefore optional (default None).
    If set, ForgeHttpClient sends Authorization: Bearer <token>. If None, no
    auth header is sent — matching Straumur's H-005 security model.

    KEY INVARIANT: request_timeout_seconds defaults to 120 (not 30) because
    Blender render passes can take minutes. Operators driving complex builds
    should increase this further.

    NEVER set token_env to the raw token string. If auth is needed (non-localhost
    Straumur), set token_env to the ENV VAR NAME; ForgeHttpClient resolves the
    value from os.environ at init time.

    Heretic.yaml key: skilningr.smidja.forge.*
    Ref: src/heretic/skilningr/senses/smidja/INTERFACE.md §Forge dispatch
         src/seidr_smidja/bridges/straumur/api.py (endpoint contracts — authoritative)
    """

    enabled: bool = False
    """Opt-in. Must be explicitly set to true to expose Forge tools to the agent.
    Default false: the agent gains no headless Blender capability until the
    operator enables it AND a Seidr-Smidja Straumur daemon is running.
    Brúarhönd half (SmidjaConfig.enabled) and Forge half (ForgeConfig.enabled)
    are independent — one may be enabled without the other."""

    endpoint: str = "http://127.0.0.1:8765"
    """Full base URL of the Seidr-Smidja Straumur REST bridge.
    Default: http://127.0.0.1:8765 (localhost, confirmed in api.py __main__).
    For cross-machine use, set to the Tailscale IP/MagicDNS name.
    Never an absolute file path. httpx connects to this URL normally.
    IMPORTANT: Straumur H-005 requires straumur.allow_remote_bind: true in
    seidr-smidja config before it will accept non-localhost connections."""

    token_env: str | None = None
    """Optional name of the environment variable holding the bearer token.
    Straumur does NOT require auth on localhost — set this only when running
    Straumur on a remote host that has been configured with token auth.
    When None (default), no Authorization header is sent.
    When set, must be a valid env var name (uppercase, underscores, digits).
    The token value MUST NEVER appear in heretic.yaml — only the var name."""

    request_timeout_seconds: int = 120
    """Per-request HTTP timeout in seconds. Default 120 — Blender renders are
    slow; a full avatar build pass can take 60–120 seconds. Operators driving
    high-poly models or complex render views should increase this.
    Must be > 0."""

    def __post_init__(self) -> None:
        """Validate config fields at construction time.

        Raises:
            ValueError: if token_env is set but not a valid env var name,
                        endpoint is empty, or request_timeout_seconds <= 0.

        Warns (but does not raise) if enabled=True and token_env is set but
        the named env var is unset, so that config construction succeeds in
        CI/test environments where tokens are not present.
        """
        if not self.endpoint or not self.endpoint.strip():
            raise ValueError(
                "ForgeConfig.endpoint must be a non-empty URL string. "
                f"Got {self.endpoint!r}."
            )

        if self.token_env is not None:
            if not _is_valid_env_var_name(self.token_env):
                raise ValueError(
                    f"ForgeConfig.token_env {self.token_env!r} is not a valid "
                    f"environment variable name. Must match [A-Z_][A-Z0-9_]* "
                    f"(uppercase only). Example: SEIDR_SMIDJA_FORGE_TOKEN"
                )
            # Warn (not error) if enabled but the env var is absent
            if self.enabled and not os.environ.get(self.token_env):
                warnings.warn(
                    f"ForgeConfig: enabled=True and token_env={self.token_env!r} is set "
                    f"but the environment variable is not present. "
                    f"ForgeHttpClient will send requests without an auth header. "
                    f"If Straumur requires auth, set {self.token_env}=<your_token> "
                    f"before starting HERETIC.",
                    stacklevel=2,
                )

        if self.request_timeout_seconds <= 0:
            raise ValueError(
                f"ForgeConfig.request_timeout_seconds must be > 0, "
                f"got {self.request_timeout_seconds!r}."
            )


# ---------------------------------------------------------------------------
# L5.5 Smiðja — Brúarhönd config
# ---------------------------------------------------------------------------

@dataclass
class SmidjaConfig:
    """Configuration for the Smiðja sense — HERETIC's Brúarhönd HTTP client.

    Smiðja is the sense that wraps Seidr-Smidja's Brúarhönd daemon (Horfunarþjónn).
    It is the body's first hand: it lets the agent execute real GUI primitives
    (screenshot, click, type, hotkey, VRoid Studio open/export) on a machine
    reachable via Tailscale or localhost.

    Key invariant: `token_env` holds an env var NAME, never the token value.
    The BrunhandHttpClient resolves the actual token at init time via os.environ.
    This field must NEVER be set to a raw token string in heretic.yaml.

    Full config reference: docs/architecture/LAYER_INTERFACES.md §L5 Skilningr
    Endpoint contracts: src/seidr_smidja/brunhand/daemon/INTERFACE.md

    Heretic.yaml key: skilningr.smidja.*
    """

    enabled: bool = False
    """Opt-in. Must be explicitly set to true to expose Brúarhönd tools to the agent.
    Default false is a safety default: the agent gains no remote-control capability
    unless the operator consciously enables it and sets up the bearer token."""

    host: str = "127.0.0.1"
    """IP address, hostname, or Tailscale MagicDNS name of the Brúarhönd daemon host.
    For same-machine use: 127.0.0.1 (default).
    For cross-machine via Tailscale: the host's Tailscale IP or MagicDNS name
    (e.g. vroid-workstation.tailnet.ts.net or 100.x.y.z).
    Never an absolute file path. httpx connects to this address normally."""

    port: int = 8848
    """TCP port the Brúarhönd daemon is listening on (default 8848, per Seidr-Smidja).
    Must be in valid port range 1–65535."""

    token_env: str = "BRUNHAND_TOKEN_HERETIC"
    """Name of the environment variable holding the bearer token.
    The token itself must NEVER appear in heretic.yaml or in any log line.
    BrunhandHttpClient resolves os.environ[token_env] at init time.
    Example: set BRUNHAND_TOKEN_HERETIC=<your_token> before starting HERETIC."""

    request_timeout_seconds: int = 30
    """Per-request HTTP timeout in seconds. Applies to all Brúarhönd calls.
    VRoid export and open may take longer than the default; set to 120 when
    driving complex VRoid Studio flows. Must be > 0."""

    require_https: bool = True
    """If True (production default), all HTTP connections to the daemon must use
    HTTPS. Set to False for local same-machine development where the daemon is
    bound to 127.0.0.1 without a TLS certificate.
    NEVER set False for cross-machine Tailscale connections in production."""

    host_name: str = "default"
    """A logical label for this Brúarhönd host, used in log lines and audit events.
    Does not affect routing or auth. Choose a human-readable name that matches
    the machine running VRoid Studio (e.g. vroid-workstation)."""

    forge: "ForgeConfig" = field(default_factory=lambda: ForgeConfig())
    """v0.6.1 — Forge (Straumur) sub-config: headless Blender pipeline half of Smiðja.
    The Forge half is independent of the Brúarhönd half above. Both may be
    enabled or disabled independently. Set forge.enabled: true in heretic.yaml
    to expose smidja.forge_* tools to the agent.
    Ref: src/heretic/skilningr/senses/smidja/INTERFACE.md §Forge dispatch"""

    def __post_init__(self) -> None:
        """Validate config fields at construction time.

        Raises:
            ValueError: if token_env is not a valid env var name, port is out of
                range, or request_timeout_seconds is <= 0.

        Warns (but does not raise) if enabled=True and the named env var is unset,
        so that config construction succeeds even in CI/test environments where
        tokens are not set, while still alerting operators to the missing token.
        """
        if not _is_valid_env_var_name(self.token_env):
            raise ValueError(
                f"SmidjaConfig.token_env {self.token_env!r} is not a valid "
                f"environment variable name. Must match [A-Z_][A-Z0-9_]*. "
                f"Example: BRUNHAND_TOKEN_HERETIC"
            )

        if not (1 <= self.port <= 65535):
            raise ValueError(
                f"SmidjaConfig.port {self.port!r} is out of valid range 1–65535."
            )

        if self.request_timeout_seconds <= 0:
            raise ValueError(
                f"SmidjaConfig.request_timeout_seconds must be > 0, "
                f"got {self.request_timeout_seconds!r}."
            )

        # Warn (not error) if enabled but env var not set: allows CI to construct
        # configs without the actual token while alerting operators.
        if self.enabled and not os.environ.get(self.token_env):
            warnings.warn(
                f"SmidjaConfig: enabled=True but environment variable {self.token_env!r} "
                f"is not set. The BrunhandHttpClient will raise AuthError at init time. "
                f"Set {self.token_env}=<your_token> before starting HERETIC.",
                stacklevel=2,
            )


# ---------------------------------------------------------------------------
# L5 Skilningr root config
# ---------------------------------------------------------------------------

@dataclass
class SkilningrConfig:
    """L5 Skilningr — MCP Sense Hub settings.

    Each sense uses its code-facing identifier (not its True Name) as the field
    name, per NAMING.md §5: 'The code-facing identifier is always the True Name
    transliterated without diacritics, lowercased.'

    v0.6 adds the concrete SmidjaConfig for the Smiðja sense (L5.5). Prior
    fields that were SkilningrSenseConfig stubs remain stubs for their respective
    senses — Forge expands them in future milestones.

    The canonical sense-id-to-True-Name mapping:
        filesystem (Minni)   — L5.1
        terminal   (Skepja)  — L5.2
        browser    (Leið)    — L5.3
        photopea   (Hönd)    — L5.4
        smidja     (Smiðja)  — L5.5  ← first concrete sense (v0.6)
        vrchat     (Líkami)  — L5.6
        agentmail  (Boð)     — L5.7
        library    (Mímisbrunnr) — L5.9

    Ref: docs/architecture/SENSE_CONTRACTS.md §2 (sense_id mapping table)
    """

    smidja: SmidjaConfig = field(default_factory=SmidjaConfig)
    """L5.5 Smiðja — Brúarhönd remote-control sense.
    The body's first hand. Wraps Seidr-Smidja's Horfunarþjónn HTTP daemon.
    See src/heretic/skilningr/senses/smidja/INTERFACE.md for the full contract."""

    # -----------------------------------------------------------------------
    # Future sense stubs — Forge expands each in its own milestone.
    # All kept as generic dict stubs until their config_model submodules exist.
    # -----------------------------------------------------------------------

    filesystem: dict[str, Any] = field(default_factory=lambda: {"enabled": False})
    """L5.1 Minni — FileSystem sense stub. Forge expands in v0.7+."""

    terminal: dict[str, Any] = field(default_factory=lambda: {"enabled": False})
    """L5.2 Skepja — Terminal sense stub. Forge expands in v0.7+."""

    browser: dict[str, Any] = field(default_factory=lambda: {"enabled": False})
    """L5.3 Leið — Browser sense stub. Forge expands in v0.7+."""

    photopea: dict[str, Any] = field(default_factory=lambda: {"enabled": False})
    """L5.4 Hönd — Photopea sense stub. Forge expands in v0.7+."""

    vrchat: dict[str, Any] = field(default_factory=lambda: {"enabled": False})
    """L5.6 Líkami — VRChat sense stub. Forge expands in v0.7+."""

    agentmail: dict[str, Any] = field(default_factory=lambda: {"enabled": False})
    """L5.7 Boð — AgentMail sense stub. Forge expands in v0.7+."""

    library: dict[str, Any] = field(default_factory=lambda: {"enabled": False})
    """L5.9 Mímisbrunnr — Library sense stub. Forge expands in v0.7+."""
