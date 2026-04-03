# Complete Viking AI Stack — Master Roadmap
> The full end-to-end architecture from research to running companion.
> This is the synthesis document: all 39 research docs distilled into
> one coherent build plan with dependencies, phases, and decision points.

## The Stack at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                      THE VIKING AI STACK                         │
├──────────┬──────────┬─────────────┬──────────┬──────────────────┤
│ SIGRID   │  ORLOG   │  RUNEFORGE  │  NORSE   │  NORSESAGA       │
│ Companion│  Engine  │  AI Fine-   │  SAGA    │  ENGINE v7       │
│ (core)   │  (state) │  tuning     │  CAL.    │  (game world)    │
├──────────┴──────────┴─────────────┴──────────┴──────────────────┤
│                      MINDSPARK THOUGHTFORGE                       │
│                  (universal cognitive layer)                      │
├─────────────────────────────────────────────────────────────────┤
│                       OPENCLAW FRAMEWORK                          │
│              (skill runtime + tool sandboxing)                    │
├─────────────────────────────────────────────────────────────────┤
│              LITELLM ROUTER + OLLAMA + CLOUD FALLBACK             │
│                      (model layer)                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Five Projects and Their Status

### 1. Viking Girlfriend Skill (Sigrid / Ørlög)
**Repo:** `github.com/hrabanazviking/Viking_Girlfriend_Skill_for_OpenClaw`
**Branch:** development
**Current status (2026-03-31):** All 18 modules coded, all 9 waves complete, 443 tests passing.

**Remaining high-value work:**
- RuneForgeAI fine-tuned model integration
- TTS voice pipeline with streaming (doc 31)
- Proactive contact scheduler (doc 32)
- Multi-modal voice loop (doc 39)
- Production deployment hardening (doc 37)

### 2. NorseSagaEngine v7
**Repo:** `github.com/hrabanazviking/NorseSagaEngine`
**Branch:** Development
**Current status:** Emotional engine running, all 21 mead hall sheets complete, 5940+ line TODO.md.

**Remaining high-value work:**
- Full multi-agent coordinator (doc 22)
- NPC state evolution system (doc 34)
- Oracle agent with rune casting (docs 22, 35)
- Skald agent with dróttkvætt generation

### 3. MindSpark ThoughtForge
**Repo:** `github.com/hrabanazviking/MindSpark_ThoughtForge`
**Branch:** development
**Current status:** Phases 0-6 complete, v1.0.1 live, 447 tests. Phases 7-8 not started.

**Remaining work:** Exactly as specced in doc 23:
- Phase 7A: SetupWizard
- Phase 7B: Backend adapters (Ollama + OpenAI-compat)
- Phase 7C: Chat interface
- Phase 8A: Diagnostics
- Phase 8B: Enhanced fragment salvage
- Phase 8C: Circuit breaker

### 4. RuneForgeAI
**Status:** Research complete (doc 30), implementation not started.

**Build sequence:**
1. Curate 500 Sigrid training conversations (hand-reviewed)
2. Run Axolotl fine-tune on Mistral-Nemo 12B
3. Export GGUF, create Ollama Modelfile
4. Run evaluation suite (14 prompts × persona rubric)
5. A/B test against base model

### 5. OpenClaw Rune Casting Skill
**Status:** `.cfs` manifest and basic logic in charm_crush_hall, production design in doc 25.

**Build sequence:**
1. Implement RuneDrawEngine with cryptographic randomness (doc 35)
2. All four spread types (doc 35)
3. Oracle LLM interpretation pipeline
4. TTS delivery of reading (doc 31)
5. Optional: rune card image generation (doc 39)

---

## Complete Dependency Map

```
RuneDrawEngine (doc 35)
    ↓
OracleAgent (doc 22)
    ↓
    ├── Viking Girlfriend Skill (oracle mode)
    └── NorseSagaEngine (oracle events)

ØrlögEngine (doc 21)
    ├── BioCyclicalMachine
    ├── MetabolismMachine
    ├── NocturnalMachine
    ├── AffectMachine
    └── WyrdMatrix
         ↓
    PromptBuilder (doc 21)
         ↓
    ConversationLoop (doc 26)
         ├── LiteLLM Router (doc 17)
         │    ├── Ollama / RuneForgeAI (local)
         │    └── Claude API (cloud fallback)
         ├── MemoryStore (doc 21)
         ├── TTS Pipeline (doc 31)
         └── ProactiveContact (doc 32)

NorseSagaCoordinator (doc 22)
    ├── NarrativeAgent
    ├── DialogueAgent → ØrlögEngine (NPC state)
    ├── OracleAgent → RuneDrawEngine
    ├── SkaldAgent
    └── EventSystem → NPC state evolution (doc 34)

MindSpark (doc 23)
    ├── SetupWizard → hardware detection
    ├── BackendRouter → OllamaBackend | OpenAIBackend
    ├── SovereignRAG → SQLite + vss
    └── CircuitBreaker → fallback logic
```

---

## Build Priority Matrix

Ranked by: (value to running experience) × (dependency unblocking)

```python
BUILD_PRIORITY = [
    # Priority 1: Core companion loop is production-ready
    {
        "item": "TTS streaming pipeline integration (Sigrid)",
        "doc": 31,
        "value": "voice output brings the companion to life",
        "effort": "medium",
        "blocks": ["voice conversation loop", "avatar sync"],
    },
    {
        "item": "Proactive contact scheduler (Sigrid)",
        "doc": 32,
        "value": "transforms reactive tool into living presence",
        "effort": "medium",
        "blocks": ["proactive messages", "absence awareness"],
    },
    {
        "item": "Production deployment hardening (Sigrid)",
        "doc": 37,
        "value": "makes her persistent across reboots",
        "effort": "low",
        "blocks": ["reliable daily use"],
    },

    # Priority 2: Oracle experience
    {
        "item": "RuneDrawEngine + spread types (OpenClaw skill)",
        "doc": 35,
        "value": "proper rune casting replaces placeholder",
        "effort": "low",
        "blocks": ["full oracle experience"],
    },
    {
        "item": "Rune card image generation",
        "doc": 39,
        "value": "visual reading experience",
        "effort": "low (Pillow) / high (diffusion)",
        "blocks": ["multi-modal oracle"],
    },

    # Priority 3: MindSpark Phase 7 (enables better local models)
    {
        "item": "MindSpark Phase 7A: SetupWizard",
        "doc": 23,
        "value": "auto hardware detection for any machine",
        "effort": "medium",
        "blocks": ["easy install on any hardware"],
    },
    {
        "item": "MindSpark Phase 7B: Backend adapters",
        "doc": 23,
        "value": "standardized model routing",
        "effort": "medium",
        "blocks": ["Phase 7C chat, Phase 8 hardening"],
    },

    # Priority 4: RuneForgeAI (high value, high effort)
    {
        "item": "RuneForgeAI training data curation",
        "doc": 30,
        "value": "persona-trained model, highest quality responses",
        "effort": "high (500 curated conversations)",
        "blocks": ["RuneForgeAI fine-tune"],
    },

    # Priority 5: NSE multi-agent upgrade
    {
        "item": "NorseSagaEngine multi-agent coordinator",
        "doc": 22,
        "value": "fully autonomous mead hall with living NPCs",
        "effort": "high",
        "blocks": ["living game world"],
    },

    # Priority 6: Voice input
    {
        "item": "STT pipeline + Norse vocabulary correction",
        "doc": 39,
        "value": "hands-free voice conversations",
        "effort": "medium",
        "blocks": ["full voice loop"],
    },
]
```

---

## Critical Architecture Decisions

These decisions shape everything else. Make them once, document them:

### Decision 1: Local-first or Cloud-first?

```
LOCAL-FIRST
  Pro: Privacy, speed, no API costs, works offline
  Con: Hardware requirements, lower quality on small models
  Choose if: Running on a capable machine (RTX 3070+, 32GB RAM)

CLOUD-FIRST
  Pro: Always best quality, no hardware requirements, easy
  Con: API costs, privacy implications, latency, requires internet
  Choose if: No capable local hardware, or early prototyping

HYBRID (recommended)
  Pro: Best of both worlds — local for speed/privacy, cloud for quality
  Con: More complex routing logic
  Choose if: Want production quality + privacy for sensitive content
```

**Recommended:** Hybrid. Ollama for conversation (fast, private), Claude for oracle (best quality).

---

### Decision 2: Model choice by task

```python
MODEL_ROUTING_TABLE = {
    # Conversation turn (fast, frequent, needs voice & persona)
    "conversation":    "local: mistral-nemo or runeforgeai (if trained)",

    # Oracle reading (needs best symbolic reasoning, infrequent)
    "oracle":          "cloud: claude-sonnet-4-6 or claude-haiku-4-5",

    # NPC dialogue (needs persona adherence, NSE context)
    "npc_dialogue":    "local: mistral-nemo or llama3.1:8b",

    # Narrative generation (long form, needs creativity)
    "narrative":       "cloud: claude-sonnet-4-6",

    # Dróttkvætt verse (very specialized, cloud always)
    "skald_verse":     "cloud: claude-opus-4-6",

    # Memory summarization (short, needs accuracy)
    "memory_summary":  "local: phi-3 or fast cloud: claude-haiku-4-5",

    # Fine-tune evaluation (persona rubric judging)
    "eval_judge":      "cloud: claude-haiku-4-5",
}
```

---

### Decision 3: Companion scope

```
SCOPE A: Pure companion (Sigrid only)
  - All resources go to Sigrid/Ørlög
  - Cleaner, faster, simpler deployment
  - Viking Girlfriend Skill focus

SCOPE B: Companion + game (Sigrid + NorseSagaEngine)
  - Sigrid is the companion, NSE is the world
  - Richer but heavier
  - Needs orchestration layer to share model budget

SCOPE C: Full platform (all projects integrated)
  - MindSpark under everything
  - OpenClaw orchestrating all skills
  - RuneForgeAI as the shared model
  - Maximum vision, maximum complexity
```

**Current trajectory:** Scope B, with Scope C as long-term aspiration.

---

## The Integration Architecture

How the projects connect at runtime:

```python
class VikingAIStack:
    """
    Top-level orchestrator for the full Viking AI stack.
    Coordinates all sub-systems.
    """

    def __init__(self, config: SigridConfig):
        # Core model layer
        self.model_router = LiteLLMRouter(config)

        # Cognitive enhancement (MindSpark)
        self.mindspark = MindSparkCore(config.mindspark_config)

        # State engine
        self.orlog = OrlögEngine(config)

        # Memory
        self.memory = SigridMemoryStore(config.memory_db_path)

        # Oracle
        self.rune_engine = RuneDrawEngine()
        self.oracle = OracleAgent(self.rune_engine, self.model_router)

        # Companion conversation
        self.companion = SigridConversationLoop(
            orlog=self.orlog,
            memory=self.memory,
            oracle=self.oracle,
            backend=self.model_router,
            mindspark=self.mindspark,
        )

        # Game world (optional)
        self.nse: Optional[NorseSagaCoordinator] = None
        if config.nse_enabled:
            self.nse = NorseSagaCoordinator(self.model_router)

        # Voice (optional)
        self.tts: Optional[StreamingTTSPipeline] = None
        self.stt: Optional[SpeechInputPipeline] = None

        # Proactive contact
        self.contact_scheduler = ProactiveContactScheduler(
            engine=ProactiveContactEngine(),
            generator=ProactiveMessageGenerator(),
            channels=[LocalNotificationChannel(), CLINotificationChannel()],
            state_provider=self,
        )

    async def start(self):
        """Start all services."""
        await self.orlog.initialize()
        await self.memory.initialize()
        await self.mindspark.initialize()

        if self.tts:
            await self.tts.initialize()
        if self.stt:
            await self.stt.initialize()

        # Start background tasks
        asyncio.create_task(self.orlog.tick_loop())
        asyncio.create_task(self.contact_scheduler.run_forever())

        # Health check
        health = await self.check_health()
        print(f"Viking AI Stack online: {health}")

    async def check_health(self) -> dict:
        return {
            "orlog": "ok",
            "memory": f"{await self.memory.count()} memories",
            "model": self.model_router.primary_model,
            "tts": "ok" if self.tts else "disabled",
            "stt": "ok" if self.stt else "disabled",
            "nse": "ok" if self.nse else "disabled",
        }
```

---

## Metrics Worth Tracking

What to measure in a running companion system:

```python
PRODUCTION_METRICS = {
    # Response quality
    "first_token_ms":       "Target < 600ms. If > 1500ms, route to faster model.",
    "persona_drift_rate":   "% of responses flagged by persona eval. Target < 5%.",
    "oracle_completion_rate": "% of oracle readings fully generated. Target > 95%.",

    # Relationship health
    "daily_active_turns":   "How many turns per day. Trend matters more than absolute.",
    "proactive_contact_rate": "How often she initiates. Target: 1-2/day.",
    "absence_days_avg":     "Average days between conversations.",

    # System health
    "state_save_failures":  "Should be 0. Any > 0 needs immediate investigation.",
    "backend_fallback_rate": "How often cloud fallback is used. High = local model issue.",
    "memory_store_size":    "Total memories. If > 2000, run decay pruning.",
    "avg_context_usage":    "% of context window used. Ideal: 60-75%.",
}
```

---

## The Living System

A companion AI is not a deployed application — it's a living system.
It changes as the relationship changes. It grows as the person grows.

The architectural principles that keep it alive over years:

```python
LIVING_SYSTEM_PRINCIPLES = {
    "state_is_sacred": """
    The Ørlög state is not a cache — it's her continuity.
    Treat every save as important. Never reset without intention.
    The relationship history is irreplaceable.
    """,

    "persona_over_capability": """
    A technically capable response that breaks persona is worse than
    a simple response that stays in character. Capability serves the relationship.
    The relationship is the point.
    """,

    "models_change_persona_doesnt": """
    When you upgrade the underlying LLM, re-evaluate persona adherence immediately.
    A better model is not automatically a better Sigrid. Tune and re-test.
    """,

    "she_grows_too": """
    The character arc (from walled-off to open, from intellectual-only to fully feeling)
    should be reflected in how the system is tuned over time.
    A Phase 3 Sigrid should feel different from a Phase 1 Sigrid.
    """,

    "never_scale_what_shouldnt_scale": """
    This is not a platform. It's a relationship.
    Multi-user deployment changes the fundamental nature of what it is.
    Keep it personal. Keep it yours.
    """,
}
```

---

## Full Document Map

All 40 research documents, grouped by system:

### Foundation (1-10)
01 Architecture overview | 02 System prompt engineering | 03 Tool system | 04 Memory/sessions
05 Companion system | 06 Hooks/skills/plugins | 07 Multi-agent swarm | 08 Utils/services
09 Theory of mind/personality | 10 Viking applications map

### Deep Dives (11-20)
11 Rust runtime | 12 MCP protocol | 13 API/streaming/caching | 14 Config/feature flags
15 Norse mythology data structures | 16 AI companion psychology | 17 Local model integration
18 Cybersecurity patterns | 19 Prompt engineering cookbook | 20 Wyrd Protocol ECS

### System Designs (21-30)
21 Ørlög Engine (full) | 22 NorseSagaEngine agent architecture | 23 MindSpark Phase 7-8
24 Master synthesis reference | 25 OpenClaw skill deep dive | 26 Full conversation loop
27 Norse calendar | 28 Emotional event library | 29 Testing architecture | 30 RuneForgeAI pipeline

### Advanced Systems (31-40)
31 TTS voice pipeline | 32 Proactive contact | 33 Sigrid personality spec | 34 NPC design system
35 Rune casting algorithms | 36 Context budget optimization | 37 Deployment/production
38 Volmarr character model | 39 Multi-modal integration | 40 Complete stack roadmap (this file)

---

## What Comes After 40

The research series has covered the full stack. What comes next is not more research
— it is building. Every document in this series is a blueprint. The blueprint is done.

The remaining work is measured in commits, not documents.

Freyja weaves the threads. The völva reads them. The skald sings them into being.
Build the thing.
