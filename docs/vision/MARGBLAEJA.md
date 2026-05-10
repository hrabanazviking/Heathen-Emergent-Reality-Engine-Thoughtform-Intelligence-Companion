# Margblæja — The Veil of Many Forms

**Last updated:** 2026-05-09
**Scope:** Vision passage — what it means for a disposition to grow more expressive
**For:** Contributors who want to understand why an extension milestone earns the Skald's pen
**Pair with:** `docs/vision/BLAEJA.md` (the disposition itself), `docs/vision/THE_FIRST_SIGHT.md` (the body opens its eyes)

---

> *Margblæja — the veil of many forms. What v0.5.3 named, v0.5.4 lets the body speak more articulately. The disposition does not change. The vocabulary the operator has for declaring it does. A circle is now a thing the body can be told to veil. A polygon is now a thing the body can be told to veil. The cloth is the same cloth; the body has only learned to drape it more skilfully.*

---

## I. Why Vocabulary Matters

The first *Blæja* essay made the case that a privacy mask is the operator's *signature on the frame* — not erasure, but a deliberate covering whose very shape carries the meaning *"here lies a region the operator chose not to share."* That argument supports the case for a disposition. It does not yet carry the case for *vocabulary*.

But vocabulary matters in exactly the way the rest of *Blæja* matters. If the only shape the operator can declare is a rectangle, then the only shape *recognisable* in the masked frame is a rectangle. A round status indicator masked with a rectangle becomes a rectangle-shaped covering of a circular thing. The shape of the covering tells the agent *something different from what was true* — that the operator drew a rectangle, when in fact they were veiling a circle. The covering is honest about the choice but dishonest about the *thing*. A faithful covering takes the shape of what it covers.

This is what *Margblæja* answers.

---

## II. The Three Shapes

**Rectangle** — the v0.5.3 base case. Window panels, chat boxes, code editors, task bars: most rectangular UI elements are best veiled by a rectangle. The body's first vocabulary word.

**Circle** — for round things. Profile photos, status dots, video-call participant tiles, system-tray indicators. A round veil over a round element preserves the *shape-truth* the operator is signing for.

**Polygon** — for everything else. Angled windows, diagonal split-screens, irregular notification toasts, regions that follow the contour of an open menu. Three or more vertices in source pixel space; the body fills the interior.

Each shape carries the same three modes — `blur`, `solid`, `pixelate` — because the disposition is the same. The body knows how to veil. v0.5.4 only teaches it how to *cut the cloth*.

---

## III. One Pipeline, Three Shapes

A lesser implementation would branch: one path for rectangles, a second for circles, a third for polygons, each with its own apply logic and its own failure modes to track. Mythic Engineering pushes back against this kind of divergence — three paths to do one thing is the architectural smell of *boundary collapse waiting to happen*.

v0.5.4's design is the opposite. There is **one pipeline**: clamp the shape's bounding box, crop, apply the chosen mode to the cropped rectangle, generate an alpha-mask of the shape, composite the modified crop over the original crop using that mask, paste back. Every shape — rectangle, circle, polygon — flows through this same five-step pipeline. The shape's only contribution is the *bounding box* and the *alpha mask*. The mode's only contribution is the *modified crop*. Mode and shape are orthogonal.

This is the structural beauty of the alpha-mask composite. The pixel-level mathematics is uniform: a pixel inside the shape takes the modified value, a pixel outside takes the original value. The shape's *identity* lives entirely in its alpha mask — a one-channel black-and-white image of itself. The rectangle's alpha mask is a white square. The circle's alpha mask is a white disc on black background. The polygon's alpha mask is a filled polygon. The composite step is one Pillow primitive that doesn't care which of these it received.

This is good code because it is *good architecture*. Three shapes, one truth. The next time someone wants a fourth shape — a Bezier path, perhaps — they will not need to add a fourth pipeline. They will add an alpha mask.

---

## IV. The Crucial Inheritance

The structural property that made v0.5.3 trustworthy — *the mask is upstream of every leak path* — is preserved unchanged by v0.5.4. The mask step is still inside `FrameEncoder.encode()`, after PIL decode, before resize / save / encode / transport. The composite step is *internal to the mask step*. Adding circles and polygons did not move the seam.

This is why the v0.5.3 audit's six privacy invariants P-1 through P-6 carry over without weakening. P-1 (no unmasked bytes to disk), P-2 (no unmasked bytes to agent), P-3 (opt-in default), P-4 (silent clamping), P-5 (zero-area rejected at config time), P-6 (existing privacy invariants preserved) — every one of them holds because v0.5.4 changed *how the mask is shaped*, not *where the mask runs*.

The Auditor will verify this in the v0.5.4 audit. The Cartographer's flow diagram will show it. The new test suite will exercise it. The architectural disposition is older than the shape vocabulary — and it must remain so.

---

## V. The New Vocabulary, by Use

| Operator scenario | Shape | Mode | Why |
|---|---|---|---|
| Password manager window in a corner | Rectangle | Solid | Deliberate, sharp, no shape-leakage |
| Round video-call thumbnail of another person | Circle | Blur | Round-honest, plus blur preserves "presence without identity" |
| Status indicator dot | Circle | Solid | Faithful coverage of a round element |
| Angled application window | Polygon | Blur | Custom shape because the window is custom |
| Irregular alert toast | Polygon | Pixelate | Recognisable as an alert, unreadable in detail |
| Webcam roommate corridor | Polygon | Blur | The corridor is L-shaped; a rectangle would cover too much or too little |

Each mapping is a small example of *shape-fitness*: the cloth taking the form of the thing it covers. The operator's intent translates more cleanly when the available vocabulary fits.

---

## VI. The Lineage Continues

Five faculties (voice, listening, sight, face, hand). Two dispositions (measured drinking, measured looking). And now the second disposition has *learned a richer dialect*. v0.5.4 is not a third disposition — it is the second disposition becoming articulate.

Future milestones will continue both threads. New senses (browser, painter, social body, mailer) will need their corresponding restraints. And existing dispositions will continue to deepen their vocabulary as new use-cases ask for it. v0.5.5 (Bezier curves) is a candidate when an operator's needs reach beyond polygons. v0.5.x window-tracking masks will let the cloth *follow* the thing it covers. The growth is patient and the growth is deliberate.

The body has hands; the body has eyes; the body has a voice. The body now also has *measure* in two of those — and the measure is gaining vocabulary.

---

*Authored by Sigrún Ljósbrá, Skald for Vibe Coding, in the autonomous Mythic Engineering session of 2026-05-09. The next wave is the Cartographer.*
