"""
Tests for SkepjaSense — L5.2 terminal sense orchestrator.

Covers:
    - Config validation
    - Sense lifecycle (open/close/is_available)
    - Tool definitions
    - dispatch_tool_call routing (mocked client)
    - Error handling (CommandNotAllowedError, CommandTimeoutError, etc.)
    - JSON argument errors

Ref: src/heretic/skilningr/senses/skepja/sense.py
     TASK_HERETIC_v0.6.2_MORE_SENSES.md
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from heretic.skilningr.config_model import SkepjaConfig
from heretic.skilningr.senses.skepja.client import SkepjaClient
from heretic.skilningr.senses.skepja.errors import (
    CommandNotAllowedError,
    CommandTimeoutError,
)
from heretic.skilningr.senses.skepja.sense import SkepjaSense
from heretic.skilningr.senses.skepja.tools import SKEPJA_TOOL_DEFINITIONS


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

class TestSkepjaConfig:

    def test_skepja_config_defaults_disabled(self):
        """SkepjaConfig defaults to enabled=False."""
        config = SkepjaConfig()
        assert config.enabled is False

    def test_skepja_config_default_allowlist_empty(self):
        """SkepjaConfig default command_allowlist is empty."""
        config = SkepjaConfig()
        assert config.command_allowlist == []

    def test_skepja_config_invalid_timeout_raises(self):
        """timeout_seconds <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="timeout_seconds"):
            SkepjaConfig(timeout_seconds=0)

    def test_skepja_config_invalid_output_bytes_raises(self):
        """max_output_bytes <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="max_output_bytes"):
            SkepjaConfig(max_output_bytes=-1)


# ---------------------------------------------------------------------------
# Sense lifecycle
# ---------------------------------------------------------------------------

class TestSkepjaSenseLifecycle:

    @pytest.mark.asyncio
    async def test_sense_disabled_not_available(self):
        """A disabled SkepjaSense is not available."""
        config = SkepjaConfig(enabled=False)
        client = SkepjaClient(config)
        sense = SkepjaSense(config, client)
        await sense.open()
        assert sense.is_available is False

    @pytest.mark.asyncio
    async def test_sense_enabled_is_available(self):
        """An enabled SkepjaSense is available after open."""
        config = SkepjaConfig(enabled=True)
        client = SkepjaClient(config)
        sense = SkepjaSense(config, client)
        await sense.open()
        assert sense.is_available is True

    @pytest.mark.asyncio
    async def test_sense_close_marks_unavailable(self):
        """Closing a SkepjaSense marks it unavailable."""
        config = SkepjaConfig(enabled=True)
        client = SkepjaClient(config)
        sense = SkepjaSense(config, client)
        await sense.open()
        await sense.close()
        assert sense.is_available is False


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

class TestSkepjaSenseToolDefinitions:

    def test_tool_definitions_when_enabled(self):
        """tool_definitions returns 2 tools when enabled."""
        config = SkepjaConfig(enabled=True)
        client = SkepjaClient(config)
        sense = SkepjaSense(config, client)
        assert len(sense.tool_definitions) == 2

    def test_tool_definitions_when_disabled(self):
        """tool_definitions returns empty list when disabled."""
        config = SkepjaConfig(enabled=False)
        client = SkepjaClient(config)
        sense = SkepjaSense(config, client)
        assert sense.tool_definitions == []

    def test_tool_names_locked(self):
        """The two Skepja tool names are locked as specified."""
        names = {t["function"]["name"] for t in SKEPJA_TOOL_DEFINITIONS}
        assert "skepja.run_command" in names
        assert "skepja.get_working_directory" in names


# ---------------------------------------------------------------------------
# dispatch_tool_call — happy path and error paths (mocked client)
# ---------------------------------------------------------------------------

class TestSkepjaSenseDispatch:

    def _make_tool_call(self, name: str, args: dict) -> dict:
        return {
            "id": "call_s01",
            "function": {
                "name": name,
                "arguments": json.dumps(args),
            },
        }

    @pytest.mark.asyncio
    async def test_run_command_dispatch_success(self):
        """dispatch_tool_call routes skepja.run_command and returns result."""
        config = SkepjaConfig(enabled=True, command_allowlist=["git"])
        mock_client = MagicMock(spec=SkepjaClient)
        mock_client.run_command.return_value = {
            "command": "git status",
            "args": ["git", "status"],
            "exit_code": 0,
            "stdout": "on branch main\n",
            "stderr": "",
            "timed_out": False,
            "truncated": False,
            "working_directory": "/home/user/workspace",
        }
        sense = SkepjaSense(config, mock_client)
        await sense.open()
        tool_call = self._make_tool_call("skepja.run_command", {"command": "git status"})
        result = await sense.dispatch_tool_call(tool_call)
        assert result["role"] == "tool"
        parsed = json.loads(result["content"])
        assert parsed["exit_code"] == 0
        assert "main" in parsed["stdout"]

    @pytest.mark.asyncio
    async def test_get_working_directory_dispatch(self):
        """dispatch_tool_call routes skepja.get_working_directory and returns result."""
        config = SkepjaConfig(enabled=True)
        mock_client = MagicMock(spec=SkepjaClient)
        mock_client.get_working_directory.return_value = {
            "working_directory": "/home/user/heretic_workspace",
            "exists": True,
        }
        sense = SkepjaSense(config, mock_client)
        await sense.open()
        tool_call = self._make_tool_call("skepja.get_working_directory", {})
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["exists"] is True

    @pytest.mark.asyncio
    async def test_command_not_allowed_returns_error_result(self):
        """dispatch_tool_call returns error tool_result on CommandNotAllowedError."""
        config = SkepjaConfig(enabled=True, command_allowlist=["git"])
        mock_client = MagicMock(spec=SkepjaClient)
        mock_client.run_command.side_effect = CommandNotAllowedError("rm not permitted")
        sense = SkepjaSense(config, mock_client)
        await sense.open()
        tool_call = self._make_tool_call("skepja.run_command", {"command": "rm -rf /"})
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["error"] is True
        assert parsed["code"] == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_command_timeout_returns_error_result(self):
        """dispatch_tool_call returns error tool_result on CommandTimeoutError."""
        config = SkepjaConfig(enabled=True, command_allowlist=["sleep"])
        mock_client = MagicMock(spec=SkepjaClient)
        mock_client.run_command.side_effect = CommandTimeoutError("timed out")
        sense = SkepjaSense(config, mock_client)
        await sense.open()
        tool_call = self._make_tool_call("skepja.run_command", {"command": "sleep 999"})
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["error"] is True
        assert parsed["code"] == "SENSE_TIMEOUT"

    @pytest.mark.asyncio
    async def test_invalid_json_args_returns_error_result(self):
        """dispatch_tool_call returns error result when arguments are invalid JSON."""
        config = SkepjaConfig(enabled=True)
        mock_client = MagicMock(spec=SkepjaClient)
        sense = SkepjaSense(config, mock_client)
        await sense.open()
        bad_call = {
            "id": "call_bad",
            "function": {"name": "skepja.run_command", "arguments": "{bad json"},
        }
        result = await sense.dispatch_tool_call(bad_call)
        parsed = json.loads(result["content"])
        assert parsed["error"] is True
        assert parsed["code"] == "INVALID_ARGUMENTS"
