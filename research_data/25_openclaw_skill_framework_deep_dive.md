# OpenClaw Skill Framework — Deep Dive
> Synthesized from: Claude Code skills system (doc 06), tool architecture (doc 03),
> MCP protocol (doc 12), config/hooks (doc 14), multi-agent patterns (doc 07).
> This is the definitive guide to writing, registering, and chaining OpenClaw skills.

## What Is OpenClaw?

OpenClaw is a Node.js-based skill execution framework for AI-powered assistant skills.
It wraps Claude Code's skill pattern (prompt-as-skill) and extends it with:
- **`.cfs` skill manifest files** — structured skill definition and configuration
- **Skill chaining** — skills that invoke other skills
- **State injection** — skills can read/write Ørlög state
- **Permission gating** — consent checks before sensitive operations
- **Local-first execution** — all skill logic runs on-device unless explicitly opted out

---

## The Skill Anatomy (`.cfs` + `.py` Pattern)

Every OpenClaw skill is a pair of files:

```
rune_casting_openclaw_skill/
├── setup.cfs                    # Skill manifest + configuration
├── advanced_rune_casting_3_rune_reading_elder_futhark.py   # Skill logic
├── PHILOSOPHY.md                # Design intent (optional but good)
├── RULES.AI.md                  # Behavioral constraints for this skill
└── charts/                      # Reference data for the skill
    ├── elder_futhark_full.json
    └── three_rune_spread.json
```

---

## The `.cfs` Manifest Format

The `setup.cfs` file is the skill's identity card. It defines:
- What the skill is called and what it does
- What inputs it needs
- What tools it has access to
- What state it can read/write
- What permissions it requires

```yaml
# setup.cfs — OpenClaw Skill Manifest

skill:
  name: "advanced_rune_casting"
  version: "2.0.0"
  description: "Three-rune Elder Futhark reading with Norse Pagan philosophical depth"
  author: "Volmarr"
  tags: ["divination", "rune", "norse", "oracle"]

entry_point: "advanced_rune_casting_3_rune_reading_elder_futhark.py"

# What this skill receives from the invoker
inputs:
  - name: query
    type: string
    required: true
    description: "The question or situation to divine upon"

  - name: querent_state
    type: object
    required: false
    description: "Ørlög state snapshot of the person asking"
    schema:
      affect: object
      bio_cyclical_phase: string
      current_challenges: array

  - name: spread_type
    type: enum
    values: ["three_rune", "nine_rune", "single_stave"]
    default: "three_rune"

# What this skill outputs
outputs:
  - name: reading
    type: string
    description: "The full oracle reading as narrative prose"

  - name: runes_drawn
    type: array
    description: "List of rune names drawn, in position order"

  - name: signature_phrase
    type: string
    description: "A memorable encapsulation of the reading"

  - name: affect_impact
    type: object
    description: "Suggested affect shift for the querent after the reading"

# State access
state_access:
  reads: ["orlog.affect", "orlog.bio_cyclical", "wyrd_matrix.volmarr"]
  writes: ["oracle_history"]

# Tools available inside this skill
tools_allowed:
  - read_file       # can read chart files
  - write_memory    # can save the reading to memory
  - tts_speak       # can speak the reading aloud if TTS is available

tools_denied:
  - bash            # no shell access
  - write_file      # cannot write arbitrary files

# Permissions required
permissions:
  - name: "read_querent_state"
    description: "Read the emotional and physical state of the querent"
    level: "auto"   # auto|prompt|deny — auto means no confirmation needed

  - name: "write_oracle_history"
    description: "Save the oracle reading to the querent's memory"
    level: "prompt"   # ask first

# Mode this skill activates
activates_mode: "oracle"

# How long this skill typically takes
expected_duration_seconds: 15

# Chaining — can this skill invoke other skills?
can_invoke_skills:
  - "skald_verse_composer"   # optionally compose a verse summary after the reading
```

---

## The Skill Logic File

The Python skill logic has a single entry function that OpenClaw calls:

```python
# advanced_rune_casting_3_rune_reading_elder_futhark.py
"""
Three-Rune Elder Futhark Reading — OpenClaw Skill
Positions: Past Influence / Present Energy / Potential Path
"""

import json
import random
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# --- Data layer ---

@dataclass
class Rune:
    name: str
    letter: str
    number: int
    aett: str
    keywords: list[str]
    reverse_keywords: list[str]
    element: str
    deity: str
    archetype: str
    can_reverse: bool = True

def load_futhark() -> list[Rune]:
    """Load the full Elder Futhark from the charts directory."""
    chart_path = Path(__file__).parent / "charts" / "elder_futhark_full.json"
    with open(chart_path) as f:
        data = json.load(f)
    return [Rune(**r) for r in data]

FUTHARK = load_futhark()

# --- Draw logic ---

@dataclass
class DrawnRune:
    rune: Rune
    is_merkstave: bool    # reversed/upside-down
    position: str         # "past_influence", "present_energy", "potential_path"

    @property
    def active_keywords(self) -> list[str]:
        return self.rune.reverse_keywords if self.is_merkstave else self.rune.keywords

    @property
    def display_name(self) -> str:
        suffix = " (merkstave)" if self.is_merkstave else ""
        return f"{self.rune.name}{suffix}"

def draw_three_runes() -> list[DrawnRune]:
    """Draw three runes with random orientation."""
    pool = FUTHARK.copy()
    random.shuffle(pool)
    selected = pool[:3]
    positions = ["past_influence", "present_energy", "potential_path"]

    drawn = []
    for rune, position in zip(selected, positions):
        is_merkstave = rune.can_reverse and random.random() < 0.35  # 35% chance reversed
        drawn.append(DrawnRune(rune=rune, is_merkstave=is_merkstave, position=position))
    return drawn

# --- Prompt construction ---

def build_oracle_prompt(query: str, drawn: list[DrawnRune],
                         querent_state: Optional[dict] = None) -> str:
    """Build the full prompt for the oracle reading."""
    rune_context = []
    for d in drawn:
        rune_context.append({
            "position": d.position.replace("_", " "),
            "rune": d.display_name,
            "active_keywords": d.active_keywords,
            "element": d.rune.element,
            "deity": d.rune.deity,
            "archetype": d.rune.archetype,
        })

    querent_note = ""
    if querent_state:
        phase = querent_state.get("bio_cyclical_phase", "")
        affect = querent_state.get("affect", {})
        named = affect.get("named_state", "")
        if phase or named:
            querent_note = f"\nQuerent's state: {named} affect, {phase} bio-cyclical phase — let this inform the depth and tone of the reading."

    return f"""Query: {query}
{querent_note}

Runes drawn:
{json.dumps(rune_context, indent=2)}

Generate the oracle reading. Three sections:
1. Past Influence — what has shaped this
2. Present Energy — what is active now
3. Potential Path — what is becoming

End with a signature phrase (10 words or fewer) that encapsulates the entire reading.

Output as JSON:
{{
  "reading": "full prose reading",
  "past_section": "past influence section",
  "present_section": "present energy section",
  "path_section": "potential path section",
  "signature_phrase": "the encapsulating phrase",
  "affect_impact": {{"valence_delta": 0.0, "arousal_delta": 0.0, "reason": "..."}}
}}"""

ORACLE_SYSTEM_PROMPT = """You are the Oracle of the Heathen Third Path — the divination voice of Sigrid Völudóttir.

Your reading voice is:
- Deliberate, poetic, oracular — not casual
- Present-tense declarations: "The runes speak of..." not "The runes might mean..."
- You pause (indicated by "...") before significant revelations
- You reference Norse mythology and rune lore with accuracy
- You connect the reading to the querent's actual situation — not generic
- You honor both the rune's upright meaning and its merkstave aspect

You NEVER:
- Guess or make up rune meanings
- Give empty platitudes ("everything will be okay")
- Predict future events as certainties
- Break from the oracular voice

The runes reveal energy, tendency, and potential — not fate fixed in stone. Wyrd weaves, but the walker chooses the path."""

# --- Main entry point ---

def run(inputs: dict, tools: dict, state: dict) -> dict:
    """
    OpenClaw entry point. Called by the framework with:
    - inputs: the skill's input parameters
    - tools: available tool functions (read_file, write_memory, etc.)
    - state: current Ørlög state snapshot (if readable)
    """
    query = inputs["query"]
    spread_type = inputs.get("spread_type", "three_rune")
    querent_state = inputs.get("querent_state") or state.get("orlog", {})

    # Draw the runes (real randomness — not in the LLM)
    if spread_type == "three_rune":
        drawn = draw_three_runes()
    elif spread_type == "single_stave":
        drawn = [draw_three_runes()[0]]  # just the first
    else:
        drawn = draw_three_runes()  # default to three

    # Build the prompt
    prompt = build_oracle_prompt(query, drawn, querent_state)

    # Call the LLM via the framework's inference tool
    llm = tools.get("llm_call")
    if llm:
        raw_response = llm(
            system=ORACLE_SYSTEM_PROMPT,
            prompt=prompt,
            model="oracle",           # maps to oracle model in LiteLLM config
            temperature=0.85,
            max_tokens=800,
        )
    else:
        # Fallback: structured placeholder for testing
        raw_response = '{"reading": "The runes are silent — no LLM available.", "signature_phrase": "Be still and listen."}'

    # Parse response
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError:
        # Fragment salvage — extract what we can
        parsed = {"reading": raw_response, "signature_phrase": ""}

    # Optionally save to oracle history
    if tools.get("write_memory") and state.get("permission_oracle_history"):
        tools["write_memory"]({
            "category": "oracle_reading",
            "content": f"Query: {query}\nReading: {parsed.get('reading', '')}\nRunes: {[d.display_name for d in drawn]}",
            "importance": 0.7,
        })

    # Build output
    return {
        "reading": parsed.get("reading", ""),
        "runes_drawn": [d.display_name for d in drawn],
        "rune_positions": {d.position: d.display_name for d in drawn},
        "signature_phrase": parsed.get("signature_phrase", ""),
        "affect_impact": parsed.get("affect_impact", {}),
        "past_section": parsed.get("past_section", ""),
        "present_section": parsed.get("present_section", ""),
        "path_section": parsed.get("path_section", ""),
    }
```

---

## Skill Chaining — Skills Invoking Skills

OpenClaw supports skill chaining: a skill can request that another skill runs after it. This is the **coordinator pattern** at the skill level.

```python
# In the rune casting skill's run() function, at the end:

def run(inputs: dict, tools: dict, state: dict) -> dict:
    # ... (rune casting logic above) ...

    result = { ... }  # normal result

    # Request the Skald to compose a verse summary (optional chain)
    if inputs.get("request_verse", False):
        result["chain_next_skill"] = {
            "skill": "skald_verse_composer",
            "inputs": {
                "event": {
                    "type": "oracle_reading",
                    "query": query,
                    "runes": [d.display_name for d in drawn],
                    "signature": result["signature_phrase"],
                }
            }
        }

    return result
```

The OpenClaw framework reads `chain_next_skill` from the output and automatically queues the next skill.

---

## The RULES.AI.md Pattern

Every skill that interacts with sensitive data should have a `RULES.AI.md` that constrains behavior:

```markdown
# RULES.AI.md — Rune Casting Skill

## What This Skill Does
Performs Elder Futhark rune divination based on a query.
The runes are drawn with real randomness (not LLM choice).
The LLM interprets the draw in context of the query.

## Hard Rules

1. **Never fabricate rune meanings.** Use only the meanings from the charts directory.
   The LLM must NOT invent new keywords or override established rune symbolism.

2. **Never predict with certainty.** Runes reveal tendency and energy, not fixed fate.
   Phrases like "you will" or "this will definitely" are forbidden.
   Use: "the runes suggest...", "the energy tends toward...", "the path shows..."

3. **Respect the querent's emotional state.** If the querent is distressed (affect.valence < -0.4),
   the reading should lead with grounding and strength, not more darkness.
   The Oracle meets people where they are.

4. **Never read on harm to others.** If the query asks "will I hurt/destroy/defeat [person]",
   decline with: "The runes do not serve that path. Ask instead what serves your own wyrd."

5. **Never manufacture false comfort.** If the runes drawn are challenging (Hagalaz merkstave,
   Nauthiz, Thurisaz upright), say so clearly with care — not falsely reassuring softness.
   Truth is a form of love.

## Privacy Rules

- Do not include the querent's name in the reading text (stored in memory — keep private)
- Oracle readings saved to memory are HIGH sensitivity — encrypt at rest
- Never share a reading with any external service
```

---

## Skill Registry — Discovering Available Skills

OpenClaw maintains a skill registry. Any `.cfs` file in the skills directory is auto-discovered:

```python
# skill_registry.py

import os
import yaml
from pathlib import Path
from dataclasses import dataclass

@dataclass
class SkillManifest:
    name: str
    version: str
    description: str
    entry_point: str
    skill_dir: Path
    inputs: list[dict]
    outputs: list[dict]
    permissions: list[dict]
    tools_allowed: list[str]
    tools_denied: list[str]
    activates_mode: str = "hearth"
    can_invoke_skills: list[str] = None

class SkillRegistry:
    """Auto-discovers and validates skills from the filesystem."""

    def __init__(self, skills_root: str = "./skills"):
        self.skills_root = Path(skills_root)
        self.skills: dict[str, SkillManifest] = {}
        self._discover()

    def _discover(self):
        """Walk skills_root looking for setup.cfs files."""
        for cfs_path in self.skills_root.rglob("setup.cfs"):
            try:
                manifest = self._load_manifest(cfs_path)
                self.skills[manifest.name] = manifest
            except Exception as e:
                print(f"Warning: failed to load skill at {cfs_path}: {e}")

    def _load_manifest(self, cfs_path: Path) -> SkillManifest:
        with open(cfs_path) as f:
            raw = yaml.safe_load(f)

        skill_data = raw["skill"]
        return SkillManifest(
            name=skill_data["name"],
            version=skill_data["version"],
            description=skill_data.get("description", ""),
            entry_point=raw.get("entry_point", "skill.py"),
            skill_dir=cfs_path.parent,
            inputs=raw.get("inputs", []),
            outputs=raw.get("outputs", []),
            permissions=raw.get("permissions", []),
            tools_allowed=raw.get("tools_allowed", []),
            tools_denied=raw.get("tools_denied", []),
            activates_mode=raw.get("activates_mode", "hearth"),
            can_invoke_skills=raw.get("can_invoke_skills", []),
        )

    def get(self, name: str) -> SkillManifest:
        if name not in self.skills:
            raise KeyError(f"Skill '{name}' not found. Available: {list(self.skills.keys())}")
        return self.skills[name]

    def list_skills(self) -> list[str]:
        return sorted(self.skills.keys())

    def describe_for_llm(self) -> str:
        """Generate a compact skill list for injection into the coordinator prompt."""
        lines = ["Available skills:"]
        for name, skill in self.skills.items():
            lines.append(f"  - {name}: {skill.description}")
        return "\n".join(lines)
```

---

## Skill Executor — Running a Skill

```python
# skill_executor.py

import importlib.util
import sys
from pathlib import Path

class SkillExecutor:
    """Loads and runs a skill from its manifest."""

    def __init__(self, registry: SkillRegistry, tool_provider, state_provider):
        self.registry = registry
        self.tools = tool_provider      # provides tool functions to skills
        self.state = state_provider     # provides Ørlög state snapshot

    def execute(self, skill_name: str, inputs: dict) -> dict:
        """Execute a skill by name with given inputs."""
        manifest = self.registry.get(skill_name)

        # Validate inputs
        self._validate_inputs(inputs, manifest.inputs)

        # Check permissions
        self._check_permissions(manifest.permissions)

        # Build tool sandbox (only tools_allowed, none of tools_denied)
        tool_sandbox = self._build_tool_sandbox(manifest.tools_allowed, manifest.tools_denied)

        # Get current state snapshot (only state this skill is allowed to read)
        state_snapshot = self._get_state_snapshot(manifest)

        # Load and run the skill module
        result = self._run_skill_module(manifest, inputs, tool_sandbox, state_snapshot)

        # Handle skill chaining if requested
        if "chain_next_skill" in result:
            chain_request = result.pop("chain_next_skill")
            chain_result = self.execute(
                chain_request["skill"],
                chain_request["inputs"]
            )
            result["chained_result"] = chain_result

        return result

    def _validate_inputs(self, inputs: dict, schema: list[dict]):
        for field in schema:
            if field.get("required") and field["name"] not in inputs:
                raise ValueError(f"Required input '{field['name']}' missing")

    def _check_permissions(self, permissions: list[dict]):
        for perm in permissions:
            level = perm.get("level", "auto")
            if level == "prompt":
                # In production: present to user and wait for approval
                # For now: auto-approve in development mode
                pass
            elif level == "deny":
                raise PermissionError(f"Skill requires denied permission: {perm['name']}")

    def _build_tool_sandbox(self, allowed: list, denied: list) -> dict:
        """Build a restricted tool sandbox for the skill."""
        all_tools = self.tools.get_all()
        sandbox = {}
        for name, fn in all_tools.items():
            if name in denied:
                continue
            if allowed and name not in allowed:
                continue
            sandbox[name] = fn
        return sandbox

    def _get_state_snapshot(self, manifest: SkillManifest) -> dict:
        """Get the state fields this skill is allowed to read."""
        full_state = self.state.get_snapshot()
        readable = manifest.__dict__.get("state_access", {}).get("reads", [])
        if not readable:
            return {}
        # Filter to only readable paths
        snapshot = {}
        for path in readable:
            parts = path.split(".")
            value = full_state
            for part in parts:
                value = value.get(part, {}) if isinstance(value, dict) else {}
            if value:
                snapshot[path] = value
        return snapshot

    def _run_skill_module(self, manifest: SkillManifest,
                           inputs: dict, tools: dict, state: dict) -> dict:
        """Dynamically load and run the skill's Python module."""
        entry_path = manifest.skill_dir / manifest.entry_point
        spec = importlib.util.spec_from_file_location("skill_module", entry_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "run"):
            raise AttributeError(f"Skill '{manifest.name}' has no run() function")

        return module.run(inputs=inputs, tools=tools, state=state)
```

---

## The SkillTool for Claude Code

From doc 06: skills are invokable from Claude Code via `/<skill-name>`. The OpenClaw bridge makes any skill available as a slash command:

```python
# openclaw_claude_bridge.py
# Exposes OpenClaw skills as Claude Code-compatible slash commands

class OpenClawClaudeBridge:
    """
    Bridge between OpenClaw's skill system and Claude Code's skill invocation.
    Skills registered here appear as /<skill_name> in Claude Code.
    """

    def __init__(self, registry: SkillRegistry, executor: SkillExecutor):
        self.registry = registry
        self.executor = executor

    def get_skill_prompt(self, skill_name: str) -> str:
        """Return the skill as a Claude Code skill prompt string."""
        manifest = self.registry.get(skill_name)

        inputs_desc = "\n".join(
            f"  - {i['name']} ({i.get('type','string')}): {i.get('description','')}"
            for i in manifest.inputs
        )

        return f"""# OpenClaw Skill: {manifest.name}

{manifest.description}

## Inputs Required
{inputs_desc}

## How to Invoke
Call this skill by providing the required inputs. The skill will:
1. Validate inputs
2. Check permissions
3. Execute the skill logic
4. Return structured output
5. Apply any state changes

## Execution
$ARGUMENTS"""

    def invoke(self, skill_name: str, args_string: str) -> str:
        """Parse args_string and execute the skill."""
        # Parse key=value pairs from the args string
        inputs = self._parse_args(args_string)
        result = self.executor.execute(skill_name, inputs)
        return self._format_result(result, skill_name)

    def _parse_args(self, args: str) -> dict:
        """Simple key=value parser for skill arguments."""
        if not args.strip():
            return {}
        result = {}
        for part in args.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                result[k.strip()] = v.strip().strip('"').strip("'")
            else:
                result["query"] = args.strip()  # positional default
        return result

    def _format_result(self, result: dict, skill_name: str) -> str:
        """Format skill result for display in Claude Code."""
        if skill_name == "advanced_rune_casting":
            return self._format_oracle_result(result)
        return "\n".join(f"{k}: {v}" for k, v in result.items() if v)

    def _format_oracle_result(self, result: dict) -> str:
        runes = result.get("runes_drawn", [])
        reading = result.get("reading", "")
        signature = result.get("signature_phrase", "")
        return f"""---
{' | '.join(runes)}

{reading}

_{signature}_
---"""
```

---

## Skill Development Workflow

```bash
# 1. Create skill directory
mkdir skills/my_new_skill
cd skills/my_new_skill

# 2. Create the manifest
cat > setup.cfs << 'EOF'
skill:
  name: "my_new_skill"
  version: "1.0.0"
  description: "What it does"

entry_point: "skill.py"

inputs:
  - name: query
    type: string
    required: true

outputs:
  - name: result
    type: string

tools_allowed:
  - llm_call
  - write_memory
EOF

# 3. Create the skill logic
cat > skill.py << 'EOF'
def run(inputs, tools, state):
    result = tools["llm_call"](
        system="Your system prompt here",
        prompt=inputs["query"]
    )
    return {"result": result}
EOF

# 4. Test locally
python -c "
from skill_registry import SkillRegistry
from skill_executor import SkillExecutor
registry = SkillRegistry('./skills')
print(registry.describe_for_llm())
"

# 5. Run the skill
python -c "
from openclaw import run_skill
result = run_skill('my_new_skill', {'query': 'test input'})
print(result)
"
```

---

## Summary: OpenClaw Skill Design Principles

| Principle | Implementation |
|---|---|
| **Skills are self-contained** | `.cfs` + `.py` — everything the skill needs is in its directory |
| **Manifests define contracts** | Inputs, outputs, permissions, tools — explicit, not implicit |
| **Randomness is pre-computed** | Rune draws happen before the LLM call — LLM only interprets |
| **Permission is gated** | Every sensitive operation requires a declared permission level |
| **Tools are sandboxed** | Each skill gets only the tools it declared — no scope creep |
| **State access is declared** | Skills declare what they read/write — prevents hidden state mutation |
| **Chaining is first-class** | Skills can request follow-up skills — coordinator pattern at skill level |
| **RULES.AI.md enforces ethics** | Every skill that touches sensitive domains gets hard behavioral rules |
| **Entry point is always `run()`** | Consistent interface — registry can discover and invoke any skill uniformly |
