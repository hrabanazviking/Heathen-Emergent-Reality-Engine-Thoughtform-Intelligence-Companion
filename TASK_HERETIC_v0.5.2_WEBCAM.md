# TASK — HERETIC v0.5.2 WEBCAM

> **Operational task resumption file** — per Volmarr's session-resume protocol.

> **Started: 2026-05-08** (immediately after v0.6 Hands at the Forge shipped + audited + cleaned at HEAD `1f91847`)

> **Mode: extension of v0.5.** No new faculty; activates the SjonWebcamConfig stub declared in v0.5. Slim wave plan: no Skald (no new vision essay).

---

## 1. Task scope

Activate the second sight source: the **webcam**.

v0.5 declared `SjonWebcamConfig` but did not implement it. v0.5.2 implements it: when `sjon.webcam.enabled: true`, Sjón captures a frame from the webcam device IN ADDITION TO or INSTEAD OF the screen, per `sjon.webcam.attach_policy` ("alongside" | "replace_screen" | "alternate" | "screen_only" — last for backward compat).

Privacy invariant carries: NEVER auto-save frames; default `webcam.enabled: false` (stronger consent gate than screen — webcam captures the user's physical presence).

What v0.5.2 does NOT add:
- Multi-webcam support (single device for v0.5.2; multi v0.5.x)
- Webcam ring buffer (v0.5.2 ships on-demand only, mirroring v0.5; periodic webcam is v0.5.x)
- Privacy mask regions (v0.5.3)
- Audio-from-webcam (Hlust handles audio capture separately)

---

## 2. Current status — 2026-05-08

**Phase:** v0.6 SHIPPED + AUDITED + CLEANED at `1f91847`. Test baseline: 691 Python + 91 frontend = 782.

### v0.5.2 deliverables
- ⏳ Activate `SjonWebcamConfig` (declared in v0.5; fields: enabled, device_index, max_width, max_height, format ["png"|"jpeg"], jpeg_quality, attach_policy)
- ⏳ `src/heretic/sjon/webcam.py` — WebcamCaptureBackend ABC + OpenCvBackend (cv2.VideoCapture) + NullBackend + best_available()
- ⏳ Sjón orchestrator extension: `snapshot_webcam()` returns webcam frame as data URL, mirroring `snapshot()` for screen
- ⏳ CLI dispatch — when both screen+webcam enabled: per attach_policy combine into image_data_urls list
- ⏳ Frontend Sjón row: small badge or sub-indicator when webcam active (no new layer row; Sjón still owns)
- ⏳ pyproject.toml — add `opencv-python>=4.8` to `[vision]` extra (heaviest dep so far; ~70MB; acceptable for opt-in)
- ⏳ heretic.example.yaml — uncomment + complete `webcam:` block
- ⏳ Tests — 20+ new Python tests; total target 711+ Python + 92+ frontend = 803+

### Privacy stance (stronger than screen)

- `enabled: false` default — operator must explicitly opt in
- No Slokna recording; no buffer for v0.5.2 (continuous webcam in v0.5.x)
- INTERFACE.md prose clearly notes physical-presence implications

---

## 3. Architectural decisions

| Decision | Choice | Rationale |
|---|---|---|
| Webcam library | `opencv-python` (cv2.VideoCapture) | Industry standard; cross-platform; well-tested |
| Encoding format | JPEG default (smaller); PNG opt-in | Webcam frames don't need lossless; JPEG ~5-10x smaller for vision API token cost |
| Capture mode | On-demand only for v0.5.2 | Mirror v0.5; periodic webcam is v0.5.x |
| Attach policy default | "screen_only" | Webcam off by default; explicit opt-in |
| Single device | `device_index: 0` (first available) | Multi-camera deferred to v0.5.x |
| Failure mode | Webcam unavailable → degrade silently; screen continues | Per RULES.AI fault tolerance |

---

## 4. Mythic Engineering wave plan (slim)

### Wave 1 — parallel
- **Cartographer**: Extend §4.10 with webcam subsection §4.10.11; update §15 component diagram with WebcamCaptureBackend; document the 4 attach_policy paths
- **Architect**: Activate SjonWebcamConfig + scaffold `src/heretic/sjon/webcam.py` (ABC + OpenCvBackend skeleton + NullBackend); extend `Sjón.snapshot_webcam()` stub; update INTERFACE.md; pyproject.toml `[vision]` extra adds opencv-python

### Wave 2
- **Forge**: Implement OpenCvBackend (cv2.VideoCapture lifecycle, lazy init, frame BGR→RGB→PIL→PNG/JPEG→base64); Sjón.snapshot_webcam(); CLI attach_policy dispatch (mirror screen attach_policy); frontend badge; 20+ tests
- **Auditor**: AUDIT_v0.5.2_WEBCAM.md; verify privacy invariant (no disk writes; webcam disabled by default); cv2 mock pattern; degradation paths

### Wave 3 — cleanup if needed

### Close-out
- **Scribe**: DEVLOG entry 10 + TASK update + memory refresh

---

## 5. Files to be created/extended

```
src/heretic/sjon/
  webcam.py                NEW — WebcamCaptureBackend ABC + OpenCvBackend + NullBackend + best_available
  config_model.py          extend — SjonWebcamConfig completed (was stub)
  sjon.py                  extend — snapshot_webcam(), webcam state attrs
  capture.py               minimal touch — keep MssBackend separate; webcam.py is parallel
  errors.py                extend — WebcamCaptureError, WebcamBackendUnavailableError
tests/
  test_sjon_webcam.py      NEW — 12+ tests
  test_sjon_orchestrator.py extend — webcam path tests
  test_cli_vision.py       extend — webcam attach_policy CLI tests
src/heretic/cli.py         extend — webcam dispatch in attach_policy logic
heretic.example.yaml       uncomment webcam: block
pyproject.toml             [vision] += opencv-python>=4.8
```

---

## 6. v0.5.2 exit criteria
- `heretic light` with `sjon.webcam.enabled: true` AND agent supporting `?vision_in` attaches webcam frame per attach_policy
- Privacy: webcam disabled by default; never persists to disk
- Configurable via heretic.yaml `sjon.webcam.*`
- Graceful degradation if cv2 unavailable or device missing
- Test count ≥711 Python; total ≥803
- Audit verdict PASS or PASS WITH CONCERNS, no blockers

---

## 7. Backlog forward
- v0.5.3 privacy masks (blur/mask configurable regions)
- v0.5.x periodic webcam (continuous mode + ring buffer) — mirrors v0.5.1 for screen
- v0.5.x multi-camera support
- v0.6.1 Forge dispatch (next milestone)
- v0.6.2 more senses
- v0.6.x native MCP server hosting
- v0.7 Mímisbrunnr starter pack
- v0.4.1 first compile (awaits operator linker install)

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-08.*
*v0.5.2 — when the eye learns to look at faces.*
