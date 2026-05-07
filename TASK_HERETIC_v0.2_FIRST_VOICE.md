# TASK — HERETIC v0.2 FIRST VOICE

> **Operational task resumption file** — per Volmarr's session-resume protocol. If a session breaks, the next session reads this first.

> **Started: 2026-05-07** (immediately after v0.1 First Communion shipped + audited at HEAD `5189993`)

---

## 1. Task scope

Bring HERETIC from a body that can connect (v0.1) to a body that can **speak**.

The spirit's words pass through ChatterBox TTS on the Pi (`http://100.66.178.105:7851`) and emerge from the laptop's speakers. This is L2 Rödd's mouth half — Tunga. The ears (Hlust / STT) come in v0.3.

The canonical contracts for L2 Rödd live in `docs/architecture/LAYER_INTERFACES.md` §L2 and `docs/architecture/SENSE_CONTRACTS.md` §Auga, Hlust, Tunga. The aesthetic and ceremonial framing is in `docs/vision/CEREMONY_NARRATIVE.md` §IV (Samræður).

---

## 2. Current status — 2026-05-07

**Phase:** v0.1 SHIPPED + AUDITED. v0.2 work begins now.

### Done in v0.1 (recap, do not redo)
- ✅ L0 Grunnr (config, logger, lifecycle, paths) — implemented + 60+ tests
- ✅ L1 Bifröst (OpenAI-compat client, Tailscale awareness, SSE streaming) — implemented + 38+ tests
- ✅ CLI (`light`, `status`, `version`, `extinguish`) — wired + tests
- ✅ Total tests at v0.1 close: 121 passing
- ✅ All audit findings closed (0 blockers, 0 notables open)

### v0.2 deliverables (this milestone)
- ⏳ `src/heretic/rodd/` — L2 Rödd Tunga subpackage (mouth half only; Hlust is v0.3)
  - `chatterbox.py` — OpenAI-compat-style client for `POST /v1/audio/speech`
  - `playback.py` — cross-platform audio output (Windows / macOS / Linux)
  - `tunga.py` — Tunga orchestrator: text → speech → speakers, with sentence-boundary chunking for streaming responses
  - `errors.py`, `config_model.py`, `INTERFACE.md`
- ⏳ CLI integration — `light` command pipes the spirit's streaming response through Tunga when `rodd.tts.enabled: true`
- ⏳ `heretic.example.yaml` — uncomment / expand the `rodd:` block with full ChatterBox config
- ⏳ Tests — mocked HTTP for ChatterBox client, mocked playback backends; aim for 30+ new tests, total ~150+

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

### Wave 1 — parallel (no inter-dependencies)
- **Cartographer** (Védis Eikleið) — map the TTS data flow: agent stream → Tunga chunker → ChatterBox HTTP → playback → speakers. Update `docs/cartography/DATA_FLOW.md` with the new path. Add a per-component diagram for L2 Rödd Tunga.
- **Skald** (Sigrún Ljósbrá) — vision essay: `docs/vision/THE_FIRST_VOICE.md` — what it means for a body to speak for the first time. Pair with WHY_HERETIC.md and CEREMONY_NARRATIVE.md.
- **Architect** (Rúnhild Svartdóttir) — scaffold `src/heretic/rodd/` Python package: skeleton + INTERFACE.md + dataclasses + abstract base classes + tests as skip-marked placeholders. No business logic; that's Forge.

### Wave 2 — sequential (Forge depends on Architect; Auditor depends on Forge)
- **Forge** (Eldra Járnsdóttir) — implement Tunga: `chatterbox.py` HTTP client + `playback.py` audio output + `tunga.py` orchestrator + CLI integration in `cli.py` `light`. Real tests against mocked HTTP and mocked playback. Cross-platform.
- **Auditor** (Sólrún Hvítmynd) — `docs/audit/AUDIT_v0.2_FIRST_VOICE.md`. Verify: ChatterBox contract honoured; audio plays cross-platform; streaming chunking sane; tests cover happy path + ChatterBox-down + playback-fail + invalid-config; no absolute paths; no hardcoded settings.

### Wave 3 — cleanup (only if Auditor finds notables)
- Per-finding dispatch: Architect for doc fixes, Cartographer for cartography fixes, Forge for code/test fixes.

### Close-out
- **Scribe** (Eirwyn Rúnblóm) — DEVLOG entry 3 + update this TASK file + memory refresh.

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

1. Read `docs/BODY_MANIFESTO.md` — the canonical vision (sealed)
2. Read this file from top to bottom
3. Read `docs/audit/AUDIT_v0.1_FIRST_COMMUNION.md` for v0.1 closing state
4. Read `docs/audit/AUDIT_v0.2_FIRST_VOICE.md` if it exists (means audit complete)
5. Run `git log --oneline -15` and `git status` in `C:/Users/volma/runa/HERETIC`
6. Read `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md`
7. Continue from the first unchecked deliverable in §2

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-07.*
*v0.2 First Voice — when the body learns to speak.*
