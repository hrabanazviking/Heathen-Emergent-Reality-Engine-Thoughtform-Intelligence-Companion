# HERETIC — Audit: v0.2 First Voice

**Date:** 2026-05-07
**Auditor:** Sólrún Hvítmynd (Auditor role, Mythic Engineering)
**Scope:** Full code audit of the v0.2 First Voice wave: `src/heretic/rodd/` (all modules), `src/heretic/cli.py` (Tunga integration), `tests/test_rodd_*.py`, `tests/test_cli_voice.py`, `pyproject.toml` `[voice]` extra, `docs/cartography/DATA_FLOW.md §4.6–§4.6.4`, `docs/architecture/LAYER_INTERFACES.md §L2`, `src/heretic/rodd/INTERFACE.md`. Branch: `development`. Commits since prior audit: `7d4c27f`, `ecb8507`, `b7e978e`, `d4fd532`, `077bd9a`, `e4a5232`.
**Environment:** Windows 11 Home 10.0.22621, Python 3.11.9, PowerShell.

**Commands run:**
- `py -3.11 -m pytest tests/ -v 2>&1 | tail -60`
- `py -3.11 -m heretic version`
- `py -3.11 -m heretic --help`
- `py -3.11 -m heretic status`
- `py -3.11 -m pytest tests/ --collect-only -q` (per-module counts)
- `grep -rn "C:/Users|C:\\Users|/home/|/Users/" src/ tests/` (absolute path check)
- `grep -rn "endpoint = \"" src/heretic/rodd/` (hardcoded URL check)
- `grep -n "numpy" pyproject.toml src/heretic/rodd/playback.py` (dependency check)
- `grep -rn "print(" src/heretic/rodd/` (print in library check)
- `grep -n "class RoddTtsConfig" src/heretic/grunnr/config.py` (grunnr stub check)
- `grep -n "temperature|exaggeration|chunk_min_chars" src/heretic/grunnr/config.py` (stub field gap)
- `grep -n "asyncio.get_event_loop" src/heretic/rodd/tunga.py` (event loop call)
- `grep -n "DATA_FLOW|4.6.1|drift" src/heretic/rodd/chatterbox.py`
- `grep -n "WAV file path|voice cloning" src/heretic/rodd/INTERFACE.md`
- `grep -n "language_id.*en" src/heretic/rodd/chatterbox.py`
- Read all source files: `rodd/__init__.py`, `rodd/chatterbox.py`, `rodd/config_model.py`, `rodd/errors.py`, `rodd/playback.py`, `rodd/tunga.py`, `rodd/INTERFACE.md`, `cli.py`, `grunnr/config.py` (§RoddTtsConfig + _hydrate_config).
- Read all test files: `test_rodd_chatterbox.py`, `test_rodd_playback.py`, `test_rodd_tunga.py`, `test_rodd_config.py`, `test_rodd_errors.py`, `test_cli_voice.py`.

---

## Summary Verdict

**PASS WITH CONCERNS**

The v0.2 voice layer is structurally sound. 221 tests pass. The ChatterBox API contract is correctly implemented in `chatterbox.py`: endpoint paths, field names, `response_format: "wav"` hardcoded, `speed` drift handled with a debug-log guard and zero API exposure, `voice` field correctly omitted on `"default"`. The sentence-boundary chunker uses the last-boundary policy as designed. Fault tolerance is thorough — ChatterBox down, playback unavailable, 3-consecutive-failure degradation, idempotent close. No absolute paths in code. No emoji. No `print()` in library code.

Two SERIOUS findings break the operator's ability to configure v0.2 TTS from `heretic.yaml`: the grunnr `RoddTtsConfig` stub is missing 10 synthesis and chunking fields, so any operator-set `temperature`, `model`, `exaggeration`, `chunk_min_chars` etc. in `heretic.yaml` are silently discarded. The `[voice]` extra does not declare `numpy` despite `SoundDeviceBackend.play()` importing it at call-time; a `pip install heretic[voice]` without separately installing numpy will crash on first audio playback attempt.

These are configuration-path failures, not ceremony-crashing failures — a degraded-mode ceremony still runs text-only. Neither blocks a development milestone, but both must be fixed before v0.2 is tagged stable.

| Severity | Count | Items |
|---|---|---|
| BLOCKER | 0 | — |
| SERIOUS | 2 | S-1 (grunnr RoddTtsConfig stub gap), S-2 (numpy absent from [voice] extra) |
| NOTABLE | 3 | N-1 (asyncio.get_event_loop deprecated), N-2 (language_id silently excluded for "en"), N-3 (voice_id WAV semantics undocumented in INTERFACE.md prose) |
| NIT | 3 | X-1 (default endpoint hardcoded in rodd config_model), X-2 (cli_voice tests thin — only 3 tests for TENGSL integration), X-3 (test_rodd_chatterbox missing 403 coverage) |
| VERIFIED | 10 | A-1 request fields, A-2 response_format, A-3 voice field omission, A-4 speed drift, A-5 endpoint paths, A-6 error mapping, A-7 chunking boundary, A-8 flush no-min-length, A-9 lifecycle integration, A-10 fault tolerance |
| DRIFT/BACKLOG | 1 | G-1 (LAYER_INTERFACES.md L2 still shows legacy `speed` and minimal `tts` block — cleanup deferred per §G-1 below) |

---

## Part 1 — Internal Consistency (Section A)

---

### A-1 — ChatterBox API Request Fields

**Claim:** `chatterbox.py` `_build_request_body()` sends the correct fields per the live API contract from `TASK_HERETIC_v0.2_FIRST_VOICE.md §3`.

**Evidence:** Read `src/heretic/rodd/chatterbox.py:219–284`. Fields in the output dict:

| Contract field | Present in body | Source |
|---|---|---|
| `model` | Yes — line 242 | config.model or override |
| `input` | Yes — line 243 | text argument |
| `response_format` | Yes — line 244 | hardcoded `"wav"` |
| `voice` | Yes — line 251 | present only when not "default"/None |
| `language_id` | Yes — line 257 | present only when not "en" |
| `exaggeration` | Yes — line 261 | config or override |
| `cfg_weight` | Yes — line 263 | config or override |
| `temperature` | Yes — line 265 | config or override |
| `top_p` | Yes — line 267 | config or override |
| `repetition_penalty` | Yes — line 270 | config or override |
| `speed` | Absent — intentionally | drift guard at line 277 |

**Verdict: VERIFIED.** All 10 contract fields present. `speed` correctly excluded. `response_format` hardcoded to `"wav"`.

---

### A-2 — Voice Field Handling

**Claim:** `"default"` or `None` → field omitted; WAV path → resolved and sent.

**Evidence:** `chatterbox.py:201–217` (`_resolve_voice_path`):
```python
if not voice_value or voice_value.strip().lower() == "default":
    return None
resolved = Path(voice_value).expanduser().resolve()
return str(resolved)
```

`_build_request_body:248–251`:
```python
effective_voice = voice if voice is not None else self._config.voice_prompt_path
resolved_voice = self._resolve_voice_path(effective_voice)
if resolved_voice is not None:
    body["voice"] = resolved_voice
```

Test coverage: `test_synthesize_voice_default_omits_voice_field` (line 268) and `test_synthesize_empty_voice_omits_voice_field` (line 291) both assert `"voice" not in captured_body[0]`. WAV path resolution: a capturing transport test at line 238 verifies the model field; voice path resolution is exercised implicitly. A dedicated WAV-path-value test is absent from `test_rodd_chatterbox.py` — the resolve path logic is not directly tested for the non-"default" branch.

**Verdict: VERIFIED** for the omission path. The WAV path resolution branch has no direct test coverage — flagged as NIT-level (X-3 is about 403; this attaches to N-3 below).

---

### A-3 — Speed Drift Handling

**Claim:** `speed` in config is accepted, not sent to ChatterBox, and triggers a debug log at non-default values. Reference: `DATA_FLOW.md §4.6.1`.

**Evidence:** `chatterbox.py:274–282`:
```python
# NOTE: `speed` from config is intentionally NOT included here.
if hasattr(self._config, "speed") and self._config.speed != 1.0:
    self._log.debug(
        "rodd.tts.speed=%s is configured but has no effect — "
        "ChatterBox API does not expose a speed parameter (DATA_FLOW.md §4.6.1)",
        self._config.speed,
    )
```

The module docstring at lines 12–20 contains two explicit drift notes referencing `DATA_FLOW.md §4.6.1`. The anchor is present. The Architect's corrective pass on `LAYER_INTERFACES.md` has a cited code-side anchor.

`config_model.py:80–81` confirms `speed: float = 1.0` is stored in `RoddTtsConfig`.

**Verdict: VERIFIED.** Speed accepted in config, excluded from API body, debug log guards non-default values, drift annotation present.

---

### A-4 — Endpoint Paths

**Claim:** POST goes to `/v1/audio/speech`, GET to `/health` and `/v1/models`.

**Evidence:**
- `open()`: `url = f"{self._config.endpoint.rstrip('/')}/health"` (line 319)
- `health()`: same pattern (line 364)
- `list_models()`: `url = f"{self._config.endpoint.rstrip('/')}/v1/models"` (line 388)
- `synthesize()`: `url = f"{self._config.endpoint.rstrip('/')}/v1/audio/speech"` (line 466)

All four paths match the live contract. Trailing-slash stripping is applied consistently.

**Verdict: VERIFIED.**

---

### A-5 — Error Response Mapping

**Claim:** Each error response maps to the correct exception class.

**Evidence:** `chatterbox.py:286–305` (`_map_http_error`):
- 401, 403 → `ChatterboxAuthError` (line 297)
- any other status → `ChatterboxApiError` with `status_code` and `detail` (line 301)

Direct exception catches:
- `httpx.ConnectError` → `ChatterboxConnectionError` (line 324, 370, 399, 478)
- `httpx.TimeoutException` → `ChatterboxTimeoutError` (line 331, 373, 401, 481)
- Non-WAV `Content-Type` on 200 → `ChatterboxApiError` (line 492)

Test coverage: `test_synthesize_raises_auth_error_on_401` (line 347), `test_synthesize_raises_api_error_on_500` (line 358), `test_synthesize_raises_timeout_error` (line 334), `test_synthesize_raises_connection_error_on_connect_error` (line 381), `test_synthesize_raises_api_error_on_wrong_content_type` (line 370).

Gap: HTTP 403 has no dedicated test — only 401 is tested. The code handles both via `status in (401, 403)`.

**Verdict: VERIFIED.** Minor coverage gap on 403 noted as X-3.

---

### A-6 — Sentence-Boundary Chunking

**Claim:** 80-char minimum respected; LAST boundary chosen; `flush()` ignores minimum.

**Evidence:** `tunga.py:191–212`:

```python
# Only attempt a boundary flush once we've built up enough text
if len(self._buffer) < self._config.chunk_min_chars:
    return

# Find the last sentence terminator in the accumulated buffer.
last_boundary_end = -1
for terminator in self._config.sentence_terminators:
    idx = self._buffer.rfind(terminator)   # rfind = LAST occurrence
    if idx != -1:
        candidate_end = idx + len(terminator)
        if candidate_end > last_boundary_end:
            last_boundary_end = candidate_end
```

`flush()` at line 222–235: calls `_speak_chunk(remaining)` directly with no `chunk_min_chars` check.

Test `test_feed_chunk_handles_multiple_terminators_in_one_delta` (line 161) feeds `"One sentence. Two sentence. Partial"` and asserts `tunga._buffer == "Partial"` — confirming the last-boundary policy: the chunk ends at "Two sentence. " not "One sentence. ".

Test `test_chunking_respects_min_chars_threshold` (line 428) with `chunk_min_chars=80` feeds `"Short. "` (7 chars) and asserts `synthesize.assert_not_called()`.

Test `test_flush_speaks_remaining_buffer` (line 266) with `chunk_min_chars=500` sets `tunga._buffer = "This is still in the buffer"` and confirms `synthesize.assert_called_once_with("This is still in the buffer")` — no length gate.

**Verdict: VERIFIED.** All three invariants confirmed.

---

### A-7 — Lifecycle Integration in CLI

**Claim:** Tunga lifecycle phases wire correctly to the ceremony lifecycle: open at TENGSL, feed_chunk during SAMRAEDUR, flush after each turn, close at SLOKNA.

**Evidence:** `cli.py` `_async_light`:
- Tunga instantiated at lines 103–129, conditional on `grunnr_tts.enabled` — this block runs after `lc.transition(TENGSL)` at line 97. `await tunga.open()` at line 124.
- `feed_chunk` called at line 180: inside the `async for chunk in client.send_message(messages)` streaming loop, during SAMRAEDUR state.
- `flush` called at line 193: after the streaming loop per turn, before appending to messages.
- `close` called at line 211: in the SLOKNA block, before `client.close()`.

All Tunga calls are wrapped in `try/except Exception` catching at lines 182, 195, 212 — exceptions are logged as WARNING and not re-raised.

**Verdict: VERIFIED.** Lifecycle integration matches the contract.

---

### A-8 — Fault Tolerance

**Claim:** ChatterBox unreachable at `open()` → `self._degraded = True`, no exception to lifecycle. 3-consecutive failures → degrade. Playback failure → log and continue.

**Evidence:** `tunga.py:131–163` — `open()` catches `ChatterboxError` and `Exception` both, sets `self._degraded = True`, logs WARNING.

`_speak_chunk:295–329` — synthesis failure increments `self._consecutive_failures`; at `>= _MAX_CONSECUTIVE_FAILURES` (3) sets `self._degraded = True`.

`_speak_chunk:336–354` — `PlaybackError` caught, logged as WARNING; consecutive_failures NOT incremented (correct — ChatterBox still reachable).

Test `test_tunga_degraded_when_client_open_raises_connection_error` (tunga.py line 97) confirms degraded state after open failure.

Test `test_feed_chunk_sets_degraded_on_synthesize_error` (line 200) loops exactly `_MAX_CONSECUTIVE_FAILURES` times and asserts `tunga.is_degraded is True`.

**Verdict: VERIFIED.**

---

### A-9 — Config Validation Timing

**Claim:** Config validation fires at construction (Kynding), not at synthesis (Samræður).

**Evidence:** `config_model.py:96–123` — `RoddTtsConfig.__post_init__()` validates all ranges at dataclass construction time and raises `TungaConfigError` immediately.

In `cli.py:112–119` the `RoddTtsConfig(...)` construction is inside a `try/except Exception` block (line 125) — `TungaConfigError` raised here is caught, logged, and Tunga set to `None`, ceremony continues text-only. This is Kynding.

**Verdict: VERIFIED.**

---

## Part 2 — Cross-Platform Playback (Section B)

---

### B-1 — SoundDeviceBackend.available() Edge Cases

**Evidence:** `playback.py:152–165`:
```python
def available(self) -> bool:
    try:
        import sounddevice as sd  # ImportError if not installed
        device_arg = None if self._config.device == "default" else self._config.device
        sd.query_devices(device=device_arg, kind="output")  # Exception if no device
        return True
    except Exception:
        return False
```

Both `ImportError` (no sounddevice) and any `Exception` from `sd.query_devices()` are caught by the bare `except Exception` block. Returns `False` on both failure modes.

Test coverage: `test_sounddevice_available_false_when_import_fails` (line 107) and `test_sounddevice_available_false_when_device_missing` (line 118).

**Verdict: VERIFIED.**

---

### B-2 — PlatformFallbackBackend Platform Coverage

**Evidence:** `playback.py:279–293` (`available()`): Windows uses `winsound` stdlib; macOS uses `shutil.which("afplay")`; Linux uses `shutil.which("aplay") or paplay or play`. Unknown platform returns `False`.

`play()` at line 295: writes temp file, calls `_play_via_native`, removes in `finally` block (lines 330–337).

`_play_via_native:339–366`: Windows uses `winsound.PlaySound`; macOS uses `subprocess.run(["afplay", ...], check=True)`; Linux delegates to `_play_linux`.

Each platform dispatch has its own graceful failure path — `subprocess.CalledProcessError` maps to `PlaybackError`.

Test coverage: all three platforms tested in `test_rodd_playback.py` lines 216–261.

**Verdict: VERIFIED.**

---

### B-3 — NullPlaybackBackend

**Evidence:** `playback.py:397–426`. `available()` always returns `False`. `play()` logs at DEBUG and returns. `close()` marks closed and logs.

Test: `test_null_backend_available_returns_false`, `test_null_backend_play_does_not_raise`, `test_null_backend_close_does_not_raise` — all pass.

**Verdict: VERIFIED.**

---

### B-4 — best_available() Factory Order

**Evidence:** `playback.py:63–96`:
1. `SoundDeviceBackend(config, logger)` constructed; `available()` called
2. If True → return SoundDeviceBackend
3. Else `PlatformFallbackBackend(config, logger)` constructed; `available()` called
4. If True → return PlatformFallbackBackend
5. Else → return NullPlaybackBackend with warning log

Order: SoundDevice → PlatformFallback → Null. Matches spec.

Tests: `test_best_available_returns_sounddevice_backend_when_importable`, `test_best_available_returns_fallback_when_sounddevice_unavailable`, `test_best_available_returns_null_when_no_backend_available`.

**Verdict: VERIFIED.**

---

## Part 3 — Fault Tolerance (Section C)

All four fault-tolerance claims are verified as part of §A-7 and §A-8 above. See those sections. Summary:

- **C-1** ChatterBox unreachable → `_degraded = True`, no raise — VERIFIED
- **C-2** 3-consecutive synthesis failures → degrade — VERIFIED
- **C-3** Playback failure → log + continue (no consecutive_failures increment) — VERIFIED
- **C-4** Config validation at Kynding — VERIFIED

---

## Part 4 — Drift Handling (Section D)

---

### D-1 — speed Drift Annotation

**Claim:** Comment in `chatterbox.py` references `DATA_FLOW.md §4.6.1`.

**Evidence:** Module docstring lines 12–20 contain two explicit drift notes with `DATA_FLOW.md §4.6.1` cited. `_build_request_body` docstring at line 236–239 repeats the citation. Debug log message at line 279 references `DATA_FLOW.md §4.6.1`.

**Verdict: VERIFIED.** The code-side anchor exists for the Architect's corrective LAYER_INTERFACES.md pass.

---

### D-2 — voice_id Semantics in INTERFACE.md

**Claim:** INTERFACE.md documents `voice` field as "WAV file path or 'default'."

**Evidence:** Grep for `"WAV file path|voice cloning"` in `INTERFACE.md` returns no results. The config key block at `INTERFACE.md:120` shows `voice_id: "default"` but no prose explains the WAV-path semantics. The `chatterbox.py` module docstring (line 17–20) does document this correctly:

> `voice_id` in the config is a WAV file PATH for voice cloning, not a string identifier. When voice_id is "default" or empty, the `voice` field is omitted from the request body.

The documentation of this semantic lives in the implementation module, not in the canonical interface document. Operators reading `INTERFACE.md` would not learn that `voice_id` is a WAV path.

**Finding:**

- **N-3 (NOTABLE):** `src/heretic/rodd/INTERFACE.md` config key block (line 120) shows `voice_id: "default"` with no prose explaining that non-"default" values are WAV file paths (>=5s for turbo) interpreted as voice cloning prompts. The semantic lives only in `chatterbox.py:17–20`. An operator setting `voice_id: "custom_voice"` (a string identifier) rather than a `.wav` path will silently cause ChatterBox to receive a non-path string as the `voice` field, resulting in a synthesis error. Resolution: add a note to INTERFACE.md §Config Keys explaining the WAV path contract.

---

## Part 5 — Code Quality (Section E)

---

### E-1 — No Absolute Paths

**Command:** `grep -rn "C:/Users|C:\\Users|/home/|/Users/" src/ tests/`

**Result:** No output. No absolute paths in source or tests.

**Verdict: VERIFIED.**

---

### E-2 — Hardcoded Settings

**Finding:**

- **X-1 (NIT):** `src/heretic/rodd/config_model.py:44`: `endpoint: str = "http://100.66.178.105:7851"`. This is the Pi's Tailscale IP as the default value in the `RoddTtsConfig` dataclass. The same IP appears in `INTERFACE.md:119`. This is a Pi-specific address and will not work for operators with a different Pi address who forget to configure the `rodd.tts.endpoint` field. The address is not hardcoded in logic — it is a default value in a dataclass — but it is non-portable as a default. A `localhost` or empty default forcing operator configuration would be safer. **NIT** severity because `heretic.yaml` overrides the default and the example YAML shows the field clearly.

---

### E-3 — max_tokens: 127000

**Evidence:** `src/heretic/grunnr/config.py:96`: `max_tokens: int = 127000`. Voice does not directly use max_tokens; it is a Bifröst concern. The Bifröst config default is unchanged.

**Verdict: VERIFIED.** Voice additions did not reduce max_tokens.

---

### E-4 — PEP 8 / Type Hints / No print() in Library

**Evidence:**
- `grep -rn "print(" src/heretic/rodd/` returns no output — no `print()` in library code.
- All public methods in `chatterbox.py`, `tunga.py`, `playback.py`, `config_model.py`, `errors.py` carry full type hints.
- Code is 4-space-indented throughout.
- `tunga.py:336` uses `asyncio.get_event_loop()` which is deprecated in Python 3.10+ in favor of `asyncio.get_running_loop()` (when a loop is running). Tested: in Python 3.11 inside a running loop, `asyncio.get_event_loop()` returns the running loop without DeprecationWarning when the loop was set explicitly. Still, `asyncio.get_running_loop()` is the PEP-correct call.

**Finding:**

- **N-1 (NOTABLE):** `src/heretic/rodd/tunga.py:336`: `loop = asyncio.get_event_loop()` should be `loop = asyncio.get_running_loop()`. The latter is the correct call inside a coroutine (always has a running loop at that point), is available from Python 3.7, raises `RuntimeError` if no loop runs (vs. silently creating a new one in Python 3.9), and is not deprecated. The current call works in Python 3.11 but is fragile if backported or if the coroutine is ever invoked outside `asyncio.run()`.

**Verdict: PASS with N-1 notation.**

---

### E-5 — No Emoji in Source

**Command:** `grep -rn "emoji|🎙|🔊|🎤|✅|❌|⚠|🌐" src/heretic/rodd/ tests/`

**Result:** No output.

**Verdict: VERIFIED.**

---

### E-6 — pyproject.toml [voice] Extra

**Evidence:** `pyproject.toml`:
```toml
voice = [
    "sounddevice>=0.4.6",
]
```

`sounddevice` is present. `numpy` is **absent**.

`playback.py:179`: `import numpy as np` — imported inside `SoundDeviceBackend.play()` at call time.

**Finding:**

- **S-2 (SERIOUS):** `pyproject.toml` `[voice]` extra declares `sounddevice>=0.4.6` but does not declare `numpy`. `SoundDeviceBackend.play()` imports `numpy` at line 179 inside the `play()` body. On a fresh `pip install heretic[voice]`, `numpy` is pulled as a transitive dependency of `sounddevice` on most platforms — but `sounddevice`'s own dependency declaration does not guarantee numpy across all platforms and future package versions. If `numpy` is not installed, the `play()` call raises `ImportError` which is caught as `PlaybackBackendUnavailableError` (line 182) — but only at play-time, not at `available()` check time. The `available()` check at line 152 does NOT import numpy; it only imports `sounddevice`. This means `available()` returns `True`, Tunga does NOT degrade, and the failure occurs mid-ceremony on the first audio chunk, instead of gracefully at Kynding. This violates the graceful-degradation invariant.

  Evidence of impact path:
  ```
  SoundDeviceBackend.available() -> imports sounddevice only -> returns True
  Tunga.__init__: playback.available() True -> _degraded = False
  First play(): import numpy -> ImportError -> PlaybackBackendUnavailableError
  Tunga._speak_chunk: PlaybackError caught -> log warning -> continue
  ```
  The ceremony continues text-only but the degraded-mode detection fires at runtime rather than at construction time, contradicting `INTERFACE.md §Invariants 5`: "sounddevice is an optional dependency. pip install heretic (without [voice]) must not fail due to a missing sounddevice import." The invariant is met but the related invariant — that `available()` is authoritative about play-time readiness — is not.

  Resolution required: either add `numpy` to the `[voice]` extra, or import numpy in `available()` as an additional availability check.

---

### E-7 — Tests Use Mocking Only

**Evidence:** All HTTP calls in `test_rodd_chatterbox.py` go through `_MockTransport` (inheriting `httpx.AsyncBaseTransport`) or `MagicMock` — no real network. Grep confirms no calls to live endpoints (100.66.178.105 or localhost:7851 without mock). All playback calls in `test_rodd_playback.py` use `patch.dict("sys.modules", {"sounddevice": mock_sd})` and `patch("subprocess.run")`.

**Verdict: VERIFIED.**

---

### E-8 — Forge's Noted Fragilities

Forge flagged two fragilities: numpy ImportError at play-time, and blocking-play in the default thread pool.

**numpy ImportError at play-time:** Addressed as S-2 above — SERIOUS.

**Blocking play in thread pool executor:** `tunga.py:338`: `await loop.run_in_executor(None, self._playback.play, wav_bytes)`. Using `None` = default thread pool. `sounddevice.play(blocking=True)` blocks the thread for the duration of audio. This is correct behavior for a thread pool executor — the point is to offload the blocking call from the asyncio event loop. The concern is that a long audio clip will occupy one thread-pool thread for its full duration. With `_speak_lock` guaranteeing only one synthesis + playback at a time, this is bounded: one thread occupied per ceremony at most. For the current CLI use-case (one turn at a time), this is acceptable.

**Verdict: NOTABLE** severity, documented as Forge acknowledged.

---

## Part 6 — SERIOUS Finding Detail: grunnr RoddTtsConfig Stub Gap (S-1)

---

### S-1 — Grunnr RoddTtsConfig Missing 10 Synthesis Fields

**Finding: SERIOUS**

**Location:** `src/heretic/grunnr/config.py:126–133`

**Evidence:**

The grunnr `RoddTtsConfig` stub:
```python
@dataclass
class RoddTtsConfig:
    enabled: bool = True
    engine: str = "chatterbox"
    endpoint: str = "http://100.66.178.105:7851"
    voice_id: str = "default"
    device: str = "default"
    speed: float = 1.0
```

The canonical rodd `RoddTtsConfig` in `src/heretic/rodd/config_model.py` has these additional fields:
`voice_prompt_path`, `model`, `language_id`, `exaggeration`, `cfg_weight`, `temperature`, `top_p`, `repetition_penalty`, `request_timeout_seconds`, `chunk_min_chars`, `sentence_terminators` — **11 fields absent from the grunnr stub**.

The `_merge_dict_into_dataclass` function in `config.py:356–366`:
```python
field_names = {f.name for f in dataclasses.fields(dc_instance)}
for key, value in raw.items():
    if key not in field_names:
        continue  # silently skip unknown keys
```

When `heretic.yaml` contains:
```yaml
rodd:
  tts:
    temperature: 0.5
    model: tts
    chunk_min_chars: 120
```

All three values are silently dropped because `temperature`, `model`, and `chunk_min_chars` are not fields of the grunnr `RoddTtsConfig`. The CLI bridge in `_async_light:112–119` copies only the 6 stub fields into the rodd `RoddTtsConfig`, using rodd-side defaults for everything else.

**Impact:** Operators cannot tune TTS synthesis quality or chunking behavior from `heretic.yaml`. The example config (`heretic.example.yaml`) likely documents these fields (not verified in this audit, but if it does, operators will be misled). The mismatch is silent — no warning log, no error.

**Resolution required:** Expand grunnr `RoddTtsConfig` to include all fields declared in rodd `config_model.RoddTtsConfig`, OR have the CLI bridge use the rodd `config_model` directly for the full set of YAML values. The dual-dataclass pattern is the same drift risk flagged in `AUDIT_v0.1_FIRST_COMMUNION.md N-3`.

---

## Part 7 — Notable Findings Detail (Section N)

---

### N-2 — language_id Silently Excluded for "en"

**Finding: NOTABLE**

**Location:** `src/heretic/rodd/chatterbox.py:254–257`

```python
effective_language = language_id if language_id is not None else self._config.language_id
if effective_language and effective_language != "en":
    body["language_id"] = effective_language
```

The `language_id` is excluded from the request body when it equals `"en"`. The comment states "only meaningful for the multilingual model." This is a reasonable optimization — ChatterBox's default is English and sending `language_id: "en"` to the `turbo` or `tts` models is a no-op.

However, there is no test covering the case where an operator uses the `multilingual` model and sets `language_id: "de"` to verify the field is included. More subtly: if an operator sets `language_id: "en"` explicitly in the YAML and expects the field in the body for debugging purposes, it will be absent. The `"en"` exclusion is undocumented in `INTERFACE.md`.

**No resolution required** to unblock v0.2 (English is the only use-case in v0.2), but the exclusion logic should be documented in `INTERFACE.md §Config Keys` and a test for the non-"en" inclusion path added.

---

## Part 8 — Tests (Section F)

---

### F-1 — Test Run Result

**Command:** `py -3.11 -m pytest tests/ -v 2>&1 | tail -60`

**Result:**
```
============================= 221 passed in 1.40s =============================
```

221 passing, 0 failures, 0 skips. Forge's claim is correct.

**Verdict: VERIFIED.**

---

### F-2 — Smoke Tests

**Commands and results:**
```
py -3.11 -m heretic version    → 0.1.0.dev0
py -3.11 -m heretic --help     → Full help text printed, all 4 commands present
py -3.11 -m heretic status     → Reports HVILD, Config OK: False,
                                  Config error: "Cannot find heretic.yaml.
                                  Searched: C:\Users\volma\heretic.yaml
                                  Create a config file or set the $HERETIC_CONFIG
                                  environment variable. See heretic.example.yaml
                                  for the full config reference."
```

The `status` error is clear and actionable. CLI exits 0 for all three commands.

**Verdict: VERIFIED.**

---

### F-3 — Per-Test-File Counts

| File | Expected | Actual |
|---|---|---|
| test_rodd_chatterbox.py | 22 | 22 |
| test_rodd_playback.py | 21 | 21 |
| test_rodd_tunga.py | 30 | 30 |
| test_rodd_config.py | 16 | 16 |
| test_rodd_errors.py | 9 | 9 |
| test_cli_voice.py | 3 | 3 |
| **Total new** | **~101** | **101** |

All counts match Forge's stated targets exactly.

**Spot-check: 3-consecutive-failure degradation test** (`test_feed_chunk_sets_degraded_on_synthesize_error`, `test_rodd_tunga.py:200–221`):
- Configures `client.synthesize` to raise `ChatterboxConnectionError("gone")`
- Loops up to `_MAX_CONSECUTIVE_FAILURES` times calling `feed_chunk` with a triggering chunk (`"A failing sentence. "`, 21 chars, min_chars=5)
- After the loop asserts `tunga.is_degraded is True`
- Quality assessment: **genuine assertion** — it tests the actual public invariant, not a mock call count. The loop correctly breaks early if degraded mid-loop. This test would catch a regression where the counter threshold was raised or the degradation logic was removed.

**Spot-check: LAST-boundary chunking test** (`test_feed_chunk_handles_multiple_terminators_in_one_delta`, `test_rodd_tunga.py:161–172`):
- Feeds `"One sentence. Two sentence. Partial"` (35 chars, min_chars=5)
- Asserts `tunga._buffer == "Partial"` and `client.synthesize.assert_called_once()`
- Quality assessment: **genuine boundary assertion** — checks the buffer state after the call, which directly proves the last-boundary algorithm. If the implementation used `find()` instead of `rfind()`, the buffer would contain `"Two sentence. Partial"` and this test would fail.

**Spot-check: ChatterBox-unreachable graceful degradation test** (`test_tunga_degraded_when_client_open_raises_connection_error`, `test_rodd_tunga.py:97–100`):
- Builds Tunga with `open_raises=ChatterboxConnectionError("unreachable")`
- Asserts `tunga.is_degraded is True` after `await tunga.open()`
- Quality assessment: **correct** — tests the actual public invariant and the actual error type. Would catch a regression where `ChatterboxError` catch was narrowed or removed.

All three spot-checked tests assert on real invariants, not tautological shapes.

**Verdict: VERIFIED.**

---

## Part 9 — Drift Backlog (Section G)

---

### G-1 — LAYER_INTERFACES.md §L2 Rödd Cleanup Queue

**Status:** Deferred — not a blocker.

`docs/architecture/LAYER_INTERFACES.md:191–197` still shows the pre-probe `tts:` block:
```yaml
  tts:
    enabled: true
    engine: chatterbox
    endpoint: "http://100.66.178.105:7851"
    voice_id: "default"
    device: default
    speed: 1.0
```

This block is a 6-field stub that predates the live ChatterBox probe. It does not reflect the full synthesis parameter set (`model`, `temperature`, `exaggeration`, etc.), and retains `speed: 1.0` which the probe established has no API support. The code-side anchor in `chatterbox.py:236–239` references `DATA_FLOW.md §4.6.1` as the correction target.

This cleanup belongs to the Architect's corrective pass in a future wave. It is documented and anchored. Not a blocker for v0.2 development. Architect should update `LAYER_INTERFACES.md §L2` to reflect the full `RoddTtsConfig` schema and remove or annotate `speed: 1.0`.

---

## Part 10 — Finding Summary

### SERIOUS

| ID | Location | Evidence | Resolution |
|---|---|---|---|
| S-1 | `src/heretic/grunnr/config.py:126–133` | grunnr RoddTtsConfig has 6 fields; rodd RoddTtsConfig has 17. `_merge_dict_into_dataclass` silently drops 11 fields (model, temperature, exaggeration, cfg_weight, top_p, repetition_penalty, language_id, voice_prompt_path, chunk_min_chars, sentence_terminators, request_timeout_seconds) from heretic.yaml. CLI bridge copies only the 6 stub fields. | Expand grunnr RoddTtsConfig OR route YAML parsing directly through rodd config_model. |
| S-2 | `pyproject.toml` [voice] extra, `src/heretic/rodd/playback.py:179` | `numpy` imported at play-time but not declared in [voice]. `available()` imports only sounddevice — returns True even when numpy absent. First audio chunk raises ImportError→PlaybackBackendUnavailableError at runtime, not at Kynding. Violates the invariant that degradation is detected at construction. | Add `numpy>=1.21` to the [voice] extra, OR add a numpy import check inside `available()`. |

### NOTABLE

| ID | Location | Evidence | Resolution |
|---|---|---|---|
| N-1 | `src/heretic/rodd/tunga.py:336` | `asyncio.get_event_loop()` — deprecated in Python 3.10+; correct call inside coroutine is `asyncio.get_running_loop()` | Replace with `asyncio.get_running_loop()` |
| N-2 | `src/heretic/rodd/chatterbox.py:255` | `language_id` excluded from request body when value == "en" — logic is undocumented in INTERFACE.md, no test for non-"en" inclusion | Document in INTERFACE.md; add test for multilingual language_id inclusion |
| N-3 | `src/heretic/rodd/INTERFACE.md:120` | `voice_id: "default"` shown with no prose explaining WAV file path semantics for non-"default" values | Add prose to INTERFACE.md §Config Keys describing the WAV path contract |

### NIT

| ID | Location | Evidence | Resolution |
|---|---|---|---|
| X-1 | `src/heretic/rodd/config_model.py:44` | Pi Tailscale IP `http://100.66.178.105:7851` as hardcoded dataclass default — non-portable across Pi configurations | Consider an empty string default requiring explicit operator configuration |
| X-2 | `tests/test_cli_voice.py` | Only 3 tests; feed_chunk/flush call paths not exercised via CLI integration (only Tunga instantiation is verified) | Add CLI integration tests that exercise the actual feed_chunk→flush path through the turn loop |
| X-3 | `tests/test_rodd_chatterbox.py` | HTTP 403 not tested; only 401 is covered | Add `test_synthesize_raises_auth_error_on_403` |

### VERIFIED

A-1 (request fields), A-2 (voice field omission), A-3 (speed drift), A-4 (endpoint paths), A-5 (error mapping), A-6 (chunking), A-7 (lifecycle integration), A-8 (fault tolerance), A-9 (config validation timing), E-1 (no absolute paths), E-3 (max_tokens), E-4 (no print in library), E-5 (no emoji), E-7 (tests use mocking), F-1 (221 tests pass), F-2 (smoke tests), F-3 (per-file counts and quality), B-1, B-2, B-3, B-4.

---

## Releasability

**v0.2 as a development milestone: RELEASABLE WITH CONDITIONS.**

The two SERIOUS findings (S-1 and S-2) do not crash the ceremony — they silently limit operator configuration and cause a late degradation detection respectively. The body still speaks, the ceremony still runs. For an internal development milestone with known configuration, these are acceptable.

**v0.2 as a tagged release for operator use: NOT RECOMMENDED** until S-1 and S-2 are resolved. An operator who sets `temperature: 1.5` in their `heretic.yaml` to change voice expressiveness would receive silence on that configuration with no warning whatsoever.

---

*Auditor: Sólrún Hvítmynd — 2026-05-07*
*The body can speak. The claims mostly hold. Two gaps between what can be configured and what the system actually reads.*
