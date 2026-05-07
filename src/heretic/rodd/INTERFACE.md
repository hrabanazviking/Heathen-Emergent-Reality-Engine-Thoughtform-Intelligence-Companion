# Rödd Module Interface

**Last updated:** 2026-05-07 | 2026-05-07 drift corrective pass — Rúnhild Svartdóttir, resolving N-2 (language_id semantics) and N-3 (voice WAV path semantics). Config Keys block updated: `speed` annotated removed; `voice` WAV-path semantics documented in prose; `language_id` multilingual scope and exclusion logic documented. New section §Voice Field Semantics added.
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
Canonical type definitions live in `src/heretic/rodd/config_model.py`.

> **Corrective note — 2026-05-07 (N-2, N-3 — Rúnhild Svartdóttir):**
> `speed` is removed from this block. `voice_id` and `language_id` now carry full
> semantic prose — see §Voice Field Semantics and §Language Field Semantics below.

```yaml
rodd:
  tts:
    enabled: true
    engine: chatterbox            # chatterbox | openai_compat (future)
    endpoint: "http://100.66.178.105:7851"

    # Voice field — see §Voice Field Semantics below for full prose
    voice_id: "default"           # "default" = omit from request; any other value = WAV path
    voice_prompt_path: null       # alternative path field; same WAV-path semantics; null = omit

    # Model and language — see §Language Field Semantics below
    model: turbo                  # turbo | tts | multilingual
    language_id: en               # ISO code; ONLY applied when model is "multilingual"

    exaggeration: 0.5             # float 0.0–2.0; emotional exaggeration factor
    cfg_weight: 1.0               # float 0.0–2.0; CFG dual-pass weight (tts model only)
    temperature: 0.8              # float 0.05–2.0; sampling temperature
    top_p: 0.95                   # float 0.0–1.0; nucleus sampling cutoff
    repetition_penalty: 1.2      # float 0.1–5.0; repetition penalty
    device: default               # OS audio device name or "default"
    request_timeout_seconds: 30   # int; HTTP timeout for /v1/audio/speech
    chunk_min_chars: 80           # int >= 1; min chars before sentence-boundary flush
    sentence_terminators: [". ", "! ", "? ", "\n\n"]

    # speed: 1.0
    # REMOVED 2026-05-07 (G-1, N-3 — Rúnhild Svartdóttir):
    # The live ChatterBox API has no "speed" field. This key was a pre-probe assumption.
    # It is stored in RoddTtsConfig for backward config compatibility but is never sent
    # to ChatterBox. A debug log is emitted if speed != 1.0 at synthesis time.
    # Do not set this field; it has no effect on ChatterBox output.
    # Reference: DATA_FLOW.md §4.6.1, chatterbox.py _build_request_body.

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

## Voice Field Semantics

> Resolves audit finding N-3 (2026-05-07).

The `voice_id` config key (and its alias `voice_prompt_path`) controls the `voice` field
in ChatterBox's `/v1/audio/speech` request body. The semantics are specific and must be
understood by any operator configuring voice cloning.

**`"default"` (or empty string, or `null`):**
The `voice` field is **omitted entirely** from the ChatterBox request body. ChatterBox
responds with its own built-in default voice. This is the v0.2 shipped behaviour.

**Any other value:**
The value is treated as a **WAV file path** for voice cloning — not a symbolic voice
identifier or a model name. The path undergoes the following resolution at synthesis time
(not at config load):
- `~` is expanded to the user home directory.
- Relative paths are resolved against the current working directory at synthesis time.
  Operators should prefer paths relative to the project root, as the process working
  directory is the project root by convention.
- The file must exist when synthesis runs. Config load does not validate path existence —
  this allows operators to configure a voice path before the WAV file is in place, and
  swap voice files without restarting the process.

**Model constraint for voice cloning:**
For the `turbo` model, the voice prompt WAV must be **at least 5 seconds** in duration.
ChatterBox enforces this on the server side; shorter files will result in a synthesis
error (ChatterboxApiError). The `tts` and `multilingual` models have a lower minimum;
consult the ChatterBox documentation for those models.

**Implementation reference:** `src/heretic/rodd/chatterbox.py`, method `_resolve_voice_path`.

---

## Language Field Semantics

> Resolves audit finding N-2 (2026-05-07).

The `language_id` config key controls whether the `language_id` field appears in the
ChatterBox `/v1/audio/speech` request body. Its behavior depends on the configured model.

**When `model` is `turbo` or `tts`:**
`language_id` is **excluded from the request body**, regardless of the configured value.
Both `turbo` and `tts` are English-only models. Sending `language_id` to these models
would be a no-op at best and may produce an API warning. The implementation detects this
by checking whether the effective `language_id` value equals `"en"` (the default) or is
empty — if so, the field is omitted. In practice, with `turbo` or `tts`, setting any
value for `language_id` in `heretic.yaml` has no effect on the synthesised audio.

**When `model` is `multilingual`:**
`language_id` IS included in the request body when its value is non-empty and not equal
to `"en"`. The exclusion of `"en"` is intentional: ChatterBox's multilingual model
defaults to English, so sending `language_id: "en"` is redundant. When set to any other
ISO code, the field is included and ChatterBox synthesises in that language.

Supported ISO 639-1 codes (ChatterBox multilingual model, probed 2026-05-07):
`en`, `de`, `es`, `fr`, `it`, `pt`, `pl`, `nl`, `ru`, `ja`, `ko`, `zh`, `ar`, `tr`,
`id`, `vi`, `th`, `cs`, `sv`, `da`, `fi`, `el`, `ro` (23 languages).

**Default behaviour summary:**

| Configured value | Model | Field in request body |
|---|---|---|
| `"en"` (default) | `turbo` or `tts` | Omitted |
| `"en"` | `multilingual` | Omitted (ChatterBox default) |
| `"de"` (any non-"en") | `turbo` or `tts` | Omitted (model is English-only) |
| `"de"` (any non-"en") | `multilingual` | Included — `"language_id": "de"` |

**Implementation reference:** `src/heretic/rodd/chatterbox.py`, method `_build_request_body`,
the `effective_language` block at approximately line 254.

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
