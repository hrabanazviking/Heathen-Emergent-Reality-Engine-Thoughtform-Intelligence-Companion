# H.E.R.E.T.I.C. — Data Flow Map

**Last updated:** 2026-05-07 (corrective pass — Védis Eikleið, resolving audit findings A-2 + A-1 config key drift; tool routing format canonicalized to two-part `<sense_id>.<action>`; sense process labels de-prefixed; Kynding config keys aligned with LAYER_INTERFACES.md post-2d1312f)
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
       |  POST <chatterbox_endpoint>/tts  (or configured TTS API)
       |  body: {"text": "<agent greeting text>", "voice": "<configured voice>"}
       |
       |  <-- returns: audio/wav or audio/mp3 stream
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
       |       text --> L2 Rödd: Tunga --> ChatterBox TTS --> audio --> speakers
       |
       |-- if response contains tool_call(s) (case B):
       |       tool_call(s) --> L5 Skilningr (MCP dispatch)  [see §4.2]
       |       after tool results returned: final text --> L2 Rödd: Tunga
       v
  [L2 Rödd: Tunga]
       |
       |  POST <chatterbox_endpoint>/tts
       |  body: {"text": "<agent response>", "voice": "<configured voice>"}
       |
       |  <-- audio stream returned (warm)
       |
       |  audio plays through speakers
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
  [L2 Rödd: Tunga] --> ChatterBox --> speakers  (as in §4.1)
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
  [L2 Rödd: Tunga --> ChatterBox --> speakers]
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
              POST <chatterbox>/tts
              {text: "The shield mesh is ready..."}

  T+5200–5500ms ChatterBox synthesizes audio (~300ms)                         (wrm)

  T+5500ms    Audio begins playing through speakers

  T+5500ms    Session log event written:
              {type:"voice_turn_with_tool", transcript:"...", tool:"blender.run_script",
               tool_result_summary:"shield mesh created", ts_start: T+0, ts_audio_start: T+5500}
```

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
  Rödd (Tunga) → ChatterBox outward text-to-speech request          HTTP POST JSON
  ChatterBox → Rödd (Tunga) inward audio stream                     audio/wav or audio/mp3
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

*Drawn by Védis Eikleið, Cartographer for Vibe Coding, 2026-05-07.*
*The rivers do not invent themselves. They were always there — I only followed their course.*
