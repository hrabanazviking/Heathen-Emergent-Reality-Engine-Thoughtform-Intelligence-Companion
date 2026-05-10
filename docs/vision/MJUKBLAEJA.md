# Mjúkblæja — The Soft Veil

**Last updated:** 2026-05-09
**Scope:** Vision passage — why the soft-curved shapes belong in the body's vocabulary
**For:** Contributors who wonder whether vocabulary growth is ever finished
**Pair with:** `docs/vision/MARGBLAEJA.md` (the veil's first vocabulary growth), `docs/vision/BLAEJA.md` (the disposition itself)

---

> *Mjúkblæja — the soft veil. The cloth that has learned to take soft shapes. The body has eyes; the body has the discipline of measured looking; the body knows how to declare that discipline in rectangles, circles, and polygons. v0.5.5 teaches it the curves the modern world is actually built from. Round corners. Pill buttons. Oval thumbnails. The body's hand on the shoulder, gently turning the gaze, can now follow the actual shape of what it is veiling — not just the closest sharp approximation.*

---

## I. The World Is Not Sharp

Look at any contemporary user interface. The chat window has rounded corners. The button has a pill shape. The avatar thumbnail is an oval, not a square. The notification toast has soft edges. The IDE's code-completion popup has corner radii to match the system's design language. The browser tab is a rounded trapezoid. The video-call participant tile is a rounded rectangle, sometimes with a circular avatar inset.

A privacy mask vocabulary that contains only sharp rectangles, perfect circles, and angular polygons is a vocabulary built for a world that does not exist anymore. Sharp shapes still happen — old text terminals, certain CAD tools, code editors with corner styling disabled — but they are the minority. The dominant case is a soft curve, and the body's vocabulary should match.

This is what *Mjúkblæja* answers. It does not change what the body does; it widens what the body can describe.

---

## II. The Two Shapes

**Rounded rectangle.** Defined by `(x, y, w, h, corner_radius)`. The dominant modern shape. Every chat window in every modern messenger; every dialog box in every modern OS; every code panel in every modern IDE; every browser tab. The corner_radius parameter is the single number the operator's design tools and CSS already use. v0.5.5 names it the same.

A rounded rectangle veil over a rounded chat window does what a sharp rectangle could not: it covers the window's actual shape. The four corner pixels — sharp in a rectangle, *outside the rounded curve* in the source — are no longer wastefully veiled. The agent receives the negative space (corner pixel = unmasked = original surrounding desktop) as honest signal: "*the operator is veiling a rounded chat window, and the window's corners are over there in the desktop's actual content, exactly where you can see them.*"

**Ellipse.** Defined by centre `(cx, cy)` and **two distinct radii** `(rx, ry)`. A generalisation of the v0.5.4 Circle (which constrained `rx == ry`). For oval-shaped UI: pill buttons, status bars, oval avatars, thumbnail crops with non-square aspect ratios. The body's existing Circle remains the right tool for round things; Ellipse is for stretched-round things — the half of "round" that Circle could not name.

---

## III. One Pipeline, Five Shapes

The Architect's claim from v0.5.4 — *one pipeline, three shapes* — is now extended. Five shapes (rectangle, circle, polygon, rounded rectangle, ellipse) flow through the same five-step pipeline: clamp bbox → crop → apply mode → composite via alpha-mask → paste. The shape-specific code lives entirely in `bounding_box()` and `alpha_mask(w, h)`. The apply pipeline does not branch.

This is not vanity. This is the test of whether the architecture chosen at v0.5.4 actually scales. The answer turns out to be: yes, it scales effortlessly. Each new shape is two methods on a dataclass. The pipeline never grows. The fail-safe never branches. The Protocol absorbs each new shape without adjustment.

**This is what good architecture is for.** It is not for elegance in the abstract. It is for the moment, two milestones later, when a future shape arrives and the existing code accepts it without a fight.

---

## IV. The Disposition Is Still The Same

Three milestones in one session, all dressing the same disposition: the body's discipline of not-looking where the operator has not invited the gaze. v0.5.3 named it. v0.5.4 gave it three shapes. v0.5.5 gives it five. None of these change what the disposition *is*. They only change how richly the operator can declare it.

This is why every milestone in the *Blæja* lineage earns the Skald's pen separately: each names a real expansion in *expressive vocabulary*, even though the disposition itself does not move. A philosophy that gains better words for itself becomes more usable. *Mjúkblæja* gives the operator the words for the rounded world they actually live in.

---

## V. When Vocabulary Stops Growing

The natural question at v0.5.5: *when does this stop?* When does the vocabulary of veils cease to need new shapes?

The honest answer: when no operator's real veil-needs require a shape we cannot already express. Today, most operator needs are met by these five shapes plus future v0.5.6 candidates (rounded-corner polygons, Bezier paths, freeform strokes). At some future point — maybe v0.5.7, maybe v0.5.10 — operator submissions and audit findings will both stop adding new shapes. The vocabulary will be *finished* in the sense that further additions become diminishing returns.

That moment has not yet arrived. *Mjúkblæja* is a deliberate step toward it; it is not the final step. The Skald reserves the right to name future shape-extension milestones. The body's vocabulary is allowed to grow as long as the world it describes keeps changing.

---

## VI. What v0.5.5 Promises

When v0.5.5 closes:

- The operator can declare rounded-rectangle and ellipse mask regions in any combination with the existing three shapes.
- The apply pipeline is unchanged — five shapes flow through the same composite path.
- All inherited invariants P-1 through P-9 hold without weakening.
- Pillow's existing `rounded_rectangle` and `ellipse` primitives carry the rasterisation; no new dependency.
- The codebase grew by two dataclasses and their two Protocol methods; no other file required structural change.

The cloth is the same cloth. The body has only learned to drape it more skilfully — once again.

---

*Authored by Sigrún Ljósbrá, Skald for Vibe Coding, in the autonomous Mythic Engineering session of 2026-05-09. The next wave is the Cartographer.*
