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
