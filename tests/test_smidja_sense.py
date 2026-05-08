"""
SmidjaSense orchestrator tests — Forge Wave 2 implementation.

Tests use mocked BrunhandHttpClient and a mock event emitter.
dispatch_tool_call NEVER raises — all errors return structured tool_result dicts.

Ref: src/heretic/skilningr/senses/smidja/sense.py
     docs/architecture/SENSE_CONTRACTS.md §1 (lifecycle) §3 (error format)
"""

from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from heretic.skilningr.config_model import SmidjaConfig
from heretic.skilningr.senses.smidja.client import BrunhandHttpClient
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

def make_config(enabled: bool = True) -> SmidjaConfig:
    return SmidjaConfig(
        enabled=enabled,
        host="127.0.0.1",
        port=8848,
        token_env="BRUNHAND_TOKEN_HERETIC",
        require_https=False,
        request_timeout_seconds=5,
        host_name="test-sense-host",
    )


def make_mock_client() -> MagicMock:
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

def test_tool_definitions_returns_smidja_tool_definitions_when_enabled():
    """tool_definitions returns SMIDJA_TOOL_DEFINITIONS when config.enabled=True."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    sense = SmidjaSense(cfg, client)
    assert sense.tool_definitions == SMIDJA_TOOL_DEFINITIONS
    assert len(sense.tool_definitions) == 6


def test_tool_definitions_returns_empty_when_disabled():
    """tool_definitions returns [] when config.enabled=False."""
    cfg = make_config(enabled=False)
    client = make_mock_client()
    sense = SmidjaSense(cfg, client)
    assert sense.tool_definitions == []


# ---------------------------------------------------------------------------
# is_available property
# ---------------------------------------------------------------------------

def test_is_available_false_before_open():
    """is_available is False before open() is called."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    sense = SmidjaSense(cfg, client)
    assert sense.is_available is False


@pytest.mark.asyncio
async def test_is_available_true_after_successful_open():
    """is_available is True after open() completes without error."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    client.open = AsyncMock()
    sense = SmidjaSense(cfg, client)
    await sense.open()
    assert sense.is_available is True


@pytest.mark.asyncio
async def test_is_available_false_after_close():
    """is_available is False after close() is called."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    sense = SmidjaSense(cfg, client)
    await sense.open()
    assert sense.is_available is True
    await sense.close()
    assert sense.is_available is False


def test_is_available_false_when_disabled():
    """is_available is False when config.enabled=False even if opened."""
    cfg = make_config(enabled=False)
    client = make_mock_client()
    sense = SmidjaSense(cfg, client)
    # Force _is_open to True to test that enabled=False still gates is_available
    sense._is_open = True
    assert sense.is_available is False


# ---------------------------------------------------------------------------
# open / close fault tolerance
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_open_degrades_gracefully_on_unreachable_daemon():
    """open() catches BrunhandUnreachableError and sets is_available=False without raising."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    client.open = AsyncMock(side_effect=BrunhandUnreachableError("not reachable"))
    sense = SmidjaSense(cfg, client)
    # Must NOT raise
    await sense.open()
    assert sense.is_available is False


@pytest.mark.asyncio
async def test_open_degrades_gracefully_on_auth_error():
    """open() catches BrunhandAuthError and sets is_available=False without raising."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    client.open = AsyncMock(side_effect=BrunhandAuthError("rejected"))
    sense = SmidjaSense(cfg, client)
    await sense.open()
    assert sense.is_available is False


@pytest.mark.asyncio
async def test_open_degrades_gracefully_on_unexpected_error():
    """open() catches unexpected exceptions and sets is_available=False without raising."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    client.open = AsyncMock(side_effect=RuntimeError("unexpected"))
    sense = SmidjaSense(cfg, client)
    await sense.open()
    assert sense.is_available is False


@pytest.mark.asyncio
async def test_close_is_idempotent():
    """close() can be called multiple times without raising."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    sense = SmidjaSense(cfg, client)
    await sense.open()
    await sense.close()
    await sense.close()  # second call must not raise
    assert sense.is_available is False


# ---------------------------------------------------------------------------
# dispatch_tool_call — never raises
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatch_screenshot_returns_tool_result():
    """dispatch_tool_call for smidja.screenshot returns dict with tool_call_id, role, content."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    raw_png = b"\x89PNG" + b"\x00" * 16
    client.screenshot = AsyncMock(return_value=raw_png)

    sense = SmidjaSense(cfg, client)
    sense._is_open = True

    tc = make_tool_call("smidja.screenshot", {})
    result = await sense.dispatch_tool_call(tc)

    assert result["tool_call_id"] == tc["id"]
    assert result["role"] == "tool"
    assert "content" in result


@pytest.mark.asyncio
async def test_dispatch_screenshot_encodes_png_as_data_url():
    """smidja.screenshot result content contains a base64 data URL for the PNG."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    raw_png = b"\x89PNG" + b"\x00" * 16
    client.screenshot = AsyncMock(return_value=raw_png)

    sense = SmidjaSense(cfg, client)
    sense._is_open = True

    tc = make_tool_call("smidja.screenshot", {})
    result = await sense.dispatch_tool_call(tc)

    content = json.loads(result["content"])
    assert "data_url" in content
    assert content["data_url"].startswith("data:image/png;base64,")

    # Verify the data URL actually decodes back to the original bytes
    b64_part = content["data_url"][len("data:image/png;base64,"):]
    decoded = base64.b64decode(b64_part)
    assert decoded == raw_png


@pytest.mark.asyncio
async def test_dispatch_click_returns_tool_result():
    """dispatch_tool_call for smidja.click returns tool_result with click payload."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    client.click = AsyncMock(return_value={"x": 100, "y": 200, "clicks_delivered": 1})

    sense = SmidjaSense(cfg, client)
    sense._is_open = True

    tc = make_tool_call("smidja.click", {"x": 100, "y": 200})
    result = await sense.dispatch_tool_call(tc)

    assert result["role"] == "tool"
    content = json.loads(result["content"])
    assert content["x"] == 100


@pytest.mark.asyncio
async def test_dispatch_type_text_calls_client(monkeypatch):
    """dispatch_tool_call for smidja.type_text calls client.type_text with text param."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    client.type_text = AsyncMock(return_value={"characters_typed": 5})

    sense = SmidjaSense(cfg, client)
    sense._is_open = True

    tc = make_tool_call("smidja.type_text", {"text": "hello"})
    result = await sense.dispatch_tool_call(tc)

    client.type_text.assert_called_once_with(text="hello", interval=0.05)
    assert result["role"] == "tool"


@pytest.mark.asyncio
async def test_dispatch_hotkey_calls_client():
    """dispatch_tool_call for smidja.hotkey calls client.hotkey with keys param."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    client.hotkey = AsyncMock(return_value={"keys": ["ctrl", "s"]})

    sense = SmidjaSense(cfg, client)
    sense._is_open = True

    tc = make_tool_call("smidja.hotkey", {"keys": ["ctrl", "s"]})
    result = await sense.dispatch_tool_call(tc)

    client.hotkey.assert_called_once_with(keys=["ctrl", "s"])
    assert result["role"] == "tool"


@pytest.mark.asyncio
async def test_dispatch_vroid_open_calls_client():
    """dispatch_tool_call for smidja.vroid_open calls client.vroid_open."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    client.vroid_open = AsyncMock(return_value={"opened_path": "char.vroid"})

    sense = SmidjaSense(cfg, client)
    sense._is_open = True

    tc = make_tool_call("smidja.vroid_open", {"project_path": "char.vroid"})
    result = await sense.dispatch_tool_call(tc)

    client.vroid_open.assert_called_once_with(project_path="char.vroid", wait_timeout_seconds=60.0)
    assert result["role"] == "tool"


@pytest.mark.asyncio
async def test_dispatch_vroid_export_calls_client():
    """dispatch_tool_call for smidja.vroid_export calls client.vroid_export."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    client.vroid_export = AsyncMock(return_value={"exported_path": "avatar.vrm"})

    sense = SmidjaSense(cfg, client)
    sense._is_open = True

    tc = make_tool_call("smidja.vroid_export", {"output_path": "avatar.vrm"})
    result = await sense.dispatch_tool_call(tc)

    client.vroid_export.assert_called_once_with(
        output_path="avatar.vrm", overwrite=True, wait_timeout_seconds=120.0
    )
    assert result["role"] == "tool"


@pytest.mark.asyncio
async def test_dispatch_never_raises_on_client_error():
    """dispatch_tool_call catches all client errors and returns error tool_result."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    client.screenshot = AsyncMock(side_effect=BrunhandUnreachableError("daemon down"))

    sense = SmidjaSense(cfg, client)
    sense._is_open = True

    tc = make_tool_call("smidja.screenshot", {})
    # Must NOT raise
    result = await sense.dispatch_tool_call(tc)

    assert result["role"] == "tool"
    content = json.loads(result["content"])
    assert content["error"] is True
    assert content["code"] == "EXTERNAL_APP_UNAVAILABLE"


@pytest.mark.asyncio
async def test_dispatch_never_raises_on_unexpected_exception():
    """dispatch_tool_call catches unexpected exceptions and returns error tool_result."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    client.click = AsyncMock(side_effect=RuntimeError("something exploded"))

    sense = SmidjaSense(cfg, client)
    sense._is_open = True

    tc = make_tool_call("smidja.click", {"x": 0, "y": 0})
    result = await sense.dispatch_tool_call(tc)

    assert result["role"] == "tool"
    content = json.loads(result["content"])
    assert content["error"] is True


@pytest.mark.asyncio
async def test_dispatch_unknown_tool_name_returns_error():
    """dispatch_tool_call with unknown smidja.* name returns SENSE_INTERNAL_ERROR."""
    cfg = make_config(enabled=True)
    client = make_mock_client()

    sense = SmidjaSense(cfg, client)
    sense._is_open = True

    tc = make_tool_call("smidja.does_not_exist", {})
    result = await sense.dispatch_tool_call(tc)

    assert result["role"] == "tool"
    content = json.loads(result["content"])
    assert content["error"] is True


@pytest.mark.asyncio
async def test_dispatch_invalid_json_arguments_returns_error():
    """dispatch_tool_call with invalid JSON arguments returns INVALID_ARGUMENTS error."""
    cfg = make_config(enabled=True)
    client = make_mock_client()

    sense = SmidjaSense(cfg, client)
    sense._is_open = True

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


@pytest.mark.asyncio
async def test_dispatch_emits_started_and_completed_events():
    """dispatch_tool_call calls event_emitter with STARTED then COMPLETED events."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    client.screenshot = AsyncMock(return_value=b"\x89PNG\x00" * 4)

    emitted_events = []
    sense = SmidjaSense(cfg, client, event_emitter=emitted_events.append)
    sense._is_open = True

    tc = make_tool_call("smidja.screenshot", {})
    await sense.dispatch_tool_call(tc)

    # Two events: STARTED then COMPLETED
    assert len(emitted_events) == 2
    states = [e.state.value for e in emitted_events]
    assert states[0] == "started"
    assert states[1] == "completed"


@pytest.mark.asyncio
async def test_dispatch_emits_failed_event_on_error():
    """dispatch_tool_call calls event_emitter with FAILED event when client raises."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    client.screenshot = AsyncMock(side_effect=BrunhandTimeoutError("timeout"))

    emitted_events = []
    sense = SmidjaSense(cfg, client, event_emitter=emitted_events.append)
    sense._is_open = True

    tc = make_tool_call("smidja.screenshot", {})
    result = await sense.dispatch_tool_call(tc)

    # Must have emitted: STARTED, then FAILED
    assert len(emitted_events) == 2
    states = [e.state.value for e in emitted_events]
    assert "failed" in states

    # Result is still a valid error tool_result (never raises)
    assert result["role"] == "tool"


@pytest.mark.asyncio
async def test_dispatch_completed_event_has_duration_ms():
    """COMPLETED event has duration_ms set."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    client.hotkey = AsyncMock(return_value={"keys": ["enter"]})

    emitted_events = []
    sense = SmidjaSense(cfg, client, event_emitter=emitted_events.append)
    sense._is_open = True

    tc = make_tool_call("smidja.hotkey", {"keys": ["enter"]})
    await sense.dispatch_tool_call(tc)

    completed_event = [e for e in emitted_events if e.state.value == "completed"][0]
    assert completed_event.duration_ms is not None
    assert completed_event.duration_ms >= 0


@pytest.mark.asyncio
async def test_dispatch_event_has_correct_tool_name_and_call_id():
    """Events emitted by dispatch_tool_call carry the correct tool_name and call_id."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    client.click = AsyncMock(return_value={"x": 5, "y": 10})

    emitted_events = []
    sense = SmidjaSense(cfg, client, event_emitter=emitted_events.append)
    sense._is_open = True

    tc = make_tool_call("smidja.click", {"x": 5, "y": 10})
    await sense.dispatch_tool_call(tc)

    for event in emitted_events:
        assert event.tool_name == "smidja.click"
        assert event.call_id == tc["id"]


@pytest.mark.asyncio
async def test_dispatch_without_event_emitter_does_not_raise():
    """dispatch_tool_call without event_emitter does not raise (emitter is optional)."""
    cfg = make_config(enabled=True)
    client = make_mock_client()
    client.screenshot = AsyncMock(return_value=b"\x89PNG")

    sense = SmidjaSense(cfg, client, event_emitter=None)
    sense._is_open = True

    tc = make_tool_call("smidja.screenshot", {})
    result = await sense.dispatch_tool_call(tc)
    assert result["role"] == "tool"
