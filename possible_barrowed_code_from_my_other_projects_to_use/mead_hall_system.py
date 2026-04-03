"""
Mead Hall Population System
===========================

Dynamic NPC population management for the main mead hall.
Handles:
- Rotating skalds (entertainers)
- Bondmaid service staff
- Random patrons
- Social groups
- Ship crews seeking recruits
- Quest and bounty boards
- Rumors and conversations
- Room rentals
- Sauna/bath services

The mead hall is the hub of opportunities for adventurers.
"""

import random
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class SocialGroupType(Enum):
    """Types of social groups that visit the mead hall."""
    MERCHANTS = "merchants"
    WARRIORS = "warriors"
    NOBLES = "nobles"
    PILGRIMS = "pilgrims"
    TRAVELERS = "travelers"
    WEDDING_PARTY = "wedding_party"
    FUNERAL_WAKE = "funeral_wake"
    CELEBRATION = "celebration"
    THING_ASSEMBLY = "thing_assembly"
    TRADERS = "traders"
    RAIDERS_RETURNED = "raiders_returned"
    REFUGEES = "refugees"


@dataclass
class Skald:
    """A skald (Norse bard/poet) who performs at the mead hall."""
    id: str
    name: str
    gender: str
    specialty: str  # sagas, love songs, battle hymns, riddles
    description: str
    personality_traits: List[str]
    famous_for: str
    
    def to_npc_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "identity": {
                "name": self.name,
                "gender": self.gender,
                "role": "skald",
                "culture": "norse",
                "age": random.randint(20, 50),
            },
            "personality": {
                "traits": self.personality_traits,
                "first_impression": f"A {self.gender} skald known for {self.famous_for}",
            },
            "backstory": {
                "summary": f"A traveling skald who specializes in {self.specialty}",
                "motivation": "To spread tales and earn silver through song",
            },
            "appearance": {
                "summary": self.description,
            },
            "current_activity": f"performing {self.specialty} for the patrons",
        }


@dataclass
class MeadHallBondmaid:
    """A bondmaid who serves at the mead hall."""
    id: str
    name: str
    description: str
    personality_traits: List[str]
    special_skills: List[str]
    beauty_description: str
    
    def to_npc_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "identity": {
                "name": self.name,
                "gender": "female",
                "role": "bondmaid",
                "culture": "norse",
                "age": random.randint(18, 28),
            },
            "personality": {
                "traits": self.personality_traits,
                "first_impression": f"An exceptionally beautiful bondmaid - {self.beauty_description}",
            },
            "appearance": {
                "summary": f"{self.beauty_description}. She wears only a metal collar, wrist cuffs, and ankle cuffs.",
                "clothing": "Metal collar, wrist cuffs, ankle cuffs - nothing else",
            },
            "skills": self.special_skills,
            "current_activity": random.choice([
                "serving mead to patrons",
                "playing hnefatafl with a patron",
                "dancing gracefully between the tables",
                "attending to a patron in a private alcove",
                "warming by the central hearth",
                "carrying platters of roasted meat",
            ]),
        }


@dataclass 
class ShipCrew:
    """A viking ship crew looking for recruits."""
    ship_name: str
    captain_name: str
    crew_size: int
    destination: str
    purpose: str  # raiding, trading, exploration, war
    recruitment_needs: List[str]  # warrior, navigator, healer, etc.
    departure_time: str
    reward_type: str
    danger_level: str
    
    def to_quest(self) -> Dict[str, Any]:
        return {
            "id": f"crew_{self.ship_name.lower().replace(' ', '_')}",
            "title": f"Join the {self.ship_name}",
            "type": "ship_recruitment",
            "giver": self.captain_name,
            "description": f"Captain {self.captain_name} of the {self.ship_name} seeks crew for a {self.purpose} expedition to {self.destination}.",
            "objectives": [
                f"Speak with Captain {self.captain_name}",
                f"Join the crew of {self.crew_size} sailors",
                f"Set sail for {self.destination}",
            ],
            "requirements": self.recruitment_needs,
            "rewards": self.reward_type,
            "departure": self.departure_time,
            "danger": self.danger_level,
        }


@dataclass
class QuestPosting:
    """A quest posted on the board."""
    id: str
    title: str
    description: str
    quest_type: str  # bounty, exploration, escort, retrieval, investigation
    reward_silver: int
    danger_level: str
    location: str
    posted_by: str
    expires_in: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "type": self.quest_type,
            "reward": f"{self.reward_silver} silver",
            "danger": self.danger_level,
            "location": self.location,
            "posted_by": self.posted_by,
            "expires": self.expires_in,
        }


@dataclass
class Rumor:
    """A rumor being discussed in the mead hall."""
    id: str
    topic: str
    content: str
    source_type: str  # traveler, merchant, warrior, local
    reliability: str  # reliable, questionable, wild
    related_quest: Optional[str] = None
    related_location: Optional[str] = None
    
    def to_conversation(self) -> str:
        return f'A {self.source_type} mentions: "{self.content}"'


class MeadHallPopulationManager:
    """
    Manages the dynamic population of the main mead hall.
    Loads data from YAML files in data/mead_hall/
    """
    
    def __init__(self, data_path: str = None):
        self.data_path = Path(data_path) if data_path else Path("data")
        self.mead_hall_data_path = self.data_path / "mead_hall"

        # Initialize NPC pools - load from YAML character sheets first, then config YAML, then hardcoded defaults
        self._load_skalds()
        self._load_bondmaids()
        self._load_social_groups()
        self._load_ship_crews()
        self._load_captain_sheets()
        self._load_quests()
        self._load_bounties()
        self._load_rumors()

        # Current state — pools hold full YAML dicts when sheets are available, else dataclass instances
        self.current_skald: Optional[Any] = None
        self.current_bondmaids: List[Any] = []
        self.current_patrons: List[Dict] = []
        self.current_social_group: Optional[Dict] = None
        self.current_ship_crews: List[ShipCrew] = []

        # Timing
        self.last_rotation_time: Optional[datetime] = None
        self.turns_since_rotation: int = 0

        try:
            _display_path = self.mead_hall_data_path.relative_to(Path.cwd())
        except (ValueError, AttributeError):
            _display_path = self.mead_hall_data_path
        logger.info(f"MeadHallPopulationManager initialized from {_display_path}")
    
    def _load_yaml(self, filename: str) -> Optional[Dict]:
        """Load a YAML file from the mead_hall data directory."""
        filepath = self.mead_hall_data_path / filename
        if filepath.exists():
            try:
                import yaml
                with open(filepath, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Failed to load {filename}: {e}")
        return None

    def _load_character_sheets(self, pattern: str) -> List[Dict[str, Any]]:
        """Load full character YAML sheets matching a glob pattern from data/characters/mead_hall/."""
        import yaml
        sheet_dir = self.data_path / "characters" / "mead_hall"
        if not sheet_dir.exists():
            return []
        sheets = []
        for path in sorted(sheet_dir.glob(pattern)):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if isinstance(data, dict):
                    data.setdefault("id", path.stem)
                    sheets.append(data)
            except Exception as exc:
                logger.warning("Failed to load character sheet %s: %s", path, exc)
        return sheets

    def _load_captain_sheets(self) -> None:
        """Build a lookup map of captain YAML sheets keyed by normalised ship name and captain name."""
        sheets = self._load_character_sheets("mh_captain_*.yaml")
        self.captain_sheet_map: Dict[str, Dict[str, Any]] = {}
        for sheet in sheets:
            identity = sheet.get("identity", {}) if isinstance(sheet.get("identity"), dict) else {}
            ship = str(identity.get("ship", "")).strip().lower().replace(" ", "_")
            name = str(identity.get("name", sheet.get("id", ""))).strip().lower().replace(" ", "_")
            if ship:
                self.captain_sheet_map[ship] = sheet
            if name:
                self.captain_sheet_map[name] = sheet
        logger.info("Loaded %d captain sheets into lookup map", len(sheets))
    
    def _load_skalds(self):
        """Load skalds from character sheets, then config YAML, then hardcoded defaults."""
        sheets = self._load_character_sheets("mh_skald_*.yaml")
        if sheets:
            self.skald_pool = sheets
            logger.info("Loaded %d skald sheets from data/characters/mead_hall/", len(sheets))
            return

        data = self._load_yaml("skalds.yaml")
        self.skald_pool = []
        if data and "skalds" in data:
            for s in data["skalds"]:
                self.skald_pool.append(Skald(
                    id=s.get("id", f"skald_{len(self.skald_pool)}"),
                    name=s.get("name", "Unknown Skald"),
                    gender=s.get("gender", "male"),
                    specialty=s.get("specialty", "sagas"),
                    description=s.get("description", "A traveling poet"),
                    personality_traits=s.get("personality_traits", ["artistic"]),
                    famous_for=s.get("famous_for", "their performances")
                ))
            logger.info(f"Loaded {len(self.skald_pool)} skalds from skalds.yaml")
        else:
            self._init_skald_pool_defaults()
    
    def _load_bondmaids(self):
        """Load bondmaids from character sheets, then config YAML, then hardcoded defaults."""
        sheets = self._load_character_sheets("mh_bondmaid_*.yaml")
        if sheets:
            self.bondmaid_pool = sheets
            logger.info("Loaded %d bondmaid sheets from data/characters/mead_hall/", len(sheets))
            return

        data = self._load_yaml("bondmaids.yaml")
        self.bondmaid_pool = []
        if data and "bondmaids" in data:
            for b in data["bondmaids"]:
                appearance = b.get("appearance", {})
                self.bondmaid_pool.append(MeadHallBondmaid(
                    id=b.get("id", f"bondmaid_{len(self.bondmaid_pool)}"),
                    name=b.get("name", "Unknown"),
                    description=f"{appearance.get('hair', '')} hair, {appearance.get('eyes', '')} eyes, {appearance.get('build', '')} build",
                    personality_traits=b.get("personality_traits", ["quiet"]),
                    special_skills=b.get("special_skills", []),
                    beauty_description=appearance.get("beauty_description", "beautiful")
                ))
            logger.info(f"Loaded {len(self.bondmaid_pool)} bondmaids from bondmaids.yaml")
        else:
            self._init_bondmaid_pool_defaults()
    
    def _load_social_groups(self):
        """Load social groups from YAML or use defaults."""
        data = self._load_yaml("social_groups.yaml")
        self.social_group_templates = []
        
        if data and "social_groups" in data:
            for g in data["social_groups"]:
                size_range = g.get("size_range", [4, 10])
                self.social_group_templates.append({
                    "type": (lambda t: SocialGroupType(t) if t in [e.value for e in SocialGroupType] else SocialGroupType.TRAVELERS)(g.get("type", "travelers")),
                    "name": g.get("name", "Travelers"),
                    "size": tuple(size_range),
                    "description": g.get("description", "A group of travelers"),
                    "appearance": g.get("appearance", ""),
                    "potential_quests": g.get("potential_interactions", []),
                })
            logger.info(f"Loaded {len(self.social_group_templates)} social groups from YAML")
        else:
            self._init_social_groups_defaults()
    
    def _load_ship_crews(self):
        """Load ship crews from YAML or use defaults."""
        data = self._load_yaml("ship_crews.yaml")
        self.ship_crew_templates = []
        
        if data and "ship_crews" in data:
            for c in data["ship_crews"]:
                captain = c.get("captain", {})
                self.ship_crew_templates.append(ShipCrew(
                    ship_name=c.get("ship_name", "Unknown Ship"),
                    captain_name=captain.get("name", "Unknown Captain"),
                    crew_size=c.get("crew_size", 30),
                    destination=c.get("destination", "unknown"),
                    purpose=c.get("purpose", "trading"),
                    recruitment_needs=c.get("recruitment_needs", ["sailors"]),
                    departure_time=c.get("departure_time", "soon"),
                    reward_type=c.get("reward_type", "silver"),
                    danger_level=c.get("danger_level", "moderate")
                ))
            logger.info(f"Loaded {len(self.ship_crew_templates)} ship crews from YAML")
        else:
            self._init_ship_crews_defaults()
    
    def _load_quests(self):
        """Load quests from YAML or use defaults."""
        data = self._load_yaml("quests.yaml")
        self.quest_templates = []
        
        if data and "quests" in data:
            for q in data["quests"]:
                self.quest_templates.append(QuestPosting(
                    id=q.get("id", f"quest_{len(self.quest_templates)}"),
                    title=q.get("title", "Unknown Quest"),
                    description=q.get("description", "A quest awaits"),
                    quest_type=q.get("quest_type", "adventure"),
                    reward_silver=q.get("reward_silver", 50),
                    danger_level=q.get("danger_level", "moderate"),
                    location=q.get("location", "Unknown"),
                    posted_by=q.get("posted_by", "Anonymous"),
                    expires_in=q.get("expires_in", "ongoing")
                ))
            logger.info(f"Loaded {len(self.quest_templates)} quests from YAML")
        else:
            self._init_quest_defaults()
    
    def _load_bounties(self):
        """Load bounties from YAML or use defaults."""
        data = self._load_yaml("bounties.yaml")
        self.bounty_templates = []
        
        if data and "bounties" in data:
            for b in data["bounties"]:
                self.bounty_templates.append({
                    "id": b.get("id", f"bounty_{len(self.bounty_templates)}"),
                    "target": b.get("target", "Unknown"),
                    "crime": b.get("crime", "Crimes against the people"),
                    "description": b.get("description", ""),
                    "reward_alive": b.get("reward_alive", 100),
                    "reward_dead": b.get("reward_dead", 50),
                    "last_seen": b.get("last_seen", "Unknown"),
                    "danger": b.get("danger_level", "moderate"),
                    "appearance": b.get("appearance", ""),
                })
            logger.info(f"Loaded {len(self.bounty_templates)} bounties from YAML")
        else:
            self._init_bounty_defaults()
    
    def _load_rumors(self):
        """Load rumors from YAML or use defaults."""
        data = self._load_yaml("rumors.yaml")
        self.rumor_pool = []
        
        if data and "rumors" in data:
            for r in data["rumors"]:
                self.rumor_pool.append(Rumor(
                    id=r.get("id", f"rumor_{len(self.rumor_pool)}"),
                    topic=r.get("topic", "Gossip"),
                    content=r.get("content", "They say..."),
                    source_type=r.get("source_type", "patron"),
                    reliability=r.get("reliability", "questionable"),
                    related_quest=r.get("related_quest"),
                    related_location=r.get("related_location")
                ))
            logger.info(f"Loaded {len(self.rumor_pool)} rumors from YAML")
        else:
            self._init_rumor_defaults()
    
    # Default initialization methods (fallback if YAML not found)
    def _init_skald_pool_defaults(self):
        """Initialize the pool of available skalds."""
        self.skald_pool = [
            Skald(
                id="skald_bjorn",
                name="Bjorn Silvertongue",
                gender="male",
                specialty="heroic sagas",
                description="A weathered man with a powerful voice and eyes that have seen many battles",
                personality_traits=["dramatic", "wise", "melancholic"],
                famous_for="his epic recitation of the Völsunga saga"
            ),
            Skald(
                id="skald_freydis",
                name="Freydis the Fair",
                gender="female",
                specialty="love songs",
                description="A stunningly beautiful woman with hair like spun gold and a voice like honey",
                personality_traits=["passionate", "flirtatious", "clever"],
                famous_for="her heartbreaking ballads of doomed lovers"
            ),
            Skald(
                id="skald_ragnar",
                name="Ragnar Bloodsong",
                gender="male",
                specialty="battle hymns",
                description="A scarred warrior-poet whose songs can drive men to battle-frenzy",
                personality_traits=["fierce", "proud", "inspiring"],
                famous_for="composing songs during actual battles"
            ),
            Skald(
                id="skald_sigrid",
                name="Sigrid Riddleweaver",
                gender="female",
                specialty="riddles and wisdom poetry",
                description="An enigmatic woman with knowing eyes and a mysterious smile",
                personality_traits=["mysterious", "intellectual", "playful"],
                famous_for="riddles that have stumped even jarls"
            ),
            Skald(
                id="skald_erik",
                name="Erik the Wanderer",
                gender="male",
                specialty="tales of distant lands",
                description="A well-traveled man with foreign trinkets woven into his beard",
                personality_traits=["curious", "talkative", "worldly"],
                famous_for="tales of Miklagard and the lands of the Saracens"
            ),
            Skald(
                id="skald_inga",
                name="Inga Flamehair",
                gender="female",
                specialty="drinking songs and comedy",
                description="A vivacious redhead whose laughter is infectious",
                personality_traits=["bawdy", "cheerful", "bold"],
                famous_for="songs that make even dour warriors spit out their mead laughing"
            ),
        ]
    
    def _init_bondmaid_pool_defaults(self):
        """Initialize the pool of mead hall bondmaids."""
        self.bondmaid_pool = [
            MeadHallBondmaid(
                id="mh_bondmaid_astrid",
                name="Astrid",
                description="Slender with long silver-blonde hair and ice-blue eyes",
                personality_traits=["graceful", "quiet", "attentive"],
                special_skills=["massage", "hnefatafl", "singing"],
                beauty_description="ethereal Nordic beauty with delicate features and porcelain skin"
            ),
            MeadHallBondmaid(
                id="mh_bondmaid_runa",
                name="Runa",
                description="Curvaceous with flowing auburn hair and green eyes",
                personality_traits=["warm", "nurturing", "sensual"],
                special_skills=["bathing service", "conversation", "dancing"],
                beauty_description="voluptuous figure with fiery hair cascading to her hips"
            ),
            MeadHallBondmaid(
                id="mh_bondmaid_svala",
                name="Svala",
                description="Athletic with raven-black hair and dark eyes",
                personality_traits=["playful", "competitive", "spirited"],
                special_skills=["wrestling", "board games", "acrobatics"],
                beauty_description="toned physique with exotic dark features rare in these lands"
            ),
            MeadHallBondmaid(
                id="mh_bondmaid_thyra",
                name="Thyra",
                description="Petite with honey-gold hair and amber eyes",
                personality_traits=["sweet", "shy", "devoted"],
                special_skills=["music", "poetry", "weaving"],
                beauty_description="doll-like perfection with an innocent expression"
            ),
            MeadHallBondmaid(
                id="mh_bondmaid_ylva",
                name="Ylva",
                description="Tall with wheat-blonde braids and storm-grey eyes",
                personality_traits=["proud", "intelligent", "commanding"],
                special_skills=["leadership", "negotiation", "storytelling"],
                beauty_description="statuesque beauty with an aristocratic bearing suggesting noble birth"
            ),
            MeadHallBondmaid(
                id="mh_bondmaid_sigrun",
                name="Sigrun",
                description="Lithe with copper hair and freckled skin",
                personality_traits=["mischievous", "quick-witted", "adaptable"],
                special_skills=["sleight of hand", "information gathering", "seduction"],
                beauty_description="captivating with a knowing smile and eyes full of secrets"
            ),
            MeadHallBondmaid(
                id="mh_bondmaid_hild",
                name="Hild",
                description="Strong with sun-kissed skin and golden hair",
                personality_traits=["bold", "protective", "loyal"],
                special_skills=["self-defense", "swimming", "endurance"],
                beauty_description="athletic goddess with muscles beneath silk-smooth skin"
            ),
            MeadHallBondmaid(
                id="mh_bondmaid_embla",
                name="Embla",
                description="Willowy with platinum hair and pale blue eyes",
                personality_traits=["dreamy", "artistic", "otherworldly"],
                special_skills=["rune-reading", "herb lore", "meditation"],
                beauty_description="otherworldly beauty as if touched by the Alfar"
            ),
            MeadHallBondmaid(
                id="mh_bondmaid_gudrun",
                name="Gudrun",
                description="Buxom with chestnut hair and warm brown eyes",
                personality_traits=["motherly", "comforting", "wise"],
                special_skills=["cooking", "healing", "counseling"],
                beauty_description="lush feminine curves and a welcoming warmth"
            ),
            MeadHallBondmaid(
                id="mh_bondmaid_valdis",
                name="Valdis",
                description="Exotic with midnight hair and violet eyes",
                personality_traits=["mysterious", "passionate", "intense"],
                special_skills=["exotic dance", "massage", "fortune telling"],
                beauty_description="striking foreign beauty with hypnotic eyes"
            ),
            MeadHallBondmaid(
                id="mh_bondmaid_eira",
                name="Eira",
                description="Elfin with white-blonde hair and sea-green eyes",
                personality_traits=["gentle", "healing", "serene"],
                special_skills=["wound care", "calming presence", "bathing arts"],
                beauty_description="delicate fairy-like features and an aura of peace"
            ),
            MeadHallBondmaid(
                id="mh_bondmaid_torunn",
                name="Torunn",
                description="Fierce with wild red curls and blazing green eyes",
                personality_traits=["fiery", "proud", "untamed"],
                special_skills=["weapon handling", "riding", "challenge games"],
                beauty_description="wild beauty like a flame that cannot be contained"
            ),
        ]
    
    def _init_social_groups_defaults(self):
        """Initialize templates for social groups."""
        self.social_group_templates = [
            {
                "type": SocialGroupType.MERCHANTS,
                "name": "Merchant Guild Delegation",
                "size": (4, 8),
                "description": "A group of wealthy merchants discussing trade routes and opportunities",
                "potential_quests": ["escort cargo", "investigate theft", "negotiate deals"],
            },
            {
                "type": SocialGroupType.WARRIORS,
                "name": "Veteran Warband",
                "size": (5, 12),
                "description": "Battle-hardened warriors sharing tales of past campaigns",
                "potential_quests": ["join raid", "rescue mission", "mercenary work"],
            },
            {
                "type": SocialGroupType.NOBLES,
                "name": "Noble Retinue",
                "size": (3, 6),
                "description": "A minor noble with their retainers, conducting political business",
                "potential_quests": ["deliver message", "political intrigue", "bodyguard duty"],
            },
            {
                "type": SocialGroupType.PILGRIMS,
                "name": "Temple Pilgrims",
                "size": (6, 15),
                "description": "Devout travelers on a sacred journey to holy sites",
                "potential_quests": ["escort pilgrims", "recover relic", "cleanse shrine"],
            },
            {
                "type": SocialGroupType.WEDDING_PARTY,
                "name": "Wedding Celebration",
                "size": (10, 25),
                "description": "A joyous wedding party celebrating a union between families",
                "potential_quests": ["wedding gift retrieval", "entertain guests", "rival family trouble"],
            },
            {
                "type": SocialGroupType.FUNERAL_WAKE,
                "name": "Funeral Wake",
                "size": (8, 20),
                "description": "Mourners honoring a fallen warrior with drinks and remembrance",
                "potential_quests": ["avenge the fallen", "recover inheritance", "fulfill dying wish"],
            },
        ]
    
    def _init_ship_crews_defaults(self):
        """Initialize ship crew templates."""
        self.ship_crew_templates = [
            ShipCrew(
                ship_name="Storm Serpent",
                captain_name="Olaf Ironjaw",
                crew_size=45,
                destination="the Frankish coast",
                purpose="raiding",
                recruitment_needs=["warriors", "shield-bearers"],
                departure_time="in three days",
                reward_type="Share of plunder",
                danger_level="high"
            ),
            ShipCrew(
                ship_name="Silver Wave",
                captain_name="Gunnar the Trader",
                crew_size=30,
                destination="Miklagard",
                purpose="trading",
                recruitment_needs=["guards", "translator", "healer"],
                departure_time="next week",
                reward_type="Silver wages + trade bonus",
                danger_level="moderate"
            ),
            ShipCrew(
                ship_name="Northern Star",
                captain_name="Leif Farsight",
                crew_size=35,
                destination="unknown western lands",
                purpose="exploration",
                recruitment_needs=["experienced sailors", "scouts", "hardy souls"],
                departure_time="when the weather turns",
                reward_type="Land claims + discovery fame",
                danger_level="extreme"
            ),
            ShipCrew(
                ship_name="Blood Raven",
                captain_name="Sigurd Snake-Eye",
                crew_size=60,
                destination="the English kingdoms",
                purpose="war",
                recruitment_needs=["berserkers", "archers", "siege experts"],
                departure_time="at the spring thaw",
                reward_type="War plunder + land",
                danger_level="very high"
            ),
        ]
    
    def _init_quest_defaults(self):
        """Initialize quest board postings."""
        self.quest_templates = [
            QuestPosting(
                id="quest_burial_mound",
                title="Clear the Haunted Burial Mound",
                description="The old kings' mound northeast of town has become restless. Draugr walk at night. Clear the tomb and claim whatever treasure you find.",
                quest_type="exploration",
                reward_silver=200,
                danger_level="high",
                location="Konungshaugr Burial Mound",
                posted_by="Temple of Odin",
                expires_in="ongoing"
            ),
            QuestPosting(
                id="quest_outlaw_camp",
                title="Bounty: Outlaw Band",
                description="A band of outlaws preys on travelers on the northern road. Bring proof of their defeat for reward.",
                quest_type="bounty",
                reward_silver=150,
                danger_level="moderate",
                location="Northern Forest Road",
                posted_by="Merchant Guild",
                expires_in="30 days"
            ),
            QuestPosting(
                id="quest_missing_daughter",
                title="Find the Missing Daughter",
                description="Merchant Bjorn's daughter vanished near the old battlefield. He suspects foul play or worse.",
                quest_type="investigation",
                reward_silver=100,
                danger_level="unknown",
                location="Ancient Battlefield",
                posted_by="Bjorn the Fat",
                expires_in="urgent"
            ),
            QuestPosting(
                id="quest_wolf_pack",
                title="Wolf Pack Terrorizing Farms",
                description="An unusually large wolf pack led by a monstrous alpha threatens outlying farms. Some say the alpha is no natural beast.",
                quest_type="hunt",
                reward_silver=80,
                danger_level="moderate",
                location="Western Farmlands",
                posted_by="Farmers' Collective",
                expires_in="7 days"
            ),
            QuestPosting(
                id="quest_cursed_sword",
                title="Retrieve the Cursed Blade",
                description="The sword Grimfang lies in a haunted barrow. It is needed to lift a family curse, but beware - the blade is guarded.",
                quest_type="retrieval",
                reward_silver=300,
                danger_level="very high",
                location="Grimfang's Barrow",
                posted_by="Lady Sigrid",
                expires_in="60 days"
            ),
        ]
        self.bounty_board = []
    
    def _init_bounty_defaults(self):
        """Initialize bounty board postings."""
        self.bounty_templates = [
            {
                "target": "Erik the Red-Hand",
                "crime": "Murder of three merchants",
                "reward_alive": 200,
                "reward_dead": 100,
                "last_seen": "Northern wilderness",
                "danger": "Dangerous warrior with two accomplices",
            },
            {
                "target": "The Shadow",
                "crime": "Theft from the temple treasury",
                "reward_alive": 150,
                "reward_dead": 50,
                "last_seen": "Unknown - strikes at night",
                "danger": "Cunning and stealthy, possibly uses seidr",
            },
            {
                "target": "Grim Wolfbane",
                "crime": "Kidnapping for ransom",
                "reward_alive": 180,
                "reward_dead": 120,
                "last_seen": "Cave system in eastern hills",
                "danger": "Commands a small warband",
            },
        ]
    
    def _init_rumor_defaults(self):
        """Initialize rumor pool."""
        self.rumor_pool = [
            Rumor(
                id="rumor_burial_treasure",
                topic="Ancient Treasure",
                content="They say the burial mounds to the north contain the gold of forgotten kings, but draugr guard it jealously.",
                source_type="old warrior",
                reliability="reliable",
                related_quest="quest_burial_mound",
                related_location="Konungshaugr"
            ),
            Rumor(
                id="rumor_war_brewing",
                topic="Coming War",
                content="The Danes are gathering ships. War is coming, and there'll be plenty of work for those who can swing a sword.",
                source_type="merchant",
                reliability="reliable",
                related_quest=None,
                related_location="Denmark"
            ),
            Rumor(
                id="rumor_haunted_battlefield",
                topic="Haunted Place",
                content="I saw lights on the old battlefield last full moon. The dead warriors still fight there, they say.",
                source_type="frightened traveler",
                reliability="questionable",
                related_quest="quest_missing_daughter",
                related_location="Ancient Battlefield"
            ),
            Rumor(
                id="rumor_seer_vision",
                topic="Prophecy",
                content="The völva at the temple spoke of a stranger who would change Uppsala's fate. She was looking right at the door when she said it.",
                source_type="temple acolyte",
                reliability="mysterious",
                related_quest=None,
                related_location="Temple"
            ),
            Rumor(
                id="rumor_magic_weapon",
                topic="Legendary Weapon",
                content="My grandfather swore he saw the Ulfberht blade that could cut through shields like cloth. It's buried with its last owner somewhere nearby.",
                source_type="drunk patron",
                reliability="questionable",
                related_quest="quest_cursed_sword",
                related_location="Unknown barrow"
            ),
            Rumor(
                id="rumor_troll_sighting",
                topic="Monster Sighting",
                content="Farmers say a troll has moved into the caves by the waterfall. Lost two sheep to it already.",
                source_type="local farmer",
                reliability="reliable",
                related_quest=None,
                related_location="Waterfall Caves"
            ),
        ]
    
    def populate_mead_hall(self, turn_number: int = 0) -> Dict[str, Any]:
        """
        Generate the current population of the mead hall.
        
        Args:
            turn_number: Current game turn for rotation timing
            
        Returns:
            Dict with all current NPCs and features
        """
        result = {
            "skald": None,
            "bondmaids": [],
            "patrons": [],
            "social_group": None,
            "ship_crews": [],
            "quest_board": [],
            "bounty_board": [],
            "active_rumors": [],
            "services": {
                "rooms_available": random.randint(2, 6),
                "room_prices": {"day": 5, "week": 25, "month": 80},
                "sauna_open": True,
                "bath_available": True,
            }
        }
        
        # Rotate if needed (every 10 turns or so)
        should_rotate = (turn_number - self.turns_since_rotation) >= 10
        
        # Select current skald (1 at a time)
        if (should_rotate or not self.current_skald) and self.skald_pool:
            self.current_skald = random.choice(self.skald_pool)
        if isinstance(self.current_skald, dict):
            _id = self.current_skald.get("identity", {})
            _spec = str(_id.get("specialization") or _id.get("occupation") or "songs")
            result["skald"] = {**self.current_skald, "current_activity": f"performing {_spec} for the patrons"}
        else:
            result["skald"] = self.current_skald.to_npc_dict()

        # Select bondmaids (6 from pool of 12)
        if should_rotate or len(self.current_bondmaids) < 6:
            self.current_bondmaids = random.sample(self.bondmaid_pool, min(6, len(self.bondmaid_pool)))
        _bm_activities = [
            "serving mead to patrons",
            "playing hnefatafl with a patron",
            "dancing gracefully between the tables",
            "attending to a patron in a private alcove",
            "warming by the central hearth",
            "carrying platters of roasted meat",
        ]
        bondmaid_npcs = []
        for b in self.current_bondmaids:
            if isinstance(b, dict):
                bondmaid_npcs.append({**b, "current_activity": random.choice(_bm_activities)})
            else:
                bondmaid_npcs.append(b.to_npc_dict())
        result["bondmaids"] = bondmaid_npcs
        
        # Generate random patrons (12 people)
        result["patrons"] = self._generate_random_patrons(12)
        
        # Maybe add a social group (30% chance)
        if random.random() < 0.30 or should_rotate:
            group_template = random.choice(self.social_group_templates)
            size = random.randint(*group_template["size"])
            result["social_group"] = {
                "type": group_template["type"].value,
                "name": group_template["name"],
                "size": size,
                "description": group_template["description"],
                "potential_quests": group_template["potential_quests"],
            }
        
        # Ship crews (1-2 recruiting)
        num_crews = random.randint(1, 2)
        result["ship_crews"] = [
            crew.to_quest() for crew in random.sample(
                self.ship_crew_templates, min(num_crews, len(self.ship_crew_templates))
            )
        ]
        
        # Quest board (3-5 active quests)
        num_quests = random.randint(3, 5)
        result["quest_board"] = [
            q.to_dict() for q in random.sample(self.quest_templates, min(num_quests, len(self.quest_templates)))
        ]
        
        # Bounty board (1-3 active bounties)
        num_bounties = random.randint(1, 3)
        result["bounty_board"] = random.sample(self.bounty_templates, min(num_bounties, len(self.bounty_templates)))
        
        # Active rumors (2-4)
        num_rumors = random.randint(2, 4)
        selected_rumors = random.sample(self.rumor_pool, min(num_rumors, len(self.rumor_pool)))
        result["active_rumors"] = [r.to_conversation() for r in selected_rumors]
        
        if should_rotate:
            self.turns_since_rotation = turn_number
        
        return result
    
    def _generate_random_patrons(self, count: int) -> List[Dict[str, Any]]:
        """Generate random patron NPCs."""
        patron_types = [
            ("warrior", ["battle-scarred", "boastful", "drinking heavily", "arm-wrestling"]),
            ("merchant", ["counting coins", "negotiating", "examining goods", "suspicious"]),
            ("farmer", ["weathered hands", "simple clothes", "enjoying rare visit", "wide-eyed"]),
            ("traveler", ["dusty from the road", "tired", "asking questions", "foreign accent"]),
            ("craftsman", ["calloused hands", "proud of work", "seeking commission", "skilled"]),
            ("sailor", ["sea-weathered", "restless", "telling tales", "looking for crew"]),
            ("hunter", ["furs and leather", "quiet", "keen-eyed", "selling pelts"]),
            ("thrall", ["accompanying master", "serving", "quiet", "watchful"]),
        ]
        
        patrons = []
        for i in range(count):
            ptype, traits = random.choice(patron_types)
            gender = random.choice(["male", "female"]) if ptype != "thrall" else random.choice(["male", "female"])
            
            # Generate Norse-style name
            if gender == "male":
                first_names = ["Bjorn", "Erik", "Gunnar", "Harald", "Ivar", "Knut", "Leif", "Magnus", "Olaf", "Ragnar", "Sigurd", "Thor", "Ulf"]
            else:
                first_names = ["Astrid", "Freya", "Gudrun", "Helga", "Ingrid", "Sigrid", "Thyra", "Yrsa", "Ragnhild", "Solveig"]
            
            name = random.choice(first_names)
            
            patrons.append({
                "id": f"patron_{i}_{name.lower()}",
                "identity": {
                    "name": name,
                    "gender": gender,
                    "role": ptype,
                    "culture": "norse",
                },
                "current_activity": random.choice(traits),
                "is_temporary": True,
            })
        
        return patrons
    
    def get_all_npcs_for_scene(self, turn_number: int = 0) -> List[Dict[str, Any]]:
        """Get all NPCs currently in the mead hall as a flat list."""
        population = self.populate_mead_hall(turn_number)

        npcs = []

        # Add skald
        if population["skald"]:
            npcs.append(population["skald"])

        # Add bondmaids
        npcs.extend(population["bondmaids"])

        # Add patrons
        npcs.extend(population["patrons"])

        # Add ship crew captains as full NPC entries (from YAML sheets where available)
        seen_captain_ids: set = set()
        for crew_quest in population.get("ship_crews", []):
            ship_raw = str(crew_quest.get("title", "")).replace("Join the ", "").strip()
            captain_raw = str(crew_quest.get("giver", "")).strip()
            ship_key = ship_raw.lower().replace(" ", "_")
            captain_key = captain_raw.lower().replace(" ", "_")
            captain_sheet = self.captain_sheet_map.get(ship_key) or self.captain_sheet_map.get(captain_key)
            if captain_sheet:
                cid = str(captain_sheet.get("id", captain_key))
                if cid not in seen_captain_ids:
                    seen_captain_ids.add(cid)
                    npcs.append({
                        **captain_sheet,
                        "current_activity": f"recruiting crew for the {ship_raw}",
                    })
            else:
                # Fallback: minimal entry so captain still appears in scene
                cid = f"captain_{captain_key}"
                if cid not in seen_captain_ids:
                    seen_captain_ids.add(cid)
                    npcs.append({
                        "id": cid,
                        "identity": {
                            "name": captain_raw,
                            "role": "ship_captain",
                            "culture": "norse",
                        },
                        "current_activity": f"recruiting crew for the {ship_raw}",
                        "is_temporary": True,
                    })

        # Add social group members (simplified)
        if population["social_group"]:
            group = population["social_group"]
            for i in range(min(group["size"], 5)):  # Only detail first 5
                npcs.append({
                    "id": f"group_member_{i}",
                    "identity": {
                        "name": f"{group['name']} Member",
                        "role": group["type"],
                    },
                    "current_activity": f"part of {group['name']}",
                    "is_temporary": True,
                })

        return npcs

    def get_current_npcs(self, turn_number: int = 0) -> List[Dict[str, Any]]:
        """Compatibility shim for engine callers expecting legacy method names."""
        try:
            return self.get_all_npcs_for_scene(turn_number)
        except Exception as exc:
            logger.warning("get_current_npcs fallback failed: %s", exc)
            return []
    
    def get_scene_description(self, turn_number: int = 0) -> str:
        """Generate a rich description of the current mead hall scene."""
        population = self.populate_mead_hall(turn_number)
        
        desc_parts = []
        
        # Skald
        if population["skald"]:
            skald = population["skald"]
            desc_parts.append(f"The skald {skald['identity']['name']} performs near the hearth, {skald['current_activity']}.")
        
        # Bondmaids
        if population["bondmaids"]:
            bondmaid_names = [b["identity"]["name"] for b in population["bondmaids"][:3]]
            desc_parts.append(f"Beautiful collared bondmaids including {', '.join(bondmaid_names)} move gracefully through the hall, serving patrons and attending to their needs.")
        
        # Patrons
        patron_count = len(population["patrons"])
        desc_parts.append(f"About {patron_count} patrons fill the benches - warriors, merchants, and travelers.")
        
        # Social group
        if population["social_group"]:
            group = population["social_group"]
            desc_parts.append(f"A {group['name']} of {group['size']} people has gathered in one corner, {group['description'].lower()}.")
        
        # Ship crews
        if population["ship_crews"]:
            crew = population["ship_crews"][0]
            desc_parts.append(f"A ship captain seeking crew for the {crew['title'].replace('Join the ', '')} speaks with potential recruits.")
        
        # Rumors
        if population["active_rumors"]:
            desc_parts.append("Conversations drift through the smoky air - rumors of treasure, war, and strange happenings.")
        
        return " ".join(desc_parts)


# Factory function
def create_mead_hall_manager(data_path: str = None) -> MeadHallPopulationManager:
    """Create a mead hall population manager."""
    return MeadHallPopulationManager(data_path)
