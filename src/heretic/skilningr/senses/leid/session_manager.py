"""
BrowserSessionManager — owns the open Leið Innan Hurðar sessions.

The manager is the dictionary of open sessions, the concurrency cap enforcer,
and the lazy-eviction worker. It does NOT launch browsers itself — the
client (PlaywrightLeidClient) builds the (pw, browser, context, page) quartet
and registers it with the manager via ``register_session``.

SANDBOX INVARIANTS (B-13 .. B-18) — DO NOT WEAKEN:

    B-13  ``check_capacity`` raises LeidSessionLimitError when at cap. No
          silent eviction of existing sessions to make room.
    B-14  Each registered session owns its own (pw, browser, context, page)
          quartet. The manager holds references but never shares.
    B-15  ``evict_expired_sessions`` is called by the client at the start of
          every session-tool call. Eviction uses ``_close_session_internal``
          (same cleanup ordering as ``close_session``).
    B-16  ``get_session(session_id)`` returns the session OR raises
          LeidSessionExpiredError. Callers must use this, not raw dict access.
    B-17  Callers update ``session.last_activity_at`` after each successful
          tool call (the manager doesn't know which calls "count"; the client
          marks them).
    B-18  ``close_session(session_id)`` is idempotent: returns True if a
          session was actually closed, False if the id was unknown. The dict
          mutation happens BEFORE cleanup begins so a concurrent eviction
          sweep cannot double-clean.

Concurrency:
    asyncio.Lock around the dict mutations (D-35). Concurrent open_session
    calls are serialised at the cap-check boundary so the cap is honoured
    exactly. Concurrent calls on different session_ids do NOT serialise.

Time:
    All timestamps are ``time.monotonic()`` floats. We never persist these,
    we only compare them; monotonic is correct for "did N seconds pass?"
    questions and immune to wall-clock adjustments.

Ref: src/heretic/skilningr/senses/leid/INTERFACE.md §12
     docs/cartography/DATA_FLOW.md §4.12.2.4
     TASK_HERETIC_v0.8.2_INNAN_HURDAR.md
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from heretic.skilningr.config_model import LeidConfig
from heretic.skilningr.senses.leid.errors import (
    LeidSessionExpiredError,
    LeidSessionLimitError,
)

logger = logging.getLogger(__name__)


@dataclass
class _LeidSession:
    """Internal record for a single open browser session.

    Holds the four Playwright resources (pw, browser, context, page) plus
    the lifetime metadata used by the eviction logic.

    Use ``mark_activity()`` to update the last-activity timestamp after a
    successful session-affecting tool call (B-17).
    """

    session_id: str
    pw: Any  # playwright.async_api.Playwright runtime
    browser: Any  # playwright.async_api.Browser
    context: Any  # playwright.async_api.BrowserContext
    page: Any  # playwright.async_api.Page
    created_at: float = field(default_factory=time.monotonic)
    last_activity_at: float = field(default_factory=time.monotonic)

    def mark_activity(self) -> None:
        """Update ``last_activity_at`` to the current monotonic time. (B-17)"""
        self.last_activity_at = time.monotonic()

    def age_seconds(self, now: float | None = None) -> float:
        """Return seconds since this session was created."""
        return (now if now is not None else time.monotonic()) - self.created_at

    def idle_seconds(self, now: float | None = None) -> float:
        """Return seconds since the last activity on this session."""
        return (now if now is not None else time.monotonic()) - self.last_activity_at


class BrowserSessionManager:
    """The dictionary of open Leið Innan Hurðar sessions plus enforcement of
    the concurrency cap and lazy eviction of expired sessions.

    The manager does NOT spawn browsers; PlaywrightLeidClient does that and
    registers the resulting session with this manager. The manager:
        - tracks the open sessions (B-14: each owns its own quartet)
        - enforces the concurrency cap (B-13: explicit refusal at limit)
        - lazily evicts sessions past idle/absolute timeout (B-15)
        - performs cleanup on close + on eviction
        - serialises mutations with an asyncio.Lock (D-35)

    Usage:
        manager = BrowserSessionManager(config)
        await manager.evict_expired_sessions()                  # before any op
        await manager.check_capacity()                          # before launch
        # ... PlaywrightLeidClient launches the browser ...
        session_id = "leid-" + uuid.uuid4().hex
        session = _LeidSession(session_id, pw, browser, context, page)
        await manager.register_session(session)
        # ... later ...
        session = await manager.get_session(session_id)         # raises if gone
        # ... do work, then mark activity ...
        session.mark_activity()
        # ... eventually ...
        was_closed = await manager.close_session(session_id)    # idempotent
    """

    def __init__(
        self,
        config: LeidConfig,
        log: logging.Logger | None = None,
    ) -> None:
        """Construct an empty session manager.

        Args:
            config: LeidConfig — provides max_concurrent_sessions, idle and
                    absolute timeouts.
            log:    Optional logger. Defaults to module logger.
        """
        self._config = config
        self._log = log if log is not None else logging.getLogger(__name__)
        self._sessions: dict[str, _LeidSession] = {}
        self._lock = asyncio.Lock()

    @property
    def active_count(self) -> int:
        """Return the number of currently-registered sessions.

        Read without locking — for observability only. Authoritative checks
        (e.g. cap enforcement) take the lock.
        """
        return len(self._sessions)

    async def check_capacity(self) -> None:
        """Raise LeidSessionLimitError if the cap is already reached. (B-13)

        Called by PlaywrightLeidClient.open_session BEFORE launching the
        browser. No silent eviction — explicit refusal so the agent's mental
        model of which sessions are alive remains correct.

        Raises:
            LeidSessionLimitError: if active_count >= cap.
        """
        # No lock — read is fine; the cap is checked again under-lock at
        # registration time, which is the authoritative gate.
        if len(self._sessions) >= self._config.browser_max_concurrent_sessions:
            raise LeidSessionLimitError(
                f"Cannot open new browser session: "
                f"{len(self._sessions)} of "
                f"{self._config.browser_max_concurrent_sessions} session slots "
                f"are in use. Close an existing session with leid.close_session "
                f"before opening a new one, or raise "
                f"LeidConfig.browser_max_concurrent_sessions if your hardware "
                f"can support more."
            )

    async def register_session(self, session: _LeidSession) -> None:
        """Register a freshly-launched session under its session_id.

        Re-checks the cap under the lock for safety against concurrent
        open_session calls (D-35). If the cap was reached between
        ``check_capacity`` and here, the registration is refused and the
        caller must clean up the just-launched browser.

        Args:
            session: The fully-launched _LeidSession to register.

        Raises:
            LeidSessionLimitError: if a concurrent registration filled the
                last slot between check_capacity and register_session.
        """
        async with self._lock:
            # Re-check under lock — cap enforcement has to be exact even
            # under concurrent open_session calls (D-35).
            if len(self._sessions) >= self._config.browser_max_concurrent_sessions:
                raise LeidSessionLimitError(
                    f"Lost the race to register session {session.session_id!r}: "
                    f"a concurrent open_session call filled the last slot. "
                    f"Try again or close an existing session first."
                )
            if session.session_id in self._sessions:
                # Should never happen with UUID4-based ids, but defensive.
                raise LeidSessionLimitError(
                    f"session_id collision: {session.session_id!r} is already "
                    f"registered. This indicates a UUID generation defect."
                )
            self._sessions[session.session_id] = session
            self._log.info(
                "Leið session opened: %s (active=%d / max=%d)",
                session.session_id,
                len(self._sessions),
                self._config.browser_max_concurrent_sessions,
            )

    async def get_session(self, session_id: str) -> _LeidSession:
        """Return the session for *session_id* or raise LeidSessionExpiredError. (B-16)

        Use this from any tool that REQUIRES the session to exist
        (status, click, future type/navigate). For ``close_session``, use
        ``close_session()`` directly which is idempotent for unknown ids.

        Args:
            session_id: The session_id from a prior open_session response.

        Returns:
            The _LeidSession.

        Raises:
            LeidSessionExpiredError: if the id is unknown or has been evicted.
        """
        # Read under no lock — if a concurrent close races us we'll see one
        # snapshot or the other; either way the agent gets a coherent answer.
        session = self._sessions.get(session_id)
        if session is None:
            raise LeidSessionExpiredError(
                f"Session {session_id!r} is not active. It may have been "
                f"closed, evicted by idle timeout "
                f"({self._config.browser_session_idle_timeout_seconds}s), "
                f"evicted by absolute lifetime "
                f"({self._config.browser_session_max_lifetime_seconds}s), or "
                f"never existed. Call leid.open_session to start a new one."
            )
        return session

    async def close_session(self, session_id: str) -> bool:
        """Close the session and release its resources. Idempotent. (B-18)

        Removes the session from the dict BEFORE cleanup begins so a
        concurrent eviction sweep cannot double-clean (B-18).

        Args:
            session_id: The session_id to close.

        Returns:
            True if a session was actually closed; False if the id was
            unknown (idempotent path).
        """
        # Pop-then-clean. The dict mutation happens under lock; the cleanup
        # itself happens outside the lock so other manager operations are
        # not blocked by browser-teardown latency.
        async with self._lock:
            session = self._sessions.pop(session_id, None)

        if session is None:
            self._log.debug(
                "Leið close_session: unknown id %s — idempotent no-op",
                session_id,
            )
            return False

        await self._cleanup_session_resources(session, reason="close_session")
        self._log.info(
            "Leið session closed: %s (active=%d / max=%d)",
            session_id,
            len(self._sessions),
            self._config.browser_max_concurrent_sessions,
        )
        return True

    async def evict_expired_sessions(self) -> list[str]:
        """Evict sessions past idle or absolute timeout. (B-15)

        Called by PlaywrightLeidClient at the start of every session-tool
        call. Lazy — no background task. Correctness is operator-perceivable
        (sessions visibly closed when the next call happens).

        Returns:
            List of evicted session_ids (for caller-side logging if useful).
        """
        now = time.monotonic()
        idle_cap = self._config.browser_session_idle_timeout_seconds
        age_cap = self._config.browser_session_max_lifetime_seconds

        # Snapshot the candidate sessions under lock; do the actual removal
        # under lock per-session below.
        async with self._lock:
            expired_ids = [
                sid for sid, s in self._sessions.items()
                if s.idle_seconds(now) > idle_cap
                or s.age_seconds(now) > age_cap
            ]

        evicted: list[str] = []
        for session_id in expired_ids:
            async with self._lock:
                session = self._sessions.pop(session_id, None)
            if session is None:
                # Lost a race with close_session — fine.
                continue
            reason = (
                "idle_timeout"
                if session.idle_seconds(now) > idle_cap
                else "max_lifetime"
            )
            self._log.warning(
                "Leið session evicted by %s: %s "
                "(age=%.1fs, idle=%.1fs, idle_cap=%ds, age_cap=%ds)",
                reason,
                session_id,
                session.age_seconds(now),
                session.idle_seconds(now),
                idle_cap,
                age_cap,
            )
            await self._cleanup_session_resources(session, reason=reason)
            evicted.append(session_id)

        return evicted

    async def _cleanup_session_resources(
        self,
        session: _LeidSession,
        *,
        reason: str,
    ) -> None:
        """Tear down a session's (context, browser, pw) quartet.

        Three-stage cleanup mirroring render_url's `finally` shape — each
        close defensively wrapped so a failure in one does not block the
        others (B-7-style discipline at session close time).

        Args:
            session: the _LeidSession whose resources to release.
            reason:  string label for log lines (e.g. "close_session",
                     "idle_timeout", "max_lifetime").
        """
        if session.context is not None:
            try:
                await session.context.close()
            except Exception as exc:
                self._log.warning(
                    "Leið session %s (%s): context.close() raised "
                    "(non-fatal): %s",
                    session.session_id, reason, exc,
                )
        if session.browser is not None:
            try:
                await session.browser.close()
            except Exception as exc:
                self._log.warning(
                    "Leið session %s (%s): browser.close() raised "
                    "(non-fatal): %s",
                    session.session_id, reason, exc,
                )
        if session.pw is not None:
            try:
                await session.pw.stop()
            except Exception as exc:
                self._log.warning(
                    "Leið session %s (%s): playwright.stop() raised "
                    "(non-fatal): %s",
                    session.session_id, reason, exc,
                )
