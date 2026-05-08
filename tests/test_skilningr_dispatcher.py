"""
ToolDispatcher routing tests — Forge Wave 2 implementation.

Ref: src/heretic/skilningr/dispatcher.py
     docs/architecture/SENSE_CONTRACTS.md §3 (error format)
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from heretic.skilningr.dispatcher import ToolDispatcher, _error_result


# ---------------------------------------------------------------------------
# _error_result helper (pure function — no stubs needed)
# ---------------------------------------------------------------------------

def test_error_result_structure():
    """_error_result returns a dict with tool_call_id, role='tool', content (JSON)."""
    result = _error_result("call-1", "smidja.screenshot", "SENSE_UNAVAILABLE", "down")
    assert result["tool_call_id"] == "call-1"
    assert result["role"] == "tool"
    payload = json.loads(result["content"])
    assert payload["error"] is True
    assert payload["code"] == "SENSE_UNAVAILABLE"
    assert payload["sense"] == "smidja"
    assert payload["tool"] == "smidja.screenshot"


def test_error_result_derives_sense_from_tool_name():
    """_error_result derives sense from tool_name prefix when sense='' ."""
    result = _error_result("x", "filesystem.read_file", "NOT_FOUND", "missing")
    payload = json.loads(result["content"])
    assert payload["sense"] == "filesystem"


def test_error_result_explicit_sense_overrides_prefix():
    """Explicit sense argument takes precedence over tool_name prefix derivation."""
    result = _error_result("x", "smidja.click", "PERMISSION_DENIED", "no", sense="custom")
    payload = json.loads(result["content"])
    assert payload["sense"] == "custom"


def test_error_result_detail_included_when_given():
    """Optional detail field appears in content JSON when non-empty."""
    result = _error_result("x", "smidja.hotkey", "SENSE_TIMEOUT", "timed out", detail="30s")
    payload = json.loads(result["content"])
    assert payload["detail"] == "30s"


def test_error_result_detail_absent_when_empty():
    """detail field must be absent from content JSON when not provided."""
    result = _error_result("x", "smidja.hotkey", "SENSE_TIMEOUT", "timed out")
    payload = json.loads(result["content"])
    assert "detail" not in payload


def test_error_result_content_is_valid_json():
    """content field of error_result is always valid JSON."""
    result = _error_result("cid", "smidja.screenshot", "SENSE_INTERNAL_ERROR", "oops")
    parsed = json.loads(result["content"])
    assert isinstance(parsed, dict)


# ---------------------------------------------------------------------------
# ToolDispatcher.register_sense
# ---------------------------------------------------------------------------

def test_register_sense_stores_sense():
    """register_sense("smidja", mock_sense) — sense retrievable; no exception."""
    dispatcher = ToolDispatcher()
    mock_sense = MagicMock()
    dispatcher.register_sense("smidja", mock_sense)
    assert "smidja" in dispatcher.registered_prefixes
    assert dispatcher._senses["smidja"] is mock_sense


def test_register_sense_rejects_dotted_prefix():
    """register_sense raises ValueError if prefix contains a dot."""
    dispatcher = ToolDispatcher()
    with pytest.raises(ValueError, match="dot"):
        dispatcher.register_sense("smidja.sub", MagicMock())


def test_register_sense_rejects_empty_prefix():
    """register_sense raises ValueError if prefix is empty string."""
    dispatcher = ToolDispatcher()
    with pytest.raises(ValueError, match="non-empty"):
        dispatcher.register_sense("", MagicMock())


def test_register_multiple_senses():
    """Multiple senses can be registered under different prefixes."""
    dispatcher = ToolDispatcher()
    dispatcher.register_sense("smidja", MagicMock())
    dispatcher.register_sense("filesystem", MagicMock())
    assert set(dispatcher.registered_prefixes) == {"smidja", "filesystem"}


def test_unregister_sense_removes_prefix():
    """unregister_sense removes the sense from the registry."""
    dispatcher = ToolDispatcher()
    dispatcher.register_sense("smidja", MagicMock())
    dispatcher.unregister_sense("smidja")
    assert "smidja" not in dispatcher.registered_prefixes


def test_unregister_sense_no_op_if_not_registered():
    """unregister_sense is a no-op if prefix is not registered."""
    dispatcher = ToolDispatcher()
    dispatcher.unregister_sense("nonexistent")  # Must not raise


# ---------------------------------------------------------------------------
# ToolDispatcher.all_tool_definitions
# ---------------------------------------------------------------------------

def test_all_tool_definitions_aggregates_senses():
    """all_tool_definitions returns flat list of tool dicts from all registered senses."""
    dispatcher = ToolDispatcher()

    sense_a = MagicMock()
    sense_a.tool_definitions = [{"type": "function", "function": {"name": "a.tool1"}}]
    sense_b = MagicMock()
    sense_b.tool_definitions = [
        {"type": "function", "function": {"name": "b.tool1"}},
        {"type": "function", "function": {"name": "b.tool2"}},
    ]

    dispatcher.register_sense("a", sense_a)
    dispatcher.register_sense("b", sense_b)

    defs = dispatcher.all_tool_definitions()
    assert len(defs) == 3
    names = {d["function"]["name"] for d in defs}
    assert names == {"a.tool1", "b.tool1", "b.tool2"}


def test_all_tool_definitions_empty_when_no_senses():
    """all_tool_definitions returns empty list when no senses are registered."""
    dispatcher = ToolDispatcher()
    assert dispatcher.all_tool_definitions() == []


def test_all_tool_definitions_tolerates_sense_without_definitions():
    """all_tool_definitions skips senses that raise on tool_definitions."""
    dispatcher = ToolDispatcher()

    bad_sense = MagicMock()
    type(bad_sense).tool_definitions = MagicMock(side_effect=RuntimeError("broken"))
    good_sense = MagicMock()
    good_sense.tool_definitions = [{"type": "function", "function": {"name": "ok.tool"}}]

    dispatcher.register_sense("bad", bad_sense)
    dispatcher.register_sense("ok", good_sense)

    defs = dispatcher.all_tool_definitions()
    # Should still return the good sense's definitions
    assert len(defs) == 1
    assert defs[0]["function"]["name"] == "ok.tool"


# ---------------------------------------------------------------------------
# ToolDispatcher.dispatch
# ---------------------------------------------------------------------------

def make_tool_call_dict(name: str, arguments: str = "{}") -> dict:
    return {
        "id": f"call_{name.replace('.', '_')}",
        "type": "function",
        "function": {"name": name, "arguments": arguments},
    }


@pytest.mark.asyncio
async def test_dispatch_routes_to_registered_sense():
    """dispatch with a registered prefix calls sense.dispatch_tool_call."""
    dispatcher = ToolDispatcher()

    mock_sense = MagicMock()
    mock_sense.is_available = True
    expected_result = {"tool_call_id": "call_smidja_screenshot", "role": "tool", "content": "{}"}
    mock_sense.dispatch_tool_call = AsyncMock(return_value=expected_result)

    dispatcher.register_sense("smidja", mock_sense)

    tc = make_tool_call_dict("smidja.screenshot")
    result = await dispatcher.dispatch(tc)

    mock_sense.dispatch_tool_call.assert_called_once_with(tc)
    assert result == expected_result


@pytest.mark.asyncio
async def test_dispatch_unknown_prefix_returns_error_json():
    """dispatch with unknown prefix returns tool_result with TOOL_NOT_FOUND error."""
    dispatcher = ToolDispatcher()

    tc = make_tool_call_dict("unknown_sense.do_something")
    result = await dispatcher.dispatch(tc)

    assert result["role"] == "tool"
    payload = json.loads(result["content"])
    assert payload["error"] is True
    assert payload["code"] == "TOOL_NOT_FOUND"


@pytest.mark.asyncio
async def test_dispatch_unavailable_sense_returns_error_json():
    """dispatch when sense.is_available=False returns SENSE_UNAVAILABLE tool_result."""
    dispatcher = ToolDispatcher()

    mock_sense = MagicMock()
    mock_sense.is_available = False
    mock_sense.dispatch_tool_call = AsyncMock()
    dispatcher.register_sense("smidja", mock_sense)

    tc = make_tool_call_dict("smidja.screenshot")
    result = await dispatcher.dispatch(tc)

    # dispatch_tool_call should NOT have been called
    mock_sense.dispatch_tool_call.assert_not_called()
    payload = json.loads(result["content"])
    assert payload["code"] == "SENSE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_dispatch_never_raises():
    """dispatch catches all exceptions and returns tool_result — never raises."""
    dispatcher = ToolDispatcher()

    bad_sense = MagicMock()
    bad_sense.is_available = True
    bad_sense.dispatch_tool_call = AsyncMock(side_effect=RuntimeError("violated contract"))
    dispatcher.register_sense("bad", bad_sense)

    tc = make_tool_call_dict("bad.tool")
    # Must NOT raise
    result = await dispatcher.dispatch(tc)

    assert result["role"] == "tool"
    payload = json.loads(result["content"])
    assert payload["error"] is True


@pytest.mark.asyncio
async def test_dispatch_missing_function_name_returns_error():
    """dispatch with missing function.name returns TOOL_NOT_FOUND error."""
    dispatcher = ToolDispatcher()
    tc = {"id": "bad", "type": "function", "function": {"name": "", "arguments": "{}"}}
    result = await dispatcher.dispatch(tc)
    payload = json.loads(result["content"])
    assert payload["error"] is True


@pytest.mark.asyncio
async def test_dispatch_returns_sense_result_verbatim():
    """dispatch returns whatever dispatch_tool_call returns, unmodified."""
    dispatcher = ToolDispatcher()

    mock_sense = MagicMock()
    mock_sense.is_available = True
    raw_result = {"tool_call_id": "c1", "role": "tool", "content": '{"data": "value"}'}
    mock_sense.dispatch_tool_call = AsyncMock(return_value=raw_result)
    dispatcher.register_sense("smidja", mock_sense)

    tc = make_tool_call_dict("smidja.screenshot")
    result = await dispatcher.dispatch(tc)
    assert result == raw_result


@pytest.mark.asyncio
async def test_dispatch_call_id_echoed_in_error_results():
    """Dispatcher error results echo the call_id correctly."""
    dispatcher = ToolDispatcher()
    tc = make_tool_call_dict("no_such_prefix.tool")
    result = await dispatcher.dispatch(tc)
    assert result["tool_call_id"] == tc["id"]
