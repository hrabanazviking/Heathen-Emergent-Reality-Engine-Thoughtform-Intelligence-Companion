"""
Tests — ForgeHttpClient (full method-level httpx-mocked coverage).

All tests use unittest.mock.patch to mock httpx.AsyncClient — no live Straumur
daemon required. Pattern mirrors test_smidja_client.py (BrunhandHttpClient tests).

Coverage targets per S-1 audit finding:
    - Lifecycle: open (success, ConnectError, TimeoutError, non-ok health status)
    - Auth: token_env=None, token resolved, token never in repr
    - Close: idempotent
    - _assert_open guard: methods raise before open()
    - Endpoints: health, build_avatar, get_avatar, inspect_avatar, list_assets
    - Error mapping: ForgeUnreachableError, ForgeTimeoutError,
                     ForgeValidationError, ForgeServerError
    - list_assets: dict-wrapper unwrapping, query param passthrough

Ref: src/heretic/skilningr/senses/smidja/forge_client.py
     src/heretic/skilningr/config_model.ForgeConfig
     docs/architecture/SENSE_CONTRACTS.md §Smiðja Forge dispatch
     docs/audit/AUDIT_v0.6.1_FORGE_DISPATCH.md S-1
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretic.skilningr.config_model import ForgeConfig
from heretic.skilningr.senses.smidja.forge_client import ForgeHttpClient, _TIMEOUT_HINT
from heretic.skilningr.senses.smidja.errors import (
    ForgeError,
    ForgeServerError,
    ForgeTimeoutError,
    ForgeUnreachableError,
    ForgeValidationError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_forge_response(
    status_code: int = 200,
    json_body: dict | list | None = None,
    text_body: str = "",
) -> MagicMock:
    """Build a mock httpx.Response."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.is_success = 200 <= status_code < 300
    mock.json.return_value = json_body if json_body is not None else {}
    mock.text = text_body
    return mock


# ---------------------------------------------------------------------------
# ForgeConfig tests
# ---------------------------------------------------------------------------

def test_forge_config_default_values():
    """ForgeConfig must have documented defaults: disabled, localhost:8765, 120s."""
    cfg = ForgeConfig()
    assert cfg.enabled is False
    assert "127.0.0.1" in cfg.endpoint
    assert "8765" in cfg.endpoint
    assert cfg.token_env is None
    assert cfg.request_timeout_seconds == 120


def test_forge_config_rejects_empty_endpoint():
    """ForgeConfig must raise ValueError if endpoint is empty."""
    with pytest.raises(ValueError, match="endpoint"):
        ForgeConfig(endpoint="")


def test_forge_config_rejects_invalid_token_env():
    """ForgeConfig must raise ValueError if token_env is not a valid env var name."""
    with pytest.raises(ValueError, match="token_env"):
        ForgeConfig(token_env="not-valid-123")


def test_forge_config_rejects_zero_timeout():
    """ForgeConfig must raise ValueError if request_timeout_seconds <= 0."""
    with pytest.raises(ValueError, match="request_timeout_seconds"):
        ForgeConfig(request_timeout_seconds=0)


def test_forge_config_accepts_valid_token_env():
    """ForgeConfig must accept a valid uppercase env var name for token_env."""
    cfg = ForgeConfig(token_env="SEIDR_SMIDJA_FORGE_TOKEN")
    assert cfg.token_env == "SEIDR_SMIDJA_FORGE_TOKEN"


# ---------------------------------------------------------------------------
# ForgeHttpClient construction tests
# ---------------------------------------------------------------------------

def test_forge_client_constructs_with_defaults():
    """ForgeHttpClient must construct without raising given a default ForgeConfig."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)
    assert client is not None
    assert client._is_open is False
    assert client._http is None


def test_forge_client_repr_does_not_include_token(monkeypatch):
    """ForgeHttpClient repr must never include a token value."""
    monkeypatch.setenv("SEIDR_SMIDJA_FORGE_TOKEN", "super_secret_token")
    cfg = ForgeConfig(token_env="SEIDR_SMIDJA_FORGE_TOKEN")
    client = ForgeHttpClient(cfg)
    r = repr(client)
    assert "super_secret_token" not in r


def test_forge_client_token_env_none_does_not_raise():
    """token_env=None leaves _token as None — no exception raised at construction."""
    cfg = ForgeConfig(token_env=None)
    client = ForgeHttpClient(cfg)
    assert client._token is None


def test_forge_client_token_env_set_resolves_from_env(monkeypatch):
    """token_env set to a valid env var name resolves the token value at init."""
    monkeypatch.setenv("MY_FORGE_TOKEN", "secret-forge-key")
    cfg = ForgeConfig(token_env="MY_FORGE_TOKEN")
    client = ForgeHttpClient(cfg)
    assert client._token == "secret-forge-key"


def test_forge_client_token_env_set_but_unset_in_env(monkeypatch):
    """token_env named but env var unset → _token is None; no raise (auth is optional)."""
    monkeypatch.delenv("MY_FORGE_TOKEN", raising=False)
    cfg = ForgeConfig(token_env="MY_FORGE_TOKEN")
    client = ForgeHttpClient(cfg)
    # Forge auth is optional (unlike Brúarhönd); no AuthError raised
    assert client._token is None


# ---------------------------------------------------------------------------
# Error hierarchy tests
# ---------------------------------------------------------------------------

def test_forge_error_hierarchy():
    """ForgeError and subclasses must sit in the correct inheritance tree."""
    from heretic.skilningr.errors import SmidjaError, SkilningrError

    assert issubclass(ForgeError, SmidjaError)
    assert issubclass(ForgeServerError, ForgeError)
    assert issubclass(ForgeUnreachableError, ForgeError)
    assert issubclass(ForgeTimeoutError, ForgeError)
    assert issubclass(ForgeValidationError, ForgeError)
    # All should catch as SkilningrError
    assert issubclass(ForgeError, SkilningrError)
    assert issubclass(ForgeServerError, SkilningrError)


# ---------------------------------------------------------------------------
# Lifecycle — open()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_forge_client_open_succeeds_with_mocked_health_200():
    """open() completes when /v1/health returns 200 with status 'ok'."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    health_response = make_forge_response(200, {"status": "ok", "version": "0.1.0"})

    import httpx
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.get = AsyncMock(return_value=health_response)

    with patch("httpx.AsyncClient", return_value=mock_http):
        await client.open()

    assert client._is_open is True
    assert client._http is mock_http


@pytest.mark.asyncio
async def test_forge_client_open_raises_unreachable_on_connect_error():
    """open() raises ForgeUnreachableError when httpx.ConnectError is raised."""
    import httpx

    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

    with patch("httpx.AsyncClient", return_value=mock_http):
        with pytest.raises(ForgeUnreachableError):
            await client.open()


@pytest.mark.asyncio
async def test_forge_client_open_raises_unreachable_on_health_non_ok_status():
    """open() raises ForgeUnreachableError when health returns non-'ok' status."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    health_response = make_forge_response(200, {"status": "degraded", "version": "0.1.0"})

    import httpx
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.get = AsyncMock(return_value=health_response)

    with patch("httpx.AsyncClient", return_value=mock_http):
        with pytest.raises(ForgeUnreachableError, match="degraded"):
            await client.open()


@pytest.mark.asyncio
async def test_forge_client_open_raises_timeout_on_health_timeout():
    """open() raises ForgeTimeoutError when the health probe times out."""
    import httpx

    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.get = AsyncMock(side_effect=httpx.ReadTimeout("timed out"))

    with patch("httpx.AsyncClient", return_value=mock_http):
        with pytest.raises(ForgeTimeoutError):
            await client.open()


@pytest.mark.asyncio
async def test_forge_client_open_raises_unreachable_on_health_500():
    """open() raises ForgeServerError (subclass of ForgeUnreachableError catch path) on 5xx health."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    error_response = make_forge_response(500, {"detail": "internal server error"})

    import httpx
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.get = AsyncMock(return_value=error_response)

    with patch("httpx.AsyncClient", return_value=mock_http):
        # ForgeServerError is a subclass of ForgeError — open() re-raises or wraps it
        with pytest.raises((ForgeServerError, ForgeUnreachableError, ForgeError)):
            await client.open()


# ---------------------------------------------------------------------------
# Lifecycle — close()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_forge_client_close_is_idempotent():
    """close() can be called multiple times without error; _http is None after."""
    import httpx

    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.aclose = AsyncMock()
    client._http = mock_http
    client._is_open = True

    await client.close()
    assert client._http is None
    assert client._is_open is False

    # Second close — no error
    await client.close()
    assert client._is_open is False


# ---------------------------------------------------------------------------
# _assert_open guard
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_forge_client_method_raises_unreachable_before_open():
    """Methods raise ForgeUnreachableError if called before open()."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)
    # _http is None; _assert_open should fire

    with pytest.raises(ForgeUnreachableError, match="not open"):
        await client.health()


@pytest.mark.asyncio
async def test_forge_client_build_avatar_raises_before_open():
    """build_avatar raises ForgeUnreachableError when client is not open."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    with pytest.raises(ForgeUnreachableError):
        await client.build_avatar({"base_asset_id": "test"})


# ---------------------------------------------------------------------------
# health()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_forge_client_health_returns_dict():
    """health() returns a dict with at least status and version keys."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    health_response = make_forge_response(200, {"status": "ok", "version": "0.1.0"})

    import httpx
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.get = AsyncMock(return_value=health_response)
    # Inject the mock client directly (skip open() for this unit test)
    client._http = mock_http

    result = await client.health()
    assert isinstance(result, dict)
    assert result["status"] == "ok"
    assert result["version"] == "0.1.0"


# ---------------------------------------------------------------------------
# build_avatar()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_forge_client_build_avatar_posts_to_v1_avatars_with_loom_spec():
    """build_avatar() POSTs to /v1/avatars with correct body shape."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    success_response = make_forge_response(200, {
        "success": True,
        "request_id": "req-uuid",
        "session_id": "sess-uuid",
        "vrm_path": None,
        "render_paths": {},
        "compliance_passed": None,
        "elapsed_seconds": 42.0,
        "errors": [],
    })

    import httpx
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=success_response)
    client._http = mock_http

    loom_spec = {"base_asset_id": "vroid_base_v1", "hair_color": "#8B4513"}
    result = await client.build_avatar(loom_spec)

    # Verify POST was called with correct path
    call_kwargs = mock_http.post.call_args
    assert call_kwargs[0][0] == "/v1/avatars"  # positional path arg
    body_sent = call_kwargs[1]["json"]
    assert body_sent["spec"] == loom_spec
    assert "output_dir" in body_sent
    assert "session_metadata" in body_sent

    # Verify response shape
    assert result["success"] is True
    assert result["session_id"] == "sess-uuid"


@pytest.mark.asyncio
async def test_forge_client_build_avatar_timeout_raises_forge_timeout_with_hint():
    """build_avatar() raises ForgeTimeoutError with hint when request times out."""
    import httpx

    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(side_effect=httpx.ReadTimeout("render timed out"))
    client._http = mock_http

    with pytest.raises(ForgeTimeoutError) as exc_info:
        await client.build_avatar({"base_asset_id": "test"})

    # Hint string must be present in the error message
    assert _TIMEOUT_HINT in str(exc_info.value)


@pytest.mark.asyncio
async def test_forge_client_build_avatar_422_raises_forge_validation_error():
    """build_avatar() raises ForgeValidationError on HTTP 422."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    error_response = make_forge_response(422, {"detail": "spec invalid — missing base_asset_id"})

    import httpx
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=error_response)
    client._http = mock_http

    with pytest.raises(ForgeValidationError) as exc_info:
        await client.build_avatar({})

    assert "spec invalid" in str(exc_info.value)


@pytest.mark.asyncio
async def test_forge_client_build_avatar_500_raises_forge_server_error():
    """build_avatar() raises ForgeServerError on HTTP 500."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    error_response = make_forge_response(500, {"detail": "Blender crashed"})

    import httpx
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=error_response)
    client._http = mock_http

    with pytest.raises(ForgeServerError):
        await client.build_avatar({"base_asset_id": "test"})


@pytest.mark.asyncio
async def test_forge_client_build_avatar_connect_error_raises_unreachable():
    """build_avatar() raises ForgeUnreachableError on httpx.ConnectError."""
    import httpx

    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
    client._http = mock_http

    with pytest.raises(ForgeUnreachableError):
        await client.build_avatar({"base_asset_id": "test"})


# ---------------------------------------------------------------------------
# get_avatar()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_forge_client_get_avatar_gets_v1_avatars_session_id():
    """get_avatar() GETs /v1/avatars/{session_id} with correct path."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    session_record = {
        "session_id": "my-session-uuid",
        "agent_id": "rest_client",
        "bridge_type": "straumur",
        "started_at": "2026-05-08T10:00:00",
        "ended_at": "2026-05-08T10:01:00",
        "success": True,
        "summary": "Build completed.",
        "events": [],
    }
    get_response = make_forge_response(200, session_record)

    import httpx
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.get = AsyncMock(return_value=get_response)
    client._http = mock_http

    result = await client.get_avatar("my-session-uuid")

    call_args = mock_http.get.call_args
    assert call_args[0][0] == "/v1/avatars/my-session-uuid"
    assert result["session_id"] == "my-session-uuid"
    assert result["success"] is True


@pytest.mark.asyncio
async def test_forge_client_get_avatar_404_raises_forge_validation_error():
    """get_avatar() raises ForgeValidationError on HTTP 404 (session not found)."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    not_found_response = make_forge_response(404, {"detail": "session not found"})

    import httpx
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.get = AsyncMock(return_value=not_found_response)
    client._http = mock_http

    with pytest.raises(ForgeValidationError):
        await client.get_avatar("nonexistent-uuid")


# ---------------------------------------------------------------------------
# inspect_avatar()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_forge_client_inspect_avatar_posts_with_vrm_path_and_targets():
    """inspect_avatar() POSTs to /v1/inspect with {vrm_path, targets} body."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    inspect_response = make_forge_response(200, {
        "passed": True,
        "vrm_path": "output/my.vrm",
        "targets_checked": ["vrchat"],
        "elapsed_seconds": 2.0,
        "results": {},
    })

    import httpx
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=inspect_response)
    client._http = mock_http

    result = await client.inspect_avatar("output/my.vrm", targets=["vrchat"])

    call_kwargs = mock_http.post.call_args
    assert call_kwargs[0][0] == "/v1/inspect"
    body_sent = call_kwargs[1]["json"]
    assert body_sent["vrm_path"] == "output/my.vrm"
    assert body_sent["targets"] == ["vrchat"]
    assert result["passed"] is True


@pytest.mark.asyncio
async def test_forge_client_inspect_avatar_targets_none_sends_null():
    """inspect_avatar() with targets=None sends null in request body."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    inspect_response = make_forge_response(200, {
        "passed": True,
        "vrm_path": "output/my.vrm",
        "targets_checked": [],
        "elapsed_seconds": 1.5,
        "results": {},
    })

    import httpx
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=inspect_response)
    client._http = mock_http

    await client.inspect_avatar("output/my.vrm", targets=None)

    call_kwargs = mock_http.post.call_args
    body_sent = call_kwargs[1]["json"]
    assert body_sent["targets"] is None


@pytest.mark.asyncio
async def test_forge_client_inspect_avatar_400_raises_forge_validation_error():
    """inspect_avatar() raises ForgeValidationError on HTTP 400 (path outside allow-list)."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    bad_response = make_forge_response(400, {"detail": "path outside allow-listed directories"})

    import httpx
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(return_value=bad_response)
    client._http = mock_http

    with pytest.raises(ForgeValidationError, match="allow"):
        await client.inspect_avatar("/etc/secret.vrm")


# ---------------------------------------------------------------------------
# list_assets()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_forge_client_list_assets_returns_list():
    """list_assets() GETs /v1/assets and returns a Python list."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    asset_list = [
        {"id": "vroid_base_v1", "asset_type": "base", "tags": []},
        {"id": "hair_pack_01", "asset_type": "texture", "tags": ["hair"]},
    ]
    assets_response = make_forge_response(200, asset_list)

    import httpx
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.get = AsyncMock(return_value=assets_response)
    client._http = mock_http

    result = await client.list_assets()

    call_args = mock_http.get.call_args
    assert call_args[0][0] == "/v1/assets"
    assert isinstance(result, list)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_forge_client_list_assets_passes_asset_type_query_param():
    """list_assets(asset_type='base') passes asset_type as a query parameter."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    assets_response = make_forge_response(200, [{"id": "vroid_base_v1", "asset_type": "base"}])

    import httpx
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.get = AsyncMock(return_value=assets_response)
    client._http = mock_http

    await client.list_assets(asset_type="base")

    call_kwargs = mock_http.get.call_args
    assert call_kwargs[1].get("params", {}).get("asset_type") == "base"


@pytest.mark.asyncio
async def test_forge_client_list_assets_handles_dict_wrapper_gracefully():
    """list_assets() unwraps {assets: [...]} server response to a plain list."""
    cfg = ForgeConfig()
    client = ForgeHttpClient(cfg)

    # Server returns wrapped dict instead of bare list
    wrapped_response = make_forge_response(200, {"assets": [{"id": "x"}, {"id": "y"}]})

    import httpx
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.get = AsyncMock(return_value=wrapped_response)
    client._http = mock_http

    result = await client.list_assets()

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["id"] == "x"


# ---------------------------------------------------------------------------
# Auth token header injection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_forge_client_token_env_set_includes_authorization_header(monkeypatch):
    """When token_env is set and resolved, Authorization: Bearer <token> is sent."""
    monkeypatch.setenv("MY_FORGE_TOKEN", "forge-bearer-token")
    cfg = ForgeConfig(token_env="MY_FORGE_TOKEN")
    client = ForgeHttpClient(cfg)

    assert client._token == "forge-bearer-token"

    health_response = make_forge_response(200, {"status": "ok", "version": "0.1.0"})

    import httpx
    captured_headers: dict = {}

    def capture_client(**kwargs):
        # Capture the headers passed to AsyncClient constructor
        captured_headers.update(kwargs.get("headers", {}))
        mock = AsyncMock(spec=httpx.AsyncClient)
        mock.get = AsyncMock(return_value=health_response)
        return mock

    with patch("httpx.AsyncClient", side_effect=capture_client):
        await client.open()

    assert "Authorization" in captured_headers
    assert captured_headers["Authorization"] == "Bearer forge-bearer-token"


# ---------------------------------------------------------------------------
# Live daemon tests (require Straumur running at localhost:8765) — SKIPPED
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Requires live Seidr-Smidja Straumur daemon at localhost:8765")
@pytest.mark.asyncio
async def test_forge_client_live_health():
    """Forge implements: verify GET /v1/health returns {'status': 'ok'}."""
    cfg = ForgeConfig(enabled=True)
    client = ForgeHttpClient(cfg)
    await client.open()
    health = await client.health()
    assert health.get("status") == "ok"
    await client.close()


@pytest.mark.skip(reason="Requires live Seidr-Smidja Straumur daemon + valid Loom spec")
@pytest.mark.asyncio
async def test_forge_client_live_build_avatar():
    """Forge implements: verify POST /v1/avatars returns success response shape."""
    cfg = ForgeConfig(enabled=True)
    client = ForgeHttpClient(cfg)
    await client.open()
    result = await client.build_avatar({"base_asset_id": "vroid_base_v1"})
    assert "success" in result
    assert "session_id" in result
    await client.close()
