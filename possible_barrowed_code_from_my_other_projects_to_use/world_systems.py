#!/usr/bin/env python3
"""
World Systems - Location Grid, Party, Loyalty, and Factions
============================================================

Implements:
1. Local Grid System - Sub-locations within cities (buildings, areas)
2. Party System - Allies list + active party management
3. Loyalty System - NPC relationship tracking
4. Faction System - Group reputation tracking
5. NPC Behavior Rules - Social appropriateness

Key Principles:
- NPCs stay in their designated locations, don't follow you
- Party members must be recruited and can leave
- Loyalty changes based on actions and shared experiences
- Factions have reputations that affect how NPCs treat you
- NPCs behave according to personality + situation, not as annoying stereotypes
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# Flag to indicate world systems are available
HAS_WORLD_SYSTEMS = True


# ============================================================================
# LOCAL GRID SYSTEM - Sub-locations within cities
# ============================================================================

class SubLocationType(Enum):
    """Types of sub-locations within a city."""
    MEAD_HALL = "mead_hall"           # Social gathering, adventurers
    JARL_HALL = "jarl_hall"           # Ruler's seat
    TEMPLE = "temple"                  # Religious site
    GROVE = "grove"                    # Sacred grove
    MARKET = "market"                  # Trading
    FORGE = "forge"                    # Blacksmith
    HEALER_HUT = "healer_hut"         # Healing services
    SEER_HUT = "seer_hut"             # Völva/seer dwelling
    DOCKS = "docks"                    # Ships, fishing
    BARRACKS = "barracks"              # Warriors
    TAVERN = "tavern"                  # Drinking, rumors
    RESIDENTIAL = "residential"        # Homes
    OUTSKIRTS = "outskirts"           # City edges
    CEMETERY = "cemetery"              # Burial mounds
    TRAINING_GROUNDS = "training_grounds"  # Combat practice
    STABLES = "stables"               # Horses
    WAREHOUSE = "warehouse"            # Storage
    FARM = "farm"                      # Agriculture (outskirts)
    WOODS = "woods"                    # Forest area (outskirts)
    SHORE = "shore"                    # Beach/waterfront


@dataclass
class SubLocation:
    """A specific place within a city."""
    id: str
    name: str
    type: SubLocationType
    description: str
    atmosphere: str = ""
    
    # NPCs
    resident_npcs: List[str] = field(default_factory=list)  # NPCs who live/work here
    visiting_npcs: List[str] = field(default_factory=list)  # Temporary visitors
    max_visitors: int = 5  # How many random visitors can be here
    
    # Connections to other sub-locations
    connections: List[str] = field(default_factory=list)  # Adjacent sub-location IDs
    
    # Properties
    is_public: bool = True  # Can anyone enter?
    required_reputation: int = 0  # Min faction rep to enter (negative = enemies only)
    controlling_faction: str = ""  # Which faction controls this place
    
    # Services available
    services: List[str] = field(default_factory=list)  # e.g., ["trade", "healing", "rumors"]

    # Combat hazards — SRD conditions that have an elevated chance of applying
    # at this location.  e.g. ["prone"] for icy docks, ["grappled"] for close
    # quarters, ["blinded"] for smoke-filled forge.  Keyed by condition name.
    combat_hazards: List[str] = field(default_factory=list)

    def get_hazard_condition_modifiers(self) -> dict:
        """Return a dict of {condition: +0.20} for all declared combat hazards.

        This can be merged with RuneIntent.get_condition_modifiers() and
        ChaosSystem.get_combat_modifiers() to produce a final probability table.
        """
        return {str(h).lower().strip(): 0.20 for h in self.combat_hazards if h}

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "atmosphere": self.atmosphere,
            "resident_npcs": self.resident_npcs,
            "visiting_npcs": self.visiting_npcs,
            "max_visitors": self.max_visitors,
            "connections": self.connections,
            "is_public": self.is_public,
            "required_reputation": self.required_reputation,
            "controlling_faction": self.controlling_faction,
            "services": self.services,
            "combat_hazards": self.combat_hazards,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'SubLocation':
        # Use `or` so that None (from `type: null` in YAML) also falls back to default,
        # not just absent keys (which dict.get default alone would not handle).
        loc_type = data.get("type") or "residential"
        if isinstance(loc_type, str):
            try:
                loc_type = SubLocationType(loc_type)
            except ValueError:
                loc_type = SubLocationType.RESIDENTIAL
        elif not isinstance(loc_type, SubLocationType):
            loc_type = SubLocationType.RESIDENTIAL
        
        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Unknown"),
            type=loc_type,
            description=data.get("description", ""),
            atmosphere=data.get("atmosphere", ""),
            resident_npcs=data.get("resident_npcs", []),
            visiting_npcs=data.get("visiting_npcs", []),
            max_visitors=data.get("max_visitors", 5),
            connections=data.get("connections", []),
            is_public=data.get("is_public", True),
            required_reputation=data.get("required_reputation", 0),
            controlling_faction=data.get("controlling_faction", ""),
            services=data.get("services", []),
            combat_hazards=data.get("combat_hazards", []),
        )
    
    def unlock(self, reason: str = "") -> bool:
        """BUG-016 FIX: Unlock this location if it was locked.
        
        Args:
            reason: Why the location was unlocked (for logging)
            
        Returns:
            True if location was unlocked, False if already public
        """
        if not self.is_public:
            self.is_public = True
            return True
        return False
    
    def check_unlock_condition(self, player_reputation: int, faction_id: str = "") -> bool:
        """BUG-016 FIX: Check if location should unlock based on player reputation.
        
        Args:
            player_reputation: Player's reputation score
            faction_id: Optional faction ID to check against
            
        Returns:
            True if location should be unlocked
        """
        if self.is_public:
            return False  # Already unlocked
            
        # If no reputation required, unlock immediately
        if self.required_reputation <= 0:
            return True
            
        # Check if player meets reputation requirement
        if player_reputation >= self.required_reputation:
            return True
            
        return False


@dataclass  
class CityGrid:
    """The complete local grid for a city."""
    city_id: str
    city_name: str
    sub_locations: Dict[str, SubLocation] = field(default_factory=dict)
    default_entry_point: str = ""  # Where you arrive when entering city
    
    def get_npcs_at_location(self, sub_location_id: str) -> List[str]:
        """Get all NPC IDs at a specific sub-location."""
        if sub_location_id not in self.sub_locations:
            return []
        loc = self.sub_locations[sub_location_id]
        return loc.resident_npcs + loc.visiting_npcs
    
    def find_npc_location(self, npc_id: str) -> Optional[str]:
        """Find which sub-location an NPC is in."""
        for loc_id, loc in self.sub_locations.items():
            if npc_id in loc.resident_npcs or npc_id in loc.visiting_npcs:
                return loc_id
        return None
    
    def to_dict(self) -> Dict:
        return {
            "city_id": self.city_id,
            "city_name": self.city_name,
            "sub_locations": {k: v.to_dict() for k, v in self.sub_locations.items()},
            "default_entry_point": self.default_entry_point
        }
    
    def check_and_unlock_locations(self, player_reputation: int, faction_id: str = "") -> List[str]:
        """BUG-016 FIX: Check all locations and unlock any that should now be accessible.
        
        Args:
            player_reputation: Player's current reputation score
            faction_id: Optional faction ID to check against
            
        Returns:
            List of location IDs that were unlocked
        """
        unlocked = []
        for loc_id, loc in self.sub_locations.items():
            if loc.check_unlock_condition(player_reputation, faction_id):
                if loc.unlock(f"Reputation {player_reputation} >= {loc.required_reputation}"):
                    unlocked.append(loc_id)
        return unlocked
    
    def get_locked_locations(self) -> List[Tuple[str, SubLocation]]:
        """Get list of currently locked locations with their requirements.
        
        Returns:
            List of (loc_id, SubLocation) tuples for locked locations
        """
        return [(loc_id, loc) for loc_id, loc in self.sub_locations.items() if not loc.is_public]


# ============================================================================
# PARTY AND ALLIES SYSTEM
# ============================================================================

@dataclass
class AllyRelationship:
    """Tracks relationship with a potential party member."""
    npc_id: str
    npc_name: str
    
    # Relationship status
    is_ally: bool = False          # Have they agreed to potentially join you?
    is_in_party: bool = False      # Are they currently in your active party?
    
    # Loyalty (0-100)
    loyalty: int = 50              # Starting neutral
    max_loyalty_reached: int = 50  # Highest loyalty ever achieved
    
    # Relationship history
    battles_together: int = 0
    gifts_given: int = 0
    promises_kept: int = 0
    promises_broken: int = 0
    times_abandoned: int = 0       # Left them in danger
    times_saved: int = 0           # Rescued them
    
    # Current state
    current_location: str = ""     # Where they are right now
    mood: str = "neutral"          # Current emotional state
    last_interaction: str = ""     # Last significant interaction
    grievances: List[str] = field(default_factory=list)  # Things they're upset about
    positive_memories: List[str] = field(default_factory=list)  # Good times
    
    def adjust_loyalty(self, amount: int, reason: str = "") -> int:
        """Adjust loyalty and track the change."""
        old_loyalty = self.loyalty
        self.loyalty = max(0, min(100, self.loyalty + amount))
        
        if self.loyalty > self.max_loyalty_reached:
            self.max_loyalty_reached = self.loyalty
        
        # Track significant negative events
        if amount < -10 and reason:
            self.grievances.append(reason)
            if len(self.grievances) > 5:
                self.grievances = self.grievances[-5:]
        
        # Track positive events
        if amount > 10 and reason:
            self.positive_memories.append(reason)
            if len(self.positive_memories) > 5:
                self.positive_memories = self.positive_memories[-5:]
        
        return self.loyalty - old_loyalty
    
    def get_loyalty_description(self) -> str:
        """Get a description of the current loyalty level."""
        if self.loyalty >= 90:
            return "devoted"
        elif self.loyalty >= 75:
            return "loyal"
        elif self.loyalty >= 60:
            return "friendly"
        elif self.loyalty >= 40:
            return "neutral"
        elif self.loyalty >= 25:
            return "wary"
        elif self.loyalty >= 10:
            return "distrustful"
        else:
            return "hostile"
    
    def should_leave_party(self) -> Tuple[bool, str]:
        """Check if this ally would leave the party."""
        if self.loyalty < 15:
            return (True, f"{self.npc_name} can no longer tolerate traveling with you.")
        if len(self.grievances) >= 4 and self.loyalty < 40:
            return (True, f"{self.npc_name} has had enough of your behavior.")
        return (False, "")
    
    def would_join_party(self) -> Tuple[bool, str]:
        """Check if this ally would agree to join the party right now."""
        if not self.is_ally:
            return (False, f"{self.npc_name} is not your ally.")
        if self.loyalty < 25:
            return (False, f"{self.npc_name} doesn't trust you enough to travel together.")
        if self.mood == "angry" and self.loyalty < 60:
            return (False, f"{self.npc_name} is too upset with you right now.")
        return (True, "")
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AllyRelationship':
        import dataclasses as _dc
        _list_fields = {f.name for f in _dc.fields(cls) if 'List' in str(f.type) or 'list' in str(f.type)}
        filtered = {
            k: (v if v is not None or k not in _list_fields else [])
            for k, v in data.items() if k in cls.__dataclass_fields__
        }
        return cls(**filtered)


@dataclass
class PartySystem:
    """Manages the player's allies and active party."""
    
    # All allies (people who have agreed to potentially join you)
    allies: Dict[str, AllyRelationship] = field(default_factory=dict)
    
    # Current active party members (subset of allies)
    active_party: List[str] = field(default_factory=list)
    
    # Party limits
    max_party_size: int = 4  # Including player
    
    def add_ally(self, npc_id: str, npc_name: str, starting_loyalty: int = 50) -> AllyRelationship:
        """Add someone as a potential ally."""
        if npc_id not in self.allies:
            self.allies[npc_id] = AllyRelationship(
                npc_id=npc_id,
                npc_name=npc_name,
                is_ally=True,
                loyalty=starting_loyalty
            )
        else:
            self.allies[npc_id].is_ally = True
        return self.allies[npc_id]
    
    def remove_ally(self, npc_id: str) -> bool:
        """Remove someone from allies list."""
        if npc_id in self.allies:
            # Also remove from active party
            if npc_id in self.active_party:
                self.active_party.remove(npc_id)
            self.allies[npc_id].is_ally = False
            self.allies[npc_id].is_in_party = False
            return True
        return False
    
    def add_to_party(self, npc_id: str, npc_location: str, player_location: str) -> Tuple[bool, str]:
        """Try to add an ally to the active party."""
        if npc_id not in self.allies:
            return (False, "They are not your ally.")
        
        ally = self.allies[npc_id]
        
        if not ally.is_ally:
            return (False, f"{ally.npc_name} is not your ally.")
        
        if ally.is_in_party:
            return (False, f"{ally.npc_name} is already in your party.")
        
        if npc_location != player_location:
            return (False, f"{ally.npc_name} is not here. They are at {npc_location}.")
        
        if len(self.active_party) >= self.max_party_size - 1:  # -1 for player
            return (False, f"Your party is full (max {self.max_party_size}).")
        
        # Check if they're willing
        would_join, reason = ally.would_join_party()
        if not would_join:
            return (False, reason)
        
        # Success
        self.active_party.append(npc_id)
        ally.is_in_party = True
        return (True, f"{ally.npc_name} joins your party.")
    
    def remove_from_party(self, npc_id: str) -> Tuple[bool, str]:
        """Remove someone from the active party."""
        if npc_id not in self.active_party:
            return (False, "They are not in your party.")
        
        self.active_party.remove(npc_id)
        if npc_id in self.allies:
            self.allies[npc_id].is_in_party = False
            name = self.allies[npc_id].npc_name
            return (True, f"{name} leaves your party.")
        return (True, "Party member removed.")
    
    def get_party_members(self) -> List[AllyRelationship]:
        """Get all active party member relationships."""
        return [self.allies[npc_id] for npc_id in self.active_party if npc_id in self.allies]
    
    def check_party_loyalty(self) -> List[Tuple[str, str]]:
        """Check if any party members want to leave. Returns list of (npc_id, reason)."""
        leaving = []
        for npc_id in self.active_party:
            if npc_id in self.allies:
                should_leave, reason = self.allies[npc_id].should_leave_party()
                if should_leave:
                    leaving.append((npc_id, reason))
        return leaving
    
    def apply_shared_experience(self, experience_type: str, amount: int = 5):
        """Apply loyalty change to all party members for shared experience."""
        for npc_id in self.active_party:
            if npc_id in self.allies:
                self.allies[npc_id].adjust_loyalty(amount, experience_type)
                if experience_type == "battle_victory":
                    self.allies[npc_id].battles_together += 1
    
    def to_dict(self) -> Dict:
        return {
            "allies": {k: v.to_dict() for k, v in self.allies.items()},
            "active_party": self.active_party,
            "max_party_size": self.max_party_size
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PartySystem':
        party = cls(max_party_size=data.get("max_party_size", 4))
        party.active_party = data.get("active_party", [])
        for npc_id, ally_data in data.get("allies", {}).items():
            party.allies[npc_id] = AllyRelationship.from_dict(ally_data)
        return party


# ============================================================================
# FACTION SYSTEM
# ============================================================================

@dataclass
class Faction:
    """A group or organization with shared interests."""
    id: str
    name: str
    description: str
    
    # Leadership
    leader_npc_id: str = ""
    
    # Reputation with player (-100 to 100)
    player_reputation: int = 0
    
    # Alignment/values
    values: List[str] = field(default_factory=list)  # What they care about
    enemies: List[str] = field(default_factory=list)  # Faction IDs they oppose
    allies: List[str] = field(default_factory=list)   # Faction IDs they support
    
    # Control
    controlled_locations: List[str] = field(default_factory=list)  # Sub-location IDs
    
    # Members
    member_npc_ids: List[str] = field(default_factory=list)
    
    def get_reputation_description(self) -> str:
        """Get description of player's standing with this faction."""
        if self.player_reputation >= 80:
            return "revered"
        elif self.player_reputation >= 60:
            return "honored"
        elif self.player_reputation >= 40:
            return "friendly"
        elif self.player_reputation >= 20:
            return "liked"
        elif self.player_reputation >= -20:
            return "neutral"
        elif self.player_reputation >= -40:
            return "disliked"
        elif self.player_reputation >= -60:
            return "unfriendly"
        elif self.player_reputation >= -80:
            return "hostile"
        else:
            return "hated"
    
    def adjust_reputation(self, amount: int) -> int:
        """Adjust reputation and return new value."""
        self.player_reputation = max(-100, min(100, self.player_reputation + amount))
        return self.player_reputation
    
    def is_enemy(self) -> bool:
        return self.player_reputation < -40
    
    def is_friend(self) -> bool:
        return self.player_reputation > 40
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Faction':
        import dataclasses as _dc
        _list_fields = {f.name for f in _dc.fields(cls) if 'List' in str(f.type) or 'list' in str(f.type)}
        filtered = {
            k: (v if v is not None or k not in _list_fields else [])
            for k, v in data.items() if k in cls.__dataclass_fields__
        }
        return cls(**filtered)


@dataclass
class FactionSystem:
    """Manages all factions and reputations."""
    factions: Dict[str, Faction] = field(default_factory=dict)
    
    def get_faction(self, faction_id: str) -> Optional[Faction]:
        return self.factions.get(faction_id)
    
    def add_faction(self, faction: Faction):
        self.factions[faction.id] = faction
    
    def adjust_reputation(self, faction_id: str, amount: int, reason: str = "") -> Optional[int]:
        """Adjust reputation with a faction."""
        if faction_id not in self.factions:
            return None
        
        faction = self.factions[faction_id]
        new_rep = faction.adjust_reputation(amount)
        
        # Ripple effect to allied/enemy factions (smaller effect)
        ripple = amount // 3
        if ripple != 0:
            for ally_id in faction.allies:
                if ally_id in self.factions:
                    self.factions[ally_id].adjust_reputation(ripple)
            for enemy_id in faction.enemies:
                if enemy_id in self.factions:
                    self.factions[enemy_id].adjust_reputation(-ripple)
        
        return new_rep
    
    def get_npc_faction(self, npc_id: str) -> Optional[Faction]:
        """Find which faction an NPC belongs to."""
        for faction in self.factions.values():
            if npc_id in faction.member_npc_ids:
                return faction
        return None
    
    def get_hostile_factions(self) -> List[Faction]:
        """Get factions that are hostile to the player."""
        return [f for f in self.factions.values() if f.is_enemy()]
    
    def get_friendly_factions(self) -> List[Faction]:
        """Get factions that are friendly to the player."""
        return [f for f in self.factions.values() if f.is_friend()]
    
    def to_dict(self) -> Dict:
        return {
            "factions": {k: v.to_dict() for k, v in self.factions.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FactionSystem':
        system = cls()
        for faction_id, faction_data in data.get("factions", {}).items():
            system.factions[faction_id] = Faction.from_dict(faction_data)
        return system


# ============================================================================
# DEFAULT CITY GRIDS - Pre-built sub-location templates
# ============================================================================

def create_default_uppsala_grid() -> CityGrid:
    """Create the default sub-location grid for Uppsala."""
    grid = CityGrid(
        city_id="uppsala",
        city_name="Uppsala",
        default_entry_point="main_mead_hall"
    )
    
    # Main Mead Hall - Starting point, adventurer hub
    grid.sub_locations["main_mead_hall"] = SubLocation(
        id="main_mead_hall",
        name="The Raven's Rest Mead Hall",
        type=SubLocationType.MEAD_HALL,
        description="A great timber hall with carved dragon heads on the roof beams. The central hearth blazes day and night, around which warriors, merchants, and travelers gather to drink, boast, and seek companions for their ventures. The walls are hung with shields and weapons, trophies of past glories.",
        atmosphere="The air is thick with woodsmoke, roasting meat, and the rumble of conversation. Skalds sing of old battles. Dice clatter on tables. Warriors size each other up while merchants haggle quietly in corners.",
        resident_npcs=[],  # Staff only - adventurers are visitors
        max_visitors=12,
        connections=["market_square", "temple_district", "docks", "residential_east"],
        services=["rumors", "hire_companions", "food", "lodging"],
        controlling_faction="uppsala_merchants"
    )
    
    # Jarl's Hall - Seat of power
    grid.sub_locations["jarl_hall"] = SubLocation(
        id="jarl_hall",
        name="Jarl Eriksson's Great Hall",
        type=SubLocationType.JARL_HALL,
        description="The grandest hall in Uppsala, seat of Jarl Eriksson's power. Massive oak pillars support the roof, carved with scenes from the sagas. The high seat is adorned with wolf pelts and silver, and the walls display the wealth of generations.",
        atmosphere="Guards in mail stand at attention. Petitioners wait nervously. The Jarl's household moves with practiced efficiency, and the weight of authority hangs in the air.",
        resident_npcs=["jarl_eriksson", "jarl_huskarl_captain", "jarl_steward"],
        max_visitors=4,
        connections=["market_square", "barracks"],
        is_public=False,  # Need permission or reputation to enter freely
        required_reputation=20,
        services=["audience", "justice", "quests"],
        controlling_faction="jarl_court"
    )
    
    # Temple of the Gods
    grid.sub_locations["temple_district"] = SubLocation(
        id="temple_district",
        name="Temple of the Aesir",
        type=SubLocationType.TEMPLE,
        description="A sacred grove with three great wooden temples dedicated to Odin, Thor, and Freyr. Rune-carved standing stones mark the boundaries of holy ground. The great tree at the center is hung with offerings.",
        atmosphere="Incense and wood smoke mingle. Priests chant the old prayers. Pilgrims come to make offerings and seek blessings. The sense of the divine is palpable.",
        resident_npcs=["head_gothi", "temple_acolyte"],
        max_visitors=6,
        connections=["main_mead_hall", "cemetery", "sacred_grove"],
        services=["blessings", "healing", "divination", "sacrifice"],
        controlling_faction="temple_priests"
    )
    
    # Sacred Grove - Mystical area near temple
    grid.sub_locations["sacred_grove"] = SubLocation(
        id="sacred_grove",
        name="The Sacred Grove",
        type=SubLocationType.GROVE,
        description="A ring of ancient oaks surrounding a clearing where the gods are said to walk. Offerings hang from branches. Few venture here after dark.",
        atmosphere="The air is still and heavy with presence. Birds go silent. Even the boldest warriors speak in whispers here.",
        resident_npcs=[],
        max_visitors=4,
        connections=["temple_district"],
        is_public=False,
        services=["meditation", "offerings"],
        controlling_faction=""
    )
    
    # Blacksmith's Forge
    grid.sub_locations["forge"] = SubLocation(
        id="forge",
        name="Thorbjorn's Forge",
        type=SubLocationType.FORGE,
        description="A large smithy with multiple forges, the sound of hammers ringing from dawn to dusk. Weapons, armor, and tools of all kinds hang from the walls or lean against posts. The heat is intense.",
        atmosphere="The ring of hammer on steel, the hiss of quenched metal, the glow of forge-fire. The smell of hot iron and sweat. Workers move with practiced efficiency.",
        resident_npcs=["thorbjorn_blacksmith"],
        max_visitors=3,
        connections=["market_square", "barracks"],
        services=["trade_weapons", "trade_armor", "repair", "commission"],
        controlling_faction="craftsmen_guild"
    )
    
    # Market Square
    grid.sub_locations["market_square"] = SubLocation(
        id="market_square",
        name="Uppsala Market Square",
        type=SubLocationType.MARKET,
        description="A bustling open square where merchants from many lands display their wares. Stalls sell everything from local wool to exotic silks, from simple bread to rare spices. The babel of tongues and clink of silver fills the air.",
        atmosphere="Haggling voices, the smell of spices and leather, colorful awnings snapping in the wind. People of many cultures mingle - Norse, Slavic, even the occasional Arab trader.",
        resident_npcs=["market_master"],
        max_visitors=15,
        connections=["main_mead_hall", "forge", "jarl_hall", "docks", "residential_west"],
        services=["trade_general", "rumors", "hire_services"],
        controlling_faction="uppsala_merchants"
    )
    
    # Docks
    grid.sub_locations["docks"] = SubLocation(
        id="docks",
        name="Uppsala Docks",
        type=SubLocationType.DOCKS,
        description="The waterfront where longships and knarrs bob at their moorings. Cargo is loaded and unloaded constantly. Sailors swap tales while waiting for favorable winds.",
        atmosphere="The creak of ship timbers, the cry of gulls, the smell of tar and fish. Weather-beaten sailors eye the sky and discuss the tides.",
        resident_npcs=["harbor_master", "ship_wright"],
        max_visitors=8,
        connections=["main_mead_hall", "market_square", "warehouse_district"],
        services=["travel", "ship_hire", "cargo", "rumors_foreign"],
        controlling_faction="ship_captains"
    )
    
    # Barracks
    grid.sub_locations["barracks"] = SubLocation(
        id="barracks",
        name="Jarl's Guard Barracks",
        type=SubLocationType.BARRACKS,
        description="A long building where the Jarl's warriors live and train. Weapons racks line the walls, and the sound of sparring echoes from the attached training yard.",
        atmosphere="The clang of practice swords, grunts of exertion, veterans shouting corrections. The smell of sweat and weapon oil.",
        resident_npcs=["weapons_master", "veteran_huskarl"],
        max_visitors=4,
        connections=["jarl_hall", "forge", "training_grounds"],
        is_public=False,
        required_reputation=10,
        services=["training", "sparring", "military_quests"],
        controlling_faction="jarl_court"
    )
    
    # Training Grounds
    grid.sub_locations["training_grounds"] = SubLocation(
        id="training_grounds",
        name="Training Grounds",
        type=SubLocationType.TRAINING_GROUNDS,
        description="An open area with practice dummies, archery targets, and a sparring ring. Warriors of all skill levels come here to hone their craft.",
        atmosphere="The thud of arrows, clash of practice weapons, shouted challenges. Young warriors trying to prove themselves, veterans maintaining their edge.",
        resident_npcs=[],
        max_visitors=10,
        connections=["barracks", "residential_east"],
        services=["training", "challenges", "tournaments"],
        controlling_faction="jarl_court"
    )
    
    # Healer's Hut
    grid.sub_locations["healer_hut"] = SubLocation(
        id="healer_hut",
        name="Yrsa's Healing House",
        type=SubLocationType.HEALER_HUT,
        description="A clean, herb-scented building where the sick and wounded are tended. Bundles of dried herbs hang from the rafters, and shelves hold salves and poultices.",
        atmosphere="Quiet voices, the smell of medicinal herbs, the occasional moan of a patient. A sense of calm competence.",
        resident_npcs=["healer_yrsa"],  # STAYS HERE
        max_visitors=4,
        connections=["residential_west", "temple_district"],
        services=["healing", "medicine", "herbs"],
        controlling_faction=""  # Independent
    )
    
    # Residential Areas
    grid.sub_locations["residential_east"] = SubLocation(
        id="residential_east",
        name="Eastern Residences",
        type=SubLocationType.RESIDENTIAL,
        description="A neighborhood of timber houses where craftsmen and their families live. Children play between the buildings, and the smell of cooking fires drifts from open doors.",
        atmosphere="Domestic sounds - children laughing, dogs barking, the clatter of daily life. A sense of community.",
        resident_npcs=[],
        max_visitors=5,
        connections=["main_mead_hall", "training_grounds"],
        services=[],
        controlling_faction=""
    )
    
    grid.sub_locations["residential_west"] = SubLocation(
        id="residential_west",
        name="Western Residences",
        type=SubLocationType.RESIDENTIAL,
        description="The wealthier residential district, with larger houses and well-kept gardens. Merchants and successful craftsmen make their homes here.",
        atmosphere="Quieter and more orderly than other parts of the city. Servants go about their work, and the houses show signs of prosperity.",
        resident_npcs=[],
        max_visitors=4,
        connections=["market_square", "healer_hut"],
        services=[],
        controlling_faction="uppsala_merchants"
    )
    
    # Outskirts
    grid.sub_locations["city_outskirts"] = SubLocation(
        id="city_outskirts",
        name="City Outskirts",
        type=SubLocationType.OUTSKIRTS,
        description="The edges of Uppsala where the city meets the surrounding farmland and forest. Travelers arrive and depart, and those who prefer solitude make their homes.",
        atmosphere="The transition between civilization and wilderness. The sounds of the city fade, replaced by birdsong and wind.",
        resident_npcs=[],
        max_visitors=6,
        connections=["residential_east", "cemetery", "forest_edge"],
        services=["travel_overland"],
        controlling_faction=""
    )
    
    # Cemetery/Burial Mounds
    grid.sub_locations["cemetery"] = SubLocation(
        id="cemetery",
        name="Ancestral Burial Mounds",
        type=SubLocationType.CEMETERY,
        description="Ancient burial mounds where the honored dead rest. Some mounds are centuries old, grass-covered hills where kings of old were laid with their treasures. Newer graves cluster around them.",
        atmosphere="A solemn silence. The weight of generations watching. Some claim to see lights among the mounds at night.",
        resident_npcs=[],
        max_visitors=3,
        connections=["temple_district", "city_outskirts"],
        services=["burial", "ancestor_communion"],
        controlling_faction="temple_priests"
    )
    
    # Warehouse District
    grid.sub_locations["warehouse_district"] = SubLocation(
        id="warehouse_district",
        name="Warehouse District",
        type=SubLocationType.WAREHOUSE,
        description="Large storage buildings near the docks where trade goods are kept. Guards patrol day and night to protect the valuable cargo.",
        atmosphere="The smell of stored goods - wool, grain, furs, exotic imports. Workers loading and unloading. An air of commerce.",
        resident_npcs=["warehouse_keeper"],
        max_visitors=4,
        connections=["docks", "market_square"],
        services=["storage", "bulk_trade"],
        controlling_faction="uppsala_merchants"
    )
    
    # Forest Edge (leads to wilderness)
    grid.sub_locations["forest_edge"] = SubLocation(
        id="forest_edge",
        name="Edge of the Wildwood",
        type=SubLocationType.WOODS,
        description="Where the forest begins in earnest, the trees closing in and the paths growing narrow. Hunters and woodcutters know these trails, but deeper in lie unknown dangers.",
        atmosphere="The smell of pine and earth. Bird calls and rustling leaves. The feeling of being watched by unseen eyes.",
        resident_npcs=[],
        max_visitors=3,
        connections=["city_outskirts"],
        services=["hunting", "foraging", "wilderness_travel"],
        controlling_faction=""
    )
    
    return grid


def create_default_factions() -> FactionSystem:
    """Create the default faction system for Uppsala."""
    system = FactionSystem()
    
    # Jarl's Court - The ruling power
    system.add_faction(Faction(
        id="jarl_court",
        name="Jarl Eriksson's Court",
        description="The ruling authority of Uppsala, including the Jarl's huskarls, advisors, and household.",
        leader_npc_id="jarl_eriksson",
        player_reputation=0,
        values=["order", "loyalty", "strength", "law"],
        enemies=["outlaws", "foreign_raiders"],
        allies=["temple_priests", "ship_captains"],
        controlled_locations=["jarl_hall", "barracks", "training_grounds"],
        member_npc_ids=["jarl_eriksson", "jarl_huskarl_captain", "jarl_steward", "weapons_master", "veteran_huskarl"]
    ))
    
    # Temple Priests
    system.add_faction(Faction(
        id="temple_priests",
        name="Keepers of the Old Ways",
        description="The priests and gothi who maintain the temples and sacred traditions.",
        leader_npc_id="head_gothi",
        player_reputation=0,
        values=["tradition", "sacrifice", "wisdom", "the_gods"],
        enemies=["christian_missionaries"],
        allies=["jarl_court"],
        controlled_locations=["temple_district", "cemetery"],
        member_npc_ids=["head_gothi", "temple_acolyte"]
    ))
    
    # Uppsala Merchants
    system.add_faction(Faction(
        id="uppsala_merchants",
        name="Uppsala Merchant Guild",
        description="The wealthy traders who control much of Uppsala's commerce.",
        leader_npc_id="market_master",
        player_reputation=0,
        values=["profit", "trade", "stability", "connections"],
        enemies=[],
        allies=["ship_captains"],
        controlled_locations=["main_mead_hall", "market_square", "warehouse_district", "residential_west"],
        member_npc_ids=["market_master", "warehouse_keeper"]
    ))
    
    # Ship Captains
    system.add_faction(Faction(
        id="ship_captains",
        name="Brotherhood of the Sail",
        description="The captains and experienced sailors who control the waterways.",
        leader_npc_id="harbor_master",
        player_reputation=0,
        values=["freedom", "adventure", "honor_among_sailors", "profit"],
        enemies=["foreign_raiders"],
        allies=["jarl_court", "uppsala_merchants"],
        controlled_locations=["docks"],
        member_npc_ids=["harbor_master", "ship_wright"]
    ))
    
    # Craftsmen Guild
    system.add_faction(Faction(
        id="craftsmen_guild",
        name="Craftsmen's Guild",
        description="The skilled artisans - smiths, woodworkers, leatherworkers, and more.",
        leader_npc_id="bjorn_ironhand",
        player_reputation=0,
        values=["skill", "quality", "fair_dealing", "craft_secrets"],
        enemies=[],
        allies=["uppsala_merchants"],
        controlled_locations=["forge"],
        member_npc_ids=["bjorn_ironhand", "smith_apprentice"]
    ))
    
    # Outlaws (hidden faction)
    system.add_faction(Faction(
        id="outlaws",
        name="The Unseen",
        description="Outlaws, exiles, and those who live outside the law. They have no formal structure but look out for each other.",
        leader_npc_id="",
        player_reputation=0,
        values=["survival", "freedom", "mutual_aid", "revenge"],
        enemies=["jarl_court"],
        allies=[],
        controlled_locations=[],
        member_npc_ids=[]
    ))
    
    return system


# ============================================================================
# NPC BEHAVIOR RULES FOR AI PROMPTS
# ============================================================================

NPC_BEHAVIOR_RULES = """
## NPC BEHAVIOR AND SOCIAL RULES

### CORE PRINCIPLE: NPCs Are Real People, Not Game Mechanics

NPCs have their own lives, locations, and concerns. They do NOT:
- Follow the player around without reason
- Comment on everything the player does
- Act as annoying stereotypes
- Initiate conversation repeatedly if ignored
- Treat every player action as noteworthy

### LOCATION-BASED PRESENCE

NPCs stay in their designated locations unless they have specific reason to move:

**Resident NPCs** (stay at their location):
- Völva Grimhild → Her seer's hut (does NOT wander around being mystical at people)
- Bjorn Ironhand → His forge (working, trading, available but not pushy)
- The Jarl → His hall (ruling, holding court, not wandering markets)
- Healers → Their healing houses
- Priests → The temple

**If player is NOT at an NPC's location:**
- That NPC is NOT present and does NOT interact
- Do not have NPCs appear out of nowhere
- Do not have NPCs send messages unless it makes narrative sense

### SOCIAL APPROPRIATENESS

NPCs respect social boundaries:

1. **Initiation Rules:**
   - NPCs may initiate conversation ONCE if they have genuine reason
   - If player ignores them, they return to their own business
   - They do not pester, follow, or demand attention
   - Exception: If NPC is angry/has grievance, they may press ONCE more

2. **Response to Player:**
   - React based on: personality + relationship history + reputation + current situation
   - NOT based on: being helpful to the player, advancing plot, or game mechanics
   - A suspicious NPC stays suspicious. A busy NPC stays busy.

3. **Conversation Endings:**
   - NPCs end conversations when natural (they have work, other concerns)
   - NPCs don't hang around waiting for player to do something
   - "I have work to do" is a valid NPC response

### PARTY MEMBERS ONLY

Only characters in the player's ACTIVE PARTY travel with them:
- Party members follow to new locations
- Party members can comment on situations (sparingly, in character)
- Party members have their own reactions based on personality and loyalty

Non-party NPCs:
- Stay at their locations
- Live their own lives
- Can be visited when the player goes to them
- Do NOT appear in scenes they wouldn't logically be in

### ALLY AND LOYALTY CONSIDERATIONS

When the player has allies:
- High loyalty allies are more helpful, forgiving, willing
- Low loyalty allies are suspicious, less cooperative
- Very low loyalty allies may refuse requests or leave
- Grievances affect behavior (an ally you betrayed remembers)

### FACTION REPUTATION EFFECTS

NPC behavior is affected by faction standing:
- Hostile faction members are uncooperative or aggressive
- Friendly faction members are helpful and trusting
- Neutral members judge player on direct interactions

### MEAD HALL ADVENTURERS

The mead hall contains various adventurer NPCs who:
- Have their own conversations (that player can overhear)
- May approach player ONCE to propose partnership, trade info, etc.
- Respect if player declines or ignores
- Size up new arrivals but don't stare or pester
- Have their own agendas and business
- Are potential allies but must be properly recruited

### FORBIDDEN BEHAVIORS

NEVER have NPCs:
- Follow player from location to location (unless in party)
- Comment on every action ("I see you're looking at that sword!")
- Act as tour guides or exposition machines
- Interrupt player constantly
- Appear in locations where they don't belong
- Act out of character to be "helpful" to the player
- Break the fourth wall or acknowledge game mechanics
"""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_npcs_at_sublocation(
    city_grid: CityGrid, 
    sub_location_id: str,
    party_member_ids: List[str],
    all_npcs: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Get the NPCs that should be present at a sub-location.
    
    Args:
        city_grid: The city's sub-location grid
        sub_location_id: Current sub-location
        party_member_ids: IDs of NPCs in player's party
        all_npcs: Dictionary of all NPC data
        
    Returns:
        List of NPC data dicts for those present
    """
    if sub_location_id not in city_grid.sub_locations:
        return []
    
    loc = city_grid.sub_locations[sub_location_id]
    present_ids = set(loc.resident_npcs + loc.visiting_npcs)
    
    # Add party members (they follow)
    present_ids.update(party_member_ids)
    
    # Get actual NPC data
    present_npcs = []
    for npc_id in present_ids:
        if npc_id in all_npcs:
            npc = all_npcs[npc_id].copy()
            npc["is_resident"] = npc_id in loc.resident_npcs
            npc["is_party_member"] = npc_id in party_member_ids
            present_npcs.append(npc)
    
    return present_npcs


def calculate_loyalty_change(
    action: str,
    ally: AllyRelationship,
    npc_personality: Dict,
    context: Dict = None
) -> Tuple[int, str]:
    """
    Calculate loyalty change based on action and NPC personality.
    
    Args:
        action: Type of action taken
        ally: The ally relationship
        npc_personality: NPC's personality data
        context: Additional context
        
    Returns:
        (change_amount, reason)
    """
    context = context or {}
    traits = npc_personality.get("traits", [])
    alignment = npc_personality.get("alignment", "neutral").lower()
    
    # Base changes by action type
    action_changes = {
        "battle_victory": (8, "Victory in battle together"),
        "battle_defeat": (-3, "Defeat in battle"),
        "saved_life": (20, "You saved their life"),
        "abandoned_danger": (-25, "You abandoned them in danger"),
        "gift_valuable": (10, "Valuable gift given"),
        "gift_personal": (15, "Thoughtful personal gift"),
        "insult": (-10, "You insulted them"),
        "defended_honor": (12, "You defended their honor"),
        "broke_promise": (-20, "You broke a promise to them"),
        "kept_promise": (10, "You kept your word"),
        "shared_loot_fairly": (5, "Fair division of spoils"),
        "hoarded_loot": (-8, "You kept more than your share"),
        "listened_to_advice": (5, "You valued their counsel"),
        "ignored_advice": (-3, "You dismissed their counsel"),
        "helped_personal_goal": (15, "You helped with their personal goal"),
        "opposed_personal_goal": (-15, "You opposed their personal goal"),
        "time_together": (1, "Traveling together"),
    }
    
    if action not in action_changes:
        return (0, "")
    
    base_change, reason = action_changes[action]
    
    # Modify based on personality
    trait_str = " ".join(traits).lower()
    
    if "loyal" in trait_str and base_change > 0:
        base_change = int(base_change * 1.3)  # Loyal NPCs bond faster
    if "suspicious" in trait_str and base_change > 0:
        base_change = int(base_change * 0.7)  # Suspicious NPCs bond slower
    if "forgiving" in trait_str and base_change < 0:
        base_change = int(base_change * 0.6)  # Forgiving NPCs lose loyalty slower
    if "vengeful" in trait_str and base_change < 0:
        base_change = int(base_change * 1.4)  # Vengeful NPCs hold grudges
    
    # Modify based on alignment for certain actions
    if "evil" in alignment:
        if action == "hoarded_loot":
            base_change = int(base_change * 0.5)  # Evil NPCs expect this
        if action == "shared_loot_fairly":
            base_change = int(base_change * 0.5)  # They don't value fairness
    
    if "good" in alignment:
        if action == "abandoned_danger":
            base_change = int(base_change * 1.5)  # Good NPCs are more hurt by betrayal
    
    return (base_change, reason)
