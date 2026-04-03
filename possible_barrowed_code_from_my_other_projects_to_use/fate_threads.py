"""
Fate Threads — Symbolic Recurrence (5-10 turns)

Persistent symbolic themes that keep echoing through the narrative,
creating a sense of wyrd weaving through the story. New threads
are added every 5 turns, and up to 5 active threads shape events.

Part of the Norse Saga Engine Myth Engine (v4.2.0)
"""
import random
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_THREADS = [
    "the cost of loyalty",
    "hidden fire beneath calm waters",
    "echoes of old promises",
    "forgotten kinship",
    "the weight of honor",
    "blood memory stirring",
    "broken oaths seeking mending",
    "the wanderer's return",
    "shadows cast by ancient light",
    "roots reaching through stone",
    "the price of forbidden knowledge",
    "bonds tested by distance",
    "an old debt unpaid",
    "the silence before a storm",
    "whispers carried by northern winds",
    "a name spoken in dreams",
    "the pull of ancestral ground",
    "flame and ice in balance",
    "the mask a warrior wears",
    "gifts that bind the giver",
]


class FateThreads:
    """Symbolic recurrence layer — persistent themes that echo through turns."""

    def __init__(self):
        self.threads = []
        self.thread_records: List[FateThreadRecord] = []
        self.thread_options = DEFAULT_THREADS[:]
        self.weave_interval = 5
        self.max_active = 5
        self.max_records = 40

    def update(self, turn_count: int) -> None:
        """Weave a new thread every N turns."""
        try:
            if turn_count <= 0 or turn_count % self.weave_interval != 0:
                return
            if not self.thread_options:
                logger.debug("FateThreads.update(): thread_options exhausted; skipping weave.")
                return
            new_thread = random.choice(self.thread_options)
            # Avoid exact duplicates in active threads
            if new_thread not in self.threads:
                self.threads.append(new_thread)
            else:
                # Pick a different one
                available = [t for t in self.thread_options if t not in self.threads]
                if available:
                    self.threads.append(random.choice(available))
                else:
                    logger.debug("FateThreads.update(): all thread_options active; skipping weave.")
                    return
            self.threads = self.threads[-self.max_active:]
            logger.info("Fate thread woven: %s", self.threads[-1])
        except Exception:
            logger.warning(
                "FateThreads.update() failed (turn_count=%r); threads unchanged.",
                turn_count,
                exc_info=True,
            )

    def add_custom_thread(self, thread_text: str, turn_count: int = 0) -> None:
        """Add a player-driven or narrative-driven custom thread.

        Args:
            thread_text: The theme string to add.
            turn_count: The current game turn. Passing the actual turn ensures
                        the pressure record decays correctly (was always 0,
                        causing instant decay for high-turn games).
        """
        try:
            if not isinstance(thread_text, str) or not thread_text.strip():
                logger.warning(
                    "FateThreads.add_custom_thread() received invalid value %r; ignored.",
                    thread_text,
                )
                return
            self.threads.append(thread_text)
            self.threads = self.threads[-self.max_active:]
            self._upsert_record(
                theme=thread_text,
                turn_count=int(turn_count or 0),
                source="custom",
                pressure_delta=4,  # slightly higher than auto-detected — player choice matters
            )
        except Exception:
            logger.warning(
                "FateThreads.add_custom_thread() failed for value %r; threads unchanged.",
                thread_text,
                exc_info=True,
            )

    def build_context(self):
        """Build the fate threads context block for prompt injection."""
        try:
            if not self.threads:
                return ""
            lines = "\n".join([f"  - {t}" for t in self.threads])
            return (
                "=== FATE THREADS (WYRD'S WEAVE) ===\n"
                f"Active symbolic themes echoing through the story:\n{lines}\n"
                "These themes may reappear naturally in narration, dialogue, or atmosphere."
            )
        except Exception:
            logger.error(
                "FateThreads.build_context() failed; returning empty string.",
                exc_info=True,
            )
            return ""

    def observe_turn(
        self,
        turn_count: int,
        player_action: str,
        narrative_result: str,
        location: str,
        npcs_present: List[str],
        chaos_factor: int,
        wyrd_summary: str = "",
        event_signals: Optional[List[str]] = None,
        thread_hints: Optional[List[str]] = None,
        chaos_story_pressure: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Track turn-level fate pressure so recurring themes stay active in prompts."""
        try:
            self.update(turn_count)

            scan_text = " ".join(
                [
                    str(player_action or ""),
                    str(narrative_result or ""),
                    str(wyrd_summary or ""),
                ]
            ).lower()
            # Skuld listens not only to narration, but also to explicit event omens.
            for signal in (event_signals or []):
                scan_text += f" {str(signal or '').lower()}"

            score_by_theme: Dict[str, int] = {}
            for theme in self.thread_options:
                score = self._theme_match_score(theme, scan_text)
                if score > 0:
                    score_by_theme[theme] = score

            for hinted in (thread_hints or []):
                hint = str(hinted or "").strip().lower()
                if not hint:
                    continue
                score_by_theme[hint] = max(3, score_by_theme.get(hint, 0) + 2)

            chaos_temp = max(1, min(100, int(chaos_factor or 30)))
            chaos_bonus = max(1, int(chaos_temp / 20))
            pressure_bonus = int((chaos_story_pressure or {}).get("fate_pressure_bonus", 0) or 0)
            hottest = sorted(
                score_by_theme.items(), key=lambda item: item[1], reverse=True
             )[:8]
            for theme, score in hottest:
                self._upsert_record(
                    theme=theme,
                    turn_count=turn_count,
                    source="turn_scan",
                    pressure_delta=min(12, score + chaos_bonus + pressure_bonus),
                    location=location,
                    npcs_present=npcs_present,
                )

            for chaos_theme in self._chaos_seed_themes(chaos_story_pressure):
                self._upsert_record(
                    theme=chaos_theme,
                    turn_count=turn_count,
                    source="chaos_heat",
                    pressure_delta=2 + max(0, pressure_bonus),
                    location=location,
                    npcs_present=npcs_present,
                )

            # Huginn marks old threads that have gone cold.
            for record in self.thread_records:
                if turn_count - record.last_turn_seen >= 4:
                    record.pressure = max(0, record.pressure - 1)

            self.thread_records.sort(
                key=lambda rec: (rec.pressure, rec.last_turn_seen), reverse=True
            )
            self.thread_records = self.thread_records[: self.max_records]
            self.threads = [rec.theme for rec in self.thread_records[: self.max_active]]

            return {
                "active_themes": list(self.threads),
                "pressure_map": {
                    rec.theme: rec.pressure for rec in self.thread_records[:10]
                },
                "turn": int(turn_count or 0),
            }
        except Exception:
            logger.warning("FateThreads.observe_turn() failed; continuing safely.", exc_info=True)
            return {"active_themes": list(self.threads), "pressure_map": {}, "turn": 0}

    def get_prompt_payload(self, limit: int = 5, chaos_story_pressure: Optional[Dict[str, Any]] = None) -> str:
        """Create a robust fate payload for AI prompts each turn."""
        try:
            if not self.thread_records:
                return ""

            lines = ["=== FATE PRESSURE (NORN THREAD MAP) ==="]
            for record in self.thread_records[: max(1, int(limit))]:
                npc_text = ", ".join(record.npcs_present[:3]) if record.npcs_present else "none"
                lines.append(
                    f"- {record.theme} | pressure={record.pressure} | last_seen=T{record.last_turn_seen} | "
                    f"location={record.location or 'unknown'} | npcs={npc_text}"
                )
            pressure = chaos_story_pressure or {}
            if pressure:
                directives = [str(d) for d in pressure.get("story_directives", []) if str(d).strip()]
                lines.append(
                    f"CHAOS HEAT: {pressure.get('chaos_temperature', '?')}/100 "
                    f"({pressure.get('heat_band', 'unknown')}) | persistent={pressure.get('persistent_pressure', 0)}"
                )
                for directive in directives[:2]:
                    lines.append(f"- Chaos directive: {directive}")

            lines.append(
                "FOR THIS TURN: reinforce at least two top-pressure threads via concrete NPC intent, location detail, and immediate consequences."
            )
            lines.append(
                "Never ignore these pressures when resolving the player's current goal."
            )
            return "\n".join(lines)
        except Exception:
            logger.warning("FateThreads.get_prompt_payload() failed.", exc_info=True)
            return ""

    def _chaos_seed_themes(self, chaos_story_pressure: Optional[Dict[str, Any]]) -> List[str]:
        """Seed fate threads from chaos heat so Norn pressure matches world instability."""
        try:
            pressure = chaos_story_pressure or {}
            band = str(pressure.get("heat_band", "warm") or "warm").lower()
            if band == "cool":
                return ["quiet oaths tested in ordinary hours"]
            if band == "warm":
                return ["omens threading through daily life"]
            if band == "hot":
                return ["blood-price rising with every rash deed", "the law's shadow tightening"]
            return [
                "the land convulses under broken authority",
                "spirits gather where mortal order fails",
            ]
        except Exception:
            logger.warning("FateThreads._chaos_seed_themes() failed.", exc_info=True)
            return []

    def _theme_match_score(self, theme: str, scan_text: str) -> int:
        words = [w for w in re.split(r"[^a-z0-9]+", theme.lower()) if len(w) >= 4]
        return sum(1 for word in words if word in scan_text)

    def _upsert_record(
        self,
        theme: str,
        turn_count: int,
        source: str,
        pressure_delta: int,
        location: str = "",
        npcs_present: List[str] = None,
    ) -> None:
        for record in self.thread_records:
            if record.theme == theme:
                record.pressure = min(15, max(0, record.pressure + int(pressure_delta)))
                record.last_turn_seen = max(record.last_turn_seen, int(turn_count or 0))
                if location:
                    record.location = location
                if npcs_present:
                    record.npcs_present = [str(npc) for npc in npcs_present[:5]]
                record.updated_at = datetime.utcnow().isoformat()
                return

        self.thread_records.append(
            FateThreadRecord(
                theme=theme,
                # SH-04: floor at 3 so new records survive at least 3 turns of decay
                pressure=max(3, int(pressure_delta)),
                introduced_turn=int(turn_count or 0),
                last_turn_seen=int(turn_count or 0),
                source=source,
                location=location,
                npcs_present=[str(npc) for npc in (npcs_present or [])[:5]],
            )
        )


    def get_focus_themes(self, limit: int = 3) -> List[str]:
        """Return highest-pressure themes to seed other systems and prompt scaffolds."""
        try:
            self.thread_records.sort(
                key=lambda rec: (rec.pressure, rec.last_turn_seen), reverse=True
            )
            return [rec.theme for rec in self.thread_records[: max(1, int(limit))]]
        except Exception:
            logger.warning("FateThreads.get_focus_themes() failed.", exc_info=True)
            return list(self.threads[: max(1, int(limit))])

    def _safe_threads(self) -> list:
        """Return validated thread list stripped of any non-string entries."""
        safe = [t for t in self.threads if isinstance(t, str)]
        if len(safe) != len(self.threads):
            logger.warning(
                "FateThreads: found %d non-string thread(s); stripped.",
                len(self.threads) - len(safe),
            )
        return safe

    def to_dict(self) -> dict:
        """Minimal serialization — active thread names only.
        Backward-compatible with legacy callers and tests."""
        try:
            return {"threads": self._safe_threads()}
        except Exception:
            logger.error("FateThreads.to_dict() failed; returning empty threads.", exc_info=True)
            return {"threads": []}

    def to_full_dict(self) -> dict:
        """Complete serialization including pressure telemetry (thread_records).
        Use this in save_session() to preserve Norn pressure data across reloads."""
        try:
            return {
                "threads": self._safe_threads(),
                "thread_records": [rec.to_dict() for rec in self.thread_records],
            }
        except Exception:
            logger.error("FateThreads.to_full_dict() failed; returning threads only.", exc_info=True)
            return {"threads": self._safe_threads()}

    def validate(self) -> bool:
        """SH-01/SH-02: Auto-repair state after load or corruption.

        Returns True if any repairs were made.
        Safe to call at any time — never raises.
        """
        try:
            repaired = False
            # Ensure threads is a list of non-empty strings within cap
            if not isinstance(self.threads, list):
                self.threads = []
                repaired = True
            clean = [str(t) for t in self.threads if t and isinstance(t, str)]
            if len(clean) != len(self.threads):
                self.threads = clean
                repaired = True
            self.threads = self.threads[:self.max_active]
            # Ensure thread_records contains only valid FateThreadRecord instances
            clean_recs = [r for r in self.thread_records if isinstance(r, FateThreadRecord)]
            if len(clean_recs) != len(self.thread_records):
                self.thread_records = clean_recs
                repaired = True
            self.thread_records = self.thread_records[:self.max_records]
            # SH-05: ensure thread_options never fully depleted
            self._maybe_refresh_pool()
            if repaired:
                logger.info("FateThreads.validate(): self-repair completed.")
            return repaired
        except Exception:
            logger.warning("FateThreads.validate(): repair failed.", exc_info=True)
            return False

    def _maybe_refresh_pool(self) -> None:
        """SH-05: Refresh thread_options when pool falls below minimum threshold.

        Prevents update() from being unable to weave new threads when the
        pool is near exhaustion. Adds DEFAULT_THREADS entries not currently
        active, up to the full default pool size.
        """
        try:
            if len(self.thread_options) < 5:
                new_options = [t for t in DEFAULT_THREADS if t not in self.thread_options]
                if new_options:
                    self.thread_options.extend(new_options)
                    logger.debug(
                        "FateThreads: pool refreshed with %d new thread options.", len(new_options)
                    )
        except Exception:
            logger.warning("FateThreads._maybe_refresh_pool() failed.", exc_info=True)

    def from_dict(self, data):
        """Restore from save."""
        try:
            if data:
                self.threads = data.get("threads", [])
                self.thread_records = []
                for raw in data.get("thread_records", []):
                    try:
                        self.thread_records.append(FateThreadRecord.from_dict(raw))
                    except Exception:
                        continue
            self.validate()  # SH-01/SH-02: auto-repair after any load
        except Exception:
            logger.error(
                "FateThreads.from_dict() failed; leaving current state unchanged.",
                exc_info=True,
            )


@dataclass
class FateThreadRecord:
    """Detailed fate-thread telemetry for medium-term narrative continuity."""

    theme: str
    pressure: int = 1
    introduced_turn: int = 0
    last_turn_seen: int = 0
    source: str = "system"
    location: str = ""
    npcs_present: List[str] = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "theme": self.theme,
            "pressure": self.pressure,
            "introduced_turn": self.introduced_turn,
            "last_turn_seen": self.last_turn_seen,
            "source": self.source,
            "location": self.location,
            "npcs_present": list(self.npcs_present),
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FateThreadRecord":
        return cls(
            theme=str(data.get("theme", "")),
            pressure=int(data.get("pressure", 1) or 1),
            introduced_turn=int(data.get("introduced_turn", 0) or 0),
            last_turn_seen=int(data.get("last_turn_seen", 0) or 0),
            source=str(data.get("source", "system")),
            location=str(data.get("location", "")),
            npcs_present=[str(npc) for npc in data.get("npcs_present", [])[:5]],
            updated_at=str(data.get("updated_at", datetime.utcnow().isoformat())),
        )
