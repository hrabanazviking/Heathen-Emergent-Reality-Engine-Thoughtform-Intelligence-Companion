"""
Skilningr config model — SkilningrConfig, SmidjaConfig, ForgeConfig,
MinniConfig, SkepjaConfig, LeidConfig.

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

MinniConfig / SkepjaConfig / LeidConfig (v0.6.2):
    Three new senses — filesystem, terminal, HTTP fetch. All default enabled=False.
    Privacy-first: no capability is granted until the operator explicitly opts in.
    Sandbox primitives live in heretic.skilningr.sandbox (stdlib-only).

LibraryConfig (v0.7):
    Library sense config (L5.9 Mímisbrunnr). enabled=False by default.
    storage_path: resolved at init time via platformdirs.user_data_dir if empty.
    sources: list of source_ids the operator permits to be downloaded. Empty
    default = none enabled (all consent prompts will be shown for any download).

Ref: TASK_HERETIC_v0.6_HANDS_AT_FORGE.md §3 (architectural decisions)
     TASK_HERETIC_v0.6.1_FORGE_DISPATCH.md §3 (Forge architectural decisions)
     TASK_HERETIC_v0.6.2_MORE_SENSES.md §3 (sandbox invariants)
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
# L5.1 Minni — filesystem sense config  [v0.6.2]
# ---------------------------------------------------------------------------

@dataclass
class MinniConfig:
    """Configuration for the Minni sense — sandboxed local filesystem access.

    Minni is the body's memory: it reads and writes files within a strict
    sandbox. The sandbox boundary is defined by allowed_roots — an explicit
    opt-in list. Everything outside is inaccessible regardless of OS permissions.

    KEY INVARIANTS (DO NOT BREAK):
        - enabled defaults False. The agent gains no filesystem access until
          the operator explicitly sets enabled: true in heretic.yaml.
        - Every path submitted to Minni is validated against allowed_roots via
          sandbox.path_within_allowed_roots() BEFORE any I/O occurs.
        - Symlinks are NOT followed during validation (follow_symlinks: false
          default). This prevents symlink escape attacks.
        - File sizes are capped at max_read_bytes / max_write_bytes to prevent
          token-blowup and resource exhaustion.
        - No execute permission is ever touched by Minni.

    Heretic.yaml key: skilningr.minni.*
    Ref: src/heretic/skilningr/senses/minni/INTERFACE.md
         TASK_HERETIC_v0.6.2_MORE_SENSES.md §3 (Minni sandbox invariants)
    """

    enabled: bool = False
    """Opt-in. Must be explicitly set to true in heretic.yaml to expose Minni
    filesystem tools to the agent. Default false is the privacy-first safe state:
    the agent gains no local filesystem capability until the operator consciously
    enables it AND configures the allowed_roots list."""

    allowed_roots: list[str] = field(default_factory=lambda: ["~/heretic_workspace"])
    """List of root directories the agent may read from and write to.
    Each entry is resolved to an absolute path by sandbox.path_within_allowed_roots().
    The ~ home-directory shorthand is supported. Default is ~/heretic_workspace —
    a single dedicated workspace directory.

    IMPORTANT: An empty list means no filesystem access is granted regardless
    of enabled=True. Operators MUST add at least one entry to permit any access.

    Example:
        allowed_roots:
          - ~/heretic_workspace
          - /data/agent_output
    """

    max_read_bytes: int = 1_048_576  # 1 MB
    """Maximum bytes to read from a single file. Files larger than this are
    rejected with a MinniFileTooLargeError — no partial read is attempted.
    Default: 1 MiB. Increase for specific workflows that require larger files,
    but be aware that very large reads consume significant agent context window.
    Must be > 0."""

    max_write_bytes: int = 1_048_576  # 1 MB
    """Maximum bytes the agent may write in a single write_file call.
    Content exceeding this limit is rejected before any file is created or
    overwritten. Default: 1 MiB. Must be > 0."""

    follow_symlinks: bool = False
    """Whether to follow symlinks when resolving paths during I/O operations.
    Default false (privacy-first): a symlink that points outside allowed_roots
    is treated as a sandbox violation even if the symlink itself is inside.
    Set to true only if your workspace uses symlinks intentionally and you
    accept the risk that a symlink could point outside the sandbox boundary."""

    def __post_init__(self) -> None:
        """Validate config fields at construction time.

        Raises:
            ValueError: if max_read_bytes or max_write_bytes are <= 0.
        """
        if self.max_read_bytes <= 0:
            raise ValueError(
                f"MinniConfig.max_read_bytes must be > 0, got {self.max_read_bytes!r}."
            )
        if self.max_write_bytes <= 0:
            raise ValueError(
                f"MinniConfig.max_write_bytes must be > 0, got {self.max_write_bytes!r}."
            )


# ---------------------------------------------------------------------------
# L5.2 Skepja — terminal sense config  [v0.6.2]
# ---------------------------------------------------------------------------

@dataclass
class SkepjaConfig:
    """Configuration for the Skepja sense — sandboxed shell command execution.

    Skepja is the body's shaping hand: it runs commands in a controlled
    environment. The command_allowlist is the gate — no executable may run
    unless the operator explicitly permits it. An empty allowlist permits nothing.

    KEY INVARIANTS (DO NOT BREAK):
        - enabled defaults False. The agent gains no terminal capability until
          the operator explicitly enables it.
        - command_allowlist defaults [] (empty). No command runs until the
          operator adds entries. This is the safest possible default.
        - All commands are executed with subprocess.run(shell=False).
          The client splits the command via shlex.split — this function validates
          here, but shell=False enforcement lives in client.py.
        - The subprocess does NOT inherit HERETIC's environment unless
          inherit_env: true (default false). This prevents credential leakage.
        - Output is capped at max_output_bytes to prevent token-blowup.
        - Each run_command invocation starts a fresh subprocess — there is no
          persistent shell session (stateless by design in v0.6.2).

    Heretic.yaml key: skilningr.skepja.*
    Ref: src/heretic/skilningr/senses/skepja/INTERFACE.md
         TASK_HERETIC_v0.6.2_MORE_SENSES.md §3 (Skepja sandbox invariants)
    """

    enabled: bool = False
    """Opt-in. Must be explicitly set to true in heretic.yaml. Default false."""

    command_allowlist: list[str] = field(default_factory=list)
    """Explicit list of permitted executable names or full command patterns.
    Default: [] (empty) — nothing can run. The operator must add entries.

    Each entry may be:
        - A bare executable name: "git"  (permits any git <subcommand>)
        - A full pattern: "git status"   (permits only this exact invocation)

    The sandbox.command_in_allowlist() function checks the first token of the
    parsed command against this list. Case-sensitive on all platforms.

    Example:
        command_allowlist:
          - git
          - python
          - pytest
    """

    working_directory: str = "~/heretic_workspace"
    """Directory in which all commands are executed. The agent cannot change
    this directory — it is fixed for all Skepja invocations.
    Default: ~/heretic_workspace. The ~ home-directory shorthand is supported.
    Must be an existing directory when a command is first run."""

    timeout_seconds: int = 60
    """Maximum wall-clock seconds a subprocess may run before being terminated.
    Default: 60. Increase for long-running build tasks. Must be > 0."""

    inherit_env: bool = False
    """Whether the subprocess inherits HERETIC's environment variables.
    Default false — the subprocess starts with a minimal environment, preventing
    accidental exposure of API keys, tokens, or other credentials present in
    HERETIC's environment. Set to true only when the command requires specific
    environment variables that cannot be set by other means."""

    max_output_bytes: int = 65_536  # 64 KB
    """Maximum bytes to capture from stdout and stderr combined.
    Output beyond this limit is truncated. Default: 64 KiB. Must be > 0."""

    def __post_init__(self) -> None:
        """Validate config fields at construction time.

        Raises:
            ValueError: if timeout_seconds or max_output_bytes are <= 0.
        """
        if self.timeout_seconds <= 0:
            raise ValueError(
                f"SkepjaConfig.timeout_seconds must be > 0, got {self.timeout_seconds!r}."
            )
        if self.max_output_bytes <= 0:
            raise ValueError(
                f"SkepjaConfig.max_output_bytes must be > 0, got {self.max_output_bytes!r}."
            )


# ---------------------------------------------------------------------------
# L5.3 Leið — HTTP fetch sense config  [v0.6.2]
# ---------------------------------------------------------------------------

@dataclass
class LeidConfig:
    """Configuration for the Leið sense — sandboxed HTTP fetch and text extraction.

    Leið is the body's path outward: it fetches pages from the web within an
    explicit URL allowlist. No URL is accessible unless the operator adds a
    matching pattern. An empty allowlist fetches nothing.

    KEY INVARIANTS (DO NOT BREAK):
        - enabled defaults False. The agent gains no outbound HTTP capability
          until the operator explicitly enables it.
        - url_allowlist_patterns defaults [] (empty). No URL is fetchable until
          the operator adds patterns. A "*" wildcard pattern enables unrestricted
          fetch — this is logged as a warning at ceremony start.
        - HTTPS only by default (allow_http: false). HTTP URLs are rejected with
          a sandbox error unless allow_http: true is explicitly set.
        - Cookies are never stored, sent, or accepted (stateless by design).
        - No JavaScript execution — httpx only; playwright = v0.6.2.1+.
        - Response size is capped at max_response_bytes to prevent token-blowup.
        - Redirects are followed up to max_redirects (default 5); beyond that
          the request is aborted.

    Heretic.yaml key: skilningr.leid.*
    Ref: src/heretic/skilningr/senses/leid/INTERFACE.md
         TASK_HERETIC_v0.6.2_MORE_SENSES.md §3 (Leið sandbox invariants)
    """

    enabled: bool = False
    """Opt-in. Must be explicitly set to true in heretic.yaml. Default false."""

    url_allowlist_patterns: list[str] = field(default_factory=list)
    """Explicit list of URL patterns the agent may fetch. Default: [] (empty).
    No URL is fetchable until the operator adds at least one pattern.

    Pattern forms:
        "*"                        — unrestricted wildcard (allow all URLs)
                                     WARNING: a "*" pattern is logged as a
                                     security warning at ceremony start.
        "https://docs.python.org/*" — prefix wildcard (any path under this host)
        "https://example.com/page"  — exact URL match

    fnmatch semantics are used: "*" matches any sequence of characters.
    Scheme comparison is case-insensitive; host comparison is lowercase-normalised.

    Example:
        url_allowlist_patterns:
          - "https://docs.python.org/*"
          - "https://en.wikipedia.org/*"
    """

    timeout_seconds: int = 30
    """Maximum wall-clock seconds for the full HTTP request (connect + read).
    Default: 30. Must be > 0."""

    max_redirects: int = 5
    """Maximum number of HTTP redirects to follow before aborting.
    Default: 5. Must be >= 0 (0 = no redirects followed)."""

    max_response_bytes: int = 1_048_576  # 1 MB
    """Maximum bytes to read from an HTTP response body. Responses larger
    than this limit are truncated. Default: 1 MiB. Must be > 0."""

    user_agent: str = "HERETIC/0.6.2 (heretic-summoning-circle)"
    """User-Agent header sent with all Leið requests. Must be a non-empty string.
    Identifies the HERETIC agent to remote servers. Do not set to an empty string."""

    allow_http: bool = False
    """Whether HTTP (non-TLS) URLs are permitted. Default false — HTTPS only.
    Setting this to true allows fetching http:// URLs that match the allowlist.
    HTTP URLs are logged as warnings even when allow_http is true, because they
    expose request/response content without encryption.
    NEVER set allow_http: true in production unless HTTP is unavoidable."""

    # ----- v0.8.0 Opið Vef — browser-render fields (apply to leid.render_url only) -----

    browser_navigation_timeout_seconds: int = 30
    """Maximum wall-clock seconds for ``page.goto()`` during a ``leid.render_url``
    call. INTENTIONALLY separate from ``timeout_seconds`` (which governs the
    httpx tools): rendered pages legitimately take longer than static fetches,
    and conflating the two would force a global increase. Default 30. Must be > 0.

    Used only by ``PlaywrightLeidClient.render_url`` (v0.8.0+). Has no effect on
    ``leid.fetch_url`` or ``leid.extract_text``."""

    browser_load_state: str = "domcontentloaded"
    """Playwright wait-condition for ``page.goto()`` during a ``leid.render_url``
    call. One of: ``commit`` (response received), ``domcontentloaded`` (default —
    HTML parsed and synchronous scripts run), ``load`` (load event fired),
    ``networkidle`` (no network activity for 500 ms — slowest, most complete).
    Default ``domcontentloaded`` is the best balance of "page is rendered enough
    to extract" vs "no waiting forever for trackers." Must be one of the four
    documented values."""

    # ----- v0.8.1 Mynd af Vegferð — screenshot field (applies to leid.screenshot only) -----

    browser_screenshot_full_page: bool = True
    """Whether ``leid.screenshot`` captures the full scrollable page (True) or
    only the current viewport (False, default 1280x720). Default True — matches
    the typical "show me the page" agent intent. Set False for SPAs whose full
    page is enormous; the viewport-only screenshot is bounded in size by the
    viewport dimensions and tends to fit within smaller ``max_response_bytes``
    caps. Has no effect on ``leid.render_url`` or the httpx tools."""

    # ----- v0.8.2 Innan Hurðar — session lifecycle + click fields -----

    browser_max_concurrent_sessions: int = 3
    """Maximum number of simultaneously-open browser sessions for ``leid.open_session``.
    Default 3 — defensive cap because each session holds an entire Chromium
    process. ``open_session`` at cap raises ``LeidSessionLimitError`` (D-33);
    no silent eviction. Operators with more headroom can raise this; operators
    on small hardware can lower it. Must be >= 1."""

    browser_session_idle_timeout_seconds: int = 300
    """Session idle timeout — sessions with no successful tool-call activity
    for this many seconds are evicted. Default 300 (5 minutes). Activity is
    updated by ``session_status``, ``click``, and any future session-affecting
    tool. Must be > 0."""

    browser_session_max_lifetime_seconds: int = 1800
    """Session absolute lifetime — even active sessions are evicted after this
    many seconds. Default 1800 (30 minutes). Hard ceiling to prevent indefinite
    resource holding. Must be > 0 AND >= browser_session_idle_timeout_seconds
    (a max-lifetime shorter than the idle timeout would be incoherent)."""

    browser_click_timeout_seconds: int = 10
    """Maximum wall-clock seconds for a single ``leid.click`` call. Separate
    from ``browser_navigation_timeout_seconds`` because click is a fast
    interactive action; long timeout = bad UX when the selector is wrong.
    Default 10. Must be > 0."""

    def __post_init__(self) -> None:
        """Validate config fields at construction time.

        Raises:
            ValueError: if timeout_seconds, max_response_bytes, or
                        browser_navigation_timeout_seconds are <= 0,
                        max_redirects < 0, user_agent is empty, or
                        browser_load_state is not one of the four allowed values.

        Warns (but does not raise) if url_allowlist_patterns contains "*"
        (unrestricted wildcard) while enabled is True.
        """
        if self.timeout_seconds <= 0:
            raise ValueError(
                f"LeidConfig.timeout_seconds must be > 0, got {self.timeout_seconds!r}."
            )
        if self.max_redirects < 0:
            raise ValueError(
                f"LeidConfig.max_redirects must be >= 0, got {self.max_redirects!r}."
            )
        if self.max_response_bytes <= 0:
            raise ValueError(
                f"LeidConfig.max_response_bytes must be > 0, got {self.max_response_bytes!r}."
            )
        if not self.user_agent or not self.user_agent.strip():
            raise ValueError(
                "LeidConfig.user_agent must be a non-empty string. "
                f"Got {self.user_agent!r}."
            )
        # v0.8.0 — browser-render field validation
        if self.browser_navigation_timeout_seconds <= 0:
            raise ValueError(
                f"LeidConfig.browser_navigation_timeout_seconds must be > 0, "
                f"got {self.browser_navigation_timeout_seconds!r}."
            )
        _allowed_load_states = {"commit", "domcontentloaded", "load", "networkidle"}
        if self.browser_load_state not in _allowed_load_states:
            raise ValueError(
                f"LeidConfig.browser_load_state must be one of "
                f"{sorted(_allowed_load_states)}, got {self.browser_load_state!r}."
            )
        # v0.8.2 — session + click field validation
        if self.browser_max_concurrent_sessions < 1:
            raise ValueError(
                f"LeidConfig.browser_max_concurrent_sessions must be >= 1, "
                f"got {self.browser_max_concurrent_sessions!r}."
            )
        if self.browser_session_idle_timeout_seconds <= 0:
            raise ValueError(
                f"LeidConfig.browser_session_idle_timeout_seconds must be > 0, "
                f"got {self.browser_session_idle_timeout_seconds!r}."
            )
        if self.browser_session_max_lifetime_seconds <= 0:
            raise ValueError(
                f"LeidConfig.browser_session_max_lifetime_seconds must be > 0, "
                f"got {self.browser_session_max_lifetime_seconds!r}."
            )
        if (
            self.browser_session_max_lifetime_seconds
            < self.browser_session_idle_timeout_seconds
        ):
            raise ValueError(
                f"LeidConfig.browser_session_max_lifetime_seconds "
                f"({self.browser_session_max_lifetime_seconds}) must be >= "
                f"browser_session_idle_timeout_seconds "
                f"({self.browser_session_idle_timeout_seconds}) — a max-lifetime "
                f"shorter than the idle timeout would be incoherent."
            )
        if self.browser_click_timeout_seconds <= 0:
            raise ValueError(
                f"LeidConfig.browser_click_timeout_seconds must be > 0, "
                f"got {self.browser_click_timeout_seconds!r}."
            )
        # Warn on unrestricted wildcard
        if self.enabled and "*" in self.url_allowlist_patterns:
            warnings.warn(
                "LeidConfig: url_allowlist_patterns contains '*' — ALL URLs are "
                "fetchable. This disables the URL sandbox entirely. "
                "Remove '*' and add specific patterns unless unrestricted fetch "
                "is intentional.",
                stacklevel=2,
            )


# ---------------------------------------------------------------------------
# L5.0 MCP Server config  [v0.6.x]
# ---------------------------------------------------------------------------

@dataclass
class McpServerConfig:
    """Configuration for HERETIC's MCP server transport.

    When enabled, McpServer opens an MCP-protocol transport alongside (or instead
    of) the OpenAI tool_call path.  MCP-compatible agents — Claude Desktop,
    Continue, future OpenClaw with an MCP client — can connect directly to
    HERETIC without requiring an OpenAI-compatible intermediary.

    The same tools, the same dispatcher, the same sandboxes, and the same auth
    invariants apply regardless of which transport the agent uses.

    Transport options
    -----------------
    stdio   — The process communicates over stdin/stdout.  The MCP client
              (e.g. Claude Desktop) launches HERETIC as a subprocess.  No bind
              address or port is needed.  Auth is implicit (process ownership).

    http    — HERETIC launches a Starlette/uvicorn HTTP server at host:port.
              Non-loopback bind addresses require allow_remote_bind==True.
              Auth for remote binds is a Forge responsibility (middleware).

    KEY INVARIANTS (DO NOT BREAK):
        - enabled defaults False.  The MCP transport is not opened until the
          operator explicitly opts in.
        - Non-loopback host requires allow_remote_bind==True (mirrors Vébond and
          Brúarhönd patterns throughout HERETIC).  __post_init__ enforces this.
        - port must be in valid range 1–65535.
        - transport must be "stdio" or "http".
        - request_timeout_seconds must be > 0.

    Heretic.yaml key: skilningr.mcp_server.*
    Ref: src/heretic/skilningr/mcp_server.py
         src/heretic/skilningr/INTERFACE.md §MCP Server
         docs/architecture/AGENT_AGNOSTIC_PROTOCOL.md §v0.6.x MCP transport addendum
    """

    enabled: bool = False
    """Opt-in.  Must be explicitly set to true to open an MCP transport.
    Default false: HERETIC does not expose an MCP surface until the operator
    consciously enables it.  This is consistent with all other HERETIC sense
    and transport opt-ins."""

    transport: str = "stdio"
    """Which MCP transport to open.  Must be "stdio" or "http".
    Default "stdio": the safest and most portable choice.  Claude Desktop, for
    example, launches HERETIC as an stdio MCP server subprocess.
    Use "http" when remote agents (on other machines or containers) need to
    connect to HERETIC's MCP surface over the network."""

    host: str = "127.0.0.1"
    """Bind address for the HTTP transport.  Ignored when transport="stdio".
    Default 127.0.0.1 (loopback only — safe).  For cross-machine use, set to a
    Tailscale IP or MagicDNS name.
    INVARIANT: non-loopback host requires allow_remote_bind==True."""

    port: int = 8643
    """TCP port for the HTTP transport.  Ignored when transport="stdio".
    Default 8643 — matches the Hermes endpoint port in heretic.example.yaml for
    conceptual consistency.  Must be in valid range 1–65535.
    IMPORTANT: ensure this port does not conflict with other HERETIC services
    (Vébond WebSocket defaults to 8642)."""

    allow_remote_bind: bool = False
    """Whether to allow the HTTP transport to bind to a non-loopback address.
    Default False.  When False, __post_init__ rejects any host other than
    127.0.0.1 with a ValueError — protecting operators from accidentally
    exposing the MCP surface to the network without consciously opting in.
    Set to True only when you intend cross-machine MCP agent connections AND
    you have configured appropriate authentication (bearer token middleware).
    Ref: Vébond allow_remote_bind pattern (same invariant across all HERETIC
    transports)."""

    request_timeout_seconds: int = 60
    """Per-request timeout in seconds applied by the MCP server to tool call
    execution.  Default 60.  Increase for senses with slow operations (e.g.
    Forge/Blender builds).  Must be > 0."""

    def __post_init__(self) -> None:
        """Validate config fields at construction time.

        Raises:
            ValueError: if transport is not "stdio" or "http";
                        if port is out of range 1–65535;
                        if request_timeout_seconds <= 0;
                        if host is not 127.0.0.1 and allow_remote_bind is False
                        (remote bind safety gate — mirrors Vébond/Brúarhönd pattern).
        """
        _valid_transports = {"stdio", "http"}
        if self.transport not in _valid_transports:
            raise ValueError(
                f"McpServerConfig.transport {self.transport!r} is not valid. "
                f"Must be one of {sorted(_valid_transports)}."
            )
        if not (1 <= self.port <= 65535):
            raise ValueError(
                f"McpServerConfig.port {self.port!r} is out of valid range 1–65535."
            )
        if self.request_timeout_seconds <= 0:
            raise ValueError(
                f"McpServerConfig.request_timeout_seconds must be > 0, "
                f"got {self.request_timeout_seconds!r}."
            )
        # Remote bind safety gate — identical pattern to Vébond ws_host validation.
        # F-3: include "::1" (IPv6 loopback) in the loopback set to match the
        # identical set used by _start_http at runtime.  Without this, an operator
        # who sets host: "::1" is incorrectly required to also set allow_remote_bind,
        # creating an asymmetry between construction-time and runtime checks.
        _loopback_hosts = {"127.0.0.1", "localhost", "::1"}
        if self.transport == "http" and self.host not in _loopback_hosts:
            if not self.allow_remote_bind:
                raise ValueError(
                    f"McpServerConfig: host {self.host!r} is not loopback but "
                    f"allow_remote_bind is False. "
                    f"Set mcp_server.allow_remote_bind: true in heretic.yaml to "
                    f"permit binding to non-loopback addresses. "
                    f"Ensure you have also configured authentication middleware "
                    f"before enabling remote MCP access."
                )


# ---------------------------------------------------------------------------
# L5.9 Mímisbrunnr — Library sense config  [v0.7]
# ---------------------------------------------------------------------------

@dataclass
class LibraryConfig:
    """Configuration for the Library sense — Mímisbrunnr text corpus access.

    The Library sense gives the agent access to the Norse starter-pack
    corpus (five public-domain texts downloaded from Project Gutenberg)
    via a lightweight keyword-search index. It also supports operator-
    curated file libraries and optional MindSpark integration.

    KEY INVARIANTS (DO NOT BREAK):
        - enabled defaults False. The agent gains no corpus access until
          the operator explicitly sets enabled: true in heretic.yaml.
        - storage_path defaults to "" (empty). When empty, the Library
          sense resolves it at init time via platformdirs.user_data_dir
          ("heretic/library/mimisbrunnr") — Forge implements this.
        - sources defaults to [] (empty list) — no sources are downloaded
          automatically. The operator must add source_ids to this list
          to pre-approve downloads, OR the agent can trigger consent
          prompts at runtime.
        - max_results caps the number of hits returned per library.search
          tool call. Default 20.
        - autoindex_on_open: if True, the Library sense rebuilds the
          keyword index at sense.open() time if the index is stale.

    Heretic.yaml key: skilningr.library.*
    Ref: src/heretic/skilningr/senses/library/INTERFACE.md
         src/heretic/skilningr/mimisbrunnr/INTERFACE.md
         TASK_HERETIC_v0.7_MIMISBRUNNR.md §Config
    """

    enabled: bool = False
    """Opt-in. Must be explicitly set to true in heretic.yaml to expose
    Library tools to the agent. Default false is the privacy-first safe
    state: the agent gains no corpus access until the operator enables it."""

    storage_path: str = ""
    """Absolute or ~ path to the Mímisbrunnr data directory.
    When empty (default), the Library sense resolves the path at init
    time using platformdirs.user_data_dir("heretic") / "library" /
    "mimisbrunnr". Forge implements this resolution.

    If set explicitly, the operator's path is used verbatim (after ~
    expansion). The directory is created at sense.open() time if it
    does not exist.

    Never hardcode an absolute path in heretic.yaml for portability —
    prefer the empty-string default which uses platformdirs."""

    max_results: int = 20
    """Maximum number of search results returned per library.search call.
    Default 20. Must be > 0. Increase for workflows that need broad
    coverage; decrease to keep agent context usage low."""

    autoindex_on_open: bool = True
    """If True, the Library sense calls KeywordIndex.build() at
    sense.open() time whenever the index file is absent or older than
    any source file. Default True — keeps the index fresh automatically.
    Set to False to disable automatic rebuilds (useful in production
    where the index is pre-built and should not be rebuilt on startup)."""

    sources: list[str] = field(default_factory=list)
    """List of source_ids the operator pre-approves for download.
    Each entry must be a valid id from NORSE_STARTER_PACK.source_ids.
    Default [] (empty) — no sources are pre-approved; consent prompts
    will appear at runtime for any download.

    To pre-approve all five starter-pack sources:
        sources:
          - prose_edda_brodeur
          - poetic_edda_bellows
          - heimskringla_laing
          - volsunga_saga_morris
          - erik_red_saga

    Sources not in this list will require interactive consent unless
    the sense is invoked from a non-interactive context, in which case
    the download is skipped and the agent receives a structured error."""

    def __post_init__(self) -> None:
        """Validate config fields at construction time.

        Raises:
            ValueError: if max_results <= 0.
        """
        if self.max_results <= 0:
            raise ValueError(
                f"LibraryConfig.max_results must be > 0, "
                f"got {self.max_results!r}."
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
    # v0.6.2 — three concrete sense configs (Minni, Skepja, Leið)
    # The prior dict stubs are replaced with typed dataclasses.
    # All default enabled=False (privacy-first).
    # -----------------------------------------------------------------------

    minni: MinniConfig = field(default_factory=MinniConfig)
    """L5.1 Minni — filesystem sense (sandboxed read/write).
    The body's memory. Exposes 3 tools: minni.read_file, minni.write_file,
    minni.list_directory. All paths validated against allowed_roots.
    Ref: src/heretic/skilningr/senses/minni/INTERFACE.md"""

    skepja: SkepjaConfig = field(default_factory=SkepjaConfig)
    """L5.2 Skepja — terminal sense (allowlisted shell commands).
    The body's shaping hand. Exposes 2 tools: skepja.run_command,
    skepja.get_working_directory. command_allowlist defaults empty.
    Ref: src/heretic/skilningr/senses/skepja/INTERFACE.md"""

    leid: LeidConfig = field(default_factory=LeidConfig)
    """L5.3 Leið — HTTP fetch sense (URL-allowlisted outbound fetch).
    The body's road. Exposes 2 tools: leid.fetch_url, leid.extract_text.
    url_allowlist_patterns defaults empty; HTTPS-only by default.
    Ref: src/heretic/skilningr/senses/leid/INTERFACE.md"""

    # -----------------------------------------------------------------------
    # Future sense stubs — Forge expands each in its own milestone.
    # -----------------------------------------------------------------------

    photopea: dict[str, Any] = field(default_factory=lambda: {"enabled": False})
    """L5.4 Hönd — Photopea sense stub. Forge expands in v0.7+."""

    vrchat: dict[str, Any] = field(default_factory=lambda: {"enabled": False})
    """L5.6 Líkami — VRChat sense stub. Forge expands in v0.7+."""

    agentmail: dict[str, Any] = field(default_factory=lambda: {"enabled": False})
    """L5.7 Boð — AgentMail sense stub. Forge expands in v0.8+."""

    library: "LibraryConfig" = field(default_factory=lambda: LibraryConfig())
    """L5.9 Mímisbrunnr — Library (wisdom well) sense.
    The body's access to the Norse starter-pack text corpus.
    Exposes 3 tools: library.search, library.get_text, library.list_sources.
    enabled defaults False; storage_path resolved at init if empty.
    Ref: src/heretic/skilningr/senses/library/INTERFACE.md"""

    mcp_server: "McpServerConfig" = field(default_factory=lambda: McpServerConfig())
    """v0.6.x — MCP server configuration.

    When enabled, HERETIC opens an MCP transport (stdio or http) so that
    MCP-compatible agents (Claude Desktop, Continue, future OpenClaw with MCP
    client) can connect directly and call HERETIC's tools.

    The same 16+ tools exposed via OpenAI tool_use are also exposed here.
    Same dispatcher.  Same sandboxes.  Same auth invariants.

    Heretic.yaml key: skilningr.mcp_server.*
    Ref: src/heretic/skilningr/mcp_server.py
         docs/architecture/AGENT_AGNOSTIC_PROTOCOL.md §v0.6.x MCP transport addendum
         src/heretic/skilningr/INTERFACE.md §MCP Server
    """
