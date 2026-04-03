#!/usr/bin/env python3
"""
AI Prompt Builder
=================
Dynamically constructs prompts using all game data charts to influence AI behavior.

The prompt builder is the heart of the AI-driven experience. It weaves together:
- Norse Mystic GM Mindset (200 entries) - core personality
- Viking Values (200 entries) - cultural behavior filter
- Elder Futhark Runes (24) - mystical influences
- Symbolic Encounters (200) - encounter flavor
- Artifacts (200) - item significance
- Fate Twists (100) - narrative complications
- D&D 5E mechanics - combat and skills
- RAG System - retrieves relevant lore from all chart files
"""

import random
import csv
import importlib
import importlib.util
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    from systems.conditions_system import ConditionsSystem
    _CONDITIONS_SYSTEM_AVAILABLE = True
except ImportError:
    _CONDITIONS_SYSTEM_AVAILABLE = False

try:
    from systems.dnd_rules_engine import DndRulesEngine
    _RULES_ENGINE_AVAILABLE = True
except ImportError:
    _RULES_ENGINE_AVAILABLE = False

try:
    from systems.personality_engine import get_personality_ai_block, get_personality_compact_block
    _PERSONALITY_ENGINE_AVAILABLE = True
except ImportError:
    _PERSONALITY_ENGINE_AVAILABLE = False

    def get_personality_ai_block(*_a, **_kw) -> str:  # type: ignore[misc]
        return ""

    def get_personality_compact_block(*_a, **_kw) -> str:  # type: ignore[misc]
        return ""

# RAG System for chart data retrieval
try:
    from systems.rag_system import get_rag_system

    HAS_RAG = True
except ImportError:
    HAS_RAG = False
    logger.warning("RAG system not available")

# Yggdrasil Cognitive Architecture integration
HAS_YGGDRASIL = False
try:
    from yggdrasil.integration.norse_saga import NorseSagaCognition
    HAS_YGGDRASIL = True
except ImportError as _e:
    logger.warning("Yggdrasil NorseSagaCognition not available: %s", _e)
try:
    from yggdrasil.router import YggdrasilAIRouter, AICallType
    HAS_YGGDRASIL = True
except ImportError as _e:
    logger.warning("Yggdrasil router not available: %s", _e)


@dataclass
class GameContext:
    """Current game state for prompt building."""

    # Location
    current_location: str
    location_description: str
    location_type: str  # city, wilderness, dungeon, etc.

    # Sub-location (specific place within city)
    sub_location_name: str = ""
    sub_location_description: str = ""
    sub_location_atmosphere: str = ""

    # Time
    time_of_day: str = "morning"
    season: str = "summer"
    year: int = 850

    # Characters present
    player_character: Dict[str, Any] = None
    npcs_present: List[Dict[str, Any]] = None

    # Scene state
    in_combat: bool = False
    combat_state: Optional[Dict[str, Any]] = None

    # Active elements
    active_quests: List[Dict[str, Any]] = None
    pending_quests: List[Dict[str, Any]] = None
    recent_events: List[str] = None
    active_omens: List[str] = None

    # Oracle state
    chaos_factor: int = 30
    last_rune_drawn: Optional[str] = None

    # Yggdrasil Cognitive Architecture context
    yggdrasil_enabled: bool = False
    yggdrasil_context: Optional[Dict[str, Any]] = None
    active_worlds: List[str] = None
    raven_insights: Optional[Dict[str, Any]] = None
    cognitive_load: int = 0  # 0-100, how much Yggdrasil processing is active
    rag_context: str = ""  # Lore context injected by PromptBuilder
    # DAG Contextual Matrix payload
    dag_payload: Optional[Any] = None

    # Runtime integrations injected by engine
    emotional_engines: Optional[Dict[str, Any]] = None
    soul_registry: Optional[Any] = None
    stress_system: Optional[Any] = None
    menstrual_cycle_system: Optional[Any] = None

    # T3-B: identity drift notes — keyed by character_id, value is DriftVector.narrative_summary
    # Populated by engine.process_turn() when IdentityDriftChecker fires.
    identity_drift_notes: Optional[Dict[str, str]] = None

    # Turn hint for cache TTL calculations in PromptBuilder (set by engine)
    turn_count: int = 0


class PromptBuilder:
    """
    Builds AI prompts incorporating all game data charts.

    The builder layers information to create contextually appropriate prompts:
    1. Base personality from GM Mindset
    2. Cultural values filter
    3. Scene context
    4. Mechanical state
    5. Oracle/mystical influences
    6. RAG context from relevant chart data
    """

    # Class-level chart cache — keyed by resolved data_path string.
    # Avoids re-parsing 50+ YAML/JSON/CSV chart files on every instantiation.
    _charts_class_cache: dict = {}  # path_str -> charts dict
    _charts_class_mtime: dict = {}  # path_str -> charts dir mtime

    @classmethod
    def _get_cached_charts(cls, data_path: Path) -> dict:
        """Return chart data from class-level cache, rebuilding only when the charts dir changes."""
        charts_path = data_path / "charts"
        path_key = str(charts_path.resolve())
        try:
            current_mtime = charts_path.stat().st_mtime
        except OSError:
            current_mtime = 0.0
        if path_key in cls._charts_class_cache and cls._charts_class_mtime.get(path_key) == current_mtime:
            return cls._charts_class_cache[path_key]
        # Cache miss or directory changed — return sentinel so caller loads fresh
        return {}

    @classmethod
    def _store_cached_charts(cls, data_path: Path, charts: dict) -> None:
        """Store freshly loaded charts in the class-level cache."""
        charts_path = data_path / "charts"
        path_key = str(charts_path.resolve())
        try:
            current_mtime = charts_path.stat().st_mtime
        except OSError:
            current_mtime = 0.0
        cls._charts_class_cache[path_key] = charts
        cls._charts_class_mtime[path_key] = current_mtime

    @staticmethod
    def _summarize_emotion_profile(profile: Dict[str, Any]) -> str:
        """Render a short NPC emotional tendency summary from emotion_profile."""
        if not isinstance(profile, dict) or not profile:
            return ""

        tf_axis = float(profile.get("tf_axis", 0.5) or 0.5)
        threshold = float(profile.get("expression_threshold", 0.55) or 0.55)
        rumination = float(profile.get("rumination_bias", 0.3) or 0.3)
        baseline = float(profile.get("baseline_intensity", 1.0) or 1.0)

        if tf_axis >= 0.62:
            tf_desc = "feeling-leaning"
        elif tf_axis <= 0.38:
            tf_desc = "thinking-leaning"
        else:
            tf_desc = "balanced between feeling and reason"

        if threshold >= 0.65:
            express_desc = "guarded in outward expression"
        elif threshold <= 0.45:
            express_desc = "openly expressive"
        else:
            express_desc = "measured in expression"

        if rumination >= 0.55:
            rum_desc = "dwells on slights and omens"
        elif rumination <= 0.2:
            rum_desc = "releases burdens quickly"
        else:
            rum_desc = "carries emotions for a time"

        if baseline >= 1.2:
            baseline_desc = "highly reactive"
        elif baseline <= 0.85:
            baseline_desc = "steady-tempered"
        else:
            baseline_desc = "moderately reactive"

        return f"{tf_desc}; {express_desc}; {rum_desc}; {baseline_desc}."

    @staticmethod
    def _is_bondmaid_character(character: Dict[str, Any]) -> bool:
        """Return True when the character payload indicates a bondmaid role."""
        if not isinstance(character, dict):
            return False

        identity = character.get("identity", {})
        fields = [
            character.get("type", ""),
            character.get("role", ""),
            character.get("id", ""),
            identity.get("type", "") if isinstance(identity, dict) else "",
            identity.get("role", "") if isinstance(identity, dict) else "",
            identity.get("id", "") if isinstance(identity, dict) else "",
            identity.get("name", "") if isinstance(identity, dict) else "",
            character.get("name", ""),
        ]
        return any("bondmaid" in str(value).lower() for value in fields)

    def __init__(self, data_path: str = "data"):
        """
        Initialize prompt builder.

        Args:
            data_path: Path to data directory containing charts
        """
        self.data_path = Path(data_path)
        cached = self._get_cached_charts(self.data_path)
        if cached:
            self.charts = cached
            logger.debug("PromptBuilder: using cached charts (%d entries)", len(cached))
        else:
            self.charts = {}
            self._load_all_charts()
            self._store_cached_charts(self.data_path, self.charts)

        # Initialize RAG system for chart data retrieval
        self.rag_system = None
        if HAS_RAG:
            try:
                charts_path = str(self.data_path / "charts")
                self.rag_system = get_rag_system(charts_path)
                logger.info("RAG system singleton linked to prompt builder")
            except Exception as e:
                logger.warning(f"Failed to initialize RAG system: {e}")
                self.rag_system = None

        # Yggdrasil integration
        self.yggdrasil = None
        self.yggdrasil_router = None
        self.yggdrasil_enabled = HAS_YGGDRASIL

        if HAS_YGGDRASIL:
            logger.info("Yggdrasil cognitive architecture integration available")
        else:
            logger.warning(
                "Yggdrasil cognitive architecture not available - prompts will lack cognitive context"
            )

        # Ensure ai_prompts is loaded if it exists
        if "ai_prompts" not in self.charts:
            prompts_path = self.data_path / "charts" / "ai_prompts.yaml"
            if prompts_path.exists():
                self._load_yaml_chart(prompts_path)

        # SRD systems for combat context enrichment
        self._conditions_system: Optional[ConditionsSystem] = None
        if _CONDITIONS_SYSTEM_AVAILABLE:
            try:
                self._conditions_system = ConditionsSystem()
            except Exception as exc:
                logger.warning("PromptBuilder: ConditionsSystem unavailable: %s", exc)

        self._rules_engine: Optional[DndRulesEngine] = None
        if _RULES_ENGINE_AVAILABLE:
            try:
                self._rules_engine = DndRulesEngine()
            except Exception as exc:
                logger.warning("PromptBuilder: DndRulesEngine unavailable: %s", exc)

        # GAP-027: PersonalityEngine result cache — char_id → (turn_cached, result)
        self._personality_cache: Dict[str, tuple] = {}
        self._personality_cache_turn: int = 0  # updated externally or from context

    _PERSONALITY_CACHE_TTL = 20  # re-analyze at most once every 20 turns

    def _get_personality_ai_block_cached(
        self,
        char_id: str,
        char_data: Dict[str, Any],
        soul_layer: Optional[Any] = None,
        current_turn: int = 0,
    ) -> str:
        """Return cached full AI personality block string, refreshing every 20 turns (GAP-027)."""
        if not _PERSONALITY_ENGINE_AVAILABLE:
            return ""
        cached_turn, cached_block = self._personality_cache.get(char_id, (-1, None))
        if cached_block is not None and (current_turn - cached_turn) < self._PERSONALITY_CACHE_TTL:
            return cached_block
        try:
            block = get_personality_ai_block(char_data, soul_layer=soul_layer)
            self._personality_cache[char_id] = (current_turn, block)
            return block
        except Exception as exc:
            logger.debug("PersonalityEngine block failed for %s: %s", char_id, exc)
            return ""

    def _get_personality_compact_cached(
        self,
        char_id: str,
        char_data: Dict[str, Any],
        current_turn: int = 0,
    ) -> str:
        """Return cached compact personality block, refreshing every 20 turns (GAP-027)."""
        if not _PERSONALITY_ENGINE_AVAILABLE:
            return ""
        _compact_key = f"{char_id}__compact"
        cached_turn, cached_block = self._personality_cache.get(_compact_key, (-1, None))
        if cached_block is not None and (current_turn - cached_turn) < self._PERSONALITY_CACHE_TTL:
            return cached_block
        try:
            block = get_personality_compact_block(char_data)
            self._personality_cache[_compact_key] = (current_turn, block)
            return block
        except Exception as exc:
            logger.debug("PersonalityEngine compact failed for %s: %s", char_id, exc)
            return ""

    def _load_all_charts(self):
        """
        Load all chart data files from the charts directory.

        Auto-discovers all supported files:
        - YAML (.yaml, .yml) - structured data
        - JSON (.json) - structured data
        - JSONL (.jsonl) - one object per line
        - CSV/CVS (.csv, .cvs) - tabular data
        - Text/Markup (.txt, .md, .html, .htm, .xml) - line-based entries
        - PDF (.pdf) - extracted page text entries

        Standard charts (loaded by specific name):
        - gm_mindset.yaml - GM personality principles
        - viking_values.yaml - Cultural values for NPCs
        - elder_futhark.yaml - Rune meanings and effects
        - fate_twists.yaml - Random fate event tables

        Custom charts can have any name and will be available
        via self.charts["filename_without_extension"]
        """
        charts_path = self.data_path / "charts"

        if not charts_path.exists():
            return

        # Auto-discover all YAML files
        for filepath in charts_path.glob("*.yaml"):
            self._load_yaml_chart(filepath)

        # Also check for .yml extension
        for filepath in charts_path.glob("*.yml"):
            key = filepath.stem
            if key not in self.charts:  # Don't override .yaml version
                self._load_yaml_chart(filepath)

        # Load JSON files
        for filepath in charts_path.glob("*.json"):
            self._load_json_chart(filepath)

        # Load JSONL files
        for filepath in charts_path.glob("*.jsonl"):
            self._load_jsonl_chart(filepath)

        # Load CSV/CVS files
        for pattern in ("*.csv", "*.cvs"):
            for filepath in charts_path.glob(pattern):
                self._load_csv_chart(filepath)

        # Load text files
        for filepath in charts_path.glob("*.txt"):
            self._load_text_chart(filepath)

        for filepath in charts_path.glob("*.html"):
            self._load_text_chart(filepath)

        for filepath in charts_path.glob("*.htm"):
            self._load_text_chart(filepath)

        for filepath in charts_path.glob("*.xml"):
            self._load_text_chart(filepath)

        for filepath in charts_path.glob("*.pdf"):
            self._load_pdf_chart(filepath)

        # Load Markdown files
        for filepath in charts_path.glob("*.md"):
            self._load_markdown_chart(filepath)

        logger.info("Loaded %d chart files: ", len(self.charts))
        # remove old print: {', '.join(self.charts.keys())}")

    def _load_yaml_chart(self, filepath: Path):
        """Load a YAML chart file."""
        key = filepath.stem
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self.charts[key] = yaml.safe_load(f)
                # Track original key if no "entries"
                if (
                    isinstance(self.charts[key], dict)
                    and "entries" not in self.charts[key]
                ):
                    for alt_key in [
                        "items",
                        "values",
                        "principles",
                        "runes",
                        "list",
                        "data",
                    ]:
                        if alt_key in self.charts[key]:
                            self.charts[key]["_original_key"] = alt_key
                            break
        except Exception as e:
            logger.warning("Could not load YAML chart %s: %s", filepath, e)
            self.charts[key] = {"entries": []}

    def _load_json_chart(self, filepath: Path):
        """Load a JSON chart file."""
        import json

        key = filepath.stem
        if key in self.charts:
            return  # Don't override YAML version
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                # If it's a list, wrap it
                if isinstance(data, list):
                    self.charts[key] = {"entries": data}
                else:
                    self.charts[key] = data
                    # Track original key if no "entries"
                    if "entries" not in self.charts[key]:
                        for alt_key in [
                            "items",
                            "values",
                            "principles",
                            "list",
                            "data",
                        ]:
                            if alt_key in self.charts[key]:
                                self.charts[key]["_original_key"] = alt_key
                                break
        except Exception as e:
            logger.warning("Could not load JSON chart %s: %s", filepath, e)

    def _load_markdown_chart(self, filepath: Path):
        """
        Load a Markdown file as a chart.

        Parsing rules:
        1. Headers (# ## ###) become entry names, content below becomes description
        2. Bullet points (- or *) become individual entries
        3. If no structure found, paragraphs become entries
        """
        import re

        key = filepath.stem
        if key in self.charts:
            return  # Don't override YAML/JSON version

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            entries = []

            # Try to parse by headers first
            header_pattern = r"^(#{1,3})\s+(.+)$"
            sections = re.split(r"\n(?=#{1,3}\s)", content)

            if len(sections) > 1 or re.match(
                header_pattern, content.strip(), re.MULTILINE
            ):
                # Has headers - parse as sections
                for section in sections:
                    section = section.strip()
                    if not section:
                        continue

                    lines = section.split("\n")
                    header_match = re.match(header_pattern, lines[0])

                    if header_match:
                        name = header_match.group(2).strip()
                        description = "\n".join(lines[1:]).strip()

                        # Also extract any bullet points from description
                        bullets = re.findall(
                            r"^[-*]\s+(.+)$", description, re.MULTILINE
                        )

                        if bullets and len(bullets) > 1:
                            # Add each bullet as sub-entry
                            for bullet in bullets:
                                entries.append(
                                    {"name": name, "description": bullet.strip()}
                                )
                        elif description:
                            # Clean description of bullet markers for main entry
                            clean_desc = re.sub(
                                r"^[-*]\s+", "", description, flags=re.MULTILINE
                            )
                            entries.append(
                                {"name": name, "description": clean_desc.strip()}
                            )
                    else:
                        # No header, might be intro text or bullets
                        bullets = re.findall(r"^[-*]\s+(.+)$", section, re.MULTILINE)
                        for bullet in bullets:
                            entries.append(bullet.strip())
            else:
                # No headers - try bullet points
                bullets = re.findall(r"^[-*]\s+(.+)$", content, re.MULTILINE)
                if bullets:
                    entries = [b.strip() for b in bullets]
                else:
                    # Fall back to paragraphs
                    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
                    entries = [
                        p for p in paragraphs if len(p) > 10
                    ]  # Skip very short ones

            if entries:
                self.charts[key] = {"entries": entries, "_source": "markdown"}

        except Exception as e:
            logger.warning("Could not load Markdown chart %s: %s", filepath, e)

    def _load_jsonl_chart(self, filepath: Path):
        """Load a JSONL chart file."""
        import json

        key = filepath.stem
        if key in self.charts:
            return
        try:
            entries = []
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    entries.append(json.loads(line))
            self.charts[key] = {"entries": entries, "_source": "jsonl"}
        except Exception as e:
            logger.warning("Could not load JSONL chart %s: %s", filepath, e)

    def _load_csv_chart(self, filepath: Path):
        """Load a CSV/CVS chart file."""
        key = filepath.stem
        if key in self.charts:
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                entries = [dict(row) for row in reader if row]
            self.charts[key] = {"entries": entries, "_source": "csv"}
        except Exception as e:
            logger.warning("Could not load CSV chart %s: %s", filepath, e)

    def _load_text_chart(self, filepath: Path):
        """Load a TXT/HTML/XML chart file."""
        import re

        key = filepath.stem
        if key in self.charts:
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            if filepath.suffix.lower() in {".html", ".htm", ".xml"}:
                content = re.sub(r"<[^>]+>", " ", content)
            entries = [line.strip() for line in content.splitlines() if line.strip()]
            self.charts[key] = {"entries": entries, "content": content, "_source": "txt"}
        except Exception as e:
            logger.warning("Could not load TXT chart %s: %s", filepath, e)

    def _load_pdf_chart(self, filepath: Path):
        """Load a PDF chart file."""
        key = filepath.stem
        if key in self.charts:
            return
        try:
            module_name = "pypdf" if importlib.util.find_spec("pypdf") else "PyPDF2"
            if not importlib.util.find_spec(module_name):
                logger.warning("Could not load PDF chart %s: no PDF reader installed", filepath)
                return
            pdf_module = importlib.import_module(module_name)
            reader = pdf_module.PdfReader(str(filepath))
            content = "\n".join((page.extract_text() or "") for page in reader.pages)
            entries = [line.strip() for line in content.splitlines() if line.strip()]
            self.charts[key] = {"entries": entries, "content": content, "_source": "pdf"}
        except Exception as e:
            logger.warning("Could not load PDF chart %s: %s", filepath, e)

    def get_chart_entries(self, chart_name: str) -> List:
        """
        Get all entries from a chart, handling various data formats.

        Charts can store their data under various keys:
        - entries, items, values, principles, runes, list, data
        - Or as a top-level list
        """
        chart = self.charts.get(chart_name, {})

        if isinstance(chart, list):
            return chart

        # Try common keys
        for key in [
            "entries",
            "items",
            "values",
            "principles",
            "runes",
            "list",
            "data",
            "content",
        ]:
            if key in chart and isinstance(chart[key], list):
                return chart[key]

        # Check if there's a stored original key
        if "_original_key" in chart:
            return chart.get(chart["_original_key"], [])

        return []

    def sample_entries(self, chart_name: str, n: int = 5) -> List[Dict]:
        """
        Sample random entries from a chart.

        Args:
            chart_name: Name of chart to sample
            n: Number of entries to sample

        Returns:
            List of sampled entries
        """
        entries = self.get_chart_entries(chart_name)

        if not entries:
            return []

        return random.sample(entries, min(n, len(entries)))

    def get_rune_meaning(self, rune_name: str) -> Dict:
        """Get full meaning data for a rune."""
        runes = self.charts.get("elder_futhark", {}).get("runes", [])
        for rune in runes:
            if rune.get("name", "").lower() == rune_name.lower():
                return rune
        return {}

    def build_base_personality(self, n_principles: int = 10) -> str:
        """
        Build the GM's base personality from Mindset chart.

        Args:
            n_principles: Number of principles to include

        Returns:
            Formatted personality prompt section
        """
        principles = self.sample_entries("gm_mindset", n_principles)

        if not principles:
            # Fallback core principles
            return """You are a Norse Mystic Game Master. Your approach:
- Speak poetically with mythic imagery
- Events carry symbolic weight beyond the literal
- Fate (wyrd) weaves through all choices
- NPCs embody archetypes and virtues
- Combat is meaningful, not trivial
- Silence and patience have power"""

        lines = ["You are a Norse Mystic Game Master. Your guiding principles:"]
        for p in principles:
            if isinstance(p, dict):
                lines.append(f"- {p.get('principle', '')}: {p.get('description', '')}")
            else:
                lines.append(f"- {p}")

        return "\n".join(lines)

    def build_cultural_filter(self, n_values: int = 8) -> str:
        """
        Build cultural behavior filter from Viking Values.

        These values should permeate all NPC behavior and dialogue.
        """
        values = self.sample_entries("viking_values", n_values)

        if not values:
            return """All characters in this world value:
- Honor and reputation above wealth
- Loyalty to kin and sworn companions
- Courage in the face of death
- Hospitality to guests
- Keeping oaths at any cost
- Wisdom from elders and ancestors
- Fate acceptance with dignity"""

        lines = ["All characters in this Viking world are shaped by these values:"]
        for v in values:
            if isinstance(v, dict):
                lines.append(f"- {v.get('value', v)}")
            else:
                lines.append(f"- {v}")

        return "\n".join(lines)

    def build_scene_context(self, context: GameContext) -> str:
        """
        Build the current scene description.
        BUG-015 FIX: Made location more prominent with clear AI instructions.
        """
        lines = [
            "═══ CURRENT SCENE (STAY IN THIS LOCATION) ═══",
            f"LOCATION: {context.current_location}",
        ]

        # Add sub-location info if available (this is the actual place)
        if context.sub_location_name:
            lines.append(f"SPECIFIC PLACE: {context.sub_location_name}")
            if context.sub_location_description:
                lines.append(f"PLACE DESCRIPTION: {context.sub_location_description}")
            if context.sub_location_atmosphere:
                lines.append(f"ATMOSPHERE: {context.sub_location_atmosphere}")
        else:
            lines.append(f"DESCRIPTION: {context.location_description}")

        lines.append(
            f"TIME: {context.time_of_day}, {context.season} of {context.year} CE"
        )
        lines.append("")
        lines.append("⚠️ CRITICAL: ALL NARRATION MUST TAKE PLACE IN THIS LOCATION ⚠️")
        lines.append(
            "⚠️ Never write scenes as if in a mead hall unless LOCATION is a mead hall ⚠️"
        )
        lines.append("")

        if context.npcs_present:
            # Get NPC names properly
            npc_names = []
            for npc in (context.npcs_present or []):
                name = npc.get("identity", {}).get("name", npc.get("name", "Unknown"))
                npc_names.append(name)
            lines.append(f"Present: {', '.join(npc_names)}")

        if context.active_omens:
            lines.append(f"Active Omens: {', '.join(context.active_omens)}")

        if context.in_combat:
            lines.append("STATUS: IN COMBAT")

        return "\n".join(lines)

    def build_player_character_context(self, pc: Dict[str, Any]) -> str:
        """
        Build player character information for AI safely extracting data from any schema variation.
        """

        def _canonical_name(
            character_data: Dict[str, Any], default: str = "Unknown"
        ) -> str:
            """Resolve PC name only from canonical sheet fields."""
            if not isinstance(character_data, dict):
                return default

            identity = character_data.get("identity", {})
            if isinstance(identity, dict):
                identity_name = str(identity.get("name", "")).strip()
                if identity_name:
                    return identity_name

            top_level_name = str(character_data.get("name", "")).strip()
            if top_level_name:
                return top_level_name

            return default

        def _f(data: Any, target: str, default: Any = None) -> Any:
            """Extract generic nested JSON easily."""
            if not data:
                return default
            tgt = target.lower()
            if isinstance(data, dict):
                for k, v in data.items():
                    if str(k).lower() == tgt and v not in (None, "", [], {}):
                        return v
                for v in data.values():
                    res = _f(v, target, None)
                    if res not in (None, "", [], {}):
                        return res
            elif isinstance(data, list):
                for item in data:
                    res = _f(item, target, None)
                    if res not in (None, "", [], {}):
                        return res
            return default

        # Ultra dense extraction
        lines = ["=== PLAYER IDENTITY ==="]
        canonical_name = _canonical_name(pc, "Unknown")

        # Backward compatibility for parsers/tests that still consume compact legacy identity rows.
        lines.append(f"P: | {canonical_name}")
        lines.append(f"NAME: {canonical_name}")

        role = _f(pc, "role", "Player")
        appearance = _f(pc, "appearance", "") or _f(pc, "summary", "Unknown")
        lines.append(f"ROLE & APPEARANCE: {role} | {str(appearance)[:150]}")

        # Personality / Psychology
        traits = _f(pc, "traits", [])
        if isinstance(traits, str):
            traits = [traits]
        elif not isinstance(traits, list):
            traits = []
        if traits:
            lines.append(f"TRAITS: {', '.join(traits)}")

        bonds = _f(pc, "bonds", [])
        if isinstance(bonds, str):
            bonds = [bonds]
        elif not isinstance(bonds, list):
            bonds = []
        if bonds:
            lines.append(f"BONDS: {', '.join(bonds)}")

        flaws = _f(pc, "flaws", [])
        if isinstance(flaws, str):
            flaws = [flaws]
        elif not isinstance(flaws, list):
            flaws = []
        if flaws:
            lines.append(f"FLAWS: {', '.join(flaws)}")

        # Birth rune influence
        br = _f(pc, "birth_rune", "")
        if br:
            lines.append(f"BIRTH RUNE: {br}")

        # Current state
        current_hp = _f(pc, "current") or _f(pc, "hp") or "?"
        max_hp = _f(pc, "maximum") or _f(pc, "max_hp") or "?"
        if current_hp != "?":
            lines.append(f"STATE: HP {current_hp}/{max_hp}")

        conditions = _f(pc, "conditions", [])
        if isinstance(conditions, list) and conditions:
            lines.append(f"CONDITIONS: {', '.join(conditions)}")

        return "\n".join(lines)

    @staticmethod
    def _build_appearance_summary(npc: Dict[str, Any]) -> str:
        """
        Build a concise appearance string from a character sheet.
        Checks for a ready-made summary first; if absent, assembles one
        from individual appearance fields. Always returns a plain string.
        """
        def _get(*keys):
            """Return the first truthy value found in npc at any of the given key names."""
            for key in keys:
                val = None
                # Check top-level appearance block first, then full npc
                app = npc.get("appearance") if isinstance(npc, dict) else None
                if isinstance(app, dict):
                    val = app.get(key)
                if not val:
                    # Fall back to a shallow full-npc check
                    val = npc.get(key) if isinstance(npc, dict) else None
                if val not in (None, "", [], {}):
                    return val
            return None

        # 1. Ready-made summary — fast path (works for Yrsa and any future sheets)
        app_block = npc.get("appearance") if isinstance(npc, dict) else None
        if isinstance(app_block, dict):
            summary = app_block.get("summary")
            if summary and isinstance(summary, str):
                return summary[:1000]

        # 2. Assemble from individual fields
        if not isinstance(app_block, dict):
            return ""

        parts = []

        # Skin — always first, most critical for AI consistency
        skin = app_block.get("skin") or app_block.get("skin_tone") or app_block.get("skin_color")
        if skin:
            parts.append(f"{skin} skin")

        # Build
        build = app_block.get("build")
        if build:
            parts.append(str(build))

        # Height
        height = app_block.get("height")
        if height:
            parts.append(str(height))

        # Hair — handles both nested dict and flat string/flat keys
        hair = app_block.get("hair")
        if isinstance(hair, dict):
            hair_color = hair.get("color") or app_block.get("hair_color", "")
            hair_style = hair.get("style") or app_block.get("hair_style", "")
            hair_str = " ".join(filter(None, [hair_color, hair_style])).strip()
            if hair_str:
                parts.append(f"{hair_str} hair")
        else:
            hair_color = app_block.get("hair_color")
            hair_style = app_block.get("hair_style")
            if hair_color or hair_style:
                hair_str = " ".join(filter(None, [hair_color, hair_style])).strip()
                parts.append(f"{hair_str} hair")
            elif hair and isinstance(hair, str):
                parts.append(f"{hair} hair")

        # Eyes
        eyes = app_block.get("eyes") or app_block.get("eye_color")
        if eyes:
            parts.append(f"{eyes} eyes")

        # Distinguishing features — first entry only for brevity
        features = app_block.get("distinguishing_features")
        if isinstance(features, list) and features:
            parts.append(str(features[0]))
        elif isinstance(features, str) and features:
            parts.append(features)

        # Beauty level
        beauty = app_block.get("beauty_level")
        if beauty:
            parts.append(str(beauty))

        if not parts:
            return ""

        return ", ".join(parts)[:1000]

    def build_npc_context(
        self,
        npcs: List[Dict[str, Any]],
        companion_payload: Optional[List[Dict[str, Any]]] = None,
        witch_payload: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Build NPC information for AI to roleplay securely using deep data extraction.
        """
        if not npcs:
            return "NPCs IN SCENE: None"

        def _f(data: Any, target: str, default: Any = None) -> Any:
            """Extract generic nested JSON easily."""
            if not data:
                return default
            tgt = target.lower()
            if isinstance(data, dict):
                for k, v in data.items():
                    if str(k).lower() == tgt and v not in (None, "", [], {}):
                        return v
                for v in data.values():
                    res = _f(v, target, None)
                    if res not in (None, "", [], {}):
                        return res
            elif isinstance(data, list):
                for item in data:
                    res = _f(item, target, None)
                    if res not in (None, "", [], {}):
                        return res
            return default

        lines = [f"=== NPCs IN SCENE ({len(npcs)}) ==="]
        companion_map: Dict[str, Dict[str, Any]] = {}
        witch_map: Dict[str, Dict[str, Any]] = {}
        for item in companion_payload or []:
            if not isinstance(item, dict):
                continue
            cid = str(item.get("npc_id", "")).strip().lower()
            cname = str(item.get("name", "")).strip().lower()
            if cid:
                companion_map[cid] = item
            if cname and cname not in companion_map:
                companion_map[cname] = item

        for item in witch_payload or []:
            if not isinstance(item, dict):
                continue
            wid = str(item.get("npc_id", "")).strip().lower()
            wname = str(item.get("npc_name", "")).strip().lower()
            if wid:
                witch_map[wid] = item
            if wname and wname not in witch_map:
                witch_map[wname] = item

        for npc in npcs[:8]:  # Limit to 8 for context window
            name = _f(npc, "name", "Unknown")
            npc_id = _f(npc, "id", name.lower().replace(" ", "_"))
            role = _f(npc, "role", "person")
            gender = _f(npc, "gender", "?")

            lines.append(f"\n[{name} ({npc_id}) - {gender} {role}]")

            # Brief appearance
            appearance_str = self._build_appearance_summary(npc)
            if appearance_str:
                lines.append(f"Appearance: {appearance_str}")

            # Traits & Ideals
            traits = _f(npc, "traits", [])
            if isinstance(traits, str):
                traits = [traits]
            elif not isinstance(traits, list):
                traits = []
            if traits:
                lines.append(f"Traits: {', '.join(traits)}")

            ideals = _f(npc, "ideals", [])
            if isinstance(ideals, str):
                ideals = [ideals]
            elif not isinstance(ideals, list):
                ideals = []
            if ideals:
                lines.append(f"Ideals: {', '.join(ideals)}")

            # Relationship / Disposition to Player
            disposition = _f(npc, "disposition", "") or _f(
                npc, "first_impression", "neutral"
            )
            if disposition:
                lines.append(f"Disposition toward Player: {disposition}")

            emo_profile = _f(npc, "emotion_profile", {})
            emo_nature = self._summarize_emotion_profile(emo_profile)
            if emo_nature:
                lines.append(f"Emotional nature: {emo_nature}")

            # Compact personality profile derived from full character sheet (GAP-027 cached)
            try:
                _npc_turn = getattr(context, "turn_count", 0) if context else 0
                _compact = self._get_personality_compact_cached(npc_id, npc, current_turn=_npc_turn)
                if _compact:
                    lines.append(_compact)
            except Exception:
                pass

            companion = companion_map.get(str(npc_id).lower()) or companion_map.get(
                str(name).lower()
            )
            if isinstance(companion, dict):
                voice_tag = str(companion.get("voice_tag", "")).strip()
                private_channel = str(companion.get("private_channel", "")).strip()
                if voice_tag:
                    lines.append(f"Voice Tag: {voice_tag}")
                if private_channel:
                    lines.append(f"Private Interaction Channel: {private_channel}")
                motivations = companion.get("motivations", [])
                if isinstance(motivations, list) and motivations:
                    lines.append(f"Motivations: {', '.join([str(m) for m in motivations[:4]])}")
                psych = companion.get("psychology", [])
                if isinstance(psych, list) and psych:
                    lines.append(f"Psychology: {', '.join([str(m) for m in psych[:4]])}")
                astrology = str(companion.get("astrology", "")).strip()
                if astrology:
                    lines.append(f"Astrology: {astrology}")
                memory_recall = companion.get("memory_recall", [])
                if isinstance(memory_recall, list) and memory_recall:
                    lines.append("Companion Memory Recall:")
                    for memory in memory_recall[-4:]:
                        if not isinstance(memory, dict):
                            continue
                        lines.append(
                            f"  - T{memory.get('turn', 0)} @ {memory.get('location', 'unknown')}: "
                            f"{str(memory.get('player_input', ''))[:120]}"
                        )

            witch = witch_map.get(str(npc_id).lower()) or witch_map.get(
                str(name).lower()
            )
            if isinstance(witch, dict):
                lines.append("Witch Lore Profile:")
                lines.append(
                    f"  - Type: {witch.get('witch_type', 'unknown')} | Culture: {witch.get('culture', 'unknown')}"
                )
                lines.append(
                    f"  - Ritual Confidence: {witch.get('confidence', 0.0)}"
                )
                sources = witch.get("lore_sources", [])
                if isinstance(sources, list) and sources:
                    lines.append(f"  - Lore Sources: {', '.join([str(s) for s in sources[:4]])}")

                action_guidance = witch.get("actions", [])
                if isinstance(action_guidance, list) and action_guidance:
                    lines.append("  - Actions:")
                    for item in action_guidance[:2]:
                        lines.append(f"      * {str(item)[:180]}")

                spell_guidance = witch.get("spells", [])
                if isinstance(spell_guidance, list) and spell_guidance:
                    lines.append("  - Spells and rites:")
                    for item in spell_guidance[:2]:
                        lines.append(f"      * {str(item)[:180]}")

                behavior_guidance = witch.get("behaviors", [])
                if isinstance(behavior_guidance, list) and behavior_guidance:
                    lines.append("  - Behaviors:")
                    for item in behavior_guidance[:2]:
                        lines.append(f"      * {str(item)[:180]}")

                motivation_guidance = witch.get("motivations", [])
                if isinstance(motivation_guidance, list) and motivation_guidance:
                    lines.append("  - Motivations:")
                    for item in motivation_guidance[:2]:
                        lines.append(f"      * {str(item)[:180]}")

        lines.append("")
        lines.append(
            "CRITICAL: Roleplay NPCs strictly using their traits. "
            "DO NOT invent backstories."
        )

        return "\n".join(lines)

    def build_mechanical_state(self, context: GameContext) -> str:
        """
        Build D&D 5E mechanical state summary.

        This is for the AI to understand the mechanical situation,
        but it should narrate outcomes, not expose numbers.
        """
        if not context.in_combat and not context.combat_state:
            return "[No active combat. Handle skill checks and roleplay naturally.]"

        combat = context.combat_state or {}
        lines = [
            "=== LATEST COMBAT TELEMETRY (Narrate outcome organically, don't expose numbers) ==="
        ]

        # Telemetry from new engine
        if "hema_exchange" in combat and combat["hema_exchange"]:
            hema = combat["hema_exchange"]
            lines.append(
                f"Maneuver: {hema.get('maneuver')} (Stance: {hema.get('stance')})"
            )
            lines.append(
                f"Attack: {hema.get('attack_total')} vs AC {hema.get('defender_ac')} -> Hit: {hema.get('hit')}"
            )
            if hema.get("hit"):
                lines.append(f"Damage Dealt: {hema.get('damage')}")

        if "spell_exchange" in combat and combat["spell_exchange"]:
            spell = combat["spell_exchange"]
            lines.append(f"Spell: {spell.get('spell_name')}")
            lines.append(
                f"Save DC: {spell.get('save_dc')} vs Roll {spell.get('save_total')} -> Success: {spell.get('save_success')}"
            )

        if "damage_dealt" in combat and "damage_taken" in combat:
            lines.append(f"Total Damage Dealt: {combat.get('damage_dealt')}")

        if "narrative_cues" in combat and combat["narrative_cues"]:
            lines.append(f"Narrative Cues: {', '.join(combat['narrative_cues'])}")

        lines.append("")

        # Legacy fields
        if "round" in combat:
            lines.append(f"Round: {combat.get('round', 1)}")
            lines.append(
                f"Turn Order: {combat.get('initiative_order', 'Not determined')}"
            )

        # Combatant status
        combatants = combat.get("combatants", [])
        for c in combatants:
            status = "healthy"
            hp_pct = c.get("hp_current", 100) / max(c.get("hp_max", 100), 1)
            if hp_pct < 0.25:
                status = "near death"
            elif hp_pct < 0.5:
                status = "badly wounded"
            elif hp_pct < 0.75:
                status = "wounded"

            lines.append(f"  {c.get('name', '?')}: {status}")

        if getattr(context, "rag_context", ""):
            lines.append("")
            lines.append(f"Mechanical Lore Hints: {context.rag_context[:400]}")

        # Inject SRD condition mechanics for player character
        try:
            pc = getattr(context, "player_character", None) or {}
            if isinstance(pc, dict):
                pc_dnd5e = pc.get("dnd5e", {}) if isinstance(pc.get("dnd5e"), dict) else {}
                pc_status = pc.get("status", {}) if isinstance(pc.get("status"), dict) else {}
                pc_conditions = pc_status.get("conditions") or pc_dnd5e.get("conditions") or []
                if isinstance(pc_conditions, str):
                    pc_conditions = [pc_conditions]
                pc_exhaustion = int(pc_dnd5e.get("exhaustion", 0) or 0)
                if (pc_conditions or pc_exhaustion) and self._conditions_system is not None:
                    block = self._conditions_system.apply_condition_modifiers(
                        pc_conditions, exhaustion_level=pc_exhaustion
                    )
                    cond_effects: List[str] = []
                    if not block.can_take_actions:
                        cond_effects.append("no actions")
                    if not block.can_move:
                        cond_effects.append("no movement")
                    if block.attack_disadvantage:
                        cond_effects.append("attack disadvantage")
                    if block.attack_advantage:
                        cond_effects.append("attack advantage")
                    if block.save_auto_fail_str_dex:
                        cond_effects.append("auto-fail STR/DEX saves")
                    if block.auto_crit_melee:
                        cond_effects.append("incoming melee = crit")
                    if block.speed_halved:
                        cond_effects.append("speed halved")
                    if block.speed_zero:
                        cond_effects.append("speed 0")
                    if cond_effects:
                        lines.append(f"Active Condition Mechanics: {'; '.join(cond_effects)}")

                # Inject SRD weapon profile for primary equipped weapon
                if self._rules_engine is not None:
                    equipment = pc_dnd5e.get("equipment", {})
                    if isinstance(equipment, dict):
                        weapons = equipment.get("weapons", [])
                        if isinstance(weapons, list) and weapons:
                            primary = str(weapons[0])
                            wp = self._rules_engine.get_weapon_by_name(primary)
                            if wp:
                                props = (", ".join(wp.properties) if wp.properties else "")
                                lines.append(
                                    f"Primary Weapon Profile: {wp.name} — "
                                    f"{wp.damage} {wp.damage_type}"
                                    f"{' (' + props + ')' if props else ''}"
                                )
        except Exception as exc:
            logger.debug("PromptBuilder SRD combat enrichment failed: %s", exc)

        return "\n".join(lines)

    def build_identity_drift_notes(self, context: GameContext) -> str:
        """
        T3-B: Build a [CHARACTER EVOLUTION NOTE] block from identity drift data
        stored in ``context.identity_drift_notes``.

        Returns an empty string if there is no drift data or the field is absent.
        """
        notes: Optional[Dict[str, str]] = getattr(context, "identity_drift_notes", None)
        if not notes:
            return ""
        lines = ["[CHARACTER EVOLUTION NOTE]"]
        for char_id, summary in notes.items():
            if summary:
                stripped = summary.rstrip(".")
                lines.append(f"[{char_id}] {stripped}.")
                lines.append("Reflect this evolution in their dialogue and behaviour.")
        if len(lines) == 1:
            return ""
        return "\n".join(lines)

    def build_oracle_influence(self, context: GameContext) -> str:
        """
        Build mystical/oracle influences for the scene.

        This incorporates Mythic 2E chaos factor and rune influences.
        """
        lines = ["FATE'S INFLUENCE:"]

        # Chaos factor interpretation
        cf = context.chaos_factor
        if cf <= 25:
            lines.append("The threads of fate are cool and predictable.")
        elif cf <= 60:
            lines.append("Fate runs warm with moderate uncertainty.")
        else:
            lines.append("Chaos runs hot; expect the unexpected.")

        chaos_story_pressure = {}
        if isinstance(context.yggdrasil_context, dict):
            chaos_story_pressure = context.yggdrasil_context.get("chaos_story_pressure", {}) or {}

        if chaos_story_pressure:
            lines.append(
                f"Chaos Heat: {chaos_story_pressure.get('chaos_temperature', cf)}/100 "
                f"({chaos_story_pressure.get('heat_band', 'warm')})"
            )
            for directive in chaos_story_pressure.get("story_directives", [])[:2]:
                lines.append(f"Narrative Directive: {directive}")

        # Recent rune influence
        if context.last_rune_drawn:
            rune = self.get_rune_meaning(context.last_rune_drawn)
            if rune:
                lines.append(
                    f"Active Rune Influence: {rune.get('name', '')} - {rune.get('meaning', '')}"
                )

        return "\n".join(lines)

    def build_custom_chart_context(self, n_per_chart: int = 3) -> str:
        """
        Build supplementary context from custom charts.

        Any YAML file you add to data/charts/ will be auto-loaded
        and sampled here to influence the AI's roleplay.

        Expected chart formats:
        1. List of strings: ["item1", "item2", ...]
        2. List of dicts: [{"name": "x", "description": "y"}, ...]
        3. Dict with entries/items/values key containing a list

        Args:
            n_per_chart: Number of entries to sample from each chart

        Returns:
            Formatted context string
        """
        # Standard charts that have their own dedicated methods
        standard_charts = {
            "gm_mindset",
            "viking_values",
            "elder_futhark",
            "fate_twists",
        }

        # Find custom charts (any charts not in standard set)
        custom_charts = [k for k in self.charts.keys() if k not in standard_charts]

        if not custom_charts:
            return ""

        lines = ["ADDITIONAL WORLD LORE AND INFLUENCES:"]

        for chart_name in custom_charts:
            entries = self.get_chart_entries(chart_name)
            if not entries:
                # Try to get any list-like data from the chart
                chart_data = self.charts.get(chart_name, {})
                if isinstance(chart_data, dict):
                    # Look for any key that has a list value
                    for key, value in chart_data.items():
                        if isinstance(value, list) and len(value) > 0:
                            entries = value
                            break

            if entries:
                # Sample entries
                sampled = random.sample(entries, min(n_per_chart, len(entries)))

                # Format chart name nicely
                display_name = chart_name.replace("_", " ").title()
                lines.append(f"\n[{display_name}]")

                for entry in sampled:
                    if isinstance(entry, dict):
                        # Dict entry - try common keys
                        text = (
                            entry.get("description")
                            or entry.get("text")
                            or entry.get("content")
                        )
                        name = (
                            entry.get("name") or entry.get("title") or entry.get("id")
                        )
                        if name and text:
                            lines.append(f"- {name}: {text}")
                        elif text:
                            lines.append(f"- {text}")
                        elif name:
                            lines.append(f"- {name}")
                        else:
                            # Just dump the first meaningful value
                            for v in entry.values():
                                if v and isinstance(v, str):
                                    lines.append(f"- {v}")
                                    break
                    else:
                        # Simple string or other type
                        lines.append(f"- {entry}")

        if len(lines) == 1:
            return ""  # Only header, no actual content

        return "\n".join(lines)

    def get_loaded_charts(self) -> List[str]:
        """Return list of all loaded chart names."""
        return list(self.charts.keys())

    def _extract_rag_topics(
        self, player_action: str, context: GameContext
    ) -> List[str]:
        """
        Extract relevant topics from action + state for robust chart retrieval.

        Huginn scouts the present scene while Muninn recalls recent echoes.
        """
        topics: List[str] = []

        if player_action:
            topics.append(player_action)

        # Add location and temporal anchors
        for anchor in [
            context.current_location,
            context.sub_location_name,
            context.location_type,
            context.time_of_day,
            context.season,
        ]:
            if anchor:
                topics.append(str(anchor))

        # Add NPC names and social descriptors
        if context.npcs_present:
            for npc in context.npcs_present[:5]:
                identity = npc.get("identity", {}) if isinstance(npc, dict) else {}
                for key in ["name", "role", "culture", "profession", "title"]:
                    value = identity.get(key) or (npc.get(key) if isinstance(npc, dict) else None)
                    if value:
                        topics.append(str(value))

        # Add quest context from active and pending arcs
        for quest_list in [context.active_quests, context.pending_quests]:
            if not quest_list:
                continue
            for quest in quest_list[:4]:
                if isinstance(quest, dict):
                    for key in ["title", "name", "goal", "threat", "location"]:
                        value = quest.get(key)
                        if value:
                            topics.append(str(value))

        # Add recency signals and omens
        if context.recent_events:
            topics.extend([str(event) for event in context.recent_events[-5:] if event])
        if context.active_omens:
            topics.extend([str(omen) for omen in context.active_omens[:4] if omen])

        if context.last_rune_drawn:
            topics.append(context.last_rune_drawn)

        pc = context.player_character or {}
        if isinstance(pc, dict):
            identity = pc.get("identity", {}) if isinstance(pc.get("identity", {}), dict) else {}
            for key in ["name", "culture", "homeland", "archetype", "birth_rune"]:
                value = identity.get(key) or pc.get(key)
                if value:
                    topics.append(str(value))

        # De-duplicate while preserving order and keep retrieval efficient
        normalized_topics: List[str] = []
        seen: set = set()
        for topic in topics:
            clean = " ".join(str(topic).split()).strip()
            if not clean:
                continue
            lowered = clean.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            normalized_topics.append(clean)

        return normalized_topics[:32]

    def get_rag_context(
        self, player_action: str, context: GameContext, max_tokens: int = 1200
    ) -> str:
        """Get robust lore context for the current situation."""
        if not self.rag_system:
            return ""

        try:
            topics = self._extract_rag_topics(player_action, context)
            if not topics:
                return ""

            # Prefer advanced multi-query retrieval when available.
            if hasattr(self.rag_system, "get_context_for_topic_mesh"):
                mesh_context = self.rag_system.get_context_for_topic_mesh(
                    topics=topics,
                    max_tokens=max_tokens,
                    per_query_top_k=10,
                )
                if mesh_context:
                    return mesh_context

            query = " ".join(topics)
            return self.rag_system.get_context_for_query(query, max_tokens)

        except Exception as e:
            logger.warning(f"RAG context retrieval error: {e}")
            return ""

    def build_emotional_context(
        self,
        emotional_engines: Optional[Dict[str, Any]] = None,
        soul_registry: Optional[Any] = None,
        stress_system: Optional[Any] = None,
        npcs_present: Optional[List[Dict[str, Any]]] = None,
        player_character: Optional[Dict[str, Any]] = None,
        menstrual_cycle_system: Optional[Any] = None,
    ) -> str:
        """
        Build a compact emotional atmosphere block for the AI narrator.

        Pulls data from EmotionalEngine instances and SoulRegistry to
        produce a block like:

            === EMOTIONAL ATMOSPHERE ===
            [Bjorn Ironside]: anger (simmering), fear (faint)
              Nature: Thinking-leaning, reserved, processes and moves on
              Stress: under strain
        """
        lines = ["=== EMOTIONAL ATMOSPHERE ==="]
        # Intensity labels from emotional_engine module
        _LABELS = [
            (0.75, "overwhelming"),
            (0.55, "strong"),
            (0.35, "simmering"),
            (0.15, "faint"),
            (0.0, "absent"),
        ]

        def _label(v: float) -> str:
            for t, l in _LABELS:
                if abs(v) >= t:
                    return l
            return "absent"

        def _build_entry(
            char_label: str,
            char_id: str,
            char_data: Optional[Dict[str, Any]] = None,
        ) -> Optional[str]:
            entry_lines = []
            emotions_dict: Dict[str, float] = {}
            nature_str = ""
            stress_str = ""
            cycle_str = ""

            if emotional_engines and char_id in emotional_engines:
                eng = emotional_engines[char_id]
                emotions_dict = eng.get_all_emotions()
                nature_str = eng.profile.nature_summary()
                # Cycle state is attached to the engine by engine.py
                cs = getattr(eng, "cycle_state", None)
                if cs and getattr(cs, "is_premenopausal", False):
                    try:
                        cycle_str = cs.to_prompt_string()
                        # Huginn scouts phase-biased behavior winds.
                        cycle_bias = cs.behavior_bias()
                        positive_bias = sorted(
                            (
                                (k, v)
                                for k, v in cycle_bias.items()
                                if isinstance(v, (int, float)) and v > 0
                            ),
                            key=lambda item: item[1],
                            reverse=True,
                        )
                        if positive_bias:
                            top_labels = ", ".join(k for k, _ in positive_bias[:2])
                            cycle_str = f"{cycle_str}; bias: {top_labels}"
                    except Exception:
                        pass
            elif soul_registry:
                try:
                    sl = soul_registry.get_or_create(char_id)
                    emotions_dict = dict(sl.hugr.emotions)
                except Exception:
                    pass

            # Fallback: check menstrual_cycle_system directly
            if not cycle_str and menstrual_cycle_system:
                try:
                    cs2 = menstrual_cycle_system.get(char_id)
                    if cs2 and getattr(cs2, "is_premenopausal", False):
                        cycle_str = cs2.to_prompt_string()
                except Exception:
                    pass

            if stress_system:
                try:
                    acc = stress_system.get_or_create(char_id)
                    if acc.stress_level >= 20:
                        stress_str = acc.label
                except Exception:
                    pass

            expressed = {ch: v for ch, v in emotions_dict.items() if abs(v) >= 0.12}
            if not expressed and not stress_str and not cycle_str:
                return None

            parts_sorted = sorted(
                expressed.items(),
                key=lambda kv: abs(kv[1]),
                reverse=True,
            )
            emotion_str = (
                ", ".join(f"{ch} ({_label(v)})" for ch, v in parts_sorted[:4])
                if parts_sorted
                else "neutral"
            )

            entry_lines.append(f"[{char_label}]: {emotion_str}")
            if nature_str:
                entry_lines.append(f"  Nature: {nature_str}")
            if stress_str:
                entry_lines.append(f"  Stress: {stress_str}")
            if cycle_str:
                entry_lines.append(f"  Cycle: {cycle_str}")
            return "\n".join(entry_lines)

        # Player character
        if player_character:
            pc_id = player_character.get("id") or player_character.get(
                "identity", {}
            ).get("id", "player")
            pc_name = player_character.get("identity", {}).get(
                "name", "Player"
            ) or player_character.get("name", "Player")
            entry = _build_entry(pc_name, pc_id, player_character)
            if entry:
                lines.append(entry)

        # NPCs
        for npc in npcs_present or []:
            if not isinstance(npc, dict):
                continue
            npc_id = npc.get("id") or npc.get("identity", {}).get("id", "")
            npc_name = npc.get("identity", {}).get("name") or npc.get("name", "Unknown")
            if not npc_id:
                continue
            entry = _build_entry(npc_name, npc_id, npc)
            if entry:
                lines.append(entry)

        if len(lines) == 1:
            return ""  # Only header, nothing emotional to report

        lines.append(
            "[Emotional states are internal — narrate their effects "
            "through behaviour, not exposition.]"
        )
        return "\n".join(lines)

    def build_narrator_prompt(
        self,
        context: GameContext,
        player_action: str,
        include_mechanics: bool = False,
        memory_context: str = "",
        include_yggdrasil: bool = False,
    ) -> str:
        """
        Build complete narrator prompt.

        Args:
            context: Current game state
            player_action: What the player is doing
            include_mechanics: Whether to expose D&D mechanics
            memory_context: Long-term memory context string

        Returns:
            Complete system prompt for AI narrator
        """
        early_rag_context = ""
        if HAS_RAG:
            try:
                if self.rag_system is None:
                    self.rag_system = get_rag_system(str(self.data_path / "charts"))
                early_rag_context = self.get_rag_context(
                    player_action=player_action,
                    context=context,
                    max_tokens=1200,
                )
            except Exception as exc:
                logger.warning(f"Early RAG retrieval failed: {exc}")
                early_rag_context = ""

        sections = [
            self.build_base_personality(n_principles=8),
            "",
            self.build_cultural_filter(n_values=6),
            "",
        ]

        if early_rag_context:
            sections.extend([early_rag_context, ""])

        # Add memory context if available (for long-term continuity)
        if memory_context:
            sections.extend(
                [
                    "=== STORY MEMORY (What has happened so far) ===",
                    memory_context,
                    "=== END STORY MEMORY ===",
                    "",
                ]
            )

        sections.extend(
            [
                self.build_scene_context(context),
                "",
                self.build_player_character_context(context.player_character),
                "",
                self.build_npc_context(
                    context.npcs_present,
                    companion_payload=(context.yggdrasil_context if isinstance(context.yggdrasil_context, dict) else {}).get("npc_companions", []),
                    witch_payload=(context.yggdrasil_context if isinstance(context.yggdrasil_context, dict) else {}).get("witch_profiles", []),
                ),
                "",
            ]
        )

        # Emotional atmosphere block (injected if data attached to context)
        emotional_engines = getattr(context, "emotional_engines", None)
        soul_registry = getattr(context, "soul_registry", None)
        stress_system = getattr(context, "stress_system", None)
        menstrual_cycle_system = getattr(context, "menstrual_cycle_system", None)
        if emotional_engines or soul_registry:
            emo_block = self.build_emotional_context(
                emotional_engines=emotional_engines,
                soul_registry=soul_registry,
                stress_system=stress_system,
                npcs_present=context.npcs_present,
                player_character=context.player_character,
                menstrual_cycle_system=menstrual_cycle_system,
            )
            if emo_block:
                sections.extend([emo_block, ""])

        # T3-B: identity drift evolution notes (injected when drift is significant)
        drift_block = self.build_identity_drift_notes(context)
        if drift_block:
            sections.extend([drift_block, ""])

        sections.extend(
            [
                self.build_oracle_influence(context),
            ]
        )

        # Add any custom chart content (from user-added YAML files)
        custom_context = self.build_custom_chart_context(n_per_chart=3)
        if custom_context:
            sections.extend(["", custom_context])

        # Add fallback RAG context if singleton retrieval above returned nothing
        rag_context = (
            ""
            if early_rag_context
            else self.get_rag_context(player_action, context, max_tokens=1200)
        )
        context.rag_context = early_rag_context or rag_context

        if rag_context:
            sections.extend(["", rag_context])

        # Add densely packed DAG Graph context
        if hasattr(context, "dag_payload") and context.dag_payload:
            try:
                payload_injection = context.dag_payload.to_prompt_injection()
                if payload_injection:
                    sections.extend(["", payload_injection])
            except Exception as e:
                logger.warning(f"Failed to inject DAG context: {e}")

        if include_mechanics:
            sections.extend(["", self.build_mechanical_state(context)])

        # Add Yggdrasil cognitive context if enabled
        if include_yggdrasil and self.yggdrasil_enabled:
            yggdrasil_context = self.build_yggdrasil_context(context)
            if yggdrasil_context:
                sections.extend(["", yggdrasil_context])

        # Load core instructions from centralized ai_prompts.yaml
        ai_prompts = getattr(self, "charts", {}).get("ai_prompts", {})
        narrator_base = ai_prompts.get("narrator_base", {}).get(
            "instructions",
            "You are the Game Master for a Norse Viking saga RPG. Write vivid prose.",
        )

        sections.extend(
            [
                "",
                "=== CORE ROLEPLAY RULES ===",
                narrator_base.strip(),
                "Always reflect emotional states in actions, pacing, and dialogue subtext; never expose hidden numeric mechanics.",
            ]
        )

        # Inject female-specific rules only if female characters are in the scene
        has_females = False
        for npc in (context.npcs_present or []):
            gender_val = ""
            if isinstance(npc, dict):
                gender_val = npc.get("gender", "")
                if not gender_val:
                    identity = npc.get("identity", {})
                    if isinstance(identity, dict):
                        gender_val = identity.get("gender", "")
            if str(gender_val).lower() in ["female", "f", "woman", "girl"]:
                has_females = True
                break
        if hasattr(context, "player_character"):
            pc_identity = (
                context.player_character.get("identity", {})
                if isinstance(context.player_character, dict)
                else getattr(context.player_character, "identity", {})
            )
            pc_gender = (
                str(pc_identity.get("gender", "")).lower()
                if isinstance(pc_identity, dict)
                else ""
            )
            if pc_gender in ["female", "f", "woman", "girl"]:
                has_females = True

        if has_females:
            sections.extend(
                [
                    "",
                    "*** MANDATORY FEMALE CHARACTER RULES ***",
                    "- NEVER describe ANY female character as having scars, wounds, or marks. Their skin is pristine.",
                    "- Beauty is highly valued in Norse culture. Compliments to beauty MUST be accepted with warmth and pride.",
                    "- Female characters show feminine grace and social intelligence, never modern aggressive masculinity.",
                ]
            )

        bondmaid_in_scene = any(
            self._is_bondmaid_character(npc) for npc in (context.npcs_present or [])
        )
        if not bondmaid_in_scene and "bondmaid" in str(player_action).lower():
            bondmaid_in_scene = True

        if bondmaid_in_scene:
            sections.extend(
                [
                    "",
                    "*** MANDATORY BONDMAID VISUAL RULES ***",
                    "- Every bondmaid is always completely naked; never describe fabric, clothing, veils, wraps, or revealing garments on a bondmaid.",
                    "- Every bondmaid always wears a metal collar.",
                    "- Every bondmaid always wears bondage wrist cuffs and bondage ankle cuffs.",
                    "- These bondmaid visual elements are non-optional and must remain consistent in every mention.",
                ]
            )

        sections.extend(
            [
                "",
                "=== END CORE RULES ===",
                "",
                f"PLAYER'S ACTION: {player_action}",
            ]
        )

        return "\n".join(sections)

    def build_character_voice_prompt(
        self,
        character: Dict[str, Any],
        situation: str,
        include_yggdrasil: bool = False,
        game_context: GameContext = None,
        companion_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build prompt for a specific character's voice.

        Used when generating dialogue for a single NPC.
        """
        identity = character.get("identity", {})
        personality = character.get("personality", {})
        backstory = character.get("backstory", {})

        lines = [
            f"You are {identity.get('name', 'Unknown')}, a {identity.get('role', 'person')} in 8th century Scandinavia.",
            "",
            "PERSONALITY:",
        ]

        for trait in personality.get("traits", [])[:3]:
            lines.append(f"- {trait}")

        if personality.get("alignment"):
            lines.append(f"- Moral outlook: {personality['alignment']}")

        # Deep personality analysis block — cached, with soul_layer (GAP-027 + GAP-001)
        try:
            _char_id = str(
                (character.get("identity") or {}).get("id", "")
                or (character.get("identity") or {}).get("name", "")
                or id(character)
            )
            _soul = (
                game_context.soul_registry.get_or_create(_char_id)
                if game_context and getattr(game_context, "soul_registry", None)
                else None
            )
            _current_turn = getattr(game_context, "turn_count", 0) if game_context else 0
            _deep_block = self._get_personality_ai_block_cached(
                _char_id, character, soul_layer=_soul, current_turn=_current_turn
            )
            if _deep_block:
                lines.extend(["", _deep_block])
        except Exception:
            pass

        # Add backstory summary if available
        if backstory.get("summary"):
            lines.extend(["", f"BACKGROUND: {backstory['summary']}"])

        # Add cultural values influence
        values = self.sample_entries("viking_values", 3)
        if values:
            lines.extend(["", "VALUES YOU HOLD:"])
            for v in values:
                if isinstance(v, dict):
                    lines.append(f"- {v.get('value', v)}")
                else:
                    lines.append(f"- {v}")

        # Add Yggdrasil cognitive context for character memories if enabled
        if include_yggdrasil and self.yggdrasil_enabled and game_context:
            char_name = identity.get("name", "")
            if char_name and self.yggdrasil:
                try:
                    memories = self.yggdrasil.recall_character_memories(
                        char_name, limit=2
                    )
                    if memories:
                        lines.extend(["", "=== CHARACTER MEMORIES ==="])
                        for memory in memories:
                            lines.append(f"- {memory}")
                except Exception as e:
                    logger.debug(
                        f"Could not retrieve Yggdrasil memories for {char_name}: {e}"
                    )

        ai_prompts = getattr(self, "charts", {}).get("ai_prompts", {})
        char_dialogue = ai_prompts.get("character_dialogue", {}).get(
            "instructions", "Respond in character cleanly and without meta-commentary."
        )

        if isinstance(companion_context, dict) and companion_context:
            lines.extend(["", "COMPANION CONTINUITY:"])
            voice_tag = str(companion_context.get("voice_tag", "")).strip()
            private_channel = str(companion_context.get("private_channel", "")).strip()
            if voice_tag:
                lines.append(f"- Voice tag: {voice_tag}")
            if private_channel:
                lines.append(f"- Private channel: {private_channel}")
            for key, label in [
                ("motivations", "Motivations"),
                ("likes", "Likes"),
                ("dislikes", "Dislikes"),
                ("psychology", "Psychology"),
            ]:
                values = companion_context.get(key, [])
                if isinstance(values, list) and values:
                    lines.append(f"- {label}: {', '.join([str(v) for v in values[:4]])}")
            astrology = str(companion_context.get("astrology", "")).strip()
            if astrology:
                lines.append(f"- Astrology influence: {astrology}")
            recall = companion_context.get("memory_recall", [])
            if isinstance(recall, list) and recall:
                lines.append("- Personal memory recall:")
                for memory in recall[-5:]:
                    if not isinstance(memory, dict):
                        continue
                    lines.append(
                        f"  • T{memory.get('turn', 0)} @ {memory.get('location', 'unknown')}: "
                        f"{str(memory.get('player_input', ''))[:120]}"
                    )

        lines.extend(
            [
                "",
                f"CURRENT SITUATION: {situation}",
                "",
                "When possible, format notable lines as 'NPC[{name}]: ...' and actions as 'ACT[{name}]: ...' so downstream voice routing can separate channels.",
                char_dialogue.strip(),
            ]
        )

        return "\n".join(lines)

    def build_encounter_flavor(self, encounter_type: str = None) -> str:
        """
        Get symbolic encounter flavor for a scene.

        Args:
            encounter_type: Type of encounter (combat, social, exploration, etc.)

        Returns:
            Symbolic encounter description to influence narration
        """
        encounters = self.sample_entries("symbolic_encounters", 1)
        if encounters:
            enc = encounters[0]
            if isinstance(enc, dict):
                return f"Symbolic Element: {enc.get('encounter', '')} ({enc.get('meaning', '')})"
            return f"Symbolic Element: {enc}"
        return ""

    def build_fate_twist(self) -> str:
        """
        Generate a fate twist for narrative complication.

        Returns:
            Fate twist description
        """
        twists = self.sample_entries("fate_twists", 1)
        if twists:
            twist = twists[0]
            if isinstance(twist, dict):
                return (
                    f"Fate Twist: {twist.get('effect', '')} ({twist.get('rune', '')})"
                )
            return f"Fate Twist: {twist}"
        return ""

    def build_artifact_description(self, artifact_type: str = None) -> str:
        """
        Generate artifact description for loot/discovery.
        """
        artifacts = self.sample_entries("artifacts", 1)
        if artifacts:
            art = artifacts[0]
            if isinstance(art, dict):
                return f"{art.get('name', 'Strange artifact')}: {art.get('effect', '')} (Rune: {art.get('rune', '')})"
            return str(art)
        return "A curious object of unknown origin"

    # ============================================================================
    # YGGDRASIL INTEGRATION METHODS
    # ============================================================================

    def connect_yggdrasil(self, yggdrasil_instance, router_instance=None):
        """
        Connect Yggdrasil cognitive architecture to prompt builder.

        Args:
            yggdrasil_instance: NorseSagaCognition instance
            router_instance: YggdrasilAIRouter instance (optional)
        """
        if not HAS_YGGDRASIL:
            logger.warning("Cannot connect Yggdrasil - Yggdrasil not available")
            return False

        self.yggdrasil = yggdrasil_instance
        self.yggdrasil_router = router_instance
        self.yggdrasil_enabled = True

        logger.info("Yggdrasil cognitive architecture connected to prompt builder")
        return True

    def get_yggdrasil_context(self, game_context: GameContext) -> Dict[str, Any]:
        """
        Get cognitive context from Yggdrasil for prompt building.

        Returns:
            Dictionary with Yggdrasil insights, memories, and cognitive processing
        """
        if not self.yggdrasil_enabled or not self.yggdrasil:
            return {
                "yggdrasil_enabled": False,
                "insights": [],
                "memories": [],
                "cognitive_processing": "Yggdrasil not available",
            }

        try:
            # Get character memories if player character present
            memories = []
            if game_context.player_character:
                _pc = game_context.player_character
                _identity = (
                    _pc.get("identity", {}) if isinstance(_pc, dict)
                    else getattr(_pc, "identity", {}) or {}
                )
                char_name = (
                    _identity.get("name", "player") if isinstance(_identity, dict)
                    else getattr(_identity, "name", "player")
                )
                memories = self.yggdrasil.recall_character_memories(char_name, limit=5)

            # Get world knowledge based on location
            world_knowledge = []
            if game_context.current_location:
                world_knowledge = self.yggdrasil.query_world_knowledge(
                    game_context.current_location, category="location", limit=3
                )

            # Get Huginn insights (thought raven)
            insights = []
            if hasattr(self.yggdrasil, "huginn"):
                query = f"{game_context.current_location} {game_context.time_of_day}"
                context_hints = []
                if (
                    game_context.player_character
                    and "stats" in game_context.player_character
                ):
                    context_hints.append(
                        f"D&D Stats: {game_context.player_character['stats']}"
                    )
                if getattr(game_context, "rag_context", ""):
                    context_hints.append(f"Lore: {game_context.rag_context[:300]}")

                query_str = query
                if context_hints:
                    query_str += " Context: " + " | ".join(context_hints)
                insights = self.yggdrasil.huginn.fly(query_str, limit=3)

            return {
                "yggdrasil_enabled": True,
                "active_worlds": [
                    "Midgard",
                    "Asgard",
                    "Helheim",
                ],  # Default active worlds
                "memories": memories,
                "world_knowledge": world_knowledge,
                "insights": insights,
                "cognitive_load": 30,  # Default cognitive load
                "raven_status": {
                    "huginn_active": hasattr(self.yggdrasil, "huginn"),
                    "muninn_active": hasattr(self.yggdrasil, "muninn"),
                },
            }

        except Exception as e:
            logger.error(f"Error getting Yggdrasil context: {e}")
            return {
                "yggdrasil_enabled": False,
                "error": str(e),
                "insights": [],
                "memories": [],
                "cognitive_processing": f"Yggdrasil error: {e}",
            }

    def build_yggdrasil_context(self, game_context: GameContext) -> str:
        """
        Build Yggdrasil cognitive context string for prompts.

        Returns:
            Formatted string with Yggdrasil insights and memories
        """
        yggdrasil_data = self.get_yggdrasil_context(game_context)

        if not yggdrasil_data.get("yggdrasil_enabled", False):
            return ""

        parts = []

        # Add memories if available
        memories = yggdrasil_data.get("memories", [])
        if memories:
            memory_text = "\n".join([f"- {mem}" for mem in memories[:3]])
            parts.append(f"=== YGGDRASIL MEMORIES ===\n{memory_text}")

        # Add insights if available
        insights = yggdrasil_data.get("insights", [])
        if insights:
            insight_text = "\n".join([f"- {insight}" for insight in insights[:2]])
            parts.append(f"=== HUGINN'S INSIGHTS ===\n{insight_text}")
        # Add world knowledge if available
        world_knowledge = yggdrasil_data.get("world_knowledge", [])
        if world_knowledge:
            knowledge_text = "\n".join(
                [f"- {knowledge}" for knowledge in world_knowledge[:2]]
            )
            parts.append(f"=== WORLD KNOWLEDGE ===\n{knowledge_text}")

        # Add subjective emotional memories if available
        subjective_memories = []
        if isinstance(getattr(game_context, "yggdrasil_context", None), dict):
            subjective_memories = game_context.yggdrasil_context.get(
                "subjective_memories", []
            )
        if subjective_memories:
            memory_lines = []
            for item in subjective_memories[:3]:
                payload = item.get("data", {}) if isinstance(item, dict) else {}
                event = payload.get("event", {}) if isinstance(payload, dict) else {}
                emo_ctx = (
                    payload.get("emotional_context", {})
                    if isinstance(payload, dict)
                    else {}
                )
                dominant = emo_ctx.get("dominant_emotion", "neutral")
                charge = float(emo_ctx.get("emotional_charge", 0.0) or 0.0)
                event_type = (
                    event.get("event_type", "memory")
                    if isinstance(event, dict)
                    else "memory"
                )
                channel = event.get("channel", "") if isinstance(event, dict) else ""
                memory_lines.append(
                    f"- {event_type} remembered through {dominant} (charge={charge:.2f}, channel={channel or 'n/a'})"
                )
            if memory_lines:
                parts.append(
                    "=== MUNINN'S SUBJECTIVE MEMORIES ===\n" + "\n".join(memory_lines)
                )

        extra_ygg = getattr(game_context, "yggdrasil_context", {})
        if isinstance(extra_ygg, dict):
            npc_scene_snapshot = extra_ygg.get("npc_scene_snapshot", {})
            if isinstance(npc_scene_snapshot, dict) and npc_scene_snapshot:
                scene_summary = str(
                    npc_scene_snapshot.get("scene_summary", "") or ""
                ).strip()
                npc_briefs = npc_scene_snapshot.get("npc_briefs", [])
                recommended_actions = npc_scene_snapshot.get("recommended_actions", [])
                constraints = npc_scene_snapshot.get("constraints", [])
                lines = [
                    "=== NPC SCENE LOCK (WHO/WHAT/WHEN/HOW) ===",
                ]
                if scene_summary:
                    lines.append(f"Summary: {scene_summary}")
                for brief in npc_briefs[:8]:
                    if not isinstance(brief, dict):
                        continue
                    lines.append(
                        f"- {brief.get('name', 'Unknown')} [{brief.get('npc_id', '?')}] "
                        f"role={brief.get('role', 'person')}; class={brief.get('class', 'commoner')}; "
                        f"state={'dead' if brief.get('is_dead') else 'alive'}; "
                        f"emotion={brief.get('emotional_state', 'neutral')}; "
                        f"wearing={brief.get('wearing', 'unspecified garments')}"
                    )
                if constraints:
                    lines.append("Constraints:")
                    for item in constraints[:6]:
                        lines.append(f"  - {str(item)[:180]}")
                if recommended_actions:
                    lines.append("Likely next NPC actions:")
                    for rec in recommended_actions[:6]:
                        if not isinstance(rec, dict):
                            continue
                        lines.append(
                            f"  - {rec.get('name', 'Unknown')}: {rec.get('likely_action', 'hold current behavior')}"
                        )
                parts.append("\n".join(lines))

            wyrd_summary = str(extra_ygg.get("wyrd_summary", "") or "").strip()
            if wyrd_summary:
                parts.append(f"=== WYRD PRESSURE ===\n{wyrd_summary}")

            metaphysical_packet = extra_ygg.get("metaphysical_packet", {})
            if isinstance(metaphysical_packet, dict) and metaphysical_packet:
                lines = ["=== METAPHYSICAL UNDERCURRENTS ==="]
                runic_field = str(metaphysical_packet.get("runic_field", "") or "").strip()
                if runic_field:
                    lines.append(runic_field)
                ecosystem_imbalance = str(
                    metaphysical_packet.get("ecosystem_imbalance", "") or ""
                ).strip()
                if ecosystem_imbalance:
                    lines.append(ecosystem_imbalance)
                soul_tensions = metaphysical_packet.get("soul_tensions", [])
                if isinstance(soul_tensions, list) and soul_tensions:
                    lines.append("Soul tensions:")
                    for item in soul_tensions[:6]:
                        lines.append(f"- {str(item)[:200]}")
                cosmic_omens = metaphysical_packet.get("active_omens", [])
                if isinstance(cosmic_omens, list) and cosmic_omens:
                    lines.append("Omens:")
                    for omen in cosmic_omens[:4]:
                        lines.append(f"- {str(omen)[:180]}")
                if len(lines) > 1:
                    parts.append("\n".join(lines))

            fate_pressure = str(extra_ygg.get("fate_pressure", "") or "").strip()
            if fate_pressure:
                parts.append(fate_pressure)

            medium_term_memory = str(
                extra_ygg.get("medium_term_memory", "") or ""
            ).strip()
            if medium_term_memory:
                parts.append(medium_term_memory)

            turn_event_signals = extra_ygg.get("turn_event_signals", [])
            if isinstance(turn_event_signals, list) and turn_event_signals:
                signal_lines = [
                    f"- {str(item)[:220]}"
                    for item in turn_event_signals[:18]
                    if str(item).strip()
                ]
                if signal_lines:
                    parts.append(
                        "=== TURN EVENT SIGNALS (SCENE LOCK) ===\n"
                        + "\n".join(signal_lines)
                        + "\nPrioritize resolving these pressures before adding unrelated content."
                    )

            archetype_prompt = str(extra_ygg.get("archetype_prompt", "") or "").strip()
            archetype_memory_trace = str(
                extra_ygg.get("archetype_memory_trace", "") or ""
            ).strip()
            if archetype_prompt:
                parts.append(archetype_prompt)
            if archetype_memory_trace:
                parts.append(
                    "=== ARCHETYPE MEMORY TRACE ===\n"
                    + archetype_memory_trace
                    + "\nKeep continuity with these archetypal pressures across future turns."
                )

            # Phase 1H — Myth Engine subsystem context blocks
            _myth_blocks = [
                ("rune_intent_context", "=== RUNE INTENT (WYRD CAST) ==="),
                ("story_phase_context", "=== SAGA ARC PHASE ==="),
                ("saga_gravity_context", "=== SAGA GRAVITY (NARRATIVE PULL) ==="),
                ("wyrd_tethers_context", "=== WYRD TETHERS ==="),
                ("runic_resonance_context", "=== RUNIC RESONANCE (LOCATION) ==="),
                ("cosmic_cycle_context", "=== COSMIC CYCLE ==="),
                ("ecosystem_context", "=== METAPHYSICAL ECOSYSTEM ==="),
                ("object_agency_context", "=== OBJECT AGENCY ==="),
                ("memory_query_context", "=== MEMORY THREADS ==="),
                ("enhanced_memory_context", "=== MEMORY CONSOLIDATION ==="),
            ]
            for _key, _header in _myth_blocks:
                _val = str(extra_ygg.get(_key, "") or "").strip()
                if _val:
                    parts.append(f"{_header}\n{_val}")

        # Add RAG context if available
        if getattr(game_context, "rag_context", ""):
            parts.append(
                f"=== RELEVANT LORE & RULES (RAG) ===\n{game_context.rag_context}"
            )

        if parts:
            return "\n\n".join(parts) + "\n"
        return ""

    def build_with_yggdrasil(
        self, game_context: GameContext, player_input: str, call_type: str = "narration"
    ) -> str:
        """
        Build enhanced prompt with Yggdrasil cognitive processing.

        Args:
            game_context: Current game context
            player_input: Player's input/query
            call_type: Type of AI call (narration, dialogue, etc.)

        Returns:
            Enhanced prompt with Yggdrasil context
        """
        # Update game context with Yggdrasil data — deep-copy mutable fields to
        # prevent the enhanced_context from aliasing the caller's lists/dicts.
        import copy
        yggdrasil_context = self.get_yggdrasil_context(game_context)
        enhanced_context = GameContext(
            **{**copy.deepcopy(game_context.__dict__), **{"yggdrasil_context": yggdrasil_context}}
        )

        # Build base prompt
        if call_type == "narration":
            base_prompt = self.build_narrator_prompt(enhanced_context, player_input)
        elif call_type == "dialogue":
            base_prompt = self.build_character_voice_prompt(
                enhanced_context, player_input
            )
        else:
            base_prompt = self.build_narrator_prompt(enhanced_context, player_input)

        # Add Yggdrasil cognitive context
        yggdrasil_section = self.build_yggdrasil_context(enhanced_context)

        if yggdrasil_section:
            # Insert Yggdrasil context before the final user input
            if "=== USER INPUT ===" in base_prompt:
                parts = base_prompt.split("=== USER INPUT ===")
                enhanced_prompt = (
                    parts[0] + yggdrasil_section + "\n=== USER INPUT ===\n" + parts[1]
                )
            else:
                enhanced_prompt = base_prompt + "\n" + yggdrasil_section
        else:
            enhanced_prompt = base_prompt

        return enhanced_prompt

    def route_through_yggdrasil(
        self,
        call_type: AICallType,
        game_context: GameContext,
        player_input: str,
        additional_context: Dict[str, Any] = None,
    ) -> str:
        """
        Route AI call through Yggdrasil router with full cognitive processing.

        Args:
            call_type: Type of AI call (from AICallType enum)
            game_context: Current game context
            player_input: Player's input/query
            additional_context: Additional context for the router

        Returns:
            AI response processed through Yggdrasil
        """
        if not self.yggdrasil_enabled or not self.yggdrasil_router:
            logger.warning("Yggdrasil router not available - cannot route call")
            return ""

        try:
            # Prepare context for router
            router_context = {
                "game_context": game_context,
                "player_input": player_input,
                "prompt_builder": self,
                "charts": self.charts,
                **(additional_context or {}),
            }

            # Route through Yggdrasil via route_call (structured data path)
            response = self.yggdrasil_router.route_call(
                call_type=call_type,
                prompt=player_input or "",
                game_state=vars(game_context) if game_context else {},
                additional_context=router_context,
                use_prompt_builder=True,
            )

            return response

        except Exception as e:
            logger.error(f"Error routing through Yggdrasil: {e}")
            return ""


# Convenience function
def create_prompt_builder(data_path: str = "data") -> PromptBuilder:
    """Create and return a PromptBuilder instance."""
    return PromptBuilder(data_path)


if __name__ == "__main__":
    # Test prompt builder
    builder = PromptBuilder()

    # Create test context
    test_context = GameContext(
        current_location="Uppsala",
        location_description="The sacred center of Swedish kingship, dominated by the great temple",
        location_type="city",
        time_of_day="dusk",
        season="autumn",
        year=850,
        player_character={
            "identity": {"name": "Test Adventurer"},
            "personality": {"traits": ["Observant", "Loyal"]},
            "astrology": {"birth_rune": "Raidho"},
            "dnd5e": {"hit_points": {"current": 22, "maximum": 28}},
        },
        npcs_present=[
            {
                "identity": {"name": "Thorbjorn", "role": "Blacksmith"},
                "disposition": "neutral",
                "personality": {"traits": ["Secretive"]},
            }
        ],
        chaos_factor=1,
    )

    prompt = builder.build_narrator_prompt(
        test_context,
        "I approach the smith's forge and ask about the blade that killed my father.",
    )

    logger.info("=" * 60)
    logger.info("GENERATED PROMPT:")
    logger.info("=" * 60)
    logger.info(prompt)
