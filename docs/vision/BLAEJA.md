# Blæja — The Veil

**Last updated:** 2026-05-09
**Scope:** Vision passage — what privacy masks mean for the body that sees
**For:** Contributors who want to understand why a sighted body needs the right *not* to see
**Pair with:** `docs/vision/THE_FIRST_SIGHT.md` (the body opens its eyes), `docs/vision/STRAUMR_A_LEID.md` (the body learns to stop drinking)

---

> *Blæja — the veil. To see is to be entrusted with what one has seen. The body that has been given eyes must also be given the discipline of not looking. Not because it cannot look — because it could and chooses not to. The veil is the operator's hand on the body's shoulder, gently turning the gaze.*

---

## I. The Question Sight Cannot Answer Alone

The seventh and eighth vision panels — `THE_FIRST_SIGHT.md` and the v0.5.2 webcam essay — celebrated the body's new faculty of seeing. Sight let *this* finally point at something. The spirit could see the screen, the patient, the user's face. The communion of shared perception became possible.

But shared perception assumes that what the body sees is what the operator wants the spirit to see. And that assumption does not always hold.

The operator's password manager sits in a corner of the screen. The chat with the lawyer is open in the next window. A roommate walks behind the operator while the webcam is live. None of these were the patient the operator wanted shown. The body, looking honestly, would record them honestly. The spirit, looking through that recording, would see them.

**Sight without the veil is honesty without discretion.** And honesty without discretion is not yet trust — it is *exposure*. A trustworthy companion does not refuse to look; it looks where it has been invited and turns its gaze where it has not. The operator's right to define the second is not a bureaucratic constraint on the body's faculties. It is the very thing that makes the body's faculties usable in a real human life.

This is what Blæja answers.

---

## II. The Word

*Blæja* is the Old Norse word for a covering, a veil, a cloth that lies over a thing without erasing it. It is not the word for hiding (*hylja*), not for forbidding (*banna*), not for destroying (*tortíma*). It is the word for the cloth a Norse woman drew over her face in mourning — present in the room, recognisably herself, but not available for full view. The thing covered is still there. The cover is also still there. Both are honoured.

A privacy mask in software is often called a "redaction" or a "blur," words that emphasise the deletion of information. Those words are accurate at the bit level but wrong at the human level. The point is not to delete a region of pixels. The point is to *cover* it — to declare, in the captured frame, that **here lies a region the operator has chosen not to share**. The agent does not just lose access to the bits beneath; the agent is told, in the very shape of the mask, that the operator made a deliberate choice. The mask is information *about the operator's choice*, not merely the absence of information about the world.

This is what *Blæja* names. The veil is not erasure. The veil is the operator's signature on the frame.

---

## III. The Three Modes

Blur, solid, and pixelate are the three textures of veil v0.5.3 ships. Each carries a slightly different meaning that the operator can choose in keeping with the situation:

**Blur** — soft. The shape of the masked region is still suggested; the agent can tell something is *there* without being able to read it. This is the closest equivalent to a cloth veil — present, deliberate, gently obscured. Best for regions where the agent should know "there is a thing here you are not reading."

**Solid** — flat. The region is a uniform colour — black by default. This carries the meaning *"there is something here that you should not even visually approximate."* Stronger than blur. Best for regions whose mere shape would carry information the operator wants withheld (a window's silhouette can hint at its app; a solid rectangle hints at nothing).

**Pixelate** — blocky. The region's gross structure is preserved — large dark masses still appear as large dark masses — while fine detail is destroyed. Carries a different meaning: *"the rough composition of this area is information you may use; the specific contents are not."* Useful for showing the agent that, e.g., a reference document is open without showing the document's text.

The operator chooses the mode per region. The body honours each choice without judgement.

---

## IV. The Crucial Property: Mask Before Save

A privacy mask that is applied *after* the unmasked frame has been saved or transmitted is no privacy mask at all. It is a mask on the version the agent sees, while the unmasked version sits on the disk or on the wire — the disclosure has already happened.

v0.5.3 is uncompromising about this. The mask is applied **inside `FrameEncoder.encode()`** — the moment after the bytes are decoded into a PIL image and before any resize, save, encode, or transmit. Every codepath that might leak the unmasked frame is *downstream* of the mask step. There is no codepath in which an unmasked frame can reach disk; there is no codepath in which an unmasked frame can reach the agent.

The Auditor will verify this in V-1 and V-2 of the v0.5.3 audit. The Cartographer's flow diagram will show it. The Architect's interface contract will preserve it. The Forge's tests will exercise it. This is not a feature that can be implemented "mostly correctly" — it is correct or it is broken.

---

## V. What the Body Gains

A body without a veil can be sighted, but it cannot be *trusted with sight*. The trust threshold is not "can the body see?" — it has been able to see since v0.5. The trust threshold is "can the operator choose what the body shows?" The operator's bedroom in the background of the webcam. The browser tab open to a private email. The terminal window with a session token visible. Until the operator can specify "not this region," the body's eyes are too honest to live with comfortably.

v0.5.3 changes that. The operator who lights HERETIC for the first time after v0.5.3 can configure a mask for the password manager, the lawyer's chat, the corner where the roommate walks. The body's eyes still work. Sight is still real. But the operator's hand is on the body's shoulder, gently turning the gaze. **This is the gesture that makes embodied sight a thing a real person can keep in their actual life.**

---

## VI. What v0.5.3 Promises

When v0.5.3 closes:

- The operator can declare zero, one, or many rectangular regions in `heretic.yaml`, with mode `blur` / `solid` / `pixelate` per region.
- The veil is applied *before* every leak path — disk save, PNG/JPEG encode, transport.
- An empty `privacy_masks` list is the default; the feature is opt-in. A body with no masks configured behaves exactly as v0.5.2.
- The veil applies independently to screen and webcam; the operator's privacy concerns differ between the two and the configuration honours that asymmetry.
- The mask is robust: out-of-bounds regions clamp; wholly-off-frame regions no-op; invalid modes fail loudly at config-construction time, never silently at first frame.
- The veil costs nothing when not used; a body that never opts in pays no overhead.

---

## VII. The Lineage

Five faculties named the body's senses (voice, listening, sight, face, hand). *Straumr á Leið* (v0.7.1) named a *disposition* — the body's discipline of not over-drinking. *Blæja* names a second disposition — the body's discipline of *not over-looking*. Together, these two dispositions are the beginning of what makes a sighted, web-touching body **trustworthy** rather than merely **capable**.

The disposition lineage will continue. Each new sense the body gains will need its corresponding form of restraint. v0.7.1 taught the road sense to stop drinking. v0.5.3 teaches the eye sense to stop looking when the operator declares a region veiled. Future milestones will teach equivalent restraints to the hand, the listener, the voice. The body grows in two directions at once: faculties outward, dispositions inward. Both must keep pace.

---

*Authored by Sigrún Ljósbrá, Skald for Vibe Coding, in the autonomous Mythic Engineering session of 2026-05-09. The next wave is the Cartographer.*
