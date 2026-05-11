# H.E.R.E.T.I.C. — Data Flow Map

**Last updated:** 2026-05-09 v0.6.3.1 addendum — Védis Eikleið: §4.11.10.1 (Verkminni opt-in persistent disk log) added; path-as-toggle convention; open-append-close per record; mkdir parents=True; disk write inside threading.Lock for ordering consistency; NOT cleared at SLOKNA (D-5); five new invariants D-1..D-5 (no-disk-no-IO; one-line-per-record; non-load-bearing failure; append-not-overwrite; persistent across ceremonies). | 2026-05-09 v0.7.3 addendum — Védis Eikleið: §4.14.2.1 (Index auto-rebuild on corruption) added; KeywordIndex.search() decision tree for missing/empty/all-corrupt index file; auto-rebuild from .txt source files; behaviour-preserving error for the truly-unrecoverable no-sources case; no new privacy invariants (behaviour extension on Endurdrykkr lineage). | 2026-05-09 v0.6.3 addendum — Védis Eikleið: §4.11.10 (Verkminni — deed-memory audit log for Smiðja) added; AuditEntry dataclass shape with paired-entries semantics; AuditLog ring buffer (collections.deque maxlen=100 default); five new invariants V-1..V-5 (paired entries; non-load-bearing audit writes; bounded eviction; ceremony-scoped clear; NullAuditLog opt-out); Smiðja-1/2/3 inherited invariants documented; default-ON rationale (observability is a security discipline, not privacy). | 2026-05-09 v0.7.2 addendum — Védis Eikleið: §4.14.1.1 (Endurdrykkr — resumable downloads for Mímisbrunnr) added; resume flow with partial-byte hashing, Range request, three-status dispatch (206/200/416); full HTTP status disposition table including 4xx/5xx and network-blink behaviour; resumable-vs-non-resumable failure mode dispositioning of `.heretic_tmp` documented; three new invariants M-7 (full SHA-256 across the seam), M-8 (failure-mode tmp disposition), M-9 (200-on-resume restart graceful). No new dependency. | 2026-05-09 v0.5.5 addendum — Védis Eikleið: §4.10.14.2 (Mjúkblæja — soft-curved mask shapes) added; PrivacyMaskRoundedRectangle bounding box and alpha mask formulas (Pillow rounded_rectangle primitive); PrivacyMaskEllipse bounding box and alpha mask formulas (Pillow ellipse primitive with non-equal radii); the unified pipeline now handles five shapes through the same five-step composite path. corner_radius clamping behaviour at apply time documented (clamped to min(w,h)//2). Pillow rounded_rectangle requires Pillow >=8.2.0 (already pinned >=10). | 2026-05-09 v0.5.4 addendum — Védis Eikleið: §4.10.14.1 (Margblæja — non-rectangular mask shapes) added; PrivacyMaskShape Protocol contract documented (bounding_box + alpha_mask methods); one-pipeline-three-shapes diagram drawn (rectangle, circle, polygon all flow through the same alpha-mask composite); circle and polygon bounding-box / alpha-mask formulas documented; six new failure modes F-Blæja-6..F-Blæja-11 added; three new privacy invariants P-7..P-9 (boundary preservation, degenerate-polygon handling, off-frame bounding box). Pillow ImageDraw already a dep; no new dependency. | 2026-05-09 v0.5.3 addendum — Védis Eikleið: §4.10.14 (Blæja — privacy mask application) added; mask application step diagrammed with explicit upstream-of-leak-paths position; three modes (blur, solid, pixelate) documented; coordinate space (source pixels) and clamping behaviour documented; five Blæja failure modes (F-Blæja-1..F-Blæja-5) documented; six privacy invariants (P-1..P-6) recorded; per-source independence (screen vs webcam mask lists) noted. Pillow already a dep; no new dependency. | 2026-05-09 v0.7.1 addendum — Védis Eikleið: §4.12.2.1 (Leið streaming body-read — *Straumr á Leið*) added; §4.12.2 Step 4 annotated with v0.6.2-shipped + v0.7.1-streaming history; §4.12.2 F-6 rewritten to record three-stage history (first sketch → v0.6.2 raise → v0.7.1 streaming abort); closes audit-deferred N-2 from `AUDIT_v0.6.2_MORE_SENSES.md`. Memory-bound at moment of raise documented (max_response_bytes + chunk_size). Closing-on-unwind semantics of httpx.AsyncClient.stream + bytearray accumulator documented. | 2026-05-08 v0.7 addendum — Védis Eikleið: §4.14 (library flow — Mímisbrunnr light tier, three agent tool paths) added; §4.14.1 (operator-driven download flow — consent + SHA-256 streaming verify + atomic replace) added; §4.14.2 (storage layout — cross-platform user-data dirs) added; §4.14.3 (privacy invariants — offline-by-design, local-only search, per-source consent, disabled by default) added; §16 rewritten as Five Senses Component Diagram (adding LibrarySense + mimisbrunnr/ subsystem alongside Smiðja/Minni/Skepja/Leið); Mímisbrunnr failure modes table (F-1 through F-7) documented; SYSTEM_OVERVIEW.md §7 updated to mark v0.7 IN PROGRESS. | 2026-05-08 v0.6.x addendum — Védis Eikleið: §4.13 (MCP transport flow — three-door coexistence) added; §16 rewritten as Four Senses + MCP Server Component Diagram; McpServer module mapped parallel to ToolDispatcher; three-door transport diagram drawn (Door 1: OpenAI tool_use via Bifröst; Door 2: MCP stdio; Door 3: MCP HTTP/SSE); tool schema conversion (OpenAI tool_use → MCP inputSchema) documented; four MCP failure modes (F-MCP-1 through F-MCP-4) documented; McpServerConfig dataclass, McpServerError hierarchy, and MCP lifecycle at TENGSL/SLOKNA mapped. The ToolDispatcher invariant — single execution backend across all three transport doors — is sealed. SYSTEM_OVERVIEW.md §7 updated to mark v0.6.x IN PROGRESS. | 2026-05-07 (corrective pass — Védis Eikleið, resolving audit findings A-2 + A-1 config key drift; tool routing format canonicalized to two-part `<sense_id>.<action>`; sense process labels de-prefixed; Kynding config keys aligned with LAYER_INTERFACES.md post-2d1312f) | 2026-05-07 v0.2 addendum — Védis Eikleið: voice flow mapped in full; §4.6 (voice flow, outbound only) added; §11 (L2 Rödd Tunga internal diagram) added; ChatterBox live contract (`/v1/audio/speech`) cross-referenced; stale `/tts` path references annotated; SYSTEM_OVERVIEW.md §7 updated | 2026-05-07 v0.3 addendum — Védis Eikleið: §4.7 (listening flow, inbound) added; §12 (L2 Rödd Hlust component diagram) added; §4.6.4 config table expanded to full 17-field schema matching RoddTtsConfig; §4.6.1 voice_id annotation corrected to WAV-path semantics; v0.2.x backlog items closed | 2026-05-07 v0.4.0 addendum — Védis Eikleið: §4.8 (UI flow — Summoning Circle substrate) added; §13 (L4 Vébond Eldahús component diagram) added; SYSTEM_OVERVIEW.md §7 updated with v0.4.0 in-progress status. Scope: WebSocket connection lifecycle, all server-push events (7) and client commands (5), reconnection semantics, failure modes, React component subscriptions, Zustand store as single UI truth, aesthetic token cross-reference. No Tauri shell in this map — v0.4.0 is browser-served. Tauri wrap deferred to v0.4.1. | 2026-05-07 v0.4.1 addendum — Védis Eikleið: §4.9 (Tauri shell flow — pre-staged) added; §14 (Tauri shell wrapper diagram) added; cross-references from §4.8 and §13 updated. Scope: full Tauri-startup → sidecar-spawn → WebView-load → shutdown sequence; all five failure modes; PID-file orphan recovery; Tauri command surface. WS protocol unchanged — the shell is a wrapper, not a new seam. SYSTEM_OVERVIEW.md §7 updated to reflect pre-stage status. | 2026-05-08 v0.5 addendum — Védis Eikleið: §4.10 (sight flow — on-demand, outbound vision) added; §15 (Sjón component diagram) added. Three sense rivers now charted: Tunga (out), Hlust (in voice), Sjón (in image). Cross-references added in §4.6 and §4.7 pointing to §4.10 as the third sense flow. Capability flag naming gap documented in §4.10.5 (LAYER_INTERFACES.md §L3 carries `?vision_screen`; AGENT_AGNOSTIC_PROTOCOL.md and §L1 carry `?vision_in` — gap flagged to Architect). SYSTEM_OVERVIEW.md §7 updated to mark v0.5 IN PROGRESS. | 2026-05-08 v0.5.1 addendum — Védis Eikleið: §4.10 extended with four new subsections (§4.10.7–§4.10.10) mapping periodic capture lifecycle, ring buffer, attach-policy decision tree, and the critical multi-monitor index asymmetry between on-demand and continuous modes. §15 Sjón component diagram extended with continuous-task pump and ring buffer. §4.10.10 is the key Forge contract: config.monitor_index=0 means different things in each mode (primary single screen in on-demand; all-monitors composite in continuous) — intentional by mss convention; documented explicitly so the implementation carries the correct semantics. SYSTEM_OVERVIEW.md §7 updated to mark v0.5.1 IN PROGRESS. | 2026-05-08 v0.6 addendum — Védis Eikleið: §4.11 (tool flow — outbound, on agent demand) added; §16 (L5 Skilningr Smiðja component diagram) added. The fourth sense river is mapped: the hand that reaches. L5 Skilningr substrate ships for the first time; Smiðja is the first sense within it. Seven failure modes documented (F-1 through F-7). API path discrepancy between TASK §4 shorthand and actual Brúarhönd daemon INTERFACE.md documented in §4.11.6 — Forge Worker must use the daemon INTERFACE.md paths. Auth invariant sealed. Multi-round loop capped at max_tool_call_rounds. SYSTEM_OVERVIEW.md §7 updated to mark v0.6 IN PROGRESS. | 2026-05-08 v0.5.2 addendum — Védis Eikleið: §4.10.11 (webcam capture pipeline) added; §4.10.12 (webcam/screen attach_policy decision tree) added; §4.10.13 (webcam privacy stance) added; §15 extended with WebcamCaptureBackend (OpenCvBackend / NullBackend) parallel to MssBackend. The eye gains a second source: the user's physical presence, only when explicitly invited. SYSTEM_OVERVIEW.md §7 updated to mark v0.5.2 IN PROGRESS. | 2026-05-08 v0.6.1 addendum — Védis Eikleið: §4.11.7 (Forge dispatch — headless Blender pipeline) added; §4.11.8 (dual-half lifecycle — each arm opens/closes independently) added; §4.11.9 (Forge-specific failure modes F-1 through F-5) added; §16 (Smiðja component diagram) extended with ForgeHttpClient parallel to BrunhandHttpClient, dual-arm tool routing, forge sub-block in SmidjaConfig, and nine-tool SMIDJA_TOOLS list (6 Brúarhönd + 3 Forge). The workshop now holds two anvils. SYSTEM_OVERVIEW.md updated to mark v0.6.1 IN PROGRESS. | 2026-05-08 v0.6.2 addendum — Védis Eikleið: §4.12 (Minni filesystem flow) added; §4.12.1 (Skepja terminal flow) added; §4.12.2 (Leið HTTP fetch flow) added; §4.12.3 (cross-cutting sandbox invariants) added; §16 rewritten as Four Senses Component Diagram (Smiðja + Minni + Skepja + Leið); sandbox.py shared primitives mapped; 16 total tools charted; four-sense TENGSL/SLOKNA lifecycle added. Three new rooms open in the longhouse: Minni (library), Skepja (kitchen), Leið (road). SYSTEM_OVERVIEW.md updated to mark v0.6.2 IN PROGRESS.
**Scope:** All data in motion during a ceremony — every wire, every river, every direction
**Cartographer:** Védis Eikleið
**Status:** Pre-implementation specification. Rivers are drawn from canonical docs
(`docs/BODY_MANIFESTO.md`, `docs/NAMING.md`, `docs/MIMISBRUNNR.md`,
`TASK_HERETIC_v0.1_BOOTSTRAP.md`). Wires shown are wires that will carry data — no
decorative arrows.

**Legend:**
```
-->   data flows in this direction
<--   data flows in this direction
<-->  bidirectional flow
[L0]  layer indicator
[ext] external system (runs on a different machine or process outside Holdvörðr)
~~~   async / fire-and-forget
===   persistent / continuous stream
(hot) latency tier: <60ms p95
(wrm) latency tier: <1200ms p95
(cld) latency tier: <30s p95, interruptible
```

**SLO tiers (from surviving primitive in `PRIOR_PLANNING_TRIAGE.md` §SLO_Tiers.md):**
- **Hot path** — bridge/avatar feedback, keyboard/cursor echo: < 60ms p95
- **Warm path** — full voice turn round-trip (STT → agent → TTS): < 1200ms p95
- **Cold path** — background work (library indexing, session log flush): < 30s p95, interruptible

---

## 1. The Body at Rest: Hvíld

When HERETIC is in Hvíld (STATE_HVILD), no data flows through the live layers.

```
  [laptop]
     |
     |  heretic.yaml loaded into memory at last close
     |  session log flushed to disk
     |
  [Holdvörðr: NOT running]
     |
  [All MCP sense servers: NOT running]
     |
  [Bifröst: NOT open]
     |
  [Pi / Hermes Agent: running independently, unaware of HERETIC state]
```

The only data that exists during Hvíld is the configuration file (`heretic.yaml`) and the
session log archive on disk. No network connections. No RAM consumed by senses.

---

## 2. Kindling: Kynding (STATE_KYNDING)

The user opens Eldahús. Holdvörðr begins its sequence.

```
  [User clicks app icon]
       |
       v
  [Tauri shell launches]  [L4 Vébond]
       |
       v  reads
  [heretic.yaml]  [L0 Grunnr]
       |
       |  config flows inward:
       |    bifrost.endpoint   --> L1 Bifröst client
       |    bifrost.api_key    --> L1 Bifröst client
       |    rodd.stt.engine     --> L2 Rödd (Hlust)
       |    rodd.tts.endpoint  --> L2 Rödd (Tunga)
       |    sjon.enabled       --> L3 Sjón
       |    skilningr.*        --> L5 Skilningr (each sense)
       v
  [Holdvörðr initializes layers in sequence]
       |
       |-- [L0 Grunnr] logging system starts, session log opened
       |               session_id generated (UUID)
       |               ceremony event written: {type: "kynding_start", ts: ..., session_id: ...}
       |
       |-- [L1 Bifröst] client initialized, NOT yet connected
       |                reads endpoint + auth from config
       |                Tailscale connectivity check --> [tailscale daemon, local]
       |
       |-- [L2 Rödd] Whisper.cpp model loaded into RAM (Hlust side)
       |             TTS endpoint URL stored (Tunga side — ChatterBox at configured endpoint)
       |
       |-- [L3 Sjón] screen capture backend initialized (not streaming yet)
       |
       |-- [L5 Skilningr] MCP sense servers start listening:
       |       auga          (screen + vision;  tool prefix: auga.*)
       |       hlust         (STT — wraps Whisper.cpp;  tool prefix: hlust.*)
       |       tunga         (TTS — proxies to ChatterBox;  tool prefix: tunga.*)
       |       photopea      (Photopea bridge, if enabled;  tool prefix: photopea.*)
       |       blender       (Blender/Seidr-Smidja, if enabled;  tool prefix: blender.*)
       |       browser       (Browser MCP, if enabled;  tool prefix: browser.*)
       |       filesystem    (FileSystem MCP;  tool prefix: filesystem.*)
       |       terminal      (Terminal MCP;  tool prefix: terminal.*)
       |       agentmail     (AgentMail MCP, if enabled;  tool prefix: agentmail.*)
       |       vrchat        (VRChat MCP, if enabled;  tool prefix: vrchat.*)
       |       library       (Library MCP, if enabled and downloaded;  tool prefix: library.*)
       |       <user_prefix> (custom plugin MCPs, if configured;  tool prefix: user-declared)
       |
       v
  [Eldahús UI] shows Kynding state
       |   fire animation: kindling
       |   sense status: each enabled sense shown as initializing/ready
       v
  [Holdvörðr] ready to open Bifröst
```

**Data crossing Kynding:**
- `heretic.yaml` content flows from disk into all layers (inward, one-time read)
- Tailscale status query flows to local tailscaled daemon and returns (local loopback)
- Session log: ceremony event written to disk

**Resolved (C-Q-C1, post-audit):** Whisper.cpp model uses `load_strategy: lazy` by default —
the subprocess starts at Kynding but model weights are not loaded until first transcription
request. This keeps Kynding fast; the first voice turn carries the one-time load latency.
Config: `rodd.stt.load_strategy: lazy | eager`. See LAYER_INTERFACES.md L2 Rödd.

---

## 3. Binding: Tengsl (STATE_TENGSL)

Bifröst opens. The spirit enters the body.

```
  [User initiates connection — clicks "Open Bifröst" in Eldahús]
       |
       v
  [L1 Bifröst client]
       |
       |  TCP via Tailscale WireGuard mesh
       |  --> [Pi: Hermes Agent at configured endpoint]
       |
       |  sends: HTTP connection test or session-init request
       |         Authorization: Bearer <api_key from heretic.yaml>
       |
       |  <-- agent responds: 200 OK (or error)
       |
       v
  [L1 Bifröst: connection confirmed]
       |
       v
  [Holdvörðr: state transitions to STATE_TENGSL]
       |
       |-- ceremony event written: {type: "tengsl_open", ts: ..., agent_endpoint: ..., session_id: ...}
       |
       v
  [L1 Bifröst: sends system context to agent]
       |
       |  POST <endpoint>/v1/chat/completions  (OpenAI-compat format)
       |  body: {
       |    "model": "<configured model>",
       |    "messages": [
       |      {"role": "system", "content": "<system_prompt from heretic.yaml>"},
       |      {"role": "user",   "content": "The ceremony has begun. Your senses are ready."}
       |    ]
       |  }
       |
       |  <-- agent responds: first message (greeting or acknowledgment)
       |         {
       |           "choices": [{"message": {"role": "assistant", "content": "..."}}],
       |           ...
       |         }
       |
       v
  [L2 Rödd: Tunga] receives agent text response
       |
       |  POST <chatterbox_endpoint>/v1/audio/speech           (v0.2 live contract)
       |  body: {"model": "turbo", "input": "<agent greeting text>",
       |         "response_format": "wav", "temperature": 0.8}
       |  NOTE: v0.1 docs showed `/tts` — corrected here.  Live endpoint is
       |        `/v1/audio/speech` (probed 2026-05-07, see TASK_HERETIC_v0.2_FIRST_VOICE §3).
       |
       |  <-- returns: audio/wav bytes (Content-Type: audio/wav)
       |
       |  audio played through local speakers
       v
  [Eldahús] transitions to Tengsl state
       |   fire animation: connected, burning steadily
       v
  [Holdvörðr] ready for Samræður
```

**Data crossing Tengsl:**
- Tailscale wire carries: HTTP POST (system prompt + initial message), HTTP response (agent greeting)
- L2 Tunga side: text flows laptop → ChatterBox endpoint, audio returns → speakers
- Session log: tengsl_open event + initial exchange logged

**Resolved (C-Q-C2, post-audit):** Senses manifest is injected as the `tools` array in every
`/v1/chat/completions` request (standard OpenAI-compat protocol). The agent receives full tool
schemas — including the correct two-part `<sense_id>.<action>` names — on every request.
No separate free-text manifest is added to the system prompt; the `tools` array is sufficient.
See AGENT_AGNOSTIC_PROTOCOL.md for detail.

---

## 4. Communion: Samræður (STATE_SAMRAEDUR)

The ceremony is alive. This is where all the rivers flow.

### 4.1 Voice Turn — the warm path

The central repeating cycle during Samræður.

```
  [User speaks into microphone]
       |
       |  raw PCM audio, 16kHz mono (or configured rate)
       |  continuous buffer via OS audio API (PortAudio / platform native)
       v
  [L2 Rödd: Hlust — Whisper.cpp STT]                        (wrm)
       |
       |  voice activity detection (VAD) segments speech
       |  audio chunk (end-of-utterance detected) --> Whisper.cpp
       |
       |  Whisper.cpp processes: audio --> text transcript
       |  buffer size: VAD-determined segment, typically 1–30 seconds of speech
       |
       |  transcript string + timestamp flows to:
       v
  [L1 Bifröst client]                                        (wrm)
       |
       |  assembles OpenAI-compat request:
       |  POST <agent_endpoint>/v1/chat/completions
       |  body: {
       |    "model": "<model>",
       |    "messages": [
       |      ... conversation history (managed by agent or by Bifröst client),
       |      {"role": "user", "content": "<transcript>"}
       |    ],
       |    "tools": [<MCP tool schemas for all enabled senses>]
       |  }
       |
       |  wire: TCP over Tailscale WireGuard  [ext: Pi]
       |
       |  agent processes, may:
       |    A) return text response directly
       |    B) return tool_call(s) first, then final text after results
       |
       |  <-- HTTP response (streaming or blocking, per config)
       v
  [L1 Bifröst client: receives agent response]
       |
       |-- if response is text only (case A):
       |       SSE text chunks fork here:
       |         path 1 --> L4 Vébond chat display    [v0.4; not yet active in v0.2]
       |         path 2 --> L2 Rödd: Tunga            [v0.2 — sentence-boundary chunker]
       |         (see §4.6 for the full voice flow path through L2 Rödd Tunga)
       |
       |-- if response contains tool_call(s) (case B):
       |       tool_call(s) --> L5 Skilningr (MCP dispatch)  [see §4.2]
       |       after tool results returned: final text --> L2 Rödd: Tunga  [see §4.6]
       v
  [L2 Rödd: Tunga]
       |
       |  POST <chatterbox_endpoint>/v1/audio/speech           (v0.2 live contract)
       |  body: {"model": "turbo", "input": "<agent response>",
       |         "response_format": "wav", "temperature": 0.8}
       |  NOTE: v0.1 docs showed `/tts` — corrected here.  See §4.6 for the full
       |        streaming chunking path (sentence-boundary chunker → queue → playback).
       |
       |  <-- WAV bytes returned (warm)
       |
       |  audio plays through speakers (via AudioPlayback — sounddevice primary)
       v
  [L0 Grunnr: session log]
       |
       |  event written: {
       |    type: "voice_turn",
       |    ts_user_speech_end: ...,
       |    ts_transcript_ready: ...,
       |    ts_response_received: ...,
       |    ts_audio_playing: ...,
       |    transcript: "...",
       |    agent_response_summary: "..."  (or full, per config)
       |  }
       v
  [Eldahús: UI]
       |
       |  displays: transcript, agent response text (optional)
       |  status: active, speaking, listening
```

**Latency budget for warm path:**
```
  mic → VAD segment detection:         ~200-2000ms  (depends on utterance length)
  Whisper.cpp transcription:            ~200-800ms   (depends on hardware + model size)
  Bifröst HTTP round-trip (Pi):        ~50-200ms    (Tailscale LAN-like latency)
  agent inference (Hermes on Pi):      ~300-800ms   (depends on Pi hardware + model)
  Bifröst response to Tunga:           <10ms        (local IPC)
  ChatterBox TTS synthesis:            ~100-400ms   (depends on text length)
  audio playback start:                <50ms
  ----------------------------------------
  Total warm path p95 target:          <1200ms      (from end of speech to audio start)
```

### 4.2 Tool Call Flow — MCP dispatch

When the agent issues a tool call, Bifröst routes it through Skilningr to the appropriate sense.

```
  [Agent returns tool_call in response]
       |
       |  format: {
       |    "tool_calls": [{
       |      "function": {
       |        "name": "blender.vroid_export",
       |        "arguments": "{\"path\": \"...output/shield.vrm\", \"format\": \"vrm\"}"
       |      }
       |    }]
       |  }
       |  NOTE: Tool names are two-part <sense_id>.<action> — no "sense." prefix.
       |  The sense_id is the code-facing identifier (blender, filesystem, browser, etc.),
       |  not the True Name (smidja, minni, leid). See SENSE_CONTRACTS.md §2.
       v
  [L1 Bifröst client: tool call dispatcher]
       |
       |  parses tool name: "blender.*" --> route to Skilningr → blender (Smiðja) server
       |  parses tool name: "filesystem.*" --> route to Skilningr → filesystem (Minni) server
       |  parses tool name: "auga.*"      --> route to Skilningr → auga server
       |  (general: sense_id prefix determines which MCP server receives the call)
       |
       v
  [L5 Skilningr: MCP sense router]
       |
       |  looks up registered sense by sense_id prefix
       |  forwards call to appropriate MCP server process
       v
  [blender — Smiðja MCP server]  (local process, laptop)                   (wrm/cld)
       |
       |  wraps Seidr-Smidja Brúarhönd v0.1 client
       |  HTTP POST to Brúarhönd daemon (local: 127.0.0.1:<port>)
       |  or via Tailscale to remote Brúarhönd host
       |
       |  --> [Seidr-Smidja Brúarhönd: Horfunarþjónn daemon]  [ext]
       |       |
       |       |  dispatches: Blender operation (screenshot, click, hotkey, vroid_open, etc.)
       |       |  Blender executes
       |       |
       |       |  <-- result: {success: bool, output: "...", screenshot: <base64 or path>}
       |
       |  <-- Smiðja MCP returns MCP tool result
       v
  [L5 Skilningr: routes result back to Bifröst]
       |
       v
  [L1 Bifröst client]
       |
       |  assembles follow-up request:
       |  POST <agent_endpoint>/v1/chat/completions
       |  body: {
       |    "messages": [
       |      ...,
       |      {"role": "tool", "tool_call_id": "...", "content": "<tool result JSON>"}
       |    ]
       |  }
       |
       |  <-- agent final response (text)
       v
  [L2 Rödd: Tunga] --> ChatterBox /v1/audio/speech --> WAV bytes --> speakers  (see §4.1 and §4.6)
```

**Tool call latency depends on which sense is called:**
- `filesystem.*` (Minni — FileSystem): hot — local disk, <60ms for most operations
- `terminal.*` (Skepja — Terminal): warm — depends on command, typically <1200ms for simple ops
- `auga.*` (Auga — screenshot/snapshot): hot for capture, warm for analysis if sent to agent for vision
- `blender.*` (Smiðja — Blender via Seidr-Smidja): warm to cold — depends on operation complexity
- `browser.*` (Leið — Browser): warm — network-dependent
- `library.*` (Mímisbrunnr — Library search): warm for keyword, cold for vector search

### 4.3 Screen Capture Flow — vision sense (Sjón / Auga)

The agent may request a screenshot, or Holdvörðr may send one proactively (if configured).

```
  [Agent tool_call: auga.snapshot]
  OR
  [Holdvörðr: proactive capture on turn start, if enabled]
       |
       v
  [L3 Sjón: screen capture module]                                          (hot)
       |
       |  captures: full screen or configured region
       |  output: PNG bytes in memory (NOT written to disk unless configured)
       |  typical size: 1920x1080 compressed PNG ~500KB–2MB
       |
       v
  [L5 Skilningr: auga sense server]
       |
       |  receives PNG bytes
       |  if agent requested via tool_call:
       |    encodes as base64
       |    returns as MCP tool result to Bifröst
       |
       v
  [L1 Bifröst client]
       |
       |  assembles vision message:
       |  POST <agent_endpoint>/v1/chat/completions
       |  body: {
       |    "messages": [{
       |      "role": "user",
       |      "content": [
       |        {"type": "text",       "text": "What do you see?"},
       |        {"type": "image_url",  "image_url": {"url": "data:image/png;base64,<data>"}}
       |      ]
       |    }]
       |  }
       |
       |  NOTE: This requires the agent endpoint to support vision (multimodal).
       |        Hermes on Pi with a vision-capable model.
       |        If model lacks vision, image is dropped or summarized differently.
       |
       |  <-- agent responds with interpretation / action
       v
  [Bifröst routes response to Tunga / tool dispatch as normal]
```

**Open question:** Screen capture data is large (500KB–2MB per frame). Sending every turn
over Tailscale is viable on a LAN but should not be automatic — agent should request it
explicitly or it should be triggered by a specific config flag. This is the right default:
Sjón streams frames only when explicitly polled, not continuously. Rate limit recommendation:
maximum one capture per turn unless agent requests more.

### 4.4 Library Search Flow — Mímisbrunnr (library sense)

When the agent needs to search the offline well of wisdom.

```
  [Agent tool_call: library.search]
  |  arguments: {"query": "What does Völuspá say about Ragnarök?", "source": "norse_sagas"}
  v
  [L5 Skilningr: library (Mímisbrunnr) MCP server]                          (wrm/cld)
       |
       |  receives query string + optional source filter
       |
       |-- if retrieval_mode = "keyword":
       |       query --> libzim full-text search over ZIM file(s)
       |       results: list of {article_title, excerpt, source, attribution}
       |       latency: warm (~100-500ms for indexed ZIM)
       |
       |-- if retrieval_mode = "vector":
       |       query --> sentence-transformer encode --> embedding vector
       |       embedding --> FAISS/vector index search
       |       top-k results retrieved, decoded from index
       |       latency: cold if index is large (~1-10s for full Wikipedia)
       |
       |-- if backend = "mindspark":
       |       query --> HTTP POST to MindSpark endpoint (localhost:7777)
       |       MindSpark performs its own RAG pipeline
       |       results returned as JSON
       |       latency: warm (~200-800ms)
       |
       v
  [library (Mímisbrunnr) returns MCP tool result]
       |
       |  format: {
       |    "results": [
       |      {
       |        "source": "Poetic_Edda_Translation.json",
       |        "title": "Völuspá, stanza 44",
       |        "excerpt": "...",
       |        "attribution": "Bellows translation, public domain"
       |      },
       |      ...
       |    ],
       |    "query": "...",
       |    "retrieval_mode": "keyword"
       |  }
       v
  [L1 Bifröst: routes result to agent as tool response]
       |
       |  agent incorporates search results into next response
       v
  [L2 Rödd: Tunga --> ChatterBox /v1/audio/speech --> WAV bytes --> speakers  (see §4.6)]
```

**Note on attribution:** Mímisbrunnr result objects carry attribution metadata at all times.
The agent receives the attribution string and can cite properly in its spoken response.
This is by design — the `docs/MIMISBRUNNR.md` spec requires it.

### 4.5 Complete Representative Turn Trace

A single turn with tool use, from first breath to final word:

```
  T+0ms       User finishes speaking "Open Blender and create a basic Viking shield mesh"
              VAD detects end-of-utterance

  T+0–600ms   Whisper.cpp transcribes audio segment                          (wrm)
              output: "Open Blender and create a basic Viking shield mesh"

  T+600ms     L1 Bifröst sends to Pi:
              POST /v1/chat/completions
              {messages: [...history, {role:"user", content:"Open Blender and..."}],
               tools: [...all enabled sense schemas...]}

  T+600–900ms Tailscale wire transit (~50-100ms) + Hermes inference (~200ms)  (wrm)
              Agent decides to call tool

  T+900ms     Agent returns:
              {tool_calls: [{function: {name: "blender.run_script",
                             arguments: "{\"script\": \"create_shield_mesh.py\"}"}}]}
              (two-part tool name: sense_id "blender" + action "run_script")

  T+900ms     L1 Bifröst dispatches to L5 Skilningr → blender (Smiðja) server

  T+900–1100ms Smiðja → Seidr-Smidja Brúarhönd → Blender executes script    (cld begins)
              (Blender may take 1–10s depending on operation)

  T+1100–5000ms Blender runs script, returns result                           (cld)
              result: {success: true, output: "Shield mesh created", ...}

  T+5000ms    Smiðja returns MCP result to Bifröst

  T+5000ms    Bifröst sends tool result to agent:
              POST /v1/chat/completions
              {messages: [..., {role:"tool", content: "{success:true, output:...}"}]}

  T+5000–5200ms Agent generates final response text                           (wrm resumes)
              "The shield mesh is ready in Blender. I've given it a round Norse boss
               and basic surface divisions. Want me to add edge loops for detail work?"

  T+5200ms    L2 Tunga sends to ChatterBox:
              POST <chatterbox>/v1/audio/speech             (v0.2 live contract)
              {model: "turbo", input: "The shield mesh is ready...",
               response_format: "wav", temperature: 0.8}
              NOTE: v0.1 trace showed `/tts` — corrected; see §4.6 for streaming detail

  T+5200–5500ms ChatterBox synthesizes audio (~300ms)                         (wrm)

  T+5500ms    Audio begins playing through speakers

  T+5500ms    Session log event written:
              {type:"voice_turn_with_tool", transcript:"...", tool:"blender.run_script",
               tool_result_summary:"shield mesh created", ts_start: T+0, ts_audio_start: T+5500}
```

### 4.6 Voice Flow (v0.2 — outbound only, Tunga / TTS path)

This section maps the full route of a spoken agent response through L2 Rödd in v0.2 First
Voice. Only the outbound (Tunga / TTS) half is implemented in v0.2. The inbound (Hlust / STT)
half is v0.3 First Listening. The L5 Tunga sense wrapper (agent-callable `tunga.speak` tool)
is v0.7 and later.

> **Three sense rivers:** Tunga is the first sense river — the body speaking outward.
> Its mirror on the inbound side is §4.7 (Hlust, voice in) and §4.10 (Sjón, image in).
> Where Tunga converts agent text to audio and sends it out, Sjón converts screen pixels
> to base64 and sends them in. The asymmetry is intentional: Tunga is continuous-stream;
> Sjón is on-demand-per-turn. See §4.10 for the full sight flow mapped in v0.5.

**Lifecycle dependency:** Tunga is initialized at Kynding (client warm, no audio yet) and
first becomes active during Tengsl. It operates fully during Samræður. At Slokna, any queued
speech is flushed before the queue is closed — the agent may speak its final words before
the ceremony ends.

#### 4.6.1 End-to-End Path

```
  SAMRAEDUR — the spirit is speaking

  [L1 Bifröst: SSE stream parser]
       |
       |  agent response arrives as a stream of SSE chunks (if stream: true):
       |    data: {"choices":[{"delta":{"content":"word "}}]}
       |    data: {"choices":[{"delta":{"content":"by "}}]}
       |    data: [DONE]
       |
       |  each chunk is a token or small fragment of the spirit's reply
       |
       |  the raw SSE stream FORKS at this point:
       |    --> path A: chat display in L4 Vébond  (v0.4 Summoning Circle; not in v0.2)
       |    --> path B: L2 Rödd Tunga orchestrator (v0.2 — this section)
       v
  [L2 Rödd: Tunga orchestrator — sentence-boundary chunker]
       |
       |  CHUNKING POLICY:
       |  Tunga accumulates incoming text deltas into an internal buffer.
       |  A chunk is dispatched to synthesis when EITHER condition is met:
       |
       |    Condition 1 — sentence boundary detected:
       |      triggers on: ". " (period-space)
       |                   "! " (exclamation-space)
       |                   "? " (question-space)
       |                   "\n\n" (paragraph break)
       |      AND the accumulated buffer has reached the minimum threshold:
       |                   min 80 characters accumulated before boundary fires
       |      (the 80-char minimum prevents single-word or very-short-fragment synthesis,
       |       which sounds jarring. A sentence boundary on buffer <80 chars is swallowed
       |       into the accumulator until the next boundary or end-of-stream.)
       |
       |    Condition 2 — end-of-stream flush:
       |      when the SSE stream sends [DONE], Tunga flushes any remaining buffer
       |      regardless of boundary or minimum threshold.
       |      This ensures the last sentence of a response is always spoken.
       |
       |  SERIALIZATION:
       |    chunks are dispatched in strict arrival order
       |    only one HTTP request to ChatterBox is in-flight at a time (single-request queue)
       |    the next chunk waits until playback of the previous chunk has begun
       |    (not completed — started; this allows near-pipelined audio without overlap)
       |
       v
  [ChatterboxClient — async httpx, POST /v1/audio/speech]            (wrm)
       |
       |  Health check path (at Kynding / Tengsl init):
       |    GET <rodd.tts.endpoint>/health
       |    --> 200 OK: client warm, proceed
       |    --> timeout or error: emit warning, set voice_available = false
       |                          (see fallback path in §4.6.2)
       |
       |  Per-chunk synthesis request:
       |    POST <rodd.tts.endpoint>/v1/audio/speech
       |    body: {
       |      "model":           "<rodd.tts.model>"             (default: "turbo")
       |      "input":           "<chunk text, 1-4000 chars>"
       |      "response_format": "wav"                          (only format supported)
       |      "temperature":     <rodd.tts.temperature>         (default: 0.8)
       |      "voice":           <rodd.tts.voice_prompt_path>   (optional; omit for default voice)
       |    }
       |
       |  Config keys that influence this step:
       |    rodd.tts.endpoint          --> request target URL
       |    rodd.tts.model             --> "model" field in body ("turbo" | "tts" | "multilingual")
       |    rodd.tts.temperature       --> "temperature" field in body (default 0.8, range 0.05-2.0)
       |    rodd.tts.voice_id          --> "voice" field; semantics: WAV FILE PATH for voice cloning
       |                                   (not a symbolic identifier). "default" or empty → field
       |                                   OMITTED from request body; ChatterBox uses its built-in
       |                                   default voice. Any other value is treated as a path to a
       |                                   ≥5s WAV file (relative; "~" expanded). See _resolve_voice_path
       |                                   in chatterbox.py and LAYER_INTERFACES.md §L2 annotation N-3.
       |    rodd.tts.enabled           --> master toggle; if false, Tunga is a no-op
       |    rodd.tts.device            --> passed downstream to AudioPlayback (OS device name)
       |    (no rodd.tts.speed key in the live ChatterBox contract — speed has no API effect)
       |
       |  NOTE on config drift (corrected — v0.3 pass, Védis Eikleið 2026-05-07):
       |    The LAYER_INTERFACES.md §L2 config block was corrected in the G-1/N-2/N-3 corrective
       |    pass (also 2026-05-07) to reflect the full 17-field schema. The `speed` field is
       |    accepted by RoddTtsConfig for backward compatibility but has no effect on ChatterBox
       |    output (ChatterBox /v1/audio/speech does not expose a speed parameter). The `voice_id`
       |    field holds a WAV file path — not a symbolic voice name. At v0.2 default ("default"),
       |    the field is omitted from the request body. Full schema: see §4.6.4 below and
       |    LAYER_INTERFACES.md §L2 Rödd (authoritative). This note replaces the prior
       |    "discrepancy noted for future Architect pass" annotation — the pass is now complete.
       |
       |  <-- returns: WAV bytes (Content-Type: audio/wav)
       |               typical latency: ~100-400ms for a short sentence
       v
  [AudioPlayback — sounddevice primary, platform fallback]            (hot)
       |
       |  PRIMARY: sounddevice library
       |    reads WAV bytes into numpy array
       |    plays through OS audio device (rodd.tts.device, default: "default")
       |    non-blocking playback start; Tunga marks chunk as "playing" and accepts next
       |
       |  FALLBACK CHAIN (if sounddevice unavailable at import time):
       |    Windows: winsound.PlaySound(wav_bytes, winsound.SND_MEMORY)
       |    macOS:   afplay via subprocess (writes temp file, plays, removes)
       |    Linux:   aplay via subprocess (writes temp file, plays, removes)
       |    all fallbacks: blocking playback (next chunk waits for completion)
       |
       |  Config key: rodd.tts.device --> OS audio device name
       |              "default" = OS default output device
       |
       v
  [OS audio device → speakers]                                        (hot)
       |
       |  The spirit's words emerge in the room.
       |
       |  Events emitted (to L4 Vébond, for waveform / activity display):
       |    voice::speaking_start   (emitted when first WAV chunk begins playback)
       |    voice::speaking_end     (emitted when queue is empty and last chunk finishes)
       |
       v
  [L0 Grunnr: session log]
       |
       |  event written:
       |  {"event": "tunga_chunk_spoken", "ts": "...", "chunk_length_chars": ...,
       |   "tts_latency_ms": ..., "playback_device": "..."}
```

#### 4.6.2 Fallback Path (ChatterBox unavailable)

When ChatterBox cannot be reached, voice is degraded — the ceremony does not stop.

```
  [Tunga: health check at Kynding]
       |
       |  GET <rodd.tts.endpoint>/health
       |
       |-- 200 OK --> voice_available = true, proceed normally (§4.6.1)
       |
       |-- connection refused, timeout, or non-2xx:
       |       log.warn("ChatterBox unreachable at <endpoint> — voice disabled for this ceremony")
       |       voice_available = false
       |       capability flag ?voice_out = false
       |       --> L4 Vébond: voice::error(VOICE_TTS_UNREACHABLE)
       |       --> UI: voice degraded indicator shown
       |       ceremony continues in TEXT-ONLY mode
       v
  [Per-chunk synthesis request — if voice_available = false]:
       |
       |  Tunga short-circuits: chunk is discarded (no HTTP call made)
       |  The agent's text still flows to L4 Vébond for display (v0.4 path)
       |  No audio is played; no crash; no block on the conversation
       |
  [Mid-ceremony TTS error (after initial health check succeeded)]:
       |
       |  HTTP error on /v1/audio/speech (connection dropped, 5xx, timeout):
       |    log.warn("ChatterBox synthesis failed for chunk — skipping audio")
       |    discard chunk audio; do NOT stop the conversation
       |    if 3 consecutive failures:
       |      voice_available = false; emit voice::error(VOICE_TTS_UNREACHABLE)
       |      Tunga stops attempting synthesis for remainder of Samræður
       |      user notified via L4 Vébond
```

#### 4.6.3 Lifecycle Timeline for Tunga

```
  Kynding (STATE_KYNDING):
    RoddConfig loaded from heretic.yaml (rodd.tts.* keys)
    ChatterboxClient instantiated (httpx async session created)
    GET /health called once:
      success  --> client warm; voice_available = true
      failure  --> voice_available = false; warning logged; ceremony proceeds

  Tengsl (STATE_TENGSL):
    Tunga queue initialized (empty)
    voice::speaking_start / voice::speaking_end handlers registered with L4
    No audio produced yet (spirit has not spoken)

  Samræður (STATE_SAMRAEDUR):
    Tunga fully active — sentence-chunker consuming Bifröst SSE stream
    ChatterBox synthesis on demand per chunk
    AudioPlayback operating

  Slokna (STATE_SLOKNA) — teardown sequence:
    Bifröst stops feeding new text chunks to Tunga
    Tunga flushes current queue:
      any pending synthesized WAV (not yet started): played
      any pending text (not yet sent to ChatterBox): synthesized and played
      (the agent's parting words are spoken before silence falls)
    Drain window: bifrost.drain_timeout_seconds (default 10s)
      if queue not empty at drain timeout: remaining chunks discarded cleanly
    Tunga queue closed; httpx session closed
    voice::speaking_end emitted
    L4 Vébond receives final state
```

#### 4.6.4 Config Dependencies for the Voice Path

> **Corrective note — 2026-05-07 v0.3 pass (Védis Eikleið):** This table previously showed only
> 6 fields from the pre-probe config stub. It has been expanded to the full 17-field schema
> matching `src/heretic/rodd/config_model.py RoddTtsConfig`. For the full annotated schema with
> semantic notes (voice_id WAV-path semantics, language_id scope, speed non-effect), see
> `LAYER_INTERFACES.md §L2 Rödd` — that is the authoritative operator reference. This table
> summarises which field controls which step in the data flow.

**All `rodd.tts.*` config fields and the step they influence:**

| Config key | Default | Controls |
|---|---|---|
| `rodd.tts.enabled` | `true` | Master toggle — `false` means Tunga is a no-op; no HTTP calls, no audio |
| `rodd.tts.engine` | `"chatterbox"` | Selects the TTS backend class (`chatterbox` in v0.2; `openai_compat` future) |
| `rodd.tts.endpoint` | `"http://100.66.178.105:7851"` | ChatterboxClient target URL for `/health` and `/v1/audio/speech` |
| `rodd.tts.voice_id` | `"default"` | `"voice"` field in request body — **WAV file path** for voice cloning (not a symbolic ID). `"default"` omits the field; ChatterBox uses its built-in voice. See N-3 in LAYER_INTERFACES.md §L2. |
| `rodd.tts.voice_prompt_path` | `null` | Alternative path field; same WAV-path semantics as `voice_id`. `null` = omit from body. Takes precedence over `voice_id` when set. |
| `rodd.tts.model` | `"turbo"` | `"model"` field in request body (`"turbo"` \| `"tts"` \| `"multilingual"`) |
| `rodd.tts.language_id` | `"en"` | ISO 639-1 language code — only injected into the body when model is `"multilingual"` and value is not `"en"`. Silently excluded for `turbo` and `tts` models. See N-2 in LAYER_INTERFACES.md §L2. |
| `rodd.tts.exaggeration` | `0.5` | `"exaggeration"` field in request body; emotional expressiveness (range 0.0–2.0) |
| `rodd.tts.cfg_weight` | `1.0` | `"cfg_weight"` field; CFG dual-pass weight (range 0.0–2.0); only used by `"tts"` model |
| `rodd.tts.temperature` | `0.8` | `"temperature"` field in request body (range 0.05–2.0) |
| `rodd.tts.top_p` | `0.95` | `"top_p"` nucleus sampling cutoff (range 0.0–1.0) |
| `rodd.tts.repetition_penalty` | `1.2` | `"repetition_penalty"` field (range 0.1–5.0) |
| `rodd.tts.device` | `"default"` | AudioPlayback OS audio device name; `"default"` = OS default speaker |
| `rodd.tts.speed` | `1.0` | Accepted by config parser for backward compatibility but **has no effect on ChatterBox output** — the live `/v1/audio/speech` endpoint does not expose a speed parameter. A debug log is emitted if set to a value other than 1.0. Do not rely on this field. |
| `rodd.tts.request_timeout_seconds` | `30` | HTTP timeout for `/v1/audio/speech` requests; raises `ChatterboxTimeoutError` on breach |
| `rodd.tts.chunk_min_chars` | `80` | Minimum accumulated characters before Tunga dispatches a sentence-boundary chunk to synthesis (prevents single-word fragments) |
| `rodd.tts.sentence_terminators` | `[". ", "! ", "? ", "\n\n"]` | Substring patterns that trigger a sentence-boundary flush in the Tunga chunker |

The `chunk_min_chars` and `sentence_terminators` fields are configurable in `heretic.yaml` via
`RoddTtsConfig` — earlier notes that called these "fixed implementation choices" reflected the
pre-v0.2 stub; they are in fact exposed fields. The full canonical schema lives in
`src/heretic/rodd/config_model.py RoddTtsConfig` and LAYER_INTERFACES.md §L2 Rödd.

### 4.7 Listening Flow (v0.3 — inbound, Hlust / STT path)

> **Added 2026-05-07 v0.3 (Védis Eikleið).** This section maps the inbound path: the user's
> spoken words entering the body and becoming text that flows to the spirit. v0.2 mapped the
> outbound breath (Tunga); this maps the returning breath (Hlust). Together they complete L2 Rödd.
>
> The L5 Hlust sense (`hlust.listen` MCP tool — agent-callable STT) is **out of scope for v0.3**.
> v0.3 Hlust is human-facing input only: the CLI captures the user's voice and feeds it through
> Bifröst as a user-role message. The agent-callable surface comes in a later milestone.
>
> **Companion flow — vision in:** Hlust is the first inbound sense river (voice in). Its companion
> is §4.10 (Sjón, image in). Both are inbound; both are conditional on their respective
> capability flags (`?voice_in` for Hlust; `?vision_in` for Sjón). Both inject their payload
> into the user-role message that travels to the spirit via Bifröst.

**Lifecycle dependency:** Hlust initialises at Kynding (mic device probed; VAD wrapper
instantiated; Whisper engine object created but model weights NOT loaded). The first model load
happens during Samræður on the first user utterance. This resolves audit finding C-Q-C1 (lazy
load strategy).

**Lazy load latency budget (first-utterance-only):**
- `ggml-base.en.bin` (142 MB): approximately 2–5 s on typical laptop hardware
- `ggml-medium.en.bin` (1.5 GB): approximately 10–30 s on typical laptop hardware
- After the first load, the model stays warm in RAM for the remainder of the ceremony.
- Operators who require zero first-utterance latency may set `rodd.stt.load_strategy: eager`
  to load at Kynding instead (slows startup; keeps Samræður latency uniform).

#### 4.7.1 End-to-End Listening Path

```
  SAMRAEDUR — the user is speaking

  [User speaks into laptop microphone]
       |
       |  OS audio device (rodd.stt.device; default: OS default mic)
       |  continuous capture at 16 kHz mono int16 PCM
       |  frame size: 30 ms = 480 samples at 16 kHz
       |
       v
  [L2 Rödd: SoundDeviceMicBackend]                                    (sync I/O, run_in_executor)
       |
       |  PRIMARY: sounddevice library (already a [voice] extra dependency from v0.2)
       |    captures frames at exactly 16 kHz int16 mono — Whisper's native input format;
       |    no resample step required.
       |  FALLBACK: if sounddevice unavailable at import time:
       |    log.warn("sounddevice unavailable — Hlust disabled; falling back to stdin")
       |    Hlust is set unavailable; CLI falls back to sys.stdin.readline path (see §4.7.4)
       |
       |  30 ms frames are fed continuously to VAD as they arrive
       |  (capture loop runs in a thread via asyncio run_in_executor — not blocking the event loop)
       |
       v
  [L2 Rödd: VadDetector]                                              (sync, per-frame)
       |
       |  PRIMARY: WebRtcVadBackend (webrtcvad-wheels — BSD-3, pre-built wheels)
       |    webrtcvad.Vad(aggressiveness=rodd.stt.vad_threshold normalized to 0-3)
       |    called per 30ms frame; returns: speech (True) or silence (False)
       |    frames classified as speech are accumulated in the utterance buffer
       |    end-of-utterance detected when K consecutive silence frames observed
       |    (K is implementation-defined; typically ~300ms of silence = ~10 frames)
       |
       |  VAD FALLBACK: if webrtcvad import fails at startup:
       |    log.warn("webrtcvad unavailable — using energy-threshold VAD")
       |    EnergyThresholdBackend: computes RMS over each frame; compares to threshold
       |    same interface as WebRtcVadBackend; less accurate in noisy environments
       |
       |  DEGRADED MODE: if both VAD backends fail:
       |    NullVadBackend used: captures a fixed window (default: 3 seconds of frames)
       |    then treats the window as a complete utterance regardless of actual speech
       |    log.warn("both VAD backends unavailable — using 3s fixed-window capture (degraded)")
       |    This is degraded UX: forces the user to speak for 3 s and wait; ceremony
       |    continues but voice interaction is impractical. L4 Vébond notified.
       |
       v
  [Utterance buffer]                                                   (in memory)
       |
       |  accumulates 30ms int16 frames classified as speech
       |  concatenated into a single contiguous audio buffer at end-of-utterance
       |  typical utterance: 0.5–10 seconds of audio = 8000–160000 samples at 16kHz
       |
       v
  [L2 Rödd: WhisperEngine]                                            (async, first-call lazy load)
       |
       |  PRIMARY: PyWhisperCppBackend (pywhispercpp — MIT, wraps whisper.cpp)
       |    MODEL LOAD (first utterance only, load_strategy: lazy):
       |      pywhispercpp.Model(rodd.stt.model_path)
       |      model_path is relative to HERETIC data directory — never absolute
       |      load happens inside run_in_executor (thread); does not block event loop
       |      latency: ~2-5s for base.en (142 MB), ~10-30s for medium.en (1.5 GB)
       |      after load: model object cached in WhisperEngine for lifetime of ceremony
       |    TRANSCRIPTION (each utterance):
       |      model.transcribe(audio_buffer_as_float32_array, language=rodd.stt.language)
       |      returns: list of Segment objects; joined to transcript string
       |      latency: typically 200–800ms on laptop hardware for a 1–5s utterance
       |
       |  WHISPER FALLBACK: if pywhispercpp unavailable at import time:
       |    CliSubprocessBackend: writes utterance buffer to a temp WAV file
       |    subprocess call: shutil.which("whisper-cli") → executes whisper-cli binary
       |    reads transcript from stdout; temp file cleaned up after
       |    con: per-utterance subprocess startup cost (OS overhead)
       |    con: serialisation through temp WAV adds latency
       |
       |  HLUST UNAVAILABLE: if neither pywhispercpp nor whisper-cli on PATH:
       |    NullWhisperBackend: available() returns False
       |    Hlust marks itself unavailable; CLI falls back to stdin (§4.7.4)
       |    log.warn("no Whisper backend available — Hlust disabled")
       |    capability flag ?voice_in = false
       |
       v
  [transcript text]
       |
       |  UTF-8 string; typical example: "Open the workshop and show me the rune inscriptions"
       |  timestamp: monotonic ts at end-of-utterance detection
       |  confidence: float (from pywhispercpp segment metadata; approximated for CLI backend)
       |
       v
  [CLI display — transcript confirmation]
       |
       |  When rodd.stt.enabled and Hlust is available:
       |    CLI prints: "[heard] Open the workshop and show me the rune inscriptions"
       |    (the user sees what was transcribed before it is sent to the spirit)
       |    This surfaces transcription errors so the user can interrupt if needed.
       |    No automatic retry on misread — user re-speaks if needed.
       |
       v
  [L1 Bifröst client]                                                 (wrm)
       |
       |  transcript injected as user-role message into next chat/completions request:
       |  POST <agent_endpoint>/v1/chat/completions
       |  body: {
       |    "messages": [
       |      ... conversation history,
       |      {"role": "user", "content": "<transcript text>"}
       |    ],
       |    "tools": [<all enabled sense schemas>]
       |  }
       |
       |  from this point the flow is identical to §4.1 Voice Turn (agent processing,
       |  tool calls, Tunga TTS response) — the inbound path rejoins the main cycle.
       |
       v
  [L0 Grunnr: session log]
       |
       |  event written:
       |  {"event": "hlust_transcript", "ts": "...",
       |   "transcript": "...", "confidence": 0.92,
       |   "vad_backend": "webrtcvad", "whisper_backend": "pywhispercpp",
       |   "model_path": "models/ggml-base.en.bin",
       |   "utterance_duration_ms": 2300, "transcription_ms": 420}
```

#### 4.7.2 Fallback Chain Summary

```
  Microphone capture:
    sounddevice (primary, [voice] extra, cross-platform)
        |-- unavailable --> Hlust disabled, CLI falls back to stdin
                           voice_in capability = false

  VAD (per 30ms frame):
    WebRtcVadBackend (webrtcvad-wheels, BSD-3, primary)
        |-- import fails --> EnergyThresholdBackend (pure Python, zero deps)
                                |-- runtime error --> NullVadBackend (3s fixed window, DEGRADED)

  Whisper transcription:
    PyWhisperCppBackend (pywhispercpp, MIT, primary)
        |-- import fails --> CliSubprocessBackend (whisper-cli on PATH)
                                |-- not on PATH --> NullWhisperBackend
                                                    Hlust disabled, CLI stdin fallback
```

In all fallback paths: the lifecycle does not crash. The ceremony continues. Degraded voice
input surfaces a warning in the session log and (in v0.4+) an indicator in Eldahús.

#### 4.7.3 Lifecycle Timeline for Hlust

```
  Kynding (STATE_KYNDING):
    RoddSttConfig loaded from heretic.yaml (rodd.stt.* keys)
    SoundDeviceMicBackend probed: device available?
    VadDetector instantiated (webrtcvad or energy-threshold selected)
    WhisperEngine object created — model NOT loaded yet (load_strategy: lazy default)
    Hlust marks itself READY (device+backend available) or UNAVAILABLE (fallback to stdin)
    Note: model load does NOT happen here — Kynding stays fast regardless of model size

  Tengsl (STATE_TENGSL):
    Hlust starts mic capture loop (if available and rodd.stt.enabled = true)
    [listening...] indicator shown in CLI

  Samræður (STATE_SAMRAEDUR) — FIRST utterance:
    VAD detects end-of-utterance
    WhisperEngine.transcribe() called for the first time
    --> MODEL LOAD happens here (first-utterance latency; see load budget in §4.7 header)
    transcript produced; displayed in CLI; injected into Bifröst as user message
    Model stays warm for remainder of ceremony

  Samræður — subsequent utterances:
    Same path; model already loaded; transcription latency only (~200-800ms)

  Slokna (STATE_SLOKNA):
    Mic capture loop stopped
    Any in-progress utterance buffer discarded
    WhisperEngine context cleared (model stays loaded until process exit; not explicitly unloaded)
    Hlust closed cleanly
```

#### 4.7.4 CLI Integration — stdin Fallback Path

```
  rodd.stt.enabled = true AND Hlust available AND stdin is a TTY:
    --> capture_one_utterance() replaces sys.stdin.readline in cli.py:_async_light
    --> CLI shows: [listening...]
    --> after transcription: CLI shows: [heard] <transcript>
    --> transcript text sent as user message

  rodd.stt.enabled = false OR Hlust unavailable OR stdin is not a TTY (piped):
    --> CLI reads from sys.stdin.readline as before (text input path)
    --> scriptability preserved: `echo "hi" | heretic light` still works
```

#### 4.7.5 Config Dependencies for the Listening Path

| Config key | Default | Controls |
|---|---|---|
| `rodd.stt.enabled` | `true` | Master toggle — `false` means Hlust does not start; CLI uses stdin |
| `rodd.stt.engine` | `"whisper_cpp"` | STT backend: `"whisper_cpp"` (pywhispercpp + CLI fallback) |
| `rodd.stt.model_path` | `"models/ggml-base.en.bin"` | Path to GGML model file, relative to HERETIC data dir — never absolute |
| `rodd.stt.device` | `"default"` | Mic device name; `"default"` = OS default microphone |
| `rodd.stt.vad_threshold` | `0.6` | VAD confidence threshold (0.0–1.0); maps to webrtcvad aggressiveness 0–3 |
| `rodd.stt.language` | `"en"` | BCP-47 language code passed to Whisper for transcription |
| `rodd.stt.load_strategy` | `"lazy"` | `"lazy"` = load model on first utterance (resolves C-Q-C1); `"eager"` = load at Kynding |

Full schema lives in `src/heretic/rodd/config_model.py RoddSttConfig` and LAYER_INTERFACES.md §L2 Rödd.

---

## 5. Extinguishing: Slokna (STATE_SLOKNA)

The ceremony ends cleanly. Each river is sealed.

```
  [User clicks "Extinguish" in Eldahús]
  OR
  [agent sends session-end signal]
  OR
  [Holdvörðr detects disconnection / timeout]
       |
       v
  [L1 Bifröst]
       |
       |  sends closing message to agent:
       |  POST <endpoint>/v1/chat/completions
       |  {messages: [..., {role:"user", content:"The ceremony closes. Farewell."}]}
       |
       |  <-- optional: agent final words (played via Tunga)
       |
       |  connection closed
       v
  [L5 Skilningr]
       |
       |  each enabled MCP sense server receives shutdown signal
       |  completes any in-flight tool calls (or cancels with timeout)
       |  closes listening sockets
       v
  [L2 Rödd: Hlust]
       |
       |  microphone buffer flushed
       |  Whisper.cpp context cleared
       v
  [L2 Rödd: Tunga]
       |
       |  any pending TTS requests flushed or cancelled
       v
  [L3 Sjón]
       |
       |  screen capture stopped
       v
  [L0 Grunnr]
       |
       |  ceremony event written: {type: "slokna", ts: ..., session_id: ...}
       |  session log closed and flushed to disk
       |  session summary optionally written
       v
  [Holdvörðr: exits]
  [Eldahús: closes]
  [STATE: returns to Hvíld]
```

---

## 6. Layer-to-Layer Data Contracts Summary

A reference table of what crosses each layer boundary.

```
  Boundary           Direction    Data                              Format
  -----------------------------------------------------------------
  Grunnr → all       outward      config values                     dict / YAML parsed
  all → Grunnr       inward       ceremony events, log lines        structured JSON
  Bifröst → Pi       outward      chat completion request           OpenAI-compat JSON (HTTP)
  Pi → Bifröst       inward       chat completion response          OpenAI-compat JSON (HTTP)
  Bifröst → Skilningr outward     tool_call dispatch                function name + JSON args
  Skilningr → Bifröst inward      tool result                       JSON string
  Rödd (Hlust) → Bifröst inward   user transcript                   UTF-8 string
  Bifröst → Rödd (Tunga) outward  agent response text               UTF-8 string
  Rödd (Tunga) → ChatterBox outward text-to-speech request          HTTP POST JSON to /v1/audio/speech (live contract; v0.1 showed /tts — corrected)
  ChatterBox → Rödd (Tunga) inward audio bytes                      audio/wav (only "wav" supported per live contract)
  Sjón → Skilningr   outward      screenshot PNG                    bytes (base64 encoded for API)
  Skilningr → blender (Smiðja) outward Blender tool call            MCP call (JSON)
  blender (Smiðja) → Brúarhönd outward remote desktop dispatch     HTTP POST JSON
  Brúarhönd → blender (Smiðja) inward  operation result            HTTP response JSON
  Skilningr → library (Mímisbrunnr) outward library query          {query, source_filter}
  libzim/MindSpark → library (Mímisbrunnr) inward search results   list of {title, excerpt, attribution}
```

---

## 7. Bifröst Wire Detail

Everything that crosses the Tailscale WireGuard mesh between laptop and Pi.

```
  LAPTOP (Holdvörðr)                        PI (Hermes Agent)
  ==================                        =================

  POST /v1/chat/completions            -->
    {model, messages, tools, stream}
                                       <--  {choices: [{message|tool_calls}], usage}

  POST /v1/chat/completions            -->
    (tool result follow-up)
                                       <--  {choices: [{message}]}

  [Connection test at Tengsl]          -->
                                       <--  200 OK

  [Optional: streaming mode]
  POST /v1/chat/completions            -->
    {stream: true}
                                       <-- Server-Sent Events stream:
                                           data: {"choices":[{"delta":{"content":"word "}}]}
                                           data: {"choices":[{"delta":{"content":"by "}}]}
                                           data: [DONE]
```

**What never crosses Bifröst:**
- Raw audio (STT happens on laptop, only transcript crosses)
- Raw screenshots (bytes stay on laptop; if sent to agent, they go as base64 in the message body)
- MCP tool results (these go in the message body as JSON strings, not as binary)
- Config / auth details (config is laptop-local; API key travels only in HTTP headers)

**Open question:** For vision-capable sessions, base64 PNG in the message body may add
100-500KB per image to each Tailscale packet. If Hermes on Pi supports a URL reference
instead of inline base64, it would be worth serving the screenshot via a local HTTP server
and sending only the URL. This is an optimization for the Architect/Forge to consider at
the L3-Sjón / L1-Bifröst interface.

---

## 8. MCP Sense Hub — Internal Bus

How Skilningr routes calls between Bifröst and the senses internally.

```
  [Bifröst: tool_call arrives]
       |
       v
  [Skilningr: MCP dispatcher]
       |
       |  parses tool name: "<sense_id>.<action>"  (two-part, no "sense." prefix)
       |  sense_id is the code-facing identifier — see SENSE_CONTRACTS.md §2 for full mapping
       |  looks up registered MCP server by sense_id
       |  forwards: action + arguments JSON
       |
       |-- auga        --> Sjón screen capture / vision  (True Name: Auga)
       |-- hlust       --> Whisper.cpp on-demand STT     (True Name: Hlust; substrate: L2 Rödd)
       |-- tunga       --> ChatterBox TTS proxy          (True Name: Tunga; substrate: L2 Rödd)
       |-- photopea    --> Photopea bridge               (True Name: Hönd)
       |-- blender     --> Seidr-Smidja Brúarhönd client (True Name: Smiðja)
       |-- browser     --> Browser automation            (True Name: Leið)
       |-- filesystem  --> FileSystem operations         (True Name: Minni)
       |-- terminal    --> Terminal subprocess runner    (True Name: Skepja)
       |-- agentmail   --> AgentMail SMTP/IMAP client    (True Name: Boð)
       |-- vrchat      --> VRChat OSC/API bridge         (True Name: Líkami)
       |-- library     --> Library search backend        (True Name: Mímisbrunnr)
       |-- <prefix>/*  --> Custom plugin MCP server(s)   (True Name: Nýr Limr; prefix user-declared)
       |
       |  result returned to Skilningr dispatcher
       v
  [Skilningr: wraps result as MCP tool response]
       |
       v
  [Bifröst: receives tool result, continues agent conversation]
```

**All sense servers communicate with Skilningr over a local internal bus** — whether that is
Unix domain sockets, local TCP loopback (127.0.0.1), or direct in-process calls depends on
the implementation. The contract boundary is the MCP protocol surface. Sense servers must not
call each other directly; all inter-sense communication flows through Skilningr as the hub.

See `docs/architecture/LAYER_INTERFACES.md` for the per-layer and per-sense API contracts.

---

## 9. Session Log — the Event Ledger

Every ceremony event is appended to an on-disk session log. This is the append-only truth.

```
  Session log location:  <data_dir>/sessions/<session_id>.jsonl
  Format: one JSON object per line

  Example entries:
  {"event": "kynding_start",  "ts": "...", "session_id": "..."}
  {"event": "tengsl_open",    "ts": "...", "agent_endpoint": "..."}
  {"event": "voice_turn",     "ts": "...", "transcript": "...", "tool_calls": [...]}
  {"event": "tool_call",      "ts": "...", "sense": "smidja", "method": "execute_blender_script"}
  {"event": "tool_result",    "ts": "...", "sense": "smidja", "success": true}
  {"event": "slokna",         "ts": "...", "duration_s": 1843}

  Write pattern: append-only, never overwrite
  Flush: each event written synchronously (small events) or buffered with 1s max delay
  Rotation: one file per ceremony session (keyed by session_id)
```

This pattern is carried forward from the surviving event-ledger primitive in
`PRIOR_PLANNING_TRIAGE.md` (event envelope format from the v2 impl pack — adapted for the body,
not the brain).

---

## 10. Cold-Path Background Flows

Flows that run asynchronously, outside the hot/warm ceremony cycle.

```
  COLD PATH — Library indexing (library / Mímisbrunnr sense)                 (cld)
  ----------------------------------------------------------------
  [User runs: heretic library download wikipedia_norse_subset --confirm]
       |
       v
  [mimisbrunnr/downloaders/http_resumable.py]
       |  HTTP GET from remote source (internet)
       |  data: ZIM file (GB-scale)
       |  writes to: <data_dir>/mimisbrunnr/<source_name>/<filename>.zim
       v
  [mimisbrunnr/indexer.py]
       |  reads ZIM file via libzim
       |  optionally: encodes articles → sentence-transformer → FAISS index
       |  writes: <data_dir>/mimisbrunnr/<source_name>/index.faiss
       v
  [status update written to: <data_dir>/mimisbrunnr/status.json]

  COLD PATH — Session log archival                                            (cld)
  ----------------------------------------------------------------
  [After ceremony ends]
       |
       v
  [L0 Grunnr: background archiver]
       |  compresses old session logs (gzip)
       |  moves to: <data_dir>/sessions/archive/
       |  retention policy: configurable (default: keep all, never delete without user consent)

  COLD PATH — Tailscale keepalive (when Bifröst is open)                     (hot boundary)
  ----------------------------------------------------------------
  [WireGuard keepalive packets]
       |  ~25-second interval (WireGuard default)
       |  minimal data, keepalive UDP packets
       |  ensures the Tailscale path stays warm across NAT
```

---

---

## 11. L2 Rödd — Internal Component Map (v0.2 Tunga)

The internal layout of `src/heretic/rodd/` as it will exist after Forge implements v0.2.
Arrows show the data flow between components within the package.

```
  src/heretic/rodd/
  ├── config_model.py      RoddConfig + RoddTtsConfig + RoddSttConfig
  │                        Loaded once at Kynding from heretic.yaml
  │                        Passed to ChatterboxClient and AudioPlayback constructors
  │
  ├── errors.py            RoddError (base)
  │                        ChatterboxError     (HTTP failure, bad response, unreachable)
  │                        PlaybackError       (device unavailable, sounddevice import fail)
  │                        TtsDisabledError    (rodd.tts.enabled = false — not a crash condition)
  │
  ├── chatterbox.py        ChatterboxClient
  │                        |  __init__(config: RoddTtsConfig) -> self
  │                        |  async health_check() -> bool
  │                        |  async synthesize(text: str) -> bytes   (WAV bytes)
  │                        |
  │                        |  internally: httpx.AsyncClient
  │                        |    GET  /health
  │                        |    POST /v1/audio/speech  {model, input, response_format, temperature, [voice]}
  │                        |    raises ChatterboxError on non-2xx or timeout
  │
  ├── playback.py          AudioPlayback
  │                        |  __init__(config: RoddTtsConfig) -> self
  │                        |  play(wav_bytes: bytes) -> None
  │                        |
  │                        |  internally: attempts sounddevice first
  │                        |    sounddevice.play(numpy_array, sample_rate)  [primary]
  │                        |    winsound.PlaySound(...)                     [Windows fallback]
  │                        |    subprocess afplay temp_file                 [macOS fallback]
  │                        |    subprocess aplay  temp_file                 [Linux fallback]
  │                        |    raises PlaybackError if all backends fail
  │
  └── tunga.py             Tunga   (orchestrator)
                           |  __init__(config: RoddTtsConfig) -> self
                           |  start() -> None     (Tengsl: init queue; health check)
                           |  stop()  -> None     (Slokna: flush queue; close client)
                           |  feed(text_delta: str) -> None
                           |    (called per SSE chunk from Bifröst stream parser)
                           |
                           |  INTERNAL DATA FLOW:
                           |
                           |  Bifröst SSE chunks
                           |       |
                           |       v
                           |  [text accumulator buffer]
                           |       |
                           |       | boundary detected AND len >= 80
                           |       | OR end-of-stream flush
                           |       v
                           |  [synthesis queue]  (asyncio.Queue, maxsize=1 in-flight)
                           |       |
                           |       v
                           |  ChatterboxClient.synthesize(chunk_text)
                           |       |
                           |       | WAV bytes
                           |       v
                           |  AudioPlayback.play(wav_bytes)
                           |       |
                           |       v
                           |  events: voice::speaking_start / voice::speaking_end -> L4

  INTERFACE SUMMARY (within rodd/ package):

  Bifröst                Tunga                ChatterboxClient      AudioPlayback
  --------               -----                ----------------      -------------
  text_delta  ------>  feed(text_delta)
                         accumulate
                         detect boundary
                         flush              -----> synthesize(text)
                                                    POST /v1/audio/speech
                                                    <-- WAV bytes     -----> play(wav_bytes)
                                                                              OS audio device
                                                                              --> speakers
```

**Key invariants for this package:**
- `ChatterboxClient` has no knowledge of buffering or chunking — it is a pure HTTP client
- `AudioPlayback` has no knowledge of TTS — it is a pure audio output wrapper
- `Tunga` owns all orchestration: chunking, queue, ordering, lifecycle, event emission
- No component in `rodd/` calls any other HERETIC layer directly — they emit events
  and are called by the layer that owns them (L1 Bifröst feeds Tunga; L4 consumes events)
- All config is injected at construction time; no component reads `heretic.yaml` directly
- `rodd/` is the L2 substrate; the L5 Tunga sense (`tunga.speak` MCP tool) is a separate
  package in `v0.7`. In v0.2, Tunga runs as automatic pass-through, not as agent tool.

---

*Drawn by Védis Eikleið, Cartographer for Vibe Coding, 2026-05-07.*
*The rivers do not invent themselves. They were always there — I only followed their course.*
*v0.2 addendum: the voice path is now drawn. The body knows how to speak.*
*v0.3 addendum: the listening path is now drawn. The body knows how to hear.*
*v0.4.0 addendum: the face path is now drawn. The ceremony becomes visible.*

---

## 12. L2 Rödd — Internal Component Map (v0.3 Hlust)

The internal layout of the new Hlust half of `src/heretic/rodd/` as it will exist after Forge
implements v0.3. Drawn from `TASK_HERETIC_v0.3_FIRST_LISTENING.md §10` and the architecture
decisions in §7 of that document. Arrows show data direction; sync/async annotations indicate
execution model.

```
  src/heretic/rodd/   (Hlust half — v0.3 additions)
  |
  ├── microphone.py        MicrophoneCapture (ABC)
  │                        |  available() -> bool
  │                        |  read_frame(duration_ms: int) -> bytes   (int16 PCM)
  │                        |
  │                        ├── SoundDeviceMicBackend   (primary)
  │                        |     sounddevice.InputStream at 16kHz mono int16
  │                        |     sync I/O wrapped in run_in_executor (non-blocking for event loop)
  │                        |     frame size: 30ms = 480 samples
  │                        |
  │                        └── NullMicBackend          (no-op; available() = False)
  │
  ├── vad.py               VadDetector (ABC)
  │                        |  is_speech(frame: bytes) -> bool   (sync, per-frame, fast)
  │                        |
  │                        ├── WebRtcVadBackend         (primary; webrtcvad-wheels, BSD-3)
  │                        |     webrtcvad.Vad(aggressiveness)
  │                        |     expects 16kHz int16 PCM in 30ms frames
  │                        |     sync; typically <1ms per frame
  │                        |
  │                        ├── EnergyThresholdBackend   (fallback; zero deps, pure Python)
  │                        |     RMS of frame compared to threshold
  │                        |     less accurate in noisy environments
  │                        |
  │                        └── NullVadBackend           (degraded; 3s fixed-window)
  │                              available() = True but accuracy = none
  │                              logs DEGRADED warning; L4 notified
  │
  ├── whisper_engine.py    WhisperEngine (ABC)
  │                        |  available() -> bool
  │                        |  async transcribe(audio: bytes, language: str) -> str
  │                        |
  │                        ├── PyWhisperCppBackend      (primary; pywhispercpp, MIT)
  │                        |     LAZY LOAD: Model(model_path) on first transcribe() call
  │                        |     model_path relative to HERETIC data dir (never absolute)
  │                        |     model cached in self._model after first load
  │                        |     model.transcribe(float32_array, language=...) -> segments
  │                        |     segments joined to transcript string
  │                        |     async: load + transcribe run in run_in_executor (thread)
  │                        |
  │                        ├── CliSubprocessBackend     (fallback; whisper-cli on PATH)
  │                        |     writes temp WAV → subprocess whisper-cli → reads stdout
  │                        |     async: subprocess via asyncio.create_subprocess_exec
  │                        |     temp file cleaned up after each utterance
  │                        |
  │                        └── NullWhisperBackend       (no-op; available() = False)
  │
  └── hlust.py             Hlust   (orchestrator)
                           |  __init__(config: RoddSttConfig) -> self
                           |  start() -> None     (Tengsl: mic start; VAD ready; engine ready)
                           |  stop()  -> None     (Slokna: mic stop; context cleared)
                           |  async capture_one_utterance() -> str
                           |    (called per turn from cli.py:_async_light)
                           |
                           |  INTERNAL DATA FLOW:
                           |
                           |  [microphone — continuous 30ms frames]
                           |       |  (sync I/O in executor thread)
                           |       v
                           |  [VadDetector.is_speech(frame)]           (sync, per-frame)
                           |       |
                           |       |-- speech frame  --> utterance buffer append
                           |       |                     (list of int16 bytes chunks)
                           |       |
                           |       |-- silence frame --> silence counter increment
                           |                            if K consecutive silence frames:
                           |                              end-of-utterance detected
                           |                              --> flush to Whisper
                           |
                           |  [utterance buffer: concatenated int16 frames]
                           |       |
                           |       v
                           |  [WhisperEngine.transcribe(audio_bytes, language)]  (async)
                           |       |  (lazy load on first call; subsequent calls use cached model)
                           |       |
                           |       v
                           |  [transcript: str]
                           |       |
                           |       v
                           |  --> returned to cli.py:_async_light
                           |       CLI prints: [heard] <transcript>
                           |       transcript injected into Bifröst as user-role message

  INTERFACE SUMMARY (Hlust half of rodd/ package):

  CLI (_async_light)       Hlust                 MicrophoneCapture      VadDetector   WhisperEngine
  ------------------       -----                 -----------------      -----------   -------------
  capture_one_utterance()
      awaits result  <---> frame loop
                               read_frame()  --> 480 samples/30ms
                               is_speech()                       --> bool
                               (speech? buffer; silence K? done)
                               transcribe(buffer)                              ---> transcript str
                           return transcript
  [heard] <transcript>

  INVARIANTS (analogous to Tunga invariants in §11):
  - MicrophoneCapture has no knowledge of VAD or Whisper — it is a pure audio source
  - VadDetector has no knowledge of mic or Whisper — it is a pure frame classifier
  - WhisperEngine has no knowledge of mic or VAD — it is a pure transcription backend
  - Hlust owns all orchestration: frame loop, buffer, end-of-utterance, lazy load trigger
  - No component in the Hlust half calls any other HERETIC layer directly
  - All config injected at construction; no component reads heretic.yaml directly
  - The L5 Hlust sense (hlust.listen MCP tool — agent-callable STT) is out of scope for v0.3;
    the rodd/ Hlust module is the substrate; the L5 sense wrapper ships in a later milestone
```

---

## 13. L4 Vébond — Eldahús Component Diagram (v0.4.0)

> **Added 2026-05-07 v0.4.0 (Védis Eikleið).** Drawn in the same style as §11 (Tunga) and §12
> (Hlust). Shows the internal structure of the Eldahús layer as it ships in v0.4.0: the Python
> backend, the React component tree, the WS seam between them, and which components subscribe
> to which events. This diagram reflects the v0.4.0 substrate (browser mode); the Tauri native
> wrapper (v0.4.1) adds only the outer shell — the component tree and WS protocol do not change.
> For the outer Tauri shell wrapper diagram (Tauri main process + WebView + Python sidecar +
> PID file + Tauri command surface), see §14.

```
  BACKEND SIDE (Python — src/heretic/vebond/)
  ============================================

  src/heretic/vebond/
  |
  ├── config_model.py    VebondConfig
  │                      |  ws_port: int = 8642
  │                      |  ws_host: str = "127.0.0.1"
  │                      |  allow_remote_bind: bool = False
  │                      |  theme: str = "dark_norse"
  │                      |  show_agent_text_stream: bool = True
  │                      |  ceremony_button_confirm: bool = True
  │                      |  show_frame_thumbnail: bool = False
  │                      |  Loaded at Kynding; injected into serve.py constructor
  │
  ├── errors.py          VebondError (base)
  │                      BindError       (host/port already in use or permission denied)
  │                      ProtocolError   (malformed command from client; recoverable — emit error event)
  │                      SerializeError  (failed to JSON-encode an outbound event; log + skip)
  │
  ├── protocol.py        Pydantic models for all events and commands
  │                      |
  │                      |  -- Server-push events (server --> client) --
  │                      |  CeremonyStateChangedEvent   (from, to, timestamp)
  │                      |  BifrostHealthEvent          (status, endpoint, latency_ms)
  │                      |  TungaActivityEvent          (state)
  │                      |  HlustActivityEvent          (state, level_db)
  │                      |  AgentTokenEvent             (role, text_delta, sequence_id)
  │                      |  AgentTurnCompleteEvent      (turn_id, finish_reason)
  │                      |  ErrorEvent                  (level, source, message)
  │                      |
  │                      |  -- Client commands (client --> server) --
  │                      |  LightCommand                ({command: "light"})
  │                      |  ExtinguishCommand           ({command: "extinguish"})
  │                      |  SendMessageCommand          ({command: "send_message", text: str})
  │                      |  CancelTurnCommand           ({command: "cancel_turn", turn_id: str})
  │                      |  ToggleSenseCommand          ({command: "toggle_sense", sense_id, enabled})
  │                        (ToggleSenseCommand received but rejected with error event in v0.4.0)
  │
  └── serve.py           FastAPI application
                         |
                         |  FastAPI app + uvicorn server
                         |  ROUTE: GET /ws  -- WebSocket endpoint (upgraded from HTTP)
                         |
                         |  WebSocketEndpoint
                         |  |  on_connect():
                         |  |    adds connection to active set
                         |  |    pushes CeremonyStateChangedEvent snapshot (from=null, to=current)
                         |  |  on_message(data):
                         |  |    parses command via protocol.py
                         |  |    dispatches to: LightCommand -> lifecycle.light()
                         |  |                   ExtinguishCommand -> lifecycle.extinguish()
                         |  |                   SendMessageCommand -> bifrost_client.send_message(text)
                         |  |                   CancelTurnCommand -> bifrost_client.cancel_turn(id)
                         |  |                   ToggleSenseCommand -> reply ErrorEvent (warn, deferred)
                         |  |                   unknown -> reply ErrorEvent (warn, unknown command)
                         |  |  on_disconnect():
                         |  |    removes connection from active set; no teardown of ceremony
                         |  |
                         |  EventBus (internal async broadcast)
                         |  |  subscribed to:
                         |  |    Lifecycle state transitions
                         |  |     --> publishes CeremonyStateChangedEvent to all connections
                         |  |    BifrostClient state changes
                         |  |     --> publishes BifrostHealthEvent
                         |  |    BifrostClient agent SSE stream (token deltas)
                         |  |     --> publishes AgentTokenEvent (if show_agent_text_stream: true)
                         |  |    BifrostClient turn completions
                         |  |     --> publishes AgentTurnCompleteEvent
                         |  |    Tunga voice::speaking_start / voice::speaking_end
                         |  |     --> publishes TungaActivityEvent
                         |  |    Hlust VAD speech / transcribing / idle state
                         |  |     --> publishes HlustActivityEvent (with level_db if "listening")
                         |  |    any VebondError / downstream error
                         |  |     --> publishes ErrorEvent to all connections
                         |  |
                         |  Connections: Set[WebSocket]  (all open connections; broadcast to all)
                         |  (v0.4.0 expects exactly one connection — the browser tab;
                         |   multiple connections are tolerated: all receive all events)


  THE SEAM — WebSocket Bridge
  ============================

  frontend/src/api/ws-client.ts               Python vebond/serve.py WebSocketEndpoint
  ------------------------------               -----------------------------------------
       WsClient                                WebSocketEndpoint
       |  constructor(url: string)             |  on_connect(websocket)
       |  connect() -> void                    |    register connection
       |  send(command: Command) -> void       |    push state snapshot
       |  subscribe(handler) -> Unsubscribe    |
       |  disconnect() -> void                 |  on_message(data: str)
       |                                       |    parse command JSON
       |  reconnect loop:                      |    dispatch to layer
       |    backoff 1s, 2s, 4s ... 30s         |
       |    on reconnect: server re-snapshots  |  on_disconnect(websocket)
       |                                       |    deregister connection
       <===  ws://localhost:8642/ws  ==========>
         bidirectional JSON text frames


  FRONTEND SIDE (React — frontend/src/)
  ======================================

  frontend/src/
  |
  ├── types/ipc.ts          TypeScript mirrors of Python protocol.py
  │                         |  ServerEvent = CeremonyStateChangedEvent
  │                         |             | BifrostHealthEvent
  │                         |             | TungaActivityEvent
  │                         |             | HlustActivityEvent
  │                         |             | AgentTokenEvent
  │                         |             | AgentTurnCompleteEvent
  │                         |             | ErrorEvent
  │                         |  ClientCommand = LightCommand | ExtinguishCommand
  │                         |              | SendMessageCommand | CancelTurnCommand
  │                         |              | ToggleSenseCommand
  │
  ├── api/ws-client.ts      WsClient — typed WebSocket wrapper
  │                         subscribes / unsubscribes event handlers per event type
  │
  ├── api/events.ts         event handler registry
  │                         |  on("ceremony.state_changed", handler)
  │                         |  on("bifrost.health", handler)
  │                         |  on("tunga.activity", handler)
  │                         |  on("hlust.activity", handler)
  │                         |  on("agent.token", handler)
  │                         |  on("agent.turn_complete", handler)
  │                         |  on("error", handler)
  │
  ├── store/ceremony.ts     Zustand store — SINGLE SOURCE OF UI TRUTH
  │                         |  State fields:
  │                         |    lifecycleState:  LifecycleState | null
  │                         |    wsConnected:     boolean
  │                         |    bifrostStatus:   "open" | "closed" | "opening" | "failed" | null
  │                         |    bifrostLatencyMs: number | null
  │                         |    tungaState:      "idle"|"synthesizing"|"speaking"|"failed" | null
  │                         |    hlustState:      "idle"|"loading"|"listening"|"transcribing"|"failed" | null
  │                         |    hlustLevelDb:    number | null
  │                         |    chatHistory:     ChatMessage[]    (role, content, turnId, streaming)
  │                         |    activeToasts:    Toast[]
  │                         |    wsError:         string | null
  │                         |
  │                         |  Actions fed by WS events (via events.ts handlers):
  │                         |    setLifecycleState(state, from, timestamp)
  │                         |    setBifrostHealth(status, endpoint, latency_ms)
  │                         |    setTungaActivity(state)
  │                         |    setHlustActivity(state, level_db)
  │                         |    appendAgentToken(role, text_delta, sequence_id)
  │                         |    sealTurn(turn_id, finish_reason)
  │                         |    addToast(level, message)
  │                         |    setWsConnected(bool)
  │
  └── components/           React component tree
      |
      App.tsx
      |
      ├── ToastSystem.tsx
      │       subscribes: "error" event --> addToast()
      │       renders: ephemeral toast stack (Varúð for error, dim for warn; single pulse per AESTHETIC.md)
      │
      ├── SummoningCircle.tsx     center stage
      │   |
      │   ├── LifecyclePulse.tsx
      │   │       subscribes: ceremony.lifecycleState (from store)
      │   │       renders: the ring glow + breathing animation (Hvíla-grey at rest;
      │   │                Eld brightening bloom at OPENING; 4s sinusoidal breathing
      │   │                at Tengsl/Samræður; flicker modifier at RECOVERING;
      │   │                dimming at EXTINGUISHED; all per AESTHETIC.md motion language)
      │   │
      │   └── CenterCrest.tsx
      │           subscribes: ceremony.lifecycleState (from store)
      │           renders: Eld-flame sigil or Hvíla-grey dormant crest per state
      │
      ├── SidePanel (left)
      │   |
      │   ├── LayerStatusPanel.tsx
      │   │   |
      │   │   ├── LayerStatusItem.tsx  [Bifröst]
      │   │   │       subscribes: "bifrost.health" --> store.bifrostStatus, store.bifrostLatencyMs
      │   │   │       color: Sjón-glow when open; Hvíla-grey when closed; Varúð when failed
      │   │   │
      │   │   ├── LayerStatusItem.tsx  [Tunga]
      │   │   │       subscribes: "tunga.activity" --> store.tungaState
      │   │   │       color: Mál-green when "speaking"; Hvíla-grey when "idle"; Varúð when "failed"
      │   │   │
      │   │   └── LayerStatusItem.tsx  [Hlust]
      │   │           subscribes: "hlust.activity" --> store.hlustState, store.hlustLevelDb
      │   │           color: Mál-green when "listening" or "transcribing"; Hvíla-grey when "idle"
      │   │           animation: inward pull (receptive) when "listening" per AESTHETIC.md
      │   │
      │   └── SenseTogglePanel.tsx
      │           READ-ONLY in v0.4.0
      │           subscribes: ceremony.lifecycleState (to show/hide; enabled in Tengsl+)
      │           displays: heretic.yaml enabled senses at startup; no toggle commands sent
      │           (toggle_sense command deferred to v0.4.x)
      │
      ├── SidePanel (right)
      │   |
      │   └── ChatPanel.tsx
      │       |
      │       ├── ChatHistory.tsx
      │       │       subscribes: "agent.token" --> store.appendAgentToken()
      │       │                   "agent.turn_complete" --> store.sealTurn()
      │       │       renders: streaming message bubbles; assistant tokens appear in real time
      │       │                (JetBrains Mono for code blocks; Inter for prose per AESTHETIC.md)
      │       │
      │       └── ChatInput.tsx
      │               subscribes: store.wsConnected (disabled when false)
      │               emits: SendMessageCommand on Enter / send button
      │               (voice cue annotation: when store.hlustState = "listening",
      │                ChatInput shows a subtle Mál-green microphone indicator;
      │                the voice path from Hlust is automatic — user does not type during
      │                voice input; the indicator is purely informational)
      │
      └── BottomBar.tsx
          |
          ├── LightButton.tsx
          │       subscribes: ceremony.lifecycleState
          │       enabled when: READY (sends LightCommand on click)
          │       disabled when: OPENING, Tengsl, Samræður, RECOVERING, CONFIG_ERROR
          │       color: Eld when enabled; Hvíla-grey when disabled
          │       label: "Light the Candle" (Cinzel font per AESTHETIC.md display scale)
          │
          ├── ExtinguishButton.tsx
          │       subscribes: ceremony.lifecycleState
          │       enabled when: Tengsl or Samræður (sends ExtinguishCommand after optional confirm)
          │       disabled otherwise
          │       confirm: if vebond.ceremony_button_confirm: true, shows inline confirm before sending
          │       color: Varúð (sienna) when enabled to signal intentional finality
          │
          └── ConnectionIndicator.tsx
                  subscribes: store.wsConnected
                  renders: small dot + label
                    connected:    Mál-green dot, "Connected"
                    disconnected: Varúð dot, "Disconnected — reconnecting..."
                    (this indicator reflects the WS transport state, not the ceremony state;
                     a connected WS in Hvíld is "Connected" + ceremony ring in Hvíla-grey)


  COMPONENT-TO-EVENT SUBSCRIPTION MAP (summary)

  Component              Subscribes to events / store slices
  ---------              ------------------------------------
  LifecyclePulse         ceremony.state_changed --> lifecycleState
  CenterCrest            ceremony.state_changed --> lifecycleState
  LayerStatusItem[Bifrost] bifrost.health --> bifrostStatus, bifrostLatencyMs
  LayerStatusItem[Tunga]   tunga.activity --> tungaState
  LayerStatusItem[Hlust]   hlust.activity --> hlustState, hlustLevelDb
  ChatHistory            agent.token --> chatHistory (streaming)
                         agent.turn_complete --> chatHistory (seal)
  LightButton            ceremony.state_changed --> lifecycleState (enabled?)
  ExtinguishButton       ceremony.state_changed --> lifecycleState (enabled?)
  ConnectionIndicator    wsConnected (store)
  ToastSystem            error event --> activeToasts
  SenseTogglePanel       ceremony.state_changed --> lifecycleState (visibility)
  ChatInput              wsConnected (store) + hlustState (voice cue annotation)


  INVARIANTS:
  - ceremony.ts (Zustand store) is the ONLY source of truth for UI state
    No component reads WS events directly — all reads go through the store
    (events.ts handlers update the store; components subscribe to the store)
  - The WS seam is the ONLY path between Python and React
    No HTTP polling. No REST fallback for state. WS down = UI shows disconnected.
  - All visual state derives from store slices, not from internal component state
    (exception: ephemeral UI micro-interactions like hover are local component state)
  - vebond/serve.py broadcasts to ALL open WebSocket connections
    (v0.4.0: one browser tab expected; multiple tabs receive duplicate streams — acceptable)
  - Python protocol.py is the canonical event/command schema
    TypeScript ipc.ts must mirror it; drift between them is a bug to fix in Forge/Auditor pass
  - LightButton and ExtinguishButton commands are idempotent from the server's perspective:
    a LightCommand in Samræður emits error event (warn); it does not restart the ceremony
  - The backend does NOT persist WS session state
    After reconnect, the client receives a fresh state snapshot and rebuilds from there
    ChatHistory is client-side memory and survives reconnects (held in Zustand store)
```

---

## 14. Tauri Shell Wrapper Diagram (v0.4.1 — pre-staged)

> **Added 2026-05-07 v0.4.1 (Védis Eikleið).** Maps the outer shell that wraps the v0.4.0
> Eldahús substrate in a native desktop window. Pre-staged: the Rust code is scaffolded but
> not compiled; Rust toolchain is not yet installed. This diagram shows the process topology
> the cabin takes once Rust arrives and `cargo tauri build` runs. The WS seam and the React
> component tree inside the WebView are unchanged from §13 — the shell adds a new outer layer
> without disturbing the interior. For the full Tauri startup/shutdown flow, see §4.9.

```
  ========================================================================
  TAURI SHELL WRAPPER — v0.4.1 (pre-staged; compiles after Rust install)
  ========================================================================

  HOST OS (Windows / macOS / Linux)
  |
  +-- heretic.exe  (or heretic.app / heretic.AppImage — the Tauri-built binary)
      |
      +======================================================================+
      |  TAURI MAIN PROCESS  (Rust — src-tauri/src/main.rs)                 |
      |                                                                       |
      |  WindowManager                                                        |
      |  |  creates one WebView window at startup                            |
      |  |  window config from tauri.conf.json:                              |
      |  |    title: "H.E.R.E.T.I.C."                                       |
      |  |    frameless: true   (Norse dark chrome; no system titlebar flash)|
      |  |    theme: dark       (per AESTHETIC.md)                           |
      |  |    single-instance: yes (plugin: single-instance)                 |
      |  |  on RunEvent::ExitRequested --> SidecarManager.shutdown()         |
      |  |  then exit Tauri process                                          |
      |  |                                                                   |
      |  SidecarManager  (src-tauri/src/sidecar.rs)                         |
      |  |  on startup:                                                      |
      |  |    spawn child process: python -m heretic serve --port 8642       |
      |  |    write PID to PID file (see PID file location below)            |
      |  |    probe GET http://localhost:8642/health with backoff:            |
      |  |      attempt 1: 250ms delay                                       |
      |  |      attempt 2: 500ms delay                                       |
      |  |      attempt 3: 1s delay                                          |
      |  |      attempt 4: 2s delay                                          |
      |  |      attempt 5: 4s delay  (max total ~8s)                        |
      |  |    if /health 200 within limit --> tell WindowManager to show     |
      |  |    if timeout or spawn fail   --> show error window (see F-1)     |
      |  |  on shutdown (called from WindowManager):                         |
      |  |    send SIGTERM (Unix) or CTRL_BREAK_EVENT (Windows)              |
      |  |    wait up to 5s for sidecar exit                                 |
      |  |    if still running after 5s --> TerminateProcess (force-kill)    |
      |  |    remove PID file                                                |
      |  |  on next startup (stale-PID recovery):                            |
      |  |    read PID file if present                                       |
      |  |    if PID exists and process still alive --> kill it              |
      |  |    then proceed with normal sidecar spawn                        |
      |  |                                                                   |
      |  EventLoop                                                           |
      |  |  RunEvent::ExitRequested --> SidecarManager.shutdown()           |
      |  |  RunEvent::WindowEvent(close) --> same path                      |
      |  |                                                                   |
      |  Tauri Command Surface  (minimal — only native-only concerns)        |
      |  |  tauri::command  quit()              --> WindowManager close      |
      |  |  tauri::command  focus_window()      --> WindowManager focus      |
      |  |  tauri::command  get_sidecar_port()  --> returns u16 (e.g. 8642) |
      |  |  (all other IPC is the existing WebSocket -- Tauri does not touch)|
      |                                                                       |
      +======================================================================+
                 |                                      |
                 | spawns                               | /health probe
                 | (child process)                      | (HTTP GET once live)
                 v                                      v
      +==============================+       http://localhost:8642/health
      |  PYTHON SIDECAR              |       --> {"status":"ok", ...}
      |  (child of Tauri main)       |
      |                              |
      |  python -m heretic serve     |
      |    --port 8642               |
      |                              |
      |  vebond/serve.py             |
      |  |  FastAPI app              |
      |  |  GET  /health  --> 200    |  <-- Tauri SidecarManager probes here
      |  |  GET  /ws      --> WS     |  <-- WebView React app connects here
      |  |                           |
      |  EventBus                    |
      |  |  (same as v0.4.0)        |
      |  |  ceremony state events   |
      |  |  agent token stream      |
      |  |  Rödd activity signals   |
      |  |  error events            |
      |                              |
      |  Bound to: 127.0.0.1:8642   |
      |  (localhost only;            |
      |   allow_remote_bind: false   |
      |   unless overridden in       |
      |   heretic.yaml)              |
      +==============================+
                 |
                 | ws://localhost:8642/ws
                 | (WebSocket — unchanged from v0.4.0)
                 |
                 v
      +==============================+
      |  WEBVIEW                     |
      |  (embedded in Tauri window)  |
      |                              |
      |  React frontend              |
      |  (same component tree        |
      |   as §13 — unmodified)       |
      |                              |
      |  In dev:  http://localhost:1420  (Vite dev server, cargo tauri dev)
      |  In prod: bundled React build embedded in binary                    |
      |                              |
      |  WsClient connects to:       |
      |    ws://localhost:8642/ws    |
      |    (same URL as v0.4.0)      |
      |                              |
      |  Tauri commands available    |
      |  via @tauri-apps/api:        |
      |    invoke("quit")            |
      |    invoke("focus_window")    |
      |    invoke("get_sidecar_port")|
      |  (used sparingly — WS is     |
      |   the primary data channel)  |
      +==============================+


  PID FILE LOCATIONS (platform-specific):
  -----------------------------------------
  Windows:   %APPDATA%\heretic\sidecar.pid
             (Tauri $APPDATA placeholder resolves this at runtime)
  macOS:     ~/Library/Application Support/heretic/sidecar.pid
  Linux:     ~/.local/state/heretic/sidecar.pid
             (XDG_STATE_HOME fallback if env var absent)

  Written:   by SidecarManager immediately after successful sidecar spawn
  Removed:   by SidecarManager after sidecar exits cleanly
  Read:      by SidecarManager at next Tauri startup (stale-process recovery)
  Contents:  plain text — the sidecar process ID (integer)


  THE WS SEAM — UNCHANGED FROM v0.4.0:
  ---------------------------------------
  The WebSocket wire (ws://localhost:8642/ws) and the full event/command
  protocol described in §4.8 and §13 are NOT altered by the Tauri wrapper.
  Tauri is an outer shell. The WS seam remains the single data channel
  between Python and React. Tauri commands are orthogonal and minimal.

  Relation to §13 component diagram:
  The React tree drawn in §13 is exactly what lives inside the WebView box above.
  The Tauri shell adds the native window frame around it; nothing inside the
  WebView changes between v0.4.0 and v0.4.1.


  FAILURE MODES (pre-staged; will apply once Rust build runs):
  -------------------------------------------------------------
  F-1: Sidecar spawn fails
       Cause: Python not found on PATH, or port 8642 already in use,
              or sidecar exits immediately (import error, config error)
       Tauri: does NOT open the React WebView
       User sees: small native error dialog with actionable message
                  e.g. "Python 3.10+ not found. Install Python and try again."
                       "Port 8642 already in use. Close any prior heretic session."
       Note: PyInstaller bundling (deferred to v0.4.1.x) removes the Python-on-PATH
             requirement; until then, Python 3.10+ must be installed and reachable

  F-2: /health probe times out
       Cause: sidecar spawned but /health never returns 200 within ~8s
              (e.g. uvicorn slow start, heretic.yaml parse error delaying serve)
       Tauri: same as F-1 — error window, no WebView
       Mitigation: sidecar stderr is forwarded to host stderr for diagnosis

  F-3: Sidecar dies mid-session
       Cause: Python crash, OOM kill, user kills process externally
       Tauri: WebView is still open; React's existing WS reconnect-with-backoff runs
              (backoff: 1s, 2s, 4s ... 30s per §4.8.4 Scenario B)
       User sees: ConnectionIndicator turns red ("Disconnected -- reconnecting...")
                  ChatInput and buttons disabled until reconnect succeeds
                  If reconnect never succeeds: UI stays frozen at last state,
                  ConnectionIndicator stays red, ChatInput stays disabled
       Tauri does NOT auto-restart the sidecar mid-session (by design; restart is
       explicit — user closes and reopens the app, triggering full Kynding again)

  F-4: Tauri crash (Rust panic or OS force-kill)
       Cause: unhandled Rust panic, OOM, OS kill signal
       Result: Tauri process exits without clean SidecarManager.shutdown()
               Sidecar Python process becomes orphaned (still bound to port 8642)
       Mitigation: PID file was written at sidecar spawn; next Tauri startup reads
                   it, finds the stale process, sends SIGTERM (or equivalent),
                   waits briefly, then kills it before spawning a fresh sidecar
       Note: port 8642 remains occupied until the orphan is killed;
             this is why stale-PID recovery runs before any sidecar spawn

  F-5: Python on PATH is wrong version (< 3.10) or unsupported
       Cause: system Python is old; user has not installed Python 3.10+
       Result: spawn may succeed but sidecar immediately exits with ImportError
               or syntax error; /health probe times out --> F-2 path
       User sees: error window with "install Python 3.10+ on PATH" guidance
       Resolution: PyInstaller bundle in v0.4.1.x eliminates this failure mode
                   by embedding the interpreter inside the binary
```

---

--- (v0.4.0 — Summoning Circle Substrate)

> **Added 2026-05-07 v0.4.0 (Védis Eikleið).** This section maps the face: how L4 Vébond
> (Eldahús) becomes visible to the user in v0.4.0. The body can now connect (v0.1), speak
> (v0.2), and hear (v0.3). This path reveals how the ceremony state becomes visible and
> how the user's touch becomes a command.
>
> **v0.4.0 scope:** Python `heretic serve` backend (FastAPI + WebSocket) + React/Vite frontend
> served via `npm run dev`. Browser-rendered UI only. The Tauri native shell is deferred to
> v0.4.1 (requires Rust; see TASK_HERETIC_v0.4_SUMMONING_CIRCLE.md §2 architectural constraint).
> For the Tauri shell flow that wraps this browser-served experience in a native window, see §4.9.
>
> **Aesthetic cross-reference:** The visual language for this flow is defined in
> `docs/vision/AESTHETIC.md`. Color tokens used in the components below:
> - `Eld` (amber `#c8860a` / `#e8a020`) — active connection state, LightButton, summoning ring in Tengsl/Samræður
> - `Sjón-glow` (blue `#4080b0` / `#60a8e0`) — Bifröst/layer health indicator when probing or vision-related
> - `Mál-green` (teal `#1a6050` / `#30a880`) — voice indicators (Hlust listening, Tunga speaking), active Rödd state
> - `Hvíla-grey` (`#404850`) — dormant state; the ring and most indicators at rest (Hvíld / READY pre-connection)
> - `Varúð` (sienna `#c04020`) — error and warning indicators (RECOVERING flicker, sense degraded)
>
> Sub-state → visual mapping (from CEREMONY.md §8 L4 Vébond display rules):
> - `READY` → Kynding appearance (fire kindled, Hvíla-grey ring, LightButton active)
> - `OPENING` → Kynding-rising (Eld ring slowly brightening; 1.5–2s bloom transition per AESTHETIC.md)
> - `Tengsl` → bonded (Eld ring burning steadily; breathing pulse begins; sense toggles become interactive)
> - `Samræður` → full ceremony (ring breathes at 4s sinusoidal cycle; Mál-green Rödd pulse active)
> - `RECOVERING` → flickering modifier on Tengsl/Samræður display (Varúð flicker, once per event)
> - `EXTINGUISHED` → Slokna-fading (ring dims through Hvíla-grey; returns to READY appearance)
> - `CONFIG_ERROR` → distinct error state; clear actionable message; no phase ring indicator

**Lifecycle dependency:** The WebSocket backend (`vebond/serve.py`) starts when `heretic serve`
is invoked. It is independent of — and wraps — the existing Lifecycle, BifrostClient, Tunga,
and Hlust. It exposes a single WS endpoint. The React frontend (`frontend/src/`) connects to
that endpoint on load and does not reconnect to a resumed session — each new connection is
treated as fresh state. Config port lives at `vebond.ws_port` in heretic.yaml (default 8642);
host at `vebond.ws_host` (default 127.0.0.1 — localhost only in v0.4.0, as documented in
TASK_HERETIC_v0.4_SUMMONING_CIRCLE.md §3 and LAYER_INTERFACES.md §L4).

#### 4.8.1 WebSocket Connection Lifecycle

```
  [User opens browser to http://localhost:5173 (or npm run dev URL)]
       |
       v
  [React app mounts — frontend/src/main.tsx bootstraps <App>]
       |
       v
  [frontend/src/api/ws-client.ts: WsClient constructor]
       |
       |  opens WebSocket: ws://localhost:<vebond.ws_port>/ws
       |  (port default: 8642; read from environment at build time or runtime config)
       |
       v
  [vebond/serve.py: FastAPI WebSocket endpoint /ws]
       |
       |  connection accepted
       |
       |  IMMEDIATELY: server pushes ceremony.state_changed snapshot
       |  {
       |    "event": "ceremony.state_changed",
       |    "from": null,
       |    "to": <current LifecycleState>,
       |    "timestamp": "<ISO8601>"
       |  }
       |  (this orients the fresh client without the client asking for state)
       |
       v
  [WsClient receives snapshot]
       |
       v
  [frontend/src/store/ceremony.ts: Zustand store updated]
       |
       |  store.setState({ lifecycleState: <to>, connected: true })
       |
       v
  [React components re-render — the face becomes visible]
       |
       |  LifecyclePulse: ring color/animation reflects new state
       |  LayerStatusPanel: health indicators at their known values
       |  LightButton / ExtinguishButton: enabled or disabled per state
       |  ConnectionIndicator: shows "connected"
       |
       v
  [Bidirectional event/command stream open]
       |
       |  server pushes events as ceremony state changes (see §4.8.2)
       |  client sends commands as user acts (see §4.8.3)
       |
       v
  [Disconnect — browser closes tab, or `heretic serve` process exits]
       |
       |  WsClient detects close event
       |  --> ConnectionIndicator: "disconnected"
       |  --> text input (ChatInput) disabled
       |  --> LightButton / ExtinguishButton disabled
       |  --> frontend remains visually alive at last known state
       |  --> WsClient begins exponential-backoff reconnect loop:
       |        attempt 1: after 1s
       |        attempt 2: after 2s
       |        attempt 3: after 4s  (cap at 30s; repeat)
       |        on reconnect: full re-sync (server pushes state snapshot again)
       |  (no session resume — v0.4.0 reconnect is a fresh connection; state on
       |   the Python side is authoritative and snapshoted to the new client)
```

#### 4.8.2 Server-Push Events (backend to frontend)

The Python EventBus in `vebond/serve.py` publishes events from Lifecycle, BifrostClient,
Tunga, and Hlust onto all open WS connections. All events are JSON objects with an `"event"`
discriminator field. Frontend event handler registry lives in `frontend/src/api/events.ts`;
TypeScript types in `frontend/src/types/ipc.ts` mirror Python `vebond/protocol.py`.

Total: **7 server-push event types.**

```
  EVENT 1: ceremony.state_changed
  --------------------------------
  Direction: server --> all connected clients
  Trigger:   any LifecycleState transition (see CEREMONY.md §2 full state diagram)
  Payload:
    {
      "event":     "ceremony.state_changed",
      "from":      <LifecycleState | null>,   // null on initial snapshot
      "to":        <LifecycleState>,           // one of: Hvíld, Kynding, READY, OPENING,
                                               //         Tengsl, Samræður, RECOVERING,
                                               //         Slokna, EXTINGUISHED, CONFIG_ERROR
      "timestamp": "<ISO8601>"
    }
  Consumer: LifecyclePulse (ring animation + color), LightButton (enabled?), ExtinguishButton (enabled?)

  EVENT 2: bifrost.health
  -----------------------
  Direction: server --> all connected clients
  Trigger:   Bifröst state change (DISCONNECTED | CONNECTING | CONNECTED | RECOVERING | ERROR)
  Payload:
    {
      "event":       "bifrost.health",
      "status":      "open" | "closed" | "opening" | "failed",
      "endpoint":    "<str>",               // agent endpoint URL (no API key — informational only)
      "latency_ms":  <int | null>           // null if not yet measured
    }
  Consumer: LayerStatusPanel (Bifröst row indicator)

  EVENT 3: tunga.activity
  -----------------------
  Direction: server --> all connected clients
  Trigger:   L2 Rödd Tunga state change (emitted from voice::speaking_start / voice::speaking_end)
  Payload:
    {
      "event": "tunga.activity",
      "state": "idle" | "synthesizing" | "speaking" | "failed"
    }
  Consumer: LayerStatusPanel (Tunga row); future: waveform widget (v0.4.x)

  EVENT 4: hlust.activity
  -----------------------
  Direction: server --> all connected clients
  Trigger:   L2 Rödd Hlust state change (VAD speech detection, transcription, error)
  Payload:
    {
      "event":    "hlust.activity",
      "state":    "idle" | "loading" | "listening" | "transcribing" | "failed",
      "level_db": <float | null>   // RMS level in dBFS while "listening"; null otherwise
    }
  Consumer: LayerStatusPanel (Hlust row; Mál-green animation when "listening" or "transcribing")
  Note: level_db is available from v0.4.0 VadDetector; dedicated waveform widget deferred to v0.4.x

  EVENT 5: agent.token
  --------------------
  Direction: server --> all connected clients
  Trigger:   each SSE text_delta chunk from Bifröst while a Samræður turn is in progress
  Payload:
    {
      "event":       "agent.token",
      "role":        "assistant",
      "text_delta":  "<str>",    // one token or small fragment of the spirit's reply
      "sequence_id": <int>       // monotonically increasing per turn; lets client detect drops
    }
  Consumer: ChatHistory (appends delta to in-progress message bubble in real time)

  EVENT 6: agent.turn_complete
  ----------------------------
  Direction: server --> all connected clients
  Trigger:   SSE stream sends [DONE] for the current turn, OR tool-call round-trip finishes
  Payload:
    {
      "event":         "agent.turn_complete",
      "turn_id":       "<str>",          // UUID matching the turn that generated this event
      "finish_reason": "stop" | "length" | "tool_calls" | "cancelled" | "error"
    }
  Consumer: ChatHistory (seals the in-progress message bubble; stops streaming cursor)

  EVENT 7: error
  --------------
  Direction: server --> all connected clients
  Trigger:   any recoverable error in the Vébond layer or downstream (WS decode fail,
             invalid command, internal exception that did not abort the ceremony)
  Payload:
    {
      "event":   "error",
      "level":   "warn" | "error",
      "source":  "<str>",     // e.g. "vebond.serve", "bifrost", "hlust"
      "message": "<str>"
    }
  Consumer: ToastSystem (displays ephemeral error toast; Varúð color for "error", dimmer for "warn")
```

#### 4.8.3 Client Commands (frontend to backend)

Commands are JSON objects sent by the browser over the WS connection. The backend parses them
via `vebond/protocol.py` typed command models. An unknown command type causes the server to
reply with an `error` event (level: "warn") and take no further action.

Total: **5 client command types.**

```
  COMMAND 1: light
  ----------------
  Direction: client --> server
  Trigger:   user clicks LightButton
  Payload:   {"command": "light"}
  Effect:    initiates Kynding --> READY --> OPENING --> Tengsl sequence
             (idempotent if already in Tengsl or Samræður: server replies with error event,
              level "warn", "already connected")

  COMMAND 2: extinguish
  ---------------------
  Direction: client --> server
  Trigger:   user clicks ExtinguishButton
             (if vebond.ceremony_button_confirm: true in heretic.yaml, button shows
              a confirm step before sending this command — UI-side; command arrives only after
              confirmation)
  Payload:   {"command": "extinguish"}
  Effect:    initiates Slokna --> EXTINGUISHED --> READY sequence

  COMMAND 3: send_message
  -----------------------
  Direction: client --> server
  Trigger:   user submits text in ChatInput (Enter key or send button)
  Payload:   {"command": "send_message", "text": "<str>"}
  Effect:    backend injects text as user-role message into Bifröst, starts a new turn
             (rejected if not in Tengsl or Samræður; server replies with error event)
  Note:      ChatInput is disabled when ConnectionIndicator shows disconnected

  COMMAND 4: cancel_turn
  ----------------------
  Direction: client --> server
  Trigger:   user clicks a cancel/interrupt control during an active turn (v0.4.0 UI)
  Payload:   {"command": "cancel_turn", "turn_id": "<str>"}
  Effect:    backend signals in-flight Bifröst turn to abort; finish_reason on the resulting
             agent.turn_complete event will be "cancelled"
  Note:      if turn_id does not match any active turn, server replies with error event (warn)

  COMMAND 5: toggle_sense
  -----------------------
  Direction: client --> server
  Payload:   {"command": "toggle_sense", "sense_id": "<str>", "enabled": <bool>}
  Status:    DEFERRED to v0.4.x
             In v0.4.0: command is received and acknowledged with an error event
             (level "warn", message "sense toggle not yet implemented; edit heretic.yaml
             to enable/disable senses and restart heretic serve").
             SenseTogglePanel in v0.4.0 is READ-ONLY — it displays the heretic.yaml
             state at startup but does not send this command.
```

#### 4.8.4 Reconnection and Failure Modes

```
  SCENARIO A: Backend not running when browser loads
  ---------------------------------------------------
  WsClient: WebSocket() construction fails immediately (connection refused)
  --> ConnectionIndicator: "disconnected" (Hvíla-grey)
  --> LightButton, ExtinguishButton, ChatInput: all disabled
  --> WsClient: begins backoff reconnect loop (1s, 2s, 4s ... 30s, 30s, ...)
  --> When `heretic serve` starts: next reconnect attempt succeeds
  --> Server pushes state snapshot; UI unlocks

  SCENARIO B: Backend exits mid-ceremony (crash or Ctrl+C)
  ----------------------------------------------------------
  WsClient: receives WS close frame (or times out on keepalive if crash)
  --> ConnectionIndicator: "disconnected" immediately
  --> ChatInput disabled; buttons disabled
  --> WsClient: begins backoff reconnect loop
  --> Ceremony state on backend side is lost (v0.4.0 has no server-side session persistence)
  --> When backend restarts: client reconnects; receives fresh Hvíld snapshot
  --> User must click LightButton again to re-open Bifröst

  SCENARIO C: WS error during agent.token stream
  -----------------------------------------------
  WsClient: WS error event fires (not a clean close)
  --> log.warn in WsClient; attempt immediate single reconnect
  --> if reconnect succeeds: state snapshot received; chat history in Zustand store
      is preserved (it is client-side memory; not lost on WS reconnect)
  --> if reconnect fails: standard backoff loop begins
  --> in-progress message bubble in ChatHistory remains visible with partial content;
      ToastSystem shows a "Reconnecting..." toast

  SCENARIO D: Invalid command sent by client
  ------------------------------------------
  Server: receives unknown "command" field value
  --> server replies: {"event":"error","level":"warn","source":"vebond.serve",
                       "message":"unknown command: <cmd>"}
  --> client: ToastSystem shows warn toast; no state change

  SCENARIO E: IPC message decode error (malformed JSON from server)
  -----------------------------------------------------------------
  WsClient: JSON.parse() throws
  --> log.warn in ws-client.ts; message discarded; no crash
  --> ToastSystem: no visible toast (warn-level decode errors are silent; see LAYER_INTERFACES.md §L4)
```

#### 4.8.5 Config Dependencies for the UI Path

| Config key | Default | Controls |
|---|---|---|
| `vebond.ws_port` | `8642` | Port for WS server (`ws://localhost:<port>/ws`); frontend must match |
| `vebond.ws_host` | `"127.0.0.1"` | Bind host; localhost only in v0.4.0; set `vebond.allow_remote_bind: true` for non-localhost (opt-in, v0.4.x) |
| `vebond.theme` | `"dark_norse"` | Visual theme; no alternatives in v0.4.0 (dark mode is identity per AESTHETIC.md) |
| `vebond.show_agent_text_stream` | `true` | If false, `agent.token` events are not forwarded to WS; ChatHistory shows only completed turns |
| `vebond.ceremony_button_confirm` | `true` | If true, ExtinguishButton shows a confirm step before sending `extinguish` command |
| `vebond.show_frame_thumbnail` | `false` | If true, vision frames from Sjón are sent to UI (deferred; v0.5+ when Sjón ships) |

---

### 4.9 Tauri Shell Flow (v0.4.1 — pre-staged)

> **Added 2026-05-07 v0.4.1 (Védis Eikleið).** This section maps the lifecycle of the Tauri
> native shell that wraps the v0.4.0 substrate. The shell is pre-staged: code is scaffolded in
> `src-tauri/` but not yet compiled (Rust toolchain not installed). The routes described here
> apply once `cargo tauri build` runs and the user launches `heretic.exe` (or `.app` / `.AppImage`).
>
> The interior protocol — the WS seam, the React component tree, all seven server-push events,
> all five client commands — is the same as §4.8. This section maps only the new outer layer:
> from the OS launcher to the first WebSocket frame. For the structural diagram, see §14.
>
> **IPC note (from IPC_PROTOCOL.md §1):** The `/health` endpoint returns
> `{"status":"ok","version":"<str>","lifecycle_state":"<str>"}`. The Tauri SidecarManager
> inspects `status` only; `lifecycle_state` is informational. Tauri does not gate on ceremony
> state — it only requires the server to be up.

#### 4.9.1 Startup Sequence

```
  [User double-clicks heretic.exe (or OS launcher equivalent)]
       |
       v
  [Tauri main process initializes]
  (src-tauri/src/main.rs: tauri::Builder::default()...)
       |
       |  reads tauri.conf.json:
       |    window geometry, theme (dark), frameless flag
       |    sidecar binary reference (python -m heretic serve)
       |    single-instance plugin config
       |
       v
  [SidecarManager.startup() -- src-tauri/src/sidecar.rs]
       |
       |  (stale-PID check — runs before spawn)
       |    read PID file at:
       |      Windows: %APPDATA%\heretic\sidecar.pid
       |      macOS:   ~/Library/Application Support/heretic/sidecar.pid
       |      Linux:   ~/.local/state/heretic/sidecar.pid  (XDG_STATE_HOME or fallback)
       |    if PID file exists and process is alive --> kill it (SIGTERM + 3s + force)
       |    delete stale PID file
       |
       v
  [Tauri spawns Python sidecar as child process]
       |
       |  command: python -m heretic serve --port 8642
       |    (in dev: system Python; in prod v0.4.1.x: PyInstaller bundle -- deferred)
       |  sidecar stderr forwarded to host stderr for diagnosis
       |  if spawn returns OS error immediately (Python not found, permission denied):
       |    --> F-1: Tauri shows error window; WebView never opens; exits
       |
       |  on successful spawn:
       |    write sidecar PID to PID file
       |
       v
  [SidecarManager probes GET http://localhost:8642/health with backoff]
       |
       |  attempt 1: wait 250ms, probe
       |  attempt 2: wait 500ms, probe
       |  attempt 3: wait 1s,    probe
       |  attempt 4: wait 2s,    probe
       |  attempt 5: wait 4s,    probe  (total elapsed: ~8s max)
       |
       |  each probe: HTTP GET http://localhost:8642/health
       |    200 response with {"status":"ok",...}  --> proceed
       |    connection refused / non-200            --> retry
       |    all attempts exhausted                  --> F-2: timeout error window
       |
       v
  [/health 200 received]
       |
       v
  [WindowManager creates the WebView window]
       |
       |  dev mode:  points WebView at http://localhost:1420 (Vite dev server)
       |  prod mode: loads bundled React build from binary (no external URL)
       |  window config: frameless dark Norse chrome per AESTHETIC.md
       |  window is visible to user here for the first time
       |  (no flash: dark background fills before React hydrates)
       |
       v
  [WebView loads React app -- frontend/src/main.tsx bootstraps <App>]
       |
       v
  [WsClient constructor: opens ws://localhost:8642/ws]
       |
       v
  [Ceremony state snapshot pushed by server -- same as §4.8.1]
       |
       v
  [Bidirectional WS event/command stream open -- same as §4.8]
```

At this point the user sees Eldahús in the same Hvíld or Kynding state they would see in
browser mode. The Tauri shell has dissolved into the background — the ceremony owns the stage.
The window opens during Hvíld (READY state); the user must click "Light the Candle" (LightButton)
to begin Kynding → READY → OPENING → Tengsl. Tauri does not automatically initiate the ceremony.

#### 4.9.2 Steady-State

During the ceremony (Tengsl or Samræður), the data channels are identical to §4.8:

```
  [User action in WebView]
       |
       v WS send (ClientCommand)
  [Python sidecar: vebond/serve.py WebSocket endpoint]
       |
       v (event, agent call, layer dispatch, etc.)
  [Python sidecar: vebond/serve.py EventBus]
       |
       v WS push (ServerEvent)
  [WebView React: events.ts handlers --> store/ceremony.ts --> components re-render]
```

Tauri commands during steady-state are rare and orthogonal to the WS protocol:

```
  @tauri-apps/api invoke("quit")
      --> WindowManager.close()
      --> RunEvent::ExitRequested fires
      --> SidecarManager.shutdown() (see §4.9.3)

  @tauri-apps/api invoke("focus_window")
      --> brings the HERETIC window to the foreground
      --> used if a notification or system event causes the app to lose focus

  @tauri-apps/api invoke("get_sidecar_port")
      --> returns the configured sidecar port (u16, e.g. 8642)
      --> for informational display or future dynamic-port support
      --> not used for WS connection (WsClient uses compiled-in default or env var)
```

#### 4.9.3 Shutdown Sequence

```
  [User closes window — X button, Cmd+Q, Alt+F4 — OR clicks Extinguish then closes]
       |
       v
  [If Extinguish was clicked first (optional but graceful):
     WsClient sends ExtinguishCommand --> server initiates Slokna --> EXTINGUISHED
     Ring dims per AESTHETIC.md Slokna animation
     User then closes window]
       |
       v
  [Tauri EventLoop receives RunEvent::ExitRequested]
       |
       v
  [SidecarManager.shutdown()]
       |
       |  sends graceful termination signal to sidecar child process:
       |    Unix:    SIGTERM
       |    Windows: CTRL_BREAK_EVENT sent to the process group
       |
       |  waits up to 5s for sidecar to exit:
       |    sidecar receives signal, flushes session log, closes uvicorn
       |    exits cleanly --> SidecarManager receives exit status
       |
       |  if sidecar has NOT exited after 5s:
       |    force-kill: TerminateProcess (Windows) / SIGKILL (Unix)
       |    wait for process tree to clear
       |
       |  delete PID file (if sidecar exited cleanly or was force-killed)
       |
       v
  [Tauri closes the WebView window]
       |
       v
  [Tauri main process exits]
       |
       v
  [System returns to Hvíld -- no processes remaining on port 8642]
```

#### 4.9.4 Failure Modes

All five failure modes are mapped in §14's diagram with additional technical detail.
Summary table:

| Failure | When | Tauri response | User sees |
|---|---|---|---|
| F-1: Sidecar spawn fails | Startup | No WebView; error window | Actionable message (Python not found, port busy) |
| F-2: /health probe timeout | Startup | No WebView; error window | "Sidecar did not start in time" with stderr hint |
| F-3: Sidecar dies mid-session | During ceremony | WebView stays open | ConnectionIndicator red; WS reconnect backoff runs |
| F-4: Tauri crash / force-kill | Any time | Tauri exits ungracefully | Next startup: stale-PID recovery kills orphaned sidecar |
| F-5: Wrong Python version | Startup | Sidecar exits immediately; /health timeout | Same as F-2; message specifies "Python 3.10+ required" |

**Relation to §4.8 (browser dev mode):** §4.8 describes the same WS protocol as it runs in a
browser tab pointed at the Vite dev server. §4.9 wraps that exact experience in a Tauri window:
the frontend does not change; the WebSocket URL does not change; only the outer container changes.
In `cargo tauri dev` (development mode), Tauri opens a window pointed at `http://localhost:1420`
while the developer runs `heretic serve` separately — the same hybrid flow as §4.8 but inside a
native window. In production, Tauri both spawns the sidecar and serves the bundled React build.

**PyInstaller deferral note (from TASK_HERETIC_v0.4.1_TAURI_WRAP.md §4):** Until v0.4.1.x ships
PyInstaller bundling, the production installer requires Python 3.10+ on the user's PATH. F-1 and
F-5 are the failure modes that expose this gap. They are documented; the user receives a clear
install message. This is an accepted risk for v0.4.1. Once PyInstaller bundles the interpreter,
F-5 is eliminated and F-1 is reduced to the port-busy case only.

---

### 4.10 Sight Flow (v0.5 — on-demand, outbound vision)

> **Added 2026-05-08 v0.5 (Védis Eikleið).** This section maps the third sense river: the user's
> screen captured locally, encoded as inline base64 PNG, and injected into the user-role message
> that travels to the spirit. v0.2 mapped the outbound breath (Tunga, §4.6); v0.3 mapped the
> inbound voice (Hlust, §4.7); this maps the inbound image (Sjón).
>
> **Mirror of Tunga:** Where Tunga is automatic and continuous (every agent text fragment
> triggers audio), Sjón is on-demand and per-turn (one snapshot per user message send).
> Tunga: agent text out → audio out. Sjón: user message send → screen in → image in.
> The body speaks outward without being asked; it shows its eyes when the user speaks.
>
> **Scope:** v0.5 ships on-demand screen capture only. Periodic interval capture
> (the `sjon.screen.interval_ms` config field), ring-buffer recall, multi-monitor support,
> and webcam are deferred to v0.5.x. The L5 Auga MCP wrapper (`auga.snapshot` tool —
> agent-callable on-demand capture) is deferred to v0.7+.
>
> **Privacy invariant (sealed):** Frames are never written to disk under any default
> configuration. `sjon.screen.save_frames` defaults to false. Even when the user opts in
> (`save_frames: true`), frames are written only to an ephemeral session-scoped temp
> directory that is deleted on Slokna (STATE_SLOKNA cleanup). Frames exist only in memory
> and in the outbound HTTP request body.

**Lifecycle dependency:** Sjón initialises at Kynding (MssBackend probed; availability
determined; SjonOrchestrator created; throttle state zeroed). The first actual capture
happens during Samræður, triggered by the user sending a message.

#### 4.10.1 Trigger — when does Sjón fire?

```
  SAMRAEDUR — user submits a message via ChatInput or CLI

  [User presses Enter / sends a message]
       |
       v
  [CLI _async_light turn loop  OR  Vébond send_message handler]
       |
       |  evaluates sight conditions:
       |    1. sjon.screen.enabled = true                        (config gate)
       |    2. bifrost.client.capability_vision_in = true        (agent capability gate)
       |    3. not throttled by min_interval_ms                  (rate gate)
       |
       |  IF all three conditions met:
       |    --> await sjon.snapshot()                            (see §4.10.2)
       |    --> image_data_urls: list[str] returned (may be empty on error)
       |
       |  IF any condition is false:
       |    --> image_data_urls = []
       |    --> proceed with text-only user message (no Sjón activity emitted)
       |
       v
  [image_data_urls passed into bifrost.send_message(text, image_data_urls)]
       |
       |  (see §4.10.3 for Bifröst integration)
```

#### 4.10.2 Capture Pipeline — SjonOrchestrator.snapshot()

```
  [SjonOrchestrator.snapshot() called]
       |
       |  emits: sjon.activity  state="capturing"
       |           --> L4 Vébond LayerStatusPanel shows Sjón row as "capturing"
       |           --> color: Sjón-glow blue (#4080b0 / #60a8e0 glow per AESTHETIC.md)
       |
       v
  [MssBackend.capture(monitor="primary")]                        (sync, run_in_executor)
       |
       |  calls: mss.mss().grab(monitor)
       |    monitor: primary screen (index 1 in mss convention)
       |    returns: raw BGRA bytes + width + height
       |             (mss returns BGRA, not RGB — conversion step required)
       |
       |  wraps sync mss call in asyncio.run_in_executor(None, ...)
       |    (mss capture is not async-native; run_in_executor keeps event loop free)
       |
       v
  [SjonOrchestrator emits: sjon.activity  state="encoding"]
       |
       v
  [FrameEncoder.encode(bgra_bytes, width, height)]               (sync, run_in_executor)
       |
       |  Step 1 — BGRA → PIL.Image (RGB):
       |    PIL.Image.frombytes("RGBA", (width, height), bgra_bytes)
       |    .convert("RGB")
       |    (mss uses BGRA byte order; frombytes with "RGBA" mode + convert handles swap)
       |
       |  Step 2 — optional resize (max 1280×720):
       |    if width > 1280 OR height > 720:
       |      image.thumbnail((1280, 720), PIL.Image.LANCZOS)
       |      (thumbnail is in-place; preserves aspect ratio; does not upscale)
       |    config keys: sjon.screen.width (default 1280), sjon.screen.height (default 720)
       |
       |  Step 3 — PNG encode:
       |    buffer = io.BytesIO()
       |    image.save(buffer, format="PNG", compress_level=6)
       |    png_bytes = buffer.getvalue()
       |    (compress_level 6: good ratio, fast encode; range 0-9)
       |
       |  Step 4 — base64 encode:
       |    b64_str = base64.b64encode(png_bytes).decode("ascii")
       |
       |  Step 5 — data URL:
       |    data_url = f"data:image/png;base64,{b64_str}"
       |
       |  returns: data_url (str)
       |    typical size: 1280x720 screen → ~0.8–1.2 MB as PNG (content-dependent)
       |
       v
  [SjonOrchestrator emits: sjon.activity  state="idle"]
       |
       v
  [SjonOrchestrator returns: [data_url]]
       |
       |  throttle bookkeeping:
       |    last_capture_ts = now()
       |    (next call within min_interval_ms returns cached frame or [] — see §4.10.4 F-5)
       |
       v
  [CLI / Vébond receives: image_data_urls = [data_url]]
```

#### 4.10.3 Bifröst Integration — injecting the frame

```
  [bifrost.send_message(text, image_data_urls=["data:image/png;base64,..."])]
       |
       |  constructs OpenAI-compat message content as a typed-parts array:
       |
       |    content = [
       |      {"type": "text", "text": "<user message text>"},
       |      {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
       |    ]
       |
       |  (format sealed in audit C-Q-C3: inline base64, not URL reference;
       |   the "image_url" type with a data: URI is the OpenAI vision wire format;
       |   see AUDIT_v0.0_INITIAL_DOC_SET.md C-Q-C3)
       |
       |  IF image_data_urls is empty or None:
       |    content = "<user message text>"   (plain string, not a list)
       |    (no image content blocks; backward-compatible with non-vision agents)
       |
       |  POST <bifrost.endpoint>/v1/chat/completions
       |  body: {
       |    "model": "<bifrost.model>",
       |    "messages": [
       |      ... conversation history,
       |      {"role": "user", "content": <content above>}
       |    ],
       |    "tools": [<all enabled sense schemas>],
       |    "stream": true,
       |    "max_tokens": 127000
       |  }
       |
       v
  [Pi / Hermes Agent]
       |
       |  receives the user message with the inline PNG
       |  interprets screen content as part of the turn context
       |  responds with text (and optionally tool calls) as usual
       |
       v
  [response flows back through §4.1 / §4.6 — Tunga speaks the reply]
```

Session log entry (written by L0 Grunnr):
```json
{
  "event": "sjon_snapshot",
  "ts": "...",
  "width": 1280,
  "height": 720,
  "png_bytes": 943210,
  "b64_chars": 1257616,
  "backend": "mss",
  "monitor": "primary",
  "encode_ms": 180,
  "saved_to_disk": false
}
```

#### 4.10.4 Fallback Paths

Six failure modes are defined. In all cases the lifecycle does not crash; the turn proceeds
without an image; the user is informed via a logged warning (and, in v0.5 with Vébond active,
an `error` event surfaced as a toast notification).

```
  F-1: mss library not installed
    MssBackend.available() returns False at Kynding
    SjonOrchestrator falls back to NullBackend
    snapshot() returns []
    CLI / Vébond proceeds with text-only turn
    sjon.activity events: NOT emitted (orchestrator knows no capture will occur)
    log.warn: "mss library not available — Sjón disabled; install heretic[vision]"
    capability flag ?vision_screen becomes false (note: see §4.10.5 for naming gap)

  F-2: macOS screen recording permission denied
    MssBackend.capture() raises mss.exception.ScreenShotError (permission variant)
    SjonOrchestrator catches PermissionDeniedError
    returns []
    sjon.activity: state="failed" emitted
    log.warn: "Screen recording permission denied — grant access in System Settings > Privacy > Screen Recording"
    user must restart ceremony after granting permission
    (macOS-specific; Windows and Linux do not require explicit permission grants in typical configurations)

  F-3: PNG encoding fails (Pillow exception)
    FrameEncoder raises FrameEncodingError (wraps PIL exception)
    SjonOrchestrator catches; returns []
    sjon.activity: state="failed" emitted
    log.warn: "Frame encoding failed — Sjón frame dropped for this turn; <exception detail>"
    turn proceeds without image

  F-4: oversized result (PNG > 4 MB after compression)
    SjonOrchestrator checks len(png_bytes) after encode
    IF > 4 MB:
      retry at 50% scale (image.thumbnail(width//2, height//2))
      re-encode
      IF still > 4 MB: frame dropped; returns []
      log.warn: "Frame oversized after compression; 50% rescale applied"
      IF rescale succeeds: normal path resumes with smaller frame
    (worst case 1280x720 PNG is ~1.2 MB; this path should not trigger under normal conditions;
     it exists as a safety catch for unusual displays or future higher-resolution capture)

  F-5: throttle reject (called within min_interval_ms of last capture)
    default min_interval_ms: 1000 ms (1 second)
    SjonOrchestrator.last_capture_ts compared to now()
    IF delta < min_interval_ms:
      BEHAVIOR CHOSEN: returns [] (no cached frame sent)
      rationale: a cached frame from a prior turn may no longer represent the user's
                 current screen state; sending stale frames as if current is misleading.
                 The spirit should receive a current frame or none at all.
      log.debug: "Sjón throttle active — skipping capture (last: <delta>ms ago)"
      no sjon.activity events emitted
    config key: sjon.screen.min_interval_ms (default 1000; operator can reduce to 0 to disable)

  F-6: ?vision_in capability flag not set on connected agent
    CLI / Vébond evaluates bifrost.client.capability_vision_in = false
    snapshot() is NEVER CALLED
    no Sjón activity events emitted
    image_data_urls = [] passed to send_message (plain text turn)
    No warning emitted — this is expected behavior for non-vision agents
```

#### 4.10.5 Capability Flag Naming Gap — Architect Action Required

> **Naming inconsistency identified by Védis Eikleið, 2026-05-08.**
>
> Two different names are currently in use for the vision capability flag:
>
> | Document | Flag name used | Section |
> |---|---|---|
> | `LAYER_INTERFACES.md §L3 Sjón` (Capability flags) | `?vision_screen` | §L3 |
> | `LAYER_INTERFACES.md §L1 Bifröst` (Capability flags) | `?vision_in` | §L1 |
> | `AGENT_AGNOSTIC_PROTOCOL.md` | `?vision_in` (everywhere) | §5.1, §5.2, §5.3 |
> | `TASK_HERETIC_v0.5_FIRST_SIGHT.md §1` | `?vision_in` (as cleaned-up name) | §1 |
> | This document (§4.10) | `?vision_in` | §4.10 throughout |
>
> **Assessment:** `?vision_in` is the v0.4.1 cleaned-up name and the majority position.
> `?vision_screen` in LAYER_INTERFACES.md §L3 is a drift artifact — it pre-dates the
> v0.4.1 `?voice_in`/`?voice_out` naming cleanup that canonicalized the inbound/outbound
> pattern. The correct name is `?vision_in`.
>
> **Action required (Architect — Rúnhild Svartdóttir):** Update LAYER_INTERFACES.md §L3
> Capability flags block to read `?vision_in` (screen capture enabled and permission granted)
> in place of `?vision_screen`. The `?vision_webcam` flag in §L3 is unambiguous and
> requires no change.
>
> Until the Architect closes this gap, the Forge Worker should implement code using
> `?vision_in` as the canonical flag name — matching §L1, AGENT_AGNOSTIC_PROTOCOL.md,
> and this map.

#### 4.10.6 Config Dependencies for the Sight Path

| Config key | Default | Controls |
|---|---|---|
| `sjon.screen.enabled` | `true` | Master toggle — `false` means Sjón does not attempt capture; CLI/Vébond never calls snapshot() |
| `sjon.screen.width` | `1280` | Max output width (pixels); thumbnail() will not upscale below this |
| `sjon.screen.height` | `720` | Max output height (pixels); thumbnail() preserves aspect ratio |
| `sjon.screen.save_frames` | `false` | Opt-in disk save; even when true, saves only to ephemeral session-scoped temp dir; deleted on Slokna |
| `sjon.screen.buffer_depth` | `5` | Ring buffer size (reserved for v0.5.x periodic capture; not used in v0.5 on-demand mode) |
| `sjon.screen.min_interval_ms` | `1000` | Throttle gate — minimum ms between captures; 0 disables throttle |
| `bifrost.vision_in` | `true` | Config-level declaration of agent vision support; read as `?vision_in` capability flag (note: v0.1 probe semantics — config-read, not verified round-trip; see LAYER_INTERFACES.md §L1 probe conservatism note) |

Full schema lives in `src/heretic/sjon/config_model.py SjonConfig` and LAYER_INTERFACES.md §L3 Sjón.

#### 4.10.7 Continuous task lifecycle (v0.5.1)

> **Added 2026-05-08 v0.5.1 (Védis Eikleið).** The eye that once opened only when spoken to now
> keeps its own watch. This section maps the background capture loop that begins at TENGSL and
> runs until SLOKNA, feeding the ring buffer one frame at a time.

```
  TENGSL transition — ceremony connects
       |
       |  IF config.sjon.screen.continuous = true:
       |    sjon.start_continuous_capture() called
       |         |
       |         |  creates asyncio.Task (stored as _continuous_task)
       |         |  task body: continuous capture loop
       |         |
       |         v
       |    [continuous capture loop — runs until cancelled]
       |         |
       |         |  loop iteration:
       |         |    record tick_start = now()
       |         |
       |         |    [capture + encode — same pipeline as snapshot()]
       |         |      MssBackend.capture(monitor mapped per §4.10.10)
       |         |      run_in_executor (sync wrapped, same as on-demand path)
       |         |      FrameEncoder.encode(...)
       |         |      run_in_executor (sync wrapped)
       |         |
       |         |    IF capture+encode succeeds:
       |         |      push data_url to ring buffer (deque append, see §4.10.8)
       |         |      emit sjon.activity(state="buffer_updated", depth=len(buffer))
       |         |
       |         |    IF capture+encode fails (any exception):
       |         |      log.warning — tick skipped; buffer unchanged
       |         |      no sjon.activity failure event emitted per tick (too noisy)
       |         |
       |         |    [throttle re-enforcement]
       |         |      elapsed = now() - tick_start
       |         |      sleep_for = max(0, (config.sjon.screen.min_interval_ms / 1000) - elapsed)
       |         |      IF sleep_for < (config.sjon.screen.interval_ms / 1000):
       |         |        sleep_for = config.sjon.screen.interval_ms / 1000
       |         |        (interval_ms is the floor; min_interval_ms can only extend, never shorten)
       |         |
       |         |    [backpressure gate — was the last capture still in flight?]
       |         |      IF the previous run_in_executor had not completed when the tick woke:
       |         |        tick is SKIPPED entirely (no queued capture)
       |         |        log.debug: "Sjón continuous: tick skipped — previous capture still in flight"
       |         |        await asyncio.sleep(interval_ms / 1000) and continue
       |         |        rationale: prevents runaway accumulation under system load;
       |         |                   one frame late is better than many frames queued
       |         |
       |         v
       |    await asyncio.sleep(sleep_for)
       |    (loop repeats until task cancelled)
       |
       v
  SLOKNA transition — ceremony extinguishes
       |
       |  sjon.stop_continuous_capture() called:
       |    _continuous_task.cancel()
       |    await task (catches CancelledError)
       |    _continuous_task = None
       |
       |  ring buffer cleared (see §4.10.8 privacy invariant)
```

**Config keys for continuous mode:**

| Config key | Default | Controls |
|---|---|---|
| `sjon.screen.continuous` | `false` | Master toggle for periodic capture; on-demand path always available regardless |
| `sjon.screen.interval_ms` | (to be set by operator) | Target milliseconds between capture ticks; operator tunes to desired watch cadence |
| `sjon.screen.min_interval_ms` | `1000` | Minimum gap enforced; continuous mode respects this even if interval_ms is lower |
| `sjon.screen.attach_policy` | `"latest"` | How the per-turn message attaches buffered frames; see §4.10.9 |

#### 4.10.8 Ring buffer

> The eye does not hold every moment it sees — only the most recent handful. The oldest fades
> when a newer arrives and the depth is full.

```
  Ring buffer — lives inside SjonOrchestrator

  Implementation:
    self._frame_buffer: collections.deque = collections.deque(maxlen=config.sjon.screen.buffer_depth)
    default buffer_depth: 5 (already declared in SjonConfig; now activated in v0.5.1)

  Write path (continuous loop tick):
    self._frame_buffer.append(data_url)
    - data_url is a complete "data:image/png;base64,..." string
    - if len == maxlen: oldest entry is automatically evicted (deque maxlen behavior)
    - no explicit lock needed for append — asyncio single-threaded; appends are atomic from
      the perspective of the event loop

  Read path (Sjón.recent_frames):
    def recent_frames(n: int | None = None) -> list[str]:
      frames = list(self._frame_buffer)   (snapshot of current state)
      if n is None:
        return frames                     (all buffered frames, oldest first)
      return frames[-n:]                  (last N frames, most recent last)

  Traversal note:
    deque iteration during append is safe in asyncio (single-threaded),
    but if multi-threaded access is ever added, an asyncio.Lock would be required here.
    The current design is asyncio-only; no threading is introduced in v0.5.1.

  Overflow behavior:
    maxlen=5 means the buffer never grows beyond 5 frames.
    On the 6th append, frame[0] (oldest) is dropped silently.
    This is the standard deque(maxlen) contract — no code required for eviction.

  Privacy invariant (sealed from v0.5, re-enforced here):
    self._frame_buffer.clear() is called:
      - inside stop_continuous_capture()
      - inside Sjón.close() (called by the SLOKNA lifecycle transition)
    The buffer is NEVER written to disk.
    No frame from the ring buffer is persisted past the ceremony in any form.
    The buffer only exists while the ceremony is live and continuous mode is active.
```

**Ring buffer state transitions:**

```
  [buffer empty, continuous not started]
       |
       |  start_continuous_capture() called
       v
  [continuous running — frames accumulating]
    buffer: [frame_1, frame_2, frame_3]  (grows up to maxlen)
    on overflow: [frame_2, frame_3, frame_4]  (oldest evicted)
       |
       |  stop_continuous_capture() called  (SLOKNA)
       v
  [buffer cleared — [] — continuous stopped]
```

#### 4.10.9 Attach-policy decision tree (per-turn)

> When the user speaks, the question arises: what should the eye send with the words?
> Three answers are offered. One is the default; the others are for operators who know the cost.

```
  [user message arrives — turn begins]
       |
       |  pre-check (same as on-demand; no change from §4.10.1):
       |    capability_vision_in = true?  AND  sjon.screen.enabled = true?
       |    IF either is false: image_data_urls = []  (text-only turn)
       |
       v
  [continuous mode active? — config.sjon.screen.continuous = true?]
       |
       |  IF NOT continuous (or buffer is empty):
       |    --> fall back to on-demand snapshot() (the v0.5 path, §4.10.2)
       |    image_data_urls = [await sjon.snapshot()]  (one fresh frame)
       |    (if snapshot returns []: text-only turn)
       |
       |  IF continuous AND buffer has frames:
       |    evaluate config.sjon.screen.attach_policy:
       |
       |    attach_policy = "none":
       |      image_data_urls = []
       |      turn is text-only regardless of buffer contents
       |      use case: operator wants the eye watching but not attaching
       |                (e.g., logging only, future annotation tools)
       |
       |    attach_policy = "latest"  (DEFAULT):
       |      image_data_urls = [sjon.recent_frames(n=1)[-1]]  (most recent frame)
       |      one frame per turn — mirrors v0.5 on-demand behavior
       |      if buffer is empty (not yet filled after continuous start):
       |        fall back to on-demand snapshot()
       |      cost: same as v0.5 on-demand — one inline PNG per turn
       |
       |    attach_policy = "all_buffered":
       |      image_data_urls = sjon.recent_frames()  (up to buffer_depth frames)
       |      all currently buffered frames attached in order (oldest first)
       |      use case: operator needs temporal context ("show me the last 5 frames")
       |      COST WARNING: attaches up to buffer_depth x single-frame cost per turn
       |        at buffer_depth=5 and ~1 MB per frame: up to ~5 MB per turn injected
       |        operator must opt in explicitly; not the default
       |      token implication: each image_url content block consumes vision tokens
       |        frame count x approximate_tokens_per_image; operator is responsible for
       |        understanding the model's per-image token cost before enabling this policy
       |
       v
  [image_data_urls passed into bifrost.send_message(text, image_data_urls)]
  [Bifröst integration unchanged — see §4.10.3]
```

#### 4.10.10 Multi-monitor index mapping (CRITICAL — intentional asymmetry between modes)

> **This is the most subtle contract in v0.5.1. Forge Worker and Auditor must both read this
> section carefully.** The same config field — `config.sjon.screen.monitor_index` — resolves
> differently depending on which capture mode is active. This is not a bug; it is an intentional
> design choice that matches the semantic intent of each mode.

```
  mss monitor indexing convention (underlying library):
    mss index 0  = the all-monitors virtual composite (all displays merged into one canvas)
    mss index 1  = primary monitor (single screen, first physical display)
    mss index N  = the Nth physical display (1-indexed for individual monitors)

  config.sjon.screen.monitor_index — operator-facing field:
    default: 0

  How monitor_index 0 is mapped — PER MODE:

  +---------------------------------------------------------+
  |  MODE           | monitor_index=0 maps to | Rationale   |
  +---------------------------------------------------------+
  | ON-DEMAND       | mss index 1             | "show me my |
  | (v0.5 path)     | (primary monitor)       |  work" —    |
  |                 |                         |  one clean   |
  |                 |                         |  user-       |
  |                 |                         |  meaningful  |
  |                 |                         |  screen      |
  +---------------------------------------------------------+
  | CONTINUOUS      | mss index 0             | "watch what |
  | (v0.5.1 path)   | (all-monitors           |  I'm doing" |
  |                 |  composite)             |  — full      |
  |                 |                         |  context,    |
  |                 |                         |  multi-      |
  |                 |                         |  display     |
  |                 |                         |  visible     |
  +---------------------------------------------------------+
  | EITHER MODE     | mss index N (direct)    | operator has |
  | monitor_index=N | (individual screen N)   |  chosen a    |
  | (N >= 1)        |                         |  specific    |
  |                 |                         |  display     |
  +---------------------------------------------------------+
```

**Capture.py implementation contract for Forge:**

```python
  def _resolve_mss_monitor(mode: str, config_index: int) -> int:
      """
      Map config monitor_index to mss monitor index.

      mode: "on_demand" | "continuous"
      config_index: value from config.sjon.screen.monitor_index (default 0)

      Returns: integer index to pass to mss.mss().grab(monitors[index])
      """
      if config_index >= 1:
          return config_index          # direct pass-through for specific screen
      # config_index == 0: mode-dependent default
      if mode == "continuous":
          return 0                     # mss 0 = all-monitors composite
      else:
          return 1                     # mss 1 = primary monitor (on-demand default)
```

**Why this asymmetry is intentional:**

The on-demand path exists for the moment when the user says "look at this" — they want the agent
to see the primary working screen, cleanly framed, without distraction from secondary monitors.
Mapping config 0 to mss 1 (primary) achieves this and matches how most users think of "the screen."

The continuous path exists so the agent can keep context across time — it watches the full
workspace, not just one panel. Mapping config 0 to mss 0 (all-monitors composite) gives the
agent the widest view for that purpose. A user with multiple monitors is likely using them all.

An operator who wants on-demand to capture all monitors (or continuous to capture only primary)
can override by setting `monitor_index: 1` (primary explicit) or by choosing the mss index
directly. The default is tuned for the most common and most semantically appropriate behavior.

**Audit check for Auditor (Sólrún Hvítmynd):** verify that `_resolve_mss_monitor` is called
in BOTH the on-demand snapshot() path AND the continuous capture tick, with the correct mode
string passed. A tick that accidentally passes `"on_demand"` will silently capture only primary
instead of the composite — the wrong semantic without a visible error. The mode string must
be injected from the context where the call originates, not derived inside the function.

**Config dependencies for multi-monitor (v0.5.1 additions):**

| Config key | Default | Controls |
|---|---|---|
| `sjon.screen.monitor_index` | `0` | Operator-chosen monitor; see mapping table above |
| `sjon.screen.continuous` | `false` | Determines which branch of the index-0 mapping fires |

#### 4.10.11 Webcam capture pipeline (v0.5.2)

> **Added 2026-05-08 v0.5.2 (Védis Eikleið).** The eye gains a second source. Where the screen
> shows what the spirit can see of the work, the webcam shows what the spirit can see of the
> worker — face, room, lighting, physical presence. Because of this, the privacy gate for webcam
> is stronger than for screen: `sjon.webcam.enabled` defaults to `false` and requires an explicit
> operator opt-in. The pipeline mirrors the screen path with one additional step: OpenCV BGR frame
> bytes must be converted to RGB before PIL can interpret them correctly.
>
> **Trigger:** Webcam capture fires at exactly the same moment as the screen path — when the user
> sends a message — subject to the same three gates:
> 1. `sjon.webcam.enabled: true` (config gate — default false)
> 2. `bifrost.client.capability_vision_in = true` (agent capability gate — same as screen)
> 3. `sjon.webcam.attach_policy` is not `"screen_only"` (policy gate — see §4.10.12)

```
  [snapshot_webcam() called — by CLI / Vébond per-turn dispatch]
       |
       |  IF sjon.webcam.enabled = false:
       |    return []  (no attempt; no warning; this is expected default)
       |
       v
  [WebcamCaptureBackend.open(device_index)]                       (lazy init)
       |
       |  cv2.VideoCapture(config.sjon.webcam.device_index)
       |    device_index default: 0  (first available webcam)
       |    lazy open: VideoCapture object created on first call to snapshot_webcam();
       |    held for the ceremony lifetime; released in Sjón.close() at SLOKNA
       |
       |  IF cv2 unavailable at import time (NullWebcamBackend):
       |    return []
       |    log.warn: "opencv-python not installed — webcam capture unavailable; "
       |              "install heretic[vision] to enable"
       |    ?vision_webcam capability flag = false
       |
       |  IF device_index not found or VideoCapture.isOpened() = False:
       |    return []
       |    log.warn: "Webcam device <N> not found or could not be opened"
       |    ?vision_webcam capability flag = false
       |
       v
  [cv2.VideoCapture.read()]                                       (sync — run_in_executor)
       |
       |  ret, frame = cap.read()
       |    ret: bool — False if frame could not be captured
       |    frame: numpy.ndarray (shape: height × width × 3, dtype uint8, BGR order)
       |           OpenCV always returns BGR — NOT RGB
       |
       |  IF ret = False:
       |    return []
       |    log.warn: "Webcam read() failed — frame dropped for this turn"
       |
       v
  [BGR → RGB conversion]                                          (sync, numpy)
       |
       |  frame_rgb = frame[:, :, ::-1]
       |    (reverses the channel axis: BGR → RGB; zero-copy view in numpy)
       |    This step is mandatory — PIL.Image.fromarray() expects RGB, not BGR.
       |    Omitting it causes a blue-channel swap that subtly distorts all colours;
       |    the Auditor invariant check must verify this conversion is present.
       |
       v
  [PIL.Image.fromarray(frame_rgb)]                                (sync — run_in_executor)
       |
       |  image = PIL.Image.fromarray(frame_rgb)
       |    mode: "RGB"  (derived from shape: 3 channels)
       |    width: frame.shape[1], height: frame.shape[0]
       |
       v
  [Resize to max_width / max_height]                              (sync, Pillow)
       |
       |  config keys: sjon.webcam.max_width (default 1280), sjon.webcam.max_height (default 720)
       |  if image.width > max_width OR image.height > max_height:
       |    image.thumbnail((max_width, max_height), PIL.Image.LANCZOS)
       |    (in-place; aspect-ratio preserving; never upscales)
       |  Typical webcam resolution: 640×480 (VGA), 1280×720 (HD), 1920×1080 (FHD)
       |  At 640×480: no resize needed (below default threshold)
       |  At 1280×720: exactly at threshold — no resize (thumbnail does not upscale)
       |  At 1920×1080: scaled to 1280×720 (1.5× reduction, aspect ratio 16:9 preserved)
       |
       v
  [Encode: JPEG (default) or PNG (opt-in)]                        (sync, Pillow)
       |
       |  config key: sjon.webcam.format — "jpeg" (default) | "png"
       |
       |  IF format = "jpeg":
       |    buffer = io.BytesIO()
       |    image.save(buffer, format="JPEG", quality=config.sjon.webcam.jpeg_quality)
       |    jpeg_quality config key: default 85 (range 1–95; Pillow convention)
       |    JPEG encoding is the default because webcam frames are photographic content —
       |    lossless PNG carries 3–5× the byte cost for negligible perceptual improvement.
       |    At 1280×720 JPEG quality=85: typically 80–200 KB (vs ~800–1200 KB PNG)
       |    This is the primary token-cost argument for JPEG as default.
       |    MIME type: "image/jpeg"
       |
       |  IF format = "png":
       |    buffer = io.BytesIO()
       |    image.save(buffer, format="PNG", compress_level=6)
       |    MIME type: "image/png"
       |
       |  encoded_bytes = buffer.getvalue()
       |
       v
  [base64 encode + data URL]                                      (sync)
       |
       |  b64_str = base64.b64encode(encoded_bytes).decode("ascii")
       |  mime = "image/jpeg" if format == "jpeg" else "image/png"
       |  data_url = f"data:{mime};base64,{b64_str}"
       |
       v
  [return [data_url]]
       |
       |  No disk write under any default configuration.
       |  The data URL exists only in memory and in the outbound HTTP request body.
```

**Session log entry for webcam capture:**
```json
{
  "event": "sjon_webcam_snapshot",
  "ts": "...",
  "device_index": 0,
  "frame_width": 1280,
  "frame_height": 720,
  "format": "jpeg",
  "jpeg_quality": 85,
  "encoded_bytes": 142800,
  "b64_chars": 190416,
  "encode_ms": 22,
  "saved_to_disk": false
}
```

**Config dependencies for the webcam capture path:**

| Config key | Default | Controls |
|---|---|---|
| `sjon.webcam.enabled` | `false` | Master toggle — operator must explicitly set `true` to activate webcam capture; default off is the stronger consent gate |
| `sjon.webcam.device_index` | `0` | OpenCV VideoCapture device index; 0 = first available webcam |
| `sjon.webcam.max_width` | `1280` | Max output width after resize; thumbnail() will not upscale |
| `sjon.webcam.max_height` | `720` | Max output height after resize; aspect ratio preserved |
| `sjon.webcam.format` | `"jpeg"` | Encoding format: `"jpeg"` (smaller, photographic) or `"png"` (lossless, larger) |
| `sjon.webcam.jpeg_quality` | `85` | JPEG quality (1–95); only used when format = "jpeg"; ignored for PNG |
| `sjon.webcam.attach_policy` | `"screen_only"` | Governs how webcam and screen frames are combined per turn — see §4.10.12 |

#### 4.10.12 Webcam/screen attach_policy decision tree (v0.5.2)

> The eye now has two sources. The question on every turn: which does the spirit receive?
> Four answers are defined. One locks the old behaviour; three open the new possibilities.

This decision tree operates in the CLI / Vébond per-turn dispatch layer — not inside
SjonOrchestrator. Sjón itself provides two independent methods: `snapshot()` (screen) and
`snapshot_webcam()` (webcam). The caller decides which to invoke and in what order based on
`sjon.webcam.attach_policy`. Sjón has no knowledge of the policy; the policy logic lives
entirely in the caller.

**Pre-conditions (unchanged from §4.10.1):**
Both capture paths are gated by `capability_vision_in = true`. If the agent does not support
vision, both paths are bypassed and `image_data_urls = []` regardless of policy.

```
  [user message arrives — pre-check passed: capability_vision_in = true]
       |
       v
  [read: sjon.webcam.attach_policy]
       |
       |
  +----|---------------------------------------- attach_policy = "screen_only" (DEFAULT) ---+
  |    |                                                                                    |
  |    v                                                                                    |
  |  [screen path only — identical to v0.5 / v0.5.1]                                       |
  |    sjon.screen.enabled gate applies as before                                           |
  |    snapshot() called if gate passes                                                     |
  |    webcam_enabled flag is IGNORED regardless of its value                               |
  |    image_data_urls = [screen_data_url]  (or [] on failure)                             |
  |                                                                                         |
  |  Why this is the default:                                                               |
  |    Backward compatibility — any operator who was running v0.5 / v0.5.1 without          |
  |    touching the webcam config gets the exact same behaviour after upgrading to v0.5.2.  |
  |    The webcam block being present in heretic.yaml (enabled: false by default) does      |
  |    not change the screen path. Only an explicit attach_policy change activates webcam.  |
  +----------------------------------------------------------------------------------------+
       |
  +----|---------------------------------------- attach_policy = "webcam_only" ---------------+
  |    |                                                                                      |
  |    v                                                                                      |
  |  [webcam path only — screen NOT captured this turn]                                      |
  |    snapshot_webcam() called (if sjon.webcam.enabled = true)                              |
  |    snapshot() is NOT called                                                               |
  |    image_data_urls = [webcam_data_url]  (or [] on webcam failure)                        |
  |                                                                                           |
  |  Use case: operator wants the spirit to see the user's face / room, not the screen.      |
  |  Example: a companion app where screen content is irrelevant but physical presence        |
  |           helps the spirit understand the user's current emotional state or environment.  |
  |  Cost: same as v0.5 screen path — one image per turn.                                    |
  +-------------------------------------------------------------------------------------------+
       |
  +----|---------------------------------------- attach_policy = "alongside" ----------------+
  |    |                                                                                     |
  |    v                                                                                     |
  |  [both captured — both attached in the same turn]                                       |
  |    snapshot_webcam() called first (if sjon.webcam.enabled = true AND screen.enabled)    |
  |    snapshot() called second                                                              |
  |    failures handled independently: each returns [] or [data_url] independently          |
  |                                                                                          |
  |  Attachment order in content array:                                                      |
  |    [                                                                                     |
  |      {"type": "text",      "text": "<user message>"},                                   |
  |      {"type": "image_url", "image_url": {"url": "<webcam_data_url>"}},   // webcam first|
  |      {"type": "image_url", "image_url": {"url": "<screen_data_url>"}}    // screen last |
  |    ]                                                                                     |
  |    Webcam comes first because it provides subject context (who is asking)               |
  |    before content context (what they are looking at).                                    |
  |                                                                                          |
  |  IF either capture fails:                                                                |
  |    the successful capture is still attached; partial result is acceptable                |
  |    no failure escalation if one source is unavailable                                    |
  |                                                                                          |
  |  Cost: two images per turn. Token cost roughly doubles versus single-image policies.     |
  |  Operator should verify their vision model's per-image token cost before enabling.       |
  |  Tailscale bandwidth: ~1–1.5 MB per turn (JPEG webcam ~150 KB + PNG screen ~800–1200 KB)|
  +-------------------------------------------------------------------------------------------+
       |
  +----|---------------------------------------- attach_policy = "alternate" ---------------+
  |    |                                                                                    |
  |    v                                                                                    |
  |  [alternates between webcam and screen on successive turns]                            |
  |    state tracked per CLI ceremony session: _sjon_alternate_turn_counter (int, starts 0)|
  |                                                                                         |
  |    IF _sjon_alternate_turn_counter is ODD:                                              |
  |      webcam capture this turn (snapshot_webcam())                                       |
  |      screen NOT captured                                                                |
  |      image_data_urls = [webcam_data_url]                                                |
  |                                                                                         |
  |    IF _sjon_alternate_turn_counter is EVEN:                                             |
  |      screen capture this turn (snapshot())                                              |
  |      webcam NOT captured                                                                |
  |      image_data_urls = [screen_data_url]                                                |
  |                                                                                         |
  |    _sjon_alternate_turn_counter incremented after each turn regardless of capture       |
  |    result (including [] on failure — the counter advances to keep the alternation in    |
  |    sync with the conversation rhythm, not with capture success).                        |
  |                                                                                         |
  |    State scope: per CLI ceremony session; resets to 0 at each ceremony start.          |
  |    Not persisted across ceremonies.                                                     |
  |                                                                                         |
  |  Use case: attention shift tracking — the spirit alternates between understanding what  |
  |            the user is seeing (screen) and how the user appears to be reacting (webcam).|
  |            At every other turn each source is refreshed, at half the token cost of      |
  |            "alongside" over the same conversation length.                               |
  |  Cost: one image per turn (same as single-image policies); the cost alternates between  |
  |        webcam and screen sources.                                                        |
  +-------------------------------------------------------------------------------------------+
```

**Summary table:**

| attach_policy | Screen captured? | Webcam captured? | Images / turn | Webcam order | Notes |
|---|---|---|---|---|---|
| `"screen_only"` (default) | Yes (per §4.10.1–4.10.9) | No (ignored) | 0 or 1 | N/A | Backward compatible with v0.5/v0.5.1 |
| `"webcam_only"` | No | Yes | 0 or 1 | N/A | Screen path completely bypassed |
| `"alongside"` | Yes | Yes | 0, 1, or 2 | Webcam first | Both attached; order: webcam then screen |
| `"alternate"` | Even turns | Odd turns | 0 or 1 | N/A | Counter in CLI session state |

**Session log annotation (alternate policy):**
```json
{
  "event": "sjon_attach_policy_dispatch",
  "policy": "alternate",
  "turn_counter": 7,
  "active_source": "webcam",
  "ts": "..."
}
```

#### 4.10.13 Webcam privacy stance (v0.5.2)

> The webcam sees the person, not the work. This distinction carries a heavier obligation.

**Why the default is stronger than screen:**

Screen capture reveals what is on the display — code, documents, browser tabs. These are the
user's output, already externalized into a machine interface. Webcam capture reveals what is in
the room — the user's face, posture, lighting, background, and physical presence. This is not
output; this is the person. The distinction demands a stronger default.

| Gate | Screen | Webcam |
|---|---|---|
| Master toggle default | `sjon.screen.enabled: true` | `sjon.webcam.enabled: false` |
| Consent model | Operator opts in by enabling screen capture | Operator must explicitly opt in AND choose a non-"screen_only" policy |
| Default attach_policy | already active when enabled | `"screen_only"` ignores webcam even if enabled |
| Result | Screen capture is active unless disabled | Webcam capture requires two deliberate acts: enable it AND change the policy |

The two-gate design means that an operator who adds the webcam block to heretic.yaml with
`enabled: true` but forgets to change `attach_policy` still sends no webcam frames. The policy
gate is a second, independent consent point.

**Privacy invariants (sealed at v0.5.2 — carry forward from screen invariants in §4.10):**

1. Webcam frames are NEVER written to disk under any default configuration. No session log
   entry contains frame bytes; only metadata (device, dimensions, encoding, byte count) is
   logged.
2. Webcam frames exist only in memory and in the outbound HTTP request body. They travel
   through the same Tailscale-encrypted Bifröst wire as screen frames. No separate exfiltration
   path exists.
3. A ring buffer for webcam is NOT implemented in v0.5.2 (on-demand only, same as screen in
   v0.5). Continuous/periodic webcam capture with a ring buffer is backlog item v0.5.x.
4. The VideoCapture object is held open for the ceremony lifetime (for performance) but its
   frames are never accumulated — each `read()` call produces one frame that is immediately
   encoded, base64-encoded, returned, and then goes out of scope. No frame is retained in
   the orchestrator after the data URL is returned.
5. At SLOKNA, `cap.release()` is called on the VideoCapture object. The camera is released
   regardless of how the ceremony ends (normal Slokna, crash, or timeout teardown).

**Operator communication note (for INTERFACE.md and operator docs):**

Any operator-facing documentation that explains webcam capture should include a clear statement
that the webcam captures physical presence — face, room, and environment. Operators deploying
HERETIC in a shared, professional, or regulated environment are responsible for ensuring that
consent is obtained from any person who may appear in webcam frames before enabling this feature.
HERETIC provides the privacy defaults; obtaining consent is an operator responsibility.

---

## 15. L3 Sjón — Internal Component Diagram (v0.5)

> **Added 2026-05-08 v0.5 (Védis Eikleið).** Drawn in the same style as §11 (Tunga) and §12
> (Hlust). Shows the internal structure of the `src/heretic/sjon/` module as it ships in v0.5:
> the five source files, their data flow, and sync/async annotations.
>
> **Aesthetic note:** Where §11 (Tunga) is the outgoing voice and §12 (Hlust) is the incoming
> voice, Sjón is the incoming sight. The three together map the body's perceptual surface:
> mouth (Tunga), ear (Hlust), eye (Sjón). The Sjón-glow blue accent (`#4080b0` / `#60a8e0`
> per AESTHETIC.md) distinguishes it from the Mál-green of the Rödd senses.

```
  ============================================================
  SJÓN MODULE — src/heretic/sjon/    (v0.5 First Sight)
  ============================================================

  ENTRY: sjon.py — SjonOrchestrator
  |
  |  Public method: async snapshot() -> list[str]
  |    called by CLI _async_light turn loop / Vébond send_message handler
  |    coordinates throttle, capture, encoding, and activity events
  |    async at its surface; dispatches sync work via run_in_executor
  |
  +-- reads: config_model.py — SjonConfig
  |     |
  |     |  SjonConfig
  |     |    screen: SjonScreenConfig
  |     |    webcam: SjonWebcamConfig  (declared but not implemented in v0.5)
  |     |
  |     |  SjonScreenConfig
  |     |    enabled: bool              default true
  |     |    width: int                 default 1280
  |     |    height: int                default 720
  |     |    crop: dict | None          default null (full screen)
  |     |    buffer_depth: int          default 5  (reserved for v0.5.x ring buffer)
  |     |    save_frames: bool          default false  (privacy invariant)
  |     |    min_interval_ms: int       default 1000   (throttle)
  |     |
  |     |  SjonWebcamConfig
  |     |    enabled: bool              default false  (declared; not implemented v0.5)
  |     |    device: str                default "default"
  |     |    interval_ms: int           default 10000
  |     |
  |     Read once at Kynding; passed into SjonOrchestrator at construction.
  |     Never re-read mid-ceremony (config is immutable for the lifecycle).
  |
  +-- raises: errors.py — SjonError hierarchy
  |     SjonError (base)
  |     |-- ScreenCaptureError       raised by MssBackend on capture failure
  |     |-- BackendUnavailableError  raised when best_available() returns NullBackend
  |     |-- FrameEncodingError       raised by FrameEncoder on Pillow exception
  |     |-- PermissionDeniedError    raised on macOS screen recording denial
  |     All caught by SjonOrchestrator.snapshot(); none propagate to caller.
  |     Orchestrator returns [] on any error; logs warning.
  |
  +-- calls: capture.py — ScreenCaptureBackend + MssBackend + NullBackend
  |     |
  |     |  ScreenCaptureBackend (ABC)
  |     |    available() -> bool
  |     |    capture(monitor: str) -> CaptureResult(bgra_bytes, width, height)
  |     |
  |     |  MssBackend (primary)
  |     |    available(): imports mss; returns True if import succeeds
  |     |    capture(): calls mss.mss().grab(monitor)
  |     |               returns BGRA bytes + dimensions
  |     |               SYNC — must be wrapped in run_in_executor by caller
  |     |               raises ScreenCaptureError on mss.exception.ScreenShotError
  |     |               raises PermissionDeniedError on macOS permission denial
  |     |
  |     |  NullBackend (fallback)
  |     |    available(): always False
  |     |    capture(): raises BackendUnavailableError
  |     |    used when mss import fails; orchestrator returns [] immediately
  |     |
  |     |  best_available() -> ScreenCaptureBackend
  |     |    factory function:
  |     |      try MssBackend — if available: return MssBackend()
  |     |      else: return NullBackend()
  |     |    called once at SjonOrchestrator.__init__
  |     |
  |     SYNC I/O — always call capture() inside run_in_executor.
  |
  +-- calls: encoder.py — FrameEncoder
        |
        |  FrameEncoder
        |    encode(bgra_bytes, width, height, max_width, max_height) -> str
        |      returns data URL ("data:image/png;base64,<...>")
        |      SYNC — must be wrapped in run_in_executor by caller
        |
        |  Internal steps (all sync, all Pillow):
        |    1. PIL.Image.frombytes("RGBA", (w, h), bgra_bytes).convert("RGB")
        |         BGRA byte order from mss → "RGBA" frombytes handles channel order
        |         convert("RGB") strips alpha channel (PNG can carry it, but RGB
        |         is sufficient and smaller)
        |    2. if w > max_width or h > max_height:
        |         image.thumbnail((max_width, max_height), PIL.Image.LANCZOS)
        |         (in-place; aspect-ratio preserving; never upscales)
        |    3. buffer = io.BytesIO()
        |         image.save(buffer, format="PNG", compress_level=6)
        |         png_bytes = buffer.getvalue()
        |    4. b64_str = base64.b64encode(png_bytes).decode("ascii")
        |    5. return f"data:image/png;base64,{b64_str}"
        |
        |    FrameEncoder.oversized(png_bytes, limit_mb=4.0) -> bool
        |      helper: returns True if len(png_bytes) > limit_mb * 1024 * 1024
        |      called by SjonOrchestrator after encode to check F-4 case
        |
        |  Raises FrameEncodingError on any Pillow exception.
        |  Does not interact with the event bus or config — pure transformation.

  ============================================================
  SJÓN DATA FLOW — inside sjon.py
  ============================================================

  [SjonOrchestrator.__init__]
       |
       |  config = SjonConfig  (injected from grunnr/config.py)
       |  backend = best_available()  -> MssBackend or NullBackend
       |  encoder = FrameEncoder()
       |  last_capture_ts: float = 0.0  (throttle state)
       |

  [SjonOrchestrator.snapshot()]  (async)
       |
       |  [throttle check]
       |    if (now() - last_capture_ts) < config.screen.min_interval_ms / 1000:
       |      return []  (F-5 path)
       |
       |  [capability check already done by caller — not repeated here]
       |
       |  emit sjon.activity(state="capturing")           --> EventBus
       |
       |  [capture — sync wrapped]
       |    result = await loop.run_in_executor(None, backend.capture, "primary")
       |    raises: ScreenCaptureError, PermissionDeniedError, BackendUnavailableError
       |    all caught; on error: emit sjon.activity(state="failed"); return []
       |
       |  emit sjon.activity(state="encoding")            --> EventBus
       |
       |  [encode — sync wrapped]
       |    data_url = await loop.run_in_executor(
       |                  None, encoder.encode,
       |                  result.bgra_bytes, result.width, result.height,
       |                  config.screen.width, config.screen.height)
       |    raises: FrameEncodingError
       |    caught; on error: emit sjon.activity(state="failed"); return []
       |
       |  [F-4 oversized check]
       |    png_bytes derived from data_url  (strip data URL prefix, b64decode, len)
       |    if oversized:
       |      retry at 50% scale
       |      if still oversized: log.warn; return []
       |
       |  last_capture_ts = now()
       |
       |  emit sjon.activity(state="idle")                --> EventBus
       |
       |  return [data_url]
       |

  ============================================================
  SYNC vs ASYNC ANNOTATION
  ============================================================

  Component            Sync / Async      Notes
  ---------            -----------       -----
  SjonOrchestrator     async surface     snapshot() is async; uses await
  MssBackend.capture   sync (mss)        wrapped in run_in_executor; does not block loop
  FrameEncoder.encode  sync (Pillow)     wrapped in run_in_executor; does not block loop
  EventBus.publish     sync              fire-and-forget; no await needed
  SjonConfig           sync / init-time  read once; no I/O during capture
  NullBackend          sync              raises immediately; no I/O

  ============================================================
  INVARIANTS
  ============================================================
  - SjonOrchestrator never raises to its caller
    All exceptions are caught internally; return value is always list[str]
    (empty on any error path; [data_url] on success)
  - Frames never touch the filesystem by default
    save_frames: false is the invariant; disk write only on explicit opt-in
    Even on opt-in: writes to session-scoped temp dir only; deleted at Slokna
  - SjonOrchestrator has no knowledge of Bifröst or the agent protocol
    It only knows about capture, encode, and activity events
    The data_url it returns is opaque to it; the caller (CLI / Vébond) handles injection
  - config_model.py has no runtime dependencies
    Import order: config_model → errors → capture → encoder → sjon
    No circular imports
  - MssBackend and FrameEncoder are independently testable
    Both are pure-function wrappers with no global state
    Unit tests use mocked mss and mocked PIL to cover all paths without hardware
```

```
  ============================================================
  SJÓN MODULE — v0.5.1 EXTENSION: continuous pump + ring buffer
  ============================================================

  sjon/
    (all v0.5 files unchanged in structure; new behavior added to sjon.py)

    sjon.py
      ┌──────────────────────────────────────────────────────────┐
      │ SjonOrchestrator                                         │
      │                                                          │
      │  on-demand path (v0.5 — unchanged):                     │
      │    async snapshot() ─────────────────────────> [data_url]│
      │      throttle → capture → encode → return [data_url]    │
      │                                                          │
      │  continuous path (v0.5.1 — new):                        │
      │    start_continuous_capture()                            │
      │     └─> asyncio.Task (_continuous_task)                  │
      │           └─> capture + encode tick (loop)              │
      │                 └─> deque(maxlen=buffer_depth) ─────────>│
      │                       _frame_buffer                      │
      │                         (ring buffer, memory-only)       │
      │                                                          │
      │  recent_frames(n: int | None = None) -> list[str]        │
      │    reads _frame_buffer (snapshot copy)                   │
      │    returns last N data URLs (None = all)                 │
      │    used by attach_policy logic in CLI / Vébond per-turn  │
      │                                                          │
      │  stop_continuous_capture()                               │
      │    cancels _continuous_task                              │
      │    awaits cancellation                                    │
      │    _continuous_task = None                               │
      │                                                          │
      │  Slokna / close():                                       │
      │    stop_continuous_capture() called                      │
      │    _frame_buffer.clear()  [privacy invariant]            │
      │                                                          │
      │  monitor index resolution (per §4.10.10):               │
      │    on-demand: config 0 → mss 1 (primary)                │
      │    continuous: config 0 → mss 0 (all-monitors composite) │
      │    either mode: config N>=1 → mss N (specific display)  │
      └──────────────────────────────────────────────────────────┘

    capture.py (v0.5.1 additions):
      MssBackend
        list_monitors() -> list[dict]
          returns mss monitor list (mss.mss().monitors)
          index 0 = composite descriptor; index 1..N = individual screens
          for operator tooling / future UI config support

        capture(monitor_index: int) -> CaptureResult
          extended from v0.5 (was: capture(monitor: str))
          now accepts an integer mss index directly
          caller resolves config index to mss index via _resolve_mss_monitor()
          before passing to capture()

  ============================================================
  NEW SYNC vs ASYNC ANNOTATIONS (v0.5.1)
  ============================================================

  Component                       Sync / Async   Notes
  ---------                       -----------    -----
  start_continuous_capture()      async          creates asyncio.Task; awaitable
  _continuous_task (the loop)     async          runs as background Task; cancelled on Slokna
  stop_continuous_capture()       async          cancels task; awaits CancelledError
  recent_frames()                 sync           reads deque snapshot; no I/O; no await
  _frame_buffer (deque)           n/a            stdlib deque; asyncio-safe for single loop
  MssBackend.list_monitors()      sync           wraps mss property; call in run_in_executor
                                                 if called from async context

  ============================================================
  NEW INVARIANTS (v0.5.1)
  ============================================================
  - The continuous capture loop NEVER queues frames
    If the previous tick's capture is still running, the new tick is skipped entirely.
    One late frame is always preferable to a growing backlog under load.
  - recent_frames() ALWAYS returns a copy (list snapshot of the deque)
    Callers may not hold a reference to the internal deque.
    This prevents races if a tick fires while a turn is reading the buffer.
  - The ring buffer is CLEARED on every Slokna
    Privacy invariant carries from v0.5: frames exist only during the live ceremony.
    Even if stop_continuous_capture() is called before close(), clear() is always called.
  - monitor_index=0 means PRIMARY in on-demand mode and COMPOSITE in continuous mode
    This is a named, documented, intentional asymmetry — not a bug.
    See §4.10.10 for the full rationale and the _resolve_mss_monitor contract.
```

```
  ============================================================
  SJÓN MODULE — v0.5.2 EXTENSION: webcam capture backend
  ============================================================

  > Added 2026-05-08 v0.5.2 (Védis Eikleið). The eye gains a second source alongside MssBackend.
  > WebcamCaptureBackend is a parallel capture path, not a replacement. Both backends are
  > independently instantiated; neither knows the other exists. The SjonOrchestrator gains a
  > new method snapshot_webcam() that mirrors snapshot() but calls the webcam backend.
  > The attach_policy logic lives in the CLI / Vébond caller — Sjón is not responsible for it.

  sjon/
    (v0.5 and v0.5.1 files unchanged; new file: webcam.py)

    webcam.py                     NEW in v0.5.2
    |
    ├── WebcamCaptureBackend (ABC)
    │     available() -> bool
    │     open(device_index: int) -> None    (lazy; called on first snapshot_webcam())
    │     read_frame() -> WebcamFrame        (WebcamFrame: bgr_array, width, height)
    │     close() -> None                    (called at SLOKNA; releases cv2.VideoCapture)
    │
    ├── OpenCvBackend  (primary — requires opencv-python>=4.8)
    │     available():
    │       try: import cv2; return True
    │       except ImportError: return False
    │     open(device_index: int):
    │       self._cap = cv2.VideoCapture(device_index)
    │       if not self._cap.isOpened():
    │         raise WebcamBackendUnavailableError(f"device {device_index} not found")
    │     read_frame() -> WebcamFrame:
    │       ret, bgr_array = self._cap.read()
    │       if not ret: raise WebcamCaptureError("VideoCapture.read() returned False")
    │       return WebcamFrame(bgr_array=bgr_array,
    │                          width=bgr_array.shape[1],
    │                          height=bgr_array.shape[0])
    │     close():
    │       if self._cap is not None:
    │         self._cap.release()
    │         self._cap = None
    │
    │     SYNC I/O — all methods are synchronous.
    │     Caller (SjonOrchestrator.snapshot_webcam) must wrap in run_in_executor.
    │
    ├── NullWebcamBackend  (fallback — no-op when opencv-python not installed)
    │     available() -> False
    │     open() -> raises WebcamBackendUnavailableError immediately
    │     read_frame() -> raises WebcamBackendUnavailableError
    │     close() -> no-op
    │
    └── best_available_webcam() -> WebcamCaptureBackend
          factory function:
            try OpenCvBackend — if available: return OpenCvBackend()
            else: return NullWebcamBackend()
          called once at SjonOrchestrator.__init__
          (parallel to best_available() for the screen backend)

    errors.py  (v0.5.2 additions)
    |
    |  WebcamCaptureError          raised by OpenCvBackend.read_frame() on read failure
    |  WebcamBackendUnavailableError  raised by NullWebcamBackend or on device not found
    |    Both extend SjonError (existing base); both caught by SjonOrchestrator.snapshot_webcam()


    sjon.py  (v0.5.2 additions to SjonOrchestrator)
    |
    ├── __init__ additions:
    │     self._webcam_backend: WebcamCaptureBackend = best_available_webcam()
    │     self._webcam_opened: bool = False
    │     (VideoCapture opened lazily on first snapshot_webcam() call)
    │
    ├── async snapshot_webcam() -> list[str]
    │     Mirrors snapshot() in structure; calls the webcam backend.
    │     Steps:
    │       1. IF NOT config.webcam.enabled: return []  (fast path; no log; expected default)
    │       2. IF NOT self._webcam_opened:
    │            await loop.run_in_executor(None,
    │                    self._webcam_backend.open, config.webcam.device_index)
    │            on WebcamBackendUnavailableError: log.warn; return []
    │            self._webcam_opened = True
    │       3. emit sjon.activity(state="capturing_webcam")  --> EventBus
    │       4. frame = await loop.run_in_executor(None, self._webcam_backend.read_frame)
    │            on WebcamCaptureError: log.warn; emit sjon.activity(state="failed"); return []
    │       5. emit sjon.activity(state="encoding_webcam")
    │       6. data_url = await loop.run_in_executor(
    │                       None, _encode_webcam_frame,
    │                       frame, config.webcam.max_width, config.webcam.max_height,
    │                       config.webcam.format, config.webcam.jpeg_quality)
    │            on FrameEncodingError: log.warn; emit sjon.activity(state="failed"); return []
    │       7. emit sjon.activity(state="idle")
    │       8. return [data_url]
    │
    └── close() additions (SLOKNA):
          if self._webcam_opened:
            self._webcam_backend.close()
            self._webcam_opened = False
          (webcam is always released at SLOKNA; privacy invariant sealed)

    Internal helper (can live in webcam.py or encoder.py):

    _encode_webcam_frame(frame: WebcamFrame, max_w, max_h, fmt, quality) -> str
      Steps:
        1. bgr_to_rgb: frame.bgr_array[:, :, ::-1]  (numpy channel reverse; zero-copy)
        2. image = PIL.Image.fromarray(rgb_array)
        3. if image.width > max_w or image.height > max_h:
             image.thumbnail((max_w, max_h), PIL.Image.LANCZOS)
        4. buffer = io.BytesIO()
           if fmt == "jpeg":
             image.save(buffer, format="JPEG", quality=quality)
             mime = "image/jpeg"
           else:
             image.save(buffer, format="PNG", compress_level=6)
             mime = "image/png"
        5. b64_str = base64.b64encode(buffer.getvalue()).decode("ascii")
        6. return f"data:{mime};base64,{b64_str}"
      Raises FrameEncodingError on any Pillow exception.
      SYNC — caller wraps in run_in_executor.


  ============================================================
  PARALLEL BACKEND TOPOLOGY (v0.5.2)
  ============================================================

  SCREEN SOURCE                          WEBCAM SOURCE
  ============                           =============

  capture.py                             webcam.py
  ScreenCaptureBackend (ABC)             WebcamCaptureBackend (ABC)
    |                                      |
    ├── MssBackend (primary)               ├── OpenCvBackend (primary)
    |     mss.mss().grab()                 |     cv2.VideoCapture.read()
    |     returns BGRA bytes               |     returns BGR ndarray
    |                                      |
    └── NullBackend (fallback)             └── NullWebcamBackend (fallback)
                                                 available() = False

  Both fed into SjonOrchestrator:

  SjonOrchestrator
  |  _screen_backend = best_available()         --> MssBackend or NullBackend
  |  _webcam_backend = best_available_webcam()  --> OpenCvBackend or NullWebcamBackend
  |
  |  async snapshot()         --> screen capture pipeline  (§4.10.2)
  |  async snapshot_webcam()  --> webcam capture pipeline  (§4.10.11)
  |
  |  Attach policy dispatch lives in CLI / Vébond, NOT in SjonOrchestrator.
  |  SjonOrchestrator provides primitives; the caller decides the policy.

  EventBus activity states for webcam (new in v0.5.2):
    sjon.activity(state="capturing_webcam")   -- cv2.read() in flight
    sjon.activity(state="encoding_webcam")    -- PIL encode + base64 in flight
    (existing states "idle" and "failed" reused for webcam path; no new states added)


  ============================================================
  SYNC vs ASYNC ANNOTATIONS (v0.5.2 additions)
  ============================================================

  Component                       Sync / Async   Notes
  ---------                       -----------    -----
  OpenCvBackend.open()            sync (cv2)     wrapped in run_in_executor by snapshot_webcam
  OpenCvBackend.read_frame()      sync (cv2)     wrapped in run_in_executor by snapshot_webcam
  OpenCvBackend.close()           sync (cv2)     called at SLOKNA from async close(); no executor
                                                 needed (release() is fast and non-blocking)
  _encode_webcam_frame()          sync (Pillow)  wrapped in run_in_executor by snapshot_webcam
  NullWebcamBackend.*             sync           raises immediately; no I/O


  ============================================================
  NEW INVARIANTS (v0.5.2)
  ============================================================
  - WebcamCaptureBackend has no knowledge of the screen backend or attach policy
    It is a pure capture primitive.
  - SjonOrchestrator has no knowledge of the attach policy
    attach_policy logic belongs to CLI / Vébond caller.
  - VideoCapture is held open for the ceremony lifetime after first use
    This avoids repeated open/close latency per frame. The device is reserved
    for HERETIC while the ceremony is active.
  - VideoCapture is ALWAYS released at SLOKNA (via close())
    The camera's indicator light goes off when the ceremony ends.
  - Webcam frames are never written to disk (privacy invariant from §4.10.13)
    No frame bytes appear in session logs; only metadata.
  - attach_policy = "screen_only" ignores sjon.webcam.enabled
    An operator who sets enabled: true but does not change the policy gets no webcam frames.
    This two-gate design is intentional — see §4.10.13.
  - ring buffer for webcam is NOT implemented in v0.5.2
    snapshot_webcam() is on-demand only; no continuous webcam task.
    Periodic webcam with ring buffer is backlog item v0.5.x.
```

---

#### 4.10.14 Privacy mask application (Blæja — v0.5.3)

> **Added 2026-05-09 v0.5.3 (Védis Eikleið).** *Blæja* — the veil. The body
> learns to look without recording everything it sees. A configurable mask
> layer applies to captured frames *before* every leak path: encode, save,
> transport. The unmasked frame never reaches disk; the unmasked frame
> never reaches the agent.

```
  BLÆJA — PRIVACY MASK APPLICATION

  Position in the pipeline:
    raw bytes from MssBackend / WebcamBackend
        │
        ▼
    PIL.Image decode  (Image.frombytes)
        │
        ▼  ╔═══════════════════════════════════════════════════════╗
            ║   apply_privacy_masks(image, config.privacy_masks)    ║
            ║   ← v0.5.3 — INSERTED HERE                            ║
            ║   For each PrivacyMaskRegion:                         ║
            ║     1. Clamp (x, y, w, h) to image bounds             ║
            ║     2. If clamped area == 0:  log once, skip          ║
            ║     3. Crop region from image                         ║
            ║     4. Apply mode (blur / solid / pixelate)           ║
            ║     5. Paste masked region back at (x, y)             ║
            ╚═══════════════════════════════════════════════════════╝
        │
        ▼
    resize_to_bounds(image, max_w, max_h)   (downstream of mask)
        │
        ▼
    PNG / JPEG encode                        (downstream of mask)
        │
        ▼
    base64 data URL → agent / disk-if-save_frames

  Key property: every leak path is downstream of the mask step. There is
  no codepath in which an unmasked frame reaches encode, save, or the
  ring buffer.

  Coordinate space:
    - All region coords (x, y, w, h) are in SOURCE PIXEL SPACE — i.e., the
      monitor or webcam's native resolution before any resize.
    - This keeps operator authoring stable: if max_width changes from 1280
      to 1920 in heretic.yaml, the operator's mask coordinates remain valid.
    - The clamp is to image.size at decode time (which equals source
      resolution before resize).

  Modes (per region):

    BLUR     — Gaussian blur of the cropped region.
               Default radius: max(8, min(w, h) // 8). Manual override via
               PrivacyMaskRegion.blur_radius.
               Pillow primitive: image.filter(ImageFilter.GaussianBlur(r)).
               Use when: agent should know "something is there" but cannot read it.

    SOLID    — Region replaced with a uniform colour.
               Default: (0, 0, 0) black. Override via PrivacyMaskRegion.solid_color.
               Pillow primitive: ImageDraw.Draw(image).rectangle(..., fill=color).
               Use when: even the region's silhouette must not leak.

    PIXELATE — Region downsampled then upsampled with NEAREST resampling.
               Factor: max(8, min(w, h) // 12). Override via PrivacyMaskRegion.pixelate_factor.
               Pillow primitive: img.resize((w//f, h//f), NEAREST).resize((w, h), NEAREST).
               Use when: gross composition is OK; fine detail must not leak.

  Region clamping:
    Out-of-bounds regions are clamped to image bounds silently. A region
    wholly off-frame becomes a no-op. The first time a clamp or no-op
    happens for a given encoder instance, a debug-level log records the
    fact. Subsequent occurrences are silent (the operator's heretic.yaml
    is presumed intentional).

  Empty list:
    privacy_masks=[] (the default for both SjonScreenConfig and
    SjonWebcamConfig) returns the image untouched — early return inside
    apply_privacy_masks before any per-region work. Zero overhead when
    feature is unused.

  Per-source independence:
    SjonScreenConfig.privacy_masks and SjonWebcamConfig.privacy_masks
    are independent lists. Screen and webcam have different privacy
    concerns (a window in the corner vs a roommate in the background),
    and the operator may want different region sets for each.
```

```
  BLÆJA CONFIG (heretic.yaml — under sjon block)

    sjon:
      screen:
        # ... (existing fields unchanged)
        privacy_masks:
          - x: 0
            y: 0
            w: 320
            h: 200
            mode: blur
            # blur_radius optional; defaults to max(8, min(w,h)//8)
          - x: 1600
            y: 100
            w: 200
            h: 80
            mode: solid
            solid_color: [0, 0, 0]   # default; can be omitted
          - x: 800
            y: 600
            w: 400
            h: 300
            mode: pixelate
            # pixelate_factor optional; defaults to max(8, min(w,h)//12)
      webcam:
        # ... (existing fields unchanged)
        privacy_masks:
          - x: 0
            y: 0
            w: 1280
            h: 200
            mode: blur     # blur top strip — covers a roommate behind the operator
```

```
  BLÆJA FAILURE MODES

  F-Blæja-1 — region wholly off-frame
    Cause: operator defines x=2000, y=2000, w=100, h=100 on a 1920×1080 monitor.
    Behaviour: clamping yields zero area; region is a no-op.
    Logging: debug-level message logged once per encoder lifetime.
    No exception; ceremony continues.

  F-Blæja-2 — region partially off-frame
    Cause: x=1800, w=400 on a 1920-wide monitor — extends 280 pixels past the right edge.
    Behaviour: w clamped to 120 (1920 - 1800). Visible part of the region is masked correctly.
    Logging: debug-level message logged once per encoder lifetime.
    No exception; ceremony continues.

  F-Blæja-3 — invalid mode at config load
    Cause: operator types `mode: blue` in heretic.yaml.
    Behaviour: PrivacyMaskRegion.__post_init__ raises ValueError.
    HereticConfig load fails fast at Kynding. Operator sees a clear error
    naming the bad value and listing valid modes.

  F-Blæja-4 — zero-width or zero-height region at config load
    Cause: operator types w=0 or h=0.
    Behaviour: PrivacyMaskRegion.__post_init__ raises ValueError.
    HereticConfig load fails fast at Kynding.

  F-Blæja-5 — Pillow filter raises during apply
    Cause: extreme blur radius on a tiny region, or other Pillow edge case.
    Behaviour: apply_privacy_masks catches the exception, logs at warning
    level, and falls back to SOLID-mask the region (fail-safe: any failure
    of the mask step still results in the region being veiled, never in
    the unmasked content reaching downstream).
    Ceremony continues.
```

> **Privacy invariants added by v0.5.3:**
> - **P-1:** Unmasked frame bytes never reach disk if any privacy mask is configured.
>   The mask runs before every save/transport path.
> - **P-2:** Unmasked frame bytes never reach the agent. The mask runs before encoding.
> - **P-3:** `privacy_masks` defaults to `[]` (empty) — feature is opt-in.
> - **P-4:** Mask coordinates in source pixel space; clamping is silent except for a
>   one-time debug log per encoder lifetime.
> - **P-5:** Zero-area regions (`w == 0` or `h == 0`) are rejected at config-construction
>   with `ValueError`.
> - **P-6:** Existing privacy invariants preserved: `save_frames` defaults False,
>   webcam `enabled` defaults False, in-memory ring buffer only.

---

#### 4.10.14.1 Margblæja — non-rectangular mask shapes (v0.5.4)

> **Added 2026-05-09 v0.5.4 (Védis Eikleið).** *Margblæja* — the veil of many
> forms. Extends v0.5.3 with two new shape types (circle, polygon) under a
> `PrivacyMaskShape` Protocol. The disposition is unchanged; the operator's
> vocabulary for declaring it has expanded.

```
  ONE PIPELINE — THREE SHAPES (rectangle, circle, polygon)

  apply_privacy_masks(image, masks):
      for shape in masks:                          # Protocol-typed iteration
          bx, by, bw, bh = shape.bounding_box()
          clamp (bx, by, bw, bh) to image bounds
          if w_eff <= 0 or h_eff <= 0:
              log clamp once; skip

          crop_original = image.crop(...)           # bounding-box crop
          modified      = apply_mode(crop_original, shape)
                                                    # blur / solid / pixelate
                                                    # mode is orthogonal to shape

          alpha = shape.alpha_mask(w_eff, h_eff)    # "L" mode 0..255
                                                    # in-shape = 255, out = 0
          composited = Image.composite(modified, crop_original, alpha)
                                                    # pixel-exact:
                                                    #   alpha[p]=255 → modified
                                                    #   alpha[p]=  0 → original

          image.paste(composited, (x_eff, y_eff))   # paste-back

  Shape contributions:
    Rectangle  bounding_box = (x, y, w, h)              ; alpha = full white
    Circle     bounding_box = (cx-r, cy-r, 2r, 2r)      ; alpha = filled disc
    Polygon    bounding_box = (min_x..max_x bbox)       ; alpha = filled poly
```

The structural property: **mode and shape are orthogonal**. The composite
math is uniform across all three shapes; only the alpha mask differs. A
fourth shape (e.g. v0.5.5 Bezier) would only need to provide a `bounding_box`
and an `alpha_mask` — no new pipeline branch.

```
  PROTOCOL CONTRACT — PrivacyMaskShape

  bounding_box() -> (x, y, w, h)
      Returns the source-pixel bounds of the smallest axis-aligned rectangle
      containing the entire shape. Coordinates are pre-clamp; the apply
      step clamps them to image bounds.

  alpha_mask(w, h) -> PIL.Image
      Returns an "L" mode image of size (w, h). In-shape pixels = 255;
      out-of-shape pixels = 0. The image's coordinate system is the
      bounding-box-relative — i.e., (0, 0) of the alpha mask corresponds
      to (x, y) of the bounding box on the source image.
      For the rectangle case, alpha_mask is a fully-opaque white image
      (the entire bounding box equals the shape).

  Shared field surface (all three shapes):
      mode             : "blur" | "solid" | "pixelate"
      blur_radius      : Optional[int >= 1]    (auto if None)
      solid_color      : tuple[int, int, int]  (default black)
      pixelate_factor  : Optional[int >= 2]    (auto if None)
```

```
  CIRCLE                                 POLYGON
  ─────────                              ─────────
  fields:                                fields:
    cx, cy     : non-neg int               points : list[(int, int)]
    radius     : >= 1                              len >= 3, all coords >= 0

  bounding_box():                        bounding_box():
    return (cx - radius,                   xs = [p[0] for p in points]
            cy - radius,                   ys = [p[1] for p in points]
            2 * radius,                    return (min(xs), min(ys),
            2 * radius)                            max(xs) - min(xs) + 1,
                                                   max(ys) - min(ys) + 1)
  alpha_mask(w, h):                      alpha_mask(w, h):
    mask = Image.new("L", (w, h), 0)       mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)            draw = ImageDraw.Draw(mask)
    draw.ellipse(                          # translate points into bbox-local
      (0, 0, w-1, h-1),                    local_pts = [(p[0]-min_x,
      fill=255,                                          p[1]-min_y)
    )                                                    for p in points]
    return mask                            draw.polygon(local_pts, fill=255)
                                           return mask
```

```
  MARGBLÆJA FAILURE MODES (additions to v0.5.3 F-Blæja-1..F-Blæja-5)

  F-Blæja-6 — circle wholly off-frame
    Cause: cx + radius < 0 or cx - radius > image_width (etc.).
    Behaviour: bounding box clamps to zero area; region is a no-op.
    Same one-time debug log as v0.5.3.
    No exception; ceremony continues.

  F-Blæja-7 — polygon wholly off-frame
    Cause: every vertex outside image bounds AND the polygon's bbox does
    not overlap the image.
    Behaviour: bounding box clamps to zero area; region is a no-op.
    Same one-time debug log.

  F-Blæja-8 — degenerate polygon (co-linear or coincident vertices)
    Cause: operator types points like [(0,0), (10,0), (20,0)] (all colinear)
    or [(50,50), (50,50), (50,50)] (all coincident).
    Behaviour: Pillow's polygon rasteriser draws what it can — a 1-pixel-wide
    line for collinear points, a single pixel for coincident ones. The mask
    covers exactly that, and the rest of the image is unchanged.
    apply does not raise; ceremony continues.
    Operator can fix by adjusting vertices; no fatal error.

  F-Blæja-9 — invalid circle radius at config load
    Cause: PrivacyMaskCircle(radius=0) or radius=-3.
    Behaviour: __post_init__ raises ValueError. HereticConfig load fails
    fast at Kynding.

  F-Blæja-10 — polygon with < 3 points at config load
    Cause: PrivacyMaskPolygon(points=[(0,0), (10,10)]).
    Behaviour: __post_init__ raises ValueError. HereticConfig load fails
    fast.

  F-Blæja-11 — polygon point with non-int coordinate at config load
    Cause: PrivacyMaskPolygon(points=[(0, 0), (10, "10"), (20, 20)]).
    Behaviour: __post_init__ raises ValueError. HereticConfig load fails
    fast.
```

> **Privacy invariants added by v0.5.4 (alongside the v0.5.3 P-1..P-6 inheritance):**
> - **P-7:** The alpha-mask composite step preserves shape boundaries pixel-exactly.
>   A pixel inside the bounding box but outside the shape must be unchanged after apply.
>   A pixel inside the shape must equal the modified-crop pixel.
> - **P-8:** A degenerate polygon (co-linear or coincident vertices) is a valid
>   construction. Pillow rasterises what it can — a thin line for collinear
>   points, a single pixel for coincident ones. apply does not raise; the
>   mask covers Pillow's output exactly; the rest of the image is unchanged.
> - **P-9:** A circle / polygon whose bounding box is wholly off-frame is a no-op
>   (matches the F-Blæja-1 rectangle case).

```
  MARGBLÆJA CONFIG (heretic.yaml example with all three shape kinds)

    sjon:
      screen:
        privacy_masks:
          - x: 0                  # rectangle (v0.5.3, unchanged)
            y: 0
            w: 320
            h: 200
            mode: blur
          - cx: 1700              # circle (v0.5.4 NEW)
            cy: 200
            radius: 80
            mode: solid
            solid_color: [0, 0, 0]
          - points:               # polygon (v0.5.4 NEW)
              - [800, 600]
              - [1000, 580]
              - [1100, 700]
              - [950, 800]
              - [820, 750]
            mode: pixelate
            pixelate_factor: 12

  Note: dispatching by YAML schema is the operator's loader concern; the
  Python types (PrivacyMaskRegion, PrivacyMaskCircle, PrivacyMaskPolygon)
  are independent dataclasses. The YAML loader code identifies the shape
  by which fields are present (presence of `cx`/`radius` → circle; presence
  of `points` → polygon; otherwise rectangle).
```

---

#### 4.10.14.2 Mjúkblæja — soft-curved mask shapes (v0.5.5)

> **Added 2026-05-09 v0.5.5 (Védis Eikleið).** *Mjúkblæja* — the soft veil.
> Two new shapes both built on Pillow's curve primitives. Five shapes total
> in the vocabulary. The unified pipeline does not branch.

```
  ROUNDED RECTANGLE                   ELLIPSE
  ──────────────────                  ───────
  fields:                             fields:
    x, y      : non-neg int             cx, cy   : non-neg int
    w, h      : >= 1                    rx, ry   : >= 1 (separate radii)
    corner_radius : >= 0

  bounding_box():                     bounding_box():
    return (x, y, w, h)                 return (cx - rx,
    (curves are inside the bbox)                cy - ry,
                                                2 * rx,
                                                2 * ry)

  apply-time corner clamp:            (no apply-time clamp needed)
    eff_radius = min(corner_radius,
                     min(w, h) // 2)
    (operator never sees an error;
     the rendered shape is the
     largest valid rounded rect)

  alpha_mask(w, h):                   alpha_mask(w, h):
    mask = Image.new("L", (w, h), 0)    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)         draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(             draw.ellipse(
      (0, 0, w-1, h-1),                   (0, 0, w-1, h-1),
      radius=eff_radius,                  fill=255,
      fill=255,                         )
    )                                   return mask
    return mask

  Pillow primitives used:
    ImageDraw.rounded_rectangle()  — since Pillow 8.2.0 (we pin >=10)
    ImageDraw.ellipse()            — since early Pillow versions
```

```
  THE FIVE-SHAPE VOCABULARY (post-v0.5.5)

  | Shape                        | Bounding box                         | Alpha mask primitive            |
  | ---------------------------- | ------------------------------------ | ------------------------------- |
  | PrivacyMaskRegion            | (x, y, w, h)                         | full-white (composite=identity) |
  | PrivacyMaskCircle            | (cx-r, cy-r, 2r, 2r)                 | ellipse on equal-side bbox      |
  | PrivacyMaskPolygon           | min/max of vertex coords + 1         | polygon with bbox-local pts     |
  | PrivacyMaskRoundedRectangle  | (x, y, w, h)                         | rounded_rectangle               |
  | PrivacyMaskEllipse           | (cx-rx, cy-ry, 2rx, 2ry)             | ellipse                         |

  Five shapes → one pipeline → identical privacy invariants. The apply
  pipeline (clamp → crop → mode → alpha-composite → paste) is unchanged
  from v0.5.4. Each new shape contributed exactly two methods.
```

```
  MJÚKBLÆJA FAILURE MODES (additions to v0.5.4 F-Blæja-6..F-Blæja-11)

  F-Blæja-12 — invalid corner_radius at config load
    Cause: PrivacyMaskRoundedRectangle(corner_radius=-1).
    Behaviour: __post_init__ raises ValueError.
    HereticConfig load fails fast at Kynding.

  F-Blæja-13 — corner_radius larger than half the shorter side
    Cause: operator sets corner_radius=200 on a 50x50 rounded rect.
    Behaviour: NOT an error. apply-time clamp reduces eff_radius to
    min(corner_radius, min(w,h)//2). The operator's intent is honoured
    as much as Pillow can honour it. Clamp is silent (no debug log
    distinct from the v0.5.3 clamp_logged throttle — corner_radius
    clamp is treated as part of the same family of operator-intent-
    versus-image-reality reconciliations).

  F-Blæja-14 — invalid ellipse rx or ry at config load
    Cause: PrivacyMaskEllipse(rx=0) or ry=-3.
    Behaviour: __post_init__ raises ValueError. Same shape as the
    Circle radius-validation rule, generalised to two axes.

  F-Blæja-15 — ellipse with rx == ry (degenerate but valid)
    Cause: operator types PrivacyMaskEllipse(cx=10, cy=10, rx=5, ry=5).
    Behaviour: VALID. The ellipse renders as a circle. This is an
    intentionally redundant case — the operator's choice to use Ellipse
    over Circle is honoured even when the radii happen to match. No
    log; no warning; ceremony continues normally.
```

> **No new privacy invariants in v0.5.5.** The shape extension does not
> change the structural property that the mask runs upstream of every
> leak path. P-1 through P-9 from v0.5.3 + v0.5.4 are inherited unchanged
> and re-verified by the v0.5.5 audit across all five shapes.

```
  MJÚKBLÆJA CONFIG (heretic.yaml example with all five shape kinds)

    sjon:
      screen:
        privacy_masks:
          # rectangle (v0.5.3, unchanged)
          - {x: 0, y: 0, w: 320, h: 200, mode: blur}
          # circle (v0.5.4)
          - {cx: 1700, cy: 200, radius: 80, mode: solid}
          # polygon (v0.5.4)
          - {points: [[800,600],[1000,580],[1100,700],[950,800]],
             mode: pixelate}
          # rounded rectangle (v0.5.5 NEW) — for a chat window
          - {x: 100, y: 800, w: 600, h: 200, corner_radius: 16, mode: blur}
          # ellipse (v0.5.5 NEW) — for an oval avatar
          - {cx: 1500, cy: 900, rx: 80, ry: 60, mode: solid}

  YAML loader heuristic for distinguishing the five shapes:
    presence of `corner_radius` AND `x`/`w`/`h`  → RoundedRectangle
    presence of `rx`/`ry`                        → Ellipse
    presence of `radius` AND `cx`/`cy`           → Circle
    presence of `points`                         → Polygon
    presence of `x`/`y`/`w`/`h` only             → Region (rectangle)
```

---

### 4.11 Tool Flow (v0.6 — outbound, on agent demand)

> **Added 2026-05-08 v0.6 (Védis Eikleið).** This section maps the fourth sense river: the hand that
> reaches. Where the previous three rivers carry perception (Tunga out, Hlust in, Sjón in), this
> river carries action. The agent forms an intention, names a primitive, and the body carries that
> intention to a running application on the host — or across the Tailscale wire to a remote host.
>
> **What is new in v0.6:** L5 Skilningr substrate (the sense hub layer) ships for the first time.
> Smiðja is the first sense within it. The agent gains its first hand.
>
> **Pattern:** The tool flow follows the Tunga/Hlust pattern — it is an extension of the
> `send_message` / streaming-response cycle already established in v0.1. Where Tunga extends the
> response path (text out → audio out) and Sjón extends the request path (message send → image in),
> the tool flow creates a new loop within the response path: when the agent emits a tool call instead
> of a final answer, the body executes the primitive and feeds the result back as a new input, and
> the loop repeats until the agent is satisfied.
>
> **Scope:** v0.6 ships the Smiðja sense only (wrapping Seidr-Smidja's Brúarhönd HTTP daemon).
> Future senses (filesystem, terminal, browser) are deferred to v0.6.x and beyond.
>
> **Cross-reference — receiving end:** Seidr-Smidja's Brúarhönd daemon is documented in
> `runa/Seidr-Smidja/docs/features/brunhand/README.md` and its HTTP API contract in
> `runa/Seidr-Smidja/src/seidr_smidja/brunhand/daemon/INTERFACE.md`. HERETIC's role is to wrap
> that surface, not reimplement it. This section maps HERETIC's side of the connection only.

**Lifecycle dependency:** Skilningr initializes at Kynding (SmidjaSense constructed; BrunhandHttpClient created with configured endpoint and token env var; not yet connected). The first actual HTTP call to Brúarhönd occurs when the agent emits a `tool_call` block during Samræður.

**Privacy invariant (CRITICAL — sealed at v0.6):** The bearer token that authenticates to the
Brúarhönd daemon comes exclusively from the env var named in `skilningr.smidja.token_env`. It
is NEVER stored in `heretic.yaml` plaintext. It is NEVER logged. The httpx `Authorization` header
is set on each request without any log line that includes its value. An operator who scrubs
application logs receives a clean record with no token material.

#### 4.11.1 Trigger — when does a tool call begin?

```
  SAMRAEDUR — agent response stream arrives from Bifröst

  [Bifröst client: streaming SSE response from Pi / Hermes Agent]
       |
       |  normal text delta: choice.delta.content = "<text>"
       |    --> AgentTokenEvent published to Vébond (text appears in ChatHistory)
       |    --> Tunga sentence chunker receives text fragments (voice output path)
       |
       |  tool call delta: choice.delta.tool_calls[0] = {...}
       |    choice.finish_reason = null during accumulation
       |    --> Bifröst client: tool call accumulator receives delta
       |    --> function name accumulated across deltas (may arrive in fragments)
       |    --> arguments JSON accumulated across deltas (may arrive as a partial string)
       |
       v
  [choice.finish_reason = "tool_calls"]
       |
       |  Bifröst client: emits complete ToolCall event
       |    ToolCall { id: "<call_id>", name: "<tool_name>", arguments_json: "<json string>" }
       |
       v
  [CLI receives ToolCall event]
       |
       |  publishes: sense.tool_call (state="started", sense=<prefix>, tool_name=<name>, call_id=<id>)
       |               --> Vébond LayerStatusPanel: Smiðja row shows tool call activity
       |
       v
  [ToolDispatcher.dispatch(tool_call)]
       |  routes by tool-name prefix (e.g., "smidja.screenshot" → prefix "smidja")
       |  looks up registered sense in SkilningrConfig.senses dict
       |  passes tool_call to the sense's dispatch_tool_call() method
```

#### 4.11.2 Pipeline — ToolDispatcher → SmidjaSense → BrunhandHttpClient

```
  [ToolDispatcher.dispatch(tool_call)]
       |
       |  IF prefix matches registered sense:
       |    --> SmidjaSense.dispatch_tool_call(tool_call)
       |
       |  IF prefix unknown (not in registry):
       |    --> return tool_result with {"error": "unknown_tool", "name": "<name>"}
       |    (see F-6 in §4.11.4)
       |
       v
  [SmidjaSense.dispatch_tool_call(tool_call)]
       |
       |  maps tool_name to BrunhandHttpClient method:
       |    "smidja.screenshot"   --> client.screenshot(region=...)
       |    "smidja.click"        --> client.click(x, y, button, ...)
       |    "smidja.type"         --> client.type(text, ...)
       |    "smidja.hotkey"       --> client.hotkey(keys, ...)
       |    "smidja.vroid_open"   --> client.vroid_open_project(project_path, ...)
       |    "smidja.vroid_export" --> client.vroid_export_vrm(output_path, ...)
       |
       |  parses arguments_json into typed kwargs
       |
       v
  [BrunhandHttpClient.<method>()]
       |
       |  constructs POST request to Brúarhönd daemon:
       |    URL: https://<skilningr.smidja.host>:8848/v1/brunhand/<endpoint>
       |    Header: Authorization: Bearer <token from env var>
       |    Body: BrunhandEnvelope (request_id UUID, session_id, agent_id) + primitive-specific fields
       |
       |  HTTP endpoint mapping (HERETIC tool name → Brúarhönd daemon path):
       |    smidja.screenshot   --> POST /v1/brunhand/screenshot
       |    smidja.click        --> POST /v1/brunhand/click
       |    smidja.type         --> POST /v1/brunhand/type
       |    smidja.hotkey       --> POST /v1/brunhand/hotkey
       |    smidja.vroid_open   --> POST /v1/brunhand/vroid/open_project   (NOTE: see §4.11.6)
       |    smidja.vroid_export --> POST /v1/brunhand/vroid/export_vrm     (NOTE: see §4.11.6)
       |
       |  transport: httpx async (same library as Bifröst; reused dependency)
       |  timeout: from BifrostConfig (or dedicated smidja timeout if operator sets it)
       |  TLS: Brúarhönd daemon serves HTTPS when cert_path is configured
       |  Tailscale routing: when skilningr.smidja.host is a Tailscale MagicDNS name or
       |    100.x.y.z IP, httpx connects directly through the Tailscale virtual NIC —
       |    no special handling required; Tailscale is plumbed at the OS level
       |
       v
  [Brúarhönd daemon on VRoid host — Horfunarþjónn]
       |
       |  Gæslumaðr validates Bearer token (constant-time comparison)
       |  Sjálfsmöguleiki confirms primitive is available on this platform
       |  Primitive handler executes the GUI action on the live desktop
       |
       |  returns: BrunhandResponseEnvelope JSON
       |    {
       |      "request_id": "<echoed>",
       |      "session_id": "<echoed>",
       |      "success": true,
       |      "payload": { ... primitive-specific result ... },
       |      "error": null,
       |      "daemon_timestamp": "<ISO 8601>",
       |      "latency_ms": 42.7
       |    }
       |
       |  screenshot payload:
       |    { "png_bytes_b64": "<base64-encoded PNG>", "width": N, "height": N,
       |      "captured_at": "...", "monitor_index": 0 }
       |
       v
  [BrunhandHttpClient receives response]
       |
       |  parses BrunhandResponseEnvelope
       |
       v
  [SmidjaSense encodes result for agent]
       |
       |  screenshot primitive:
       |    png_bytes = base64.b64decode(payload.png_bytes_b64)
       |    data_url = "data:image/png;base64," + payload.png_bytes_b64
       |    content = json.dumps({"image": data_url, "width": N, "height": N})
       |    (mirrors Sjón frame format; agent receives the same data URL structure it knows
       |     from vision; the hand's eye is the same kind of eye as the body's eye)
       |
       |  all other primitives:
       |    content = json.dumps(payload)   (JSON dict serialized as string)
       |
       v
  [CLI assembles OpenAI-format tool result message]
       |
       |  appends to messages list:
       |    {
       |      "role": "tool",
       |      "tool_call_id": "<id from ToolCall event>",
       |      "content": "<json string>"
       |    }
       |
       |  publishes: sense.tool_call (state="completed", call_id=<id>)
       |               --> Vébond LayerStatusPanel: Smiðja row returns to idle
```

#### 4.11.3 Multi-round loop and the cap

```
  [CLI: tool result appended to messages]
       |
       v
  [CLI: calls bifrost.send_message again with updated messages]
       |
       |  POST <bifrost.endpoint>/v1/chat/completions
       |  body: {
       |    "model": "<configured>",
       |    "messages": [
       |      ... full conversation history including tool results ...
       |    ],
       |    "tools": [<all enabled sense schemas>],
       |    "stream": true,
       |    "max_tokens": 127000
       |  }
       |
       v
  [Agent receives tool result and responds]
       |
       |  CASE A — agent emits another tool_call:
       |    --> loop back to §4.11.1
       |    --> round counter incremented
       |
       |  CASE B — agent emits text with finish_reason = "stop":
       |    --> normal turn completion
       |    --> response text processed by Tunga (voice) and Vébond (ChatHistory)
       |    --> CLI returns to user-input prompt
       |
       |  MULTI-ROUND CAP:
       |    IF round_counter >= bifrost.max_tool_call_rounds (default: 5 from BifrostConfig):
       |      CLI halts the loop
       |      log.warning: "max_tool_call_rounds reached (<N>); halting tool dispatch for this turn"
       |      publishes: sense.tool_call (state="capped")
       |      CLI returns to next user-input prompt (final assistant message kept in history)
       |      (the agent is not notified; the truncation is on the HERETIC side)
```

**Config dependency for multi-round cap:**

| Config key | Default | Controls |
|---|---|---|
| `bifrost.max_tool_call_rounds` | `5` | Maximum tool call dispatch rounds per turn before HERETIC halts the loop; prevents runaway tool-call chains |

#### 4.11.4 Failure modes

Seven failure modes are defined. In all cases the active turn does NOT crash. The failure is
returned to the agent as a structured `tool_result` error, allowing the agent to retry, pivot,
or explain the situation to the user.

```
  F-1: Brúarhönd unreachable (httpx.ConnectError)
    Cause: skilningr.smidja.host is down, Tailscale tunnel is broken, daemon is not running,
           or port 8848 is not reachable.
    SmidjaSense catches ConnectError (via BrunhandHttpClient)
    returns tool_result content: {"error": "brunhand_unreachable", "detail": "<endpoint>"}
    log.warning: "Brúarhönd unreachable at <endpoint> — tool call returned error result"
    publishes: sense.tool_call (state="error", error_type="unreachable")
    Turn continues — agent sees the error and may retry or explain.

  F-2: Auth fails (HTTP 401)
    Cause: bearer token is wrong or env var is not set.
    BrunhandHttpClient raises AuthError on 401 response.
    SmidjaSense returns tool_result content: {"error": "auth_failed"}
    log.error: "Brúarhönd auth failed (401) — check token env var <token_env>"
    Turn continues — agent sees error.
    Operator action required: verify env var named in skilningr.smidja.token_env is set correctly.

  F-3: Timeout (httpx.TimeoutException)
    Cause: daemon reachable but request exceeds timeout threshold (slow screenshot, slow GUI op).
    SmidjaSense returns tool_result: {"error": "timeout", "after_ms": <N>}
    log.warning: "Brúarhönd request timed out after <N>ms — <tool_name>"
    Turn continues. Agent may retry.

  F-4: Brúarhönd 5xx response
    Cause: daemon internal error (unhandled exception in primitive handler, OOM, OS error).
    BrunhandHttpClient raises ServerError on 5xx response.
    SmidjaSense returns tool_result: {"error": "daemon_error", "status": <N>, "body": "<excerpt>"}
    log.warning: "Brúarhönd returned HTTP <N> for <tool_name>"
    Turn continues.

  F-5: Malformed response (daemon returns non-JSON or schema mismatch)
    Cause: version mismatch between HERETIC's BrunhandHttpClient and the daemon; partial response;
           network corruption.
    BrunhandHttpClient raises ParseError on JSON decode failure or Pydantic validation error.
    SmidjaSense returns tool_result: {"error": "malformed_response"}
    log.warning: "Brúarhönd response could not be parsed for <tool_name>"
    Turn continues.

  F-6: Unknown tool prefix (agent names a tool not in the registry)
    Cause: agent was given a tool schema but hallucinated a different tool name; or tool schema
           was not sent correctly; or a future tool was requested against a v0.6 HERETIC.
    ToolDispatcher finds no registered sense for the prefix.
    Returns tool_result: {"error": "unknown_tool", "name": "<name>"}
    log.warning: "ToolDispatcher: no sense registered for tool prefix '<prefix>'"
    Defensive path; should not occur when tool schemas are sent correctly.

  F-7: max_tool_call_rounds reached (see §4.11.3)
    Cause: agent enters a multi-round loop that exceeds bifrost.max_tool_call_rounds.
    CLI halts loop; no further tool_calls dispatched this turn.
    Final assistant message (last text or partial result) kept in messages history.
    log.warning: "max_tool_call_rounds (<N>) reached; halting tool dispatch for this turn"
    Turn ends; CLI returns to user-input prompt.
    No tool_result is sent for the uncompleted call (agent does not receive an error for F-7 —
    HERETIC simply stops. The next user message resumes normally with a clean round counter.)
```

#### 4.11.5 Config dependencies for the tool path

| Config key | Default | Controls |
|---|---|---|
| `skilningr.smidja.enabled` | `false` | Master toggle — must be `true` for Smiðja to register its tools |
| `skilningr.smidja.host` | `"127.0.0.1"` | Brúarhönd daemon host (Tailscale MagicDNS name, Tailscale IP, or localhost) |
| `skilningr.smidja.port` | `8848` | Brúarhönd daemon port (default from Seidr-Smidja) |
| `skilningr.smidja.token_env` | (required) | Name of the env var holding the bearer token — NOT the token itself |
| `bifrost.max_tool_call_rounds` | `5` | Multi-round cap |
| `bifrost.vision_in` (existing) | `true` | Existing capability flag; unrelated to tool_use but on the same capability negotiation path |

**Capability gate:** Tool schemas are sent to the agent in the `tools` array only when
`bifrost.capability_tool_use` (`?tool_use` flag per `AGENT_AGNOSTIC_PROTOCOL.md`) is true.
This flag is verified at TENGSL. If the agent does not support `?tool_use`, the `tools` array
is empty and tool calls can never arrive.

#### 4.11.6 API path discrepancy — TASK §4 vs Brúarhönd daemon INTERFACE.md

> **Discrepancy identified by Védis Eikleið, 2026-05-08.**
>
> The TASK file §4 lists simplified paths for the VRoid-specific endpoints. The actual Brúarhönd
> daemon INTERFACE.md (`runa/Seidr-Smidja/src/seidr_smidja/brunhand/daemon/INTERFACE.md`)
> specifies different, nested paths:
>
> | TASK §4 table | Actual daemon INTERFACE.md | Notes |
> |---|---|---|
> | `/v1/brunhand/vroid-open` | `/v1/brunhand/vroid/open_project` | TASK uses hyphens + flat path; actual uses slash-nested |
> | `/v1/brunhand/vroid-export` | `/v1/brunhand/vroid/export_vrm` | TASK abbreviated name; actual uses full verb |
> | `/v1/brunhand/health` (GET) | `/v1/brunhand/health` (GET) | Match |
> | `/v1/brunhand/capabilities` (GET) | `/v1/brunhand/capabilities` (GET) | Match |
> | `/v1/brunhand/screenshot` | `/v1/brunhand/screenshot` | Match |
> | `/v1/brunhand/click` | `/v1/brunhand/click` | Match |
> | `/v1/brunhand/type` | `/v1/brunhand/type` | Match |
> | `/v1/brunhand/hotkey` | `/v1/brunhand/hotkey` | Match |
>
> Additionally, the daemon INTERFACE.md defines several endpoints not listed in TASK §4
> (not relevant for the 6-tool set but present on the daemon): `/v1/brunhand/move`,
> `/v1/brunhand/drag`, `/v1/brunhand/scroll`, `/v1/brunhand/find_window`,
> `/v1/brunhand/wait_for_window`, `/v1/brunhand/vroid/save_project`.
>
> **Forge Worker action required:** The BrunhandHttpClient must use the paths from the daemon
> INTERFACE.md, not the TASK §4 shorthand. Specifically:
> - `vroid_open_project` method must POST to `/v1/brunhand/vroid/open_project`
> - `vroid_export_vrm` method must POST to `/v1/brunhand/vroid/export_vrm`
>
> The tool names exposed to the agent (`smidja.vroid_open`, `smidja.vroid_export`) are
> HERETIC-internal names and are independent of the daemon's URL paths — the mapping is
> performed inside BrunhandHttpClient.

---

## 16. L5 Skilningr — Smiðja Component Diagram (v0.6.1)

> **Added 2026-05-08 v0.6 (Védis Eikleið). Extended 2026-05-08 v0.6.1 (Védis Eikleið).**
> Maps the internal structure of the `skilningr/` module and its first sense subpackage
> `senses/smidja/`, and shows the multi-round tool-call loop from agent intent to either arm
> of the workshop and back. In v0.6 the workshop held one anvil (Brúarhönd). In v0.6.1 it holds
> two: Brúarhönd (live GUI) and Forge (headless Blender). Drawn in the same style as §11 (Tunga),
> §12 (Hlust), and §15 (Sjón).
>
> **Position in the body:** Skilningr is the discernment layer — the organ that decides which
> sense to invoke when the agent reaches. It sits between the CLI (which receives raw ToolCall
> events from Bifröst) and the individual senses (which know how to speak to external surfaces).
> In v0.6.1, Smiðja is the only mounted sense but now contains two HTTP clients: one for the live
> GUI surface (Brúarhönd) and one for the headless render surface (Forge / Straumur REST). The
> hub is designed to carry more senses; the first is the proof.

```
  ============================================================
  SKILNINGR MODULE — src/heretic/skilningr/    (v0.6 First Hand)
  ============================================================

  skilningr/
  |
  ├── config_model.py    SkilningrConfig
  │                      |  senses: dict[str, SkilningrSenseConfig]
  │                      |    key = sense_id (e.g., "smidja")
  │                      |    value = SkilningrSenseConfig (enabled, host, port, token_env, ...)
  │                      |
  │                      |  SmidjaConfig (extends SkilningrSenseConfig)   [v0.6.1: extended]
  │                      |
  │                      |    brunhand:  BrunhandConfig   (sub-block — Brúarhönd arm)
  │                      |      enabled: bool          default false
  │                      |      host: str              default "127.0.0.1"
  │                      |      port: int              default 8848
  │                      |      token_env: str         (name of env var — never the token itself)
  │                      |      timeout_ms: int        default 30000
  │                      |
  │                      |    forge:     ForgeConfig    (sub-block — Forge arm)   (v0.6.1)
  │                      |      enabled: bool                      default false
  │                      |      endpoint: str                      default "http://127.0.0.1:8765"
  │                      |      token_env: str | None              default None
  │                      |        (optional — Straumur may not require auth on localhost)
  │                      |      request_timeout_seconds: int       default 120
  │                      |        (Blender renders are slow; 120s is the minimum safe default)
  │                      |
  │                      Loaded at Kynding from grunnr/config.py (Approach B:
  │                      SkilningrConfig consolidated into HereticConfig).
  │                      Never re-read mid-ceremony.
  │
  ├── errors.py          SkilningrError (base)
  │                      |-- SenseUnavailableError   (sense not enabled or not reachable)
  │                      |-- ToolDispatchError       (dispatch failed for a registered sense)
  │
  ├── dispatcher.py      ToolDispatcher
  │                      |  __init__(senses: dict[str, SenseLike]) -> self
  │                      |    senses built from enabled SkilningrConfig entries at TENGSL
  │                      |
  │                      |  async dispatch(tool_call: ToolCall) -> ToolResult
  │                      |    1. split tool_call.name on "." → (prefix, action)
  │                      |    2. look up prefix in self._senses
  │                      |    3. IF found:  await sense.dispatch_tool_call(tool_call)
  │                      |    4. IF not found:  return error ToolResult (F-6)
  │                      |    returns ToolResult always — never raises to CLI
  │                      |
  │                      ToolDispatcher is the single dispatch seam.
  │                      CLI holds one ToolDispatcher instance per ceremony.
  │
  └── senses/
      |
      └── smidja/        Smiðja — the first sense (L5.5)
          |
          ├── errors.py      SmidjaError (base)
          │                  |-- BrunhandUnreachableError   (F-1, Brúarhönd arm)
          │                  |-- BrunhandAuthError          (F-2, Brúarhönd arm)
          │                  |-- BrunhandTimeoutError       (F-3, Brúarhönd arm)
          │                  |-- BrunhandServerError        (F-4, Brúarhönd arm)
          │                  |-- BrunhandParseError         (F-5, Brúarhönd arm)
          │                  |-- ForgeError (base for Forge arm)
          │                        |-- ForgeUnreachableError  (F-1, Forge arm)
          │                        |-- ForgeTimeoutError      (F-2, Forge arm)
          │                        |-- ForgeValidationError   (F-3 + F-5, Forge arm)
          │                        |-- ForgeServerError       (F-4, Forge arm)
          │                  All extend SmidjaError (which extends SkilningrError)
          │                  All caught by SmidjaSense; none propagate to ToolDispatcher.
          │
          ├── tools.py       ToolDefinition list (6 Brúarhönd + 3 Forge entries — OpenAI tools schema)
          │                  |                  (v0.6.1: extended from 6 to 9 entries)
          │                  |
          │                  |  SMIDJA_TOOLS: list[dict] = [
          │                  |
          │                  |    --- BRÚARHÖND ARM (live GUI) ---
          │                  |
          │                  |    smidja.screenshot
          │                  |      description: "Capture a screenshot of the remote desktop"
          │                  |      parameters: { region: ScreenRect | null }
          │                  |
          │                  |    smidja.click
          │                  |      description: "Click at screen coordinates"
          │                  |      parameters: { x: int, y: int, button: str, clicks: int,
          │                  |                    interval: float, modifiers: list[str] }
          │                  |
          │                  |    smidja.type
          │                  |      description: "Type a text string on the remote desktop"
          │                  |      parameters: { text: str, interval: float }
          │                  |
          │                  |    smidja.hotkey
          │                  |      description: "Press a key combination on the remote desktop"
          │                  |      parameters: { keys: list[str] }
          │                  |
          │                  |    smidja.vroid_open
          │                  |      description: "Open a .vroid project file in VRoid Studio"
          │                  |      parameters: { project_path: str, wait_timeout_seconds: float }
          │                  |      maps to: POST /v1/brunhand/vroid/open_project
          │                  |
          │                  |    smidja.vroid_export
          │                  |      description: "Export the open VRoid Studio project as VRM"
          │                  |      parameters: { output_path: str, overwrite: bool,
          │                  |                    wait_timeout_seconds: float }
          │                  |      maps to: POST /v1/brunhand/vroid/export_vrm
          │                  |
          │                  |    --- FORGE ARM (headless Blender render) ---   (v0.6.1)
          │                  |
          │                  |    smidja.forge_build_avatar
          │                  |      description: "Build a VRM avatar from a Loom spec via headless Blender"
          │                  |      parameters: { spec: object }
          │                  |      maps to: POST /v1/avatars
          │                  |      timeout: forge.request_timeout_seconds (default 120)
          │                  |
          │                  |    smidja.forge_get_avatar
          │                  |      description: "Get avatar metadata and artifact URLs by ID"
          │                  |      parameters: { id: str }
          │                  |      maps to: GET /v1/avatars/{id}
          │                  |
          │                  |    smidja.forge_inspect_avatar
          │                  |      description: "Inspect an avatar (schema validation and diagnostics)"
          │                  |      parameters: { id: str }
          │                  |      maps to: POST /v1/inspect
          │                  |
          │                  |  ]
          │                  |
          │                  |  Brúarhönd tools included when:
          │                  |    - skilningr.smidja.brunhand.enabled = true
          │                  |    - bifrost.capability_tool_use (?tool_use) = true
          │                  |
          │                  |  Forge tools included when:
          │                  |    - skilningr.smidja.forge.enabled = true
          │                  |    - bifrost.capability_tool_use (?tool_use) = true
          │                  |
          │                  |  Each arm contributes its tool subset independently.
          │                  |  Agent only sees tools for enabled arms.
          │
          ├── client.py      BrunhandHttpClient   [BRÚARHÖND ARM — live GUI control]
          │                  |
          │                  |  __init__(host, port, token_env, timeout_ms) -> self
          │                  |    token: str = os.environ[token_env]   (read once at init)
          │                  |    httpx.AsyncClient created with bearer auth header
          │                  |    base_url: "https://<host>:<port>"
          │                  |    (or "http://<host>:<port>" if require_https not set by operator)
          │                  |
          │                  |  async health() -> dict
          │                  |    GET /v1/brunhand/health    (no auth — liveness probe only)
          │                  |
          │                  |  async screenshot(region=None) -> BrunhandResponse
          │                  |    POST /v1/brunhand/screenshot
          │                  |
          │                  |  async click(x, y, button, clicks, interval, modifiers) -> BrunhandResponse
          │                  |    POST /v1/brunhand/click
          │                  |
          │                  |  async type(text, interval) -> BrunhandResponse
          │                  |    POST /v1/brunhand/type
          │                  |
          │                  |  async hotkey(keys) -> BrunhandResponse
          │                  |    POST /v1/brunhand/hotkey
          │                  |
          │                  |  async vroid_open_project(project_path, wait_timeout_seconds) -> BrunhandResponse
          │                  |    POST /v1/brunhand/vroid/open_project
          │                  |    (NOTE: not /v1/brunhand/vroid-open — see §4.11.6)
          │                  |
          │                  |  async vroid_export_vrm(output_path, overwrite, wait_timeout_seconds) -> BrunhandResponse
          │                  |    POST /v1/brunhand/vroid/export_vrm
          │                  |    (NOTE: not /v1/brunhand/vroid-export — see §4.11.6)
          │                  |
          │                  |  Auth invariant: Authorization header set on httpx.AsyncClient
          │                  |    at construction; never logged; token value never appears in
          │                  |    any log line emitted by this module.
          │                  |
          │                  |  Error mapping:
          │                  |    httpx.ConnectError       --> BrunhandUnreachableError (F-1)
          │                  |    HTTP 401                 --> BrunhandAuthError        (F-2)
          │                  |    httpx.TimeoutException   --> BrunhandTimeoutError     (F-3)
          │                  |    HTTP 5xx                 --> BrunhandServerError      (F-4)
          │                  |    JSON / Pydantic error    --> BrunhandParseError       (F-5)
          │
          ├── forge_client.py  ForgeHttpClient   [FORGE ARM — headless Blender render]  (v0.6.1)
          │                  |
          │                  |  __init__(endpoint, token_env, request_timeout_seconds) -> self
          │                  |    token: str | None = os.environ.get(token_env) if token_env else None
          │                  |      (optional — Straumur may run unauthenticated on localhost)
          │                  |    httpx.AsyncClient; Authorization header set only if token present
          │                  |    base_url: endpoint  (default "http://127.0.0.1:8765")
          │                  |    timeout: request_timeout_seconds  (default 120 — Blender renders slow)
          │                  |
          │                  |  async health() -> dict
          │                  |    GET /health    (no auth — liveness probe only)
          │                  |    NOTE: path is /health, NOT /v1/brunhand/health
          │                  |
          │                  |  async build_avatar(spec: dict) -> ForgeAvatarResponse
          │                  |    POST /v1/avatars
          │                  |    Body: { "spec": spec }
          │                  |    Returns: { "id": str, "status": str, "artifacts": [...] }
          │                  |
          │                  |  async get_avatar(avatar_id: str) -> ForgeAvatarResponse
          │                  |    GET /v1/avatars/{avatar_id}
          │                  |
          │                  |  async inspect_avatar(avatar_id: str) -> ForgeInspectResponse
          │                  |    POST /v1/inspect
          │                  |    Body: { "id": avatar_id }
          │                  |
          │                  |  async list_assets() -> ForgeAssetsResponse
          │                  |    GET /v1/assets
          │                  |
          │                  |  Auth note: optional bearer token; env var NAME in forge.token_env.
          │                  |    If token_env is None or env var absent: no Authorization header.
          │                  |    Pattern mirrors BrunhandHttpClient but token is not required.
          │                  |
          │                  |  Error mapping:
          │                  |    httpx.ConnectError       --> ForgeUnreachableError  (F-1)
          │                  |    httpx.TimeoutException   --> ForgeTimeoutError      (F-2)
          │                  |    HTTP 4xx                 --> ForgeValidationError   (F-3 / F-5)
          │                  |    HTTP 5xx                 --> ForgeServerError       (F-4)
          │                  |
          │                  |  PARALLEL TO BrunhandHttpClient — independent endpoint, independent
          │                  |  auth, independent timeout profile. Both live under the same sense.
          │
          └── sense.py       SmidjaSense
                             |
                             |  v0.6.1: the workshop now holds two anvils.
                             |  SmidjaSense owns one BrunhandHttpClient (Brúarhönd arm)
                             |  and one ForgeHttpClient (Forge arm). Each half opens, probes,
                             |  and closes independently. Either can be absent without preventing
                             |  the other from working.
                             |
                             |  Public interface (matches SenseLike protocol):
                             |    async open() -> None
                             |      called at TENGSL; probes BOTH arms independently (see §4.11.8)
                             |        IF brunhand.enabled: health-probe /v1/brunhand/health
                             |        IF forge.enabled:    health-probe /health
                             |      unreachable arm: logs warning; arm marked degraded
                             |      sense as a whole remains open regardless
                             |
                             |    async close() -> None
                             |      called at SLOKNA
                             |      IF brunhand client exists: BrunhandHttpClient.close()
                             |      IF forge client exists:    ForgeHttpClient.close()
                             |      each close in independent try/except
                             |
                             |    async dispatch_tool_call(tool_call: ToolCall) -> ToolResult
                             |      1. parse arguments_json into kwargs
                             |      2. route by tool_name prefix:
                             |           tool_name has "forge_" sub-prefix
                             |             --> ForgeHttpClient method
                             |           else
                             |             --> BrunhandHttpClient method
                             |      3. catch any SmidjaError subclass --> return error ToolResult
                             |         (covers both BrunhandError and ForgeError hierarchies)
                             |      4. on success: encode result for agent
                             |      5. return ToolResult always — never raises
                             |
                             |  Screenshot result encoding (Brúarhönd arm, unchanged):
                             |    data_url = "data:image/png;base64," + payload.png_bytes_b64
                             |    content = json.dumps({"image": data_url,
                             |                          "width": payload.width,
                             |                          "height": payload.height})
                             |    (mirrors Sjón data URL format)
                             |
                             |  Forge result encoding:
                             |    content = json.dumps({"id": ..., "status": ..., "artifacts": [...]})
                             |    or json.dumps(diagnostics_dict) for inspect
                             |    agent receives structured JSON in tool_result content
                             |
                             |  Other Brúarhönd primitive result encoding (unchanged):
                             |    content = json.dumps(payload)
                             |    (Pydantic model dict serialized as JSON string)


  ============================================================
  MULTI-ROUND LOOP DIAGRAM
  ============================================================

  [Agent — on Pi / Hermes]
       |
       |  turn N: emits tool_call (smidja.screenshot)
       |
       v
  [Bifröst client — accumulates deltas → ToolCall event]
       |
       v
  [CLI — publishes sense.tool_call(started)]
       v
  [ToolDispatcher → SmidjaSense]
       |
       |  routes by tool_name prefix:
       |    "forge_" sub-prefix  -->  ForgeHttpClient
       |    no "forge_" prefix   -->  BrunhandHttpClient
       |
       +--- [BrunhandHttpClient]
       |         HTTPS/HTTP request → Tailscale wire (or loopback) → Brúarhönd daemon → VRoid host
       |         (fast, sub-second for most primitives)
       |
       +--- [ForgeHttpClient]
                 HTTP request → Straumur REST → headless Blender pipeline → render
                 (slow; up to 120s default timeout; agent waits for tool_result)
       |
       v
  [Client receives response]
       v
  [SmidjaSense encodes → ToolResult]
       v
  [CLI appends {"role":"tool","tool_call_id":"<id>","content":"<json>"} to messages]
       v
  [CLI publishes sense.tool_call(completed)]
       v
  [CLI calls bifrost.send_message(messages)]
       |
       |  round_counter++
       |  IF round_counter >= max_tool_call_rounds: HALT (F-7)
       |
       v
  [Agent — receives tool result; emits next response]
       |
       |-- CASE A: another tool_call  --> loop back to top (round_counter++)
       |-- CASE B: text + finish_reason=stop  --> normal turn completion; loop exits
       |
       v
  [CLI returns to user-input prompt]


  ============================================================
  AUTH INVARIANT — SEALED AT v0.6
  ============================================================

  The token path:
    heretic.yaml → "token_env: HERETIC_SMIDJA_TOKEN"   (env var NAME only)
    OS environment → HERETIC_SMIDJA_TOKEN = "<actual token>"  (set by operator)
    BrunhandHttpClient.__init__:
      self._token = os.environ[self._token_env]   (read into memory once)
      self._client = httpx.AsyncClient(
          headers={"Authorization": f"Bearer {self._token}"},
          ...)
    No log line ever contains self._token.
    No config serialization ever contains self._token.
    The value travels only in the HTTP Authorization header, encrypted by TLS.

  Forbidden paths (must not exist anywhere in HERETIC codebase):
    skillingr.smidja.token = "<literal value>"    FORBIDDEN in heretic.yaml
    log.debug(f"token: {token}")                  FORBIDDEN in any log call
    session_log.write({"token": ...})             FORBIDDEN in session log


  ============================================================
  INVARIANTS
  ============================================================
  - ToolDispatcher never raises to CLI
    All dispatch errors are returned as ToolResult with error JSON content.
  - SmidjaSense never raises to ToolDispatcher
    All SmidjaError subclasses are caught internally (both Brúarhönd and Forge hierarchies);
    return value is always ToolResult.
  - Bearer token never appears in any log line (sealed invariant — applies to both arms)
    Brúarhönd: token_env required; Authorization header set at construction.
    Forge: token_env optional; Authorization header set only if token present.
    Neither token value appears in any log line, config serialization, or session log.
  - Tool schemas are sent to the agent ONLY per arm when both conditions hold:
      (a) arm.enabled = true  AND
      (b) bifrost.capability_tool_use (?tool_use) = true
    Brúarhönd tools and Forge tools are included independently based on their respective enabled flags.
  - Each arm opens and closes independently (v0.6.1 — dual-half lifecycle, see §4.11.8)
    Failure of one arm at TENGSL does not prevent the other arm from opening.
    Failure to close one arm at SLOKNA does not prevent the other arm from closing.
  - multi-round cap is enforced per turn, not per ceremony
    round_counter resets to 0 at the start of each new user message turn
  - The tool loop is entered ONLY on finish_reason = "tool_calls"
    Text responses with finish_reason = "stop" or "length" never enter the tool path
  - BrunhandHttpClient.close() and ForgeHttpClient.close() are always called at SLOKNA
    Each httpx.AsyncClient is closed cleanly; no connection leak on ceremony exit
  - Tool names in the OpenAI schema use HERETIC's two-part format: <sense_id>.<action>
    These are independent of the daemon URL paths.
    Brúarhönd mapping:  smidja.vroid_open → /v1/brunhand/vroid/open_project
                        smidja.vroid_export → /v1/brunhand/vroid/export_vrm
                        (See §4.11.6 for full discrepancy documentation.)
    Forge mapping:      smidja.forge_build_avatar → POST /v1/avatars
                        smidja.forge_get_avatar   → GET  /v1/avatars/{id}
                        smidja.forge_inspect_avatar → POST /v1/inspect
```

---

#### 4.11.7 Forge dispatch (v0.6.1 — headless Blender)

> **Added 2026-05-08 v0.6.1 (Védis Eikleið).** Maps the second arm of the Smiðja sense: the
> headless Blender pipeline. Where Brúarhönd controls a live GUI process, the Forge submits
> Loom specs to Seidr-Smidja's Straumur REST layer, which drives a headless Blender render and
> returns artifact URLs. Both arms live under the same sense; the workshop now houses two anvils.

```
  FORGE DISPATCH PIPELINE

  [Agent — tool_call: smidja.forge_build_avatar]
       |
       |  arguments_json:
       |    { "spec": { <Loom avatar spec JSON> } }
       |
       v
  [ToolDispatcher.dispatch(tool_call)]
       |
       |  prefix = "smidja"  --> SmidjaSense
       |
       v
  [SmidjaSense.dispatch_tool_call(tool_call)]
       |
       |  tool_name has "forge_" sub-prefix
       |    --> routed to ForgeHttpClient (not BrunhandHttpClient)
       |
       v
  [ForgeHttpClient.build_avatar(spec: dict) -> ForgeResponse]
       |
       |  POST /v1/avatars
       |  Host: skilningr.smidja.forge.endpoint   (default "http://127.0.0.1:8765")
       |  Header: Authorization: Bearer <token from forge.token_env>
       |          (optional — Straumur may run unauthenticated on localhost)
       |  Body: { "spec": <Loom spec JSON> }
       |
       |  transport: httpx async
       |  timeout: skilningr.smidja.forge.request_timeout_seconds  (default 120)
       |           (Blender renders are slow; 120s is the minimum safe default)
       |
       v
  [Seidr-Smidja — Straumur REST layer]
       |
       |  validates Loom spec
       |  schedules headless Blender pipeline
       |  returns immediately with job ID and status "accepted" OR
       |         blocks until render completes (depends on Straumur mode)
       |
       v
  [ForgeHttpClient receives response: ForgeAvatarResponse]
       |
       |  { "id": "<avatar_id>",
       |    "status": "complete" | "pending" | "failed",
       |    "artifacts": [ { "type": "vrm", "url": "<url>" }, ... ] }
       |
       v
  [SmidjaSense encodes -> ToolResult]
       |
       |  content = json.dumps({"id": ..., "status": ..., "artifacts": [...]})
       |  agent receives the avatar ID and artifact URLs in the tool_result
       |
       v
  [CLI appends tool_result to messages; resumes agent loop]


  TOOL SURFACE — FORGE ARM:

    smidja.forge_build_avatar
      POST /v1/avatars
      Body: Loom spec (JSON object supplied by agent)
      Returns: avatar id, status, artifact URLs

    smidja.forge_get_avatar
      GET /v1/avatars/{id}
      Returns: avatar metadata, render status, artifact URLs

    smidja.forge_inspect_avatar
      POST /v1/inspect
      Body: { "id": "<avatar_id>" }
      Returns: diagnostics, ground-truth schema validation output

    smidja.forge_list_assets   (optional)
      GET /v1/assets
      Returns: available asset packs

    smidja.forge_health_probe  (internal — not exposed to agent)
      GET /health
      Used by SmidjaSense.open() to probe Forge availability


  TIMING NOTE:
    Blender renders are slow. The 120s default timeout is a floor, not a ceiling.
    Operators running complex Loom specs should raise request_timeout_seconds accordingly.
    The agent sees sense.tool_call events (state="started") during the full render window.
    The agent does NOT stream progress — it waits for one tool_result.
    This is expected behavior: the forge burns at its own pace.
```

---

#### 4.11.8 Dual-half lifecycle — Brúarhönd and Forge open independently

> **Added 2026-05-08 v0.6.1 (Védis Eikleið).** Each arm of the workshop opens and closes on
> its own terms. A missing Forge daemon does not silence the live GUI arm, and vice versa.

```
  LIFECYCLE — INDEPENDENT HALVES

  At TENGSL (connection):
    SmidjaSense.open() called

    IF skilningr.smidja.brunhand.enabled = true:
      BrunhandHttpClient.health() → GET /v1/brunhand/health
        OK:        log.info  "Brúarhönd reachable at <endpoint>"
                   sense._brunhand_available = True
        ConnectError or non-200:
                   log.warning "Brúarhönd not reachable at <endpoint> — Brúarhönd tools degraded"
                   sense._brunhand_available = False
                   (ceremony continues; Brúarhönd tools return F-1 error result when called)

    IF skilningr.smidja.forge.enabled = true:
      ForgeHttpClient.health() → GET /health
        OK:        log.info  "Seidr-Smidja Forge reachable at <endpoint>"
                   sense._forge_available = True
        ConnectError or non-200:
                   log.warning "Seidr-Smidja Forge not reachable at <endpoint> — Forge tools degraded"
                   sense._forge_available = False
                   (ceremony continues; Forge tools return F-1 error result when called)

    The two probes run independently.
    Either can fail without preventing the ceremony from starting.
    Either can fail without affecting the other arm.


  AT SLOKNA (ceremony close):
    SmidjaSense.close() called

    IF brunhand client was created:  BrunhandHttpClient.close()  (closes httpx.AsyncClient)
    IF forge client was created:     ForgeHttpClient.close()      (closes httpx.AsyncClient)

    Each client closed in its own try/except.
    Close failure of one arm does not prevent close of the other.


  TOOL ROUTING BY ARM:
    Tool name has NO "forge_" sub-prefix:
      smidja.screenshot, smidja.click, smidja.type, smidja.hotkey,
      smidja.vroid_open, smidja.vroid_export
      --> routed to BrunhandHttpClient
      --> if _brunhand_available = False: F-1 error tool_result returned immediately

    Tool name has "forge_" sub-prefix:
      smidja.forge_build_avatar, smidja.forge_get_avatar,
      smidja.forge_inspect_avatar, smidja.forge_list_assets
      --> routed to ForgeHttpClient
      --> if _forge_available = False: F-1 error tool_result returned immediately


  DEGRADATION MATRIX:
    Brúarhönd up  / Forge up:   All 9+ tools available. Full workshop.
    Brúarhönd up  / Forge down: 6 Brúarhönd tools available. Forge tools return F-1.
    Brúarhönd down/ Forge up:   3+ Forge tools available. Brúarhönd tools return F-1.
    Brúarhönd down/ Forge down: All tools degraded. Ceremony still starts; agent sees errors.
```

---

#### 4.11.9 Forge-specific failure modes

> **Added 2026-05-08 v0.6.1 (Védis Eikleið).** Five failure modes specific to the Forge arm.
> All follow the invariant: no crash; structured error tool_result returned to agent; turn
> continues. See §4.11.4 for the Brúarhönd arm failure modes (F-1 through F-7).

```
  FORGE FAILURE MODES

  F-1: Forge unreachable (httpx.ConnectError)
    Cause: Seidr-Smidja Straumur daemon is not running; endpoint is wrong;
           network is unavailable.
    ForgeHttpClient raises ForgeUnreachableError.
    SmidjaSense returns tool_result: {"error": "forge_unreachable", "detail": "<endpoint>"}
    log.warning: "Seidr-Smidja Forge unreachable at <endpoint> — tool call returned error result"
    Turn continues. Agent may explain, retry, or attempt a Brúarhönd path instead.

  F-2: Timeout (render exceeds request_timeout_seconds)
    Cause: headless Blender render takes longer than the configured timeout.
           Default 120s; complex Loom specs may exceed this.
    ForgeHttpClient raises ForgeTimeoutError (httpx.TimeoutException).
    SmidjaSense returns tool_result: {"error": "forge_timeout",
                                      "timeout_seconds": <configured value>,
                                      "hint": "raise skilningr.smidja.forge.request_timeout_seconds"}
    log.warning: "Seidr-Smidja Forge timed out after <N>s for <tool_name>"
    Turn continues. Agent may advise operator to raise the timeout or simplify the spec.

  F-3: Spec validation error (4xx with validation body)
    Cause: Loom spec submitted by agent is invalid — missing required fields, bad types,
           or references an unknown asset pack.
    Straumur returns HTTP 4xx with a structured validation error body.
    ForgeHttpClient raises ForgeValidationError.
    SmidjaSense returns tool_result: {"error": "forge_validation_error",
                                      "status": <N>,
                                      "detail": "<excerpt from validation body>"}
    log.warning: "Seidr-Smidja Forge rejected spec (HTTP <N>) for <tool_name>"
    Turn continues. Agent may revise the spec and retry.

  F-4: Render failure (5xx)
    Cause: Straumur / Blender internal error — unhandled exception in the render pipeline,
           OOM during render, corrupt asset, Blender crash.
    Straumur returns HTTP 5xx.
    ForgeHttpClient raises ForgeServerError.
    SmidjaSense returns tool_result: {"error": "forge_server_error",
                                      "status": <N>,
                                      "body": "<excerpt>"}
    log.warning: "Seidr-Smidja Forge returned HTTP <N> for <tool_name>"
    Turn continues. Agent may retry or diagnose.

  F-5: Missing asset pack referenced by Loom spec
    Cause: Loom spec names an asset pack ID that does not exist in Seidr-Smidja's Hoard.
    Straumur returns HTTP 4xx with an asset-not-found body.
    Behavior: same as F-3 (spec validation error), but with a specific error key:
    tool_result: {"error": "forge_asset_not_found",
                  "asset_id": "<id from spec>",
                  "hint": "call smidja.forge_list_assets to see available packs"}
    Agent can recover by calling smidja.forge_list_assets and revising the spec.


  FORGE ERROR CLASS HIERARCHY (mirrors Brúarhönd):
    SmidjaError (base)
      |-- ForgeError (base for all Forge arm errors; extends SmidjaError)
            |-- ForgeUnreachableError   (F-1)
            |-- ForgeTimeoutError       (F-2)
            |-- ForgeValidationError    (F-3)
            |-- ForgeServerError        (F-4)
    F-5 (asset not found) is a subcase of ForgeValidationError with distinct error key.
    All caught by SmidjaSense.dispatch_tool_call(); none propagate to ToolDispatcher.
```

---

#### 4.11.10 Verkminni — deed-memory audit log (v0.6.3)

> **Added 2026-05-09 v0.6.3 (Védis Eikleið).** *Verkminni* — deed-memory.
> Smiðja's first named discipline. The body keeps memory of what its hand
> has done, in a bounded in-memory ring buffer, parallel to (not instead of)
> the agent's narrated memory. Default ON; opt-out via config.

```
  VERKMINNI — AUDIT HOOK FLOW

  SmidjaSense.dispatch_tool_call(tool_call):
      call_id, tool_name, args = parse(tool_call)

      # NEW v0.6.3 — audit "started" recording (non-load-bearing)
      _safe_audit(state="started", call_id=call_id, tool_name=tool_name,
                  args_json=truncate_500(json.dumps(args)),
                  duration_ms=None, error=None)

      t_start = time.monotonic()
      _emit_event("started", ...)            # IPC event (existing v0.6)

      try:
          content = await self._route(tool_name, args)
          duration_ms = int((time.monotonic() - t_start) * 1000)

          # NEW v0.6.3 — audit "completed" recording
          _safe_audit(state="completed", call_id=call_id, tool_name=tool_name,
                      args_json=truncate_500(json.dumps(args)),
                      duration_ms=duration_ms, error=None)

          _emit_event("completed", ...)      # IPC event (existing)
          return success_tool_result(call_id, content)

      except SmidjaError as exc:
          duration_ms = int((time.monotonic() - t_start) * 1000)

          # NEW v0.6.3 — audit "failed" recording
          _safe_audit(state="failed", call_id=call_id, tool_name=tool_name,
                      args_json=truncate_500(json.dumps(args)),
                      duration_ms=duration_ms,
                      error=truncate_500(str(exc)))

          _emit_event("failed", ...)         # IPC event (existing)
          return error_tool_result(...)

      except Exception as exc:               # generic / unexpected
          duration_ms = int((time.monotonic() - t_start) * 1000)
          _safe_audit(state="failed", call_id=call_id, tool_name=tool_name,
                      args_json=truncate_500(json.dumps(args)),
                      duration_ms=duration_ms,
                      error=truncate_500(str(exc)))
          _emit_event("failed", ...)
          return error_tool_result(...)

  # Helper — non-load-bearing wrapper around AuditLog.record():
  _safe_audit(state, call_id, tool_name, args_json, duration_ms, error):
      try:
          self._audit_log.record(AuditEntry(
              timestamp=utcnow_iso8601(),
              call_id=call_id,
              tool_name=tool_name,
              arguments_json=args_json,
              state=state,
              duration_ms=duration_ms,
              error=error,
          ))
      except Exception as exc:
          # Audit failure must NEVER make dispatch raise.
          self._log.warning(
              "Verkminni: audit write failed (dispatch continues): %s", exc,
          )
```

```
  AUDIT ENTRY SHAPE

  AuditEntry dataclass fields:
    timestamp        : str        # UTC ISO8601, e.g. "2026-05-09T18:42:13.184Z"
    call_id          : str        # OpenAI tool_call id, links matched pairs
    tool_name        : str        # e.g. "smidja.click"
    arguments_json   : str        # JSON-serialised args, truncated to 500 chars
    state            : str        # "started" | "completed" | "failed"
    duration_ms      : int | None # None for "started"; int milliseconds for completed/failed
    error            : str | None # None on success/started; truncated str on failed

  TRUNCATION POLICY:
    arguments_json and error are each capped at 500 characters.
    If longer, the trailing portion is replaced with "... (N more chars)"
    where N is the number of characters dropped.

  PAIRED ENTRIES:
    Each tool call produces exactly TWO entries: one "started" and one
    of "completed" or "failed". Both share the same call_id, so a query
    can correlate them as a pair.
```

```
  RING BUFFER — AuditLog

  AuditLog uses collections.deque(maxlen=depth) under a threading.Lock
  for thread-safe mutation.

  Methods:
    record(entry: AuditEntry) -> None
        Appends entry; evicts oldest if at depth.
    entries(limit: int | None = None) -> list[AuditEntry]
        Returns a snapshot copy of the last `limit` entries (all if None).
        Caller can mutate the returned list without affecting the buffer.
    clear() -> None
        Empties the buffer. Called at SmidjaSense.close() / SLOKNA.
    __len__() -> int
        Current entry count.

  EVICTION:
    When depth=N entries are recorded and a new entry arrives, the oldest
    is automatically removed by deque(maxlen) semantics. No memory growth
    beyond N entries.

  DEFAULT DEPTH:
    100 — covers most operator sessions which see dozens to low-hundreds
    of tool calls.

  CEREMONY-SCOPED:
    AuditLog.clear() is called at SLOKNA (Smiðja sense close). The body's
    deed-memory does not persist across ceremonies. Privacy-by-disposition.
```

```
  VERKMINNI INVARIANTS (Auditor verification subjects)

  V-1: Every dispatched tool call produces exactly two paired audit entries
       with the same call_id (started + completed OR started + failed).
       No tool call escapes the audit log when verkminni.enabled = True.

  V-2: Audit-write failures (any Exception inside _safe_audit) are caught
       and logged at warning level. dispatch_tool_call's never-raise
       invariant is preserved. The audit log is a witness, not a gate.

  V-3: Ring buffer evicts oldest at maxlen=depth. No unbounded growth.

  V-4: SmidjaSense.close() (SLOKNA) calls AuditLog.clear(). Ceremony-scoped.

  V-5: When verkminni.enabled = False, AuditLog is replaced with a
       NullAuditLog whose record() is a no-op. dispatch path unchanged.

  Smiðja-1 INHERITED: dispatch_tool_call NEVER raises (preserved by V-2).
  Smiðja-2 INHERITED: bearer token never logged (audit records args dict
                      only; token lives in env var, fetched by client at
                      request time, never appears in args).
  Smiðja-3 INHERITED: tool_result return shape unchanged (audit is
                      additive instrumentation).
```

```
  CONFIG (heretic.yaml)

    skilningr:
      smidja:
        enabled: true                        # existing
        endpoint: http://...                 # existing
        token_env: BRUNHAND_TOKEN_HERETIC    # existing
        max_tool_call_rounds: 5              # existing
        verkminni:                           # NEW v0.6.3
          enabled: true                      # default ON; opt-out for no-log
          depth: 100                         # ring buffer max entries

  When verkminni.enabled = false, no audit hooks fire; NullAuditLog
  no-op record() preserves the dispatch shape exactly.
```

> **Note on default-ON:** Unlike privacy features (`save_frames`, webcam
> `enabled`, `privacy_masks` list) which default OFF for privacy-first
> reasons, observability features default ON because operator-visibility-
> into-agent-acts is a security discipline, not a privacy concern. The
> body keeps memory of its acts by default; the operator who wants no
> log explicitly disables it.

---

#### 4.11.10.1 Verkminni — opt-in persistent disk log (v0.6.3.1)

> **Added 2026-05-09 v0.6.3.1 (Védis Eikleið).** Extension to v0.6.3
> Verkminni. When the operator sets `disk_log_path`, every recorded
> entry is also appended to a JSONL file. Ceremony-scoped in-memory
> behaviour unchanged; disk file persists across ceremonies (point of
> the extension). Default OFF — disk persistence crosses a real privacy
> threshold the operator must explicitly opt into.

```
  PERSISTENT-LOG MIRROR FLOW (best-effort, non-load-bearing)

  AuditLog.record(entry):
      with self._lock:
          self._buffer.append(entry)         # in-memory (V-3 ring buffer)

          if self._disk_log_path is not None:
              try:
                  # Open-append-close per record — survives crashes
                  # better than holding a long-lived file handle
                  self._disk_log_path.parent.mkdir(
                      parents=True, exist_ok=True,
                  )
                  with self._disk_log_path.open("a", encoding="utf-8") as fh:
                      fh.write(json.dumps({
                          "timestamp":      entry.timestamp,
                          "call_id":        entry.call_id,
                          "tool_name":      entry.tool_name,
                          "arguments_json": entry.arguments_json,
                          "state":          entry.state,
                          "duration_ms":    entry.duration_ms,
                          "error":          entry.error,
                      }))
                      fh.write("\n")
              except Exception as exc:
                  # D-3: disk-write failures are non-load-bearing.
                  # Log warning; in-memory record already succeeded.
                  log.warning(
                      "Verkminni: disk write failed (in-memory record "
                      "completed normally): %s", exc,
                  )

  KEY PROPERTIES:

    1. Path-as-toggle: disk_log_path=None means OFF; setting any path
       turns it ON. Mirrors the Blæja privacy_masks: list[] empty=off
       convention.

    2. Open-append-close per record: minimises file-handle hold time;
       resilient to crashes (worst case: lose the in-flight write).

    3. mkdir parents=True: operator can configure a path whose parent
       doesn't exist yet; auto-created on first write.

    4. Disk write happens INSIDE the threading.Lock, so entry ordering
       on disk matches in-memory ordering exactly.

    5. NOT cleared at SLOKNA: SmidjaSense.close() clears the in-memory
       ring buffer (V-4) but does NOT touch the disk file. The
       persistent record outlives the ceremony — that IS the point.

    6. Best-effort: any I/O exception is caught and logged at warning;
       the in-memory record still succeeds; the dispatcher never raises.
       V-2 (witness, not gate) is preserved through the disk extension.
```

```
  D-INVARIANTS (Auditor verification subjects)

  D-1: When disk_log_path is None, behaviour is byte-equivalent to
       v0.6.3. No file is created; no disk I/O occurs.

  D-2: When disk_log_path is set, every successful record() produces
       exactly one new JSONL line in the file. The line is the JSON
       serialisation of the AuditEntry's seven fields.

  D-3: Disk-write failures (OSError, PermissionError, file-system-full,
       directory missing after mkdir) are caught and logged at warning.
       The in-memory record completes normally. Dispatch never raises.

  D-4: The disk file is APPENDED. Recording N entries on a fresh
       AuditLog whose disk_log_path points to a pre-existing file with
       M lines results in M+N total lines.

  D-5: The disk file is NOT cleared at SLOKNA. The persistent record
       outlives the ceremony — the operator chose persistence; the
       body honours that choice across ceremony boundaries.
```

```
  CONFIG (heretic.yaml)

    skilningr:
      smidja:
        verkminni:
          enabled: true                               # existing v0.6.3
          depth: 100                                  # existing v0.6.3
          persistent_log_path: ~/.local/share/heretic/audit/smidja.jsonl
                                                      # NEW v0.6.3.1
                                                      # Default null/None.
                                                      # When set, mirrors
                                                      # in-memory log to
                                                      # this JSONL file.
```

---

#### 4.12 Minni filesystem flow (v0.6.2)

> **Added 2026-05-08 v0.6.2 (Védis Eikleið).** The library opens beside the workshop.
> Minni ("memory") is HERETIC's filesystem sense — it lets the agent read, write, and list
> files within operator-configured roots without touching any path outside them.
> Minni is a sibling sense to Smiðja inside L5 Skilningr; it registers with the same
> ToolDispatcher under the prefix "minni". All three operations are synchronous stdlib only
> (pathlib + io) — no network, no subprocess, no external dependency beyond Python itself.

```
  MINNI FILESYSTEM FLOW

  Step 1 — tool_call arrives at ToolDispatcher
    tool_call.name begins with "minni." (e.g., "minni.read_file")
    ToolDispatcher.dispatch() → routes to MinniSense.dispatch_tool_call(tool_call)
    (same two-part prefix routing used by Smiðja)

  Step 2 — argument parse
    MinniSense parses tool_call.arguments_json
    e.g., { "path": "reports/summary.md" } for read_file
    e.g., { "path": "notes/draft.txt", "content": "..." } for write_file
    e.g., { "path": "reports/" } for list_directory

  Step 3 — sandbox check (path_within_allowed_roots)
    Called from skillingr/sandbox.py; shared across all senses.

    def path_within_allowed_roots(raw_path: str, allowed_roots: list[str]) -> Path:
      p = Path(raw_path).expanduser().resolve()
      for root in allowed_roots:
        r = Path(root).expanduser().resolve()
        IF p == r OR r in p.parents:
          RETURN p
      RAISE SandboxViolationError(f"Path {raw_path!r} is outside all allowed roots")

    Invariants enforced during this step:
      (a) Path traversal blocked: `../` sequences collapse during .resolve() and the
          post-resolution check catches any attempt to escape the root tree.
      (b) Absolute paths outside allowed_roots are rejected at the root-membership check.
      (c) Symlink non-follow: validation uses the raw resolved path of the SYMLINK itself,
          not the target it points to. A symlink inside an allowed root that points outside
          the root is caught because Path.resolve() follows the link and the resulting
          target path will fail the root-membership check. The inverse is also safe: a
          symlink outside an allowed root pointing inside is rejected because the symlink's
          own resolved path is outside the root. In both cases, validation is against the
          path supplied by the caller, resolved without trusting its symlink destination to
          stay inside the root boundary.
      (d) allowed_roots default ["~/heretic_workspace"] — operator must explicitly extend.

  Step 4 — IO operation
    read_file:
      f = validated_path.open("r", encoding="utf-8")
      data = f.read(max_bytes + 1)    # max_bytes = 1_048_576 (1 MB default)
      IF len(data) > max_bytes:
        data = data[:max_bytes]
        truncated = True
      RETURN {"content": data, "truncated": truncated}

    write_file:
      validated_path.parent.mkdir(parents=True, exist_ok=True)
      f = validated_path.open("w", encoding="utf-8")
      IF len(content_bytes) > max_bytes:  RAISE FilesizeLimitError
      f.write(content)
      RETURN {"written": True, "path": str(validated_path)}

    list_directory:
      entries = [
        {"name": e.name, "type": "file" | "dir", "size_bytes": e.stat().st_size}
        for e in validated_path.iterdir()
      ]
      RETURN {"entries": entries, "count": len(entries)}

  Step 5 — encoded result returned to ToolDispatcher
    MinniSense wraps the IO result in a ToolResult:
      content = json.dumps(result_dict)
    ToolResult is always returned — MinniSense never raises to ToolDispatcher.
    On any MinniError subclass: ToolResult with error JSON content; turn continues.
```

```
  MINNI CONFIG (MinniConfig — sub-block of SkilningrConfig)

    skilningr:
      minni:
        enabled: false              # opt-in; default false
        allowed_roots:
          - "~/heretic_workspace"   # default single root; operator extends
        max_file_size_bytes: 1048576  # 1 MB; applies to both read and write
```

```
  PRIVACY INVARIANTS — MINNI

  I-1 Disabled by default
    enabled: false until operator explicitly sets enabled: true in heretic.yaml.
    If disabled: MinniSense is not mounted; ToolDispatcher has no "minni" key;
    agent receives no minni.* tool definitions.

  I-2 allowed_roots is the hard boundary
    No file operation is performed on any path that fails path_within_allowed_roots().
    The check runs BEFORE any file handle opens. There is no code path that reads or
    writes outside the allowed roots, even on a resolved symlink target outside the tree.

  I-3 No symlink target trust
    Validation is against the path as supplied (resolved), not against the symlink target.
    A symlink inside an allowed root pointing outside the root is rejected at the
    target-resolution stage. (See Step 3(c) above.)

  I-4 File size cap
    read_file: truncates at 1 MB and returns {"truncated": true}; no crash, no hang.
    write_file: refuses payloads > 1 MB with FilesizeLimitError tool_result.
    This prevents token-blowup from large file reads and rogue write payloads.

  I-5 No execute permission touched
    Minni never sets executable bits on any file it creates or modifies.
    chmod is not called; file mode is the OS default (typically 0o644 on Unix).

  I-6 No network, no subprocess
    Minni client is pure stdlib (pathlib, io). No httpx. No subprocess. No shell.
    It cannot be used to proxy a network request or spawn a process.
```

---

#### 4.12.1 Skepja terminal flow (v0.6.2)

> **Added 2026-05-08 v0.6.2 (Védis Eikleið).** The kitchen opens — fire and knives, but
> the knives are numbered and the door is locked from the outside.
> Skepja ("shaping") is HERETIC's terminal sense — it lets the agent run shell commands
> within an explicit operator-defined allowlist, in a controlled working directory, with a
> hard output cap. Each invocation is a fresh, isolated subprocess. No persistent session.
> Skepja is the highest-risk sense in v0.6.2; the allowlist is the primary defense.

```
  SKEPJA TERMINAL FLOW

  Step 1 — tool_call arrives at ToolDispatcher
    tool_call.name begins with "skepja." (e.g., "skepja.run_command")
    ToolDispatcher.dispatch() → routes to SkepjaSense.dispatch_tool_call(tool_call)

  Step 2 — command parse
    Raw command string from tool_call.arguments_json:
      { "command": "git log --oneline -10" }

    shlex.split(command) → token list
    e.g., ["git", "log", "--oneline", "-10"]

    WHY shlex.split:
      Splits on shell word boundaries without invoking a shell.
      Handles quoted arguments correctly.
      The result is passed directly to subprocess.run with shell=False,
      so no shell metacharacters (;, |, &&, >, $(...), etc.) are interpreted.
      Shell injection is structurally impossible when shell=False is used with
      a pre-split token list.

  Step 3 — allowlist check (command_allowlist_check)
    Called from skillingr/sandbox.py; shared primitive.

    def command_allowlist_check(tokens: list[str], allowlist: list[str]) -> None:
      first_token = tokens[0]
      IF first_token not in allowlist:
        RAISE CommandNotAllowedError(
          f"Command {first_token!r} is not in the Skepja allowlist")
      (Pattern matching: first token only. Full-command pattern matching is a v0.6.x extension.)

    Default allowlist: [] (empty — nothing runs until operator adds entries).
    Operator adds entries in heretic.yaml:
      skillingr.skepja.command_allowlist: ["git", "python", "ls", "cat"]

  Step 4 — subprocess.run (shell=False)
    env = {} (empty) unless skepja.inherit_env = true in config
      IF inherit_env = true: env = os.environ.copy()
      (default false — subprocess does not inherit HERETIC's environment;
      prevents leaking API keys, token env vars, or other sensitive values
      that HERETIC holds in its own process environment)

    result = subprocess.run(
      tokens,                        # pre-split by shlex.split — no shell string
      shell=False,                   # structural shell injection prevention
      cwd=working_directory,         # default ~/heretic_workspace
      capture_output=True,
      text=True,
      timeout=timeout_seconds,       # default 60; raises subprocess.TimeoutExpired
      env=env,
    )

  Step 5 — output capture and truncation
    raw_stdout = result.stdout
    raw_stderr = result.stderr
    MAX_OUTPUT = 65_536  # 64 KB

    stdout = raw_stdout[:MAX_OUTPUT]
    stderr = raw_stderr[:MAX_OUTPUT]
    stdout_truncated = len(raw_stdout) > MAX_OUTPUT
    stderr_truncated = len(raw_stderr) > MAX_OUTPUT

    RETURN {
      "returncode": result.returncode,
      "stdout": stdout,
      "stderr": stderr,
      "stdout_truncated": stdout_truncated,
      "stderr_truncated": stderr_truncated,
    }

    Truncation policy:
      Output is truncated to 64 KB to prevent token-blowup. The agent receives
      {"stdout_truncated": true} so it can inform the user or request a narrower command.
      No error is raised on truncation — it is a normal condition for long outputs.

  Step 6 — result returned
    SkepjaSense wraps result dict in ToolResult (json.dumps).
    On any SkepjaError subclass: ToolResult with error JSON content; turn continues.
```

```
  SKEPJA CONFIG (SkepjaConfig — sub-block of SkilningrConfig)

    skillingr:
      skepja:
        enabled: false                # opt-in; default false
        command_allowlist: []         # default empty — nothing runs until operator adds entries
        working_directory: "~/heretic_workspace"
        inherit_env: false            # default false — subprocess does not inherit HERETIC env
        timeout_seconds: 60           # subprocess hard timeout; raises TimeoutExpired on breach
        max_output_bytes: 65536       # 64 KB output cap; applied independently to stdout and stderr
```

```
  CROSS-PLATFORM SEMANTICS — WINDOWS VS UNIX

  shlex.split behavior:
    On Unix: shlex.split("git log --oneline") → ["git", "log", "--oneline"]
    On Windows: shlex.split behaves identically for simple commands because shlex
      uses POSIX mode by default. For Windows-specific quoting (e.g., paths with
      backslashes), the operator should use forward slashes in command strings.
    HERETIC passes the split token list to subprocess.run with shell=False on all
    platforms — the OS selects the executable by name lookup on PATH.

  Executable resolution:
    On Unix: first token "git" → resolved via PATH lookup; subprocess.run finds /usr/bin/git.
    On Windows: first token "git" → resolved via PATH; typically C:\Program Files\Git\cmd\git.exe.
    The allowlist checks the first token string only (e.g., "git"), not the full resolved path.
    This means "git" in the allowlist permits git regardless of its installation path.

  Working directory:
    ~/heretic_workspace expands via Path.expanduser() which is cross-platform.
    On Windows: ~ expands to C:\Users\<username>.
    On Unix: ~ expands to /home/<username> or /Users/<username>.

  No shell=True anywhere:
    subprocess.run is always called with shell=False on all platforms.
    This means no cmd.exe invocation on Windows, no /bin/sh on Unix.
    Shell built-ins (cd, echo, etc.) are NOT available to the agent via Skepja.
    If the operator needs them, they must wrap them in a script and allowlist the script.

  Timeout:
    subprocess.TimeoutExpired is raised after timeout_seconds on all platforms.
    HERETIC catches this and returns a tool_result error with {"error": "skepja_timeout"}.
    The subprocess is killed (process.kill()) after timeout on both Unix and Windows.
```

```
  SKEPJA FAILURE MODES

  F-1: Command not in allowlist
    Cause: agent calls skepja.run_command with a first-token not in command_allowlist.
    SkepjaSense raises CommandNotAllowedError (from sandbox.py).
    tool_result: {"error": "command_not_allowed",
                  "command": "<first token>",
                  "hint": "operator must add this command to skillingr.skepja.command_allowlist"}
    Turn continues. Agent may explain the restriction.

  F-2: Subprocess timeout
    Cause: command runs longer than timeout_seconds (default 60).
    subprocess.TimeoutExpired is caught by SkepjaSense.
    tool_result: {"error": "skepja_timeout",
                  "timeout_seconds": <configured value>,
                  "hint": "raise skillingr.skepja.timeout_seconds or use a faster command"}
    Turn continues.

  F-3: Working directory not found
    Cause: working_directory path does not exist or is outside allowed scope.
    FileNotFoundError or NotADirectoryError caught by SkepjaSense.
    tool_result: {"error": "skepja_bad_working_dir",
                  "working_directory": "<configured path>"}
    Turn continues.

  F-4: Non-zero returncode
    Cause: command exits with non-zero status (e.g., git command fails, script errors).
    This is NOT an error at the Skepja level — it is a normal command result.
    tool_result includes returncode and stderr. Agent interprets and responds accordingly.
    No exception raised; no SkepjaError. The agent sees the real output.

  F-5: Output oversize (truncated)
    Cause: stdout or stderr exceeds 64 KB.
    Output is silently truncated; {"stdout_truncated": true} or {"stderr_truncated": true}
    flags are set in the result. No error; no exception. Turn continues.
```

---

#### 4.12.2 Leið HTTP fetch flow (v0.6.2)

> **Added 2026-05-08 v0.6.2 (Védis Eikleið).** The road opens — but only to destinations
> the operator has named. Leið ("path/way") is HERETIC's HTTP fetch sense — it lets the
> agent retrieve text content from URLs matching an operator-defined pattern allowlist.
> This is a read-only, stateless fetch: no cookies, no JS, no POST, no playwright.
> Headless browser (Leið via playwright) is deferred to v0.6.2.1.
> Transport: httpx (already a HERETIC dependency). No new external library added.

```
  LEIÐ HTTP FETCH FLOW

  Step 1 — tool_call arrives at ToolDispatcher
    tool_call.name begins with "leid." (e.g., "leid.fetch_url")
    ToolDispatcher.dispatch() → routes to LeidSense.dispatch_tool_call(tool_call)

  Step 2 — URL parse and allowlist match
    URL from tool_call.arguments_json:
      { "url": "https://docs.python.org/3/library/pathlib.html" }

    Called from skillingr/sandbox.py:

    def url_allowlist_match(url: str, patterns: list[str]) -> None:
      parsed = urllib.parse.urlparse(url)
      IF parsed.scheme not in ("http", "https"):
        RAISE UrlNotAllowedError("Only http and https schemes are permitted")
      FOR pattern in patterns:
        IF fnmatch.fnmatch(url, pattern):
          RETURN     # URL is allowed
      RAISE UrlNotAllowedError(
        f"URL {url!r} does not match any pattern in leid.url_allowlist_patterns")

    Default patterns: [] (empty — nothing fetchable until operator adds patterns).
    Operator adds in heretic.yaml:
      skillingr.leid.url_allowlist_patterns:
        - "https://docs.python.org/*"
        - "https://en.wikipedia.org/wiki/*"
        (or "*" for unrestricted — a warning is logged when wildcard is present)

    HTTPS preference:
      HTTPS URLs pass silently.
      HTTP URLs (scheme = "http") are allowed but trigger:
        log.warning("Leið: fetching plain HTTP URL — no transport encryption: <url>")
      This is advisory, not blocking. Operators who need HTTP (e.g., local dev servers)
      can allowlist http:// patterns; they receive the warning as intended.

  Step 3 — httpx GET with limits
    async with httpx.AsyncClient(
      follow_redirects=True,
      max_redirects=5,              # default; operator can override
      timeout=30.0,                 # default 30s
      headers={"User-Agent": "HERETIC/0.6.2 (heretic-summoning-circle)"},
      cookies=None,                 # no cookie jar — stateless fetch
    ) as client:
      response = await client.get(url)

    No cookies: httpx.AsyncClient is constructed without a CookieJar; cookies
      sent in Set-Cookie response headers are not stored and not sent on subsequent requests.
    No JS: no browser engine, no DOM, no event loop. Pure HTTP text response.
    No POST in v0.6.2: only GET. POST requires explicit leid.post_url tool (deferred to v0.6.x).
    Redirect cap: max 5 redirects. A redirect chain longer than 5 raises TooManyRedirects.
    Timeout: 30s end-to-end (connection + response). httpx.TimeoutException raised on breach.

  Step 4 — response body size cap
    NOTE (2026-05-09 v0.7.1): The body-read pattern shown below is HISTORICAL.
    The shipped v0.6.2 code (post audit cleanup at 6a027f3) does NOT silently
    truncate — it raises LeidResponseTooLargeError on cap breach. v0.7.1 then
    replaces the buffer-then-check with a streaming abort. The canonical flow
    is now §4.12.2.1 — Streaming body-read (Straumr á Leið). Read this Step 4
    only as a record of the very-first sketch.

    MAX_RESPONSE = 1_048_576   # 1 MB  (configurable)
    [historical sketch] body = await response.aread()
                       IF len(body) > MAX_RESPONSE:
                         body = body[:MAX_RESPONSE]; truncated = True
                       ELSE:
                         truncated = False

    The cap prevents a large response (e.g., a 50 MB HTML page) from consuming
    agent context. v0.7.1 onwards: cap is enforced by streaming abort; the agent
    receives a structured LeidResponseTooLargeError ToolResult instead of partial
    content. See §4.12.2.1.

  Step 5 — text extraction (leid.fetch_url returns raw decoded text)
    text = body.decode(response.encoding or "utf-8", errors="replace")

    leid.fetch_url returns the raw decoded text (HTML or plain text).
    leid.extract_text (second tool) runs html.parser stripping:

    import html.parser

    class _TagStripper(html.parser.HTMLParser):
      def __init__(self):
        super().__init__()
        self._parts = []
      def handle_data(self, data):
        self._parts.append(data)
      def get_text(self) -> str:
        return " ".join(self._parts)

    WHY html.parser only (no lxml, no BeautifulSoup):
      html.parser is stdlib; zero new dependencies.
      It strips tags and returns text content — sufficient for most documentation pages.
      Full HTML parsing with CSS selector queries deferred to v0.6.2.1 (headless browser).
      No JS execution — pages that render content dynamically via JS return empty text.
      This is a known limitation, documented explicitly.

  Step 6 — result returned
    LeidSense wraps result dict in ToolResult:
      leid.fetch_url result:
        { "url": url, "status_code": N, "content_type": "text/html; charset=utf-8",
          "text": "<decoded body>", "truncated": bool }
      leid.extract_text result:
        { "url": url, "text": "<stripped plain text>", "truncated": bool }
    ToolResult always returned — LeidSense never raises to ToolDispatcher.
    On any LeidError: error JSON tool_result; turn continues.
```

```
  LEIÐ CONFIG (LeidConfig — sub-block of SkilningrConfig)

    skillingr:
      leid:
        enabled: false                    # opt-in; default false
        url_allowlist_patterns: []        # default empty — nothing fetchable until operator adds
        max_response_bytes: 1048576       # 1 MB response cap
        timeout_seconds: 30              # end-to-end HTTP timeout
        max_redirects: 5                 # redirect chain cap
        # Note: user_agent is not configurable; always "HERETIC/0.6.2 (heretic-summoning-circle)"
```

```
  LEIÐ FAILURE MODES

  F-1: URL not in allowlist
    Cause: agent calls leid.fetch_url with URL not matching any allowlist pattern.
    LeidSense raises UrlNotAllowedError (from sandbox.py).
    tool_result: {"error": "url_not_allowed",
                  "url": "<url>",
                  "hint": "operator must add a pattern matching this URL to
                           skillingr.leid.url_allowlist_patterns"}
    Turn continues.

  F-2: HTTP timeout
    Cause: server does not respond within timeout_seconds (default 30s).
    httpx.TimeoutException caught by LeidSense.
    tool_result: {"error": "leid_timeout",
                  "url": "<url>",
                  "timeout_seconds": <configured value>}
    Turn continues.

  F-3: Too many redirects
    Cause: redirect chain exceeds max_redirects (default 5).
    httpx.TooManyRedirects caught by LeidSense.
    tool_result: {"error": "leid_too_many_redirects",
                  "url": "<url>",
                  "max_redirects": <configured value>}
    Turn continues.

  F-4: HTTP error status (4xx / 5xx)
    Cause: server returns a non-2xx response (e.g., 404 Not Found, 403 Forbidden, 500).
    This is NOT a Leið error — the response is returned with status_code in the tool_result.
    tool_result: {"url": "<url>", "status_code": 404, "text": "<body if any>", ...}
    Agent interprets the status code and responds accordingly.

  F-5: Connection error (host unreachable, DNS failure)
    Cause: httpx.ConnectError — DNS resolution fails, host is down, network unreachable.
    tool_result: {"error": "leid_connect_error",
                  "url": "<url>",
                  "detail": "<exception message>"}
    Turn continues.

  F-6: Response body oversize
    Cause: response body exceeds max_response_bytes (default 1 MB).
    Behaviour history:
      v0.6.2 first sketch — silently truncated (this section's old text).
      v0.6.2 shipped (6a027f3) — full-buffer-then-check; raises LeidResponseTooLargeError;
        no partial content returned to the agent.
      v0.7.1 (Straumr á Leið) — true streaming abort via aiter_bytes; same exception
        class raised mid-stream as soon as accumulator exceeds the cap; connection
        closed during stack unwind. See §4.12.2.1 for the full streaming flow.
    LeidSense catches LeidResponseTooLargeError and returns:
      tool_result: {"error": "leid_response_too_large",
                    "url": "<url>",
                    "max_response_bytes": <cap>}
    Turn continues.

  NOTE: No cookie leakage is possible. LeidSense uses a fresh httpx.AsyncClient per call
    with no persistent CookieJar. Each fetch_url call is fully stateless.
```

---

#### 4.12.2.1 Leið streaming body-read (Straumr á Leið — v0.7.1)

> **Added 2026-05-09 v0.7.1 (Védis Eikleið).** *Straumr á Leið* — the current on the road.
> Replaces the v0.6.2 buffer-then-check pattern with a true streaming abort.
> The body no longer needs to wait until the cup is full to know if it can be lifted.
> Closes audit-deferred N-2 from `AUDIT_v0.6.2_MORE_SENSES.md`.

```
  STRAUMR Á LEIÐ — STREAMING BODY-READ

  v0.6.2 sketch (now historical):
    response = await client.get(url)         # entire body lands in memory
    if len(response.content) > cap:
        raise LeidResponseTooLargeError(...)  # checked AFTER full intake
    body = response.content.decode(...)

    Defect: a 500 MB response is fully transferred and held before the cap raises.

  v0.7.1 streaming pattern:
    async with httpx.AsyncClient(...) as client:
      async with client.stream("GET", url) as response:
        # Pre-cap on Content-Length when present (saves the first chunk too):
        cl_header = response.headers.get("content-length")
        if cl_header is not None:
          try:
            if int(cl_header) > max_response_bytes:
              raise LeidResponseTooLargeError(...)
          except ValueError:
            pass   # malformed header — ignore, fall through to chunk loop

        # Status-code check uses the response object before any body iteration:
        if response.status_code >= 400:
          # Bound the error-text peek so a giant 4xx body cannot blow memory:
          error_acc = bytearray()
          async for chunk in response.aiter_bytes(4096):
            error_acc.extend(chunk)
            if len(error_acc) >= 500:
              break
          raise LeidHttpError(f"HTTP {status} from {url}; body[:500]={error_acc[:500]!r}")

        # Streaming accumulator:
        acc = bytearray()
        async for chunk in response.aiter_bytes(65536):
          acc.extend(chunk)
          if len(acc) > max_response_bytes:
            raise LeidResponseTooLargeError(
              f"Response from {url} exceeds max_response_bytes={cap}; "
              f"streamed {len(acc)} bytes before abort"
            )
        body = bytes(acc).decode("utf-8", errors="replace")
        size_bytes = len(acc)

  Position of the raise:
    - The raise happens INSIDE the `async with client.stream(...)` block.
    - On `raise`, Python unwinds the stack: the inner `__aexit__` of the
      stream context cancels the response and CLOSES the connection.
    - No further bytes are read from the network. The remote endpoint is
      not asked to send what it would have sent next.

  Memory bound at moment of raise:
    Worst case: max_response_bytes + chunk_size (because the chunk that
    pushes us over the cap is appended before the comparison).
    For default chunk_size=65536 and max_response_bytes=1_048_576, the
    bound is 1_114_112 bytes (~1.06 MB) — bounded, predictable, well below
    the unbounded 500 MB of the v0.6.2 worst case.

  Invariants preserved:
    - Allowlist gate runs BEFORE httpx.stream() opens
    - HTTPS-only check runs in the same gate
    - No cookies (httpx.AsyncClient configured without cookie jar)
    - GET only (client.stream("GET", url))
    - 4xx/5xx status raised as LeidHttpError before body accumulation
    - LeidResponseTooLargeError class shape unchanged; agent contract unchanged
    - All other LeidError subclasses still rise from their respective httpx exceptions
    - extract_text inherits streaming for free (it routes through fetch_url)

  Why bytearray, not list-of-bytes:
    - O(1) amortised extend
    - Single contiguous buffer at decode time (no per-chunk copy chain)
    - bytes(acc) is a single materialisation only on the success path
    - No hidden per-chunk Python object overhead
```

---

#### 4.12.2.2 Leið browser-render fetch (Opið Vef — v0.8.0)

> **Added 2026-05-10 v0.8.0 (Védis Eikleið).** *Opið Vef* — the open web. The body's
> path outward gains a second pair of eyes: a headless Chromium browser via Playwright
> that runs the page's scripts before reading the rendered DOM. Additive over §4.12.2 /
> §4.12.2.1 — the v0.7.1 streaming-httpx flow is unchanged and untouched. The new
> sub-faculty answers `leid.render_url`; the existing `leid.fetch_url` and
> `leid.extract_text` still answer through the v0.7.1 streaming path.

```
  OPIÐ VEF — BROWSER-RENDER FETCH FLOW (v0.8.0)

  Entry point: agent calls leid.render_url(url) via OpenAI tool_call.

  Stage 1 — Sense routing (LeidSense._route)
    tool_name == "leid.render_url"
        → dispatched to PlaywrightLeidClient.render_url(url)
        (NOT to LeidClient.fetch_url; the v0.7.1 streaming path is untouched)

  Stage 2 — URL validation (PlaywrightLeidClient._validate_url)
    sandbox.url_matches_allowlist(url, config.url_allowlist_patterns)
    HTTPS-only check (allow_http: false rejects http://)
    On rejection → UrlNotAllowedError raised; NO browser process spawned.
    This is invariant B-1 — the gate runs before any Playwright import or launch.

  Stage 3 — Playwright availability check
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise LeidPlaywrightUnavailableError("playwright not installed; ...")

    Failure here surfaces as SENSE_CONTRACTS code EXTERNAL_APP_UNAVAILABLE
    to the agent, but ONLY for leid.render_url calls. The httpx tools
    (fetch_url, extract_text) continue to dispatch normally and require
    no browser dep.

  Stage 4 — Per-call browser lifecycle (D-5: launch-per-call)
    pw = await async_playwright().start()
    try:
        try:
            browser = await pw.chromium.launch(headless=True)   # B-4: always headless
        except Exception as exc:
            raise LeidPlaywrightUnavailableError(
                "chromium binary missing; run `playwright install chromium`"
            ) from exc
        try:
            context = await browser.new_context(
                user_agent=config.user_agent,                  # B-8
            )
            try:
                page = await context.new_page()
                response = await page.goto(
                    url,
                    wait_until=config.browser_load_state,      # default "domcontentloaded" (B-5)
                    timeout=config.browser_navigation_timeout_seconds * 1000,
                )
                # Stage 5 — Status check
                if response is not None and response.status >= 400:
                    raise LeidHttpError(
                        f"HTTP {response.status} from {url}"
                    )
                # Stage 6 — Pre-cap on rendered HTML size
                html = await page.content()
                rendered_size = len(html.encode("utf-8"))
                if rendered_size > config.max_response_bytes:
                    raise LeidResponseTooLargeError(
                        f"Rendered HTML from {url} is {rendered_size} bytes, "
                        f"exceeds max_response_bytes={config.max_response_bytes}"
                    )
                # Stage 7 — Text + title extraction (re-uses stdlib HTMLParser)
                text, title = _extract_text_from_html(html)
                final_url = page.url
                source_size = rendered_size
            finally:
                await context.close()                          # B-3: cookies discarded
        finally:
            await browser.close()
    finally:
        await pw.stop()                                        # B-7: full cleanup

    return {
        "url": validated_url,
        "final_url": final_url,
        "text": text,
        "title": title,
        "source_size_bytes": source_size,
    }

  Failure mapping:
    UrlNotAllowedError              → PERMISSION_DENIED
    LeidPlaywrightUnavailableError  → EXTERNAL_APP_UNAVAILABLE (NEW v0.8.0)
    LeidTimeoutError                → SENSE_TIMEOUT  (from page.goto TimeoutError)
    LeidConnectionError             → EXTERNAL_APP_UNAVAILABLE (network)
    LeidHttpError                   → SENSE_INTERNAL_ERROR (HTTP 4xx/5xx)
    LeidResponseTooLargeError       → INVALID_ARGUMENTS (rendered HTML > cap)

  Memory bound at moment of pre-cap raise:
    page.content() materialises the rendered DOM as a single string. If that
    string's UTF-8 encoded length exceeds max_response_bytes, the raise occurs
    AFTER the string has been built — meaning the worst-case memory at the
    moment of refusal is approximately:
        len(html.encode("utf-8")) + Python string overhead
    This is intentional: Playwright does not expose a streaming DOM read.
    Operators who need true streaming must use leid.fetch_url instead, which
    has byte-level abort via aiter_bytes (§4.12.2.1).

    The cap is NOT a memory bound for the rendered path; it is a token-budget
    bound — it prevents the agent from receiving an enormous text payload,
    not from the browser materialising a moderately-large DOM. This is a
    documented trade-off, not a defect.

  State persistence between calls:
    NONE. Each call:
      - launches its own pw runtime
      - launches its own browser
      - opens its own browser context (fresh cookie jar, fresh localStorage)
      - opens its own page
      - tears all four down before returning

    No state of any kind crosses call boundaries. This is invariant B-3.

  Cost vs the httpx path:
    - httpx fetch_url:    ~50–500 ms (single HTTPS round trip)
    - render_url:         ~500–3000 ms (browser cold start + page render)

    The agent should prefer fetch_url / extract_text for static pages and
    use render_url only when the page is known to be a JS-rendered SPA.
    HERETIC does not auto-detect; the agent chooses per call.

  Invariants honoured:
    - L-1 / B-1: allowlist gate runs before any Playwright operation
    - L-2:        empty allowlist still means no URL fetchable via render_url
    - L-3:        sense disabled by default (config.enabled: false)
    - L-4 / B-9:  HTTPS-only by default; http:// rejected unless allow_http: true
    - L-5 / B-3:  no cookies persist (fresh context per call)
    - L-6:        EXPLICITLY OVERRIDDEN — render_url DOES execute JavaScript;
                  this is the entire point of the new sub-faculty. The page's
                  scripts run during render. HERETIC injects no script of its
                  own (B-10) but allows the page's scripts to run on the page.
    - L-7:        size cap honoured at the rendered-HTML pre-cap (B-6)
    - L-8:        redirects followed naturally by Playwright; final_url returned
    - L-9:        wildcard "*" warning still applies (cross-tool)

  License posture:
    - Playwright (Microsoft):    Apache-2.0           [permissive]
    - Chromium binary:           BSD-style + LGPL parts; downloaded as a
                                 runtime artifact via `playwright install
                                 chromium`, not bundled in HERETIC's wheel.
    THIRD_PARTY_NOTICES.md updated at v0.8.0 to reflect the Playwright
    dependency under [browser] extra.
```

---

#### 4.12.2.3 Leið browser-screenshot fetch (Mynd af Vegferð — v0.8.1)

> **Added 2026-05-10 v0.8.1 (Védis Eikleið).** *Mynd af Vegferð* — image of the
> journey. Adds `leid.screenshot` as the second tool on the Opið Vef sub-faculty.
> Same launch-per-call browser lifecycle as `render_url` (§4.12.2.2); same
> B-1..B-10 invariants. One new invariant: **B-11** — the size cap applies to
> the **raw PNG bytes BEFORE base64 encoding**. The `render_url` flow at §4.12.2.2
> is byte-untouched at v0.8.1.

```
  MYND AF VEGFERÐ — BROWSER-SCREENSHOT FETCH FLOW (v0.8.1)

  Entry point: agent calls leid.screenshot(url) via OpenAI tool_call.

  Stage 1 — Sense routing (LeidSense._route)
    tool_name == "leid.screenshot"
        → dispatched to PlaywrightLeidClient.screenshot(url)
        (NOT to LeidClient; NOT to PlaywrightLeidClient.render_url)

  Stage 2 — URL validation (PlaywrightLeidClient._validate_url)
    Same gate as render_url: allowlist + HTTPS-only.
    On rejection → UrlNotAllowedError; NO browser process spawned. (B-1)

  Stage 3 — Playwright availability check
    Same as render_url. ImportError or chromium.launch failure →
    LeidPlaywrightUnavailableError → EXTERNAL_APP_UNAVAILABLE. (B-2)

  Stage 4 — Per-call browser lifecycle (D-22, identical to render_url)
    pw      = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)        # B-4
    context = await browser.new_context(user_agent=...)      # B-3, B-8
    page    = await context.new_page()
    response = await page.goto(
        url,
        wait_until=config.browser_load_state,                # B-5
        timeout=config.browser_navigation_timeout_seconds * 1000,
    )

    Failure modes during navigation: identical mapping to render_url
    (TimeoutError → LeidTimeoutError; PlaywrightError → LeidConnectionError;
    response.status >= 400 → LeidHttpError).

  Stage 5 — Screenshot capture
    png_bytes = await page.screenshot(
        full_page=config.browser_screenshot_full_page,       # D-20
        type="png",                                          # D-16
    )
    # png_bytes is `bytes`, the raw PNG file content.

  Stage 6 — Pre-cap on raw PNG byte size (B-11, NEW)
    if len(png_bytes) > config.max_response_bytes:
        raise LeidResponseTooLargeError(...)
    # Cap is honest about CONTENT size (raw PNG bytes), not transport
    # size (base64 expands by ~33%). Operators set max_response_bytes to
    # cap the actual page-content payload.

  Stage 7 — Base64 encoding (D-17)
    image_base64 = base64.b64encode(png_bytes).decode("ascii")
    # ASCII-decode is safe because base64 output is by definition ASCII-only.

  Stage 8 — Resource cleanup (B-7, identical to render_url)
    finally:
        await context.close()
        await browser.close()
        await pw.stop()

    return {
        "url": validated_url,
        "final_url": page.url,
        "image_base64": image_base64,
        "image_format": "png",
        "size_bytes": len(png_bytes),
        "full_page": config.browser_screenshot_full_page,
    }

  B-11 placement (the new invariant):
    The cap check happens AFTER page.screenshot() returns the bytes (we
    cannot ask Playwright to abort mid-encode), but BEFORE the base64
    encoding step. This means at the moment of the raise, memory holds:
        - the raw PNG bytes (just received)
        - no base64 encoding yet allocated
    The base64 expansion is avoided when the cap fires. This is the
    same disposition as B-6 for render_url: the body knows what is too
    heavy before it asks anyone else to carry it.

  Memory bound at moment of B-11 raise:
    Worst case: len(png_bytes) where png_bytes was just returned by
    page.screenshot(). Playwright does not stream screenshot output;
    the entire PNG is materialised before page.screenshot() returns.
    For an oversized capture this is the same memory-bound trade-off
    as render_url's content() — operators who need streaming abort for
    page content use leid.fetch_url; operators using leid.screenshot
    accept the materialisation cost in exchange for the visual capture
    capability that no streaming-friendly alternative offers.

  State persistence between calls:
    NONE. Each call gets its own pw runtime, browser, context, page —
    same as render_url. B-3 still holds: cookies do not survive the
    call.

  Cost vs render_url:
    render_url:    page.goto + page.content (HTML string)
    screenshot:    page.goto + page.screenshot (PNG bytes)
    The two costs are similar. The base64 encoding adds O(n) post-
    processing work but no additional Chromium operation.

  Invariants honoured:
    - B-1 / B-2 / B-3 / B-4 / B-5 / B-7 / B-8 / B-9 / B-10:
                  identical to render_url; full inheritance
    - B-6:        N/A — render_url's HTML cap; screenshot uses B-11 instead
    - B-11 NEW:   raw PNG bytes <= max_response_bytes (pre-base64)

  License posture:
    No new dependencies introduced at v0.8.1. base64 is stdlib. The
    Playwright + Chromium licensing established at v0.8.0 in
    THIRD_PARTY_NOTICES.md remains the only browser-mode dependency.
```

---

#### 4.12.2.4 Leið stateful sessions + click (Innan Hurðar — v0.8.2)

> **Added 2026-05-10 v0.8.2 (Védis Eikleið).** *Innan Hurðar* — inside the door.
> Adds stateful browser sessions: open_session keeps a page alive across multiple
> tool calls. The agent can then click elements on the live page; eventually it
> closes the session, releasing all resources. New `BrowserSessionManager` owns
> the open sessions, enforces concurrency limits, and lazily evicts expired
> sessions on every call. Adds 7 new B-invariants (B-12..B-18) plus the M-1
> closure (page.content + page.screenshot exception typing) deferred from v0.8.1.

```
  INNAN HURÐAR — STATEFUL SESSION + CLICK FLOW (v0.8.2)

  Lifecycle has FOUR distinct phases keyed by the session_id.

  Phase A — open_session(url) → {session_id, final_url, title}
    LeidSense._route → PlaywrightLeidClient.open_session(url)
        ↓
    _validate_url           ── B-12: gate runs BEFORE any browser launch.
                                Same gate as render_url / screenshot.
        ↓
    BrowserSessionManager._evict_expired_sessions()    ── B-15
        ↓ (lazy eviction)
    if len(_sessions) >= browser_max_concurrent_sessions:
        raise LeidSessionLimitError                    ── B-13: explicit refusal,
                                                          no silent eviction.
        ↓
    pw      = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)  ── B-4 inherited
    context = await browser.new_context(user_agent=...)── B-8 inherited
    page    = await context.new_page()
    response = await page.goto(url,
                               wait_until=browser_load_state,
                               timeout=browser_navigation_timeout_seconds*1000)
        ↓ (failures here cleanup pw/browser/context, do NOT register session)
    if response.status >= 400: raise LeidHttpError
        ↓
    session = _LeidSession(
        session_id = "leid-" + uuid4().hex,            ── D-26
        pw, browser, context, page,
        created_at = monotonic, last_activity_at = monotonic,
    )
    _sessions[session_id] = session                    ── B-14: independent quartet
        ↓
    return {session_id, final_url=page.url, title=await page.title()}

  Phase B — session_status(session_id) → metadata (non-mutating in spirit)
    _evict_expired_sessions()                          ── B-15
    session = _sessions.get(session_id)
    if session is None: raise LeidSessionExpiredError  ── B-16
    session.last_activity_at = monotonic               ── B-17 (status counts as
                                                          activity)
    return {
        state: "alive",
        url: page.url,
        title: await page.title(),
        opened_at: created_at, last_activity_at,
        age_seconds, idle_seconds,
    }

  Phase C — click(session_id, selector) → result
    _evict_expired_sessions()
    session = _sessions.get(session_id) or raise LeidSessionExpiredError
        ↓
    locator = session.page.locator(selector).first     ── D-41: first match
    try:
        await locator.click(
            timeout = browser_click_timeout_seconds * 1000,  ── D-42
        )
    except PlaywrightTimeoutError:
        raise LeidClickElementNotFoundError(           ── D-43: agent-specific
            f"Selector {selector!r} matched no element after timeout"
        )
    except PlaywrightError as exc:
        raise LeidConnectionError(                     ── D-43: network branch
            f"Click failed at network layer: {exc}"
        )
        ↓
    session.last_activity_at = monotonic               ── B-17
    try: title = await session.page.title()            ── D-49: defensive
    except: title = None
    return {selector, clicked: true, current_url: page.url, current_title: title}

  Phase D — close_session(session_id) → idempotent
    session = _sessions.pop(session_id, None)          ── B-18: pop-then-clean
                                                          (so concurrent
                                                          eviction cannot
                                                          double-clean)
    if session is None:
        return {session_id, closed: false}             ── B-18 idempotent
        ↓
    try: await session.context.close()                 ── B-7-style cleanup
    except: log warning
    try: await session.browser.close()
    except: log warning
    try: await session.pw.stop()
    except: log warning
        ↓
    return {session_id, closed: true}

  EVICTION (lazy, on every call):
    For each session in _sessions:
        idle = now - session.last_activity_at
        age  = now - session.created_at
        if idle > browser_session_idle_timeout_seconds:
            evict (same cleanup as close_session, log WARNING)
        elif age > browser_session_max_lifetime_seconds:
            evict
    A session evicted between the agent's last call and the next one becomes
    a LeidSessionExpiredError → SENSE_UNAVAILABLE on the next reference.

  M-1 CLOSURE (deferred from AUDIT_v0.8.1 NIT M-1):
    Three additional Page.* call sites gain explicit exception typing this
    milestone:
      render_url:  await page.content()    → wrap with try/except mapping
                                              PlaywrightError →
                                              LeidConnectionError
      screenshot:  await page.screenshot() → same wrap, same mapping
      click:       await locator.click()   → wrap with try/except mapping
                                              PlaywrightTimeoutError →
                                              LeidClickElementNotFoundError;
                                              other PlaywrightError →
                                              LeidConnectionError
    The fourth site (page.goto) was already correctly typed in v0.8.0.
    All four Page.* network-level failure modes now surface to the agent
    with the same precision httpx failures already had.

  Cookie state across the lifecycle:
    Within a single session: cookies persist (that is what a session IS).
    Across sessions:         cookies do NOT persist. Each new_context is
                             fresh. close_session discards all session-
                             local cookies. B-3 holds at the session
                             boundary, not at the call boundary.

  Resource ownership:
    Each session owns its OWN (pw, browser, context, page) quartet (B-14).
    Sessions are independent — closing one does not affect any other.
    Manager owns the dict; sessions own their resources.

  Concurrency posture:
    BrowserSessionManager uses asyncio.Lock around the dict mutations
    (D-35). Concurrent open_session calls are serialised at the cap-check
    boundary so the cap is honoured exactly. Concurrent calls on different
    session_ids do NOT serialise (sessions are independent).

  Cost vs the stateless tools:
    open_session:    same as render_url cold start (~500-3000 ms)
    session_status:  trivial (~microseconds + page.title() call)
    click:           varies by element + browser_click_timeout_seconds cap
    close_session:   ~hundreds of ms (browser teardown is not free)

  License posture:
    No new dependencies. uuid + asyncio are stdlib. Playwright + Chromium
    licensing already established at v0.8.0.
```

---

#### 4.12.2.5 Leið in-session type (Innan Hurðar extension — v0.8.2.1)

> **Added 2026-05-10 v0.8.2.1 (Védis Eikleið).** Unnamed extension of Innan
> Hurðar — adds `leid.type` as the second half of the interactive gesture
> begun with click. Mirrors the click flow exactly; uses Playwright's
> `locator.fill()` (not `type()`, which is keystroke-by-keystroke). One new
> B-invariant (B-19); one new error class (`LeidTypeElementNotFoundError`);
> one new tool — same disposition as v0.8.2.

```
  LEIÐ IN-SESSION TYPE FLOW (v0.8.2.1)

  Entry point: agent calls leid.type(session_id, selector, text).

  Stage 1 — Sense routing
    LeidSense._route → "leid.type" → PlaywrightLeidClient.type(...)

  Stage 2 — Lazy eviction (B-15 inherited)
    manager.evict_expired_sessions()

  Stage 3 — Session resolution (B-16 inherited)
    session = manager.get_session(session_id)
        ↓
    raises LeidSessionExpiredError if unknown / evicted

  Stage 4 — Locate + fill
    locator = session.page.locator(selector).first    ── D-56 (first match)
    try:
        await locator.fill(
            text,                                     ── the agent's text
            timeout = browser_click_timeout_seconds * 1000,  ── D-54 (reuses click cap)
        )
    except PlaywrightTimeoutError:
        raise LeidTypeElementNotFoundError(           ── D-55 (selector wrong)
            f"Selector {selector!r} matched no actionable input "
            f"in session {session_id!r}"
        )
    except PlaywrightError as exc:
        raise LeidConnectionError(                    ── network/page issue
            f"type({selector!r}) failed at the browser level: {exc}"
        )

    Note: Playwright's locator.fill() does:
      1. wait for actionability checks (visible, enabled, editable)
      2. focus the element
      3. clear the existing value (if any)
      4. set the new value to `text`
      5. dispatch an `input` event
    This is the canonical "set this field's value" primitive — what
    agents almost always want for "type X into Y." Keystroke-by-keystroke
    simulation (page.type with delay) is a rarely-needed v0.8.x add-on.

  Stage 5 — Activity update (B-17 inherited / B-19)
    session.mark_activity()

  Stage 6 — Post-fill state read (D-57)
    current_url = session.page.url
    try:
        current_title = await session.page.title()
    except: current_title = None        ── D-49 (defensive)

    return {
        "selector": selector,
        "typed": True,
        "current_url": current_url,
        "current_title": current_title,
    }

  Inheritance from prior invariants:
    B-2 / B-3 / B-4 / B-7 / B-8 / B-9 / B-10 — all inherited via the
                                                shared session quartet
    B-15  — lazy eviction at call start
    B-16  — unknown session_id raises LeidSessionExpiredError
    B-17  — activity update after success
    B-19  — NEW: type respects same session/cap/timeout discipline as click

  Error code mapping:
    LeidSessionExpiredError       → SENSE_UNAVAILABLE
    LeidTypeElementNotFoundError  → INVALID_ARGUMENTS  (NEW)
    LeidConnectionError           → EXTERNAL_APP_UNAVAILABLE

  Cost vs click:
    type:    page.locator + locator.fill (clears + focuses + sets + input event)
    click:   page.locator + locator.first.click
    The two are roughly identical in cost. Playwright's actionability checks
    dominate either way.

  License posture:
    No new dependencies. Same Playwright + Chromium establishment from v0.8.0.
```

---

#### 4.12.2.6 Leið in-session navigation (Innan Hurðar extension — v0.8.2.2)

> **Added 2026-05-10 v0.8.2.2 (Védis Eikleið).** Unnamed extension of Innan
> Hurðar — adds `leid.navigate` for in-session URL changes. The session keeps
> its identity, cookies, and localStorage; only the page's URL changes.
> Reuses the existing browser quartet (no new launch). One new B-invariant
> (B-20); no new error classes (reuses LeidTimeoutError / LeidConnectionError
> / LeidHttpError / LeidSessionExpiredError).

```
  LEIÐ IN-SESSION NAVIGATE FLOW (v0.8.2.2)

  Entry point: agent calls leid.navigate(session_id, url).

  Stage 1 — Sense routing
    LeidSense._route → "leid.navigate" → PlaywrightLeidClient.navigate(...)

  Stage 2 — URL validation FIRST (B-12 / B-20)
    normalised_url = self._validate_url(url)
        ↓
    raises UrlNotAllowedError before session_id is even resolved.
    Order matters: an invalid URL should fail loudly even if the session
    is also gone — the operator's allowlist gate is unconditional.

  Stage 3 — Lazy eviction (B-15 inherited)
    manager.evict_expired_sessions()

  Stage 4 — Session resolution (B-16 inherited)
    session = manager.get_session(session_id)
        ↓
    raises LeidSessionExpiredError if unknown / evicted

  Stage 5 — Capture previous URL (D-64)
    previous_url = session.page.url
        ↓
    Snapshot BEFORE the navigation so we have a coherent record even
    if the goto succeeds and changes session.page.url.

  Stage 6 — Navigate (D-60, B-5 inherited)
    try:
        response = await session.page.goto(
            normalised_url,
            wait_until = config.browser_load_state,         ── reused (D-65)
            timeout    = config.browser_navigation_timeout_seconds * 1000,
        )
    except PlaywrightTimeoutError:
        raise LeidTimeoutError(...)                         ── B-5 inherited
    except PlaywrightError:
        raise LeidConnectionError(...)                      ── D-66

  Stage 7 — Status check
    if response is not None and response.status >= 400:
        raise LeidHttpError(...)                            ── D-66

  Stage 8 — Activity update (B-17 / B-20)
    session.mark_activity()

  Stage 9 — Read post-navigate state
    final_url = session.page.url   (may differ from normalised_url
                                     if the page client-side-redirected)
    try: title = await session.page.title()
    except: title = None                                    ── D-49 defensive

    return {
        "session_id": session_id,                           ── D-62 unchanged
        "previous_url": previous_url,                        ── D-64 NEW
        "final_url": final_url,
        "title": title,
    }

  State preservation across navigation (D-63):
    The session's (pw, browser, context, page) quartet is the SAME
    quartet before and after navigate. The page's URL changes; the
    BrowserContext's cookie jar does not. The localStorage scoped to
    the previous URL's origin is preserved per browser-context rules
    (cleared if cross-origin, preserved if same-origin — this is
    Chromium's intrinsic behaviour, not a HERETIC choice).

  Difference from open_session navigation phase:
    open_session navigation: launch quartet → goto → register
                             (failure cleans up the launched quartet)
    navigate:                lookup session → goto on existing page
                             (failure does NOT close the session — it
                              stays open with whatever URL it had,
                              ready for a retry or a different navigate)

    A navigation failure leaves the session in a usable state: the
    session_id remains valid; subsequent calls (status, click, type,
    or another navigate) work against whatever the page now shows.
    This is intentional — agents should not lose their entire session
    state because of a single failed navigation.

  Inheritance from prior invariants:
    B-1 / B-3 / B-7 / B-8 / B-9 / B-10  — all inherited via the
                                          shared session quartet
    B-12  — URL gate runs FIRST
    B-15  — lazy eviction at call start
    B-16  — unknown session_id raises
    B-17  — activity update after success
    B-20  — NEW: navigate respects the same gate-then-resolve discipline

  Error code mapping:
    UrlNotAllowedError            → PERMISSION_DENIED
    LeidSessionExpiredError       → SENSE_UNAVAILABLE
    LeidTimeoutError              → SENSE_TIMEOUT
    LeidHttpError                 → SENSE_INTERNAL_ERROR
    LeidConnectionError           → EXTERNAL_APP_UNAVAILABLE

  Cost vs the other in-session tools:
    open_session:       ~500-3000 ms  (launch + navigate)
    navigate:           ~500-2000 ms  (navigate only — no launch)
    click / type:       ~50-200 ms    (interaction on existing page)
    session_status:     ~5-20 ms      (URL read + title read)
    close_session:      ~200-500 ms   (browser teardown)

  License posture:
    No new dependencies. Same Playwright + Chromium establishment from v0.8.0.
```

---

#### 4.12.2.7 Leið in-session selector query (Innan Hurðar extension — v0.8.3)

> **Added 2026-05-10 v0.8.3 (Védis Eikleið).** Sixth unnamed Innan Hurðar
> extension — adds `leid.query`, the read-only sibling of click/type. Returns
> text or attribute of first matching element + total match count. **Deliberate
> error-semantic divergence**: not finding a match is NOT an error
> (`found: false`); a read tool must support "checking whether X exists."
> One new B-invariant (B-21); no new error classes; reuses click timeout.

```
  LEIÐ IN-SESSION QUERY FLOW (v0.8.3)

  Entry point: agent calls leid.query(session_id, selector, attribute="").

  Stage 1 — Sense routing
    LeidSense._route → "leid.query" → PlaywrightLeidClient.query(...)

  Stage 2 — Lazy eviction (B-15 inherited)
    manager.evict_expired_sessions()

  Stage 3 — Session resolution (B-16 inherited)
    session = manager.get_session(session_id)
        ↓
    raises LeidSessionExpiredError if unknown / evicted

  Stage 4 — Locator + count
    locator = session.page.locator(selector)
    try:
        count = await locator.count()
    except PlaywrightError as exc:
        raise LeidConnectionError(...)            ── D-79 (browser failure)

    The count call uses Playwright's default action timeout, but for
    most pages this returns essentially synchronously after DOM is
    settled. count() does NOT raise on "no matches" — it returns 0.

  Stage 5 — Not-found early return (D-72 — DELIBERATE non-error)
    if count == 0:
        session.mark_activity()                   ── B-17 (still counts)
        return {
            session_id, selector, attribute,
            found: false,
            value: null,
            count: 0,
        }

    DIVERGENCE FROM CLICK/TYPE:
      Click and type raise LeidClickElementNotFoundError /
      LeidTypeElementNotFoundError when the selector matches nothing —
      because mutating actions must succeed. Query returns
      {found: false} because read operations must support "looking to
      see if X is there." The agent that calls
        query(session, ".error-banner") to detect an error message
      should NOT have to wrap the call in try/except for the success
      case of "no error message present."

  Stage 6 — Extract from first match
    first = locator.first
    timeout_ms = config.browser_click_timeout_seconds * 1000  ── D-75 reuse
    try:
        if attribute == "":                        ── D-70 (default = text)
            value = await first.text_content(timeout=timeout_ms)
        else:                                      ── D-71 (specific attr)
            value = await first.get_attribute(attribute, timeout=timeout_ms)
    except PlaywrightTimeoutError as exc:
        raise LeidConnectionError(                 ── timeout on extract
            f"query extraction timed out: {exc}"
        )
    except PlaywrightError as exc:
        raise LeidConnectionError(...)             ── D-79

    Notes on value semantics:
      - text_content returns str OR None (None when element has no text)
      - get_attribute returns str OR None (None when attribute absent)
      - Both pass through to the agent as JSON null when None
      - found=true with value=null distinguishes "found but no text/attr"
        from "found nothing" (D-73). Useful diagnostic information.
      - Whitespace is NOT stripped (D-76 — pass-through, agent decides)

  Stage 7 — Activity update (B-17 / B-21)
    session.mark_activity()

  Stage 8 — Return
    return {
        session_id,
        selector,
        attribute,                                  ── echo back what agent asked for
        found: true,
        value,                                      ── str or None
        count,                                      ── total matches in DOM
    }

  Inheritance from prior invariants:
    B-2 / B-3 / B-7 / B-8 / B-9 / B-10  — all inherited via the
                                          shared session quartet
    B-15  — lazy eviction at call start
    B-16  — unknown session_id raises LeidSessionExpiredError
    B-17  — activity update after success (BOTH not-found and found paths)
    B-21  — NEW: query honours session/timeout discipline; not-found
              returns honestly rather than raising

  Error code mapping:
    LeidSessionExpiredError       → SENSE_UNAVAILABLE
    LeidConnectionError           → EXTERNAL_APP_UNAVAILABLE
    (no class for "not found"     — successful return with found:false)

  Cost vs the other in-session tools:
    query (no match):    ~5-20 ms     (count returns 0; fast path)
    query (with match):  ~20-50 ms    (count + text_content / get_attribute)
    click / type:        ~50-200 ms   (interaction + actionability checks)
    navigate:            ~500-2000 ms (full goto)
    open_session:        ~500-3000 ms (browser cold start + goto)

  License posture:
    No new dependencies. Same Playwright + Chromium establishment from v0.8.0.
```

---

#### 4.12.2.8 Leið in-session keyboard press (Innan Hurðar extension — v0.8.4)

> **Added 2026-05-10 v0.8.4 (Védis Eikleið).** Seventh unnamed Innan Hurðar
> extension — adds `leid.press`, the body's keyboard finger. Sends a single
> key (or modifier+key combination) to the open session's page through
> Playwright's `page.keyboard.press()`. Used for form submission via Enter,
> modal dismissal via Escape, focus traversal via Tab, and similar keyboard-
> driven flows. One new B-invariant (B-22); no new error classes; no new
> config fields.

```
  LEIÐ IN-SESSION PRESS FLOW (v0.8.4)

  Entry point: agent calls leid.press(session_id, key).

  Stage 1 — Sense routing
    LeidSense._route → "leid.press" → PlaywrightLeidClient.press(...)

  Stage 2 — Lazy eviction (B-15 inherited)
    manager.evict_expired_sessions()

  Stage 3 — Session resolution (B-16 inherited)
    session = manager.get_session(session_id)
        ↓
    raises LeidSessionExpiredError if unknown / evicted

  Stage 4 — Keyboard press
    try:
        await session.page.keyboard.press(key)
    except PlaywrightError as exc:
        raise LeidConnectionError(...)            ── D-84 (browser failure)

    Notes:
      - page.keyboard.press goes to whatever element has focus.
        Typical agent flow: click(selector) or type(selector,text)
        first, then press("Enter"). The prior call leaves focus on
        the targeted element.
      - Playwright's key syntax accepts:
          single keys:         "Enter", "Tab", "Escape", "ArrowDown",
                               "a", "A", "F5", "PageDown", " " (space)
          modifier combos:     "Control+A", "Shift+Tab", "Meta+S",
                               "Alt+F4"
        The agent supplies the key string; HERETIC does not validate
        it (Playwright will dispatch as best it can; unrecognized
        keys produce no event but do not raise — D-84 rationale).
      - keyboard.press does NOT accept a per-call timeout argument.
        Playwright applies its own internal default action timeout
        (~30s). This is acceptable: keyboard input is essentially
        synchronous; the timeout is a safety net for the rare
        pathological page.

  Stage 5 — Activity update (B-17 / B-22)
    session.mark_activity()

  Stage 6 — Read post-press state (D-85)
    current_url = session.page.url   (may differ if press triggered
                                       navigation, e.g., Enter submitted)
    try: title = await session.page.title()
    except: title = None                          ── D-49 defensive

    return {
        "session_id": session_id,
        "key": key,                                ── echo back what agent pressed
        "pressed": True,
        "current_url": current_url,
        "current_title": title,
    }

  Why "page-level" press, not element-level:
    Playwright offers two press primitives:
      - page.keyboard.press(key)       — page-level; dispatches to
                                          whatever has focus
      - locator(sel).first.press(key)  — element-level; auto-focuses
                                          and dispatches
    v0.8.4 chose page-level (D-80) because the canonical agent flow
    is type(selector, text) → press("Enter") — and after type's fill
    primitive, focus IS on the typed-into element. So page-level
    press hits the right target without requiring a redundant
    selector. Agents who want element-targeted press can call
    click(selector) first to focus.
    Element-level press as its own tool is a v0.8.x candidate.

  Inheritance from prior invariants:
    B-2 / B-3 / B-7 / B-8 / B-9 / B-10  — all inherited via the
                                          shared session quartet
    B-15  — lazy eviction at call start
    B-16  — unknown session_id raises
    B-17  — activity update after success
    B-22  — NEW: press honours session/activity discipline; uses
              Playwright's intrinsic 30s default timeout for keyboard

  Error code mapping:
    LeidSessionExpiredError       → SENSE_UNAVAILABLE
    LeidConnectionError           → EXTERNAL_APP_UNAVAILABLE
    (no class for "unrecognized key" — Playwright accepts and
     dispatches; bad key strings are no-ops, not errors. The agent
     who passes "Funky+Made+Up" gets pressed: true with no effect.
     This is consistent with Playwright's design.)

  Cost vs the other in-session tools:
    press:               ~5-30 ms     (keyboard event dispatch)
    query (no match):    ~5-20 ms
    click / type:        ~50-200 ms   (with actionability checks)
    navigate:            ~500-2000 ms

  License posture:
    No new dependencies. Same Playwright + Chromium establishment from v0.8.0.
```

---

#### 4.12.2.9 Leið in-session history navigation (Innan Hurðar extension — v0.8.5)

> **Added 2026-05-10 v0.8.5 (Védis Eikleið).** Eighth unnamed Innan Hurðar
> extension — adds the paired `leid.go_back` and `leid.go_forward` tools
> for browser history traversal. Both share identical structure (one
> private helper); both honour the deliberate "no history is not an
> error" divergence (D-89 — same posture as v0.8.3 query's not-found).
> One new B-invariant (B-23); no new error classes; no new config fields.

```
  LEIÐ IN-SESSION HISTORY NAVIGATION FLOW (v0.8.5)

  Two paired tools sharing one private helper:
    leid.go_back     → _go_history(session_id, "back")
    leid.go_forward  → _go_history(session_id, "forward")

  Stage 1 — Sense routing
    LeidSense._route → "leid.go_back" or "leid.go_forward"
                     → PlaywrightLeidClient.go_back/go_forward(...)

  Stage 2 — Lazy eviction (B-15 inherited)
    manager.evict_expired_sessions()

  Stage 3 — Session resolution (B-16 inherited)
    session = manager.get_session(session_id)
        ↓
    raises LeidSessionExpiredError if unknown / evicted

  Stage 4 — Capture previous URL (mirrors navigate D-64)
    previous_url = session.page.url

  Stage 5 — History navigation
    if direction == "back":
        primitive = session.page.go_back
    else:
        primitive = session.page.go_forward
    try:
        response = await primitive(
            wait_until = config.browser_load_state,    ── D-91 reuse
            timeout    = config.browser_navigation_timeout_seconds * 1000,
        )
    except PlaywrightTimeoutError:
        raise LeidTimeoutError(...)                    ── B-5 / B-23
    except PlaywrightError:
        raise LeidConnectionError(...)                 ── B-23

  Stage 6 — Detect "no history in this direction" (D-89)
    Playwright's go_back/go_forward return:
      - Response object  → navigation actually happened
      - None             → no history entry exists in that direction;
                            the page did NOT move
    if response is None:
        session.mark_activity()                        ── B-17 (still counts)
        return {
            session_id,
            moved: false,
            previous_url,                              ── unchanged from before
            current_url: previous_url,                 ── didn't move
            title: <still the current page's title>,
        }

    DIVERGENCE FROM B-20 (navigate's "always moved or raise" model):
      navigate is a directed action — the agent supplies a URL and
      expects either to land there or hear the failure. History nav
      is a probe — "go back if there's something to go back to";
      "moved: false" is the natural answer when the body is already
      at the start of its session's history.

  Stage 7 — Status check (only when moved)
    if response.status >= 400:
        raise LeidHttpError(...)                       ── B-23

  Stage 8 — Activity update (B-17 / B-23 — happens on BOTH paths)
    session.mark_activity()

  Stage 9 — Return on successful move
    final_url = session.page.url
    try: title = await session.page.title()
    except: title = None                               ── D-49 defensive

    return {
        session_id,
        moved: true,
        previous_url,
        current_url: final_url,
        title,
    }

  Cookie state across history nav (D-92):
    Cookies + localStorage are PRESERVED — same as navigate. The
    browser context is unchanged; only the page's history pointer
    moves. This is essential: "log in → click link → go_back to
    re-fill the form" must keep the login cookies.

  URL allowlist gate (D-92 — accepted limitation):
    History nav does NOT re-validate URLs against the allowlist.
    The URLs in the history stack were already allowlist-checked
    when the body originally navigated to them. Re-checking would
    require a post-hoc check (after the page has already moved),
    which introduces unwind problems. This is consistent with the
    pre-existing "final-URL allowlist re-check after redirect" gap
    that applies to all browser tools and is already deferred.
    v0.8.5 does NOT widen the gap; it inherits the existing posture.

  Inheritance from prior invariants:
    B-2 / B-3 / B-7 / B-8 / B-9 / B-10  — all inherited via the
                                          shared session quartet
    B-15  — lazy eviction at call start
    B-16  — unknown session_id raises
    B-17  — activity update after success (BOTH moved and not-moved paths)
    B-23  — NEW: history-nav respects same discipline as navigate; "no
              history" returns honestly rather than raising

  Error code mapping (no new classes):
    LeidSessionExpiredError       → SENSE_UNAVAILABLE
    LeidTimeoutError              → SENSE_TIMEOUT
    LeidHttpError                 → SENSE_INTERNAL_ERROR
    LeidConnectionError           → EXTERNAL_APP_UNAVAILABLE
    (no class for "no history"    — successful return with moved:false)

  Cost vs the other in-session tools:
    go_back / go_forward:    ~200-2000 ms  (depends on cached resource
                                            availability; back is often
                                            faster than forward because
                                            cache hits)
    navigate (fresh):        ~500-2000 ms
    click / type / press:    ~5-200 ms
    query:                   ~5-50 ms

  License posture:
    No new dependencies. Same Playwright + Chromium establishment from v0.8.0.
```

---

#### 4.12.2.10 Leið mid-session re-extract (Innan Hurðar extension — v0.8.6)

> **Added 2026-05-11 v0.8.6 (Védis Eikleið).** Ninth unnamed Innan Hurðar
> extension; second bundled-pair milestone. Adds `leid.session_render` and
> `leid.session_screenshot` — the in-session counterparts of the stateless
> `leid.render_url` (v0.8.0) and `leid.screenshot` (v0.8.1). Same primitives
> (`page.content()` / `page.screenshot()`); same size-cap discipline (B-6
> for HTML byte size; B-11 for raw PNG bytes); same M-1 closure pattern
> (try/except mapping PlaywrightError → LeidConnectionError); applied now
> to a live session's page rather than a freshly-launched one. One new
> B-invariant (B-24); no new error classes; no new config fields.

```
  LEIÐ MID-SESSION RE-EXTRACT FLOW (v0.8.6)

  Two paired tools sharing session-resolution discipline:
    leid.session_render      → PlaywrightLeidClient.session_render
    leid.session_screenshot  → PlaywrightLeidClient.session_screenshot

  COMMON PHASES (both tools):

  Stage 1 — Sense routing
    LeidSense._route → "leid.session_render" or "leid.session_screenshot"
                     → PlaywrightLeidClient.session_render/session_screenshot

  Stage 2 — Lazy eviction (B-15 inherited)
    manager.evict_expired_sessions()

  Stage 3 — Session resolution (B-16 inherited)
    session = manager.get_session(session_id)
        ↓
    raises LeidSessionExpiredError if unknown / evicted

  Stage 4 — Capture current_url (D-101)
    current_url = session.page.url
        ↓
    Read once at entry; reflects whatever page the session is on
    after any prior click / type / press / navigate.

  PER-TOOL PHASES:

  ─── leid.session_render ───────────────────────────────────────────
  Stage 5a — Read rendered HTML (M-1 closure pattern, D-100)
    try:
        html = await session.page.content()
    except (PlaywrightTimeoutError, PlaywrightError) as exc:
        raise LeidConnectionError(...)               ── M-1 inheritance

  Stage 6a — Pre-cap on rendered HTML byte size (B-6 inheritance)
    rendered_size = len(html.encode("utf-8"))
    if rendered_size > config.max_response_bytes:
        raise LeidResponseTooLargeError(...)          ── B-6 inherited

  Stage 7a — Extract text (uses _extract_text_from_html, D-97)
    text, title = _extract_text_from_html(html)
        ↓
    Same helper as v0.8.0 render_url. No re-implementation.

  Stage 8a — Activity update (B-17 / B-24)
    session.mark_activity()

  Stage 9a — Return
    return {
        session_id,
        current_url,
        text,
        title,
        source_size_bytes: rendered_size,
    }

  ─── leid.session_screenshot ──────────────────────────────────────
  Stage 5b — Read PNG bytes (M-1 closure pattern, D-100)
    full_page = config.browser_screenshot_full_page    ── D-98 reuse
    try:
        png_bytes = await session.page.screenshot(
            full_page=full_page,
            type="png",
        )
    except (PlaywrightTimeoutError, PlaywrightError) as exc:
        raise LeidConnectionError(...)               ── M-1 inheritance

  Stage 6b — Pre-cap on raw PNG bytes (B-11 inheritance)
    png_size = len(png_bytes)
    if png_size > config.max_response_bytes:
        raise LeidResponseTooLargeError(...)          ── B-11 inherited;
                                                          cap is on raw
                                                          bytes BEFORE
                                                          base64 encoding

  Stage 7b — Base64 encode (D-17 from v0.8.1)
    image_base64 = base64.b64encode(png_bytes).decode("ascii")

  Stage 8b — Activity update (B-17 / B-24)
    session.mark_activity()

  Stage 9b — Return
    return {
        session_id,
        current_url,
        image_base64,
        image_format: "png",
        size_bytes: png_size,
        full_page,
    }

  Difference from stateless siblings (render_url, screenshot):
    The stateless v0.8.0/v0.8.1 tools are launch-per-call: they spawn
    a Playwright runtime + browser + context + page, navigate to the
    URL, extract content, then tear all four down. Each call is its
    own browser session.

    The mid-session tools at v0.8.6 reuse the EXISTING session's
    quartet — no spawn, no navigate, no teardown. They're functionally
    Stages 5+ of the stateless tools applied to the live page.

    This means session_render / session_screenshot are MUCH cheaper
    than their stateless siblings:
      render_url:           ~500-3000 ms (cold start + goto)
      session_render:       ~20-100 ms   (just page.content + extract)
      screenshot:           ~500-3000 ms (cold start + goto)
      session_screenshot:   ~50-300 ms   (just page.screenshot + base64)

  Why these tools are needed:
    Without v0.8.6, the agent that has just clicked a button and
    wants to see the new page must EITHER:
      (a) close_session + open_session(new_url) + extract  — slow,
          loses cookies/state
      (b) call session_status to see the new URL, but get only URL
          and title — not the full text or visual
    v0.8.6 lets the agent stay in-session and re-extract at any
    moment. Essential for "verify state after each step" agent
    loops and for SPAs where URL doesn't change but DOM does.

  Inheritance from prior invariants:
    B-2 / B-3 / B-7 / B-8 / B-9 / B-10  — all inherited via the
                                          shared session quartet
    B-6   — pre-cap on rendered HTML byte size (session_render)
    B-11  — pre-cap on raw PNG bytes (session_screenshot)
    B-15  — lazy eviction at call start
    B-16  — unknown session_id raises LeidSessionExpiredError
    B-17  — activity update after success
    B-24  — NEW: in-session re-extract honours all of the above

  Error code mapping (no new classes):
    LeidSessionExpiredError       → SENSE_UNAVAILABLE
    LeidConnectionError           → EXTERNAL_APP_UNAVAILABLE
    LeidResponseTooLargeError     → INVALID_ARGUMENTS

  License posture:
    No new dependencies. Same Playwright + Chromium establishment from v0.8.0.
```

---

#### 4.12.2.11 Leið in-session reload (Innan Hurðar extension — v0.8.7)

> **Added 2026-05-11 v0.8.7 (Védis Eikleið).** Tenth unnamed Innan Hurðar
> extension — adds `leid.reload`, the body's footstep in place. Re-fetches
> the current page of an open session through Playwright's `page.reload()`.
> Reuses navigation timeout + load_state config. Cookies and localStorage
> persist (intrinsic to refresh semantics). One new B-invariant (B-25);
> no new error classes; no new config fields.

```
  LEIÐ IN-SESSION RELOAD FLOW (v0.8.7)

  Entry point: agent calls leid.reload(session_id).

  Stage 1 — Sense routing
    LeidSense._route → "leid.reload" → PlaywrightLeidClient.reload(...)

  Stage 2 — Lazy eviction (B-15 inherited)
    manager.evict_expired_sessions()

  Stage 3 — Session resolution (B-16 inherited)
    session = manager.get_session(session_id)
        ↓
    raises LeidSessionExpiredError if unknown / evicted

  Stage 4 — Reload current page (D-107)
    try:
        response = await session.page.reload(
            wait_until = config.browser_load_state,    ── D-108 reuse
            timeout    = config.browser_navigation_timeout_seconds * 1000,
        )
    except PlaywrightTimeoutError:
        raise LeidTimeoutError(...)                    ── B-5 / B-25
    except PlaywrightError:
        raise LeidConnectionError(...)                 ── D-110

    Notes on the response:
      - page.reload returns Response | None
      - Response: normal HTTP reload completed
      - None: rare cases like data: URLs that cannot be reloaded —
              treated as "no HTTP status to check," same posture as
              navigate when response is None for data: URLs

  Stage 5 — Status check (only when response is not None)
    if response is not None and response.status >= 400:
        raise LeidHttpError(...)                       ── D-110

  Stage 6 — Activity update (B-17 / B-25)
    session.mark_activity()

  Stage 7 — Read post-reload state
    current_url = session.page.url   (in normal cases unchanged from
                                       before reload; but a server-side
                                       redirect on reload could change it)
    try: title = await session.page.title()
    except: title = None                              ── D-49 defensive

    return {
        session_id,                                   ── D-111: minimal shape
        current_url,
        title,
    }

  No previous_url because reload is in-place — previous and current URL
  are conceptually the same (D-111). No `moved` boolean because reload
  is not a probe-and-act primitive — either it succeeded or it failed.

  State preservation across reload:
    Cookies, localStorage, sessionStorage all persist. The browser
    context is unchanged; the page object is the same; only the page's
    content is re-fetched from the server. This is intrinsic to refresh
    semantics — not a new HERETIC invariant.

  URL allowlist gate (D-109):
    Reload does NOT re-validate the URL against the allowlist. The URL
    the body is at was already allowlist-checked when first navigated
    to. Reload is in-place — the URL doesn't change. Same posture as
    go_back/go_forward (D-92): inherits the existing pre-existing-
    concern about final-URL allowlist re-check after redirect.

  Inheritance from prior invariants:
    B-2 / B-3 / B-7 / B-8 / B-9 / B-10  — all inherited via the
                                          shared session quartet
    B-15  — lazy eviction at call start
    B-16  — unknown session_id raises
    B-17  — activity update after success
    B-25  — NEW: reload respects same discipline as navigate

  Error code mapping (no new classes):
    LeidSessionExpiredError       → SENSE_UNAVAILABLE
    LeidTimeoutError              → SENSE_TIMEOUT
    LeidHttpError                 → SENSE_INTERNAL_ERROR
    LeidConnectionError           → EXTERNAL_APP_UNAVAILABLE

  Cost vs the other in-session tools:
    reload:                  ~200-2000 ms  (re-fetch current URL +
                                            re-render; similar to navigate
                                            but typically faster due to
                                            browser cache)
    navigate (fresh):        ~500-2000 ms
    go_back / go_forward:    ~200-2000 ms
    session_render:          ~20-100 ms    (no re-fetch)
    session_screenshot:      ~50-300 ms    (no re-fetch)

  License posture:
    No new dependencies. Same Playwright + Chromium establishment from v0.8.0.
```

---

#### 4.12.2.12 Leið in-session multi-element query (Innan Hurðar extension — v0.8.8)

> **Added 2026-05-11 v0.8.8 (Védis Eikleið).** Eleventh unnamed Innan
> Hurðar extension — adds `leid.query_all`, multi-element follow-up to
> v0.8.3 single-match `query`. Returns ALL matches as a list (in DOM
> order) up to a new cardinality cap (`browser_query_max_matches`,
> default 100). Same probe-and-act posture as query: empty result is
> NOT an error. One new B-invariant (B-26); no new error classes; ONE
> new config field (first new field since v0.8.2 — five-consecutive-
> milestone config-stability streak ends here).

```
  LEIÐ IN-SESSION MULTI-ELEMENT QUERY FLOW (v0.8.8)

  Entry point: agent calls leid.query_all(session_id, selector, attribute="").

  Stage 1 — Sense routing
    LeidSense._route → "leid.query_all" → PlaywrightLeidClient.query_all(...)

  Stage 2 — Lazy eviction (B-15 inherited)
    manager.evict_expired_sessions()

  Stage 3 — Session resolution (B-16 inherited)
    session = manager.get_session(session_id)
        ↓
    raises LeidSessionExpiredError if unknown / evicted

  Stage 4 — Locator + count
    locator = session.page.locator(selector)
    try:
        count = await locator.count()
    except PlaywrightError as exc:
        raise LeidConnectionError(...)            ── shared with query

  Stage 5 — Cardinality cap check (B-26 NEW)
    if count > config.browser_query_max_matches:
        raise LeidResponseTooLargeError(           ── D-116
            f"selector matched {count} elements, exceeds "
            f"browser_query_max_matches={cap}; refine selector"
        )

    Note: this fires even if count == 0 was the first check; the cap
    check is what bounds the iteration cost. count == 0 falls through
    to the empty-return branch below (D-117 — not an error).

  Stage 6 — Empty early return (D-117, B-26 divergence)
    if count == 0:
        session.mark_activity()                    ── B-17 (still counts)
        return {
            session_id, selector, attribute,
            count: 0, values: [],
        }

    SAME DIVERGENCE as v0.8.3 query (D-72): empty match is not an
    error. The agent's natural "give me all matches" includes the
    success case of "there were zero." Forcing exception handling
    on the empty case would invert the semantics.

  Stage 7 — Iterate matches and extract (D-118)
    timeout_ms = config.browser_click_timeout_seconds * 1000  ── D-122 reuse
    values = []
    for i in range(count):
        el = locator.nth(i)
        try:
            if attribute == "":                    ── D-120 default = text
                v = await el.text_content(timeout=timeout_ms)
            else:                                  ── D-120 attribute path
                v = await el.get_attribute(attribute, timeout=timeout_ms)
        except PlaywrightTimeoutError as exc:
            raise LeidConnectionError(             ── per-element timeout
                f"query_all extraction at index {i} timed out: {exc}"
            )
        except PlaywrightError as exc:
            raise LeidConnectionError(             ── shared with query
                f"query_all extraction at index {i} failed: {exc}"
            )
        values.append(v)

    Notes on per-element values:
      - text_content returns str OR None (None when element has no text)
      - get_attribute returns str OR None (None when attribute absent)
      - Both pass through to the agent as JSON null when None
      - The agent can distinguish "element exists but empty/no-attr"
        (None in values) from "no element matched" (count=0, values=[])

  Stage 8 — Activity update (B-17 / B-26)
    session.mark_activity()

  Stage 9 — Return
    return {
        session_id,
        selector,
        attribute,                                 ── echo back what agent asked
        count,                                     ── total matches in DOM
        values,                                    ── list of str | None,
                                                      length == count,
                                                      DOM order
    }

  Cap-vs-byte-size:
    The cap is on CARDINALITY (number of matches), not byte size of
    serialized values. This is intentional: agents care about how
    many items they get back (typical: tens, not hundreds), not
    about exact byte budget. If the agent needs 200 matches when
    cap is 100, they raise the operator's cap rather than fight a
    byte budget.

    A byte-size cap (max_response_bytes summed across values) was
    considered and rejected: it forces operators to reason about
    serialization overhead, and it forces the implementation to
    track running byte size mid-iteration. Cardinality cap is
    cleaner and matches the agent's mental model.

  Inheritance from prior invariants:
    B-2 / B-3 / B-7 / B-8 / B-9 / B-10  — all inherited via the
                                          shared session quartet
    B-15  — lazy eviction at call start
    B-16  — unknown session_id raises LeidSessionExpiredError
    B-17  — activity update after success (BOTH empty and non-empty paths)
    B-21  — query divergence (not-found is not error) inherited
    B-26  — NEW: cardinality cap; empty-result divergence preserved

  Error code mapping (no new classes):
    LeidSessionExpiredError       → SENSE_UNAVAILABLE
    LeidConnectionError           → EXTERNAL_APP_UNAVAILABLE
    LeidResponseTooLargeError     → INVALID_ARGUMENTS
    (no class for "no match"      — successful return with values:[])

  New config field:
    browser_query_max_matches: int = 100
      Bounds query_all's iteration. Validated >= 1 in __post_init__.
      Operators may raise this for use cases that genuinely need
      many matches, but defaulting to 100 catches the over-broad-
      selector mistake early.

  Cost vs query (single-match):
    query (1 match):     ~5-50 ms      (count + 1 extract)
    query_all (10):      ~50-500 ms    (count + 10 extracts)
    query_all (100):     ~500-5000 ms  (count + 100 extracts)
    query_all (cap exceeded):  ~5-20 ms (count only — early return)

    Per-element cost is roughly the same as query's single extract.
    Cap-exceeded is fast because no iteration happens.

  License posture:
    No new dependencies. Same Playwright + Chromium establishment from v0.8.0.
```

---

#### 4.12.3 Sandbox invariants (cross-cutting — v0.6.2)

> **Added 2026-05-08 v0.6.2 (Védis Eikleið).** These invariants apply across all three
> v0.6.2 senses and to any future sense added to L5 Skilningr. They are implemented once
> in `skillingr/sandbox.py` and called by each sense's client. They are enforced before
> any IO operation, subprocess invocation, or network request begins.

```
  CROSS-CUTTING SANDBOX INVARIANTS

  I-1: All three senses default disabled
    enabled: false for minni, skepja, and leid in all configuration paths.
    If a sense is not enabled:
      - it is not mounted in ToolDispatcher at TENGSL
      - agent receives no tool definitions for that sense
      - no tool_call with that prefix can be dispatched
    An operator must explicitly set enabled: true for each sense they want active.

  I-2: Path traversal blocked (Minni)
    path_within_allowed_roots() resolves the supplied path and verifies it lives
    within at least one allowed root. The check runs before any file handle opens.
    Traversal via `../`, absolute paths outside the root, and symlinks whose resolved
    targets fall outside the root are all caught and raise SandboxViolationError.
    SandboxViolationError is caught by MinniSense and returned as error ToolResult.

  I-3: Command allowlist enforced (Skepja)
    command_allowlist_check() verifies the first token of the split command list against
    the operator-defined allowlist before subprocess.run is called.
    An empty allowlist (the default) means NO command can run.
    CommandNotAllowedError is caught by SkepjaSense and returned as error ToolResult.
    shell=False is structurally enforced — shell metacharacters are never interpreted.

  I-4: URL pattern allowlist enforced (Leið)
    url_allowlist_match() tests the URL against each pattern using fnmatch before httpx
    opens any connection. An empty pattern list (the default) means NO URL can be fetched.
    UrlNotAllowedError is caught by LeidSense and returned as error ToolResult.
    Only "http" and "https" schemes are permitted; any other scheme raises UrlNotAllowedError.

  I-5: Sense isolation — one sense's failure does not affect others
    Each sense (Minni, Skepja, Leið, Smiðja) is mounted independently in ToolDispatcher.
    Each sense's open() and close() runs in its own try/except at TENGSL and SLOKNA.
    If Minni fails to open (e.g., bad config), Skepja, Leið, and Smiðja continue normally.
    If Skepja's client raises during a tool_call, it returns an error ToolResult — the
    error is contained within SkepjaSense and does not affect Minni, Leið, or Smiðja.
    ToolDispatcher.dispatch() is the seam: it routes and catches per-sense errors.
    No cross-sense state. Each sense owns its config, its client, its errors.

  I-6: No sense can be promoted to a higher trust level mid-ceremony
    Config is loaded once at Kynding (ceremony start). Config values are immutable
    during the ceremony. An agent cannot modify allowed_roots, command_allowlist, or
    url_allowlist_patterns by calling a tool — these live in the operator config layer,
    outside the agent's reach.

  I-7: sandbox.py is the single implementation
    path_within_allowed_roots, command_allowlist_check, url_allowlist_match are defined
    once in skillingr/sandbox.py. No sense re-implements these primitives locally.
    This prevents divergent implementations that could introduce gaps.

  SANDBOX ERROR HIERARCHY (all extend SkilningrError):
    SkilningrError (base)
      |-- SandboxViolationError    (Minni: path outside allowed roots)
      |-- CommandNotAllowedError   (Skepja: first token not in allowlist)
      |-- UrlNotAllowedError       (Leið: URL does not match allowlist patterns)
      |-- FilesizeLimitError       (Minni: write payload exceeds max_file_size_bytes)
    Each is caught within the sense that raises it.
    None propagate to ToolDispatcher or CLI.
```

---

## 16. L5 Skilningr — Four Senses Component Diagram (v0.6.2)

> **Added 2026-05-08 v0.6 (Védis Eikleið). Extended 2026-05-08 v0.6.1 (Védis Eikleið).
> Extended 2026-05-08 v0.6.2 (Védis Eikleið).**
> Maps the internal structure of the `skillingr/` module and all four sense subpackages
> as of v0.6.2: Smiðja (workshop — v0.6 + v0.6.1), Minni (library — v0.6.2), Skepja
> (terminal — v0.6.2), Leið (road — v0.6.2). In v0.6 the longhouse held one room.
> In v0.6.1 the workshop gained a second anvil. In v0.6.2 three new rooms open beside it.
>
> **Position in the body:** Skilningr is the discernment layer — the organ that decides
> which sense to invoke when the agent reaches. In v0.6.2, four senses are mounted.
> Each sense is a separate subpackage with its own client, tools, config, errors, and
> sense.py orchestrator. ToolDispatcher routes by tool-name prefix to the correct sense.

```
  ============================================================
  SKILNINGR MODULE — src/heretic/skilningr/    (v0.6.2 Four Senses)
  ============================================================

  skillingr/
  |
  ├── config_model.py    SkilningrConfig
  │                      |  smidja:  SmidjaConfig     (v0.6 + v0.6.1)
  │                      |    brunhand: BrunhandConfig
  │                      |    forge:    ForgeConfig
  │                      |  minni:   MinniConfig      (v0.6.2)
  │                      |    enabled: bool                       default false
  │                      |    allowed_roots: list[str]            default ["~/heretic_workspace"]
  │                      |    max_file_size_bytes: int            default 1_048_576
  │                      |  skepja:  SkepjaConfig     (v0.6.2)
  │                      |    enabled: bool                       default false
  │                      |    command_allowlist: list[str]        default []
  │                      |    working_directory: str              default "~/heretic_workspace"
  │                      |    inherit_env: bool                   default false
  │                      |    timeout_seconds: int                default 60
  │                      |    max_output_bytes: int               default 65_536
  │                      |  leid:    LeidConfig        (v0.6.2)
  │                      |    enabled: bool                       default false
  │                      |    url_allowlist_patterns: list[str]   default []
  │                      |    max_response_bytes: int             default 1_048_576
  │                      |    timeout_seconds: int                default 30
  │                      |    max_redirects: int                  default 5
  │
  ├── errors.py          SkilningrError (base)
  │                      |-- SenseUnavailableError
  │                      |-- ToolDispatchError
  │                      |-- SandboxViolationError   (v0.6.2)
  │                      |-- CommandNotAllowedError  (v0.6.2)
  │                      |-- UrlNotAllowedError      (v0.6.2)
  │                      |-- FilesizeLimitError      (v0.6.2)
  │
  ├── sandbox.py         Shared validation primitives (v0.6.2 NEW)
  │                      |  path_within_allowed_roots(raw_path, allowed_roots) -> Path
  │                      |  command_allowlist_check(tokens, allowlist) -> None
  │                      |  url_allowlist_match(url, patterns) -> None
  │                      |
  │                      Single implementation; called by Minni, Skepja, Leið clients.
  │                      Never re-implemented per-sense.
  │
  ├── dispatcher.py      ToolDispatcher  (unchanged routing logic — four senses now registered)
  │                      |  async dispatch(tool_call) -> ToolResult
  │                      |    "smidja.*" → SmidjaSense
  │                      |    "minni.*"  → MinniSense     (v0.6.2)
  │                      |    "skepja.*" → SkepjaSense    (v0.6.2)
  │                      |    "leid.*"   → LeidSense      (v0.6.2)
  │                      |    unknown   → error ToolResult (F-6)
  │
  └── senses/
      |
      ├── smidja/        Smiðja — the workshop (v0.6 + v0.6.1)
      │   ├── errors.py      SmidjaError hierarchy (Brúarhönd + Forge arms)
      │   ├── tools.py       9 tools (6 Brúarhönd + 3 Forge)
      │   ├── client.py      BrunhandHttpClient (live GUI control → Seidr-Smidja)
      │   ├── forge_client.py ForgeHttpClient (headless Blender → Straumur REST)
      │   └── sense.py       SmidjaSense (dual-half lifecycle; see §4.11)
      │
      ├── minni/         Minni — the library (v0.6.2 NEW)
      │   ├── INTERFACE.md   sense contract (allowed_roots, tools, invariants)
      │   ├── config_model.py MinniConfig
      │   ├── errors.py      MinniError hierarchy
      │   │                  |-- MinniError (base, extends SkilningrError)
      │   │                  |     |-- FileNotFoundError (sense-wrapped)
      │   │                  |     |-- FilesizeLimitError (read or write exceeds cap)
      │   │                  |     |-- SandboxViolationError (path outside allowed roots)
      │   │                  |     |-- DirectoryListError (list_directory IO failure)
      │   ├── client.py      MinniClient — sandbox-validated file ops (pure pathlib/io)
      │   │                  |  read_file(path) -> dict
      │   │                  |  write_file(path, content) -> dict
      │   │                  |  list_directory(path) -> dict
      │   │                  All operations call path_within_allowed_roots() first.
      │   ├── tools.py       3 tool definitions
      │   │                  |  minni.read_file      { path: str }
      │   │                  |  minni.write_file     { path: str, content: str }
      │   │                  |  minni.list_directory { path: str }
      │   └── sense.py       MinniSense
      │                      |  open() -> None   (validates allowed_roots exist; logs)
      │                      |  close() -> None  (no-op; no persistent resource)
      │                      |  dispatch_tool_call(tool_call) -> ToolResult
      │
      ├── skepja/        Skepja — the terminal (v0.6.2 NEW)
      │   ├── INTERFACE.md   sense contract (allowlist, working_dir, shell=False invariant)
      │   ├── config_model.py SkepjaConfig
      │   ├── errors.py      SkepjaError hierarchy
      │   │                  |-- SkepjaError (base, extends SkilningrError)
      │   │                  |     |-- CommandNotAllowedError (first token not in allowlist)
      │   │                  |     |-- SkepjaTimeoutError     (subprocess timeout)
      │   │                  |     |-- SkepjaBadWorkingDir    (working_directory not found)
      │   ├── client.py      SkepjaClient — subprocess wrapper
      │   │                  |  run_command(command: str) -> dict
      │   │                  |    shlex.split → allowlist_check → subprocess.run(shell=False)
      │   │                  |    → output capture + truncation → return dict
      │   │                  |  get_working_directory() -> dict
      │   │                  |    returns {"working_directory": str(resolved_path)}
      │   ├── tools.py       2 tool definitions
      │   │                  |  skepja.run_command       { command: str }
      │   │                  |  skepja.get_working_directory  {}
      │   └── sense.py       SkepjaSense
      │                      |  open() -> None   (validates working_directory exists; logs allowlist)
      │                      |  close() -> None  (no-op)
      │                      |  dispatch_tool_call(tool_call) -> ToolResult
      │
      └── leid/          Leið — the road (v0.6.2 NEW)
          ├── INTERFACE.md   sense contract (url allowlist, no cookies, no JS, HTTPS pref)
          ├── config_model.py LeidConfig
          ├── errors.py      LeidError hierarchy
          │                  |-- LeidError (base, extends SkilningrError)
          │                  |     |-- UrlNotAllowedError    (URL not in patterns)
          │                  |     |-- LeidTimeoutError      (httpx timeout)
          │                  |     |-- LeidTooManyRedirects  (redirect chain exceeded)
          │                  |     |-- LeidConnectError      (host unreachable)
          ├── client.py      LeidClient — httpx GET wrapper
          │                  |  async fetch_url(url: str) -> dict
          │                  |    url_allowlist_match → GET with limits → size cap → return
          │                  |  async extract_text(url: str) -> dict
          │                  |    fetch_url → html.parser tag-strip → return plain text
          │                  |  Each call: fresh httpx.AsyncClient; no persistent session.
          │                  |  No cookies stored between calls.
          ├── tools.py       2 tool definitions
          │                  |  leid.fetch_url    { url: str }
          │                  |  leid.extract_text { url: str }
          └── sense.py       LeidSense
                             |  open() -> None   (validates url_allowlist_patterns; logs warning
                             |                    if wildcard "*" pattern present)
                             |  close() -> None  (no-op; httpx clients are per-call)
                             |  dispatch_tool_call(tool_call) -> ToolResult


  ============================================================
  TOOL COUNT SUMMARY — v0.6.2
  ============================================================

  Sense      Prefix    Tools (v0.6.2)
  ---------  --------  ------------------------------------------
  Smiðja     smidja    9  (6 Brúarhönd + 3 Forge — unchanged from v0.6.1)
  Minni      minni     3  (read_file, write_file, list_directory)
  Skepja     skepja    2  (run_command, get_working_directory)
  Leið       leid      2  (fetch_url, extract_text)
  ---------  --------  ------------------------------------------
  TOTAL                16 tools available when all four senses are enabled
                       (agent only receives tools for enabled senses)


  ============================================================
  FOUR-SENSE LIFECYCLE AT TENGSL (ceremony open)
  ============================================================

  CLI.TENGSL():
    ToolDispatcher._senses = {}
    IF smidja.enabled (brunhand or forge):
      SmidjaSense.open()     → dual-half probe (Brúarhönd + Forge independently)
      _senses["smidja"] = SmidjaSense
    IF minni.enabled:
      MinniSense.open()      → validates allowed_roots paths exist
      _senses["minni"] = MinniSense
    IF skepja.enabled:
      SkepjaSense.open()     → validates working_directory; logs allowlist size
      _senses["skepja"] = SkepjaSense
    IF leid.enabled:
      LeidSense.open()       → logs url_allowlist_patterns; warns if wildcard
      _senses["leid"] = LeidSense

    Each open() is wrapped in independent try/except.
    Failure of any one sense does not abort the others.
    A failed sense is not added to _senses; its tools are not offered to the agent.


  ============================================================
  FOUR-SENSE LIFECYCLE AT SLOKNA (ceremony close)
  ============================================================

  CLI.SLOKNA():
    FOR sense_id, sense in _senses.items():
      try:
        await sense.close()
      except Exception:
        log.warning(f"Sense {sense_id!r} failed to close cleanly — ignoring")

    Each close() is isolated. All four senses are attempted regardless of prior failures.
    Minni, Skepja, Leið have no-op close() (no persistent resource to release).
    Smiðja close() shuts down both httpx.AsyncClient instances (Brúarhönd + Forge arms).
```

---

---

### 4.13 MCP Transport Flow (v0.6.x — three-door coexistence)

> **Added 2026-05-08 v0.6.x (Védis Eikleið).** This section maps the alternative transport
> door: MCP (Model Context Protocol) server hosting. It runs alongside the existing OpenAI
> tool_use path (Light / Serve) without displacing it. The workshop now has three doors.
> The same ToolDispatcher stands behind all three.

#### 4.13.1 The three doors — transport coexistence overview

```
  HERETIC TRANSPORT SURFACE (v0.6.x)
  ===================================

  Door 1 — OpenAI tool_use   (heretic light / heretic serve)
  -----------------------------------------------------------
  Agent (Hermes, OpenClaw-shim, GPT-4, etc.)
       |
       |  POST /v1/chat/completions  { "tools": [...], "tool_choice": "auto" }
       |  <-- streaming SSE delta chunks
       |  <-- finish_reason: "tool_calls"
       v
  L1 Bifröst  -->  ToolDispatcher  -->  Sense subpackage  -->  ToolResult
  (unchanged path — see §4.11 for full cartography)

  Door 2 — MCP stdio   (heretic mcp --transport stdio)
  -----------------------------------------------------
  MCP-aware agent (Claude Desktop, Continue, etc.)
       |
       |  stdin  → JSON-RPC 2.0 request
       |  stdout ← JSON-RPC 2.0 response
       v
  McpServer (stdio transport)
       |  initialize   --> return server capabilities {tools: true}
       |  tools/list   --> collect 16 tool defs from all 4 senses
       |                   convert OpenAI schema → MCP inputSchema
       |                   return [{name, description, inputSchema}, ...]
       |  tools/call   --> extract name + arguments
       v
  ToolDispatcher.dispatch(tool_call)
       v
  Sense subpackage (Smiðja / Minni / Skepja / Leið)
       v
  ToolResult  --> map to MCP content array  --> JSON-RPC response → stdout

  Door 3 — MCP HTTP/SSE   (heretic mcp --transport http)
  -------------------------------------------------------
  MCP-aware agent (browser-friendly; Tailscale-routable)
       |
       |  POST /mcp         → JSON-RPC 2.0 request (HTTP body)
       |  GET  /mcp/events  ← SSE stream (server-sent events)
       v
  McpServer (HTTP/SSE transport, uvicorn — already a dep from v0.4)
       |  (same initialize / tools/list / tools/call handlers as stdio)
       v
  ToolDispatcher  -->  Sense  -->  ToolResult  -->  MCP content array
       v
  SSE event → agent
```

#### 4.13.2 Initialize handshake

The first message on any MCP connection is `initialize`. The server responds with its
declared capabilities. In v0.6.x, HERETIC declares tools only; resources, prompts, sampling,
and logging are deferred.

```
  Client → Server:
  {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": { "name": "<agent name>", "version": "<version>" }
    }
  }

  Server → Client:
  {
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
      "protocolVersion": "2024-11-05",
      "capabilities": {
        "tools": {}
      },
      "serverInfo": {
        "name": "HERETIC",
        "version": "<heretic version>"
      }
    }
  }

  NOT declared in v0.6.x capabilities:
    resources    (deferred to v0.6.x.1)
    prompts      (deferred to v0.6.x.2)
    sampling     (out of scope)
    logging      (deferred)
```

#### 4.13.3 tools/list — schema collection and conversion

```
  Client → Server:
  { "jsonrpc": "2.0", "id": 2, "method": "tools/list" }

  McpServer handler:
       |
       |  collect all enabled senses' tool definitions:
       |    SMIDJA_TOOL_DEFINITIONS   (9 tools — Brúarhönd + Forge)
       |    MINNI_TOOL_DEFINITIONS    (3 tools — read_file, write_file, list_directory)
       |    SKEPJA_TOOL_DEFINITIONS   (2 tools — run_command, get_working_directory)
       |    LEID_TOOL_DEFINITIONS     (2 tools — fetch_url, extract_text)
       |
       |  for each OpenAI-format tool definition:
       |    convert_to_mcp_tool(openai_tool) -> mcp_tool
       |
       |    OpenAI format:                         MCP format:
       |    {                                      {
       |      "type": "function",                    "name": "<sense_id>.<action>",
       |      "function": {                          "description": "...",
       |        "name": "<sense_id>.<action>",       "inputSchema": {
       |        "description": "...",                  "type": "object",
       |        "parameters": {                        "properties": {...},
       |          "type": "object",                    "required": [...]
       |          "properties": {...},               }
       |          "required": [...]                }
       |        }
       |      }
       |    }
       |
       |    Mapping:
       |      mcp_tool["name"]        = openai_tool["function"]["name"]
       |      mcp_tool["description"] = openai_tool["function"]["description"]
       |      mcp_tool["inputSchema"] = openai_tool["function"]["parameters"]
       |      (the parameters/inputSchema content is identical JSON Schema — no conversion needed)
       |
       v
  return 16 mcp_tool objects (when all four senses are enabled)
  (agent only receives tools for senses that are enabled — same gate as OpenAI path)

  Server → Client:
  {
    "jsonrpc": "2.0",
    "id": 2,
    "result": {
      "tools": [
        { "name": "smidja.screenshot", "description": "...", "inputSchema": {...} },
        { "name": "smidja.click",      "description": "...", "inputSchema": {...} },
        ... (16 total when all enabled)
      ]
    }
  }
```

#### 4.13.4 tools/call — routing through shared ToolDispatcher

This is the invariant heart of the three-door design: a single ToolDispatcher handles all
tool execution regardless of how the call arrived.

```
  Client → Server:
  {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "smidja.screenshot",
      "arguments": { "monitor_index": 0 }
    }
  }

  McpServer handler:
       |
       |  extract name = "smidja.screenshot"
       |  extract arguments = { "monitor_index": 0 }
       |
       |  build internal ToolCall object:
       |    ToolCall(name="smidja.screenshot", arguments_json=json.dumps(arguments))
       |
       v
  ToolDispatcher.dispatch(tool_call)
       |  (IDENTICAL to the Door 1 path — no fork in the execution logic)
       |  routes by prefix "smidja" → SmidjaSense.dispatch_tool_call(tool_call)
       |  returns ToolResult
       v
  map ToolResult → MCP content array:
       |
       |  success:
       |    content = [{ "type": "text", "text": tool_result.content }]
       |    isError = false
       |
       |  tool returned error JSON:
       |    content = [{ "type": "text", "text": tool_result.content }]
       |    isError = true
       v
  Server → Client:
  {
    "jsonrpc": "2.0",
    "id": 3,
    "result": {
      "content": [{ "type": "text", "text": "<tool result JSON>" }],
      "isError": false
    }
  }
```

#### 4.13.5 Failure modes

Four failure modes on the MCP transport path; each maps to a JSON-RPC error or MCP error
result, never to a process crash. The ToolDispatcher's own invariants carry forward
unchanged — it never raises to its caller.

```
  F-MCP-1: Transport disconnect (stdio — pipe closed; HTTP — client disconnects)
    stdio:  StdioTransport catches EOF on stdin → graceful close:
              McpServer.shutdown() → all senses receive close() → process exits cleanly
    HTTP:   Starlette/uvicorn connection handler closes → SSE stream ends
              McpServer session cleaned up → senses unaffected (per-request, stateless)
    In both cases: no exception propagates to the sense layer.

  F-MCP-2: Malformed JSON-RPC request (invalid JSON, missing "method" field, wrong version)
    McpServer transport layer catches parse failure before any handler is called.
    Response:
    {
      "jsonrpc": "2.0",
      "id": null,
      "error": { "code": -32700, "message": "Parse error" }
    }
    (or -32600 Invalid Request if JSON parses but is not a valid JSON-RPC object)
    ToolDispatcher is never reached.

  F-MCP-3: Unknown tool name in tools/call (agent requests a tool not in the registry)
    McpServer extracts name, builds ToolCall, calls ToolDispatcher.dispatch().
    ToolDispatcher finds no registered sense for the prefix → returns error ToolResult.
    (same F-6 path as Door 1 — see §4.11.4)
    McpServer maps the error ToolResult to:
    {
      "jsonrpc": "2.0",
      "id": <id>,
      "result": {
        "content": [{ "type": "text", "text": "{\"error\": \"unknown_tool\", ...}" }],
        "isError": true
      }
    }
    Note: this is a result (not a JSON-RPC error) — per MCP spec, tool errors are returned
    as result.isError = true, not as JSON-RPC error objects.

  F-MCP-4: ToolDispatcher exception (sense raises unexpectedly; should be extremely rare)
    Each sense's dispatch_tool_call() wraps all paths in try/except and returns ToolResult.
    If — despite those guards — ToolDispatcher.dispatch() raises:
      McpServer catches the exception in the tools/call handler.
      Returns:
      {
        "jsonrpc": "2.0",
        "id": <id>,
        "result": {
          "content": [{ "type": "text", "text": "{\"error\": \"dispatch_exception\", ...}" }],
          "isError": true
        }
      }
    The MCP server does not crash. The connection remains open for further calls.
```

#### 4.13.6 Auth model

The MCP server carries forward the same auth model as the existing REST surfaces:

```
  stdio transport:
    No network auth is needed — the stdio pipe is the trust boundary.
    Process-level isolation (launched by a trusted MCP host such as Claude Desktop) provides
    identity. Bearer token is not passed over stdio.

  HTTP/SSE transport:
    Bearer token from environment variable: HERETIC_MCP_TOKEN (if configured).
    Sent by agent as: Authorization: Bearer <token>
    McpServer checks before dispatching any method.
    Token is never logged (same sealed invariant as Bifröst + Brúarhönd + Forge auth).
    Default: localhost only (127.0.0.1).
    allow_remote_bind: false by default; operator must set true explicitly to expose on
    non-localhost interface (e.g., Tailscale IP).
```

#### 4.13.7 CLI coexistence — three launch modes

```
  heretic light            OpenAI tool_use, single-turn demo    (Door 1, lightweight)
  heretic serve            OpenAI tool_use + REST, full daemon   (Door 1, full)
  heretic mcp --transport stdio    MCP server on stdin/stdout    (Door 2)
  heretic mcp --transport http     MCP server on host:port       (Door 3)

  Concurrent operation: MCP server (Door 2 or 3) + heretic serve (Door 1) can run
  in the same Python process. Both are async; both share the asyncio event loop.
  ToolDispatcher instance is shared — one dispatch table, all doors.
```

> The workshop now has three doors. Each opens onto a different kind of road.
> The workbench inside is the same. The hand that reaches is the same.
> Only the threshold changes.

---

### 4.14 Library Flow (v0.7 — Mímisbrunnr light tier)

> **Added 2026-05-08 v0.7 (Védis Eikleið).** The well opens for the first time.
> Mímisbrunnr is HERETIC's optional offline knowledge subsystem — a bookshelf in the
> longhouse. It plugs into L5 Skilningr as a fifth sense (LibrarySense), registered under
> the prefix "library". The agent never touches the corpus directly; it calls one of three
> tools, and LibrarySense delegates through LibraryClient to the mimisbrunnr/ backend.
>
> v0.7 ships the LIGHT TIER ONLY: file-index keyword search over plain-text corpora.
> No vector search (v0.9). No ZIM / Wikipedia (v0.8). The corpus is the Norse starter pack
> (~2.7 MB of public-domain Eddas and sagas). The network is never reached during a query.

```
  THREE AGENT TOOL PATHS

  PATH A — library.search  (keyword search across all downloaded sources)
  -----------------------------------------------------------------------

  [Agent — tool_call: library.search]
       |
       |  arguments_json:
       |    { "query": "Odin sacrifices his eye", "max_results": 5 }
       |
       v
  [ToolDispatcher.dispatch(tool_call)]
       |
       |  prefix = "library" --> LibrarySense
       |
       v
  [LibrarySense.dispatch_tool_call(tool_call)]
       |
       |  IF NOT library.enabled --> return error ToolResult (F-4 or config error)
       |
       v
  [LibraryClient.search(query, max_results)]
       |
       |  FOR each source_id in local manifest where status = "downloaded":
       |    index.py: load line-offset index for source
       |    re.search(pattern, line) for each line in sources/<source_id>/text.txt
       |    collect Match(source_id, line_number, context_text)
       |  rank by match count / position
       |  return top max_results matches
       |
       v
  [LibrarySense encodes -> ToolResult]
       |
       |  content = json.dumps({
       |    "results": [
       |      {
       |        "source_id":    "prose_edda",
       |        "line_number":  1423,
       |        "context_text": "...the eye that Odin gave for wisdom...",
       |        "source_title": "Prose Edda (Brodeur translation)"
       |      },
       |      ...
       |    ],
       |    "query": "Odin sacrifices his eye",
       |    "total_searched_sources": 3
       |  })
       |
       v
  [CLI appends tool_result to messages; resumes agent loop]


  PATH B — library.get_text  (retrieve a passage by source + line range)
  ------------------------------------------------------------------------

  [Agent — tool_call: library.get_text]
       |
       |  arguments_json:
       |    { "source_id": "prose_edda", "start_line": 1420, "end_line": 1430 }
       |
       v
  [ToolDispatcher] --> LibrarySense --> LibraryClient.get_text(source_id, start, end)
       |
       |  store.py: resolve path = <data_dir>/library/sources/<source_id>/text.txt
       |  validate path does not escape library root (store.resolve_source_path)
       |  open file, seek to start_line offset (from pre-built line index)
       |  read lines start_line..end_line inclusive
       |
       v
  [LibrarySense encodes -> ToolResult]
       |
       |  content = json.dumps({
       |    "source_id":    "prose_edda",
       |    "source_title": "Prose Edda (Brodeur translation)",
       |    "start_line":   1420,
       |    "end_line":     1430,
       |    "text":         "...passage text...",
       |    "license":      "Public Domain"
       |  })
       v
  [CLI appends tool_result; agent may cite and quote]


  PATH C — library.list_sources  (enumerate available + downloaded sources)
  --------------------------------------------------------------------------

  [Agent — tool_call: library.list_sources]
       |
       |  arguments_json: {}  (no arguments)
       |
       v
  [ToolDispatcher] --> LibrarySense --> LibraryClient.list_sources()
       |
       |  manifest.py: load manifest.yaml from library root (or starter manifest
       |               shipped with HERETIC if operator has not downloaded anything)
       |  for each source entry:
       |    check store.py: does sources/<source_id>/text.txt exist on disk?
       |    add "downloaded": true/false to each entry
       |
       v
  [LibrarySense encodes -> ToolResult]
       |
       |  content = json.dumps({
       |    "sources": [
       |      {
       |        "source_id":    "prose_edda",
       |        "title":        "Prose Edda (Brodeur translation)",
       |        "license":      "Public Domain",
       |        "approx_size":  "280 KB",
       |        "downloaded":   true
       |      },
       |      {
       |        "source_id":    "poetic_edda",
       |        "title":        "Poetic Edda (Bellows translation)",
       |        "license":      "Public Domain",
       |        "approx_size":  "600 KB",
       |        "downloaded":   false
       |      },
       |      ...
       |    ]
       |  })
       v
  [Agent can inform user which sources are available but not yet downloaded]
```

---

#### 4.14.1 Download Flow (operator-driven)

> **Added 2026-05-08 v0.7 (Védis Eikleið).** The operator tends the well — the agent
> never reaches the network. Downloads are an explicit operator-side ritual: invoke the
> CLI, read the consent prompt, confirm, and Mímisbrunnr fetches and verifies.

```
  OPERATOR-DRIVEN DOWNLOAD PIPELINE

  [Operator runs: heretic library download <source_id>]
  e.g., heretic library download prose_edda
       |
       v
  [CLI library subcommand: library_cmd.download(source_id)]
       |
       |  manifest.py: load manifest entry for source_id
       |    {
       |      source_id:   "prose_edda",
       |      title:       "Prose Edda (Brodeur translation)",
       |      url:         "https://gutenberg.org/files/18947/18947-0.txt",
       |      sha256:      "<expected hash>",
       |      approx_size: "280 KB",
       |      license:     "Public Domain"
       |    }
       |  IF source not found in manifest: raise LibraryManifestError; print error; exit
       |
       v
  [consent.py: prompt_operator_consent(manifest_entry)]
       |
       |  Display to terminal:
       |    Source: Prose Edda (Brodeur translation)
       |      URL:     https://gutenberg.org/files/18947/18947-0.txt
       |      Size:    ~280 KB
       |      License: Public Domain
       |    Confirm download? [y/N]
       |
       |  IF --yes flag passed: skip interactive prompt (consent treated as given)
       |  IF operator types anything other than 'y' or 'Y':
       |    log: "Download cancelled by operator"
       |    return ConsentRefusedResult (F-6)  -- exit cleanly, no partial state
       |
       v
  [downloader.py: async_download(url, dest_path, expected_sha256)]
       |
       |  dest_path = store.py: <data_dir>/library/sources/prose_edda/text.txt
       |  tmp_path  = dest_path.with_suffix(".tmp")
       |              (atomic write: download to .tmp, move to final only on success)
       |
       |  async with httpx.AsyncClient() as client:
       |    async with client.stream("GET", url) as response:
       |      sha256_hasher = hashlib.sha256()
       |      async for chunk in response.aiter_bytes(chunk_size=65536):
       |        tmp_file.write(chunk)
       |        sha256_hasher.update(chunk)
       |  computed_sha256 = sha256_hasher.hexdigest()
       |
       |  IF computed_sha256 != expected_sha256:
       |    tmp_path.unlink()              <- delete partial file (no corrupt state)
       |    raise IntegrityError(
       |      f"SHA-256 mismatch for {source_id}: "
       |      f"expected {expected_sha256}, got {computed_sha256}"
       |    )
       |    (F-2: mismatch deletes partial file + raises; caller prints error + exits)
       |
       |  os.replace(tmp_path, dest_path)  <- atomic rename (POSIX + Windows)
       |  (os.replace is atomic within the same filesystem — no partial visible state)
       |
       v
  [store.py: update_local_manifest(source_id, status="downloaded")]
       |
       |  Appends or updates the source record in
       |  <data_dir>/library/manifest.yaml with:
       |    downloaded: true
       |    downloaded_at: <ISO timestamp>
       |    sha256_verified: true
       |
       v
  [index.py: build_or_update_index(source_id)]
       |
       |  Read sources/<source_id>/text.txt
       |  Build line-offset table: list[int] where [i] = byte offset of line i
       |  Write index to sources/<source_id>/index.json (or .pkl — TBD by Architect)
       |  Index is used by library.search (Path A) and library.get_text (Path B) to
       |  seek directly to requested line numbers without scanning from the start.
       |
       v
  [CLI: print success message]
    "prose_edda downloaded and indexed. Use 'heretic library list' to verify."


  CLI FLAGS:
    heretic library download <source_id>          interactive consent prompt
    heretic library download <source_id> --yes    skip prompt (consent implied)
    heretic library download --all                download all manifest sources (each prompts)
    heretic library download --all --yes           download all, no prompts (batch mode)
```

---

#### 4.14.1.1 Endurdrykkr — Resumable Downloads (v0.7.2)

> **Added 2026-05-09 v0.7.2 (Védis Eikleið).** *Endurdrykkr* — the resumed
> drink. When `.heretic_tmp` exists from an interrupted prior download, the
> next download attempt continues from the offset rather than starting over.
> Same Mímisbrunnr Downloader; new failure-recovery path.

```
  ENDURDRYKKR — RESUME FLOW

  Step 1 — Consent gate (UNCHANGED from v0.7)
    prompt_for_download(source, auto_yes=auto_yes)
    # M-1: gate runs FIRST, before any disk inspection or network activity.

  Step 2 — Resume detection (NEW v0.7.2)
    tmp_path = dest_path.with_suffix(".heretic_tmp")
    partial_size = tmp_path.stat().st_size if tmp_path.exists() else 0

    if partial_size > 0:
        # Hash existing partial bytes BEFORE any network call
        # so the running SHA-256 produces the full-file digest.
        hasher = hashlib.sha256()
        with tmp_path.open("rb") as fh:
            while chunk := fh.read(_CHUNK_SIZE):
                hasher.update(chunk)
        total_bytes = partial_size
        request_headers = {"Range": f"bytes={partial_size}-"}
        write_mode = "ab"   # APPEND
        log.info("Resuming download of %r from byte %d", source.id, partial_size)
    else:
        hasher = hashlib.sha256()
        total_bytes = 0
        request_headers = {}
        write_mode = "wb"   # WRITE FRESH

  Step 3 — HTTP stream + status dispatch (NEW v0.7.2)
    async with httpx.AsyncClient(...) as client:
        async with client.stream("GET", source.url, headers=request_headers) as resp:

            # 206 Partial Content — server honoured Range; append to tmp
            if resp.status_code == 206:
                pass  # write_mode already "ab"

            # 200 OK — server returned full body. If we asked for Range and got 200,
            # the server doesn't support Range. Reset hasher; truncate tmp; restart.
            elif resp.status_code == 200:
                if partial_size > 0:
                    log.info(
                        "Resume requested but server returned 200; "
                        "restarting fresh download of %r", source.id,
                    )
                    hasher = hashlib.sha256()
                    total_bytes = 0
                    write_mode = "wb"   # truncate

            # 416 Range Not Satisfiable — partial bytes don't align with current source.
            # Delete tmp and raise a recoverable error.
            elif resp.status_code == 416:
                tmp_path.unlink(missing_ok=True)
                raise LibraryDownloadError(
                    "Range not satisfiable; partial removed; retry fresh"
                )

            # All other status codes — error
            else:
                raise LibraryDownloadError(...)

            # Step 3a — Stream body, append/write, update hasher
            with tmp_path.open(write_mode) as fh:
                async for chunk in resp.aiter_bytes(chunk_size=_CHUNK_SIZE):
                    total_bytes += len(chunk)
                    if total_bytes > size_cap:
                        # NON-RESUMABLE failure — delete tmp
                        fh.close()
                        self._cleanup_tmp(tmp_path)
                        raise IntegrityError(...)
                    hasher.update(chunk)
                    fh.write(chunk)

  Step 4 — SHA-256 verify (UNCHANGED contract; correctness preserved by Step 2 + 3)
    computed_sha256 = hasher.hexdigest()
    if source.sha256 is not None and computed_sha256 != source.sha256:
        # NON-RESUMABLE failure — partial bytes are poisoned
        self._cleanup_tmp(tmp_path)
        raise IntegrityError(...)

  Step 5 — Atomic rename (UNCHANGED)
    os.replace(str(tmp_path), str(dest_path))
```

```
  HTTP STATUS DISPATCH TABLE

  | Status                          | partial_size > 0   | partial_size == 0 |
  |---------------------------------|--------------------|-------------------|
  | 206 Partial Content             | resume (append)    | (server gave 206  |
  |                                 |                    |  unprovoked —     |
  |                                 |                    |  treat as 200)    |
  | 200 OK                          | RESTART FRESH      | normal fresh DL   |
  | 416 Range Not Satisfiable       | delete + raise     | n/a (we sent no   |
  |                                 |                    |  Range header)    |
  | 4xx (other)                     | preserve tmp +     | preserve any tmp  |
  |                                 | raise              | + raise           |
  | 5xx                             | preserve tmp +     | preserve any tmp  |
  |                                 | raise              | + raise           |

  RESUMABLE vs NON-RESUMABLE FAILURE — tmp file disposition:

    Resumable (preserve .heretic_tmp):
      - httpx.TransportError  (DNS / TCP / TLS)
      - httpx.TimeoutException
      - httpx.RequestError    (any other request-level error)
      - OSError during disk write (transient I/O)
      - 4xx / 5xx HTTP status (other than 416)

    Non-resumable (delete .heretic_tmp):
      - IntegrityError from SHA-256 mismatch  (file at source has changed)
      - IntegrityError from safety size cap   (response body too large)
      - 416 Range Not Satisfiable             (partial bytes don't align)
```

> **New invariants added by v0.7.2:**
> - **M-7:** Full-file SHA-256 after resume equals SHA-256 of the bytes that
>   would have been written by a single uninterrupted download. Partial-byte
>   hashing across the seam is the load-bearing mechanism.
> - **M-8:** Resumable failures preserve `.heretic_tmp`; non-resumable
>   failures delete it. The dispositioning table above is the canonical record.
> - **M-9:** Server returns 200 in response to a Range request → reset hasher,
>   truncate tmp, restart streaming write — without raising.

---

#### 4.14.2 Storage Layout

> **Added 2026-05-08 v0.7 (Védis Eikleið).** The library root lives under the
> user-data directory resolved by the `dirs` library (already a HERETIC dependency
> from v0.6.1). All paths are cross-platform by construction.

```
  STORAGE LAYOUT

  Root (resolved by dirs.user_data_dir("heretic") at runtime):

    Unix:
      ~/.local/share/heretic/library/

    Windows:
      %APPDATA%\heretic\library\
      (i.e., C:\Users\<username>\AppData\Roaming\heretic\library\)

    macOS:
      ~/Library/Application Support/heretic/library/


  Directory tree under library root:

    library/
    |
    ├── manifest.yaml                    <- operator-local manifest
    │                                       (authoritative for what is downloaded)
    │                                       Updated by store.py after each download.
    │                                       Initially absent; first download creates it.
    │
    └── sources/
        |
        ├── prose_edda/
        │   ├── text.txt                 <- downloaded UTF-8 plain text
        │   └── index.json               <- line-offset table (built by index.py)
        │
        ├── poetic_edda/
        │   ├── text.txt
        │   └── index.json
        │
        ├── heimskringla/
        │   ├── text.txt
        │   └── index.json
        │
        ├── volsunga_saga/
        │   ├── text.txt
        │   └── index.json
        │
        └── erik_the_red_saga/
            ├── text.txt
            └── index.json


  Naming invariant:
    Each source occupies exactly one subdirectory under sources/.
    The subdirectory name = source_id (snake_case, as defined in the manifest).
    text.txt is always the canonical corpus file for a plain-text source.
    index.json is always the line-offset index file.
    No other files are created in sources/<source_id>/ by mimisbrunnr/.

  Manifest format (manifest.yaml excerpt):
    sources:
      - source_id:      prose_edda
        title:          "Prose Edda (Brodeur translation)"
        url:            "https://gutenberg.org/files/18947/18947-0.txt"
        sha256:         "<hash — verified at Architect scaffold time>"
        license:        "Public Domain"
        approx_size:    "280 KB"
        downloaded:     true
        downloaded_at:  "2026-05-08T14:32:00Z"
        sha256_verified: true
      - source_id:      poetic_edda
        title:          "Poetic Edda (Bellows translation)"
        url:            "..."
        sha256:         "..."
        license:        "Public Domain"
        approx_size:    "600 KB"
        downloaded:     false

  The starter manifest (shipped with HERETIC as a package asset) lists all 5 Norse sources
  with their URLs and expected SHA-256 hashes. The operator-local manifest.yaml tracks
  what has actually been downloaded. store.py merges the two on load.
```

---

#### 4.14.2.1 Index auto-rebuild on corruption (v0.7.3)

> **Added 2026-05-09 v0.7.3 (Védis Eikleið).** Continuity discipline extension —
> the Endurdrykkr disposition (v0.7.2) now applies to the keyword index as well
> as the source bytes. When the index is missing or corrupt but source files
> are present, search() rebuilds automatically.

```
  KEYWORDINDEX.search() — AUTO-REBUILD FLOW (v0.7.3)

  if self._cache is None:
      self._cache = self._load_or_rebuild_cache()

  _load_or_rebuild_cache() decision tree:

      index_path = data_dir / "keyword_index.jsonl"

      ┌─────────────────────────────────────────────────┐
      │ index_path.exists() ?                           │
      └─────────────────────────────────────────────────┘
                  │            │
                  ▼ yes        ▼ no
        ┌──────────────────┐  ┌──────────────────────────┐
        │ load entries     │  │ log INFO "no index file" │
        │ from disk        │  │ proceed to rebuild path  │
        └──────────────────┘  └──────────────────────────┘
                  │
                  ▼
        ┌──────────────────────────────────┐
        │ entries non-empty?                │
        └──────────────────────────────────┘
                  │            │
                  ▼ yes        ▼ no (or load raised LibraryIndexError)
        ┌──────────────────┐  ┌──────────────────────────────┐
        │ return entries   │  │ log WARNING "index empty/    │
        │ (happy path —    │  │  corrupt" — proceed to       │
        │  no rebuild)     │  │  rebuild path                │
        └──────────────────┘  └──────────────────────────────┘
                                          │
                                          ▼
                              ┌──────────────────────────────┐
                              │ txt_files in data_dir?       │
                              └──────────────────────────────┘
                                          │            │
                                          ▼ yes        ▼ no
                              ┌──────────────────┐  ┌──────────────────┐
                              │ self.build()     │  │ raise            │
                              │ (rebuild from    │  │ LibraryIndexError│
                              │  source files)   │  │ — operator must  │
                              │ return _cache    │  │  download first  │
                              └──────────────────┘  └──────────────────┘

  KEY PROPERTIES:

    1. Non-disruptive: search() returns hits as if the rebuild were
       transparent. The operator may not even notice it happened
       (only the INFO/WARNING logs reveal it).

    2. Behaviour-preserving on the truly-unrecoverable case: if no
       .txt files exist either (no source has been downloaded), the
       same actionable LibraryIndexError is raised as before — the
       operator gets pointed to 'heretic library download'.

    3. Manual rebuild-index CLI unchanged: 'heretic library rebuild-index'
       still works for operators who want to force a rebuild.

    4. Atomic rebuild: build() writes to a .heretic_tmp file and renames
       atomically. If the rebuild itself fails partway, the existing
       (possibly stale) index is preserved.
```

> **No new privacy invariants in v0.7.3.** This is a behaviour extension on the
> Endurdrykkr lineage, not a new discipline. The Mímisbrunnr offline / consent /
> SHA-256 / privacy invariants from v0.7 are untouched.

---

#### 4.14.3 Privacy Invariants

> **Added 2026-05-08 v0.7 (Védis Eikleið).** The well is deaf to the network during a
> ceremony. It answers only from what the operator has already placed inside it.
> These invariants are sealed at v0.7 and carry forward to all future library tiers.

```
  LIBRARY PRIVACY INVARIANTS (v0.7 — sealed)

  I-LIB-1: Disabled by default
    skilningr.library.enabled: false in all config paths.
    If disabled:
      LibrarySense is NOT mounted in ToolDispatcher at TENGSL.
      Agent receives no library.* tool definitions.
      No library tool_call can be dispatched.
    Operator must explicitly set enabled: true in heretic.yaml to activate the sense.

  I-LIB-2: Per-source consent enforced
    No source is downloaded without explicit operator confirmation.
    consent.py displays source metadata (URL, size, license) and requires 'y' or --yes.
    A consent refusal cancels the download immediately with no partial file left on disk.
    The agent CANNOT trigger a download. Downloads are operator-CLI-only.
    (The library.search / library.get_text / library.list_sources tools are read-only.
     None of them call downloader.py. No tool_call can initiate a download.)

  I-LIB-3: Queries are LOCAL keyword search ONLY
    library.search performs re-based iteration over local text.txt files.
    No network connection is opened during a search query.
    No external API is called.
    The agent's query stays on the operator's machine.

  I-LIB-4: Offline-by-design during agent queries
    Mímisbrunnr NEVER reaches the network during an agent ceremony.
    The network is only touched during operator-initiated downloads (CLI only).
    Once text.txt is on disk and indexed, all subsequent queries are file I/O only.
    LibraryClient has no httpx import. downloader.py is never called by LibraryClient.

  I-LIB-5: Storage path traversal rejected
    store.resolve_source_path(source_id) resolves
      <data_dir>/library/sources/<source_id>/text.txt
    and verifies the resolved path is within the library root.
    A source_id containing path traversal sequences (e.g., "../../../etc/passwd")
    is rejected before any file handle opens.
    Raises LibraryPathError (caught by LibraryClient; returned as error ToolResult).

  I-LIB-6: Index files never leave the library root
    index.py writes line-offset tables to sources/<source_id>/index.json only.
    No index data is written to arbitrary paths.
    Path for index file is derived by the same store.resolve_source_path contract.

  I-LIB-7: No corpus data is sent to the agent model
    library.search returns context_text excerpts (one surrounding line).
    library.get_text returns the requested line range.
    Neither returns the entire corpus. The corpus never leaves the local machine.
    Excerpt size is bounded by max_results * context_window (Architect sets limits).

  BOUNDARY SUMMARY:
    Download (network reach): operator CLI only, per-source, consent-gated
    Search / retrieve (agent tools): local file I/O only, never network
    Data direction:    network → disk (download only)
                       disk → tool_result (query only)
    The two directions are strictly separated by code path — downloader.py vs LibraryClient.
```

```
  MÍMISBRUNNR FAILURE MODES

  F-1: Download fail (network error)
    Cause: httpx.ConnectError, DNS failure, server unreachable during download.
    downloader.py raises DownloadNetworkError.
    tmp file is deleted (never partially committed).
    CLI prints: "Download failed: <detail>. No file written."
    Library state unchanged from before the attempt.

  F-2: SHA-256 mismatch (integrity failure)
    Cause: downloaded bytes do not match expected SHA-256 in manifest.
    downloader.py deletes tmp file, raises IntegrityError.
    CLI prints: "Integrity check failed for <source_id>. File deleted. Do not use."
    No corrupt state is left on disk.
    Operator should verify the manifest hash or re-download.

  F-3: Source missing on disk (agent query — source listed but not downloaded)
    Cause: agent calls library.search or library.get_text for a source_id where
           text.txt does not exist on disk (source in manifest but not downloaded).
    LibraryClient.search(): skips the source, returns matches from other sources only.
    LibraryClient.get_text(): returns error ToolResult:
      {"error": "library_source_not_downloaded",
       "source_id": "<id>",
       "hint": "operator must run: heretic library download <source_id>"}
    No crash. Agent can inform the user.

  F-4: Index empty — operator has not downloaded any source
    Cause: library is enabled but no source has been downloaded.
           manifest exists (shipped starter) but no text.txt files on disk.
    library.search: returns empty results list with a hint field:
      {"results": [], "hint": "No sources downloaded. Run: heretic library download <source_id>"}
    library.get_text: returns F-3 error for any source_id requested.
    library.list_sources: returns all 5 manifest entries with "downloaded": false for each.
    No crash. This is the expected initial state for a fresh install.

  F-5: Storage path traversal attempt
    Cause: source_id in a tool_call argument contains traversal sequences
           (e.g., source_id = "../../etc/passwd").
    store.resolve_source_path raises LibraryPathError before any file open.
    LibraryClient catches and returns error ToolResult:
      {"error": "library_path_violation",
       "source_id": "<malicious id>",
       "detail": "source_id resolves outside the library root"}
    No file I/O performed. No crash. Turn continues.

  F-6: Consent refused (download cancelled cleanly)
    Cause: operator answers 'n' or presses Enter at the consent prompt.
    consent.py returns ConsentRefused; download is not attempted.
    CLI prints: "Download cancelled."
    No partial file. No manifest change. Clean exit.
    Return code 0 (cancelled is not an error; operator made an intentional choice).

  F-7: Corpus reading I/O error (graceful degrade)
    Cause: text.txt exists but is unreadable (permissions error, disk fault, corrupted file).
    LibraryClient catches IOError during file read.
    library.search: skips the unreadable source; includes it in a "degraded_sources" list
      in the tool_result so the agent can report the issue.
    library.get_text: returns error ToolResult:
      {"error": "library_read_error", "source_id": "<id>", "detail": "<OS message>"}
    No crash. Turn continues.


  ERROR CLASS HIERARCHY (mimisbrunnr/errors.py):
    LibraryError (base, extends SkilningrError)
      |-- LibraryManifestError       (source not found in manifest)
      |-- LibraryPathError           (path traversal rejected — F-5)
      |-- DownloadNetworkError       (F-1)
      |-- IntegrityError             (F-2 — SHA-256 mismatch)
      |-- LibrarySourceNotDownloaded (F-3)
      |-- LibraryReadError           (F-7)
    ConsentRefused                   (F-6 — not an error; returned as a typed result)
    All LibraryError subclasses caught by LibraryClient; none propagate to ToolDispatcher.
```

---

## 16. L5 Skilningr — Five Senses + MCP Server Component Diagram (v0.7)

> **Added 2026-05-08 v0.6 (Védis Eikleið). Extended 2026-05-08 v0.6.1 (Védis Eikleið).
> Extended 2026-05-08 v0.6.2 (Védis Eikleið).
> Extended 2026-05-08 v0.6.x (Védis Eikleið) — mcp_server.py module added; three-door
> transport surface mapped; ToolDispatcher reuse across all three shown.
> Extended 2026-05-08 v0.7 (Védis Eikleið) — LibrarySense (L5.9 Mímisbrunnr light tier)
> added as fifth sense; mimisbrunnr/ subsystem mapped (manifest.py, downloader.py, store.py,
> index.py, consent.py, errors.py); LibraryConfig with enabled:false default; 3 new library
> tools (library.search, library.get_text, library.list_sources); ToolDispatcher updated to
> route "library.*"; tool count updated to 19 when all five senses enabled.**
> Maps the internal structure of the `skillingr/` module: five sense subpackages
> (Smiðja, Minni, Skepja, Leið, Library) and the MCP server adapter module.
>
> **Position in the body:** Skilningr is the discernment layer — the organ that decides
> which sense to invoke when the agent reaches. In v0.7, five senses are mounted.
> In v0.6.x, a new door opened: an MCP server sits parallel to the existing OpenAI tool_use
> path, routing through the same ToolDispatcher. One execution backend; three transport paths.
> In v0.7, the well opens: the fifth sense lets the agent drink from offline corpora.

```
  ============================================================
  SKILNINGR MODULE — src/heretic/skilningr/    (v0.7 Five Senses + Three Doors)
  ============================================================

  skillingr/
  |
  ├── config_model.py    SkilningrConfig
  │                      |  smidja:      SmidjaConfig      (v0.6 + v0.6.1)
  │                      |    brunhand: BrunhandConfig
  │                      |    forge:    ForgeConfig
  │                      |  minni:     MinniConfig         (v0.6.2)
  │                      |  skepja:    SkepjaConfig        (v0.6.2)
  │                      |  leid:      LeidConfig          (v0.6.2)
  │                      |  library:   LibraryConfig       (v0.7 NEW)
  │                      |    enabled:          bool       default false
  │                      |    max_results:       int       default 10
  │                      |    max_context_lines: int       default 3
  │                      |    data_dir:          str       default "" (resolved by dirs)
  │                      |    sources:           list[str] default [] (all available)
  │                      |  mcp_server: McpServerConfig    (v0.6.x)
  │                      |    enabled:           bool      default false
  │                      |    transport:         str       "stdio" | "http"   default "stdio"
  │                      |    host:              str       default "127.0.0.1"
  │                      |    port:              int       default 8645
  │                      |    allow_remote_bind: bool      default false
  │
  ├── errors.py          SkilningrError (base)
  │                      |-- SenseUnavailableError
  │                      |-- ToolDispatchError
  │                      |-- SandboxViolationError   (v0.6.2)
  │                      |-- CommandNotAllowedError  (v0.6.2)
  │                      |-- UrlNotAllowedError      (v0.6.2)
  │                      |-- FilesizeLimitError      (v0.6.2)
  │                      |-- McpServerError          (v0.6.x)
  │                      |   |-- TransportError      (stdio EOF; HTTP bind failure)
  │                      |   |-- ProtocolError       (malformed JSON-RPC; see F-MCP-2)
  │                      |-- LibraryError            (v0.7 NEW — base for all library errors)
  │                          |-- LibraryManifestError
  │                          |-- LibraryPathError
  │                          |-- DownloadNetworkError
  │                          |-- IntegrityError
  │                          |-- LibrarySourceNotDownloaded
  │                          |-- LibraryReadError
  │
  ├── sandbox.py         Shared validation primitives (v0.6.2)
  │                      |  path_within_allowed_roots(raw_path, allowed_roots) -> Path
  │                      |  command_allowlist_check(tokens, allowlist) -> None
  │                      |  url_allowlist_match(url, patterns) -> None
  │
  ├── dispatcher.py      ToolDispatcher  (v0.7 — five senses registered)
  │                      |  async dispatch(tool_call) -> ToolResult
  │                      |    "smidja.*"  → SmidjaSense
  │                      |    "minni.*"   → MinniSense
  │                      |    "skepja.*"  → SkepjaSense
  │                      |    "leid.*"    → LeidSense
  │                      |    "library.*" → LibrarySense    (v0.7 NEW)
  │                      |    unknown    → error ToolResult (F-6 / F-MCP-3)
  │
  │                      ToolDispatcher is the single dispatch seam across all three doors.
  │                      Door 1 (OpenAI tool_use via L1 Bifröst) --> ToolDispatcher
  │                      Door 2 (MCP stdio via McpServer)        --> ToolDispatcher
  │                      Door 3 (MCP HTTP/SSE via McpServer)     --> ToolDispatcher
  │                      Same instance. Same routing table. Same execution path.
  │
  ├── mimisbrunnr/       Mímisbrunnr subsystem (v0.7 NEW)
  │   │                  The corpus backend — operator-facing corpus management.
  │   │                  Never called directly by agent tools; accessed only via LibraryClient.
  │   │
  │   ├── __init__.py
  │   ├── INTERFACE.md   subsystem contract (storage layout, consent invariant, SHA-256)
  │   ├── manifest.py    NorseStarterPackManifest dataclass; load/save manifest.yaml
  │   │                  |  load_starter_manifest() -> list[SourceEntry]
  │   │                  |    (reads the package-asset starter manifest — 5 Norse sources)
  │   │                  |  load_local_manifest(data_dir) -> list[SourceEntry]
  │   │                  |    (reads operator-local manifest.yaml tracking downloaded state)
  │   │                  |  merge(starter, local) -> list[SourceEntry]
  │   │                  |    (starter entries + downloaded status from local)
  │   │
  │   ├── downloader.py  async httpx download + SHA-256 streaming verify + atomic write
  │   │                  |  async download(url, dest_path, expected_sha256) -> None
  │   │                  |    streams to .tmp, verifies hash, os.replace → final path
  │   │                  |    deletes .tmp + raises IntegrityError on SHA-256 mismatch
  │   │
  │   ├── store.py       local filesystem layout manager
  │   │                  |  get_library_root(data_dir: str | None) -> Path
  │   │                  |    uses dirs.user_data_dir("heretic") / "library" if data_dir empty
  │   │                  |  resolve_source_path(source_id, library_root) -> Path
  │   │                  |    returns library_root / "sources" / source_id / "text.txt"
  │   │                  |    validates resolved path is within library_root (traversal block)
  │   │                  |    raises LibraryPathError if validation fails
  │   │                  |  update_local_manifest(source_id, status, library_root) -> None
  │   │                  |    writes/updates manifest.yaml with downloaded state
  │   │
  │   ├── index.py       line-offset index — build and query
  │   │                  |  build_index(text_path: Path) -> list[int]
  │   │                  |    scans text.txt; records byte offset of each line start
  │   │                  |    writes index to sources/<source_id>/index.json
  │   │                  |  load_index(source_id, library_root) -> list[int]
  │   │                  |    loads pre-built index.json; raises LibraryReadError if absent
  │   │                  |  search(query: str, text_path: Path, index: list[int],
  │   │                  |         max_results: int, context_lines: int) -> list[Match]
  │   │                  |    re.search(query) over each line; collect Match objects
  │   │                  |    Match: { line_number, context_text (surrounding N lines) }
  │   │                  |  get_lines(text_path: Path, index: list[int],
  │   │                  |            start: int, end: int) -> str
  │   │                  |    seek to byte offset index[start]; read through index[end]
  │   │
  │   ├── consent.py     operator-confirmation flow
  │   │                  |  prompt_operator_consent(entry: SourceEntry,
  │   │                  |                          skip: bool = False) -> ConsentResult
  │   │                  |    displays: title, URL, size, license
  │   │                  |    if skip=True (--yes flag): return ConsentGranted immediately
  │   │                  |    reads stdin; 'y'/'Y' → ConsentGranted; anything else → ConsentRefused
  │   │
  │   └── errors.py      LibraryError hierarchy (see errors.py entry above)
  │
  ├── mcp_server.py      McpServer  (v0.6.x — unchanged from v0.6.x description)
  │                      (handles_tools_list now collects from 5 senses; max 19 tools)
  │
  └── senses/
      |
      ├── smidja/        Smiðja — the workshop (v0.6 + v0.6.1)
      │   (unchanged — see §4.11 for full flow)
      │
      ├── minni/         Minni — the filesystem library (v0.6.2)
      │   (unchanged — see §4.12 for full flow)
      │
      ├── skepja/        Skepja — the terminal (v0.6.2)
      │   (unchanged — see §4.12.1 for full flow)
      │
      ├── leid/          Leið — the road (v0.6.2)
      │   (unchanged — see §4.12.2 for full flow)
      │
      └── library/       Library — the well (v0.7 NEW)
          ├── __init__.py
          ├── INTERFACE.md   sense contract (3 tools, offline-only search, privacy invariants)
          ├── config_model.py  LibraryConfig
          ├── errors.py      LibraryError hierarchy re-exported from mimisbrunnr/errors.py
          ├── client.py      LibraryClient — wraps mimisbrunnr/ for sense-level operations
          │                  |  search(query, max_results) -> list[Match]
          │                  |    loads merged manifest; for each downloaded source:
          │                  |      load_index → index.search → collect matches
          │                  |    returns ranked list[Match] with source attribution
          │                  |  get_text(source_id, start_line, end_line) -> dict
          │                  |    store.resolve_source_path → index.get_lines → return
          │                  |  list_sources() -> list[dict]
          │                  |    merge starter + local manifest → return with downloaded flag
          │                  |  All methods: pure local I/O. No network access.
          ├── tools.py       3 tool definitions
          │                  |  library.search
          │                  |    { "query": str, "max_results": int (optional, default 10) }
          │                  |    Returns: list of { source_id, line_number, context_text,
          │                  |                        source_title } + total_searched_sources
          │                  |  library.get_text
          │                  |    { "source_id": str, "start_line": int, "end_line": int }
          │                  |    Returns: { source_id, source_title, start_line, end_line,
          │                  |               text, license }
          │                  |  library.list_sources
          │                  |    {}  (no arguments)
          │                  |    Returns: list of { source_id, title, license,
          │                  |                        approx_size, downloaded }
          └── sense.py       LibrarySense orchestrator
                             |  open() -> None
                             |    validates library root exists (creates if absent)
                             |    loads merged manifest; logs source count + downloaded count
                             |    IF no sources downloaded: logs hint about heretic library download
                             |  close() -> None  (no-op; no persistent resource)
                             |  dispatch_tool_call(tool_call) -> ToolResult
                             |    routes to LibraryClient.search / get_text / list_sources
                             |    wraps all LibraryError subclasses → error ToolResult
                             |    never raises to ToolDispatcher


  ============================================================
  LIBRARY SENSE DELEGATION CHAIN
  ============================================================

  Agent tool_call  -->  ToolDispatcher  -->  LibrarySense
                                                  |
                                                  v
                                           LibraryClient
                                                  |
                                     +-----------+-----------+
                                     |           |           |
                                     v           v           v
                                manifest.py  index.py   store.py
                                (what exists) (search)  (path resolve)
                                     |
                                     v
                             mimisbrunnr/sources/<source_id>/text.txt
                                     |
                                     v
                             tool_result with source attribution
                             { source_id, line_number, context_text, source_title }

  Download (operator CLI only — never via agent tool_call):
  heretic library download  -->  consent.py  -->  downloader.py  -->  store.py  -->  index.py
  (CLI subcommand)               (prompt)         (httpx + SHA256)   (manifest)    (rebuild)


  ============================================================
  THREE-DOOR TRANSPORT DIAGRAM — v0.7 (unchanged routing; fifth sense added)
  ============================================================

                    ┌──────────────────────────────────────────────────┐
                    │              L5 Skilningr — v0.7                 │
                    │                                                  │
  Door 1            │                                                  │
  OpenAI tool_use   │                                                  │
  (heretic light    │                                                  │
   / heretic serve) │                                                  │
  Agent             │                                                  │
  POST /v1/chat/    │                                                  │
  completions  ─────┼──> L1 Bifröst                                   │
                    │          │                                       │
                    │          ▼                                       │
  Door 2            │    ┌─────────────┐                               │
  MCP stdio         │    │    Tool     │                               │
  (Claude Desktop)  │    │ Dispatcher  │◄───────────────────────┐     │
  stdin/stdout ─────┼──> │             │                        │     │
                    │    └──────┬──────┘                        │     │
  Door 3            │           │                               │     │
  MCP HTTP/SSE      │           │ routes by prefix              │     │
  (browser-friendly │           ├──> SmidjaSense                │     │
  / Tailscale)      │           ├──> MinniSense                 │     │
  POST /mcp    ─────┼──> McpServer    SkepjaSense               │     │
  GET /mcp/events   │    │      │──> LeidSense                  │     │
                    │    │      └──> LibrarySense (v0.7 NEW)    │     │
                    │    └──────────────────────────────────────┘     │
                    │    (McpServer calls dispatcher.dispatch()        │
                    │     — same instance used by Bifröst)             │
                    │                                                  │
                    └──────────────────────────────────────────────────┘

  Arrows to ToolDispatcher:
    L1 Bifröst  ──────────────────────────────> ToolDispatcher
    McpServer (stdio transport)  ─────────────> ToolDispatcher
    McpServer (HTTP/SSE transport) ───────────> ToolDispatcher
    All three share one instance. No duplication of dispatch logic.


  ============================================================
  TOOL COUNT SUMMARY — v0.7
  ============================================================

  Sense      Prefix    Tools    Notes
  ---------  --------  -------  -------------------------------------
  Smiðja     smidja    9        6 Brúarhönd + 3 Forge (v0.6 + v0.6.1)
  Minni      minni     3        read_file, write_file, list_directory (v0.6.2)
  Skepja     skepja    2        run_command, get_working_directory (v0.6.2)
  Leið       leid      2        fetch_url, extract_text (v0.6.2)
  Library    library   3        search, get_text, list_sources (v0.7 NEW)
  ---------  --------  -------  -------------------------------------
  TOTAL                19       when all five senses are enabled
                                (agent receives only tools for enabled senses)


  ============================================================
  FIVE-SENSE LIFECYCLE AT TENGSL (ceremony open) — v0.7
  ============================================================

  CLI.TENGSL():
    ToolDispatcher._senses = {}
    IF smidja.enabled (brunhand or forge):
      SmidjaSense.open()     → dual-half probe (Brúarhönd + Forge independently)
      _senses["smidja"] = SmidjaSense
    IF minni.enabled:
      MinniSense.open()      → validates allowed_roots paths exist
      _senses["minni"] = MinniSense
    IF skepja.enabled:
      SkepjaSense.open()     → validates working_directory; logs allowlist size
      _senses["skepja"] = SkepjaSense
    IF leid.enabled:
      LeidSense.open()       → logs url_allowlist_patterns; warns if wildcard
      _senses["leid"] = LeidSense
    IF library.enabled:
      LibrarySense.open()    → resolves library root; loads merged manifest
                               logs downloaded source count
                               IF 0 downloaded: log.info hint about heretic library download
      _senses["library"] = LibrarySense

    Each open() is wrapped in independent try/except.
    Failure of any one sense does not abort the others.
    A failed sense is not added to _senses; its tools are not offered to the agent.


  ============================================================
  FIVE-SENSE LIFECYCLE AT SLOKNA (ceremony close) — v0.7
  ============================================================

  CLI.SLOKNA():
    FOR sense_id, sense in _senses.items():
      try:
        await sense.close()
      except Exception:
        log.warning(f"Sense {sense_id!r} failed to close cleanly — ignoring")

    Each close() is isolated.
    LibrarySense.close() is a no-op (no persistent resource — all file handles close per call).
    Minni, Skepja, Leið have no-op close().
    Smiðja close() shuts down both httpx.AsyncClient instances.


  ============================================================
  MCP SERVER LIFECYCLE AT TENGSL / SLOKNA (unchanged from v0.6.x)
  ============================================================

  CLI.TENGSL() — when heretic mcp is launched:
    McpServerConfig read from heretic.yaml (skilningr.mcp_server block)
    IF mcp_server.enabled:
      ToolDispatcher built from enabled senses (same as Door 1 path — now up to 5 senses)
      IF transport == "stdio":
        McpServer.start_stdio()     blocks on stdin; exits on EOF (F-MCP-1)
      IF transport == "http":
        IF allow_remote_bind: false AND host != "127.0.0.1":
          abort with McpServerError(TransportError) + user message
        McpServer.start_http(host, port)
          uvicorn starts on configured host:port (already in dep tree from v0.4)

  CLI.SLOKNA() — graceful close:
    stdio:  EOF on stdin triggers StdioTransport close → McpServer.shutdown()
              → ToolDispatcher.close() → each sense.close()
    http:   SIGTERM / KeyboardInterrupt → uvicorn shutdown
              → McpServer.shutdown() → ToolDispatcher.close() → each sense.close()
    Each sense.close() wrapped in independent try/except.


  ============================================================
  INVARIANTS — v0.7
  ============================================================
  - ToolDispatcher is the single dispatch backend across all three transport doors.
    The dispatch routing table is built once at TENGSL. All three doors read it.
  - McpServer never raises to CLI. All handler exceptions are caught and returned
    as JSON-RPC error objects or MCP isError=true results.
  - Bearer token is never logged. MCP HTTP auth follows the same scrubbing invariant
    as L1 Bifröst and Brúarhönd HTTP clients.
  - allow_remote_bind defaults false. Non-localhost exposure requires explicit opt-in.
  - Tool schema conversion is lossless. inputSchema = parameters (same JSON Schema).
    No information is added or removed by convert_to_mcp_tool().
  - tools/list returns only enabled senses' tools. A disabled sense contributes 0 tools
    on the MCP path, exactly as it contributes 0 entries to the OpenAI tools[] array.
  - Library sense is offline-by-design during agent queries. No network call is made
    by LibraryClient or LibrarySense. Only downloader.py reaches the network, and
    downloader.py is only called by the operator CLI subcommand.
  - Library downloads require per-source consent. The agent cannot initiate a download.
    All three library tools (search, get_text, list_sources) are read-only.
  - SHA-256 mismatch during download: partial file deleted immediately; no corrupt state.
  - Storage path traversal in any tool_call argument: rejected by store.resolve_source_path
    before any file handle opens.
```

---

*Drawn by Védis Eikleið, Cartographer for Vibe Coding, 2026-05-08.*
*Three sense rivers now flow toward the spirit: Tunga (out, voice), Hlust (in, voice), Sjón (in, image).*
*The body shows its eyes when the user speaks — not always, not uninvited, but when asked.*
*v0.5.1: the eye keeps its own watch now, frame by frame, breath by breath, into the ring.*
*v0.6: the hand reaches. The hand has learned to act — not only to perceive.*
*Four rivers: Tunga (out voice), Hlust (in voice), Sjón (in image), Smiðja (out action).*
*v0.5.2: the eye gains a second source. The screen shows the work; the webcam shows the worker.*
*Only when invited — stronger gate, stronger consent, the camera's light goes off when the ceremony ends.*
*v0.6.1: the workshop holds two anvils. Brúarhönd tends the living GUI; Forge drives headless Blender.*
*v0.6.2: three new rooms open in the longhouse — the library (Minni), the kitchen (Skepja), the road (Leið).*
*Seven senses mapped. The body is learning to read, to act, and to travel.*
*One arm reaches for the screen. The other reaches into the render. Both belong to the same hand.*
*v0.6.x: the workshop opens a third door. MCP agents may now enter — stdio or HTTP/SSE, as they prefer.*
*v0.7: the well opens. The spirit may now drink of the offline corpus — Eddas, sagas, the deep Norse word.*
*Five senses mapped. The well is sealed to the network during ceremony. Only the operator may tend it.*
*Mímisbrunnr answers from what has been placed inside it — never from what lies beyond the machine.*
*The ToolDispatcher stands in the center. All three doors lead to the same workbench.*
