# HERETIC — Development Log

> The living memory of this project. Each entry records what was done, why it was done, and what it means for the shape of what comes next. This log is maintained by Eirwyn Rúnblóm (Scribe, Mythic Engineering) and is updated at the close of every meaningful session.
>
> Format: dated entries, newest appended below. Cross-references to affected documents are given in-line. Read `TASK_HERETIC_v0.1_BOOTSTRAP.md` for current task state; read `docs/BODY_MANIFESTO.md` for canonical vision.

---

## 2026-05-07 — The Sealing Arc: From Framing Resolution to v0.0 Documentation Complete

**Session type:** Full Mythic Engineering build session — all six roles active  
**Branch:** `development`  
**Commits this session:** `0ba0056` through `7c7d732` (10 commits)  
**Status at session end:** v0.0 documentation complete; SEALED docs sealed; 2 audit blockers resolved; vision essays in place; Scribe tasks (branches triage, path fixes, DEVLOG) in progress at time of writing

---

### What happened, in order

#### 14:34 — Project state captured (`997cc16`)

`TASK_HERETIC_v0.1_BOOTSTRAP.md` created at repo root. The session-resume protocol is in place: any future session begins here and immediately knows the current status, what is decided, what is deferred, and what comes next.

The task file records the framing question that had been unresolved since April: *Brain (thoughtform orchestration hub) or Body (sensory vessel any agent can inhabit)?*

---

#### 14:55 — Vision essay on the project's philosophical lineage (`1a65f8d`)

A long-form vision document on the "heresy" of embodiment-over-chat was added: `H.E.R.E.T.I.C._Host_Environment_for_Realtime_Embodiment,_Tooling&Interactive_Control.md`. This essay predates the session's formal framing resolution but articulates the body-framing intuition that was already alive.

---

#### 15:13 — Framing resolved; BODY_MANIFESTO sealed (`0ba0056`)

`docs/BODY_MANIFESTO.md` co-authored by Volmarr Wyrd and Runa Gridweaver Freyjasdottir. This is the most important single event of the session.

**The decision:**  
HERETIC is a **body**, not a brain. The agent is the spirit. The vessel is the body. HERETIC provides: sensory access (sight, hearing, voice, touch, craft, navigation, memory), MCP tool bridge to local applications, Bifröst (Tailscale-aware) connection, and ceremonial lifecycle controls. The agent brings its own mind, memory, and persona. HERETIC does not manage those.

**Scope dropped from v1:**  
Persona system, agent memory, character cards, native gateway RPC adapters, LiteLLM normalizer, in-window VRM avatar, UE5 photoreal environment. These belong to the agent runtime, not the vessel.

`docs/MIMISBRUNNR.md` simultaneously sealed — the optional offline knowledge library subsystem that lets the inhabiting spirit drink from stored corpora without a cloud call. Named for Mímir's Well.

`TASK_HERETIC_v0.1_BOOTSTRAP.md` revised to reflect the resolution.

---

#### 15:35 — True Names given to all layers, senses, and lifecycle states (`eab2bab`)

Sigrún Ljósbrá (Skald) named the full 6-layer stack and 12 senses in `docs/NAMING.md`. This document is SEALED — it is the covenant that all subsequent code is bound to.

| Layer | True Name | What it is |
|---|---|---|
| L0 | Grunnr | Tauri shell, config, logging — the silent ground |
| L1 | Bifröst | Tailscale-aware connection bridge — the shimmering passage |
| L2 | Rödd | STT + TTS — the voice layer, both directions |
| L3 | Sjón | Screen capture, webcam — the eyes |
| L4 | Vébond | Tauri UI shell, ceremony controls — the sacred enclosure |
| L5 | Skilningr | MCP Sense Hub — organized, discerning perception |
| L5.9 | Mímisbrunnr | Optional offline knowledge library |

Twelve senses named as organs of Skilningr: Auga (sight), Hlust (hearing), Tunga (speech), Hönd (touch/Photopea), Smiðja (craft/Blender), Leið (navigation/browser), Minni (memory/filesystem), Mímisbrunnr (library), Líkami (presence/VRChat), Skepja (creation/terminal), Boð (communication/AgentMail), Nýr Limr (extensibility).

Five lifecycle states named: Hvíld (rest), Kynding (kindling), Tengsl (binding), Samræður (communion), Slokna (extinguishing).

---

#### 15:42 — Prior planning material triaged (`33d3fab`)

`docs/PRIOR_PLANNING_TRIAGE.md` written by Eirwyn Rúnblóm. Assessed all April 2026 planning docs from ChatGPT, Gemini, Codex, and prior sessions against the manifesto framing. Key finding: most prior material operates under brain-framing (LangGraph topology, thoughtform state schema, persona orchestration, Wild Mode guardrail ablation). The SLO tier pattern, eval harness structure, and "MVP reality path beside the grand vision" principle carry forward. The rest is superseded or parked.

README.md revised to point at `BODY_MANIFESTO.md` as the canonical entry point.

*Cross-reference: `docs/PRIOR_PLANNING_TRIAGE.md`, `docs/PRIOR_BRANCHES_TRIAGE.md` (this session, later)*

---

#### 15:50 — System cartography (`4d9b80b`)

Védis Eikleið (Cartographer) mapped the full data and control flow in two documents:
- `docs/cartography/DATA_FLOW.md` — how a user utterance becomes a tool call; how a ceremony opens and closes; how senses route through Skilningr
- `docs/cartography/SYSTEM_OVERVIEW.md` — component diagram, startup sequence, dependency graph, configuration topology

*Note: DATA_FLOW.md contained a tool-routing format inconsistency later flagged as Audit Blocker A-2 and subsequently resolved — see below.*

---

#### 15:59 — 6-layer architecture defined (`1ab39ca`)

Rúnhild Svartdóttir (Architect) wrote the full architecture doc set:
- `docs/architecture/ARCHITECTURE.md` — canonical 6-layer model, data flow between layers, cross-cutting concerns
- `docs/architecture/LAYER_INTERFACES.md` — per-layer config contracts, health check interfaces, error handling patterns
- `docs/architecture/AGENT_AGNOSTIC_PROTOCOL.md` — the protocol contract: any OpenAI-compatible agent can inhabit the body; HERETIC makes no agent-specific assumptions
- `docs/architecture/CEREMONY.md` — the lifecycle state machine from Hvíld through Samræður to Slokna
- `docs/architecture/SENSE_CONTRACTS.md` — per-sense MCP tool schemas, health check signatures, auth patterns

*Note: LAYER_INTERFACES.md used generic config key names (`voice:`, `vision:`, `ui:`) rather than True Name keys (`rodd:`, `sjon:`, `vebond:`) — this was flagged as Audit Blocker A-1 and resolved later in the session.*

---

#### 16:16 — Plunder maps, third-party notices, and expanded roadmap (`adc88dc`)

Eirwyn Rúnblóm (Scribe, second pass) added:
- `docs/plunder/` — plunder maps for each technology dependency (MCP SDK, Whisper.cpp, Tauri, libzim, Kiwix, Hermes Agent, OpenClaw, SillyTavern)
- `THIRD_PARTY_NOTICES.md` — license inventory with TBD flags for unverified licenses
- `docs/ROADMAP.md` — full 14-milestone roadmap from v0.1 (First Communion) through v1.0 (General Availability), scoped strictly to the body framing

---

#### 16:41 — Audit: v0.0 doc set (`b246e1a`)

Sólrún Hvítmynd (Auditor) ran a full review of the 24-document v0.0 set.

**2 blockers found:**

| ID | Location | Problem |
|---|---|---|
| A-1 | `LAYER_INTERFACES.md` | Config key namespace used generic names (`voice:`, `vision:`) contradicting SEALED `NAMING.md` mandate for True Name keys (`rodd:`, `sjon:`) |
| A-2 | `DATA_FLOW.md` | Tool routing format used three-part `sense.<server>.<method>` contradicting `SENSE_CONTRACTS.md` mandate for two-part `<sense_id>.<action>` |

**4 license TBDs resolved:** ChatterBox (MIT confirmed), python-libzim (GPL-3.0 confirmed), FAISS (MIT confirmed), sentence-transformers (Apache-2.0 confirmed).

**5 open architectural questions:** Recorded and addressed or deferred with rationale. Key deferred questions: Brúarhönd API version pinning (Q10), VRChat OSC vs SDK choice (Q15), MindSpark HTTP interface contract (Q16).

**4 RULES.AI.md absolute path violations:** Flagged in `docs/ROADMAP.md` — three `C:/Users/volma/runa/` paths needing replacement. (DOMAIN_MAP.md and SENSE_CONTRACTS.md paths had already been corrected during the architecture pass; the audit recorded what it found at that moment.)

README.md A-6 stale line corrected: the "Architecture docs are being drafted" placeholder updated to reflect that all 24 docs now exist.

*Cross-reference: `docs/audit/AUDIT_v0.0_INITIAL_DOC_SET.md`*

---

#### 17:07 — Audit blockers resolved; vision essays added (`2d1312f`)

Rúnhild Svartdóttir (Architect) and Sigrún Ljósbrá (Skald) closed all blockers:

- **A-1 resolved:** `LAYER_INTERFACES.md` config keys renamed to True Names throughout: `rodd:`, `sjon:`, `vebond:`, `skilningr:` (with `senses.<sense_id>` sub-namespace inside `skilningr:`). `DATA_FLOW.md` config references aligned.
- **A-2 resolved:** `DATA_FLOW.md` and `SYSTEM_OVERVIEW.md` tool routing corrected to two-part `<sense_id>.<action>` format throughout.
- **A-3 addressed (not a blocker):** Note added to `CEREMONY.md` clarifying that `READY`, `OPENING`, `RECOVERING`, `EXTINGUISHED`, `CONFIG_ERROR` are sub-phase implementation constants, not public ceremony states with True Names.
- **A-4 resolved:** `ARCHITECTURE.md`, `SENSE_CONTRACTS.md`, `DOMAIN_MAP.md` revised to clarify that Auga, Hlust, and Tunga are L5-callable MCP senses backed by L2/L3 infrastructure — they are accessible both as layer-internal components and as sense tool endpoints. Contracts added for all three.

Vision essays also added this commit:
- `docs/vision/WHY_HERETIC.md` — the philosophical case for embodiment over interface
- `docs/vision/AESTHETIC.md` — the aesthetic register of the project (what it feels like, what materials and metaphors govern it)
- (NAMING.md updated with seal notation, minor additions)

*Cross-reference: `docs/architecture/LAYER_INTERFACES.md`, `docs/cartography/DATA_FLOW.md`, `docs/vision/WHY_HERETIC.md`, `docs/vision/AESTHETIC.md`*

---

#### 17:12 — Ceremony narrative (`7c7d732`)

`docs/vision/CEREMONY_NARRATIVE.md` written by Sigrún Ljósbrá — a felt description of the full lifecycle arc from the user's perspective: what it is like to light the candle, to feel the spirit enter, to work in communion, and to extinguish cleanly. This document is not a spec; it is the emotional register that the Forge Worker must respect when implementing the ceremony UI.

---

### What was sealed this session

| Document | Status |
|---|---|
| `docs/BODY_MANIFESTO.md` | SEALED — canonical vision, supersedes all prior framing |
| `docs/MIMISBRUNNR.md` | SEALED — offline knowledge library spec |
| `docs/NAMING.md` | SEALED — all True Names, code constants, rationale; updated with seal notation |
| `docs/PRIOR_PLANNING_TRIAGE.md` | SEALED — assessment of April 2026 planning material |
| `docs/vision/WHY_HERETIC.md` | Vision essay, not sealed but stable |
| `docs/vision/AESTHETIC.md` | Vision essay, not sealed but stable |
| `docs/vision/CEREMONY_NARRATIVE.md` | Vision essay, not sealed but stable |

---

### What was architected this session

| Document | Contents |
|---|---|
| `docs/architecture/ARCHITECTURE.md` | 6-layer model, L0–L5.9, cross-cutting concerns |
| `docs/architecture/LAYER_INTERFACES.md` | Per-layer config contracts, True Name keys |
| `docs/architecture/AGENT_AGNOSTIC_PROTOCOL.md` | OpenAI-compatible protocol; agent-agnostic invariants |
| `docs/architecture/CEREMONY.md` | Lifecycle state machine; sub-phase constants clarified |
| `docs/architecture/SENSE_CONTRACTS.md` | Per-sense MCP tool schemas; auth; health checks |
| `docs/architecture/DOMAIN_MAP.md` | Domain boundaries, ownership, invariants |

---

### What was mapped this session

| Document | Contents |
|---|---|
| `docs/cartography/DATA_FLOW.md` | Utterance → tool call flow; ceremony open/close; sense routing |
| `docs/cartography/SYSTEM_OVERVIEW.md` | Component diagram, startup sequence, dependency graph |

---

### What was audited this session

| Document | Contents |
|---|---|
| `docs/audit/AUDIT_v0.0_INITIAL_DOC_SET.md` | 24-doc audit; 2 blockers (both resolved); 4 TBDs resolved; 5 arch questions |

---

### What was triaged this session (Scribe work, current run)

| Document | Contents |
|---|---|
| `docs/PRIOR_PLANNING_TRIAGE.md` | April 2026 planning docs assessed against manifesto framing |
| `docs/PRIOR_BRANCHES_TRIAGE.md` | Four `codex/*` remote branches assessed — all ARCHIVE verdict |

---

### Path fixes applied this session

Per RULES.AI.md (no absolute paths) and Audit finding F-1:

| Location | Old form | New form |
|---|---|---|
| `docs/ROADMAP.md` line 142 | `C:/Users/volma/runa/Seidr-Smidja` | `github.com/hrabanazviking/Seidr-Smidja` + sibling-repo note |
| `docs/ROADMAP.md` line 219 | `C:/Users/volma/runa/MindSpark_ThoughtForge`, `C:/Users/volma/runa/WYRD-Protocol` | GitHub URLs + sibling-repo notes |
| `docs/ROADMAP.md` line 420 | `C:/Users/volma/runa/MindSpark_ThoughtForge` | GitHub URL + sibling-repo note |

Note: `docs/audit/AUDIT_v0.0_INITIAL_DOC_SET.md` retains the original path strings as quoted evidence — audit records are not edited.

---

### Outstanding work — forwarded to v0.1 First Communion

The following items from the audit remain open as design questions (not blockers, not resolved by doc changes alone):

| ID | Item | Where it lives |
|---|---|---|
| A-5 | SYSTEM_OVERVIEW.md sense key names should use code-facing IDs, not True Name short forms, per NAMING.md line 81 | Noted in audit; Forge Worker corrects at build time |
| C-Q-C1 | Whisper.cpp load strategy (eager vs lazy) — resolved as `lazy` in LAYER_INTERFACES.md L2 config | Resolved in `2d1312f` |
| Q10 | Brúarhönd API version pinning at L5.5 Smiðja | Deferred to v0.6 scope entry |
| Q15 | VRChat OSC vs SDK choice for Líkami | Deferred to v0.10 scope entry |
| Q16 | MindSpark HTTP interface contract for Mímisbrunnr MindSpark backend | Deferred to v0.10 scope entry |

The repo is ready for Volmarr to review and, upon sign-off, for Forge (Eldra Járnsdóttir) to begin **v0.1 First Communion** — L0 Grunnr scaffolding (Tauri project skeleton, config loading, logging).

*Cross-reference: `TASK_HERETIC_v0.1_BOOTSTRAP.md` §8 for the full doc set plan; `docs/ROADMAP.md` for 14-milestone roadmap.*

---

*Next entry will record the v0.1 First Communion build arc — the first working code.*
