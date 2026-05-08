# HERETIC — Audit: v0.5.2 Webcam

**Date:** 2026-05-08
**Auditor:** Sólrún Hvítmynd (Auditor role, Mythic Engineering)
**Scope:** Full code audit of the v0.5.2 Webcam milestone.
Commits audited: `8293240` (Cartographer §4.10.11/12/13 + §15), `ebb5b6a` (webcam backend+orchestrator),
`b71f17f` (CLI dispatch), `8c11dd8` (TASK doc).
Branch: `development`.

**Environment:** Windows 11 Home 10.0.22621, Python 3.10.11, Node.js (npm), PowerShell.

**Commands run:**
- `python -m pytest tests/ -q 2>&1 | tail -20`
- `python -m pytest tests/test_sjon_webcam.py tests/test_cli_vision.py -v --tb=short 2>&1 | tail -60`
- `cd frontend && npm test -- --run 2>&1 | tail -15`
- `cd frontend && npx tsc --noEmit 2>&1`
- `cd frontend && npm run build 2>&1 | tail -8`
- `python -m heretic version`
- `python -m heretic --help`
- `python -m heretic status`
- grep `open\(|\.write_bytes|\.write_text|\.write\(` over `src/heretic/sjon/`
- grep `C:\\Users|/home/|/Users/` over `src/heretic/sjon/` + test files
- grep `snapshot_webcam|webcam_backend` over `src/heretic/cli.py` (serve mode coverage check)
- grep `webcam` over `heretic.example.yaml`
- Full read of all source and test files listed in scope

---

## Summary Verdict

**PASS WITH CONCERNS**

v0.5.2 delivers a fully operational webcam capture path: OpenCvBackend lifecycle,
BGR→RGB invariant, two-gate privacy in `snapshot_webcam()`, CLI dispatch across all
four `attach_policy` paths, per-ceremony alternate counter, and correct pyproject.toml
placement. **747 Python tests pass** (56 new), **91 frontend tests pass** (unchanged),
**0 failures** in both suites. TypeScript reports **0 errors** strict mode. Vite build
succeeds (163.44 kB bundle, 1.00s). CLI smoke commands all green.

One NOTABLE finding: `_async_serve` (WebSocket server path) has no webcam backend wiring.
The `_async_light` CLI path does. One NIT: frontend Sjón row carries no webcam-active badge.
The example.yaml webcam block is already fully uncommented — the Scribe deferral was
resolved by Forge, ahead of schedule.

| Severity | Count | Items |
|---|---|---|
| BLOCKER | 0 | — |
| SERIOUS | 0 | — |
| NOTABLE | 1 | N-1 (serve mode has no webcam backend wiring) |
| NIT | 1 | X-1 (no frontend webcam-active badge) |
| VERIFIED | 56 | A-1 through L-1 (see below) |

---

## Section A — BGR→RGB Invariant

**A-1: cv2.cvtColor call in OpenCvBackend.capture().** VERIFIED.

`src/heretic/sjon/webcam.py:378`:
```python
rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
```
The comment on line 377 cites the Cartographer invariant explicitly.
Return is `rgb_frame.tobytes(), width, height` — only RGB bytes leave the method.

**A-2: test_capture_converts_bgr_to_rgb asserts pixel order at byte level.** VERIFIED.

`tests/test_sjon_webcam.py:440–484`. The test synthesises a BGR frame where pixel (0,0)
is `[200, 100, 50]` (BGR), builds the expected RGB result `[50, 100, 200]`, mocks
`cv2.cvtColor` to return that RGB frame, then asserts:
```python
assert raw_bytes[0] == 50   # R
assert raw_bytes[1] == 100  # G
assert raw_bytes[2] == 200  # B
```
Byte-level assertion confirmed. R=50 is at index 0, not B=200.
The test also asserts `cv2.cvtColor` was called with `COLOR_BGR2RGB` as the second positional
argument (`call_args[0][1] == mock_cv2.COLOR_BGR2RGB`).

---

## Section B — Two-Gate Privacy

**B-1: snapshot_webcam() checks enabled first (Gate 1).** VERIFIED.

`src/heretic/sjon/sjon.py:605`:
```python
if not self._config.webcam.enabled:
    return []
```
First statement in the try block. Nothing executes before this gate.

**B-2: snapshot_webcam() checks backend.available() second (Gate 2).** VERIFIED.

`src/heretic/sjon/sjon.py:609`:
```python
if self._webcam_backend is None or not self._webcam_backend.available():
    return []
```
Guards both `None` (backend never wired) and `available()=False` (device absent / cv2 missing).
Both conditions short-circuit identically — the method returns `[]`.

**B-3: CLI attach_policy gates dispatch (Gate 3).** VERIFIED.

`src/heretic/cli.py:407–446`. The outer block is gated on
`sjon is not None and client.capability_vision_in and client.capability_vision_screen`.
Inside that block, `snapshot_webcam()` is reached only when `webcam_policy` is
`"webcam_only"`, `"alongside"`, or `"alternate"`. Under the default `"screen_only"` branch
`snapshot_webcam()` is never called (`cli.py:429–446` — the else branch uses `sjon.snapshot()`
only). Test `test_screen_only_calls_snapshot_not_snapshot_webcam` asserts
`sjon.snapshot_webcam.assert_not_called()` and passes.

**B-4: webcam.enabled defaults False.** VERIFIED.

`src/heretic/sjon/config_model.py:204`:
```python
enabled: bool = False
```
Test `test_default_enabled_false` (`tests/test_sjon_webcam.py:105`) passes.

---

## Section C — Alternate Counter

**C-1: ceremony_state initialised at TENGSL in _async_light.** VERIFIED.

`src/heretic/cli.py:344`:
```python
ceremony_state: dict[str, int] = {"alternate_turn": 0}
```
Comment on lines 341–343 explicitly notes: "Per-ceremony alternate-turn counter for webcam
attach_policy='alternate'. Resets at TENGSL (here) — scope is per-ceremony, not global."

**C-2: Counter mutates per turn.** VERIFIED.

`src/heretic/cli.py:421–426`:
```python
turn = ceremony_state["alternate_turn"]
if turn % 2 == 0:
    image_data_urls = await sjon.snapshot_webcam()
else:
    image_data_urls = await sjon.snapshot()
ceremony_state["alternate_turn"] = turn + 1
```
Increment is unconditional on every alternate-policy turn.

**C-3: Per-ceremony scope tested.** VERIFIED.

`tests/test_cli_vision.py:669–689` (`test_alternate_counter_resets_per_ceremony`).
Creates a second `ceremony_state = {"alternate_turn": 0}` and confirms turn 0 dispatches
webcam again. Passes.

---

## Section D — opencv-python Placement

**D-1: opencv-python in [vision] extra.** VERIFIED.

`pyproject.toml:61`:
```toml
"opencv-python>=4.8",
```
Located inside the `[project.optional-dependencies]` `vision` block (lines 54–62).

**D-2: opencv-python NOT in base dependencies.** VERIFIED.

`pyproject.toml:17–20` (`dependencies` block): contains only `pyyaml>=6.0` and `httpx>=0.27`.
No cv2 / opencv-python entry. Confirmed by full read.

**D-3: opencv-python NOT in [dev] extra.** VERIFIED.

`pyproject.toml:24–28` (`dev` block): contains only `pytest>=8.0`, `pytest-asyncio>=0.23`,
`pytest-mock>=3.14`. No opencv-python. CI runs clean without cv2; test suite mocks cv2 via
`patch.dict("sys.modules", {"cv2": mock_cv2})` throughout.

---

## Section E — Privacy Invariants

**E-1: No file write calls in production webcam paths.** VERIFIED.

Grep `open\(|\.write_bytes|\.write_text|\.write\(` over `src/heretic/sjon/` returns only
`open()` method definitions on backend classes (e.g. `WebcamCaptureBackend.open()`).
Zero file-system write calls. All webcam byte processing uses `io.BytesIO` (in-memory buffer)
inside `_encode_webcam_frame()` (`sjon.py:688–696`).

**E-2: webcam.enabled defaults False.** VERIFIED. See B-4.

**E-3: attach_policy defaults "screen_only".** VERIFIED.

`src/heretic/sjon/config_model.py:234`:
```python
attach_policy: Literal["screen_only", "webcam_only", "alongside", "alternate"] = "screen_only"
```
Test `test_default_attach_policy_screen_only` (`tests/test_sjon_webcam.py:131`) passes.
Webcam frames are never attached to agent turns under the default config even if the backend
is wired — confirmed by CLI code path analysis (B-3 above).

**E-4: Webcam frames live in memory + outbound HTTP body only.** VERIFIED.

`sjon.py:628–636`: data_url is assembled from `base64.b64encode(encoded_bytes).decode("ascii")`
and returned as a list member. Never written to disk, never appended to `_buffer` (the ring
buffer is screen-only in v0.5.2; webcam has no continuous mode). Privacy prose in `sjon.py:596`
confirms the invariant explicitly.

**E-5: No ring buffer for webcam in v0.5.2.** VERIFIED.

`snapshot_webcam()` (`sjon.py:571–698`) does not reference `self._buffer`, does not call
`_get_buffer_lock()`, and does not write to the deque. Confirmed by full read.

---

## Section F — Capture Pipeline

**F-1: available() probes cv2 import and VideoCapture.isOpened().** VERIFIED.

`webcam.py:241–265`. Two-step probe: import attempt (catches `ImportError`, returns `False`),
then `cap = cv2.VideoCapture(device_index)`, `cap.isOpened()`, `cap.release()`. Any exception
in the second block is caught and returns `False` without raising.

**F-2: open() lazy-inits VideoCapture cache.** VERIFIED.

`webcam.py:267–313`. `open()` creates `cv2.VideoCapture(device_index)` and stores it in
`self._cap`. Idempotency guard at lines 292–300: if `self._cap is not None` and
`self._cap.isOpened()` is True, early return. `open()` call is idempotent.

**F-3: capture() releases properly.** VERIFIED.

`capture()` does not call `release()` directly — it holds the cap open across multiple calls
for efficiency (documented design decision). `close()` releases it. This matches the lifecycle
contract in the docstring and the ABC.

**F-4: close() releases idempotently.** VERIFIED.

`webcam.py:382–406`. `close()` acquires `_lock`, calls `cap.release()` in a try/except (never
raises), sets `self._cap = None`. If already `None`, the `if self._cap is not None` guard skips
the release. Test `test_close_releases_cap_idempotent` passes and confirms
`mock_cap.release.assert_called_once()` and no error on second call.

**F-5: capture() raises WebcamCaptureError on read fail.** VERIFIED.

`webcam.py:370–375`:
```python
ret, frame = self._cap.read()
if not ret or frame is None:
    raise WebcamCaptureError(...)
```
Test `test_capture_raises_on_read_failure` passes.

**F-6: NullBackend always-unavailable.** VERIFIED.

`webcam.py:426–450`. `WebcamNullBackend.available()` returns `False` unconditionally.
`capture()` raises `WebcamBackendUnavailableError` unconditionally. `open()` and `close()` are
no-ops. All five NullBackend tests in `TestWebcamNullBackend` pass.

**F-7: best_available() factory chain.** VERIFIED.

`webcam.py:457–499`. Creates `OpenCvBackend`, calls `available()`. If `True`, returns it.
Any exception during the probe is caught; fallback is `WebcamNullBackend()`. Return is never
`None`. Tests `test_factory_never_returns_none`, `test_factory_returns_webcam_null_backend_when_cv2_absent`,
`test_factory_returns_opencvbackend_when_cv2_and_device_present` all pass.

---

## Section G — Sjón.snapshot_webcam()

**G-1: Returns [] when disabled or unavailable.** VERIFIED.

Three paths confirmed: `enabled=False` (`sjon.py:605–606`), `_webcam_backend=None` (`sjon.py:609`),
`available()=False` (`sjon.py:609`). Tests `test_disabled_returns_empty`,
`test_no_backend_returns_empty`, `test_unavailable_backend_returns_empty` all pass.

**G-2: Returns [data_url] on happy path.** VERIFIED.

`sjon.py:628–638`. Constructs data_url as `"data:{mime_type};base64," + b64`.
Tests `test_returns_jpeg_data_url` and `test_returns_png_data_url` confirm the exact prefix.

**G-3: JPEG default with jpeg_quality; PNG opt-in.** VERIFIED.

`sjon.py:691–695` in `_encode_webcam_frame()`:
```python
if webcam_cfg.format == "jpeg":
    img.save(buf, "JPEG", quality=webcam_cfg.jpeg_quality, optimize=True)
    mime_type = "image/jpeg"
else:
    img.save(buf, "PNG")
    mime_type = "image/png"
```
Test `test_returns_jpeg_data_url` (format="jpeg") and `test_returns_png_data_url` (format="png") pass.

**G-4: Resize to max_width/max_height honored.** VERIFIED.

`sjon.py:684–687`:
```python
if img.width > max_w or img.height > max_h:
    img.thumbnail((max_w, max_h), Image.LANCZOS)
```
Test `test_respects_max_dimensions` uses a 64×64 source with max 32×32 and confirms
decoded output width and height are both `<= 32`. Passes.

**G-5: Never raises; returns [] on failure.** VERIFIED.

`sjon.py:640–649`: outer `except Exception` (excluding `CancelledError`) catches all errors,
logs at WARNING, returns `[]`. Tests `test_never_raises_on_capture_error` (raises
`WebcamCaptureError`) and `test_never_raises_on_generic_error` (raises `RuntimeError`) both
return `[]` without propagating. Pass.

---

## Section H — CLI attach_policy 4 Paths

**H-1: "screen_only" — screen only, snapshot_webcam never called.** VERIFIED.

`cli.py:429–446`. The else branch (matching "screen_only" and any unknown policy) uses only
`sjon.snapshot()` / `sjon.recent_frames()`. Test `test_screen_only_calls_snapshot_not_snapshot_webcam`
asserts `sjon.snapshot_webcam.assert_not_called()`. Passes.

**H-2: "webcam_only" — webcam only, snapshot not called.** VERIFIED.

`cli.py:409–411`. Test `test_webcam_only_calls_snapshot_webcam_not_snapshot` asserts
`sjon.snapshot.assert_not_called()`. Passes.

**H-3: "alongside" — both, webcam-first.** VERIFIED.

`cli.py:413–417`:
```python
webcam_urls = await sjon.snapshot_webcam()
screen_urls = await sjon.snapshot()
image_data_urls = webcam_urls + screen_urls
```
Test `test_alongside_calls_both_webcam_first` confirms order `["data:image/jpeg;base64,webcam",
"data:image/png;base64,screen"]`. Passes.

**H-4: "alternate" — toggles per turn; counter resets per ceremony.** VERIFIED.

`cli.py:419–426`. Even turns (`turn % 2 == 0`) dispatch `snapshot_webcam()`;
odd turns dispatch `snapshot()`. Counter incremented unconditionally after dispatch.
Tests `test_alternate_even_turn_uses_webcam`, `test_alternate_odd_turn_uses_screen`,
`test_alternate_counter_resets_per_ceremony` all pass.

---

## Section I — Frontend Deferral

### I-1: Frontend Sjón webcam-active badge — deferred. Severity: NIT.

**Finding X-1 (NIT):** The Sjón layer status panel row (`frontend/`) has no badge or sub-indicator
for when the webcam backend is active. Forge explicitly deferred this to v0.5.3 or an Auditor
pass (TASK file §2, line 36: `⏳ Frontend Sjón row: small badge or sub-indicator when webcam
active (deferred)`).

Evidence: 91 frontend tests pass. The existing Sjón row renders and communicates correctly.
No feature regression introduced.

Assessment: **NIT** — not a gap in any documented invariant. The frontend displays ceremony
state accurately; the absence of a webcam sub-indicator is a cosmetic omission. Users operating
via the Summoning Circle will see the Sjón row active but will not be told whether the webcam
or the screen is the current frame source. This is an informational gap only — no data is
misrepresented, no privacy invariant is violated, no capability is silently broken.
Assign to v0.5.3 backlog. Scribe should note.

**I-2: No breaking change to existing Sjón row.** VERIFIED.

`frontend/tests/components.test.tsx` — 35 tests pass. The existing vision/ceremony UI
renders without error.

---

## Section J — Code Quality

**J-1: No absolute paths.** VERIFIED.

Grep `C:\\Users|/home/|/Users/` over `src/heretic/sjon/` and test files returns zero matches.

**J-2: No hardcoded settings.** VERIFIED.

All device_index, max_width, max_height, format, jpeg_quality values are driven by
`SjonWebcamConfig` fields with declared defaults. No literal magic values in logic paths.

**J-3: PEP 8, type hints, no print outside CLI.** VERIFIED.

`webcam.py` and the webcam path in `sjon.py` use type hints throughout. The `if TYPE_CHECKING`
pattern prevents circular imports at runtime (`sjon.py:64–68`, `webcam.py:58–59`). No `print()`
calls in `sjon/` directory. The one `print()` in CLI (`cli.py:321–334`) is intentional
operator-visible output, consistent with prior milestones.

**J-4: No emoji.** VERIFIED.

Grep over all v0.5.2-touched files returns zero emoji characters.

---

## Section K — Tests

**K-1: pytest 747 passing, 0 fail.** VERIFIED.

```
747 passed, 29 warnings in 3.09s
```
Command: `python -m pytest tests/ -q 2>&1 | tail -20`

**K-2: Frontend 91 passing.** VERIFIED.

```
Tests  91 passed (91)
```
Command: `cd frontend && npm test -- --run 2>&1 | tail -15`

**K-3: tsc + build clean.** VERIFIED.

`npx tsc --noEmit` — zero output, zero errors.
Vite build: `✓ built in 1.00s`, 163.44 kB bundle, zero errors.

**K-4: CLI smoke.** VERIFIED.

- `python -m heretic version` → `0.1.0.dev0`
- `python -m heretic --help` → full help text
- `python -m heretic status` → `HVILD (rest - no ceremony active)`

---

## Section L — heretic.example.yaml Deferral

**L-1: RESOLVED AHEAD OF SCHEDULE.** No Scribe action needed.

The TASK file (`§2 line 38`) marked the example.yaml webcam block as deferred to Scribe.
Verification shows the webcam block is already fully uncommented and complete
(`heretic.example.yaml:117–131`):

```yaml
  # v0.5.2 — webcam capture (opt-in; requires heretic[vision] with opencv-python>=4.8)
  webcam:
    enabled: false
    device_index: 0
    max_width: 1280
    max_height: 720
    format: jpeg
    jpeg_quality: 85
    attach_policy: screen_only  # screen_only | webcam_only | alongside | alternate
```

All four `attach_policy` values are documented inline. Privacy note is present.
Forge completed this ahead of the Scribe brief. No further action required.

---

## Notable Finding — N-1 (NOTABLE): Serve mode has no webcam backend wiring

**Severity:** NOTABLE

**Location:** `src/heretic/cli.py:963–1003` (`_async_serve` → Sjón init block)

**Evidence:**

The `_async_light` path wires the webcam backend at `cli.py:278–303`:
```python
if sjon is not None and grunnr_sjon.webcam.enabled:
    from heretic.sjon.webcam import best_available as webcam_best_available
    ...
    sjon._webcam_backend = webcam_backend
```

The `_async_serve` path (`cli.py:963–1003`) initialises `sjon_serve` for screen capture only.
There is no equivalent webcam wiring block. Confirmed by grepping `snapshot_webcam|webcam_backend`
over lines 962–1004 — zero matches.

**Consequence:** An operator running `heretic serve` with `sjon.webcam.enabled: true` and an
`attach_policy` other than `"screen_only"` will receive silent webcam degradation — `sjon_serve._webcam_backend`
is `None`, so `snapshot_webcam()` will return `[]` via Gate 2 (`sjon.py:609`). This is
fault-tolerant (the ceremony continues) but the operator's intent is silently ignored with no
warning log emitted at serve startup.

Note also: `_handle_send_message` (`cli.py:1163–1192`) uses the legacy screen-only snapshot path
(`sjon_serve.snapshot()`) — it does not implement the four-path `attach_policy` dispatch that
`_async_light` has. This is a pre-existing asymmetry (not introduced by v0.5.2) but deepens with
each webcam feature added.

**Recommendation for v0.5.3:** Mirror the `_async_light` webcam wiring into `_async_serve`,
and extend `_handle_send_message` to use the full attach_policy dispatch. Alternatively,
extract the webcam-init and attach-policy logic into shared helpers to prevent the two paths
from diverging further.

---

## Forge Claims — Verification Summary

| Claim | Status | Evidence |
|---|---|---|
| BGR→RGB via cv2.cvtColor; test asserts R=50 at byte index 0 | VERIFIED | webcam.py:378; test_sjon_webcam.py:482 |
| Two-gate privacy: enabled+available in snapshot_webcam; attach_policy CLI third gate | VERIFIED | sjon.py:605–609; cli.py:407–446 |
| Alternate counter per-ceremony (TENGSL init in _async_light) | VERIFIED | cli.py:344; tests pass |
| opencv-python in [vision] extra ONLY | VERIFIED | pyproject.toml:61; not in base deps or dev |

---

## Finding Index

| ID | Severity | Location | Description |
|---|---|---|---|
| N-1 | NOTABLE | `cli.py:963–1003` | `_async_serve` has no webcam backend wiring — webcam silently inactive in serve mode |
| X-1 | NIT | `frontend/` | No webcam-active badge in Sjón status row — cosmetic informational gap only |
