import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MetaphysicalTurnResult:
    """One turn of macro/micro metaphysical synchronization output."""

    turn: int
    location_id: str
    spiritual_weight: float
    cosmic_events: List[Dict[str, Any]] = field(default_factory=list)
    active_omens: List[str] = field(default_factory=list)
    ecosystem_order_score: Optional[float] = None


class MetaphysicalSyncEngine:
    """As above, so below: binds action gravity to cosmos, place, and psyche."""

    def sync_turn(
        self,
        *,
        turn: int,
        location_id: str,
        spiritual_weight: float,
        resonance_system: Any = None,
        ecosystem: Any = None,
        cosmic_cycle: Any = None,
        soul_registry: Any = None,
        dispatcher: Any = None,
    ) -> MetaphysicalTurnResult:
        location = str(location_id or "unknown")
        weight = max(0.0, min(1.0, float(spiritual_weight or 0.0)))
        result = MetaphysicalTurnResult(
            turn=int(turn),
            location_id=location,
            spiritual_weight=weight,
        )

        # Verðandi: local field shift based on present deed gravity.
        if resonance_system:
            try:
                resonance_system.apply_event(
                    location_id=location,
                    event_type="player_action",
                    turn=int(turn),
                    custom_weight=round(weight * 0.22, 4),
                )
            except Exception as exc:
                logger.warning("Metaphysical sync resonance step skipped: %s", exc)

        # Region-scale balance drifts toward chaos under heavy spiritual strain.
        if ecosystem:
            try:
                ecosystem.apply_pressure(
                    region_id=location,
                    delta=round(-(weight * 0.14), 4),
                    cause="turn_spiritual_weight",
                    turn=int(turn),
                )
                region = ecosystem.get_region(location)
                result.ecosystem_order_score = float(region.order_score)
            except Exception as exc:
                logger.warning("Metaphysical sync ecosystem step skipped: %s", exc)

        # Macro cycles influence micro states and surface omens.
        if cosmic_cycle:
            try:
                cosmic_events = cosmic_cycle.tick(
                    turn=int(turn),
                    soul_registry=soul_registry,
                    resonance_system=resonance_system,
                    dispatcher=dispatcher,
                )
                result.cosmic_events = list(cosmic_events or [])
                result.active_omens = list(cosmic_cycle.get_active_omens() or [])
            except Exception as exc:
                logger.warning("Metaphysical sync cosmic step skipped: %s", exc)

        return result
