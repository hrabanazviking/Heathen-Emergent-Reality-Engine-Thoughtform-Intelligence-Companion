"""
Menstrual Cycle System
======================

Models the 9-phase menstrual cycle for pre-menopausal female characters.

Each phase applies:
  * energy_modifier   — additive delta for EmotionalProfile.baseline_intensity
  * emotion_multiplier — per-channel scaling applied inside compute_impact()
  * behavior_bias      — weight delta injected into EmotionalBehavior tables

Integration points:
  MenstrualCycleState  — per-character runtime state (carry/tick each turn)
  MenstrualCycleSystem — registry; mirrors StressSystem pattern
  engine.py ticks tick_all() from _decay_emotional_states()
  EmotionalEngine.compute_impact() reads cycle_state.emotion_multiplier()
  prompt_builder.build_emotional_context() reads current_phase().name
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 9-Phase definition table (also stored in data/charts/menstrual_cycle.yaml)
# This in-code fallback is used if the YAML chart cannot be loaded.
# ---------------------------------------------------------------------------

_DEFAULT_PHASES: List[Dict[str, Any]] = [
    {
        "phase": 1,
        "name": "Menstrual Start",
        "days": [1, 2, 3],
        "energy_modifier": -0.15,
        "emotion_multiplier": {
            "fear": 1.10,
            "anger": 1.15,
            "sadness": 1.10,
            "joy": 0.85,
            "attachment": 0.95,
            "shame": 1.05,
        },
        "behavior_bias": {
            "withdrawal": 0.30,
            "rest": 0.20,
            "social": -0.15,
            "risk_taking": -0.15,
        },
        "narrative_hint": ("low energy, heightened sensitivity, withdrawal"),
    },
    {
        "phase": 2,
        "name": "Menstrual End",
        "days": [4, 5],
        "energy_modifier": -0.10,
        "emotion_multiplier": {
            "fear": 1.05,
            "anger": 1.05,
            "sadness": 1.05,
            "joy": 0.90,
            "attachment": 1.00,
            "shame": 1.00,
        },
        "behavior_bias": {
            "withdrawal": 0.20,
            "rest": 0.15,
            "social": -0.10,
        },
        "narrative_hint": ("easing fatigue, slowly rising mood"),
    },
    {
        "phase": 3,
        "name": "Early Follicular",
        "days": [6, 7, 8],
        "energy_modifier": 0.05,
        "emotion_multiplier": {
            "fear": 0.95,
            "anger": 0.95,
            "sadness": 0.95,
            "joy": 1.05,
            "attachment": 1.05,
            "shame": 0.95,
        },
        "behavior_bias": {
            "social": 0.15,
            "exploration": 0.10,
            "withdrawal": -0.10,
        },
        "narrative_hint": ("curiosity rising, more alert and socially engaged"),
    },
    {
        "phase": 4,
        "name": "Mid Follicular",
        "days": [9, 10, 11],
        "energy_modifier": 0.10,
        "emotion_multiplier": {
            "fear": 0.92,
            "anger": 0.90,
            "sadness": 0.90,
            "joy": 1.15,
            "attachment": 1.10,
            "shame": 0.90,
        },
        "behavior_bias": {
            "planning": 0.15,
            "cooperative": 0.10,
            "risk_taking": 0.05,
        },
        "narrative_hint": ("focus high, confidence rising, cooperative"),
    },
    {
        "phase": 5,
        "name": "Late Follicular",
        "days": [12, 13],
        "energy_modifier": 0.15,
        "emotion_multiplier": {
            "fear": 0.88,
            "anger": 0.85,
            "sadness": 0.88,
            "joy": 1.20,
            "attachment": 1.10,
            "shame": 0.85,
        },
        "behavior_bias": {
            "risk_taking": 0.15,
            "assertive": 0.10,
            "exploration": 0.10,
        },
        "narrative_hint": ("peak optimism, assertive and risk-taking"),
    },
    {
        "phase": 6,
        "name": "Ovulation",
        "days": [14],
        "energy_modifier": 0.20,
        "emotion_multiplier": {
            "fear": 0.80,
            "anger": 0.85,
            "sadness": 0.80,
            "joy": 1.30,
            "attachment": 1.25,
            "shame": 0.85,
        },
        "behavior_bias": {
            "bold": 0.20,
            "exploratory": 0.15,
            "social": 0.15,
            "risk_taking": 0.10,
        },
        "narrative_hint": ("peak energy and social confidence, bold and exploratory"),
    },
    {
        "phase": 7,
        "name": "Early Luteal",
        "days": [15, 16, 17, 18],
        "energy_modifier": -0.05,
        "emotion_multiplier": {
            "fear": 1.05,
            "anger": 1.05,
            "sadness": 1.05,
            "joy": 0.95,
            "attachment": 1.05,
            "shame": 1.00,
        },
        "behavior_bias": {
            "sensitivity": 0.15,
            "caution": 0.10,
            "social": -0.05,
        },
        "narrative_hint": ("slight fatigue, growing sensitivity and caution"),
    },
    {
        "phase": 8,
        "name": "Mid Luteal",
        "days": [19, 20, 21, 22, 23],
        "energy_modifier": -0.10,
        "emotion_multiplier": {
            "fear": 1.10,
            "anger": 1.10,
            "sadness": 1.15,
            "joy": 0.90,
            "attachment": 1.00,
            "shame": 1.10,
        },
        "behavior_bias": {
            "withdrawal": 0.20,
            "introspection": 0.15,
            "social": -0.10,
            "risk_taking": -0.10,
        },
        "narrative_hint": ("mood swings, irritability, introspective"),
    },
    {
        "phase": 9,
        "name": "Late Luteal / PMS",
        "days": [24, 25, 26, 27, 28],
        "energy_modifier": -0.15,
        "emotion_multiplier": {
            "fear": 1.15,
            "anger": 1.15,
            "sadness": 1.20,
            "joy": 0.80,
            "attachment": 0.90,
            "shame": 1.15,
        },
        "behavior_bias": {
            "rest": 0.25,
            "conflict_avoidance": 0.20,
            "withdrawal": 0.20,
            "social": -0.20,
            "risk_taking": -0.15,
        },
        "narrative_hint": ("fatigue, irritability, anxiety; rest-seeking"),
    },
]


@dataclass
class CyclePhase:
    """One of the 9 phases of the menstrual cycle."""

    phase: int
    name: str
    days: List[int]
    energy_modifier: float
    emotion_multiplier: Dict[str, float]
    behavior_bias: Dict[str, float]
    narrative_hint: str = ""

    def get_emotion_multiplier(self, channel: str) -> float:
        """Return the phase multiplier for a given emotion channel."""
        return self.emotion_multiplier.get(channel, 1.0)


def _load_phases_from_yaml(
    chart_path: Optional[str] = None,
) -> List[CyclePhase]:
    """
    Load the 9-phase table from data/charts/menstrual_cycle.yaml.
    Falls back to the built-in _DEFAULT_PHASES if file is missing.
    """
    if chart_path:
        p = Path(chart_path)
    else:
        # Resolve relative to this file's location
        p = Path(__file__).parent.parent / "data" / "charts" / "menstrual_cycle.yaml"

    raw_list = _DEFAULT_PHASES
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
            if isinstance(data.get("phases"), list):
                raw_list = data["phases"]
        except Exception as exc:
            logger.warning(
                "Could not load menstrual_cycle.yaml: %s; using built-in defaults.",
                exc,
            )

    phases = []
    for raw in raw_list:
        phases.append(
            CyclePhase(
                phase=int(raw.get("phase", 1)),
                name=str(raw.get("name", "Unknown")),
                days=list(raw.get("days", [])),
                energy_modifier=float(raw.get("energy_modifier", 0.0)),
                emotion_multiplier=dict(raw.get("emotion_multiplier", {})),
                behavior_bias=dict(raw.get("behavior_bias", {})),
                narrative_hint=str(raw.get("narrative_hint", "")),
            )
        )
    return phases


# Module-level phase table — loaded once at import time
CYCLE_PHASES: List[CyclePhase] = _load_phases_from_yaml()

# Fast lookup: cycle_day (1-based) → CyclePhase
_DAY_TO_PHASE: Dict[int, CyclePhase] = {}
for _ph in CYCLE_PHASES:
    for _d in _ph.days:
        _DAY_TO_PHASE[_d] = _ph


def phase_for_day(cycle_day: int, cycle_length: int = 28) -> CyclePhase:
    """
    Return the CyclePhase for a given 1-based cycle_day.

    Days beyond 28 (for longer cycles) are mapped to the final phase.
    """
    # Clamp to cycle_length then map into 1-28 range
    day = max(1, min(cycle_day, cycle_length))
    # Scale if cycle is non-standard length
    if cycle_length != 28:
        # Map proportionally: e.g. day 30 of 30 → day 28 of 28
        scaled = round(day / cycle_length * 28)
        day = max(1, min(scaled, 28))
    return _DAY_TO_PHASE.get(day, CYCLE_PHASES[-1])


# ---------------------------------------------------------------------------
# MenstrualCycleState — per-character runtime
# ---------------------------------------------------------------------------


@dataclass
class MenstrualCycleState:
    """
    Tracks the menstrual cycle for one female character.

    Stored in MenstrualCycleSystem._registry and attached to
    EmotionalEngine as ``cycle_state`` by engine.py.
    """

    character_id: str

    # Current position in the cycle (1-based day number)
    cycle_day: int = 1

    # Total cycle length — slight individual variation (25–32 days)
    cycle_length: int = 28

    # Individual sensitivity: 0.0 = system average, 0.20 = strongly affected
    sensitivity: float = 0.10

    # Whether this character is in a pre-menopausal state
    is_premenopausal: bool = True

    # Whether this character is in a menstruating-age range
    is_menstruating_age: bool = True

    # Track total days elapsed for diary/history
    total_days_elapsed: int = 0

    _history: List[Dict[str, Any]] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Core accessors
    # ------------------------------------------------------------------

    def current_phase(self) -> CyclePhase:
        """Return the CyclePhase active on the current cycle_day."""
        return phase_for_day(self.cycle_day, self.cycle_length)

    def emotion_multiplier(self, channel: str) -> float:
        """
        Return the combined cycle multiplier for an emotion channel.

        Applies individual sensitivity on top of the phase table value:
          multiplier = phase_base + (phase_base - 1.0) * sensitivity
        This means sensitivity 0 → phase table is used as-is.
        """
        base = self.current_phase().get_emotion_multiplier(channel)
        # Amplify deviation from neutral (1.0) by sensitivity
        delta = (base - 1.0) * (1.0 + self.sensitivity)
        return max(0.5, min(2.0, 1.0 + delta))

    def energy_delta(self) -> float:
        """Additive modifier to EmotionalProfile.baseline_intensity."""
        base = self.current_phase().energy_modifier
        return base * (1.0 + self.sensitivity)

    def behavior_bias(self) -> Dict[str, float]:
        """
        Return a copy of the current phase's behavior weight deltas,
        scaled by individual sensitivity.
        """
        raw = self.current_phase().behavior_bias
        return {k: round(v * (1.0 + self.sensitivity), 3) for k, v in raw.items()}

    def to_prompt_string(self) -> str:
        """
        One-line cycle annotation for the narrator prompt.
        E.g.: "Cycle Day 14 — Ovulation (peak energy, bold, exploratory)"
        """
        ph = self.current_phase()
        return (
            f"Cycle Day {self.cycle_day} — {ph.name}"
            f"{': ' + ph.narrative_hint if ph.narrative_hint else ''}"
        )

    # ------------------------------------------------------------------
    # Turn tick
    # ------------------------------------------------------------------

    def tick(self, days: int = 1) -> bool:
        """
        Advance cycle by ``days``.
        Returns True if the cycle has restarted (new period started).
        """
        restarted = False
        for _ in range(days):
            self.cycle_day += 1
            self.total_days_elapsed += 1
            if self.cycle_day > self.cycle_length:
                self.cycle_day = 1
                restarted = True
                self._history.append({"cycle_complete_at_day": self.total_days_elapsed})
                self._history = self._history[-12:]
        return restarted

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        ph = self.current_phase()
        return {
            "character_id": self.character_id,
            "cycle_day": self.cycle_day,
            "cycle_length": self.cycle_length,
            "sensitivity": self.sensitivity,
            "is_premenopausal": self.is_premenopausal,
            "is_menstruating_age": self.is_menstruating_age,
            "total_days_elapsed": self.total_days_elapsed,
            "current_phase": ph.name,
            "phase_number": ph.phase,
            "narrative_hint": ph.narrative_hint,
            "energy_delta": round(self.energy_delta(), 3),
        }

    @classmethod
    def from_character(
        cls,
        char_id: str,
        char_data: Dict[str, Any],
        randomise_start: bool = True,
        min_age_menstruating: int = 13,
        max_age_premenopausal: int = 50,
    ) -> "MenstrualCycleState":
        """
        Construct a MenstrualCycleState from a character YAML dict.
        Uses the ``menstrual_cycle`` block if present.
        """
        mc_block = char_data.get("menstrual_cycle") or {}
        cycle_length = int(mc_block.get("cycle_length", random.randint(25, 32)))
        if "cycle_day" in mc_block:
            cycle_day = int(mc_block["cycle_day"])
        elif randomise_start:
            cycle_day = random.randint(1, cycle_length)
        else:
            cycle_day = 1

        sensitivity = float(mc_block.get("sensitivity", 0.10))

        # Determine pre-menopausal status
        age = char_data.get("identity", {}).get("age") or char_data.get("age")
        is_menstruating_age = age is None or int(age) >= min_age_menstruating
        is_premenopausal = age is None or int(age) < max_age_premenopausal

        return cls(
            character_id=char_id,
            cycle_day=max(1, min(cycle_day, cycle_length)),
            cycle_length=cycle_length,
            sensitivity=sensitivity,
            is_premenopausal=is_premenopausal,
            is_menstruating_age=is_menstruating_age,
        )


# ---------------------------------------------------------------------------
# MenstrualCycleSystem — registry (mirrors StressSystem)
# ---------------------------------------------------------------------------


class MenstrualCycleSystem:
    """
    Registry that manages one MenstrualCycleState per applicable character.

    Applicable = gender == 'female' AND is_premenopausal AND not pregnant.

    Called from engine.py:
        menstrual_cycle_system.tick_all(days_elapsed=1)
        menstrual_cycle_system.get_or_create(char_id, char_data)
    """

    def __init__(
        self,
        randomise_start: bool = True,
        min_age_menstruating: int = 13,
        max_age_premenopausal: int = 50,
    ):
        self._registry: Dict[str, MenstrualCycleState] = {}
        self.randomise_start = randomise_start
        self.min_age_menstruating = min_age_menstruating
        self.max_age_premenopausal = max_age_premenopausal
        logger.info("MenstrualCycleSystem initialised.")

    # ------------------------------------------------------------------
    # Applicability guard
    # ------------------------------------------------------------------

    @staticmethod
    def is_applicable(
        char_data: Dict[str, Any],
        min_age: int = 13,
        max_age: int = 50,
    ) -> bool:
        """
        Return True if this character should have an active cycle state.

        Rules:
          * gender == 'female'  (identity.gender or top-level gender)
          * min_age <= age < max_age  (None age → assume applicable)
          * not pregnant        (status 'pregnant' check)
        """
        gender = (
            char_data.get("identity", {}).get("gender", "")
            or char_data.get("gender", "")
        ).lower()
        if gender not in {"female", "woman"}:
            return False

        age = char_data.get("identity", {}).get("age") or char_data.get("age")
        if age is not None and int(age) < min_age:
            return False

        if age is not None and int(age) >= max_age:
            return False

        # Skip pregnant characters
        status = (
            char_data.get("status", "")
            or char_data.get("identity", {}).get("status", "")
        ).lower()
        if "pregnant" in status or str(char_data.get("pregnant", "")).lower() in {
            "true",
            "1",
            "yes",
        }:
            return False

        return True

    # ------------------------------------------------------------------
    # Registry access
    # ------------------------------------------------------------------

    def get_or_create(
        self,
        char_id: str,
        char_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[MenstrualCycleState]:
        """
        Return existing state, create from char_data, or return None
        if character is not applicable.
        """
        if char_id in self._registry:
            return self._registry[char_id]

        if char_data is None:
            return None

        if not self.is_applicable(
            char_data,
            min_age=self.min_age_menstruating,
            max_age=self.max_age_premenopausal,
        ):
            return None

        state = MenstrualCycleState.from_character(
            char_id,
            char_data,
            self.randomise_start,
            min_age_menstruating=self.min_age_menstruating,
            max_age_premenopausal=self.max_age_premenopausal,
        )
        self._registry[char_id] = state
        logger.debug(
            "MenstrualCycle created for '%s': day %d/%d, phase=%s, sensitivity=%.2f",
            char_id,
            state.cycle_day,
            state.cycle_length,
            state.current_phase().name,
            state.sensitivity,
        )
        return state

    def get(self, char_id: str) -> Optional[MenstrualCycleState]:
        """Return existing state or None."""
        return self._registry.get(char_id)

    # ------------------------------------------------------------------
    # Turn tick
    # ------------------------------------------------------------------

    def tick_all(self, days: int = 1) -> None:
        """Advance every active cycle state by ``days``."""
        for char_id, state in self._registry.items():
            restarted = state.tick(days)
            if restarted:
                logger.debug(
                    "MenstrualCycle restarted for '%s' (day %d of %d)",
                    char_id,
                    state.cycle_day,
                    state.cycle_length,
                )

    # ------------------------------------------------------------------
    # Snapshot for debug API
    # ------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        """Return a JSON-safe snapshot of all active cycle states."""
        return {char_id: state.to_dict() for char_id, state in self._registry.items()}
