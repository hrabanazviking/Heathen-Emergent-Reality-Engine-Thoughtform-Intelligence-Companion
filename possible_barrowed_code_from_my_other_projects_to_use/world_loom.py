import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from systems.event_dispatcher import EventDispatcher, EventType

logger = logging.getLogger(__name__)

RuleValidator = Callable[[str, Dict[str, Any]], Dict[str, Any]]
WorldUpdater = Callable[[Dict[str, Any], Dict[str, Any]], None]


@dataclass
class WorldStateSnapshot:
    """The world loom keeps one authoritative snapshot for all subsystems."""

    characters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    locations: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    relationships: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    active_fate_threads: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    mythic_pressure: float = 0.0
    runic_resonance: Dict[str, float] = field(default_factory=dict)
    event_log: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SimulationEvent:
    """A standardized envelope for one event dispatched through the weave."""

    event_type: str
    action: str
    turn_number: int
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )


class WorldLoomPipeline:
    """Central event-driven turn pipeline for simulation-grade orchestration."""

    def __init__(
        self,
        dispatcher: Optional[EventDispatcher] = None,
        event_log_limit: int = 500,
    ):
        self.dispatcher = dispatcher
        self.state = WorldStateSnapshot()
        self._rule_validators: List[RuleValidator] = []
        self._world_updaters: List[WorldUpdater] = []
        self.event_log_limit = max(50, int(event_log_limit or 500))

    def register_rule_validator(self, validator: RuleValidator) -> None:
        self._rule_validators.append(validator)

    def register_world_updater(self, updater: WorldUpdater) -> None:
        self._world_updaters.append(updater)

    def mirror_runtime_state(self, runtime_state: Dict[str, Any]) -> None:
        """Huginn scouts runtime state, then braids it into one shared snapshot."""
        self.state.relationships = dict(runtime_state.get("relationships", {}))
        self.state.active_fate_threads = {
            f"thread_{idx}": {"summary": thread}
            for idx, thread in enumerate(runtime_state.get("fate_threads", []), 1)
        }
        self.state.mythic_pressure = float(runtime_state.get("mythic_pressure", 0.0))

    def _grade_spiritual_weight(self, action: str, context: Dict[str, Any]) -> float:
        """Skuld weighs deed gravity so omens can surface in narration."""
        score = 0.0
        lowered_action = (action or "").lower()
        if any(word in lowered_action for word in ("oath", "vow", "swear")):
            score += 0.35
        if any(word in lowered_action for word in ("betray", "murder", "sacrifice")):
            score += 0.5
        if bool(context.get("is_sacred_location", False)):
            score += 0.3
        return round(max(0.0, min(1.0, score)), 3)

    def _apply_resonance(self, context: Dict[str, Any], spiritual_weight: float) -> float:
        """Verðandi nudges local runes so heavy deeds stain the place."""
        location_id = str(context.get("location") or "unknown")
        current = float(self.state.runic_resonance.get(location_id, 0.0))
        delta = round(spiritual_weight * 0.2, 3)
        self.state.runic_resonance[location_id] = round(min(1.0, current + delta), 3)
        return delta

    def execute_turn(
        self,
        action: str,
        turn_number: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> SimulationEvent:
        """Run validation -> dispatch -> subsystem updates -> archival logging."""
        working_context = dict(context or {})
        for validator in self._rule_validators:
            try:
                validation_delta = validator(action, working_context)
                if validation_delta:
                    working_context.update(validation_delta)
            except Exception as exc:
                logger.warning("World loom validator skipped due to error: %s", exc)

        spiritual_weight = self._grade_spiritual_weight(action, working_context)
        working_context["spiritual_weight"] = spiritual_weight
        resonance_delta = self._apply_resonance(working_context, spiritual_weight)
        working_context["resonance_delta"] = resonance_delta

        event = SimulationEvent(
            event_type=EventType.PLAYER_ACTION.value,
            action=action,
            turn_number=turn_number,
            payload=working_context,
        )

        if self.dispatcher:
            try:
                self.dispatcher.dispatch(event.event_type, {"event": event, **working_context})
                if spiritual_weight >= 0.7:
                    self.dispatcher.dispatch(
                        EventType.RESONANCE_SPIKE.value,
                        {
                            "event": event,
                            "location": working_context.get("location", "unknown"),
                            "spiritual_weight": spiritual_weight,
                            "resonance_delta": resonance_delta,
                        },
                    )
            except Exception as exc:
                logger.warning("World loom dispatch skipped due to error: %s", exc)

        for updater in self._world_updaters:
            try:
                updater(self.state.__dict__, working_context)
            except Exception as exc:
                logger.warning("World loom updater skipped due to error: %s", exc)

        self.state.event_log.append(
            {
                "turn": turn_number,
                "event_type": event.event_type,
                "action": action,
                "created_at": event.created_at,
                "spiritual_weight": spiritual_weight,
                "resonance_delta": resonance_delta,
            }
        )
        if len(self.state.event_log) > self.event_log_limit:
            self.state.event_log = self.state.event_log[-self.event_log_limit :]
        return event
