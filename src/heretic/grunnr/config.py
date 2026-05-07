"""
Grunnr config — heretic.yaml loading and the HereticConfig dataclass.

This module is the single point of truth for configuration. Every layer reads the typed
HereticConfig struct; no layer reads heretic.yaml directly.

Config search order (per LAYER_INTERFACES.md §L0 Grunnr):
    1. $HERETIC_CONFIG environment variable (path to file)
    2. XDG config dir: $XDG_CONFIG_HOME/heretic/heretic.yaml (Linux/macOS)
       or %APPDATA%/heretic/heretic.yaml (Windows)
    3. User home dir: ~/heretic.yaml

All paths are resolved at runtime relative to the OS — never hardcoded absolute paths.

Top-level YAML keys match the True Names from NAMING.md:
    grunnr:       L0 Foundation settings
    bifrost:      L1 Agent connection
    rodd:         L2 Voice (STT/TTS)
    sjon:         L3 Vision (screen capture)
    vebond:       L4 UI ceremony shell
    skilningr:    L5 MCP Sense Hub (and all sub-sense configs nested under it)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# L0 Grunnr sub-config
# ---------------------------------------------------------------------------

@dataclass
class GrunnrConfig:
    """L0 Foundation settings.

    All keys correspond to the grunnr: YAML block documented in LAYER_INTERFACES.md.
    """
    log_level: str = "info"
    """Logging verbosity: trace | debug | info | warn | error."""

    log_file: Optional[str] = None
    """Path to log file (relative to CWD or home), or None for stdout only."""

    config_version: str = "1"
    """Schema version string. Grunnr will refuse to start if this does not match
    the version this code was built against (currently "1")."""

    startup_timeout_seconds: int = 30
    """Maximum seconds Kynding may take before slow senses are marked DEGRADED."""


# ---------------------------------------------------------------------------
# L1 Bifröst sub-config
# ---------------------------------------------------------------------------

@dataclass
class TailscaleConfig:
    """Tailscale routing preferences inside the bifrost: block."""
    prefer: bool = True
    """Prefer Tailscale 100.64.0.0/10 routes when resolving the agent endpoint."""

    fallback_to_direct: bool = True
    """If Tailscale routing fails, fall back to the raw endpoint URL."""


@dataclass
class BifrostConfig:
    """L1 Bifröst — agent connection settings.

    Full key reference: LAYER_INTERFACES.md §L1 Bifröst config keys.
    API key is resolved from the environment variable named in api_key — never
    stored in plaintext in the config file.
    """
    endpoint: str = "http://100.101.39.30:8643/v1"
    """OpenAI-compatible agent base URL."""

    api_key: str = "${HERETIC_AGENT_KEY}"
    """Environment variable reference. Forge must resolve this via paths.resolve_env_var()."""

    model: str = "coding"
    """Model name passed in every /v1/chat/completions request."""

    timeout_seconds: int = 30
    stream_timeout_seconds: int = 120
    connect_timeout_seconds: int = 15
    max_retries: int = 3
    backoff_seconds: list[int] = field(default_factory=lambda: [2, 5, 15])
    heartbeat_interval_seconds: int = 30
    heartbeat_miss_threshold: int = 3
    heartbeat_enabled: bool = True
    stream: bool = True
    max_tokens: int = 127000
    """Per RULES.AI.md — keep token limit high."""
    max_parallel_tool_calls: int = 4
    max_tool_call_rounds: int = 20
    drain_timeout_seconds: int = 10
    input_queue_depth: int = 10
    inject_context_on_connect: bool = False
    tailscale: TailscaleConfig = field(default_factory=TailscaleConfig)
    vision_in: bool = True


# ---------------------------------------------------------------------------
# L2 Rödd sub-config
# ---------------------------------------------------------------------------

@dataclass
class RoddSttConfig:
    """STT (Hlust — ear) half of the voice layer."""
    enabled: bool = True
    engine: str = "whisper_cpp"
    model_path: str = "models/ggml-base.en.bin"
    """Relative to the HERETIC data directory. Never an absolute path."""
    device: str = "default"
    vad_threshold: float = 0.6
    language: str = "en"
    load_strategy: str = "lazy"
    """lazy = load model on first utterance; eager = load at Kynding."""


@dataclass
class RoddTtsConfig:
    """TTS (Tunga — tongue) half of the voice layer."""
    enabled: bool = True
    engine: str = "chatterbox"
    endpoint: str = "http://100.66.178.105:7851"
    voice_id: str = "default"
    device: str = "default"
    speed: float = 1.0


@dataclass
class RoddConfig:
    """L2 Rödd — voice layer settings."""
    stt: RoddSttConfig = field(default_factory=RoddSttConfig)
    tts: RoddTtsConfig = field(default_factory=RoddTtsConfig)


# ---------------------------------------------------------------------------
# L3 Sjón sub-config
# ---------------------------------------------------------------------------

@dataclass
class SjonScreenConfig:
    """Screen capture settings."""
    enabled: bool = True
    interval_ms: int = 5000
    width: int = 1280
    height: int = 720
    crop: Optional[dict[str, int]] = None
    """None = full screen; or {x, y, w, h}."""
    buffer_depth: int = 5
    save_frames: bool = False
    """Opt-in only — never auto-saves captured frames."""


@dataclass
class SjonWebcamConfig:
    """Webcam capture settings."""
    enabled: bool = False
    device: str = "default"
    interval_ms: int = 10000


@dataclass
class SjonConfig:
    """L3 Sjón — vision layer settings."""
    screen: SjonScreenConfig = field(default_factory=SjonScreenConfig)
    webcam: SjonWebcamConfig = field(default_factory=SjonWebcamConfig)


# ---------------------------------------------------------------------------
# L4 Vébond sub-config
# ---------------------------------------------------------------------------

@dataclass
class VebondConfig:
    """L4 Vébond / Eldahús — UI ceremony shell settings."""
    theme: str = "dark_norse"
    show_frame_thumbnail: bool = False
    show_agent_text_stream: bool = True
    ceremony_button_confirm: bool = True
    """Require confirmation before Extinguish."""


# ---------------------------------------------------------------------------
# L5 Skilningr sub-config (skeleton — individual sense configs are stubs)
# ---------------------------------------------------------------------------

@dataclass
class SkilningrSenseConfig:
    """Common fields shared by every sense subprocess entry.

    Individual senses add their own fields; this is the base. Forge expands each sense
    config in L5 scope (v0.5+). For v0.1 only the enabled flag is load-bearing.
    """
    enabled: bool = False
    restart_policy: dict[str, Any] = field(
        default_factory=lambda: {
            "max_retries": 3,
            "backoff_seconds": [2, 5, 15],
        }
    )
    shutdown_grace_seconds: int = 5
    health_interval_seconds: int = 15


@dataclass
class SkilningrConfig:
    """L5 Skilningr — MCP Sense Hub settings.

    Each sense uses its code-facing identifier (not its True Name) as the key,
    per NAMING.md §5: 'The code-facing identifier is always the True Name
    transliterated without diacritics, lowercased.'
    """
    filesystem: SkilningrSenseConfig = field(default_factory=SkilningrSenseConfig)
    terminal: SkilningrSenseConfig = field(default_factory=SkilningrSenseConfig)
    browser: SkilningrSenseConfig = field(default_factory=SkilningrSenseConfig)
    photopea: SkilningrSenseConfig = field(default_factory=SkilningrSenseConfig)
    blender: SkilningrSenseConfig = field(default_factory=SkilningrSenseConfig)
    vrchat: SkilningrSenseConfig = field(default_factory=SkilningrSenseConfig)
    agentmail: SkilningrSenseConfig = field(default_factory=SkilningrSenseConfig)
    custom: SkilningrSenseConfig = field(default_factory=SkilningrSenseConfig)
    library: SkilningrSenseConfig = field(default_factory=SkilningrSenseConfig)


# ---------------------------------------------------------------------------
# Root config
# ---------------------------------------------------------------------------

@dataclass
class HereticConfig:
    """The complete, typed configuration for a HERETIC ceremony.

    Every layer reads its settings from this struct. No layer reads heretic.yaml
    directly after load_config() returns. This is the stable contract of L0 Grunnr.

    Top-level keys mirror the layer True Names (code-facing identifiers):
        grunnr, bifrost, rodd, sjon, vebond, skilningr

    Ref: docs/NAMING.md §"The Configuration File"
    """
    grunnr: GrunnrConfig = field(default_factory=GrunnrConfig)
    bifrost: BifrostConfig = field(default_factory=BifrostConfig)
    rodd: RoddConfig = field(default_factory=RoddConfig)
    sjon: SjonConfig = field(default_factory=SjonConfig)
    vebond: VebondConfig = field(default_factory=VebondConfig)
    skilningr: SkilningrConfig = field(default_factory=SkilningrConfig)

    @classmethod
    def default(cls) -> "HereticConfig":
        """Return a default config suitable for testing and first-run scenarios."""
        return cls()


# ---------------------------------------------------------------------------
# Config search and loading
# ---------------------------------------------------------------------------

SUPPORTED_CONFIG_VERSION = "1"
"""Schema version this codebase was built against. Grunnr refuses to start on mismatch."""


def _resolve_config_path(override: Optional[str] = None) -> Path:
    """Return the resolved Path to heretic.yaml using the canonical search order.

    Search order (per LAYER_INTERFACES.md §L0 Grunnr Inputs):
        1. override argument (from --config CLI flag)
        2. $HERETIC_CONFIG environment variable
        3. XDG config dir or %APPDATA%: <config_dir>/heretic/heretic.yaml
        4. Home directory: ~/heretic.yaml

    Returns a Path object. Does not verify that the file exists — the caller
    decides what to do if the path is absent (first-run scenario vs. hard error).

    No absolute paths are hardcoded. All resolution is relative to OS conventions.
    """
    if override:
        return Path(override).expanduser().resolve()

    env_path = os.environ.get("HERETIC_CONFIG")
    if env_path:
        return Path(env_path).expanduser().resolve()

    # XDG / APPDATA config directory
    if os.name == "nt":
        # Windows: %APPDATA%\heretic\heretic.yaml
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            candidate = Path(appdata) / "heretic" / "heretic.yaml"
            if candidate.exists():
                return candidate
    else:
        # Linux / macOS: $XDG_CONFIG_HOME/heretic/heretic.yaml
        xdg = os.environ.get("XDG_CONFIG_HOME", "")
        if xdg:
            candidate = Path(xdg) / "heretic" / "heretic.yaml"
            if candidate.exists():
                return candidate
        else:
            candidate = Path.home() / ".config" / "heretic" / "heretic.yaml"
            if candidate.exists():
                return candidate

    # Fallback: ~/heretic.yaml
    return Path.home() / "heretic.yaml"


def _parse_yaml_to_dict(path: Path) -> dict[str, Any]:
    """Load the YAML file at path and return a raw dict.

    Wraps yaml.safe_load with a clear error message on failure. Raises
    ConfigLoadError (a ValueError subclass) on parse failure so callers can
    surface a clean user-facing message.
    """
    try:
        import yaml  # runtime import: pyyaml is a declared dependency
    except ImportError as exc:
        raise ConfigLoadError(
            f"pyyaml is not installed. Cannot load heretic.yaml. "
            f"Run: pip install pyyaml  ({exc})"
        ) from exc

    try:
        with path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
    except OSError as exc:
        raise ConfigLoadError(f"Cannot read config file at {path}: {exc}") from exc
    except Exception as exc:
        raise ConfigLoadError(f"Failed to parse {path} as YAML: {exc}") from exc

    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ConfigLoadError(
            f"Expected a YAML mapping at the top level of {path}, "
            f"but got {type(raw).__name__}."
        )
    return raw


def _hydrate_config(raw: dict[str, Any]) -> HereticConfig:
    """Convert a raw YAML dict into a typed HereticConfig.

    This function is intentionally permissive about missing keys — it applies
    defaults from the dataclasses for any absent field. This means a minimal
    heretic.yaml (just a few overrides) is valid.

    Forge will expand this with recursive dict merging and type coercion as
    the full config schema is exercised in tests.
    """
    raise NotImplementedError(
        "Forge will implement: config._hydrate_config — "
        "recursively merge raw dict values into the dataclass hierarchy, "
        "resolve ${ENV_VAR} references via os.environ, "
        "validate config_version matches SUPPORTED_CONFIG_VERSION, "
        "return a fully populated HereticConfig."
    )


def load_config(path: Optional[str] = None) -> HereticConfig:
    """Load, parse, and return a typed HereticConfig from heretic.yaml.

    This is the primary entry point for all layers that need configuration.
    No layer should call _resolve_config_path or _parse_yaml_to_dict directly.

    Args:
        path: Optional override path to heretic.yaml. If None, the canonical
              search order is used (env var → XDG → home dir).

    Returns:
        HereticConfig: fully populated, typed config struct.

    Raises:
        ConfigLoadError: if the file cannot be read, is malformed YAML,
                         or the config_version does not match.
    """
    raise NotImplementedError(
        "Forge will implement: config.load_config — "
        "call _resolve_config_path(path), "
        "call _parse_yaml_to_dict(resolved_path), "
        "call _hydrate_config(raw_dict), "
        "return HereticConfig."
    )


# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------

class ConfigLoadError(ValueError):
    """Raised when heretic.yaml cannot be loaded or is invalid.

    This is a subclass of ValueError (not a custom base) so that callers who
    catch ValueError still catch it, while code that specifically handles config
    failures can catch ConfigLoadError for finer-grained handling.

    L0 Grunnr maps this to the CONFIG_ERROR terminal lifecycle state.
    """
