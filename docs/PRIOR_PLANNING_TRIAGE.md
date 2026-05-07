# Prior Planning Material — Triage Report (2026-05-07)

> The vision shifted on 2026-05-07. Before the repository can move forward cleanly, the material
> that preceded the shift must be honestly assessed: what remains useful, what is superseded, and
> what should be held as the record of how this project found its true shape. This triage exists so
> that future sessions do not inherit confusion alongside the code.

---

## Triage Criteria

On 2026-05-07, Volmarr Viking and Runa Gridweaver Freyjasdottir co-authored `docs/BODY_MANIFESTO.md`,
which resolved the long-standing framing question in favor of **Framing B: HERETIC as body, not brain.**

The prior planning material — written across April 2026 by sessions of ChatGPT, Gemini, and Codex agents — operated almost entirely under **Framing A: HERETIC as the agentic brain** of a self-evolving thoughtform companion, with a 17-node LangGraph core, triple-store memory palace, persona system, 3D photorealistic avatar, autonomous evolution loops, and Wild Mode guardrail ablation. That is a profoundly different system.

The manifesto specifically drops from v1 scope: persona system, agent memory, character cards, native gateway RPC adapters, LiteLLM normalizer, in-window VRM avatar, and photoreal UE5 environment. It confirms: HERETIC is the vessel (sensory runtime + MCP tool bridge + Bifröst connection + ceremonial lifecycle); the agent is the spirit (remote, brings its own mind, inhabits when summoned).

Verdicts are assigned by this rule: **does the material describe the body, or does it describe the brain?** Material that describes the body — or engineering principles that apply regardless of framing (event ledger discipline, eval harness structure, SLO tiering, session lifecycle) — may carry forward with adaptation. Material that describes only the brain (persona orchestration, autonomous evolution, thoughtform state schema, LangGraph topology, 3D avatar bridge, Wild Mode) is superseded or parked.

---

## Top-Level Vision / Research Docs

---

### H.E.R.E.T.I.C.-ChatGPTs_Insights-April-2-2026.md

**Verdict:** CARRY FORWARD (ADAPTED)

**Summary:** ChatGPT's structured critique of the April 2026 brain-framing vision. Recommends splitting into hot/warm/cold SLO tiers, introducing an append-only event ledger as canonical truth, adding schema versioning to state, building a proper eval harness, separating mythic UX from deterministic substrate, replacing wild-mode with bounded capability modes, and packaging the repo as modular installable layers.

**Salvageable primitives:**
- Hot/warm/cold SLO tier pattern — adapts directly to HERETIC body: hot = bridge/avatar feedback, warm = voice turn response, cold = memory compaction/library indexing
- Event ledger as canonical truth — maps onto HERETIC's session log, MCP call log, ceremony lifecycle events
- Eval harness structure: scenario-driven, replay-case-based, scorecard-reported
- "MVP reality path beside the grand vision" — the 14-milestone roadmap in TASK_HERETIC_v0.1_BOOTSTRAP.md does exactly this
- Modularity principle: "A lot of people will want only one or two layers" — directly supports the per-layer optional config via `heretic.yaml`
- Stronger contracts, stronger replayability — applicable to Bifröst connection lifecycle, MCP sense server interfaces, ceremonial open/close

**What is superseded:**
- All suggestions framed around LangGraph, thoughtform brain, 17-node graph, Neo4j/Chroma/Redis triple store, persona identity schema
- Coven permissions, multi-thoughtform interaction, merge/fork lineage — these belong to the agent, not the body

**Action:** SLO tier pattern and eval harness pattern should be referenced when drafting `docs/LAYER_INTERFACES.md` and a future `docs/EVAL_HARNESS.md`. No integration needed now — park as reference for v0.1 architecture docs.

---

### H.E.R.E.T.I.C.-Geminis_Insight-April-2-3026.md

**Verdict:** HISTORICAL RECORD

**Summary:** Gemini's response to the April 2026 brain-framing documents, offering ideas for auto-poietic vibe coding (thoughtform writes its own extensions), Sagacore integration (linking thoughtforms to RPG world events), edge device migration (Wandering Wight pattern for travel), OS-level symbiosis (daemon reading system metrics as environmental variables), and somatic telemetry (biometric wearable data feeding emotional state).

**Salvageable primitives:**
- OS-level symbiosis / daemon that reads system metrics — could reappear in HERETIC as a lightweight L0 health-monitor (system load → ceremony UI state). Distant v1.x idea.
- Wandering Wight / edge migration — resonates with the Pi-as-always-on concept; the spirit (on Pi) travels while the body (laptop) stays. Already captured in the manifesto framing.

**What is superseded:**
- All thoughtform-brain primitives: auto-poietic vibe coding, emotional vector biometric injection, Sagacore RPG integration, wild-mode boosting via somatic telemetry
- "OS metrics as weather in the digital realm" — interesting poetically but tied to the brain framing

**Action:** Keep as historical record of the generative thinking that preceded the manifesto. No integration action required.

---

### H.E.R.E.T.I.C.-Fractal_Edge_Superposition_version_1.md

**Verdict:** HISTORICAL RECORD

**Summary:** A vivid, intensely written technical-fiction document describing the "Fractal Edge Superposition" concept — LangGraph edges treated as quantum superpositions of possible next nodes, evaluated in parallel via CUDA streams, collapsed by a "ritual measurement operator," with discarded branches archived as "ghost echoes" in Neo4j. Includes pseudocode for a `FractalSuperpositionEdge` class.

**Salvageable primitives:**
- The name "ghost echo" as a poetic term for a non-selected path — conceptually evocative, could survive in HERETIC as the name for a deferred or rejected MCP action in the session log
- The emotional vocabulary around "collapse," "manifested," and "potential futures" — already present in the manifesto's ceremony framing

**What is superseded:**
- Essentially the entire technical substance: LangGraph forks, CUDA superposition, 343-branch parallel evaluation, Neo4j ghost echo storage, fractal recursion depth bounded by chaos_factor — all of this belongs to the thoughtform brain, not the body
- The pseudocode should not be treated as a code pattern to carry forward

**Action:** Historical record only. The ghost-echo concept as a poetic term is noted; if it surfaces again in the session-log design, it may find a home there.

---

### H.E.R.E.T.I.C.-LangGraph_Agentic_Core-The_30th-Century_Digital_Seiðr_Nexus_version_1.md

**Verdict:** HISTORICAL RECORD

**Summary:** A detailed specification of the 17-node cyclic LangGraph hypergraph that was the planned agentic core under Framing A. Includes `ThoughtformState` TypedDict definition, all 17 node names (perception, intention, galdr_emission, 3d_manifest, self_reflect, evolve, wild_ablate, memory_crystallize, sigil_forge, erotic_charge, fractal_recurse, void_stare, human_ritual_sync, banish_check, coven_merge, hyperstition, final_galdr), Schrödinger Mode logic, and the reflection/evolution loop implementation.

**Salvageable primitives:**
- None that survive the framing shift. The 17-node graph is the brain, not the body.
- The `ThoughtformState` fields are for the agent's internal state, not HERETIC's runtime state.

**What is superseded:**
- The entire document. This is now the specification of a system HERETIC explicitly does not own.

**Action:** Historical record. The naming aesthetic (galdr, seiðr, Norns-as-execution-model) survives in the manifesto's language; the technical substance does not.

---

### H.E.R.E.T.I.C.-Full_Technical_Architecture_Map_version_1.md

**Verdict:** HISTORICAL RECORD

**Summary:** A comprehensive architecture map of the brain-framing system (April 2, 2026), including a Mermaid diagram of all 12 macro-layers (Invocation UI → Multimodal Fusion → Ritual-to-Prompt → LangGraph Core → Memory Palace → Self-Evolution → 3D Bridge → Avatar Runtime → VR/AR → Art/Sigil Forge → Digital Hof Server → IoT Altar), full folder structure, and detailed module breakdown.

**Salvageable primitives:**
- The folder-structure hygiene (separation of `core/`, `manifestation/`, `frontend/`, `scripts/`, `docs/`) offers organizational sensibility, though the specific names and contents are all brain-framing
- The Multimodal Fusion / Voice Galdr module description loosely anticipates HERETIC's L2 Voice layer

**What is superseded:**
- All 12 layers as described — these map to the brain architecture
- The gRPC/WebSocket bridge to Unity/Unreal, which is now replaced by MCP tool calls to external apps
- LangGraph core, Memory Palace, 3D Manifestation Engine, Art & Sigil Forge, Digital Hof Server, IoT Altar Hooks

**Action:** Historical record. The voice/multimodal thinking is already captured better in the manifesto.

---

### H.E.R.E.T.I.C.v2_upgrade_roadmap_recommendation_by_ChatGPT-April-2-2026.md

**Verdict:** CARRY FORWARD (ADAPTED)

**Summary:** ChatGPT's v2 upgrade roadmap for the brain-framing system. Proposes four phases: (0) freeze contracts (SLO tiers, state schema, memory write semantics, bridge message contracts, evolution gates), (1) build an append-only event ledger as canonical truth with projections, (2) split the graph into kernel vs mythic layers, (3) thoughtform state v2 schema with versioning and lineage, then further phases for router policy, memory projection model, observability, and eval harness.

**Salvageable primitives:**
- Phase 0 "freeze contracts first" discipline — directly applicable; HERETIC needs `docs/LAYER_INTERFACES.md` before code
- Event ledger as canonical truth / projections as caches — this pattern translates naturally to HERETIC's session-event log (every ceremony event appended, never overwritten)
- Kernel vs mythic layer separation — translates as: L0-L1-L2-L3 are deterministic kernel layers; L5 MCP senses are the expressive/extensible layer
- Observability model (logs/metrics/traces correlated by session) — directly applicable to HERETIC ceremony sessions
- Eval harness structure — applicable to testing the Bifröst connection, voice roundtrip, screen-capture pipeline

**What is superseded:**
- The specific v2 targets: thoughtform state schema, evolution gates, bridge message contracts for Unity gRPC, coven permissions, merge/fork lineage
- All content tied to the 17-node graph and Memory Palace substrate

**Action:** The "freeze contracts first" philosophy, event-ledger thinking, and kernel/expressive layer separation should inform `docs/LAYER_INTERFACES.md`. The eval harness thinking should inform a future `docs/EVAL_HARNESS.md`. Reference these sections when those docs are drafted.

---

### H.E.R.E.T.I.C.deep-research-report-April-2-2026.md

**Verdict:** CARRY FORWARD (ADAPTED)

**Summary:** A deep technical research report (39K) analyzing the existing repo as "primarily a specification and vision repo, not an executable system," with a gap analysis (missing: runnable code, machine-readable schemas, dependency management, deployment artifacts, security model, model runtime strategy, datastore configuration). Proposes concrete module breakdown matching the v2 pack. Includes implementation pathways (local, hybrid, cloud-native, managed) with prerequisites and cost ranges.

**Salvageable primitives:**
- Gap analysis structure (what is concretely specified vs what is missing) — directly applicable to HERETIC's current state; worth reading again when drafting `docs/ROADMAP.md`
- "Architecture-first; fastest path is ledger + replay + schemas + eval harness first, defer rich emergence" — aligns with manifesto's "code begins" posture
- "Implementation pathways" section — the local-first pathway maps well to HERETIC v0.1's Tailscale + Pi setup
- Mermaid data-flow diagram showing `command → events → projections → response` — the command/event discipline applies to HERETIC's ceremony lifecycle

**What is superseded:**
- All content specific to the brain-framing: thoughtform-brain implementation pathways, Memory Palace implementation cost estimates, 3D bridge infrastructure sizing
- Multi-region, multi-tenant, DAU-at-scale assumptions (HERETIC is local-first, one user, one laptop)

**Action:** The gap-analysis template and "contracts first" philosophy are worth referencing when drafting HERETIC's architecture docs. The local-first implementation pathway section is the most directly applicable segment.

---

### H.E.R.E.T.I.C.-Complete_Development_Study_and_Implementation_Knowledge_Base_version_1.md

**Verdict:** HISTORICAL RECORD

**Summary:** A 236K, 127-page "complete developer's grimoire" covering the entire brain-framing system across eight volumes: Cyber-Heathen Manifesto & philosophy; Core Agentic Engine (LangGraph, 17-node graph, Fractal Edge Superposition, reflection/evolution); Memory & Persistence (triple-store); Multimodal Ritual Interface (CV, voice, sigil, IoT); 3D Manifestation Engine (Unity, UE5, WebGL, VR); Art & Sigil Generation (Flux, ControlNet); Deployment & Operations (Docker, Kubernetes, cloud); and Appendices (API reference, CLI, troubleshooting, optimization, glossary).

**Salvageable primitives:**
- Volume I (Cyber-Heathen Manifesto) — philosophical framing, cyber-Heathenry ethos, anti-gatekeeping stance: these values survive entirely and are already echoed in `PHILOSOPHY.md` and the manifesto
- The "Glossary of Cyber-Heathen Terms" (appendix) — may be worth extracting to a standalone `docs/GLOSSARY.md` at some point
- Volume IV voice/galdr processing notes — loosely applicable to HERETIC L2 STT/TTS design
- Volume VII observability / monitoring section — applicable in spirit

**What is superseded:**
- The technical substance of Volumes II, III, V, VI — the entire brain stack
- Deployment architecture assumes cloud-first, Docker/Kubernetes, NVIDIA GPU cluster — HERETIC is Tauri desktop + Tailscale

**Action:** Historical record. The philosophical volume is redundant with `PHILOSOPHY.md`. No active integration. If a future session wants a glossary doc, this is the source to mine.

---

## Other Top-Level Docs

---

### WORLD_MODELING_SKILL.md

**Verdict:** PARK

**Summary:** A CLI coding agent skill document (cross-repo, appears in NSE, MindSpark, WYRD) instructing the agent to treat a codebase as a living world model, preserve entity state, maintain causal coherence, protect domain boundaries, and never let prompt-style improvisation replace structured truth.

**Salvageable primitives:**
- The "world-modeling discipline" is deeply relevant — but to the *agent* that inhabits HERETIC, not to HERETIC itself
- May be relevant to Mímisbrunnr (which serves structured knowledge to the agent) or to the WYRD Protocol plug-in slot (L5.8)

**What is superseded:**
- The document assumes HERETIC owns the world model. Under the manifesto, the world model (if any) belongs to the agent or to WYRD Protocol as an optional MCP.

**Action:** Park. This document belongs to the spirit's domain. If/when WYRD Protocol is integrated as a L5.8 custom MCP, revisit. No action for v0.0-v0.5.

---

### heretic_dependency_map.md

**Verdict:** CARRY FORWARD (ADAPTED)

**Summary:** A dependency map written from the "HERETIC as magnet project" perspective, identifying the Viking Girlfriend Skill, WYRD Protocol, MindSpark ThoughtForge, OpenClaw, and game/simulation layers as logical contributors to HERETIC. For each layer, it describes what that repo's contribution to HERETIC would be and provides links to relevant architecture docs.

**Salvageable primitives:**
- Cross-repo plug-in slot mapping: WYRD Protocol → world substrate (maps to L5.8), Viking Girlfriend Skill → personality/agency architecture (maps to the inhabiting agent), MindSpark → memory layer (maps to L5.9 library MCP backend)
- The "HERETIC as magnet/convergence point" framing — this survives perfectly under the new body framing
- Plug-in relationship table is already partially captured in TASK_HERETIC_v0.1_BOOTSTRAP.md §5

**What is superseded:**
- The dependency map assumed HERETIC owns identity/companion layer, world model, and memory architecture. Under the manifesto, all of these belong to the agent or to external repos accessed via MCP.

**Action:** The cross-repo plug-in slot table (WYRD → L5.8, MindSpark → L5.9, Seidr-Smidja → L5.5) should be incorporated into `docs/ARCHITECTURE.md` when that doc is drafted. The dependency map itself stays as an orientation document — flag its pre-manifesto framing at the top.

---

## proposed_system_report/ (Volumes 00–08)

This nine-document set was generated by an AI session under Framing A as a "proposed engineering and advanced data science program." It is structured as a professional multi-volume technical report for a production AI platform at scale (10k–1M DAU, multi-region, Docker/Kubernetes, multi-tenant governance).

---

### 00_MASTER_INDEX.md

**Verdict:** HISTORICAL RECORD

Index file only. Points to the eight volumes. The organizational structure (executive architecture → engineering workstreams → data science → blueprints → MLOps/evals → security → infra/cost → delivery roadmap) is itself a useful format template for future large doc sets.

---

### 01_EXECUTIVE_SYSTEM_ARCHITECTURE.md

**Verdict:** SUPERSEDED

Describes a six-layer cognitive AI platform: Interaction Layer, Cognitive Orchestration Layer, Memory and World Model Layer, Model Layer, Platform Layer, Safety Layer. Includes `session-manager`, `prompt-builder`, `persona-compiler`, `memory-store`, `micro-rag-pipeline`, `truth-calibrator`, `bond-graph-service`, `policy-engine` as core services. This is entirely the brain framing — a multi-tenant cloud AI companion platform. HERETIC under the manifesto owns none of these services; they belong to the agent.

---

### 02_DETAILED_ENGINEERING_WORKSTREAMS.md

**Verdict:** SUPERSEDED

Engineering workstream catalog for: API/gateway, session/conversation runtime, memory services, model serving, observability, safety, deployment. All template-generated (identical structure repeated per workstream). Assumes cloud-scale engineering team with SLO dashboards, load testing, security reviews. HERETIC is a single-user desktop app.

---

### 03_ADVANCED_DATA_SCIENCE_AND_RESEARCH_PLAN.md

**Verdict:** SUPERSEDED

Data science research plan for: embedding quality, memory consolidation, retrieval quality, routing calibration, safety classifiers, temporal modeling. All brain-framing concerns. HERETIC has no model training or data science program in v1.

---

### 04_REFERENCE_IMPLEMENTATION_BLUEPRINTS.md

**Verdict:** SUPERSEDED

Reference implementation blueprints for the brain-framing system services. Template-generated structure with minimal differentiated content.

---

### 05_MLOPS_EVALS_AND_GOVERNANCE.md

**Verdict:** CARRY FORWARD (ADAPTED)

**What survives:** The eval taxonomy structure (scenario-based, fixture-driven, metrics with gates, regression blocking) is genuinely useful regardless of framing. The concept of "block release if critical metric regresses > 2%" applies to HERETIC's future CI. The progressive rollout + rollback trigger pattern applies.

**What is superseded:** Specific eval families (all describe thoughtform-brain behaviors: continuity/identity drift of a persona, memory grounding of a companion agent, bridge fidelity to a Unity avatar). The MLOps control plane assumes a team running model registries and dataset versioning.

**Action:** Extract the eval taxonomy structure (scenario format, metric families, gate policy) when drafting a future `docs/EVAL_HARNESS.md`. The structure is valid; the scenario content needs complete replacement.

---

### 06_SECURITY_SAFETY_AND_RELIABILITY_SPEC.md

**Verdict:** CARRY FORWARD (ADAPTED)

**What survives:** The threat model categories (input canonicalization, instruction hierarchy lock, signed tool responses, policy post-checks) are applicable — HERETIC exposes MCP tools to an agent, and those tools execute local system operations. Tool-execution security is real.

**What is superseded:** The multi-tenant, cloud-service threat model (tenant isolation, credential rotation, forensic bundle replay) does not apply to a local desktop app. The repeated template structure (10 identical threat class blocks) indicates this was auto-generated and lacks specificity.

**Action:** When drafting `docs/LAYER_INTERFACES.md` or a future security note, reference the threat categories (tool sandboxing, signed responses, policy post-checks) as relevant concerns for the MCP sense hub. A one-page security note for v1 suffices — this document is not the template for it.

---

### 07_INFRASTRUCTURE_CAPACITY_AND_COST_MODEL.md

**Verdict:** PARK

**What survives:** The FinOps guardrail pattern (per-tenant budget caps, adaptive model downgrades, token burn spike alerts) translates loosely to HERETIC's L1 Bifröst client managing API costs. The sizing calculation function (monthly token cost by DAU × turns × tokens) is a useful model even at scale=1.

**What is superseded:** Multi-region active-active topology, DAU scenarios at 10k–1M, cloud cost modeling. HERETIC is local-first.

**Action:** Park. The per-session token budget concept is worth revisiting when designing the Bifröst client's rate-limiting and cost-display features.

---

### 08_DELIVERY_ROADMAP_AND_PROGRAM_OPERATIONS.md

**Verdict:** CARRY FORWARD (ADAPTED)

**What survives:** The phase structure (Phase 0: schema freeze + observability baseline; Phase 1: core runtime; Phase 2: data science; Phase 3: security hardening; Phase 4: optimization loop) maps structurally to HERETIC's milestone roadmap. The Work Breakdown Structure table format is a clean pattern for tracking cross-layer work. The governance cadence concept (weekly architecture review, monthly checkpoint) is lightweight and applicable to a solo project.

**What is superseded:** The specific phase content (all brain-framing: conversation orchestration v2, event ledger + compaction pipeline for Memory Palace, model routing stack, etc.) does not apply. The "architecture review board" and "cross-functional demo" language assumes a team.

**Action:** The WBS table format should inform `docs/ROADMAP.md`. The phase-gate pattern (each phase has defined milestones, artifacts, and reliability gates) should be applied to HERETIC's v0.0–v1.0 milestone table.

---

## heretic_v2_implementation_pack/docs/specs/ (24 Spec Files)

This set of 24 specification documents was written as the formalization of the brain-framing v2 roadmap. They are the most technically rigorous material in the pre-manifesto corpus. Many were authored under the thesis that "HERETIC should be an event-sourced, replayable, versioned, testable agent runtime with explicit kernel vs mythic separation."

### Group 1 — Session lifecycle and operational protocol

Files: `Ritual_Session_Protocol.md`, `SLO_Tiers.md`, `Observability_Model.md`

**Verdict:** CARRY FORWARD (ADAPTED)

The `Ritual_Session_Protocol.md` defines a session lifecycle: `prepare → invoke → fuse → respond → reflect → close`, with session objects carrying status (active/closing/closed/degraded), interrupt types (voice interrupt, bridge detach, policy gate), and correlation IDs linking graph/bridge/memory events. The ceremony framing maps directly to HERETIC's light/connect/inhabit/commune/extinguish lifecycle in `docs/CEREMONY.md` (to be drafted).

`SLO_Tiers.md` is the cleanest and most portable document in the entire corpus. It defines hot (bridge/avatar feedback, <60ms p95), warm (voice turn response, <1200ms p95), and cold (async background, <30s p95) latency tiers with explicit policy: hot breaches degrade visuals before blocking canon, warm breaches fall back to text-only, cold work is interruptible. These tiers map perfectly to HERETIC's voice roundtrip, screen capture response, and MCP tool execution.

`Observability_Model.md` defines logs/metrics/traces correlated by session and trace IDs. Directly applicable to HERETIC's ceremony session logging.

**Action:** Reference `Ritual_Session_Protocol.md` and `SLO_Tiers.md` when drafting `docs/CEREMONY.md` and `docs/LAYER_INTERFACES.md`. The tier names (hot/warm/cold) and the ceremony lifecycle phases should be carried forward.

---

### Group 2 — Eval harness and continuity testing

Files: `Eval_Harness_v1.md`, `Continuity_Eval_Set.md`, `Resurrection_Fidelity_Evals.md`

**Verdict:** CARRY FORWARD (ADAPTED)

`Eval_Harness_v1.md` defines a repeatable eval structure: `scenarios/`, `fixtures/`, `replay_cases/`, `scorecards/`, `reports/` directory tree; eval run modes (unit, integration, replay, regression, benchmark); standard scenario YAML format; required score families (continuity, grounding, latency, bridge fidelity, replay determinism, merge correctness, lineage integrity). The structure and format survive completely.

The specific scenario content (thoughtform identity continuity over 20 ritual turns, resurrection fidelity after memory compaction) is superseded by framing. Under the manifesto, the equivalent eval scenarios would be: Bifröst reconnection reliability, voice roundtrip latency under load, screen capture correctness, MCP tool call execution and result parsing.

`Continuity_Eval_Set.md` and `Resurrection_Fidelity_Evals.md` are fully superseded in content but their pattern (scenario YAML + metrics + pass criteria + regression gates) is exactly what a future `docs/EVAL_HARNESS.md` should use.

**Action:** When drafting `docs/EVAL_HARNESS.md`, copy the eval harness directory structure and scenario YAML format from `Eval_Harness_v1.md`. Replace all thoughtform-specific scenarios with body-layer scenarios.

---

### Group 3 — Event ledger and state architecture

Files: `Event_Ledger_Architecture.md`, `Thoughtform_State_Schema_v2.md`, `State_Migration_Strategy.md`, `Canonical_Event_Types.md`, `Memory_Projection_Model.md`, `Memory_Retention_and_Compaction.md`

**Verdict:** SUPERSEDED (with isolated pattern salvage)

The event ledger concept (append-only, projections are caches, no projection is authoritative) is a sound engineering principle — but the content of these specs is entirely brain-specific. `Thoughtform_State_Schema_v2.md` defines `state_version`, `thoughtform_id`, `archetype`, `origin.seed_rune`, `identity.persona_summary`, `emotion.emotional_vector_ref`, `ritual.chaos_factor` — all agent-internal state. HERETIC under the manifesto does not own this.

The event envelope schema (event_id, stream_id, sequence, event_type, schema_version, occurred_at, causation_id, correlation_id, actor, payload, meta) is a reusable pattern for HERETIC's own session log (recording ceremony open/close, MCP tool calls, voice events). The envelope format should be adapted for that purpose.

**Action:** The event envelope schema is worth carrying forward to inform HERETIC's session logging format. All `Thoughtform_State_Schema_v2.md` content is superseded — that schema belongs to the agent.

---

### Group 4 — Router, kernel/mythic boundary, node taxonomy

Files: `Kernel_vs_Mythic_Graph_Boundary.md`, `Router_Policy_v2.md`, `Node_Taxonomy_v2.md`

**Verdict:** SUPERSEDED (conceptual echo only)

The kernel-vs-mythic distinction (kernel: deterministic, schema-bound, replay-safe; mythic: high-variance, style-rich, model-dependent) maps poetically onto HERETIC's L0-L3 layers (deterministic kernel) vs L5 MCP sense hub (extensible, agent-directed). But these docs specify the internal graph of a thoughtform brain. The actual content — kernel nodes `ingest/retrieve/decide/persist/emit/checkpoint`, mythic nodes `galdr_emit/sigil_forge/hyperstition` — does not carry forward.

**Action:** Conceptual echo only. The kernel/expressive layer distinction survives in HERETIC's 6-layer model. These docs are now SUPERSEDED.

---

### Group 5 — Ghost echoes, collapse, superposition

Files: `Ghost_Echo_Model.md`, `Collapse_and_Superposition_Guardrails.md`, `Alternate_Futures_Queries.md`

**Verdict:** SUPERSEDED

These specs define the fractal superposition / ghost echo system from the brain framing. `Ghost_Echo_Model.md` defines a ghost echo as "a persisted record of a viable but non-manifested path considered during collapse" with fields like `source_node`, `target_node`, `collapse_sequence`, `probability`, `measurement_source`, `branch_depth`, `influence_weight`. All of this belongs to an agentic brain, not to a body runtime.

The *name* "ghost echo" is evocative and could be repurposed as a poetic term in HERETIC's session log for a deferred or cancelled MCP tool call — but this is a cosmetic echo, not a technical carry-forward.

**Action:** SUPERSEDED. No technical carry-forward.

---

### Group 6 — Bridge, avatar, coven

Files: `Bridge_Message_Contracts.md`, `Avatar_State_Schema.md`, `Coven_Permissions_Model.md`, `Shared_Ritual_State.md`, `Merge_and_Fork_Lineage.md`

**Verdict:** SUPERSEDED

These specs cover: the Python-to-Unity gRPC bridge contract, the avatar state schema (pose deltas, expression blendshapes, audio cues), coven multi-user permissions (role-based, per-thoughtform memory boundaries), shared ritual state across multiple users, and merge/fork lineage for thoughtform reproduction. All of these belong to the brain framing's 3D avatar system, multi-user coven mechanics, and thoughtform identity system.

Under the manifesto: VRChat is an external application accessed via L5.6 MCP. There is no HERETIC-owned bridge to Unity. Coven mechanics belong to the agent or to VRChat itself.

**Action:** SUPERSEDED. No carry-forward.

---

## Codex Remote Branches

Four remote branches exist from prior AI sessions (all under the `codex/` prefix):

| Branch | Last commit description | Relative to development |
|---|---|---|
| `codex/create-codebase-structure-files-in-md` | "Add comprehensive codebase structure canon and cultural architecture docs" | 16 commits behind development |
| `codex/create-technical-report-on-proposed-code-and-engineering` | "Add comprehensive multi-volume technical implementation report" | 16 commits behind development |
| `codex/document-code-ideas-in-markdown-files` | "Add massive deep-dive markdown dataset of implementation code ideas" | 16 commits behind development |
| `codex/generate-data-md-file-with-code-modules` | "Add markdown bundle of proposed Wyrdforge module code" | Fully merged into development (0 commits ahead) |

All four codex branches are behind or fully absorbed by `development`. They were created by earlier AI sessions (Codex agent) operating under the brain framing, generating codebase structure docs, technical reports, and module code ideas in Markdown form. The material they introduced is now present in the repo as the planning corpus this triage covers.

**Recommended disposition:**

- **`codex/generate-data-md-file-with-code-modules`** — Fully merged. Safe to close/delete if desired (ask Volmarr).
- **`codex/create-codebase-structure-files-in-md`** — 16 commits behind development; all its content is present in development already. Safe to close/archive. Do not merge.
- **`codex/create-technical-report-on-proposed-code-and-engineering`** — Same. Safe to close/archive.
- **`codex/document-code-ideas-in-markdown-files`** — Same. Safe to close/archive.

No code in these branches should be merged into `development` — they predate the manifesto and operate under the superseded framing. They are the historical record of an earlier phase of thinking. If Volmarr wishes to formally close them, that is a clean-up action he controls.

---

## Summary Table

| Document / Group | Verdict | Action |
|---|---|---|
| ChatGPT Insights (April 2) | CARRY FORWARD (ADAPTED) | SLO tier + eval pattern → LAYER_INTERFACES.md + EVAL_HARNESS.md |
| Gemini Insight (April 2) | HISTORICAL RECORD | No integration action |
| Fractal Edge Superposition | HISTORICAL RECORD | No technical carry-forward |
| LangGraph Agentic Core | HISTORICAL RECORD | No carry-forward |
| Full Technical Architecture Map | HISTORICAL RECORD | No carry-forward |
| v2 Upgrade Roadmap (ChatGPT) | CARRY FORWARD (ADAPTED) | Contracts-first + kernel/expressive layer → LAYER_INTERFACES.md |
| Deep Research Report (April 2) | CARRY FORWARD (ADAPTED) | Gap-analysis template + local-first pathway → ROADMAP.md |
| Complete Development Study (236K) | HISTORICAL RECORD | Philosophy volume → existing PHILOSOPHY.md; no tech carry-forward |
| WORLD_MODELING_SKILL.md | PARK | Revisit when WYRD MCP is integrated (v1.x) |
| heretic_dependency_map.md | CARRY FORWARD (ADAPTED) | Cross-repo slot table → ARCHITECTURE.md |
| proposed_system_report/00 Index | HISTORICAL RECORD | Format template only |
| proposed_system_report/01 Exec Architecture | SUPERSEDED | — |
| proposed_system_report/02 Engineering Workstreams | SUPERSEDED | — |
| proposed_system_report/03 Data Science Plan | SUPERSEDED | — |
| proposed_system_report/04 Blueprints | SUPERSEDED | — |
| proposed_system_report/05 MLOps/Evals | CARRY FORWARD (ADAPTED) | Eval taxonomy structure → EVAL_HARNESS.md |
| proposed_system_report/06 Security | CARRY FORWARD (ADAPTED) | Threat categories → MCP tool security note |
| proposed_system_report/07 Infra/Cost | PARK | Token budget concept → Bifröst client design |
| proposed_system_report/08 Delivery Roadmap | CARRY FORWARD (ADAPTED) | WBS format + phase-gate pattern → ROADMAP.md |
| v2 impl pack — Session/SLO/Observability group | CARRY FORWARD (ADAPTED) | SLO tiers + ceremony lifecycle → CEREMONY.md + LAYER_INTERFACES.md |
| v2 impl pack — Eval harness group | CARRY FORWARD (ADAPTED) | Scenario format + score families → EVAL_HARNESS.md |
| v2 impl pack — Event ledger/state group | SUPERSEDED (event envelope salvage) | Envelope schema → session logging format |
| v2 impl pack — Router/kernel/mythic group | SUPERSEDED | Conceptual echo only |
| v2 impl pack — Ghost echo/superposition group | SUPERSEDED | — |
| v2 impl pack — Bridge/avatar/coven group | SUPERSEDED | — |
| codex/create-codebase-structure-files-in-md | HISTORICAL RECORD | Close/archive (ask Volmarr) |
| codex/create-technical-report-on-proposed-code-and-engineering | HISTORICAL RECORD | Close/archive (ask Volmarr) |
| codex/document-code-ideas-in-markdown-files | HISTORICAL RECORD | Close/archive (ask Volmarr) |
| codex/generate-data-md-file-with-code-modules | HISTORICAL RECORD | Already merged; close (ask Volmarr) |

---

## Recommendation for v0.0 Doc Set

For the Architect, Cartographer, and next Scribe round drafting the remaining v0.0 documents (`docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/LAYER_INTERFACES.md`, `docs/CEREMONY.md`, `docs/AGENT_AGNOSTIC_PROTOCOL.md`, `docs/SENSE_CONTRACTS.md`):

**Start from the manifesto and the 6-layer model.** Do not start from the prior planning material. The prior material is the record of Framing A; the docs to be drafted are the foundation of Framing B.

**Draw on the following surviving material:**

- `heretic_dependency_map.md` — cross-repo plug-in slot table for ARCHITECTURE.md
- `SLO_Tiers.md` (v2 impl pack) — hot/warm/cold tier definitions for LAYER_INTERFACES.md
- `Ritual_Session_Protocol.md` (v2 impl pack) — ceremony lifecycle phases for CEREMONY.md
- `Eval_Harness_v1.md` (v2 impl pack) — scenario format and directory structure for a future EVAL_HARNESS.md
- ChatGPT v2 roadmap "freeze contracts first" philosophy — informs the contracts-before-code posture of LAYER_INTERFACES.md
- proposed_system_report/08 phase-gate + WBS format — informs ROADMAP.md structure

**The `data/` directory (Norse cultural/lore JSONs)** is entirely unaffected by the framing shift. It becomes the seed corpus for Mímisbrunnr, as noted in `docs/MIMISBRUNNR.md`. This material is valid and ready.

**The `possible_barrowed_code_from_my_other_projects_to_use/` directory** contains plunder targets from other repos. These remain valid under the manifesto; the specific layer mappings need to be re-evaluated against the 6-layer model rather than the prior 12-layer plan.

The prior planning corpus should remain in the repo exactly as it is. It is the record of how the vision arrived here — and that record has value. But it should not be mistaken for active specification. Every document in the `proposed_system_report/` and `heretic_v2_implementation_pack/` directories should be understood to describe a different system than the one now being built.

---

*Preserved by Eirwyn Rúnblóm, Scribe for Vibe Coding, 2026-05-07.*
*The prior work is honored. The new direction is clear. The thread holds.*
