"""
Tests — heretic.rodd.chatterbox (ChatterboxClient / ChatterboxHttpClient).

All HTTP calls are mocked via httpx.MockTransport — no real network calls,
no Pi required. Tests cover happy paths, error mapping, voice path handling,
and the drift adaptations documented in DATA_FLOW.md §4.6.1.
"""

from __future__ import annotations

import io
import json
import struct
import wave
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from heretic.rodd.chatterbox import ChatterboxHttpClient
from heretic.rodd.config_model import RoddTtsConfig
from heretic.rodd.errors import (
    ChatterboxApiError,
    ChatterboxAuthError,
    ChatterboxConnectionError,
    ChatterboxTimeoutError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(**kwargs) -> RoddTtsConfig:
    """Build a RoddTtsConfig for testing."""
    defaults = {
        "endpoint": "http://chatterbox.test:7851",
        "model": "turbo",
        "temperature": 0.8,
        "request_timeout_seconds": 10,
    }
    defaults.update(kwargs)
    return RoddTtsConfig(**defaults)


def _make_logger():
    """Return a silent test logger."""
    import logging
    log = logging.getLogger("test.rodd.chatterbox")
    log.setLevel(logging.CRITICAL)  # suppress output during tests
    return log


def _make_wav_bytes(text: str = "test") -> bytes:
    """Build a minimal valid WAV file in memory for use as mock API response."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        # Short silence — 0.1 seconds at 22050 Hz, 16-bit mono
        n_frames = 2205
        wf.writeframes(struct.pack(f"<{n_frames}h", *([0] * n_frames)))
    return buf.getvalue()


class _MockTransport(httpx.AsyncBaseTransport):
    """Minimal httpx async transport that returns pre-canned responses."""

    def __init__(self, responses: dict):
        # responses maps (method, path) -> (status_code, headers, body_bytes | body_str)
        self._responses = responses

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        if key not in self._responses:
            raise httpx.ConnectError(f"No mock for {request.method} {request.url}")
        status, headers, body = self._responses[key]
        if isinstance(body, str):
            body = body.encode()
        return httpx.Response(status, headers=headers, content=body)


def _make_client_with_transport(transport: httpx.AsyncBaseTransport, config: RoddTtsConfig) -> ChatterboxHttpClient:
    """Build a ChatterboxHttpClient and inject the mock transport into its internal httpx client."""
    logger = _make_logger()
    client = ChatterboxHttpClient(config, logger)
    # Inject the mock transport so open()/health()/synthesize() use it
    client._client = httpx.AsyncClient(transport=transport)
    client._open = True
    return client


# ---------------------------------------------------------------------------
# open()
# ---------------------------------------------------------------------------

async def test_open_success_on_healthy_endpoint() -> None:
    """open() sets is_open True when /health returns 200."""
    transport = _MockTransport({
        ("GET", "/health"): (200, {"content-type": "application/json"}, json.dumps({"status": "ok"})),
    })
    config = _make_config()
    logger = _make_logger()
    client = ChatterboxHttpClient(config, logger)
    # Inject mock transport by patching httpx.AsyncClient at construction time
    with patch("httpx.AsyncClient") as mock_cls:
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_instance
        client2 = ChatterboxHttpClient(config, logger)
        await client2.open()
        assert client2.is_open is True


async def test_open_raises_connection_error_on_refused() -> None:
    """open() raises ChatterboxConnectionError when the endpoint is unreachable."""
    config = _make_config()
    logger = _make_logger()
    client = ChatterboxHttpClient(config, logger)
    with patch("httpx.AsyncClient") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_instance.aclose = AsyncMock()
        mock_cls.return_value = mock_instance
        client2 = ChatterboxHttpClient(config, logger)
        with pytest.raises(ChatterboxConnectionError):
            await client2.open()
        assert client2.is_open is False


async def test_open_raises_timeout_error() -> None:
    """open() raises ChatterboxTimeoutError when the health probe times out."""
    config = _make_config()
    logger = _make_logger()
    with patch("httpx.AsyncClient") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
        mock_instance.aclose = AsyncMock()
        mock_cls.return_value = mock_instance
        client = ChatterboxHttpClient(config, logger)
        with pytest.raises(ChatterboxTimeoutError):
            await client.open()


# ---------------------------------------------------------------------------
# health()
# ---------------------------------------------------------------------------

async def test_health_returns_dict() -> None:
    """health() returns a non-empty dict from the /health response body."""
    health_data = {"status": "ok", "model": "turbo"}
    transport = _MockTransport({
        ("GET", "/health"): (200, {"content-type": "application/json"}, json.dumps(health_data)),
    })
    config = _make_config()
    client = _make_client_with_transport(transport, config)
    result = await client.health()
    assert isinstance(result, dict)
    assert result["status"] == "ok"


async def test_health_raises_connection_error_on_network_failure() -> None:
    """health() raises ChatterboxConnectionError on network failure."""
    config = _make_config()
    logger = _make_logger()
    client = ChatterboxHttpClient(config, logger)
    mock_http = MagicMock()
    mock_http.get = AsyncMock(side_effect=httpx.ConnectError("gone"))
    client._client = mock_http
    client._open = True
    with pytest.raises(ChatterboxConnectionError):
        await client.health()


# ---------------------------------------------------------------------------
# list_models()
# ---------------------------------------------------------------------------

async def test_list_models_returns_list() -> None:
    """list_models() returns a list of dicts from the /v1/models response."""
    models_data = {
        "object": "list",
        "data": [
            {"id": "turbo", "aliases": ["default"], "loaded": True},
            {"id": "tts", "aliases": [], "loaded": False},
        ],
    }
    transport = _MockTransport({
        ("GET", "/v1/models"): (200, {"content-type": "application/json"}, json.dumps(models_data)),
    })
    config = _make_config()
    client = _make_client_with_transport(transport, config)
    result = await client.list_models()
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["id"] == "turbo"


async def test_list_models_handles_bare_list_response() -> None:
    """list_models() handles responses that are a bare JSON array (no 'data' wrapper)."""
    models_list = [{"id": "turbo"}, {"id": "tts"}]
    transport = _MockTransport({
        ("GET", "/v1/models"): (200, {"content-type": "application/json"}, json.dumps(models_list)),
    })
    config = _make_config()
    client = _make_client_with_transport(transport, config)
    result = await client.list_models()
    assert isinstance(result, list)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# synthesize() — happy path
# ---------------------------------------------------------------------------

async def test_synthesize_returns_wav_bytes() -> None:
    """synthesize() returns bytes whose first 4 bytes are b'RIFF' (valid WAV magic)."""
    wav_data = _make_wav_bytes()
    transport = _MockTransport({
        ("POST", "/v1/audio/speech"): (200, {"content-type": "audio/wav"}, wav_data),
    })
    config = _make_config()
    client = _make_client_with_transport(transport, config)
    result = await client.synthesize("Hello, body.")
    assert result[:4] == b"RIFF"
    assert len(result) > 0


async def test_synthesize_uses_config_model_when_no_override() -> None:
    """synthesize() includes config.model in the request body when no override provided."""
    wav_data = _make_wav_bytes()
    captured_body: list[dict] = []

    class CapturingTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            if request.url.path == "/v1/audio/speech":
                captured_body.append(json.loads(request.content))
            return httpx.Response(200, headers={"content-type": "audio/wav"}, content=wav_data)

    config = _make_config(model="tts")
    client = _make_client_with_transport(CapturingTransport(), config)
    await client.synthesize("Hello.")
    assert len(captured_body) == 1
    assert captured_body[0]["model"] == "tts"


async def test_synthesize_uses_override_model_when_provided() -> None:
    """synthesize() uses the override model instead of config.model when passed."""
    wav_data = _make_wav_bytes()
    captured_body: list[dict] = []

    class CapturingTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            if request.url.path == "/v1/audio/speech":
                captured_body.append(json.loads(request.content))
            return httpx.Response(200, headers={"content-type": "audio/wav"}, content=wav_data)

    config = _make_config(model="turbo")
    client = _make_client_with_transport(CapturingTransport(), config)
    await client.synthesize("Hello.", model="multilingual")
    assert captured_body[0]["model"] == "multilingual"


async def test_synthesize_voice_default_omits_voice_field() -> None:
    """synthesize() omits the 'voice' field when voice_id is 'default'.

    DATA_FLOW.md §4.6.1: 'default' means use ChatterBox's built-in voice.
    """
    wav_data = _make_wav_bytes()
    captured_body: list[dict] = []

    class CapturingTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            if request.url.path == "/v1/audio/speech":
                captured_body.append(json.loads(request.content))
            return httpx.Response(200, headers={"content-type": "audio/wav"}, content=wav_data)

    config = _make_config(voice_id="default", voice_prompt_path=None)
    client = _make_client_with_transport(CapturingTransport(), config)
    await client.synthesize("Hello.")
    assert "voice" not in captured_body[0], (
        "voice field must be omitted when voice_id is 'default' — "
        "ChatterBox uses its built-in voice (DATA_FLOW.md §4.6.1)"
    )


async def test_synthesize_empty_voice_omits_voice_field() -> None:
    """synthesize() omits the 'voice' field when voice_prompt_path is None or empty."""
    wav_data = _make_wav_bytes()
    captured_body: list[dict] = []

    class CapturingTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            if request.url.path == "/v1/audio/speech":
                captured_body.append(json.loads(request.content))
            return httpx.Response(200, headers={"content-type": "audio/wav"}, content=wav_data)

    config = _make_config(voice_id="default", voice_prompt_path=None)
    client = _make_client_with_transport(CapturingTransport(), config)
    await client.synthesize("Hello.")
    assert "voice" not in captured_body[0]


# ---------------------------------------------------------------------------
# synthesize() — error paths
# ---------------------------------------------------------------------------

async def test_synthesize_raises_value_error_on_empty_text() -> None:
    """synthesize() raises ValueError when text is empty string."""
    config = _make_config()
    logger = _make_logger()
    client = ChatterboxHttpClient(config, logger)
    client._client = MagicMock()
    client._open = True
    with pytest.raises(ValueError, match="empty"):
        await client.synthesize("")


async def test_synthesize_raises_value_error_on_text_over_4000_chars() -> None:
    """synthesize() raises ValueError when text exceeds 4000 characters."""
    config = _make_config()
    logger = _make_logger()
    client = ChatterboxHttpClient(config, logger)
    client._client = MagicMock()
    client._open = True
    with pytest.raises(ValueError, match="4000"):
        await client.synthesize("x" * 4001)


async def test_synthesize_raises_timeout_error() -> None:
    """synthesize() raises ChatterboxTimeoutError on httpx.TimeoutException."""
    config = _make_config()
    logger = _make_logger()
    client = ChatterboxHttpClient(config, logger)
    mock_http = MagicMock()
    mock_http.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
    client._client = mock_http
    client._open = True
    with pytest.raises(ChatterboxTimeoutError):
        await client.synthesize("Hello.")


async def test_synthesize_raises_auth_error_on_401() -> None:
    """synthesize() raises ChatterboxAuthError on HTTP 401."""
    transport = _MockTransport({
        ("POST", "/v1/audio/speech"): (401, {"content-type": "application/json"}, json.dumps({"error": "Unauthorized"})),
    })
    config = _make_config()
    client = _make_client_with_transport(transport, config)
    with pytest.raises(ChatterboxAuthError):
        await client.synthesize("Hello.")


async def test_synthesize_raises_api_error_on_500() -> None:
    """synthesize() raises ChatterboxApiError on HTTP 500."""
    transport = _MockTransport({
        ("POST", "/v1/audio/speech"): (500, {"content-type": "application/json"}, json.dumps({"error": "Internal Server Error"})),
    })
    config = _make_config()
    client = _make_client_with_transport(transport, config)
    with pytest.raises(ChatterboxApiError) as exc_info:
        await client.synthesize("Hello.")
    assert exc_info.value.status_code == 500


async def test_synthesize_raises_api_error_on_wrong_content_type() -> None:
    """synthesize() raises ChatterboxApiError when Content-Type is not audio/wav."""
    transport = _MockTransport({
        ("POST", "/v1/audio/speech"): (200, {"content-type": "application/json"}, json.dumps({"error": "unexpected"})),
    })
    config = _make_config()
    client = _make_client_with_transport(transport, config)
    with pytest.raises(ChatterboxApiError, match="Content-Type"):
        await client.synthesize("Hello.")


async def test_synthesize_raises_connection_error_on_connect_error() -> None:
    """synthesize() raises ChatterboxConnectionError on httpx.ConnectError."""
    config = _make_config()
    logger = _make_logger()
    client = ChatterboxHttpClient(config, logger)
    mock_http = MagicMock()
    mock_http.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
    client._client = mock_http
    client._open = True
    with pytest.raises(ChatterboxConnectionError):
        await client.synthesize("Hello.")


# ---------------------------------------------------------------------------
# Lifecycle — is_open, close
# ---------------------------------------------------------------------------

async def test_is_open_lifecycle() -> None:
    """is_open is False before open(), True after, False after close()."""
    config = _make_config()
    logger = _make_logger()
    client = ChatterboxHttpClient(config, logger)
    assert client.is_open is False

    with patch("httpx.AsyncClient") as mock_cls:
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_instance.aclose = AsyncMock()
        mock_cls.return_value = mock_instance
        await client.open()
        assert client.is_open is True
        await client.close()
        assert client.is_open is False


async def test_close_is_safe_when_never_opened() -> None:
    """close() does not raise when called before open()."""
    config = _make_config()
    logger = _make_logger()
    client = ChatterboxHttpClient(config, logger)
    # Should not raise even though _client is None
    await client.close()
    assert client.is_open is False


async def test_context_manager_opens_and_closes() -> None:
    """ChatterboxHttpClient works as async context manager — open on enter, close on exit."""
    config = _make_config()
    logger = _make_logger()
    client = ChatterboxHttpClient(config, logger)

    with patch("httpx.AsyncClient") as mock_cls:
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_instance.aclose = AsyncMock()
        mock_cls.return_value = mock_instance

        client2 = ChatterboxHttpClient(config, logger)
        async with client2:
            assert client2.is_open is True
        assert client2.is_open is False
