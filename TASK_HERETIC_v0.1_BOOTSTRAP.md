# TASK — HERETIC v0.1 BOOTSTRAP

> **Operational task resumption file** — per Volmarr's session-resume protocol. If a session breaks, the next session reads this first.

---

## 1. Task scope

Bring H.E.R.E.T.I.C. — *Heathen Emergent Reality Engine Thoughtform Intelligence Companion* — from a long-planned vision repo to a real, modular, MIT-licensed cyber-Heathen application that:

- Connects to **any open-source AI agent** (Hermes Agent by Nous Research, OpenClaw, plus generic OpenAI-compat fallbacks) as the brain
- Provides **voice** (TTS via ChatterBox + STT via Whisper.cpp)
- Provides **animated avatars** (VRM via three-vrm in v0.6, photoreal UE5 in v1.1)
- Provides an **MCP tool hub** so agents can use Volmarr's other projects (Seidr-Smidja for VRoid, MindSpark for memory, etc.)
- **Modular** — every layer optional, user picks via single config file
- **Phased** — 12 milestones, each independently shippable and usable

The Pi runs the agent (Hermes); the laptop runs all heavy stuff (HERETIC, voice, avatar, UE5).

---

## 2. Current status — 2026-05-07

**Phase: VISION / PLANNING — repo cloned, no architecture docs canonicalized yet, zero code written.**

### Done
- ✅ Repo cloned to `C:\Users\volma\runa\HERETIC` from `hrabanazviking/Heathen-Emergent-Reality-Engine-Thoughtform-Intelligence-Companion`
- ✅ `development` branch created locally
- ✅ Both Tier 1 backends verified:
  - Hermes Agent (Nous Research) — `https://github.com/NousResearch/hermes-agent`, MIT, 137k★, Python
  - OpenClaw — `https://github.com/openclaw/openclaw`, MIT, 369k★, TypeScript
- ✅ Pi-Hermes endpoint verified live at `http://100.101.39.30:8643/v1` (model `coding`, key `hermes`)
- ✅ ChatterBox TTS reachable at `http://100.66.178.105:7851`
- ✅ Architecture decisions made (see §4)
- ✅ Memory captured to `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md`

### Pending
- ⏳ **DEFERRED**: HERETIC role framing — brain (A) vs node/channel (B). Volmarr to decide. (See §5.)
- ⏳ Read Hermes Gateway RPC reference (`hermes-agent.nousresearch.com/docs/reference/rpc`)
- ⏳ Read OpenClaw Gateway RPC reference (`docs.openclaw.ai/reference/rpc`)
- ⏳ Consolidate the existing planning material in the repo into canonical ME-protocol doc set (after framing decided)
- ⏳ Write plunder maps for all v0.1 plundered targets
- ⏳ First push to `development`
- ⏳ Sign-off from Volmarr → Forge starts on v0.1

---

## 3. Repo state — what's already in HERETIC before our build phase

The repo is **not** empty bones. It has substantial pre-existing planning material from prior AI-collaboration sessions (April 2026):

### Top-level vision/philosophy docs (already exist)

| File | Size | Purpose |
|---|---|---|
| `PHILOSOPHY.md` | 3.8K | Skald-tier vision (Wyrd of the Code, mythic ethos) |
| `README.md` | 12K | Initial vision document |
| `RULES.AI.md` | 21K | Coding rules per Volmarr's standard |
| `MYTHIC_ENGINEERING_PLUNDERING_WORKFLOW.md` | 31K | Plunder rules — already canonical here |
| `Heathen_Third_Path_and_Cyber-Viking_Ethos.md` | 31K | Cultural/philosophical context |
| `Technical_Architecture_of_Volmarrs_AI_Ecosystem.md` | 54K | Broader ecosystem context (cross-repo) |
| `WORLD_MODELING_SKILL.md` | 19K | World-modeling design |
| `heretic_dependency_map.md` | 13K | Dependency map |

### Planning/research docs from April 2026 (un-integrated, by various AI agents)

| File | Size |
|---|---|
| `H.E.R.E.T.I.C.-Complete_Development_Study_and_Implementation_Knowledge_Base_version_1.md` | 236K |
| `H.E.R.E.T.I.C.deep-research-report-April-2-2026.md` | 39K |
| `H.E.R.E.T.I.C.-Full_Technical_Architecture_Map_version_1.md` | 12K |
| `H.E.R.E.T.I.C.-LangGraph_Agentic_Core-The_30th-Century_Digital_Seiðr_Nexus_version_1.md` | 11K |
| `H.E.R.E.T.I.C.v2_upgrade_roadmap_recommendation_by_ChatGPT-April-2-2026.md` | 15K |
| `H.E.R.E.T.I.C.-Fractal_Edge_Superposition_version_1.md` | 9.3K |
| `H.E.R.E.T.I.C.-ChatGPTs_Insights-April-2-2026.md` | 6.2K |
| `H.E.R.E.T.I.C.-Geminis_Insight-April-2-3026.md` | 5K |

### Structured directories (already exist)

- `proposed_system_report/` — 9 numbered docs (00-08) covering exec architecture, eng workstreams, ML-ops, security, infra, roadmap
- `heretic_v2_implementation_pack/docs/specs/` — 24 spec files (event ledger, kernel-vs-mythic boundary, thoughtform state v2, ghost echoes, replay/resurrection, eval harness, etc.)
- `possible_barrowed_code_from_my_other_projects_to_use/` — ~30 Python files curated for plunder from NSE / VGSK / etc.
- `data/` — Norse cultural/lore JSON+JSONL+YAML
- `data_project_development_resources/`, `research_data/`, `docs/codebase_structure/`

### Remote branches (from prior AI sessions)

- `codex/create-codebase-structure-files-in-md`
- `codex/create-technical-report-on-proposed-code-and-engineering`
- `codex/document-code-ideas-in-markdown-files`
- `codex/generate-data-md-file-with-code-modules`

These contain prior AI-generated drafts. They are **not yet reviewed or merged**. May or may not align with current architecture decisions.

### Implication

The doc-set work is **NOT** "write 13 fresh docs." It's "consolidate existing material + integrate new architecture decisions + reconcile with deferred framing decision." Most pieces exist in some form; the work is canonicalization, not invention.

---

## 4. Architecture decisions made 2026-05-07

| Decision | Status | Notes |
|---|---|---|
| HERETIC is the project | ✅ | Existing repo, MIT, never built — populating |
| 12-layer modular stack | ✅ | L0 foundation, L1 brain, L2 voice, L3 persona, L4 GUI, L5 2D avatar, L6 VRM, L7 MCP, L8 memory, L9 UE5, L10 VR, L11 wild |
| Each layer optional via `heretic.yaml` | ✅ | User runs as much or as little as wanted |
| Pattern A — monorepo with feature flags | ✅ | Matches NSE / MindSpark / WYRD pattern |
| Frontend: Tauri + React + three-vrm | ✅ | Confirmed after LobeChat-Electron-lag pain |
| UE5 integration: Hybrid (separate process, WebSocket bridge) | ✅ | UE not embedded, runs side-by-side, optional |
| 12-milestone phased roadmap (v0.0 → v1.2) | ✅ | UE/VR are v1.1+ stretch |
| Multi-license layout | ✅ | Own code MIT, plundered code in `vendor/` under permissive license, runtime engines (UE5) external |
| Persona ↔ Agent decoupling | ✅ | Personas client-side, agents pluggable |
| LiteLLM (Apache-2.0) for Tier 2/3 wire-format normalization | ✅ | Avoids reinventing 100+ provider adapters |
| Tier 1 backends: Nous Research Hermes + OpenClaw, native | ✅ | Both designed-for-natively, not adapted-onto |
| L7 MCP unifies HERETIC's local tools with agent's native tools | ✅ | HERETIC exposes MCP server; Hermes/OpenClaw consume it |
| **HERETIC role framing — brain (A) vs node (B)** | ⏳ **DEFERRED** | See §5 |

---

## 5. DEFERRED DECISION — HERETIC role framing

Two framings on the table. Volmarr deferred 2026-05-07 ("we will sort that part later").

### Framing A — HERETIC as brain
HERETIC is a full chat client + UI shell. Agent backends are LLM endpoints. Memory, skills, persona orchestration all live in HERETIC. Backends do raw LLM inference.

- L8 (Memory) is HERETIC's own — SQLite → Chroma → Neo4j, optional MindSpark integration
- L7 (MCP) — HERETIC hosts MCP, all tools called from HERETIC's loop
- L3 (Persona) — character cards owned by HERETIC; system prompts drive backends
- AgentBackend interface = OpenAI-compat-shaped, Hermes/OpenClaw treated as flexible OpenAI-compat targets

### Framing B — HERETIC as node/channel
HERETIC is a custom immersive cyber-Heathen *node* for the agent runtimes — like OpenClaw's iOS/Android nodes today, but with avatar + voice + UE5 + VR + ritual UI. Hermes/OpenClaw own memory/skills/persona; HERETIC contributes embodiment.

- L8 (Memory) shrinks to a fallback — only used for raw LLM backends without their own memory
- L7 (MCP) — HERETIC exposes itself as an MCP server; Hermes/OpenClaw consume it as clients
- L3 (Persona) — SOUL.md lives in Hermes/OpenClaw; HERETIC reads/displays
- AgentBackend interface = native Gateway RPC for Hermes + OpenClaw, OpenAI-compat as fallback

### Tradeoffs

| | A (brain) | B (node) |
|---|---|---|
| HERETIC scope | Larger | Smaller, more focused |
| Reinventing | More memory/skill systems | Less |
| Faithful to original README | Less ("they live in your VR worlds") | More |
| Coupling to Hermes/OpenClaw | Loose | Tight (gateway protocols) |
| Works without Hermes/OpenClaw | Yes | Needs raw-LLM fallback path |
| Roadmap impact | L8 stays full size | L8 shrinks substantially |

### Recommendation in our chat (Runa, 2026-05-07): Framing B
But Volmarr deferred. No architecture docs locked to either until decided.

---

## 6. Tier 1 native backend research — what to read before drafting AgentBackend interface

When framing decision is made and we're ready to draft the AgentBackend interface, READ THESE FIRST so the interface fits both natively rather than coercing one to fit the other:

- [ ] Hermes Architecture — `https://hermes-agent.nousresearch.com/docs/developer-guide/architecture`
- [ ] Hermes Gateway RPC reference — `https://hermes-agent.nousresearch.com/docs/reference/rpc` (or wherever it actually lives — find it)
- [ ] Hermes MCP integration — `https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp`
- [ ] Hermes Skills system — `https://hermes-agent.nousresearch.com/docs/user-guide/features/skills`
- [ ] OpenClaw Architecture — `https://docs.openclaw.ai/concepts/architecture`
- [ ] OpenClaw Gateway protocol — `https://docs.openclaw.ai/reference/rpc`
- [ ] OpenClaw Agent concept — `https://docs.openclaw.ai/concepts/agent`
- [ ] OpenClaw Session model — `https://docs.openclaw.ai/concepts/session`
- [ ] OpenClaw Tools / Skills — `https://docs.openclaw.ai/tools`
- [ ] OpenClaw Live Canvas / A2UI — `https://docs.openclaw.ai/platforms/mac/canvas`
- [ ] agentskills.io open standard — for skill compatibility

Estimated 3-4 hours of focused reading + cross-reference. Yields: AgentBackend interface that supports both natively + clear boundaries between what HERETIC owns vs what the agent runtime owns (resolves Framing A/B by surfacing real constraints).

---

## 7. Cross-repo plug-in slots — confirmed

| HERETIC layer | Existing repo | Status of integration |
|---|---|---|
| L1 Brain | Hermes-on-Pi (`100.101.39.30:8643/v1`) | Live |
| L2 Voice TTS | ChatterBox at `100.66.178.105:7851` | Live |
| L7 MCP — VRoid avatar build | **Seidr-Smidja Brúarhönd v0.1** (`runa/Seidr-Smidja`) | Shipped, 489 tests green |
| L7 MCP — game state | WYRD Protocol (`runa/WYRD-Protocol`) | v1.0 shipped |
| L8 Memory (fallback) | MindSpark ThoughtForge (`runa/MindSpark_ThoughtForge`) | v1.2.0 shipped |
| L9 alternative engine | pygame Viking Edition (`runa/pygame`) | Phase 1A-1D done |

---

## 8. Next concrete steps (in order)

1. **Push this task file** to `development` (this commit)
2. **Volmarr decides** Framing A vs B
3. **Read Hermes + OpenClaw gateway RPC + architecture docs** (3-4 h)
4. **Survey existing repo planning material** — read PHILOSOPHY.md, proposed_system_report/00-08, heretic_v2_implementation_pack/specs/*, the 8 April-2026 vision docs — identify what carries forward vs what's now superseded by 2026-05-07 decisions
5. **Triage the 4 `codex/*` remote branches** — review what they propose, decide for each: cherry-pick, merge, archive, or close
6. **Draft canonical ME doc set** in `docs/`:
   - `docs/SYSTEM_VISION.md` (Skald — extends existing PHILOSOPHY.md)
   - `docs/ARCHITECTURE.md` (Architect — 12-layer model, hybrid UE, layer interfaces)
   - `docs/DOMAIN_MAP.md` (Architect — folder ownership)
   - `docs/DATA_FLOW.md` (Cartographer — wires across all layers + cross-repo)
   - `docs/ROADMAP.md` (12-milestone table, detailed)
   - `docs/AGENT_BACKEND_INTERFACE.md` (post-research)
   - `docs/AGENTS_SUPPORTED.md` (running list of Tier 1-4 backends)
   - `docs/PERSONA_AGENT_BINDING.md` (decoupling pattern + config recipe)
   - `docs/LAYER_INTERFACES.md` (per-layer contract)
   - `docs/plunder/SILLYTAVERN_PLUNDER_MAP.md` (architectural reference only — AGPL)
   - `docs/plunder/THREE_VRM_PLUNDER_MAP.md` (MIT)
   - `docs/plunder/WHISPER_CPP_PLUNDER_MAP.md` (MIT)
   - `docs/plunder/TAURI_PLUNDER_MAP.md` (Apache-2.0/MIT)
   - `docs/plunder/MCP_SDK_PLUNDER_MAP.md` (MIT)
   - `docs/plunder/HERMES_AGENT_PLUNDER_MAP.md` (MIT — for native backend study)
   - `docs/plunder/OPENCLAW_PLUNDER_MAP.md` (MIT — for native backend study)
   - `THIRD_PARTY_NOTICES.md` (root, running list)
7. **Push doc set** to `development`
8. **Volmarr review** — sign-off / redirect / addenda
9. **Then and only then**: Forge starts on **v0.1 First Word** (L0 + L1)

---

## 9. Operational rules in effect

Per Volmarr's standing rules:

- ✅ Branch: all work on `development` (per push-often / branch-discipline laws)
- ✅ Push frequently
- ✅ Data MD files first, no pseudocode (per RULES.AI.md)
- ✅ Always finish all connections — no orphans
- ✅ Modular, fault-tolerant, file-location-agnostic code
- ✅ Plunder rules: Apache-2.0 / MIT / BSD only into `vendor/`; AGPL/GPL never plundered, only studied
- ✅ Multi-license respect: own code MIT, plunder keeps original headers, runtime engines external
- ✅ Mythic Engineering protocol: Skald → Architect → Cartographer → Forge → Auditor → Scribe
- ✅ Update this task file at the end of every work session
- ✅ Update `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md` after each phase

---

## 10. How to resume this task in a future session

1. Read this file from top to bottom.
2. Read `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md` for memory state.
3. Run `git status` and `git log --oneline -10` in `C:\Users\volma\runa\HERETIC` to see latest work state.
4. Check whether Volmarr has resolved the Framing A vs B decision in §5.
5. Continue from "Next concrete steps" §8 at the first uncompleted item.

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-07.*
*This is the canonical task-state document for the HERETIC v0.1 bootstrap phase. Update it as work progresses.*
