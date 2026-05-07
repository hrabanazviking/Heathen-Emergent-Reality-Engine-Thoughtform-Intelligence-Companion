"""
Tests for heretic.cli — CLI command dispatch, version output, status, and help.

Does not invoke any real network — all tests use either --version/version
(pure Python, no I/O) or mock config paths.
"""

from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path
from unittest import mock

import pytest

from heretic.cli import build_parser, _cmd_version, _cmd_extinguish, _cmd_status, _get_version


# ---------------------------------------------------------------------------
# version command
# ---------------------------------------------------------------------------

def test_version_command_prints_version(capsys: pytest.CaptureFixture) -> None:
    """'heretic version' prints the package version string and exits 0."""
    parser = build_parser()
    args = parser.parse_args(["version"])
    exit_code = args.func(args)
    captured = capsys.readouterr()
    assert "0.1.0" in captured.out
    assert exit_code == 0


def test_get_version_is_semver() -> None:
    """_get_version() returns a string matching a semver-like pattern."""
    import re
    version = _get_version()
    assert re.match(r"\d+\.\d+\.\d+", version), f"Not semver-like: {version!r}"


def test_version_matches_package_version() -> None:
    """CLI version output matches heretic.__version__."""
    import heretic
    assert _get_version() == heretic.__version__


# ---------------------------------------------------------------------------
# --help flag — no exception
# ---------------------------------------------------------------------------

def test_help_flag_exits_cleanly() -> None:
    """heretic --help triggers SystemExit(0) — argparse standard behaviour."""
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--help"])
    assert exc_info.value.code == 0


def test_version_subcommand_help() -> None:
    """heretic version --help works without crashing."""
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["version", "--help"])
    assert exc_info.value.code == 0


def test_light_subcommand_help() -> None:
    """heretic light --help works without crashing."""
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["light", "--help"])
    assert exc_info.value.code == 0


# ---------------------------------------------------------------------------
# extinguish command — no-op in v0.1
# ---------------------------------------------------------------------------

def test_extinguish_returns_zero(capsys: pytest.CaptureFixture) -> None:
    """'heretic extinguish' returns 0 (no-op in v0.1, explains daemon not running)."""
    parser = build_parser()
    args = parser.parse_args(["extinguish"])
    exit_code = args.func(args)
    assert exit_code == 0
    captured = capsys.readouterr()
    # Should mention v0.1 limitation
    assert "v0.1" in captured.err or "no running" in captured.err.lower()


# ---------------------------------------------------------------------------
# status command — no live daemon in v0.1
# ---------------------------------------------------------------------------

def test_status_with_missing_config_runs(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """'heretic status' runs without crashing even if heretic.yaml is absent."""
    missing = tmp_path / "heretic.yaml"
    parser = build_parser()
    args = parser.parse_args(["--config", str(missing), "status"])
    exit_code = args.func(args)
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "HVILD" in captured.out or "Status" in captured.out


def test_status_with_valid_config(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """'heretic status' reports agent endpoint when config is valid."""
    config_file = tmp_path / "heretic.yaml"
    config_file.write_text(
        'grunnr:\n  config_version: "1"\nbifrost:\n  endpoint: "http://test.agent/v1"\n',
        encoding="utf-8",
    )
    parser = build_parser()
    args = parser.parse_args(["--config", str(config_file), "status"])
    exit_code = args.func(args)
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "http://test.agent/v1" in captured.out


# ---------------------------------------------------------------------------
# Parser structure tests
# ---------------------------------------------------------------------------

def test_parser_has_required_subcommands() -> None:
    """Parser exposes light, extinguish, status, version subcommands."""
    parser = build_parser()
    # Each subcommand should parse without error
    for cmd in ("version", "extinguish"):
        args = parser.parse_args([cmd])
        assert hasattr(args, "func")


def test_parser_config_flag() -> None:
    """--config flag is accepted by the top-level parser."""
    parser = build_parser()
    args = parser.parse_args(["--config", "/some/path/heretic.yaml", "version"])
    assert args.config == "/some/path/heretic.yaml"


def test_parser_debug_flag() -> None:
    """--debug flag is accepted by the top-level parser."""
    parser = build_parser()
    args = parser.parse_args(["--debug", "version"])
    assert args.debug is True


def test_parser_no_subcommand_required() -> None:
    """Calling heretic with no subcommand raises SystemExit (argparse enforces required)."""
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])
