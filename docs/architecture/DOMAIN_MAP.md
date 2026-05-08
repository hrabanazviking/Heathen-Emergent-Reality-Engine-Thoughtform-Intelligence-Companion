# HERETIC — Domain Map

**Last updated:** 2026-05-07 (corrective pass — Rúnhild Svartdóttir, removing absolute path references)
**Scope:** Folder-level ownership, boundary statements, cross-domain dependency graph (must remain acyclic), extension rules.
**Authority:** Derives from `ARCHITECTURE.md` and `docs/BODY_MANIFESTO.md`.
**Owner:** Architect (Rúnhild Svartdóttir)
**Legend:** True Names from `docs/NAMING.md` appear first; code-facing identifiers in parentheses on first use per domain.

---

## 1. Top-Level Folder Map

```
HERETIC/
│
├── heretic/                   ← Source root — all runtime code
│   ├── foundation/            ← L0 Grunnr — config, logging, process supervisor
│   ├── bifrost/               ← L1 Bifröst — agent client, connection lifecycle
│   ├── voice/                 ← L2 Rödd — STT/TTS bridges (Hlust + Tunga)
│   ├── vision/                ← L3 Sjón — screen capture
│   ├── ui/                    ← L4 Vébond — Tauri React frontend (Eldahús)
│   └── sense_hub/             ← L5 Skilningr — MCP router + per-sense servers
│       ├── filesystem/        ← L5.1 Minni (minni)
│       ├── terminal/          ← L5.2 Skepja (skepja)
│       ├── browser/           ← L5.3 Leið (leid)
│       ├── photopea/          ← L5.4 Hönd (hond)
│       ├── blender/           ← L5.5 Smiðja (smidja) — wraps Seidr-Smidja Brúarhönd
│       ├── vrchat/            ← L5.6 Líkami (likami)
│       ├── agentmail/         ← L5.7 Boð (bod)
│       ├── custom/            ← L5.8 Nýr Limr (nyr_limr) — plugin slot
│       └── library/           ← L5.9 Mímisbrunnr (mimisbrunnr)
│           └── mimisbrunnr/   ← offline library subsystem (spec: docs/MIMISBRUNNR.md)
│
├── vendor/                    ← Plundered permissive-licensed code (MIT/Apache)
│   └── <project-name>/        ← One subdirectory per source; original headers preserved
│
├── config/                    ← heretic.yaml template + JSON Schema + config docs
│
├── docs/                      ← All documentation
│   ├── BODY_MANIFESTO.md      ← Canonical sealed vision — DO NOT EDIT
│   ├── MIMISBRUNNR.md         ← Library subsystem spec — DO NOT EDIT
│   ├── NAMING.md              ← True Names — DO NOT EDIT
│   ├── PRIOR_PLANNING_TRIAGE.md ← Triage record — DO NOT EDIT
│   ├── architecture/          ← THIS directory — Architect's domain
│   ├── vision/                ← Skald's domain — DO NOT EDIT from here
│   ├── cartography/           ← Cartographer's domain
│   └── plunder/               ← Scribe's domain — plunder maps and adaptation logs
│
├── tests/                     ← Test suite, mirrors heretic/ structure
│
├── scripts/                   ← Build, CI, release scripts
│
├── data/                      ← Norse cultural/lore data — seed corpus for Mímisbrunnr
│
├── THIRD_PARTY_NOTICES.md     ← Scribe's domain — all attribution notices
├── TASK_HERETIC_v0.1_BOOTSTRAP.md  ← Session-resume task file
├── RULES.AI.md                ← Volmarr's law — all agents honor this
├── LICENSE                    ← MIT
└── README.md                  ← Scribe's domain
```

---

## 2. Domain Ownership Declarations

Each domain is described by: what it owns, what it depends on, and what it must never know about. The boundary statement after each declaration is the one-line invariant: what it protects, what it keeps out, what it makes replaceable.

---

### Domain: L0 Grunnr (`heretic/foundation/`)

**True Name:** Grunnr (grunnr) — the foundation, the ground everything stands on.

**Owns:**
- Loading and parsing `heretic.yaml` into typed `Config` struct (the `foundation::config()` accessor)
- Structured logging initialization (log level, log destination, rotation)
- Tauri subprocess supervisor (spawn, restart-on-crash per `restart_policy`, clean shutdown)
- Crash guard / panic handler — ensures clean subprocess teardown on unrecoverable error
- Version introspection (HERETIC version, layer API versions)

**Depends on:**
- `heretic.yaml` file path (resolved from `$HERETIC_CONFIG` → XDG config dir → home dir — in that priority order; never hardcoded)
- Tauri runtime APIs

**Must never know about:**
- Agent conversation content
- Voice audio data
- Screen frame data
- MCP tool schemas or results
- Any sense's internal logic

**Boundary statement:** Grunnr is the silent ground. It exposes typed configuration to all layers and owns the process lifecycle. Replacing the config format or log backend affects only this domain.

---

### Domain: L1 Bifröst (`heretic/bifrost/`)

**True Name:** Bifröst (bifrost) — the shimmering bridge between the local body and the remote spirit.

**Owns:**
- Agent endpoint URL (read from L0 `Config`)
- Bearer token management (load, validate, rotate per policy in config; env var reference only — never plaintext in YAML)
- Tailscale-aware endpoint resolution (tries Tailscale mesh first; falls back to direct HTTPS if configured)
- HTTP client for `/v1/chat/completions` (streaming and non-streaming)
- Agent connection state machine: DISCONNECTED → CONNECTING → CONNECTED → RECOVERING → ERROR → DISCONNECTED
- Message queue: outbound (body → spirit) and inbound (spirit → body) buffers
- Heartbeat / keepalive loop
- Graceful close protocol on ceremony extinguish (Slokna)
- Reconnect policy (exponential backoff, max-retry config)
- Tool call dispatch: receives `tool_use` from agent, routes to L5; receives result from L5, returns to agent

**Depends on:**
- L0 Grunnr (config: endpoint URL, token, Tailscale options, timeout values)
- L5 Skilningr (tool schema list for capability injection; tool call routing)
- L2 Rödd (receives `voice::transcript` events; injects as user-role messages)
- L3 Sjón (receives `vision::frame` events; injects as image-role content when vision-in enabled)

**Must never know about:**
- Agent's memory, persona, or system prompt contents
- What any MCP tool actually does internally
- Audio DSP, VAD, or device management
- UI rendering logic

**Boundary statement:** Bifröst is the one and only seam between body and spirit. All traffic between them passes through here. Replacing the agent protocol or auth mechanism affects only this domain.

---

### Domain: L2 Rödd (`heretic/voice/`)

**True Name:** Rödd (rodd) — voice; the complete faculty of speaking and hearing.
Sub-faculties: Hlust (hlust) for hearing (STT), Tunga (tunga) for speaking (TTS).

**Owns:**
- Microphone device enumeration and selection
- Audio capture loop + VAD (Voice Activity Detection) for turn segmentation
- Whisper.cpp subprocess management (Hlust — spawn, pass audio, receive transcript)
- Transcript event emission: `voice::transcript(text, timestamp, confidence)`
- ChatterBox TTS client (Tunga — HTTP calls to TTS server; receive audio stream)
- Speaker device selection and audio playback
- STT-enable / TTS-enable independent flags (both individually configurable via `heretic.yaml`)

**Depends on:**
- L0 Grunnr (config: mic device, speaker device, ChatterBox endpoint, Whisper model path, VAD threshold)
- OS audio API (CoreAudio / WASAPI / ALSA — abstracted via Tauri or cross-platform crate)
- ChatterBox TTS server (Tailscale endpoint or any OpenAI-compat TTS endpoint)

**Must never know about:**
- Agent conversation logic or content
- What the agent says or why
- MCP tools or results
- Screen capture data

**Boundary statement:** Rödd owns the voice channel in both directions. Replacing Whisper.cpp or ChatterBox affects only this domain. L1 Bifröst receives transcripts and speaks to Tunga; it does not manage audio.

---

### Domain: L3 Sjón (`heretic/vision/`)

**True Name:** Sjón (sjon) — sight; the faculty of perception through eyes.

**Owns:**
- Screen capture schedule (interval configurable in `heretic.yaml`)
- Platform-specific capture backend selection (DXGI / X11 / CoreGraphics)
- Resolution and crop-region configuration
- Optional webcam capture (independent of screen capture)
- Frame buffer (ring buffer, configurable depth)
- Frame emission: `vision::frame(base64_png, timestamp, source)`

**Depends on:**
- L0 Grunnr (config: capture interval, resolution, crop, webcam device, buffer depth)
- OS screen capture permission grant

**Must never know about:**
- What the agent does with frames
- Audio data
- MCP tools
- UI rendering

**Boundary statement:** Sjón captures and emits. It never interprets. Replacing the capture backend (e.g., swapping DXGI for a game capture library) affects only this domain.

---

### Domain: L4 Vébond (`heretic/ui/`)

**True Name:** Vébond (vebond) — the sacred enclosure. The UI shell is Eldahús (Fire-House).

**Owns:**
- Summoning Circle visual presentation (React components, Norse dark theme)
- Ceremony control buttons (Light the Candle / Extinguish)
- Layer status indicator panel (per-layer health, active/inactive state)
- Voice activity waveform display
- Sense enable/disable toggle panel
- Config surface (surface-level settings accessible without editing YAML directly)
- Error / warning toast notifications

**Depends on:**
- L0 Grunnr event bus (`heretic::lifecycle::*`, `heretic::ui::*` events)
- L1 Bifröst connection state events
- L2 Rödd voice activity events (for waveform)
- Tauri IPC bridge (frontend ↔ backend)

**Must never know about:**
- Agent conversation content
- MCP tool schemas or results
- Audio signal processing
- Screen capture data
- Network routing logic

**Boundary statement:** Vébond is the fire-room — the threshold where human and ceremony meet. It displays state; it never creates it. Replacing the React frontend with another web framework affects only this domain.

---

### Domain: L5 Skilningr (`heretic/sense_hub/`)

**True Name:** Skilningr (skilningr) — organized, discerning perception; the faculty that distinguishes one sense from another.

**Owns:**
- Sense subprocess registry (which senses are enabled, their process handles)
- MCP tool schema aggregation (collects tool definitions from all active senses)
- Tool call routing table (maps `tool_name` → responsible sense subprocess)
- Sense health monitoring (per-sense heartbeat via `tools/list` probe, restart policy)
- Inter-sense isolation (a crashed sense does not affect others)

**Depends on:**
- L0 Grunnr (config: which senses are enabled, per-sense config block)
- Each L5.x sense subprocess (via stdio MCP protocol)

**Must never know about:**
- Agent conversation context
- Voice/vision data streams
- UI rendering

**Boundary statement:** Skilningr is the hub that makes many senses appear as one surface. L1 Bifröst calls two functions; the rest is hidden. Adding or removing a sense affects only the registry and this domain.

---

### Domain: L5.1 Minni (`heretic/sense_hub/filesystem/`)

**True Name:** Minni (minni) — memory, the faculty of recollection; external memory in Midgard.

**Owns:** Sandboxed read/write access to user-configured allowed directories.
**Depends on:** L0 Grunnr (allowed paths, sandbox root), OS filesystem.
**Must never know about:** Agent conversation, other senses, voice/vision.
**Boundary statement:** Minni is the file accessor. It enforces path sandbox boundaries and nothing else.

---

### Domain: L5.2 Skepja (`heretic/sense_hub/terminal/`)

**True Name:** Skepja (skepja) — to shape, create; the act of making through direct action on the machine.

**Owns:** Sandboxed shell command execution within allowed working directories.
**Depends on:** L0 Grunnr (allowed dirs, shell, timeout, forbidden-command list), OS shell.
**Must never know about:** Other senses, agent persona, voice/vision.
**Boundary statement:** Skepja shapes the machine. It enforces dir and command-pattern boundaries; it never enforces agent policy.

---

### Domain: L5.3 Leið (`heretic/sense_hub/browser/`)

**True Name:** Leið (leid) — path, route; the navigator's knowledge of how to travel.

**Owns:** Browser automation (navigate, click, type, screenshot, DOM query).
**Depends on:** L0 Grunnr (browser binary, profile, allowed-domain list), Playwright or Puppeteer.
**Must never know about:** Other senses, voice/vision, agent conversation.
**Boundary statement:** Leið navigates. It does not interpret what it finds; that is the agent's work.

---

### Domain: L5.4 Hönd (`heretic/sense_hub/photopea/`)

**True Name:** Hönd (hond) — hand; touch and craft through hands; the mark-maker on surfaces.

**Owns:** Browser-automation wrapper targeting Photopea's JavaScript API.
**Depends on:** L5.3 Leið (Photopea is a web app; Hönd drives it via browser automation). This is the only inter-sense dependency permitted in the system, and it is a transport dependency only — not a business-logic dependency.
**Must never know about:** Other senses except Leið as transport, voice/vision.
**Boundary statement:** Hönd is the painter's hand. Replacing Photopea with another canvas app (self-hosted or different) affects only this domain's driver.

**Open question:** Photopea's automation surface (`app.echoToOE()` JavaScript API) needs verification against the current live version before L5.4 implementation begins. Audit required at v0.9 scope entry.

---

### Domain: L5.5 Smiðja (`heretic/sense_hub/blender/`)

**True Name:** Smiðja (smidja) — forge, smithy; the place of making three-dimensional form.

**Owns:** MCP wrapper around Seidr-Smidja Brúarhönd's 8 CLI subcommands + 3 MCP tools.
**Depends on:** L0 Grunnr (Brúarhönd daemon endpoint), Seidr-Smidja project (`github.com/hrabanazviking/Seidr-Smidja`) running as a separate process not managed by HERETIC.
**Must never know about:** Other senses, voice/vision, agent conversation logic.
**Boundary statement:** Smiðja delegates all execution to Brúarhönd. Upgrading Seidr-Smidja affects only this domain's delegation layer.

---

### Domain: L5.6 Líkami (`heretic/sense_hub/vrchat/`)

**True Name:** Líkami (likami) — body, physical form; the vessel of life in the world.

**Owns:** VRChat OSC / SDK integration for agent social embodiment.
**Depends on:** L0 Grunnr (VRChat OSC port, avatar ID), VRChat client installed.
**Must never know about:** Other senses, voice/vision.
**Boundary statement:** Líkami gives the spirit a social body. The underlying protocol (OSC vs SDK) is hidden behind this domain's MCP surface.

**Open question:** VRChat API surface for agent-driven avatar control (OSC vs SDK vs both) needs verification at v0.10 scope entry.

---

### Domain: L5.7 Boð (`heretic/sense_hub/agentmail/`)

**True Name:** Boð (bod) — message, announcement; the formal message sent between parties.

**Owns:** Email send/receive integration (SMTP + IMAP or provider API).
**Depends on:** L0 Grunnr (mail credentials via env vars, provider endpoint).
**Must never know about:** Other senses, voice/vision, agent memory.
**Boundary statement:** Boð is correspondence. Replacing the mail provider or protocol affects only this domain.

---

### Domain: L5.8 Nýr Limr (`heretic/sense_hub/custom/`)

**True Name:** Nýr Limr (nyr_limr) — new limb; the capacity to grow new branches.

**Owns:** Plugin slot — user-provided MCP server configurations loaded dynamically.
**Depends on:** L0 Grunnr (custom sense definitions, each with `command`, `args`, `env`).
**Must never know about:** Internal sense implementations; other senses' business logic.
**Boundary statement:** Nýr Limr is the extensibility seam. User-provided servers are black boxes to HERETIC. The system grows limbs without knowing what they are.

---

### Domain: L5.9 Mímisbrunnr (`heretic/sense_hub/library/`)

**True Name:** Mímisbrunnr (mimisbrunnr) — Mímir's Well; the well of wisdom the agent drinks from.

**Owns:** Unified library search across multiple backends (ZIM/vector, MindSpark, file-index). Full spec in `docs/MIMISBRUNNR.md`.
**Depends on:** L0 Grunnr (enabled backends, retrieval mode), Mímisbrunnr submodule (`library/mimisbrunnr/`), optional MindSpark HTTP endpoint.
**Must never know about:** Other senses, agent conversation, voice/vision.
**Boundary statement:** Mímisbrunnr is the bookshelf, not the agent's mind. What the spirit does with knowledge is the spirit's concern.

---

### Domain: `vendor/`

**Owns:** Copies of third-party code adapted under permissive licenses.
**Depends on:** Nothing in `heretic/` (dependency runs the other way).
**Must never:** Contain GPL/AGPL code; contain unattributed code; be modified without updating `THIRD_PARTY_NOTICES.md`.
**Boundary statement:** `vendor/` is plunder, lawfully taken and marked. No GPL crosses this threshold.

---

### Domain: `config/`

**Owns:** `heretic.yaml` template, JSON Schema for validation, and configuration documentation.
**Depends on:** Nothing at runtime.
**Must never:** Contain secrets, hardcoded endpoints, or user-specific values.

---

### Domain: `data/`

**Owns:** Norse cultural/lore JSON data — seed corpus for Mímisbrunnr's Norse starter pack.
**Depends on:** Nothing at runtime until L5.9 ingests it.
**Must never:** Contain user-generated data, session state, or agent memory.

---

## 3. Cross-Domain Dependency Graph

Arrows indicate "depends on." The graph must remain acyclic. Any proposed change that introduces a cycle is rejected.

```
                 ┌──────────────────────────────────┐
                 │     SPIRIT (external — abstracted) │
                 └────────────────┬─────────────────┘
                                  │ OpenAI-compat API (HTTPS/Tailscale)
                                  ▼
  ┌──────────────┐    ┌──────────────────────────────────────┐
  │  L4 Vébond  │◄───│            L1  Bifröst                │
  │  (ui events)│    └──────┬──────────────┬─────────────────┘
  └─────┬───────┘           │              │
        │                   ▼              ▼
        │             ┌──────────┐  ┌──────────────────────────┐
        │             │  L2 Rödd │  │   L5  Skilningr           │
        │             │  (voice) │  │   5.1 Minni               │
        │             └────┬─────┘  │   5.2 Skepja              │
        │                  │        │   5.3 Leið                │
        │                  │        │   5.4 Hönd ──► Leið       │
        │                  │        │   (transport only)        │
        │                  │        │   5.5 Smiðja              │
        │                  │        │   5.6 Líkami              │
        │                  │        │   5.7 Boð                 │
        │                  │        │   5.8 Nýr Limr            │
        │                  │        │   5.9 Mímisbrunnr         │
        │                  │        └──────────────────────┬────┘
        │                  │                               │
        │             ┌────┴───────────────────────────────┴────┐
        └────────────►│              L0  Grunnr                  │
                      │  (config, logging, process supervisor)   │
                      └─────────────────────────────────────────┘
                                        ▲
                              ┌─────────┴──────────┐
                              │     L3  Sjón        │
                              │     (vision frames) │
                              └────────────────────┘
```

**Enforced acyclicity rules:**
- L0 Grunnr depends on nothing in HERETIC.
- L1 Bifröst depends on L0, L2 (event subscription), L3 (event subscription), L5.
- L2 Rödd depends on L0 only (for config).
- L3 Sjón depends on L0 only (for config).
- L4 Vébond depends on L0 event bus only — never on L1, L2, L3, or L5 directly.
- L5 Skilningr depends on L0 and its own sense subprocesses (external stdio).
- No sense subprocess depends on another sense subprocess. The sole exception: L5.4 Hönd depends on L5.3 Leið as a **transport mechanism only** — Hönd drives Photopea through the browser; it does not call Leið's business logic. This dependency is a one-way transport bridge, not a business coupling.

---

## 4. Where New Modules Go

| Adding... | Goes in | Rules |
|---|---|---|
| New config key | `config/heretic.yaml` template + L0 Grunnr `Config` struct | Must have a default value; never required for basic operation unless layer is core |
| New sense | `heretic/sense_hub/<sense-name>/` + entry in `SENSE_CONTRACTS.md` | Must implement standard sense lifecycle; must be opt-in via `heretic.yaml`; must receive a True Name from Skald before implementation begins |
| New voice engine (replace Whisper) | `heretic/voice/` — new backend module implementing `VoiceSTTBackend` trait | Old backend stays; config key selects which; Hlust/Tunga names persist regardless of underlying engine |
| New agent protocol adapter | `heretic/bifrost/adapters/` | OpenAI-compat must remain the default; new adapter is a non-default variant behind a config flag |
| New UI panel | `heretic/ui/src/components/` | Must communicate only via Tauri IPC events; no direct Rust calls from JS |
| Plundered code | `vendor/<project-name>/` | Must have LICENSE file; must be logged in `THIRD_PARTY_NOTICES.md`; must follow `MYTHIC_ENGINEERING_PLUNDERING_WORKFLOW.md` |
| Mímisbrunnr data source | `heretic/sense_hub/library/mimisbrunnr/manifests/` | New YAML manifest per source; license field required; listed in `docs/MIMISBRUNNR.md` |
| Norse lore data | `data/` | JSON; must be public domain or clearly licensed; becomes Mímisbrunnr seed |
