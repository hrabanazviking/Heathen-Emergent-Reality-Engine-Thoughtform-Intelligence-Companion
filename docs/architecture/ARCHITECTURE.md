# HERETIC — Master Architecture Document

**Last updated:** 2026-05-08 (v0.7 scaffold — Rúnhild Svartdóttir: Mímisbrunnr/Library sense scaffold; LibraryConfig promoted from dict stub to typed dataclass; 5 Norse starter-pack sources with verified URLs locked in manifest; mimisbrunnr/ backend subsystem and senses/library/ sense layer created; IPC_PROTOCOL §8.4 updated; heretic.example.yaml library block rewritten) | 2026-05-07 (corrective pass — Rúnhild Svartdóttir, adding sense layering section, fixing cross-repo references)
**Scope:** Whole-system structural decomposition — layers, process model, data ownership, lifecycle, licensing layout, technology decisions, and non-goals.
**Authority:** Derives from `docs/BODY_MANIFESTO.md` (sealed vision). All conflicts defer to the manifesto.
**Owner:** Architect (Rúnhild Svartdóttir)
**Legend:** True Names appear first; code-facing identifiers follow in parentheses on first use.

---

## 1. The Body / Spirit Split — System Diagram

```
╔══════════════════════════════════════════════════════════════════════════╗
║                         YOUR LAPTOP  (The Vessel)                       ║
║                                                                          ║
║  ┌────────────────────────────────────────────────────────────────────┐  ║
║  │               H.E.R.E.T.I.C. Runtime — Holdvörðr                  │  ║
║  │                     (process: holdvordur)                          │  ║
║  │                                                                    │  ║
║  │  ┌────────────────────────────────────────────────────────────┐   │  ║
║  │  │  L4  Vébond  (vebond) — Eldahús UI                        │   │  ║
║  │  │       Summoning Circle · Tauri + React · Norse dark mode   │   │  ║
║  │  └─────────────────────────────┬──────────────────────────────┘   │  ║
║  │                                │ renders / receives user events   │  ║
║  │  ┌──────────────┐  ┌───────────┴──────────┐                       │  ║
║  │  │  L2  Rödd    │  │    L3  Sjón           │                       │  ║
║  │  │  (rodd)      │  │    (sjon)             │                       │  ║
║  │  │  STT/TTS     │  │    Screen capture     │                       │  ║
║  │  │  (subprocess)│  │    (Tauri sidecar or  │                       │  ║
║  │  │  Whisper.cpp │  │     native capture)   │                       │  ║
║  │  │  ChatterBox  │  └──────────┬────────────┘                       │  ║
║  │  │  client      │             │                                   │  ║
║  │  └──────┬───────┘             │ raw frames / transcripts          │  ║
║  │         │                     │                                   │  ║
║  │  ┌──────┴─────────────────────┴───────────────────────────────┐   │  ║
║  │  │         L5  Skilningr  (skilningr) — MCP Sense Hub         │   │  ║
║  │  │                  (Python MCP servers)                       │   │  ║
║  │  │                                                             │   │  ║
║  │  │  5.1 Minni (minni) FileSystem                               │   │  ║
║  │  │  5.2 Skepja (skepja) Terminal                               │   │  ║
║  │  │  5.3 Leið (leid) Browser                                    │   │  ║
║  │  │  5.4 Hönd (hond) Photopea                                   │   │  ║
║  │  │  5.5 Smiðja (smidja) Blender / Seidr-Smidja                 │   │  ║
║  │  │  5.6 Líkami (likami) VRChat                                 │   │  ║
║  │  │  5.7 Boð (bod) AgentMail                                    │   │  ║
║  │  │  5.8 Nýr Limr (nyr_limr) Custom plugins                     │   │  ║
║  │  │  5.9 Mímisbrunnr (mimisbrunnr) Library                      │   │  ║
║  │  └──────────────────────────────┬──────────────────────────────┘  │  ║
║  │                                 │  tool schemas (JSON) +           │  ║
║  │                                 │  tool results                    │  ║
║  │  ┌──────────────────────────────┴──────────────────────────────┐   │  ║
║  │  │   L1  Bifröst  (bifrost) — OpenAI-compat agent client       │   │  ║
║  │  │   Tailscale-aware routing | auth | ceremonial lifecycle      │   │  ║
║  │  └──────────────────────────────┬──────────────────────────────┘   │  ║
║  │                                 │  HTTPS / Tailscale WireGuard      │  ║
║  │  ┌──────────────────────────────┴──────────────────────────────┐   │  ║
║  │  │   L0  Grunnr  (grunnr) — Foundation                         │   │  ║
║  │  │   Tauri shell · heretic.yaml · logging · subprocess super   │   │  ║
║  │  └─────────────────────────────────────────────────────────────┘   │  ║
║  └────────────────────────────────────────────────────────────────────┘  ║
╚═══════════════════════════════════════════════════════╤══════════════════╝
                                                        │ Tailscale mesh
                                         ┌──────────────┴────────────────┐
                                         │      THE SPIRIT  (any agent)  │
                                         │                               │
                                         │  Speaks: OpenAI Chat API      │
                                         │  Calls: tool_use JSON         │
                                         │  Receives: tool_result JSON   │
                                         │                               │
                                         │  Examples:                    │
                                         │  · Hermes on Raspberry Pi     │
                                         │  · Claude via Anthropic API   │
                                         │  · GPT-4 via OpenAI API       │
                                         │  · Local LLM via Ollama       │
                                         │  · OpenClaw runtime           │
                                         └───────────────────────────────┘

          ┌─────────────────────────────────────────────────┐
          │   EXTERNAL APPLICATIONS  (not HERETIC's code)   │
          │   Blender · Photopea · VRChat · Browser         │
          │   Managed by OS; MCP servers call their APIs    │
          └─────────────────────────────────────────────────┘
```

The body/spirit separation is the single most load-bearing invariant in this system. HERETIC never owns the spirit's mind. The spirit never owns the body's hardware.

---

## 2. The Six-Layer Stack

### L0 — Grunnr (Foundation)

| Attribute | Value |
|---|---|
| True Name | Grunnr (grunnr) |
| Purpose | Tauri shell initialization, configuration loading, logging, crash guard, subprocess supervision |
| Technology | Rust (Tauri core) + heretic.yaml (YAML config, never hardcoded settings) |
| Owns | Process lifecycle, heretic.yaml parsing, structured logging, panic guard |
| Depends on | OS, Tauri runtime |
| Must never control | Agent conversation, sense data, voice audio, screen frames, network routing |
| Stable contract | Exposes `Config` struct (typed) to all layers; emits `heretic::lifecycle` log channel; every layer reads config through `foundation::config()` — no layer reads heretic.yaml directly |
| SLO tier | Infrastructure — no latency SLO; must complete startup within `foundation.startup_timeout_seconds` |

### L1 — Bifröst (Agent Connection)

| Attribute | Value |
|---|---|
| True Name | Bifröst (bifrost) |
| Purpose | Ceremonial connection to the agent — the one and only seam between body and spirit |
| Technology | Rust + `reqwest` HTTP client; Tailscale-aware endpoint routing |
| Owns | Agent endpoint URL, Bearer token, connection state machine, retry logic, heartbeat, message queue, tool call dispatch |
| Depends on | L0 Grunnr config, Tailscale network presence, L5 Skilningr (tool schemas), L2 Rödd (transcript events), L3 Sjón (frame events) |
| Must never control | Agent memory, agent persona, conversation history persistence, sense data routing, what tools do |
| Stable contract | `bifrost::send_turn(messages, tools, stream) -> Result<AgentResponseStream>` — one call per agent turn |
| SLO tier | Warm — response stream start < 1200 ms p95; voice transcript dispatch < 100 ms after receipt |

### L2 — Rödd (Voice)

| Attribute | Value |
|---|---|
| True Name | Rödd (rodd) |
| Purpose | Give the agent ears (Hlust / STT) and a voice (Tunga / TTS) |
| Technology | Whisper.cpp (subprocess, MIT) for STT; ChatterBox HTTP client (TTS server on Tailscale) |
| Owns | Microphone device selection, audio capture loop, VAD, STT transcript queue, TTS queue, speaker output |
| Depends on | L0 Grunnr config (device IDs, ChatterBox endpoint), OS audio API |
| Must never control | What the agent says, conversation routing, MCP tools, screen capture |
| Stable contract | STT emits `voice::transcript(text, timestamp, confidence)` events; TTS accepts `voice::speak(text)` commands from L1; each half independently configurable |
| SLO tier | Warm (STT round-trip < 1200 ms for typical utterance); Hot for TTS chunk playback start (< 60 ms after first audio chunk received) |

### L3 — Sjón (Vision)

| Attribute | Value |
|---|---|
| True Name | Sjón (sjon) |
| Purpose | Give the agent sight — periodic screen captures delivered as images |
| Technology | Tauri native screen capture or platform sidecar (Windows: DXGI, Linux: X11/Wayland, macOS: CoreGraphics) |
| Owns | Screen capture schedule, resolution/crop config, capture buffer, optional webcam feed |
| Depends on | L0 Grunnr config (capture interval, resolution, crop, webcam device, buffer depth), OS screen capture permission |
| Must never control | How the agent interprets frames, what it does with them, audio, MCP tools |
| Stable contract | Emits `vision::frame(base64_png, timestamp, source)` events on schedule; L1 Bifröst consumes them when assembling agent turns |
| SLO tier | Cold — frames captured at user-configured interval (default 5 s); not latency-critical |

### L4 — Vébond (UI — Eldahús)

| Attribute | Value |
|---|---|
| True Name | Vébond (vebond); the UI shell is Eldahús (Fire-House) |
| Purpose | The Summoning Circle — human-facing ceremony interface; purely presentational |
| Technology | Tauri + React (TypeScript), Norse dark aesthetic, glowing rune accents |
| Owns | Ceremony controls (light/extinguish), layer status indicators, voice waveform display, sense toggle panel, config surface |
| Depends on | L0 Grunnr event bus, L1 Bifröst connection state events, L2 Rödd voice activity events; Tauri IPC bridge |
| Must never control | Agent conversation content, MCP tools, audio processing, network routing |
| Stable contract | Receives `heretic::ui::state_update` events from backend; emits `heretic::ui::command::*` events to backend; never reads internal layer state directly |
| SLO tier | Hot — UI must reflect state changes (connection status, sense health, voice activity) within 60 ms of event emission |

### L5 — Skilningr (MCP Sense Hub)

| Attribute | Value |
|---|---|
| True Name | Skilningr (skilningr) |
| Purpose | Host the agent's senses as MCP tool servers; multiplex tool calls from the agent |
| Technology | Python MCP SDK (MIT, Anthropic) — one subprocess per enabled sense |
| Owns | Sense subprocess registry, tool routing table, sense health monitoring, tool schema aggregation, inter-sense isolation |
| Depends on | L0 Grunnr config (which senses are enabled, their endpoint/process config), each L5.x sense subprocess (via stdio MCP) |
| Must never control | Agent conversation context, voice/vision data streams, UI rendering, what tools' underlying applications do |
| Stable contract | `sense_hub::get_tools() -> Vec<ToolSchema>` and `sense_hub::call_tool(name, args) -> ToolResult` — two calls, full encapsulation |
| SLO tier | Warm for interactive tools (tool call dispatch < 100 ms); Cold for library search and file indexing operations |

Sub-senses (L5.1–L5.12) are documented in full in `SENSE_CONTRACTS.md`. Each runs as an independent subprocess. Failure of one sense does not crash the body.

---

## 2a. Sense Layering — L5 Surface, L2/L3 Substrate

**The architectural resolution for Auga, Hlust, and Tunga.**

NAMING.md assigns `sense.auga`, `sense.hlust`, and `sense.tunga` identifiers to three things that look like they belong in L2/L3:
- Hlust (hearing / STT) and Tunga (speech / TTS) — physically owned by L2 Rödd
- Auga (sight / screen capture) — physically owned by L3 Sjón

The resolution: **all senses are exposed as L5.x MCP tool subprocesses**, regardless of which layer's hardware they operate on top of. L2 and L3 own the physical infrastructure (mic capture, speaker output, Whisper subprocess, ChatterBox client, screen capture schedule, frame buffer). They do not expose tools directly to the agent. The agent has no direct contact with L2 or L3.

The L5 sense subprocesses for Hlust (L5.10), Tunga (L5.11), and Auga (L5.12) call into L2/L3 via internal Holdvörðr IPC to fulfil agent tool calls:

```
Agent calls tunga.speak(text)
    ↓
L5 Skilningr routes to heretic-sense-tunga subprocess
    ↓
heretic-sense-tunga calls L2 Rödd's TTS interface (internal IPC, not MCP)
    ↓
L2 Rödd invokes ChatterBox HTTP client; plays audio
    ↓
heretic-sense-tunga returns ok: true to agent
```

```
Agent calls hlust.listen(duration_ms)
    ↓
L5 Skilningr routes to heretic-sense-hlust subprocess
    ↓
heretic-sense-hlust requests a transcript segment from L2 Rödd's STT interface (internal IPC)
    ↓
L2 Rödd reads from its VAD/transcript buffer (or initiates a capture segment)
    ↓
heretic-sense-hlust returns transcript to agent
```

```
Agent calls auga.snapshot(source)
    ↓
L5 Skilningr routes to heretic-sense-auga subprocess
    ↓
heretic-sense-auga requests a frame from L3 Sjón's capture interface (internal IPC)
    ↓
L3 Sjón captures or returns the buffered frame
    ↓
heretic-sense-auga returns base64_png to agent
```

**What this means for boundaries:**
- L2 Rödd: owns infrastructure; exposes no tools; never speaks to the agent endpoint.
- L3 Sjón: owns infrastructure; exposes no tools; never speaks to the agent endpoint.
- L5.10 Hlust, L5.11 Tunga, L5.12 Auga: thin MCP wrappers over L2/L3 infrastructure; the only surfaces the agent touches.

The Auga sense differs from L3's scheduled background capture: L3 captures on a timer and injects frames into turns automatically (when `?vision_in` is set). Auga gives the agent an on-demand snapshot tool (`auga.snapshot`) — complementary, not redundant.

---

## 3. Process Model

```
┌─────────────────────────────────────────────────────────────────────┐
│  Tauri Process  (Rust + WebView)  — Holdvörðr                       │
│  Owns: L0 Grunnr, L1 Bifröst, L3 Sjón, L4 Vébond, L5 Skilningr    │
│        router                                                        │
│  Spawns and supervises all subprocesses                             │
└──────┬────────────────────────────┬──────────────────────────────────┘
       │ subprocess IPC             │ subprocess IPC
       ▼                            ▼
┌──────────────────┐      ┌─────────────────────────────────────────┐
│ L2 Rödd          │      │ L5.x Sense subprocesses  (Python)       │
│ Subprocess(es)   │      │ One per enabled sense                   │
│                  │      │                                         │
│ Hlust (whisper-  │      │  · heretic-sense-minni    (filesystem)  │
│  cpp STT engine) │      │  · heretic-sense-skepja   (terminal)    │
│ Tunga (chatter-  │      │  · heretic-sense-leid     (browser)     │
│  box TTS client) │      │  · heretic-sense-hond     (photopea)    │
│                  │      │  · heretic-sense-smidja   (blender)     │
│                  │      │  · heretic-sense-likami   (vrchat)      │
│                  │      │  · heretic-sense-bod      (agentmail)   │
│                  │      │  · heretic-sense-nyr-limr (custom-*)    │
└──────────────────┘      │  · heretic-sense-mimisbrunnr (library)  │
                          └─────────────────────────────────────────┘

External processes (NOT spawned by HERETIC — user installs separately):
  Blender, Photopea (browser app), VRChat, browser (Chromium-family),
  ChatterBox TTS server, Tailscale daemon
```

**In-process (Tauri/Holdvörðr):** L0 Grunnr, L1 Bifröst, L3 Sjón, L4 Vébond, L5 Skilningr MCP router.
**Out-of-process subprocesses:** L2 Rödd voice binaries (Hlust/Tunga), each L5.x sense MCP server.
**External services (not managed by HERETIC):** ChatterBox, Tailscale, Blender, Photopea, VRChat, agent endpoint.

The Tauri process (Holdvörðr) supervises subprocesses. A crashed sense subprocess is restarted with exponential backoff (config: `heretic.yaml` → `senses.<id>.restart_policy`). The Tauri process itself crashing ends the ceremony cleanly — no dangling processes, because Holdvörðr owns the subprocess tree.

---

## 4. Data Ownership

### Persistent state (survives across ceremonies)

| What | Where | Owner |
|---|---|---|
| Configuration | `heretic.yaml` (OS config dir — never hardcoded path) | L0 Grunnr |
| Library indices (Mímisbrunnr) | `~/.heretic/library/` (configurable) | L5.9 Mímisbrunnr |
| MindSpark knowledge base | MindSpark's own storage (external project) | MindSpark |
| Plundered vendor code | `vendor/` in repo | L0 / build |
| Agent session history | **NOT in HERETIC** — belongs to the spirit | Spirit |

### Session state (lives for one ceremony; zeroed on Slokna / EXTINGUISHED)

| What | Where | Owner |
|---|---|---|
| Agent message queue | L1 Bifröst in-memory buffer | L1 Bifröst |
| Voice transcript buffer | L2 Rödd in-memory queue | L2 Rödd |
| Vision frame buffer | L3 Sjón in-memory ring buffer (configurable depth) | L3 Sjón |
| Active tool call table | L5 Skilningr in-memory map | L5 Skilningr |
| Tailscale connection state | L1 Bifröst | L1 Bifröst |
| UI ceremony state | L4 Vébond React state | L4 Vébond |

### Explicitly not owned by HERETIC

- Agent memory, persona, world model, character card — the spirit brings its mind.
- Conversation history persistence — the agent's server or Hermes's own memory system.
- User's personal files (the agent may request access via L5.1 Minni FileSystem; HERETIC provides only a sandboxed accessor).

---

## 5. Activation Lifecycle (high-level)

The full state machine lives in `CEREMONY.md`. True Names from `docs/NAMING.md` are used throughout:

```
  Hvíld  (STATE_HVILD — dormant, not running)
    │  user launches app
    ▼
  Kynding  (STATE_KYNDING — kindling)
    L0 Grunnr loads config; L5 Skilningr spawns sense subprocesses
    │  all enabled senses healthy OR timeout
    ▼
  Ready  (intermediate — Summoning Circle visible; Bifröst not yet open)
    │  user clicks "Light the Candle"
    ▼
  Opening  (L1 Bifröst attempts Tailscale-aware connection, capability probe)
    │  connection accepted, capability handshake complete
    ▼
  Tengsl  (STATE_TENGSL — bound; spirit present)
    │
    ▼
  Samræður  (STATE_SAMRAEDUR — communion; active session running)
    │  user clicks "Extinguish" OR error OR agent disconnect
    ▼
  Slokna  (STATE_SLOKNA — extinguishing → clean shutdown)
    │  all subprocesses confirm clean state; session state zeroed
    ▼
  Hvíld  (dormant again)
```

No state leaks from one ceremony to the next. Session state is zeroed on Slokna.

---

## 6. SLO Tiers

Carried forward from the surviving `SLO_Tiers.md` triage (see `docs/PRIOR_PLANNING_TRIAGE.md`). These tiers govern how HERETIC degrades gracefully under load or failure.

| Tier | Name | Latency target | Applies to | Breach behavior |
|---|---|---|---|---|
| Hot | Avatar / bridge feedback | < 60 ms p95 | L4 Vébond UI state updates; TTS first-chunk start | Degrade visual polish before blocking canon |
| Warm | Voice turn response | < 1200 ms p95 | L1 Bifröst turn round-trip; L2 Rödd STT | Fall back to text-only mode if voice path breaches |
| Cold | Background async | < 30 s p95 | L5.9 library indexing; Mímisbrunnr download progress; L3 Sjón frame injection into long turns | Interruptible; user notified; ceremony unblocked |

Senses report their expected tier in their capability flags (see `SENSE_CONTRACTS.md`). Hot breaches in L4 must not propagate to L1. Cold operations must not block Samræður.

---

## 7. Multi-License Layout

HERETIC respects four distinct licensing zones. They must never be conflated.

### Zone 1 — Own code (MIT)

Everything in `heretic/`, `src/`, `tests/`, config templates, and documentation written by this project.
License: MIT. No restrictions on downstream use.

### Zone 2 — Vendored permissive code (original license preserved)

Code studied and selectively adapted from open-source projects under MIT, Apache-2.0, or BSD licenses.
Location: `vendor/<project-name>/` — never modify without attribution update.
Original license header preserved in every file. Tracked in `THIRD_PARTY_NOTICES.md`.

Candidate plunder sources (per `MYTHIC_ENGINEERING_PLUNDERING_WORKFLOW.md`):
- MCP Python SDK (MIT, Anthropic)
- Whisper.cpp (MIT)
- Tauri (MIT / Apache-2.0)
- Hermes Agent reference patterns (MIT)
- OpenClaw reference patterns (MIT)

### Zone 3 — Runtime dependencies (external, used not vendored)

Libraries and tools that HERETIC calls at runtime but does not vendor or redistribute.
User installs these independently. They retain their own licenses.
Declared in `THIRD_PARTY_NOTICES.md` for attribution; not in `vendor/`.

Examples:
- `libzim` (GPL-2) — used as runtime dep for Mímisbrunnr, never vendored
- `kiwix-tools` (GPL-3) — same
- Blender (GPL-3) — external application; L5.5 Smiðja MCP server calls its API
- Photopea — proprietary web app; accessed via L5.4 Hönd browser automation
- VRChat SDK (VRChat TOS) — external
- python-osc (MIT) — may be vendored; used by L5.6 Líkami

**GPL / AGPL rule:** Never vendor GPL or AGPL code. Use it only as an installed runtime dependency. Zero GPL code enters `vendor/` or `heretic/`.

### Zone 4 — External applications (not HERETIC's code at all)

Applications the agent controls via MCP: Blender, browser, VRChat, mail client.
HERETIC merely calls their APIs. Their licenses have no effect on HERETIC's MIT grant.

---

## 8. Technology Stack Decisions

### Tauri + React (not Electron)

**Rationale:** Tauri uses the OS's native WebView rather than bundling Chromium. This gives fast cold-start (the manifesto's "ceremonial activation" requires near-instant summoning), a small binary, and low idle RAM during Hvíld. Electron's ~150 MB Chromium bundle is antithetical to a body that "rests" when not summoned. Tauri's Rust core provides subprocess management (Holdvörðr process tree) for free.

**Trade-off accepted:** Native WebView quirks across platforms require defensive CSS. React's component model handles the status-heavy Summoning Circle UI elegantly.

### Whisper.cpp (not cloud STT)

**Rationale:** Locality as power (manifesto principle). No audio leaves the machine. No API key required. Runs on user's GPU or CPU via `ggml`. MIT licensed — clean for subprocess use. Model file (`.gguf`) ships separately; user downloads the size they want.

**Trade-off accepted:** Slightly higher latency than cloud APIs on older hardware. Acceptable: the STT path is async; L1 Bifröst does not block on transcription.

### ChatterBox TTS (not cloud TTS)

**Rationale:** ChatterBox runs on the Tailscale network at `100.66.178.105:7851` — a live, verified endpoint. No integration cost for v0.2. MIT licensed. Keeps voice local or within the trusted Tailscale mesh. Configurable — user can point `heretic.yaml` at any OpenAI-compat TTS endpoint.

**Trade-off accepted:** ChatterBox runs on Pi hardware; latency may be higher than GPU TTS on the laptop.

### Python MCP SDK for sense subprocesses (not Rust)

**Rationale:** The MCP Python SDK (MIT, Anthropic) is the reference implementation — most mature, best documented, primary target for new MCP tooling. Senses like Minni (FileSystem) and Skepja (Terminal) are I/O-bound; Python's async model handles them well. For Smiðja (Blender / Seidr-Smidja) integration, Python is already the lingua franca.

**Trade-off accepted:** Python subprocesses add ~30–60 MB RSS each. Acceptable because senses are optional and the number active at once is user-controlled.

### Tailscale (not raw WireGuard / not SSH tunnel)

**Rationale:** The Pi endpoint is verified live on Tailscale (`100.101.39.30:8643`). Tailscale handles NAT traversal, device identity, and MACsec-grade encryption without manual key rotation. It is the established trust fabric of this ecosystem. Any HTTPS endpoint also works — Tailscale is the default routing strategy for Hermes-on-Pi, not the only one.

**Trade-off accepted:** Requires user to have Tailscale installed for the Pi case.

### OpenAI Chat Completions API as the agent protocol

**Rationale:** Both primary agents (Hermes, OpenClaw) speak this format. Claude, GPT-4, local Ollama models all speak it. One adapter, all spirits. Confirmed sufficient in manifesto — no native RPC adapters needed in v1.

**Trade-off accepted:** OpenAI format evolves (function call vs tool call history). HERETIC targets the stable `/v1/chat/completions` with `tools` (not deprecated `functions`). LiteLLM wire normalizer explicitly dropped from v1 scope.

---

## 9. Cross-Repo Plug-In Slots

| HERETIC slot | Repo connected | Protocol | Status |
|---|---|---|---|
| L1 Bifröst — primary spirit | Hermes on Pi (`100.101.39.30:8643/v1`) | OpenAI-compat client | Live |
| L2 Rödd TTS — Tunga | ChatterBox at `100.66.178.105:7851` | Native HTTP client | Live |
| L5.5 Smiðja — Blender | Seidr-Smidja Brúarhönd v0.1 (`github.com/hrabanazviking/Seidr-Smidja`) | MCP wrapper over Brúarhönd REST + 3 MCP tools | Shipped; 489 tests green |
| L5.9 Mímisbrunnr — MindSpark backend | MindSpark ThoughtForge (`github.com/hrabanazviking/MindSpark_ThoughtForge`) | MCP wrapper; optional library backend | v1.2.0 shipped |
| L5.8 Nýr Limr — WYRD Protocol (optional) | WYRD Protocol (`github.com/hrabanazviking/WYRD-Protocol-World-Yielding-Real-time-Data-AI-world-model`) | Optional custom MCP if user wants world-model access | v1.0 shipped |

---

## 10. Explicit Non-Goals

These are things HERETIC will not do, by design. Each boundary protects the body/spirit invariant or the resource budget.

| Non-goal | Reason |
|---|---|
| Agent memory / persona / world model | The spirit brings its mind. Manifesto: "H.E.R.E.T.I.C. is not a replacement for the agent's own memory." |
| Always-on background service | Manifesto: "the body rests." No tray daemon, no startup service, no background polling. |
| Conversation history persistence | That is the agent server's job. L1 Bifröst holds messages in a session-only buffer; zeroed on Slokna. |
| Photoreal UE5 / MetaHuman environment | Demoted to v2.x stretch. Not core to embodiment. Líkami (VRChat) handles social presence. |
| In-window VRM avatar rendering | Not needed. The agent's avatar lives in VRChat (L5.6 Líkami), not in HERETIC's window. |
| LiteLLM wire normalizer | OpenAI-compat is sufficient for v1. Dropped. |
| Native Hermes Gateway RPC adapter | OpenAI-compat is enough. Dropped for v1. |
| Cloud service operation | HERETIC is a local runtime. No SaaS model, no cloud hosting, no telemetry. |
| Being a chat UI | Manifesto: "H.E.R.E.T.I.C. is not a chat UI with a text box." |
| Fine-tuning or training models | A different project entirely. |
| Content filtering / safety layer | The user selects their spirit. HERETIC routes, not censors. |

---

*"The völva didn't just tell people what the spirits said. She became the conduit."*
*— docs/BODY_MANIFESTO.md*
