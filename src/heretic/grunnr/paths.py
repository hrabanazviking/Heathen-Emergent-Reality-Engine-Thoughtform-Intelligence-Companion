"""
Grunnr paths — portable path resolution helpers.

RULES.AI.md is absolute on this: no hardcoded absolute paths, anywhere. This module
centralises all path logic so every other module imports from here and never constructs
paths directly.

All paths returned by this module are:
    - Resolved relative to OS conventions (home dir, data dir, config dir)
    - Never constructed with hardcoded drive letters or Unix roots
    - Cross-platform: work on Windows, Linux, macOS, Raspberry Pi

The Tauri-side (Rust, v0.4+) has its own path resolver. This Python module covers the
Python runtime layers (L0 Grunnr config/logging, L1 Bifröst, L5 Skilningr senses).

Key paths:
    heretic_config_dir()  — where heretic.yaml lives (per OS convention)
    heretic_data_dir()    — where runtime data lives (models, library indices)
    heretic_log_dir()     — where log files are written if log_file is set
    resolve_env_var(s)    — expand "${ENV_VAR}" references in config strings
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Optional

# Pattern for ${ENV_VAR} references in config values.
_ENV_VAR_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}")


def heretic_config_dir() -> Path:
    """Return the OS-appropriate directory for heretic.yaml.

    Windows:  %APPDATA%/heretic/
    macOS:    ~/Library/Application Support/heretic/
    Linux:    $XDG_CONFIG_HOME/heretic/ or ~/.config/heretic/

    Returns the directory as a Path (may not exist yet — caller decides whether
    to create it).
    """
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            return Path(appdata) / "heretic"
        return Path.home() / "AppData" / "Roaming" / "heretic"

    # macOS — sys.platform is "darwin" on all macOS versions
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "heretic"

    # Linux / other POSIX
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    if xdg:
        return Path(xdg) / "heretic"
    return Path.home() / ".config" / "heretic"


def heretic_data_dir() -> Path:
    """Return the OS-appropriate directory for HERETIC runtime data.

    This is where model files, library indices, and other persistent runtime
    data live. Never the same as the config dir.

    Windows:  %LOCALAPPDATA%/heretic/
    macOS:    ~/Library/Application Support/heretic/data/
    Linux:    $XDG_DATA_HOME/heretic/ or ~/.local/share/heretic/
    """
    if sys.platform == "win32":
        localappdata = os.environ.get("LOCALAPPDATA", "")
        if localappdata:
            return Path(localappdata) / "heretic"
        return Path.home() / "AppData" / "Local" / "heretic"

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "heretic" / "data"

    xdg = os.environ.get("XDG_DATA_HOME", "")
    if xdg:
        return Path(xdg) / "heretic"
    return Path.home() / ".local" / "share" / "heretic"


def heretic_log_dir() -> Path:
    """Return the directory for HERETIC log files.

    Windows:  %LOCALAPPDATA%/heretic/logs/
    macOS:    ~/Library/Logs/heretic/
    Linux:    $XDG_STATE_HOME/heretic/ or ~/.local/state/heretic/
    """
    if sys.platform == "win32":
        localappdata = os.environ.get("LOCALAPPDATA", "")
        if localappdata:
            return Path(localappdata) / "heretic" / "logs"
        return Path.home() / "AppData" / "Local" / "heretic" / "logs"

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Logs" / "heretic"

    xdg = os.environ.get("XDG_STATE_HOME", "")
    if xdg:
        return Path(xdg) / "heretic"
    return Path.home() / ".local" / "state" / "heretic"


def resolve_relative_path(raw: str, base: Optional[Path] = None) -> Path:
    """Resolve a config path string relative to a base directory.

    Config values like ``"models/ggml-base.en.bin"`` or ``"~/heretic_workspace"``
    are resolved here. Never returns an absolute constructed path — the result is
    always derived from runtime locations.

    Args:
        raw: The path string from config (may contain ~, relative segments).
        base: Base directory to resolve relative paths against. Defaults to
              heretic_data_dir() if None.

    Returns:
        Resolved, absolute Path object. Never a hardcoded string.
    """
    p = Path(raw).expanduser()
    if p.is_absolute():
        return p
    base_dir = base if base is not None else heretic_data_dir()
    return (base_dir / p).resolve()


def resolve_env_var(value: str) -> str:
    """Expand ``${ENV_VAR}`` references in a config string.

    Used specifically for the ``bifrost.api_key`` and credential fields in
    heretic.yaml that must never be stored as plaintext.

    Args:
        value: A string that may contain one or more ``${VAR_NAME}`` tokens.

    Returns:
        The string with all ``${VAR_NAME}`` tokens replaced by their environment
        variable values.

    Raises:
        EnvironmentError: if a referenced variable is not set.
    """
    def _replace(match: re.Match) -> str:
        var_name = match.group(1)
        env_val = os.environ.get(var_name)
        if env_val is None:
            raise EnvironmentError(
                f"heretic.yaml references ${{{var_name}}} "
                f"but that environment variable is not set. "
                f"Set it before starting HERETIC: "
                f"export {var_name}=<your_value>"
            )
        return env_val

    return _ENV_VAR_PATTERN.sub(_replace, value)


def package_root() -> Path:
    """Return the root directory of the installed heretic package.

    This is ``src/heretic/`` in the development layout. Used for locating
    bundled assets (example configs, schema files) that ship with the package.

    Never used for user data — that lives in heretic_data_dir().
    """
    return Path(__file__).resolve().parent.parent
