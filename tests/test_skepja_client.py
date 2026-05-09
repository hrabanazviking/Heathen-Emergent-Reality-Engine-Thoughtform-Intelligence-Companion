"""
Tests for SkepjaClient — sandboxed subprocess execution.

Covers:
    - Allowlist gateway (_validate_command)
    - run_command: happy path, allowlist rejection, timeout, output truncation,
                   env inheritance OFF default, FileNotFoundError mapping,
                   cwd validation, non-zero exit code
    - get_working_directory: resolution and existence check

All subprocess.run calls are mocked — no real subprocess execution occurs.

Ref: src/heretic/skilningr/senses/skepja/client.py
     TASK_HERETIC_v0.6.2_MORE_SENSES.md §3
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from heretic.skilningr.config_model import SkepjaConfig
from heretic.skilningr.senses.skepja.client import SkepjaClient
from heretic.skilningr.senses.skepja.errors import (
    CommandExecutionError,
    CommandNotAllowedError,
    CommandParseError,
    CommandTimeoutError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_proc(
    returncode: int = 0,
    stdout: bytes = b"",
    stderr: bytes = b"",
) -> MagicMock:
    """Return a mock CompletedProcess."""
    mock = MagicMock()
    mock.returncode = returncode
    mock.stdout = stdout
    mock.stderr = stderr
    return mock


# ---------------------------------------------------------------------------
# Allowlist gateway — _validate_command
# ---------------------------------------------------------------------------

class TestSkepjaClientAllowlistGateway:

    def test_validate_command_accepted(self):
        """_validate_command accepts a command whose executable is in the allowlist."""
        config = SkepjaConfig(command_allowlist=["git"])
        client = SkepjaClient(config)
        tokens = client._validate_command("git status")
        assert tokens[0] == "git"
        assert "status" in tokens

    def test_validate_command_not_in_allowlist_raises(self):
        """_validate_command raises CommandNotAllowedError for unlisted executables."""
        config = SkepjaConfig(command_allowlist=["git"])
        client = SkepjaClient(config)
        with pytest.raises(CommandNotAllowedError):
            client._validate_command("rm -rf /")

    def test_validate_command_empty_allowlist_raises(self):
        """_validate_command raises when allowlist is empty."""
        config = SkepjaConfig(command_allowlist=[])
        client = SkepjaClient(config)
        with pytest.raises(CommandNotAllowedError):
            client._validate_command("git status")

    def test_validate_command_returns_token_list(self):
        """_validate_command returns the parsed token list."""
        config = SkepjaConfig(command_allowlist=["python"])
        client = SkepjaClient(config)
        tokens = client._validate_command("python -m pytest tests/")
        assert tokens == ["python", "-m", "pytest", "tests/"]

    def test_validate_command_malformed_quoting_raises(self):
        """_validate_command raises CommandParseError on malformed shell quoting."""
        config = SkepjaConfig(command_allowlist=["git"])
        client = SkepjaClient(config)
        # Unclosed quote — shlex will raise ValueError on POSIX; may vary on Windows
        with pytest.raises((CommandParseError, CommandNotAllowedError)):
            client._validate_command("git 'unclosed")


# ---------------------------------------------------------------------------
# run_command
# ---------------------------------------------------------------------------

class TestSkepjaClientRunCommand:

    def test_run_allowed_command_success(self, tmp_path):
        """run_command returns structured result for an allowed, successful command."""
        config = SkepjaConfig(
            command_allowlist=["git"],
            working_directory=str(tmp_path),
        )
        client = SkepjaClient(config)
        mock_proc = make_proc(returncode=0, stdout=b"on branch main\n", stderr=b"")
        with patch("subprocess.run", return_value=mock_proc):
            result = client.run_command("git status")
        assert result["exit_code"] == 0
        assert "main" in result["stdout"]
        assert result["timed_out"] is False
        assert result["truncated"] is False
        assert result["command"] == "git status"

    def test_run_command_rejected_by_allowlist(self, tmp_path):
        """run_command raises CommandNotAllowedError for non-allowlisted command."""
        config = SkepjaConfig(
            command_allowlist=["git"],
            working_directory=str(tmp_path),
        )
        client = SkepjaClient(config)
        with pytest.raises(CommandNotAllowedError):
            client.run_command("rm -rf /")

    def test_run_command_timeout_raises(self, tmp_path):
        """run_command raises CommandTimeoutError when subprocess times out."""
        config = SkepjaConfig(
            command_allowlist=["sleep"],
            working_directory=str(tmp_path),
            timeout_seconds=5,
        )
        client = SkepjaClient(config)
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["sleep", "100"], timeout=5)
        ):
            with pytest.raises(CommandTimeoutError):
                client.run_command("sleep 100")

    def test_run_command_output_truncation(self, tmp_path):
        """run_command truncates stdout/stderr at max_output_bytes."""
        config = SkepjaConfig(
            command_allowlist=["echo"],
            working_directory=str(tmp_path),
            max_output_bytes=10,
        )
        client = SkepjaClient(config)
        big_output = b"x" * 1000
        mock_proc = make_proc(returncode=0, stdout=big_output, stderr=b"")
        with patch("subprocess.run", return_value=mock_proc):
            result = client.run_command("echo hello")
        assert len(result["stdout"]) <= 10
        assert result["truncated"] is True

    def test_run_command_env_not_inherited_by_default(self, tmp_path):
        """run_command does not inherit full env when inherit_env=False (default)."""
        config = SkepjaConfig(
            command_allowlist=["env"],
            working_directory=str(tmp_path),
            inherit_env=False,
        )
        client = SkepjaClient(config)
        mock_proc = make_proc(returncode=0, stdout=b"PATH=/usr/bin\n", stderr=b"")
        captured_env = {}

        def capture_run(*args, **kwargs):
            captured_env.update(kwargs.get("env", {}))
            return mock_proc

        with patch("subprocess.run", side_effect=capture_run):
            client.run_command("env")

        # Should only contain PATH, not arbitrary host env vars
        assert "PATH" in captured_env
        # SECRET_TOKEN or similar should not leak (we check there are very few keys)
        assert len(captured_env) == 1

    def test_run_command_file_not_found_mapped(self, tmp_path):
        """run_command maps FileNotFoundError to CommandExecutionError."""
        config = SkepjaConfig(
            command_allowlist=["nonexistent_binary"],
            working_directory=str(tmp_path),
        )
        client = SkepjaClient(config)
        with patch("subprocess.run", side_effect=FileNotFoundError("not found")):
            with pytest.raises(CommandExecutionError, match="not found on PATH"):
                client.run_command("nonexistent_binary --help")

    def test_run_command_invalid_cwd_raises(self, tmp_path):
        """run_command raises CommandExecutionError when working_directory does not exist."""
        config = SkepjaConfig(
            command_allowlist=["git"],
            working_directory=str(tmp_path / "nonexistent_dir"),
        )
        client = SkepjaClient(config)
        with pytest.raises(CommandExecutionError, match="does not exist"):
            client.run_command("git status")

    def test_run_command_non_zero_exit_still_returns(self, tmp_path):
        """run_command returns result dict even on non-zero exit code."""
        config = SkepjaConfig(
            command_allowlist=["git"],
            working_directory=str(tmp_path),
        )
        client = SkepjaClient(config)
        mock_proc = make_proc(returncode=1, stdout=b"", stderr=b"error: not a git repo\n")
        with patch("subprocess.run", return_value=mock_proc):
            result = client.run_command("git status")
        assert result["exit_code"] == 1
        assert "git repo" in result["stderr"]

    def test_run_command_shell_false_invariant(self, tmp_path):
        """subprocess.run is called with shell=False invariant."""
        config = SkepjaConfig(
            command_allowlist=["echo"],
            working_directory=str(tmp_path),
        )
        client = SkepjaClient(config)
        mock_proc = make_proc(returncode=0, stdout=b"hi\n", stderr=b"")
        with patch("subprocess.run", return_value=mock_proc) as mock_run:
            client.run_command("echo hi")
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs.get("shell") is False


# ---------------------------------------------------------------------------
# get_working_directory
# ---------------------------------------------------------------------------

class TestSkepjaClientGetWorkingDirectory:

    def test_returns_resolved_path(self, tmp_path):
        """get_working_directory returns the resolved absolute path."""
        config = SkepjaConfig(
            command_allowlist=[],
            working_directory=str(tmp_path),
        )
        client = SkepjaClient(config)
        result = client.get_working_directory()
        assert Path(result["working_directory"]).is_absolute()
        assert result["exists"] is True

    def test_returns_exists_false_for_missing_dir(self, tmp_path):
        """get_working_directory reports exists=False for a non-existent dir."""
        config = SkepjaConfig(
            command_allowlist=[],
            working_directory=str(tmp_path / "not_here"),
        )
        client = SkepjaClient(config)
        result = client.get_working_directory()
        assert result["exists"] is False
