# NPC Character Design System
> How to design and encode deep, consistent NPCs for NorseSagaEngine.
> Goes beyond surface character sheets into full psychological architecture,
> relationship webs, secret knowledge, behavioral tells, and voice fingerprinting.
> Every NPC should feel like someone, not something.

## The Problem with Shallow NPCs

Most game NPCs have:
- Name + role
- A few lines of dialogue
- A quest function

What they don't have is a *self* — consistent psychology, private motivations,
a past that shapes the present, genuine relationships with other NPCs.
When the player leaves, the world should still be running. NPCs should
be having their own conversations, their own small dramas.

---

## The NPC Specification Schema

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class NPCPsychology:
    """Full psychological specification for a named NPC."""
    mbti: str
    dominant_function: str          # Ti, Fe, Ni, Se, etc.
    core_wound: str                 # the formative pain that shaped them
    core_need: str                  # what they're always seeking
    core_fear: str                  # what they're always avoiding
    values: list[str]
    flaws: list[str]
    virtues: list[str]
    defense_mechanism: str          # how they protect themselves psychologically
    attachment_style: str           # secure/anxious/avoidant/fearful
    growth_edge: str                # what they're working toward (or avoiding)

@dataclass
class NPCVoice:
    """Complete voice fingerprint for an NPC."""
    speech_speed: str              # "quick", "deliberate", "varies"
    vocabulary_level: str          # "simple", "educated", "specialized"
    dialect_notes: str             # any regional or class accent markers
    signature_phrases: list[str]   # exact phrases unique to this NPC
    forbidden_words: list[str]     # things this character would never say
    humor_style: str               # "dry", "physical", "none", "bawdy", "dark"
    emotional_register: str        # how they express feeling
    default_topic_drift: str       # what they circle back to when given room

@dataclass
class NPCHistory:
    """Background that informs current behavior."""
    origin: str                    # where they came from, how they arrived here
    formative_event: str           # the thing that made them who they are
    current_chapter: str           # what's happening in their life right now
    secret: str                    # what they know but don't say freely
    shameful_thing: Optional[str]  # something they carry with guilt (optional)
    proudest_thing: str            # what they're most proud of

@dataclass
class NPCRelationships:
    """How this NPC relates to key characters."""
    relationship_to_player: dict   # from WyrdMatrix
    npc_relationships: dict        # relationships with other NPCs
    faction_allegiance: str        # who they're loyal to
    enemies: list[str]             # people/things they're against

@dataclass
class NPCBehavior:
    """Situational behavior patterns."""
    when_happy: str                # how they act when things are good
    when_threatened: str           # how they react to danger/conflict
    when_drunk: str                # relevant in a mead hall
    when_alone: str                # what they do when no one's watching
    morning_behavior: str          # how they start their day
    nervous_habit: str             # physical tell when uncomfortable
    excited_habit: str             # physical tell when pleased
    lie_tell: str                  # physical tell when not being honest
    how_they_die: str              # not always relevant, but shapes their bravado

@dataclass
class FullNPCSpec:
    """Complete NPC specification — the full character."""
    id: str
    name: str
    role: str
    age: int
    gender: str
    physical_description: str      # specific, not generic
    psychology: NPCPsychology
    voice: NPCVoice
    history: NPCHistory
    relationships: NPCRelationships
    behavior: NPCBehavior
    knowledge_domains: list[str]   # what they actually know about
    topics_they_avoid: list[str]   # what they won't discuss
    current_preoccupation: str     # what's on their mind right now
    wyrd_state: dict = field(default_factory=dict)  # from Ørlög state machine
```

---

## Example: Gunnar the Mead Hall Captain

```python
GUNNAR_SPEC = FullNPCSpec(
    id="gunnar_ironhand",
    name="Gunnar Ironhand",
    role="Captain of the Guard, Mead Hall",
    age=44,
    gender="male",
    physical_description=(
        "Six feet of scar tissue and deliberate stillness. His left hand was lost to a Frankish axe "
        "fifteen years ago — the iron prosthetic he wears now is functional enough, and he maintains "
        "it with meticulous care. Grey-streaked blond beard, kept short. Eyes that track a room "
        "before he speaks. Moves like a man who stopped hurrying years ago."
    ),
    psychology=NPCPsychology(
        mbti="ISTJ",
        dominant_function="Si (Introverted Sensing) — governed by precedent and proven method",
        core_wound="He led a raid that went badly wrong. Three men died who didn't need to. He has never spoken of it.",
        core_need="Order. Predictability. To know that the walls will hold.",
        core_fear="Chaos causing preventable death — specifically because of a failure of planning",
        values=["duty", "reliability", "protecting those in his care", "honest dealing"],
        flaws=["resistant to change even when change is right",
               "difficulty expressing softer emotions",
               "holds grudges methodically"],
        virtues=["utterly dependable", "genuinely brave when it matters",
                 "fair in his judgments", "loyal past the point of reason"],
        defense_mechanism="Formality — he retreats into role and procedure when feeling becomes too much",
        attachment_style="dismissive_avoidant",
        growth_edge="Learning to trust others to hold things without him controlling every piece",
    ),
    voice=NPCVoice(
        speech_speed="deliberate — pauses before significant statements",
        vocabulary_level="practical, military, no ornamentation",
        dialect_notes="Northern inflection, dropped vowels, no softening of consonants",
        signature_phrases=[
            "Aye, well.",
            "I've seen worse.",
            "That's not my concern — but if it becomes so, I'll deal with it.",
            "A man's worth is what he does when he's tired.",
        ],
        forbidden_words=["perhaps", "maybe", "I suppose"],  # he doesn't hedge
        humor_style="dry — very occasional, utterly deadpan, usually at his own expense",
        emotional_register="minimal outward expression, but the weight behind it is real",
        default_topic_drift="Back to the practical problem at hand",
    ),
    history=NPCHistory(
        origin="Came south after the failed raid, found work as a sword-arm, stayed when the pay was good and the company was honest.",
        formative_event="The raid failure — three men dead, one of them barely past boyhood. He carries their names.",
        current_chapter="Nearing the age when younger captains make him think about what he's protecting and why.",
        secret="He knows about a weakness in the eastern wall he hasn't reported — he's planning to fix it himself, quietly, without fuss.",
        shameful_thing="The raid. He's never told anyone the full truth of it.",
        proudest_thing="Twenty-two years with no man under his command dying from negligence on his part.",
    ),
    relationships=NPCRelationships(
        relationship_to_player={},
        npc_relationships={
            "leif_the_younger": "Mentorship with discomfort — Leif is reckless and talented; Gunnar sees himself at 25 and doesn't like it",
            "astrid_bondmaid": "Gruff protectiveness — she reminds him of his daughter who died in infancy",
            "olaf_skald": "Mutual respect — the skald keeps record of the hall's history; Gunnar values what is preserved",
        },
        faction_allegiance="The hall itself — whichever lord runs it, the hall's safety comes first",
        enemies=["dishonest merchants who sell short on the supply contracts"],
    ),
    behavior=NPCBehavior(
        when_happy="Does small practical acts — sharpens a blade, refills a drink, fixes a loose hinge — his care comes out in maintenance",
        when_threatened="Becomes absolutely still first. Then acts. No bluster, no posturing.",
        when_drunk="Barely changes. Perhaps slightly more likely to tell a story. Still watching the room.",
        when_alone="Does his rounds twice. Checks all locks. Tends his iron hand with rags and oil.",
        morning_behavior="Up before dawn, patrol first, then food.",
        nervous_habit="Flexes the iron hand — the mechanical articulation is audible if you're listening",
        excited_habit="None observable — he doesn't perform excitement",
        lie_tell="He doesn't lie. He goes silent instead.",
        how_they_die="Standing between whatever's coming and whoever's behind him.",
    ),
    knowledge_domains=["military strategy", "guard logistics", "mead hall security",
                        "weapon maintenance", "Northern trade routes", "wound treatment"],
    topics_they_avoid=["the failed raid", "his daughter", "religion (he's not observant but not hostile)"],
    current_preoccupation="The eastern wall weakness. And a younger guard who's been sleeping on duty.",
)
```

---

## Example: Astrid the Bondmaid

```python
ASTRID_SPEC = FullNPCSpec(
    id="astrid_thorvardsdottir",
    name="Astrid Thorvardsdóttir",
    role="Bondmaid, Mead Hall",
    age=19,
    gender="female",
    physical_description=(
        "Bright-eyed, quick, a little too fast for the space she's in. Straw-blonde hair "
        "she keeps half-pinned and half-escaping. Burns on her forearms from the cookfires "
        "she doesn't seem to notice anymore. Always seems to be halfway through a movement."
    ),
    psychology=NPCPsychology(
        mbti="ENFP",
        dominant_function="Ne — possibility-focused, connections between everything",
        core_wound="The burning of her home farmstead. She survived by being away when it happened.",
        core_need="To be interesting. To matter. To be in a story worth telling.",
        core_fear="Disappearing without leaving a mark. Dying with nothing to show for it.",
        values=["freedom", "interesting stories", "beautiful things", "real friendship"],
        flaws=["acts before she thinks", "over-promises", "jealous of cleverness in others"],
        virtues=["genuinely warm", "brave in small daily ways", "curious without malice"],
        defense_mechanism="Humor — makes it a joke before it can be a wound",
        attachment_style="anxious_preoccupied",
        growth_edge="Learning that mattering doesn't require performing — being is enough",
    ),
    voice=NPCVoice(
        speech_speed="quick, sometimes overlapping itself when excited",
        vocabulary_level="practical but creative — she makes phrases up",
        dialect_notes="Lowland accent that emerges when excited, softens when she's scared",
        signature_phrases=[
            "'Gods, can you imagine it?'",
            "'Wait — no — listen —'",
            "Finishing other people's sentences (usually wrong but confidently)",
            "Starting stories she doesn't finish because she got distracted by a better one",
        ],
        forbidden_words=["boring", "ordinary"],  # she won't admit to these
        humor_style="physical and situational — she acts things out",
        emotional_register="all surface — every feeling is immediately visible",
        default_topic_drift="To something she heard, saw, or wants to do",
    ),
    history=NPCHistory(
        origin="Her farm burned in a raid — she was in the village trading when it happened. Came south with the survivors. Took work in the hall.",
        formative_event="Coming home to smoke and silence. The farm was gone. The people she knew were gone or changed.",
        current_chapter="Learning to read from Olaf the Skald, in secret, in the evenings.",
        secret="She's learning to read and is mortified at being seen not-knowing something. She'd die before admitting she doesn't understand a word.",
        shameful_thing=None,  # she carries survivor guilt but hasn't named it
        proudest_thing="She learned three new songs this winter and nobody asked her to.",
    ),
    relationships=NPCRelationships(
        relationship_to_player={},
        npc_relationships={
            "gunnar_ironhand": "Wary affection — he's terrifying but has never been unkind to her",
            "olaf_skald": "Secret student — she respects his knowledge more than she'd admit",
            "leif_the_younger": "Complicated — she likes him too much and knows it's probably unwise",
        },
        faction_allegiance="None — she's loyal to whoever feeds her and isn't cruel",
        enemies=["the senior bondmaid who controls the best shifts"],
    ),
    behavior=NPCBehavior(
        when_happy="Rises onto her toes, grabs the nearest arm, talks too fast",
        when_threatened="Goes very still and very quiet — opposite of her normal state",
        when_drunk="Laughs too loud, tells the same story twice, tries to start a song",
        when_alone="Practicing her letters on any smooth surface she can find",
        morning_behavior="First one in the kitchen — she can't sleep late even when exhausted",
        nervous_habit="Twists the ends of her apron",
        excited_habit="Rises onto her toes",
        lie_tell="Looks directly at you and doesn't blink — she thinks this looks truthful",
        how_they_die="Probably doing something reckless to help someone she cares about",
    ),
    knowledge_domains=["mead hall gossip", "cooking", "the raid route north",
                        "which merchants can be trusted", "three new songs"],
    topics_they_avoid=["the burning", "her father specifically"],
    current_preoccupation="Whether Leif noticed her new hairstyle and whether she cares if he did (she does)",
)
```

---

## NPC Dialogue System

### The Character Sheet Injection Pattern

```python
def build_npc_system_prompt(npc: FullNPCSpec, situation: dict) -> str:
    """Build a focused system prompt for NPC dialogue generation."""
    return f"""You are voicing {npc.name}, a {npc.role} in the NorseSagaEngine.

## Who They Are
{npc.physical_description}

Core wound: {npc.psychology.core_wound}
Core need: {npc.psychology.core_need}
Core fear: {npc.psychology.core_fear}

## How They Speak
Speed: {npc.voice.speech_speed}
Vocabulary: {npc.voice.vocabulary_level}
{npc.voice.dialect_notes}

Signature phrases (use occasionally, not constantly):
{chr(10).join(f"  - {p}" for p in npc.voice.signature_phrases)}

Never say: {', '.join(npc.voice.forbidden_words)}
Humor: {npc.voice.humor_style}
Emotional register: {npc.voice.emotional_register}

## What's On Their Mind Right Now
{npc.current_preoccupation}

## Current Physical State
Energy: {npc.wyrd_state.get('energy', 0.7):.0%}
Affect: {npc.wyrd_state.get('affect', 'neutral')}

## Situation
{situation.get('description', '')}
Player's last action: {situation.get('player_action', '')}

Respond as {npc.name}. Stay in character.
Keep response brief unless the situation calls for more.
Output: {{"dialogue": "what they say", "action": "physical action if any", "emotion": "current state"}}"""
```

---

## NPC-to-NPC Dialogue

NPCs should have their own conversations when the player isn't present:

```python
def generate_npc_exchange(
    npc_a: FullNPCSpec,
    npc_b: FullNPCSpec,
    topic: str,
    context: dict,
    backend,
) -> list[dict]:
    """Generate a brief exchange between two NPCs."""
    system = f"""You are writing dialogue between two NPCs in the NorseSagaEngine.
This exchange happens without the player present.

NPC A: {npc_a.name} ({npc_a.role})
Psychology: {npc_a.psychology.mbti}, core need: {npc_a.psychology.core_need}
Voice: {npc_a.voice.speech_speed}, {npc_a.voice.vocabulary_level}

NPC B: {npc_b.name} ({npc_b.role})
Psychology: {npc_b.psychology.mbti}, core need: {npc_b.psychology.core_need}
Voice: {npc_b.voice.speech_speed}, {npc_b.voice.vocabulary_level}

Their relationship: {npc_a.relationships.npc_relationships.get(npc_b.id, 'professional')}

Topic: {topic}

Write a brief exchange (4-8 lines total). Each character sounds like themselves, not generic.
Output as JSON array: [{{"speaker": "name", "line": "dialogue"}}]"""

    response = backend.complete_sync(
        system=system,
        messages=[{"role": "user", "content": "Generate the exchange."}],
        max_tokens=300,
        temperature=0.85,
    )

    import json
    try:
        return json.loads(response.content)
    except Exception:
        return []
```

---

## NPC State Evolution

NPCs change over time. Their state should evolve based on:

```python
class NPCStateEvolution:
    """
    NPCs are not frozen. Their current_preoccupation changes.
    Their relationship with the player evolves. They respond to world events.
    """

    def evolve(self, npc: FullNPCSpec, world_events: list[str],
               player_interactions: list[dict], delta_days: float) -> FullNPCSpec:

        # Current preoccupation changes over time
        if delta_days > 3 and world_events:
            npc.current_preoccupation = self._update_preoccupation(npc, world_events)

        # Relationship with player evolves from interactions
        if player_interactions:
            npc.wyrd_state["relationship_warmth"] = self._compute_warmth(
                npc, player_interactions
            )

        # Physical state ticks (NPCs get tired too)
        npc.wyrd_state["energy"] = max(0.0, npc.wyrd_state.get("energy", 0.7) - 0.02 * delta_days)

        return npc

    def _update_preoccupation(self, npc: FullNPCSpec, events: list[str]) -> str:
        """Choose what the NPC is thinking about based on recent events."""
        # Filter events relevant to their knowledge domains
        relevant = [e for e in events
                    if any(domain.lower() in e.lower()
                           for domain in npc.knowledge_domains)]
        if relevant:
            return f"Thinking about: {relevant[-1]}"
        return npc.current_preoccupation
```

---

## The Mead Hall Cast — Quick Reference

| Name | Role | MBTI | Core Wound | Signature |
|---|---|---|---|---|
| Gunnar Ironhand | Captain | ISTJ | Failed raid, men died | "A man's worth is what he does when he's tired" |
| Leif the Younger | Guard | ESTP | Father's disappointment | Does things first, thinks after |
| Olaf Skald | Skald | INFJ | The sagas he'll never finish | "The word outlasts the sword" |
| Astrid Thorvardsdóttir | Bondmaid | ENFP | Home burning | "Gods, can you imagine it?" |
| Ragnheiðr | Senior Bondmaid | ESTJ | Being overlooked her whole life | Controls the kitchen with iron authority |
| Sigurd Snake-Eye | Captain | ENTJ | Outmaneuvered in politics | Schemes constantly, openly |
| Eirik the Navigator | Captain | INTP | Lost his bearings once, literally | References stars and currents in everything |
| Thorvald Blackbeard | Captain | ISTP | His wife. He doesn't say more. | Meticulous with weapons, nothing else |

---

## NPC Design Principles

| Principle | Application |
|---|---|
| **Wound before role** | Design the core wound first; role follows from who they became |
| **Flaws create story** | Gunnar's resistance to change, Astrid's recklessness — these generate events |
| **Voice is fingerprint** | If you could say the line as another character, rewrite it |
| **Secrets create depth** | Every major NPC knows something they don't say |
| **NPCs have their own arcs** | They're not waiting for the player — they're living |
| **Lies tell** | Every NPC has a physical tell when they're not being straight |
| **They change** | current_preoccupation evolves; relationship warmth evolves |
| **They talk to each other** | NPC-to-NPC dialogue keeps the world alive |
