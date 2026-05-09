"""
Placeholder tests — McpServer class and convert_to_mcp_tool helper.

Scaffold state: McpServer.start(), handle_initialize(), handle_tools_list(),
and handle_tools_call() all raise NotImplementedError.  The tests that verify
those call paths are marked pytest.mark.skip until Forge implements the bodies.

convert_to_mcp_tool() IS implemented (pure dict reshape) and its tests run now.

Ref: src/heretic/skilningr/mcp_server.py
     src/heretic/skilningr/config_model.py (McpServerConfig)
     TASK_HERETIC_v0.6.x_MCP_SERVER.md
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# convert_to_mcp_tool — pure function; tests run now
# ---------------------------------------------------------------------------

class TestConvertToMcpTool:
    """convert_to_mcp_tool is a pure function — no stubs needed."""

    def test_valid_tool_minimal(self) -> None:
        from heretic.skilningr.mcp_server import convert_to_mcp_tool

        openai_tool = {
            "type": "function",
            "function": {
                "name": "smidja.screenshot",
                "description": "Capture the current screen state.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }
        result = convert_to_mcp_tool(openai_tool)
        assert result["name"] == "smidja.screenshot"
        assert result["description"] == "Capture the current screen state."
        assert result["inputSchema"] == openai_tool["function"]["parameters"]

    def test_valid_tool_with_properties(self) -> None:
        from heretic.skilningr.mcp_server import convert_to_mcp_tool

        params = {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X coordinate"},
                "y": {"type": "integer", "description": "Y coordinate"},
            },
            "required": ["x", "y"],
        }
        openai_tool = {
            "type": "function",
            "function": {
                "name": "smidja.click",
                "description": "Click at a screen position.",
                "parameters": params,
            },
        }
        result = convert_to_mcp_tool(openai_tool)
        assert result["name"] == "smidja.click"
        assert result["inputSchema"] is params

    def test_missing_description_defaults_empty_string(self) -> None:
        from heretic.skilningr.mcp_server import convert_to_mcp_tool

        openai_tool = {
            "type": "function",
            "function": {
                "name": "skepja.run_command",
                # description intentionally absent
            },
        }
        result = convert_to_mcp_tool(openai_tool)
        assert result["description"] == ""

    def test_not_a_dict_raises_type_error(self) -> None:
        from heretic.skilningr.mcp_server import convert_to_mcp_tool

        with pytest.raises(TypeError, match="expected dict"):
            convert_to_mcp_tool("not a dict")  # type: ignore[arg-type]

    def test_wrong_type_field_raises_value_error(self) -> None:
        from heretic.skilningr.mcp_server import convert_to_mcp_tool

        with pytest.raises(ValueError, match="type.*function"):
            convert_to_mcp_tool({"type": "unknown", "function": {}})

    def test_missing_function_key_raises_value_error(self) -> None:
        from heretic.skilningr.mcp_server import convert_to_mcp_tool

        with pytest.raises(ValueError, match="function.*must be a dict"):
            convert_to_mcp_tool({"type": "function", "function": None})

    def test_empty_name_raises_value_error(self) -> None:
        from heretic.skilningr.mcp_server import convert_to_mcp_tool

        with pytest.raises(ValueError, match="name.*non-empty string"):
            convert_to_mcp_tool({"type": "function", "function": {"name": ""}})

    def test_missing_parameters_defaults_empty_schema(self) -> None:
        from heretic.skilningr.mcp_server import convert_to_mcp_tool

        result = convert_to_mcp_tool(
            {"type": "function", "function": {"name": "leid.fetch_url"}}
        )
        assert result["inputSchema"] == {"type": "object", "properties": {}}


# ---------------------------------------------------------------------------
# McpServerConfig — validation; tests run now
# ---------------------------------------------------------------------------

class TestMcpServerConfig:
    """McpServerConfig is a plain dataclass — fully testable without mcp installed."""

    def test_default_config_valid(self) -> None:
        from heretic.skilningr.config_model import McpServerConfig

        cfg = McpServerConfig()
        assert cfg.enabled is False
        assert cfg.transport == "stdio"
        assert cfg.host == "127.0.0.1"
        assert cfg.port == 8643
        assert cfg.allow_remote_bind is False
        assert cfg.request_timeout_seconds == 60

    def test_invalid_transport_raises(self) -> None:
        from heretic.skilningr.config_model import McpServerConfig

        with pytest.raises(ValueError, match="transport"):
            McpServerConfig(transport="websocket")

    def test_port_too_low_raises(self) -> None:
        from heretic.skilningr.config_model import McpServerConfig

        with pytest.raises(ValueError, match="port"):
            McpServerConfig(port=0)

    def test_port_too_high_raises(self) -> None:
        from heretic.skilningr.config_model import McpServerConfig

        with pytest.raises(ValueError, match="port"):
            McpServerConfig(port=99999)

    def test_timeout_zero_raises(self) -> None:
        from heretic.skilningr.config_model import McpServerConfig

        with pytest.raises(ValueError, match="request_timeout_seconds"):
            McpServerConfig(request_timeout_seconds=0)

    def test_non_loopback_without_allow_remote_bind_raises(self) -> None:
        from heretic.skilningr.config_model import McpServerConfig

        with pytest.raises(ValueError, match="allow_remote_bind"):
            McpServerConfig(transport="http", host="0.0.0.0", allow_remote_bind=False)

    def test_non_loopback_with_allow_remote_bind_ok(self) -> None:
        from heretic.skilningr.config_model import McpServerConfig

        cfg = McpServerConfig(
            transport="http", host="100.101.39.30", allow_remote_bind=True
        )
        assert cfg.host == "100.101.39.30"

    def test_stdio_transport_ignores_remote_bind_gate(self) -> None:
        """stdio transport never opens a socket — remote bind gate should not fire."""
        from heretic.skilningr.config_model import McpServerConfig

        # stdio with a non-loopback host is not blocked — the host field is ignored
        # for stdio.  The gate only activates for transport="http".
        cfg = McpServerConfig(
            transport="stdio", host="10.0.0.1", allow_remote_bind=False
        )
        assert cfg.transport == "stdio"


# ---------------------------------------------------------------------------
# McpServer class — NotImplementedError stubs (skip until Forge fills bodies)
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="McpServer.start() not yet implemented — Forge milestone")
class TestMcpServerStart:
    """These tests verify the start() method once Forge implements it."""

    @pytest.mark.asyncio
    async def test_start_stdio_runs_until_eof(self) -> None:
        raise NotImplementedError("Forge implements this after start() body is live.")

    @pytest.mark.asyncio
    async def test_start_http_binds_loopback(self) -> None:
        raise NotImplementedError("Forge implements this after start() body is live.")

    @pytest.mark.asyncio
    async def test_start_http_rejects_non_loopback_without_flag(self) -> None:
        raise NotImplementedError("Forge implements this after start() body is live.")

    @pytest.mark.asyncio
    async def test_start_raises_import_error_without_mcp_extra(self) -> None:
        raise NotImplementedError("Forge implements this after start() body is live.")


@pytest.mark.skip(reason="McpServer.handle_tools_list() not yet implemented — Forge milestone")
class TestMcpServerHandleToolsList:
    """These tests verify handle_tools_list() once Forge implements it."""

    @pytest.mark.asyncio
    async def test_tools_list_returns_mcp_tool_objects(self) -> None:
        raise NotImplementedError("Forge implements this after handle_tools_list() is live.")

    @pytest.mark.asyncio
    async def test_tools_list_empty_dispatcher_returns_empty(self) -> None:
        raise NotImplementedError("Forge implements this after handle_tools_list() is live.")


@pytest.mark.skip(reason="McpServer.handle_tools_call() not yet implemented — Forge milestone")
class TestMcpServerHandleToolsCall:
    """These tests verify handle_tools_call() once Forge implements it."""

    @pytest.mark.asyncio
    async def test_call_tool_routes_through_dispatcher(self) -> None:
        raise NotImplementedError("Forge implements this after handle_tools_call() is live.")

    @pytest.mark.asyncio
    async def test_call_unknown_tool_returns_error_content(self) -> None:
        raise NotImplementedError("Forge implements this after handle_tools_call() is live.")
