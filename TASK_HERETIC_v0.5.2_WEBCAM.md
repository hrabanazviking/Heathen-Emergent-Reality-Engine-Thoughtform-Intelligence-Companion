# TASK — HERETIC v0.5.2 WEBCAM

> **Operational task resumption file** — per Volmarr's session-resume protocol.

> **Started: 2026-05-08** (immediately after v0.6 Hands at the Forge shipped + audited + cleaned at HEAD `1f91847`)

> **Closed: 2026-05-08** — SHIPPED + AUDITED + CLEANED. HEAD: `f0089d6`. 750 Python + 91 frontend = 841 tests. 0 open findings.

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

**Phase:** COMPLETE — SHIPPED + AUDITED + CLEANED. HEAD: `f0089d6`. Test count: 750 Python + 91 frontend = 841.

### v0.5.2 deliverables
- DONE Activate `SjonWebcamConfig` (fields live and validated in config_model.py)
- DONE `src/heretic/sjon/webcam.py` — OpenCvBackend fully implemented: available()/open()/capture()/close() + BGR→RGB conversion + NullBackend + best_available() factory live
- DONE Sjón orchestrator: `snapshot_webcam()` + `_encode_webcam_frame()` implemented, fault-tolerant, never raises
- DONE CLI dispatch — webcam init at TENGSL + all 4 attach_policy paths (screen_only/webcam_only/alongside/alternate) + per-ceremony alternate counter + Slokna teardown
- DEFERRED-v0.5.3 Frontend Sjón row: small badge or sub-indicator when webcam active — X-1 NIT from audit; deferred to v0.5.3 backlog
- DONE pyproject.toml — `opencv-python>=4.8` in `[vision]` extra (confirmed present)
- DONE heretic.example.yaml — full webcam block uncommented (Forge completed ahead of Scribe brief at `ebb5b6a`)
- DONE Tests — 59 new Python tests (+37 webcam backend/orchestrator, +7 webcam CLI attach_policy, +3 serve-mode Wave 3 fixes, +12 remainder); 750 total (+59 from baseline 691)
- DONE Audit — PASS WITH CONCERNS; N-1 serve wiring RESOLVED at `f0089d6`; X-1 badge NIT DEFERRED; 56 items verified

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

## 4. Mythic Engineering wave plan (slim) — COMPLETE

### Wave 1 — DONE (`8293240`, `05bb030`)
- **Cartographer**: Extended §4.10 with webcam subsections §4.10.11–13; updated §15 component diagram with WebcamCaptureBackend; documented the 4 attach_policy paths
- **Architect**: Activated SjonWebcamConfig + scaffolded `src/heretic/sjon/webcam.py` (ABC + OpenCvBackend skeleton + NullBackend); extended `Sjón.snapshot_webcam()` stub; updated INTERFACE.md; pyproject.toml `[vision]` extra adds opencv-python

### Wave 2 — DONE (`ebb5b6a`, `b71f17f`, `8c11dd8`)
- **Forge**: Implemented OpenCvBackend (cv2.VideoCapture lifecycle, BGR→RGB, JPEG/PNG encode, base64); Sjón.snapshot_webcam(); CLI attach_policy dispatch; 44+ tests
- **Auditor**: AUDIT_v0.5.2_WEBCAM.md — PASS WITH CONCERNS; 56 verified; N-1 NOTABLE + X-1 NIT

### Wave 3 — DONE (`f0089d6`)
- **Forge**: Resolved N-1 — mirrored webcam wiring + attach_policy dispatch into `_async_serve`; 3 new serve-mode tests

### Close-out — DONE (this Scribe session)
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

| Item | Status | Notes |
|---|---|---|
| v0.5.3 frontend webcam sub-badge (X-1) | BACKLOG — named | Sjón row badge for active webcam source; cosmetic only |
| v0.5.3 privacy masks | BACKLOG | Blur/mask configurable regions before frame send |
| v0.5.x periodic webcam | BACKLOG | Continuous mode + ring buffer — mirrors v0.5.1 for screen |
| v0.5.x multi-camera | BACKLOG | `device_index > 0` coverage; multi-camera selection |
| v0.6.1 Forge dispatch | BACKLOG | Blender MCP via Seidr-Smidja Forge; Seidr-Smidja v0.2 gate |
| v0.6.2 more senses | BACKLOG | Filesystem, terminal, browser |
| v0.6.x native MCP server | BACKLOG | MCP SDK integration |
| v0.7 Mímisbrunnr | BACKLOG | First Drink at the Well |
| v0.4.1 first compile | PENDING — awaits linker | MSVC Build Tools or full MinGW-w64 |

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-08.*
*v0.5.2 — when the eye learns to look at faces.*
*Closed by Eirwyn Rúnblóm, 2026-05-08. The eye gained its second source. Record sealed.*
