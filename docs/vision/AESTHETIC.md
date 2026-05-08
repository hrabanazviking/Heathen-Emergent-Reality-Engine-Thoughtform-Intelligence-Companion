# HERETIC — Aesthetic Guide

**Last updated:** 2026-05-07
**Scope:** Visual and sonic design language for L4 Galdrhringr (the Summoning Circle UI)
**For:** Designers and developers building any part of the HERETIC user interface

---

## The Single Governing Principle

HERETIC should feel like a modern longhouse in the dark: warm, purposeful, and alive — with the specific quality of aliveness that comes from things that breathe rather than things that blink. The UI does not perform busyness. It holds space. When the ceremony is not active, it is still and dim. When the spirit enters, it pulses.

Every design decision below follows from that.

---

## Color Palette

### Dark Mode (default — the only mode that feels right for this)

HERETIC is a nocturnal instrument. The ceremony happens when you choose to enter the ritual space, which is not always in daylight and should not feel like a browser tab. Dark mode is not a preference setting; it is the identity.

**Background layers** (deepest to surface):

| Role | Description | Approximate value |
|---|---|---|
| **Void** | The deepest background. Near-black with a barely perceptible cool blue-grey undertone — not pure black, which is flat. The ceiling of the longhouse, the sky before dawn. | `#0a0c10` |
| **Structure** | Panels, sidebars, container backgrounds. Slightly lighter — charcoal with warm ash in it. The stone walls. | `#111418` |
| **Surface** | Card backgrounds, input fields, elevated elements. Warmer still — the hearthlit floor. | `#1a1e25` |
| **Raised** | Tooltips, dropdowns, modals that float above the surface. The table brought close to the fire. | `#232830` |

**Text:**

| Role | Description | Approximate value |
|---|---|---|
| **Primary text** | Off-white with a warm gold tinge — parchment, not paper. Not pure white, which is harsh. | `#e8dfc8` |
| **Secondary text** | Muted warm grey — readable but receding. | `#8a8070` |
| **Inactive / ghost** | Barely perceptible. For disabled states and labels that are present but not demanding attention. | `#4a4540` |

**Accent colors — the bioluminescence:**

These are the glowing elements: status indicators, active states, hover highlights, the pulse of the spirit's presence. They should feel like foxfire in the dark — present, alive, not quite of this world.

| Role | Description | Approximate value |
|---|---|---|
| **Eld** (the primary accent — fire and light) | A deep, rich amber-gold that suggests candlelight. The color of something burning with intention. Used for the active connection state, primary action buttons, the summoning-circle ring when alive. | `#c8860a` / `#e8a020` (glow) |
| **Sjón-glow** (vision / perception accent) | A cool blue-silver that suggests moonlight on water or bioluminescent sea life. Used for vision-layer indicators, sight-related UI elements. | `#4080b0` / `#60a8e0` (glow) |
| **Mál-green** (voice accent) | A deep, rich teal-green — the color of aurora borealis as a thin thread. Used for voice indicators (listening, speaking, microphone active). | `#1a6050` / `#30a880` (glow) |
| **Varúð** (warning / attention) | Burnt sienna — the color of dying embers. Warm enough not to feel clinical, clear enough to signal caution. | `#c04020` |
| **Hvíla-grey** (dormant / resting state) | Desaturated steel — neither warm nor cold. For the UI in its resting state, before the ceremony. | `#404850` |

### Light Theme (for the rare bright-environment user)

If a light theme is ever implemented — and it is a low priority — the palette inverts to warm parchment and aged linen rather than clinical white. The accent colors remain but shift slightly warmer.

| Role | Description | Approximate value |
|---|---|---|
| **Page background** | Aged parchment — the color of a manuscript left in a dry place. Never white. | `#f0ead8` |
| **Surface** | Warm cream. | `#e8e0cc` |
| **Primary text** | Very dark warm grey-brown. Not pure black. | `#1a1610` |
| **Accents** | Same family, shifted slightly warmer and slightly lower luminance so they don't burn in daylight. |  |

The light theme, if built, should feel like the same longhouse in daylight — the same warmth, the same proportions — not like a different product.

---

## Typography

### Principles

Typography in HERETIC should feel legible, grounded, and subtly archaic — not in the sense of difficult to read, but in the sense of *having weight*. Fonts that feel like they were designed last week by a startup are wrong. Fonts that feel like they were carved are wrong in the other direction.

The target: fonts with genuine craft history, good legibility at small sizes, and a quiet dignity.

### Font Stack

**Display / Headings (large titles, section headers, the app name):**

*Cinzel* — a Roman-influenced serif with monumental letterforms, designed in 2011 but rooted in classical proportions. It reads immediately as serious, ancient-adjacent, and ceremonial without touching the rune-font trap. Available via Google Fonts (Open Font License). Use for: app title, section names in the Summoning Circle, milestone/ceremony labels.

Alternative: *Cormorant Garamond* — warmer, slightly more humanist. Use if Cinzel reads as too Roman for a given context.

**Body / Reading (descriptions, help text, labels, status messages):**

*Inter* — the modern standard for legible screen text. It has no period flavor, which is the point here: body text should disappear, not compete with the aesthetic. The flavor lives in the display type, the glows, the motion. The body text serves clarity. Available via Google Fonts (OFL).

*Source Sans 3* is an acceptable alternative.

**Code / Monospace (command output, file paths, config values, MCP tool names):**

*JetBrains Mono* — clean ligatures, excellent legibility at small sizes, slightly warmer than Fira Code. Available under the OFL. The coding font should feel like runes on a technical instrument — precise, purposeful.

*Fira Code* is an acceptable alternative.

**Rune / Ceremonial (sparingly — single characters as decorative accents, not for reading):**

Old Norse and Elder Futhark glyphs used as decorative single-character accents (not for reading text) should use Unicode rune codepoints rendered in a clean sans-serif rather than a "rune font." This keeps them legible and avoids the clip-art-rune trap. See Anti-Patterns below.

### Type Scale

Keep the scale modest and well-spaced. HERETIC is not a dashboard with twenty data points competing for attention. It is a ritual space. Whitespace is part of the design.

- Display: 28–36px, Cinzel, generous tracking (+0.02–0.04em)
- Heading 1: 20–24px, Cinzel or Cormorant, moderate tracking
- Heading 2: 16–18px, Inter Semibold
- Body: 14–15px, Inter Regular, line-height 1.6
- Small / labels: 12px, Inter Medium, letter-spacing +0.04em
- Code: 13px, JetBrains Mono

---

## Iconography

### Philosophy

Icons in HERETIC should feel like marks made by someone who understood what they were marking. Geometric, minimalist, line-based. Asymmetry is welcome where asymmetry is honest — organic systems are not symmetrical, and forced symmetry in icons looks like corporate placeholder art.

Do not use literal runes as icons. A rune character dropped into an icon slot is not design; it is borrowed meaning that the viewer may not share. Instead, take the geometric *quality* of runic forms — the angularity, the intentional line weight, the way a mark can carry meaning in very few strokes — and apply it to functionally meaningful shapes.

### Icon Vocabulary

**The circle** is the primary motif: the ring of the Galdrhringr, the summoning circle, the boundary between inside and outside. It appears in the main ceremony control, in status indicators, in the alive/dormant states.

**The bridge** (two points connected by a line that arcs or trembles) appears in Bifröst-related UI: the connection indicator, the agent status.

**The flame** appears for the lighting/extinguishing control — a simple, single-stroke stylized flame, not a clipart candle.

**The eye** appears for Vision layer (Sjón) — minimal, almond-shaped, with a single dot. Not elaborate.

**The wave / sound form** appears for Voice layer (Mál) — a simple three-wave radiating form, not the standard wifi icon (too associative).

**The branch / limb** appears for the Nýlimir (custom plugin) slot — a forked line suggesting growth and extensibility.

All icons should be constructed on a consistent grid (24x24 or 32x32 base), with line weights that feel balanced at both small sizes and at 2x. Avoid filled icons where outline icons carry the same meaning — the outline version reads as lighter, less imposing.

---

## Motion Language

### The animating principle: breathing, not blinking

Everything in HERETIC that moves should move like something alive. Not like a notification badge urgently demanding attention. Not like a progress spinner implying that computation is happening and you should wait. Like something that breathes.

### Specific Motion Patterns

**The summoning ring (Galdrhringr) in active state:**
A slow, continuous radial pulse — the ring gently expanding and contracting with a luminance oscillation. Period: approximately 4 seconds for a full breath cycle. Easing: sinusoidal (ease-in-out across the full period, no hard starts or stops). Amplitude: subtle — a 4–8% luminance change and a 1–2px scale change. It should be something you notice peripherally and find calming rather than something demanding your attention.

**Connection state transitions (kynda → opna Bifröst → innkoma):**
A slow brightening of the ring from Hvíla-grey through the warmth of Eld. Duration: 1.5–2 seconds. Not a jump cut; not a loading bar. A gradual illumination, like fire catching.

**Agent-speaking indicator (voice out / Raust active):**
The Mál-green voice indicator expands and contracts in rough synchrony with the TTS amplitude — a simple waveform pulse or radial bloom that responds to the actual audio envelope. This gives the sense that the agent's voice is *coming from somewhere*, that something is generating it.

**Listening indicator (voice in / Hlusta active):**
A different motion: a slow inward pull rather than an outward pulse. The indicator contracts slightly toward its center while listening, then releases when the utterance ends. Listening is receptive; the motion reflects receptivity.

**Status changes / sense toggles:**
Cross-fade between states, 200–300ms. No sliding panels, no accordion animations. Things appear and disappear cleanly, as if light conditions changed rather than elements moved.

**Error states:**
A single, slow, dull-orange pulse — once, not repeating — and then a return to resting state with the error message present. Errors should not perform urgency. They should be present and readable.

**What to avoid in motion:** rapid blinking, carousel auto-play, bouncing elements, spring-physics that overshoots, any animation under 150ms that implies quickness rather than intention, any motion that continues running while the user is not looking at it (except the breathing pulse of the active ring, which is the heartbeat of the ceremony).

### Timing Reference

- Micro (hover state, toggle): 150–200ms ease-out
- Transition (scene change, state shift): 250–350ms ease-in-out
- Ceremonial (ring breath, connection bloom): 1500–4000ms sinusoidal
- Never use linear easing for organic/living elements. Linear is mechanical.

---

## Sonic Palette

Sound in HERETIC is not a notification system. It is ceremony. Every sound should feel like it belongs in the space — like it would feel wrong absent, but also like it never startles.

All sounds are subtle by default. The user controls volume. Default volume for all UI sounds: low, ambient-level.

**Ambient presence tone (active ceremony):**
A very subtle, continuous low drone — the acoustic equivalent of the hearth fire. A held low fundamental (around 80–100 Hz) with a slow tremolo, barely audible. It should create the sense that the space is inhabited without calling attention to itself. Should fade in over 2–3 seconds when the ceremony opens. Optional; off by default. On when the user enables "ambient mode."

**Connection-open chime (Innkoma — spirit enters):**
A single struck tone followed by a slow, rich harmonic decay. Something like a large singing bowl or a struck piece of metal with long sustain. Not a bell (too bright), not a chime (too light). A deeper, rounder tone that suggests presence arriving rather than a notification firing. Duration: the strike plus 3–4 seconds of natural decay. Pitch: somewhere around D3–G3.

**Connection-close sound (Slökkva — extinguish):**
The reverse of the open chime in emotional quality: a sound that recedes rather than arrives. A soft descending tone, like a fire burning low, or a single bowed note that fades out. Not sad — more like the satisfaction of a completed ceremony. Something that makes the closing feel intentional.

**Agent speaking indicator (Raust active):**
Not a sound — a visual pulse. The sound of the agent speaking is the agent's voice itself. No additional UI sound for this state. The TTS audio is the signal.

**Listening indicator (Hlusta active):**
An extremely soft, brief click or inhale-tone when the STT begins recording — low-level confirmation that the microphone is now open. Something like the very quiet sound of a recording device starting. This is a safety/clarity feature as much as an aesthetic one: the user should always know when they are being heard.

**Error tone:**
A single, soft low tone — not a buzzer, not a harsh beep. One gentle negative note, slow attack, medium decay. Something that signals "something requires attention" without triggering alarm. Think of the sound of someone placing their hand on your arm to get your attention, not knocking loudly.

**What to avoid in sound:** notification dings, phone-like sounds, Windows XP sounds, anything that evokes a browser tab or an email arriving, anything that repeats more than once per event, anything that would feel wrong if the user's housemates heard it unexpectedly.

---

## Norse Aesthetic Anti-Patterns

These are the things that immediately break the aesthetic and must be avoided categorically.

**1. Horned helmets and touristic Viking iconography.**
Viking helmets did not have horns. More relevantly: that entire visual vocabulary (drinking horns held in fists, longships with cartoon waves, fur-draped warriors) is the aesthetic of a Halloween store. It trivializes the culture and reduces the aesthetic to a costume. HERETIC is not wearing a costume.

**2. Clip-art runes used as decoration.**
Elder Futhark runes used as decorative assets — backgrounds tiled with ᚱᚢᚾᛖᛊ, icons built from random rune characters, section dividers made of rune borders — is the visual equivalent of using Chinese characters on a restaurant logo without understanding them. Each rune has specific meaning and use. If you use a rune, use the right one, understand why, and use it once with intention. Do not use them as texture.

**3. Helvetica, Roboto, or any sans-serif with no personality.**
The generic modern sans-serif is the voice of product design consensus. It says "we wanted to be legible and not offend anyone." HERETIC has a point of view. The typography should have one too. See the Typography section for the right choices.

**4. Gradients that feel like Web 2.0 or Microsoft Office.**
Gradients are not wrong. The warm glow of the active ring is a gradient. But the gradient should feel like light and shadow, not like a PowerPoint template. If it looks like something you'd see on a service provider's pricing page, delete it.

**5. Light mode defaulting.**
HERETIC should never ship with light mode as default. This is not a preference issue. The ceremony takes place in the dark. The aesthetic only fully resolves in dark mode. If you are building the UI and you are defaulting to light, you are building a different product.

**6. Using "Viking" as a design direction.**
This is subtle but important. Designing for "Viking aesthetic" leads to horned helmets and knotwork borders. Designing for "modern Heathen: a dark longhouse at night, with fire, with craft objects, with the sense that something is being made here" leads to the right place. The word is a tourist trap. The *feeling* is what we are after.

---

## Reference Inspirations

These are existing interfaces and environments that capture some facet of the right aesthetic. They are references, not targets — HERETIC is not a clone of any of them.

**1. Obsidian (obsidian.md)**
The dark mode, the way text feels like it is being laid into deep space, the candle-warm graph view, the sense that your notes are a living structure rather than a filing system. HERETIC is not a note-taking app but Obsidian has found the visual register of "dark, purposeful, alive without being aggressive." Study its color use, its typography choices, the way it handles density without crowding.

**2. Hades (Supergiant Games)**
The UI typography and icon language in Hades: Grecian in origin but executed with such restraint and modern clarity that it never reads as a costume. The ambient sound design that feels fully within the world. The way each UI element has weight and character without being loud. HERETIC aims for something analogous in Norse register.

**3. Darkroom (for iOS/Mac) — the photo editing app**
Not Norse, but exemplary in a specific way: a dark-mode interface that achieves warmth through restraint. Large amounts of space. Careful use of subtle accent color. Text that is legible without shouting. The sense that the tool respects the work you are doing rather than competing with it. That is the relationship HERETIC should have with the agent's work.

**4. Elpass / 1Password 8 in dark mode**
A security tool that managed to make a dark interface feel trustworthy and inhabited rather than cold and technical. The rounded containers, the subtle shadows, the careful accent use. Not the same aesthetic as HERETIC, but evidence that dark mode can feel warm and craft-like rather than hacker-minimal.

**5. Rogue Legacy 2 and similar "northern Gothic" game UIs**
Not the gameplay — the menus, the item screens, the way information is presented in a dark, parchment-and-iron visual language. The use of serif type at scale. The subtle texture in backgrounds. The sense of earned weight in every UI element. That weight is what HERETIC is after.

---

## Summary for New Contributors

When you are making a design decision for HERETIC, the three questions to hold:

1. **Does this feel like it belongs in the longhouse?** Warm, dark, purposeful, alive-but-still.
2. **Does it breathe or does it blink?** If it pulses, the pulse should be slow and intentional. If it moves, the motion should feel like something living, not something loading.
3. **Is the Norse element here because it means something, or because it looks old?** If the latter, take it out.

Everything else follows.
