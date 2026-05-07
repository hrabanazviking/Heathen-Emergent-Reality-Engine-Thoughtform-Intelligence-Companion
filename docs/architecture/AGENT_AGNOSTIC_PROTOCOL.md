# HERETIC — Agent-Agnostic Protocol (Bifröst Contract)

**Last updated:** 2026-05-07
**Scope:** The exact protocol any inhabiting agent must speak; what HERETIC promises; what HERETIC requires; authentication; routing; capability negotiation; tool call format; lifecycle messages mapped to True Names.
**Authority:** Derives from `ARCHITECTURE.md` (L1 Bifröst domain).
**Owner:** Architect (Rúnhild Svartdóttir)
**Legend:** True Names from `docs/NAMING.md` are used for lifecycle states throughout.

---

## 1. The Fundamental Principle

HERETIC is body-agnostic toward the spirit and spirit-agnostic toward the body.

From the manifesto: "Any AI system that can speak OpenAI-compatible API can inhabit the body."

The Bifröst contract defines the minimum surface any spirit must present, and the maximum surface HERETIC will assume. Nothing outside this contract is required of the spirit. Nothing outside this contract will be assumed of it.

Bifröst (L1) is the one and only point of contact between HERETIC's body and the inhabiting spirit. No other layer speaks to the agent endpoint.

---

## 2. Required OpenAI API Subset

HERETIC targets the stable `/v1/chat/completions` endpoint. The agent must implement the following fields exactly.

### 2.1 Request format (HERETIC → agent)

```json
POST /v1/chat/completions
Authorization: Bearer <token>
Content-Type: application/json

{
  "model": "<configured model name>",
  "messages": [
    {
      "role": "system",
      "content": "<system prompt if configured>"
    },
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "<transcript or user text>"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/png;base64,<base64_frame>"
          }
        }
      ]
    },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "<call_id>",
          "type": "function",
          "function": {
            "name": "<tool_name>",
            "arguments": "<json_string>"
          }
        }
      ]
    },
    {
      "role": "tool",
      "tool_call_id": "<call_id>",
      "content": "<tool_result_json_string>"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "<tool_name>",
        "description": "<tool_description>",
        "parameters": { "<json_schema>" }
      }
    }
  ],
  "tool_choice": "auto",
  "stream": true,
  "max_tokens": 127000
}
```

**Required fields the agent must accept:**
- `model` (string)
- `messages` array with roles: `system`, `user`, `assistant`, `tool`
- `tools` array in the `function` format above (not the deprecated `functions` format)
- `tool_choice: "auto"`
- `stream: true` (HERETIC defaults to streaming; non-streaming is a fallback)
- `max_tokens` (agent must honor or soft-cap with a warning; HERETIC sets 127000 per RULES.AI.md)

**Image content in messages** is included only when `vision_in: true` is in HERETIC config AND the agent reports `?vision_in` capability during the capability probe. If the agent does not support image content, HERETIC omits the `image_url` content blocks silently.

**Optional fields HERETIC may send** (agent must not crash if it receives them):
- `temperature`
- `top_p`
- `stop`
- `user` (for audit logging on the agent side)

### 2.2 Response format (agent → HERETIC)

**Streaming (SSE — preferred):**

```
data: {"id":"...","object":"chat.completion.chunk","model":"...","choices":[{"delta":{"role":"assistant","content":"<text>"},"finish_reason":null}]}
data: {"id":"...","choices":[{"delta":{"tool_calls":[{"index":0,"id":"<call_id>","type":"function","function":{"name":"<tool>","arguments":"<partial_json>"}}]},"finish_reason":null}]}
data: {"id":"...","choices":[{"delta":{},"finish_reason":"tool_calls"}]}
data: [DONE]
```

**Non-streaming (fallback):**

```json
{
  "id": "...",
  "object": "chat.completion",
  "model": "...",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "<text or null>",
        "tool_calls": [
          {
            "id": "<call_id>",
            "type": "function",
            "function": {
              "name": "<tool_name>",
              "arguments": "<json_string>"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

**Finish reasons HERETIC handles:**
- `stop` — natural end of response; turn complete
- `tool_calls` — agent wants to call tools; HERETIC dispatches and continues turn
- `length` — max_tokens reached; HERETIC logs a warning; presents partial response
- `content_filter` — agent filtered content; HERETIC treats as soft error; logs; does not crash

**Finish reasons HERETIC does NOT handle** (treated as `stop`):
- Any proprietary extension values — logged and ignored

### 2.3 What HERETIC does NOT require

- Streaming (configurable fallback to non-streaming via `bifrost.stream: false`)
- Vision support (probed; gracefully omitted if absent)
- Function calling (probed; if absent, HERETIC operates without MCP tools for that agent)
- Any specific model name — `model` is passed through from config

---

## 3. Authentication Contract

### 3.1 Bearer token

HERETIC passes the agent's API key as a standard HTTP Bearer token:

```
Authorization: Bearer <api_key>
```

The token is read from `heretic.yaml` via an environment variable reference — never stored as plaintext in the YAML file:

```yaml
bifrost:
  api_key: "${HERETIC_AGENT_KEY}"
```

At runtime, L0 Grunnr resolves `${HERETIC_AGENT_KEY}` from the process environment. If the variable is unset, L0 emits `heretic::lifecycle::config_error(MISSING_ENV_VAR)` and aborts startup with a clear user-readable message.

### 3.2 Token rotation

HERETIC does not implement automatic token rotation in v1. Token changes require a ceremony restart (Slokna → re-Kynding). This is a deliberate simplicity tradeoff appropriate to ceremonial activation.

**Open question:** If demand emerges in v1.x for live token rotation (hot-swap without ceremony restart), a `bifrost::rotate_token(new_token)` command can be added to the L4 Vébond command surface. Deferred until required.

### 3.3 Token storage

Token lives only in the environment at process startup. HERETIC does not write tokens to disk, cache them in session state, or log them. Log scrubbing: L1 Bifröst redacts `Authorization` headers from all log output at info level and below; full headers appear only at `trace` level with a prominent warning that secrets are exposed.

### 3.4 Agent-side authentication of HERETIC

Currently out of scope — HERETIC authenticates to the agent; the agent does not authenticate to HERETIC. The Tailscale mesh provides network-level identity for the Hermes-on-Pi case. If the agent needs to authenticate inbound callers, it does so via its own mechanism; HERETIC passes whatever token is configured.

---

## 4. Tailscale-Aware Routing

### 4.1 Endpoint resolution algorithm

```
1. Read bifrost.endpoint from config (a full URL, e.g., "http://100.101.39.30:8643/v1")
2. If bifrost.tailscale.prefer: true:
   a. Attempt to resolve the hostname via Tailscale DNS
   b. If Tailscale IP resolves and ping succeeds → use Tailscale path
   c. If Tailscale unavailable AND tailscale.fallback_to_direct: true → use URL as-is
   d. If Tailscale unavailable AND fallback_to_direct: false → emit BIFROST_UNREACHABLE; abort
3. If bifrost.tailscale.prefer: false → use URL directly
```

### 4.2 What the user configures for a Tailscale agent (Hermes-on-Pi)

```yaml
bifrost:
  endpoint: "http://100.101.39.30:8643/v1"   # Tailscale IP + agent port
  tailscale:
    prefer: true
    fallback_to_direct: true
```

### 4.3 Non-Tailscale agents

For cloud agents (Claude, GPT-4, Ollama on localhost):

```yaml
bifrost:
  endpoint: "https://api.anthropic.com/v1"    # or openai, ollama, etc.
  api_key: "${ANTHROPIC_API_KEY}"
  tailscale:
    prefer: false
```

HERETIC does not require Tailscale. It is the default routing strategy for the Hermes-on-Pi case, not a hard dependency.

---

## 5. Capability Negotiation

HERETIC uses a minimal probe turn rather than a dedicated capabilities endpoint.

### 5.1 Probe sequence on connection (Tengsl entry)

Immediately after establishing the HTTP connection — at entry to Tengsl (STATE_TENGSL) — L1 Bifröst sends:

```json
{
  "model": "<configured>",
  "messages": [
    {"role": "user", "content": [{"type": "text", "text": "HERETIC_CAPABILITY_PROBE"}]}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "heretic_probe",
        "description": "Capability probe — respond with tool call to confirm tool support",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": false}
      }
    }
  ],
  "tool_choice": "auto",
  "stream": false,
  "max_tokens": 50
}
```

**Interpreting the probe response:**
- If agent calls `heretic_probe` → `?tool_use = true`
- If agent returns text without tool call → `?tool_use = false` (ceremony proceeds text-only; no MCP tools)
- If `stream: false` yields SSE events → agent ignores `stream`; L1 sets `stream: true` always for this agent
- If the probe itself fails (timeout, HTTP error) → `BIFROST_PROBE_FAILED`; use conservative defaults

A separate short image probe is sent only if `vision_in: true` in config:
- If no `invalid_request_error` → `?vision_in = true`
- If error received → `?vision_in = false`

**Capability flags set from probe:**

| Flag | How detected |
|---|---|
| `?tool_use` | Agent returned `finish_reason: tool_calls` or called `heretic_probe` |
| `?vision_in` | Short image probe did not return `invalid_request_error` |
| `?streaming` | Agent sent SSE events when `stream: true` in probe |

If probe fails entirely: `?tool_use = false`, `?vision_in = false`, `?streaming = false` as conservative defaults. Ceremony proceeds without those capabilities.

### 5.2 Capability flag effects

| Flag | If true | If false |
|---|---|---|
| `?tool_use` | Tool schemas injected into all turns; tool_call dispatch active | No tools sent; agent operates text-only |
| `?vision_in` | Sjón frames injected as image_url content blocks | Frames buffered in Sjón but not sent |
| `?streaming` | SSE streaming used for all turns | Non-streaming POST used; L4 shows response when complete |

---

## 6. Tool Call Protocol

### 6.1 How HERETIC presents senses as tools

On connection, L1 Bifröst calls `sense_hub::get_tools()` and receives a flat list of `ToolSchema` objects. These are injected into every `/v1/chat/completions` request in the `tools` array. The agent sees one unified tool surface — it has no knowledge of which sense owns which tool.

Tool naming convention: `<sense_id>.<action>` — e.g., `filesystem.read_file`, `blender.screenshot`, `library.search`. Full tool naming spec in `SENSE_CONTRACTS.md`.

The sense True Names correspond to their `sense_id` code-facing identifiers as follows:
- Minni (minni) → `filesystem.*`
- Skepja (skepja) → `terminal.*`
- Leið (leid) → `browser.*`
- Hönd (hond) → `photopea.*`
- Smiðja (smidja) → `blender.*`
- Líkami (likami) → `vrchat.*`
- Boð (bod) → `agentmail.*`
- Nýr Limr (nyr_limr) → `<custom_prefix>.*`
- Mímisbrunnr (mimisbrunnr) → `library.*`

### 6.2 Tool call routing

```
Agent emits tool_call with name "filesystem.read_file"
    ↓
L1 Bifröst receives tool_call; extracts name prefix "filesystem"
    ↓
L5 Skilningr router looks up "filesystem" in sense registry
    ↓
Routes to heretic-sense-minni subprocess via MCP stdio protocol
    ↓
Subprocess executes; returns result
    ↓
L5 Skilningr returns tool_result to L1 Bifröst
    ↓
L1 appends {"role": "tool", "tool_call_id": id, "content": result} to message array
    ↓
L1 continues turn (sends updated messages back to agent for next completion)
```

### 6.3 Multiple tool calls in one turn

The agent may return multiple `tool_calls` in a single response. Bifröst dispatches them concurrently (within configurable parallelism limits) and waits for all results before continuing the turn. Result order in the message array matches the order of calls as emitted by the agent.

```yaml
bifrost:
  max_parallel_tool_calls: 4   # default 4; set to 1 for serial execution
```

### 6.4 Tool errors returned to agent

When a tool fails, Bifröst does not hide the error. The tool_result content is a structured error object:

```json
{
  "error": true,
  "code": "SENSE_UNAVAILABLE",
  "message": "The filesystem sense is currently unavailable. Retry in a moment or proceed without filesystem access.",
  "sense": "filesystem",
  "tool": "filesystem.read_file"
}
```

The agent receives this and decides how to proceed (retry, inform user, change plan). Bifröst does not retry tool calls automatically — that is the agent's decision.

### 6.5 Tool call loop termination

Bifröst continues the tool call loop (call → result → next completion) until:
- Agent returns `finish_reason: stop` (turn complete)
- Maximum loop depth reached (configurable; default 20 tool call rounds)
- Ceremony extinguish is triggered (Slokna)

```yaml
bifrost:
  max_tool_call_rounds: 20
```

If max rounds is hit, L1 injects a system message: `"Maximum tool call depth reached. Please complete your response."` and sends one final completion request with `tool_choice: none`.

---

## 7. Lifecycle Messages (mapped to True Names)

### 7.1 Connection open sequence (Kynding → Tengsl → Samræður)

```
1. User triggers "Light the Candle" in Vébond (L4 UI) → ceremony enters opening state
2. L1 Bifröst resolves agent endpoint (Tailscale or direct)
3. L1 sends capability probe (§5.1) — this is the Tengsl binding moment
4. L1 records capability flags
5. L1 emits bifrost::state(CONNECTED) → STATE_TENGSL achieved
6. L4 Vébond transitions to INHABITED ceremony appearance (Eldahús: fire burning)
7. L2 Rödd STT (Hlust) activates — listening begins
8. L3 Sjón capture schedule starts — first frame captured
9. L5 Skilningr sense health check loop starts
10. Ceremony enters Samræður — active Communion
```

### 7.2 Heartbeat (during Samræður)

Every `bifrost.heartbeat_interval_seconds` (default 30 s), Bifröst sends a minimal keepalive:

```json
POST /v1/chat/completions
{
  "model": "<configured>",
  "messages": [{"role": "user", "content": [{"type": "text", "text": "HERETIC_HEARTBEAT"}]}],
  "max_tokens": 1,
  "stream": false
}
```

If the agent does not respond within `timeout_seconds`, Bifröst increments a miss counter. After `heartbeat_miss_threshold` consecutive misses (default 3), Bifröst transitions to RECOVERING state and attempts reconnect. If reconnect fails within the retry window, ceremony transitions to Tengsl-broken (READY). User is notified via L4 Vébond.

Note: Cloud API endpoints may charge per heartbeat. Users may disable heartbeat:
```yaml
bifrost:
  heartbeat_enabled: false
```

### 7.3 Graceful close (Slokna — Extinguish)

When the user triggers Extinguish from Vébond:

```
1. L1 Bifröst stops accepting new turns from L2 Rödd (STT transcripts queued, not dispatched)
2. L1 waits for in-flight tool calls to complete (drain window: bifrost.drain_timeout_seconds)
3. L1 sends optional final close notification to agent:
   {"role": "system", "content": "HERETIC_CEREMONY_END"}
4. L1 closes HTTP connection
5. L1 emits bifrost::state(DISCONNECTED)
6. L5 Skilningr emits shutdown to all sense subprocesses
7. L2 Rödd (Rödd) stops capture loop; TTS queue flushed (plays queued speech before stopping)
8. L3 Sjón stops capture schedule; frame buffer cleared
9. Session state zeroed in memory (message array, frame buffer, tool routing table)
10. L4 Vébond returns to READY appearance (Eldahús: fire banked — Hvíld achieved)
```

### 7.4 Ungraceful disconnect recovery (Tengsl broken → recovery → Tengsl restored)

If the connection drops unexpectedly during Samræður:

```
1. L1 Bifröst detects dropped connection (HTTP error, timeout, or missed heartbeats)
2. L1 transitions to ERROR state → enters recovery
3. L1 emits bifrost::state(ERROR) → L4 Vébond shows "Connection lost" indicator
4. L1 begins reconnect attempt sequence (exponential backoff per config)
   During recovery: L2 Rödd continues capturing voice (queued, not dispatched)
                    L3 Sjón continues capturing (buffered)
5. If reconnect succeeds:
   a. L1 repeats capability probe
   b. L1 injects recovery message:
      {"role": "system", "content": "Connection was interrupted and restored. Continue from where you left off."}
   c. L1 transitions to CONNECTED → Tengsl re-established; Samræður resumes
   d. L4 Vébond updates indicator (fire restored)
6. If reconnect exhausted (max_retries hit):
   a. L1 transitions to DISCONNECTED
   b. Ceremony transitions to READY (senses still alive, Bifröst closed — partial Hvíld)
   c. User may re-open Bifröst manually from L4 Vébond
```

---

## 8. What HERETIC Promises the Agent (Bifröst Covenant)

These are binding commitments. Violating them constitutes a Bifröst breach.

1. **Clean tool surface.** Every tool in the `tools` array at turn time is callable and will return a `tool_result` within the configured timeout. If a sense dies mid-ceremony, its tools are removed from the next turn's tool list and a system message is injected to inform the agent.

2. **Consistent capability flags.** Capabilities reported at connection time (Tengsl) remain stable for the duration of that ceremony. HERETIC does not add or remove tool capabilities mid-ceremony without a system message notification.

3. **No surprise reconnects mid-turn.** HERETIC will not initiate a reconnect while a turn is in progress. If a connection drop is detected mid-turn, HERETIC waits for the turn to complete (or timeout) before attempting reconnect.

4. **Honest tool errors.** Tool failures return structured `tool_error` objects, never silently empty results. The agent always knows when a tool failed and why.

5. **Respect for agent rate limits.** If the agent returns HTTP 429, L1 backs off per the `Retry-After` header or exponential backoff; it does not hammer the endpoint.

6. **Voice transcripts as clean user messages.** STT (Hlust) transcripts are injected as `{"role": "user", "content": [{"type": "text", "text": transcript}]}` — standard user-role messages; no custom wrapper, no proprietary fields.

7. **Vision frames as standard image_url.** Sjón captures are injected as `{"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}` within user content — standard OpenAI vision format.

---

## 9. What HERETIC Requires from the Agent

These are the minimum obligations any inhabiting spirit must meet.

1. **Responds within timeout.** Default 30 s for a streaming response start. If no SSE event arrives within timeout, Bifröst treats it as a failure and retries per policy.

2. **Emits valid tool calls.** When `finish_reason: tool_calls`, the `tool_calls` array must contain valid JSON in the `function.arguments` field. Malformed JSON → `BIFROST_PROTOCOL_ERROR`; the turn is abandoned with a user notification.

3. **Respects `tool_choice: auto`.** Bifröst always sends `tool_choice: auto`. The agent may choose not to call tools. It must not return an error for this field.

4. **Handles `role: tool` messages.** After a tool call, Bifröst appends a `{"role": "tool", ...}` message. The agent must accept this role in the messages array.

5. **Accepts `max_tokens: 127000`.** Per RULES.AI.md, token limits are kept high. The agent may soft-cap lower if its context window is smaller, but must not return an error for receiving this value.

6. **Does not require HERETIC-specific headers.** Bifröst sends only `Authorization: Bearer` and `Content-Type: application/json`. No proprietary headers.

7. **Signals end of response.** The agent must terminate streaming with `data: [DONE]` and set `finish_reason` in the final chunk. Streams that do not terminate are killed after `bifrost.stream_timeout_seconds` (default 120 s).

---

*"The spirit doesn't need to know what kind of body it wears. It speaks its tongue and the body listens."*
