"""
SmidjaSense orchestrator tests — Forge Wave 2 implementation.

Tests use mocked BrunhandHttpClient, mocked ForgeHttpClient, and a mock event emitter.
dispatch_tool_call NEVER raises — all errors return structured tool_result dicts.

v0.6.0: Brúarhönd half tests
v0.6.1: + dual-half lifecycle tests, Forge routing stubs

Ref: src/heretic/skilningr/senses/smidja/sense.py
     docs/architecture/SENSE_CONTRACTS.md §1 (lifecycle) §3 (error format)
"""

from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from heretic.skilningr.config_model import ForgeConfig, SmidjaConfig
from heretic.skilningr.senses.smidja.client import BrunhandHttpClient
from heretic.skilningr.senses.smidja.forge_client import ForgeHttpClient
from heretic.skilningr.senses.smidja.sense import SmidjaSense
from heretic.skilningr.senses.smidja.errors import (
    BrunhandAuthError,
    BrunhandTimeoutError,
    BrunhandUnreachableError,
)
from heretic.skilningr.senses.smidja.tools import SMIDJA_TOOL_DEFINITIONS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_config(enabled: bool = True, forge_enabled: bool = False) -> SmidjaConfig:
    return SmidjaConfig(
        enabled=enabled,
        host="127.0.0.1",
        port=8848,
        token_env="BRUNHAND_TOKEN_HERETIC",
        require_https=False,
        request_timeout_seconds=5,
        host_name="test-sense-host",
        forge=ForgeConfig(enabled=forge_enabled),
    )


def make_mock_brunhand_client() -> MagicMock:
    """Build a mock BrunhandHttpClient with async methods."""
    client = MagicMock(spec=BrunhandHttpClient)
    client.open = AsyncMock()
    client.close = AsyncMock()
    client.screenshot = AsyncMock()
    client.click = AsyncMock()
    client.type_text = AsyncMock()
    client.hotkey = AsyncMock()
    client.vroid_open = AsyncMock()
    client.vroid_export = AsyncMock()
    return client


def make_mock_forge_client() -> MagicMock:
    """Build a mock ForgeHttpClient with async stubs."""
    client = MagicMock(spec=ForgeHttpClient)
    client.open = AsyncMock()
    client.close = AsyncMock()
    client.health = AsyncMock()
    client.build_avatar = AsyncMock()
    client.get_avatar = AsyncMock()
    client.inspect_avatar = AsyncMock()
    client.list_assets = AsyncMock()
    return client


# Keep backwards-compatible alias
def make_mock_client() -> MagicMock:
    return make_mock_brunhand_client()


def make_sense(
    cfg: SmidjaConfig | None = None,
    brunhand_client: MagicMock | None = None,
    forge_client: MagicMock | None = None,
    event_emitter=None,
) -> SmidjaSense:
    """Construct a SmidjaSense with both halves mocked."""
    if cfg is None:
        cfg = make_config()
    if brunhand_client is None:
        brunhand_client = make_mock_brunhand_client()
    if forge_client is None:
        forge_client = make_mock_forge_client()
    return SmidjaSense(cfg, brunhand_client, forge_client, event_emitter=event_emitter)


def make_tool_call(tool_name: str, arguments: dict) -> dict:
    """Build an OpenAI-format tool_call dict."""
    return {
        "id": f"call_{tool_name.replace('.', '_')}",
        "type": "function",
        "function": {
            "name": tool_name,
            "arguments": json.dumps(arguments),
        },
    }


# ---------------------------------------------------------------------------
# tool_definitions property
# ---------------------------------------------------------------------------

def test_tool_definitions_returns_only_brunhand_tools_when_only_brunhand_enabled():
    """tool_definitions returns only Brúarhönd tools when only config.enabled=True."""
    cfg = make_config(enabled=True, forge_enabled=False)
    sense = make_sense(cfg)
    defs = sense.tool_definitions
    names = {t["function"]["name"] for t in defs}
    assert len(defs) == 6
    assert "smidja.forge_build_avatar" not in names
    assert "smidja.screenshot" in names


def test_tool_definitions_returns_only_forge_tools_when_only_forge_enabled():
    """tool_definitions returns only Forge tools when only forge.enabled=True."""
    cfg = make_config(enabled=False, forge_enabled=True)
    sense = make_sense(cfg)
    defs = sense.tool_definitions
    names = {t["function"]["name"] for t in defs}
    assert len(defs) == 3
    assert all(n.startswith("smidja.forge_") for n in names)


def test_tool_definitions_returns_all_nine_when_both_enabled():
    """tool_definitions returns all 9 tools when both halves are enabled."""
    cfg = make_config(enabled=True, forge_enabled=True)
    sense = make_sense(cfg)
    assert len(sense.tool_definitions) == 9


def test_tool_definitions_returns_empty_when_both_disabled():
    """tool_definitions returns [] when both halves are disabled."""
    cfg = make_config(enabled=False, forge_enabled=False)
    sense = make_sense(cfg)
    assert sense.tool_definitions == []


# ---------------------------------------------------------------------------
# is_available property (dual-half)
# ---------------------------------------------------------------------------

def test_is_available_false_before_open():
    """is_available is False before open() is called."""
    cfg = make_config(enabled=True)
    sense = make_sense(cfg)
    assert sense.is_available is False


@pytest.mark.asyncio
async def test_is_available_true_after_brunhand_open():
    """is_available is True after Brúarhönd half opens successfully."""
    cfg = make_config(enabled=True, forge_enabled=False)
    sense = make_sense(cfg)
    await sense.open()
    assert sense.is_available is True
    assert sense.brunhand_available is True
    assert sense.forge_available is False


@pytest.mark.asyncio
async def test_is_available_false_after_close():
    """is_available is False after close() is called."""
    cfg = make_config(enabled=True)
    sense = make_sense(cfg)
    await sense.open()
    assert sense.is_available is True
    await sense.close()
    assert sense.is_available is False


def test_is_available_false_when_both_disabled():
    """is_available is False when both halves are disabled."""
    cfg = make_config(enabled=False, forge_enabled=False)
    sense = make_sense(cfg)
    sense._brunhand_open = True
    sense._forge_open = True
    assert sense.is_available is False


# ---------------------------------------------------------------------------
# open / close — Brúarhönd half fault tolerance
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_open_degrades_gracefully_on_unreachable_daemon():
    """open() catches BrunhandUnreachableError and sets brunhand_available=False."""
    cfg = make_config(enabled=True)
    bc = make_mock_brunhand_client()
    bc.open = AsyncMock(side_effect=BrunhandUnreachableError("not reachable"))
    sense = make_sense(cfg, brunhand_client=bc)
    await sense.open()
    assert sense.is_available is False
    assert sense.brunhand_available is False


@pytest.mark.asyncio
async def test_open_degrades_gracefully_on_auth_error():
    """open() catches BrunhandAuthError and sets brunhand_available=False without raising."""
    cfg = make_config(enabled=True)
    bc = make_mock_brunhand_client()
    bc.open = AsyncMock(side_effect=BrunhandAuthError("rejected"))
    sense = make_sense(cfg, brunhand_client=bc)
    await sense.open()
    assert sense.is_available is False


@pytest.mark.asyncio
async def test_open_degrades_gracefully_on_unexpected_error():
    """open() catches unexpected exceptions and sets brunhand_available=False."""
    cfg = make_config(enabled=True)
    bc = make_mock_brunhand_client()
    bc.open = AsyncMock(side_effect=RuntimeError("unexpected"))
    sense = make_sense(cfg, brunhand_client=bc)
    await sense.open()
    assert sense.is_available is False


@pytest.mark.asyncio
async def test_close_is_idempotent():
    """close() can be called multiple times without raising."""
    cfg = make_config(enabled=True)
    sense = make_sense(cfg)
    await sense.open()
    await sense.close()
    await sense.close()
    assert sense.is_available is False


# ---------------------------------------------------------------------------
# open / close — Forge half degrades on NotImplementedError (Wave 1 stub)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_forge_half_degrades_gracefully_on_not_implemented():
    """open() catches NotImplementedError from ForgeHttpClient stub and sets forge_open=False."""
    cfg = make_config(enabled=True, forge_enabled=True)
    bc = make_mock_brunhand_client()
    fc = make_mock_forge_client()
    fc.open = AsyncMock(side_effect=NotImplementedError("stub"))
    sense = make_sense(cfg, brunhand_client=bc, forge_client=fc)
    await sense.open()
    # Brúarhönd should still be open; Forge degraded
    assert sense.brunhand_available is True
    assert sense.forge_available is False
    # Overall sense is still available via Brúarhönd
    assert sense.is_available is True


@pytest.mark.asyncio
async def test_brunhand_not_affected_when_forge_fails():
    """Brúarhönd remains available if Forge half fails to open."""
    cfg = make_config(enabled=True, forge_enabled=True)
    bc = make_mock_brunhand_client()
    fc = make_mock_forge_client()
    fc.open = AsyncMock(side_effect=RuntimeError("forge down"))
    sense = make_sense(cfg, brunhand_client=bc, forge_client=fc)
    await sense.open()
    assert sense.brunhand_available is True
    assert sense.forge_available is False


# ---------------------------------------------------------------------------
# dispatch_tool_call — Brúarhönd tools route to BrunhandHttpClient
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatch_screenshot_returns_tool_result():
    """dispatch_tool_call for smidja.screenshot returns dict with tool_call_id, role, content."""
    cfg = make_config(enabled=True)
    bc = make_mock_brunhand_client()
    raw_png = b"\x89PNG" + b"\x00" * 16
    bc.screenshot = AsyncMock(return_value=raw_png)

    sense = make_sense(cfg, brunhand_client=bc)
    sense._brunhand_open = True

    tc = make_tool_call("smidja.screenshot", {})
    result = await sense.dispatch_tool_call(tc)

    assert result["tool_call_id"] == tc["id"]
    assert result["role"] == "tool"
    assert "content" in result


@pytest.mark.asyncio
async def test_dispatch_screenshot_encodes_png_as_data_url():
    """smidja.screenshot result content contains a base64 data URL for the PNG."""
    cfg = make_config(enabled=True)
    bc = make_mock_brunhand_client()
    raw_png = b"\x89PNG" + b"\x00" * 16
    bc.screenshot = AsyncMock(return_value=raw_png)

    sense = make_sense(cfg, brunhand_client=bc)
    sense._brunhand_open = True

    tc = make_tool_call("smidja.screenshot", {})
    result = await sense.dispatch_tool_call(tc)

    content = json.loads(result["content"])
    assert "data_url" in content
    assert content["data_url"].startswith("data:image/png;base64,")
    b64_part = content["data_url"][len("data:image/png;base64,"):]
    decoded = base64.b64decode(b64_part)
    assert decoded == raw_png


@pytest.mark.asyncio
async def test_dispatch_click_returns_tool_result():
    """dispatch_tool_call for smidja.click returns tool_result with click payload."""
    cfg = make_config(enabled=True)
    bc = make_mock_brunhand_client()
    bc.click = AsyncMock(return_value={"x": 100, "y": 200, "clicks_delivered": 1})

    sense = make_sense(cfg, brunhand_client=bc)
    sense._brunhand_open = True

    tc = make_tool_call("smidja.click", {"x": 100, "y": 200})
    result = await sense.dispatch_tool_call(tc)

    assert result["role"] == "tool"
    content = json.loads(result["content"])
    assert content["x"] == 100


@pytest.mark.asyncio
async def test_dispatch_type_text_calls_client():
    """dispatch_tool_call for smidja.type_text calls brunhand_client.type_text."""
    cfg = make_config(enabled=True)
    bc = make_mock_brunhand_client()
    bc.type_text = AsyncMock(return_value={"characters_typed": 5})

    sense = make_sense(cfg, brunhand_client=bc)
    sense._brunhand_open = True

    tc = make_tool_call("smidja.type_text", {"text": "hello"})
    result = await sense.dispatch_tool_call(tc)

    bc.type_text.assert_called_once_with(text="hello", interval=0.05)
    assert result["role"] == "tool"


@pytest.mark.asyncio
async def test_dispatch_hotkey_calls_client():
    """dispatch_tool_call for smidja.hotkey calls brunhand_client.hotkey."""
    cfg = make_config(enabled=True)
    bc = make_mock_brunhand_client()
    bc.hotkey = AsyncMock(return_value={"keys": ["ctrl", "s"]})

    sense = make_sense(cfg, brunhand_client=bc)
    sense._brunhand_open = True

    tc = make_tool_call("smidja.hotkey", {"keys": ["ctrl", "s"]})
    result = await sense.dispatch_tool_call(tc)

    bc.hotkey.assert_called_once_with(keys=["ctrl", "s"])
    assert result["role"] == "tool"


@pytest.mark.asyncio
async def test_dispatch_vroid_open_calls_client():
    """dispatch_tool_call for smidja.vroid_open calls brunhand_client.vroid_open."""
    cfg = make_config(enabled=True)
    bc = make_mock_brunhand_client()
    bc.vroid_open = AsyncMock(return_value={"opened_path": "char.vroid"})

    sense = make_sense(cfg, brunhand_client=bc)
    sense._brunhand_open = True

    tc = make_tool_call("smidja.vroid_open", {"project_path": "char.vroid"})
    result = await sense.dispatch_tool_call(tc)

    bc.vroid_open.assert_called_once_with(project_path="char.vroid", wait_timeout_seconds=60.0)
    assert result["role"] == "tool"


@pytest.mark.asyncio
async def test_dispatch_vroid_export_calls_client():
    """dispatch_tool_call for smidja.vroid_export calls brunhand_client.vroid_export."""
    cfg = make_config(enabled=True)
    bc = make_mock_brunhand_client()
    bc.vroid_export = AsyncMock(return_value={"exported_path": "avatar.vrm"})

    sense = make_sense(cfg, brunhand_client=bc)
    sense._brunhand_open = True

    tc = make_tool_call("smidja.vroid_export", {"output_path": "avatar.vrm"})
    result = await sense.dispatch_tool_call(tc)

    bc.vroid_export.assert_called_once_with(
        output_path="avatar.vrm", overwrite=True, wait_timeout_seconds=120.0
    )
    assert result["role"] == "tool"


# ---------------------------------------------------------------------------
# dispatch_tool_call — Forge tools return structured error (Wave 1 stubs)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_forge_tool_when_forge_not_open_returns_sense_unavailable():
    """smidja.forge_* tools return SENSE_UNAVAILABLE when Forge half is not open."""
    cfg = make_config(enabled=True, forge_enabled=True)
    sense = make_sense(cfg)
    sense._brunhand_open = True
    sense._forge_open = False  # Forge half not open

    tc = make_tool_call("smidja.forge_build_avatar", {"loom_spec": {"base_asset_id": "test"}})
    result = await sense.dispatch_tool_call(tc)

    assert result["role"] == "tool"
    content = json.loads(result["content"])
    assert content["error"] is True
    assert content["code"] == "SENSE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_forge_tool_when_forge_open_returns_not_implemented_error():
    """smidja.forge_* tools return SENSE_INTERNAL_ERROR (NotImplementedError) in Wave 1."""
    cfg = make_config(enabled=True, forge_enabled=True)
    sense = make_sense(cfg)
    sense._brunhand_open = True
    sense._forge_open = True  # Forge open but method is still a stub

    tc = make_tool_call("smidja.forge_build_avatar", {"loom_spec": {"base_asset_id": "test"}})
    result = await sense.dispatch_tool_call(tc)

    # dispatch_tool_call NEVER raises — NotImplementedError is caught as unexpected exception
    assert result["role"] == "tool"
    content = json.loads(result["content"])
    assert content["error"] is True


# ---------------------------------------------------------------------------
# dispatch_tool_call — error handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatch_never_raises_on_client_error():
    """dispatch_tool_call catches all client errors and returns error tool_result."""
    cfg = make_config(enabled=True)
    bc = make_mock_brunhand_client()
    bc.screenshot = AsyncMock(side_effect=BrunhandUnreachableError("daemon down"))

    sense = make_sense(cfg, brunhand_client=bc)
    sense._brunhand_open = True

    tc = make_tool_call("smidja.screenshot", {})
    result = await sense.dispatch_tool_call(tc)

    assert result["role"] == "tool"
    content = json.loads(result["content"])
    assert content["error"] is True
    assert content["code"] == "EXTERNAL_APP_UNAVAILABLE"


@pytest.mark.asyncio
async def test_dispatch_never_raises_on_unexpected_exception():
    """dispatch_tool_call catches unexpected exceptions and returns error tool_result."""
    cfg = make_config(enabled=True)
    bc = make_mock_brunhand_client()
    bc.click = AsyncMock(side_effect=RuntimeError("something exploded"))

    sense = make_sense(cfg, brunhand_client=bc)
    sense._brunhand_open = True

    tc = make_tool_call("smidja.click", {"x": 0, "y": 0})
    result = await sense.dispatch_tool_call(tc)

    assert result["role"] == "tool"
    content = json.loads(result["content"])
    assert content["error"] is True


@pytest.mark.asyncio
async def test_dispatch_unknown_tool_name_returns_error():
    """dispatch_tool_call with unknown smidja.* name returns structured error."""
    cfg = make_config(enabled=True)
    sense = make_sense(cfg)
    sense._brunhand_open = True

    tc = make_tool_call("smidja.does_not_exist", {})
    result = await sense.dispatch_tool_call(tc)

    assert result["role"] == "tool"
    content = json.loads(result["content"])
    assert content["error"] is True


@pytest.mark.asyncio
async def test_dispatch_invalid_json_arguments_returns_error():
    """dispatch_tool_call with invalid JSON arguments returns INVALID_ARGUMENTS error."""
    cfg = make_config(enabled=True)
    sense = make_sense(cfg)
    sense._brunhand_open = True

    tc = {
        "id": "call_bad",
        "type": "function",
        "function": {"name": "smidja.screenshot", "arguments": "{invalid json"},
    }
    result = await sense.dispatch_tool_call(tc)

    assert result["role"] == "tool"
    content = json.loads(result["content"])
    assert content["error"] is True
    assert content["code"] == "INVALID_ARGUMENTS"


# ---------------------------------------------------------------------------
# Event emission
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatch_emits_started_and_completed_events():
    """dispatch_tool_call calls event_emitter with STARTED then COMPLETED events."""
    cfg = make_config(enabled=True)
    bc = make_mock_brunhand_client()
    bc.screenshot = AsyncMock(return_value=b"\x89PNG\x00" * 4)

    emitted_events = []
    sense = make_sense(cfg, brunhand_client=bc, event_emitter=emitted_events.append)
    sense._brunhand_open = True

    tc = make_tool_call("smidja.screenshot", {})
    await sense.dispatch_tool_call(tc)

    assert len(emitted_events) == 2
    states = [e.state.value for e in emitted_events]
    assert states[0] == "started"
    assert states[1] == "completed"


@pytest.mark.asyncio
async def test_dispatch_emits_failed_event_on_error():
    """dispatch_tool_call emits FAILED event when client raises."""
    cfg = make_config(enabled=True)
    bc = make_mock_brunhand_client()
    bc.screenshot = AsyncMock(side_effect=BrunhandTimeoutError("timeout"))

    emitted_events = []
    sense = make_sense(cfg, brunhand_client=bc, event_emitter=emitted_events.append)
    sense._brunhand_open = True

    tc = make_tool_call("smidja.screenshot", {})
    result = await sense.dispatch_tool_call(tc)

    assert len(emitted_events) == 2
    states = [e.state.value for e in emitted_events]
    assert "failed" in states
    assert result["role"] == "tool"


@pytest.mark.asyncio
async def test_dispatch_completed_event_has_duration_ms():
    """COMPLETED event has duration_ms set."""
    cfg = make_config(enabled=True)
    bc = make_mock_brunhand_client()
    bc.hotkey = AsyncMock(return_value={"keys": ["enter"]})

    emitted_events = []
    sense = make_sense(cfg, brunhand_client=bc, event_emitter=emitted_events.append)
    sense._brunhand_open = True

    tc = make_tool_call("smidja.hotkey", {"keys": ["enter"]})
    await sense.dispatch_tool_call(tc)

    completed_event = [e for e in emitted_events if e.state.value == "completed"][0]
    assert completed_event.duration_ms is not None
    assert completed_event.duration_ms >= 0


@pytest.mark.asyncio
async def test_dispatch_event_has_correct_tool_name_and_call_id():
    """Events carry the correct tool_name and call_id."""
    cfg = make_config(enabled=True)
    bc = make_mock_brunhand_client()
    bc.click = AsyncMock(return_value={"x": 5, "y": 10})

    emitted_events = []
    sense = make_sense(cfg, brunhand_client=bc, event_emitter=emitted_events.append)
    sense._brunhand_open = True

    tc = make_tool_call("smidja.click", {"x": 5, "y": 10})
    await sense.dispatch_tool_call(tc)

    for event in emitted_events:
        assert event.tool_name == "smidja.click"
        assert event.call_id == tc["id"]


@pytest.mark.asyncio
async def test_dispatch_without_event_emitter_does_not_raise():
    """dispatch_tool_call without event_emitter does not raise."""
    cfg = make_config(enabled=True)
    bc = make_mock_brunhand_client()
    bc.screenshot = AsyncMock(return_value=b"\x89PNG")

    sense = make_sense(cfg, brunhand_client=bc, event_emitter=None)
    sense._brunhand_open = True

    tc = make_tool_call("smidja.screenshot", {})
    result = await sense.dispatch_tool_call(tc)
    assert result["role"] == "tool"
