# HERETIC — Layer Interfaces

**Last updated:** 2026-05-08 (v0.5 scaffold — Rúnhild Svartdóttir: resolved naming gap in §L3 Sjón — `?vision_screen` (internal-bus) vs `?vision_in` (agent-protocol probe). Both flags now documented with authoritative cross-references. §L3 config block updated to match SjonScreenConfig canonical fields: `width`/`height` renamed to `max_width`/`max_height`; added `monitor_index`, `min_interval_ms`.) | 2026-05-07 (corrective pass — Rúnhild Svartdóttir, resolving audit blockers A-1, A-3, A-4, C-Q-C1; X-3 corrective pass: capability probe conservatism for `?streaming` and `?vision_in` documented in §L1 Bifröst) | 2026-05-07 drift corrective pass — Rúnhild Svartdóttir, resolving G-1 (LAYER_INTERFACES.md §L2 tts block stale), N-2 (language_id semantics), N-3 (voice WAV path semantics). §L2 Rödd config block expanded from 6-field pre-probe stub to full 17-field schema matching `src/heretic/rodd/config_model.py RoddTtsConfig`; `speed` annotated removed; `voice_id` WAV-path semantics documented; `language_id` multilingual scope documented. See also `src/heretic/rodd/INTERFACE.md` (same corrective pass).
**Scope:** Per-layer and per-sense contracts: inputs, outputs, owns, never-controls, error model, config keys, event types, capability flags, and SLO tier.
**Authority:** Derives from `ARCHITECTURE.md` and `DOMAIN_MAP.md`.
**Owner:** Architect (Rúnhild Svartdóttir)
**Legend:**
- `→` event emitted by this layer
- `←` event consumed by this layer
- `⚙` config key in `heretic.yaml`
- `?` capability flag (reported in capability handshake; see `AGENT_AGNOSTIC_PROTOCOL.md`)
- True Names from `docs/NAMING.md` appear in section headers; code-facing identifiers in parentheses.
- SLO tiers: **Hot** (< 60 ms p95) | **Warm** (< 1200 ms p95) | **Cold** (< 30 s p95). Source: carried-forward SLO tier pattern from `docs/PRIOR_PLANNING_TRIAGE.md` § v2 impl pack, adapted for HERETIC body framing.

---

## L0 — Grunnr (Foundation)

### Role
Tauri process bootstrap, config parsing, structured logging, subprocess supervisor. The silent ground.

### Inputs
- `heretic.yaml` file (path resolved from `$HERETIC_CONFIG` → XDG config dir → home dir — in that priority order; never hardcoded)
- OS signals (SIGTERM, Ctrl+C on Windows)

### Outputs
- `Config` struct (typed, passed to all layers at startup via `foundation::config()` accessor)
- Subprocess handles (passed to layer owners to supervise their own subprocesses)
- → `heretic::lifecycle::starting`
- → `heretic::lifecycle::layer_ready(layer_id)`
- → `heretic::lifecycle::layer_error(layer_id, error)`
- → `heretic::lifecycle::shutdown`

### Owns
Config loading, logging initialization, subprocess supervision, crash guard, version introspection.

### Never controls
Agent conversation, sense data, audio, screen frames, network routing.

### Error model
- Config parse failure → emit `heretic::lifecycle::config_error(detail)`; abort startup with user-readable message; reach `CONFIG_ERROR` terminal state.
- Subprocess crash → emit `heretic::lifecycle::layer_error`; restart per `restart_policy`; log each attempt.
- Unrecoverable panic → clean subprocess teardown before exit; write final log entry.

### Config keys
```yaml
grunnr:
  log_level: info           # trace | debug | info | warn | error
  log_file: null            # path or null (stdout only)
  config_version: "1"       # schema version; Grunnr refuses to start if mismatch
  startup_timeout_seconds: 30

# Per-sense process supervision is declared under skilningr: (the sense hub layer owns
# the subprocess registry). The keys below are nested inside skilningr.<sense_id>.
# See L5 Skilningr config block for the full example.
skilningr:
  <sense_id>:
    restart_policy:
      max_retries: 3
      backoff_seconds: [2, 5, 15]   # wait before retry 1, 2, 3
    shutdown_grace_seconds: 5
    health_interval_seconds: 15
```

### Capability flags
None — Grunnr is infrastructure, not a capability surface.

### SLO tier
Infrastructure — not latency-sensitive. Must complete startup before `startup_timeout_seconds` (default 30 s).

---

## L1 — Bifröst (Agent Connection)

### Role
Ceremonial connection to the inhabiting spirit — the one and only seam between body and agent.

### Inputs
- ← `L0 Grunnr Config` (agent endpoint, auth token, Tailscale options, timeout values)
- ← `L2 Rödd voice::transcript(text, timestamp, confidence)` (injected as user-role messages)
- ← `L3 Sjón vision::frame(base64_png, timestamp, source)` (injected as image content when vision enabled)
- ← `L5 Skilningr sense_hub::tool_result(call_id, result)` responses
- ← `L4 Vébond heretic::ui::command::open_bifrost` / `command::close_bifrost` triggers
- ← `heretic::lifecycle::shutdown`

### Outputs
- → `bifrost::state(DISCONNECTED | CONNECTING | CONNECTED | RECOVERING | ERROR)` (consumed by L4)
- → `bifrost::agent_turn_start` / `bifrost::agent_turn_end`
- → `bifrost::tool_call(call_id, tool_name, args)` (routed to L5)
- → `bifrost::agent_text_delta(text)` streaming chunk (consumed by L4 for status display)
- → `bifrost::error(code, message)` events

### Owns
Agent endpoint, Bearer token, connection state machine, message queue, heartbeat, retry logic, tool call dispatch, capability flag registry for current ceremony.

### Never controls
Agent memory, persona, system prompt contents, sense implementations, what tools actually do.

### Error model
- `BIFROST_AUTH_FAILED` — token rejected (HTTP 401/403); surface in UI; do not retry automatically.
- `BIFROST_TIMEOUT` — no response within `timeout_seconds`; emit `bifrost::error`; retry per policy.
- `BIFROST_UNREACHABLE` — Tailscale or endpoint not responding; offer UI retry button.
- `BIFROST_PROBE_FAILED` — capability probe timed out; continue with conservative capability defaults (`?tool_use = false`, `?vision_in = false`, `?streaming = false`).
- `BIFROST_TOOL_CALL_UNKNOWN` — agent called a tool not in the registry; return `tool_error` with `tool_not_found`; do not crash.
- `BIFROST_PROTOCOL_ERROR` — malformed response from agent; log full response; emit error; abort turn.

### Config keys
```yaml
bifrost:
  endpoint: "http://100.101.39.30:8643/v1"   # agent base URL
  api_key: "${HERETIC_AGENT_KEY}"             # env var reference; never plaintext
  model: "coding"                             # model name passed in requests
  timeout_seconds: 30
  stream_timeout_seconds: 120
  connect_timeout_seconds: 15
  max_retries: 3
  backoff_seconds: [2, 5, 15]
  heartbeat_interval_seconds: 30
  heartbeat_miss_threshold: 3
  heartbeat_enabled: true                     # set false for cloud agents to avoid billing
  stream: true
  max_tokens: 127000                          # per RULES.AI.md — keep high
  max_parallel_tool_calls: 4
  max_tool_call_rounds: 20
  drain_timeout_seconds: 10
  input_queue_depth: 10
  inject_context_on_connect: false            # optional HERETIC context message at session start
  tailscale:
    prefer: true
    fallback_to_direct: true
  vision_in: true
```

### Capability flags (queried from agent on connect)
- `?vision_in` — agent can receive image content in messages
- `?tool_use` — agent can emit tool_call / tool_result format
- `?streaming` — agent supports SSE streaming responses

> **v0.1 probe conservatism (X-3, 2026-05-07):** In v0.1, these flags are not determined by a full round-trip capability exchange. `?streaming` is set optimistically to `True` after any successful `/models` reachability probe — the assumption is that a reachable OpenAI-compatible endpoint supports SSE streaming. No actual stream response is sent to verify. `?vision_in` is read directly from `bifrost.vision_in` in `heretic.yaml` — no image is transmitted and round-tripped to confirm the agent accepts multimodal content. Both flags are therefore declarations of intent, not verified proofs. This is sufficient for v0.1 where Sjón (L3, screen capture) is not yet active. When Sjón ships in v0.2, a genuine image round-trip probe will replace the config-read path for `?vision_in`, and the `?streaming` probe will be strengthened. Until then, operators must ensure their agent endpoint actually supports the capabilities they declare in config.

### SLO tier
**Warm** — response stream start < 1200 ms p95 under normal load. If breached, L4 Vébond can surface a latency warning without aborting the ceremony.

---

## L2 — Rödd (Voice)

### Role
Ears (Hlust — STT inbound) and mouth (Tunga — TTS outbound). Two independent halves of the voice faculty.

**Infrastructure vs agent surface:** L2 Rödd owns the physical capture and playback infrastructure — mic device, Whisper.cpp subprocess, ChatterBox client, speaker output. However, Hlust and Tunga are also exposed as **agent-callable L5 senses** (`hlust.*` and `tunga.*` tools in Skilningr). The L2 infrastructure is the substrate; the L5 sense is the tool surface the agent calls. L2 Rödd does not expose tools directly to the agent. All agent contact with voice capability flows through L5 Skilningr's Hlust and Tunga sense subprocesses, which call into L2's infrastructure. See `ARCHITECTURE.md` §"Sense layering" and `SENSE_CONTRACTS.md` §"Auga, Hlust, Tunga" for the full layering resolution.

### Inputs (Hlust / STT half)
- ← `L0 Grunnr Config` (mic device, Whisper model path, VAD config)
- OS audio stream from microphone

### Inputs (Tunga / TTS half)
- ← `L0 Grunnr Config` (speaker device, ChatterBox endpoint, voice ID)
- ← `L1 Bifröst bifrost::agent_text_delta` or `voice::speak(text)` command

### Outputs (Hlust / STT half)
- → `voice::transcript(text, timestamp, confidence)` — consumed by L1 Bifröst

### Outputs (Tunga / TTS half)
- → `voice::speaking_start` / `voice::speaking_end` — consumed by L4 Vébond (waveform display)
- → `voice::error(DEVICE_UNAVAILABLE | TTS_UNREACHABLE | STT_CRASH)` — consumed by L4

### Owns
Mic capture loop, VAD, Whisper.cpp subprocess (Hlust), ChatterBox HTTP client (Tunga), speaker output. Both halves independently operatable.

### Never controls
What the agent says, conversation routing, MCP tools, screen capture data.

### Error model
- `VOICE_DEVICE_UNAVAILABLE` — mic or speaker not found; disable affected half; allow other half to continue; notify L4.
- `VOICE_STT_CRASH` — Whisper subprocess died; restart per `restart_policy`; emit `voice::error` to L4; queue transcription requests until restored.
- `VOICE_TTS_UNREACHABLE` — ChatterBox endpoint not responding; emit `voice::error`; queue or discard pending speech per config.
- `VOICE_PERMISSION_DENIED` — OS denied mic access; emit error; do not retry until user grants permission.

### Config keys

> **Corrective note — 2026-05-07 (G-1, N-2, N-3 — Rúnhild Svartdóttir):**
> The `tts:` block below was expanded from a 6-field pre-probe stub to the full 17-field schema
> as implemented in `src/heretic/rodd/config_model.py`. The `speed: 1.0` field has been removed
> (see annotation below). The canonical 17-field type definitions live in `config_model.py`;
> this YAML block is the operator-facing reference. All defaults match `RoddTtsConfig` defaults.
> Cross-references: `DATA_FLOW.md §4.6.1` (drift annotation), `chatterbox.py _build_request_body`
> (implementation truth), `src/heretic/rodd/INTERFACE.md §Config Keys` (module-level contract).

```yaml
rodd:
  stt:
    enabled: true
    engine: whisper_cpp                    # whisper_cpp | (future: whisper_api)
    model_path: "models/ggml-base.en.bin"  # relative to heretic data dir — never absolute
    device: default                        # OS device name or "default"
    vad_threshold: 0.6
    language: en
    load_strategy: lazy                    # lazy | eager; default lazy — see C-Q-C1 resolution
  tts:
    enabled: true
    engine: chatterbox                     # chatterbox | openai_compat (future)
    endpoint: "http://100.66.178.105:7851" # ChatterBox base URL; never hardcode in logic

    # --- Voice prompt ---
    voice_id: "default"
    # SEMANTICS (N-3): This field is a WAV FILE PATH for voice cloning — not a symbolic
    # voice identifier. Two valid states:
    #   "default" (or empty / null) — field is OMITTED from the ChatterBox request body;
    #                                  ChatterBox uses its own built-in default voice.
    #   any other value            — treated as a WAV file path (relative to project root;
    #                                "~" is expanded). The file must exist at synthesis time
    #                                (not at config load). For the "turbo" model, the WAV
    #                                must be >= 5 seconds; shorter files are rejected by
    #                                ChatterBox. Path resolution: see chatterbox.py
    #                                _resolve_voice_path().
    # v0.2 ships with "default" — no voice prompt. User may configure later.

    voice_prompt_path: null
    # Alternative path field — accepted by RoddTtsConfig when voice_id field is not set.
    # Same WAV-path semantics as voice_id above. null = omit from request body.

    # --- Model selection ---
    model: turbo                           # turbo | tts | multilingual
    # "turbo"       — GPT2-medium + S3Gen; always warm, lowest latency. v0.2 default.
    # "tts"         — Full English dual-pass CFG; slower, higher quality. English only.
    # "multilingual" — 23-language model; requires language_id field (see below).

    # --- Language selection (N-2) ---
    language_id: en
    # SEMANTICS (N-2): This field is an ISO 639-1 language code. It is ONLY meaningful
    # when model is "multilingual". Behavior by model:
    #   model: turbo        — language_id is silently excluded from the request body
    #                         (turbo is English-only; sending language_id is a no-op).
    #   model: tts          — same: English-only; language_id excluded.
    #   model: multilingual — language_id IS included when it is non-empty and != "en".
    #                         "en" is excluded because ChatterBox's multilingual default
    #                         is English; sending it is redundant. If you explicitly need
    #                         the field in the body for debugging, set any other code.
    # Supported ISO codes (ChatterBox multilingual model, probed 2026-05-07):
    #   en, de, es, fr, it, pt, pl, nl, ru, ja, ko, zh, ar, tr, id, vi, th, cs, sv, da, fi, el, ro
    # Default "en" — correct for turbo/tts; operators using multilingual must override.
    # Implementation reference: chatterbox.py _build_request_body line ~255.

    # --- Synthesis parameters ---
    exaggeration: 0.5                      # float; range 0.0–2.0. Emotional exaggeration.
    cfg_weight: 1.0                        # float; range 0.0–2.0. CFG dual-pass weight.
                                           # Only used by "tts" model; ignored by turbo.
    temperature: 0.8                       # float; range 0.05–2.0. Sampling temperature.
                                           # Controls expressiveness; ChatterBox default 0.8.
    top_p: 0.95                            # float; range 0.0–1.0. Nucleus sampling cutoff.
    repetition_penalty: 1.2               # float; range 0.1–5.0. Repetition penalty.
                                           # ChatterBox default 1.2.

    # --- Audio output ---
    device: default                        # OS audio device name or "default" (OS default)

    # --- Chunking policy ---
    chunk_min_chars: 80                    # int; >= 1. Minimum accumulated characters before
                                           # flushing a sentence-boundary chunk to TTS.
                                           # Prevents single-word audio (jarring). See tunga.py.
    sentence_terminators: [". ", "! ", "? ", "\n\n"]
                                           # list[str]; substring patterns marking a sentence
                                           # boundary for streaming chunking.

    # --- HTTP ---
    request_timeout_seconds: 30            # int; HTTP timeout for /v1/audio/speech requests.

    # --- REMOVED FIELD (drift annotation) ---
    # speed: 1.0
    # Removed 2026-05-07 (G-1 corrective pass — Rúnhild Svartdóttir).
    # `speed` appeared in the pre-probe config stub but has NO counterpart in the live
    # ChatterBox API. The /v1/audio/speech endpoint does not expose a speed parameter.
    # The field is still present in RoddTtsConfig as a stored-but-ignored value for
    # backward compatibility with any existing heretic.yaml files that set it; a debug
    # log is emitted if speed != 1.0 (see chatterbox.py _build_request_body).
    # Speed is NOT sent to ChatterBox. Do not set this field; it has no effect.
    # Reference: DATA_FLOW.md §4.6.1, chatterbox.py _build_request_body.
```

### Capability flags
- `?voice_in` — STT enabled and mic available
- `?voice_out` — TTS enabled and speaker available

### SLO tier
**Warm** for STT round-trip (utterance end → transcript → L1 dispatch < 1200 ms p95). **Hot** for TTS first audio chunk playback start (< 60 ms after first audio chunk received from ChatterBox).

---

## L3 — Sjón (Vision)

### Role
The agent's sight — periodic screen capture, optional webcam.

### Inputs
- ← `L0 Grunnr Config` (capture interval, resolution, crop, webcam device, buffer depth)
- OS screen capture permission

### Outputs
- → `vision::frame(base64_png, timestamp, source)` — `source` is `"screen"` or `"webcam"`

### Owns
Capture schedule, platform capture backend selection, frame ring buffer.

### Never controls
Frame interpretation, what the agent does with images, audio, MCP tools.

### Error model
- `VISION_PERMISSION_DENIED` — OS denied screen capture; disable Sjón; continue ceremony without vision; capability flag `?vision_screen` becomes false.
- `VISION_DEVICE_LOST` — screen or webcam disconnected; retry device enumeration on next capture cycle; emit `vision::warn(DEVICE_LOST)`.
- `VISION_BUFFER_OVERFLOW` — frame buffer full; drop oldest frames; emit `vision::warn(BUFFER_OVERFLOW)`.

### Config keys

> **Corrective note — 2026-05-08 (v0.5 scaffold — Rúnhild Svartdóttir):**
> The config block below is updated to match `src/heretic/sjon/config_model.py SjonScreenConfig`
> (the canonical definition, moved from grunnr.config per Approach B).
> `width`/`height` are renamed `max_width`/`max_height` to clarify they are output
> size caps, not capture dimensions. `monitor_index` and `min_interval_ms` are added.
> `heretic.example.yaml` is updated accordingly.

```yaml
sjon:
  screen:
    enabled: true
    interval_ms: 5000         # ms between periodic captures (v0.5.x — not active in v0.5 on-demand mode)
    max_width: 1280           # max output width; frame scaled down proportionally if wider
    max_height: 720           # max output height; frame scaled down proportionally if taller
    crop: null                # null = full screen; or {x, y, w, h}
    buffer_depth: 5           # frames in ring buffer (v0.5.x — not active in v0.5 on-demand mode)
    save_frames: false        # opt-in only; NEVER auto-saves; warning logged when true
    monitor_index: 0          # 0 = primary monitor; increase for secondary monitors
    min_interval_ms: 1000     # minimum ms between any two captures (throttle guard)
  webcam:
    enabled: false            # declared; not implemented in v0.5 (implementation target: v1.x)
    device: default
    interval_ms: 10000
```

**Infrastructure vs agent surface:** L3 Sjón owns the physical capture schedule, backend, and frame buffer. Auga (`auga.*` tools) is the **agent-callable L5 sense** that surfaces snapshot capability. The capture infrastructure lives in L3; the agent tool surface lives in L5 Skilningr. L3 does not expose tools directly. See `ARCHITECTURE.md` §"Sense layering" for the full resolution.

### Capability flags

> **Naming gap resolution — 2026-05-08 (Rúnhild Svartdóttir):**
> Two distinct capability namespaces exist. This note resolves the v0.4.1-era gap
> between them. The cross-reference is now canonical.

**`?vision_screen` (internal-bus name)**
- Set by HERETIC from its own layer state (L3 Sjón) — `sjon.screen.enabled AND MssBackend.available()`.
- Used internally to decide whether to call `snapshot()` in the turn loop.
- Reported to the agent in the senses-manifest system message at Tengsl (same mechanism as `?voice_in`).
- Authoritative source: this file (`LAYER_INTERFACES.md §L3 Sjón`).
- Cross-reference: `IPC_PROTOCOL.md §8.2` (naming bridge).

**`?vision_in` (agent-protocol probe name)**
- Set by the agent-protocol capability probe (or read from `bifrost.vision_in` in v0.4.x).
- Determines whether L1 Bifröst injects Sjón frames as `image_url` content blocks into
  agent turns. When `?vision_in` is False, frames are captured (if `?vision_screen` is True)
  but not transmitted — they are held in the ring buffer only.
- Authoritative source: `AGENT_AGNOSTIC_PROTOCOL.md §5.1` and `§5.2`.
- Cross-reference: `IPC_PROTOCOL.md §8.2` (naming bridge).

**Relationship between the two flags:**
  - `?vision_screen` answers: "Can HERETIC's body see at all?"
  - `?vision_in` answers: "Does the spirit accept images in its messages?"
  - Frames are injected ONLY when BOTH flags are True.
  - Either flag can independently be False (body cannot see, or spirit cannot receive images).

**Additional flags:**
- `?vision_webcam` — webcam enabled and device available (declared; not active in v0.5)

### SLO tier
**Cold** — frames captured at user-configured interval (default 5 s). Frame injection into agent turns is not latency-critical; late frames are simply the next scheduled capture.

---

## L4 — Vébond / Eldahús (UI — Summoning Circle)

### Role
Human-facing ceremony interface. Purely presentational — receives state, emits commands. The fire-room where the ceremony is conducted.

### Inputs
- ← `heretic::lifecycle::*` events
- ← `bifrost::state` events
- ← `voice::speaking_start`, `voice::speaking_end`, `voice::error` events
- ← `vision::frame` events (optional: show latest frame as thumbnail if `show_frame_thumbnail: true`)
- ← `heretic::ui::state_update(full_state_snapshot)` (authoritative UI state — single source)
- ← `sense_hub::sense_healthy(sense_id)` / `sense_hub::sense_degraded(sense_id)`

### Outputs
- → `heretic::ui::command::open_bifrost`
- → `heretic::ui::command::close_bifrost`
- → `heretic::ui::command::toggle_sense(sense_id, enabled)`
- → `heretic::ui::command::toggle_voice_in(enabled)`
- → `heretic::ui::command::toggle_voice_out(enabled)`
- → `heretic::ui::command::update_config(key, value)` (surface-level config only — does not write heretic.yaml directly; deferred to L0)

### Owns
React component tree, Norse visual theme (Eldahús aesthetic), ceremony controls, status indicators, sense toggles, error toast notifications.

### Never controls
Agent conversation content, MCP tools, audio DSP, network routing.

### Error model
- UI WebView crash → Tauri auto-restarts the WebView; ceremony state lives in Rust backend, not in React — no state is lost.
- IPC message decode error → log warning; discard malformed message; do not crash.

### Config keys
```yaml
vebond:
  theme: dark_norse              # dark_norse | (future: custom)
  show_frame_thumbnail: false
  show_agent_text_stream: true   # show streaming text in status panel
  ceremony_button_confirm: true  # require confirmation before Extinguish
```

### Capability flags
None — Vébond/Eldahús is not a capability surface.

### SLO tier
**Hot** — UI must reflect state changes (connection status, sense health, voice activity) within 60 ms of event emission. Status animations (fire-language indicators) must not lag ceremony state.

---

## L5 — Skilningr (MCP Sense Hub)

### Role
Registry and router for all sense subprocesses. Single interface between L1 Bifröst and all senses.

### Inputs
- ← `L0 Grunnr Config` (which senses are enabled, per-sense config)
- ← `L1 Bifröst bifrost::tool_call(call_id, tool_name, args)`

### Outputs
- → `sense_hub::tool_result(call_id, result)` → to L1
- → `sense_hub::tool_schemas(Vec<ToolSchema>)` → to L1 on connect (capability injection)
- → `sense_hub::sense_error(sense_id, error)` → to L4 for display
- → `sense_hub::sense_healthy(sense_id)` / `sense_hub::sense_degraded(sense_id)` → to L4

### Owns
Sense subprocess registry, tool routing table, health monitoring loop, schema aggregation. Inter-sense isolation is enforced here: a crashed sense subprocess does not affect others.

### Never controls
Agent conversation context, voice/vision data, what tools actually do, UI rendering.

### Error model
- `SENSE_NOT_FOUND` — tool call targets unknown sense; return `tool_error` to agent immediately; no retry.
- `SENSE_SUBPROCESS_DEAD` — MCP subprocess exited; return `tool_error(SENSE_UNAVAILABLE)` for in-flight calls; restart per policy; remove sense from tool registry until restored.
- `SENSE_TIMEOUT` — sense took too long; return `tool_error(SENSE_TIMEOUT)` to agent; log; do not crash hub.

### Config keys

The `skilningr:` top-level key is the namespace for the entire sense hub and all its subprocesses. Each sense uses its code-facing identifier (not its True Name) as the sub-key — per NAMING.md line 81.

```yaml
skilningr:
  filesystem:
    enabled: true
    # (see L5.1 below for full keys)
  terminal:
    enabled: true
  browser:
    enabled: false
  photopea:
    enabled: false
  blender:
    enabled: false
  vrchat:
    enabled: false
  agentmail:
    enabled: false
  custom:
    enabled: false
  library:
    enabled: false
```

### Capability flags
Aggregate of all enabled senses' capability flags. Reported to agent as the merged tool schemas list on connection.

### SLO tier
**Warm** for interactive tool calls (tool call dispatch < 100 ms). **Cold** for library search and indexing. Skilningr itself adds negligible overhead — most time is in the sense subprocess.

---

## L5.1 — Minni (FileSystem Sense)

**True Name:** Minni (minni) — memory; the agent's external memory in Midgard.

### Tools exposed
- `filesystem.read_file(path) -> content`
- `filesystem.write_file(path, content) -> ok`
- `filesystem.append_file(path, content) -> ok`
- `filesystem.list_directory(path, recursive) -> entries`
- `filesystem.create_directory(path) -> ok`
- `filesystem.delete_file(path) -> ok` — requires `allow_delete: true`
- `filesystem.move_file(src, dst) -> ok`
- `filesystem.file_exists(path) -> bool`
- `filesystem.get_file_info(path) -> {name, size, modified, mime_type}`

### Config keys
```yaml
skilningr:
  filesystem:
    enabled: true
    allowed_roots:
      - "~/heretic_workspace"    # relative to home — never absolute
    allow_write: true
    allow_delete: false
    max_file_size_mb: 50
```

### Capability flags
- `?filesystem` — enabled and at least one allowed root is accessible

### Error model
- Path outside allowed roots → `PERMISSION_DENIED` immediately; do not attempt access.
- File too large → `FILE_TOO_LARGE(size, limit)`.
- OS error → `FILESYSTEM_ERROR(os_error_code, message)`.
- Non-UTF-8 file when binary mode not requested → `FILESYSTEM_ENCODING_ERROR`.

---

## L5.2 — Skepja (Terminal Sense)

**True Name:** Skepja (skepja) — to shape, create; action on the machine world.

### Tools exposed
- `terminal.run_command(command, cwd, timeout_seconds) -> {stdout, stderr, exit_code}`
- `terminal.list_processes() -> [{pid, name, cpu, mem}]`

### Config keys
```yaml
skilningr:
  terminal:
    enabled: true
    allowed_dirs:
      - "~/heretic_workspace"
    shell: "bash"                # bash | powershell | cmd | sh
    default_timeout_seconds: 30
    safe_mode: true              # Tier 0 default — see SENSE_CONTRACTS.md §L5.2 for tier model
    allow_unrestricted_dirs: false   # Tier 2 opt-in
    forbidden_patterns:          # regex list; commands matching any are blocked
      - "rm -rf /"
      - "format c:"
```

### Capability flags
- `?terminal` — enabled

### Error model
- Command matches forbidden pattern → `COMMAND_FORBIDDEN`; do not execute.
- Working dir outside allowed dirs → `PERMISSION_DENIED`.
- Timeout exceeded → terminate process; return `PARTIAL_SUCCESS` with partial stdout + `TERMINAL_TIMEOUT` code.
- Non-zero exit code → `TERMINAL_EXIT_ERROR` (informational — not a sense failure; agent decides).

---

## L5.3 — Leið (Browser Sense)

**True Name:** Leið (leid) — path, route; the navigator's way through the web.

### Tools exposed
- `browser.navigate(url) -> {url, title, status_code}`
- `browser.get_page_text() -> text`
- `browser.get_page_html() -> html`
- `browser.screenshot(full_page) -> base64_png`
- `browser.click(selector) -> ok`
- `browser.type_text(selector, text) -> ok`
- `browser.evaluate_js(script) -> result`
- `browser.get_current_url() -> url`
- `browser.wait_for_selector(selector, timeout_ms) -> ok`
- `browser.get_element_text(selector) -> text`

### Config keys
```yaml
skilningr:
  browser:
    enabled: false
    browser_binary: null         # null = auto-detect Chromium/Chrome/Firefox
    allowed_domains: []          # empty = all domains allowed; non-empty = allowlist
    headless: false
    screenshot_on_navigate: false
```

### Capability flags
- `?browser` — enabled and browser binary found

### Error model
- Domain not in allowlist → `DOMAIN_NOT_ALLOWED`.
- Navigation timeout → `BROWSER_TIMEOUT`.
- JS evaluation error → `JS_ERROR(message)`.

---

## L5.4 — Hönd (Photopea Sense)

**True Name:** Hönd (hond) — hand; the painter's touch on a surface.

### Tools exposed
- `photopea.new_document(width, height, name) -> ok`
- `photopea.open_file(path) -> ok`
- `photopea.save_as(path, format) -> ok`
- `photopea.run_action(action_name) -> ok`
- `photopea.evaluate_script(script) -> result`
- `photopea.screenshot() -> base64_png`
- `photopea.get_layer_list() -> [{id, name, type, visible}]`
- `photopea.set_layer_visibility(layer_id, visible) -> ok`

Hönd depends on Leið (L5.3 Browser) — Photopea runs as a web app. Leið must be enabled for Hönd to function.

### Config keys
```yaml
skilningr:
  photopea:
    enabled: false
    photopea_url: "https://www.photopea.com"
```

### Capability flags
- `?photopea` — enabled and Leið (L5.3 Browser) is available

**API verified 2026-05-07:** `app.echoToOE()` and `app.activeDocument.saveToOE()` confirmed documented at https://www.photopea.com/api/live. The integration is viable via postMessage-based iframe messaging within a Tauri WebView. Hönd requires its own WebView panel — it cannot route through Leið's headless Playwright instance, as Photopea requires direct iframe postMessage communication. Implementation target: v0.9 scope.

---

## L5.5 — Smiðja (Blender Sense)

**True Name:** Smiðja (smidja) — forge, smithy; the place of making three-dimensional form.

### Tools exposed (current Seidr-Smidja Brúarhönd v0.1 surface)
- `blender.health() -> {status, version}`
- `blender.capabilities() -> capability_list`
- `blender.screenshot() -> base64_png`
- `blender.click(x, y) -> ok`
- `blender.type_text(text) -> ok`
- `blender.hotkey(key_combo) -> ok`
- `blender.vroid_open(path) -> ok`
- `blender.vroid_export(path, format) -> ok`

Depends on Seidr-Smidja Brúarhönd daemon running at configured endpoint (separate process; not managed by HERETIC).

### Config keys
```yaml
skilningr:
  blender:
    enabled: false
    brunhand_endpoint: "http://localhost:8765"
    auth_token: "${SEIDR_BRUNHAND_TOKEN}"
    timeout_seconds: 60
```

### Capability flags
- `?blender` — enabled and Brúarhönd daemon reachable

---

## L5.6 — Líkami (VRChat Sense)

**True Name:** Líkami (likami) — body, physical form; social embodiment.

### Tools exposed (design — subject to VRChat API verification at v0.10)
- `vrchat.send_osc(address, args) -> ok`
- `vrchat.get_avatar_parameters() -> {params: {name: value}}`
- `vrchat.set_avatar_parameter(name, value) -> ok`
- `vrchat.get_player_position() -> {x, y, z, rotation}`

### Config keys
```yaml
skilningr:
  vrchat:
    enabled: false
    osc_host: "127.0.0.1"
    osc_port: 9000
```

### Capability flags
- `?vrchat` — enabled

**OSC protocol verified 2026-05-07:** Standard UDP 9000 (send) / 9001 (receive), VRChat OSC format confirmed at docs.vrchat.com/docs/osc-overview. Address format: `/avatar/parameters/<parameterName>`. `get_avatar_parameters()` returns whatever parameters VRChat broadcasts — a static list cannot be defined (avatar-specific). Implementation target: v0.10 scope.

---

## L5.7 — Boð (AgentMail Sense)

**True Name:** Boð (bod) — message; formal correspondence between parties.

### Tools exposed
- `agentmail.send(to, subject, body, cc) -> ok`
- `agentmail.list_inbox(limit, unread_only) -> messages`
- `agentmail.read_message(message_id) -> {from, to, subject, date, body, attachments}`
- `agentmail.reply(message_id, body) -> ok`
- `agentmail.delete_message(message_id) -> ok`
- `agentmail.search(query, limit) -> messages`

### Config keys
```yaml
skilningr:
  agentmail:
    enabled: false
    smtp_host: "smtp.example.com"
    smtp_port: 587
    smtp_user: "${HERETIC_MAIL_USER}"
    smtp_password: "${HERETIC_MAIL_PASSWORD}"
    imap_host: "imap.example.com"
    imap_port: 993
    from_address: "agent@example.com"
```

### Capability flags
- `?agentmail` — enabled and credentials configured

---

## L5.8 — Nýr Limr (Custom Sense / Plugin Slot)

**True Name:** Nýr Limr (nyr_limr) — new limb; the capacity to grow.

### Tools exposed
Defined entirely by the user-provided MCP server. Loaded from tool schemas at sense startup. Tool names must start with the declared `prefix`.

### Config keys
```yaml
skilningr:
  custom:
    enabled: false
    plugins:
      - id: "home_assistant"
        command: "python"
        args: ["-m", "heretic_sense_homeassistant"]
        env:
          HA_TOKEN: "${HA_TOKEN}"
          HA_URL: "http://homeassistant.local:8123"
        prefix: "home."
```

### Capability flags
- `?custom_<id>` per enabled plugin

---

## L5.9 — Mímisbrunnr (Library Sense)

**True Name:** Mímisbrunnr (mimisbrunnr) — Mímir's Well; the well of wisdom.

### Tools exposed
- `library.search(query, limit, sources) -> {results: [{source, title, snippet, score, id}]}`
- `library.get_article(source, article_id) -> {title, content, source, attribution}`
- `library.list_sources() -> {sources: [{id, name, type, status, entry_count}]}`
- `library.source_status(source_id) -> {status, index_type, last_indexed, disk_mb}`

CLI well-tending commands (user-facing, not agent-facing):
```
heretic library list | inspect | download | status | index | remove | reindex | serve
```

### Config keys
```yaml
skilningr:
  library:
    enabled: false
    backends:
      - type: file_index
        path: "~/heretic_workspace/library/curated"
      - type: mimisbrunnr
        data_dir: "~/.heretic/library/mimisbrunnr"    # configurable; never hardcoded
        sources: []
        retrieval: keyword                            # keyword | vector | hybrid
      - type: mindspark
        endpoint: "http://localhost:7777"
        enabled: false
```

### Capability flags
- `?library` — enabled and at least one backend available
- `?library_vector` — vector retrieval available (requires indexed source + sufficient compute)

### SLO tier
**Cold** — library search is background knowledge retrieval; < 30 s p95 for keyword; vector search timing depends on indexed corpus size.

---

*All sense error codes follow the taxonomy defined in `SENSE_CONTRACTS.md`.*
