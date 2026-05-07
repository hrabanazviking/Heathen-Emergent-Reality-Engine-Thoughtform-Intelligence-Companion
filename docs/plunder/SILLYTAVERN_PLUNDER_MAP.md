# SillyTavern — Plunder Map

**Map authored:** 2026-05-07
**Author:** Eirwyn Rúnblóm, Scribe for Vibe Coding
**Status:** architectural reference only — no code plundered, none planned; AGPL-3.0 makes any code reuse incompatible with HERETIC's MIT license

---

## Upstream Identity

| Field | Value |
|---|---|
| Project name | SillyTavern |
| Repository | https://github.com/SillyTavern/SillyTavern |
| Primary language | JavaScript (Node.js backend) + HTML/CSS/JS frontend |
| Primary maintainer | SillyTavern community |
| License | **AGPL-3.0 (GNU Affero General Public License, version 3)** |
| License URL | https://github.com/SillyTavern/SillyTavern/blob/release/LICENSE |
| License verification status | **Verified AGPL-3.0 2026-05-07** (LICENSE file confirms AGPL v3) |

**Physical location in HERETIC's ecosystem:** SillyTavern is a well-known AI companion/chat frontend. It is NOT a spirit HERETIC hosts and NOT a library HERETIC uses. It is studied as an architectural reference for AI persona, tool call, and character card design patterns — nothing more.

---

## Upstream License

**AGPL-3.0 (GNU Affero General Public License, version 3).**

The AGPL-3.0 is the strongest copyleft license in common use. Its defining feature beyond GPL-3.0: **if you run a modified AGPL-3.0 program over a network and users interact with it, you must offer them the source code of your modifications.** This "network use" clause means even web services using AGPL code must open-source their modifications.

More critically for HERETIC: **any code copied, adapted, or derived from AGPL-3.0 source must be licensed under AGPL-3.0**. This is completely incompatible with HERETIC's MIT license. There is no path to using SillyTavern code inside a MIT-licensed project.

---

## Compatibility Verdict

**INCOMPATIBLE — AGPL-3.0 is categorically incompatible with HERETIC's MIT license. Zero SillyTavern code may be copied, adapted, or derived in HERETIC under any circumstances.**

This verdict is absolute and permanent unless Volmarr formally changes HERETIC's license to AGPL (which would require re-licensing all other HERETIC code and all dependency licenses — a major decision that is not on the roadmap).

### What this means concretely
- **No code copy** — not a single function, not a single CSS rule, not a single HTML component.
- **No adaptation** — even rewriting SillyTavern code in a different language constitutes a derivative work if the implementation is substantially copied.
- **No pattern copy that is uniquely SillyTavern** — HERETIC may use general UI/UX patterns that happen to appear in SillyTavern (e.g., a chat history panel) because those patterns are industry-standard and SillyTavern did not invent them. But any pattern that is specific and distinctive to SillyTavern's implementation cannot be adapted.
- **No binary redistribution** — HERETIC must never bundle, include, or redistribute any SillyTavern file.

---

## What We Study (Not Plunder)

### Architectural reference patterns (study only — implement independently)

SillyTavern is one of the most mature open-source AI companion frontends. Studying it informs HERETIC's design in the following respects, without copying any code:

**Persona and tool integration patterns**
- How SillyTavern structures character cards (persona definition format) — studied as a reference for how inhabiting agents might describe their personas in a standardized way. HERETIC does not own persona architecture (manifesto principle: "the spirit brings its mind"), but understanding how character cards are structured informs the capability probe design in `AGENT_AGNOSTIC_PROTOCOL.md`.
- How SillyTavern's tool calling UI works — studied to understand what the agent-side tool call UX looks like when tools are exposed. Informs HERETIC's L4 Vébond tool call status display (the badge system showing active tool calls in the Summoning Circle).

**Extension and plugin architecture**
- SillyTavern's extension/plugin system structure — studied as a reference for HERETIC's L5.8 Nýr Limr (custom MCP plugin slot). SillyTavern has solved the problem of loading user-provided extensions; studying their approach (not copying it) informs HERETIC's plugin slot design decisions.

**Disconnected/ceremonial UI patterns**
- SillyTavern's connection management and "character enters/leaves" UI patterns — studied as a reference for HERETIC's Kynding → Tengsl → Samræður → Slokna ceremony lifecycle UI in L4 Vébond. Both products handle the concept of "an AI presence becoming active." SillyTavern's UX decisions (not its code) are instructive.

### What specifically is NOT usable from SillyTavern study
- Any code pattern that is novel or distinctive enough that copying it would constitute a derivative work.
- SillyTavern's character card format as a standard HERETIC must implement — character cards belong to the spirit's domain, not HERETIC's body.
- SillyTavern's specific API implementation, request format modifications, or backend architecture.

---

## What We DO NOT Plunder

Everything. The AGPL license makes this simple and absolute:

- **No JavaScript/Node.js source** — forbidden.
- **No HTML/CSS UI components** — forbidden.
- **No configuration schema** — forbidden if distinctive.
- **No data format implementations** — forbidden if distinctive.
- **No test patterns** — forbidden if copied.
- **No documentation structure** — forbidden if copied verbatim.

If any future contributor wishes to bring a SillyTavern-derived pattern into HERETIC, they must demonstrate independently that the pattern is (a) sufficiently generic to not constitute a derivative work, and (b) arrived at independently. When in doubt: do not use.

---

## Local Domain Ownership

There is no integration. SillyTavern is a reference only.

| HERETIC concern | What SillyTavern reference informs | How HERETIC implements independently |
|---|---|---|
| Ceremony UI lifecycle | SillyTavern's connection/disconnection UI patterns | L4 Vébond's Hvíld → Kynding → Tengsl → Slokna fire-language states — entirely original HERETIC design |
| Tool call status display | SillyTavern's tool use badges in chat | L4 Vébond's sense health indicator and active tool call badge — original HERETIC design in the Eldahús aesthetic |
| Plugin extensibility | SillyTavern's extension loader | L5.8 Nýr Limr custom MCP plugin slot — original HERETIC design |

---

## Attribution Requirements

| Requirement | Status |
|---|---|
| Preserve LICENSE file | Not applicable — no SillyTavern code in HERETIC |
| THIRD_PARTY_NOTICES.md entry | Yes — SillyTavern should be listed as an architectural reference study only, with its AGPL-3.0 license noted and the explicit statement that NO code was copied or adapted |
| In-source headers | Not applicable |
| Trademark | Do not imply SillyTavern team endorsement; do not imply HERETIC is a fork or derivative of SillyTavern |

---

## Verification Status

- License re-verified: **2026-05-07** — AGPL-3.0 confirmed at https://github.com/SillyTavern/SillyTavern/blob/release/LICENSE
- Incompatibility verdict: **permanent** under HERETIC's current MIT license.
- This map records the study and the boundary; it does not represent a risk to be resolved — it is a resolved decision: do not use.

---

## AGPL Compliance Note for Future Sessions

Any session encountering SillyTavern code in a proposed HERETIC contribution should:

1. Identify the provenance of the code immediately.
2. Reject the contribution if it is SillyTavern-derived.
3. Add a note to this map's history if a new SillyTavern pattern is encountered and studied.
4. Never import, adapt, or copy under any circumstances.

This is not a judgment on SillyTavern's quality — it is a valuable, well-designed project. It is simply that AGPL and MIT are incompatible licensing regimes, and HERETIC's MIT grant must be kept clean.

---

*Plunder map authored by Eirwyn Rúnblóm, 2026-05-07.*
*SillyTavern stands behind a wall of copyleft that HERETIC will not cross.*
*We study it from the far shore, take no steel, and build our own forge.*
