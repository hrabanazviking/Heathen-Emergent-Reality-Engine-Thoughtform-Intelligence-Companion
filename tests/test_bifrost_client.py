"""
Tests for bifrost.client — BifrostClient ABC and OpenAICompatClient.

Covers: capability defaults, open/close lifecycle, SSE parsing, tool call
assembly, error responses, and HTTP mocking via pytest-mock + httpx.
"""

from __future__ import annotations

import json
from typing import Any
from unittest import mock

import httpx
import pytest

from heretic.bifrost.client import BifrostClient, OpenAICompatClient
from heretic.bifrost.config_model import BifrostConfig, TailscaleOptions
from heretic.bifrost.errors import (
    BifrostError,
    BifrostConnectionError,
    BifrostAuthError,
    BifrostTimeoutError,
    BifrostProtocolError,
)


# ---------------------------------------------------------------------------
# BifrostClient is abstract
# ---------------------------------------------------------------------------

def test_bifrost_client_is_abstract() -> None:
    """BifrostClient cannot be instantiated directly — it is an ABC."""
    import inspect
    assert inspect.isabstract(BifrostClient)


# ---------------------------------------------------------------------------
# Default capability flags before open()
# ---------------------------------------------------------------------------

def test_openai_compat_client_default_capabilities() -> None:
    """OpenAICompatClient starts with all capability flags False before open()."""
    client = OpenAICompatClient(BifrostConfig())
    assert client.capability_tool_use is False
    assert client.capability_vision_in is False
    assert client.capability_streaming is False


# ---------------------------------------------------------------------------
# Error hierarchy
# ---------------------------------------------------------------------------

def test_error_hierarchy() -> None:
    """All Bifröst error types are subclasses of BifrostError."""
    for cls in (BifrostConnectionError, BifrostAuthError, BifrostTimeoutError):
        assert issubclass(cls, BifrostError)


def test_bifrost_auth_error_code() -> None:
    """BifrostAuthError carries the BIFROST_AUTH_FAILED code."""
    exc = BifrostAuthError("test")
    assert exc.code == "BIFROST_AUTH_FAILED"


def test_bifrost_connection_error_code() -> None:
    """BifrostConnectionError carries the BIFROST_UNREACHABLE code."""
    exc = BifrostConnectionError("test")
    assert exc.code == "BIFROST_UNREACHABLE"


def test_bifrost_timeout_error_code() -> None:
    """BifrostTimeoutError carries the BIFROST_TIMEOUT code."""
    exc = BifrostTimeoutError("test")
    assert exc.code == "BIFROST_TIMEOUT"


# ---------------------------------------------------------------------------
# close() before open() — must be a no-op
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_close_before_open_is_noop() -> None:
    """close() is safe to call before open() — no exception, no crash."""
    client = OpenAICompatClient(BifrostConfig())
    await client.close()  # Should not raise
    # Capability flags stay False
    assert client.capability_tool_use is False


# ---------------------------------------------------------------------------
# open() — success with tool capability
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_open_success_sets_tool_use_capability() -> None:
    """open() against a probe endpoint that returns tool_calls sets ?tool_use=True."""
    probe_response_body = {
        "id": "probe-1",
        "object": "chat.completion",
        "model": "test",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "type": "function",
                            "function": {"name": "heretic_probe", "arguments": "{}"},
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
    }

    cfg = BifrostConfig(
        endpoint="http://mock-agent.test/v1",
        api_key="test-key",
        tailscale=TailscaleOptions(prefer=False),
    )
    client = OpenAICompatClient(cfg)

    # Mock TailscaleAwareness to return endpoint directly (no Tailscale needed)
    with mock.patch(
        "heretic.bifrost.client.TailscaleAwareness.resolve_endpoint",
        return_value="http://mock-agent.test/v1",
    ), mock.patch(
        "heretic.bifrost.client.TailscaleAwareness.tailscale_active",
        new_callable=lambda: property(lambda self: False),
    ):
        # Use MagicMock (not AsyncMock) for the response so .json() is sync
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = probe_response_body

        # httpx.AsyncClient.post is an async method — mock it as a coroutine
        async def fake_post(*args: Any, **kwargs: Any) -> mock.MagicMock:
            return mock_response

        with mock.patch.object(httpx.AsyncClient, "post", new=fake_post):
            await client.open()

    assert client.capability_tool_use is True
    await client.close()


# ---------------------------------------------------------------------------
# open() — auth error on probe
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_open_raises_auth_error_on_401() -> None:
    """open() raises BifrostAuthError when the probe returns HTTP 401."""
    cfg = BifrostConfig(
        endpoint="http://mock-agent.test/v1",
        api_key="bad-key",
        tailscale=TailscaleOptions(prefer=False),
    )
    client = OpenAICompatClient(cfg)

    with mock.patch(
        "heretic.bifrost.client.TailscaleAwareness.resolve_endpoint",
        return_value="http://mock-agent.test/v1",
    ):
        mock_response = mock.MagicMock()
        mock_response.status_code = 401

        async def fake_post_401(*args: Any, **kwargs: Any) -> mock.MagicMock:
            return mock_response

        with mock.patch.object(httpx.AsyncClient, "post", new=fake_post_401):
            with pytest.raises(BifrostAuthError):
                await client.open()


# ---------------------------------------------------------------------------
# open() — connection refused
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_open_raises_connection_error_on_refused() -> None:
    """open() raises BifrostConnectionError when the endpoint refuses connection."""
    cfg = BifrostConfig(
        endpoint="http://localhost:9999/v1",
        api_key="key",
        tailscale=TailscaleOptions(prefer=False),
    )
    client = OpenAICompatClient(cfg)

    with mock.patch(
        "heretic.bifrost.client.TailscaleAwareness.resolve_endpoint",
        return_value="http://localhost:9999/v1",
    ):
        with mock.patch.object(
            httpx.AsyncClient, "post",
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            with pytest.raises(BifrostConnectionError):
                await client.open()


# ---------------------------------------------------------------------------
# open() — probe timeout
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_open_raises_probe_error_on_timeout() -> None:
    """open() raises BifrostProbeError when the probe times out."""
    from heretic.bifrost.errors import BifrostProbeError

    cfg = BifrostConfig(
        endpoint="http://mock-agent.test/v1",
        api_key="key",
        connect_timeout_seconds=1,
        tailscale=TailscaleOptions(prefer=False),
    )
    client = OpenAICompatClient(cfg)

    with mock.patch(
        "heretic.bifrost.client.TailscaleAwareness.resolve_endpoint",
        return_value="http://mock-agent.test/v1",
    ):
        with mock.patch.object(
            httpx.AsyncClient, "post",
            side_effect=httpx.TimeoutException("timeout"),
        ):
            with pytest.raises(BifrostProbeError):
                await client.open()


# ---------------------------------------------------------------------------
# SSE parsing — text deltas
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_parse_sse_stream_yields_text_deltas() -> None:
    """_parse_sse_stream yields text content from SSE data lines."""
    sse_lines = [
        'data: {"choices":[{"delta":{"content":"Hello"},"finish_reason":null}]}',
        'data: {"choices":[{"delta":{"content":" world"},"finish_reason":null}]}',
        'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}',
        "data: [DONE]",
    ]

    cfg = BifrostConfig()
    client = OpenAICompatClient(cfg)

    # aiter_lines must be a proper async generator, not AsyncMock.return_value
    mock_response = mock.MagicMock()
    mock_response.aiter_lines = lambda: _async_iter(sse_lines)

    chunks: list[str] = []
    async for chunk in client._parse_sse_stream(mock_response):
        chunks.append(chunk)

    assert chunks == ["Hello", " world"]


@pytest.mark.asyncio
async def test_parse_sse_stream_yields_tool_call_on_finish() -> None:
    """_parse_sse_stream assembles and yields a tool call JSON record."""
    sse_lines = [
        'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call-abc","type":"function","function":{"name":"filesystem","arguments":""}}]},"finish_reason":null}]}',
        'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"{\\"path\\":\\"/tmp\\"}"}}]},"finish_reason":null}]}',
        'data: {"choices":[{"delta":{},"finish_reason":"tool_calls"}]}',
        "data: [DONE]",
    ]

    cfg = BifrostConfig()
    client = OpenAICompatClient(cfg)

    mock_response = mock.MagicMock()
    mock_response.aiter_lines = lambda: _async_iter(sse_lines)

    chunks: list[str] = []
    async for chunk in client._parse_sse_stream(mock_response):
        chunks.append(chunk)

    # Should have yielded one tool call JSON record
    assert len(chunks) == 1
    tc = json.loads(chunks[0])
    assert tc["type"] == "tool_call"
    assert tc["id"] == "call-abc"
    assert tc["name"] == "filesystem"
    assert "path" in tc["arguments"]


@pytest.mark.asyncio
async def test_parse_sse_stream_handles_done_sentinel() -> None:
    """[DONE] sentinel terminates the SSE stream cleanly."""
    sse_lines = [
        'data: {"choices":[{"delta":{"content":"hi"},"finish_reason":null}]}',
        "data: [DONE]",
        'data: {"choices":[{"delta":{"content":"should not appear"},"finish_reason":null}]}',
    ]

    cfg = BifrostConfig()
    client = OpenAICompatClient(cfg)

    mock_response = mock.MagicMock()
    mock_response.aiter_lines = lambda: _async_iter(sse_lines)

    chunks: list[str] = []
    async for chunk in client._parse_sse_stream(mock_response):
        chunks.append(chunk)

    # Only "hi" should appear — everything after [DONE] is ignored
    assert chunks == ["hi"]


# ---------------------------------------------------------------------------
# _build_payload
# ---------------------------------------------------------------------------

def test_build_payload_includes_tools() -> None:
    """_build_payload includes tools array and tool_choice when tools are provided."""
    cfg = BifrostConfig(model="test-model", max_tokens=100, stream=False)
    client = OpenAICompatClient(cfg)

    tools = [{"type": "function", "function": {"name": "filesystem.read_file"}}]
    payload = client._build_payload([{"role": "user", "content": "hi"}], tools)

    assert payload["model"] == "test-model"
    assert payload["max_tokens"] == 100
    assert payload["tools"] == tools
    assert payload["tool_choice"] == "auto"
    assert "functions" not in payload  # deprecated key must never appear


def test_build_payload_no_tools() -> None:
    """_build_payload omits tools and tool_choice when tools is None."""
    cfg = BifrostConfig(model="test", max_tokens=127000)
    client = OpenAICompatClient(cfg)

    payload = client._build_payload([{"role": "user", "content": "hi"}], None)

    assert "tools" not in payload
    assert "tool_choice" not in payload
    assert "functions" not in payload


def test_build_payload_max_tokens_from_config() -> None:
    """_build_payload uses max_tokens from BifrostConfig (127000 by default)."""
    cfg = BifrostConfig()
    client = OpenAICompatClient(cfg)
    payload = client._build_payload([], None)
    assert payload["max_tokens"] == 127000


# ---------------------------------------------------------------------------
# close() zeros capability flags
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_close_zeros_capability_flags() -> None:
    """close() resets all capability flags to False regardless of prior state."""
    cfg = BifrostConfig()
    client = OpenAICompatClient(cfg)
    # Manually set flags as if open() ran
    client._capability_tool_use = True
    client._capability_streaming = True
    client._capability_vision_in = True

    await client.close()

    assert client.capability_tool_use is False
    assert client.capability_streaming is False
    assert client.capability_vision_in is False


# ---------------------------------------------------------------------------
# send_message() — not open raises ConnectionError
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_message_before_open_raises() -> None:
    """send_message() raises BifrostConnectionError if called before open()."""
    client = OpenAICompatClient(BifrostConfig())
    with pytest.raises(BifrostConnectionError, match="not open"):
        async for _ in client.send_message([]):
            pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _async_iter(items: list[str]):
    """Helper: async generator that yields from a list."""
    for item in items:
        yield item
