"""NPC Companion intelligence layer for persistent, character-faithful interactions."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class NPCCompanionProfile:
    """Persistent social and behavioral scaffolding for one NPC."""

    npc_id: str
    name: str
    role: str
    personality_traits: List[str] = field(default_factory=list)
    psychology: List[str] = field(default_factory=list)
    astrology: str = ""
    motivations: List[str] = field(default_factory=list)
    likes: List[str] = field(default_factory=list)
    dislikes: List[str] = field(default_factory=list)
    speaking_style: str = ""
    appearance_anchor: str = ""
    outfit_anchor: str = ""
    private_channel: str = ""
    voice_tag: str = ""
    memory_log: List[Dict[str, Any]] = field(default_factory=list)


class NPCCompanionSystem:
    """Tracks per-NPC memory and builds context packets for robust continuity."""

    def __init__(self, memory_limit: int = 120):
        self.memory_limit = max(20, int(memory_limit))
        self._profiles: Dict[str, NPCCompanionProfile] = {}

    def to_dict(self) -> Dict[str, Any]:
        try:
            return {
                "memory_limit": self.memory_limit,
                "profiles": {
                    npc_id: {
                        "npc_id": profile.npc_id,
                        "name": profile.name,
                        "role": profile.role,
                        "personality_traits": profile.personality_traits,
                        "psychology": profile.psychology,
                        "astrology": profile.astrology,
                        "motivations": profile.motivations,
                        "likes": profile.likes,
                        "dislikes": profile.dislikes,
                        "speaking_style": profile.speaking_style,
                        "appearance_anchor": profile.appearance_anchor,
                        "outfit_anchor": profile.outfit_anchor,
                        "private_channel": profile.private_channel,
                        "voice_tag": profile.voice_tag,
                        "memory_log": profile.memory_log,
                    }
                    for npc_id, profile in self._profiles.items()
                },
            }
        except Exception:
            logger.warning("Companion state serialization failed.", exc_info=True)
            return {"memory_limit": self.memory_limit, "profiles": {}}

    def from_dict(self, payload: Dict[str, Any]) -> None:
        try:
            if not isinstance(payload, dict):
                return
            self.memory_limit = max(20, int(payload.get("memory_limit", self.memory_limit)))
            profiles = payload.get("profiles", {})
            if not isinstance(profiles, dict):
                return
            self._profiles = {}
            for npc_id, entry in profiles.items():
                if not isinstance(entry, dict):
                    continue
                self._profiles[str(npc_id)] = NPCCompanionProfile(
                    npc_id=str(entry.get("npc_id", npc_id)),
                    name=str(entry.get("name", "Unknown")),
                    role=str(entry.get("role", "person")),
                    personality_traits=list(entry.get("personality_traits", []) or []),
                    psychology=list(entry.get("psychology", []) or []),
                    astrology=str(entry.get("astrology", "")),
                    motivations=list(entry.get("motivations", []) or []),
                    likes=list(entry.get("likes", []) or []),
                    dislikes=list(entry.get("dislikes", []) or []),
                    speaking_style=str(entry.get("speaking_style", "")),
                    appearance_anchor=str(entry.get("appearance_anchor", "")),
                    outfit_anchor=str(entry.get("outfit_anchor", "")),
                    private_channel=str(entry.get("private_channel", "")),
                    voice_tag=str(entry.get("voice_tag", "")),
                    memory_log=list(entry.get("memory_log", []) or []),
                )
        except Exception:
            logger.warning("Companion state restore failed.", exc_info=True)

    def register_npcs(self, npcs_present: List[Dict[str, Any]]) -> None:
        """Muninn etches each soul-signature so future scenes stay faithful."""
        try:
            for npc in npcs_present or []:
                self._ensure_profile(npc)
        except Exception:
            logger.warning("NPC registration skipped.", exc_info=True)

    def record_turn(
        self,
        turn_number: int,
        player_input: str,
        ai_response: str,
        location: str,
        time_of_day: str,
        npcs_present: List[Dict[str, Any]],
    ) -> None:
        try:
            for npc in npcs_present or []:
                profile = self._ensure_profile(npc)
                if not profile:
                    continue
                profile.memory_log.append(
                    {
                        "turn": int(turn_number or 0),
                        "timestamp": datetime.now().isoformat(),
                        "location": str(location or "unknown"),
                        "time_of_day": str(time_of_day or "day"),
                        "player_input": str(player_input or "")[:320],
                        "scene_result": str(ai_response or "")[:500],
                    }
                )
                profile.memory_log = profile.memory_log[-self.memory_limit :]
        except Exception:
            logger.warning("Companion turn memory update failed.", exc_info=True)

    def get_scene_companion_payload(
        self,
        npcs_present: List[Dict[str, Any]],
        max_memories: int = 10,
    ) -> List[Dict[str, Any]]:
        try:
            payload: List[Dict[str, Any]] = []
            for npc in npcs_present or []:
                profile = self._ensure_profile(npc)
                if not profile:
                    continue
                payload.append(
                    {
                        "npc_id": profile.npc_id,
                        "name": profile.name,
                        "role": profile.role,
                        "voice_tag": profile.voice_tag,
                        "private_channel": profile.private_channel,
                        "motivations": profile.motivations[:4],
                        "likes": profile.likes[:4],
                        "dislikes": profile.dislikes[:4],
                        "astrology": profile.astrology,
                        "psychology": profile.psychology[:4],
                        "personality_traits": profile.personality_traits[:5],
                        "appearance_anchor": profile.appearance_anchor,
                        "outfit_anchor": profile.outfit_anchor,
                        "speaking_style": profile.speaking_style,
                        "memory_recall": profile.memory_log[-max(1, int(max_memories)) :],
                    }
                )
            return payload
        except Exception:
            logger.warning("Companion scene payload failed.", exc_info=True)
            return []

    def get_private_context(self, npc_lookup: str, max_memories: int = 12) -> str:
        try:
            profile = self._find_profile(npc_lookup)
            if not profile:
                return ""
            lines = [
                f"=== PRIVATE THREAD: {profile.name} ({profile.npc_id}) ===",
                f"Companion channel: {profile.private_channel}",
                f"Voice tag for TTS routing: {profile.voice_tag}",
            ]
            if profile.motivations:
                lines.append(f"Motivations: {', '.join(profile.motivations[:5])}")
            if profile.psychology:
                lines.append(f"Psychology: {', '.join(profile.psychology[:5])}")
            if profile.astrology:
                lines.append(f"Astrology influence: {profile.astrology}")
            for memory in profile.memory_log[-max(1, int(max_memories)) :]:
                lines.append(
                    f"- T{memory.get('turn', 0)} @ {memory.get('location', 'unknown')}: "
                    f"player='{memory.get('player_input', '')[:120]}'"
                )
            return "\n".join(lines)
        except Exception:
            logger.warning("Private companion context build failed.", exc_info=True)
            return ""

    @staticmethod
    def extract_tts_segments(narrative_text: str) -> List[Dict[str, str]]:
        """Parse optional scene tags to route NPC lines into separate voices."""
        try:
            segments: List[Dict[str, str]] = []
            for raw in (narrative_text or "").splitlines():
                line = raw.strip()
                if not line:
                    continue
                tagged = re.match(
                    r"^(NPC|ACT|NARRATOR)\[(?P<speaker>[^\]]+)\]\s*:\s*(?P<content>.+)$",
                    line,
                    re.IGNORECASE,
                )
                if tagged:
                    segments.append(
                        {
                            "kind": tagged.group(1).upper(),
                            "speaker": tagged.group("speaker").strip(),
                            "content": tagged.group("content").strip(),
                        }
                    )
                    continue
                segments.append(
                    {
                        "kind": "NARRATOR",
                        "speaker": "narrator",
                        "content": line,
                    }
                )
            return segments
        except Exception:
            logger.warning("TTS segment extraction failed.", exc_info=True)
            return []

    def _find_profile(self, npc_lookup: str) -> Optional[NPCCompanionProfile]:
        if not npc_lookup:
            return None
        key = str(npc_lookup).strip().lower()
        if key in self._profiles:
            return self._profiles[key]
        for profile in self._profiles.values():
            if profile.name.lower() == key:
                return profile
        return None

    def _ensure_profile(self, npc: Dict[str, Any]) -> Optional[NPCCompanionProfile]:
        try:
            if not isinstance(npc, dict):
                return None
            identity = npc.get("identity", {}) if isinstance(npc.get("identity", {}), dict) else {}
            npc_id = str(npc.get("id") or identity.get("id") or identity.get("name") or "unknown").strip().lower().replace(" ", "_")
            name = str(identity.get("name") or npc.get("name") or npc_id).strip()
            role = str(identity.get("role") or npc.get("role") or "person")

            existing = self._profiles.get(npc_id)
            if existing:
                return existing

            profile = NPCCompanionProfile(
                npc_id=npc_id,
                name=name,
                role=role,
                personality_traits=self._ensure_list(
                    self._pick(npc, "traits") or self._pick(npc, "personality_traits")
                ),
                psychology=self._ensure_list(
                    self._pick(npc, "psychological_profile")
                    or self._pick(npc, "psychology")
                ),
                astrology=str(
                    self._pick(npc, "astrology")
                    or self._pick(npc, "astrological_profile")
                    or ""
                ),
                motivations=self._ensure_list(
                    self._pick(npc, "motivations") or self._pick(npc, "goals")
                ),
                likes=self._ensure_list(self._pick(npc, "likes")),
                dislikes=self._ensure_list(self._pick(npc, "dislikes")),
                speaking_style=str(self._pick(npc, "speech_style") or ""),
                appearance_anchor=str(
                    self._pick(npc, "appearance") or self._pick(npc, "summary") or ""
                )[:220],
                outfit_anchor=str(self._pick(npc, "wearing") or self._pick(npc, "clothing") or "")[:220],
                private_channel=f"private::{npc_id}",
                voice_tag=f"voice::{npc_id}",
            )
            self._profiles[npc_id] = profile
            return profile
        except Exception:
            logger.warning("Profile creation failed.", exc_info=True)
            return None

    def _pick(self, data: Any, target: str) -> Any:
        if isinstance(data, dict):
            for key, value in data.items():
                if str(key).lower() == str(target).lower() and value not in (None, "", [], {}):
                    return value
            for value in data.values():
                found = self._pick(value, target)
                if found not in (None, "", [], {}):
                    return found
        elif isinstance(data, list):
            for value in data:
                found = self._pick(value, target)
                if found not in (None, "", [], {}):
                    return found
        return None

    @staticmethod
    def _ensure_list(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, dict):
            return [f"{k}: {v}" for k, v in value.items() if str(v).strip()]
        return [str(value).strip()]
