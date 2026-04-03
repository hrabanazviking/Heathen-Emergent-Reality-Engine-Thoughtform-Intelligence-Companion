import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List

from .event_dispatcher import get_global_dispatcher, EventType

logger = logging.getLogger(__name__)


@dataclass
class RelationshipLedger:
    """Formal social ledger tracking an NPC's stance toward the player."""

    npc_id: str
    player_id: str = "player"
    trust: float = 0.0
    fear: float = 0.0
    respect: float = 0.0
    familiarity: float = 0.0
    obligation: float = 0.0
    grievance: float = 0.0
    ideological_alignment: float = 0.0
    utility_dependency: float = 0.0
    perceived_reciprocity: float = 0.0
    volatility: float = 0.0
    momentum: float = 0.0
    interactions: int = 0
    last_event: str = ""
    social_label: str = "unknown"
    entries: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trust": self.trust,
            "fear": self.fear,
            "respect": self.respect,
            "familiarity": self.familiarity,
            "obligation": self.obligation,
            "grievance": self.grievance,
            "ideological_alignment": self.ideological_alignment,
            "utility_dependency": self.utility_dependency,
            "perceived_reciprocity": self.perceived_reciprocity,
            "volatility": self.volatility,
            "momentum": self.momentum,
            "interactions": self.interactions,
            "last_event": self.last_event,
            "social_label": self.social_label,
            "entries": self.entries,
        }


class RelationshipGraph:
    """
    Manages interpersonal bonds between NPCs and player (trust, fear, respect).
    Uses formal per-NPC ledgers that evolve from runtime events.
    """

    def __init__(self, engine=None, dispatcher=None):
        self.engine = engine
        self.dispatcher = dispatcher or get_global_dispatcher()
        # Bind event listeners
        self.dispatcher.subscribe(
            EventType.EMOTION_SPIKED.value, self._on_emotion_spiked
        )
        self.dispatcher.subscribe(EventType.PLAYER_ACTION.value, self._on_player_action)
        self.dispatcher.subscribe(EventType.AI_NARRATION.value, self._on_ai_narration)
        self.dispatcher.subscribe(EventType.OATH_SWORN.value, self._on_oath_sworn)
        self.dispatcher.subscribe(EventType.OATH_BROKEN.value, self._on_oath_broken)
        self.dispatcher.subscribe(EventType.BETRAYAL_DETECTED.value, self._on_betrayal)

    def _get_relationship(self, actor_id: str, target_id: str) -> Dict[str, Any]:
        """Fetch/create ledger-backed relationship metrics from world state."""
        if not self.engine or not hasattr(self.engine, "state"):
            return {}
        if not hasattr(self.engine.state, "relationships"):
            self.engine.state.relationships = {}

        rels = self.engine.state.relationships
        if actor_id not in rels:
            rels[actor_id] = {}
        if target_id not in rels[actor_id]:
            rels[actor_id][target_id] = RelationshipLedger(npc_id=actor_id).to_dict()
        return rels[actor_id][target_id]

    def _append_entry(
        self,
        actor_id: str,
        target_id: str,
        event_name: str,
        deltas: Dict[str, float],
        note: str,
    ) -> None:
        """Muninn inscribes every social shift in a formal ledger trail."""
        bond = self._get_relationship(actor_id, target_id)
        if not bond:
            return
        entries = bond.setdefault("entries", [])
        turn = int(getattr(getattr(self.engine, "state", None), "turn_count", 0))
        entries.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "turn": turn,
                "event": event_name,
                "deltas": deltas,
                "note": note,
            }
        )
        # Huginn keeps the short saga sharp for prompt budgets.
        if len(entries) > 60:
            del entries[:-60]

    def _relationship_stance_multiplier(self, actor_id: str) -> float:
        """Read actor personality and derive social responsiveness multiplier."""
        if not self.engine or not hasattr(self.engine, "state"):
            return 1.0
        npcs = getattr(self.engine.state, "npcs_present", [])
        actor = next((n for n in npcs if isinstance(n, dict) and n.get("id") == actor_id), None)
        if not actor:
            return 1.0
        personality = str(actor.get("personality", "")).lower()
        if any(flag in personality for flag in ["loyal", "warm", "devoted"]):
            return 1.15
        if any(flag in personality for flag in ["suspicious", "paranoid", "cold"]):
            return 0.85
        return 1.0

    def _action_intensity_multiplier(self, action: str) -> float:
        """Heavier words and deeds carve deeper social runes."""
        severe_words = ["swear", "oath", "betray", "kill", "save", "sacrifice"]
        if any(word in action for word in severe_words):
            return 1.5
        if len(action.split()) > 12:
            return 1.2
        return 1.0

    def _refresh_social_state(self, actor_id: str, target_id: str, event_name: str) -> None:
        """Muninn recomputes higher-order social signals after each event."""
        bond = self._get_relationship(actor_id, target_id)
        if not bond:
            return

        trust = float(bond.get("trust", 0.0))
        fear = float(bond.get("fear", 0.0))
        respect = float(bond.get("respect", 0.0))
        familiarity = float(bond.get("familiarity", 0.0))
        grievance = float(bond.get("grievance", 0.0))
        ideological_alignment = float(bond.get("ideological_alignment", 0.0))
        utility_dependency = float(bond.get("utility_dependency", 0.0))

        # Urd's braid: recurrent contact tempers fear and sharpens identity.
        bond["familiarity"] = max(0.0, min(1.0, familiarity + 0.03))
        familiarity = float(bond.get("familiarity", 0.0))
        bond["interactions"] = int(bond.get("interactions", 0)) + 1
        bond["last_event"] = event_name
        bond["volatility"] = round(min(1.0, (abs(trust) + abs(fear) + abs(respect)) / 3.0), 3)
        bond["momentum"] = round(max(-1.0, min(1.0, trust + respect - grievance - fear)), 3)
        # Muninn tracks asymmetric perception: what actor *believes* player stance is.
        bond["perceived_reciprocity"] = round(
            max(-1.0, min(1.0, (trust + ideological_alignment + utility_dependency - grievance) / 2.2)),
            3,
        )

        if trust >= 0.65 and respect >= 0.45 and fear < 0.2:
            label = "sworn_ally"
        elif trust >= 0.3 and grievance < 0.35 and ideological_alignment >= -0.2:
            label = "friend"
        elif grievance >= 0.65 or (fear >= 0.45 and trust < 0.0):
            label = "enemy"
        elif fear >= 0.5 and respect > 0.2:
            label = "intimidated_vassal"
        elif ideological_alignment >= 0.45 and trust < 0.2:
            label = "ideological_ally"
        elif utility_dependency >= 0.55 and trust < 0.25:
            label = "transactional_ally"
        elif familiarity >= 0.4:
            label = "known_acquaintance"
        else:
            label = "unknown"
        bond["social_label"] = label

    def _derive_secondary_deltas(self, deltas: Dict[str, float]) -> Dict[str, float]:
        """Map primary emotional shifts to richer social dynamics."""
        enriched: Dict[str, float] = dict(deltas)
        trust_delta = float(deltas.get("trust", 0.0))
        fear_delta = float(deltas.get("fear", 0.0))
        respect_delta = float(deltas.get("respect", 0.0))

        if trust_delta > 0:
            enriched["obligation"] = enriched.get("obligation", 0.0) + (trust_delta * 0.3)
            enriched["grievance"] = enriched.get("grievance", 0.0) - (trust_delta * 0.2)
        if trust_delta < 0:
            enriched["grievance"] = enriched.get("grievance", 0.0) + abs(trust_delta) * 0.4
        if fear_delta > 0:
            enriched["grievance"] = enriched.get("grievance", 0.0) + fear_delta * 0.2
        if respect_delta > 0:
            enriched["obligation"] = enriched.get("obligation", 0.0) + respect_delta * 0.25
            enriched["ideological_alignment"] = enriched.get("ideological_alignment", 0.0) + respect_delta * 0.2
        if fear_delta > 0 and trust_delta < 0:
            enriched["utility_dependency"] = enriched.get("utility_dependency", 0.0) + fear_delta * 0.35
        if trust_delta > 0:
            enriched["utility_dependency"] = enriched.get("utility_dependency", 0.0) + trust_delta * 0.15
        return enriched

    def _apply_reciprocity_echo(
        self,
        actor_id: str,
        target_id: str,
        event_name: str,
        deltas: Dict[str, float],
    ) -> None:
        """Frigg's mirror: strong actions create a weaker reciprocal shadow."""
        if target_id != "player" or actor_id == "player":
            return
        reciprocal = {k: round(v * 0.35, 4) for k, v in deltas.items() if k in {"trust", "fear", "respect"}}
        if not reciprocal:
            return
        self._apply_deltas(
            actor_id="player",
            target_id=actor_id,
            event_name=f"{event_name}:reciprocity",
            deltas=reciprocal,
            note=f"Reciprocity echo from {actor_id}'s stance shift.",
            include_reciprocity=False,
        )

    def _update_bond(self, actor_id: str, target_id: str, metric: str, amount: float):
        """Update one ledger metric and clamp within saga-scale bounds."""
        bond = self._get_relationship(actor_id, target_id)
        if not bond:
            return
        current = bond.get(metric, 0.0)

        if metric in {"familiarity", "obligation", "grievance", "volatility"}:
            bond[metric] = max(0.0, min(1.0, current + amount))
        elif metric == "interactions":
            bond[metric] = max(0, int(current) + int(amount))
        else:
            # Clamp between -1.0 (extreme negative) and 1.0 (extreme positive)
            bond[metric] = max(-1.0, min(1.0, current + amount))

        logger.debug(
            f"[RELATIONSHIP] {actor_id} -> {target_id} | {metric} adjusted by {amount:+.2f} (now {bond[metric]:.2f})"
        )

        # Dispatch event if a significant shift occurs
        if abs(bond[metric]) >= 0.8 and abs(current) < 0.8:
            self.dispatcher.dispatch(
                EventType.RELATIONSHIP_CHANGED.value,
                {
                    "actor": actor_id,
                    "target": target_id,
                    "metric": metric,
                    "value": bond[metric],
                },
            )

    def _apply_deltas(
        self,
        actor_id: str,
        target_id: str,
        event_name: str,
        deltas: Dict[str, float],
        note: str,
        include_reciprocity: bool = True,
    ) -> None:
        """Apply a batch of metric updates and write one formal ledger row."""
        if not deltas:
            return
        enriched = self._derive_secondary_deltas(deltas)
        for metric, amount in enriched.items():
            self._update_bond(actor_id, target_id, metric, amount)
        self._refresh_social_state(actor_id, target_id, event_name)
        self._append_entry(actor_id, target_id, event_name, enriched, note)
        if include_reciprocity:
            self._apply_reciprocity_echo(actor_id, target_id, event_name, enriched)

    def _on_emotion_spiked(self, event_type: str, context: Dict[str, Any]):
        """When someone's emotion spikes, trace it back to shift relationships."""
        try:
            actor_id = context.get("character_id")
            emotion = str(context.get("emotion", "")).lower().strip()
            impact = float(context.get("impact", 0.0) or 0.0)
            target_id = context.get("target", "player")

            if not self.engine or not actor_id or actor_id == target_id:
                return

            if emotion == "anger":
                self._apply_deltas(
                    actor_id,
                    target_id,
                    event_name=event_type,
                    deltas={"trust": -impact * 0.5, "respect": -impact * 0.2},
                    note="Anger hardens the bond against the target.",
                )
            elif emotion == "fear":
                self._apply_deltas(
                    actor_id,
                    target_id,
                    event_name=event_type,
                    deltas={"fear": impact * 0.8, "trust": -impact * 0.3},
                    note="Fear grows while trust frays.",
                )
            elif emotion == "joy":
                self._apply_deltas(
                    actor_id,
                    target_id,
                    event_name=event_type,
                    deltas={"trust": impact * 0.5, "respect": impact * 0.2},
                    note="Joy strengthens kin-feeling and esteem.",
                )
        except Exception as exc:
            logger.warning("Relationship emotion event skipped: %s", exc)

    def _on_player_action(self, event_type: str, context: Dict[str, Any]):
        """Interpret social actions into trust/fear/respect ledger updates."""
        try:
            action = str(context.get("action", "")).lower()
            npcs = context.get("characters_involved", [])

            if not self.engine or not npcs:
                return

            action_to_delta = [
                (["bow", "kneel", "praise", "honor", "salute"], {"respect": 0.12, "ideological_alignment": 0.04}),
                (["help", "save", "protect", "heal", "gift"], {"trust": 0.14, "respect": 0.08, "utility_dependency": 0.06}),
                (["trade", "barter", "hire", "payment", "coin"], {"utility_dependency": 0.12}),
                (["threaten", "intimidate", "coerce", "blackmail"], {"fear": 0.18, "trust": -0.1, "utility_dependency": 0.08}),
                (["lie", "deceive", "trick", "betray"], {"trust": -0.22, "respect": -0.08, "ideological_alignment": -0.08}),
                (["insult", "mock", "humiliate", "spit"], {"respect": -0.2, "trust": -0.1, "ideological_alignment": -0.06}),
                (["faith", "clan", "ancestral", "oath", "tradition"], {"ideological_alignment": 0.1}),
            ]

            matched_deltas: Dict[str, float] = {}
            for keywords, deltas in action_to_delta:
                if any(word in action for word in keywords):
                    for metric, amount in deltas.items():
                        matched_deltas[metric] = matched_deltas.get(metric, 0.0) + amount

            if not matched_deltas:
                return

            for npc_id in npcs:
                if not npc_id:
                    continue
                personality_scale = self._relationship_stance_multiplier(str(npc_id))
                intensity_scale = self._action_intensity_multiplier(action)
                scaled_deltas = {
                    metric: round(amount * personality_scale * intensity_scale, 4)
                    for metric, amount in matched_deltas.items()
                }
                self._apply_deltas(
                    actor_id=str(npc_id),
                    target_id="player",
                    event_name=event_type,
                    deltas=scaled_deltas,
                    note=f"Derived from player action: {action[:120]}",
                )
        except Exception as exc:
            logger.warning("Relationship player-action event skipped: %s", exc)

    def _on_ai_narration(self, event_type: str, context: Dict[str, Any]):
        """Refine ledgers from narrative outcomes after the turn resolves."""
        try:
            narrative = str(context.get("narrative", "")).lower()
            npcs = [
                c.get("id", "")
                for c in context.get("state", {}).get("npcs_present", [])
                if isinstance(c, dict)
            ]
            if not narrative or not npcs:
                return

            deltas: Dict[str, float] = {}
            if any(word in narrative for word in ["trusted", "grateful", "thankful", "oath kept"]):
                deltas["trust"] = deltas.get("trust", 0.0) + 0.08
            if any(word in narrative for word in ["cowered", "afraid", "terror", "feared"]):
                deltas["fear"] = deltas.get("fear", 0.0) + 0.1
            if any(word in narrative for word in ["honored", "saluted", "admired", "respected"]):
                deltas["respect"] = deltas.get("respect", 0.0) + 0.08

            if not deltas:
                return

            for npc_id in npcs:
                if npc_id:
                    self._apply_deltas(
                        actor_id=str(npc_id),
                        target_id="player",
                        event_name=event_type,
                        deltas=deltas,
                        note="Narrative consequence detected in AI output.",
                    )
        except Exception as exc:
            logger.warning("Relationship narration event skipped: %s", exc)

    def _on_oath_sworn(self, event_type: str, context: Dict[str, Any]):
        """Oaths sworn to the player build trust and respect."""
        npc_id = str(context.get("npc_id", "")).strip()
        if npc_id:
            self._apply_deltas(
                actor_id=npc_id,
                target_id="player",
                event_name=event_type,
                deltas={"trust": 0.2, "respect": 0.12},
                note="Oath sworn before witnesses.",
            )

    def _on_oath_broken(self, event_type: str, context: Dict[str, Any]):
        """Broken oaths crush trust and often raise fear."""
        npc_id = str(context.get("npc_id", "")).strip()
        if npc_id:
            self._apply_deltas(
                actor_id=npc_id,
                target_id="player",
                event_name=event_type,
                deltas={"trust": -0.35, "respect": -0.2, "fear": 0.06},
                note="Oath broken and kin-memory darkened.",
            )

    def _on_betrayal(self, event_type: str, context: Dict[str, Any]):
        """Handle severe trust violations."""
        betrayer = context.get("betrayer")
        victim = context.get("victim")

        if self.engine and betrayer and victim:
            self._apply_deltas(
                actor_id=str(victim),
                target_id=str(betrayer),
                event_name=event_type,
                deltas={"trust": -0.8, "fear": 0.3, "respect": -0.2},
                note="Betrayal event detected by fate threads.",
            )

    def decay_relationships(self, turns: int = 1) -> None:
        """Age old bonds naturally soften without fresh interaction."""
        try:
            if not self.engine or not hasattr(self.engine, "state"):
                return
            relationships = getattr(self.engine.state, "relationships", {})
            if not isinstance(relationships, dict):
                return
            turns = max(1, turns)
            decay_rate = min(0.12, 0.015 * turns)
            for actor_map in relationships.values():
                if not isinstance(actor_map, dict):
                    continue
                for bond in actor_map.values():
                    if not isinstance(bond, dict):
                        continue
                    for key in ("trust", "fear", "respect", "momentum"):
                        current = float(bond.get(key, 0.0))
                        bond[key] = round(current * (1.0 - decay_rate), 4)
                    for key in ("obligation", "grievance", "utility_dependency"):
                        current = float(bond.get(key, 0.0))
                        bond[key] = round(max(0.0, current * (1.0 - (decay_rate * 0.8))), 4)
                    current_alignment = float(bond.get("ideological_alignment", 0.0))
                    bond["ideological_alignment"] = round(current_alignment * (1.0 - (decay_rate * 0.5)), 4)
                    bond["familiarity"] = round(min(1.0, float(bond.get("familiarity", 0.0)) + 0.002 * turns), 4)
                    bond["volatility"] = round(
                        min(1.0, math.sqrt(abs(float(bond.get("trust", 0.0))) + abs(float(bond.get("fear", 0.0)))) / 1.5),
                        4,
                    )
        except Exception as exc:
            logger.warning("Relationship decay skipped: %s", exc)

    def get_relationship_snapshot(self, actor_id: str, target_id: str = "player") -> Dict[str, Any]:
        """Return a normalized social snapshot useful for prompts and UI."""
        bond = self._get_relationship(actor_id, target_id)
        if not bond:
            return {}
        return {
            "actor": actor_id,
            "target": target_id,
            "label": bond.get("social_label", "unknown"),
            "trust": round(float(bond.get("trust", 0.0)), 3),
            "fear": round(float(bond.get("fear", 0.0)), 3),
            "respect": round(float(bond.get("respect", 0.0)), 3),
            "familiarity": round(float(bond.get("familiarity", 0.0)), 3),
            "obligation": round(float(bond.get("obligation", 0.0)), 3),
            "grievance": round(float(bond.get("grievance", 0.0)), 3),
            "ideological_alignment": round(float(bond.get("ideological_alignment", 0.0)), 3),
            "utility_dependency": round(float(bond.get("utility_dependency", 0.0)), 3),
            "perceived_reciprocity": round(float(bond.get("perceived_reciprocity", 0.0)), 3),
            "momentum": round(float(bond.get("momentum", 0.0)), 3),
            "interactions": int(bond.get("interactions", 0)),
        }
