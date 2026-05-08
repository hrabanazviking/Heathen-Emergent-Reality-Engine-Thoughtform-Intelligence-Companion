"""
Placeholder tests for the Vébond WebSocket server and EventBus.

These tests are skip-marked during the scaffold phase. Forge activates them
when FastAPI, uvicorn, websockets, and pydantic are installed (pip install heretic[serve]).

The structure below defines the expected test surface. Forge implements each body,
likely using pytest-asyncio and httpx.AsyncClient for HTTP tests and websockets
for WebSocket tests.

Canonical reference: src/heretic/vebond/serve.py
"""

import pytest


class TestEventBus:
    """EventBus subscribe/publish contract."""

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_subscribe_and_publish(self) -> None:
        # Forge: from heretic.vebond.serve import EventBus
        #        from heretic.vebond.protocol import TungaActivity
        #        received = []
        #        bus = EventBus()
        #        bus.subscribe("tunga.activity", received.append)
        #        event = TungaActivity(state="speaking")
        #        bus.publish(event)
        #        assert len(received) == 1
        #        assert received[0].state == "speaking"
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_catchall_subscription(self) -> None:
        # Forge: bus receives all events regardless of type when subscribed with '*'
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_publish_to_unsubscribed_type_is_noop(self) -> None:
        # Forge: publishing an event with no subscribers does not raise
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    @pytest.mark.asyncio
    async def test_async_handler_invoked(self) -> None:
        # Forge: subscribe an async handler, publish event, confirm handler is awaited
        pass


class TestWebSocketServerHealth:
    """WebSocketServer /health endpoint."""

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates with [serve] installed")
    @pytest.mark.asyncio
    async def test_health_endpoint_returns_200(self) -> None:
        # Forge: use httpx.AsyncClient with ASGITransport to test the FastAPI app
        #        directly without binding a real port:
        #        from heretic.vebond.config_model import VebondConfig
        #        from heretic.vebond.serve import WebSocketServer, EventBus
        #        import httpx
        #        from httpx import AsyncClient
        #        server = WebSocketServer(VebondConfig(), EventBus())
        #        app = server._create_app()
        #        async with AsyncClient(app=app, base_url="http://test") as client:
        #            resp = await client.get("/health")
        #        assert resp.status_code == 200
        #        assert resp.json()["status"] == "ok"
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    @pytest.mark.asyncio
    async def test_health_endpoint_includes_version(self) -> None:
        # Forge: assert resp.json()["version"] == heretic.__version__
        pass


class TestWebSocketConnection:
    """WebSocketServer /ws WebSocket endpoint."""

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates with [serve] installed")
    @pytest.mark.asyncio
    async def test_ws_accepts_connection(self) -> None:
        # Forge: use starlette.testclient.TestClient or httpx websocket
        #        support to confirm /ws upgrades and accepts connection
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    @pytest.mark.asyncio
    async def test_ws_receives_event_after_publish(self) -> None:
        # Forge: connect to /ws, publish a CeremonyStateChanged event via EventBus,
        #        read the WS message, decode as JSON, assert type == "ceremony.state_changed"
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    @pytest.mark.asyncio
    async def test_ws_dispatches_light_command(self) -> None:
        # Forge: connect to /ws, send {"type": "light"} as text frame,
        #        assert that the command handler is invoked (mock or spy)
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    @pytest.mark.asyncio
    async def test_ws_rejects_oversized_message(self) -> None:
        # Forge: configure VebondConfig(max_message_size_bytes=100)
        #        send a message > 100 bytes to /ws
        #        assert an error event with source='vebond' is received
        #        assert connection remains open (not closed for this error)
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    @pytest.mark.asyncio
    async def test_ws_handles_malformed_json(self) -> None:
        # Forge: send "not valid json" to /ws
        #        assert an ErrorEvent (level='warn') is received
        #        assert connection remains open
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    @pytest.mark.asyncio
    async def test_ws_handles_unknown_command_type(self) -> None:
        # Forge: send {"type": "totally_unknown"} to /ws
        #        assert an ErrorEvent is received
        #        assert connection remains open
        pass


class TestWebSocketServerBindError:
    """WebSocketServer raises VebondBindError when port is in use."""

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    @pytest.mark.asyncio
    async def test_start_raises_on_port_conflict(self) -> None:
        # Forge: bind a socket to a port, then call WebSocketServer.start() with
        #        the same port and assert VebondBindError is raised
        pass
