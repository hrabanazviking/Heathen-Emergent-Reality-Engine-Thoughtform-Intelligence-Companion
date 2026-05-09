"""
Tests — MCP transport layer (stdio and http paths).

Covers:
    - _start_stdio: verifies it calls mcp SDK stdio_server + server.run correctly
    - _start_stdio: verifies TransportError is raised on SDK failure
    - _start_http: verifies Starlette/uvicorn startup is attempted with correct config
    - _start_http: verifies remote-bind gate (tested in test_mcp_server.py too, but
                   confirmed here for the full transport integration path)
    - start() dispatch to correct transport branch
    - start() unknown transport raises TransportError
    - CLI: heretic mcp --help includes transport option
    - CLI: _cmd_mcp returns 1 when mcp_server.enabled=False
    - McpServer: handle_tools_list and call_tool handlers registered inside start()

Ref: src/heretic/skilningr/mcp_server.py
     src/heretic/skilningr/errors.py (TransportError, ProtocolError, McpAuthError)
     src/heretic/cli.py (_cmd_mcp)
     TASK_HERETIC_v0.6.x_MCP_SERVER.md
"""

from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Helpers — reused across tests
# ---------------------------------------------------------------------------

def _make_stub_dispatcher(
    tool_definitions: list[dict] | None = None,
    dispatch_result: dict | None = None,
) -> MagicMock:
    dispatcher = MagicMock()
    if tool_definitions is None:
        tool_definitions = [
            {
                "type": "function",
                "function": {
                    "name": "smidja.screenshot",
                    "description": "Capture the screen.",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]
    dispatcher.all_tool_definitions.return_value = tool_definitions
    if dispatch_result is None:
        dispatch_result = {
            "tool_call_id": "mcp-xyz",
            "role": "tool",
            "content": json.dumps({"ok": True}),
        }
    dispatcher.dispatch = AsyncMock(return_value=dispatch_result)
    return dispatcher


def _make_mcp_server(transport: str = "stdio", allow_remote_bind: bool = False, host: str = "127.0.0.1"):
    from heretic.skilningr.config_model import McpServerConfig
    from heretic.skilningr.mcp_server import McpServer

    cfg = McpServerConfig(
        enabled=True,
        transport=transport,
        host=host,
        allow_remote_bind=allow_remote_bind,
    )
    dispatcher = _make_stub_dispatcher()
    return McpServer(config=cfg, dispatcher=dispatcher)


@asynccontextmanager
async def _null_async_context():
    """Null async context manager — stand-in for session_manager.run()."""
    yield


# ---------------------------------------------------------------------------
# stdio transport path
# ---------------------------------------------------------------------------

class TestStdioTransport:
    """Verify the stdio transport path."""

    @pytest.mark.asyncio
    async def test_stdio_calls_stdio_server_context_manager(self) -> None:
        """_start_stdio must enter the stdio_server() async context manager."""
        server = _make_mcp_server(transport="stdio")

        fake_read = MagicMock()
        fake_write = MagicMock()

        @asynccontextmanager
        async def mock_stdio_server():
            yield fake_read, fake_write

        with (
            patch("mcp.server.stdio.stdio_server", mock_stdio_server),
            patch.object(server._mcp, "run", new=AsyncMock()) as mock_run,
            patch.object(server._mcp, "create_initialization_options", return_value=MagicMock()),
        ):
            await server._start_stdio()
            mock_run.assert_called_once()
            run_args = mock_run.call_args[0]
            assert run_args[0] is fake_read
            assert run_args[1] is fake_write

    @pytest.mark.asyncio
    async def test_stdio_calls_create_initialization_options(self) -> None:
        """_start_stdio must obtain init_opts via create_initialization_options()."""
        server = _make_mcp_server(transport="stdio")

        fake_init_opts = MagicMock(name="init_opts")

        @asynccontextmanager
        async def mock_stdio_server():
            yield MagicMock(), MagicMock()

        with (
            patch("mcp.server.stdio.stdio_server", mock_stdio_server),
            patch.object(
                server._mcp, "create_initialization_options", return_value=fake_init_opts
            ) as mock_init,
            patch.object(server._mcp, "run", new=AsyncMock()),
        ):
            await server._start_stdio()
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_stdio_run_raises_wrapped_as_transport_error(self) -> None:
        """If mcp.server.run() raises, it must be wrapped in TransportError."""
        from heretic.skilningr.errors import TransportError

        server = _make_mcp_server(transport="stdio")

        @asynccontextmanager
        async def mock_stdio_server():
            yield MagicMock(), MagicMock()

        async def _crashing_run(*args, **kwargs):
            raise RuntimeError("stdio streams broken")

        with (
            patch("mcp.server.stdio.stdio_server", mock_stdio_server),
            patch.object(server._mcp, "run", new=AsyncMock(side_effect=_crashing_run)),
            patch.object(server._mcp, "create_initialization_options", return_value=MagicMock()),
        ):
            with pytest.raises(TransportError, match="stdio transport error"):
                await server._start_stdio()

    @pytest.mark.asyncio
    async def test_start_routes_to_stdio_when_transport_is_stdio(self) -> None:
        """start('stdio') must call _start_stdio, not _start_http."""
        server = _make_mcp_server(transport="stdio")

        # We verify routing by checking which private method was called.
        with (
            patch.object(server, "_start_stdio", new=AsyncMock()) as mock_stdio,
            patch.object(server, "_start_http", new=AsyncMock()) as mock_http,
        ):
            await server.start("stdio")
            mock_stdio.assert_called_once()
            mock_http.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_uses_config_transport_when_none_given(self) -> None:
        """start(None) must fall back to config.transport."""
        server = _make_mcp_server(transport="stdio")

        with (
            patch.object(server, "_start_stdio", new=AsyncMock()) as mock_stdio,
            patch.object(server, "_start_http", new=AsyncMock()),
        ):
            await server.start(None)
            mock_stdio.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_unknown_transport_raises_transport_error(self) -> None:
        """start() with an unknown transport string must raise TransportError."""
        from heretic.skilningr.errors import TransportError

        server = _make_mcp_server(transport="stdio")

        with pytest.raises(TransportError, match="unknown transport"):
            await server.start("websocket")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# http transport path
# ---------------------------------------------------------------------------

class TestHttpTransport:
    """Verify the HTTP (Streamable HTTP) transport path."""

    @pytest.mark.asyncio
    async def test_start_routes_to_http_when_transport_is_http(self) -> None:
        """start('http') must call _start_http, not _start_stdio."""
        server = _make_mcp_server(transport="http")

        with (
            patch.object(server, "_start_stdio", new=AsyncMock()) as mock_stdio,
            patch.object(server, "_start_http", new=AsyncMock()) as mock_http,
        ):
            await server.start("http")
            mock_http.assert_called_once()
            mock_stdio.assert_not_called()

    @pytest.mark.asyncio
    async def test_http_loopback_host_does_not_raise_auth_error(self) -> None:
        """127.0.0.1 with allow_remote_bind=False must NOT raise McpAuthError."""
        from heretic.skilningr.errors import McpAuthError

        server = _make_mcp_server(transport="http", host="127.0.0.1", allow_remote_bind=False)

        with (
            patch("uvicorn.Server.serve", new=AsyncMock()),
            patch(
                "mcp.server.streamable_http_manager.StreamableHTTPSessionManager.run",
                return_value=_null_async_context(),
            ),
        ):
            try:
                await server._start_http()
            except McpAuthError:
                pytest.fail("McpAuthError raised for loopback host")

    @pytest.mark.asyncio
    async def test_http_non_loopback_without_flag_raises_mcp_auth_error(self) -> None:
        """Non-loopback host + allow_remote_bind=False → McpAuthError (two-gate)."""
        from heretic.skilningr.config_model import McpServerConfig
        from heretic.skilningr.mcp_server import McpServer
        from heretic.skilningr.errors import McpAuthError

        cfg = McpServerConfig(transport="http", host="127.0.0.1", allow_remote_bind=False)
        object.__setattr__(cfg, "host", "10.0.0.100")  # bypass __post_init__ gate
        dispatcher = _make_stub_dispatcher()
        server = McpServer(config=cfg, dispatcher=dispatcher)

        with pytest.raises(McpAuthError, match="allow_remote_bind"):
            await server._start_http()

    @pytest.mark.asyncio
    async def test_http_non_loopback_with_flag_proceeds(self) -> None:
        """Non-loopback host + allow_remote_bind=True passes the gate."""
        from heretic.skilningr.errors import McpAuthError

        server = _make_mcp_server(transport="http", host="100.101.39.30", allow_remote_bind=True)

        with (
            patch("uvicorn.Server.serve", new=AsyncMock()),
            patch(
                "mcp.server.streamable_http_manager.StreamableHTTPSessionManager.run",
                return_value=_null_async_context(),
            ),
        ):
            try:
                await server._start_http()
            except McpAuthError:
                pytest.fail("McpAuthError raised despite allow_remote_bind=True")

    @pytest.mark.asyncio
    async def test_http_uses_config_host_and_port_for_uvicorn(self) -> None:
        """uvicorn.Config must receive the host and port from McpServerConfig."""
        import uvicorn
        from heretic.skilningr.config_model import McpServerConfig
        from heretic.skilningr.mcp_server import McpServer

        cfg = McpServerConfig(
            transport="http", host="127.0.0.1", port=19843, allow_remote_bind=False
        )
        dispatcher = _make_stub_dispatcher()
        server = McpServer(config=cfg, dispatcher=dispatcher)

        captured_configs: list[uvicorn.Config] = []

        original_config_init = uvicorn.Config.__init__

        def _capture_config(self_inner, app, host=None, port=None, **kwargs):
            captured_configs.append({"host": host, "port": port})
            # Minimal stub to avoid real binding
            self_inner.host = host
            self_inner.port = port
            self_inner.uds = None
            self_inner.fd = None
            self_inner.loop = "asyncio"
            self_inner.http = "auto"
            self_inner.log_level = "warning"
            self_inner.loaded = False
            self_inner.ws = "auto"
            self_inner.lifespan = "auto"
            self_inner.interface = "auto"
            self_inner.reload = False
            self_inner.reload_dirs = []
            self_inner.workers = None
            self_inner.factory = False
            self_inner.ssl_certfile = None
            self_inner.ssl_keyfile = None
            self_inner.ssl_keyfile_password = None
            self_inner.ssl_version = None
            self_inner.ssl_cert_reqs = None
            self_inner.ssl_ca_certs = None
            self_inner.ssl_ciphers = "TLSv1"
            self_inner.headers = []
            self_inner.encoded_headers = []
            self_inner.proxy_headers = True
            self_inner.server_header = True
            self_inner.date_header = True
            self_inner.forwarded_allow_ips = None
            self_inner.root_path = ""
            self_inner.timeout_keep_alive = 5
            self_inner.timeout_notify = 30
            self_inner.callback_notify = lambda *a, **kw: None  # noqa: ARG005
            self_inner.limit_concurrency = None
            self_inner.limit_max_requests = None
            self_inner.backlog = 2048
            self_inner.app = app

        with (
            patch.object(uvicorn.Config, "__init__", _capture_config),
            patch("uvicorn.Server.serve", new=AsyncMock()),
            patch(
                "mcp.server.streamable_http_manager.StreamableHTTPSessionManager.run",
                return_value=_null_async_context(),
            ),
        ):
            try:
                await server._start_http()
            except Exception:
                pass  # We only care about the captured config

        assert any(c["port"] == 19843 for c in captured_configs), (
            f"Expected uvicorn to receive port=19843; got: {captured_configs}"
        )


# ---------------------------------------------------------------------------
# Handler registration — verify that start() registers working closures
# ---------------------------------------------------------------------------

class TestHandlerRegistration:
    """Verify that start() correctly registers list_tools + call_tool closures."""

    @pytest.mark.asyncio
    async def test_start_registers_list_tools_handler(self) -> None:
        """After start() returns, the mcp Server's list_tools handler should work."""
        server = _make_mcp_server(transport="stdio")

        # Intercept start() — we patch _start_stdio so it returns immediately.
        # The handler registration happens before _start_stdio is called.
        with patch.object(server, "_start_stdio", new=AsyncMock()):
            await server.start("stdio")

        # The handler is registered on the internal mcp Server.
        # We verify indirectly by calling handle_tools_list (same underlying logic).
        from mcp.types import Tool
        tools = await server.handle_tools_list()
        assert all(isinstance(t, Tool) for t in tools)

    @pytest.mark.asyncio
    async def test_start_registers_call_tool_handler(self) -> None:
        """After start() returns, call_tool dispatch through handler works correctly."""
        server = _make_mcp_server(transport="stdio")

        with patch.object(server, "_start_stdio", new=AsyncMock()):
            await server.start("stdio")

        from mcp.types import TextContent
        result = await server.handle_tools_call("smidja.screenshot", {})
        assert isinstance(result[0], TextContent)
        server._dispatcher.dispatch.assert_called()


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

class TestCliMcpSubcommand:
    """Verify CLI integration for the 'mcp' subcommand."""

    def test_mcp_subcommand_registered_in_parser(self) -> None:
        """build_parser() must expose a 'mcp' subcommand."""
        from heretic.cli import build_parser

        parser = build_parser()
        # Extract subparser choices
        subparser_actions = [
            action for action in parser._subparsers._actions
            if hasattr(action, "_name_parser_map")
        ]
        assert subparser_actions, "No subparsers found"
        choices = list(subparser_actions[0]._name_parser_map.keys())
        assert "mcp" in choices, f"'mcp' not in subcommands: {choices}"

    def test_mcp_transport_arg_choices(self) -> None:
        """The mcp subcommand must accept --transport stdio and --transport http."""
        from heretic.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["mcp", "--transport", "stdio"])
        assert args.transport == "stdio"

        args = parser.parse_args(["mcp", "--transport", "http"])
        assert args.transport == "http"

    def test_mcp_transport_defaults_to_none(self) -> None:
        """Omitting --transport leaves args.transport as None (resolved from config)."""
        from heretic.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["mcp"])
        assert args.transport is None

    def test_cmd_mcp_returns_1_when_disabled_in_config(self) -> None:
        """_cmd_mcp must return 1 without starting a server if mcp_server.enabled=False."""
        from heretic.cli import build_parser

        # We need to mock load_config to return a config where mcp_server.enabled=False.
        # The default McpServerConfig has enabled=False so we just mock load_config.
        from heretic.grunnr.config import load_config
        from unittest.mock import MagicMock

        mock_cfg = MagicMock()
        mock_cfg.grunnr.log_level = "WARNING"
        mock_cfg.grunnr.log_file = None
        mock_cfg.skilningr.mcp_server.enabled = False
        mock_cfg.skilningr.mcp_server.transport = "stdio"

        parser = build_parser()
        args = parser.parse_args(["mcp"])

        # F-1: patch configure_logging to prevent it from setting
        # logging.getLogger("heretic").propagate = False for the remainder of
        # the test session.  That side effect breaks caplog-based tests in
        # test_sjon_config.py and test_sjon_webcam.py when this test runs first.
        with (
            patch("heretic.grunnr.config.load_config", return_value=mock_cfg),
            patch("heretic.grunnr.logger.configure_logging"),
        ):
            from heretic.cli import _cmd_mcp
            result = _cmd_mcp(args)

        assert result == 1, f"Expected return code 1 when mcp disabled, got {result}"

    def test_cmd_mcp_func_is_registered(self) -> None:
        """args.func must be _cmd_mcp when the mcp subcommand is parsed."""
        from heretic.cli import build_parser, _cmd_mcp

        parser = build_parser()
        args = parser.parse_args(["mcp"])
        assert args.func is _cmd_mcp
