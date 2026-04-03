"""
Enhanced Context Builder
========================

Phase 4.2 of the Memory Consolidation Plan.

Builds richly structured, human-readable context strings that are
injected into the AI prompt each turn.  All memory access goes through
:class:`~systems.memory_query_engine.MemoryQueryEngine` so this class
stays decoupled from the underlying Muninn storage layer.

Usage::

    from systems.memory_query_engine import MemoryQueryEngine
    from systems.enhanced_context_builder import EnhancedContextBuilder

    engine = MemoryQueryEngine(muninn_instance)
    builder = EnhancedContextBuilder(engine)

    prompt_ctx = builder.build_turn_context(current_turn=42)
    char_ctx   = builder.build_character_context("sigrid_ironweave")
    world_ctx  = builder.build_world_context(location="hedeby")
"""

import logging
from typing import Any, Dict, List, Optional

from systems.memory_query_engine import MemoryQueryEngine

logger = logging.getLogger(__name__)

_NONE = "(none)"
_NO_DATA = "(no data)"


class EnhancedContextBuilder:
    """
    Builds comprehensive AI context strings from unified memory.

    Each ``build_*`` method assembles one or more labelled sections and
    returns a single newline-joined string ready for prompt injection.
    Sections that have no data emit a placeholder line rather than being
    omitted, so the AI always sees a consistent context skeleton.
    """

    # How many past turns to look back for recent-history section.
    RECENT_TURNS_LOOKBACK: int = 5
    # Maximum event bullets shown in the recent-history section.
    RECENT_EVENTS_SHOWN: int = 3

    def __init__(self, memory: MemoryQueryEngine) -> None:
        """
        Args:
            memory: A fully initialised :class:`MemoryQueryEngine` instance.
        """
        self.memory = memory

    # ------------------------------------------------------------------ #
    # Primary context builder                                              #
    # ------------------------------------------------------------------ #

    def build_turn_context(self, current_turn: int) -> str:
        """
        Build the main AI context string for *current_turn*.

        Sections
        --------
        1. **RECENT HISTORY** — last ``RECENT_TURNS_LOOKBACK`` turns of events
        2. **EMOTIONAL CONTEXT** — dominant emotion per character this turn
        3. **NARRATIVE MOMENTUM** — story phase and active themes
        4. **WORLD STATE** — season and political-tension level

        Returns a single newline-joined string.
        """
        parts: List[str] = []

        try:
            parts += self._section_recent_history(current_turn)
        except Exception:
            logger.exception("build_turn_context: recent-history section failed")
            parts += ["=== RECENT HISTORY ===", _NO_DATA]

        try:
            parts += self._section_emotional_context(current_turn)
        except Exception:
            logger.exception("build_turn_context: emotional-context section failed")
            parts += ["\n=== EMOTIONAL CONTEXT ===", _NO_DATA]

        try:
            parts += self._section_narrative_momentum()
        except Exception:
            logger.exception("build_turn_context: narrative-momentum section failed")
            parts += ["\n=== NARRATIVE MOMENTUM ===", _NO_DATA]

        try:
            parts += self._section_world_state()
        except Exception:
            logger.exception("build_turn_context: world-state section failed")
            parts += ["\n=== WORLD STATE ===", _NO_DATA]

        return "\n".join(parts)

    # ------------------------------------------------------------------ #
    # Supplementary context builders                                       #
    # ------------------------------------------------------------------ #

    def build_character_context(self, character_id: str) -> str:
        """
        Build a character-focused context string for *character_id*.

        Sections: SKILL PROGRESSION · RELATIONSHIPS · EMOTIONAL PATTERNS ·
        NARRATIVE ARC.
        """
        parts: List[str] = [f"=== CHARACTER: {character_id.upper()} ==="]
        try:
            dev = self.memory.query_character_development(character_id)
        except Exception:
            logger.exception(
                "build_character_context: query_character_development failed for %r",
                character_id,
            )
            parts.append(_NO_DATA)
            return "\n".join(parts)

        # Skill progression
        parts.append("\n-- Skill Progression --")
        skills = dev.get("skill_progression") or []
        if skills:
            for rec in skills[:5]:
                skill = rec.get("skill") or rec.get("summary") or str(rec)
                parts.append(f"• {skill}")
        else:
            parts.append(_NONE)

        # Relationship evolution
        parts.append("\n-- Relationships --")
        rels = dev.get("relationship_evolution") or []
        if rels:
            for rec in rels[:5]:
                desc = rec.get("description") or rec.get("summary") or str(rec)
                parts.append(f"• {desc}")
        else:
            parts.append(_NONE)

        # Emotional patterns
        parts.append("\n-- Emotional Patterns --")
        patterns = dev.get("emotional_patterns") or []
        if patterns:
            for p in patterns[:5]:
                parts.append(f"• {p['emotion']}: {p['count']}×")
        else:
            parts.append(_NONE)

        # Narrative arc
        parts.append("\n-- Narrative Arc --")
        arc = dev.get("narrative_arc") or []
        if arc:
            for milestone in arc[:5]:
                event = milestone.get("event") or milestone.get("summary") or str(milestone)
                turn = (
                    (milestone.get("game_timestamp") or {}).get("turn", "?")
                )
                parts.append(f"• [turn {turn}] {event}")
        else:
            parts.append(_NONE)

        return "\n".join(parts)

    def build_world_context(self, location: Optional[str] = None) -> str:
        """
        Build a world-state context string, optionally scoped to *location*.

        Sections: CURRENT EVENTS · FACTION STATUS · CULTURAL CLIMATE ·
        ENVIRONMENT.
        """
        header = f"=== WORLD STATE{': ' + location.upper() if location else ''} ==="
        parts: List[str] = [header]

        try:
            ws = self.memory.query_world_state(location=location)
        except Exception:
            logger.exception("build_world_context: query_world_state failed")
            parts.append(_NO_DATA)
            return "\n".join(parts)

        # Current events
        parts.append("\n-- Current Events --")
        events = ws.get("current_events") or []
        if events:
            for ev in events[-5:]:
                desc = ev.get("event") or ev.get("summary") or str(ev)
                parts.append(f"• {desc}")
        else:
            parts.append(_NONE)

        # Faction status
        parts.append("\n-- Faction Status --")
        factions = ws.get("faction_status") or []
        if factions:
            for f in factions[-3:]:
                desc = f.get("summary") or f.get("faction") or str(f)
                parts.append(f"• {desc}")
        else:
            parts.append(_NONE)

        # Cultural climate
        parts.append("\n-- Cultural Climate --")
        culture = ws.get("cultural_climate") or []
        if culture:
            for c in culture[-3:]:
                desc = c.get("summary") or c.get("shift") or str(c)
                parts.append(f"• {desc}")
        else:
            parts.append(_NONE)

        # Environmental conditions
        parts.append("\n-- Environment --")
        env = ws.get("environmental_conditions") or []
        if env:
            for e in env[-2:]:
                desc = e.get("summary") or e.get("condition") or str(e)
                parts.append(f"• {desc}")
        else:
            parts.append(_NONE)

        return "\n".join(parts)

    # ------------------------------------------------------------------ #
    # Private section builders                                             #
    # ------------------------------------------------------------------ #

    def _section_recent_history(self, current_turn: int) -> List[str]:
        lines = ["=== RECENT HISTORY ==="]
        lookback_start = max(0, current_turn - self.RECENT_TURNS_LOOKBACK)
        recent_events: List[Dict[str, Any]] = []
        for turn in range(lookback_start, current_turn):
            ctx = self.memory.query_turn_context(turn)
            recent_events.extend(ctx.get("events") or [])

        shown = recent_events[-self.RECENT_EVENTS_SHOWN:]
        if shown:
            for ev in shown:
                summary = (
                    ev.get("summary")
                    or ev.get("text")
                    or ev.get("description")
                    or str(ev)
                )
                lines.append(f"• {summary}")
        else:
            lines.append(_NONE)
        return lines

    def _section_emotional_context(self, current_turn: int) -> List[str]:
        lines = ["\n=== EMOTIONAL CONTEXT ==="]
        emotional_state = self.memory.query_emotional_state(current_turn)
        if emotional_state:
            for char_id, emotions in emotional_state.items():
                if emotions:
                    dominant = max(emotions.items(), key=lambda x: x[1])
                    lines.append(
                        f"{char_id}: {dominant[0]} ({dominant[1]:.1f})"
                    )
        else:
            lines.append(_NONE)
        return lines

    def _section_narrative_momentum(self) -> List[str]:
        lines = ["\n=== NARRATIVE MOMENTUM ==="]
        ns = self.memory.query_narrative_state()
        lines.append(f"Story phase: {ns.get('current_phase', 'unknown')}")
        themes = ns.get("active_themes") or []
        lines.append(f"Themes: {', '.join(themes) if themes else _NONE}")
        return lines

    def _section_world_state(self) -> List[str]:
        lines = ["\n=== WORLD STATE ==="]
        ws = self.memory.query_world_state()

        # Pull season and political tension from whichever sub-list has them.
        season = _extract_field(
            ws.get("environmental_conditions") or ws.get("current_events") or [],
            "season",
        )
        tension = _extract_field(
            ws.get("faction_status") or ws.get("current_events") or [],
            "political_tension",
        )

        lines.append(f"Season: {season if season is not None else 'unknown'}")
        if tension is not None:
            lines.append(f"Political climate: {tension}/100")
        else:
            lines.append("Political climate: unknown")

        return lines


# ─────────────────────────────────────────────────────────────────────────────
# Module-level helpers
# ─────────────────────────────────────────────────────────────────────────────


def _extract_field(
    records: List[Dict[str, Any]], field: str
) -> Optional[Any]:
    """
    Walk *records* newest-first and return the first non-None value for
    *field*, or ``None`` if no record contains it.
    """
    for rec in reversed(records):
        value = rec.get(field)
        if value is not None:
            return value
    return None
