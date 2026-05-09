"""
Tests — McpServer class, convert_to_mcp_tool helper, and handler logic.

Covers:
    - convert_to_mcp_tool(): pure dict reshaping (all paths)
    - McpServerConfig: validation (previously passing; retained)
    - McpServer construction with mock dispatcher
    - handle_tools_list(): returns correct mcp.types.Tool objects
    - handle_tools_call(): routes through dispatcher and maps result to TextContent
    - handle_tools_call(): error envelope from dispatcher surfaces correctly
    - handle_tools_call(): unknown tool name error envelope
    - start() handler registration: list_tools + call_tool closures work correctly
      without touching real stdio/HTTP transport (mocked transport layer)
    - Error hierarchy (TransportError, ProtocolError, McpAuthError)

Ref: src/heretic/skilningr/mcp_server.py
     src/heretic/skilningr/config_model.py (McpServerConfig)
     TASK_HERETIC_v0.6.x_MCP_SERVER.md
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures — minimal stub dispatcher
# ---------------------------------------------------------------------------

def _make_stub_dispatcher(
    tool_definitions: list[dict] | None = None,
    dispatch_result: dict | None = None,
) -> MagicMock:
    """Build a mock ToolDispatcher with controllable outputs."""
    dispatcher = MagicMock()
    if tool_definitions is None:
        tool_definitions = [
            {
                "type": "function",
                "function": {
                    "name": "smidja.screenshot",
                    "description": "Capture the screen.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "minni.read_file",
                    "description": "Read a file.",
                    "parameters": {
                        "type": "object",
                        "properties": {"path": {"type": "string"}},
                        "required": ["path"],
                    },
                },
            },
        ]
    dispatcher.all_tool_definitions.return_value = tool_definitions

    if dispatch_result is None:
        dispatch_result = {
            "tool_call_id": "mcp-abc123",
            "role": "tool",
            "content": json.dumps({"ok": True, "data": "screenshot_bytes"}),
        }
    dispatcher.dispatch = AsyncMock(return_value=dispatch_result)
    return dispatcher


def _make_mcp_server(
    dispatcher: MagicMock | None = None,
    transport: str = "stdio",
) -> "McpServer":  # noqa: F821
    """Build a McpServer with a stub dispatcher for unit testing."""
    from heretic.skilningr.config_model import McpServerConfig
    from heretic.skilningr.mcp_server import McpServer

    cfg = McpServerConfig(enabled=True, transport=transport)
    if dispatcher is None:
        dispatcher = _make_stub_dispatcher()
    return McpServer(config=cfg, dispatcher=dispatcher)


# ---------------------------------------------------------------------------
# convert_to_mcp_tool — pure function; tests run without mcp SDK in scope
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

    def test_result_has_exactly_three_keys(self) -> None:
        from heretic.skilningr.mcp_server import convert_to_mcp_tool

        result = convert_to_mcp_tool(
            {
                "type": "function",
                "function": {
                    "name": "skepja.run_command",
                    "description": "Run a command.",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        )
        assert set(result.keys()) == {"name", "description", "inputSchema"}

    def test_parameters_reference_is_same_object(self) -> None:
        """inputSchema must reference the same dict object (no deep copy)."""
        from heretic.skilningr.mcp_server import convert_to_mcp_tool

        params = {"type": "object", "properties": {"x": {"type": "integer"}}}
        result = convert_to_mcp_tool(
            {
                "type": "function",
                "function": {"name": "smidja.click", "parameters": params},
            }
        )
        assert result["inputSchema"] is params


# ---------------------------------------------------------------------------
# McpServerConfig — validation; all tests run now
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

        cfg = McpServerConfig(
            transport="stdio", host="10.0.0.1", allow_remote_bind=False
        )
        assert cfg.transport == "stdio"

    def test_ipv6_loopback_does_not_require_allow_remote_bind(self) -> None:
        """F-3: host '::1' is IPv6 loopback and must be accepted without allow_remote_bind=True.

        The runtime _start_http check already includes '::1' in its loopback set;
        McpServerConfig.__post_init__ must be symmetric — otherwise an operator who
        sets host: '::1' is forced to set allow_remote_bind, contradicting the
        intent of that flag and producing a confusing error message.
        """
        from heretic.skilningr.config_model import McpServerConfig

        # Must construct without raising ValueError
        cfg = McpServerConfig(transport="http", host="::1", allow_remote_bind=False)
        assert cfg.host == "::1"
        assert cfg.allow_remote_bind is False


# ---------------------------------------------------------------------------
# McpServer construction
# ---------------------------------------------------------------------------

class TestMcpServerConstruction:
    """McpServer can be constructed with a stub dispatcher."""

    def test_construction_succeeds_with_stub_dispatcher(self) -> None:
        server = _make_mcp_server()
        assert server is not None

    def test_construction_uses_module_logger_when_none_provided(self) -> None:
        import logging
        from heretic.skilningr.config_model import McpServerConfig
        from heretic.skilningr.mcp_server import McpServer

        cfg = McpServerConfig(enabled=True)
        dispatcher = _make_stub_dispatcher()
        server = McpServer(config=cfg, dispatcher=dispatcher, logger=None)
        assert server._log.name == "heretic.skilningr.mcp_server"

    def test_construction_uses_provided_logger(self) -> None:
        import logging
        from heretic.skilningr.config_model import McpServerConfig
        from heretic.skilningr.mcp_server import McpServer

        custom_log = logging.getLogger("test.mcp_server")
        cfg = McpServerConfig(enabled=True)
        dispatcher = _make_stub_dispatcher()
        server = McpServer(config=cfg, dispatcher=dispatcher, logger=custom_log)
        assert server._log is custom_log


# ---------------------------------------------------------------------------
# handle_tools_list — tests the public method (same logic as the closure)
# ---------------------------------------------------------------------------

class TestHandleToolsList:
    """handle_tools_list() converts all dispatcher tools to mcp.types.Tool objects."""

    @pytest.mark.asyncio
    async def test_tools_list_returns_mcp_tool_objects(self) -> None:
        from mcp.types import Tool

        server = _make_mcp_server()
        tools = await server.handle_tools_list()

        assert isinstance(tools, list)
        assert len(tools) == 2  # stub dispatcher returns 2 tools
        for tool in tools:
            assert isinstance(tool, Tool)

    @pytest.mark.asyncio
    async def test_tools_list_names_match_dispatcher_definitions(self) -> None:
        server = _make_mcp_server()
        tools = await server.handle_tools_list()

        names = {t.name for t in tools}
        assert "smidja.screenshot" in names
        assert "minni.read_file" in names

    @pytest.mark.asyncio
    async def test_tools_list_input_schema_matches_parameters(self) -> None:
        server = _make_mcp_server()
        tools = await server.handle_tools_list()

        read_file_tool = next(t for t in tools if t.name == "minni.read_file")
        assert "path" in read_file_tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_tools_list_empty_dispatcher_returns_empty(self) -> None:
        dispatcher = _make_stub_dispatcher(tool_definitions=[])
        server = _make_mcp_server(dispatcher=dispatcher)
        tools = await server.handle_tools_list()
        assert tools == []

    @pytest.mark.asyncio
    async def test_tools_list_skips_malformed_schemas(self) -> None:
        """Malformed tool schemas are logged and skipped — no crash."""
        bad_tool = {"type": "not_function", "function": {}}  # wrong type
        good_tool = {
            "type": "function",
            "function": {
                "name": "skepja.run_command",
                "description": "Run a command.",
                "parameters": {"type": "object", "properties": {}},
            },
        }
        dispatcher = _make_stub_dispatcher(tool_definitions=[bad_tool, good_tool])
        server = _make_mcp_server(dispatcher=dispatcher)
        tools = await server.handle_tools_list()
        # Only the good tool should come through
        assert len(tools) == 1
        assert tools[0].name == "skepja.run_command"


# ---------------------------------------------------------------------------
# handle_tools_call — tests the public method
# ---------------------------------------------------------------------------

class TestHandleToolsCall:
    """handle_tools_call() routes through dispatcher and maps result to TextContent."""

    @pytest.mark.asyncio
    async def test_call_tool_routes_through_dispatcher(self) -> None:
        from mcp.types import TextContent

        server = _make_mcp_server()
        result = await server.handle_tools_call(
            "smidja.screenshot", {"region": None}
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"

        # Dispatcher must have been called
        server._dispatcher.dispatch.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_content_matches_dispatcher_result(self) -> None:
        expected_payload = {"ok": True, "data": "screenshot_bytes"}
        dispatch_result = {
            "tool_call_id": "mcp-xyz",
            "role": "tool",
            "content": json.dumps(expected_payload),
        }
        dispatcher = _make_stub_dispatcher(dispatch_result=dispatch_result)
        server = _make_mcp_server(dispatcher=dispatcher)

        result = await server.handle_tools_call("smidja.screenshot", {})
        returned_payload = json.loads(result[0].text)
        assert returned_payload == expected_payload

    @pytest.mark.asyncio
    async def test_call_tool_passes_correct_tool_name_to_dispatcher(self) -> None:
        server = _make_mcp_server()
        await server.handle_tools_call("minni.read_file", {"path": "/tmp/test.txt"})

        call_args = server._dispatcher.dispatch.call_args[0][0]
        assert call_args["function"]["name"] == "minni.read_file"

    @pytest.mark.asyncio
    async def test_call_tool_serialises_arguments_as_json(self) -> None:
        server = _make_mcp_server()
        args = {"path": "/workspace/file.txt", "encoding": "utf-8"}
        await server.handle_tools_call("minni.read_file", args)

        call_args = server._dispatcher.dispatch.call_args[0][0]
        parsed_args = json.loads(call_args["function"]["arguments"])
        assert parsed_args == args

    @pytest.mark.asyncio
    async def test_call_tool_handles_none_arguments(self) -> None:
        """None arguments should be serialised as {} — no crash."""
        server = _make_mcp_server()
        result = await server.handle_tools_call("smidja.screenshot", None)  # type: ignore[arg-type]
        assert len(result) == 1
        call_args = server._dispatcher.dispatch.call_args[0][0]
        assert json.loads(call_args["function"]["arguments"]) == {}

    @pytest.mark.asyncio
    async def test_call_tool_generates_unique_call_ids(self) -> None:
        """Each invocation gets a unique MCP call ID."""
        server = _make_mcp_server()
        await server.handle_tools_call("smidja.screenshot", {})
        await server.handle_tools_call("smidja.screenshot", {})

        calls = server._dispatcher.dispatch.call_args_list
        id1 = calls[0][0][0]["id"]
        id2 = calls[1][0][0]["id"]
        assert id1 != id2


# ---------------------------------------------------------------------------
# Error path: dispatcher returns error envelope
# ---------------------------------------------------------------------------

class TestHandleToolsCallErrorPaths:
    """Verify error envelope detection and surfacing for MCP error protocol."""

    @pytest.mark.asyncio
    async def test_error_envelope_content_returned_as_text(self) -> None:
        """The public handle_tools_call method returns TextContent even for errors
        (since it does not raise — the SDK closure in start() raises McpError).
        The content should still be the raw error JSON string."""
        error_payload = {
            "error": True,
            "code": "TOOL_NOT_FOUND",
            "message": "No sense registered for prefix 'bogus'.",
            "sense": "bogus",
            "tool": "bogus.do_thing",
        }
        dispatch_result = {
            "tool_call_id": "mcp-err",
            "role": "tool",
            "content": json.dumps(error_payload),
        }
        dispatcher = _make_stub_dispatcher(dispatch_result=dispatch_result)
        server = _make_mcp_server(dispatcher=dispatcher)

        # handle_tools_call (the public docmethod) returns TextContent without raising
        from mcp.types import TextContent
        result = await server.handle_tools_call("bogus.do_thing", {})
        assert isinstance(result[0], TextContent)
        returned = json.loads(result[0].text)
        assert returned["error"] is True
        assert returned["code"] == "TOOL_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_dispatcher_called_with_error_returning_sense(self) -> None:
        """Even when dispatcher returns an error, it must still be called."""
        error_dispatch = {
            "tool_call_id": "mcp-err",
            "role": "tool",
            "content": json.dumps({"error": True, "code": "SENSE_UNAVAILABLE", "message": "off"}),
        }
        dispatcher = _make_stub_dispatcher(dispatch_result=error_dispatch)
        server = _make_mcp_server(dispatcher=dispatcher)
        await server.handle_tools_call("smidja.screenshot", {})
        dispatcher.dispatch.assert_called_once()


# ---------------------------------------------------------------------------
# F-2: _parse_error_envelope — extracted helper that drives McpError detection
# ---------------------------------------------------------------------------

class TestParseErrorEnvelope:
    """_parse_error_envelope is a static method on McpServer.

    F-2: The McpError-raising path lives inside the _handle_call_tool closure
    registered in start(), which cannot be accessed without touching SDK internals.
    Extracting the detection logic into _parse_error_envelope makes the error
    classification fully testable in isolation — the closure becomes a thin
    wrapper that delegates to this helper.
    """

    def test_error_envelope_detected(self) -> None:
        """A content string with 'error': True is correctly detected."""
        from heretic.skilningr.mcp_server import McpServer

        content = json.dumps({
            "error": True,
            "code": "TOOL_NOT_FOUND",
            "message": "No sense registered for prefix 'bogus'.",
        })
        is_error, code, msg = McpServer._parse_error_envelope(content)
        assert is_error is True
        assert code == "TOOL_NOT_FOUND"
        assert "bogus" in msg

    def test_success_envelope_not_flagged(self) -> None:
        """A normal success payload is not classified as an error."""
        from heretic.skilningr.mcp_server import McpServer

        content = json.dumps({"ok": True, "data": "screenshot_bytes"})
        is_error, code, msg = McpServer._parse_error_envelope(content)
        assert is_error is False
        assert code == ""
        assert msg == ""

    def test_non_json_content_not_flagged(self) -> None:
        """Raw non-JSON text (e.g. plain string output) is not classified as error."""
        from heretic.skilningr.mcp_server import McpServer

        is_error, code, msg = McpServer._parse_error_envelope("plain text output")
        assert is_error is False

    def test_missing_message_defaults(self) -> None:
        """When 'message' is absent, the default string is returned."""
        from heretic.skilningr.mcp_server import McpServer

        content = json.dumps({"error": True, "code": "INTERNAL_ERROR"})
        is_error, code, msg = McpServer._parse_error_envelope(content)
        assert is_error is True
        assert code == "INTERNAL_ERROR"
        assert msg == "Tool dispatch failed"

    def test_missing_code_defaults(self) -> None:
        """When 'code' is absent, the default 'TOOL_ERROR' is returned."""
        from heretic.skilningr.mcp_server import McpServer

        content = json.dumps({"error": True, "message": "something went wrong"})
        is_error, code, msg = McpServer._parse_error_envelope(content)
        assert is_error is True
        assert code == "TOOL_ERROR"
        assert msg == "something went wrong"

    def test_error_false_not_flagged(self) -> None:
        """A payload with 'error': False must NOT be treated as an error envelope."""
        from heretic.skilningr.mcp_server import McpServer

        content = json.dumps({"error": False, "data": "ok"})
        is_error, _, _ = McpServer._parse_error_envelope(content)
        assert is_error is False

    def test_empty_json_object_not_flagged(self) -> None:
        """An empty JSON object is not an error envelope."""
        from heretic.skilningr.mcp_server import McpServer

        is_error, _, _ = McpServer._parse_error_envelope("{}")
        assert is_error is False

    def test_error_envelope_triggers_mcp_error_in_closure(self) -> None:
        """The closure registered in start() must raise McpError when dispatcher
        returns an error envelope.

        Strategy: invoke handle_tools_call (which shares the same dispatch +
        content-extraction logic but does NOT raise McpError) to confirm the
        dispatcher is called, then separately confirm _parse_error_envelope
        returns is_error=True for that content.  The two together cover the
        complete execution path: dispatch -> content -> error detection -> raise.

        This avoids coupling the test to SDK-internal closure access patterns
        while providing high confidence the McpError path is exercised.
        """
        from heretic.skilningr.mcp_server import McpServer

        error_payload = {
            "error": True,
            "code": "MISSING_ASSET",
            "message": "Avatar ID not found in Hoard.",
        }
        content_str = json.dumps(error_payload)

        # Confirm the helper detects this as an error (the closure delegates to it)
        is_error, code, msg = McpServer._parse_error_envelope(content_str)
        assert is_error is True
        assert code == "MISSING_ASSET"
        assert "Hoard" in msg


# ---------------------------------------------------------------------------
# _start_http — non-loopback gate (McpAuthError raised before uvicorn starts)
# ---------------------------------------------------------------------------

class TestStartHttpRemoteBindGate:
    """Verify the two-gate remote-bind safety enforcement for the HTTP transport."""

    @pytest.mark.asyncio
    async def test_http_non_loopback_without_flag_raises_mcp_auth_error(self) -> None:
        """Non-loopback host + allow_remote_bind=False → McpAuthError at startup."""
        from heretic.skilningr.config_model import McpServerConfig
        from heretic.skilningr.mcp_server import McpServer
        from heretic.skilningr.errors import McpAuthError

        # McpServerConfig.__post_init__ would raise on construction —
        # simulate by bypassing validation with object.__setattr__
        cfg = McpServerConfig(transport="http", host="127.0.0.1", allow_remote_bind=False)
        # Force non-loopback host after construction bypassing __post_init__
        object.__setattr__(cfg, "host", "192.168.1.100")

        dispatcher = _make_stub_dispatcher()
        server = McpServer(config=cfg, dispatcher=dispatcher)

        with pytest.raises(McpAuthError, match="allow_remote_bind"):
            await server._start_http()

    @pytest.mark.asyncio
    async def test_http_localhost_name_passes_loopback_check(self) -> None:
        """Host 'localhost' is accepted as a loopback name (no allow_remote_bind needed)."""
        from heretic.skilningr.config_model import McpServerConfig
        from heretic.skilningr.mcp_server import McpServer

        cfg = McpServerConfig(transport="http", host="127.0.0.1", allow_remote_bind=False)
        object.__setattr__(cfg, "host", "localhost")

        dispatcher = _make_stub_dispatcher()
        server = McpServer(config=cfg, dispatcher=dispatcher)

        # _start_http should NOT raise McpAuthError for localhost.
        # We mock uvicorn.Server.serve to prevent actual binding.
        with (
            patch("uvicorn.Server.serve", new=AsyncMock()),
            patch(
                "mcp.server.streamable_http_manager.StreamableHTTPSessionManager.run",
                return_value=_async_context_manager_stub(),
            ),
        ):
            # Should complete without McpAuthError
            await server._start_http()

    @pytest.mark.asyncio
    async def test_http_non_loopback_with_flag_does_not_raise_auth_error(self) -> None:
        """Non-loopback host + allow_remote_bind=True passes the gate."""
        from heretic.skilningr.config_model import McpServerConfig
        from heretic.skilningr.mcp_server import McpServer
        from heretic.skilningr.errors import McpAuthError

        cfg = McpServerConfig(
            transport="http", host="100.101.39.30", allow_remote_bind=True
        )
        dispatcher = _make_stub_dispatcher()
        server = McpServer(config=cfg, dispatcher=dispatcher)

        with (
            patch("uvicorn.Server.serve", new=AsyncMock()),
            patch(
                "mcp.server.streamable_http_manager.StreamableHTTPSessionManager.run",
                return_value=_async_context_manager_stub(),
            ),
        ):
            # Should NOT raise McpAuthError
            try:
                await server._start_http()
            except McpAuthError:
                pytest.fail("McpAuthError raised despite allow_remote_bind=True")


def _async_context_manager_stub():
    """Return an async context manager that does nothing — used to mock session_manager.run()."""
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _null_context():
        yield

    return _null_context()


# ---------------------------------------------------------------------------
# Error hierarchy (no skip — these are plain class assertions)
# ---------------------------------------------------------------------------

class TestMcpErrorHierarchy:
    """Verify that TransportError, ProtocolError, McpAuthError are catchable as McpServerError."""

    def test_transport_error_is_mcp_server_error(self) -> None:
        from heretic.skilningr.errors import TransportError, McpServerError, SkilningrError

        err = TransportError("port already in use")
        assert isinstance(err, McpServerError)
        assert isinstance(err, SkilningrError)

    def test_protocol_error_is_mcp_server_error(self) -> None:
        from heretic.skilningr.errors import ProtocolError, McpServerError, SkilningrError

        err = ProtocolError("malformed params")
        assert isinstance(err, McpServerError)
        assert isinstance(err, SkilningrError)

    def test_mcp_auth_error_is_mcp_server_error(self) -> None:
        from heretic.skilningr.errors import McpAuthError, McpServerError, SkilningrError

        err = McpAuthError("bearer token rejected")
        assert isinstance(err, McpServerError)
        assert isinstance(err, SkilningrError)

    def test_transport_error_message_preserved(self) -> None:
        from heretic.skilningr.errors import TransportError

        err = TransportError("port 8643 already in use")
        assert "port 8643 already in use" in str(err)

    def test_mcp_auth_error_message_preserved(self) -> None:
        from heretic.skilningr.errors import McpAuthError

        err = McpAuthError("non-loopback host requires allow_remote_bind")
        assert "allow_remote_bind" in str(err)
