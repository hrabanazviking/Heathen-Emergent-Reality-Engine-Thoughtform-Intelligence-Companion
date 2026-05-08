# TASK — HERETIC v0.2 FIRST VOICE

> **Operational task resumption file** — per Volmarr's session-resume protocol. If a session breaks, the next session reads this first.

> **Started: 2026-05-07** (immediately after v0.1 First Communion shipped + audited at HEAD `5189993`)
> **Status: v0.2 SHIPPED + AUDITED 2026-05-07** — HEAD `435dfa3`, 224 tests passing, 0 open findings

---

## 1. Task scope

Bring HERETIC from a body that can connect (v0.1) to a body that can **speak**.

The spirit's words pass through ChatterBox TTS on the Pi (`http://100.66.178.105:7851`) and emerge from the laptop's speakers. This is L2 Rödd's mouth half — Tunga. The ears (Hlust / STT) come in v0.3.

The canonical contracts for L2 Rödd live in `docs/architecture/LAYER_INTERFACES.md` §L2 and `docs/architecture/SENSE_CONTRACTS.md` §Auga, Hlust, Tunga. The aesthetic and ceremonial framing is in `docs/vision/CEREMONY_NARRATIVE.md` §IV (Samræður).

---

## 2. Current status — 2026-05-07

**Phase:** v0.2 SHIPPED + AUDITED 2026-05-07. All deliverables complete.

### Done in v0.1 (recap, do not redo)
- ✅ L0 Grunnr (config, logger, lifecycle, paths) — implemented + 60+ tests
- ✅ L1 Bifröst (OpenAI-compat client, Tailscale awareness, SSE streaming) — implemented + 38+ tests
- ✅ CLI (`light`, `status`, `version`, `extinguish`) — wired + tests
- ✅ Total tests at v0.1 close: 121 passing
- ✅ All audit findings closed (0 blockers, 0 notables open)

### v0.2 deliverables (this milestone)
- ✅ `src/heretic/rodd/` — L2 Rödd Tunga subpackage (mouth half only; Hlust is v0.3) — Done 2026-05-07
  - ~~`chatterbox.py` — OpenAI-compat-style client for `POST /v1/audio/speech`~~ Done 2026-05-07 (`d4fd532`)
  - ~~`playback.py` — cross-platform audio output (Windows / macOS / Linux)~~ Done 2026-05-07 (`d4fd532`)
  - ~~`tunga.py` — Tunga orchestrator: text → speech → speakers, with sentence-boundary chunking for streaming responses~~ Done 2026-05-07 (`077bd9a`)
  - ~~`errors.py`, `config_model.py`, `INTERFACE.md`~~ Done 2026-05-07 (`b7e978e` scaffold + `d4fd532` implementation)
- ✅ CLI integration — `light` command pipes the spirit's streaming response through Tunga when `rodd.tts.enabled: true` — Done 2026-05-07 (`e4a5232`)
- ✅ `heretic.example.yaml` — `rodd:` block updated with full ChatterBox config including all 17 synthesis fields — Done 2026-05-07
- ✅ Tests — 103 new tests added (Wave 2: 100; Wave 3: 3); total at v0.2 close: **224 passing** — Done 2026-05-07

### Constraints carried from v0.1
- All settings via `heretic.yaml` (no hardcoding)
- No absolute paths
- Cross-platform (Windows / Linux / macOS)
- Modular, fault-tolerant, type-hinted
- `max_tokens: 127000` continues to apply where relevant
- Fault tolerance: if Tunga can't reach ChatterBox, lifecycle does not crash — fall back to text-only output with warning log

---

## 3. ChatterBox API contract (probed live 2026-05-07)

Endpoint: `http://100.66.178.105:7851`

| Path | Method | Purpose |
|---|---|---|
| `/health` | GET | Health check |
| `/v1/models` | GET | List available TTS variants |
| `/v1/audio/speech` | POST | Generate WAV audio from text |

### `/v1/models` response
Three variants available:
- `turbo` (default, always-warm, GPT2-medium T3 + meanflow S3Gen, voice prompt ≥5s)
- `tts` (full English with CFG dual-pass, slower, higher quality)
- `multilingual` (23 languages, requires `language_id`)

### `/v1/audio/speech` request schema
```json
{
  "model": "turbo",                         // optional, default "turbo"
  "input": "text to speak",                 // 1-4000 chars
  "voice": "/path/to/voice_prompt.wav",     // optional, ≥5s for turbo
  "response_format": "wav",                 // only "wav" supported
  "language_id": "en",                      // multilingual only
  "exaggeration": 0.5,                      // optional, 0.0-2.0
  "cfg_weight": 1.0,                        // optional, 0.0-2.0
  "temperature": 0.8,                       // default 0.8, 0.05-2.0
  "top_p": 0.95,                            // optional, 0.0-1.0
  "repetition_penalty": 1.2                 // default 1.2, 0.1-5.0
}
```
Returns: WAV audio bytes (`Content-Type: audio/wav`).

### Recommended v0.2 defaults
- Model: `turbo` (lowest latency, suitable for streaming response speech)
- No voice prompt initially (use ChatterBox's built-in default voice)
- Temperature: 0.8 (default)
- Repetition penalty: 1.2 (default)
- Streaming policy: speak per sentence boundary (`. `, `! `, `? `, `\n\n`) once 80+ chars accumulated, OR at end-of-stream, whichever comes first

---

## 4. Architectural decisions for v0.2

| Decision | Choice | Rationale |
|---|---|---|
| L2 substrate vs L5 sense | **L2 substrate only in v0.2** | L5 Skilningr/Tunga MCP wrapper is later (v0.7). v0.2 = automatic pass-through. |
| Audio backend | `sounddevice` library | Cross-platform pure-Python, no native shell-out, works on Windows/macOS/Linux. Falls back to platform commands (`aplay`/`afplay`/`winsound`) only if sounddevice unavailable. |
| Streaming chunking | Sentence-boundary, min 80 chars | Latency-vs-naturalness tradeoff. Avoids speaking single words (jarring) and avoids waiting for full response (slow). |
| Voice prompt | None for v0.2 (default ChatterBox voice) | User can configure later via `rodd.tts.voice_prompt_path`. v0.2 ships out-of-box. |
| Failure mode | Fall back to text-only logging | Per RULES.AI fault tolerance. Voice is augmentation, not blocking. |
| HTTP client | Reuse `httpx` from L1 | Already a dependency. Async fits the streaming pattern. |
| Concurrent requests | Single in-flight request, queue | Simpler than parallel. Sentences arrive in order; speak in order. |

---

## 5. Roadmap slot (from `docs/ROADMAP.md`)

> **v0.2 — First Voice** — TTS — Hermes speaks through ChatterBox — L2 (out) — 1 wk

Exit criteria (this task):
- `heretic light` causes the spirit's spoken words to be heard from the laptop speakers
- Streaming response → audio in near-real-time (sentence-by-sentence)
- Configurable via `heretic.yaml` `rodd.tts.*` keys
- Graceful degradation if ChatterBox unreachable
- Test count ≥150 total
- Audit verdict PASS or PASS WITH CONCERNS, no blockers

---

## 6. Mythic Engineering wave plan

Same protocol as v0.1. Six roles, two waves, plus close-out.

### Wave 1 — parallel (no inter-dependencies) — COMPLETE
- ✅ **Cartographer** (Védis Eikleið) — `docs/cartography/DATA_FLOW.md §4.6` voice flow + §4.6.1 drift annotations — Done 2026-05-07 (`ecb8507`)
- ✅ **Skald** (Sigrún Ljósbrá) — `docs/vision/THE_FIRST_VOICE.md` — Done 2026-05-07 (`7d4c27f`)
- ✅ **Architect** (Rúnhild Svartdóttir) — `src/heretic/rodd/` skeleton + INTERFACE.md — Done 2026-05-07 (`b7e978e`)

### Wave 2 — sequential — COMPLETE
- ✅ **Forge** (Eldra Járnsdóttir) — `chatterbox.py` + `playback.py` (`d4fd532`); `tunga.py` + CLI wiring + 101 tests (`077bd9a`, `e4a5232`) — Done 2026-05-07
- ✅ **Auditor** (Sólrún Hvítmynd) — `docs/audit/AUDIT_v0.2_FIRST_VOICE.md` — PASS WITH CONCERNS, 0 blockers, 2 SERIOUS, 3 NOTABLE — Done 2026-05-07 (`59414d8`)

### Wave 3 — cleanup — COMPLETE
- ✅ **Forge**: S-1 (grunnr RoddTtsConfig parity + parity test), S-2 (numpy probe in available() + pyproject.toml), N-1 (get_running_loop) — Done 2026-05-07 (`03dbbea`, `4aebd98`, `bf77abe`, `435dfa3`)
- ✅ **Architect**: G-1 (LAYER_INTERFACES.md §L2 full schema), N-2 (INTERFACE.md language_id note + test), N-3 (INTERFACE.md WAV path prose) — Done 2026-05-07 (`fee6816`)

### Close-out — COMPLETE
- ✅ **Scribe** (Eirwyn Rúnblóm) — DEVLOG entry 3 + TASK file update + memory refresh — Done 2026-05-07

---

## 7. Files to be created (Forge target list)

```
src/heretic/rodd/
  __init__.py
  INTERFACE.md
  config_model.py       # RoddConfig + RoddTtsConfig + RoddSttConfig dataclasses
  errors.py             # RoddError, ChatterboxError, PlaybackError, etc.
  chatterbox.py         # ChatterboxClient — HTTP client for the Pi service
  playback.py           # AudioPlayback — sounddevice-first, platform-fallback
  tunga.py              # Tunga orchestrator — text-stream-to-speech-stream
tests/
  test_rodd_chatterbox.py
  test_rodd_playback.py
  test_rodd_tunga.py
  test_rodd_config.py     # if config_model.py has its own logic worth testing
  test_cli_voice.py       # CLI integration
```

---

## 8. Operational rules (carried from v0.1, immutable)

- Branch: `development` only
- Push frequently (every wave at minimum)
- No absolute paths
- No hardcoded settings — everything via `heretic.yaml`
- Modular, fault-tolerant, cross-platform
- No emoji in code or docs
- Type hints everywhere, PEP 8
- Each subagent commits with their own attribution line
- After EVERY completed phase: update this TASK file + memory immediately

---

## 9. How to resume this task in a future session

v0.2 is fully closed — no unchecked deliverables remain. The next task is **v0.3 First Listening** (STT via Whisper.cpp).

To orient for v0.3:
1. Read `docs/BODY_MANIFESTO.md` — the canonical vision (sealed)
2. Read `docs/ROADMAP.md §v0.3` — milestone scope for STT / Hlust
3. Read `docs/audit/AUDIT_v0.2_FIRST_VOICE.md` for v0.2 closing audit detail
4. Read `docs/DEVLOG.md` entry 3 (2026-05-07 — The First Voice Arc) for full session record
5. Run `git log --oneline -15` and `git status`
6. Read `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md`
7. Open a new task file: `TASK_HERETIC_v0.3_FIRST_LISTENING.md`

The Tunga pattern (chunked streaming, lifecycle-bound open/close, graceful degradation, `_degraded` flag, `run_in_executor` for blocking calls) is the established template for v0.3 Hlust.

---

## 10. v0.2.x backlog (open items, not yet started)

These items do not block v0.2 milestone delivery. They are preserved here so a future Cartographer or Forge pass can find them cleanly.

### Cartographer alignment items (DATA_FLOW.md drift)

| Item | Location | Work needed |
|---|---|---|
| §4.6.4 config table | `docs/cartography/DATA_FLOW.md §4.6.4` | Abbreviated 6-key table predates the ChatterBox probe. Should reflect the full 17-field `RoddTtsConfig` schema now canonical in `LAYER_INTERFACES.md §L2`. Invoke Cartographer. |
| §4.6.1 inline annotation | `docs/cartography/DATA_FLOW.md §4.6.1` | Inline code annotation still references `rodd.tts.voice_id`. Should be `rodd.tts.voice_prompt_path` per the corrected field name established in Wave 3. Invoke Cartographer. |

### Forge fragilities (noted, non-blocking)

| Item | Location | Notes |
|---|---|---|
| numpy probe regression risk | `src/heretic/rodd/playback.py` `SoundDeviceBackend.available()` | S-2 was resolved by adding numpy probe inside `available()`. If `sounddevice`'s transitive dependency relationship with numpy changes in a future package version, the probe provides the safety net. Watch for `ImportError` appearing in Kynding logs rather than at play-time — that is the signal the probe is working. No action needed now. |
| `sounddevice` blocking-play in default thread pool | `src/heretic/rodd/tunga.py` `_speak_chunk()` | `run_in_executor(None, ...)` uses the default thread pool. Long audio clips occupy one thread for their duration. With `_speak_lock` bounding this to one concurrent synthesis, the impact is acceptable for the current single-turn CLI use-case. If v0.4+ introduces parallel ceremonies, revisit whether a dedicated executor is warranted. |

### NIT items from audit (deferred, non-blocking)

| ID | Item | Work needed |
|---|---|---|
| X-1 | `src/heretic/rodd/config_model.py:44` — Pi Tailscale IP as dataclass default | Consider an empty-string default with clear error if not configured. Minor UX improvement; does not affect working ceremonies where `heretic.yaml` is properly configured. |
| X-2 | `tests/test_cli_voice.py` — only 3 integration tests | Add tests that exercise the `feed_chunk` → `flush` path through the full turn loop, not just Tunga instantiation. |
| X-3 | `tests/test_rodd_chatterbox.py` — HTTP 403 not tested | Add `test_synthesize_raises_auth_error_on_403` alongside the existing 401 test. |

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-07.*
*Updated by Eirwyn Rúnblóm (Scribe), 2026-05-07 — v0.2 SHIPPED + AUDITED, all waves closed.*
*v0.2 First Voice — the body learned to speak. v0.3 First Listening is next.*
