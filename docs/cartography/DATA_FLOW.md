# H.E.R.E.T.I.C. — Data Flow Map

**Last updated:** 2026-05-07 (corrective pass — Védis Eikleið, resolving audit findings A-2 + A-1 config key drift; tool routing format canonicalized to two-part `<sense_id>.<action>`; sense process labels de-prefixed; Kynding config keys aligned with LAYER_INTERFACES.md post-2d1312f) | 2026-05-07 v0.2 addendum — Védis Eikleið: voice flow mapped in full; §4.6 (voice flow, outbound only) added; §11 (L2 Rödd Tunga internal diagram) added; ChatterBox live contract (`/v1/audio/speech`) cross-referenced; stale `/tts` path references annotated; SYSTEM_OVERVIEW.md §7 updated | 2026-05-07 v0.3 addendum — Védis Eikleið: §4.7 (listening flow, inbound) added; §12 (L2 Rödd Hlust component diagram) added; §4.6.4 config table expanded to full 17-field schema matching RoddTtsConfig; §4.6.1 voice_id annotation corrected to WAV-path semantics; v0.2.x backlog items closed
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
