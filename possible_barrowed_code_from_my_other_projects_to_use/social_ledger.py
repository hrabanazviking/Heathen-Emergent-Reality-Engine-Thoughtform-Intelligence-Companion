"""NPC social memory ledger with Gebo-informed event impacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml


@dataclass
class NpcLedger:
    npc_id: str
    honor_score: float = 0.0
    debt_score: float = 0.0
    reputation_score: float = 0.0
    events: List[Dict[str, Any]] = field(default_factory=list)


class SocialLedgerEngine:
    """Tracks long-horizon social consequences for present NPCs."""

    def __init__(self, data_path: str = "data") -> None:
        self.data_path = Path(data_path)
        raw = self._load_yaml("charts/social_ledger_events.yaml", {})
        self.impact_defaults = raw.get("impact_defaults", {}) if isinstance(raw, dict) else {}
        self.ledgers: Dict[str, NpcLedger] = {}

    def process_turn(self, action: str, response: str, npcs_present: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Muninn inscribes social debts and honors from the turn narrative."""
        lowered = f"{action} {response}".lower()
        event_types = self._infer_events(lowered)
        updated: List[str] = []

        for npc in npcs_present:
            if not isinstance(npc, dict):
                continue
            npc_id = str(npc.get("id") or npc.get("identity", {}).get("name", "")).strip()
            if not npc_id:
                continue
            ledger = self.ledgers.setdefault(npc_id, NpcLedger(npc_id=npc_id))
            if event_types:
                updated.append(npc_id)
            for evt in event_types:
                impact = float(self.impact_defaults.get(evt, 0.1))
                ledger.events.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "event": evt,
                        "impact": impact,
                    }
                )
                if evt in ("gift_given", "oath_kept", "debt_repaid"):
                    ledger.honor_score += max(0.0, impact)
                if evt in ("oath_broken", "insult_public"):
                    ledger.reputation_score += impact
                if evt in ("gift_received",):
                    ledger.debt_score += abs(impact)

        return {
            "updated_npcs": updated,
            "event_types": event_types,
            "ledger_count": len(self.ledgers),
        }

    def _infer_events(self, lowered_text: str) -> List[str]:
        inferred: List[str] = []
        if any(k in lowered_text for k in ["gift", "gave", "offered tribute"]):
            inferred.append("gift_given")
        if any(k in lowered_text for k in ["swore", "kept oath", "honored oath"]):
            inferred.append("oath_kept")
        if any(k in lowered_text for k in ["broke oath", "betray"]):
            inferred.append("oath_broken")
        if any(k in lowered_text for k in ["insult", "mocked", "shamed"]):
            inferred.append("insult_public")
        if any(k in lowered_text for k in ["repaid", "settled debt"]):
            inferred.append("debt_repaid")
        return inferred

    def _load_yaml(self, relative_path: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        path = self.data_path / relative_path
        if not path.exists():
            return fallback
        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or fallback
        return loaded if isinstance(loaded, dict) else fallback
