"""Deterministic turn trace and replay bundle persistence."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class TurnTraceBundle:
    """Serializable trace payload for one processed turn."""

    turn_id: int
    session_id: str
    timestamp_utc: str
    player_input: str
    context_ids: List[str]
    prompt_hash: str
    model_id: str
    temperature: float
    state_diff_hash: str
    state_before: Dict[str, Any]
    state_after: Dict[str, Any]
    state_intent: Dict[str, Any]


class TurnReplayService:
    """Stores replayable turn traces with redaction policy support."""

    def __init__(self, data_path: str = "data", diagnostics_dir: str = "diagnostics") -> None:
        self.data_path = Path(data_path)
        self.trace_path = Path(diagnostics_dir) / "turn_trace.jsonl"
        self.trace_path.parent.mkdir(parents=True, exist_ok=True)
        self.redaction_policy = self._load_yaml("charts/replay_redaction_policy.yaml", {})

    def record_turn(
        self,
        turn_id: int,
        session_id: str,
        player_input: str,
        context_ids: List[str],
        prompt_payload: str,
        model_id: str,
        temperature: float,
        state_before: Dict[str, Any],
        state_after: Dict[str, Any],
        state_intent: Optional[Dict[str, Any]] = None,
    ) -> TurnTraceBundle:
        """Huginn binds a deterministic trace bundle for diagnostics."""
        prompt_hash = self._hash_obj(prompt_payload)
        state_diff_hash = self._hash_obj({"before": state_before, "after": state_after})
        bundle = TurnTraceBundle(
            turn_id=turn_id,
            session_id=session_id,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            player_input=player_input,
            context_ids=context_ids,
            prompt_hash=prompt_hash,
            model_id=model_id,
            temperature=float(temperature),
            state_diff_hash=state_diff_hash,
            state_before=state_before,
            state_after=state_after,
            state_intent=state_intent or {},
        )
        self._append_jsonl(asdict(bundle))
        return bundle

    def load_turn(self, turn_id: int) -> Optional[Dict[str, Any]]:
        """Return redacted trace for requested turn."""
        if not self.trace_path.exists():
            return None
        selected: Optional[Dict[str, Any]] = None
        with self.trace_path.open("r", encoding="utf-8") as handle:
            for raw in handle:
                line = raw.strip()
                if not line:
                    continue
                payload = json.loads(line)
                if int(payload.get("turn_id", -1)) == int(turn_id):
                    selected = payload
        if not selected:
            return None
        return self._redact(selected)

    def _append_jsonl(self, payload: Dict[str, Any]) -> None:
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        with self.trace_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{serialized}\n")

    def _redact(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        redacted = dict(payload)
        for field in self.redaction_policy.get("redact_fields", []):
            if field in redacted:
                redacted[field] = "<redacted>"
        return redacted

    def _hash_obj(self, value: Any) -> str:
        body = json.dumps(value, sort_keys=True, default=str)
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def _load_yaml(self, relative_path: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        path = self.data_path / relative_path
        if not path.exists():
            return fallback
        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or fallback
        return loaded if isinstance(loaded, dict) else fallback
