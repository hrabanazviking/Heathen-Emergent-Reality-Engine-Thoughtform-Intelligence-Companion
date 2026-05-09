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

import logging
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
    # Public API
    # ------------------------------------------------------------------

    async def start(self, transport: Literal["stdio", "http"] | None = None) -> None:
        """Open the MCP transport and enter the request–response loop.

        For stdio transport: calls ``mcp.server.stdio.stdio_server()`` and
            then ``self._mcp.run(read_stream, write_stream, init_opts)``.
            Blocks until the client closes the pipe (EOF on stdin).

        For http transport: constructs a
            ``mcp.server.streamable_http_manager.StreamableHTTPSessionManager``
            and launches uvicorn at McpServerConfig.host:port.
            Non-loopback bind addresses require allow_remote_bind==True.

        Handler registration (list_tools, call_tool) happens HERE — inside
        start() — so that the dispatcher is guaranteed to be populated before
        the first client request arrives.

        Args:
            transport: Override the transport from McpServerConfig.  If None,
                       uses self._config.transport.  Must be "stdio" or "http".

        Raises:
            NotImplementedError: always — Forge implements this body.
        """
        raise NotImplementedError(
            "McpServer.start() — Forge implements: "
            "(1) resolve transport from arg or config.transport; "
            "(2) register @self._mcp.list_tools() handler that calls "
            "    self._dispatcher.all_tool_definitions() and maps each through "
            "    convert_to_mcp_tool, then constructs mcp.types.Tool(**mcp_dict); "
            "(3) register @self._mcp.call_tool() handler that calls "
            "    await self._dispatcher.dispatch(tool_call_dict) and returns "
            "    [mcp.types.TextContent(type='text', text=json.dumps(result))]; "
            "(4a) stdio: async with mcp.server.stdio.stdio_server() as (r, w): "
            "     init_opts = self._mcp.create_initialization_options(); "
            "     await self._mcp.run(r, w, init_opts); "
            "(4b) http: build Starlette app with "
            "     StreamableHTTPSessionManager(self._mcp).handle() mounted at '/mcp'; "
            "     if config.host != '127.0.0.1' and not config.allow_remote_bind: raise; "
            "     uvicorn.run(app, host=config.host, port=config.port); "
            "(5) handle SIGINT gracefully (cancel the anyio task group)."
        )

    async def handle_initialize(self) -> None:
        """Return the MCP initialization result for the connecting client.

        In the mcp 1.27.0 lowlevel API, initialization is handled automatically
        by mcp.server.session.ServerSession — the host does not need to
        implement a custom handler.  This method is kept as a documentation
        anchor and may be used by Forge to inject custom initialization-time
        capability negotiation (e.g. checking agent identity headers on http
        transport).

        Raises:
            NotImplementedError: always — Forge implements if bespoke init logic
                                 is required; otherwise remove and rely on SDK defaults.
        """
        raise NotImplementedError(
            "McpServer.handle_initialize() — Forge implements if custom "
            "initialization-time logic is needed.  In the mcp 1.27.0 SDK, "
            "initialization is handled by ServerSession automatically via the "
            "InitializeRequest → create_initialization_options() path.  "
            "This hook exists for auth-header inspection or agent-identity "
            "whitelisting on the HTTP transport."
        )

    async def handle_tools_list(self) -> list:
        """Return the list of mcp.types.Tool objects for the registered senses.

        This is the handler body Forge registers with @self._mcp.list_tools().
        It converts every OpenAI-format tool schema from the dispatcher into an
        mcp.types.Tool instance via convert_to_mcp_tool().

        Expected return type:
            list[mcp.types.Tool]
            The SDK wraps this into ListToolsResult automatically (old-style API).

        Raises:
            NotImplementedError: always — Forge registers this as the actual
                                 @self._mcp.list_tools() handler inside start().
        """
        raise NotImplementedError(
            "McpServer.handle_tools_list() — Forge implements: "
            "tools = [] "
            "for openai_tool in self._dispatcher.all_tool_definitions(): "
            "    mcp_dict = convert_to_mcp_tool(openai_tool); "
            "    tools.append(mcp.types.Tool(**mcp_dict)); "
            "return tools"
        )

    async def handle_tools_call(self, name: str, arguments: dict) -> list:
        """Dispatch a tool call from an MCP client through the ToolDispatcher.

        This is the handler body Forge registers with @self._mcp.call_tool().
        It translates the MCP (name, arguments) pair into an OpenAI-format
        tool_call dict, dispatches it, and translates the tool_result back into
        an MCP content list.

        Args:
            name:      The tool name, e.g. "smidja.screenshot".
            arguments: The tool arguments dict (SDK has already validated against
                       inputSchema if validate_input=True on the decorator call).

        Returns:
            list[mcp.types.TextContent] — the tool_result content serialised as
            JSON text.  Structured content (dict) may be added in a future pass.

        Raises:
            NotImplementedError: always — Forge registers this as the actual
                                 @self._mcp.call_tool() handler inside start().
        """
        raise NotImplementedError(
            "McpServer.handle_tools_call(name, arguments) — Forge implements: "
            "import json, mcp.types; "
            "tool_call = { "
            "    'id': f'mcp_{name}_{id(arguments)}', "
            "    'type': 'function', "
            "    'function': {'name': name, 'arguments': json.dumps(arguments)} "
            "}; "
            "result = await self._dispatcher.dispatch(tool_call); "
            "content_str = result.get('content', json.dumps(result)); "
            "return [mcp.types.TextContent(type='text', text=content_str)]"
        )
