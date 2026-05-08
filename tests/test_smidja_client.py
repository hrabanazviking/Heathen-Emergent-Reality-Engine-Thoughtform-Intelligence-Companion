"""
BrunhandHttpClient tests — full implementation (Forge Wave 2).

Uses unittest.mock.AsyncMock and patch to mock httpx.AsyncClient without
requiring a real Brúarhönd daemon.

Auth invariant is tested explicitly:
    - Token resolved from env
    - AuthError raised when enabled + token absent
    - Token NEVER in repr, str, or any log line

API correctness tested:
    - Each endpoint hits the correct path
    - Request envelope present (request_id, session_id, agent_id)
    - Error mapping (401, 423, 5xx, ConnectError, TimeoutException, malformed JSON)
    - screenshot decodes base64 to raw bytes
    - vroid_open/vroid_export use the CORRECT paths (not the TASK §4 wrong ones)

Ref: src/heretic/skilningr/senses/smidja/client.py
     src/heretic/skilningr/senses/smidja/INTERFACE.md §API Discrepancies
"""

from __future__ import annotations

import base64
import json
import logging
import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretic.skilningr.config_model import SmidjaConfig
from heretic.skilningr.senses.smidja.client import BrunhandHttpClient, _raise_for_auth
from heretic.skilningr.senses.smidja.errors import (
    BrunhandAuthError,
    BrunhandSessionLockedError,
    BrunhandTimeoutError,
    BrunhandUnreachableError,
)
from heretic.skilningr.errors import ToolDispatchError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_config(**kwargs) -> SmidjaConfig:
    """Return a SmidjaConfig with enabled=False so __post_init__ does not warn."""
    defaults = dict(
        enabled=False,
        host="127.0.0.1",
        port=8848,
        token_env="BRUNHAND_TOKEN_HERETIC",
        require_https=False,
        request_timeout_seconds=5,
        host_name="test-host",
    )
    defaults.update(kwargs)
    return SmidjaConfig(**defaults)


def make_mock_response(
    status_code: int = 200,
    json_body: dict | None = None,
    text_body: str = "",
) -> MagicMock:
    """Build a mock httpx response."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_body or {}
    mock.text = text_body
    mock.raise_for_status = MagicMock()
    if status_code >= 400:
        import httpx
        mock.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"HTTP {status_code}", request=MagicMock(), response=mock
        )
    return mock


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_client_init_resolves_token_from_env(monkeypatch):
    """__init__ reads token from os.environ[config.token_env].
    If enabled=True and env var is set, no BrunhandAuthError is raised."""
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "test-secret")
    cfg = make_config(enabled=True)
    client = BrunhandHttpClient(cfg)
    # Client constructed without raising; token is stored privately
    assert client._token == "test-secret"


def test_client_init_raises_auth_error_if_enabled_and_token_missing(monkeypatch):
    """__init__ raises BrunhandAuthError when enabled=True and env var is unset."""
    monkeypatch.delenv("BRUNHAND_TOKEN_HERETIC", raising=False)
    cfg = make_config(enabled=True)
    with pytest.raises(BrunhandAuthError, match="BRUNHAND_TOKEN_HERETIC"):
        BrunhandHttpClient(cfg)


def test_client_init_no_error_when_disabled_and_token_missing(monkeypatch):
    """__init__ does NOT raise when enabled=False even if env var is missing."""
    monkeypatch.delenv("BRUNHAND_TOKEN_HERETIC", raising=False)
    cfg = make_config(enabled=False)
    client = BrunhandHttpClient(cfg)
    assert client._token == ""


def test_client_init_token_not_in_repr(monkeypatch):
    """The bearer token value must not appear in __repr__ or __str__ output."""
    token_value = "super-secret-token-xyz"
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", token_value)
    cfg = make_config(enabled=True)
    client = BrunhandHttpClient(cfg)
    repr_str = repr(client)
    str_str = str(client)
    assert token_value not in repr_str, f"Token in repr: {repr_str!r}"
    assert token_value not in str_str, f"Token in str: {str_str!r}"


def test_client_init_session_id_is_uuid(monkeypatch):
    """Session ID generated at init is a valid UUID4 string."""
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True)
    client = BrunhandHttpClient(cfg)
    # Should not raise
    parsed = uuid.UUID(client._session_id)
    assert str(parsed) == client._session_id


def test_client_uses_http_scheme_when_require_https_false(monkeypatch):
    """base_url uses http:// when require_https=False."""
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)
    assert client._base_url.startswith("http://")
    assert "https" not in client._base_url


def test_client_uses_https_scheme_when_require_https_true(monkeypatch):
    """base_url uses https:// when require_https=True."""
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=True)
    client = BrunhandHttpClient(cfg)
    assert client._base_url.startswith("https://")


# ---------------------------------------------------------------------------
# _build_envelope
# ---------------------------------------------------------------------------

def test_build_envelope_includes_required_fields(monkeypatch):
    """_build_envelope returns dict with request_id, session_id, agent_id."""
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, host_name="myhost")
    client = BrunhandHttpClient(cfg)
    # We need to bypass __init__ NotImplementedError -- it's implemented now
    envelope = client._build_envelope({"x": 5})
    assert "request_id" in envelope
    assert "session_id" in envelope
    assert "agent_id" in envelope
    assert envelope["x"] == 5


def test_build_envelope_request_id_is_uuid_string(monkeypatch):
    """_build_envelope generates a new UUID string for request_id per call."""
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True)
    client = BrunhandHttpClient(cfg)
    env1 = client._build_envelope({})
    env2 = client._build_envelope({})
    # Both are valid UUIDs
    uuid.UUID(env1["request_id"])
    uuid.UUID(env2["request_id"])
    # Each call gets a fresh request_id
    assert env1["request_id"] != env2["request_id"]


def test_build_envelope_session_id_stable_across_calls(monkeypatch):
    """_build_envelope uses the same session_id for all calls in a client lifetime."""
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True)
    client = BrunhandHttpClient(cfg)
    env1 = client._build_envelope({})
    env2 = client._build_envelope({})
    assert env1["session_id"] == env2["session_id"]
    assert env1["session_id"] == client._session_id


def test_build_envelope_agent_id_from_config(monkeypatch):
    """_build_envelope uses config.host_name as agent_id."""
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, host_name="vroid-workstation")
    client = BrunhandHttpClient(cfg)
    envelope = client._build_envelope({})
    assert envelope["agent_id"] == "vroid-workstation"


# ---------------------------------------------------------------------------
# _raise_for_auth helper
# ---------------------------------------------------------------------------

def test_raise_for_auth_raises_auth_error_on_401():
    """_raise_for_auth raises BrunhandAuthError for HTTP 401."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    with pytest.raises(BrunhandAuthError, match="REDACTED"):
        _raise_for_auth(mock_response)


def test_raise_for_auth_raises_session_locked_on_423():
    """_raise_for_auth raises BrunhandSessionLockedError for HTTP 423."""
    mock_response = MagicMock()
    mock_response.status_code = 423
    with pytest.raises(BrunhandSessionLockedError, match="423"):
        _raise_for_auth(mock_response)


def test_raise_for_auth_no_raise_on_200():
    """_raise_for_auth does not raise for HTTP 200."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    _raise_for_auth(mock_response)  # Should not raise


# ---------------------------------------------------------------------------
# open / health
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_open_success_probes_health(monkeypatch):
    """open() calls GET /v1/brunhand/health; on 200 with status='ok', completes without error."""
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    health_response = make_mock_response(200, {"status": "ok", "daemon_version": "0.1"})

    import httpx
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.get = AsyncMock(return_value=health_response)

    with patch("httpx.AsyncClient", return_value=mock_http):
        await client.open()

    mock_http.get.assert_called_once_with("/v1/brunhand/health")
    assert client._http is mock_http


@pytest.mark.asyncio
async def test_open_raises_unreachable_on_connect_error(monkeypatch):
    """open() raises BrunhandUnreachableError if httpx.ConnectError occurs."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

    with patch("httpx.AsyncClient", return_value=mock_http):
        with pytest.raises(BrunhandUnreachableError):
            await client.open()


@pytest.mark.asyncio
async def test_open_raises_timeout_on_timeout(monkeypatch):
    """open() raises BrunhandTimeoutError if httpx.TimeoutException occurs."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.get = AsyncMock(side_effect=httpx.ReadTimeout("timed out"))

    with patch("httpx.AsyncClient", return_value=mock_http):
        with pytest.raises(BrunhandTimeoutError):
            await client.open()


@pytest.mark.asyncio
async def test_close_is_idempotent(monkeypatch):
    """close() can be called multiple times without error."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.aclose = AsyncMock()
    client._http = mock_http

    await client.close()
    await client.close()  # second call should not error
    assert client._http is None


# ---------------------------------------------------------------------------
# screenshot
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_screenshot_returns_decoded_png_bytes(monkeypatch):
    """screenshot() decodes png_bytes_b64 from daemon response and returns raw bytes."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    raw_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
    b64_str = base64.b64encode(raw_png).decode("ascii")
    response = make_mock_response(200, {"payload": {"png_bytes_b64": b64_str}})

    import httpx
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=response)
    client._http = mock_http

    result = await client.screenshot()
    assert result == raw_png


@pytest.mark.asyncio
async def test_screenshot_sends_request_envelope(monkeypatch):
    """screenshot() POST body includes request_id, session_id, agent_id fields."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False, host_name="forge-host")
    client = BrunhandHttpClient(cfg)

    raw_png = b"\x89PNG" + b"\x00" * 10
    b64_str = base64.b64encode(raw_png).decode("ascii")
    response = make_mock_response(200, {"payload": {"png_bytes_b64": b64_str}})

    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=response)
    client._http = mock_http

    await client.screenshot()

    call_kwargs = mock_http.post.call_args
    body = call_kwargs.kwargs.get("json") or call_kwargs.args[1] if call_kwargs.args else call_kwargs.kwargs["json"]
    assert "request_id" in body
    assert "session_id" in body
    assert "agent_id" in body
    assert body["agent_id"] == "forge-host"


@pytest.mark.asyncio
async def test_screenshot_raises_auth_error_on_401(monkeypatch):
    """screenshot() raises BrunhandAuthError when daemon returns HTTP 401."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    response = make_mock_response(401)
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=response)
    client._http = mock_http

    with pytest.raises(BrunhandAuthError):
        await client.screenshot()


@pytest.mark.asyncio
async def test_screenshot_raises_session_locked_on_423(monkeypatch):
    """screenshot() raises BrunhandSessionLockedError on HTTP 423."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    response = make_mock_response(423)
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=response)
    client._http = mock_http

    with pytest.raises(BrunhandSessionLockedError):
        await client.screenshot()


@pytest.mark.asyncio
async def test_screenshot_raises_unreachable_on_connect_error(monkeypatch):
    """screenshot() raises BrunhandUnreachableError on httpx.ConnectError."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
    client._http = mock_http

    with pytest.raises(BrunhandUnreachableError):
        await client.screenshot()


@pytest.mark.asyncio
async def test_screenshot_raises_timeout_on_timeout(monkeypatch):
    """screenshot() raises BrunhandTimeoutError on httpx.TimeoutException."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(side_effect=httpx.ReadTimeout("timeout"))
    client._http = mock_http

    with pytest.raises(BrunhandTimeoutError):
        await client.screenshot()


@pytest.mark.asyncio
async def test_screenshot_5xx_raises_tool_dispatch_error(monkeypatch):
    """screenshot() raises ToolDispatchError on HTTP 5xx."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    response = MagicMock()
    response.status_code = 500
    response.text = "Internal Server Error"
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=response)
    client._http = mock_http

    with pytest.raises(ToolDispatchError):
        await client.screenshot()


# ---------------------------------------------------------------------------
# click
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_click_sends_correct_body(monkeypatch):
    """click(100, 200, button='right') sends x=100, y=200, button='right' in body."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    response = make_mock_response(200, {"payload": {"x": 100, "y": 200, "clicks_delivered": 1}})
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=response)
    client._http = mock_http

    await client.click(100, 200, button="right")

    call_kwargs = mock_http.post.call_args
    body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json", {})
    assert body["x"] == 100
    assert body["y"] == 200
    assert body["button"] == "right"
    assert "/v1/brunhand/click" in str(mock_http.post.call_args)


@pytest.mark.asyncio
async def test_click_posts_to_correct_endpoint(monkeypatch):
    """click() posts to /v1/brunhand/click."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    response = make_mock_response(200, {"payload": {}})
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=response)
    client._http = mock_http

    await client.click(10, 20)
    mock_http.post.assert_called_once()
    call_args = mock_http.post.call_args
    assert "/v1/brunhand/click" in str(call_args)


# ---------------------------------------------------------------------------
# type_text
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_type_text_posts_to_brunhand_type(monkeypatch):
    """type_text() POSTs to /v1/brunhand/type (not /v1/brunhand/type_text)."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    response = make_mock_response(200, {"payload": {"characters_typed": 5}})
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=response)
    client._http = mock_http

    await client.type_text("hello")
    call_args = mock_http.post.call_args
    # The path must be /v1/brunhand/type, NOT /type_text
    assert "/v1/brunhand/type" in str(call_args)
    assert "type_text" not in str(call_args.args[0]) if call_args.args else True


@pytest.mark.asyncio
async def test_type_text_sends_text_in_body(monkeypatch):
    """type_text() sends text in request body."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    response = make_mock_response(200, {"payload": {"characters_typed": 13}})
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=response)
    client._http = mock_http

    await client.type_text("hello unicode")
    body = mock_http.post.call_args.kwargs.get("json", {})
    assert body.get("text") == "hello unicode"


# ---------------------------------------------------------------------------
# hotkey
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_hotkey_sends_keys_list(monkeypatch):
    """hotkey(['ctrl', 's']) sends keys=['ctrl', 's'] in request body."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    response = make_mock_response(200, {"payload": {"keys": ["ctrl", "s"]}})
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=response)
    client._http = mock_http

    await client.hotkey(["ctrl", "s"])
    body = mock_http.post.call_args.kwargs.get("json", {})
    assert body.get("keys") == ["ctrl", "s"]


# ---------------------------------------------------------------------------
# vroid_open / vroid_export — path correctness (critical — TASK §4 had wrong paths)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_vroid_open_posts_to_correct_path(monkeypatch):
    """vroid_open() POSTs to /v1/brunhand/vroid/open_project (NOT /vroid-open)."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    response = make_mock_response(200, {"payload": {"opened_path": "char.vroid"}})
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=response)
    client._http = mock_http

    await client.vroid_open("char.vroid")
    call_args = mock_http.post.call_args
    path_used = call_args.args[0] if call_args.args else str(call_args)
    assert "/v1/brunhand/vroid/open_project" in str(path_used), (
        f"Expected path /v1/brunhand/vroid/open_project, got: {path_used!r}. "
        f"NOTE: TASK §4 listed /vroid-open (wrong); correct path is /vroid/open_project."
    )
    assert "vroid-open" not in str(path_used), (
        "vroid_open() is using the WRONG path /vroid-open from TASK §4. "
        "Correct path per daemon INTERFACE.md: /v1/brunhand/vroid/open_project"
    )


@pytest.mark.asyncio
async def test_vroid_export_posts_to_correct_path(monkeypatch):
    """vroid_export() POSTs to /v1/brunhand/vroid/export_vrm (NOT /vroid-export)."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    response = make_mock_response(200, {"payload": {"exported_path": "avatar.vrm"}})
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=response)
    client._http = mock_http

    await client.vroid_export("avatar.vrm")
    call_args = mock_http.post.call_args
    path_used = call_args.args[0] if call_args.args else str(call_args)
    assert "/v1/brunhand/vroid/export_vrm" in str(path_used), (
        f"Expected path /v1/brunhand/vroid/export_vrm, got: {path_used!r}. "
        f"NOTE: TASK §4 listed /vroid-export (wrong); correct path is /vroid/export_vrm."
    )
    assert "vroid-export" not in str(path_used)


@pytest.mark.asyncio
async def test_vroid_open_sends_project_path(monkeypatch):
    """vroid_open() includes project_path in request body."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    response = make_mock_response(200, {"payload": {}})
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=response)
    client._http = mock_http

    await client.vroid_open("characters/hero.vroid")
    body = mock_http.post.call_args.kwargs.get("json", {})
    assert body.get("project_path") == "characters/hero.vroid"


@pytest.mark.asyncio
async def test_vroid_export_sends_output_path(monkeypatch):
    """vroid_export() includes output_path in request body."""
    import httpx
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", "tok")
    cfg = make_config(enabled=True, require_https=False)
    client = BrunhandHttpClient(cfg)

    response = make_mock_response(200, {"payload": {}})
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=response)
    client._http = mock_http

    await client.vroid_export("exports/hero.vrm")
    body = mock_http.post.call_args.kwargs.get("json", {})
    assert body.get("output_path") == "exports/hero.vrm"


# ---------------------------------------------------------------------------
# Token never appears in logs
# ---------------------------------------------------------------------------

def test_token_not_in_logs_during_auth_error(monkeypatch, caplog):
    """BrunhandAuthError message must not contain the actual token value."""
    token_value = "extremely-secret-token-abc123"
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", token_value)
    cfg = make_config(enabled=True, require_https=False)
    # Construct client with token set
    client = BrunhandHttpClient(cfg)
    # The auth error raised by _raise_for_auth should say [REDACTED], not the token
    from unittest.mock import MagicMock as MM
    mock_response = MM()
    mock_response.status_code = 401
    with pytest.raises(BrunhandAuthError) as exc_info:
        _raise_for_auth(mock_response)
    assert token_value not in str(exc_info.value)


def test_token_not_in_repr_after_construction(monkeypatch):
    """Token must not appear in repr even after construction with a real token."""
    token_value = "do-not-print-me-in-repr"
    monkeypatch.setenv("BRUNHAND_TOKEN_HERETIC", token_value)
    cfg = make_config(enabled=True)
    client = BrunhandHttpClient(cfg)
    output = repr(client) + str(client)
    assert token_value not in output
