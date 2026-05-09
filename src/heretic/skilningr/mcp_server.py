"""
Skilningr MCP Server — McpServer class and convert_to_mcp_tool helper.

This module hosts HERETIC's MCP server: it exposes the same 16 tool schemas
that ToolDispatcher serves to OpenAI-compatible agents, but via the Model
Context Protocol transport instead of OpenAI tool_call / tool_result JSON.

The same dispatcher and the same sandboxes handle every call.  Same auth
invariants.  Same error taxonomy.  The transport is different; the logic is
identical.

SDK verified: mcp==1.27.0 (Anthropic, MIT).

Transport paths
---------------
stdio
    mcp.server.stdio.stdio_server() — async context manager that yields
    (read_stream, write_stream): MemoryObjectReceiveStream / MemoryObjectSendStream.
    The caller then calls await server.run(read_stream, write_stream, init_opts).
    Run with: anyio.run(…) or asyncio.run(…).

http (Streamable HTTP)
    mcp.server.streamable_http_manager.StreamableHTTPSessionManager — wraps the
    lowlevel Server instance in a Starlette ASGI app.  The manager is mounted at
    the root path and uvicorn drives it.
    Session-tracking is stateful by default; set stateless=True for load-balanced
    multi-node deployments.

Handler registration (mcp.server.lowlevel.Server decorator API)
----------------------------------------------------------------
list_tools decorator:
    @mcp_server.list_tools()
    async def handle_list_tools() -> list[mcp.types.Tool]:
        return [mcp.types.Tool(name=..., description=..., inputSchema=...) ...]

    The SDK accepts both list[Tool] (old-style) and ListToolsResult (new-style).
    We use list[Tool] for simplicity — the SDK wraps it automatically.

call_tool decorator:
    @mcp_server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict
    ) -> list[mcp.types.TextContent]:
        ...

    The handler receives (tool_name: str, arguments: dict) after the SDK has
    validated the input against the registered tool's inputSchema.
    Return value: iterable of ContentBlock (TextContent, ImageContent, etc.)
    or a dict (structured) or a CallToolResult directly.

Ref: mcp.server.lowlevel.server — verified 2026-05-08 (mcp==1.27.0)
     mcp.server.stdio.stdio_server — verified 2026-05-08
     mcp.server.streamable_http_manager.StreamableHTTPSessionManager — verified 2026-05-08
     docs/architecture/AGENT_AGNOSTIC_PROTOCOL.md §v0.6.x (MCP transport addendum)
     src/heretic/skilningr/INTERFACE.md §MCP Server
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from heretic.skilningr.config_model import McpServerConfig
    from heretic.skilningr.dispatcher import ToolDispatcher


# ---------------------------------------------------------------------------
# Module-level pure helper: convert_to_mcp_tool
# ---------------------------------------------------------------------------

def convert_to_mcp_tool(openai_tool: dict) -> dict:
    """Convert an OpenAI function-calling tool schema to MCP tool format.

    This is a pure function — no I/O, no imports, no side effects.  It is safe
    to call at any point without a live dispatcher or MCP server.

    OpenAI input format (the ``type == "function"`` wrapper):
        {
            "type": "function",
            "function": {
                "name": "smidja.screenshot",
                "description": "Capture the current screen state.",
                "parameters": {
                    "type": "object",
                    "properties": { ... },
                    "required": [...]
                }
            }
        }

    MCP output format (``Tool`` fields as a plain dict, ready for
    ``mcp.types.Tool(**result)``):
        {
            "name": "smidja.screenshot",
            "description": "Capture the current screen state.",
            "inputSchema": {
                "type": "object",
                "properties": { ... },
                "required": [...]
            }
        }

    The mapping is:
        openai_tool["function"]["name"]        → result["name"]
        openai_tool["function"]["description"] → result["description"]
        openai_tool["function"]["parameters"]  → result["inputSchema"]

    Args:
        openai_tool: A dict in the ``{"type": "function", "function": {...}}``
                     OpenAI tool schema format.

    Returns:
        A plain dict with keys ``name``, ``description``, and ``inputSchema``
        suitable for constructing ``mcp.types.Tool(**result)``.

    Raises:
        ValueError: if the input does not match the expected OpenAI tool schema
                    shape (missing ``function`` key, missing ``name``, etc.).
        TypeError:  if openai_tool is not a dict.
    """
    if not isinstance(openai_tool, dict):
        raise TypeError(
            f"convert_to_mcp_tool: expected dict, got {type(openai_tool).__name__!r}."
        )
    if openai_tool.get("type") != "function":
        raise ValueError(
            f"convert_to_mcp_tool: expected openai_tool['type'] == 'function', "
            f"got {openai_tool.get('type')!r}."
        )
    fn = openai_tool.get("function")
    if not isinstance(fn, dict):
        raise ValueError(
            "convert_to_mcp_tool: openai_tool['function'] must be a dict, "
            f"got {type(fn).__name__!r}."
        )
    name = fn.get("name")
    if not name or not isinstance(name, str):
        raise ValueError(
            "convert_to_mcp_tool: openai_tool['function']['name'] must be a "
            f"non-empty string, got {name!r}."
        )
    description = fn.get("description", "")
    parameters = fn.get("parameters", {"type": "object", "properties": {}})

    return {
        "name": name,
        "description": description,
        "inputSchema": parameters,
    }


# ---------------------------------------------------------------------------
# McpServer class
# ---------------------------------------------------------------------------

class McpServer:
    """HERETIC's MCP server — hosts the sense hub tools over MCP transport.

    This class owns the lifecycle of a single MCP server instance.  It wraps
    ``mcp.server.lowlevel.Server`` and registers two handlers:
        - list_tools  → returns all tool schemas from the ToolDispatcher,
                         translated from OpenAI format via convert_to_mcp_tool.
        - call_tool   → routes the call through ToolDispatcher.dispatch() and
                         returns the result as MCP TextContent.

    The same ToolDispatcher that serves OpenAI-format tool_calls is reused
    here.  Same senses.  Same sandboxes.  Same auth invariants.  The MCP
    server is an alternative transport, not a separate capability surface.

    Transport selection
    -------------------
    start(transport="stdio") — opens stdio streams and blocks until the client
        disconnects.  The process runs as a long-lived subprocess in the client's
        I/O channels (Claude Desktop, Continue, etc.).

    start(transport="http") — launches a Starlette/uvicorn HTTP server.  The
        bind address is McpServerConfig.host:port.  Non-loopback binds require
        McpServerConfig.allow_remote_bind == True (mirrors the Vébond pattern).

    Auth note (http transport)
    --------------------------
    The lowlevel mcp.server.Server does NOT enforce bearer tokens internally.
    For http transport, authentication must be applied at the Starlette/uvicorn
    layer (middleware).  This is a Forge responsibility: the scaffold stubs the
    start() method body as NotImplementedError.  Forge will add middleware here.
    For stdio transport, auth is implicit — the MCP client controls the process.

    Usage (Forge will implement — do not call in tests yet)
    -------------------------------------------------------
        config = McpServerConfig(enabled=True, transport="stdio")
        dispatcher = ToolDispatcher(...)
        server = McpServer(config=config, dispatcher=dispatcher, logger=log)
        anyio.run(server.start, "stdio")

    Ref: mcp.server.lowlevel.Server — source verified 2026-05-08 (mcp==1.27.0)
         mcp.server.stdio.stdio_server — source verified 2026-05-08
         mcp.server.streamable_http_manager.StreamableHTTPSessionManager — source verified 2026-05-08
         docs/architecture/AGENT_AGNOSTIC_PROTOCOL.md §v0.6.x MCP transport addendum
         src/heretic/skilningr/INTERFACE.md §MCP Server
    """

    def __init__(
        self,
        config: "McpServerConfig",
        dispatcher: "ToolDispatcher",
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialise the MCP server.

        Args:
            config:     McpServerConfig controlling transport, bind address, port,
                        timeout, and the allow_remote_bind safety gate.
            dispatcher: A live ToolDispatcher with at least one sense registered.
                        The dispatcher supplies tool schemas (all_tool_definitions())
                        and handles tool execution (dispatch()).
            logger:     Optional logger.  If None, a module-level logger is used.

        The mcp.server.lowlevel.Server instance is created here but not started.
        Call start() to open the transport and enter the request loop.
        """
        self._config = config
        self._dispatcher = dispatcher
        self._log = logger or logging.getLogger("heretic.skilningr.mcp_server")

        # Deferred import — mcp is an optional extra ([mcp]).
        # Forge will call this only when config.enabled is True and the
        # [mcp] extra is installed.  The ImportError is intentional:
        # if [mcp] is absent, McpServer cannot be constructed at all.
        try:
            from mcp.server.lowlevel import Server as LowlevelMcpServer
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "McpServer requires the [mcp] extra: pip install heretic[mcp]"
            ) from exc

        self._mcp: "LowlevelMcpServer" = LowlevelMcpServer(  # type: ignore[type-arg]
            name="heretic-mcp",
            version="0.6.x",
            instructions=(
                "HERETIC sense hub — exposes body tools (filesystem, terminal, "
                "HTTP fetch, Smiðja remote-control) to MCP-compatible agents."
            ),
        )
        self._log.debug("McpServer: mcp.server.lowlevel.Server instance created.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_error_envelope(content_str: str) -> tuple[bool, str, str]:
        """Parse a ToolDispatcher content string and detect the error-envelope pattern.

        ToolDispatcher.dispatch() never raises — when a tool call fails it
        returns a result whose ``content`` field is a JSON object with
        ``"error": True``.  This helper centralises the detection logic so that
        both the live ``_handle_call_tool`` closure (registered in start()) and
        the test suite can verify the same code path without coupling tests to
        SDK internals.

        Args:
            content_str: The raw ``content`` string from a ToolDispatcher result.

        Returns:
            (is_error, error_code, error_msg) where ``is_error`` is True when the
            content is a JSON error envelope.  If not an error envelope, returns
            (False, "", "").

        F-2: This method is extracted so tests can verify the error-detection
        logic directly, without needing to reach into the SDK's registered
        call_tool closure.
        """
        try:
            payload = json.loads(content_str)
            if isinstance(payload, dict) and payload.get("error") is True:
                error_msg = payload.get("message", "Tool dispatch failed")
                error_code = payload.get("code", "TOOL_ERROR")
                return True, error_code, error_msg
        except (json.JSONDecodeError, AttributeError):
            # Non-JSON content is not an error envelope — treat as raw text.
            pass
        return False, "", ""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def start(self, transport: Literal["stdio", "http"] | None = None) -> None:
        """Open the MCP transport and enter the request–response loop.

        For stdio transport: calls ``mcp.server.stdio.stdio_server()`` and
            then ``self._mcp.run(read_stream, write_stream, init_opts)``.
            Blocks until the client closes the pipe (EOF on stdin).

            Auth note (stdio): The OS pipe is the trust boundary.  There is no
            bearer-token layer here — the MCP client controls the process
            stdin/stdout channel.  Never add in-band auth to the stdio path;
            process-ownership IS the auth.

        For http transport: constructs a
            ``mcp.server.streamable_http_manager.StreamableHTTPSessionManager``
            and launches uvicorn at McpServerConfig.host:port.
            Non-loopback bind addresses require allow_remote_bind==True (two-gate
            safety: operator must set BOTH a non-loopback host AND allow_remote_bind).

        Handler registration (list_tools, call_tool) happens HERE — inside
        start() — so that the dispatcher is guaranteed to be populated before
        the first client request arrives.

        MCP error contract (Cartographer thread #3):
            Tool dispatch errors are surfaced as content with is_error=True via
            the SDK's CallToolResult mechanism, NOT as JSON-RPC error objects.
            When the SDK's call_tool handler raises an exception, the SDK wraps
            the exception message automatically and sets isError=true on the
            response.  When dispatch succeeds but the content is an error
            envelope, we set is_error=True explicitly so the client can detect
            the error via the MCP protocol field rather than parsing JSON content.

        Args:
            transport: Override the transport from McpServerConfig.  If None,
                       uses self._config.transport.  Must be "stdio" or "http".

        Raises:
            TransportError: if the transport fails to initialise (port in use,
                            bind permission denied, non-loopback without flag).
            ImportError:    if the [mcp] extra is not installed.
        """
        from mcp.types import Tool, TextContent, CallToolResult
        from mcp.server.lowlevel import NotificationOptions
        from heretic.skilningr.errors import TransportError

        resolved_transport: str = transport or self._config.transport
        if resolved_transport not in ("stdio", "http"):
            raise TransportError(
                f"McpServer.start: unknown transport {resolved_transport!r}. "
                f"Must be 'stdio' or 'http'."
            )

        # ------------------------------------------------------------------
        # Register handlers — done inside start() so dispatcher is fully
        # populated before the first client request arrives.
        # ------------------------------------------------------------------

        @self._mcp.list_tools()
        async def _handle_list_tools() -> list[Tool]:
            """Return all 16 tool schemas from registered senses as MCP Tool objects.

            Aggregates OpenAI-format tool schemas from ToolDispatcher and converts
            each via convert_to_mcp_tool().  The SDK accepts list[Tool] and wraps
            it into ListToolsResult automatically.
            """
            openai_tools = self._dispatcher.all_tool_definitions()
            tools: list[Tool] = []
            for openai_tool in openai_tools:
                try:
                    mcp_dict = convert_to_mcp_tool(openai_tool)
                    tools.append(Tool(**mcp_dict))
                except (TypeError, ValueError) as exc:
                    self._log.warning(
                        "McpServer: could not convert tool schema to MCP format: %s", exc
                    )
            self._log.debug("McpServer: list_tools returning %d tools.", len(tools))
            return tools

        @self._mcp.call_tool()
        async def _handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Dispatch a tool call through ToolDispatcher and return MCP content.

            Translates the MCP (name, arguments) into an OpenAI tool_call dict,
            routes through ToolDispatcher.dispatch(), and translates the
            tool_result content back into MCP TextContent.

            Error surface (Cartographer thread #3):
                ToolDispatcher.dispatch() never raises — it returns error-envelope
                JSON in the content field.  We detect the error envelope by checking
                for the "error": True key and raise a McpError (which the SDK maps
                to isError=true in the CallToolResult) so MCP clients receive the
                correct protocol-level error signal rather than having to parse the
                content to detect failures.
            """
            # Build a synthetic OpenAI tool_call dict for the dispatcher
            call_id = f"mcp-{uuid.uuid4().hex[:12]}"
            tool_call = {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": json.dumps(arguments if arguments is not None else {}),
                },
            }
            self._log.debug(
                "McpServer: dispatching tool %r (call_id=%s)", name, call_id
            )
            tool_result = await self._dispatcher.dispatch(tool_call)

            # tool_result shape: {"tool_call_id": ..., "role": "tool", "content": "<json>"}
            content_str: str = tool_result.get("content", "{}")

            # Detect error envelope via the extracted helper (_parse_error_envelope).
            # ToolDispatcher.dispatch() returns error JSON with "error": True when
            # dispatch fails (unknown tool, sense unavailable, internal error).
            # Surface these as a raised McpError so the SDK sets isError=true on
            # the CallToolResult per the MCP protocol spec.
            is_error, error_code, error_msg = McpServer._parse_error_envelope(content_str)
            if is_error:
                self._log.warning(
                    "McpServer: tool %r returned error envelope: [%s] %s",
                    name, error_code, error_msg,
                )
                from mcp import McpError
                from mcp.types import ErrorData, INTERNAL_ERROR
                raise McpError(
                    ErrorData(code=INTERNAL_ERROR, message=f"[{error_code}] {error_msg}")
                )

            return [TextContent(type="text", text=content_str)]

        # ------------------------------------------------------------------
        # Transport branches
        # ------------------------------------------------------------------

        if resolved_transport == "stdio":
            await self._start_stdio()
        else:
            await self._start_http()

    async def handle_initialize(self) -> None:
        """Documentation anchor for initialization-time logic.

        In mcp 1.27.0 the lowlevel ServerSession handles initialize automatically
        via create_initialization_options().  No custom handler is required.
        This method exists as a future hook for auth-header inspection or
        agent-identity whitelisting on the HTTP transport (v0.6.x scope: not needed).
        """

    async def handle_tools_list(self) -> list:
        """Return the list of mcp.types.Tool objects for the registered senses.

        This is a documentation method showing the contract of the list_tools
        handler registered inside start().  The live handler is the closure
        ``_handle_list_tools`` defined in start().

        Returns:
            list[mcp.types.Tool] — one entry per tool schema from all registered senses.
        """
        from mcp.types import Tool

        openai_tools = self._dispatcher.all_tool_definitions()
        tools: list[Tool] = []
        for openai_tool in openai_tools:
            try:
                mcp_dict = convert_to_mcp_tool(openai_tool)
                tools.append(Tool(**mcp_dict))
            except (TypeError, ValueError) as exc:
                self._log.warning(
                    "McpServer.handle_tools_list: skipping malformed tool schema: %s", exc
                )
        return tools

    async def handle_tools_call(self, name: str, arguments: dict) -> list:
        """Dispatch a tool call from an MCP client through the ToolDispatcher.

        This is a documentation method showing the contract of the call_tool
        handler registered inside start().  The live handler is the closure
        ``_handle_call_tool`` defined in start().

        Args:
            name:      The tool name, e.g. "smidja.screenshot".
            arguments: The tool arguments dict.

        Returns:
            list[mcp.types.TextContent] — the tool_result content serialised as JSON text.
        """
        from mcp.types import TextContent

        call_id = f"mcp-{uuid.uuid4().hex[:12]}"
        tool_call = {
            "id": call_id,
            "type": "function",
            "function": {
                "name": name,
                "arguments": json.dumps(arguments if arguments is not None else {}),
            },
        }
        tool_result = await self._dispatcher.dispatch(tool_call)
        content_str: str = tool_result.get("content", "{}")
        return [TextContent(type="text", text=content_str)]

    # ------------------------------------------------------------------
    # Private transport methods
    # ------------------------------------------------------------------

    async def _start_stdio(self) -> None:
        """Open the stdio transport and run the MCP server loop.

        Uses ``mcp.server.stdio.stdio_server()`` which yields a pair of anyio
        memory-object streams connected to process stdin/stdout.  The server
        blocks until the client closes the pipe (EOF on stdin), which signals
        normal shutdown (e.g. Claude Desktop exits).

        Auth note: stdio transport auth is implicit — the OS pipe IS the trust
        boundary.  The MCP client (Claude Desktop, Continue) owns the subprocess
        and its stdin/stdout channels.  No bearer-token layer is added here.
        """
        from mcp.server.stdio import stdio_server

        self._log.info(
            "McpServer: opening stdio transport — server ready for MCP client."
        )
        try:
            async with stdio_server() as (read_stream, write_stream):
                init_opts = self._mcp.create_initialization_options()
                await self._mcp.run(
                    read_stream,
                    write_stream,
                    init_opts,
                    raise_exceptions=False,
                )
        except Exception as exc:
            from heretic.skilningr.errors import TransportError
            raise TransportError(
                f"McpServer stdio transport error: {type(exc).__name__}: {exc}"
            ) from exc
        finally:
            self._log.info("McpServer: stdio transport closed.")

    async def _start_http(self) -> None:
        """Open the HTTP (Streamable HTTP) transport and run the uvicorn server.

        Two-gate remote-bind enforcement (Cartographer thread #4 / allow_remote_bind
        invariant):  A non-loopback bind address requires BOTH:
            (a) self._config.host not in (127.0.0.1, localhost, ::1)  [non-loopback]
            (b) self._config.allow_remote_bind == True                 [explicit opt-in]
        If (a) is True and (b) is False, McpAuthError is raised at startup —
        before uvicorn binds the socket — so no network exposure occurs.

        Starlette mounts the StreamableHTTPSessionManager ASGI app at the root
        (``/``).  MCP clients connect to ``http://host:port/`` per the Streamable
        HTTP transport spec.
        """
        from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
        from starlette.applications import Starlette
        from starlette.routing import Mount
        import uvicorn
        from heretic.skilningr.errors import McpAuthError, TransportError

        # Two-gate remote-bind safety check (mirrors Vébond pattern)
        _loopback_hosts = {"127.0.0.1", "localhost", "::1"}
        is_loopback = self._config.host in _loopback_hosts
        if not is_loopback and not self._config.allow_remote_bind:
            raise McpAuthError(
                f"McpServer HTTP transport: host {self._config.host!r} is not loopback "
                f"but allow_remote_bind is False. "
                f"Set skilningr.mcp_server.allow_remote_bind: true in heretic.yaml "
                f"to permit non-loopback MCP HTTP access. "
                f"Ensure bearer-token authentication middleware is configured before "
                f"enabling remote MCP access."
            )

        self._log.info(
            "McpServer: opening HTTP transport on %s:%d (allow_remote_bind=%s).",
            self._config.host,
            self._config.port,
            self._config.allow_remote_bind,
        )

        # Streamable HTTP session manager wraps the lowlevel Server as an ASGI app.
        # stateless=False (default) enables proper session tracking — required for
        # multi-turn interactions (initialize + list_tools + call_tool in one session).
        session_manager = StreamableHTTPSessionManager(
            app=self._mcp,
            json_response=False,
            stateless=False,
        )

        async def _handle_mcp(scope: dict, receive: object, send: object) -> None:
            await session_manager.handle_request(scope, receive, send)  # type: ignore[arg-type]

        starlette_app = Starlette(
            routes=[Mount("/", app=_handle_mcp)],  # type: ignore[list-item]
        )

        uvicorn_config = uvicorn.Config(
            starlette_app,
            host=self._config.host,
            port=self._config.port,
            log_level="warning",  # uvicorn access logs go to warning; MCP logs via heretic logger
        )
        uvicorn_server = uvicorn.Server(uvicorn_config)

        try:
            async with session_manager.run():
                await uvicorn_server.serve()
        except Exception as exc:
            raise TransportError(
                f"McpServer HTTP transport error: {type(exc).__name__}: {exc}"
            ) from exc
        finally:
            self._log.info(
                "McpServer: HTTP transport closed (%s:%d).",
                self._config.host,
                self._config.port,
            )
