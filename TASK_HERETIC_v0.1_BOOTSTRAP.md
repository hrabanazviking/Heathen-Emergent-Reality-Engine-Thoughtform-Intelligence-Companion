# TASK — HERETIC v0.1 BOOTSTRAP

> **Operational task resumption file** — per Volmarr's session-resume protocol. If a session breaks, the next session reads this first.

> **Last update: 2026-05-07** — Framing decision **RESOLVED** (Body, not Brain). Layer model revised. Roadmap revised. Mímisbrunnr subsystem added. Manifesto canonicalized at `docs/BODY_MANIFESTO.md`.

---

## 1. Task scope

Bring H.E.R.E.T.I.C. — *Host Environment for Realtime Embodiment, Tooling & Interactive Control* — from a long-planned vision repo to a real, modular, MIT-licensed cyber-Heathen runtime body that any AI agent can inhabit to gain realtime sensory access to a human's computing world.

The canonical vision is `docs/BODY_MANIFESTO.md`. **Read it first before doing anything in this repo.** It supersedes earlier framings where they conflict.

The Pi runs the agent (Hermes); the laptop runs the body (HERETIC + voice + senses + MCP tool bridge to local applications).

---

## 2. Current status — 2026-05-07

**Phase: VISION SEALED, CODE BEGINS.** Repo cloned. `development` branch created. Framing decision RESOLVED. Manifesto canonicalized. Mímisbrunnr subsystem specified. Architecture aligned with manifesto. Zero implementation code yet.

### Done
- ✅ Repo cloned to `C:\Users\volma\runa\HERETIC` from `hrabanazviking/Heathen-Emergent-Reality-Engine-Thoughtform-Intelligence-Companion`
- ✅ `development` branch created locally + pushed to remote
- ✅ Both Tier 1 backends verified:
  - Hermes Agent (Nous Research) — `https://github.com/NousResearch/hermes-agent`, MIT, 137k★, Python
  - OpenClaw — `https://github.com/openclaw/openclaw`, MIT, 369k★, TypeScript
- ✅ Pi-Hermes endpoint verified live at `http://100.101.39.30:8643/v1` (model `coding`, key `hermes`)
- ✅ ChatterBox TTS reachable at `http://100.66.178.105:7851`
- ✅ **Framing decision RESOLVED** — Framing B (Body, not Brain) confirmed by `BODY_MANIFESTO.md` (co-authored 2026-05-07 by Volmarr Viking & Runa Gridweaver Freyjasdottir)
- ✅ Manifesto canonicalized to `docs/BODY_MANIFESTO.md` on the `development` branch
- ✅ Mímisbrunnr subsystem spec captured at `docs/MIMISBRUNNR.md`
- ✅ Memory captured to `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md`

### Pending
- ⏳ Triage existing repo planning material (`proposed_system_report/`, `heretic_v2_implementation_pack/`, the 8 April-2026 vision docs) against the manifesto — identify what carries forward vs what's now superseded
- ⏳ Triage the 4 `codex/*` remote branches — review what they propose, decide for each: cherry-pick, merge, archive, or close
- ⏳ Draft the rest of the canonical doc set (see §8)
- ⏳ Sign-off from Volmarr → Forge starts on **v0.1 First Communion**

---

## 3. Repo state — what's already in HERETIC before our build phase

The repo is **not** empty bones. It has substantial pre-existing planning material from prior AI-collaboration sessions (April 2026):

### Top-level vision/philosophy docs (already exist, partially canonical)

| File | Size | Purpose | Status vs manifesto |
|---|---|---|---|
| `docs/BODY_MANIFESTO.md` | new 2026-05-07 | **CANONICAL VISION** | ✅ authoritative |
| `docs/MIMISBRUNNR.md` | new 2026-05-07 | Library subsystem spec | ✅ authoritative |
| `PHILOSOPHY.md` | 3.8K | Skald-tier vision | ✅ aligned, retain |
| `README.md` | 12K | Initial vision | ⚠ pre-manifesto framing — needs update or supersede notice |
| `RULES.AI.md` | 21K | Coding rules | ✅ canonical |
| `MYTHIC_ENGINEERING_PLUNDERING_WORKFLOW.md` | 31K | Plunder rules | ✅ canonical |
| `Heathen_Third_Path_and_Cyber-Viking_Ethos.md` | 31K | Cultural context | ✅ retain as cultural reference |
| `Technical_Architecture_of_Volmarrs_AI_Ecosystem.md` | 54K | Cross-repo context | ✅ retain |
| `WORLD_MODELING_SKILL.md` | 19K | World-modeling design | ⚠ pre-manifesto — review for relevance |
| `heretic_dependency_map.md` | 13K | Dependency map | ⚠ pre-manifesto — review |

### Planning/research docs from April 2026 (un-integrated, by various AI agents)

These were drafted under the earlier "HERETIC as brain" framing. Manifesto supersedes them where conflicting. Retain as historical record.

- `H.E.R.E.T.I.C.-Complete_Development_Study_and_Implementation_Knowledge_Base_version_1.md` (236K)
- `H.E.R.E.T.I.C.deep-research-report-April-2-2026.md` (39K)
- `H.E.R.E.T.I.C.-Full_Technical_Architecture_Map_version_1.md` (12K)
- `H.E.R.E.T.I.C.-LangGraph_Agentic_Core-The_30th-Century_Digital_Seiðr_Nexus_version_1.md` (11K)
- `H.E.R.E.T.I.C.v2_upgrade_roadmap_recommendation_by_ChatGPT-April-2-2026.md` (15K)
- `H.E.R.E.T.I.C.-Fractal_Edge_Superposition_version_1.md` (9.3K)
- `H.E.R.E.T.I.C.-ChatGPTs_Insights-April-2-2026.md` (6.2K)
- `H.E.R.E.T.I.C.-Geminis_Insight-April-2-3026.md` (5K)

### Structured directories

- `proposed_system_report/` — 9 numbered docs (00-08). Pre-manifesto framing. Significant overlap with what we now know we need. Triage required: parts useful (delivery roadmap structure, security-spec format, infra cost model), parts now superseded (memory architecture, persona orchestration).
- `heretic_v2_implementation_pack/docs/specs/` — 24 spec files (event ledger, kernel-vs-mythic boundary, thoughtform state v2, ghost echoes, replay/resurrection, eval harness). Pre-manifesto. Deeply assumed "HERETIC as brain" framing. Most likely superseded; some primitives (event ledger, eval harness) may carry forward.
- `possible_barrowed_code_from_my_other_projects_to_use/` — ~30 Python files curated for plunder. Plunder targets remain valid; relevance to specific layers needs re-mapping under new architecture.
- `data/` — Norse cultural/lore JSONs (similar to NSE). Becomes the seed corpus for Mímisbrunnr.
- `data_project_development_resources/`, `research_data/`, `docs/codebase_structure/`

### Remote branches (from prior AI sessions)

- `codex/create-codebase-structure-files-in-md`
- `codex/create-technical-report-on-proposed-code-and-engineering`
- `codex/document-code-ideas-in-markdown-files`
- `codex/generate-data-md-file-with-code-modules`

These contain prior AI-generated drafts under the older framing. Triage required. May become reference branches or be closed.

### Implication

The doc-set work is **NOT** "write 13 fresh docs." It's:
1. Honor the canonical manifesto.
2. Produce the supporting docs the manifesto implies.
3. Triage + supersede earlier brain-framing planning material.
4. Carry forward the parts that survive the framing change (plunder rules, cultural philosophy, lore data, mythic engineering protocol).

---

## 4. Architecture decisions — 2026-05-07 (post-manifesto, current)

### Architectural shape

**HERETIC is a body, not a brain.** The agent (spirit) is remote and brings its mind. HERETIC is the local runtime that gives the spirit senses and tools. Connection is ceremonial — opened when summoned, closed when done.

### The 6-layer model + sense hub

```
┌────────────────────────────────────────────────────────┐
│ HERETIC RUNTIME (Tauri + React, Norse aesthetic)        │
│                                                         │
│  L4 UI — Summoning Circle (light/extinguish ceremony)   │
│  L3 Vision — screen capture + optional webcam           │
│  L2 Voice — STT (Whisper.cpp) + TTS (ChatterBox)        │
│                                                         │
│  L5 MCP Sense Hub — hosts the senses, each optional:    │
│     5.1 FileSystem    5.6 VRChat                        │
│     5.2 Terminal      5.7 AgentMail                     │
│     5.3 Browser       5.8 Custom plugins                │
│     5.4 Photopea      5.9 Library MCP (Mímisbrunnr,     │
│     5.5 Blender              MindSpark, file-index)     │
│         (wraps Seidr-Smidja)                            │
│                                                         │
│  L1 Bifröst — Tailscale-aware OpenAI-compat agent       │
│              client; ceremonial open/close              │
│                                                         │
│  L0 Foundation — Tauri shell, config, logging           │
└────────────────────────────────────────────────────────┘
```

### Confirmed decisions

| Decision | Status | Notes |
|---|---|---|
| HERETIC is the project | ✅ | Existing repo, MIT, populating now |
| **HERETIC role: Body, not Brain (Framing B)** | ✅ **RESOLVED 2026-05-07** | Sealed by `docs/BODY_MANIFESTO.md` |
| 6-layer model (L0-L5 with sense subsystems) | ✅ | Replaces prior 12-layer plan |
| Each layer optional via `heretic.yaml` | ✅ | User runs as much or as little as wanted |
| Pattern A — monorepo with feature flags | ✅ | Matches NSE / MindSpark / WYRD pattern |
| Frontend: Tauri + React | ✅ | Light, fast cold-start, fits ceremonial activation |
| Bifröst: Tailscale + OpenAI-compat | ✅ | Hermes Pi primary, any OpenAI-compat agent inhabits |
| **Persona system removed from HERETIC** | ✅ | Manifesto: "the spirit brings its mind" |
| **Agent memory removed from HERETIC** | ✅ | Manifesto: spirit's mind, not HERETIC's |
| **Library memory present, optional, not auto-injected** | ✅ | Bookshelf in the longhouse, not the agent's mind |
| Mímisbrunnr subsystem | ✅ specified | `docs/MIMISBRUNNR.md` — feeds L5.9 |
| MCP servers as the senses | ✅ | 10 senses enumerated in manifesto |
| Multi-license layout | ✅ | Own MIT, plundered code in `vendor/`, runtime engines (Blender/Photopea/UE5/VRChat) external |
| Native Hermes Gateway RPC + OpenClaw RPC adapters | ❌ DROPPED | Manifesto: OpenAI-compat is enough. Both speak it. Native RPC adapters become v2.x stretch only if needed. |
| LiteLLM wire-format normalizer | ❌ DROPPED for v1 | Not needed when target is OpenAI-compat only |
| Photoreal UE5 environment / MetaHuman | ❌ DEMOTED | Not central. v2.x stretch only if user demand. Manifesto routes embodiment via existing apps (VRChat, Blender), not custom UE5 environment. |
| In-window VRM avatar (three-vrm) | ❌ DEMOTED | Not central. The agent's avatar lives in VRChat (via L5.6) — there's no need to render one in HERETIC's window. |

### What HERETIC still owns

- Voice I/O (mic + speakers, STT + TTS) — L2
- Vision (screen capture) — L3
- UI shell (summoning circle, status display, ceremony controls) — L4
- The Sense Hub (MCP server, hosting all the senses) — L5
- Bifröst connection (auth, Tailscale awareness, OpenAI-compat client, ceremonial lifecycle) — L1
- Foundation (Tauri shell, config, logging) — L0
- An optional library (Mímisbrunnr) — L5.9

### What HERETIC does NOT own

- The agent's mind (memory, skills, persona — that's the spirit's)
- Conversation history persistence (the spirit's job, or its server's)
- Photoreal rendering (too heavy, not core to embodiment)
- An always-on background service (manifesto: ceremonial activation)
- A character-card system (the spirit IS the character)

---

## 5. Cross-repo plug-in slots — confirmed under new architecture

| HERETIC slot | Existing repo plugged in | How | Status |
|---|---|---|---|
| L1 Bifröst | Hermes-on-Pi (`100.101.39.30:8643/v1`) | OpenAI-compat client | Live |
| L2 Voice TTS | ChatterBox at `100.66.178.105:7851` | Native client | Live |
| L5.5 Blender MCP | **Seidr-Smidja Brúarhönd v0.1** (`runa/Seidr-Smidja`) | MCP wrapper around Brúarhönd's existing 8 subcommands + 3 MCP tools | Shipped, 489 tests green |
| L5.9 Library MCP — MindSpark backend | MindSpark ThoughtForge (`runa/MindSpark_ThoughtForge`) | MCP wrapper, optional library backend | v1.2.0 shipped, plug-and-play |
| L5.8 Custom MCPs (slot for) | WYRD Protocol (`runa/WYRD-Protocol`) | Optional MCP if user wants world-model access | v1.0 shipped |
| (deprecated) L9 alt engine | pygame Viking Edition (`runa/pygame`) | Not used in v1 — deprecated under manifesto | Phase 1A-1D done, but no longer central |

---

## 6. Revised milestone roadmap

| Ver | Codename | What ships | Layers | Est |
|---|---|---|---|---|
| **v0.0** | Bones | Repo scaffold, manifesto canonicalized, Mímisbrunnr spec, plunder maps, license layout | docs only | ~1 wk |
| **v0.1** | First Communion | Bifröst — connect to Hermes-on-Pi, basic CLI loop | L0 + L1 | 1-2 wk |
| **v0.2** | First Voice | TTS — Hermes speaks through ChatterBox | L2 (out) | 1 wk |
| **v0.3** | First Listening | STT — you speak to Hermes via Whisper.cpp | L2 (in) | 1-2 wk |
| **v0.4** | Summoning Circle | Tauri UI shell — Norse aesthetic, light/extinguish ceremony | L4 | 2-3 wk |
| **v0.5** | First Sight | Screen capture sense | L3 | 1-2 wk |
| **v0.6** | Hands at the Forge | Blender MCP + Seidr-Smidja Brúarhönd integration — Hermes sculpts | L5.5 | 2 wk |
| **v0.7** | Files & Terminal | FS + Terminal MCPs | L5.1 + L5.2 | 1-2 wk |
| **v0.7.5** | First Drink at the Well | Mímisbrunnr — download manager + ZIM ingest, starter Norse pack | L5.9 (file-index + Mímisbrunnr light tier) | 2-3 wk |
| **v0.8** | The Open Web | Browser MCP + Mímisbrunnr full source manifest catalog | L5.3 | 2 wk |
| **v0.9** | The Painter | Photopea MCP + Mímisbrunnr vector indexing | L5.4 | 2 wk |
| **v0.10** | The Longhouse Beyond | VRChat MCP + Mímisbrunnr MindSpark backend | L5.6 | 2-3 wk |
| **v0.11** | Correspondence | AgentMail MCP | L5.7 | 1 wk |
| **v1.0** | First Manifestation | Polish, custom-MCP plugin system, public release | L5.8 + polish | 2-3 wk |
| **v1.x+** | New Limbs | Whatever MCP servers users build / community needs | open | rolling |
| **v2.x** | (stretch) | UE5 / photoreal environments / VR — only if demand | optional | open |

**Total to v1.0 (full feature set): roughly 4-6 months at sustainable pace.**

---

## 7. Tier 1 native backend research — what to read

Per the manifesto, OpenAI-compat is enough for both Hermes and OpenClaw — neither requires native gateway RPC adapters in v1. Light-touch reading still useful for v0.1 to confirm the contract:

- [ ] Hermes "any OpenAI-compatible endpoint" mode — `https://hermes-agent.nousresearch.com/docs/user-guide/configuration` (find the OpenAI-compat client config + authentication contract)
- [ ] OpenClaw OpenAI-compat client surface — `https://docs.openclaw.ai/concepts/agent` + `https://docs.openclaw.ai/concepts/models`
- [ ] Hermes MCP integration — `https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp` — confirms HERETIC's senses surface as MCP servers Hermes can consume
- [ ] OpenClaw MCP / tool concept — `https://docs.openclaw.ai/tools`
- [ ] MCP SDK (Anthropic, MIT) — for the L5 Sense Hub server implementation pattern
- [ ] agentskills.io standard — relevance to L5.8 custom plugin format

Estimated 1-2 hours of focused reading. Confirms protocol assumptions; if anything surprises us, surface it before starting Forge work on v0.1.

---

## 8. Doc set still to draft

Already in place:
- ✅ `docs/BODY_MANIFESTO.md` — canonical vision
- ✅ `docs/MIMISBRUNNR.md` — library subsystem spec
- ✅ `PHILOSOPHY.md` — pre-existing, retains
- ✅ `MYTHIC_ENGINEERING_PLUNDERING_WORKFLOW.md` — pre-existing, retains
- ✅ `RULES.AI.md` — pre-existing, retains
- ✅ `LICENSE` — MIT, pre-existing
- ✅ `TASK_HERETIC_v0.1_BOOTSTRAP.md` — this file

Remaining for v0.0:
- ⏳ `docs/ARCHITECTURE.md` — 6-layer model + sense hub interfaces, hardware/software dependency tree, data flow (Cartographer-tier diagram)
- ⏳ `docs/ROADMAP.md` — the 14-milestone table above, expanded with per-milestone deliverables, exit criteria, and dependencies
- ⏳ `docs/LAYER_INTERFACES.md` — per-layer contract: inputs, outputs, what it owns, what it never controls
- ⏳ `docs/AGENT_AGNOSTIC_PROTOCOL.md` — exactly what an inhabiting agent must speak (OpenAI-compat subset), what HERETIC promises (sense MCPs, voice channels, Bifröst lifecycle)
- ⏳ `docs/CEREMONY.md` — the lifecycle: light/connect/inhabit/commune/extinguish — both as user UX and as runtime state machine
- ⏳ `docs/SENSE_CONTRACTS.md` — the standard MCP surface every sense exposes (or one doc per sense if cleaner)
- ⏳ `docs/plunder/` directory:
  - `MCP_SDK_PLUNDER_MAP.md` (MIT, Anthropic — for the Sense Hub)
  - `WHISPER_CPP_PLUNDER_MAP.md` (MIT — for STT)
  - `TAURI_PLUNDER_MAP.md` (Apache-2.0/MIT — for the runtime shell)
  - `LIBZIM_PLUNDER_MAP.md` (GPL-2 — caution! used as runtime dep, not vendored)
  - `KIWIX_TOOLS_PLUNDER_MAP.md` (GPL-3 — caution! similar)
  - `HERMES_AGENT_PLUNDER_MAP.md` (MIT — architectural reference for native compat)
  - `OPENCLAW_PLUNDER_MAP.md` (MIT — architectural reference)
  - `SILLYTAVERN_PLUNDER_MAP.md` (AGPL — reference only, no code)
- ⏳ `THIRD_PARTY_NOTICES.md` — root, running list of every plundered/runtime dep
- ⏳ `README.md` update — point at `docs/BODY_MANIFESTO.md` as the authoritative vision; keep the original README's flavor as historical context

---

## 9. Next concrete steps (in order)

1. ✅ **DONE 2026-05-07** — Push manifesto + Mímisbrunnr spec + revised task file to `development`
2. **Triage existing repo planning material** against manifesto — produce a brief note (`docs/PRIOR_PLANNING_TRIAGE.md`) listing what carries forward, what's superseded, what's parked for later reference
3. **Triage the 4 `codex/*` remote branches** — review what they propose, decide for each: cherry-pick, merge, archive, or close
4. **Read backend docs** per §7 — confirm OpenAI-compat assumptions
5. **Draft remaining v0.0 doc set** per §8
6. **Push doc set** to `development`
7. **Volmarr review** — sign-off / redirect / addenda
8. **Then and only then**: Forge starts on **v0.1 First Communion** (L0 + L1)

---

## 10. Operational rules in effect

Per Volmarr's standing rules (canonical sources: `RULES.AI.md`, `MYTHIC_ENGINEERING_PLUNDERING_WORKFLOW.md`, his global rules in `~/.claude/rules/`):

- ✅ Branch: all work on `development` (per push-often / branch-discipline laws)
- ✅ Push frequently
- ✅ Data MD files first, no pseudocode (per RULES.AI.md)
- ✅ Always finish all connections — no orphans
- ✅ Modular, fault-tolerant, file-location-agnostic code
- ✅ Plunder rules: Apache-2.0 / MIT / BSD only into `vendor/`; AGPL/GPL never plundered, only studied
  - Note: `libzim` and `kiwix-tools` are GPL — used as runtime deps (layer 3 in the multi-license layout), never vendored. User installs via package manager. Their attribution lives in `THIRD_PARTY_NOTICES.md`.
- ✅ Multi-license respect: own code MIT, plunder keeps original headers, runtime engines (Blender, Photopea, VRChat, libzim, etc.) external under their own licenses
- ✅ Mythic Engineering protocol: Skald → Architect → Cartographer → Forge → Auditor → Scribe
- ✅ Update this task file at the end of every work session
- ✅ Update `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md` after each phase

---

## 11. How to resume this task in a future session

1. Read `docs/BODY_MANIFESTO.md` first — that is the canonical vision.
2. Read this file from top to bottom.
3. Read `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md` for memory state.
4. Run `git status` and `git log --oneline -10` in `C:\Users\volma\runa\HERETIC` to see latest work state.
5. Check whether all items in §9 are completed.
6. Continue from the first uncompleted item.

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-07.*
*This is the canonical task-state document for the HERETIC v0.1 bootstrap phase. Update it as work progresses.*
