"""
Vébond WebSocket server — L4 Eldahús IPC backend.

This module provides:
    - WebSocketServer: manages the FastAPI app, the /ws endpoint, and the /health
      endpoint. Binds to the address specified in VebondConfig.
    - EventBus: in-process publish/subscribe bus. Backend layers publish events;
      WebSocketServer delivers them to all connected WebSocket clients.

All method bodies in this skeleton raise NotImplementedError with a clear message
describing what Forge must implement.

Forge implementation guide (priority order):
    1. EventBus.subscribe() / EventBus.publish() — these are called by all layers;
       implement first so integration tests can stub event flow.
    2. WebSocketServer._create_app() — build the FastAPI app with /health and /ws.
    3. WebSocketServer.start() — bind uvicorn, handle VebondBindError on port conflict.
    4. WebSocketServer._handle_ws() — accept WS connection, read commands, fan-out events.
    5. WebSocketServer.stop() — clean drain of connected clients, then server shutdown.

Dependencies (install with pip install heretic[serve]):
    fastapi>=0.110
    uvicorn[standard]>=0.27
    websockets>=12
    pydantic>=2.5
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Optional

from heretic.vebond.config_model import VebondConfig
from heretic.vebond.errors import VebondBindError, VebondError, ProtocolError


class EventBus:
    """In-process publish/subscribe bus for IPC events.

    Layers call publish() to emit ProtocolEvent instances. WebSocketServer
    subscribes to all event types and serializes them to connected WebSocket clients.
    Any other component (e.g. integration tests, future logging sinks) may also subscribe.

    Thread safety: Forge must ensure that publish() is safe to call from async
    context (from within asyncio tasks). Use asyncio.Queue or asyncio.Lock as
    appropriate — the choice is Forge's to make during implementation.

    The subscribe/publish interface is intentionally minimal so that early
    integration tests can inject a mock EventBus without pulling in FastAPI.
    """

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Any], None],
    ) -> None:
        """Register a handler for a specific event type.

        Args:
            event_type: The value of the 'type' field on ProtocolEvent models.
                        Example: 'ceremony.state_changed', 'agent.token'.
                        Use '*' to subscribe to all event types (catch-all).
            handler:    Callable invoked with the ProtocolEvent model instance
                        whenever a matching event is published. The handler may
                        be a coroutine (async def); EventBus must await it.

        Forge implementation note:
            Store handlers in a dict[str, list[Callable]]. The '*' catch-all
            should be maintained as a separate list and called for every event.
        """
        raise NotImplementedError(
            "Forge will implement: store handler in a per-type registry. "
            "Support '*' as a catch-all. EventBus must be safe to use from "
            "asyncio tasks — use asyncio primitives, not threading locks."
        )

    def publish(self, event: Any) -> None:
        """Publish a ProtocolEvent to all matching subscribers.

        Args:
            event: A ProtocolEvent model instance (CeremonyStateChanged,
                   BifrostHealth, TungaActivity, etc.). The event's 'type'
                   field is used to route to registered handlers.

        Forge implementation note:
            Iterate the per-type handler list and the catch-all list. Invoke
            each handler. If the handler is a coroutine, schedule it with
            asyncio.ensure_future() — publish() itself must be synchronous so
            that non-async callers (e.g. Lifecycle state machine callbacks)
            can call it safely.
        """
        raise NotImplementedError(
            "Forge will implement: route event to all subscribers for event.type "
            "and all '*' catch-all subscribers. Schedule coroutine handlers via "
            "asyncio.ensure_future(). Log a warning if a handler raises."
        )


class WebSocketServer:
    """L4 Vébond WebSocket and REST server.

    Wraps a FastAPI application serving:
        GET  /health  — returns JSON health status (always 200 if server is up)
        GET  /ws      — WebSocket upgrade endpoint; accepts client connections

    One WebSocketServer instance per HERETIC process. Lifecycle:
        1. Forge Worker constructs WebSocketServer(config, event_bus)
        2. Forge Worker calls await server.start() — binds port, begins serving
        3. EventBus publishes events -> server fans them out to all connected clients
        4. WebSocket clients send commands -> server dispatches to command handlers
        5. Forge Worker calls await server.stop() during Slokna teardown

    The server is localhost-only by default (VebondConfig.ws_host = '127.0.0.1').
    Non-loopback binds require allow_remote_bind: true and are rejected by
    VebondConfig.__post_init__ at construction time.
    """

    def __init__(
        self,
        config: VebondConfig,
        event_bus: EventBus,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Construct the server but do not bind the port yet.

        Args:
            config:    Typed VebondConfig. All server parameters (host, port,
                       max_message_size_bytes, heartbeat) are read from here.
            event_bus: The shared EventBus. WebSocketServer subscribes to all
                       events ('*') on start() and fans them out to WS clients.
            logger:    Optional logger. If None, a logger named 'heretic.vebond.serve'
                       will be created via heretic.grunnr.logger.get_logger().
        """
        self.config = config
        self.event_bus = event_bus
        self._logger = logger or logging.getLogger("heretic.vebond.serve")
        self._app: Any = None  # FastAPI app; created in _create_app()
        self._server: Any = None  # uvicorn Server instance; created in start()
        self._connected_clients: set[Any] = set()  # WebSocket connection objects

    def _create_app(self) -> Any:
        """Create and return the FastAPI application instance.

        The app must include:
            GET /health  — returns {'status': 'ok', 'version': heretic.__version__}
            GET /ws      — WebSocket upgrade; calls self._handle_ws(websocket)

        Forge implementation note:
            Import fastapi inside this method (not at module level) so that importing
            heretic.vebond.serve does not fail when fastapi is not installed.
            Raise a clear ImportError with the install hint if fastapi is missing.

        Returns:
            FastAPI: the configured application instance.

        Raises:
            ImportError: if fastapi is not installed.
        """
        raise NotImplementedError(
            "Forge will implement: create FastAPI app, register /health GET endpoint "
            "returning {'status': 'ok', 'version': heretic.__version__}, register "
            "/ws WebSocket endpoint calling self._handle_ws(websocket). "
            "Import fastapi inside this method to guard against missing dep gracefully."
        )

    async def _handle_ws(self, websocket: Any) -> None:
        """Handle one WebSocket client connection for its full lifetime.

        Called by FastAPI for each new /ws connection. Must:
            1. Add websocket to self._connected_clients
            2. Subscribe a fan-out coroutine to the event_bus ('*') that serializes
               ProtocolEvent models to JSON and sends via websocket.send_text()
            3. Read incoming messages in a loop:
               a. Check message size against config.max_message_size_bytes
               b. Parse as ProtocolCommand (via pydantic TypeAdapter)
               c. Dispatch to the appropriate command handler
               d. On ProtocolError or MessageTooLargeError: send ErrorEvent (level='warn')
                  and continue — do not close the connection for a single bad message
            4. On disconnect (WebSocketDisconnect): remove from self._connected_clients,
               clean up the fan-out subscription

        Forge implementation note:
            The fan-out must be an asyncio task or coroutine driven by an asyncio.Queue
            so that event publication does not block the command read loop. The two
            loops (read commands / write events) must run concurrently per connection.

            Heartbeat: send ping frames every config.heartbeat_interval_seconds seconds.
            If no pong received within config.connection_timeout_seconds: close cleanly.

        Args:
            websocket: FastAPI WebSocket instance.
        """
        raise NotImplementedError(
            "Forge will implement: accept WS connection, register event fan-out task, "
            "read/dispatch commands in loop, handle disconnect. "
            "See docs/architecture/IPC_PROTOCOL.md for the full command/event schema. "
            "See VebondConfig for heartbeat_interval_seconds and connection_timeout_seconds."
        )

    async def start(self) -> None:
        """Bind the server to the configured address and begin serving.

        This coroutine returns only when the server is fully bound and ready to
        accept connections. It does NOT block indefinitely — the caller (Forge)
        is responsible for keeping the event loop alive (e.g. by running the main
        ceremony turn loop concurrently with the server).

        Forge implementation note:
            1. Call self._create_app() to get the FastAPI instance.
            2. Configure uvicorn.Config with host=self.config.ws_host,
               port=self.config.ws_port, log_level='warning' (uvicorn's own
               logging should not overwhelm the heretic log).
            3. Construct uvicorn.Server(config) and call server.startup().
            4. If the OS raises OSError (port in use): raise VebondBindError with
               a user-readable message including the port number.
            5. Subscribe self._fan_out_all to event_bus('*') so events start
               flowing to connected clients immediately.

        Raises:
            VebondBindError: if the configured host/port cannot be bound.
            VebondError: on any other server startup failure.
        """
        raise NotImplementedError(
            "Forge will implement: create FastAPI app, configure uvicorn, bind port, "
            "subscribe to EventBus. Raise VebondBindError on port conflict. "
            f"Target: ws://{self.config.ws_host}:{self.config.ws_port}/ws"
        )

    async def stop(self) -> None:
        """Gracefully stop the server and close all connected clients.

        Called during Slokna teardown. Must:
            1. Stop accepting new connections
            2. Send a close frame to all currently connected WebSocket clients
            3. Wait for all clients to disconnect (with a brief timeout)
            4. Shut down the uvicorn server cleanly

        Forge implementation note:
            Use asyncio.gather() with a timeout (suggest: 5 seconds) to wait for
            client disconnects. After the timeout, forcibly close any remaining
            connections. Log a warning for each client that did not disconnect cleanly.

        Raises:
            VebondError: on unexpected server shutdown failure.
        """
        raise NotImplementedError(
            "Forge will implement: stop uvicorn server, close all WS client connections "
            "gracefully with a timeout, log any forced disconnects."
        )
