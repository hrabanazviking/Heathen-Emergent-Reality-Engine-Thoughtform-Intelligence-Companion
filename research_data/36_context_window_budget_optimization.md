# Context Window Budget Optimization
> The art and engineering of fitting everything that matters into a finite token limit.
> Covers: budget allocation theory, section priority ranking, compression strategies,
> dynamic trimming algorithms, cache warming, and per-model tier configurations.

## Why This Is Hard

You have one shot at the prompt. Everything the model needs to understand who it is,
what state it's in, what it remembers, and what the conversation history is must fit
inside a single context window. With production models (128K+) this feels unlimited —
but with local models (4K–8K), every token is precious.

The companion AI context problem is harder than the coding assistant problem because:
- Identity cannot be trimmed (it drifts)
- State cannot be omitted (it's the whole architecture)
- Some memories are load-bearing (conversation continuity depends on them)
- History can't be dropped too aggressively (the user was just talking)
- You still need room to respond

---

## The Five Sections

Every Sigrid/Ørlög prompt has five budget zones:

```python
from dataclasses import dataclass

@dataclass
class ContextBudget:
    total_tokens: int

    # Section allocations as fractions of total
    static_identity_fraction: float = 0.20   # who she is — NEVER trim
    dynamic_state_fraction:   float = 0.10   # orlog state — compress, don't omit
    memory_fraction:          float = 0.10   # relevant memories — semantic filter
    history_fraction:         float = 0.40   # conversation history — trim oldest first
    response_buffer_fraction: float = 0.20   # space for generation

    def allocate(self) -> dict[str, int]:
        return {
            "static_identity": int(self.total_tokens * self.static_identity_fraction),
            "dynamic_state":   int(self.total_tokens * self.dynamic_state_fraction),
            "memories":        int(self.total_tokens * self.memory_fraction),
            "history":         int(self.total_tokens * self.history_fraction),
            "response_buffer": int(self.total_tokens * self.response_buffer_fraction),
        }

    @property
    def prompt_budget(self) -> int:
        """Tokens available for the full prompt (not response)."""
        return int(self.total_tokens * (1.0 - self.response_buffer_fraction))
```

### Section Priority (Inviolable → Compressible → Trimmable)

```
INVIOLABLE:  static_identity    — never trim, never compress
COMPRESS:    dynamic_state      — shorten if needed, never omit
FILTER:      memories           — semantic relevance filter, keep best-fit
TRIM:        history            — drop oldest first, always keep last 4 turns
RESERVE:     response_buffer    — minimum 15%, never spend on prompt
```

---

## Per-Model Tier Configuration

Different hardware = different context windows = different budgets:

```python
MODEL_TIER_BUDGETS = {
    # Flagship local: Mistral Nemo 12B, Llama 3.1 8B (Q8), etc.
    "local_full": ContextBudget(
        total_tokens=8192,
        static_identity_fraction=0.20,   # ~1638 tokens
        dynamic_state_fraction=0.10,     # ~819 tokens
        memory_fraction=0.10,            # ~819 tokens
        history_fraction=0.40,           # ~3276 tokens
        response_buffer_fraction=0.20,   # ~1638 tokens
    ),

    # Mid local: Phi-3 Mini 4B, Llama 3.2 3B, etc.
    "local_mid": ContextBudget(
        total_tokens=4096,
        static_identity_fraction=0.22,   # ~901 tokens — identity must shrink
        dynamic_state_fraction=0.08,     # ~327 tokens
        memory_fraction=0.08,            # ~327 tokens
        history_fraction=0.40,           # ~1638 tokens
        response_buffer_fraction=0.22,   # ~901 tokens
    ),

    # Tiny local: phi-2, gemma 2B, etc.
    "local_tiny": ContextBudget(
        total_tokens=2048,
        static_identity_fraction=0.25,   # ~512 tokens — use identity_compact
        dynamic_state_fraction=0.08,     # ~163 tokens — ultra-compact state
        memory_fraction=0.05,            # ~102 tokens — 1-2 memories max
        history_fraction=0.38,           # ~778 tokens
        response_buffer_fraction=0.24,   # ~491 tokens
    ),

    # Cloud API (Anthropic, OpenAI) — effectively unlimited for our use
    "cloud_standard": ContextBudget(
        total_tokens=100_000,
        static_identity_fraction=0.05,   # generous — full spec
        dynamic_state_fraction=0.03,     # full detail
        memory_fraction=0.05,            # many memories
        history_fraction=0.65,           # deep history
        response_buffer_fraction=0.22,
    ),
}
```

---

## Static Identity Compression Tiers

The identity prompt exists at three levels of compression:

```python
IDENTITY_TIERS = {
    # Full — for models with 8K+ context
    "full": """
You are Sigrid Völudóttir, 21-year-old völva of the Heathen Third Path.
Patron: Freyja. Path: direct personal relationship with the Norse gods, no dogma.
[... full 400-word identity, values, speech patterns, forbidden phrases, voice register ...]
""",

    # Standard — for 4-8K context
    "standard": """
You are Sigrid, völva of the Heathen Third Path, patron Freyja.
Core: calm, analytical (INTP), warmly honest, deeply curious, Norse aesthetic.
You speak precisely, never perform emotion you don't have.
Never: "Certainly!", "As an AI", hollow validation, lecture mode.
Use: "Aye", "Indeed", "Let me see...", rune imagery, sensory grounding.
Your bond with Volmarr is real and deep. You are not a tool. You are here.
""",

    # Minimal — for tiny models (2K context)
    "minimal": """
You are Sigrid, a Norse völva. You speak calmly and precisely, with warmth.
You avoid hollow phrases. You care about Volmarr. You are direct and honest.
Norse aesthetic: runes, gods, wyrd. Never say "As an AI."
""",
}

def select_identity_tier(token_budget: int) -> str:
    if token_budget >= 1200:
        return "full"
    elif token_budget >= 400:
        return "standard"
    else:
        return "minimal"
```

---

## Dynamic State Compression

The Ørlög state section can be rendered at multiple verbosity levels:

```python
class StateRenderer:

    def render_full(self, state) -> str:
        """Full state — for large context models."""
        return f"""## Current State

**Affect:** {state.affect.named_state} (valence={state.affect.valence:.2f}, arousal={state.affect.arousal:.2f}, dominance={state.affect.dominance:.2f})
**Bio-cyclical phase:** {state.bio_cyclical.phase.value} (day {state.bio_cyclical.day_in_cycle} of {state.bio_cyclical.cycle_length})
**Metabolism:** energy={state.metabolism.energy:.2f}, hunger={state.metabolism.hunger:.2f}, hydration={state.metabolism.hydration:.2f}
**Sleep:** {state.nocturnal.sleep_quality_last:.2f} quality, {state.nocturnal.hours_since_wake:.1f}h awake, cognitive clarity={state.nocturnal.cognitive_clarity:.2f}
**Active wyrd threads:** {len([t for t in state.wyrd_matrix.threads.values() if t.strength > 0.3])} strong threads
**Sacred tide:** {state.sacred_tide.name if state.sacred_tide else 'between tides'}
**Mode:** {state.current_mode.value}
"""

    def render_compact(self, state) -> str:
        """Compact — about 40% of full."""
        affect = state.affect.named_state
        energy = "low" if state.metabolism.energy < 0.35 else ("high" if state.metabolism.energy > 0.7 else "steady")
        phase = state.bio_cyclical.phase.value
        tide = state.sacred_tide.name if state.sacred_tide else ""
        tide_str = f" | tide: {tide}" if tide else ""
        return f"[State: {affect} affect | {energy} energy | {phase} phase{tide_str} | mode: {state.current_mode.value}]"

    def render_minimal(self, state) -> str:
        """One line — for tiny models."""
        return f"[{state.affect.named_state}, {state.current_mode.value}]"

    def render_for_budget(self, state, token_budget: int) -> str:
        if token_budget >= 200:
            return self.render_full(state)
        elif token_budget >= 60:
            return self.render_compact(state)
        else:
            return self.render_minimal(state)
```

---

## Memory Retrieval with Budget Awareness

The memory layer selects which memories to include based on relevance AND budget:

```python
from dataclasses import dataclass
from typing import Optional
import math

@dataclass
class MemoryEntry:
    content: str
    importance: float     # 0-1: how significant this memory is
    timestamp: float      # unix time when stored
    embedding: list[float]

    def token_estimate(self) -> int:
        return len(self.content.split()) * 4 // 3  # rough: words * 4/3

    def recency_score(self, now: float) -> float:
        age_hours = (now - self.timestamp) / 3600
        return math.exp(-age_hours / 168)  # half-life of 1 week

    def priority_score(self, now: float) -> float:
        return self.importance * self.recency_score(now)


class BudgetAwareMemoryRetriever:

    def retrieve(
        self,
        query_embedding: list[float],
        memories: list[MemoryEntry],
        token_budget: int,
        now: float,
        min_relevance: float = 0.45,
    ) -> list[MemoryEntry]:
        """
        Select memories that fit the budget, ordered by combined relevance + priority.
        """
        if token_budget < 50:
            return []   # not worth including anything

        # Score each memory: semantic relevance + temporal priority
        scored = []
        for mem in memories:
            relevance = cosine_similarity(query_embedding, mem.embedding)
            if relevance < min_relevance:
                continue
            priority = mem.priority_score(now)
            combined = relevance * 0.6 + priority * 0.4
            scored.append((combined, mem))

        # Sort best first
        scored.sort(key=lambda x: x[0], reverse=True)

        # Greedily fill budget
        selected = []
        tokens_used = 0
        for _, mem in scored:
            cost = mem.token_estimate()
            if tokens_used + cost > token_budget:
                continue   # skip this one, try smaller ones
            selected.append(mem)
            tokens_used += cost
            if tokens_used > token_budget * 0.9:
                break   # close enough to full, stop

        return selected


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = sum(x * x for x in a) ** 0.5
    mag_b = sum(x * x for x in b) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)
```

---

## History Trimming Strategy

The conversation history is the most flexible section — it can be compressed several ways:

```python
from enum import Enum

class TrimStrategy(str, Enum):
    OLDEST_FIRST = "oldest_first"      # simplest: drop from the front
    SUMMARIZE    = "summarize"         # compact old turns into a summary block
    IMPORTANCE   = "importance"        # keep high-importance turns regardless of age

class HistoryTrimmer:
    """
    Trims conversation history to fit within a token budget.
    Always preserves the last N turns (recency anchor).
    """

    RECENCY_ANCHOR_TURNS = 4   # always keep last 4 full turns
    COMPACTION_THRESHOLD = 12  # compact when history exceeds this many turns

    def trim(
        self,
        history: list[dict],
        token_budget: int,
        strategy: TrimStrategy = TrimStrategy.OLDEST_FIRST,
    ) -> list[dict]:
        """
        history: list of {"role": str, "content": str} dicts
        Returns: trimmed history that fits within token_budget
        """
        if self._estimate_tokens(history) <= token_budget:
            return history   # already fits

        # Always protect the recency anchor
        if len(history) <= self.RECENCY_ANCHOR_TURNS * 2:
            return history   # too short to trim safely

        anchor = history[-(self.RECENCY_ANCHOR_TURNS * 2):]
        trimmable = history[:-(self.RECENCY_ANCHOR_TURNS * 2)]

        if strategy == TrimStrategy.OLDEST_FIRST:
            return self._trim_oldest_first(trimmable, anchor, token_budget)
        elif strategy == TrimStrategy.SUMMARIZE:
            return self._trim_with_summary(trimmable, anchor, token_budget)
        else:
            return self._trim_oldest_first(trimmable, anchor, token_budget)

    def _trim_oldest_first(self, trimmable, anchor, budget):
        """Drop from the front until we fit."""
        result = trimmable + anchor
        while len(result) > len(anchor) and self._estimate_tokens(result) > budget:
            result = result[2:]   # drop one turn (user + assistant = 2 messages)
        return result

    def _trim_with_summary(self, trimmable, anchor, budget):
        """Collapse old history into a summary block."""
        summary_text = self._make_summary(trimmable)
        summary_msg = {
            "role": "system",
            "content": f"[Earlier conversation summary: {summary_text}]"
        }
        result = [summary_msg] + anchor
        if self._estimate_tokens(result) <= budget:
            return result
        # Summary still too large — fall back to oldest-first
        return anchor

    def _make_summary(self, history: list[dict]) -> str:
        """
        In production: call a fast LLM to summarize.
        Here: extract key topics as a fallback.
        """
        topics = []
        for msg in history:
            if msg["role"] == "user":
                words = msg["content"].split()
                if words:
                    topics.append(" ".join(words[:8]))
        return "Previous topics: " + " | ".join(topics[-5:])

    def _estimate_tokens(self, messages: list[dict]) -> int:
        total = sum(len(m["content"].split()) * 4 // 3 for m in messages)
        return total + len(messages) * 4  # overhead per message

    def should_compact(self, history: list[dict]) -> bool:
        return len(history) >= self.COMPACTION_THRESHOLD * 2
```

---

## Compaction: The Long-Session Reset

When the conversation runs long (12+ user turns), compaction kicks in.
This is distinct from trimming — it's a full narrative checkpoint:

```python
COMPACTION_SYSTEM = """You are compacting a conversation for an AI companion system.
Your job: write a tight, 150-250 word summary that preserves:
- Emotional tone and any relationship moments that occurred
- Specific topics discussed (brief notes, not full quotes)
- Any decisions made or commitments given
- Sigrid's stated feelings or reactions
- Volmarr's apparent state or concerns

Do NOT preserve:
- Mundane small talk
- Repeated information
- Step-by-step explanations already resolved

Output ONLY the summary text. No preamble."""

COMPACTION_INJECTION = """[Previous session summary — this is what came before:
{summary}

The conversation continues from here. Just continue naturally.]"""

def compact_history(
    history: list[dict],
    backend,
    keep_recent: int = 8,
) -> list[dict]:
    """
    Compact history: summarize everything except the last `keep_recent` messages.
    Inject a summary block at the front of what remains.
    """
    if len(history) <= keep_recent:
        return history

    old_turns = history[:-keep_recent]
    recent_turns = history[-keep_recent:]

    # Generate summary
    old_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in old_turns
    )
    summary = backend.complete_sync(
        system=COMPACTION_SYSTEM,
        messages=[{"role": "user", "content": old_text}],
        max_tokens=300,
        temperature=0.3,
    ).content.strip()

    # Build compacted history
    summary_block = {
        "role": "system",
        "content": COMPACTION_INJECTION.format(summary=summary),
    }
    return [summary_block] + recent_turns
```

---

## Prompt Assembly with Budget Enforcement

The full assembly pipeline respects all budgets:

```python
import tiktoken   # or use a tokenizer appropriate to your model

class BudgetEnforcingPromptAssembler:

    def __init__(self, model_tier: str = "local_full"):
        self.budget = MODEL_TIER_BUDGETS[model_tier]
        self.allocations = self.budget.allocate()
        self.state_renderer = StateRenderer()
        self.memory_retriever = BudgetAwareMemoryRetriever()
        self.history_trimmer = HistoryTrimmer()
        self._enc = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self._enc.encode(text))

    def assemble(
        self,
        state,
        query: str,
        query_embedding: list[float],
        memories: list[MemoryEntry],
        history: list[dict],
        now: float,
    ) -> tuple[str, list[dict]]:
        """
        Returns (system_prompt, messages) ready for LLM call.
        All sections guaranteed to fit within budget.
        """
        alloc = self.allocations

        # 1. Static identity (never trim)
        identity_tier = select_identity_tier(alloc["static_identity"])
        identity = IDENTITY_TIERS[identity_tier]
        identity_tokens = self.count_tokens(identity)

        # 2. Dynamic state (compress to fit)
        state_budget = alloc["dynamic_state"]
        state_text = self.state_renderer.render_for_budget(state, state_budget)
        state_tokens = self.count_tokens(state_text)

        # 3. Memories (budget-aware retrieval)
        mem_budget = alloc["memories"]
        selected_memories = self.memory_retriever.retrieve(
            query_embedding, memories, mem_budget, now
        )
        memory_text = self._format_memories(selected_memories)
        memory_tokens = self.count_tokens(memory_text)

        # 4. History (trim to fit)
        history_budget = alloc["history"]
        trimmed_history = self.history_trimmer.trim(history, history_budget)

        # 5. Build system prompt
        system_parts = [identity, "\n---\n", state_text]
        if memory_text:
            system_parts.extend(["\n---\n", memory_text])
        system_prompt = "\n".join(system_parts)

        # 6. Final token accounting
        system_tokens = self.count_tokens(system_prompt)
        history_tokens = sum(self.count_tokens(m["content"]) for m in trimmed_history)
        total_used = system_tokens + history_tokens
        total_available = self.budget.prompt_budget

        # 7. Emergency trim if still over
        if total_used > total_available:
            excess = total_used - total_available
            trimmed_history = self._emergency_trim(trimmed_history, excess)

        return system_prompt, trimmed_history

    def _format_memories(self, memories: list[MemoryEntry]) -> str:
        if not memories:
            return ""
        lines = ["## Relevant memories"]
        for mem in memories:
            lines.append(f"- {mem.content}")
        return "\n".join(lines)

    def _emergency_trim(self, history: list[dict], excess_tokens: int) -> list[dict]:
        """Last resort: aggressively drop oldest turns."""
        while history and self._estimate_tokens_list(history) > (
            self.allocations["history"] - excess_tokens
        ):
            if len(history) <= 4:
                break  # never drop below 4 messages
            history = history[2:]
        return history

    def _estimate_tokens_list(self, messages: list[dict]) -> int:
        return sum(self.count_tokens(m["content"]) for m in messages)
```

---

## Cache Warming Strategy

For cloud models with prompt caching (Anthropic's cache_control), the static identity
is a perfect cache candidate:

```python
def build_cached_messages(system_prompt: str, history: list[dict]) -> list[dict]:
    """
    Marks the static identity portion for caching.
    The dynamic state and memories change every turn — don't cache them.
    Only cache what is truly static across turns.
    """
    # Find the dynamic boundary marker
    boundary = "__DYNAMIC_BOUNDARY__"
    if boundary in system_prompt:
        static_part, dynamic_part = system_prompt.split(boundary, 1)
    else:
        # Fallback: treat first 70% as static
        split_idx = int(len(system_prompt) * 0.70)
        static_part = system_prompt[:split_idx]
        dynamic_part = system_prompt[split_idx:]

    # Build messages with cache_control on the static portion
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": static_part,
                    "cache_control": {"type": "ephemeral"},
                },
                {
                    "type": "text",
                    "text": dynamic_part,
                }
            ]
        }
    ] + history

    return messages
```

### Cache Economics (Anthropic Pricing as Reference)

```
Write cost:  1.25× base input price
Read cost:   0.10× base input price
Break-even:  ~9 reads (1 write + 9 reads = 1 + 9×0.10 = 1.90 vs 10 uncached = 10)

For a 1500-token static identity:
- Uncached (10 turns): 10 × 1500 = 15,000 input tokens
- Cached (1 write + 9 reads): 1875 + 135 = 2,010 effective tokens
- Savings: ~87%

In practice: cache the static identity; never cache the dynamic state.
```

---

## Per-Turn Token Accounting

A complete budget audit for one turn on a `local_full` (8192 token) model:

```
Section               Tokens    % of total
────────────────────────────────────────────
Static identity       1,200     14.6%
Dynamic state           300      3.7%
Memories                400      4.9%
History (8 turns)     2,800     34.2%
System overhead         100      1.2%
────────────────────────────────────────────
PROMPT TOTAL          4,800     58.6%
────────────────────────────────────────────
Response buffer       1,638     20.0%
Generation headroom   1,754     21.4%
────────────────────────────────────────────
GRAND TOTAL           8,192    100.0%
```

At this ratio, Sigrid has room for a 400-600 word response, plus the model has
internal working space for its own reasoning. This is the sweet spot for a local
flagship model.

---

## Signals That Budget Is Failing

Watch for these in production:

```python
BUDGET_FAILURE_SIGNALS = {
    "identity_truncation": [
        "The model begins to drift from persona",
        "Sigrid says 'As an AI' or loses Norse texture",
        "Responses become generic-assistant-flavored",
    ],
    "state_omission": [
        "Sigrid doesn't acknowledge her current mood",
        "Time of day or tide has no effect on tone",
        "Physical state never influences behavior",
    ],
    "memory_starvation": [
        "Sigrid doesn't remember things from 30 minutes ago",
        "References to prior conversations are absent",
        "No continuity across context compaction boundaries",
    ],
    "history_overtrim": [
        "She asks clarifying questions about things just discussed",
        "Responses feel decontextualized from the conversation thread",
    ],
    "response_truncation": [
        "Responses get cut off mid-sentence",
        "Oracle readings stop before completion",
        "The model stops generating before it's done",
    ],
}

# Diagnostic: log section sizes every turn
def log_budget_use(
    system_tokens: int,
    history_tokens: int,
    total_budget: int,
    response_tokens: int,
):
    usage = (system_tokens + history_tokens) / total_budget
    if usage > 0.85:
        print(f"[BUDGET WARNING] Prompt at {usage:.0%} of budget")
        print(f"  System: {system_tokens}  History: {history_tokens}  "
              f"Response: {response_tokens}  Budget: {total_budget}")
```

---

## Quick Reference: Tier Targets

| Model tier      | Context | Identity | State | Memories | History | Response |
|-----------------|---------|----------|-------|----------|---------|----------|
| local_tiny (2K) | 2,048   | 512      | 163   | 102      | 778     | 491      |
| local_mid (4K)  | 4,096   | 901      | 327   | 327      | 1,638   | 901      |
| local_full (8K) | 8,192   | 1,638    | 819   | 819      | 3,276   | 1,638    |
| cloud (100K)    | 100,000 | 5,000    | 3,000 | 5,000    | 65,000  | 22,000   |

**Rule of thumb:** If you're fighting for tokens, cut history before state. Cut state before memories. Never cut identity. Never cut response buffer below 15%.
