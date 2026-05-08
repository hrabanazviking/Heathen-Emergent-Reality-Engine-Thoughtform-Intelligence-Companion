# H.E.R.E.T.I.C. — Data Flow Map

**Last updated:** 2026-05-07 (corrective pass — Védis Eikleið, resolving audit findings A-2 + A-1 config key drift; tool routing format canonicalized to two-part `<sense_id>.<action>`; sense process labels de-prefixed; Kynding config keys aligned with LAYER_INTERFACES.md post-2d1312f) | 2026-05-07 v0.2 addendum — Védis Eikleið: voice flow mapped in full; §4.6 (voice flow, outbound only) added; §11 (L2 Rödd Tunga internal diagram) added; ChatterBox live contract (`/v1/audio/speech`) cross-referenced; stale `/tts` path references annotated; SYSTEM_OVERVIEW.md §7 updated | 2026-05-07 v0.3 addendum — Védis Eikleið: §4.7 (listening flow, inbound) added; §12 (L2 Rödd Hlust component diagram) added; §4.6.4 config table expanded to full 17-field schema matching RoddTtsConfig; §4.6.1 voice_id annotation corrected to WAV-path semantics; v0.2.x backlog items closed | 2026-05-07 v0.4.0 addendum — Védis Eikleið: §4.8 (UI flow — Summoning Circle substrate) added; §13 (L4 Vébond Eldahús component diagram) added; SYSTEM_OVERVIEW.md §7 updated with v0.4.0 in-progress status. Scope: WebSocket connection lifecycle, all server-push events (7) and client commands (5), reconnection semantics, failure modes, React component subscriptions, Zustand store as single UI truth, aesthetic token cross-reference. No Tauri shell in this map — v0.4.0 is browser-served. Tauri wrap deferred to v0.4.1. | 2026-05-07 v0.4.1 addendum — Védis Eikleið: §4.9 (Tauri shell flow — pre-staged) added; §14 (Tauri shell wrapper diagram) added; cross-references from §4.8 and §13 updated. Scope: full Tauri-startup → sidecar-spawn → WebView-load → shutdown sequence; all five failure modes; PID-file orphan recovery; Tauri command surface. WS protocol unchanged — the shell is a wrapper, not a new seam. SYSTEM_OVERVIEW.md §7 updated to reflect pre-stage status. | 2026-05-08 v0.5 addendum — Védis Eikleið: §4.10 (sight flow — on-demand, outbound vision) added; §15 (Sjón component diagram) added. Three sense rivers now charted: Tunga (out), Hlust (in voice), Sjón (in image). Cross-references added in §4.6 and §4.7 pointing to §4.10 as the third sense flow. Capability flag naming gap documented in §4.10.5 (LAYER_INTERFACES.md §L3 carries `?vision_screen`; AGENT_AGNOSTIC_PROTOCOL.md and §L1 carry `?vision_in` — gap flagged to Architect). SYSTEM_OVERVIEW.md §7 updated to mark v0.5 IN PROGRESS. | 2026-05-08 v0.5.1 addendum — Védis Eikleið: §4.10 extended with four new subsections (§4.10.7–§4.10.10) mapping periodic capture lifecycle, ring buffer, attach-policy decision tree, and the critical multi-monitor index asymmetry between on-demand and continuous modes. §15 Sjón component diagram extended with continuous-task pump and ring buffer. §4.10.10 is the key Forge contract: config.monitor_index=0 means different things in each mode (primary single screen in on-demand; all-monitors composite in continuous) — intentional by mss convention; documented explicitly so the implementation carries the correct semantics. SYSTEM_OVERVIEW.md §7 updated to mark v0.5.1 IN PROGRESS.
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

---

*Drawn by Védis Eikleið, Cartographer for Vibe Coding, 2026-05-08.*
*Three sense rivers now flow toward the spirit: Tunga (out, voice), Hlust (in, voice), Sjón (in, image).*
*The body shows its eyes when the user speaks — not always, not uninvited, but when asked.*
*v0.5.1: the eye keeps its own watch now, frame by frame, breath by breath, into the ring.*
