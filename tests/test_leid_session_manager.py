"""
Tests for BrowserSessionManager — Leið Innan Hurðar session manager (v0.8.2).

Covers:
    - Empty manager construction
    - Session registration + count
    - check_capacity at and under cap (B-13)
    - register_session under-lock cap re-check (race protection)
    - get_session valid + unknown (B-16)
    - close_session active + unknown (B-18 idempotent)
    - evict_expired_sessions: idle eviction (B-15)
    - evict_expired_sessions: absolute lifetime eviction
    - evict_expired_sessions: fresh sessions stay
    - evict_expired_sessions: mixed expired + fresh
    - cleanup ordering: context → browser → pw
    - cleanup defensive wrapping: failure in one close does not block others

All Playwright resources are mocked — no real Chromium spawned.

Ref: src/heretic/skilningr/senses/leid/session_manager.py
     src/heretic/skilningr/senses/leid/INTERFACE.md §12
     TASK_HERETIC_v0.8.2_INNAN_HURDAR.md §7.1
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from heretic.skilningr.config_model import LeidConfig
from heretic.skilningr.senses.leid.errors import (
    LeidSessionExpiredError,
    LeidSessionLimitError,
)
from heretic.skilningr.senses.leid.session_manager import (
    BrowserSessionManager,
    _LeidSession,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_config(
    max_concurrent: int = 3,
    idle_timeout: int = 300,
    max_lifetime: int = 1800,
) -> LeidConfig:
    return LeidConfig(
        url_allowlist_patterns=["https://example.com/*"],
        browser_max_concurrent_sessions=max_concurrent,
        browser_session_idle_timeout_seconds=idle_timeout,
        browser_session_max_lifetime_seconds=max_lifetime,
    )


def make_session(
    session_id: str = "leid-test-001",
    *,
    age_offset: float = 0.0,
    idle_offset: float = 0.0,
    pw_close: AsyncMock | None = None,
    browser_close: AsyncMock | None = None,
    context_close: AsyncMock | None = None,
) -> _LeidSession:
    """Construct a _LeidSession with mock Playwright resources.

    age_offset:  seconds to subtract from created_at (older session)
    idle_offset: seconds to subtract from last_activity_at (more idle)
    """
    pw = MagicMock()
    pw.stop = pw_close if pw_close is not None else AsyncMock(return_value=None)
    browser = MagicMock()
    browser.close = (
        browser_close if browser_close is not None else AsyncMock(return_value=None)
    )
    context = MagicMock()
    context.close = (
        context_close if context_close is not None else AsyncMock(return_value=None)
    )
    page = MagicMock()
    now = time.monotonic()
    return _LeidSession(
        session_id=session_id,
        pw=pw,
        browser=browser,
        context=context,
        page=page,
        created_at=now - age_offset,
        last_activity_at=now - idle_offset,
    )


# ---------------------------------------------------------------------------
# Construction + basic state
# ---------------------------------------------------------------------------


class TestBrowserSessionManagerConstruction:

    def test_manager_starts_empty(self):
        manager = BrowserSessionManager(make_config())
        assert manager.active_count == 0

    @pytest.mark.asyncio
    async def test_manager_register_increments_count(self):
        manager = BrowserSessionManager(make_config())
        await manager.register_session(make_session("leid-aaa"))
        assert manager.active_count == 1


# ---------------------------------------------------------------------------
# Capacity enforcement (B-13)
# ---------------------------------------------------------------------------


class TestBrowserSessionManagerCapacity:

    @pytest.mark.asyncio
    async def test_check_capacity_under_cap_returns_silently(self):
        manager = BrowserSessionManager(make_config(max_concurrent=3))
        await manager.register_session(make_session("leid-1"))
        # Under cap (1 of 3) — should not raise
        await manager.check_capacity()

    @pytest.mark.asyncio
    async def test_check_capacity_at_cap_raises(self):
        manager = BrowserSessionManager(make_config(max_concurrent=2))
        await manager.register_session(make_session("leid-1"))
        await manager.register_session(make_session("leid-2"))
        with pytest.raises(LeidSessionLimitError, match="2 of 2"):
            await manager.check_capacity()

    @pytest.mark.asyncio
    async def test_register_session_at_cap_raises_under_lock(self):
        """B-13 race protection — re-checks cap inside the lock."""
        manager = BrowserSessionManager(make_config(max_concurrent=1))
        await manager.register_session(make_session("leid-1"))
        with pytest.raises(LeidSessionLimitError, match="Lost the race"):
            await manager.register_session(make_session("leid-2"))


# ---------------------------------------------------------------------------
# get_session (B-16)
# ---------------------------------------------------------------------------


class TestBrowserSessionManagerGet:

    @pytest.mark.asyncio
    async def test_get_session_returns_registered(self):
        manager = BrowserSessionManager(make_config())
        session = make_session("leid-known")
        await manager.register_session(session)
        retrieved = await manager.get_session("leid-known")
        assert retrieved is session

    @pytest.mark.asyncio
    async def test_get_session_unknown_raises_expired(self):
        manager = BrowserSessionManager(make_config())
        with pytest.raises(LeidSessionExpiredError, match="not active"):
            await manager.get_session("leid-never-existed")


# ---------------------------------------------------------------------------
# close_session (B-18)
# ---------------------------------------------------------------------------


class TestBrowserSessionManagerClose:

    @pytest.mark.asyncio
    async def test_close_active_session_returns_true(self):
        manager = BrowserSessionManager(make_config())
        session = make_session("leid-active")
        await manager.register_session(session)
        result = await manager.close_session("leid-active")
        assert result is True
        assert manager.active_count == 0

    @pytest.mark.asyncio
    async def test_close_unknown_session_returns_false_idempotent(self):
        """B-18: closing unknown id is idempotent — does NOT raise."""
        manager = BrowserSessionManager(make_config())
        result = await manager.close_session("leid-never-existed")
        assert result is False

    @pytest.mark.asyncio
    async def test_close_runs_cleanup_in_order(self):
        """Cleanup order: context.close → browser.close → pw.stop."""
        call_order: list[str] = []

        async def _ctx_close():
            call_order.append("context")

        async def _browser_close():
            call_order.append("browser")

        async def _pw_stop():
            call_order.append("pw")

        manager = BrowserSessionManager(make_config())
        session = make_session(
            "leid-order",
            context_close=AsyncMock(side_effect=_ctx_close),
            browser_close=AsyncMock(side_effect=_browser_close),
            pw_close=AsyncMock(side_effect=_pw_stop),
        )
        await manager.register_session(session)
        await manager.close_session("leid-order")

        assert call_order == ["context", "browser", "pw"]

    @pytest.mark.asyncio
    async def test_close_continues_when_one_cleanup_raises(self):
        """A failure in one close does not block the other two."""
        manager = BrowserSessionManager(make_config())
        browser_close_mock = AsyncMock(return_value=None)
        pw_stop_mock = AsyncMock(return_value=None)
        session = make_session(
            "leid-broken",
            context_close=AsyncMock(side_effect=RuntimeError("context boom")),
            browser_close=browser_close_mock,
            pw_close=pw_stop_mock,
        )
        await manager.register_session(session)
        # Should NOT raise
        result = await manager.close_session("leid-broken")
        assert result is True
        # Both subsequent closes still ran
        browser_close_mock.assert_awaited_once()
        pw_stop_mock.assert_awaited_once()


# ---------------------------------------------------------------------------
# evict_expired_sessions (B-15)
# ---------------------------------------------------------------------------


class TestBrowserSessionManagerEviction:

    @pytest.mark.asyncio
    async def test_eviction_removes_idle_session(self):
        """Session idle > idle_timeout is evicted."""
        manager = BrowserSessionManager(make_config(idle_timeout=10))
        # Idle 20s ago — should be evicted
        await manager.register_session(
            make_session("leid-idle", idle_offset=20.0)
        )
        evicted = await manager.evict_expired_sessions()
        assert "leid-idle" in evicted
        assert manager.active_count == 0

    @pytest.mark.asyncio
    async def test_eviction_removes_session_past_max_lifetime(self):
        """Session age > max_lifetime is evicted even if active.

        Config validation requires max_lifetime >= idle_timeout, so we use
        idle_timeout=10, max_lifetime=60 and a session aged 120s with idle
        only 1s — past max_lifetime but not past idle.
        """
        manager = BrowserSessionManager(
            make_config(idle_timeout=10, max_lifetime=60)
        )
        # Created 120s ago, active 1s ago — past max_lifetime, NOT past idle
        await manager.register_session(
            make_session("leid-old", age_offset=120.0, idle_offset=1.0)
        )
        evicted = await manager.evict_expired_sessions()
        assert "leid-old" in evicted

    @pytest.mark.asyncio
    async def test_eviction_keeps_fresh_session(self):
        """Fresh session within both limits stays."""
        manager = BrowserSessionManager(make_config(idle_timeout=300))
        await manager.register_session(
            make_session("leid-fresh", idle_offset=1.0, age_offset=5.0)
        )
        evicted = await manager.evict_expired_sessions()
        assert evicted == []
        assert manager.active_count == 1

    @pytest.mark.asyncio
    async def test_eviction_mixed_only_removes_expired(self):
        """One expired, one fresh: only expired removed."""
        manager = BrowserSessionManager(make_config(idle_timeout=10))
        await manager.register_session(
            make_session("leid-fresh", idle_offset=1.0)
        )
        await manager.register_session(
            make_session("leid-expired", idle_offset=20.0)
        )
        evicted = await manager.evict_expired_sessions()
        assert evicted == ["leid-expired"]
        assert manager.active_count == 1

    @pytest.mark.asyncio
    async def test_eviction_runs_cleanup_callbacks(self):
        """Eviction calls context.close → browser.close → pw.stop."""
        ctx_mock = AsyncMock(return_value=None)
        browser_mock = AsyncMock(return_value=None)
        pw_mock = AsyncMock(return_value=None)
        manager = BrowserSessionManager(make_config(idle_timeout=10))
        await manager.register_session(
            make_session(
                "leid-cleanup",
                idle_offset=20.0,
                context_close=ctx_mock,
                browser_close=browser_mock,
                pw_close=pw_mock,
            )
        )
        await manager.evict_expired_sessions()
        ctx_mock.assert_awaited_once()
        browser_mock.assert_awaited_once()
        pw_mock.assert_awaited_once()


# ---------------------------------------------------------------------------
# _LeidSession dataclass behaviour
# ---------------------------------------------------------------------------


class TestLeidSessionRecord:

    def test_mark_activity_updates_last_activity(self):
        session = make_session("leid-mark", idle_offset=10.0)
        before = session.last_activity_at
        time.sleep(0.05)  # ensure monotonic clock advances (Windows ~16ms granularity)
        session.mark_activity()
        assert session.last_activity_at > before

    def test_age_seconds_returns_positive(self):
        session = make_session("leid-age", age_offset=5.0)
        assert session.age_seconds() >= 5.0

    def test_idle_seconds_returns_positive(self):
        session = make_session("leid-idle-q", idle_offset=2.0)
        assert session.idle_seconds() >= 2.0
