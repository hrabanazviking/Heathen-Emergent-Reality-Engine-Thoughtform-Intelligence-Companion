"""
Smiðja Verkminni — deed-memory audit log (v0.6.3).

This module owns the per-tool-call audit log for L5.5 Smiðja. Every Smiðja
tool call dispatched via SmidjaSense.dispatch_tool_call records two paired
entries (started + completed/failed) into a bounded in-memory ring buffer.
The operator can review the log to verify what the agent's hand actually
did, parallel to the agent's narrated transcript.

Public surface:
    - `AuditEntry` dataclass — one record per state transition.
    - `AuditLog` class — bounded ring buffer with thread-safe mutation.
    - `NullAuditLog` class — no-op replacement when verkminni.enabled=False.

Privacy / integrity invariants (cross-checked by Auditor):
    V-1: Every dispatched tool call produces exactly two paired entries
         (started + completed/failed) with the same call_id when the audit
         log is enabled.
    V-2: Audit-write failures cannot make SmidjaSense.dispatch_tool_call
         raise. The audit log is a witness, not a gate. Wrap calls to
         AuditLog.record() in try/except at the call site.
    V-3: Ring buffer evicts oldest entries at maxlen=depth. No unbounded
         memory growth.
    V-4: SmidjaSense.close() (SLOKNA) calls AuditLog.clear(). Ceremony-
         scoped — deed-memory does not persist across ceremonies.
    V-5: When verkminni.enabled=False, NullAuditLog replaces AuditLog;
         record() is a no-op; the dispatch path is unchanged.

    Smiðja-1 INHERITED: dispatch_tool_call NEVER raises (preserved by V-2).
    Smiðja-2 INHERITED: bearer token never recorded — args dict never
         contains the token (token is in env var, fetched by client at
         request time).
    Smiðja-3 INHERITED: tool_result return shape unchanged.

Truncation policy:
    arguments_json and error are each capped at 500 characters with a
    trailing `... (N more chars)` marker. This bounds per-entry memory.

Ref: src/heretic/skilningr/senses/smidja/sense.py (integration site)
     docs/cartography/DATA_FLOW.md §4.11.10
     docs/vision/VERKMINNI.md
     TASK_HERETIC_v0.6.3_VERKMINNI.md
"""

from __future__ import annotations

import logging
import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


_LOG = logging.getLogger(__name__)


# Per-field truncation cap (characters) — bounds per-entry memory.
_TRUNCATION_CAP: int = 500


def _truncate(text: str, cap: int = _TRUNCATION_CAP) -> str:
    """Return text truncated to cap chars with a `... (N more chars)` marker.

    If text is None or already within cap, returns it unchanged. Otherwise
    returns the first `cap` characters followed by an explicit marker
    indicating how many characters were dropped.
    """
    if text is None:
        return text  # type: ignore[return-value]
    if len(text) <= cap:
        return text
    dropped = len(text) - cap
    return f"{text[:cap]}... ({dropped} more chars)"


def _utcnow_iso8601() -> str:
    """Return current UTC time as ISO8601 string with millisecond precision.

    Format: "2026-05-09T18:42:13.184Z" — operator-readable, sortable,
    timezone-explicit.
    """
    now = datetime.now(timezone.utc)
    # Trim microseconds to milliseconds (3 digits), preserve Z suffix.
    iso = now.isoformat(timespec="milliseconds")
    # isoformat for tz-aware with timespec=milliseconds produces "+00:00";
    # replace with "Z" for compactness.
    if iso.endswith("+00:00"):
        iso = iso[:-6] + "Z"
    return iso


# ---------------------------------------------------------------------------
# AuditEntry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuditEntry:
    """One record of a Smiðja tool call state transition.

    Each tool call dispatched through SmidjaSense produces exactly two
    AuditEntry instances sharing the same call_id:
      - One with state="started" (entry into dispatch)
      - One with state="completed" or state="failed" (exit from dispatch)

    Frozen so existing entries cannot be mutated after recording — the
    record is a witness, not a working scratch buffer.

    Fields:
        timestamp:      UTC ISO8601 string with millisecond precision.
                        Operator-readable, sortable, timezone-explicit.
        call_id:        OpenAI tool_call id from the dispatched tool_call.
                        Links the started entry with its completed/failed pair.
        tool_name:      Full tool name (e.g., "smidja.click", "smidja.forge_build_avatar").
        arguments_json: JSON-serialised tool call arguments, truncated to
                        500 chars with "... (N more chars)" marker if longer.
                        For "started" and "completed"/"failed" entries of
                        the same call, arguments_json is identical.
        state:          "started" | "completed" | "failed".
        duration_ms:    None for "started" entries; non-negative integer
                        milliseconds for "completed"/"failed" entries
                        (elapsed since the matching started recording).
        error:          None for "started" and "completed"; truncated
                        error message for "failed".
    """

    timestamp: str
    call_id: str
    tool_name: str
    arguments_json: str
    state: str  # "started" | "completed" | "failed"
    duration_ms: Optional[int]
    error: Optional[str]


# ---------------------------------------------------------------------------
# AuditLog
# ---------------------------------------------------------------------------


class AuditLog:
    """Bounded in-memory ring buffer of AuditEntry records.

    Backed by `collections.deque(maxlen=depth)` for O(1) append + automatic
    eviction of oldest entries at depth. Thread-safe mutation via
    `threading.Lock`.

    Public surface:
        record(entry)      — append; evicts oldest at depth (V-3)
        entries(limit=N)   — snapshot list of last N entries (or all if None)
        clear()            — empty the buffer (called at SLOKNA, V-4)
        __len__()          — current entry count

    Default depth is set by the caller (typically 100, from VerkminniConfig).
    """

    def __init__(self, depth: int = 100) -> None:
        """Initialise the audit log with the given ring buffer depth.

        Args:
            depth: Maximum entries retained. Must be >= 1. Default 100.

        Raises:
            ValueError: if depth < 1.
        """
        if not isinstance(depth, int) or depth < 1:
            raise ValueError(
                f"AuditLog.depth must be a positive integer, got {depth!r}"
            )
        self._depth = depth
        self._buffer: deque[AuditEntry] = deque(maxlen=depth)
        self._lock = threading.Lock()

    @property
    def depth(self) -> int:
        """Maximum entries the ring buffer retains."""
        return self._depth

    def record(self, entry: AuditEntry) -> None:
        """Append an entry to the ring buffer.

        At maxlen, the oldest entry is evicted automatically (deque semantics).
        Thread-safe.

        Args:
            entry: AuditEntry to record. Must be a valid AuditEntry instance.
        """
        with self._lock:
            self._buffer.append(entry)

    def entries(self, limit: Optional[int] = None) -> list[AuditEntry]:
        """Return a snapshot list of recent entries, oldest-to-newest.

        The returned list is a fresh copy — mutating it does not affect
        the underlying buffer.

        Args:
            limit: If provided, return only the last `limit` entries.
                   If None (default), return all entries currently buffered.

        Returns:
            list[AuditEntry] — empty list if buffer is empty.
        """
        with self._lock:
            if limit is None or limit >= len(self._buffer):
                return list(self._buffer)
            # Last `limit` entries — most recent.
            return list(self._buffer)[-limit:]

    def clear(self) -> None:
        """Empty the ring buffer.

        Called at SmidjaSense.close() (SLOKNA) to enforce ceremony-scoped
        privacy: the body's deed-memory does not persist across ceremonies.
        """
        with self._lock:
            self._buffer.clear()

    def __len__(self) -> int:
        """Number of entries currently in the buffer."""
        with self._lock:
            return len(self._buffer)

    def __repr__(self) -> str:
        return f"AuditLog(depth={self._depth}, entries={len(self)})"


# ---------------------------------------------------------------------------
# NullAuditLog — opt-out replacement
# ---------------------------------------------------------------------------


class NullAuditLog:
    """No-op audit log used when verkminni.enabled=False.

    Has the same public surface as AuditLog but every method is a no-op
    or returns an empty result. SmidjaSense uses this when the operator
    has explicitly disabled Verkminni; the dispatch path is unchanged
    (it still calls audit.record(...)) but no entries are stored.

    This pattern preserves the Open/Closed Principle: adding/removing
    Verkminni doesn't require dispatch-site branching on enabled/disabled.
    """

    @property
    def depth(self) -> int:
        return 0

    def record(self, entry: AuditEntry) -> None:
        """No-op."""
        pass

    def entries(self, limit: Optional[int] = None) -> list[AuditEntry]:
        """Always returns an empty list."""
        return []

    def clear(self) -> None:
        """No-op."""
        pass

    def __len__(self) -> int:
        return 0

    def __repr__(self) -> str:
        return "NullAuditLog()"


# ---------------------------------------------------------------------------
# Helper: build_entry
# ---------------------------------------------------------------------------


def build_entry(
    *,
    state: str,
    call_id: str,
    tool_name: str,
    arguments_json: str,
    duration_ms: Optional[int] = None,
    error: Optional[str] = None,
) -> AuditEntry:
    """Construct an AuditEntry with current UTC timestamp + truncation.

    Convenience helper for SmidjaSense's `_safe_audit` to avoid repeating
    the truncation policy + timestamp generation at each call site.

    Args:
        state:          "started" | "completed" | "failed".
        call_id:        OpenAI tool_call id.
        tool_name:      Full tool name.
        arguments_json: Already JSON-serialised args; will be truncated.
        duration_ms:    None for started; int for completed/failed.
        error:          None for started/completed; truncated for failed.

    Returns:
        AuditEntry with timestamp set to current UTC ISO8601 (ms precision)
        and arguments_json + error fields truncated per the 500-char policy.
    """
    return AuditEntry(
        timestamp=_utcnow_iso8601(),
        call_id=call_id,
        tool_name=tool_name,
        arguments_json=_truncate(arguments_json),
        state=state,
        duration_ms=duration_ms,
        error=_truncate(error) if error is not None else None,
    )
