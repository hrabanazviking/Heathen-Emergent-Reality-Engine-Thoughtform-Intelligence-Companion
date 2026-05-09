"""
Placeholder tests for SkepjaClient — sandboxed command execution.

Ref: src/heretic/skilningr/senses/skepja/client.py
"""

from __future__ import annotations

import pytest

from heretic.skilningr.config_model import SkepjaConfig
from heretic.skilningr.senses.skepja.client import SkepjaClient
from heretic.skilningr.senses.skepja.errors import (
    CommandNotAllowedError,
    CommandParseError,
)


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

    def test_validate_command_malformed_quoting_raises(self):
        """_validate_command raises CommandParseError on malformed shell quoting."""
        config = SkepjaConfig(command_allowlist=["git"])
        client = SkepjaClient(config)
        with pytest.raises((CommandParseError, CommandNotAllowedError)):
            # Unclosed quote — shlex will raise ValueError
            client._validate_command("git 'unclosed")


@pytest.mark.skip(reason="Wave 2 — SkepjaClient.run_command not yet implemented by Forge")
class TestSkepjaClientRunCommand:

    def test_run_allowed_command(self):
        pass

    def test_run_command_timeout(self):
        pass

    def test_run_command_output_truncation(self):
        pass


@pytest.mark.skip(reason="Wave 2 — SkepjaClient.get_working_directory not yet implemented by Forge")
class TestSkepjaClientGetWorkingDirectory:

    def test_returns_resolved_path(self):
        pass
