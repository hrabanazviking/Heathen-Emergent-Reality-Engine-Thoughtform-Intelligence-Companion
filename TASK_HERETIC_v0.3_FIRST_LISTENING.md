# TASK — HERETIC v0.3 FIRST LISTENING

> **Operational task resumption file** — per Volmarr's session-resume protocol. If a session breaks, the next session reads this first.

> **Started: 2026-05-07** (immediately after v0.2 First Voice shipped + audited at HEAD `f9c58cd`)

---

## 1. Task scope

Bring HERETIC from a body that can connect (v0.1) and speak (v0.2) to a body that can also **listen**.

The user's spoken words enter through the laptop microphone, pass through Voice Activity Detection (VAD), are transcribed by Whisper.cpp running locally on the same machine, and become text that flows through L1 Bifröst to the spirit. This is L2 Rödd's ear half — **Hlust**. The mouth (Tunga) shipped in v0.2; together they complete L2.

The canonical contract for L2 Rödd lives in `docs/architecture/LAYER_INTERFACES.md §L2`. The `rodd.stt:` config block and `RoddSttConfig` dataclass already exist (declared in v0.2 to keep `heretic.yaml` parseable). The aesthetic and ceremonial framing should appear as `docs/vision/THE_FIRST_LISTENING.md` (Skald wave-1 deliverable).

---

## 2. Current status — 2026-05-07

**Phase:** v0.2 SHIPPED + AUDITED at `f9c58cd`. v0.3 work begins now. Baseline: 224 tests passing.

### Done in v0.1+v0.2 (recap, do not redo)
- v0.1: L0 Grunnr, L1 Bifröst, CLI shell — 121 tests
- v0.2: L2 Rödd Tunga (TTS via ChatterBox) + 103 new tests → 224 tests
- All audit findings closed
- `RoddSttConfig` dataclass already exists at `src/heretic/rodd/config_model.py:130-160`

### v0.3 deliverables (this milestone)
- ⏳ `src/heretic/rodd/microphone.py` — cross-platform mic capture (sounddevice primary, platform fallback)
- ⏳ `src/heretic/rodd/vad.py` — Voice Activity Detection wrapper (webrtcvad primary, energy-threshold fallback)
- ⏳ `src/heretic/rodd/whisper_engine.py` — Whisper.cpp wrapper (pywhispercpp primary, CLI subprocess fallback)
- ⏳ `src/heretic/rodd/hlust.py` — Hlust orchestrator: mic → VAD → Whisper → text
- ⏳ Lazy model loading per audit C-Q-C1 resolution: model loads on first utterance, NOT at Kynding
- ⏳ CLI integration — when `rodd.stt.enabled: true`, the `light` command captures from mic instead of stdin (with stdin fallback for piped input / non-interactive contexts)
- ⏳ `heretic.example.yaml` — `rodd.stt:` block already complete from v0.2; verify
- ⏳ Tests — mocked microphone, mocked Whisper, mocked VAD; aim for 30+ new tests; total ~255+

### Constraints carried from v0.1+v0.2
- All settings via `heretic.yaml` (no hardcoding)
- No absolute paths
- Cross-platform (Windows / Linux / macOS)
- Modular, fault-tolerant, type-hinted
- `max_tokens: 127000` continues to apply where relevant
- Fault tolerance: if Hlust can't capture or transcribe, lifecycle does not crash — fall back to stdin with warning log
- Whisper.cpp is GPL... wait, no — whisper.cpp is **MIT** (per `docs/plunder/WHISPER_CPP_PLUNDER_MAP.md`). It's permissively licensed; safe to wrap as a runtime dep or embed if Forge chooses.

---

## 3. Whisper integration choices

Three viable approaches, in order of preference:

### Option A (preferred) — pywhispercpp Python bindings
- Package: `pywhispercpp` on PyPI (MIT, wraps whisper.cpp)
- Pro: clean Python API; no subprocess marshalling; reasonable performance
- Con: requires native build at install time on some platforms; binary wheel availability depends on platform
- Add to `[voice]` extra alongside `sounddevice`/`numpy`/`webrtcvad`
- Falls back gracefully via `available()` check if import fails

### Option B (fallback) — whisper.cpp CLI subprocess
- User installs `whisper-cli` binary themselves; HERETIC subprocesses to it
- Pro: zero install pain for HERETIC; works wherever whisper-cli is on PATH
- Con: per-utterance subprocess startup cost; serialization via temp WAV files
- Use as fallback when pywhispercpp unavailable

### Option C (rejected for v0.3) — faster-whisper
- Different implementation (CT2-based), not whisper.cpp
- Different license profile and accuracy curve
- Out of scope; reconsider in v0.3.x if user demand emerges

**Forge decides at implementation time**: try pywhispercpp first; if it fails to import, try `shutil.which("whisper-cli")`; if neither, return `available() = False` and fall back to stdin.

---

## 4. VAD (Voice Activity Detection) choices

VAD is needed to know when the user finished speaking. Three approaches:

### Option A (preferred) — webrtcvad
- Package: `webrtcvad-wheels` on PyPI (BSD-3, prebuilt wheels)
- Pro: small, fast, well-tested, real-time on 30ms frames
- Con: expects 16kHz int16 PCM; we feed sounddevice output through a small adapter

### Option B (fallback) — energy-threshold
- Pure Python: compute RMS over the last N frames; if below threshold for K seconds, utterance ended
- Pro: zero deps, works always
- Con: noisy in real-world (fans, breathing, ambient noise)
- Use only when webrtcvad unavailable

### Option C (rejected for v0.3) — silero-vad
- Heavier (PyTorch), better accuracy
- Out of scope; reconsider for v0.3.x or v1.x

---

## 5. Microphone capture

Reuse `sounddevice` (already in `[voice]` extra from v0.2). Capture at 16 kHz mono int16 (Whisper's native input format) — saves a resampling step.

Stream the mic input as 30ms frames to VAD. Buffer accumulating frames. On VAD-detected end-of-utterance:
- Stop capture
- Concatenate accumulated frames
- Feed buffer to Whisper for transcription
- Yield text to caller (Hlust orchestrator → CLI loop → Bifröst)

If sounddevice unavailable: log warning, set Hlust unavailable, CLI falls back to stdin.

---

## 6. CLI integration model

When `rodd.stt.enabled: true` AND Hlust initialises successfully AND stdin is a TTY:
- Replace the `await loop.run_in_executor(None, sys.stdin.readline)` in `cli.py:153` with `await hlust.capture_one_utterance()` returning the transcribed text
- Display a small "[listening...]" cue when the user should speak
- After transcription, display the transcribed text so the user can confirm what was heard before it sends

When `rodd.stt.enabled: false` OR Hlust unavailable OR stdin is piped (not a TTY):
- Use the existing stdin path

This preserves scriptability (piping `echo "hi" | heretic light`) while enabling voice when configured.

---

## 7. Architectural decisions for v0.3

| Decision | Choice | Rationale |
|---|---|---|
| Whisper integration | pywhispercpp primary, CLI fallback | MIT; clean Python API; graceful fallback to user-installed whisper-cli binary. |
| VAD | webrtcvad primary, energy-threshold fallback | BSD-3; small; real-time. Energy-threshold guarantees zero-dep fallback. |
| Mic capture | sounddevice (reuse from v0.2 [voice] extra) | Already present; cross-platform; 16kHz int16 PCM matches Whisper input. |
| Model loading | Lazy (resolves audit C-Q-C1) | Sealed in v0.0 audit. Load on first utterance, not at Kynding. |
| CLI integration | Replace stdin readline when STT enabled + TTY | Preserves scriptability via stdin fallback. |
| Confirmation display | Show transcript before send | User can correct or cancel. Reduces hallucination harm. |
| Failure mode | Fall back to stdin with warning log | Per RULES.AI fault tolerance. Listening is augmentation, not blocking. |
| L5 Hlust sense | Out of scope for v0.3 | Hlust as MCP-callable agent tool is later. v0.3 = human → spirit input only. |
| Webcam capture | Out of scope (v0.5+) | L3 Sjón is its own milestone. |

---

## 8. Roadmap slot (from `docs/ROADMAP.md`)

> **v0.3 — First Listening** — STT — you speak to Hermes via Whisper.cpp — L2 (in) — 1-2 wk

Exit criteria (this task):
- `heretic light` with `rodd.stt.enabled: true` lets the user speak; transcript is shown; spirit receives it
- VAD correctly ends utterance after speech stops
- Whisper model lazy-loads on first utterance
- Configurable via `heretic.yaml` `rodd.stt.*` keys (already declared)
- Graceful degradation if mic, VAD, or Whisper unavailable
- Test count ≥255 total (224 + ~30+)
- Audit verdict PASS or PASS WITH CONCERNS, no blockers

---

## 9. Mythic Engineering wave plan

Same protocol as v0.1 + v0.2.

### Wave 1 — parallel (no inter-dependencies)
- **Cartographer** (Védis Eikleið) — map the listening flow: mic → 30ms frames → VAD → utterance buffer → Whisper → transcript → Bifröst. Update `docs/cartography/DATA_FLOW.md` with the new inbound voice path. Add a per-component diagram for L2 Rödd Hlust. Also clean v0.2.x backlog items (§4.6.4 abbreviated config table + §4.6.1 inline `voice_id` annotation alignment).
- **Skald** (Sigrún Ljósbrá) — `docs/vision/THE_FIRST_LISTENING.md` — vision essay companion to THE_FIRST_VOICE. The body has had a tongue since v0.2; v0.3 gives it ears. Pair with WHY_HERETIC, CEREMONY_NARRATIVE, THE_FIRST_VOICE.
- **Architect** (Rúnhild Svartdóttir) — scaffold the four new modules (microphone.py, vad.py, whisper_engine.py, hlust.py) with INTERFACE.md updates, abstract base classes, NotImplementedError stubs, skip-marked placeholder tests. Update pyproject.toml `[voice]` extra with `pywhispercpp` and `webrtcvad-wheels` (both as optional). No business logic.

### Wave 2 — sequential (Forge depends on Architect; Auditor depends on Forge)
- **Forge** (Eldra Járnsdóttir) — implement Hlust end-to-end: mic capture, VAD wrapper, Whisper engine, orchestrator, CLI integration in `cli.py` `light`. Real tests against mocked sounddevice / mocked VAD / mocked Whisper. Cross-platform.
- **Auditor** (Sólrún Hvítmynd) — `docs/audit/AUDIT_v0.3_FIRST_LISTENING.md`. Verify: mic capture cross-platform; VAD logic sane; lazy model loading honoured; transcript confirmation surfaces; tests cover happy path + mic-unavailable + Whisper-unavailable + VAD-unavailable + invalid-config; no absolute paths; no hardcoded settings; fault tolerance solid.

### Wave 3 — cleanup (only if Auditor finds notables)
- Per-finding dispatch, same pattern as v0.1 and v0.2.

### Close-out
- **Scribe** (Eirwyn Rúnblóm) — DEVLOG entry 4 + update this TASK file + memory refresh.

---

## 10. Files to be created (Forge target list)

```
src/heretic/rodd/
  microphone.py       # MicrophoneCapture ABC + SoundDeviceMicBackend + NullMicBackend
  vad.py              # VadDetector ABC + WebRtcVadBackend + EnergyThresholdBackend + NullVadBackend
  whisper_engine.py   # WhisperEngine ABC + PyWhisperCppBackend + CliSubprocessBackend + NullWhisperBackend
  hlust.py            # Hlust orchestrator
tests/
  test_rodd_microphone.py
  test_rodd_vad.py
  test_rodd_whisper.py
  test_rodd_hlust.py
  test_cli_listen.py  # CLI integration
```

Existing files Forge updates (additive):
- `src/heretic/rodd/__init__.py` — export new types
- `src/heretic/rodd/INTERFACE.md` — extend with Hlust contract
- `src/heretic/cli.py` — wire Hlust into `_async_light`
- `pyproject.toml` — `[voice]` extra adds `pywhispercpp` and `webrtcvad-wheels`
- `heretic.example.yaml` — verify `rodd.stt:` block matches `RoddSttConfig` defaults (already done in v0.2; verify)

---

## 11. Operational rules (carried from v0.1+v0.2, immutable)

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

## 12. v0.2.x backlog (carry forward; address in wave 1)

From v0.2 Scribe close-out:
- `docs/cartography/DATA_FLOW.md §4.6.4` — abbreviated 6-key config table needs alignment with corrected 17-field LAYER_INTERFACES.md L2 block (Cartographer's territory)
- `docs/cartography/DATA_FLOW.md §4.6.1` — inline `voice_id` annotation needs updating to reflect WAV-path semantics

Cartographer wave-1 brief includes these.

---

## 13. How to resume this task in a future session

1. Read `docs/BODY_MANIFESTO.md` — sealed vision
2. Read this file from top to bottom
3. Read `docs/audit/AUDIT_v0.2_FIRST_VOICE.md` for v0.2 closing state
4. Read `docs/audit/AUDIT_v0.3_FIRST_LISTENING.md` if it exists (audit complete)
5. Run `git log --oneline -15` and `git status` in `C:/Users/volma/runa/HERETIC`
6. Read `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md`
7. Continue from the first unchecked deliverable in §2

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-07.*
*v0.3 First Listening — when the body learns to listen.*
