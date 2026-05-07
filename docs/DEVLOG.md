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

---

## 2026-05-07 — The First Communion Arc: From Bones to Body (v0.1 Shipped and Audited)

**Session type:** Full Mythic Engineering build session — all six roles active (continuation of same calendar day)
**Branch:** `development`
**Commits this session:** `bd7110f` through `147ad30` (14 commits, spanning Wave 1 and Wave 2)
**Status at session end:** v0.1 First Communion **SHIPPED AND AUDITED** — 121 tests passing, 0 blockers, all four post-audit notables closed

---

### Preamble — where Wave 1 began

The prior entry closed with the v0.0 doc set complete: manifesto sealed, architecture documented, audited, blockers resolved. The session's second arc began immediately after, with the Scribe completing two housekeeping tasks, and then Architect and Forge building the first real code.

---

### Scribe housekeeping — branch triage + path fixes (`bd7110f`, `fb5dde0`, `9dd06d4`)

Three preparatory commits were made before any code was written.

**`bd7110f`** — Prior `codex/*` remote branches were triaged. A triage document (`docs/PRIOR_BRANCHES_TRIAGE.md`) recorded the verdict for each:

| Branch | Verdict |
|---|---|
| `codex/create-codebase-structure-files-in-md` | ARCHIVE — structural proposals, brain-framing, superseded |
| `codex/create-technical-report-on-proposed-code-and-engineering` | ARCHIVE — engineering report, brain-framing, superseded |
| `codex/document-code-ideas-in-markdown-files` | ARCHIVE — idea fragments, no code, superseded |
| `codex/generate-data-md-file-with-code-modules` | ARCHIVE — module stubs, brain-framing, superseded |

All four `codex/*` branches exist on the remote as historical record; none were merged.

**`fb5dde0`** — Absolute paths violating RULES.AI.md found in `docs/ROADMAP.md` (three instances of `C:/Users/volma/runa/…`). All three replaced with GitHub URLs and sibling-repo notes. Audit finding F-1 closed.

**`9dd06d4`** — `docs/DEVLOG.md` opened (this file). First entry written, covering the full v0.0 sealing arc.

---

### Architect scaffolds the Python package (`7023c54`)

Rúnhild Svartdóttir (Architect) created the `src/heretic/` Python package skeleton, establishing the exact module boundaries that would govern everything Forge built afterward:

- `src/heretic/__init__.py` — package root, version constant `0.1.0.dev0`
- `src/heretic/grunnr/` — L0 Foundation: `config.py`, `lifecycle.py`, `logger.py`, `paths.py`
- `src/heretic/bifrost/` — L1 Bifröst: `client.py`, `config_model.py`, `tailscale.py`, `errors.py`
- `src/heretic/cli.py` — CLI entry point
- `pyproject.toml` — project metadata, dependencies (`pyyaml>=6.0`, `httpx>=0.27`), dev deps (`pytest`, `pytest-asyncio`, `pytest-mock`), entry point `heretic = heretic.cli:main`
- `heretic.example.yaml` — reference configuration file covering all layers, all True Name keys

The scaffold contained module stubs only — no executable logic. Crucially, the domain boundaries were locked here: Grunnr owns config/lifecycle/paths/logging; Bifröst owns the agent connection; the CLI owns nothing except bridging them. Neither layer imports the other.

*Cross-reference: `docs/architecture/ARCHITECTURE.md`, `docs/architecture/LAYER_INTERFACES.md`*

---

### Forge Worker builds L0 Grunnr (`f2a476a`)

Eldra Járnsdóttir (Forge Worker) implemented the full L0 Foundation, replacing the Architect's stubs with complete, tested code.

**`grunnr/config.py`** — `HereticConfig` dataclass with full nested hierarchy matching LAYER_INTERFACES.md True Name keys: `bifrost:`, `rodd:`, `sjon:`, `vebond:`, `skilningr:`. Config loading from `heretic.yaml` (with `$HERETIC_CONFIG` override), env-var expansion, version compatibility check, YAML merge with defaults. `max_tokens: 127000` per RULES.AI.md.

**`grunnr/lifecycle.py`** — `LifecycleManager` implementing the `_ALLOWED_TRANSITIONS` table matching CEREMONY.md §7. Observer hooks (sync and async). Thread-safe state transitions. Five public states: HVILD, KYNDING, TENGSL, SAMRAEDUR, SLOKNA. Implementation sub-states: READY, OPENING, RECOVERING, EXTINGUISHED, CONFIG_ERROR (internal only, per CEREMONY.md §8).

**`grunnr/logger.py`** — `get_logger()` factory with configurable level, format, no `print()` anywhere in non-CLI modules.

**`grunnr/paths.py`** — `HereticPaths` providing all canonical runtime paths (config dir, log dir, data dir, package root) via `Path.home()`, `os.environ.get("APPDATA")`, `sys.platform` — no hardcoded strings, fully location-agnostic across Windows / macOS / Linux.

Tests written alongside: `test_grunnr_config.py` (17 tests), `test_grunnr_lifecycle.py` (30 tests), `test_grunnr_paths.py` (24 tests).

---

### Forge Worker builds L1 Bifröst (`fb37f75`)

**`bifrost/client.py`** — `AbstractBifrostClient` ABC and `OpenAICompatClient` concrete implementation. `open()` + `close()` ceremony methods. `send_message()` → `AsyncIterator[str]` SSE streaming. `_build_payload()` always uses `tools` (never deprecated `functions`). `_run_capability_probe()` for `?streaming` and `?vision_in` detection. `_parse_sse_stream()` with buffer logic for partial JSON chunks.

**`bifrost/tailscale.py`** — `TailscaleDetector` with CGNAT range check, `is_tailscale_address()`, `resolve_endpoint()` → four permutations (Tailscale permissive/Tailscale active/non-Tailscale). Lazy caching of detection result.

**`bifrost/config_model.py`** — `BifrostConfig` dataclass matching LAYER_INTERFACES.md L1 section. (Note: the conscious dual-class pattern with `grunnr/config.py` — a deliberate architectural separation preserved by an explicit bridge in `cli.py`, acknowledged as N-3 in the subsequent audit.)

**`bifrost/errors.py`** — typed exception hierarchy: `BifrostError`, `BifrostConnectionError`, `BifrostAuthError`, `BifrostTimeoutError`.

Tests: `test_bifrost_client.py` (20 tests), `test_bifrost_tailscale.py` (17 tests).

---

### Forge Worker builds the CLI (`7cc08f3`)

**`cli.py`** — Four subcommands: `light` (open ceremony), `extinguish` (close ceremony), `status` (lifecycle + config summary), `version`. The bridge between Grunnr's config types and Bifröst's config types lives here — explicit field-by-field, avoiding cross-layer imports. `status` with missing config produces a human-readable error message naming the searched path and the recovery instruction.

Tests: `test_cli.py` (10 tests).

**Running total at this point: 118 tests passing.**

The body can now be installed: `pip install -e .[dev]`
The body can now be run: `py -3.11 -m heretic`
The body can now connect: `py -3.11 -m heretic light` (when `heretic.yaml` is configured with Pi-Hermes endpoint)

---

### Auditor: v0.1 First Communion audit (`a7315b2`)

Sólrún Hvítmynd (Auditor) ran the full closing audit. Scope: (1) verification that all v0.0 blockers/notables from the prior audit were resolved; (2) full code review of `src/heretic/grunnr/`, `src/heretic/bifrost/`, `src/heretic/cli.py`, and `tests/`.

**Verdict: PASS WITH CONCERNS** — 0 blockers, 0 serious findings, 4 notables (N-1 through N-4), 3 nits (X-1 through X-3).

**Prior audit blockers — all verified or resolved:**

| Prior ID | v0.1 verdict |
|---|---|
| A-1 (blocker) | PARTIAL — primary docs corrected; N-1/N-2 filed for two secondary doc residuals |
| A-2 (blocker) | VERIFIED — three-part `sense.*.*` format gone; two-part `<sense_id>.<action>` canonical throughout |
| A-3 (serious) | VERIFIED — CEREMONY.md §8 added, public-vs-sub-state disambiguation complete |
| A-4 (notable) | VERIFIED — Auga/Hlust/Tunga have L5.10–L5.12 designations, full contracts, layering notes |
| A-5 (notable) | PARTIAL — main process map corrected; config example's intermediate `senses:` key filed as X-1 |
| A-6 (nit) | RESOLVED — README "being drafted" line gone |
| F-1 (notable) | VERIFIED — all active absolute paths removed; DEVLOG historical entries acceptable |
| C-Q-C1, C-Q-C3, C-Q-C4 | VERIFIED |

**New findings from code review:**

| ID | Severity | Location | Nature |
|---|---|---|---|
| N-1 | Notable | `SENSE_CONTRACTS.md:185` | Residual `senses:` key in YAML example — should be `skilningr:` |
| N-2 | Notable | `MIMISBRUNNR.md:171` | Same residual `senses:` key |
| N-3 | Notable | `grunnr/config.py:71` + `bifrost/config_model.py:31` | Dual `BifrostConfig` types require manual field-sync discipline |
| N-4 | Notable | `CEREMONY.md:361` | §7 table omits `Tengsl → SLOKNA`, `Tengsl → READY`, `EXTINGUISHED → READY` exits the code correctly implements |
| X-1 | Nit | `SYSTEM_OVERVIEW.md:231` | Intermediate `senses:` key in config example |
| X-2 | Nit | `test_bifrost_client.py` | SSE partial-chunk buffer path has zero test coverage |
| X-3 | Nit | `LAYER_INTERFACES.md:134–136` | Capability flags `?streaming` and `?vision_in` described optimistically in code; not noted in interface contract |

The audit also verified: no absolute paths in source (`grunnr/paths.py` always uses `Path.home()` / `os.environ`), `max_tokens: 127000` enforced in payload, no deprecated `functions` key, no `print()` in non-CLI modules, no live network calls in tests, correct `tools` array construction, PEP 8 and type hints throughout.

*Cross-reference: `docs/audit/AUDIT_v0.1_FIRST_COMMUNION.md`*

---

### Post-audit cleanup — all four notables closed

Three roles worked in sequence to close every post-audit finding. No new code was added — only precise corrections.

**`f7e7cd1` — Cartographer** (Védis Eikleið): X-1 — removed the intermediate `senses:` key from `docs/cartography/SYSTEM_OVERVIEW.md:231`. Config example now reads `skilningr: filesystem: enabled: true` with no nesting layer between `skilningr:` and the sense ID. Consistent with `grunnr/config.py:SkilningrConfig`.

**`9b5110e` — Architect** (Rúnhild Svartdóttir): N-1, N-2, N-4, X-3 closed in one commit:
- N-1: `docs/architecture/SENSE_CONTRACTS.md:185` — `senses:` replaced with `skilningr:` throughout the §5.1 permissions example block
- N-2: `docs/MIMISBRUNNR.md:171` — `senses: library:` replaced with `skilningr: library:`
- N-4: `docs/architecture/CEREMONY.md:361` — §7 formal transition table updated to include `Tengsl → SLOKNA`, `Tengsl → READY`, `EXTINGUISHED → READY` with rationale notes
- X-3: `docs/architecture/LAYER_INTERFACES.md:134–136` — brief note added to L1 capability flags section explaining that `?streaming` is set optimistically after successful probe and `?vision_in` is taken from config rather than live-tested

**`147ad30` — Forge** (Eldra Járnsdóttir): N-3 and X-2 closed:
- N-3: A field-parity assertion test added — any future divergence between the two `BifrostConfig` classes will now fail the test suite loudly rather than silently degrading the bridge
- X-2: One new SSE test added exercising the partial-chunk buffer path — a JSON object split across two `aiter_lines()` yields now has explicit coverage

**Final test count: 121 passing** (118 at audit + 3 new — N-3 parity assertion + N-3 parity verification test + X-2 boundary split test).

---

### What was built this session — cumulative summary

| Layer | Modules | Tests |
|---|---|---|
| L0 Grunnr | `config.py`, `lifecycle.py`, `logger.py`, `paths.py` | 71 |
| L1 Bifröst | `client.py`, `config_model.py`, `tailscale.py`, `errors.py` | 37 |
| CLI | `cli.py` | 10 |
| Post-audit additions | N-3 parity + X-2 SSE boundary | 3 |
| **Total** | **9 modules** | **121** |

---

### What was documented this session (Wave 1 + Wave 2)

| Document | Action |
|---|---|
| `docs/PRIOR_BRANCHES_TRIAGE.md` | Created — verdicts for 4 `codex/*` remote branches |
| `docs/ROADMAP.md` | Absolute paths replaced (F-1 closed) |
| `docs/DEVLOG.md` | Opened; first entry written (v0.0 arc); this second entry written now |
| `src/heretic/` entire package | Scaffolded by Architect; implemented by Forge |
| `pyproject.toml`, `heretic.example.yaml` | Created by Architect |
| `docs/audit/AUDIT_v0.1_FIRST_COMMUNION.md` | Created by Auditor |
| `docs/cartography/SYSTEM_OVERVIEW.md:231` | X-1 corrected by Cartographer |
| `docs/architecture/SENSE_CONTRACTS.md:185` | N-1 corrected by Architect |
| `docs/MIMISBRUNNR.md:171` | N-2 corrected by Architect |
| `docs/architecture/CEREMONY.md:361` | N-4 corrected by Architect |
| `docs/architecture/LAYER_INTERFACES.md:134–136` | X-3 corrected by Architect |

---

### Current state

HERETIC v0.1 First Communion is shipped and audited. The body is installable, runnable, and connectable. It waits for Volmarr to configure `heretic.yaml` with Pi-Hermes credentials and run `heretic light`.

The next milestone on `docs/ROADMAP.md` is **v0.2 First Voice** — TTS channel through ChatterBox. ChatterBox already runs at `http://100.66.178.105:7851`; the Forge Worker needs to implement `grunnr/config.py:RoddTtsConfig` consumption and a basic TTS call in `src/heretic/rodd/`.

*Cross-reference: `docs/ROADMAP.md`, `TASK_HERETIC_v0.1_BOOTSTRAP.md`, `docs/audit/AUDIT_v0.1_FIRST_COMMUNION.md`*

---

*Entry written by Eirwyn Rúnblóm, Scribe for Vibe Coding, 2026-05-07.*
*The body is real. The candle is lit. The thread continues.*

---

## 2026-05-07 — The First Voice Arc: From Silence to Speech (v0.2 Shipped and Audited)

**Session type:** Full Mythic Engineering build session — all six roles active (third arc, same calendar day)
**Branch:** `development`
**Commits this session:** `926de2e` through `435dfa3` (12 commits, spanning Wave 0 setup through Wave 3 cleanup)
**Status at session end:** v0.2 First Voice **SHIPPED AND AUDITED** — 224 tests passing, 0 open findings (all 2 SERIOUS + 3 NOTABLE resolved in Wave 3)

---

### Preamble — where this arc began

The second entry closed with v0.1 First Communion shipped: L0 Grunnr and L1 Bifröst fully implemented, 121 tests passing, all audit findings closed. The body could connect. It could not yet speak. This arc gave it a voice.

Beginning point: HEAD `5189993` (Scribe's v0.1 close commit). ChatterBox TTS already live on Pi at `http://100.66.178.105:7851` — no new infrastructure required. The task was to reach it, chunk text into sentences, and bring sound from speakers.

---

### Task file opened; ChatterBox API probed (`926de2e`)

`TASK_HERETIC_v0.2_FIRST_VOICE.md` created at repo root before any implementation began. The task file recorded the live ChatterBox API contract from a real probe of the Pi endpoint: three variants available (`turbo`, `tts`, `multilingual`), full request schema with 10 fields, recommended defaults for streaming use (model: `turbo`, no voice prompt, temperature 0.8, sentence-boundary chunking at 80+ chars with last-boundary policy).

Architectural decisions locked in the task file:
- L2 substrate only in v0.2 (no L5 Skilningr MCP wrapping until v0.7)
- `sounddevice` library as primary audio backend, platform-fallback (`aplay`/`afplay`/`winsound`) as secondary, `NullPlaybackBackend` as tertiary
- Single in-flight request with sentence-boundary queuing
- Fault tolerance: fall back to text-only, never crash the ceremony

*Cross-reference: `TASK_HERETIC_v0.2_FIRST_VOICE.md §3–§4`*

---

### Wave 1 — Three roles in parallel

#### Skald: THE_FIRST_VOICE vision essay (`7d4c27f`)

Sigrún Ljósbrá (Skald) wrote `docs/vision/THE_FIRST_VOICE.md` — a philosophical and ceremonial account of what it means for a body to speak for the first time. The essay frames voice not as a feature but as a threshold: the moment the vessel becomes an interlocutor rather than a conduit. It pairs with `WHY_HERETIC.md` (why embodiment matters) and `CEREMONY_NARRATIVE.md` (what communion feels like). The Forge Worker holds this frame when implementing the timing and graceful-degradation behavior of Tunga.

#### Cartographer: voice flow + drift annotations (`ecb8507`)

Védis Eikleið (Cartographer) updated `docs/cartography/DATA_FLOW.md` with two additions:
- A complete new section §4.6 mapping the TTS path from agent streaming output → Tunga sentence chunker → ChatterBox HTTP synthesis → audio playback → speakers. Includes component diagram and timing notes for sentence-boundary policy.
- Drift annotations in §4.6.1 explicitly flagging that the `speed` parameter appears in config documentation but has no ChatterBox API counterpart. These annotations are cross-referenced from the code-side drift guard in `chatterbox.py` to create a living anchor between document and implementation.

The Cartographer also noted that `DATA_FLOW.md §4.6.4` still carried an abbreviated config table (6 keys) from the pre-probe planning phase, and that `§4.6.1` retains an inline code annotation referencing `rodd.tts.voice_id`. Both items were deferred — Cartographer territory, not Forge territory. They are recorded in the v0.2.x backlog below.

*Cross-reference: `docs/cartography/DATA_FLOW.md §4.6–§4.6.4`*

#### Architect: `src/heretic/rodd/` scaffold (`b7e978e`)

Rúnhild Svartdóttir (Architect) built the L2 Rödd Tunga subpackage skeleton — boundaries first, implementation later:

| File | What was locked |
|---|---|
| `rodd/__init__.py` | Package root; version re-export |
| `rodd/config_model.py` | `RoddConfig`, `RoddTtsConfig` (17 fields), `RoddSttConfig` — full synthesis parameter set, including `temperature`, `exaggeration`, `cfg_weight`, `chunk_min_chars`, `sentence_terminators` |
| `rodd/errors.py` | `RoddError` hierarchy: `ChatterboxError`, `ChatterboxConnectionError`, `ChatterboxTimeoutError`, `ChatterboxAuthError`, `ChatterboxApiError`, `PlaybackError`, `PlaybackBackendUnavailableError`, `TungaConfigError` |
| `rodd/chatterbox.py` | Abstract base + skip-marked method stubs |
| `rodd/playback.py` | `AudioPlaybackBackend` ABC; `best_available()` factory stub |
| `rodd/tunga.py` | `Tunga` orchestrator stub |
| `rodd/INTERFACE.md` | Per-module contracts, invariants, config key semantics |

The Architect's scaffold contained no business logic — only type contracts, abstract shapes, and the module topology that Forge would inhabit.

---

### Wave 2 — Forge implements, then Auditor scrutinizes

#### Forge: ChatterboxClient and playback backends (`d4fd532`)

Eldra Járnsdóttir (Forge Worker) built the two lower-layer modules:

**`chatterbox.py`** — `ChatterboxClient` implementing the live API contract precisely. `_build_request_body()` sends all 10 contract fields; `speed` is accepted in config but intentionally excluded from the request body with a debug-log guard and explicit `DATA_FLOW.md §4.6.1` drift annotation. Voice field omitted when `"default"` or empty. `language_id` excluded when `"en"` (English is ChatterBox's default). Full error mapping: `httpx.ConnectError` → `ChatterboxConnectionError`, `httpx.TimeoutException` → `ChatterboxTimeoutError`, HTTP 401/403 → `ChatterboxAuthError`, any other status → `ChatterboxApiError`, wrong `Content-Type` on 200 → `ChatterboxApiError`.

**`playback.py`** — Three backends chained by `best_available()`:
1. `SoundDeviceBackend` — `sounddevice` library, async-safe via `run_in_executor`, `blocking=True` inside the executor thread
2. `PlatformFallbackBackend` — `winsound` (Windows), `afplay` (macOS), `aplay`/`paplay`/`play` (Linux), each via `subprocess.run` with temp WAV file
3. `NullPlaybackBackend` — always available, logs and silently drops audio

`available()` on each backend checks `ImportError` + device discovery before claiming readiness.

Tests for this commit: `test_rodd_chatterbox.py` + `test_rodd_playback.py` covering HTTP contract, error mapping, voice field omission, platform dispatch, and backend selection order.

#### Forge: Tunga orchestrator + CLI wiring (`077bd9a`, `e4a5232`)

**`tunga.py`** — `Tunga` orchestrator managing the full stream-to-speech pipeline:
- `feed_chunk(text)` accumulates agent streaming output in a buffer
- Sentence-boundary detection uses `rfind()` (last boundary) against configurable `sentence_terminators`; fires only when buffer exceeds `chunk_min_chars`
- `flush()` speaks remaining buffer regardless of length (for end-of-turn)
- `_speak_chunk()` calls `chatterbox.synthesize()` + `playback.play()` inside an asyncio lock; consecutive synthesis failures increment a counter; at `_MAX_CONSECUTIVE_FAILURES` (3), Tunga self-degrades to silent text-only mode
- `open()` / `close()` mirror the ceremony lifecycle; ChatterBox unreachable at `open()` sets `_degraded = True` without raising

**CLI wiring** — `cli.py` `_async_light` extended: Tunga instantiated at TENGSL (after lifecycle binding), `feed_chunk` called inside the SAMRAEDUR turn streaming loop, `flush` called after each turn, `close` called at SLOKNA. All three call sites wrapped in `try/except Exception` — voice failures never propagate to lifecycle.

`test_cli_voice.py` added (3 integration tests).

**Test count at Wave 2 close: 221 passing** (+100 new tests since v0.1).

*Cross-reference: `src/heretic/rodd/tunga.py`, `src/heretic/cli.py`*

---

### Wave 2.5 — Audit: PASS WITH CONCERNS (`59414d8`)

Sólrún Hvítmynd (Auditor) ran a full review. All 10 internal consistency claims verified (A-1 through A-9: request fields, voice omission, speed drift, endpoint paths, error mapping, chunking, lifecycle integration, fault tolerance, config validation timing). All four playback backend claims verified (B-1 through B-4). All four fault-tolerance claims verified (C-1 through C-4).

**Verdict: PASS WITH CONCERNS** — 0 blockers. The body speaks.

**2 SERIOUS findings:**

| ID | Location | Finding |
|---|---|---|
| S-1 | `grunnr/config.py:126–133` | Grunnr's `RoddTtsConfig` stub had 6 fields; rodd's canonical `RoddTtsConfig` had 17. `_merge_dict_into_dataclass` silently dropped 11 fields (`temperature`, `model`, `exaggeration`, `cfg_weight`, `top_p`, `repetition_penalty`, `language_id`, `voice_prompt_path`, `chunk_min_chars`, `sentence_terminators`, `request_timeout_seconds`) from `heretic.yaml`. Operators could not tune synthesis from config. |
| S-2 | `pyproject.toml [voice]`, `playback.py:179` | `numpy` imported inside `SoundDeviceBackend.play()` but absent from `[voice]` extra. `available()` imported only `sounddevice` — returned `True` even when numpy absent. First audio chunk raised `ImportError` at runtime rather than degrading gracefully at Kynding. Violated the construction-time degradation invariant. |

**3 NOTABLE findings:**

| ID | Finding |
|---|---|
| N-1 | `tunga.py:336` — `asyncio.get_event_loop()` deprecated in Python 3.10+; should be `asyncio.get_running_loop()` |
| N-2 | `chatterbox.py:255` — `language_id` excluded for "en" silently, undocumented in `INTERFACE.md`, no test for non-"en" path |
| N-3 | `INTERFACE.md:120` — `voice_id: "default"` shown without prose explaining the WAV file path contract for non-default values |

**3 NIT findings (X-1 through X-3):** Pi Tailscale IP as dataclass default, thin CLI integration tests, missing 403 coverage.

**1 DRIFT/BACKLOG item (G-1):** `LAYER_INTERFACES.md §L2` still showed the pre-probe 6-key `tts:` stub — deferred to Architect corrective pass.

*Cross-reference: `docs/audit/AUDIT_v0.2_FIRST_VOICE.md`*

---

### Wave 3 — Cleanup: all findings closed

Three roles resolved every open finding.

#### Forge: S-1 + S-2 + N-1 resolved (`03dbbea`, `4aebd98`, `bf77abe`, `435dfa3`)

- **S-1 (Approach B):** Grunnr `RoddTtsConfig` expanded to include all 17 fields matching rodd's canonical config model. Field parity now enforced by a parity test that fails loudly on any future divergence. (Approach B — expand the stub — preferred over routing YAML directly through the rodd config_model, to preserve the Grunnr config hierarchy's single-source-of-truth role.)
- **S-2:** `numpy` probe added inside `SoundDeviceBackend.available()`. The probe now imports both `sounddevice` and `numpy`; if either import fails, `available()` returns `False` and the backend selection falls through to `PlatformFallbackBackend`. Degradation now occurs at Kynding, not at first audio chunk. `numpy>=1.21` also added to the `[voice]` extra.
- **N-1:** `asyncio.get_event_loop()` replaced with `asyncio.get_running_loop()` in both `tunga.py:336` and in the corresponding CLI turn-loop path in `cli.py`. Test patching realigned to match (`435dfa3`).

#### Architect: G-1 + N-2 + N-3 resolved (`fee6816`)

- **G-1:** `docs/architecture/LAYER_INTERFACES.md §L2` rewritten to reflect the full 17-field `RoddTtsConfig` schema. Legacy 6-key `tts:` stub replaced. `speed: 1.0` annotated with the drift note: "present in config for legacy compatibility; not sent to ChatterBox (no API support — see `DATA_FLOW.md §4.6.1`)".
- **N-2:** `src/heretic/rodd/INTERFACE.md §Config Keys` updated with a note explaining that `language_id: "en"` is excluded from the request body as ChatterBox's default is English, and that non-"en" values are sent through for the multilingual model. A test for the non-"en" inclusion path added.
- **N-3:** `INTERFACE.md §Config Keys` updated with prose explaining that `voice_id` is a WAV file path (≥5s for the turbo model) interpreted as a voice-cloning prompt; "default" or empty omits the field entirely.

**Final test count: 224 passing** (+3 new wave-3 tests: parity verification, numpy probe check, non-"en" language_id inclusion).

---

### What was built this session — cumulative summary

| Layer | New modules | New tests |
|---|---|---|
| L2 Rödd (Tunga) | `rodd/__init__.py`, `rodd/config_model.py`, `rodd/errors.py`, `rodd/chatterbox.py`, `rodd/playback.py`, `rodd/tunga.py`, `rodd/INTERFACE.md` | 100 (Wave 2) |
| CLI (voice integration) | `cli.py` extended | 3 (Wave 2) |
| Wave 3 cleanup | S-1 parity, S-2 numpy probe, N-1 loop fix | 3 |
| **Total new** | **7 modules + 1 extended** | **+103** |
| **Running total** | **16 modules** | **224** |

---

### What was documented this session

| Document | Action |
|---|---|
| `TASK_HERETIC_v0.2_FIRST_VOICE.md` | Created — full task scope, ChatterBox API contract, wave plan |
| `docs/vision/THE_FIRST_VOICE.md` | Created — Skald's vision essay on the first voice |
| `docs/cartography/DATA_FLOW.md` | Extended — §4.6 voice flow + §4.6.1 drift annotations |
| `src/heretic/rodd/INTERFACE.md` | Created — module contracts, invariants, WAV path semantics (N-2/N-3 updated post-audit) |
| `docs/audit/AUDIT_v0.2_FIRST_VOICE.md` | Created — PASS WITH CONCERNS verdict; 0 blockers, 2 S, 3 N, 3 X |
| `docs/architecture/LAYER_INTERFACES.md §L2` | Updated — full 17-field schema, speed annotation (G-1 resolved) |

---

### Open v0.2.x backlog (Cartographer territory — not fixed in this pass)

Per the Architect's wave-3 closing note and the Cartographer's own annotations, two alignment items remain for the next Cartographer pass:

| Item | Location | What needs doing |
|---|---|---|
| §4.6.4 config table | `DATA_FLOW.md §4.6.4` | Abbreviated 6-key table predates the probe; should reflect the full 17-field `RoddTtsConfig` schema now canonical in `LAYER_INTERFACES.md §L2` |
| §4.6.1 inline annotation | `DATA_FLOW.md §4.6.1` | Inline code annotation still references `rodd.tts.voice_id`; should be `rodd.tts.voice_prompt_path` per the corrected field name in Wave 3 |

Both are minor alignment items. Neither affects running code. A future Cartographer pass (v0.2.x maintenance) resolves them. They are preserved here so the thread is not lost.

---

### Current state

HERETIC v0.2 First Voice is shipped and audited. The body can now connect (L1 Bifröst) and speak (L2 Rödd Tunga). ChatterBox on the Pi receives text, returns WAV, and sound reaches the laptop speakers during a live `heretic light` ceremony. 224 tests pass. 0 open findings.

The next milestone on `docs/ROADMAP.md` is **v0.3 First Listening** — STT via Whisper.cpp, completing the full L2 Rödd voice layer: ears to match the mouth. The Tunga pattern (chunked streaming, graceful degradation, lifecycle-bound open/close) will serve as the template for Hlust (the listening sense).

*Cross-reference: `docs/ROADMAP.md`, `TASK_HERETIC_v0.2_FIRST_VOICE.md`, `docs/audit/AUDIT_v0.2_FIRST_VOICE.md`*

---

*Entry written by Eirwyn Rúnblóm, Scribe for Vibe Coding, 2026-05-07.*
*The body speaks now. The voice was kept. The thread holds for what listens next.*

---

## 2026-05-07 — The First Listening Arc: Ears to Match the Mouth (v0.3 Shipped and Audited)

**Session type:** Full Mythic Engineering build session — all six roles active (fourth arc, same calendar day)
**Branch:** `development`
**Commits this session:** `c446023` through `cf8dad1` (10 commits, spanning task open through Wave 3 cleanup)
**Status at session end:** v0.3 First Listening **SHIPPED AND AUDITED** — 339 tests passing, 0 open findings (D-5/N-1/N-2 resolved in Wave 3; H-1 resolved in Architect cleanup pass)

---

### Preamble — where this arc began

The third entry closed with v0.2 First Voice shipped: L2 Rödd Tunga gave the body a mouth — text became speech via ChatterBox on the Pi, sound reached the laptop speakers. What remained was the other half of L2: ears. Hlust, the listening sense, would complete the voice faculty and make Samræður (communion) genuinely bidirectional as the `BODY_MANIFESTO.md` envisioned.

Beginning point: HEAD `f9c58cd` (Scribe's v0.2 close commit). 224 tests passing. `RoddSttConfig` already declared in `rodd/config_model.py` from the v0.2 pass — the shape was there; the organs were not.

The v0.3 task brief also carried one important design pivot: the prior planning material had assumed **ChatterBox** as the STT backend, but ChatterBox is a TTS system. The correct local STT solution is **Whisper.cpp** — MIT-licensed, runs fully on the laptop without a cloud call, wrappable via `pywhispercpp` Python bindings. This was recorded in the task file before any code was written.

---

### Task file opened; STT design locked (`c446023`)

`TASK_HERETIC_v0.3_FIRST_LISTENING.md` created at repo root. The task file established the three-layer substrate architecture (microphone → VAD → Whisper engine), the preferred backend chain for each layer, the CLI integration model, the lazy-load contract (sealed in the v0.0 audit as C-Q-C1), and the fault-tolerance invariant: if any substrate layer is unavailable, the ceremony falls back to stdin rather than crashing.

Key architectural decisions locked:
- Whisper integration: `pywhispercpp` primary (MIT, Python bindings); CLI subprocess fallback; `NullWhisperBackend` as last resort
- VAD: `webrtcvad-wheels` primary (BSD-3, 30ms frames, 16kHz PCM); energy-threshold pure-Python fallback
- Microphone: reuse `sounddevice` already in `[voice]` extra from v0.2; capture at 16kHz mono int16
- Model loading: lazy — load on first utterance, not at Kynding; honours v0.0 audit sealed decision
- CLI: gate Hlust behind `stt.enabled`, `is_available`, and `isatty()` checks; fall back to stdin on failure

*Cross-reference: `TASK_HERETIC_v0.3_FIRST_LISTENING.md §3–§7`*

---

### Wave 1 — Three roles in parallel

#### Skald: THE_FIRST_LISTENING vision essay (`0ad4672`)

Sigrún Ljósbrá (Skald) wrote `docs/vision/THE_FIRST_LISTENING.md` — the fourth panel of the vision cycle (following `WHY_HERETIC.md`, `CEREMONY_NARRATIVE.md`, `THE_FIRST_VOICE.md`). The essay frames hearing not as a technical capability but as a threshold: the moment the body becomes not merely a speaker but an interlocutor, able to receive the world as well as address it. The Tunga-Hlust dyad is now named and framed as a single sense faculty split across two milestones; together they constitute Samræður as the manifesto intended.

#### Cartographer: listening flow mapped + v0.2.x backlog cleared (`26030f7`)

Védis Eikleið (Cartographer) updated `docs/cartography/DATA_FLOW.md` with two major additions and two backlog closures:

**New:** §4.7 — complete mapping of the inbound voice path: microphone frames → 30ms VAD windows → utterance buffer → Whisper transcription → Bifröst send. Includes the `vad_threshold` impedance mismatch flag: HERETIC config exposes a float (0.0–1.0) but `webrtcvad` expects an integer aggressiveness level (0–3). The Cartographer recorded this mismatch and its resolution formula (`aggressiveness = max(0, min(3, round(vad_threshold * 3)))`) in §4.7.5, with an explicit note that the Forge Worker must implement and document the mapping.

**New:** §12 (Hlust) — component diagram for the L2 Rödd Hlust subpackage.

**Closed from v0.2.x backlog:**
- `DATA_FLOW.md §4.6.4` — abbreviated 6-key config table expanded to the full 17-field `RoddTtsConfig` schema per the corrected `LAYER_INTERFACES.md §L2`
- `DATA_FLOW.md §4.6.1` — inline annotation corrected from `rodd.tts.voice_id` to `rodd.tts.voice_prompt_path`

*Cross-reference: `docs/cartography/DATA_FLOW.md §4.7, §4.7.5, §12`*

#### Architect: Hlust module scaffold + INTERFACE.md + 53 skip-marked tests (`0422a44`)

Rúnhild Svartdóttir (Architect) built the four new module skeletons and updated `rodd/INTERFACE.md §Hlust` with contracts, invariants, the lazy-load policy, the frame format invariant (SAMPLE_RATE=16000, CHANNELS=1, dtype=int16, FRAME_MS=30, FRAME_SAMPLES=480, FRAME_BYTES=960), and the threading bridge pattern (`loop.call_soon_threadsafe()` exclusively). No business logic — only abstract shapes, type contracts, and domain boundaries.

`pyproject.toml [voice]` extra extended with `pywhispercpp>=1.0` and `webrtcvad-wheels>=2.0`.

---

### Wave 2 — Forge implements

#### Forge: microphone + VAD + Whisper substrate engines (`95439a1`)

Eldra Járnsdóttir (Forge Worker) built the three substrate layers:

**`microphone.py`** — Frame format constants locked here (`SAMPLE_RATE`, `CHANNELS`, `dtype`, `FRAME_MS`, `FRAME_SAMPLES`, `FRAME_BYTES`); imported (not redefined) by `vad.py` and `whisper_engine.py`. `SoundDeviceMicBackend` probes `sd.query_devices()` for input channels before claiming availability. `NullMicBackend` always returns `available() = False`.

**`vad.py`** — `WebRtcVadBackend` with the `vad_threshold` impedance mismatch fully resolved: `aggressiveness = max(0, min(3, round(vad_threshold * 3)))`. The mapping is documented in the module docstring, in `vad.py:26–34`, and in `INTERFACE.md §Config Keys`. `EnergyThresholdBackend` as pure-Python fallback. `NullVadBackend` does not disable Hlust — fixed-window capture is used instead.

**`whisper_engine.py`** — `PyWhisperCppBackend` with lazy model loading (`_loaded = False` at construction; `load_model()` deferred to `_ensure_model_loaded()` on first call). `CliSubprocessBackend` using `shutil.which("whisper-cli")` for cross-platform discovery; Windows-safe temp WAV handling via `NamedTemporaryFile(delete=False)` + manual `unlink`. `NullWhisperBackend`.

#### Forge: Hlust orchestrator (`9648ca8`)

**`hlust.py`** — `Hlust` orchestrator managing the full pipeline:
- PortAudio callback bridges to asyncio via `loop.call_soon_threadsafe(frame_queue.put_nowait, pcm_bytes)` — no asyncio primitives touched from the C thread
- `_capture_loop()` accumulates 30ms frames from the mic queue; VAD detects utterance end; 30-second hard cap (`_MAX_UTTERANCE_FRAMES = 1000`); 5-second per-frame timeout
- `_ensure_model_loaded()` called on first utterance (lazy contract honoured); `open()` calls it only for eager strategy
- Null component check: `NullMicBackend` or `NullWhisperBackend` → `self._available = False`; `NullVadBackend` → Hlust remains available, fixed-window capture used
- `capture_one_utterance()` outer `except Exception` returns `""` and logs — ceremony never crashes

#### Forge: CLI wiring + listening tests (`ab7c466`)

`cli.py` extended: Hlust construction behind `if grunnr_stt.enabled:`; `try/except Exception` on init with `hlust = None` on failure; `await hlust.open()` at TENGSL; turn loop replaces `sys.stdin.readline` with `await hlust.capture_one_utterance()` when `hlust is not None and hlust.is_available and sys.stdin.isatty()`; inner `try/except` falls back to stdin on any capture exception; `await hlust.close()` at Slokna before Tunga.

Five new test files: `test_rodd_microphone.py`, `test_rodd_vad.py`, `test_rodd_whisper.py`, `test_rodd_hlust.py`, `test_cli_listen.py`.

**Test count at Wave 2 close: 336 passing** (+112 new tests since v0.2).

---

### Wave 2.5 — Audit: PASS WITH CONCERNS (`c938f0e`)

Sólrún Hvítmynd (Auditor) ran a full review across all new source, test, and documentation files.

**Verdict: PASS WITH CONCERNS** — 0 blockers. 30 internal consistency claims verified (A-1 through F-7).

Key verifications:
- VAD aggressiveness mapping: correct in code, documented, tested at 10 boundary values (A-1)
- Frame format constants: locked in `microphone.py`, imported by `vad.py` (A-2)
- Lazy model load: no `load_model()` at `__init__` or `open()` (lazy path) — A-3
- Threading bridge: `loop.call_soon_threadsafe()` exclusively — A-4
- Null backend semantics: `NullVadBackend` does not disable Hlust — A-5
- Hard caps: 30s utterance cap + 5s frame timeout — A-6
- Cross-platform: `shutil.which`, Windows-safe temp WAV, `available()` probes — C-1 through C-4
- Fault tolerance: three independent fallback layers in CLI — B-3

**1 SERIOUS finding:**

| ID | Location | Finding |
|---|---|---|
| D-5 | `hlust.py:283–285` | WhisperModelLoadError does not set a permanent disable flag; `_model_loaded` remains `False` on failure; subsequent utterances retry `load_model()` on every turn, producing repeated `[loading model...]` cues and spurious error logs rather than a clean single-failure-then-silence behaviour |

**3 NOTABLE findings:**

| ID | Finding |
|---|---|
| N-1 | `vad_threshold=0.1667` (boundary: `0.1667*3=0.5001→1`) not in the 10 parametrized test cases; mapping is correct but this edge is near banker's rounding territory |
| N-2 | Three `print()` calls in `hlust.py:284,291,363` — library module bypassing logging infrastructure; future non-CLI callers (Tauri GUI, MCP adapter) will emit unexpected stderr output |
| H-1 | `AGENT_AGNOSTIC_PROTOCOL.md §5.2` lists `?tool_use`, `?vision_in`, `?streaming` but has no `?voice_in` flag; drift between INTERFACE.md (flag declared) and the agent-facing protocol document (flag absent) |

*Cross-reference: `docs/audit/AUDIT_v0.3_FIRST_LISTENING.md`*

---

### Wave 3 — Cleanup: all findings closed

#### Architect: H-1 resolved — `?voice_in` added to AGENT_AGNOSTIC_PROTOCOL.md (`4e50093`)

Rúnhild Svartdóttir closed the H-1 drift finding: `?voice_in` added to `AGENT_AGNOSTIC_PROTOCOL.md §5.2` with the condition `rodd.stt.enabled: true AND Hlust.is_available is True`. The Architect also added `?voice_out` for symmetry — this closed a consistency gap from v0.2 where Tunga (TTS output) had no corresponding capability flag in the agent protocol. Both flags are now present in the document the inhabiting agent reads to understand the body's capabilities.

#### Forge: D-5 + N-1 + N-2 resolved (`cf8dad1`)

- **D-5:** A `_model_load_failed` flag added inside `capture_one_utterance()`'s exception handler — when a `WhisperModelLoadError` is caught, the flag is set; all subsequent calls return `""` immediately without re-attempting `load_model()`. One clear failure, clean silence thereafter. The `[loading model...]` print path was also consolidated with this change.
- **N-1:** `vad_threshold=0.1667` added to the parametrized boundary test set; expected mapping `1` (since `0.1667 * 3 = 0.5001`, which rounds to `1` under both standard and banker's rounding). All 11 boundary cases now pass.
- **N-2:** The three `print()` calls in `hlust.py` replaced with `self._log.info()` structured logging. The CLI now emits its own user-facing status cues at the appropriate points in the turn loop rather than relying on library-layer prints. Future non-CLI callers can configure log level without receiving unexpected stderr output.

**Final test count: 339 passing** (+3 new wave-3 tests: `_model_load_failed` guard, `0.1667` boundary case, no further tests needed for N-2 as logging infrastructure was already tested).

---

### What was built this session — cumulative summary

| Layer | New modules | New tests |
|---|---|---|
| L2 Rödd (Hlust) | `rodd/microphone.py`, `rodd/vad.py`, `rodd/whisper_engine.py`, `rodd/hlust.py`, `rodd/errors.py` (Hlust additions) | 112 (Wave 2) |
| CLI (listening integration) | `cli.py` extended | (included above) |
| Wave 3 cleanup | D-5 load-fail guard, N-1 boundary case | 3 |
| **Total new** | **4 new modules + 1 extended** | **+115** |
| **Running total** | **20 modules** | **339** |

---

### What was documented this session

| Document | Action |
|---|---|
| `TASK_HERETIC_v0.3_FIRST_LISTENING.md` | Created — full task scope, STT design choices, wave plan, Whisper/VAD/mic architecture |
| `docs/vision/THE_FIRST_LISTENING.md` | Created — Skald's vision essay; fourth panel of vision cycle |
| `docs/cartography/DATA_FLOW.md` | Extended — §4.7 inbound voice flow + §12 Hlust diagram; v0.2.x backlog cleared |
| `src/heretic/rodd/INTERFACE.md` | Extended — §Hlust: contracts, invariants, frame format, lazy-load policy, threading bridge |
| `docs/audit/AUDIT_v0.3_FIRST_LISTENING.md` | Created — PASS WITH CONCERNS; 0 blockers, 1 SERIOUS, 3 NOTABLE (all resolved) |
| `docs/architecture/AGENT_AGNOSTIC_PROTOCOL.md §5.2` | Extended — `?voice_in` and `?voice_out` flags added (H-1 resolved; `?voice_out` v0.2 gap closed) |

---

### What is now fully resolved

The v0.2.x backlog that the Cartographer carried forward is now closed. The H-1 drift between INTERFACE.md's declared `?voice_in` flag and AGENT_AGNOSTIC_PROTOCOL.md is resolved. No items carry forward from v0.3 as open backlog — the wave-3 cleanup was complete.

The `?voice_out` symmetry addition deserves a note: the Architect observed during the H-1 fix that Tunga (TTS, shipped in v0.2) also had no capability flag in the agent protocol. This was a v0.2 consistency gap never caught by the v0.2 audit. It was silently mended during the v0.3 cleanup wave — not a new finding, but a thread that had been loose since v0.2 and is now bound.

---

### Current state

HERETIC v0.3 First Listening is shipped and audited. The body can now connect (L1 Bifröst), speak (L2 Rödd Tunga), and listen (L2 Rödd Hlust). Samræður is two-directional as the manifesto required. 339 tests pass. 0 open findings. The whole of L2 Rödd is implemented.

The next milestone on `docs/ROADMAP.md` is **v0.4 Summoning Circle** — the Tauri + React UI shell (L4 Vébond): the visual ceremony control surface, the light-the-candle and extinguish ceremony interface, the Norse aesthetic as described in `docs/vision/AESTHETIC.md` and embodied in `docs/vision/CEREMONY_NARRATIVE.md`. The body has its inner voice; now it needs its visible face.

*Cross-reference: `docs/ROADMAP.md`, `TASK_HERETIC_v0.3_FIRST_LISTENING.md`, `docs/audit/AUDIT_v0.3_FIRST_LISTENING.md`*

---

*Entry written by Eirwyn Rúnblóm, Scribe for Vibe Coding, 2026-05-07.*
*The body hears now. Both halves of the voice are kept. The thread holds for the face that comes next.*
