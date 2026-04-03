"""
Soul Mechanics
==============

The Norse three-part psyche as a living simulation layer.

Norse metaphysics divides consciousness into distinct but interacting
soul-parts that can conflict, amplify, or override one another. This
module models:

  Hugr  — The Conscious Mind
          Immediate, volatile emotional states that drive short-term
          reactions and dialogue tone. Decays toward the character's
          baseline after each turn.

  Fylgja — The Subconscious / Instinct
           Deep-seated psychological drivers, hidden traumas, and
           intuitive responses. Shifts slowly. Can override the Hugr
           in high-stress situations (fight-or-flight override).

  Hamingja — Spiritual Momentum / Luck
             Metaphysical tracking of a character's spiritual weight.
             High Hamingja = alignment with fate; low = cursed drift.
             Broken oaths, betrayals, and sacred acts all shift it.

Additionally:
  CognitiveFriction — Tracks dissonance between core values and
                      recent actions. High friction triggers
                      psychological events.
  EmotionalMemoryEcho — When Muninn recalls a memory, a decaying
                        re-application of those original emotions
                        is temporarily layered onto the character.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SRD condition → soul-impact mapping (lazy-loaded)
# ---------------------------------------------------------------------------

# Hamingja deltas keyed by SRD condition name
_CONDITION_HAMINGJA_DELTA: Dict[str, float] = {
    "unconscious": -0.12,
    "dying":       -0.15,
    "paralyzed":   -0.08,
    "petrified":   -0.10,
    "stunned":     -0.05,
    "frightened":  -0.04,
    "charmed":     -0.03,
    "poisoned":    -0.03,
    "exhaustion":  -0.02,   # per level, multiplied below
}

# Hugr emotion spikes keyed by SRD condition name → {emotion: delta}
_CONDITION_HUGR_SPIKES: Dict[str, Dict[str, float]] = {
    "frightened":  {"fear": +0.6, "courage": -0.4},
    "charmed":     {"love": +0.5, "suspicion": -0.2},
    "unconscious": {"pain": +0.5},
    "paralyzed":   {"despair": +0.4, "fear": +0.3},
    "stunned":     {"confusion": +0.4},
    "poisoned":    {"pain": +0.3, "nausea": +0.2},
    "prone":       {"shame": +0.15},
    "grappled":    {"anger": +0.3},
}

# Conditions that trigger Fylgja trauma scarring
_TRAUMA_CONDITIONS = {"unconscious", "dying", "petrified", "paralyzed"}

_conditions_system_cls = None


def _get_conditions_system():
    global _conditions_system_cls
    if _conditions_system_cls is None:
        try:
            from systems.conditions_system import ConditionsSystem
            _conditions_system_cls = ConditionsSystem
        except ImportError:
            pass
    return _conditions_system_cls() if _conditions_system_cls else None


def apply_conditions_to_soul(
    soul: "SoulLayer",
    conditions: List[str],
    turn: int,
    exhaustion_level: int = 0,
) -> List[str]:
    """Apply D&D 5E SRD condition effects to a SoulLayer.

    Maps active conditions to:
      - Hamingja deltas (spiritual weight / luck drain)
      - Hugr emotional spikes
      - Fylgja trauma scars (for severe conditions)

    Args:
        soul: SoulLayer to modify in-place.
        conditions: List of SRD condition strings.
        turn: Current turn number.
        exhaustion_level: 0-6 exhaustion level.

    Returns:
        List of event strings for the dispatcher (same format as SoulLayer.tick()).
    """
    events: List[str] = []
    if not conditions and not exhaustion_level:
        return events

    try:
        normalized: List[str] = []
        cs = _get_conditions_system()
        if cs is not None:
            normalized = cs.normalize_conditions(conditions)
        else:
            normalized = [str(c).lower().strip() for c in conditions]

        # Hamingja deltas
        for cond in normalized:
            delta = _CONDITION_HAMINGJA_DELTA.get(cond, 0.0)
            if delta:
                soul.hamingja.shift(delta, f"condition:{cond}")

        # Exhaustion Hamingja drain (stacks per level)
        if exhaustion_level > 0:
            exh_delta = -0.02 * min(exhaustion_level, 6)
            soul.hamingja.shift(exh_delta, f"exhaustion_level_{exhaustion_level}")

        # Hugr emotion spikes
        for cond in normalized:
            spikes = _CONDITION_HUGR_SPIKES.get(cond, {})
            for emotion, delta in spikes.items():
                soul.hugr.apply(emotion, delta, turn)

        # Fylgja trauma scarring for severe conditions
        for cond in normalized:
            if cond in _TRAUMA_CONDITIONS:
                trauma_msg = f"Suffered {cond} in combat — spiritual scar"
                soul.fylgja.add_trauma(trauma_msg)
                events.append(f"CONDITION_TRAUMA:{soul.character_id}:{cond}")

        # Death-adjacent trigger
        if "unconscious" in normalized or "dying" in normalized:
            events.append(f"DEATH_ADJACENT:{soul.character_id}")

        logger.debug(
            "apply_conditions_to_soul(%s): conds=%s exh=%d",
            soul.character_id, normalized, exhaustion_level,
        )
    except Exception as exc:
        logger.warning("apply_conditions_to_soul failed for %s: %s", soul.character_id, exc)

    return events


# ---------------------------------------------------------------------------
# Soul Layers
# ---------------------------------------------------------------------------


@dataclass
class Hugr:
    """
    The Conscious Mind — volatile, short-term emotional surface state.

    Emotions here are 'hot' and influential in immediate reactions.
    Each emotion is a float in [-1.0, +1.0].
    Positive = intensity toward that emotion; 0 = neutral.
    The state decays toward 0 each turn by ``decay_rate``.
    """

    emotions: Dict[str, float] = field(default_factory=dict)
    decay_rate: float = 0.15  # Fraction lost per turn
    spikes: List[Tuple[str, float, int]] = field(
        default_factory=list
    )  # (emotion, magnitude, turn_triggered)

    def apply(self, emotion: str, delta: float, turn: int) -> float:
        """Apply a delta to an emotion. Returns the new clamped value."""
        current = self.emotions.get(emotion, 0.0)
        new_val = max(-1.0, min(1.0, current + delta))
        self.emotions[emotion] = new_val
        if abs(delta) >= 0.4:
            self.spikes.append((emotion, delta, turn))
        return new_val

    def decay(self):
        """Move all emotions toward 0 (neutrality) each turn."""
        self.emotions = {
            k: v * (1.0 - self.decay_rate)
            for k, v in self.emotions.items()
            if abs(v) > 0.01
        }

    def dominant_emotion(self) -> Optional[Tuple[str, float]]:
        """Return the strongest current emotion by absolute magnitude."""
        if not self.emotions:
            return None
        return max(self.emotions.items(), key=lambda kv: abs(kv[1]))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "emotions": self.emotions,
            "decay_rate": self.decay_rate,
            "spikes": [
                {"emotion": e, "magnitude": m, "turn": t}
                for e, m, t in self.spikes[-20:]
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hugr":
        obj = cls(
            emotions=data.get("emotions", {}),
            decay_rate=data.get("decay_rate", 0.15),
        )
        obj.spikes = [
            (s["emotion"], s["magnitude"], s["turn"]) for s in data.get("spikes", [])
        ]
        return obj


@dataclass
class Fylgja:
    """
    The Subconscious / Instinct — deep drivers and trauma signatures.

    Shifts very slowly over many turns. In extreme stress it can
    *override* the Hugr (triggering a FYLGJA_OVERRIDE event).
    Traumas leave permanent 'scars' that lower override thresholds.
    """

    drivers: Dict[str, float] = field(default_factory=dict)
    trauma_scars: List[str] = field(default_factory=list)
    override_threshold: float = 0.85  # cumulative stress required
    drift_rate: float = 0.02  # how fast it shifts per turn

    def imprint(self, driver: str, delta: float) -> float:
        """Slowly imprint a psychological driver."""
        current = self.drivers.get(driver, 0.0)
        new_val = max(-1.0, min(1.0, current + delta * self.drift_rate))
        self.drivers[driver] = new_val
        return new_val

    def add_trauma(self, description: str):
        """Record a trauma scar, which lowers the override threshold."""
        if description not in self.trauma_scars:
            self.trauma_scars.append(description)
            self.override_threshold = max(0.4, self.override_threshold - 0.08)
            logger.info(
                "Fylgja trauma imprinted: %s (threshold now %.2f)",
                description,
                self.override_threshold,
            )

    def check_override(self, hugr: Hugr) -> Optional[str]:
        """
        Return the overriding driver name if accumulated stress in the
        Hugr surpasses the threshold, else None.
        """
        stress = sum(abs(v) for v in hugr.emotions.values())
        if stress >= self.override_threshold:
            # The strongest subconscious driver takes control
            if self.drivers:
                dominant = max(self.drivers.items(), key=lambda kv: abs(kv[1]))
                return dominant[0]
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "drivers": self.drivers,
            "trauma_scars": self.trauma_scars,
            "override_threshold": self.override_threshold,
            "drift_rate": self.drift_rate,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Fylgja":
        obj = cls(
            drivers=data.get("drivers", {}),
            trauma_scars=data.get("trauma_scars", []),
            override_threshold=data.get("override_threshold", 0.85),
            drift_rate=data.get("drift_rate", 0.02),
        )
        return obj


@dataclass
class Hamingja:
    """
    Spiritual Momentum / Luck — metaphysical weight of the soul.

    Range 0.0 (cursed, spiritually depleted) to 1.0 (blessed,
    fate-aligned). Broken oaths, betrayals, and dishonorable acts
    drain it. Heroic deeds, sacred acts, and honoring debts restore it.
    """

    value: float = 0.5
    history: List[Dict[str, Any]] = field(default_factory=list)

    def shift(self, delta: float, reason: str):
        """Apply delta and record the cause."""
        old = self.value
        self.value = max(0.0, min(1.0, self.value + delta))
        self.history.append(
            {
                "from": round(old, 3),
                "to": round(self.value, 3),
                "delta": round(delta, 3),
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
            }
        )
        logger.debug("Hamingja: %.2f → %.2f (%s)", old, self.value, reason)

    @property
    def state_label(self) -> str:
        if self.value >= 0.8:
            return "blessed"
        if self.value >= 0.6:
            return "favored"
        if self.value >= 0.4:
            return "uncertain"
        if self.value >= 0.2:
            return "burdened"
        return "cursed"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "history": self.history[-20:],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hamingja":
        obj = cls(value=data.get("value", 0.5))
        obj.history = data.get("history", [])
        return obj


# ---------------------------------------------------------------------------
# Cognitive Friction
# ---------------------------------------------------------------------------


@dataclass
class CognitiveFriction:
    """
    Tracks the psychological friction between a character's declared
    core values and their actual recent behavioral record.

    High friction → stress accumulates → breakdown events fire.
    """

    core_values: List[str] = field(default_factory=list)
    violations: List[Dict[str, Any]] = field(default_factory=list)
    friction_score: float = 0.0
    breakdown_threshold: float = 0.75
    relief_rate: float = 0.05  # friction released per pass turn

    def record_action(
        self, action: str, violates_values: List[str], turn: int
    ) -> float:
        """
        Log an action and its value conflicts. Returns updated friction.
        """
        if not violates_values:
            # Consistent action reduces friction slightly
            self.friction_score = max(0.0, self.friction_score - self.relief_rate)
            return self.friction_score

        delta = 0.1 * len(violates_values)
        self.friction_score = min(1.0, self.friction_score + delta)
        self.violations.append(
            {
                "action": action[:200],
                "conflicts": violates_values,
                "turn": turn,
                "friction_after": round(self.friction_score, 3),
            }
        )
        return self.friction_score

    def check_breakdown(self) -> bool:
        """Return True if friction has crossed the breakdown threshold."""
        return self.friction_score >= self.breakdown_threshold

    def resolve(self, reason: str):
        """Cathartic resolution — sharply drop friction."""
        self.friction_score = max(0.0, self.friction_score - 0.4)
        logger.info(
            "Cognitive friction resolved: %s (now %.2f)", reason, self.friction_score
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "core_values": self.core_values,
            "violations": self.violations[-20:],
            "friction_score": self.friction_score,
            "breakdown_threshold": self.breakdown_threshold,
            "relief_rate": self.relief_rate,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CognitiveFriction":
        obj = cls(
            core_values=data.get("core_values", []),
            friction_score=data.get("friction_score", 0.0),
            breakdown_threshold=data.get("breakdown_threshold", 0.75),
            relief_rate=data.get("relief_rate", 0.05),
        )
        obj.violations = data.get("violations", [])
        return obj


# ---------------------------------------------------------------------------
# Emotional Memory Echo
# ---------------------------------------------------------------------------


@dataclass
class EmotionalMemoryEcho:
    """
    When Muninn recalls a memory, the emotional charge of that original
    event is temporarily re-applied to the character's Hugr with a
    decaying intensity.
    """

    source_memory_id: str
    emotion_deltas: Dict[str, float]  # original emotion shifts
    strength: float = 1.0  # starts full, decays each turn
    decay_per_turn: float = 0.25
    turn_applied: int = 0

    def apply_to_hugr(self, hugr: Hugr, current_turn: int) -> bool:
        """
        Apply the echo to a Hugr. Returns False when the echo is spent.
        """
        elapsed = current_turn - self.turn_applied
        intensity = self.strength * ((1.0 - self.decay_per_turn) ** elapsed)
        if intensity < 0.05:
            return False  # Echo spent

        for emotion, base_delta in self.emotion_deltas.items():
            hugr.apply(emotion, base_delta * intensity, current_turn)

        logger.debug(
            "Memory echo '%s' applied at %.2f intensity",
            self.source_memory_id,
            intensity,
        )
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_memory_id": self.source_memory_id,
            "emotion_deltas": self.emotion_deltas,
            "strength": self.strength,
            "decay_per_turn": self.decay_per_turn,
            "turn_applied": self.turn_applied,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmotionalMemoryEcho":
        return cls(
            source_memory_id=data.get("source_memory_id", ""),
            emotion_deltas=data.get("emotion_deltas", {}),
            strength=data.get("strength", 1.0),
            decay_per_turn=data.get("decay_per_turn", 0.25),
            turn_applied=data.get("turn_applied", 0),
        )


# ---------------------------------------------------------------------------
# SoulLayer — the unified composite per character
# ---------------------------------------------------------------------------


@dataclass
class SoulLayer:
    """
    The complete Norse psyche for a single character.
    Aggregates Hugr, Fylgja, Hamingja, CognitiveFriction, and active
    memory echoes into one serializable unit.
    """

    character_id: str
    hugr: Hugr = field(default_factory=Hugr)
    fylgja: Fylgja = field(default_factory=Fylgja)
    hamingja: Hamingja = field(default_factory=Hamingja)
    friction: CognitiveFriction = field(default_factory=CognitiveFriction)
    active_echoes: List[EmotionalMemoryEcho] = field(default_factory=list)

    def tick(self, turn: int) -> List[str]:
        """
        Advance one turn. Returns list of triggered events as strings.
        """
        events = []

        # 1. Decay Hugr emotions toward neutral
        self.hugr.decay()

        # 2. Apply and cull spent memory echoes
        live_echoes = []
        for echo in self.active_echoes:
            if echo.apply_to_hugr(self.hugr, turn):
                live_echoes.append(echo)
            else:
                logger.debug("Memory echo '%s' expired", echo.source_memory_id)
        self.active_echoes = live_echoes

        # 3. Check for Fylgja override
        override = self.fylgja.check_override(self.hugr)
        if override:
            events.append(f"FYLGJA_OVERRIDE:{self.character_id}:{override}")
            logger.info(
                "Fylgja override triggered for %s — driver: %s",
                self.character_id,
                override,
            )

        # 4. Check cognitive breakdown
        if self.friction.check_breakdown():
            events.append(f"COGNITIVE_BREAKDOWN:{self.character_id}")
            logger.info(
                "Cognitive breakdown for %s (friction %.2f)",
                self.character_id,
                self.friction.friction_score,
            )

        return events

    def attach_echo(
        self,
        memory_id: str,
        emotion_deltas: Dict[str, float],
        turn: int,
        strength: float = 0.6,
    ):
        """Attach a memory echo to this soul layer."""
        echo = EmotionalMemoryEcho(
            source_memory_id=memory_id,
            emotion_deltas=emotion_deltas,
            strength=strength,
            turn_applied=safe_turn,
        )
        self.active_echoes.append(echo)
        # Cap to last 5 concurrent echoes
        if len(self.active_echoes) > 5:
            self.active_echoes = self.active_echoes[-5:]

    def get_ai_summary(self) -> str:
        """Return a compact human-readable summary for the AI Narrator."""
        dominant = self.hugr.dominant_emotion()
        dom_str = f"{dominant[0]} ({dominant[1]:+.2f})" if dominant else "neutral"
        return (
            f"Soul [{self.character_id}]: "
            f"Hugr={dom_str}, "
            f"Hamingja={self.hamingja.state_label} "
            f"({self.hamingja.value:.2f}), "
            f"Friction={self.friction.friction_score:.2f}, "
            f"Trauma scars={len(self.fylgja.trauma_scars)}, "
            f"Active echoes={len(self.active_echoes)}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "character_id": self.character_id,
            "hugr": self.hugr.to_dict(),
            "fylgja": self.fylgja.to_dict(),
            "hamingja": self.hamingja.to_dict(),
            "friction": self.friction.to_dict(),
            "active_echoes": [e.to_dict() for e in self.active_echoes],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SoulLayer":
        obj = cls(character_id=data["character_id"])
        if "hugr" in data:
            obj.hugr = Hugr.from_dict(data["hugr"])
        if "fylgja" in data:
            obj.fylgja = Fylgja.from_dict(data["fylgja"])
        if "hamingja" in data:
            obj.hamingja = Hamingja.from_dict(data["hamingja"])
        if "friction" in data:
            obj.friction = CognitiveFriction.from_dict(data["friction"])
        obj.active_echoes = [
            EmotionalMemoryEcho.from_dict(e) for e in data.get("active_echoes", [])
        ]
        return obj


# ---------------------------------------------------------------------------
# SoulRegistry — manages all character soul layers
# ---------------------------------------------------------------------------


class SoulRegistry:
    """
    Global registry of SoulLayer objects, one per active character.
    Dispatches tick events each turn and feeds the EventDispatcher.
    """

    def __init__(self, dispatcher=None):
        self._souls: Dict[str, SoulLayer] = {}
        self.dispatcher = dispatcher

    def get_or_create(self, character_id: str) -> SoulLayer:
        """Return existing soul layer or create a fresh one."""
        if character_id not in self._souls:
            self._souls[character_id] = SoulLayer(character_id=character_id)
        return self._souls[character_id]

    def apply_conditions(
        self,
        character_id: str,
        conditions: List[str],
        turn: int,
        exhaustion_level: int = 0,
    ) -> List[str]:
        """Apply SRD condition effects to a character's soul layer.

        Creates the soul layer if it doesn't exist yet.
        Returns event strings (CONDITION_TRAUMA, DEATH_ADJACENT) for the dispatcher.
        """
        soul = self.get_or_create(character_id)
        events = apply_conditions_to_soul(soul, conditions, turn, exhaustion_level)
        if self.dispatcher:
            for event_str in events:
                try:
                    from systems.event_dispatcher import EventType
                    kind, *rest = event_str.split(":", 1)
                    if kind == "DEATH_ADJACENT":
                        char_id = rest[0] if rest else character_id
                        self.dispatcher.dispatch(
                            "death_adjacent",
                            {"character_id": char_id, "turn": turn},
                        )
                    elif kind == "CONDITION_TRAUMA":
                        parts = rest[0].split(":", 1) if rest else [character_id, "unknown"]
                        char_id, cond = parts[0], parts[1] if len(parts) > 1 else "unknown"
                        self.dispatcher.dispatch(
                            "condition_trauma",
                            {"character_id": char_id, "condition": cond, "turn": turn},
                        )
                except Exception as exc:
                    logger.warning("Soul condition dispatch failed: %s", exc)
        return events

    def tick_all(self, turn: int):
        """Advance all souls one turn and dispatch any triggered events."""
        for soul in self._souls.values():
            events = soul.tick(turn)
            if self.dispatcher:
                for event_str in events:
                    kind, *rest = event_str.split(":", 1)
                    try:
                        from systems.event_dispatcher import EventType

                        if kind == "FYLGJA_OVERRIDE":
                            char_id, driver = (
                                rest[0].split(":", 1) if rest else ("", "")
                            )
                            self.dispatcher.dispatch(
                                EventType.FYLGJA_OVERRIDE.value,
                                {
                                    "character_id": char_id,
                                    "driver": driver,
                                    "turn": turn,
                                },
                            )
                        elif kind == "COGNITIVE_BREAKDOWN":
                            char_id = rest[0] if rest else ""
                            self.dispatcher.dispatch(
                                EventType.COGNITIVE_BREAKDOWN.value,
                                {
                                    "character_id": char_id,
                                    "friction": (
                                        self._souls[char_id].friction.friction_score
                                        if char_id in self._souls
                                        else 0.0
                                    ),
                                    "turn": turn,
                                },
                            )
                    except Exception as exc:
                        logger.warning("Soul event dispatch failed: %s", exc)

    def _infer_action_signals(
        self, action: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Huginn scouts action text for value conflicts and soul pressure."""
        context = context or {}
        lowered = (action or "").lower()
        violations: List[str] = []
        hamingja_delta = 0.0
        driver_deltas: Dict[str, float] = {}

        if any(token in lowered for token in ("betray", "deceive", "steal")):
            violations.extend(["honor", "oath-keeping"])
            hamingja_delta -= 0.08
            driver_deltas["paranoia"] = 0.5
        if any(token in lowered for token in ("murder", "slay", "sacrifice")):
            violations.append("mercy")
            hamingja_delta -= 0.1
            driver_deltas["wrath"] = 0.45
        if any(token in lowered for token in ("protect", "aid", "heal", "honor")):
            hamingja_delta += 0.06
            driver_deltas["duty"] = 0.35

        trauma_note = ""
        if context.get("is_sacred_location") and any(
            token in lowered for token in ("betray", "murder", "sacrifice")
        ):
            hamingja_delta -= 0.12
            trauma_note = "Profaned sacred ground through violence or betrayal"

        return {
            "violations": sorted(set(violations)),
            "hamingja_delta": round(hamingja_delta, 3),
            "driver_deltas": driver_deltas,
            "trauma_note": trauma_note,
        }

    def process_action(
        self,
        character_id: str,
        action: str,
        turn: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Apply action-derived psyche shifts for one character."""
        soul = self.get_or_create(character_id)
        safe_action = str(action or "").strip()
        safe_turn = max(0, int(turn or 0))
        signals = self._infer_action_signals(safe_action, context=context)
        friction = soul.friction.record_action(
            safe_action,
            signals.get("violations", []),
            safe_turn,
        )

        hamingja_delta = float(signals.get("hamingja_delta", 0.0))
        if abs(hamingja_delta) > 0.001:
            soul.hamingja.shift(hamingja_delta, reason=f"Action: {safe_action[:80]}")

        for driver, delta in (signals.get("driver_deltas", {}) or {}).items():
            soul.fylgja.imprint(str(driver), float(delta))

        trauma_note = str(signals.get("trauma_note", "") or "").strip()
        if trauma_note:
            soul.fylgja.add_trauma(trauma_note)

        return {
            "character_id": character_id,
            "friction": round(friction, 3),
            "hamingja": round(soul.hamingja.value, 3),
            "breakdown_risk": soul.friction.check_breakdown(),
            "signals": signals,
        }

    def get_ai_context(self) -> str:
        """Return multi-character soul summary for AI prompts."""
        if not self._souls:
            return ""
        lines = [s.get_ai_summary() for s in self._souls.values()]
        return "SOUL STATES:\n" + "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {cid: soul.to_dict() for cid, soul in self._souls.items()}

    def load_from_dict(self, data: Dict[str, Any]):
        """Restore all souls from serialized state."""
        for char_id, soul_data in data.items():
            self._souls[char_id] = SoulLayer.from_dict(soul_data)
        logger.info("SoulRegistry loaded %d soul layers", len(self._souls))
