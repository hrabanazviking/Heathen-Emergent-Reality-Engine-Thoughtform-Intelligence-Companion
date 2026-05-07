# Rödd Module Interface

**Last updated:** 2026-05-07
**Scope:** L2 Rödd — the voice layer Python module (`src/heretic/rodd/`)
**Owner:** Architect (Rúnhild Svartdóttir)
**Derives from:** `docs/architecture/LAYER_INTERFACES.md §L2 Rödd`
**Legend:** Owns = authoritative data owner; Never-controls = hard boundary.

---

## What Rödd Owns

- ChatterBox HTTP client lifecycle (open, synthesize, close)
- Audio playback backend selection and playback lifecycle
- Tunga orchestrator: text-stream buffering, sentence-boundary chunking, synthesis dispatch
- RoddConfig, RoddTtsConfig, RoddSttConfig — the typed config structs for both voice halves
- The Rödd error hierarchy (RoddError and all subclasses)
- Degraded-mode state tracking: if ChatterBox is unreachable or playback is unavailable,
  Tunga enters text-only mode without crashing the ceremony

Hlust (STT / Whisper.cpp) is declared in config structs but not yet implemented.
Implementation target: v0.3.

---

## What Rödd Exposes (Public API)

| Export | Module | Purpose |
|---|---|---|
| `RoddConfig` | `rodd.config_model` | Root config struct for both TTS and STT halves. |
| `RoddTtsConfig` | `rodd.config_model` | Tunga (mouth) config: endpoint, model, chunking, timeouts. |
| `RoddSttConfig` | `rodd.config_model` | Hlust (ear) config: engine, model path, VAD, language. |
| `Tunga` | `rodd.tunga` | Orchestrator: receives text deltas, chunks, synthesises, plays. |
| `ChatterboxClient` | `rodd.chatterbox` | ABC for all ChatterBox-compatible TTS service clients. |
| `ChatterboxHttpClient` | `rodd.chatterbox` | httpx-based production ChatterBox client. |
| `AudioPlayback` | `rodd.playback` | ABC for all audio output backends. |
| `SoundDeviceBackend` | `rodd.playback` | Primary backend: sounddevice library (optional dep). |
| `PlatformFallbackBackend` | `rodd.playback` | Fallback backend: OS-native (winsound / afplay / aplay). |
| `RoddError` | `rodd.errors` | Root error; all Rödd errors are subclasses. |
| `ChatterboxError` | `rodd.errors` | Root error for all ChatterBox service failures. |
| `ChatterboxConnectionError` | `rodd.errors` | Endpoint unreachable (VOICE_TTS_UNREACHABLE). |
| `ChatterboxAuthError` | `rodd.errors` | HTTP 401/403 from ChatterBox. |
| `ChatterboxTimeoutError` | `rodd.errors` | HTTP request timeout. |
| `ChatterboxApiError` | `rodd.errors` | Non-200 status or non-WAV response. Carries `status_code`, `detail`. |
| `PlaybackError` | `rodd.errors` | Any audio playback failure. |
| `PlaybackBackendUnavailableError` | `rodd.errors` | No playback backend available (VOICE_DEVICE_UNAVAILABLE). |
| `TungaConfigError` | `rodd.errors` | Invalid or inconsistent RoddTtsConfig. |

All of the above are re-exported from `heretic.rodd` directly.

---

## What Rödd Must Never Control

- What the agent says — conversation content is L1 Bifröst's domain
- System prompt contents or conversation history
- MCP tool calls or tool routing (L5 Skilningr)
- Screen capture or frame injection (L3 Sjón)
- UI rendering or status event display (L4 Vébond)
- Config file loading — Rödd receives a typed `RoddConfig`; it never reads heretic.yaml directly

---

## Inputs

| Input | Source | Notes |
|---|---|---|
| `RoddConfig` | L0 Grunnr `load_config()` | Resolved and typed at Kynding; passed to Tunga.__init__(). |
| `bifrost::agent_text_delta(text)` | L1 Bifröst | Streaming text chunk; caller passes to Tunga.feed_chunk(). |
| `bifrost::agent_turn_end` | L1 Bifröst | Signals end of turn; caller calls Tunga.flush(). |

---

## Outputs (events emitted)

| Event | Consumer | Condition |
|---|---|---|
| `voice::speaking_start` | L4 Vébond | Emitted when playback begins for a chunk (v0.2: log only; Vébond wiring is v0.4). |
| `voice::speaking_end` | L4 Vébond | Emitted when playback completes for a turn (v0.2: log only). |
| `voice::error(VOICE_TTS_UNREACHABLE)` | L4 Vébond | Emitted when Tunga enters degraded mode (v0.2: log only). |
| `voice::error(VOICE_DEVICE_UNAVAILABLE)` | L4 Vébond | Emitted when no playback backend is available (v0.2: log only). |

**v0.2 event bus note:** In v0.2 these events are not yet wired to a formal event bus — they are
represented as structured log messages. The Vébond UI event integration ships in v0.4.

---

## Error Model

| Code | Class | Condition | Recovery |
|---|---|---|---|
| `VOICE_TTS_UNREACHABLE` | `ChatterboxConnectionError` | ChatterBox endpoint not reachable | Tunga enters degraded mode; ceremony continues text-only |
| `BIFROST_AUTH_FAILED` (TTS) | `ChatterboxAuthError` | HTTP 401/403 from ChatterBox | Log; enter degraded mode; do not auto-retry |
| Timeout | `ChatterboxTimeoutError` | HTTP request to /v1/audio/speech exceeds `request_timeout_seconds` | Log; drop chunk; continue ceremony |
| `VOICE_DEVICE_UNAVAILABLE` | `PlaybackBackendUnavailableError` | No playback backend available | Enter degraded mode; ceremony continues text-only |
| Config invalid | `TungaConfigError` | RoddTtsConfig validation fails | Raised at Kynding; lifecycle must catch and disable voice-out |

---

## Capability Flags

| Flag | Meaning | Set True When |
|---|---|---|
| `?voice_out` | TTS enabled and speaker available | `rodd.tts.enabled: true` AND playback backend available |
| `?voice_in` | STT enabled and mic available | v0.3 — not yet implemented |

---

## Config Keys

Full reference: `docs/architecture/LAYER_INTERFACES.md §L2 Rödd config keys`.
All defaults in `RoddTtsConfig` and `RoddSttConfig` match the reference block exactly.

```yaml
rodd:
  tts:
    enabled: true
    engine: chatterbox            # chatterbox | openai_compat (future)
    endpoint: "http://100.66.178.105:7851"
    voice_id: "default"
    voice_prompt_path: null       # path relative to heretic data dir, or null
    model: turbo                  # turbo | tts | multilingual
    language_id: en
    exaggeration: 0.5
    cfg_weight: 1.0
    temperature: 0.8
    top_p: 0.95
    repetition_penalty: 1.2
    device: default
    speed: 1.0
    request_timeout_seconds: 30
    chunk_min_chars: 80           # min chars before sentence-boundary flush
    sentence_terminators: [". ", "! ", "? ", "\n\n"]
  stt:
    enabled: true
    engine: whisper_cpp
    model_path: "models/ggml-base.en.bin"   # relative to heretic data dir
    device: default
    vad_threshold: 0.6
    language: en
    load_strategy: lazy           # lazy | eager
```

---

## SLO Tier

**Hot** — TTS first audio chunk playback start < 60 ms after first audio chunk received from
ChatterBox (per LAYER_INTERFACES.md §L2 SLO tier).

**Warm** — ChatterBox synthesis round-trip (text sent → WAV bytes received) is not under
HERETIC's control; it depends on the Pi's GPU. The chunking policy (chunk_min_chars: 80)
is designed to keep chunks large enough that ChatterBox latency is amortised.

---

## Invariants

1. No Rödd module reads `heretic.yaml` directly. All config flows through `RoddConfig`.
2. No absolute paths anywhere in Rödd. All path fields are relative strings resolved by
   `grunnr.paths.resolve_relative_path()` at runtime.
3. Tunga degrades gracefully on any ChatterBox or playback failure. It never raises to
   the caller during a live ceremony. The ceremony continues text-only.
4. The ChatterBox endpoint is never contacted during test runs — all HTTP is mocked.
5. sounddevice is an optional dependency. `pip install heretic` (without `[voice]`) must
   not fail due to a missing sounddevice import.
6. `Tunga.close()` is idempotent — calling it multiple times is safe.
7. Synthesis requests are in-flight one at a time. The sentence queue is processed in order.

---

## What Callers Must Not Assume

- That `Tunga` is reentrant. One caller, one asyncio task, in order.
- That `Tunga` can be reused after `close()`.
- That `ChatterboxHttpClient` can be reused after `close()`.
- That sounddevice is always importable — check `SoundDeviceBackend.available()` first.
- That the ChatterBox endpoint is reachable — Tunga may enter degraded mode at any time.
- That `feed_chunk()` is synchronous in the final implementation — Forge may make it async;
  callers must await it if it becomes a coroutine.
