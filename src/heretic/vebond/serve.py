"""
Vebond WebSocket server — L4 Eldahus IPC backend.

This module provides:
    - EventBus: in-process publish/subscribe bus. Backend layers publish ProtocolEvent
      instances; WebSocketServer delivers them to all connected WebSocket clients.
    - WebSocketServer: manages the FastAPI app, the /ws endpoint, and the /health
      endpoint. Binds to the address specified in VebondConfig.

Architecture decisions (recorded here for future Architect review):

    EventBus async strategy: the bus uses a synchronous dictionary of handler lists.
    publish() is synchronous so that non-async callers (e.g. Lifecycle state machine
    callbacks, hooks registered from cli.py) can call it safely from any context.
    Coroutine handlers are scheduled via asyncio.ensure_future() when an event loop
    is running; if no loop is running (e.g. in a test without asyncio), the async
    handler is silently skipped with a warning. This is the simplest design that
    handles both sync and async callers without a threading.Thread or asyncio.Queue
    per subscriber.

    Per-connection fan-out: each WebSocket connection gets its own asyncio.Queue.
    The EventBus '*' catchall pushes into all live connection queues; a dedicated
    asyncio Task per connection drains the queue and sends JSON frames. This
    separates the publish path (fast, synchronous) from the send path (async, can
    block on slow clients).

    Heartbeat: a separate asyncio Task per connection sends WS ping frames at
    config.heartbeat_interval_seconds. If uvicorn's websocket transport handles pong
    automatically (which it does via websockets library), we just send pings and let
    the transport close the connection on timeout rather than implementing our own
    pong timeout — uvicorn/websockets handles this for us.

Canonical reference: docs/architecture/IPC_PROTOCOL.md
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Set

from heretic.vebond.config_model import VebondConfig
from heretic.vebond.errors import VebondBindError, VebondError, ProtocolError, MessageTooLargeError

# FastAPI is an optional [serve] dependency. Import WebSocket at module level with a
# guard so that FastAPI's dependency resolver can recognize the WebSocket annotation
# in websocket_endpoint routes. (Without a module-level import, the deferred
# annotations from `from __future__ import annotations` cannot be resolved against
# the module's global namespace, causing FastAPI to treat `websocket: WebSocket`
# as a query parameter rather than the WebSocket injection.)
try:
    from fastapi import WebSocket as _FastAPIWebSocket
except ImportError:
    _FastAPIWebSocket = Any  # type: ignore[assignment, misc]


# ==============================================================================
# EventBus
# ==============================================================================

class EventBus:
    """In-process publish/subscribe bus for IPC protocol events.

    Layers call publish() to emit ProtocolEvent instances. WebSocketServer
    subscribes via a queue-based mechanism to receive all events and forward them
    to connected WebSocket clients.

    Handler contract:
        - Sync handlers: called directly in publish().
        - Async handlers: scheduled via asyncio.ensure_future() if a loop is running.
        - Both receive the raw event object (a pydantic BaseModel instance).

    Thread safety: all operations modify Python dicts and lists, which are
    protected by the GIL in CPython 3.10. For coroutine safety the publish()
    method uses asyncio.ensure_future() which is safe to call from any async task.
    """

    def __init__(self) -> None:
        # Registry: maps event type string (or "*") to list of handlers.
        self._handlers: Dict[str, List[Callable]] = {}
        # Weak per-connection queues: each live WS connection registers a queue
        # that receives all published events. WebSocketServer manages this set.
        self._queues: Set[asyncio.Queue] = set()

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Any], Any],
    ) -> Callable[[], None]:
        """Register a handler for a specific event type.

        Args:
            event_type: The 'type' field value on ProtocolEvent models, e.g.
                        'ceremony.state_changed'. Use '*' to receive all events.
            handler:    Callable(event) -> None | Awaitable. May be a coroutine.

        Returns:
            An unsubscribe callable. Call it to deregister the handler.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

        def _unsubscribe() -> None:
            try:
                self._handlers[event_type].remove(handler)
            except (ValueError, KeyError):
                pass  # Already removed — no-op

        return _unsubscribe

    def publish(self, event: Any) -> None:
        """Publish a ProtocolEvent to all matching subscribers and connection queues.

        Args:
            event: A ProtocolEvent model instance. Must have a 'type' attribute.

        This method is synchronous so non-async callers can use it freely.
        Async handlers are scheduled on the running event loop if one exists.
        """
        event_type: str = getattr(event, "type", "")

        # Gather all applicable handlers: type-specific + catch-all
        handlers: List[Callable] = []
        handlers.extend(self._handlers.get(event_type, []))
        handlers.extend(self._handlers.get("*", []))

        for handler in handlers:
            try:
                result = handler(event)
                # If handler returned a coroutine, schedule it
                if asyncio.iscoroutine(result):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(result)
                    except RuntimeError:
                        # No running loop — close the coroutine to avoid ResourceWarning
                        result.close()
                        logging.getLogger("heretic.vebond.event_bus").warning(
                            "Async handler called outside event loop for event '%s' — skipped",
                            event_type,
                        )
            except Exception as exc:
                logging.getLogger("heretic.vebond.event_bus").warning(
                    "EventBus handler raised for event '%s': %s", event_type, exc
                )

        # Push into all live per-connection queues (non-blocking)
        for queue in list(self._queues):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logging.getLogger("heretic.vebond.event_bus").warning(
                    "Connection event queue full — dropping event '%s'", event_type
                )

    def add_connection_queue(self, queue: asyncio.Queue) -> None:
        """Register a per-connection event queue. Called by WebSocketServer on connect."""
        self._queues.add(queue)

    def remove_connection_queue(self, queue: asyncio.Queue) -> None:
        """Remove a per-connection event queue. Called by WebSocketServer on disconnect."""
        self._queues.discard(queue)


# ==============================================================================
# WebSocketServer
# ==============================================================================

class WebSocketServer:
    """L4 Vebond WebSocket and REST server.

    Wraps a FastAPI application serving:
        GET  /health  — returns JSON health status (always 200 if server is up)
        GET  /ws      — WebSocket upgrade endpoint; accepts client connections

    Lifecycle:
        1. CLI constructs WebSocketServer(config, event_bus, command_handlers, logger)
        2. CLI calls await server.start() — binds port, begins serving
        3. EventBus publishes events -> server fans them out to all connected clients
        4. WebSocket clients send commands -> server dispatches to command_handlers
        5. CLI calls await server.stop() during Slokna teardown
    """

    def __init__(
        self,
        config: VebondConfig,
        event_bus: EventBus,
        command_handlers: Optional[Dict[str, Callable]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Construct the server but do not bind the port yet.

        Args:
            config:           Typed VebondConfig. All server parameters read from here.
            event_bus:        The shared EventBus instance.
            command_handlers: Maps command 'type' string to a handler coroutine/callable.
                              Example: {"light": handle_light, "extinguish": handle_extinguish}
                              If None, all commands receive an 'unhandled' error response.
            logger:           Optional logger; defaults to 'heretic.vebond.serve'.
        """
        self.config = config
        self.event_bus = event_bus
        self._command_handlers: Dict[str, Callable] = command_handlers or {}
        self._logger = logger or logging.getLogger("heretic.vebond.serve")
        self._app: Any = None      # FastAPI app; created in _create_app()
        self._server: Any = None   # uvicorn Server instance; created in start()
        # Currently connected WebSocket objects (for broadcast on stop)
        self._connected_clients: Set[Any] = set()
        # Track the current ceremony lifecycle state for snapshot on connect
        self._current_lifecycle_state: str = "hvild"

    def _create_app(self) -> Any:
        """Create and return the FastAPI application instance.

        Registers:
            GET  /health  — heartbeat; always 200 when server is up
            GET  /ws      — WebSocket upgrade; calls _handle_ws per connection

        Imports fastapi inside this method to guard against missing dep gracefully.

        Returns:
            FastAPI: the configured application instance.

        Raises:
            ImportError: if fastapi is not installed (pip install heretic[serve]).
        """
        try:
            from fastapi import FastAPI, WebSocket, WebSocketDisconnect
        except ImportError as exc:
            raise ImportError(
                "fastapi is required for heretic serve. "
                "Install it with: pip install heretic[serve]"
            ) from exc

        import heretic

        app = FastAPI(
            title="HERETIC Vebond",
            description="L4 Vebond IPC WebSocket server — Summoning Circle backend",
            version=heretic.__version__,
            # Disable default OpenAPI docs (not needed for a WebSocket IPC server)
            docs_url=None,
            redoc_url=None,
        )

        # Capture reference to self for use in route closures
        server_ref = self

        @app.get("/health")
        async def health() -> dict:
            """Health check endpoint. Returns 200 when server is up."""
            return {
                "status": "ok",
                "version": heretic.__version__,
                "lifecycle_state": server_ref._current_lifecycle_state,
            }

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: _FastAPIWebSocket) -> None:
            """WebSocket endpoint — one connection per client.

            _FastAPIWebSocket is imported at the module level so that FastAPI's
            dependency resolver can recognize this as the WebSocket injection
            parameter when resolving deferred annotations (from __future__ import
            annotations). See module header comment for explanation.
            """
            await server_ref._handle_ws(websocket)

        return app

    async def _handle_ws(self, websocket: Any) -> None:
        """Handle one WebSocket client connection for its full lifetime.

        Protocol (per IPC_PROTOCOL.md §5 Connection Lifecycle):
            1. Accept the connection
            2. Register a per-connection asyncio.Queue on the EventBus
            3. Push current-state snapshot events immediately
            4. Run two concurrent tasks:
               a. Fan-out task: drain the queue and send events as JSON frames
               b. Read loop: parse commands and dispatch to command_handlers
            5. On disconnect: remove queue from EventBus, clean up tasks

        Args:
            websocket: FastAPI WebSocket instance.
        """
        try:
            from fastapi import WebSocketDisconnect
        except ImportError as exc:
            raise ImportError(
                "fastapi is required for heretic serve. "
                "Install it with: pip install heretic[serve]"
            ) from exc

        try:
            from pydantic import TypeAdapter, ValidationError
        except ImportError as exc:
            raise ImportError(
                "pydantic is required for heretic serve. "
                "Install it with: pip install heretic[serve]"
            ) from exc

        # Accept the WebSocket upgrade
        await websocket.accept()
        self._connected_clients.add(websocket)
        self._logger.info(
            "WebSocket client connected: %s", websocket.client
        )

        # Per-connection event queue — EventBus pushes events here
        connection_queue: asyncio.Queue = asyncio.Queue(maxsize=256)
        self.event_bus.add_connection_queue(connection_queue)

        # Subscribe to EventBus updates about lifecycle state for snapshot tracking
        def _track_lifecycle(event: Any) -> None:
            if getattr(event, "type", "") == "ceremony.state_changed":
                self._current_lifecycle_state = getattr(event, "to_state", self._current_lifecycle_state)
        unsub_tracker = self.event_bus.subscribe("ceremony.state_changed", _track_lifecycle)

        # Helper: send a single event model to this client
        async def _send_event(event: Any) -> None:
            try:
                # pydantic model: use model_dump_json for correct serialization
                if hasattr(event, "model_dump_json"):
                    await websocket.send_text(event.model_dump_json())
                else:
                    await websocket.send_text(json.dumps(event))
            except Exception as exc:
                self._logger.debug("Failed to send event to client: %s", exc)

        # Helper: send a raw error dict (used before pydantic models are available)
        async def _send_error(level: str, source: str, message: str) -> None:
            try:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "level": level,
                    "source": source,
                    "message": message,
                }))
            except Exception:
                pass

        # Push current-state snapshot immediately on connect
        # This lets the frontend initialize its UI without waiting for the next transition
        try:
            from heretic.vebond.protocol import (
                CeremonyStateChanged,
                BifrostHealth,
                TungaActivity,
                HlustActivity,
            )
            import datetime

            snapshot_ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")

            # Ceremony state snapshot
            await _send_event(CeremonyStateChanged(
                from_state=self._current_lifecycle_state,
                to_state=self._current_lifecycle_state,
                timestamp=snapshot_ts,
            ))
            # Bifrost health snapshot (closed by default; the CLI will publish real state)
            await _send_event(BifrostHealth(
                status="closed",
                endpoint="",
                latency_ms=None,
            ))
            # Voice layer snapshots
            await _send_event(TungaActivity(state="idle"))
            await _send_event(HlustActivity(state="idle", level_db=None))
        except Exception as exc:
            self._logger.warning("Failed to send snapshot on connect: %s", exc)

        # Fan-out task: drain connection queue and send to this client
        async def _fanout_task() -> None:
            while True:
                try:
                    event = await asyncio.wait_for(
                        connection_queue.get(), timeout=self.config.heartbeat_interval_seconds
                    )
                    await _send_event(event)
                except asyncio.TimeoutError:
                    # Send a WebSocket ping to keep the connection alive
                    try:
                        await websocket.send_text(json.dumps({"type": "_ping"}))
                    except Exception:
                        break
                except asyncio.CancelledError:
                    break
                except Exception as exc:
                    self._logger.debug("Fan-out task error: %s", exc)
                    break

        fanout_task = asyncio.ensure_future(_fanout_task())

        # Lazy-import pydantic TypeAdapter for command deserialization
        try:
            from heretic.vebond.protocol import ProtocolCommand
            _cmd_adapter = TypeAdapter(ProtocolCommand)
        except Exception as exc:
            self._logger.error("Failed to import ProtocolCommand adapter: %s", exc)
            await _send_error("error", "vebond", "Server protocol initialization failed.")
            fanout_task.cancel()
            self.event_bus.remove_connection_queue(connection_queue)
            unsub_tracker()
            self._connected_clients.discard(websocket)
            return

        # Command read loop
        try:
            while True:
                try:
                    # Receive the next text frame
                    raw = await websocket.receive_text()
                except WebSocketDisconnect:
                    self._logger.info("WebSocket client disconnected: %s", websocket.client)
                    break
                except Exception as exc:
                    self._logger.info("WebSocket receive error: %s", exc)
                    break

                # Check message size before doing anything else
                raw_bytes = len(raw.encode("utf-8"))
                if raw_bytes > self.config.max_message_size_bytes:
                    self._logger.warning(
                        "Oversized WS message: %d bytes (limit %d)",
                        raw_bytes,
                        self.config.max_message_size_bytes,
                    )
                    await _send_error(
                        "warn",
                        "vebond",
                        f"Message too large: {raw_bytes} bytes exceeds limit of "
                        f"{self.config.max_message_size_bytes} bytes. "
                        f"Adjust vebond.max_message_size_bytes in heretic.yaml if needed.",
                    )
                    # Keep connection open — oversized message is a client bug, not fatal
                    continue

                # Parse as ProtocolCommand
                try:
                    data = json.loads(raw)
                    command = _cmd_adapter.validate_python(data)
                except json.JSONDecodeError as exc:
                    self._logger.debug("Malformed JSON from client: %s", exc)
                    await _send_error(
                        "warn",
                        "vebond",
                        "Invalid JSON in command frame. Check client serialization.",
                    )
                    continue
                except ValidationError as exc:
                    # Unknown type or missing required fields
                    cmd_type = (data.get("type") if isinstance(data, dict) else "unknown")
                    self._logger.debug("Unknown/invalid command type '%s': %s", cmd_type, exc)
                    await _send_error(
                        "warn",
                        "vebond",
                        f"Unrecognized command type: '{cmd_type}'. "
                        f"Valid types: light, extinguish, send_message, cancel_turn, toggle_sense.",
                    )
                    continue
                except Exception as exc:
                    self._logger.warning("Unexpected command parse error: %s", exc)
                    await _send_error("warn", "vebond", "Failed to parse command.")
                    continue

                # Dispatch to command handler
                cmd_type = command.type
                handler = self._command_handlers.get(cmd_type)
                if handler is None:
                    self._logger.warning("No handler registered for command '%s'", cmd_type)
                    await _send_error(
                        "warn",
                        "vebond",
                        f"No handler registered for command '{cmd_type}'.",
                    )
                    continue

                try:
                    result = handler(command)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as exc:
                    self._logger.warning("Command handler '%s' raised: %s", cmd_type, exc)
                    await _send_error(
                        "error",
                        "vebond",
                        f"Command '{cmd_type}' failed: {exc}",
                    )

        finally:
            # Cleanup: remove from connected set, cancel fan-out task, deregister queue
            self._connected_clients.discard(websocket)
            fanout_task.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(fanout_task), timeout=1.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            unsub_tracker()
            self.event_bus.remove_connection_queue(connection_queue)
            self._logger.debug("WebSocket connection cleanup complete")

    async def start(self) -> None:
        """Bind the server to the configured address and begin serving.

        Creates the FastAPI app, configures uvicorn, and calls server.startup()
        to bind the port without blocking the event loop indefinitely.

        Raises:
            VebondBindError: if the configured host/port cannot be bound.
            VebondError: on any other server startup failure.
        """
        try:
            import uvicorn
        except ImportError as exc:
            raise VebondError(
                "uvicorn is required for heretic serve. "
                "Install it with: pip install heretic[serve]"
            ) from exc

        self._app = self._create_app()

        uv_config = uvicorn.Config(
            app=self._app,
            host=self.config.ws_host,
            port=self.config.ws_port,
            log_level="warning",   # Do not overwhelm heretic's own logging
            access_log=False,
            loop="asyncio",
            ws="websockets",
        )
        self._server = uvicorn.Server(uv_config)

        try:
            await self._server.startup()
        except OSError as exc:
            # Port already in use, permission denied, or interface not found
            raise VebondBindError(
                f"Cannot bind WebSocket server to {self.config.ws_host}:{self.config.ws_port}. "
                f"Port may already be in use, or the interface does not exist. "
                f"Change vebond.ws_port in heretic.yaml to a free port. "
                f"OS error: {exc}"
            ) from exc
        except Exception as exc:
            raise VebondError(
                f"Unexpected error starting WebSocket server: {exc}"
            ) from exc

        self._logger.info(
            "Vebond WebSocket server listening on ws://%s:%d/ws",
            self.config.ws_host,
            self.config.ws_port,
        )

    async def serve(self) -> None:
        """Run the server's main loop until shutdown is requested.

        Call start() first to bind the port, then serve() to handle requests.
        This coroutine runs indefinitely until stop() is called.
        """
        if self._server is None:
            raise VebondError("WebSocketServer.start() must be called before serve()")
        await self._server.main_loop()

    async def stop(self) -> None:
        """Gracefully stop the server and close all connected clients.

        Called during Slokna teardown. Sends close frames, waits briefly for
        clients to disconnect, then shuts down uvicorn.

        Raises:
            VebondError: on unexpected server shutdown failure.
        """
        if self._server is None:
            return  # Never started; nothing to stop

        self._logger.info("Vebond WebSocket server shutting down...")

        # Send close frames to all connected clients
        close_tasks = []
        for ws in list(self._connected_clients):
            try:
                close_tasks.append(ws.close(1001))  # 1001 Going Away
            except Exception:
                pass

        if close_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*close_tasks, return_exceptions=True),
                    timeout=5.0,
                )
            except asyncio.TimeoutError:
                self._logger.warning(
                    "Timed out waiting for %d client(s) to disconnect cleanly",
                    len(self._connected_clients),
                )

        # Shutdown uvicorn
        try:
            self._server.should_exit = True
            await asyncio.wait_for(self._server.shutdown(), timeout=10.0)
        except asyncio.TimeoutError:
            self._logger.warning("uvicorn shutdown timed out; forcing exit")
        except Exception as exc:
            self._logger.warning("uvicorn shutdown error: %s", exc)

        self._logger.info("Vebond WebSocket server stopped.")
