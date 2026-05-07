"""
Tests for grunnr.paths — portable OS path resolution.

Validates that paths are derived from OS conventions (never hardcoded), that
${ENV_VAR} expansion works, and that sys.platform switching returns the right
directory structures for each platform.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from heretic.grunnr.paths import (
    heretic_config_dir,
    heretic_data_dir,
    heretic_log_dir,
    resolve_relative_path,
    resolve_env_var,
    package_root,
)


# ---------------------------------------------------------------------------
# heretic_config_dir
# ---------------------------------------------------------------------------

def test_config_dir_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    """On Windows (sys.platform=='win32'), config dir uses %APPDATA%/heretic."""
    monkeypatch.setenv("APPDATA", "C:\\Users\\Test\\AppData\\Roaming")
    with mock.patch("sys.platform", "win32"):
        result = heretic_config_dir()
    assert "heretic" in result.parts
    # Must be derived from APPDATA — not a hardcoded absolute path constant
    assert str(result).startswith("C:\\Users\\Test")


def test_config_dir_windows_no_appdata(monkeypatch: pytest.MonkeyPatch) -> None:
    """On Windows without APPDATA, config dir falls back to home/AppData/Roaming."""
    monkeypatch.delenv("APPDATA", raising=False)
    with mock.patch("sys.platform", "win32"):
        result = heretic_config_dir()
    assert "heretic" in result.parts
    assert isinstance(result, Path)


def test_config_dir_macos() -> None:
    """On macOS (sys.platform=='darwin'), config dir uses ~/Library/Application Support."""
    with mock.patch("sys.platform", "darwin"):
        result = heretic_config_dir()
    assert "Library" in result.parts
    assert "Application Support" in result.parts
    assert "heretic" in result.parts


def test_config_dir_linux_xdg(monkeypatch: pytest.MonkeyPatch) -> None:
    """On Linux with XDG_CONFIG_HOME, config dir uses $XDG_CONFIG_HOME/heretic."""
    monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/config")
    with mock.patch("sys.platform", "linux"):
        result = heretic_config_dir()
    # Compare as Path to handle Windows forward/back slash normalization in tests
    assert result == Path("/custom/config/heretic")


def test_config_dir_linux_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """On Linux without XDG, config dir uses ~/.config/heretic."""
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    with mock.patch("sys.platform", "linux"):
        result = heretic_config_dir()
    assert ".config" in result.parts
    assert "heretic" in result.parts


# ---------------------------------------------------------------------------
# heretic_data_dir
# ---------------------------------------------------------------------------

def test_data_dir_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    """On Windows, data dir uses %LOCALAPPDATA%/heretic."""
    monkeypatch.setenv("LOCALAPPDATA", "C:\\Users\\Test\\AppData\\Local")
    with mock.patch("sys.platform", "win32"):
        result = heretic_data_dir()
    assert "heretic" in result.parts


def test_data_dir_macos() -> None:
    """On macOS, data dir uses ~/Library/Application Support/heretic/data."""
    with mock.patch("sys.platform", "darwin"):
        result = heretic_data_dir()
    assert "data" in result.parts
    assert "heretic" in result.parts


def test_data_dir_linux_xdg(monkeypatch: pytest.MonkeyPatch) -> None:
    """On Linux with XDG_DATA_HOME, data dir uses $XDG_DATA_HOME/heretic."""
    monkeypatch.setenv("XDG_DATA_HOME", "/custom/data")
    with mock.patch("sys.platform", "linux"):
        result = heretic_data_dir()
    assert result == Path("/custom/data/heretic")


# ---------------------------------------------------------------------------
# heretic_log_dir
# ---------------------------------------------------------------------------

def test_log_dir_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    """On Windows, log dir uses %LOCALAPPDATA%/heretic/logs."""
    monkeypatch.setenv("LOCALAPPDATA", "C:\\Users\\Test\\AppData\\Local")
    with mock.patch("sys.platform", "win32"):
        result = heretic_log_dir()
    assert "logs" in result.parts
    assert "heretic" in result.parts


def test_log_dir_macos() -> None:
    """On macOS, log dir uses ~/Library/Logs/heretic."""
    with mock.patch("sys.platform", "darwin"):
        result = heretic_log_dir()
    assert "Logs" in result.parts
    assert "heretic" in result.parts


# ---------------------------------------------------------------------------
# resolve_relative_path
# ---------------------------------------------------------------------------

def test_resolve_relative_path_tilde() -> None:
    """~-prefixed paths expand to the user's home directory."""
    result = resolve_relative_path("~/heretic_workspace")
    assert result.is_absolute()
    assert "heretic_workspace" in result.parts


def test_resolve_relative_path_relative(tmp_path: Path) -> None:
    """Relative paths are resolved against a supplied base directory."""
    result = resolve_relative_path("models/ggml-base.en.bin", base=tmp_path)
    assert result.is_absolute()
    assert result.parent == tmp_path / "models"


def test_resolve_relative_path_absolute_unchanged(tmp_path: Path) -> None:
    """Absolute paths are returned as-is (still wrapped in Path)."""
    abs_path = str(tmp_path / "models" / "ggml.bin")
    result = resolve_relative_path(abs_path)
    assert result.is_absolute()


# ---------------------------------------------------------------------------
# resolve_env_var
# ---------------------------------------------------------------------------

def test_resolve_env_var_simple(monkeypatch: pytest.MonkeyPatch) -> None:
    """${VAR} in a string is replaced with the env var value."""
    monkeypatch.setenv("HERETIC_AGENT_KEY", "my-secret-key")
    result = resolve_env_var("${HERETIC_AGENT_KEY}")
    assert result == "my-secret-key"


def test_resolve_env_var_multiple(monkeypatch: pytest.MonkeyPatch) -> None:
    """Multiple ${VAR} references in one string are all expanded."""
    monkeypatch.setenv("HOST", "localhost")
    monkeypatch.setenv("PORT", "8080")
    result = resolve_env_var("http://${HOST}:${PORT}/v1")
    assert result == "http://localhost:8080/v1"


def test_resolve_env_var_no_reference() -> None:
    """Strings with no ${...} pass through unchanged."""
    plain = "http://100.101.39.30:8643/v1"
    assert resolve_env_var(plain) == plain


def test_resolve_env_var_missing_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing env var raises EnvironmentError."""
    monkeypatch.delenv("HERETIC_AGENT_KEY", raising=False)
    with pytest.raises(EnvironmentError, match="HERETIC_AGENT_KEY"):
        resolve_env_var("${HERETIC_AGENT_KEY}")


# ---------------------------------------------------------------------------
# package_root
# ---------------------------------------------------------------------------

def test_package_root_is_absolute() -> None:
    """package_root() returns an absolute Path."""
    root = package_root()
    assert root.is_absolute()


def test_package_root_contains_heretic() -> None:
    """package_root() points to a directory that contains the heretic package files."""
    root = package_root()
    # In dev layout: src/heretic/; the __init__.py should be present
    assert (root / "__init__.py").exists()
