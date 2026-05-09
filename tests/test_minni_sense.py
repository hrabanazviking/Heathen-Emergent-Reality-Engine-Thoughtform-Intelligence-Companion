"""
Tests for MinniSense — L5.1 filesystem sense orchestrator.

Covers:
    - Config validation
    - Sense lifecycle (open/close/is_available)
    - Tool definitions
    - dispatch_tool_call routing (mocked client)
    - Error handling (sandbox violations, file not found, etc. mapped to tool_result)
    - JSON argument parsing errors

Ref: src/heretic/skilningr/senses/minni/sense.py
     TASK_HERETIC_v0.6.2_MORE_SENSES.md
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from heretic.skilningr.config_model import MinniConfig
from heretic.skilningr.senses.minni.client import MinniClient
from heretic.skilningr.senses.minni.errors import (
    MinniFileNotFoundError,
    MinniSandboxViolation,
)
from heretic.skilningr.senses.minni.sense import MinniSense
from heretic.skilningr.senses.minni.tools import MINNI_TOOL_DEFINITIONS


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

class TestMinniSenseConfig:

    def test_minni_config_defaults_disabled(self):
        """MinniConfig defaults to enabled=False."""
        config = MinniConfig()
        assert config.enabled is False

    def test_minni_config_default_roots(self):
        """MinniConfig default allowed_roots contains the workspace path."""
        config = MinniConfig()
        assert len(config.allowed_roots) >= 1
        assert any("heretic_workspace" in r for r in config.allowed_roots)

    def test_minni_config_invalid_read_bytes_raises(self):
        """max_read_bytes <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="max_read_bytes"):
            MinniConfig(max_read_bytes=0)

    def test_minni_config_invalid_write_bytes_raises(self):
        """max_write_bytes <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="max_write_bytes"):
            MinniConfig(max_write_bytes=-1)


# ---------------------------------------------------------------------------
# Sense lifecycle
# ---------------------------------------------------------------------------

class TestMinniSenseLifecycle:

    @pytest.mark.asyncio
    async def test_sense_disabled_not_available(self):
        """A disabled MinniSense is not available."""
        config = MinniConfig(enabled=False)
        client = MinniClient(config)
        sense = MinniSense(config, client)
        await sense.open()
        assert sense.is_available is False

    @pytest.mark.asyncio
    async def test_sense_enabled_is_available(self):
        """An enabled MinniSense is available after open."""
        config = MinniConfig(enabled=True)
        client = MinniClient(config)
        sense = MinniSense(config, client)
        await sense.open()
        assert sense.is_available is True

    @pytest.mark.asyncio
    async def test_sense_close_marks_unavailable(self):
        """Closing a MinniSense marks it unavailable."""
        config = MinniConfig(enabled=True)
        client = MinniClient(config)
        sense = MinniSense(config, client)
        await sense.open()
        await sense.close()
        assert sense.is_available is False


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

class TestMinniSenseToolDefinitions:

    def test_tool_definitions_when_enabled(self):
        """tool_definitions returns 3 tools when enabled."""
        config = MinniConfig(enabled=True)
        client = MinniClient(config)
        sense = MinniSense(config, client)
        defs = sense.tool_definitions
        assert len(defs) == 3

    def test_tool_definitions_when_disabled(self):
        """tool_definitions returns empty list when disabled."""
        config = MinniConfig(enabled=False)
        client = MinniClient(config)
        sense = MinniSense(config, client)
        defs = sense.tool_definitions
        assert defs == []

    def test_tool_names_locked(self):
        """The three Minni tool names are locked as specified."""
        names = {t["function"]["name"] for t in MINNI_TOOL_DEFINITIONS}
        assert "minni.read_file" in names
        assert "minni.write_file" in names
        assert "minni.list_directory" in names


# ---------------------------------------------------------------------------
# dispatch_tool_call — happy path (mocked client)
# ---------------------------------------------------------------------------

class TestMinniSenseDispatch:

    def _make_tool_call(self, name: str, args: dict) -> dict:
        return {
            "id": "call_001",
            "function": {
                "name": name,
                "arguments": json.dumps(args),
            },
        }

    @pytest.mark.asyncio
    async def test_read_file_dispatch_success(self, tmp_path):
        """dispatch_tool_call routes minni.read_file to client and returns result."""
        config = MinniConfig(enabled=True, allowed_roots=[str(tmp_path)])
        mock_client = MagicMock(spec=MinniClient)
        mock_client.read_file.return_value = {
            "path": str(tmp_path / "notes.md"),
            "content": "hello",
            "size_bytes": 5,
            "encoding": "utf-8",
        }
        sense = MinniSense(config, mock_client)
        await sense.open()
        tool_call = self._make_tool_call("minni.read_file", {"path": str(tmp_path / "notes.md")})
        result = await sense.dispatch_tool_call(tool_call)
        assert result["role"] == "tool"
        parsed = json.loads(result["content"])
        assert parsed["content"] == "hello"

    @pytest.mark.asyncio
    async def test_write_file_dispatch_success(self, tmp_path):
        """dispatch_tool_call routes minni.write_file to client and returns result."""
        config = MinniConfig(enabled=True, allowed_roots=[str(tmp_path)])
        mock_client = MagicMock(spec=MinniClient)
        mock_client.write_file.return_value = {
            "path": str(tmp_path / "out.txt"),
            "bytes_written": 5,
            "created": True,
        }
        sense = MinniSense(config, mock_client)
        await sense.open()
        tool_call = self._make_tool_call(
            "minni.write_file",
            {"path": str(tmp_path / "out.txt"), "content": "hello"}
        )
        result = await sense.dispatch_tool_call(tool_call)
        assert result["role"] == "tool"
        parsed = json.loads(result["content"])
        assert parsed["created"] is True

    @pytest.mark.asyncio
    async def test_list_directory_dispatch_success(self, tmp_path):
        """dispatch_tool_call routes minni.list_directory to client and returns result."""
        config = MinniConfig(enabled=True, allowed_roots=[str(tmp_path)])
        mock_client = MagicMock(spec=MinniClient)
        mock_client.list_directory.return_value = {
            "path": str(tmp_path),
            "entries": [],
            "recurse": False,
            "total_entries": 0,
        }
        sense = MinniSense(config, mock_client)
        await sense.open()
        tool_call = self._make_tool_call("minni.list_directory", {"path": str(tmp_path)})
        result = await sense.dispatch_tool_call(tool_call)
        assert result["role"] == "tool"
        parsed = json.loads(result["content"])
        assert parsed["total_entries"] == 0

    @pytest.mark.asyncio
    async def test_sandbox_violation_returns_error_result(self, tmp_path):
        """dispatch_tool_call returns error tool_result on MinniSandboxViolation."""
        config = MinniConfig(enabled=True, allowed_roots=[str(tmp_path)])
        mock_client = MagicMock(spec=MinniClient)
        mock_client.read_file.side_effect = MinniSandboxViolation("access denied")
        sense = MinniSense(config, mock_client)
        await sense.open()
        tool_call = self._make_tool_call("minni.read_file", {"path": "/etc/passwd"})
        result = await sense.dispatch_tool_call(tool_call)
        assert result["role"] == "tool"
        parsed = json.loads(result["content"])
        assert parsed["error"] is True
        assert parsed["code"] == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_file_not_found_returns_error_result(self, tmp_path):
        """dispatch_tool_call returns error tool_result on MinniFileNotFoundError."""
        config = MinniConfig(enabled=True, allowed_roots=[str(tmp_path)])
        mock_client = MagicMock(spec=MinniClient)
        mock_client.read_file.side_effect = MinniFileNotFoundError("not found")
        sense = MinniSense(config, mock_client)
        await sense.open()
        tool_call = self._make_tool_call("minni.read_file", {"path": str(tmp_path / "missing.txt")})
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["error"] is True
        assert "sense" in parsed

    @pytest.mark.asyncio
    async def test_invalid_json_args_returns_error_result(self):
        """dispatch_tool_call returns error result when arguments are invalid JSON."""
        config = MinniConfig(enabled=True)
        mock_client = MagicMock(spec=MinniClient)
        sense = MinniSense(config, mock_client)
        await sense.open()
        bad_call = {
            "id": "call_bad",
            "function": {"name": "minni.read_file", "arguments": "{not valid json"},
        }
        result = await sense.dispatch_tool_call(bad_call)
        parsed = json.loads(result["content"])
        assert parsed["error"] is True
        assert parsed["code"] == "INVALID_ARGUMENTS"

    @pytest.mark.asyncio
    async def test_unknown_tool_name_returns_error_result(self):
        """dispatch_tool_call returns error result for unknown tool names."""
        config = MinniConfig(enabled=True)
        mock_client = MagicMock(spec=MinniClient)
        sense = MinniSense(config, mock_client)
        await sense.open()
        tool_call = {
            "id": "call_x",
            "function": {"name": "minni.nonexistent_tool", "arguments": "{}"},
        }
        result = await sense.dispatch_tool_call(tool_call)
        parsed = json.loads(result["content"])
        assert parsed["error"] is True
