# H.E.R.E.T.I.C. — System Overview

**Last updated:** 2026-05-08 v0.6.x addendum — Védis Eikleið: §7 milestone topology updated; v0.6.x (MCP server hosting — three-door transport coexistence) marked IN PROGRESS; cross-references to DATA_FLOW.md §4.13 (MCP transport flow) and §16 v0.6.x extension (McpServer module + three-door diagram) added. | 2026-05-07 (corrective pass — Védis Eikleið, resolving audit finding A-5; sense config subkeys aligned to code-facing IDs per NAMING.md §line 81; sense process labels de-prefixed to match SENSE_CONTRACTS.md §2 canonical format) | 2026-05-07 second pass — audit nit X-1 resolved: removed intermediate `senses:` key from §3 config example; sense IDs now nest directly under `skilningr:` matching `grunnr/config.py:SkilningrConfig` field access | 2026-05-07 v0.2 addendum — Védis Eikleið: §7 milestone topology updated to mark v0.2 as active; §2 Rödd note updated; cross-reference to DATA_FLOW.md §4.6 added | 2026-05-07 v0.3 addendum — Védis Eikleið: §2 Rödd note updated to reflect L2 Rödd Tunga (v0.2) SHIPPED + Hlust (v0.3) IN PROGRESS; §7 milestone topology updated accordingly; cross-reference to DATA_FLOW.md §4.7 added | 2026-05-07 v0.4.0 addendum — Védis Eikleið: §7 milestone topology updated; v0.3 marked SHIPPED; v0.4.0 (L4 Vébond Eldahús substrate — Python WS backend + React/Vite frontend) marked IN PROGRESS; v0.4.1 (Tauri wrap, requires Rust) noted as deferred separate session; §2 Holdvörðr process map updated to show L4 Vébond role; cross-reference to DATA_FLOW.md §4.8 and §13 added | 2026-05-07 v0.4.1 addendum — Védis Eikleið: §7 milestone topology updated; v0.4.0 marked SHIPPED (HEAD 9e9a5aa); v0.4.1 (Tauri shell wrap) marked PRE-STAGED — src-tauri/ scaffolded, Rust toolchain not yet installed, no binary produced; cross-reference to DATA_FLOW.md §4.9 and §14 added | 2026-05-08 v0.5 addendum — Védis Eikleið: §7 milestone topology updated; v0.4.1 remains PRE-STAGED (Rust not yet installed); v0.5 (L3 Sjón substrate — screen capture, on-demand per user message send) marked IN PROGRESS; §2 Sjón note expanded; cross-references to DATA_FLOW.md §4.10 and §15 added | 2026-05-08 v0.5.1 addendum — Védis Eikleið: §7 milestone topology updated; v0.5 First Sight marked SHIPPED (HEAD 4d9d2fa); v0.5.1 Periodic Sight (continuous capture loop + ring buffer + multi-monitor mapping) marked IN PROGRESS; v0.5.1 is an extension of v0.5 — no new layer, same L3 Sjón substrate deepened; cross-reference to DATA_FLOW.md §4.10.7–§4.10.10 added | 2026-05-08 v0.6 addendum — Védis Eikleið: §7 milestone topology updated; v0.5.1 Periodic Sight marked SHIPPED; v0.6 Hands at the Forge (L5 Skilningr substrate + Smiðja sense + Brúarhönd integration) marked IN PROGRESS; cross-references to DATA_FLOW.md §4.11 and §16 added | 2026-05-08 v0.5.2 addendum — Védis Eikleið: §7 milestone topology updated; v0.5.2 Webcam Capture (WebcamCaptureBackend, OpenCvBackend, NullWebcamBackend, snapshot_webcam(), 4-path attach_policy decision tree, stronger privacy stance) marked IN PROGRESS; cross-references to DATA_FLOW.md §4.10.11–§4.10.13 and §15 v0.5.2 extension added | 2026-05-08 v0.6.2 addendum — Védis Eikleið: §7 milestone topology updated; v0.6.1 marked SHIPPED; v0.6.2 More Senses (Minni + Skepja + Leið) marked IN PROGRESS; cross-references to DATA_FLOW.md §4.12, §4.12.1, §4.12.2, §4.12.3, §16 v0.6.2 extension added; §8 security topology references updated (Skepja = highest risk; Minni = scoped to root)
**Scope:** Full terrain — machines, layers, cross-repo plug-ins, optional vs required, runtime states
**Cartographer:** Védis Eikleið
**Status:** Pre-implementation specification. Drawn from canonical docs
(`docs/BODY_MANIFESTO.md`, `docs/NAMING.md`, `TASK_HERETIC_v0.1_BOOTSTRAP.md`,
`heretic_dependency_map.md`, `docs/MIMISBRUNNR.md`).

**Legend:**
```
[LAPTOP]    physical machine — the user's laptop
[PI]        physical machine — the Raspberry Pi in the closet
[TAILSCALE] the WireGuard mesh network — the bridge between them
[REQUIRED]  must be present for any ceremony to work
[OPTIONAL]  user enables in heretic.yaml; absent = sense not available
[ext-repo]  lives in a sibling repo under runa/, not in HERETIC itself
```

---

## 1. The Three-Machine Picture

There are two real machines and one mesh between them.

```
  +----------------------------------------------------------+
  |                     TAILSCALE MESH                       |
  |                   (WireGuard layer)                      |
  |                                                          |
  |   100.101.39.30 (Pi)          100.66.178.105 (Pi/same)  |
  |   Hermes Agent :8643          ChatterBox TTS :7851       |
  |                                                          |
  |   <laptop IP>                                            |
  |   Holdvörðr (HERETIC)                                    |
  +----------------------------------------------------------+
          |                              |
          | WireGuard encrypted          | WireGuard encrypted
          |                              |
  +-------+------+              +--------+--------+
  |    LAPTOP    |              |        PI        |
  |  (The Body)  |              |   (The Shrine)   |
  +-------+------+              +--------+--------+
          |                              |
  Tauri app runs here          Hermes Agent runs here
  All senses live here         ChatterBox TTS runs here
  User sits here               Always on, always waiting
  GPU, mic, speakers, screen   Low power, tucked away
  Heavy apps (Blender, etc.)   Brings the intelligence
```

The manifesto says it clearly: *"The Pi is the shrine — Hermes lives there always.
H.E.R.E.T.I.C. is the ritual space — the body the spirit wears when called into Midgard."*

When HERETIC is in Hvíld, the Pi runs independently. When HERETIC opens Bifröst, the spirit
inhabits the body. When the ceremony ends, the body sleeps and the shrine endures.

---

## 2. What Runs Where

### On the Laptop — Holdvörðr and the Senses

```
  LAPTOP PROCESS MAP (during Samræður)
  =====================================

  Tauri desktop app (Eldahús)
  |-- Holdvörðr (Rust/Tauri backend)
       |
       |-- [L0] Grunnr
       |    config loader, logger, session log writer
       |    reads: heretic.yaml
       |    writes: <data_dir>/sessions/<session_id>.jsonl
       |
       |-- [L1] Bifröst client
       |    OpenAI-compat HTTP client
       |    Tailscale-aware (uses tailscale IP as endpoint)
       |
       |-- [L2] Rödd
       |    Tunga: ChatterBox client  — HTTP to Pi:7851/v1/audio/speech  [v0.2 — SHIPPED]
       |    (Tunga voice flow: SSE chunk → sentence-boundary chunker → ChatterboxClient
       |     → POST /v1/audio/speech → WAV bytes → AudioPlayback → speakers;
       |     full path mapped in DATA_FLOW.md §4.6)
       |    Hlust: Whisper.cpp (STT)  — mic → VAD → Whisper → transcript  [v0.3 — IN PROGRESS]
       |    (Hlust flow: 16kHz int16 30ms frames → VadDetector utterance boundary
       |     → utterance buffer → WhisperEngine lazy load → transcript → CLI display → Bifröst;
       |     full path in DATA_FLOW.md §4.7; component diagram in DATA_FLOW.md §12)
       |
       |-- [L3] Sjón                                                   [v0.5 — IN PROGRESS]
       |    screen capture via mss (cross-platform BGRA → PIL RGB → PNG → base64 data URL)
       |    on-demand per-turn: fires when user sends a message AND sjon.screen.enabled AND ?vision_in
       |    webcam: declared in config (SjonWebcamConfig) but not implemented in v0.5
       |    (Sjón sight flow: user message send → MssBackend.capture() → FrameEncoder BGRA→PNG→b64
       |     → data URL → bifrost.send_message(image_data_urls) → OpenAI image_url content block;
       |     full path in DATA_FLOW.md §4.10; component diagram in DATA_FLOW.md §15)
       |
       |-- [L4] Vébond
       |    ceremony state machine
       |    lifecycle event emitter
       |    drives Eldahús UI state                            [v0.4.0 IN PROGRESS]
       |    Python backend: FastAPI WebSocket server (vebond/serve.py)
       |    React frontend: Vite + React + TypeScript + Tailwind + Zustand
       |    WS protocol: ws://localhost:8642/ws (default; port via vebond.ws_port)
       |    See DATA_FLOW.md §4.8 and §13 for full cartography
       |
       |-- [L5] Skilningr (MCP Sense Hub)
            |  (tool prefix is the sense_id — no "sense." prefix in any tool name)
            |
            |-- auga        MCP server  [id: auga]        (screen + vision)        [REQUIRED]
            |-- hlust       MCP server  [id: hlust]       (STT; substrate: L2 Rödd)[REQUIRED STT]
            |-- tunga       MCP server  [id: tunga]       (TTS; substrate: L2 Rödd)[REQUIRED voice]
            |-- photopea    MCP server  [id: photopea]    (Photopea bridge)         [OPTIONAL]
            |-- blender     MCP server  [id: blender]     (Seidr-Smidja client)     [OPTIONAL]
            |-- browser     MCP server  [id: browser]     (Browser automation)      [OPTIONAL]
            |-- filesystem  MCP server  [id: filesystem]  (FileSystem)              [REQUIRED min]
            |-- terminal    MCP server  [id: terminal]    (Terminal)                [OPTIONAL]
            |-- agentmail   MCP server  [id: agentmail]   (AgentMail)               [OPTIONAL]
            |-- vrchat      MCP server  [id: vrchat]      (VRChat bridge)           [OPTIONAL]
            |-- library     MCP server  [id: library]     (Library / Mímisbrunnr)   [OPTIONAL]
            |-- <prefix>/*  MCP server  [id: user-defined](custom plugins)          [OPTIONAL]
```

### On the Pi — the Spirit and its Voice

```
  PI PROCESS MAP (always running)
  ================================

  Hermes Agent (Nous Research)
  |-- OpenAI-compatible API server on :8643
  |-- Accepts: chat/completions requests from Holdvörðr
  |-- Returns: text responses and tool_call requests
  |-- Manages: conversation history (its own memory)
  |-- Model: <configured — typically a Hermes-series LLM>

  ChatterBox TTS server
  |-- HTTP API on :7851
  |-- Accepts: {text, voice} POST requests from Holdvörðr
  |-- Returns: synthesized audio stream
  |-- Runs independently of HERETIC lifecycle
```

### In Sibling Repos — the Cross-Repo Organs

These are not inside HERETIC's codebase. They live in adjacent repos and are called
at runtime through the sense layer.

```
  SIBLING REPOS AND THEIR HERETIC PLUG-IN SLOTS
  ===============================================

  runa/Seidr-Smidja                    --> L5.5 blender sense  [OPTIONAL]
  |-- Brúarhönd v0.1 — cross-machine VRoid Studio / Blender live GUI remote control
  |   Provides: smidja.screenshot, smidja.click, smidja.type, smidja.hotkey,
  |             smidja.vroid_open, smidja.vroid_export
  |   Endpoint: default https://<host>:8848  (Tailscale or loopback)
  |   Auth: bearer token from env var
  |-- Straumur REST — headless Blender render pipeline  (v0.6.1)
  |   Provides: smidja.forge_build_avatar, smidja.forge_get_avatar, smidja.forge_inspect_avatar
  |   Endpoint: default http://127.0.0.1:8765
  |   Auth: optional bearer token (not required on localhost)
  |-- Status: 489 tests green, Brúarhönd v0.1 shipped; Straumur integration v0.6.1 IN PROGRESS
  |-- How: Smiðja sense holds two independent HTTP clients — BrunhandHttpClient + ForgeHttpClient
  |-- Lives: laptop (apps running locally) or remote via Tailscale

  runa/MindSpark_ThoughtForge          --> L5.9 library sense backend  [OPTIONAL]
  |-- Universal RAG + cognitive scaffolding layer
  |-- Provides: library search, document ingestion, vector retrieval
  |-- Status: v1.2.0, 620 tests, shipped
  |-- How: library (Mímisbrunnr) sense sends HTTP POST to MindSpark at localhost:7777
  |-- Lives: laptop (local process, optional)

  runa/WYRD-Protocol                   --> L5.8 Nýr Limr custom sense slot  [OPTIONAL, v1.x]
  |-- ECS-based AI world model
  |-- Provides: deterministic entity state, world ground truth
  |-- Status: v1.0.0 released, all 19 phases complete
  |-- How: custom MCP server wrapping WYRD oracle API; tool prefix: wyrd.*
  |-- Lives: laptop or Pi (flexible)
  |-- Timeline: v1.0 HERETIC — optional; becomes relevant when agent needs situated world model

  [Pi] Hermes Agent (Nous Research)    --> L1 Bifröst endpoint  [REQUIRED]
  |-- Remote agent runtime
  |-- Provides: intelligence, tool-call generation, conversation
  |-- Status: verified live at 100.101.39.30:8643/v1
  |-- How: Bifröst connects via OpenAI-compat HTTP

  [Pi] ChatterBox TTS                  --> L2 Rödd (Tunga side)  [REQUIRED for voice]
  |-- Text-to-speech synthesis
  |-- Provides: spoken audio for agent responses
  |-- Status: verified live at 100.66.178.105:7851
  |-- How: Tunga MCP server proxies POST requests to ChatterBox
```

---

## 3. Optional vs Required — The Minimal Install

A traveler should know which roads must be walked and which are chosen paths.

### Absolute minimum — a working ceremony without voice output

```
  REQUIRED for any ceremony:
  - L0 Grunnr (always present — it is the ground)
  - L1 Bifröst + Pi Hermes Agent (without this, there is no spirit)
  - L4 Vébond (UI — the ceremony controls exist)
  - L5 Skilningr (the hub exists even if few senses are mounted)

  REQUIRED for voice input (speaking to agent):
  - L2 Rödd: Hlust (Whisper.cpp)

  REQUIRED for voice output (agent speaks back):
  - L2 Rödd: Tunga + ChatterBox on Pi (or alternative TTS)

  REQUIRED for agent to have ANY tools:
  - At least one sense in L5 must be enabled
  - Minimum useful: filesystem sense (True Name: Minni) — agent can read/write files
```

### Minimal install

```
  Minimal viable ceremony:
  [L0 Grunnr] + [L1 Bifröst] + [L2 Rödd both] + [L4 Vébond] + [L5.1 filesystem (Minni)]

  What the agent can do:
  - hear you speak
  - speak back
  - read and write files on your laptop  (tools: filesystem.read_file, filesystem.write_file, …)
  - nothing else

  What requires more senses:
  - seeing your screen:     enable auga     (L3 Sjón substrate; tools: auga.snapshot, auga.describe)
  - running commands:       enable terminal (tools: terminal.run_command)
  - browsing the web:       enable browser  (tools: browser.navigate, browser.screenshot, …)
  - sculpting in Blender:   enable blender  (+ Seidr-Smidja running; tools: blender.screenshot, …)
  - painting in Photopea:   enable photopea (tools: photopea.new_document, photopea.evaluate_script, …)
  - library access:         enable library  (+ corpora downloaded; tools: library.search, …)
  - VRChat presence:        enable vrchat   (tools: vrchat.send_osc, vrchat.set_avatar_parameter, …)
  - email:                  enable agentmail(tools: agentmail.send, agentmail.list_inbox, …)
  - world model:            add custom Nýr Limr sense wrapping WYRD Protocol (prefix: wyrd.*)
```

Each sense is individually toggled in `heretic.yaml` using the code-facing sense_id as the
subkey — not the True Name (except for auga/hlust/tunga whose True Names ARE their code-facing IDs).
See NAMING.md §line 81 and SENSE_CONTRACTS.md §2 for the full True Name → sense_id mapping.

```yaml
skilningr:
  filesystem:             # True Name: Minni
    enabled: true
  auga:                   # True Name: Auga (True Name = code-facing ID for L5.10-12 senses)
    enabled: true
  hlust:                  # True Name: Hlust
    enabled: true
  tunga:                  # True Name: Tunga
    enabled: true
  blender:                # True Name: Smiðja
    enabled: false        # won't start if Seidr-Smidja isn't running
  browser:                # True Name: Leið
    enabled: false
  photopea:               # True Name: Hönd
    enabled: false
  terminal:               # True Name: Skepja
    enabled: false
  agentmail:              # True Name: Boð
    enabled: false
  vrchat:                 # True Name: Líkami
    enabled: false
  library:                # True Name: Mímisbrunnr
    enabled: false        # won't start until corpora are downloaded
```

---

## 4. The Runtime States — What's Running When

### Hvíld (dormant)

```
  LAPTOP               PI
  ------               --
  nothing running      Hermes Agent: running, waiting
                       ChatterBox: running, waiting
  disk: heretic.yaml,  disk: model weights loaded
        session logs         in memory
```

### Kynding (startup sequence)

```
  LAPTOP                                      PI
  ------                                      --
  Tauri app launching                         Hermes Agent: running (unaware)
  Holdvörðr starting                          ChatterBox: running (unaware)
  heretic.yaml loading
  Hlust initialised: mic probed, VAD backend selected, Whisper engine object created
  (Whisper model weights NOT loaded at Kynding — lazy load on first utterance per C-Q-C1)
  MCP sense servers initializing
  Tailscale daemon: queried for connectivity
  Eldahús: showing kindling animation
  L1 Bifröst: initialized but not connected
```

### Tengsl (Bifröst open, spirit present)

```
  LAPTOP                                      PI
  ------                                      --
  All Kynding processes running               Hermes Agent: session active
  L1 Bifröst: HTTP connection established     ChatterBox: ready for TTS calls
  Session log: active                         Conversation history: held by Hermes
  Eldahús: burning steadily
  All enabled senses: listening on local ports
```

### Samræður (communion, active exchange)

```
  LAPTOP                                      PI
  ------                                      --
  Hlust: mic capture active, VAD detecting utterances, Whisper   Hermes Agent: processing requests
  model lazy-loads on first utterance (first-utterance latency)
  Screen capture: available on demand         ChatterBox: synthesizing audio on demand
  All senses: responding to tool calls
  Session log: appending events
  Eldahús: active ceremony display
  Optional cold-path:
    library (Mímisbrunnr) sense indexing in background
    session log archiver compressing old logs
```

### Slokna (extinguishing)

```
  LAPTOP                                      PI
  ------                                      --
  Bifröst: sending closing message            Hermes Agent: receives farewell, continues running
  MCP servers: graceful shutdown              ChatterBox: continues running
  Whisper.cpp: flushing buffers
  Session log: final event, file closed
  Holdvörðr: exits
  Eldahús: fire dying animation
  --> returns to Hvíld
```

---

## 5. The Full Terrain at a Glance

This is the map a traveler should be able to read at a glance: what lives where, what
connects to what, what is optional.

```
  +============================+          TAILSCALE MESH          +=====================+
  |         LAPTOP             |  ==============================  |         PI          |
  |      (The Vessel)          |                                  |    (The Shrine)     |
  |                            |                                  |                     |
  |  +----------------------+  |                                  |  +--------------+  |
  |  | Eldahús (UI)         |  |                                  |  | Hermes Agent |  |
  |  | [L4 Vébond]          |  |                                  |  | :8643/v1     |  |
  |  +----------+-----------+  |                                  |  | [REQUIRED]   |  |
  |             |              |                                  |  +--------------+  |
  |  +----------+-----------+  |                                  |                     |
  |  | Holdvörðr            |  |                                  |  +--------------+  |
  |  | (Runtime Warden)     |  |                                  |  | ChatterBox   |  |
  |  |                      |  |                                  |  | TTS :7851    |  |
  |  | [L0] Grunnr          |  |                                  |  | [REQUIRED    |  |
  |  |   config, logging    |  |                                  |  |  for voice]  |  |
  |  |   session log        |  |                                  |  +--------------+  |
  |  |                      |  |                                  |                     |
  |  | [L1] Bifröst --------+--+------ HTTP (OpenAI-compat) -----+-> Hermes Agent      |
  |  |   connection layer   |  |                                  |                     |
  |  |                      |  |                                  |                     |
  |  | [L2] Rödd            |  |                                  |                     |
  |  |   Hlust (STT)        |  |                                  |                     |
  |  |   Tunga (TTS) -------+--+------ HTTP (TTS) ---------------+-> ChatterBox        |
  |  |                      |  |                                  |                     |
  |  | [L3] Sjón            |  |                                  |                     |
  |  |   screen capture     |  |                                  |                     |
  |  |   webcam [opt]       |  |                                  |                     |
  |  |                      |  |                                  |                     |
  |  | [L5] Skilningr       |  |                                  |                     |
  |  |  (MCP Sense Hub)     |  |                                  |                     |
  |  |                      |  |                                  |                     |
  |  |  Auga [req+opt] <----+--+--- screen data                   |                     |
  |  |  Hlust [req]         |  |                                  |                     |
  |  |  Tunga [req voice]   |  |                                  |                     |
  |  |  Hönd [opt]  <-------+--+--- Photopea (local app)          |                     |
  |  |  Smiðja [opt] <------+--+--- Seidr-Smidja [ext-repo]       |                     |
  |  |                      |  |   --> Blender (local app)        |                     |
  |  |  Leið [opt] <--------+--+--- Browser (local/web)           |                     |
  |  |  Minni [req min]<----+--+--- local filesystem              |                     |
  |  |  Skepja [opt] <------+--+--- local terminal                |                     |
  |  |  Boð [opt] <---------+--+--- email (SMTP/IMAP)             |                     |
  |  |  Líkami [opt] <------+--+--- VRChat (local/network)        |                     |
  |  |  Mímisbrunnr [opt]<--+--+--- local ZIM/FAISS index         |                     |
  |  |   or MindSpark [opt]-+--+--- MindSpark :7777 [ext-repo]    |                     |
  |  |  Nýr Limr [opt] <----+--+--- WYRD Protocol [ext-repo, v1x] |                     |
  |  |  Nýr Limr [opt] <----+--+--- user custom plugins           |                     |
  |  +----------------------+  |                                  |                     |
  +============================+                                  +=====================+

  SIBLING REPOS (on laptop, running as local processes):
  - runa/Seidr-Smidja  -- L5.5 Smiðja backend  [OPTIONAL, v0.6+]
  - runa/MindSpark_ThoughtForge -- L5.9 library backend [OPTIONAL, v0.7.5+]
  - runa/WYRD-Protocol -- L5.8 world model MCP [OPTIONAL, v1.x+]
```

---

## 6. Cross-Repo Plug-In Slot Table

A single reference for all external connections — physical location, HERETIC slot, status.

| Plug-in | Physical location | HERETIC slot | Layer | Required? | Status |
|---|---|---|---|---|---|
| Hermes Agent | Pi: `100.101.39.30:8643/v1` | L1 Bifröst endpoint | Bifröst | Required | Live |
| ChatterBox TTS | Pi: `100.66.178.105:7851` | L2 Rödd (Tunga) | Rödd | Required for voice | Live |
| Seidr-Smidja Brúarhönd | Laptop: sibling repo `github.com/hrabanazviking/Seidr-Smidja` | L5.5 blender sense (True Name: Smiðja) | Skilningr | Optional | Shipped v0.1 |
| Blender (application) | Laptop: user-installed | Controlled via blender sense / Brúarhönd | Skilningr | Optional | External |
| MindSpark ThoughtForge | Laptop: sibling repo `github.com/hrabanazviking/MindSpark_ThoughtForge` | L5.9 library sense backend (True Name: Mímisbrunnr) | Skilningr | Optional | Shipped v1.2.0 |
| WYRD Protocol | Laptop: sibling repo `github.com/hrabanazviking/WYRD-Protocol-World-Yielding-Real-time-Data-AI-world-model` | L5.8 Nýr Limr custom MCP (prefix: wyrd.*) | Skilningr | Optional v1.x | Shipped v1.0.0 |
| Photopea | Laptop: browser/app | L5.4 photopea sense (True Name: Hönd) | Skilningr | Optional | External |
| VRChat | Laptop/network | L5.6 vrchat sense (True Name: Líkami) | Skilningr | Optional | External |
| libzim (Kiwix) | Laptop: installed by user | Mímisbrunnr library backend | Skilningr | Optional | GPL-2, runtime dep |
| Whisper.cpp | Laptop: bundled or installed | L2 Rödd (Hlust) | Rödd | Required for STT | MIT |
| Tailscale daemon | Laptop + Pi | Bifröst transport | Bifröst | Required | External |

**Note on Seidr-Smidja:** The Smiðja sense in HERETIC wraps two surfaces of Seidr-Smidja:
Brúarhönd v0.1 (live GUI control, port 8848) and Straumur REST (headless Blender render, port 8765,
v0.6.1). Seidr-Smidja is a sibling repo at `github.com/hrabanazviking/Seidr-Smidja` — it must be
running locally. HERETIC calls its HTTP endpoints via two independent HTTP clients (BrunhandHttpClient
and ForgeHttpClient). Each arm opens and closes independently; either can be absent without affecting
the other. Tool calls are prefixed `smidja.*` — Brúarhönd tools have no sub-prefix; Forge tools carry
a `forge_` sub-prefix (e.g., `smidja.forge_build_avatar`).

---

## 7. Milestone Topology — When Each Layer Comes Alive

Following the roadmap in `TASK_HERETIC_v0.1_BOOTSTRAP.md`:

```
  v0.0  Bones            docs only          L0 (config schema only)
  v0.1  First Communion  CLI ceremony       L0 + L1 (Bifröst live, text only)       SHIPPED HEAD 926de2e
  v0.2  First Voice      TTS                L0 + L1 + L2 Tunga                      SHIPPED HEAD f9c58cd AUDITED
        |  Tunga path: SSE stream → sentence-boundary chunker → ChatterboxClient
        |    → POST /v1/audio/speech (Pi 100.66.178.105:7851) → WAV bytes
        |    → AudioPlayback → OS audio device → speakers
        |  Fallback: /health fail or synthesis error → text-only, ceremony continues
        |  See DATA_FLOW.md §4.6 and §11 for full cartography of this path.
  v0.3  First Listening  STT                L0 + L1 + L2 full Rödd (Hlust / Whisper.cpp)   SHIPPED HEAD 77d49c9 AUDITED
        |  Hlust path: mic 16kHz int16 30ms frames → VadDetector (webrtcvad primary,
        |    energy-threshold fallback) → utterance buffer → WhisperEngine (pywhispercpp
        |    primary, whisper-cli fallback) → transcript → CLI display → Bifröst user message
        |  Lazy load: Whisper model loads on first utterance (resolves C-Q-C1); not at Kynding
        |  Fallback chain: sounddevice fail → Hlust disabled → stdin; webrtcvad fail → energy RMS;
        |    pywhispercpp fail → whisper-cli; neither Whisper → stdin fallback; ceremony never crashes
        |  See DATA_FLOW.md §4.7 and §12 for full cartography of this path.
  v0.4  Summoning Circle L4 Vébond          Eldahús UI — Python WS backend + React/Vite frontend
        |
        |  v0.4.0 — Eldahús Substrate (SHIPPED — HEAD 9e9a5aa)
        |    Python `heretic serve`: FastAPI + WebSocket on ws://localhost:8642/ws
        |    React/Vite frontend in frontend/ directory; served via `npm run dev`
        |    Norse dark aesthetic per AESTHETIC.md (Eld/Sjón-glow/Mál-green/Hvíla-grey)
        |    Components: SummoningCircle, LifecyclePulse, CenterCrest, ChatPanel, ChatHistory,
        |      ChatInput, LayerStatusPanel, SenseTogglePanel (read-only), LightButton,
        |      ExtinguishButton, ConnectionIndicator, ToastSystem
        |    WS event protocol: 7 server-push events + 5 client commands
        |    Zustand store: single source of UI truth; fed by WS events
        |    SSE text chunks fork to ChatHistory display alongside Tunga TTS (as projected in v0.2)
        |    See DATA_FLOW.md §4.8 (UI flow) and §13 (L4 Vébond component diagram)
        |
        |  v0.4.1 — Tauri Shell Wrap (PRE-STAGED — HEAD d1bdb05)
        |    src-tauri/ directory scaffolded: Cargo.toml, tauri.conf.json, main.rs,
        |      sidecar.rs, error.rs, build.rs, placeholder icons, capabilities/default.json
        |    Tauri spawns Python `heretic serve` as sidecar; probes /health before opening WebView
        |    Graceful shutdown: SIGTERM / CTRL_BREAK_EVENT; force-kill after 5s; PID file recovery
        |    Native window: dark, frameless, Norse chrome per AESTHETIC.md
        |    Tauri commands: quit, focus_window, get_sidecar_port (minimal; WS is primary IPC)
        |    Frontend code does NOT change between v0.4.0 and v0.4.1
        |    NOT yet compiled: Rust toolchain not installed; first `cargo tauri build` pending
        |    Prerequisite to compile: `winget install Rustlang.Rust.MSVC` (Windows) or rustup-init
        |    See DATA_FLOW.md §4.9 (Tauri shell flow) and §14 (shell wrapper diagram)
        |    PyInstaller bundling deferred to v0.4.1.x — v0.4.1 requires Python 3.10+ on PATH
  v0.5  First Sight      screen capture     L3 Sjón substrate                       SHIPPED HEAD 4d9d2fa AUDITED
        |  Sjón path: user message send → SjonOrchestrator.snapshot()
        |    → MssBackend.capture(monitor=primary) [mss, MIT, cross-platform]
        |    → FrameEncoder: BGRA → PIL.Image(RGB) → thumbnail(1280×720) → PNG(compress_level=6)
        |    → base64 → data URL → bifrost.send_message(image_data_urls)
        |    → OpenAI image_url content block → agent receives inline PNG with user message
        |  Trigger: on-demand per user-message send (not periodic; interval_ms reserved for v0.5.x)
        |  Gate: sjon.screen.enabled AND ?vision_in capability AND not throttled (min_interval_ms)
        |  Privacy: save_frames defaults false; frames exist in memory + HTTP body only
        |  Failure modes: F-1 mss absent, F-2 macOS permission, F-3 encode fail,
        |    F-4 oversized (50% rescale retry), F-5 throttle (returns []), F-6 !vision_in
        |  All failures: lifecycle does not crash; turn proceeds text-only; warning logged
        |  Capability flag gap: LAYER_INTERFACES.md §L3 uses ?vision_screen (drift artifact);
        |    canonical name is ?vision_in per §L1 + AGENT_AGNOSTIC_PROTOCOL.md (Architect to fix)
        |  New deps: mss>=9 (MIT) + Pillow>=10 (HPND/MIT-style) in [vision] extra
        |  v0.5 does NOT include: L5 Auga sense wrapper (deferred v0.7+), webcam (v0.5.x),
        |    periodic interval capture (v0.5.x), ring buffer recall (v0.5.x)
        |  See DATA_FLOW.md §4.10 (sight flow) and §15 (Sjón component diagram)
        |
        |  v0.5.1 — Periodic Sight (SHIPPED — extension of v0.5, NOT a new layer)
        |    SAME L3 Sjón substrate; no new layer added; on-demand path unchanged
        |    New: continuous background capture task (asyncio.Task, loops at interval_ms)
        |    New: ring buffer (collections.deque, maxlen=buffer_depth, default 5)
        |    New: attach_policy field — "latest" (default) | "all_buffered" | "none"
        |    New: continuous config field — sjon.screen.continuous: bool (default false)
        |    New: multi-monitor support — monitor_index=0 maps differently by mode:
        |           on-demand: config 0 → mss 1 (primary screen)
        |           continuous: config 0 → mss 0 (all-monitors composite)
        |           either mode: config N>=1 → mss N (specific display)
        |    New: MssBackend.list_monitors() helper
        |    Privacy invariant preserved: ring buffer cleared on Slokna; never to disk
        |    Backpressure: slow capture skips next tick rather than queuing
        |    See DATA_FLOW.md §4.10.7–§4.10.10 (periodic subsections) and §15 v0.5.1 extension
        |
        |  v0.5.2 — Webcam Capture (IN PROGRESS)
        |    SAME L3 Sjón substrate; no new layer; screen path unchanged
        |    New: WebcamCaptureBackend ABC + OpenCvBackend (cv2.VideoCapture) + NullWebcamBackend
        |      src/heretic/sjon/webcam.py — parallel to capture.py (MssBackend)
        |    New: SjonOrchestrator.snapshot_webcam() — mirrors snapshot() for webcam source
        |      pipeline: VideoCapture.read() → BGR ndarray → BGR[:,:,::-1] (→ RGB) → PIL.Image
        |                → thumbnail(max_width, max_height) → JPEG (default) or PNG
        |                → base64 → data URL → return [data_url]
        |      JPEG default: photographic content; ~80–200 KB vs ~800–1200 KB PNG;
        |                    configurable via sjon.webcam.format + sjon.webcam.jpeg_quality
        |    New: attach_policy field (sjon.webcam.attach_policy) — 4 values:
        |      "screen_only" (DEFAULT): webcam silently ignored even if enabled;
        |                               backward-compatible with all prior v0.5 configs
        |      "webcam_only": webcam attaches; screen NOT captured this turn
        |      "alongside":   both captured; webcam first then screen in content array
        |      "alternate":   toggles per turn; state tracked in CLI session (_sjon_alternate_turn_counter)
        |                     odd turns → webcam; even turns → screen
        |    New: SjonWebcamConfig fields completed:
        |      device_index (default 0), max_width (1280), max_height (720),
        |      format ("jpeg"), jpeg_quality (85), attach_policy ("screen_only")
        |    Privacy gate (STRONGER than screen):
        |      sjon.webcam.enabled defaults false — operator must explicitly opt in
        |      attach_policy "screen_only" (default) ignores webcam even when enabled
        |      two deliberate acts required to send any webcam frame
        |      webcam captures physical presence (face, room, environment) — not just screen output
        |      frames never written to disk; VideoCapture released at SLOKNA
        |      ring buffer NOT implemented (on-demand only; ring buffer deferred to v0.5.x)
        |    New dep: opencv-python>=4.8 added to [vision] extra in pyproject.toml
        |    See DATA_FLOW.md §4.10.11 (pipeline), §4.10.12 (attach_policy tree),
        |        §4.10.13 (privacy stance), §15 v0.5.2 extension (WebcamCaptureBackend diagram)
  v0.6  Hands at the Forge  Brúarhönd MCP   L5 Skilningr substrate + L5.5 Smiðja sense  IN PROGRESS
        |
        |  v0.6.0 — First Hand (IN PROGRESS)
        |    NEW: L5 Skilningr substrate (the sense hub layer) — ships for the first time
        |      src/heretic/skilningr/: SkilningrConfig, ToolDispatcher, errors
        |      designed to host multiple senses; Smiðja is the first
        |    NEW: L5.5 Smiðja sense — wraps Seidr-Smidja's Brúarhönd HTTP daemon
        |      src/heretic/skilningr/senses/smidja/: BrunhandHttpClient, ToolDefinitions,
        |        SmidjaSense, SmidjaError hierarchy
        |    NEW: Bifröst client extension — tool_call delta accumulator; emits ToolCall event
        |    NEW: CLI integration — builds tool registry at TENGSL; passes tools array to
        |      send_message; routes tool_calls via ToolDispatcher; multi-round loop with
        |      max_tool_call_rounds cap (default 5)
        |    NEW: Vébond protocol: sense.tool_call event (state, sense, tool_name, call_id)
        |    NEW: Frontend: LayerStatusPanel Smiðja row
        |    NEW: heretic.example.yaml: skilningr.smidja.* block
        |    Brúarhönd HTTP API: 6 tool surfaces exposed to agent via OpenAI tool_use format
        |      smidja.screenshot, smidja.click, smidja.type, smidja.hotkey,
        |      smidja.vroid_open, smidja.vroid_export
        |    Auth: bearer token from env var named in skilningr.smidja.token_env (never logged)
        |    Tailscale routing: when skilningr.smidja.host is a Tailscale name/IP, httpx
        |      connects directly — no special handling; Tailscale plumbed at OS level
        |    Failure modes: 7 (all return tool_result error JSON; turn never crashes)
        |      F-1 unreachable, F-2 auth, F-3 timeout, F-4 5xx, F-5 malformed,
        |      F-6 unknown tool, F-7 max rounds reached
        |    See DATA_FLOW.md §4.11 (tool flow) and §16 (Smiðja component diagram)
        |
        |  v0.6.1 — Second Anvil (SHIPPED)
        |    NEW: ForgeHttpClient — second HTTP client inside Smiðja sense (parallel to BrunhandHttpClient)
        |      wraps Seidr-Smidja Straumur REST API (/v1/avatars, /v1/inspect, /v1/assets, /health)
        |      independent endpoint (default http://127.0.0.1:8765), optional bearer token,
        |      120s default timeout (Blender renders are slow)
        |    NEW: SmidjaConfig.forge sub-block — ForgeConfig dataclass
        |      fields: enabled, endpoint, token_env (optional), request_timeout_seconds
        |    NEW: 3 Forge tools added to SMIDJA_TOOL_DEFINITIONS:
        |      smidja.forge_build_avatar  (POST /v1/avatars)
        |      smidja.forge_get_avatar    (GET /v1/avatars/{id})
        |      smidja.forge_inspect_avatar (POST /v1/inspect)
        |    NEW: Dual-half lifecycle — SmidjaSense.open() probes both arms independently
        |      either arm can be absent without affecting the other
        |      degradation matrix: full / Brúarhönd-only / Forge-only / both degraded
        |    NEW: Forge error class hierarchy: ForgeError → ForgeUnreachableError,
        |      ForgeTimeoutError, ForgeValidationError, ForgeServerError
        |    NEW: Forge failure modes F-1 through F-5 (see DATA_FLOW.md §4.11.9)
        |    See DATA_FLOW.md §4.11.7 (Forge dispatch), §4.11.8 (dual-half lifecycle),
        |        §4.11.9 (Forge failure modes), §16 v0.6.1 extension (ForgeHttpClient diagram)
        |
        |  v0.6.2 — More Senses (IN PROGRESS)
        |    NEW: Minni sense (filesystem) — senses/minni/
        |      tools: minni.read_file, minni.write_file, minni.list_directory
        |      sandbox: allowed_roots list (default ["~/heretic_workspace"]); path traversal blocked;
        |      no symlink-follow; 1MB file size cap; pure pathlib/io; no network, no subprocess
        |    NEW: Skepja sense (terminal) — senses/skepja/
        |      tools: skepja.run_command, skepja.get_working_directory
        |      sandbox: command_allowlist (default []); shlex.split; subprocess.run shell=False;
        |      60s timeout; 64KB output cap; env isolation (inherit_env: false default)
        |    NEW: Leið sense (HTTP fetch) — senses/leid/
        |      tools: leid.fetch_url, leid.extract_text
        |      sandbox: url_allowlist_patterns (default []); HTTPS preferred; HTTP allowed+warning;
        |      httpx GET only; no cookies; no JS; 1MB response cap; html.parser text strip
        |    NEW: skillingr/sandbox.py — shared primitives (path_within_allowed_roots,
        |      command_allowlist_check, url_allowlist_match) called by all three senses
        |    NEW: SandboxViolationError, CommandNotAllowedError, UrlNotAllowedError,
        |      FilesizeLimitError added to errors.py
        |    All three senses default disabled; each isolated (failure of one does not affect others)
        |    16 total tools when all four senses enabled (9 Smiðja + 3 Minni + 2 Skepja + 2 Leið)
        |    See DATA_FLOW.md §4.12 (Minni), §4.12.1 (Skepja), §4.12.2 (Leið),
        |        §4.12.3 (cross-cutting sandbox invariants), §16 (Four Senses Component Diagram)
        |
        |  v0.6.x — MCP Server (IN PROGRESS)
        |    NEW: McpServer adapter module (src/heretic/skilningr/mcp_server.py)
        |    NEW: heretic mcp --transport stdio | http  (third CLI launch mode)
        |    NEW: McpServerConfig + McpServerError hierarchy in SkilningrConfig
        |    Door 1 (OpenAI tool_use) unchanged; Door 2 (stdio) + Door 3 (HTTP/SSE) added
        |    ToolDispatcher: single backend shared across all three transport doors
        |    tools/list: 16 tool defs converted from OpenAI schema → MCP inputSchema
        |    tools/call: routes through existing ToolDispatcher (no new dispatch logic)
        |    initialize handshake: capabilities = {tools: {}} (resources/prompts deferred)
        |    Auth: bearer token from env on HTTP transport; stdio trust boundary = pipe
        |    allow_remote_bind: false default; Tailscale-routable via explicit opt-in
        |    See DATA_FLOW.md §4.13 (MCP transport flow + three-door diagram)
        |        DATA_FLOW.md §16 v0.6.x (McpServer module + ToolDispatcher reuse diagram)
        |  v0.6.x further backlog:
        |    v0.6.2.1: headless browser (Leið via playwright)
        |    v0.6.x.1: MCP resources/* hosting (deferred from v0.6.x scope)
  v0.7  Files & Terminal    FS + terminal   L5.1 + L5.2 (filesystem + terminal senses)
        |  v0.7 also: L5.11 Tunga sense (tunga.speak MCP tool — agent-callable TTS)
  v0.7.5 First Drink     Mímisbrunnr        L5.9 light (library sense + Norse seed corpus)
  v0.8  The Open Web     Browser MCP        L5.3 (browser sense)
  v0.9  The Painter      Photopea MCP       L5.4 (photopea sense)
  v0.10 The Longhouse Beyond VRChat + MindSpark  L5.6 (vrchat sense) + L5.9 MindSpark backend
  v0.11 Correspondence   AgentMail          L5.7 (agentmail sense)
  v1.0  First Manifestation  full polish    L5.8 (Nýr Limr custom plugin system)
  v1.x+ New Limbs           community MCPs Nýr Limr slots open
  v2.x  (stretch)           UE5/VR          optional photorealistic layer
```

**v0.2 Tunga — layer topology addition:**

The following connections become active when v0.2 ships:

```
  LAPTOP                                      PI
  ------                                      --
  [L1 Bifröst SSE stream parser]
       |
       | text_delta per token
       v
  [L2 Rödd: Tunga orchestrator]          ChatterBox TTS :7851
       |  sentence-boundary chunker            |
       |  synthesis queue                      |
       +--- POST /v1/audio/speech -----------> |
       <--- WAV bytes ------------------------ |
       |
       v
  [AudioPlayback: sounddevice → speakers]
```

This Tunga path is purely automatic in v0.2 (pass-through from Bifröst). The agent does not
call a tool to speak — the body speaks automatically as the spirit's words arrive. The
agent-callable `tunga.speak` tool surface (L5.11) comes in v0.7.

---

## 8. Security Topology

*Drawn lightly — full security model deferred to docs/architecture/LAYER_INTERFACES.md.*

```
  Threat boundary points:
  1. Bifröst wire (L1)    — API key in HTTP header; Tailscale provides transport encryption
  2. Sense tool calls (L5) — agent can call any enabled sense; no sandbox yet in v0.x
  3. Seidr-Smidja (L5.5)  — Brúarhönd auth: bearer token + constant-time comparison
                             path-traversal blocked; concurrent session lock HTTP 423
  4. Terminal sense (L5.2) — highest risk: agent can run arbitrary commands
                             restrict via allowlist in heretic.yaml (Architect decision)
  5. FileSystem sense (L5.1) — scoped to configured root path; no traversal outside root

  Primary defense: the user runs HERETIC on their own hardware, on their own Tailscale
  network, with their own agent. The primary threat model is misconfigured tool exposure,
  not external attackers. Network perimeter = Tailscale ACL policy.
```

See also: `PRIOR_PLANNING_TRIAGE.md` §proposed_system_report/06 for threat category taxonomy
carried forward from pre-manifesto security spec.

---

## 9. The "Pi as Shrine, Laptop as Ritual Space" Made Concrete

The Body Manifesto contains this image: *"The Pi is the shrine — Hermes lives there always.
H.E.R.E.T.I.C. is the ritual space — the body the spirit wears when called into Midgard."*

What this looks like running on a desk:

```
  ON THE DESK (physical reality during a ceremony):
  =================================================

  Laptop screen:        Eldahús open, fire burning, ceremony active
                        Agent responses displayed (text + voice)
                        Status of each enabled sense shown

  Laptop mic:           Listening for user speech → Hlust → Whisper.cpp

  Laptop speakers:      Playing ChatterBox TTS audio → agent's voice in the room

  Laptop display:       Available to Sjón for screen capture on demand

  Blender (if open):    Running on laptop, receiving commands from the blender sense
                        (Smiðja) via Seidr-Smidja — the agent sculpts in your 3D space

  In the closet (Pi):   Hermes Agent quietly running — the spirit in its shrine
                        Waiting to be called, processing when called
                        Memory of conversations, personality, full intelligence — all on Pi

  On the Tailscale mesh: The bridge between them — invisible, always present
                         WireGuard keepalives keeping the path warm
                         The ritual space and the shrine, connected

  When the ceremony ends:
  Laptop screen:        Eldahús shows fire dying (Slokna state)
                        Then closes — no background processes
                        RAM freed, no drain

  In the closet (Pi):   Hermes still running, unchanged
                        Waiting for the next ceremony
```

---

## 10. The Naming Field — Body Parts on a Map

The naming document (`docs/NAMING.md`) made a promise: the senses are named as body-parts
or faculties because *they form the body*. This overview honors that.

```
  The Body of HERETIC

                        [Grunnr — the ground it stands on]
                         |
               +----------+-----------+
               |   Bifröst — the      |
               |   spine / nerve      |
               |   connecting to the  |
               |   remote mind        |
               +----------+-----------+
                         |
            +------------+------------+
            |                         |
       [Rödd — voice]            [Sjón — sight]
       Hlust (ear)               screen capture
       Tunga (tongue)            webcam
            |                         |
            +------------+------------+
                         |
                    [Vébond — the sacred circle]
                    ceremony controls, UI shell
                         |
                    [Skilningr — discernment]
                    the sense hub, the organizer
                         |
         +---------------+------------------+
         |       |       |       |          |
       [Auga]  [Hönd] [Smiðja] [Leið]  [Minni]
        eye    hand    forge    path    memory
         |       |       |       |          |
       [Skepja] [Boð] [Líkami] [Mímisbrunnr] [Nýr Limr]
       creation message  body     wisdom well  new limbs
```

Every sense is a faculty of the same body. They grow from the same ground (Grunnr).
They speak through the same nerve (Bifröst) to the same mind (Hermes on Pi).
The naming field is not decoration — it is the architecture.

---

*Drawn by Védis Eikleið, Cartographer for Vibe Coding, 2026-05-07. Updated 2026-05-08 (v0.5 in-progress). Updated 2026-05-08 (v0.6 in-progress — L5 Skilningr substrate + Smiðja first hand). Updated 2026-05-08 (v0.6.1 in-progress — Smiðja second anvil: ForgeHttpClient + dual-half lifecycle). Updated 2026-05-08 (v0.6.2 in-progress — three new senses: Minni library, Skepja terminal, Leið road; §7 v0.6.2 milestone block added; §8 security topology references Skepja + Minni). v0.6.1 marked SHIPPED.*
*A body well-mapped is a body that knows itself.*
*Seven senses charted: the mouth speaks (Tunga), the ear hears (Hlust), the eye sees (Sjón), the hand reaches (Smiðja), the library remembers (Minni), the kitchen shapes (Skepja), the road connects (Leið).*
*The workshop holds two anvils: one for the living GUI, one for the headless forge.*
*Three new rooms open in the longhouse. The spirit can only inhabit what has been named.*
