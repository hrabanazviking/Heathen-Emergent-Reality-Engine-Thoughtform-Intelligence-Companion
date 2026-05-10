"""
v0.6.3 Verkminni tests — deed-memory audit log for Smiðja.

Covers:
    - AuditEntry construction (frozen dataclass)
    - AuditLog ring buffer: record / entries / clear / __len__
    - Ring-buffer eviction at maxlen=depth (V-3)
    - NullAuditLog no-op behaviour (V-5)
    - Argument and error truncation policy
    - SmidjaSense dispatch hook records started + completed on success
    - SmidjaSense dispatch hook records started + failed on SmidjaError
    - SmidjaSense dispatch hook records started + failed on unexpected Exception
    - Audit-write failure cannot break dispatch (V-2)
    - SmidjaSense.close() clears the audit log (V-4)
    - opt-out via NullAuditLog (V-5)

Ref: src/heretic/skilningr/senses/smidja/verkminni.py
     src/heretic/skilningr/senses/smidja/sense.py (integration site)
     TASK_HERETIC_v0.6.3_VERKMINNI.md §6
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from heretic.skilningr.config_model import ForgeConfig, SmidjaConfig
from heretic.skilningr.senses.smidja.client import BrunhandHttpClient
from heretic.skilningr.senses.smidja.forge_client import ForgeHttpClient
from heretic.skilningr.senses.smidja.errors import BrunhandUnreachableError
from heretic.skilningr.senses.smidja.sense import SmidjaSense
from heretic.skilningr.senses.smidja.verkminni import (
    AuditEntry,
    AuditLog,
    NullAuditLog,
    build_entry,
    _truncate,
)


# ---------------------------------------------------------------------------
# Helpers (mirror test_smidja_sense.py)
# ---------------------------------------------------------------------------

def make_config(enabled: bool = True, forge_enabled: bool = False) -> SmidjaConfig:
    return SmidjaConfig(
        enabled=enabled,
        host="127.0.0.1",
        port=8848,
        token_env="BRUNHAND_TOKEN_HERETIC",
        require_https=False,
        request_timeout_seconds=5,
        host_name="test-verkminni-host",
        forge=ForgeConfig(enabled=forge_enabled),
    )


def make_mock_brunhand_client() -> MagicMock:
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
    client = MagicMock(spec=ForgeHttpClient)
    client.open = AsyncMock()
    client.close = AsyncMock()
    client.health = AsyncMock()
    client.build_avatar = AsyncMock()
    client.get_avatar = AsyncMock()
    client.inspect_avatar = AsyncMock()
    client.list_assets = AsyncMock()
    return client


def make_sense_with_audit(
    audit_log=None,
    cfg: SmidjaConfig | None = None,
    brunhand_client: MagicMock | None = None,
    forge_client: MagicMock | None = None,
) -> SmidjaSense:
    if cfg is None:
        cfg = make_config()
    if brunhand_client is None:
        brunhand_client = make_mock_brunhand_client()
    if forge_client is None:
        forge_client = make_mock_forge_client()
    return SmidjaSense(
        cfg,
        brunhand_client,
        forge_client,
        audit_log=audit_log,
    )


def make_tool_call(tool_name: str, arguments: dict) -> dict:
    return {
        "id": f"call_{tool_name.replace('.', '_')}",
        "type": "function",
        "function": {
            "name": tool_name,
            "arguments": json.dumps(arguments),
        },
    }


# ---------------------------------------------------------------------------
# AuditEntry construction
# ---------------------------------------------------------------------------

class TestAuditEntry:

    def test_construction_with_all_fields(self):
        e = AuditEntry(
            timestamp="2026-05-09T18:42:13.184Z",
            call_id="call_test",
            tool_name="smidja.click",
            arguments_json='{"x": 100, "y": 200}',
            state="completed",
            duration_ms=42,
            error=None,
        )
        assert e.timestamp == "2026-05-09T18:42:13.184Z"
        assert e.call_id == "call_test"
        assert e.tool_name == "smidja.click"
        assert e.state == "completed"
        assert e.duration_ms == 42
        assert e.error is None

    def test_frozen_dataclass(self):
        """AuditEntry is frozen — fields cannot be mutated after construction."""
        e = AuditEntry(
            timestamp="x", call_id="x", tool_name="x",
            arguments_json="x", state="started",
            duration_ms=None, error=None,
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            e.timestamp = "y"  # type: ignore[misc]


class TestTruncation:

    def test_short_text_unchanged(self):
        assert _truncate("hello") == "hello"

    def test_exact_cap_unchanged(self):
        s = "x" * 500
        assert _truncate(s) == s

    def test_one_over_cap_gets_marker(self):
        s = "x" * 501
        result = _truncate(s)
        assert len(result) > 500
        assert "more chars" in result
        assert result.startswith("x" * 500)

    def test_long_text_truncated(self):
        s = "y" * 1500
        result = _truncate(s)
        assert result.startswith("y" * 500)
        assert "(1000 more chars)" in result

    def test_none_passes_through(self):
        # _truncate(None) returns None per the docstring contract
        assert _truncate(None) is None  # type: ignore[arg-type]

    def test_build_entry_truncates_args(self):
        long_args = "x" * 1000
        entry = build_entry(
            state="started",
            call_id="c",
            tool_name="t",
            arguments_json=long_args,
        )
        assert len(entry.arguments_json) < 1000  # truncated
        assert "more chars" in entry.arguments_json

    def test_build_entry_truncates_error(self):
        long_err = "fail " * 200  # 1000 chars
        entry = build_entry(
            state="failed",
            call_id="c",
            tool_name="t",
            arguments_json="{}",
            duration_ms=10,
            error=long_err,
        )
        assert len(entry.error) < 1000
        assert "more chars" in entry.error


# ---------------------------------------------------------------------------
# AuditLog ring buffer
# ---------------------------------------------------------------------------

class TestAuditLog:

    def test_default_depth_is_set(self):
        log = AuditLog(depth=50)
        assert log.depth == 50

    def test_zero_depth_raises(self):
        with pytest.raises(ValueError):
            AuditLog(depth=0)

    def test_negative_depth_raises(self):
        with pytest.raises(ValueError):
            AuditLog(depth=-1)

    def test_record_appends(self):
        log = AuditLog(depth=10)
        e = build_entry(state="started", call_id="c", tool_name="t",
                        arguments_json="{}")
        log.record(e)
        assert len(log) == 1

    def test_entries_returns_snapshot(self):
        log = AuditLog(depth=10)
        log.record(build_entry(state="started", call_id="c1",
                               tool_name="t1", arguments_json="{}"))
        snapshot1 = log.entries()
        log.record(build_entry(state="started", call_id="c2",
                               tool_name="t2", arguments_json="{}"))
        # snapshot1 must NOT see the second entry
        assert len(snapshot1) == 1
        # but the live log does
        assert len(log) == 2

    def test_entries_with_limit(self):
        log = AuditLog(depth=10)
        for i in range(5):
            log.record(build_entry(state="started", call_id=f"c{i}",
                                    tool_name="t", arguments_json="{}"))
        last_two = log.entries(limit=2)
        assert len(last_two) == 2
        assert last_two[-1].call_id == "c4"

    def test_ring_buffer_evicts_oldest(self):
        """V-3: at maxlen, the oldest entry is evicted."""
        log = AuditLog(depth=3)
        for i in range(5):
            log.record(build_entry(state="started", call_id=f"c{i}",
                                    tool_name="t", arguments_json="{}"))
        # Only 3 entries retained; oldest is c2
        assert len(log) == 3
        ids = [e.call_id for e in log.entries()]
        assert ids == ["c2", "c3", "c4"]

    def test_clear_empties_buffer(self):
        log = AuditLog(depth=10)
        for i in range(3):
            log.record(build_entry(state="started", call_id=f"c{i}",
                                    tool_name="t", arguments_json="{}"))
        log.clear()
        assert len(log) == 0
        assert log.entries() == []


class TestNullAuditLog:
    """V-5: NullAuditLog is a no-op opt-out replacement."""

    def test_record_is_noop(self):
        n = NullAuditLog()
        e = build_entry(state="started", call_id="c", tool_name="t",
                        arguments_json="{}")
        n.record(e)  # Must not raise
        assert len(n) == 0

    def test_entries_is_empty(self):
        n = NullAuditLog()
        assert n.entries() == []
        assert n.entries(limit=100) == []

    def test_clear_is_noop(self):
        n = NullAuditLog()
        n.clear()  # Must not raise

    def test_depth_is_zero(self):
        n = NullAuditLog()
        assert n.depth == 0


# ---------------------------------------------------------------------------
# SmidjaSense dispatch hook
# ---------------------------------------------------------------------------

class TestSmidjaSenseDispatchHook:
    """V-1: every tool call produces paired (started, completed/failed) entries."""

    @pytest.mark.asyncio
    async def test_success_records_started_and_completed(self):
        cfg = make_config(enabled=True)
        bc = make_mock_brunhand_client()
        bc.click = AsyncMock(return_value={"x": 100, "y": 200, "clicks_delivered": 1})

        log = AuditLog(depth=100)
        sense = make_sense_with_audit(audit_log=log, cfg=cfg, brunhand_client=bc)
        sense._brunhand_open = True

        tc = make_tool_call("smidja.click", {"x": 100, "y": 200})
        await sense.dispatch_tool_call(tc)

        entries = log.entries()
        assert len(entries) == 2
        assert entries[0].state == "started"
        assert entries[1].state == "completed"
        # Same call_id ties them together
        assert entries[0].call_id == entries[1].call_id == tc["id"]
        # tool_name matches
        assert entries[0].tool_name == "smidja.click"
        # duration_ms None on started, int on completed
        assert entries[0].duration_ms is None
        assert isinstance(entries[1].duration_ms, int)
        assert entries[1].duration_ms >= 0

    @pytest.mark.asyncio
    async def test_smidja_error_records_started_and_failed(self):
        cfg = make_config(enabled=True)
        bc = make_mock_brunhand_client()
        bc.click = AsyncMock(side_effect=BrunhandUnreachableError("daemon down"))

        log = AuditLog(depth=100)
        sense = make_sense_with_audit(audit_log=log, cfg=cfg, brunhand_client=bc)
        sense._brunhand_open = True

        tc = make_tool_call("smidja.click", {"x": 1, "y": 2})
        result = await sense.dispatch_tool_call(tc)

        # Result is still a normal tool_result (dispatcher never raised)
        assert "tool_call_id" in result
        # And the audit log captured both transitions
        entries = log.entries()
        assert len(entries) == 2
        assert entries[0].state == "started"
        assert entries[1].state == "failed"
        assert "daemon down" in entries[1].error

    @pytest.mark.asyncio
    async def test_unexpected_exception_records_started_and_failed(self):
        """An unexpected RuntimeError still produces a paired audit entry."""
        cfg = make_config(enabled=True)
        bc = make_mock_brunhand_client()
        bc.click = AsyncMock(side_effect=RuntimeError("boom"))

        log = AuditLog(depth=100)
        sense = make_sense_with_audit(audit_log=log, cfg=cfg, brunhand_client=bc)
        sense._brunhand_open = True

        tc = make_tool_call("smidja.click", {"x": 1, "y": 2})
        result = await sense.dispatch_tool_call(tc)

        # Dispatcher returned normally
        assert "tool_call_id" in result
        # Audit captured both transitions
        entries = log.entries()
        assert len(entries) == 2
        assert entries[1].state == "failed"
        assert "boom" in entries[1].error

    @pytest.mark.asyncio
    async def test_audit_write_failure_does_not_break_dispatch(self):
        """V-2: AuditLog.record() raises → dispatch_tool_call still returns normal result."""
        cfg = make_config(enabled=True)
        bc = make_mock_brunhand_client()
        bc.click = AsyncMock(return_value={"x": 1, "y": 2, "clicks_delivered": 1})

        # Build an AuditLog whose record() always raises
        broken_log = AuditLog(depth=10)
        broken_log.record = MagicMock(side_effect=RuntimeError("audit broken"))  # type: ignore[method-assign]

        sense = make_sense_with_audit(audit_log=broken_log, cfg=cfg, brunhand_client=bc)
        sense._brunhand_open = True

        tc = make_tool_call("smidja.click", {"x": 1, "y": 2})
        # Must not raise even though every audit write raises internally
        result = await sense.dispatch_tool_call(tc)
        assert result["tool_call_id"] == tc["id"]
        assert result["role"] == "tool"
        assert "content" in result

    @pytest.mark.asyncio
    async def test_close_clears_audit_log(self):
        """V-4: SmidjaSense.close() clears the audit log."""
        cfg = make_config(enabled=True)
        bc = make_mock_brunhand_client()
        bc.click = AsyncMock(return_value={"x": 1, "y": 2, "clicks_delivered": 1})

        log = AuditLog(depth=100)
        sense = make_sense_with_audit(audit_log=log, cfg=cfg, brunhand_client=bc)
        sense._brunhand_open = True

        tc = make_tool_call("smidja.click", {"x": 1, "y": 2})
        await sense.dispatch_tool_call(tc)
        assert len(log) == 2  # paired entries exist

        await sense.close()
        assert len(log) == 0  # cleared at SLOKNA

    @pytest.mark.asyncio
    async def test_null_audit_log_records_nothing(self):
        """V-5: when audit_log is NullAuditLog, no entries are recorded."""
        cfg = make_config(enabled=True)
        bc = make_mock_brunhand_client()
        bc.click = AsyncMock(return_value={"x": 1, "y": 2, "clicks_delivered": 1})

        null_log = NullAuditLog()
        sense = make_sense_with_audit(audit_log=null_log, cfg=cfg, brunhand_client=bc)
        sense._brunhand_open = True

        tc = make_tool_call("smidja.click", {"x": 1, "y": 2})
        result = await sense.dispatch_tool_call(tc)

        # Dispatch worked
        assert result["tool_call_id"] == tc["id"]
        # But null log still has zero entries
        assert len(null_log) == 0
        assert null_log.entries() == []

    @pytest.mark.asyncio
    async def test_default_audit_log_is_enabled(self):
        """When audit_log=None, default AuditLog is used (default ON)."""
        cfg = make_config(enabled=True)
        bc = make_mock_brunhand_client()
        bc.click = AsyncMock(return_value={"x": 1, "y": 2, "clicks_delivered": 1})

        # Don't pass audit_log — should construct a default AuditLog
        sense = make_sense_with_audit(audit_log=None, cfg=cfg, brunhand_client=bc)
        sense._brunhand_open = True

        tc = make_tool_call("smidja.click", {"x": 1, "y": 2})
        await sense.dispatch_tool_call(tc)

        # Default audit log captured the paired entries
        assert len(sense._audit_log) == 2
