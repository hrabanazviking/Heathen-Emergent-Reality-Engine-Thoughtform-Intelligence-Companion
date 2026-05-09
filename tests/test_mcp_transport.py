"""
Placeholder tests — MCP transport layer (stdio and http paths).

All tests in this file are marked pytest.mark.skip.  They document what Forge
must verify once McpServer.start() is implemented.  The file exists now so that
the test inventory is visible and the CI baseline is not broken.

Ref: src/heretic/skilningr/mcp_server.py
     src/heretic/skilningr/errors.py (TransportError, ProtocolError, McpAuthError)
     TASK_HERETIC_v0.6.x_MCP_SERVER.md
"""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="MCP stdio transport not yet implemented — Forge milestone")
class TestStdioTransport:
    """Verify the stdio transport path end-to-end."""

    @pytest.mark.asyncio
    async def test_stdio_initialize_handshake(self) -> None:
        """Client sends InitializeRequest; server responds with capabilities."""
        raise NotImplementedError("Forge implements when McpServer.start('stdio') is live.")

    @pytest.mark.asyncio
    async def test_stdio_list_tools_after_init(self) -> None:
        """After handshake, ListToolsRequest returns the full tool roster."""
        raise NotImplementedError("Forge implements when McpServer.start('stdio') is live.")

    @pytest.mark.asyncio
    async def test_stdio_call_tool_returns_text_content(self) -> None:
        """CallToolRequest routes through dispatcher and returns TextContent."""
        raise NotImplementedError("Forge implements when McpServer.start('stdio') is live.")

    @pytest.mark.asyncio
    async def test_stdio_unknown_tool_returns_error_envelope(self) -> None:
        """CallToolRequest for unknown tool returns error content, not a crash."""
        raise NotImplementedError("Forge implements when McpServer.start('stdio') is live.")

    @pytest.mark.asyncio
    async def test_stdio_eof_on_stdin_triggers_graceful_shutdown(self) -> None:
        """EOF on stdin causes the server to exit cleanly without exception."""
        raise NotImplementedError("Forge implements when McpServer.start('stdio') is live.")


@pytest.mark.skip(reason="MCP http transport not yet implemented — Forge milestone")
class TestHttpTransport:
    """Verify the http (Streamable HTTP / Starlette) transport path."""

    @pytest.mark.asyncio
    async def test_http_server_binds_loopback(self) -> None:
        """Server binds 127.0.0.1:port successfully."""
        raise NotImplementedError("Forge implements when McpServer.start('http') is live.")

    @pytest.mark.asyncio
    async def test_http_server_rejects_non_loopback_without_flag(self) -> None:
        """Non-loopback bind with allow_remote_bind=False raises TransportError."""
        raise NotImplementedError("Forge implements when McpServer.start('http') is live.")

    @pytest.mark.asyncio
    async def test_http_server_allows_non_loopback_with_flag(self) -> None:
        """Non-loopback bind with allow_remote_bind=True proceeds without error."""
        raise NotImplementedError("Forge implements when McpServer.start('http') is live.")

    @pytest.mark.asyncio
    async def test_http_mcp_session_list_tools(self) -> None:
        """HTTP client session can fetch the tool list."""
        raise NotImplementedError("Forge implements when McpServer.start('http') is live.")

    @pytest.mark.asyncio
    async def test_http_mcp_session_call_tool(self) -> None:
        """HTTP client session can invoke a tool and receive TextContent."""
        raise NotImplementedError("Forge implements when McpServer.start('http') is live.")

    @pytest.mark.asyncio
    async def test_http_auth_rejection_raises_mcp_auth_error(self) -> None:
        """Missing or invalid bearer token on http transport raises McpAuthError."""
        raise NotImplementedError("Forge implements when auth middleware is wired.")


@pytest.mark.skip(reason="MCP error hierarchy — integration tests pending Forge milestone")
class TestMcpErrorHierarchy:
    """Verify that TransportError, ProtocolError, McpAuthError are catchable."""

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
