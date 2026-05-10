# TASK — HERETIC v0.5.3 BLÆJA (Privacy Masks for Sjón)

> **Operational task resumption file** — per Volmarr's session-resume protocol.
>
> **Started: 2026-05-09** (immediately after v0.7.1 *Straumr á Leið* sealed at `117f063`)
>
> **Codename (proposed, Skald to seal):** *Blæja* — "the veil." A covering that does not erase what is beneath, but spares it from being seen.
>
> **Mythic Engineering mode:** AUTONOMOUS continuation. Volmarr asleep / hands-off; this is the second milestone of the autonomous session.

---

## 1. Task scope

Add a configurable **privacy mask** layer to L3 Sjón, applied to captured frames before they are encoded for transport to the agent.

The body has eyes; the operator has the right to **veil** specific regions of what those eyes record. Common cases: the operator's password manager window in a corner of the screen; a webcam frame's background showing a roommate; a chat window with sensitive correspondence. The agent never receives the unmasked bytes — the mask is applied inside `FrameEncoder.encode()`, after PIL decoding and before resize / save / transport. There is no codepath in which the unmasked frame leaves the encoder.

v0.5.3 ships **the rectangular mask** with three application modes:
1. `blur` — Gaussian blur of the region (default radius depends on region size)
2. `solid` — region filled with a solid colour (default: black)
3. `pixelate` — region downsampled then upsampled (retro pixelation effect)

Non-rectangular shapes (circle, polygon) are **out of scope** for v0.5.3 — they are v0.5.4+.

---

## 2. Current status — 2026-05-09

**Phase:** v0.5.3 **OPEN — wave plan published, no code written yet.**

**HEAD (development):** `117f063` (v0.7.1 Scribe seal — parent of upcoming Wave 0 commit)

**Test count baseline (before this milestone):** Leið scope 50/50 + Sjón scope ~134 (test_sjon_orchestrator + test_sjon_encoder + test_sjon_capture + test_sjon_webcam) on full-extras host. Broader Python suite expected 1239 passing on full-extras host.

### v0.5.3 deliverables — pending

- ☐ Skald — `docs/vision/BLAEJA.md` — the body learns to look without recording all it sees
- ☐ Cartographer — `docs/cartography/DATA_FLOW.md` Sjón sub-section addendum: where mask application sits in the pipeline, coordinate space, ordering vs resize
- ☐ Architect — `PrivacyMaskRegion` dataclass; new `privacy_masks: list[PrivacyMaskRegion]` field on `SjonScreenConfig` and `SjonWebcamConfig` (both default `[]`); INTERFACE / LAYER docs updated
- ☐ Forge — `encoder.py` mask application after PIL decode and before resize; `config_model.py` field additions + validation; tests (8+)
- ☐ Auditor — `docs/audit/AUDIT_v0.5.3_BLAEJA.md` — verifies mask precedes any save/transport path; verifies blur radius actually obscures; verifies opt-in default
- ☐ Scribe — DEVLOG entry 16; TASK seal; memory refresh

### What v0.5.3 does NOT add

- Non-rectangular shapes (circle, polygon, freeform) — v0.5.4+
- Mask-region "follow-the-window" tracking (a mask that follows a moving window) — v0.6+ would need OS-level window position events
- Per-monitor mask sets (the same mask list applies regardless of which monitor is captured in v0.5.3)
- Animated masks (a region whose mask drifts each frame) — out of scope
- Frontend mask-region picker UI — operator edits `heretic.yaml` directly in v0.5.3

---

## 3. Architectural decisions (Architect to confirm at Wave 3)

| Decision | Choice | Rationale |
|---|---|---|
| Mask region shape | Rectangle: `(x, y, w, h)` in source pixel coordinates | Simplest geometry; matches operator's existing mental model (pixel ruler / screenshot tools); covers the dominant use case (windows, panels) |
| Coordinate space | **Source pixels** (before resize) | Operators identify regions on the actual screen; resize ratio would force them to recalculate after every `max_width` change |
| Application order | After PIL decode → before resize → before save → before encode | Mask must precede everything that could leak the unmasked bytes; resize comes after because mask coordinates are in source space |
| Out-of-bounds regions | Clamped to image bounds; silently. Region wholly off-frame becomes a no-op | Robust to operator typos and resolution changes. A no-op region is logged at `debug` level once per encoder lifetime |
| Modes | `blur` (default), `solid`, `pixelate` | Three covers the dominant privacy use cases. Each has a clear visual signature so the agent + operator can identify a mask region easily |
| Blur radius | `radius = max(8, min(w, h) // 8)` | Auto-scales: larger regions get larger blur; minimum 8px ensures meaningful obscuration. Manual override via `PrivacyMaskRegion.blur_radius` |
| Solid colour | RGB tuple `(0, 0, 0)` (black) by default; configurable via `PrivacyMaskRegion.solid_color` | Black is the most common and safest privacy-mask convention |
| Pixelate factor | `factor = max(8, min(w, h) // 12)` | Auto-scales similarly. Manual override via `PrivacyMaskRegion.pixelate_factor` |
| Empty list semantics | `privacy_masks: []` (default) → no masks applied; encoder fast-path skips the mask step entirely | Zero overhead when feature is unused |
| Per-source masking | `SjonScreenConfig.privacy_masks` and `SjonWebcamConfig.privacy_masks` are **independent lists** | Screen and webcam have different privacy concerns; symmetry is wrong here |
| Validation | At config construction: x, y >= 0; w, h >= 1; mode in {blur, solid, pixelate}; solid_color is a 3-tuple of ints in [0, 255]; blur_radius >= 1; pixelate_factor >= 2 | Fail loudly at startup, never silently at first frame |
| Class location | New file `src/heretic/sjon/privacy.py` — single module owns the dataclass + apply function | Keeps `config_model.py` slim; gives the apply function its own home for testing |
| Public surface | `apply_privacy_masks(image, masks) -> image` (returns the same PIL.Image, modified in place) | Pure function — no encoder coupling — easy to test; encoder just calls it |

---

## 4. Privacy invariants (cross-checked by Auditor)

These are the non-negotiable rules that v0.5.3 must preserve and (in some cases) extend:

| # | Invariant | Source |
|---|-----------|--------|
| P-1 | Unmasked frame bytes never reach disk if any privacy mask is configured. The mask runs before every save/transport path. | NEW (v0.5.3) |
| P-2 | Unmasked frame bytes never reach the agent. The mask runs before encoding to PNG/JPEG. | NEW (v0.5.3) |
| P-3 | `privacy_masks` defaults to `[]` (empty) — feature is opt-in. | NEW (v0.5.3) |
| P-4 | Mask coordinates in source pixel space; clamping to bounds is silent except a one-time debug log per encoder lifetime. | NEW (v0.5.3) |
| P-5 | Mask region with `w == 0` or `h == 0` is rejected at config-construction time with `ValueError`. | NEW (v0.5.3) |
| P-6 | Existing Sjón privacy invariants preserved: `save_frames` defaults False; webcam `enabled` defaults False; in-memory ring buffer only; `buffer.clear()` on Slokna. | v0.5+ (carried) |

---

## 5. Mask application sketch (for Cartographer + Forge)

```
  FRAME PIPELINE WITH PRIVACY MASKS

  raw_bytes (BGRA) from MssBackend / WebcamBackend
       │
       ▼
  PIL.Image.frombytes("RGB", ..., "raw", "BGRX")    # decode
       │
       ▼
  apply_privacy_masks(image, config.privacy_masks)  # ← NEW: v0.5.3 step
       │  for each region:
       │    clamp (x, y, w, h) to image bounds
       │    if effective area is 0:  log once, skip
       │    crop region → apply mode (blur / solid / pixelate)
       │    paste back at (x, y)
       │
       ▼
  resize_to_bounds(image, max_w, max_h)             # downscale
       │
       ▼
  buf.save(buf, format="PNG", compress_level=6)     # encode
       │
       ▼
  PNG bytes  →  base64 data URL  →  agent / disk (if save_frames)
```

The crucial property: **the mask step is upstream of every leak path**. A frame that has been through `apply_privacy_masks` is the only frame the rest of the pipeline ever sees.

---

## 6. Test plan — Forge writes; Auditor verifies

New tests in `tests/test_sjon_privacy.py` (new file):

| Test | Asserts |
|---|---|
| `test_blur_region_actually_obscures` | A blurred 100×100 region of a synthetic checkerboard image has lower per-pixel variance than the original — i.e., blur is real |
| `test_solid_region_is_solid_colour` | A 50×50 solid-mask region of a multi-colour image is all the same single colour after mask application |
| `test_pixelate_region_has_blocky_structure` | A pixelated region's distinct-colour count is much smaller than the original region's |
| `test_multi_region_all_applied` | Two distinct regions both get masked (verify by sampling pixels in each region) |
| `test_region_clamping_partially_off_frame` | A region with x+w > image_width is clamped; the visible part inside the image is masked correctly |
| `test_region_wholly_off_frame_is_noop` | A region entirely off-frame produces no error and no change |
| `test_empty_mask_list_is_noop` | `privacy_masks=[]` returns the image untouched (identity check) |
| `test_invalid_mode_raises_at_config_time` | `PrivacyMaskRegion(mode="invalid")` raises `ValueError` |
| `test_zero_width_region_raises_at_config_time` | `PrivacyMaskRegion(x=0,y=0,w=0,h=10)` raises `ValueError` |
| `test_negative_coordinates_raise_at_config_time` | `PrivacyMaskRegion(x=-1, ...)` raises `ValueError` |

Integration test in `tests/test_sjon_encoder.py` (extension):

| Test | Asserts |
|---|---|
| `test_encoder_applies_privacy_masks_before_resize` | A FrameEncoder configured with a mask produces PNG bytes whose decoded version has the masked region obscured at the corresponding (proportionally-translated) location after resize |

Existing Sjón tests must continue to pass without modification.

---

## 7. Mythic Engineering wave plan

### Wave 0 — TASK file (this commit)

### Wave 1 — Skald
- `docs/vision/BLAEJA.md` — what the veil means for a body that sees

### Wave 2 — Cartographer
- `docs/cartography/DATA_FLOW.md` — Sjón sub-section addendum on mask application step
- Memory: mask runs in the same step on screen and webcam pipelines (single function, two callers)

### Wave 3 — Architect
- `src/heretic/sjon/privacy.py` — `PrivacyMaskRegion` dataclass + `apply_privacy_masks` function signature only (no logic; logic is Forge's)
- `src/heretic/sjon/config_model.py` — add `privacy_masks: list[PrivacyMaskRegion]` to both `SjonScreenConfig` and `SjonWebcamConfig`
- `src/heretic/sjon/INTERFACE.md` — document the new field + behaviour

### Wave 4 — Forge
- `src/heretic/sjon/privacy.py` — implement the three modes (blur, solid, pixelate) + clamping + once-per-lifetime debug log
- `src/heretic/sjon/encoder.py` — call `apply_privacy_masks` after decode, before resize
- `tests/test_sjon_privacy.py` — new file with 10+ tests
- `tests/test_sjon_encoder.py` — integration test extension

### Wave 5 — Auditor
- `docs/audit/AUDIT_v0.5.3_BLAEJA.md`
- Verify P-1 through P-6 hold in the post-Forge code

### Wave 6 — Forge cleanup (only if Wave 5 raises items)

### Wave 7 — Scribe
- DEVLOG entry 16
- TASK §2 sealed
- `project_heretic_status.md` updated; `MEMORY.md` quick-facts refreshed

---

## 8. Forbidden moves

- ☒ Do **not** make `privacy_masks` a config flag like `privacy_masks.enabled: bool`. The list IS the toggle — empty list means off.
- ☒ Do **not** apply masks in source-resolution coordinates AFTER resize. Source coordinates are only meaningful before resize.
- ☒ Do **not** silently drop an invalid mode or out-of-range region at runtime. Fail at config-construction time.
- ☒ Do **not** introduce a new dependency. Pillow is already present.
- ☒ Do **not** touch the existing privacy invariants (`save_frames`, webcam `enabled` defaults). The new invariants are additive.
- ☒ Do **not** alter the public encoder return shape or the `encode_to_data_url` signature (additive change inside `encode()` only).

---

## 9. Backlog forward (post-v0.5.3)

| Item | Requires | Notes |
|---|---|---|
| v0.5.4 non-rectangular masks | Pillow ImageDraw paths | Circle + polygon mask shapes |
| v0.5.x window-tracking masks | OS window enumeration | Mask follows a named window across moves |
| v0.5.x frontend mask picker UI | Frontend dev | Visual region selection in Eldahús |
| v0.5.3 webcam sub-badge | Frontend only | Carried X-1 NIT from v0.5.2 — still pending |
| v0.6.x.1 MCP resources | mcp_server.py extension | `resources/*` file hosting |
| v0.6.x Mode C Smiðja composition | No external gate | Multi-step Brúarhönd + Forge orchestration |
| **v0.8 Opið Vef** | Playwright | Full browser sense; subsumes httpx Leið |
| v0.9 Málari | Playwright (v0.8) | Photopea editor |
| v0.10 Langhúsið Ytra | OSC + MindSpark | VRChat embodiment |
| v0.11 Bréfasamtök | aiosmtplib + aioimaplib | Email |
| v0.4.1 first compile | MSVC Build Tools | Operator-blocked |

The natural successor in roadmap order is **v0.8 Opið Vef** — the full Playwright browser sense.

---

## 10. Session-resumption pointer

If this session is interrupted before Wave 7 closes, resume by:
1. Read this TASK file §2 for current phase
2. `git log --oneline -20` — identify which Wave commits exist
3. Continue from the first missing Wave

---

*Authored by Runa Gridweaver Freyjasdottir, in the autonomous Mythic Engineering mode requested by Volmarr 2026-05-09.*
*The next wave is the Skald.*
