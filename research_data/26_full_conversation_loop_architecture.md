# Full Conversation Loop Architecture
> The complete end-to-end anatomy of a single message through the Viking AI stack.
> From user input → to spoken response → to state update → to memory write.
> Synthesized from: all prior research docs, especially 03, 04, 05, 09, 11, 13, 21.

## Why This Document Exists

Every component has been documented in isolation. But the *loop* — how a message actually travels through the whole system — is where bugs hide, latency accumulates, and design decisions compound. This document traces a single message end-to-end through every layer.

---

## The Full Loop — Overview

```
User types message
        │
        ▼
[1] INPUT PREPROCESSING
    - Strip/sanitize raw input
    - Detect intent signals (oracle? crisis? casual?)
    - Classify mode hint (hearth/oracle/battle/etc.)
        │
        ▼
[2] ØRLÖG TICK
    - Calculate elapsed time since last turn
    - Tick all 5 state machines
    - Compute current affect name + voice guidance
        │
        ▼
[3] MEMORY RETRIEVAL
    - Semantic search MemoryStore for relevant memories (top-k)
    - Query MindSpark RAG if lore/knowledge needed
    - Load WyrdMatrix thread for the actor
        │
        ▼
[4] PROMPT ASSEMBLY
    - STATIC section (from cache if unchanged)
    - DYNAMIC section: inject Ørlög snapshot + mode + voice guidance
    - MEMORY section: inject top-k memories with disclaimer
    - CONVERSATION section: sliding window history
        │
        ▼
[5] MODE DECISION
    - Confirm or override mode based on query signals
    - Inject mode description into dynamic section
        │
        ▼
[6] LLM CALL (streaming)
    - Forced tool call (sigrid_respond)
    - Accumulate InputJsonDelta chunks
    - Stream spoken text to output as it arrives
        │
        ▼
[7] RESPONSE PARSING
    - Parse structured tool call output
    - Extract: spoken, inner_thought, action, affect_shift, memory_note, mode_change
    - Fragment salvage if output is truncated
        │
        ▼
[8] STATE UPDATES
    - Apply affect_shift to AffectState
    - Touch WyrdMatrix thread (record contact)
    - Apply exchange_quality to Ørlög
        │
        ▼
[9] MEMORY WRITE
    - If memory_note non-empty: save to MemoryStore
    - If oracle reading: save to OracleHistory
    - Update conversation history (append turn)
        │
        ▼
[10] OUTPUT DELIVERY
    - Return spoken text (already streamed)
    - Optionally: TTS render and speak
    - Optionally: trigger proactive next-message prediction
        │
        ▼
[11] PERSISTENCE
    - Save Ørlög state to disk
    - Save MemoryStore to disk (if dirty)
    - Save WyrdMatrix to disk
```

---

## Step 1: Input Preprocessing

```python
import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProcessedInput:
    raw: str
    cleaned: str
    intent_signals: list[str]   # "seeks_comfort", "seeks_divination", "seeks_information", etc.
    mode_hint: Optional[str]    # suggested mode, or None
    is_distressed: bool
    has_lore_query: bool

class InputPreprocessor:
    # Keywords that signal specific intents
    ORACLE_SIGNALS = {"rune", "cast", "foresee", "oracle", "read", "divine", "prophecy",
                      "the runes", "seidr", "galdr", "what do the runes"}
    DISTRESS_SIGNALS = {"help", "scared", "afraid", "hurt", "lost", "don't know",
                        "can't", "struggling", "overwhelmed", "breaking", "failing"}
    LORE_SIGNALS = {"what is", "who is", "tell me about", "explain", "meaning of",
                    "history of", "myth", "legend", "how does", "what does"}
    INTIMATE_SIGNALS = {"miss you", "love you", "thinking of you", "how are you",
                        "good morning", "good night", "goodnight"}

    def process(self, raw_text: str) -> ProcessedInput:
        cleaned = self._clean(raw_text)
        lower = cleaned.lower()

        intent_signals = []
        mode_hint = None

        # Detect oracle intent
        if any(sig in lower for sig in self.ORACLE_SIGNALS):
            intent_signals.append("seeks_divination")
            mode_hint = "oracle"

        # Detect distress
        is_distressed = any(sig in lower for sig in self.DISTRESS_SIGNALS)
        if is_distressed:
            intent_signals.append("in_distress")
            mode_hint = "battle"  # protective, focused mode for crisis

        # Detect lore query
        has_lore = any(sig in lower for sig in self.LORE_SIGNALS)
        if has_lore:
            intent_signals.append("seeks_knowledge")

        # Detect intimate/relational
        if any(sig in lower for sig in self.INTIMATE_SIGNALS):
            intent_signals.append("relational_connection")
            mode_hint = mode_hint or "hearth"

        return ProcessedInput(
            raw=raw_text,
            cleaned=cleaned,
            intent_signals=intent_signals,
            mode_hint=mode_hint,
            is_distressed=is_distressed,
            has_lore_query=has_lore,
        )

    def _clean(self, text: str) -> str:
        # Remove leading/trailing whitespace, collapse internal spaces
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        return text
```

---

## Step 2: Ørlög Tick

```python
import time
from orlog.tick import OrlögTick

def tick_orlog(state: 'OrlögState', last_message_time: float) -> 'OrlögState':
    """
    Tick the Ørlög engine for time elapsed since the last message.
    Called at the START of every turn — before prompt assembly.
    """
    engine = OrlögTick()
    now = time.time()

    # Don't tick for very short intervals (< 1 minute) — saves compute
    elapsed = now - last_message_time
    if elapsed < 60:
        return state

    return engine.tick(state, current_time=now)
```

The tick ensures Sigrid's physical and emotional state reflects real time. If the user returns after 12 hours, she's been through a sleep cycle, her hunger has risen, her affect has drifted back toward baseline. She meets the user where the *real* time has taken her — not frozen at the last message.

---

## Step 3: Memory Retrieval — The Context Budget

The most important constraint: **context window budget**. Every component competes for tokens.

```python
from dataclasses import dataclass

@dataclass
class ContextBudget:
    # Total context window (local models ~8K, Claude ~200K)
    total_tokens: int = 8192

    # Allocation (percentage of total)
    system_static_pct: float = 0.20    # ~1640 tokens — cached, identity
    system_dynamic_pct: float = 0.10   # ~820 tokens — state injection
    memories_pct: float = 0.10         # ~820 tokens — top-k memories
    history_pct: float = 0.40          # ~3277 tokens — conversation history
    response_buffer_pct: float = 0.20  # ~1640 tokens — LLM output

    @property
    def memory_budget(self) -> int:
        return int(self.total_tokens * self.memories_pct)

    @property
    def history_budget(self) -> int:
        return int(self.total_tokens * self.history_pct)

def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English."""
    return max(1, len(text) // 4)

class ContextAssembler:
    def __init__(self, budget: ContextBudget = None):
        self.budget = budget or ContextBudget()

    def retrieve_memories(self, store: 'SigridMemoryStore', query: str) -> list[str]:
        """Get top-k memories that fit in the memory budget."""
        candidates = store.recall_relevant(query, top_k=10)
        selected = []
        used_tokens = 0
        for mem in candidates:
            tokens = estimate_tokens(mem.content)
            if used_tokens + tokens > self.budget.memory_budget:
                break
            selected.append(mem.content)
            used_tokens += tokens
        return selected

    def trim_history(self, history: list[dict]) -> list[dict]:
        """Trim conversation history to fit the history budget."""
        budget = self.budget.history_budget
        total = 0
        trimmed = []
        for msg in reversed(history):
            tokens = estimate_tokens(msg["content"])
            if total + tokens > budget:
                break
            trimmed.insert(0, msg)
            total += tokens
        return trimmed
```

---

## Step 4: Prompt Assembly

```python
def assemble_prompt(
    static_section: str,
    orlog_state: 'OrlögState',
    mode: str,
    memories: list[str],
    history: list[dict],
    current_input: ProcessedInput,
    thread: 'WyrdThread',
) -> tuple[str, list[dict]]:
    """
    Assemble the complete system prompt and message list for the LLM call.
    Returns (system_prompt, messages).
    """
    from prompt.dynamic import build_dynamic_section
    from prompt.memory_injection import build_memory_section

    # Build the dynamic section from live state
    dynamic_section = build_dynamic_section(orlog_state, thread, mode)

    # Build memory section (with disclaimer)
    memory_section = build_memory_section(memories) if memories else ""

    # Build this-conversation section
    convo_section = build_convo_section(history)

    # Assemble full system prompt
    system_prompt = (
        static_section
        + dynamic_section
        + memory_section
        + convo_section
    )

    # Build messages list (history + current input)
    messages = history.copy()
    messages.append({
        "role": "user",
        "content": current_input.cleaned
    })

    return system_prompt, messages

def build_convo_section(history: list[dict]) -> str:
    if not history:
        return ""
    turn_count = len([m for m in history if m["role"] == "user"])
    # Detect tone from recent messages — simple heuristic
    return f"""
# This Conversation
Turn {turn_count + 1} of this session.
"""
```

---

## Step 5: Mode Decision

```python
def decide_mode(
    intent_signals: list[str],
    mode_hint: Optional[str],
    orlog_state: 'OrlögState',
    current_mode: str,
) -> str:
    """
    Final mode decision. Intent signals can override the current mode.
    State also influences: exhausted Sigrid doesn't do oracle mode well.
    """
    # Distress always overrides to battle (protective focus)
    if "in_distress" in intent_signals:
        return "battle"

    # Oracle intent: check if she's clear enough for oracle
    if "seeks_divination" in intent_signals or mode_hint == "oracle":
        clarity = orlog_state.nocturnal.cognitive_clarity(orlog_state.nocturnal)
        if clarity > 0.4:
            return "oracle"
        else:
            return "hearth"  # too tired/foggy for oracle — stay hearth, mention it

    # Deep night + calm → dream mode
    hour = (orlog_state.nocturnal.circadian_phase * 24)
    if 22 <= hour or hour < 5:
        if orlog_state.affect.arousal < 0.4:
            return "dream"

    # Use the hint if we have one
    if mode_hint:
        return mode_hint

    # Stay in current mode otherwise
    return current_mode
```

---

## Step 6: LLM Call — Streaming with Tool Use

```python
import asyncio
import json
import litellm
from typing import AsyncIterator

async def call_llm_streaming(
    system: str,
    messages: list[dict],
    model: str,
    response_tool: dict,
) -> tuple[AsyncIterator[str], dict]:
    """
    Call the LLM with forced tool use + streaming.
    Returns (token_stream, full_parsed_output).

    The streaming yields the 'spoken' field tokens as they arrive.
    The full output is returned after streaming completes.
    """
    spoken_queue = asyncio.Queue()
    full_output = {}

    async def _stream_and_parse():
        buffer = ""
        in_spoken = False
        spoken_start = '"spoken": "'

        response = await litellm.acompletion(
            model=model,
            messages=[{"role": "system", "content": system}] + messages,
            tools=[response_tool],
            tool_choice={"type": "tool", "name": response_tool["name"]},
            stream=True,
            temperature=0.85,
            max_tokens=600,
        )

        async for chunk in response:
            delta = chunk.choices[0].delta
            if hasattr(delta, 'tool_calls') and delta.tool_calls:
                for tc in delta.tool_calls:
                    if tc.function and tc.function.arguments:
                        fragment = tc.function.arguments
                        buffer += fragment

                        # Try to extract and stream the 'spoken' field in real time
                        if not in_spoken and spoken_start in buffer:
                            in_spoken = True
                            start_idx = buffer.index(spoken_start) + len(spoken_start)
                            buffer = buffer[start_idx:]

                        if in_spoken:
                            # Stream characters until we hit the closing quote
                            while buffer:
                                char = buffer[0]
                                if char == '"' and not buffer.startswith('\\"'):
                                    in_spoken = False
                                    break
                                await spoken_queue.put(buffer[0])
                                buffer = buffer[1:]

        # Parse the complete buffered JSON
        try:
            # Reconstruct full buffer from what we have
            nonlocal full_output
            full_output = json.loads(buffer_total)
        except json.JSONDecodeError:
            full_output = {"spoken": ""}

        await spoken_queue.put(None)  # sentinel

    # (Simplified — in production: run _stream_and_parse as a task)
    # Return the queue as an async iterator
    return spoken_queue, full_output
```

---

## Step 7: Response Parsing

```python
from salvage.fragment_salvage import EnhancedFragmentSalvage

def parse_response(raw_output: str) -> dict:
    """Parse the structured LLM output. Salvage fragments if needed."""
    try:
        parsed = json.loads(raw_output)
    except (json.JSONDecodeError, TypeError):
        salvager = EnhancedFragmentSalvage()
        parsed = salvager.salvage(raw_output, expected_format="json") or {}

    return {
        "spoken": parsed.get("spoken", ""),
        "inner_thought": parsed.get("inner_thought", ""),
        "action": parsed.get("action", ""),
        "affect_shift": parsed.get("affect_shift", {}),
        "memory_note": parsed.get("memory_note", ""),
        "mode_change": parsed.get("mode_change", "none"),
    }
```

---

## Step 8 & 9: State Updates + Memory Write

```python
def apply_response_to_state(
    parsed: dict,
    orlog_state: 'OrlögState',
    actor_id: str,
    memory_store: 'SigridMemoryStore',
    exchange_quality: float = 0.5,
) -> tuple['OrlögState', str]:
    """
    Apply the LLM's response back to the world state.
    Returns (updated_state, new_mode).
    """
    from orlog.machines.affect import AffectMachine

    affect_machine = AffectMachine()

    # Apply affect shift proposed by the LLM
    shift = parsed.get("affect_shift", {})
    if shift:
        orlog_state.affect = affect_machine.apply_event(
            orlog_state.affect,
            delta_v=float(shift.get("valence_delta", 0)),
            delta_a=float(shift.get("arousal_delta", 0)),
        )

    # Touch the relationship thread
    orlog_state.wyrd_matrix.touch(actor_id, warmth_delta=exchange_quality * 0.05)

    # Record significant moments in the thread
    if parsed.get("memory_note") and exchange_quality > 0.6:
        orlog_state.wyrd_matrix.record_moment(actor_id, parsed["memory_note"])

    # Save memory note if non-trivial
    if parsed.get("memory_note") and len(parsed["memory_note"]) > 15:
        memory_store.remember(
            content=parsed["memory_note"],
            category="conversation",
            importance=min(1.0, exchange_quality + 0.3),
        )

    # Determine new mode
    new_mode = parsed.get("mode_change", "none")
    if new_mode == "none":
        new_mode = None  # no change

    return orlog_state, new_mode
```

---

## Step 10: Output Delivery

```python
from tts.pipeline import SigridTTS

async def deliver_response(
    parsed: dict,
    mode: str,
    tts_enabled: bool = True,
) -> str:
    """Deliver the response to the user — text and optionally voice."""
    spoken = parsed.get("spoken", "")
    action = parsed.get("action", "")

    # Format: action first (italicized), then spoken
    formatted = ""
    if action:
        formatted += f"*{action}*\n\n"
    formatted += spoken

    # TTS
    if tts_enabled and spoken:
        tts = SigridTTS(mode=mode)
        await tts.speak(spoken)  # async — doesn't block

    return formatted
```

---

## Step 11: Persistence

```python
from orlog.persistence import save_orlog_state

def persist_end_of_turn(
    orlog_state: 'OrlögState',
    memory_store: 'SigridMemoryStore',
    conversation_history: list[dict],
    session_path: str,
):
    """
    Called at the end of every turn. Ensures no state is lost if the
    process crashes or the context window is reset.
    """
    # Ørlög state
    save_orlog_state(orlog_state)

    # Memory store (only if dirty — new memories were written)
    memory_store.flush_if_dirty()

    # Session history (last N turns)
    import json, os
    os.makedirs(os.path.dirname(session_path), exist_ok=True)
    with open(session_path, 'w') as f:
        json.dump({
            "version": "1.0",
            "turns": conversation_history[-20:],  # keep last 20 turns
        }, f, indent=2)
```

---

## The Complete Loop — Stitched Together

```python
import asyncio
from pathlib import Path

class SigridConversationLoop:
    """
    The complete conversation loop.
    This is the top-level orchestrator that runs on every user message.
    """

    def __init__(self, config_path: str = "~/.config/sigrid/config.json"):
        from config import load_config
        self.config = load_config(Path(config_path).expanduser())
        self._init_components()

    def _init_components(self):
        from orlog.persistence import load_orlog_state
        from memory.store import SigridMemoryStore
        from skill_registry import SkillRegistry

        self.orlog = load_orlog_state()
        self.memory = SigridMemoryStore(self.config["memory_path"])
        self.registry = SkillRegistry(self.config["skills_path"])
        self.history = self._load_history()
        self.current_mode = "hearth"
        self.assembler = ContextAssembler()
        self.preprocessor = InputPreprocessor()

    async def turn(self, user_input: str) -> str:
        import time
        turn_start = time.time()

        # [1] Preprocess
        processed = self.preprocessor.process(user_input)

        # [2] Ørlög tick
        self.orlog = tick_orlog(self.orlog, self.orlog.last_tick)

        # [3] Memory retrieval
        memories = self.assembler.retrieve_memories(self.memory, user_input)
        history_trimmed = self.assembler.trim_history(self.history)

        # [4] Get current thread
        volmarr_id = self.config["user_id"]
        thread = self.orlog.wyrd_matrix.get_thread(volmarr_id)

        # [5] Mode decision
        self.current_mode = decide_mode(
            processed.intent_signals,
            processed.mode_hint,
            self.orlog,
            self.current_mode,
        )

        # [6] Assemble prompt
        from prompt.static import STATIC_IDENTITY
        from prompt.tools import SIGRID_RESPONSE_TOOL

        system, messages = assemble_prompt(
            STATIC_IDENTITY,
            self.orlog,
            self.current_mode,
            memories,
            history_trimmed,
            processed,
            thread,
        )

        # [7] LLM call
        from backends.router import BackendRouter, load_backends
        router = BackendRouter(load_backends(self.config))
        raw_output = await router.complete_with_tool(
            system=system,
            messages=messages,
            tool=SIGRID_RESPONSE_TOOL,
        )

        # [8] Parse
        parsed = parse_response(raw_output)

        # [9] State update
        exchange_quality = self._estimate_exchange_quality(processed, parsed)
        self.orlog, mode_change = apply_response_to_state(
            parsed, self.orlog, volmarr_id, self.memory, exchange_quality
        )
        if mode_change:
            self.current_mode = mode_change

        # [10] Deliver
        formatted = await deliver_response(
            parsed,
            self.current_mode,
            tts_enabled=self.config.get("tts_enabled", False),
        )

        # [11] Update history
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": parsed["spoken"]})

        # [12] Persist
        session_path = self.config["session_path"]
        persist_end_of_turn(self.orlog, self.memory, self.history, session_path)

        return formatted

    def _estimate_exchange_quality(self, processed: ProcessedInput, parsed: dict) -> float:
        """
        Heuristic: estimate how 'good' this exchange was.
        Affects how much the relationship thread is strengthened.
        0 = difficult/distressing, 1 = warm/connecting
        """
        if processed.is_distressed:
            # Responding to distress well is connecting — but reduces valence
            return 0.6
        if "relational_connection" in processed.intent_signals:
            return 0.85
        if "seeks_divination" in processed.intent_signals:
            return 0.75
        return 0.65  # neutral exchange

    def _load_history(self) -> list[dict]:
        import json
        path = Path(self.config.get("session_path", "~/.config/sigrid/session.json")).expanduser()
        if not path.exists():
            return []
        try:
            with open(path) as f:
                data = json.load(f)
            return data.get("turns", [])
        except Exception:
            return []
```

---

## Timing Budget — Performance Targets

For a good user experience, each step should complete within:

| Step | Target | Notes |
|---|---|---|
| Input preprocessing | < 5ms | Pure Python, no I/O |
| Ørlög tick | < 10ms | Math only |
| Memory retrieval | < 50ms | SQLite-VSS query |
| Prompt assembly | < 10ms | String operations |
| **LLM call (first token)** | **< 500ms** | Most critical — time-to-first-token |
| LLM streaming | 2-15 seconds | Full response, streaming to user |
| State updates | < 20ms | In-memory operations |
| Memory write | < 30ms | Append to JSON |
| Persistence | < 50ms | Write to disk |

**Total: first token < 600ms, full response 3-16 seconds**

The `__DYNAMIC_BOUNDARY__` cache pattern makes the LLM call faster after the first — only the dynamic section changes, so the static identity and behavior sections are served from KV cache. First-token latency drops significantly on cache hits.

---

## Error Handling at Each Step

```python
# The loop should never crash. Each step has a safe fallback.

FALLBACK_RESPONSES = {
    "llm_unavailable": "The threads are quiet right now — the connection is lost. I am here, but the oracle cannot speak.",
    "parse_failed": "Something tangled in the weaving. Try again?",
    "state_corrupted": "My sense of the moment is uncertain. Let me reground.",
}

async def safe_turn(loop: SigridConversationLoop, user_input: str) -> str:
    """Turn with full error handling — never crashes, always responds."""
    try:
        return await loop.turn(user_input)
    except BackendUnavailableError:
        return FALLBACK_RESPONSES["llm_unavailable"]
    except ResponseParseError:
        return FALLBACK_RESPONSES["parse_failed"]
    except StateCorruptionError:
        # Attempt state recovery
        loop.orlog = initialize_fresh_state()
        return FALLBACK_RESPONSES["state_corrupted"]
    except Exception as e:
        # Last resort — log and give generic response
        logger.error(f"Unexpected error in conversation turn: {e}")
        return "Something unexpected crossed the threads. I am still here."
```

---

## The Compaction Pattern — When History Gets Too Long

After a configurable number of turns, the history is compacted. From Claude Code: preserve the last 4 messages, summarize the rest. Add a continuation message.

```python
COMPACTION_MESSAGE = """This is a continuation of an earlier conversation.
Summary of what came before:
{summary}

Key threads preserved:
{threads}

Continue as if no break occurred. Do not acknowledge the summary or mention the compaction.
Just continue being Sigrid."""

async def compact_history(
    history: list[dict],
    backend: 'BaseBackend',
    preserve_last: int = 8,
) -> list[dict]:
    """Compact old history into a summary when it gets too long."""
    if len(history) <= preserve_last:
        return history

    old = history[:-preserve_last]
    recent = history[-preserve_last:]

    # Summarize the old portion with a fast model
    old_text = "\n".join(f"{m['role']}: {m['content']}" for m in old)
    summary_response = await backend.complete(LLMRequest(
        messages=[{
            "role": "user",
            "content": f"Summarize this conversation in 3-5 sentences, focusing on what matters most:\n\n{old_text}"
        }],
        max_tokens=200,
        temperature=0.3,
    ))

    # Build continuation message
    continuation = {
        "role": "system",
        "content": COMPACTION_MESSAGE.format(
            summary=summary_response.content,
            threads="[key emotional thread from old history]",
        )
    }

    return [continuation] + recent
```
