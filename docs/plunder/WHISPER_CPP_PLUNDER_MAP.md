# whisper.cpp — Plunder Map

**Map authored:** 2026-05-07
**Author:** Eirwyn Rúnblóm, Scribe for Vibe Coding
**Status:** studying — no code adapted yet; required for v0.3 First Listening (L2 Rödd / Hlust STT)

---

## Upstream Identity

| Field | Value |
|---|---|
| Project name | whisper.cpp |
| Repository | https://github.com/ggerganov/whisper.cpp |
| Version as of write | Latest tagged release — verify at build time (e.g., v1.7.x; check GitHub releases page) |
| Primary maintainer | Georgi Gerganov (ggerganov) and community contributors |
| License | MIT |
| License URL | https://github.com/ggerganov/whisper.cpp/blob/master/LICENSE |
| License verification status | **Verified MIT 2026-05-07** (GitHub LICENSE file: MIT, copyright Georgi Gerganov) |

---

## Upstream License

**MIT License** — permissive, compatible with HERETIC's MIT license. No copyleft constraints. May be vendored, distributed as binary, or used as a subprocess without license obligations beyond copyright notice preservation.

---

## Compatibility Verdict

**CLEAN — no caveats.** MIT upstream into MIT receiving project. whisper.cpp has no GPL dependencies in its core; its optional CUDA/Metal backends are also permissively licensed. The `.gguf` model files are distributed separately under their own licenses (see model licensing note below).

**Model file licensing note:** The model weights (`.gguf` files) are derived from OpenAI's Whisper models, which are released under the MIT license by OpenAI. However, users download model files independently. HERETIC does not bundle or redistribute model files; users obtain them via the whisper.cpp model download script or equivalent. HERETIC only ships the binary or instructs users to install it — not the weights. No model license obligation falls on HERETIC.

---

## What We Plunder

whisper.cpp is used as a **runtime subprocess dependency**, not a vendored source plunder. HERETIC's L2 Rödd (Hlust / STT half) spawns it as a child process and passes audio through stdin or a temporary file.

### Runtime subprocess usage
- The `whisper-cli` binary (or `main` binary in older releases) — spawned by L2 Rödd as a subprocess.
- The `--model` flag to select GGUF model file; `--language` for locale; `--output-txt` or stdout for transcript.
- The VAD integration (if whisper.cpp's built-in VAD is used) or HERETIC handles VAD externally and passes segmented audio chunks.
- The Python bindings (`pywhisper` or `whispercpp` pip package) — may be used instead of the binary if a Python interface is preferred. Both are MIT licensed.

### Architectural patterns (study, implement locally in HERETIC style)
- The subprocess-based invocation pattern: audio in → transcript text out. HERETIC's `heretic/voice/` module implements this interface boundary.
- The model-size tradeoff table (tiny / base / small / medium / large) — referenced in `heretic.yaml` config documentation so users understand the CPU/quality tradeoff when choosing `voice.stt.model_path`.
- The GGUF model path configuration pattern — HERETIC follows this: `voice.stt.model_path` is a relative path in `heretic.yaml` (never absolute, per RULES.AI.md).

### What we study but do not copy
- The C/C++ ggml inference core — we run it as a binary, not an imported library.
- The full VAD algorithm source — if HERETIC needs custom VAD, it implements its own lightweight version rather than copying whisper.cpp's.

---

## What We DO NOT Plunder

- Any GPU backend code (CUDA/Metal/Vulkan) — these are backend optimizations inside the binary; HERETIC does not need to touch them.
- The whisper.cpp server mode (`--server`) — HERETIC runs it as a batch subprocess, not a persistent server.
- The whisper.cpp fine-tuning tools — not relevant to HERETIC.
- The Android/iOS bindings — HERETIC is a desktop application.

---

## Local Domain Ownership

| HERETIC layer | True Name | Owns this integration |
|---|---|---|
| L2 Rödd — Hlust half | Hlust (hlust) — the ear | STT subprocess management: spawn whisper.cpp binary, feed audio, receive transcript, emit `voice::transcript` events to L1 Bifröst |
| L0 Grunnr | Grunnr (grunnr) | Config: `voice.stt.model_path` (relative path), `voice.stt.device`, `voice.stt.language`, `voice.stt.vad_threshold` read from `heretic.yaml` |

The whisper.cpp binary itself is **not managed by HERETIC's codebase** — it is installed by the user or bundled as a platform binary in the distribution package. HERETIC's `heretic/voice/` module contains only the subprocess wrapper and the audio-pipe logic.

---

## Public Interface

Inside HERETIC, whisper.cpp is surfaced as follows:

- `L2 Rödd (Hlust)` manages the subprocess; no other layer knows whisper.cpp exists.
- Output: `voice::transcript(text: String, timestamp: u64, confidence: f32)` events emitted on L0 Grunnr's event bus — consumed by L1 Bifröst.
- Config consumed: `voice.stt.engine = "whisper_cpp"`, `voice.stt.model_path`, `voice.stt.language`, `voice.stt.vad_threshold`.
- Replacing whisper.cpp with another STT engine (e.g., a cloud API) changes only `heretic/voice/backends/whisper_cpp.rs` (or equivalent) — the `voice::transcript` event contract remains stable.

---

## Attribution Requirements

| Requirement | Status |
|---|---|
| Preserve LICENSE file | Yes — if binary bundled: include `whisper.cpp LICENSE` in distribution; if user-installed: note in `THIRD_PARTY_NOTICES.md` |
| NOTICE file required | No — MIT |
| In-source headers required | Only if any whisper.cpp source is directly adapted (not currently planned) |
| THIRD_PARTY_NOTICES.md entry | Yes — required |
| Trademark / branding | No trademark concerns; whisper.cpp is a community project without aggressive branding |

---

## Verification Status

- License re-verified: **2026-05-07** — MIT confirmed at https://github.com/ggerganov/whisper.cpp/blob/master/LICENSE
- Current stable version: **verify at build time** (check https://github.com/ggerganov/whisper.cpp/releases)
- Model file license: OpenAI Whisper models = MIT (https://github.com/openai/whisper/blob/main/LICENSE) — user downloads separately; not HERETIC's obligation to redistribute.
- Open question: confirm Python binding package name at build time (`whispercpp` on PyPI vs `pywhisper` vs direct subprocess invocation) — the ecosystem has fragmented. Direct subprocess invocation of the compiled binary is the most stable approach and is the recommended default.

---

## Vendor Path

**External runtime dependency — user installs binary or HERETIC bundles platform binary in release package.**

Not vendored as source. Two distribution strategies:

1. **User-installed (development builds):** User compiles from source or downloads pre-built binary. `heretic.yaml` points to binary path via env var or auto-detection.
2. **Bundled binary (release builds):** HERETIC's release pipeline includes platform-specific whisper.cpp binaries (Windows x64, macOS arm64, Linux x64). The binary ships alongside HERETIC; `LICENSE` from whisper.cpp is included in the distribution's `NOTICES/` folder.

If Python bindings are used instead: `vendor/whispercpp/` with `LICENSE` preserved, or `pip install whispercpp` as a runtime dep.

---

## Open Questions for Architect

1. **subprocess vs Python binding:** Should Hlust call the `whisper-cli` binary directly via subprocess, or use a Python binding (`whispercpp` / similar)? Trade-off: binary is more stable and hardware-accelerated; Python binding is easier to integrate into the MCP sense subprocess model. Recommend: Python binding for v0.3; migrate to direct binary if latency or hardware acceleration proves insufficient.
2. **VAD strategy:** Use whisper.cpp built-in VAD, or implement lightweight energy-threshold VAD in Rödd? whisper.cpp's VAD is accurate but adds latency. For v0.3, built-in VAD is acceptable; revisit at v0.5 if warm-path SLO (<1200ms p95) is threatened.
3. **Model bundling in release:** Decide at v1.0 packaging phase. For v0.x development: user downloads model manually via `heretic setup whisper-model --size base.en` (a setup CLI command to be designed).

---

*Plunder map authored by Eirwyn Rúnblóm, 2026-05-07.*
*Hlust — the ear — will be forged from this material. The transcript is the voice that enters the body.*
