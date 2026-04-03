"""Freyja Patronage System.

Models the living patronage of Freyja, Vanadis and Mistress of Seiðr, over
characters who walk under her favour.  She rules love, desire, hope, beauty,
fertility, and the wisdom of the heart — but also the fallen: half of all
slain warriors ride to Fólkvangr before Óðinn claims his share.

Mechanical effects
──────────────────
  - Blessing:          Hamingja boost when no negative conditions press upon
                       the soul.  Emotional resonance seeded into the Hugr:
                       love, desire, hope.
  - Charm/domination:  Freyja's warmth grants advantage on saves against
                       charmed and frightened states.
  - Victory reward:    Achievement-keyed Hamingja gifts — social victories,
                       romantic connections, diplomatic resolutions, and
                       creative performances all reflect her domains.
  - Death grace:       When a character stands at the edge of death (unconscious
                       or dying), Freyja's grace slows the Hamingja drain from
                       -0.12 to -0.03, offering a hand across the threshold.

This module exposes a module-level singleton via ``get_freyja_patronage()``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-import sentinels
# ---------------------------------------------------------------------------

_ConditionsSystem: Any = None
_SoulLayer: Any = None


def _import_conditions_system() -> Any:
    """Lazy import of ConditionsSystem; returns None on failure."""
    global _ConditionsSystem
    if _ConditionsSystem is None:
        try:
            from systems.conditions_system import ConditionsSystem
            _ConditionsSystem = ConditionsSystem
        except Exception as exc:
            logger.warning("FreyjaPatronage: could not import ConditionsSystem: %s", exc)
    return _ConditionsSystem


def _import_soul_layer() -> Any:
    """Lazy import of SoulLayer; returns None on failure."""
    global _SoulLayer
    if _SoulLayer is None:
        try:
            from systems.soul_mechanics import SoulLayer
            _SoulLayer = SoulLayer
        except Exception as exc:
            logger.warning("FreyjaPatronage: could not import SoulLayer: %s", exc)
    return _SoulLayer


# ---------------------------------------------------------------------------
# Achievement type registry
# ---------------------------------------------------------------------------

#: Hamingja deltas keyed by achievement type (all within Freyja's domains).
ACHIEVEMENT_HAMINGJA: Dict[str, float] = {
    "social_victory": 0.05,
    "romantic_connection": 0.08,
    "diplomatic_resolution": 0.06,
    "creative_performance": 0.04,
}

#: Conditions that trigger Freyja's charm/save advantage.
CHARM_SAVE_CONDITIONS: frozenset[str] = frozenset({"charmed", "frightened"})

#: Conditions considered negative for the blessing check.
NEGATIVE_CONDITIONS: frozenset[str] = frozenset({
    "blinded",
    "charmed",
    "deafened",
    "exhaustion",
    "frightened",
    "grappled",
    "incapacitated",
    "paralyzed",
    "petrified",
    "poisoned",
    "prone",
    "restrained",
    "stunned",
    "unconscious",
})

#: Conditions that activate death grace.
DEATH_THRESHOLD_CONDITIONS: frozenset[str] = frozenset({"unconscious", "dying"})

#: Emotional resonance Freyja seeds into the Hugr each blessing tick.
BLESSING_EMOTIONS: Dict[str, float] = {
    "love": 0.12,
    "desire": 0.08,
    "hope": 0.10,
}

#: Hamingja boost from the standard blessing.
BLESSING_HAMINGJA_BOOST: float = 0.08

#: Normal Hamingja drain at death's edge (reduced from -0.12 by Freyja's grace).
DEATH_HAMINGJA_DRAIN_NORMAL: float = -0.12
#: Reduced Hamingja drain under Freyja's death grace.
DEATH_HAMINGJA_DRAIN_GRACE: float = -0.03


# ---------------------------------------------------------------------------
# Core class
# ---------------------------------------------------------------------------


class FreyjaPatronage:
    """Freyja's living influence over characters in her favour.

    All public methods accept duck-typed ``soul_layer`` objects that expose
    ``hugr.apply(emotion, delta, turn)`` and ``hamingja.shift(delta, reason)``
    interfaces matching ``SoulLayer`` from ``systems.soul_mechanics``.

    All operations are wrapped in try/except so a failure in patronage logic
    never interrupts the main saga turn.
    """

    def __init__(self) -> None:
        # Trigger lazy imports; cache results but do not fail on import error.
        _import_conditions_system()
        _import_soul_layer()
        logger.debug("FreyjaPatronage initialised.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply_blessing(
        self,
        soul_layer: Any,
        conditions: List[str],
        turn: int,
    ) -> bool:
        """Apply Freyja's blessing when no negative conditions are present.

        Grants a Hamingja boost of +0.08 and seeds love, desire, and hope into
        the Hugr.  Returns True if the blessing was applied, False otherwise.

        Args:
            soul_layer: A ``SoulLayer`` instance (or compatible duck-type).
            conditions:  Current active condition names (lowercase strings).
            turn:        The current game turn number.

        Returns:
            True if the blessing fired; False if blocked by conditions or error.
        """
        try:
            active = {c.lower() for c in (conditions or [])}
            if active & NEGATIVE_CONDITIONS:
                logger.debug(
                    "FreyjaPatronage: blessing suppressed (negative conditions: %s).",
                    active & NEGATIVE_CONDITIONS,
                )
                return False

            # Hamingja boost
            soul_layer.hamingja.shift(
                BLESSING_HAMINGJA_BOOST,
                "Freyja's blessing — heart clear of shadow",
            )

            # Emotional resonance into Hugr
            for emotion, delta in BLESSING_EMOTIONS.items():
                soul_layer.hugr.apply(emotion, delta, turn)

            logger.debug(
                "FreyjaPatronage: blessing applied at turn %d "
                "(hamingja +%.2f, emotions: %s).",
                turn,
                BLESSING_HAMINGJA_BOOST,
                list(BLESSING_EMOTIONS.keys()),
            )
            return True

        except Exception as exc:
            logger.error("FreyjaPatronage.apply_blessing failed: %s", exc)
            return False

    def check_charm_save_advantage(self, conditions: List[str]) -> bool:
        """Return True if Freyja's blessing grants advantage on a charm/domination save.

        Advantage is granted when the character is afflicted by ``charmed`` or
        ``frightened`` — Freyja's warmth steadies the heart against such snares.

        Args:
            conditions: Current active condition names (lowercase strings).

        Returns:
            True if advantage applies, False otherwise.
        """
        try:
            active = {c.lower() for c in (conditions or [])}
            if active & CHARM_SAVE_CONDITIONS:
                logger.debug(
                    "FreyjaPatronage: charm-save advantage granted (matched: %s).",
                    active & CHARM_SAVE_CONDITIONS,
                )
                return True
            return False
        except Exception as exc:
            logger.error("FreyjaPatronage.check_charm_save_advantage failed: %s", exc)
            return False

    def roleplay_victory_reward(
        self,
        soul_layer: Any,
        achievement_type: str,
        turn: int,
    ) -> float:
        """Boost Hamingja for achievements within Freyja's domains.

        Recognised achievement types and their bonuses:

        ========================  ========
        achievement_type          delta
        ========================  ========
        ``social_victory``        +0.05
        ``romantic_connection``   +0.08
        ``diplomatic_resolution`` +0.06
        ``creative_performance``  +0.04
        ========================  ========

        Unknown types are silently ignored (delta = 0.0).

        Args:
            soul_layer:       A ``SoulLayer`` instance (or compatible duck-type).
            achievement_type: One of the keys listed above.
            turn:             The current game turn number.

        Returns:
            The Hamingja delta applied, or 0.0 if not recognised or on error.
        """
        try:
            key = (achievement_type or "").lower().strip()
            delta = ACHIEVEMENT_HAMINGJA.get(key, 0.0)
            if delta == 0.0:
                logger.debug(
                    "FreyjaPatronage: unrecognised achievement_type '%s'; no reward.",
                    achievement_type,
                )
                return 0.0

            soul_layer.hamingja.shift(
                delta,
                f"Freyja's victory gift — {key.replace('_', ' ')}",
            )
            logger.info(
                "FreyjaPatronage: victory reward '%s' applied at turn %d "
                "(hamingja +%.2f).",
                key,
                turn,
                delta,
            )
            return delta

        except Exception as exc:
            logger.error("FreyjaPatronage.roleplay_victory_reward failed: %s", exc)
            return 0.0

    def apply_death_grace(
        self,
        soul_layer: Any,
        conditions: List[str],
        turn: int,
    ) -> bool:
        """Reduce Hamingja drain when a character stands at death's threshold.

        Normally dying/unconscious states drain Hamingja by -0.12.  Freyja's
        grace reduces this to -0.03, holding the soul a little longer in the
        light.

        Args:
            soul_layer: A ``SoulLayer`` instance (or compatible duck-type).
            conditions: Current active condition names (lowercase strings).
            turn:       The current game turn number.

        Returns:
            True if death grace was applied, False if not applicable or on error.
        """
        try:
            active = {c.lower() for c in (conditions or [])}
            if not (active & DEATH_THRESHOLD_CONDITIONS):
                return False

            # Apply grace-reduced drain instead of normal drain
            soul_layer.hamingja.shift(
                DEATH_HAMINGJA_DRAIN_GRACE,
                "Freyja's death grace — soul held at the threshold",
            )
            logger.info(
                "FreyjaPatronage: death grace applied at turn %d "
                "(hamingja %.2f instead of %.2f; conditions: %s).",
                turn,
                DEATH_HAMINGJA_DRAIN_GRACE,
                DEATH_HAMINGJA_DRAIN_NORMAL,
                active & DEATH_THRESHOLD_CONDITIONS,
            )
            return True

        except Exception as exc:
            logger.error("FreyjaPatronage.apply_death_grace failed: %s", exc)
            return False

    def get_patronage_summary(self, soul_layer: Any) -> Dict[str, Any]:
        """Return a summary dict describing current patronage state.

        The returned dict always contains the three keys below even when
        soul_layer access fails (graceful degradation):

        - ``hamingja_label``   (str)  — e.g. ``"blessed"``, ``"favored"``
        - ``active_blessing``  (bool) — whether a blessing is nominally in effect
        - ``emotional_state``  (dict) — snapshot of the Hugr emotions (may be
                                        empty if Hugr is unavailable)

        Args:
            soul_layer: A ``SoulLayer`` instance (or compatible duck-type).

        Returns:
            Dict with keys ``hamingja_label``, ``active_blessing``,
            ``emotional_state``.
        """
        summary: Dict[str, Any] = {
            "hamingja_label": "unknown",
            "active_blessing": False,
            "emotional_state": {},
        }
        try:
            hamingja_label: str = soul_layer.hamingja.state_label
            summary["hamingja_label"] = hamingja_label
            summary["active_blessing"] = hamingja_label in ("blessed", "favored")
        except Exception as exc:
            logger.warning("FreyjaPatronage.get_patronage_summary: hamingja read failed: %s", exc)

        try:
            summary["emotional_state"] = dict(soul_layer.hugr.emotions)
        except Exception as exc:
            logger.warning("FreyjaPatronage.get_patronage_summary: hugr read failed: %s", exc)

        return summary


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_patronage_instance: Optional[FreyjaPatronage] = None


def get_freyja_patronage() -> FreyjaPatronage:
    """Return the module-level FreyjaPatronage singleton, creating it if needed.

    Returns:
        The shared ``FreyjaPatronage`` instance.
    """
    global _patronage_instance
    if _patronage_instance is None:
        try:
            _patronage_instance = FreyjaPatronage()
            logger.debug("FreyjaPatronage singleton created.")
        except Exception as exc:
            logger.error("FreyjaPatronage singleton creation failed: %s", exc)
            # Return a fresh instance on each call rather than a broken singleton
            return FreyjaPatronage()
    return _patronage_instance
