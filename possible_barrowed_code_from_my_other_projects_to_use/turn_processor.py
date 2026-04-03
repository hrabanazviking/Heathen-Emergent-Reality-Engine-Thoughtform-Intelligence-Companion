#!/usr/bin/env python3
"""
Turn Processor v3.0 - Comprehensive Turn Management
====================================================

Handles everything that happens each turn:
1. Draw rune and prepare influence data
2. Gather complete state context
3. Build AI prompt with all context
4. Process AI response
5. Run housekeeping (extract characters, quests, locations)
6. Update memory systems
7. Track quest progress
8. Generate random interactions based on rune

This is the central coordinator that makes all systems work together.
"""

import random
import re
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from systems.scripted_combat import ScriptedCombatResolver

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


logger = logging.getLogger(__name__)


@dataclass
class TurnContext:
    """Complete context for a single turn."""
    turn_number: int
    player_action: str
    
    # Location info
    city: str
    sub_location: str
    sub_location_name: str
    sub_location_description: str
    sub_location_atmosphere: str
    
    # Character info
    player_character: Dict[str, Any]
    npcs_present: List[Dict[str, Any]]
    party_members: List[Dict[str, Any]]
    
    # Rune for this turn
    rune: Optional[Dict[str, Any]] = None
    rune_influence: str = ""
    
    # State info
    chaos_factor: int = 30
    time_of_day: str = "morning"
    season: str = "autumn"
    year: int = 850
    
    # Quest info
    active_quests: List[Dict] = field(default_factory=list)
    pending_quests: List[Dict] = field(default_factory=list)  # Offered but not accepted
    
    # Faction standings
    faction_standings: Dict[str, Dict] = field(default_factory=dict)
    
    # Memory context
    memory_context: str = ""
    recent_events: List[str] = field(default_factory=list)
    
    # Combat state
    in_combat: bool = False
    combat_data: Optional[Dict] = None
    
    # Custom prompts from config
    custom_system_prompt: str = ""
    custom_post_history: str = ""
    world_rules: str = ""
    character_voice: str = ""
    narration_style: str = ""


@dataclass
class TurnResult:
    """Result of processing a turn."""
    ai_response: str
    ai_summary: str
    
    # Extracted content
    new_characters: List[str] = field(default_factory=list)
    new_quests: List[Dict] = field(default_factory=list)
    new_locations: List[str] = field(default_factory=list)
    
    # State changes
    quest_updates: List[str] = field(default_factory=list)
    loyalty_changes: Dict[str, int] = field(default_factory=dict)
    reputation_changes: Dict[str, int] = field(default_factory=dict)
    
    # Random interactions that occurred
    random_interactions: List[str] = field(default_factory=list)
    
    # Combat results
    combat_occurred: bool = False
    damage_dealt: int = 0
    damage_taken: int = 0
    combat_data: Dict[str, Any] = field(default_factory=dict)


class RuneSystem:
    """
    Comprehensive rune system with full influence data.
    """
    
    def __init__(self, runes_path: str = "data/charts/elder_futhark.yaml"):
        self.runes_path = Path(runes_path)
        self.runes = []
        self.runes_by_name = {}
        self._load_runes()
    
    def _load_runes(self):
        """Load rune data from YAML."""
        if self.runes_path.exists():
            with open(self.runes_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self.runes = data.get("runes", [])
                self.runes_by_name = {r["name"].lower(): r for r in self.runes}
    
    def draw_rune(self) -> Dict[str, Any]:
        """Draw a random rune and return full influence data."""
        if not self.runes:
            return self._default_rune()
        
        rune = random.choice(self.runes)
        return self._expand_rune(rune)
    
    def get_rune(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific rune by name."""
        rune = self.runes_by_name.get(name.lower())
        if rune:
            return self._expand_rune(rune)
        return None
    
    def _expand_rune(self, rune: Dict) -> Dict[str, Any]:
        """Expand rune data with full influence description."""
        expanded = dict(rune)
        
        # Build comprehensive influence text for AI
        influence_parts = []
        
        # Core meaning
        influence_parts.append(f"RUNE: {rune['symbol']} {rune['name']} - {rune['meaning']}")
        
        # Keywords for theme
        if rune.get('keywords'):
            influence_parts.append(f"Themes: {', '.join(rune['keywords'])}")
        
        # Symbolic encounter suggestion
        if rune.get('symbolic_encounter'):
            influence_parts.append(f"Symbolic elements: {rune['symbolic_encounter']}")
        
        # Outcome twist
        if rune.get('outcome_twist'):
            influence_parts.append(f"Narrative influence: {rune['outcome_twist']}")
        
        # Mystic effect for in-game
        if rune.get('mystic_effect'):
            effect = rune['mystic_effect']
            influence_parts.append(f"Mystic effect: {effect.get('description', '')}")
            if effect.get('flavor'):
                influence_parts.append(f"Flavor: {effect['flavor']}")
        
        expanded['influence_text'] = "\n".join(influence_parts)
        
        # Generate narrative hooks based on rune
        expanded['narrative_hooks'] = self._generate_hooks(rune)
        
        return expanded
    
    def _generate_hooks(self, rune: Dict) -> List[str]:
        """Generate narrative hooks based on rune."""
        name = rune['name'].lower()
        hooks = []
        
        # Rune-specific narrative hooks
        rune_hooks = {
            'fehu': [
                "A merchant offers an unexpected deal",
                "Gold or valuables are glimpsed or mentioned",
                "Someone discusses wealth or prosperity",
                "An opportunity for profit presents itself"
            ],
            'uruz': [
                "A test of strength or endurance arises",
                "A wild animal is seen or heard",
                "Physical prowess is needed or displayed",
                "Someone speaks of primal power"
            ],
            'thurisaz': [
                "A challenge or obstacle appears",
                "Defense becomes necessary",
                "A rival or enemy is mentioned",
                "Thorny brambles or barriers noticed"
            ],
            'ansuz': [
                "A message or omen is received",
                "Someone speaks words of wisdom",
                "A prophecy or riddle is offered",
                "The gods seem to speak through events"
            ],
            'raidho': [
                "Travel or movement is discussed",
                "A journey is planned or begins",
                "The rhythm of events shifts",
                "Paths and roads feature prominently"
            ],
            'kenaz': [
                "Light reveals something hidden",
                "Knowledge or skill becomes key",
                "Craft or creativity is displayed",
                "A torch or fire illuminates"
            ],
            'gebo': [
                "A gift is offered or exchanged",
                "A partnership is proposed",
                "Hospitality features prominently",
                "Reciprocity is expected or honored"
            ],
            'wunjo': [
                "Joy or celebration occurs",
                "Fellowship brings comfort",
                "Success is achieved or celebrated",
                "Harmony among people"
            ],
            'hagalaz': [
                "Sudden disruption or change",
                "Weather turns harsh",
                "Plans are interrupted",
                "Transformation through difficulty"
            ],
            'nauthiz': [
                "Need or constraint is felt",
                "Resources are limited",
                "Patience is required",
                "Hardship teaches a lesson"
            ],
            'isa': [
                "A pause or stillness occurs",
                "Cold or ice features",
                "Reflection becomes necessary",
                "Movement is blocked or slowed"
            ],
            'jera': [
                "Harvest or reward is due",
                "Cycles or seasons are noted",
                "Patience pays off",
                "What was sown is reaped"
            ],
            'eihwaz': [
                "Endurance is tested",
                "Protection manifests",
                "Death and life intertwine",
                "The world tree is invoked"
            ],
            'perthro': [
                "Fate or chance plays a role",
                "Secrets are hinted at",
                "Gambling or risk appears",
                "Hidden knowledge surfaces"
            ],
            'algiz': [
                "Protection is offered or needed",
                "A guardian appears",
                "Sanctuary is found",
                "Divine protection manifests"
            ],
            'sowilo': [
                "Sun breaks through",
                "Victory is glimpsed",
                "Guidance is received",
                "Light conquers darkness"
            ],
            'tiwaz': [
                "Justice or honor is invoked",
                "A duel or challenge",
                "Sacrifice for greater good",
                "Oaths are sworn or tested"
            ],
            'berkano': [
                "Growth or healing occurs",
                "Renewal is offered",
                "Feminine wisdom appears",
                "New beginnings emerge"
            ],
            'ehwaz': [
                "Partnership proves valuable",
                "Horses or mounts feature",
                "Trust is tested or proven",
                "Movement with others"
            ],
            'mannaz': [
                "Human connection matters",
                "Self-reflection is needed",
                "Humanity's nature shown",
                "Social bonds are key"
            ],
            'laguz': [
                "Water or intuition features",
                "Dreams or visions occur",
                "Emotions run deep",
                "Flow and adaptation needed"
            ],
            'ingwaz': [
                "Potential awaits release",
                "Fertility or growth",
                "Internal development",
                "Seeds of future planted"
            ],
            'dagaz': [
                "Dawn or breakthrough",
                "Transformation complete",
                "Balance achieved",
                "New day begins"
            ],
            'othala': [
                "Heritage matters",
                "Ancestors are invoked",
                "Home or inheritance",
                "Legacy is discussed"
            ]
        }
        
        return rune_hooks.get(name, ["Fate's hand moves mysteriously"])
    
    def _default_rune(self) -> Dict[str, Any]:
        """Return a default rune if none loaded."""
        return {
            'name': 'Perthro',
            'symbol': 'ᛈ',
            'meaning': 'Mystery, fate',
            'keywords': ['fate', 'mystery', 'chance'],
            'influence_text': 'RUNE: ᛈ Perthro - Mystery and fate guide this moment.',
            'narrative_hooks': ['Fate moves in mysterious ways']
        }


class TurnProcessor:
    """
    Central turn processor that coordinates all game systems.
    """
    
    def __init__(self, engine, config: Dict = None):
        """
        Initialize with reference to main engine.
        
        Args:
            engine: The NorseSagaEngine instance
            config: Configuration dictionary
        """
        self.engine = engine
        self.config = config or {}
        
        # Initialize rune system
        data_path = self.config.get("paths", {}).get("data", "data")
        self.rune_system = RuneSystem(f"{data_path}/charts/elder_futhark.yaml")
        
        # Current turn rune
        self.current_rune: Optional[Dict] = None
        
        # Auto-draw settings
        self.auto_draw_every_n_turns = self.config.get("mystic", {}).get(
            "auto_draw_rune_every_n_turns", 3
        )
        self.rune_influence_strength = self.config.get("mystic", {}).get(
            "rune_influence_strength", "moderate"
        )

        # Huginn scouts battle signs; Muninn preserves structured combat memory.
        try:
            self.combat_resolver = ScriptedCombatResolver()
        except Exception as exc:
            logger.warning("Combat resolver unavailable: %s", exc)
            self.combat_resolver = None

        self._conditions_system: Optional[ConditionsSystem] = None
        if _CONDITIONS_SYSTEM_AVAILABLE:
            try:
                self._conditions_system = ConditionsSystem()
            except Exception as exc:
                logger.warning("ConditionsSystem unavailable in TurnProcessor: %s", exc)

        self._rules_engine: Optional[DndRulesEngine] = None
        if _RULES_ENGINE_AVAILABLE:
            try:
                self._rules_engine = DndRulesEngine()
            except Exception as exc:
                logger.warning("DndRulesEngine unavailable in TurnProcessor: %s", exc)
    
    def prepare_turn(self, player_action: str) -> TurnContext:
        """
        Prepare complete context for a turn.
        
        This gathers ALL relevant state to pass to the AI.
        """
        state = self.engine.state
        if not state:
            raise ValueError("No active game state")
        
        # Draw or get rune for this turn
        turn_number = state.turn_count
        if self.auto_draw_every_n_turns > 0:
            if turn_number % self.auto_draw_every_n_turns == 0 or not self.current_rune:
                self.current_rune = self.rune_system.draw_rune()
        
        # Get sub-location info
        sub_loc_name = ""
        sub_loc_desc = ""
        sub_loc_atmo = ""
        
        if hasattr(self.engine, 'city_grids'):
            city_id = state.current_location_id
            sub_loc_id = getattr(state, 'current_sub_location_id', 'main_mead_hall')
            
            if city_id in self.engine.city_grids:
                grid = self.engine.city_grids[city_id]
                if sub_loc_id in grid.sub_locations:
                    sub_loc = grid.sub_locations[sub_loc_id]
                    sub_loc_name = sub_loc.name
                    sub_loc_desc = sub_loc.description
                    sub_loc_atmo = sub_loc.atmosphere
        
        # Get party members specifically
        party_members = []
        other_npcs = []
        
        for npc in state.npcs_present:
            if npc.get("is_party_member"):
                party_members.append(npc)
            else:
                other_npcs.append(npc)
        
        # Get faction standings
        faction_standings = {}
        if hasattr(self.engine, 'faction_system') and self.engine.faction_system:
            for fid, faction in self.engine.faction_system.factions.items():
                faction_standings[fid] = {
                    "name": faction.name,
                    "reputation": faction.player_reputation,
                    "standing": faction.get_reputation_description()
                }
        
        # Get memory context
        memory_context = ""
        if hasattr(self.engine, 'memory_system_v3') and self.engine.memory_system_v3:
            memory_context = self.engine.memory_system_v3.get_context()
        elif hasattr(self.engine, 'memory_manager') and self.engine.memory_manager:
            memory_context = self.engine.memory_manager.get_summary()
        
        # Get custom prompts from config
        ai_prompts = self.config.get("ai_prompts", {})
        
        # Build turn context
        context = TurnContext(
            turn_number=turn_number,
            player_action=player_action,
            
            city=state.current_location_id,
            sub_location=getattr(state, 'current_sub_location_id', 'main_mead_hall'),
            sub_location_name=sub_loc_name or "Unknown",
            sub_location_description=sub_loc_desc,
            sub_location_atmosphere=sub_loc_atmo,
            
            player_character=state.player_character,
            npcs_present=other_npcs,
            party_members=party_members,
            
            rune=self.current_rune,
            rune_influence=self.current_rune.get('influence_text', '') if self.current_rune else '',
            
            chaos_factor=state.chaos_factor,
            time_of_day=state.time_of_day,
            season=state.season,
            year=state.year,
            
            active_quests=state.active_quests,
            pending_quests=getattr(state, 'pending_quests', []),
            
            faction_standings=faction_standings,
            memory_context=memory_context,
            recent_events=state.recent_events[-10:] if state.recent_events else [],
            
            in_combat=state.in_combat,
            combat_data=state.combat_data,
            
            custom_system_prompt=ai_prompts.get("system_prompt", ""),
            custom_post_history=ai_prompts.get("post_history_instruction", ""),
            world_rules=ai_prompts.get("world_rules", ""),
            character_voice=ai_prompts.get("character_voice", ""),
            narration_style=ai_prompts.get("narration_style", "")
        )
        
        return context
    
    def build_ai_prompt(self, context: TurnContext) -> str:
        """
        Build comprehensive AI prompt from turn context.
        
        This creates a complete prompt with all state information.
        """
        sections = []
        
        # ===== CUSTOM SYSTEM PROMPT (if any) =====
        if context.custom_system_prompt:
            sections.append(f"=== CUSTOM INSTRUCTIONS ===\n{context.custom_system_prompt}\n")
        
        # ===== CORE IDENTITY =====
        sections.append("""=== NORSE SAGA ENGINE - AI NARRATOR ===
You are the narrator of a Viking-age roleplaying game set in 9th century Scandinavia.
You control all NPCs, describe scenes, and narrate outcomes based on the player's actions.
The game uses D&D 5E mechanics invisibly - you describe results, not dice numbers.
""")
        
        # ===== WORLD RULES =====
        if context.world_rules:
            sections.append(f"=== WORLD RULES ===\n{context.world_rules}\n")
        
        # ===== CURRENT SCENE =====
        scene_info = f"""=== CURRENT SCENE ===
LOCATION: {context.sub_location_name} in {context.city.replace('_', ' ').title()}
TIME: {context.time_of_day.title()}, {context.season.title()}, Year {context.year} CE
CHAOS TEMPERATURE: {context.chaos_factor}/100 (higher = more unstable events)
"""
        
        if context.sub_location_description:
            scene_info += f"\nSCENE DESCRIPTION: {context.sub_location_description}"

        if context.sub_location_atmosphere:
            scene_info += f"\nATMOSPHERE: {context.sub_location_atmosphere}"
        
        sections.append(scene_info)
        
        # ===== RUNE INFLUENCE - CRITICAL =====
        if context.rune:
            rune_section = f"""=== RUNE INFLUENCE FOR THIS TURN ===
{context.rune_influence}

NARRATIVE HOOKS (weave one or more into the scene):
"""
            for hook in context.rune.get('narrative_hooks', []):
                rune_section += f"  - {hook}\n"
            
            rune_section += f"""
INFLUENCE STRENGTH: {self.rune_influence_strength}
The rune's themes should subtly influence the scene, NPC behavior, and outcomes.
"""
            sections.append(rune_section)
        
        # ===== PLAYER CHARACTER =====
        pc = context.player_character
        pc_identity = pc.get("identity", {})
        pc_personality = pc.get("personality", {})
        
        pc_section = f"""=== PLAYER CHARACTER ===
NAME: {pc_identity.get('name', 'Unknown')}
CLASS: {pc_identity.get('class', 'Fighter')} Level {pc_identity.get('level', 1)}
CULTURE: {pc_identity.get('culture', 'Norse').replace('_', ' ').title()}
"""
        
        if pc_personality.get('traits'):
            pc_section += f"PERSONALITY: {', '.join(pc_personality['traits'][:3])}\n"
        
        sections.append(pc_section)
        
        # ===== PARTY MEMBERS =====
        if context.party_members:
            party_section = "=== PARTY MEMBERS (traveling with player) ===\n"
            for member in context.party_members:
                identity = member.get("identity", {})
                name = identity.get("name", "Unknown")
                role = identity.get("role", "companion")
                loyalty = member.get("loyalty", 50)
                loyalty_desc = member.get("loyalty_desc", "neutral")
                party_section += f"  - {name} ({role}) - Loyalty: {loyalty} ({loyalty_desc})\n"
            sections.append(party_section)
        
        # ===== NPCs AT THIS LOCATION =====
        if context.npcs_present:
            npc_section = "=== PEOPLE AT THIS LOCATION ===\n"
            npc_section += "These NPCs are here. Only include them if interaction makes sense.\n"
            npc_section += "They do NOT follow the player. They have their own business.\n\n"
            
            for npc in context.npcs_present:
                identity = npc.get("identity", {})
                name = identity.get("name", "Unknown")
                role = identity.get("role", "")
                personality = npc.get("personality", {})
                traits = personality.get("traits", [])[:2]
                
                is_resident = npc.get("is_resident", False)
                status = "(lives/works here)" if is_resident else "(visiting)"
                
                npc_section += f"  - {name}: {role} {status}\n"
                if traits:
                    npc_section += f"    Personality: {', '.join(traits)}\n"
            
            
            sections.append(npc_section)
        
        # ===== FACTION STANDINGS =====
        if context.faction_standings:
            faction_section = "=== FACTION STANDINGS ===\n"
            for fid, data in context.faction_standings.items():
                if data['reputation'] != 0:
                    faction_section += f"  - {data['name']}: {data['reputation']:+d} ({data['standing']})\n"
            if faction_section.strip() != "=== FACTION STANDINGS ===":
                sections.append(faction_section)
        
        # ===== ACTIVE QUESTS =====
        if context.active_quests:
            quest_section = "=== ACTIVE QUESTS ===\n"
            for quest in context.active_quests[:5]:
                if isinstance(quest, dict):
                    quest_section += f"  - {quest.get('name', quest.get('id', 'Unknown quest'))}\n"
                else:
                    quest_section += f"  - {quest}\n"
            sections.append(quest_section)
        
        # ===== RECENT EVENTS =====
        if context.recent_events:
            events_section = "=== RECENT EVENTS ===\n"
            for event in context.recent_events[-5:]:
                events_section += f"  - {event}\n"
            sections.append(events_section)
        
        # ===== MEMORY CONTEXT =====
        if context.memory_context:
            sections.append(f"=== SESSION MEMORY ===\n{context.memory_context}\n")
        
        # ===== NPC BEHAVIOR RULES =====
        sections.append("""=== NPC BEHAVIOR RULES ===
CRITICAL: NPCs stay at their locations. They do NOT:
  - Follow the player around (unless in party)
  - Comment on everything the player does
  - Act as annoying stereotypes
  - Pester or demand attention

NPCs should:
  - React based on personality + relationship + situation
  - Have their own concerns and business
  - Respect social boundaries
  - End conversations naturally when done

Location-specific NPCs (Völva, Blacksmith, Jarl, etc.) STAY at their locations.
Only PARTY MEMBERS travel with the player.
""")
        
        # ===== NARRATION STYLE =====
        style_section = "=== NARRATION STYLE ===\n"
        if context.narration_style:
            style_section += f"{context.narration_style}\n"
        else:
            style_section += """- Narrate in vivid, saga-like prose
- Roleplay ALL characters (player and NPCs)
- Write authentic dialogue for the era
- Include sensory details (sounds, smells, textures)
- Let the rune's themes subtly influence events
- End with a moment inviting the player's next action
"""
        sections.append(style_section)
        
        # ===== CHARACTER VOICE =====
        if context.character_voice:
            sections.append(f"=== CHARACTER VOICE ===\n{context.character_voice}\n")
        
        # ===== COMBAT STATE =====
        if context.in_combat and context.combat_data:
            combat_section = "=== COMBAT IN PROGRESS ===\n"
            combat_section += "Combat is ongoing. Describe the action dramatically.\n"
            combat_section += f"Round Data: {json.dumps(context.combat_data, default=str)}\n"
            combat_section += "Honor D&D 5E action economy, rune pressure, and realistic shield-line timing.\n"

            # Inject SRD condition mechanics for player character
            try:
                pc = context.player_character or {}
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
                    effects: List[str] = []
                    if not block.can_take_actions:
                        effects.append("cannot take actions")
                    if not block.can_move:
                        effects.append("cannot move")
                    if block.attack_disadvantage:
                        effects.append("attack rolls at disadvantage")
                    if block.attack_advantage:
                        effects.append("attack rolls at advantage")
                    if block.save_auto_fail_str_dex:
                        effects.append("auto-fails STR/DEX saves")
                    if block.auto_crit_melee:
                        effects.append("melee hits are critical (auto-crit)")
                    if block.speed_halved:
                        effects.append("speed halved")
                    if block.speed_zero:
                        effects.append("speed = 0")
                    if effects:
                        combat_section += f"Player Condition Effects: {'; '.join(effects)}\n"

                # Inject equipped weapon SRD profile
                if self._rules_engine is not None:
                    equipment = pc_dnd5e.get("equipment", {})
                    if isinstance(equipment, dict):
                        weapons = equipment.get("weapons", [])
                        if isinstance(weapons, list) and weapons:
                            primary_weapon = str(weapons[0]) if weapons else ""
                            if primary_weapon:
                                wp = self._rules_engine.get_weapon_by_name(primary_weapon)
                                if wp:
                                    combat_section += (
                                        f"Primary Weapon: {wp.name} "
                                        f"({wp.damage} {wp.damage_type}"
                                        f"{', ' + ', '.join(wp.properties) if wp.properties else ''})\n"
                                    )
            except Exception as exc:
                logger.debug("Combat context SRD injection failed: %s", exc)

            sections.append(combat_section)
        
        # ===== PLAYER ACTION =====
        sections.append(f"""=== PLAYER'S ACTION ===
{context.player_action}

Now narrate the scene, incorporating the rune's influence subtly.
""")
        
        # ===== POST-HISTORY INSTRUCTION =====
        if context.custom_post_history:
            sections.append(f"=== ADDITIONAL INSTRUCTION ===\n{context.custom_post_history}")
        
        return "\n".join(sections)
    
    def generate_random_interaction(self, context: TurnContext) -> Optional[str]:
        """
        Generate a random NPC interaction based on rune and chaos.
        
        Returns a description to include in the AI prompt, or None.
        """
        if not context.npcs_present:
            return None
        
        # Chance based on chaos factor
        interaction_chance = min(95, max(10, int(context.chaos_factor * 0.9)))  # 10-95%
        if random.randint(1, 100) > interaction_chance:
            return None
        
        # Pick an NPC
        npc = random.choice(context.npcs_present)
        npc_name = npc.get("identity", {}).get("name", "A stranger")
        
        # Get a narrative hook from the rune
        hook = "makes an unexpected move"
        if context.rune and context.rune.get('narrative_hooks'):
            hook = random.choice(context.rune['narrative_hooks'])
        
        return f"RANDOM INTERACTION: {npc_name} - {hook}"
    
    def extract_quest_mentions(self, ai_response: str) -> List[Dict]:
        """
        Extract potential new quests from AI response.
        """
        quests = []
        
        # Patterns that suggest quest offers
        quest_patterns = [
            r"(?:will you|would you|can you|could you)\s+([^.?!]+\?)",
            r"(?:I need|we need|someone must)\s+([^.!]+)",
            r"(?:task|mission|quest|job)\s+(?:is\s+)?(?:to\s+)?([^.!]+)",
            r"(?:reward|pay|gold)\s+(?:for|if)\s+([^.!]+)",
        ]
        
        for pattern in quest_patterns:
            matches = re.findall(pattern, ai_response, re.IGNORECASE)
            for match in matches:
                if len(match) > 20 and len(match) < 200:
                    quests.append({
                        "description": match.strip(),
                        "source": "ai_response",
                        "status": "offered"  # Not yet accepted
                    })
        
        return quests[:2]  # Max 2 per turn
    
    def process_response(
        self, 
        context: TurnContext, 
        ai_response: str
    ) -> TurnResult:
        """
        Process the AI response and extract information.
        
        This handles:
        - Summarizing the response
        - Extracting new characters/quests/locations
        - Detecting combat
        - Tracking state changes
        """
        result = TurnResult(
            ai_response=ai_response,
            ai_summary=self._summarize_response(ai_response)
        )
        
        # Check for combat
        combat_keywords = ['attack', 'sword', 'axe', 'strike', 'hit', 'damage', 
                          'wound', 'blood', 'battle', 'fight', 'combat']
        combat_count = sum(1 for kw in combat_keywords if kw in ai_response.lower())
        if combat_count >= 3:
            result.combat_occurred = True

        if result.combat_occurred:
            result.combat_data = self._resolve_structured_combat(context, ai_response)
            result.damage_dealt = int(result.combat_data.get("damage_dealt", 0))
            result.damage_taken = int(result.combat_data.get("damage_taken", 0))
        
        # Extract quest mentions
        result.new_quests = self.extract_quest_mentions(ai_response)
        
        return result

    def _resolve_structured_combat(self, context: TurnContext, ai_response: str) -> Dict[str, Any]:
        """Resolve structured combat telemetry for Yggdrasil and memory systems."""
        if not self.combat_resolver:
            return {}

        try:
            attacker = context.player_character or {}
            defender = context.npcs_present[0] if context.npcs_present else {}

            telemetry = self.combat_resolver.resolve_exchange(
                attacker=attacker,
                defender=defender,
                combat_text=f"{context.player_action}\n{ai_response}",
                active_rune=context.rune,
            )
            payload = telemetry.to_dict()
            payload["damage_dealt"] = sum(i.get("damage", 0) for i in payload.get("injuries", []))
            payload["damage_taken"] = 0
            return payload
        except Exception as exc:
            logger.exception("Structured combat resolution failed: %s", exc)
            return {
                "errors": [str(exc)],
                "damage_dealt": 0,
                "damage_taken": 0,
            }
    
    def _summarize_response(self, response: str) -> str:
        """Create a brief summary of the AI response."""
        if not response:
            return ""
        
        # Get first 2-3 sentences as summary
        sentences = response.replace('\n', ' ').split('.')
        summary_sentences = [s.strip() for s in sentences[:3] if s.strip()]
        summary = '. '.join(summary_sentences)
        
        # Truncate if still too long
        if len(summary) > 300:
            summary = summary[:297] + "..."
        
        return summary


class QuestTracker:
    """Tracks static and dynamic quests with robust relevance logic and self-healing."""

    def __init__(self, data_path: str = "data"):
        self.data_path = Path(data_path)
        self.quests_path = self.data_path / "quests"
        self.auto_quests_path = self.data_path / "auto_generated" / "quests"
        self.auto_quests_path.mkdir(parents=True, exist_ok=True)

        self.active_quests: Dict[str, Dict] = {}
        self.pending_quests: List[Dict] = []
        self.completed_quests: List[str] = []
        self.declined_quests: List[str] = []
        self.quest_catalog: Dict[str, Dict] = self.load_all_quests()

    def load_all_quests(self) -> Dict[str, Dict]:
        """Load all quests from file storage and heal malformed data."""
        catalog: Dict[str, Dict] = {}

        def _load_yaml_file(quest_file: Path):
            try:
                with open(quest_file, 'r', encoding='utf-8') as handle:
                    payload = yaml.safe_load(handle) or {}
                if isinstance(payload, dict):
                    healed = self._heal_quest(payload)
                    if healed.get('id'):
                        catalog[healed['id']] = healed
            except Exception as exc:
                logger.warning("Quest YAML load failed for %s: %s", quest_file, exc)

        def _load_jsonl_file(quest_file: Path):
            try:
                with open(quest_file, 'r', encoding='utf-8') as handle:
                    for line in handle:
                        if not line.strip():
                            continue
                        payload = json.loads(line.strip())
                        if isinstance(payload, dict):
                            healed = self._heal_quest(payload)
                            if healed.get('id'):
                                catalog[healed['id']] = healed
            except Exception as exc:
                logger.warning("Quest JSONL load failed for %s: %s", quest_file, exc)

        for quest_file in (self.quests_path.rglob("*.yaml") if self.quests_path.exists() else []):
            _load_yaml_file(quest_file)
        for quest_file in self.auto_quests_path.glob("*.yaml"):
            _load_yaml_file(quest_file)
        for quest_file in self.auto_quests_path.glob("*.jsonl"):
            _load_jsonl_file(quest_file)

        self.quest_catalog = catalog
        logger.info("Quest catalog loaded with %s quests", len(catalog))
        return catalog

    def _heal_quest(self, quest: Dict[str, Any]) -> Dict[str, Any]:
        """Self-heal incomplete quest records into a safe normalized structure."""
        import hashlib

        healed = dict(quest or {})
        if not healed.get('id'):
            source = str(healed.get('name') or healed.get('description') or datetime.now().isoformat())
            healed['id'] = f"auto_{hashlib.md5(source.encode()).hexdigest()[:8]}"

        healed.setdefault('name', str(healed['id']).replace('_', ' ').title())
        healed.setdefault('type', 'side')
        healed.setdefault('status', 'available')
        healed.setdefault('difficulty', 'moderate')

        if not isinstance(healed.get('description'), dict):
            text = str(healed.get('description') or '')
            healed['description'] = {
                'hook': text[:120] if text else f"A new saga thread calls: {healed['name']}",
                'summary': text or f"The folk whisper of {healed['name']}.",
            }

        objectives = healed.get('objectives')
        if not isinstance(objectives, list) or not objectives:
            healed['objectives'] = [{
                'id': f"{healed['id']}_objective_1",
                'description': f"Advance the quest: {healed['name']}",
                'optional': False,
            }]

        rewards = healed.get('rewards')
        if not isinstance(rewards, dict):
            rewards = {}
        rewards.setdefault('xp', 50)
        healed['rewards'] = rewards

        return healed

    def _difficulty_for_level(self, player_level: int) -> str:
        if player_level <= 2:
            return 'easy'
        if player_level <= 4:
            return 'moderate'
        if player_level <= 7:
            return 'hard'
        return 'epic'

    def _scale_quest_for_level(self, quest: Dict[str, Any], player_level: int) -> Dict[str, Any]:
        scaled = dict(quest)
        rewards = dict(scaled.get('rewards') or {})
        base_xp = int(rewards.get('xp', 50) or 50)
        rewards['xp'] = max(25, int(base_xp * (1 + (max(1, player_level) - 1) * 0.18)))
        scaled['rewards'] = rewards
        scaled['recommended_level'] = max(1, player_level)
        scaled['difficulty'] = self._difficulty_for_level(player_level)
        return scaled

    def _is_quest_relevant(self, quest: Dict[str, Any], context: Dict[str, Any]) -> bool:
        location = str(context.get('location', '')).lower()
        npcs_present = {str(n).lower() for n in context.get('npcs_present', [])}

        quest_text = ' '.join([
            str(quest.get('name', '')),
            str((quest.get('description') or {}).get('summary', '')),
            str((quest.get('description') or {}).get('hook', '')),
        ]).lower()

        if location and location in quest_text:
            return True

        for npc in npcs_present:
            if npc and npc in quest_text:
                return True

        return quest.get('type') == 'main'

    def get_relevant_quests(self, context: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Return quests matching current situation, excluding active/completed/declined."""
        try:
            player_level = int(context.get('player_level', 1) or 1)
            active_ids = set(context.get('active_quest_ids', []) or [])
            completed_ids = set(context.get('completed_quest_ids', []) or [])
            declined_ids = set(self.declined_quests)

            quests = []
            for quest_id, quest in self.quest_catalog.items():
                if quest_id in active_ids or quest_id in completed_ids or quest_id in declined_ids:
                    continue
                if self._is_quest_relevant(quest, context):
                    quests.append(self._scale_quest_for_level(quest, player_level))

            quests.sort(key=lambda q: (q.get('type') != 'main', q.get('name', '')))
            return quests[:max(1, limit)]
        except Exception as exc:
            logger.warning("Relevant quest selection failed: %s", exc)
            return []

    def get_quest(self, quest_id: str) -> Optional[Dict[str, Any]]:
        """Get a quest by ID from catalog or runtime stores."""
        if quest_id in self.active_quests:
            return self.active_quests[quest_id]
        for quest in self.pending_quests:
            if quest.get('id') == quest_id:
                return quest
        return self.quest_catalog.get(quest_id)

    def generate_dynamic_quest(self, action: str, response: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate quest stubs from narrative triggers in action/response text."""
        combined = f"{action}\n{response}".lower()
        triggers = ('help', 'trouble', 'missing', 'stolen', 'threat', 'oath', 'vengeance', 'hunt')
        if not any(token in combined for token in triggers):
            return None

        import hashlib
        sig = hashlib.md5(combined[:600].encode()).hexdigest()[:8]
        location = context.get('location', 'midgard')
        level = int(context.get('player_level', 1) or 1)

        quest = {
            'id': f'auto_{sig}',
            'name': f'Whispers in {str(location).replace("_", " ").title()}',
            'type': 'side',
            'category': 'dynamic',
            'description': {
                'hook': 'A fresh knot of wyrd has tightened around nearby folk.',
                'summary': 'Recent events reveal a pressing local need. Investigate, choose a side, and act.',
            },
            'objectives': [
                {'id': 'investigate', 'description': 'Learn the truth behind the new disturbance', 'optional': False},
                {'id': 'resolve', 'description': 'Resolve the conflict in a way that honors your saga', 'optional': False},
            ],
            'rewards': {'xp': 60 + level * 20},
            'origin': 'dynamic_generation',
            'generated_at': datetime.now().isoformat(),
        }
        healed = self._heal_quest(quest)
        self.quest_catalog[healed['id']] = healed
        self._save_quest(healed)
        return healed

    def offer_quest(self, quest: Dict) -> str:
        """Offer a quest to the player (pending acceptance)."""
        healed = self._heal_quest(quest)
        quest_id = healed['id']
        if any(q.get('id') == quest_id for q in self.pending_quests):
            return quest_id

        healed['status'] = 'offered'
        healed['offered_at'] = datetime.now().isoformat()
        self.pending_quests.append(healed)
        self.quest_catalog[quest_id] = healed
        logger.info("Quest offered: %s", quest_id)
        return quest_id

    def accept_quest(self, quest_id: str) -> Tuple[bool, str]:
        for i, quest in enumerate(self.pending_quests):
            if quest.get('id') == quest_id:
                quest['status'] = 'active'
                quest['accepted_at'] = datetime.now().isoformat()
                self.active_quests[quest_id] = quest
                self.pending_quests.pop(i)
                self._save_quest(quest)
                return (True, f"Quest accepted: {quest.get('name', quest_id)}")
        return (False, "Quest not found in pending offers")

    def decline_quest(self, quest_id: str) -> Tuple[bool, str]:
        for i, quest in enumerate(self.pending_quests):
            if quest.get('id') == quest_id:
                self.declined_quests.append(quest_id)
                self.pending_quests.pop(i)
                return (True, "Quest declined")
        return (False, "Quest not found")

    def abandon_quest(self, quest_id: str) -> Tuple[bool, str]:
        if quest_id in self.active_quests:
            quest = self.active_quests.pop(quest_id)
            quest['status'] = 'abandoned'
            self._save_quest(quest)
            return (True, f"Quest abandoned: {quest.get('name', quest_id)}")
        return (False, "Quest not active")

    def update_quest_progress(self, quest_id: str, update: Dict):
        if quest_id in self.active_quests:
            quest = self.active_quests[quest_id]
            if 'objectives' in update:
                quest['objectives'] = update['objectives']
            if update.get('completed'):
                quest['status'] = 'completed'
                quest['completed_at'] = datetime.now().isoformat()
                if quest_id not in self.completed_quests:
                    self.completed_quests.append(quest_id)
            self._save_quest(quest)

    def _save_quest(self, quest: Dict):
        quest_id = quest.get('id', 'unknown')
        quest_file = self.auto_quests_path / f"{quest_id}.yaml"
        try:
            with open(quest_file, 'w', encoding='utf-8') as handle:
                yaml.safe_dump(quest, handle, allow_unicode=True, default_flow_style=False, sort_keys=False)
        except Exception as exc:
            logger.warning("Could not persist quest %s: %s", quest_id, exc)

    def get_active_quests(self) -> List[Dict]:
        return list(self.active_quests.values())

    def get_pending_quests(self) -> List[Dict]:
        return self.pending_quests

    def to_dict(self) -> Dict:
        return {
            'active_quests': self.active_quests,
            'pending_quests': self.pending_quests,
            'completed_quests': self.completed_quests,
            'declined_quests': self.declined_quests,
        }

    def from_dict(self, data: Dict):
        self.active_quests = data.get('active_quests', {})
        self.pending_quests = data.get('pending_quests', [])
        self.completed_quests = data.get('completed_quests', [])
        self.declined_quests = data.get('declined_quests', [])
