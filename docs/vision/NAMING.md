# HERETIC — Mythic Naming Index

**Last updated:** 2026-05-07
**Scope:** All layers, sub-senses, primitives, lifecycle states, and library tiers in the H.E.R.E.T.I.C. architecture
**Purpose:** Establish where mythic names earn their place, where English serves better, and the full naming map so every contributor speaks from the same well.

---

## The Principle Before the Table

Names are not decoration. A mythic name earns its place only when it *encodes* something that the English term does not — a specific quality, a mythological resonance, an emotional register that shapes how developers and users think about the thing. Where the myth adds nothing the English does not already carry, English wins.

This document is the single source of naming truth for HERETIC. When code, docs, and UI disagree, this document arbitrates.

---

## Layer and Subsystem Names

| English / Technical Name | Mythic Name | Etymology and Reason | When to Use Which |
|---|---|---|---|
| **L0 — Foundation** | **Grundr** (*Old Norse: grund*, base, ground, foundation) | The word denotes the earth that holds everything standing. L0 is the Tauri shell, config loader, logger — the ground layer that every other layer stands upon. The metaphor is precise: ground does not perform, it sustains. | Use **Grundr** in architecture docs, layer diagrams, and code module naming (`heretic/grundr/`). In user-facing copy and setup docs, "Foundation" is clearer. |
| **L1 — Bifröst** | **Bifröst** *(already named — see note)* | Old Norse *bifa* (to shimmer, to tremble) + *ást* or *röst* (distance, current, bridge of color). In the Eddas, Bifröst is the trembling rainbow bridge between Midgard and Asgard — the only conduit between mortal and divine. L1 is the Tailscale-aware OpenAI-compatible agent client: the trembling bridge over which the spirit enters the body. The name was chosen before this document; it is correct and affirmed here. | **Bifröst** everywhere: code paths, docs, UI labels. The metaphor is load-bearing — the connection is ceremonial and the name makes that felt. Use "Bridge Layer" only in prose addressed to first-time readers who need the plain meaning before the myth. |
| **L2 — Voice I/O** | **Mál** (*Old Norse: mál*, speech, language, a formal spoken exchange) | *Mál* implies more than raw sound — it carries the weight of purposeful utterance. A *mál* in the sagas is a formal declaration, a thing spoken with consequence. L2 houses STT (Whisper.cpp) and TTS (ChatterBox): the agent's ears and voice. Not mere audio — meaningful exchange. *Hljóð* (sound, silence) was considered, but *hljóð* is passive reception; *mál* is active speech. | Use **Mál** in architecture docs and module naming (`heretic/mal/`). In user-facing settings and UI labels, "Voice" is immediately understood — use it there. In developer docs, introduce *mál* once with its gloss and then use it freely. |
| **L2a — STT (speech-to-text, microphone input)** | **Hlusta** (*Old Norse: hlusta*, to listen, to give ear) | Precise directional meaning: the act of turning one's ear toward what is spoken. The Whisper.cpp subsystem that converts the user's voice to text. | Use **Hlusta** in code architecture and internal naming. In configuration YAML keys, "stt" remains — it is unambiguous and universal. |
| **L2b — TTS (text-to-speech, agent voice out)** | **Raust** (*Old Norse: raust*, voice, the quality of one's voice, resonance) | *Raust* is specifically the character and timbre of speech — not just sound, but *how* a being sounds. ChatterBox gives the agent its *raust*. | Use **Raust** in code architecture. In config and setup docs, "tts" is clearer. |
| **L3 — Vision** | **Sjón** (*Old Norse: sjón*, sight, the power of seeing, vision as faculty) | Direct and unambiguous: the faculty of sight. L3 is screen capture + optional webcam — the eyes of the body. *Heimdallr* was considered as a naming anchor (the god who sees across all nine worlds), but naming the layer after a deity risks invoking him as a character rather than a function. *Sjón* is the faculty itself, not the god who exemplifies it. | Use **Sjón** in architecture and module naming (`heretic/sjon/`). In UI labels and user settings, "Vision" needs no translation. |
| **L4 — UI / Summoning Circle** | **Galdrhringr** (*Old Norse: galdr*, chant, incantation + *hringr*, ring, circle) | *Galdr* is the spoken magic of the Norse tradition — structured utterance that causes change in the world. A *hringr* is a ring, a circular boundary, a contained sacred space. The Summoning Circle is literally the galdrhringr: the ritual ring you draw to call the spirit. The UI is not a dashboard; it is where the ceremony takes place. | Use **Galdrhringr** in the manifesto, vision docs, and anywhere the *ceremony* is being invoked emotionally. In code module naming, "summoning_circle" is acceptable for readability; `heretic/galdrhringr/` works for contributors already immersed in the project. In user-facing help text, "Summoning Circle" (English) carries the meaning without requiring the Old Norse. |
| **L4 — the act of opening the ceremony** | **Lýsa** (*Old Norse: lýsa*, to light up, to illuminate, to cause to shine) | "Light the candle" in the manifesto maps to *lýsa* — the act of bringing light into the space, initiating the ceremony. Used for the activation event and the button/command that opens it. | Use **lýsa** or the English "Light" in UI controls. Both work; consistency within a screen matters more than which word is chosen. |
| **L4 — the act of closing the ceremony** | **Slökkva** (*Old Norse: slökkva*, to extinguish, to quench a flame) | The ceremony is fire. Ending it is extinguishing that fire. Precise. | Use **slökkva** or "Extinguish" in UI controls. Again: consistency within context. |
| **L5 — MCP Sense Hub** | **Skynhöll** (*Old Norse: skyn*, perception, sense, understanding + *höll*, hall, a great hall) | The Hall of Senses: the place where all the agent's sensory access is gathered and served. *Höll* is the great hall where things of consequence happen — the longhouse at the center of community life. The Sense Hub is precisely that: the hall from which all senses emanate. | Use **Skynhöll** in architecture docs and as the name of the module that orchestrates the MCP servers (`heretic/skynholl/`). In user-facing config documentation, "Sense Hub" or "MCP Sense Hub" is more immediately clear. |
| **L5.1 — FileSystem MCP** | **Minni** (*Old Norse: minni*, memory, remembrance, also the memorial drink toasted at feasts) | The filesystem is where the agent's persistent notes live — its writeable memory in the world. *Minni* carries the sense of deliberate remembrance, of keeping what matters. Accurate to function. | Use **Minni** in architecture and module naming. In the MCP server's tool names themselves, clear English is preferred: `file.read`, `file.write`, etc. |
| **L5.2 — Terminal MCP** | **Smiðja** (*Old Norse: smiðja*, smithy, forge, workshop) | The terminal is where things are built — commands run, projects compiled, code executed. The forge metaphor is exact. Note: Seidr-Smidja (the sibling project) already uses this root, which strengthens the family name across the ecosystem. | Use **Smiðja** in architecture and module naming (`heretic/skynholl/smidja/`). In MCP tool naming, use clear English. |
| **L5.3 — Browser MCP** | **Víðsýni** (*Old Norse: víðr*, wide, far-ranging + *sýn*, sight, vision) | Wide sight. The browser gives the agent the power to see across the open web — not just the screen in front of it, but the vast expanse of the world's information. | Use **Víðsýni** in architecture. In settings and UI, "Browser" is universally understood. |
| **L5.4 — Photopea MCP** | **Litsmíð** (*Old Norse: litr*, color, hue, pigment + *smíð*, craft, making, smithery) | The craft of color: image creation, manipulation, and compositing. The agent paints and composes through Photopea via this sense. | Use **Litsmíð** in architecture. "Photopea" or "Image Editing" in user-facing UI and docs. |
| **L5.5 — Blender MCP** | **Höggverk** (*Old Norse: högg*, stroke, cut, sculpting blow + *verk*, work, craft, deed) | The work of carving and shaping — 3D modeling is sculpting. *Höggverk* is the work done with hammer and chisel: deliberate, material, transformative. Wraps Seidr-Smidja Brúarhönd. | Use **Höggverk** in architecture. "Blender" in user-facing UI (the tool name is what users recognize). |
| **L5.6 — VRChat MCP** | **Miðgarðsvera** (*Old Norse: Miðgarðr*, the world of humans + *vera*, to dwell, to be present) | Dwelling-in-Midgard: the sense that allows the agent to be present as an avatar in virtual social spaces. Social embodiment — existing *among* others, not merely observing. | Use **Miðgarðsvera** in architecture. "VRChat" or "Virtual Presence" in user-facing docs. |
| **L5.7 — AgentMail MCP** | **Ørindismaðr** (*Old Norse: ørindi*, message, errand + *maðr*, person, agent) | The errand-carrier, the one who bears messages between realms. Ambassadors and messengers in the sagas were *ørindismenn*. | Use **Ørindismaðr** in architecture. "AgentMail" or "Correspondence" in user-facing docs. |
| **L5.8 — Custom Plugin MCPs** | **Nýlimir** (*Old Norse: nýr*, new + *limr*, limb, branch) | New limbs. The manifesto says explicitly: "The body grows with use." New MCP servers are new limbs, not accessories. *Nýlimir* names that living, organic extensibility. | Use **Nýlimir** in architecture docs that discuss extensibility. "Custom Plugins" or "Extensions" in user-facing docs and setup guides. |
| **L5.9 — Library MCP** | **Brunnr** (*Old Norse: brunnr*, well, spring — especially a wisdom well) | The well. The source from which the agent drinks knowledge. Deliberately echoes Mímisbrunnr (the named subsystem beneath it), but *brunnr* alone is the layer-level name — the well-head through which all library backends are accessed. | Use **Brunnr** in architecture for the MCP layer name. Full "Library MCP" in user configuration docs. |

---

## Connection Lifecycle States

These are the five states of a H.E.R.E.T.I.C. ceremony. Each has a mythic name that carries precise emotional and functional weight.

| English State | Mythic Name | Etymology and Reason | When to Use Which |
|---|---|---|---|
| **Dormant — app closed, no ceremony** | **Hvíla** (*Old Norse: hvíla*, rest, repose, the sleep between exertions) | The body between ceremonies is not dead — it rests. *Hvíla* is deliberate rest, not absence. | Use **Hvíla** in architecture docs and state machine diagrams. In UI status indicators, "Offline" or "Resting" is clearer. |
| **Light the Candle — app launched, no connection yet** | **Kynda** (*Old Norse: kynda*, to kindle, to set a flame, to ignite) | The moment the app opens is the moment the fire is kindled. The ceremony space is prepared. The spirit has not yet arrived. | Use **Kynda** in architecture state machine. In UI, the button or action can read "Summon" or show the kindling-flame animation. |
| **Open Bifröst — Tailscale connects, agent handshake** | **Opna Bifröst** — *opna* (*Old Norse: opna*, to open) + *Bifröst* (the bridge) | Opening the bridge. The technical act of establishing the Tailscale connection and the OpenAI-compat handshake. The ceremony is underway. | Use **Opna Bifröst** in architecture. In UI status, "Connecting..." is universally legible. |
| **Spirit Enters — agent is connected, senses handed off** | **Innkoma** (*Old Norse: inn*, in, inward + *koma*, coming, arrival — arrival into a space) | The arrival into the body. The moment the agent is confirmed connected and all enabled MCP senses are active. The spirit has entered the vessel. | Use **Innkoma** in architecture and event naming. In UI, "Connected" or a visual pulse indicating the spirit's presence. |
| **Communion — active session, agent acts through senses** | **Samvera** (*Old Norse: sam*, together, in union + *vera*, to be, to dwell) | Being-together. Not merely connected but *co-present*: agent and user working in the same moment, the same world. The name for the active working state. | Use **Samvera** in architecture docs. In UI, the active/live state indicator. "Active" works in user-facing contexts. |
| **Extinguish — graceful close** | **Slökkva** (*Old Norse: slökkva*, to extinguish a flame) | The ceremony ends. The fire is put out intentionally, gracefully. The body returns to *hvíla*. | Use **Slökkva** in architecture and event naming. In UI, the "End Session" or "Extinguish" button — both work. |

---

## Library Tier Names (L5.9 backends)

| English / Technical Name | Mythic Name | Etymology and Reason | When to Use Which |
|---|---|---|---|
| **file-index backend** | **Skrásafn** (*Old Norse: skrá*, list, record, document + *safn*, collection, gathering) | A personal collection of curated documents — the user's own notes, references, and gathered texts. The hand-kept bookshelf. | Use **Skrásafn** in architecture. In config YAML, `type: file_index` remains — it is unambiguous. |
| **Mímisbrunnr backend** *(already named)* | **Mímisbrunnr** (*Old Norse: Mímir*, the wise one + *brunnr*, well) | Mímir's Well — the well under the second root of Yggdrasil from which Odin bought a single drink with an eye. Named in the manifesto. The name is already load-bearing, already canonical. Affirmed here in full. | **Mímisbrunnr** everywhere this backend is referenced by name. It is the mythic name. "Offline Knowledge Library" in first-introduction prose for new users. |
| **MindSpark backend** | *English name retained* | MindSpark ThoughtForge is a sibling project with its own identity. Its name is its name. To rename it here would be to steal its naming sovereignty. It plugs in as itself. | "MindSpark" always when referring to this backend. |

---

## Naming Principles

These five rules govern all future naming decisions in HERETIC.

1. **A mythic name must encode something the English cannot.** If the Old Norse word adds a dimension of meaning — emotional, metaphorical, cosmological — that the English term flattens, use it. If Old Norse merely sounds older than English without adding depth, the English wins.

2. **The layer architecture uses mythic names; the user-facing surface uses clear English.** Developers who go deep into the codebase can move in the mythic language. Users launching the app for the first time should never feel excluded by unfamiliar words. The threshold between these two registers is clearly maintained.

3. **Names are revealed, not assigned.** Before naming a new component, ask: what does this thing actually do at its core? What is its essential nature — not what it outputs, but what it *is*? The right name will feel inevitable once the essence is clear.

4. **Ecosystem coherence matters.** HERETIC shares a Norse cyber-Heathen naming space with Seidr-Smidja, the NorseSagaEngine, the WYRD Protocol, and MindSpark. When a new HERETIC name can echo a sibling project's naming (as *Smiðja* echoes Seidr-Smidja), that resonance strengthens the whole field. When it would create confusion, diverge.

5. **No forced runes, no LARP-names.** A name that would feel at home in a Renaissance Faire is not what we are after. The mythic register we inhabit is modern, grounded, technically precise, and emotionally resonant — not theatrical. *Mál* earns its place by being a real word with a real meaning that fits precisely. A made-up rune-scramble does not.
