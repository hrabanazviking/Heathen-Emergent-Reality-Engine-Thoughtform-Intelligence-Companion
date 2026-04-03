"""Witch lore synthesis system.

Builds culturally grounded witch packets for NPCs by sampling chart lore.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class WitchProfile:
    """Structured witch guidance for one NPC."""

    npc_id: str
    npc_name: str
    culture: str
    witch_type: str
    confidence: float
    lore_sources: List[str]
    action_guidance: List[str]
    spell_guidance: List[str]
    behavior_guidance: List[str]
    motivation_guidance: List[str]

    def to_payload(self) -> Dict[str, Any]:
        return {
            "npc_id": self.npc_id,
            "npc_name": self.npc_name,
            "culture": self.culture,
            "witch_type": self.witch_type,
            "confidence": self.confidence,
            "lore_sources": self.lore_sources,
            "actions": self.action_guidance,
            "spells": self.spell_guidance,
            "behaviors": self.behavior_guidance,
            "motivations": self.motivation_guidance,
        }


class WitchSystem:
    """Muninn gathers witch-lore threads to steer NPC spellcraft behavior."""

    _WITCH_TOKENS = (
        "witch",
        "völva",
        "volva",
        "seidr",
        "seiðr",
        "sorcerer",
        "seer",
        "oracle",
        "wise woman",
        "cunning",
        "galdr",
        "trolldom",
    )

    _CULTURE_TRADITIONS = {
        "norse": ("norse_seidr_volva", ["norse", "viking", "seidr", "seiðr", "völva"]),
        "norse_norwegian": (
            "norse_seidr_volva",
            ["norse", "norwegian", "viking", "seidr", "völva"],
        ),
        "norse_danish": ("norse_seidr_volva", ["norse", "danish", "viking", "seidr"]),
        "norse_swedish": (
            "norse_seidr_volva",
            ["norse", "swedish", "viking", "seidr", "galdr"],
        ),
        "irish": ("gaelic_banfeasa", ["irish", "gaelic", "wise woman", "herb"]),
        "slavic": ("slavic_vedma", ["slavic", "hedge", "curse", "spirit"]),
        "anglo_saxon": (
            "cunning_folk",
            ["anglo", "saxon", "cunning", "ward", "charm"],
        ),
        "frankish": ("cunning_folk", ["frank", "cunning", "charm", "ward"]),
        "byzantine": (
            "mystic_astrologer",
            ["byzantine", "astrology", "ritual", "omen"],
        ),
        "arabic": (
            "mystic_astrologer",
            ["arabic", "astrology", "ritual", "wisdom"],
        ),
    }

    _GUIDANCE_KEYWORDS = {
        "actions": [
            "ritual",
            "chant",
            "invoke",
            "offering",
            "bind",
            "divination",
            "trance",
            "omens",
            "ward",
            "curse",
            "blot",
        ],
        "spells": [
            "spell",
            "galdr",
            "rune",
            "runes",
            "seiðr",
            "seidr",
            "healing",
            "protection",
            "storm",
            "fate",
        ],
        "behaviors": [
            "speaks",
            "speech",
            "honor",
            "kin",
            "fear",
            "respected",
            "cryptic",
            "verse",
            "wyrd",
        ],
        "motivations": [
            "purpose",
            "duty",
            "oath",
            "protect",
            "guide",
            "fate",
            "community",
            "frith",
            "balance",
            "cost",
        ],
    }

    def __init__(self, data_path: str = "data"):
        self.data_path = Path(data_path)
        self._lore_sentences: List[Dict[str, str]] = []
        self._load_lore()

    def _load_lore(self) -> None:
        """Load witch-relevant lore from chart files."""
        lore_files = [
            self.data_path / "charts" / "ABOUT_THE_VIKING_ROLEPLAY.md",
            self.data_path / "charts" / "Viking_Culture_Master_README.md",
            self.data_path / "charts" / "viking_trolldom_the_ancient_northern_ways.yaml",
            self.data_path / "charts" / "Norse_Magick_Spells_and_Rituals.json",
            self.data_path / "charts" / "trolldom_and_magick_practices_in_norse_paganism_volume1.jsonl",
        ]
        gathered: List[Dict[str, str]] = []
        for lore_file in lore_files:
            try:
                if not lore_file.exists():
                    continue
                gathered.extend(self._extract_sentences(lore_file))
            except Exception as exc:
                logger.warning("Failed loading witch lore from %s: %s", lore_file, exc)

        self._lore_sentences = gathered

    def _extract_sentences(self, filepath: Path) -> List[Dict[str, str]]:
        suffix = filepath.suffix.lower()
        if suffix == ".md":
            text = filepath.read_text(encoding="utf-8", errors="ignore")
        elif suffix in {".yaml", ".yml"}:
            raw = yaml.safe_load(filepath.read_text(encoding="utf-8", errors="ignore"))
            text = json.dumps(raw, ensure_ascii=False)
        elif suffix == ".json":
            raw = json.loads(filepath.read_text(encoding="utf-8", errors="ignore"))
            text = json.dumps(raw, ensure_ascii=False)
        elif suffix == ".jsonl":
            chunks: List[str] = []
            for line in filepath.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    chunks.append(json.dumps(json.loads(line), ensure_ascii=False))
                except json.JSONDecodeError:
                    continue
            text = "\n".join(chunks)
        else:
            return []

        clean = re.sub(r"\s+", " ", text)
        parts = re.split(r"(?<=[.!?])\s+", clean)
        out: List[Dict[str, str]] = []
        for part in parts:
            sentence = part.strip().strip("\"'")
            if len(sentence) < 48:
                continue
            low = sentence.lower()
            if not any(token in low for token in self._WITCH_TOKENS):
                continue
            out.append({"source": str(filepath), "text": sentence})
        return out

    @staticmethod
    def _fuzzy_get(data: Any, target: str, default: Any = None) -> Any:
        if not data:
            return default
        target = target.lower()
        if isinstance(data, dict):
            for key, value in data.items():
                if str(key).lower() == target and value not in (None, "", [], {}):
                    return value
            for value in data.values():
                found = WitchSystem._fuzzy_get(value, target, None)
                if found not in (None, "", [], {}):
                    return found
        if isinstance(data, list):
            for item in data:
                found = WitchSystem._fuzzy_get(item, target, None)
                if found not in (None, "", [], {}):
                    return found
        return default

    def _witch_confidence(self, npc: Dict[str, Any]) -> float:
        id_blob = " ".join(
            str(item)
            for item in [
                self._fuzzy_get(npc, "role", ""),
                self._fuzzy_get(npc, "class", ""),
                self._fuzzy_get(npc, "subclass", ""),
                self._fuzzy_get(npc, "summary", ""),
                self._fuzzy_get(npc, "appearance", ""),
                self._fuzzy_get(npc, "title", ""),
                self._fuzzy_get(npc, "traits", ""),
            ]
        ).lower()
        score = 0.0
        for token in self._WITCH_TOKENS:
            if token in id_blob:
                score += 0.13
        if "druid" in id_blob or "sorcerer" in id_blob:
            score += 0.12
        if "cleric" in id_blob and "seer" in id_blob:
            score += 0.1
        return min(1.0, score)

    def _infer_tradition(self, culture: str) -> tuple[str, List[str]]:
        key = (culture or "").strip().lower()
        if key in self._CULTURE_TRADITIONS:
            return self._CULTURE_TRADITIONS[key]
        if "norse" in key or "viking" in key:
            return "norse_seidr_volva", ["norse", "viking", "seidr", "völva"]
        return "hedge_witch", [key or "local", "witch", "ritual"]

    def _collect_guidance(
        self,
        lore_pool: List[Dict[str, str]],
        keywords: List[str],
        limit: int = 3,
    ) -> List[str]:
        picked: List[str] = []
        for sentence in lore_pool:
            text = sentence.get("text", "").strip()
            low = text.lower()
            if not any(k in low for k in keywords):
                continue
            if text not in picked:
                picked.append(text)
            if len(picked) >= limit:
                break
        return picked

    def build_witch_profiles(self, npcs_present: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Build witch guidance payloads for all witch-like NPCs in scene."""
        payloads: List[Dict[str, Any]] = []
        for npc in npcs_present or []:
            try:
                if not isinstance(npc, dict):
                    continue
                confidence = self._witch_confidence(npc)
                if confidence < 0.22:
                    continue

                name = str(self._fuzzy_get(npc, "name", "Unknown")).strip()
                npc_id = str(self._fuzzy_get(npc, "id", name.lower().replace(" ", "_"))).strip()
                culture = str(self._fuzzy_get(npc, "culture", "unknown")).strip()
                witch_type, culture_aliases = self._infer_tradition(culture)

                lore_pool: List[Dict[str, str]] = []
                for row in self._lore_sentences:
                    text = row.get("text", "").lower()
                    if any(alias and alias in text for alias in culture_aliases):
                        lore_pool.append(row)
                if not lore_pool:
                    lore_pool = list(self._lore_sentences)

                profile = WitchProfile(
                    npc_id=npc_id,
                    npc_name=name,
                    culture=culture,
                    witch_type=witch_type,
                    confidence=round(confidence, 2),
                    lore_sources=sorted(
                        {Path(item.get("source", "")).name for item in lore_pool[:10] if item.get("source")}
                    ),
                    action_guidance=self._collect_guidance(
                        lore_pool=lore_pool,
                        keywords=self._GUIDANCE_KEYWORDS["actions"],
                    ),
                    spell_guidance=self._collect_guidance(
                        lore_pool=lore_pool,
                        keywords=self._GUIDANCE_KEYWORDS["spells"],
                    ),
                    behavior_guidance=self._collect_guidance(
                        lore_pool=lore_pool,
                        keywords=self._GUIDANCE_KEYWORDS["behaviors"],
                    ),
                    motivation_guidance=self._collect_guidance(
                        lore_pool=lore_pool,
                        keywords=self._GUIDANCE_KEYWORDS["motivations"],
                    ),
                )
                payloads.append(profile.to_payload())
            except Exception as exc:
                logger.warning("Witch profile generation failed for NPC: %s", exc)

        return payloads
