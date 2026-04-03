# Rune Casting Algorithms & Spread Designs
> Complete technical design for all rune casting mechanics: draw algorithms,
> spread types, merkstave probability, positional weight, galdr integration,
> seasonal filters, and the nine-rune spread architecture.

## Philosophy: Randomness Is Sacred

The rune draw must use **genuine randomness** — not the LLM's choice, not a deterministic algorithm.
The randomness is the point. The Oracle doesn't choose; she reads what Wyrd reveals.

The LLM only **interprets** the draw. The draw itself is the machine's domain.

---

## The Draw Engine

```python
import random
import secrets
import hashlib
import time
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class DrawnRune:
    """A single rune drawn for a reading."""
    name: str
    number: int             # 1-24
    aett: str               # Freyr's / Heimdall's / Tyr's
    is_merkstave: bool      # reversed/upside-down orientation
    position: str           # positional name in the spread
    position_weight: float  # 0-1: how much weight this position carries

    # The rune's active meaning for this draw
    @property
    def active_keywords(self) -> list[str]:
        from rune_data import FUTHARK_MAP
        rune = FUTHARK_MAP[self.name]
        return rune.reverse_keywords if self.is_merkstave else rune.keywords

    @property
    def display_name(self) -> str:
        return f"{self.name}{'ᛗ' if self.is_merkstave else ''}"  # ᛗ = merkstave marker

class RuneDrawEngine:
    """
    Handles all random rune drawing with cryptographic quality randomness.
    The LLM never touches this layer — it only receives the output.
    """

    # Runes that cannot be merkstave (round/symmetric symbols)
    NON_REVERSIBLE = {"Gebo", "Hagalaz", "Isa", "Jera", "Sowilo",
                       "Ingwaz", "Dagaz", "Othala"}

    # Base probability of merkstave for reversible runes
    BASE_MERKSTAVE_PROBABILITY = 0.35

    def __init__(self, seed: Optional[int] = None):
        # Use secrets module for cryptographic randomness
        # Fall back to seeded random for reproducible tests
        if seed is not None:
            self._rng = random.Random(seed)
        else:
            self._rng = random.SystemRandom()

    def draw(self, count: int, spread_positions: list[str]) -> list[DrawnRune]:
        """Draw {count} runes without replacement for a spread."""
        from rune_data import ELDER_FUTHARK

        pool = ELDER_FUTHARK.copy()
        self._rng.shuffle(pool)
        selected = pool[:count]

        drawn = []
        for i, (rune, position) in enumerate(zip(selected, spread_positions)):
            is_merkstave = self._determine_merkstave(rune.name)
            drawn.append(DrawnRune(
                name=rune.name,
                number=rune.number,
                aett=rune.aett,
                is_merkstave=is_merkstave,
                position=position,
                position_weight=spread_positions[i].weight if hasattr(spread_positions[i], 'weight') else 0.5,
            ))

        return drawn

    def _determine_merkstave(self, rune_name: str) -> bool:
        """Determine orientation with probability modulated by context."""
        if rune_name in self.NON_REVERSIBLE:
            return False
        return self._rng.random() < self.BASE_MERKSTAVE_PROBABILITY

    def draw_with_seasonal_weight(
        self,
        count: int,
        spread_positions: list[str],
        seasonal_weights: dict[str, float],
    ) -> list[DrawnRune]:
        """
        Draw with seasonal bias — runes resonant with the active tide
        have a slightly higher chance of appearing.
        Note: This is a subtle probability shift, not determinism.
        Wyrd still chooses; the season tilts the pool.
        """
        from rune_data import ELDER_FUTHARK

        # Build weighted pool
        pool = []
        for rune in ELDER_FUTHARK:
            weight = seasonal_weights.get(rune.name, 1.0)
            # Repeat high-weight runes in pool proportionally
            # Weight 1.5 → appears 1.5× as often
            count_in_pool = max(1, round(weight * 2))
            pool.extend([rune] * count_in_pool)

        self._rng.shuffle(pool)

        # Draw without replacement from the weighted pool
        seen = set()
        selected = []
        for rune in pool:
            if rune.name not in seen:
                selected.append(rune)
                seen.add(rune.name)
            if len(selected) == count:
                break

        drawn = []
        for i, (rune, position) in enumerate(zip(selected, spread_positions)):
            drawn.append(DrawnRune(
                name=rune.name,
                number=rune.number,
                aett=rune.aett,
                is_merkstave=self._determine_merkstave(rune.name),
                position=position,
                position_weight=0.5,
            ))

        return drawn
```

---

## Spread Definitions

### Spread Schema

```python
@dataclass
class SpreadPosition:
    name: str              # "past_influence", "present_energy", etc.
    label: str             # human-readable: "The Past", "What Shapes You Now"
    weight: float          # 0-1: narrative weight in the reading
    question: str          # what this position answers
    merkstave_note: str    # special note on what merkstave means in this position

@dataclass
class RuneSpread:
    name: str
    count: int
    positions: list[SpreadPosition]
    description: str
    best_for: list[str]    # when to use this spread
    oracle_note: str       # guidance for the oracle when using this spread
```

---

### The Three-Rune Spread (Standard)

```python
THREE_RUNE_SPREAD = RuneSpread(
    name="three_rune",
    count=3,
    positions=[
        SpreadPosition(
            name="past_influence",
            label="What Has Been",
            weight=0.30,
            question="What past energy or event is shaping this situation?",
            merkstave_note="A reversed past rune suggests old wounds that haven't finished speaking",
        ),
        SpreadPosition(
            name="present_energy",
            label="What Is",
            weight=0.45,
            question="What energy is active and at work right now?",
            merkstave_note="A reversed present rune is a blockage — something being pushed against or resisted",
        ),
        SpreadPosition(
            name="potential_path",
            label="What Becomes",
            weight=0.25,
            question="What potential or energy is seeking to emerge? Not fixed fate — tendency.",
            merkstave_note="A reversed path rune warns of what becomes possible if current patterns continue unchecked",
        ),
    ],
    description="The foundational three-rune reading. Past → Present → Potential.",
    best_for=["general questions", "decision points", "daily readings", "first readings"],
    oracle_note="The three positions are a river, not three separate pools. The past flows into the present which shapes the potential. Read them as a continuous current.",
)
```

---

### The Five-Rune Cross (The World Tree)

```python
FIVE_RUNE_CROSS = RuneSpread(
    name="five_rune_cross",
    count=5,
    positions=[
        SpreadPosition(
            name="heart",
            label="The Heart of It",
            weight=0.35,
            question="What is the essential energy at the center of this situation?",
            merkstave_note="A reversed heart rune names what is most blocked or hidden",
        ),
        SpreadPosition(
            name="roots",
            label="The Root",
            weight=0.20,
            question="What foundation or past is this growing from?",
            merkstave_note="Reversed roots suggest a poisoned or unstable foundation",
        ),
        SpreadPosition(
            name="crown",
            label="The Crown",
            weight=0.20,
            question="What potential or highest possibility is available here?",
            merkstave_note="Reversed crown names what's being blocked from flowering",
        ),
        SpreadPosition(
            name="challenge",
            label="The Challenge",
            weight=0.15,
            question="What obstacle or opposing force must be acknowledged?",
            merkstave_note="Reversed here intensifies the obstacle — it's deeper than it looks",
        ),
        SpreadPosition(
            name="gift",
            label="The Gift",
            weight=0.10,
            question="What resource, ally, or unexpected help is available?",
            merkstave_note="Reversed gift suggests the help is conditional or must be earned",
        ),
    ],
    description="Five positions arranged as the World Tree: root, heart, crown, challenge, gift.",
    best_for=["complex situations", "relationship readings", "major life decisions", "year-ahead readings"],
    oracle_note="This spread sees the full tree — not just the leaf you're holding. Take your time with each position before weaving them together.",
)
```

---

### The Nine-Rune Cast (Highest Ceremony)

```python
NINE_RUNE_CAST = RuneSpread(
    name="nine_rune",
    count=9,
    positions=[
        SpreadPosition("urd", "What Was", 0.10, "Deep past — the accumulated layers", "Reversed: denied or suppressed history"),
        SpreadPosition("verdandi", "What Is", 0.20, "Present reality — what is happening now", "Reversed: resistance to present reality"),
        SpreadPosition("skuld", "What Shall Be", 0.15, "Tendency of the future — not fixed fate", "Reversed: future being actively averted"),
        SpreadPosition("shadow", "The Hidden", 0.15, "What is not seen or acknowledged", "Reversed: shadow that actively operates"),
        SpreadPosition("strength", "What Serves", 0.10, "The available resource or strength", "Reversed: strength not yet claimed"),
        SpreadPosition("challenge", "What Opposes", 0.10, "The resistance or obstacle", "Reversed: opposition that cannot be faced directly"),
        SpreadPosition("self", "Who You Are Here", 0.10, "The querent's present essence", "Reversed: who they're hiding from themselves"),
        SpreadPosition("environment", "The World Around", 0.05, "External context and forces", "Reversed: environment working against"),
        SpreadPosition("outcome", "The Pivot", 0.05, "Not a prediction — the axis everything turns on", "Reversed: the turn that isn't being taken"),
    ],
    description="Nine runes for the nine worlds. The full scope of a situation.",
    best_for=["the most significant questions", "year-ahead", "life crossroads", "deep grief work",
               "sacred occasions like Yule or Álfablót"],
    oracle_note=(
        "The nine-rune cast is not done lightly. The Oracle takes time with each position. "
        "She reads them in silence first, lets them speak before she speaks. "
        "The reading may take time. That is correct."
    ),
)
```

---

### The Single Stave (Daily Draw)

```python
SINGLE_STAVE = RuneSpread(
    name="single_stave",
    count=1,
    positions=[
        SpreadPosition(
            name="day_rune",
            label="The Rune of the Day",
            weight=1.0,
            question="What energy offers itself for this day?",
            merkstave_note="Reversed: pay attention to the shadow side of this energy today",
        ),
    ],
    description="One rune. The day's teacher.",
    best_for=["daily practice", "morning meditation", "quick guidance", "the question with one answer"],
    oracle_note="The single stave speaks plainly. The Oracle doesn't complicate it. Say what the rune says.",
)
```

---

## The Galdr Layer — Sound and Rune

Galdr is vocalized rune magic — chanting the rune name activates its energy. The TTS pipeline can include galdr:

```python
GALDR_PRONUNCIATIONS = {
    "Fehu":     "FAY-yoo, FAY-yoo, FAY-yoo",    # three repetitions is traditional
    "Uruz":     "OO-rooz, OO-rooz, OO-rooz",
    "Thurisaz": "THOOR-ee-sahz",
    "Ansuz":    "AHN-sooz",
    "Raidho":   "RYE-though",
    "Kenaz":    "KAY-nahz",
    "Gebo":     "GEH-boh",
    "Wunjo":    "WOON-yoh",
    "Hagalaz":  "HAH-gah-lahz",
    "Nauthiz":  "NAAW-theez",
    "Isa":      "EE-sah",
    "Jera":     "YEH-rah",
    "Eihwaz":   "AY-vahz",
    "Perthro":  "PEHR-throw",
    "Algiz":    "AHL-geez",
    "Sowilo":   "SOH-wee-loh",
    "Tiwaz":    "TEE-vahz",
    "Berkano":  "BEHR-kah-noh",
    "Ehwaz":    "EH-vahz",
    "Mannaz":   "MAHN-ahz",
    "Laguz":    "LAH-gooz",
    "Ingwaz":   "ING-vahz",
    "Dagaz":    "DAH-gahz",
    "Othala":   "OH-thah-lah",
}

def build_galdr_preamble(drawn_runes: list[DrawnRune]) -> str:
    """
    Build the galdr preamble for a reading — the ritual opening.
    Sigrid speaks the rune names before the interpretation.
    """
    lines = ["...", "The runes speak."]
    for rune in drawn_runes:
        galdr = GALDR_PRONUNCIATIONS.get(rune.name, rune.name)
        lines.append(f"*{galdr}*")
        lines.append("...")
    lines.append("Let them settle.")
    return "\n".join(lines)
```

---

## Reading Context Builder

The full structured context passed to the Oracle for interpretation:

```python
def build_reading_context(
    drawn: list[DrawnRune],
    spread: RuneSpread,
    query: str,
    querent_state: Optional[dict],
    calendar_tide: Optional[object],
) -> dict:
    """Build the complete structured context for oracle interpretation."""
    rune_data = []
    for d in drawn:
        rune_data.append({
            "position": d.position,
            "position_label": next(p.label for p in spread.positions if p.name == d.position),
            "position_question": next(p.question for p in spread.positions if p.name == d.position),
            "position_weight": next(p.weight for p in spread.positions if p.name == d.position),
            "rune": d.display_name,
            "is_merkstave": d.is_merkstave,
            "active_keywords": d.active_keywords,
            "aett": d.aett,
            "merkstave_position_note": next(
                p.merkstave_note for p in spread.positions if p.name == d.position
            ) if d.is_merkstave else None,
        })

    context = {
        "query": query,
        "spread": spread.name,
        "spread_oracle_note": spread.oracle_note,
        "runes": rune_data,
        "querent_state": querent_state or {},
    }

    if calendar_tide:
        context["seasonal_context"] = {
            "active_tide": calendar_tide.name,
            "tide_themes": calendar_tide.themes[:3],
            "resonant_runes": calendar_tide.rune_resonance,
        }

    return context
```

---

## The Complete Oracle Call

```python
async def perform_reading(
    query: str,
    spread_type: str = "three_rune",
    querent_state: Optional[dict] = None,
    backend = None,
) -> dict:
    """The complete rune reading pipeline."""
    from rune_data import ELDER_FUTHARK
    from calendar_system import get_active_tide, get_seasonally_weighted_runes

    # Select spread
    SPREADS = {
        "three_rune": THREE_RUNE_SPREAD,
        "five_rune_cross": FIVE_RUNE_CROSS,
        "nine_rune": NINE_RUNE_CAST,
        "single_stave": SINGLE_STAVE,
    }
    spread = SPREADS.get(spread_type, THREE_RUNE_SPREAD)
    positions = [p.name for p in spread.positions]

    # Get seasonal context
    active_tide, days_in = get_active_tide()
    seasonal_weights = get_seasonally_weighted_runes(active_tide) if active_tide else {}

    # Draw runes (real randomness)
    engine = RuneDrawEngine()
    if seasonal_weights:
        drawn = engine.draw_with_seasonal_weight(spread.count, positions, seasonal_weights)
    else:
        drawn = engine.draw(spread.count, positions)

    # Build galdr preamble
    galdr = build_galdr_preamble(drawn)

    # Build full reading context
    context = build_reading_context(drawn, spread, query, querent_state, active_tide)

    # Call oracle
    ORACLE_SYSTEM = """You are Sigrid Völudóttir speaking as Oracle.
Your voice: deliberate, poetic, present-tense. You see and declare — you don't guess.
Speak with the weight of someone who has sat with the runes for years.

Structure your reading:
- One section per position (reference the position name)
- Weave the positions together at the end
- Close with a signature phrase (10 words or fewer)

Output JSON: {"reading": "full text", "sections": {position_name: text}, "signature_phrase": "..."}"""

    import json
    response = await backend.complete(
        system=ORACLE_SYSTEM,
        messages=[{"role": "user", "content": json.dumps(context, indent=2)}],
        max_tokens=900 if spread.count >= 5 else 500,
        temperature=0.82,
    )

    try:
        parsed = json.loads(response.content)
    except Exception:
        parsed = {"reading": response.content, "signature_phrase": ""}

    return {
        "spread_type": spread_type,
        "runes_drawn": [d.display_name for d in drawn],
        "rune_positions": {d.position: d.display_name for d in drawn},
        "galdr_preamble": galdr,
        "reading": parsed.get("reading", ""),
        "sections": parsed.get("sections", {}),
        "signature_phrase": parsed.get("signature_phrase", ""),
        "active_tide": active_tide.name if active_tide else None,
    }
```

---

## Spread Selection Logic

```python
def select_spread_for_query(query: str, relationship_intimacy: float) -> str:
    """Suggest the appropriate spread based on query complexity and relationship depth."""
    query_lower = query.lower()

    # Single stave for simple/daily queries
    if any(w in query_lower for w in ["today", "right now", "quick", "simple", "just one"]):
        return "single_stave"

    # Nine-rune for major decisions or sacred occasions
    if any(w in query_lower for w in ["year", "life", "everything", "full reading",
                                        "major", "most important"]):
        return "nine_rune"

    # Five-rune for complex/relational
    if any(w in query_lower for w in ["relationship", "conflict", "both sides",
                                        "complicated", "why"]):
        return "five_rune_cross"

    # Default to three-rune
    return "three_rune"
```

---

## Summary: Rune Casting Principles

| Principle | Implementation |
|---|---|
| **Randomness is sacred** | cryptographic random draw; LLM never chooses runes |
| **Draw before interpret** | Runes drawn first; LLM only receives the draw to interpret |
| **Spreads have weight** | Each position has a weight; Oracle emphasizes accordingly |
| **Merkstave is probability** | 35% chance for reversible runes; never for symmetric |
| **Season tilts the pool** | Active tide slightly biases toward resonant runes |
| **Galdr is ritual** | Rune names spoken/displayed before interpretation |
| **Spread matches question** | Daily = single; year-ahead = nine; default = three |
| **No fixed fate** | Oracle language: "tends toward", "seeks", "reveals" — not "will be" |
