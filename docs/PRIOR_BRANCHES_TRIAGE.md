# HERETIC — Prior Codex Branch Triage

**Date:** 2026-05-07
**Author:** Eirwyn Rúnblóm (Scribe, Mythic Engineering)
**Branch examined from:** `development`
**Triage criterion:** Does this material describe the **body** (sensory runtime, MCP bridge, Bifröst connection, ceremonial lifecycle, engineering standards) — or does it describe the **brain** (persona orchestration, thoughtform state, LangGraph topology, memory palace, autonomous evolution, Wild Mode)? The manifesto resolved this question on 2026-05-07 in favour of the body. Material that described only the brain is superseded. Material that describes the body, or engineering principles that apply regardless of framing, may carry forward.

> The four branches were created by Codex agents on 2026-04-02, predating the framing resolution. They were not merged into main or development. The diff between each branch and development is empty — their commits predate `development`'s creation from the original `main` line. What each branch added are files that development's current tree does not contain.

---

## Branch 1 — `codex/create-technical-report-on-proposed-code-and-engineering`

### What it contains

Single unique commit: **`6348cb2` — "Add comprehensive multi-volume technical implementation report"**

Files added to `proposed_system_report/`:
- `00_MASTER_INDEX.md` — index of volumes
- `01_EXECUTIVE_SYSTEM_ARCHITECTURE.md` — macro architecture layers: Cognitive Orchestration, Memory and World Model, Model Layer, Platform, Safety
- `02_DETAILED_ENGINEERING_WORKSTREAMS.md` — detailed workstreams for building those layers
- `03_ADVANCED_DATA_SCIENCE_AND_RESEARCH_PLAN.md` — research plan for memory, embedding, ranking
- `04_REFERENCE_IMPLEMENTATION_BLUEPRINTS.md` — blueprints for `session-manager`, `persona-compiler`, `memory-store`, `bond-graph-service`, `policy-engine`
- `05_MLOPS_EVALS_AND_GOVERNANCE.md` — evaluation harness, SLO tiering, observability
- `06_SECURITY_SAFETY_AND_RELIABILITY_SPEC.md` — safety controls, abuse controls, injection guards
- `07_INFRASTRUCTURE_CAPACITY_AND_COST_MODEL.md` — infrastructure sizing
- `08_DELIVERY_ROADMAP_AND_PROGRAM_OPERATIONS.md` — phased delivery plan

### Framing assessment

Volume 01's macro architecture reads: *"Cognitive Orchestration Layer: Router, planner, tool policy guard, sub-agent runtime. Memory and World Model Layer: Episodic memory, semantic memory, symbolic graph memory, user-model state."* Volume 04 describes `persona-compiler`, `memory-store`, and `bond-graph-service` as core services — all named explicitly in the manifesto as **dropped from scope** for HERETIC. The safety layer (Volume 06) and MLOps/evals structure (Volume 05) contain genuinely reusable patterns, but they are not novel — the ChatGPT insights doc already in `development` (`docs/prior_planning/`) covers the same eval harness and SLO tiering in a form already triaged and incorporated.

This report was generated (not carefully hand-crafted) — the service descriptions repeat the same boilerplate SLO and failure-mode template for every service. The content is not authoritative enough to be rescued selectively.

### Verdict: ARCHIVE

**Rationale:** The report describes the brain-framed system almost entirely. The SLO/eval patterns salvageable from it are already covered by the triaged ChatGPT insights doc in `docs/prior_planning/`. Keeping the remote branch as a historical record costs nothing. No cherry-pick.

---

## Branch 2 — `codex/document-code-ideas-in-markdown-files`

### What it contains

Single unique commit: **`e2dd647` — "Add massive deep-dive markdown dataset of implementation code ideas"**

Files added to `research_data/massive_code_ideas/`:
- `00_INDEX.md` — index
- `01_SYSTEM_AND_RUNTIME_IDEAS.md` — "Cognitive Tick Engine," Intent Router with Multi-Policy Arbitration, Runbook-Driven Execution Graph, State Capsules, Declarative Prompt Assembly
- `02_MEMORY_AND_IDENTITY_IDEAS.md` — identity capsule, memory consolidation pipelines, persona stability
- `03_RETRIEVAL_AND_KNOWLEDGE_IDEAS.md` — RAG ideas, semantic routing
- `04_AGENTS_AND_SKILLS_IDEAS.md` — Triad Agent Pattern (CompanionAgent, StewardAgent, BuilderAgent), Dynamic Agent Spawning, Skill Manifest v2
- `05_SAFETY_SECURITY_GOVERNANCE_IDEAS.md` — policy engine ideas
- `06_PRODUCT_EXPERIENCE_IDEAS.md` — product/UX ideas
- `07_EVALS_AND_EXPERIMENTS_IDEAS.md` — eval ideas including replay-mode debugging
- `08_MLOPS_AND_DEPLOYMENT_IDEAS.md` — deployment ideas
- `09_DATASETS_AND_SCHEMAS_IDEAS.md` — dataset structure ideas
- `10_EXECUTION_ROADMAP_IDEAS.md` — roadmap ideas

### Framing assessment

The code ideas are heavily brain-framed: `persona_compiler`, `IdentityCapsule`, `CompanionAgent`, `BondGraphService`. The bulk concerns the thoughtform's internal cognition — which the manifesto explicitly assigns to the agent (Hermes, OpenClaw), not to HERETIC.

Volumes 07 (evals, replay-mode debugging) and parts of 01 (State Capsule pattern, Declarative Prompt Assembly) contain engineering patterns that could theoretically apply to the body. However, the eval ideas are generic and already available in better form through the plunder maps (`HERMES_AGENT_PLUNDER_MAP.md`, `MCP_SDK_PLUNDER_MAP.md`). The prompt assembly patterns are irrelevant — HERETIC does not build prompts; the agent does.

### Verdict: ARCHIVE

**Rationale:** Primarily brain-framing throughout. The few transferable engineering patterns (eval replay, state capsule) are available in better form from existing development docs. No cherry-pick needed.

---

## Branch 3 — `codex/create-codebase-structure-files-in-md`

### What it contains

Single unique commit: **`add5dcd` — "Add comprehensive codebase structure canon and cultural architecture docs"**

Files added to `docs/codebase_structure/`:
- `00_INDEX.md` — folder purpose statement and document set
- `01_REPOSITORY_ATLAS.md` — high-level map of top-level repo domains (root canon, `data/`, `research_data/`, `heretic_v2_implementation_pack/`, cultural/knowledge sets)
- `02_DIRECTORY_CONTRACTS.md` — purpose, allowed content, and maintenance rules per folder
- `03_DOCUMENT_ARCHITECTURE_LAYERS.md` — conceptual architecture layers mapped to files
- `04_ENGINEERING_STANDARDS_AND_GUARDRAILS.md` — documentation-first delivery, modularity, data-driven design, fault tolerance, portability, additive evolution
- `05_CULTURE_ETHOS_AND_SYMBOLIC_LANGUAGE.md` — Frith, reciprocity, anti-gatekeeping, human+AI co-creation, tone contract
- `06_NORSE_HEATHEN_THIRD_PATH_ALIGNMENT.md` — how Heathen values inform build decisions
- `07_HERETIC_NAME_SEMANTIC_SPEC.md` — semantic decomposition of "H.E.R.E.T.I.C." as "Heathen Emergent Reality Engine Thoughtform Intelligence Companion" (old acronym)
- `08_GROWTH_ROADMAP_FOR_STRUCTURE.md` — staged plan for keeping structure healthy as codebase scales

### Framing assessment

This branch is the most interesting case. Files 04, 05, and 06 are **framing-neutral** — they describe engineering standards, cultural philosophy, and Norse Heathen alignment that apply equally to a body-framing project. File 04 (`04_ENGINEERING_STANDARDS_AND_GUARDRAILS.md`) in particular aligns closely with `RULES.AI.md` but is articulated cleanly for this specific repo.

However, file 07 (`07_HERETIC_NAME_SEMANTIC_SPEC.md`) uses the **old acronym** — "Thoughtform Intelligence Companion" — which the manifesto and the new `TASK_HERETIC_v0.1_BOOTSTRAP.md` explicitly replace with "Tooling & Interactive Control." This file would contradict sealed documentation if brought forward as-is.

Files 01–03 describe the **old repository topology** (`heretic_v2_implementation_pack/`, `proposed_system_report/`, a brain-framing `research_data/src/wyrdforge/`) — structure that development's canonical doc set has superseded with the new 6-layer architecture.

Files 05–06 (culture/ethos/Norse alignment) are genuinely useful but shorter than what `PHILOSOPHY.md` and `Heathen_Third_Path_and_Cyber-Viking_Ethos.md` already cover, and adding them would fragment culture documentation.

**`04_ENGINEERING_STANDARDS_AND_GUARDRAILS.md`** is the one genuinely salvageable file — it states modularity, data-driven design, portability, additive evolution, and fault-tolerance in a clean standalone form that could serve as `docs/ENGINEERING_GUARDRAILS.md`. However, `RULES.AI.md` already covers the same ground as immutable project law. The guardrails doc would add a softer, more readable companion without contradicting the rules file.

Decision: the content of file 04 is **worth cherry-picking** in spirit, but the repo already has RULES.AI.md. Rather than introduce a potentially-redundant new doc, the better action is to note the useful patterns for when Forge begins — not to inflate the doc set before code exists.

### Verdict: ARCHIVE

**Rationale:** Files 05–06 are superseded by richer existing docs. Files 01–03 describe an obsolete topology. File 07 uses the old acronym and would contradict sealed docs. File 04 has useful patterns but those are covered by RULES.AI.md. No cherry-pick — archive the branch for reference.

---

## Branch 4 — `codex/generate-data-md-file-with-code-modules`

### What it contains

Two unique commits beyond the `codex/create-codebase-structure-files-in-md` base:

**`f765b9b` — "Create H.E.R.E.T.I.C.deep-research-report-April-2-2026.md"**

A deep research report by a Codex agent analyzing the April 2026 repo contents and proposing implementation paths. Key findings: repo is architecture-first but lacks runnable code; the v2 pack defines an event-sourced replayable kernel with Thoughtform State Schema v2; fastest path is "ledger + replay + schemas + eval harness first." References Chroma/Neo4j/Redis projections, LangGraph, persona identity schema — all brain-framing. Contains useful meta-observation: *"A lot of people will want only one or two layers"* — but that insight is already captured in the ChatGPT insights doc already in development.

**`b8c886f` — "Add markdown bundle of proposed Wyrdforge module code"**

Adds `data/proposed_wyrdforge_complete_modules.md` — 1,140 lines of Python code (in markdown code fences) for Wyrdforge models: `MemoryRecord`, `BondEdge`, `PersonaPacket`, `MicroContextPacket`, `EvalCase`, `EvalResult`, and their Pydantic schemas. This is **implementation code for the brain system** — companion bond graphs, persona packets, identity states — none of which belong in HERETIC's body domain.

### Framing assessment

The deep research report's analysis is interesting historically but its recommendations are written for a system HERETIC has explicitly rejected (thoughtform brain, LangGraph, Chroma/Neo4j). The Wyrdforge module code is purely brain-domain Python — persona compilers, bond edges, companion relationship graphs. Zero of this belongs in a sensory runtime body.

### Verdict: ARCHIVE

**Rationale:** Both unique files describe brain-architecture in concrete terms. The deep research report's meta-observations are already covered by existing development docs. The Wyrdforge code bundle belongs to a different system entirely. Archive both commits as historical record; no cherry-pick.

---

## Recommendations Table

| Branch | Unique commits | Framing | Verdict | Action |
|---|---|---|---|---|
| `codex/create-technical-report-on-proposed-code-and-engineering` | `6348cb2` | Brain (persona, memory-store, bond-graph as HERETIC services) | **ARCHIVE** | Keep on remote as historical record. No merge, no cherry-pick. |
| `codex/document-code-ideas-in-markdown-files` | `e2dd647` | Brain (CompanionAgent, IdentityCapsule, persona stability) | **ARCHIVE** | Keep on remote as historical record. No merge, no cherry-pick. |
| `codex/create-codebase-structure-files-in-md` | `add5dcd` | Mixed — repo-structure docs describe old topology; culture/ethos docs are framing-neutral but superseded; name spec uses old acronym | **ARCHIVE** | Keep on remote. File 04 patterns are noted for Forge reference but not cherry-picked; covered by RULES.AI.md. |
| `codex/generate-data-md-file-with-code-modules` | `f765b9b`, `b8c886f` | Brain (Wyrdforge models, LangGraph, persona packets) | **ARCHIVE** | Keep on remote as historical record. No merge, no cherry-pick. |

### Notes for Volmarr

All four branches are recommended for **ARCHIVE** status — meaning: keep them alive on remote as historical record of the April 2026 planning phase, but take no further action on their contents. None contain material that requires cherry-picking into the current body-framing development line.

If you wish to **delete** any of these branches from the remote at a future point, that action is yours to take; per RULES.AI.md, deletions require your explicit direction. The branches are harmless at rest.

The one pattern worth noting for Forge: `04_ENGINEERING_STANDARDS_AND_GUARDRAILS.md` from Branch 3 states portability and additive-evolution principles cleanly. When Forge begins building L0 Grunnr scaffolding, reading that doc alongside RULES.AI.md may be useful context. No doc change needed — just a pointer.
