# Endurdrykkr — The Resumed Drink

**Last updated:** 2026-05-09
**Scope:** Vision passage — what it means for a draught from the well to be picked up rather than restarted
**For:** Contributors who wonder why network resilience earns a Skald-given name
**Pair with:** v0.7 Mímisbrunnr (the well opens), `docs/vision/STRAUMR_A_LEID.md` (the road sense learns measured drinking)

---

> *Endurdrykkr — the resumed drink. The body is at the well of Mímir; the cup is to its lips. Something interrupts — the ceremony Slokna unexpectedly, the Tailscale wire is cut, the host of the well slips for a moment into the world's silence. The body sets the cup down. The bytes already drunk are still in the body. When the body returns to the well — perhaps minutes later, perhaps the next day — it does not begin a new draught from the empty cup. It picks up the same drink, with the bytes already in its body counted, and continues.*

---

## I. The Symmetry That Was Not Yet There

v0.7 *Mímisbrunnr* opened the well. The Norse starter pack — Eddas, sagas, Heimskringla, the Saga of Erik the Red — became the first books the body could draw from without crossing the Bifröst into a live network. Each was downloaded once, atomic-renamed into place, hashed against its manifest entry. The mechanism was clean.

But the mechanism was symmetric in a way the world is not. A successful download: the file reaches dest. A failed download: the file does not reach dest. Either-or. There was no middle state — and worse, the middle state that *did* exist on disk (the `.heretic_tmp` file) was treated as garbage on every failure path. Every interruption paid the full cost of the download from scratch.

For the Norse starter pack — five files, totaling under three megabytes — this asymmetry is invisible. For the v0.8 ZIM corpora the body is being prepared to drink from — Wikipedia ZIMs at 100 GB, Wiktionary at 1 GB, full Project Gutenberg dumps — the asymmetry is prohibitive. A 95% complete 100 GB download lost to a Tailscale flap, restarted from byte 0, is a half-day of bandwidth thrown away. The body is asked to be patient with a world that does not deserve that patience.

*Endurdrykkr* is the answer. The body remembers the bytes already in itself. The next draught starts from the offset, not the origin.

---

## II. Why Resumption Is Continuity, Not Just Optimisation

A naive reading of v0.7.2 calls it an optimisation: less bytes wasted, faster recovery, lower cost. All true. But the framing as *optimisation* misses what the milestone really is.

In Mythic Engineering, **continuity is a first-class concern**. The MD Protocol exists for it. The wave-by-wave commit trail exists for it. The TASK files that record where a session was when it broke off exist for it. The Skald, Cartographer, Architect, Forge, Auditor, Scribe — each role's hand-off to the next role is a continuity moment. *Code that loses bytes when interrupted does not honour this discipline at the layer of bytes.*

A body that re-starts every draught when interrupted is not patient with itself. It treats its own past effort as nothing the moment a connection blinks. *Endurdrykkr* lets the body's past effort matter. The bytes already drunk count toward the draught. The body does not punish itself for the world's faults.

This is not a small thing. A discipline is in part a habit of *not punishing oneself for partial progress*. The body learns this here, in the smallest gesture — picking up the cup again rather than refilling it.

---

## III. The Five Statuses That Matter

When the body sends a Range request to the well, the host can answer in five ways:

**206 Partial Content.** The host honoured the request. Bytes from offset N onward are streaming. The body appends them to the partial cup. The draught is genuinely resumed. This is the gift the world offers when both parties are well-behaved.

**200 OK.** The host did not honour the Range; it sent the full body anyway. (Some hosts do this; some HTTP/1.0 reverse proxies; some misconfigured servers.) The body resets. The hasher starts fresh. The tmp file truncates. The body downloads from offset 0 again. The world refused to be helpful, and the body does the helpful thing anyway, without complaint.

**416 Range Not Satisfiable.** The host has a different file than the one the body's partial bytes belong to. Maybe the source URL was updated; maybe the host's content moved; maybe the partial bytes are corrupted. The body deletes the partial cup and asks the operator to begin the draught fresh. This is the only status that requires operator awareness — because the previous bytes themselves were probably wrong.

**4xx, 5xx (other).** Network-level error. The body raises a typed exception and **preserves** the partial cup. The next call can resume from where this one ended.

**Network blink (TransportError, TimeoutException).** Same as the previous case. Partial preserved. Operator retries.

The body's response to each status is deliberate. It is not "retry harder." It is "honour the world's actual answer with the smallest gesture that preserves continuity."

---

## IV. SHA-256 Across The Seam

The trickiest part of resumption is the integrity check. The manifest lists a SHA-256 of the *full file*; the body has bytes from two different download attempts; the running hasher must produce the digest that would have been produced by an uninterrupted single download.

The discipline: **hash the partial bytes into the hasher BEFORE issuing the Range request.** The partial bytes are read from `.heretic_tmp`, fed into `hashlib.sha256()`, then the Range request begins. Each new chunk is also fed into the same hasher. When the streaming completes, `hasher.hexdigest()` equals what the digest of the full bytes would have been if no interruption had ever occurred. The manifest comparison works correctly across the seam.

This is the M-7 invariant the Auditor will verify: that resumption preserves digest correctness. The body's continuity at the byte layer must be indistinguishable from a draught that was never interrupted. If the digest matches, the draught was complete and correct. If it doesn't, the partial was corrupted and is deleted (M-8).

---

## V. The Distinction That Matters Most: Resumable vs Non-Resumable Failure

Not every failure deserves a preserved partial cup. Some failures mean *the bytes themselves are wrong* and must not be drunk again. Some failures mean *the connection blinked* and the bytes are still good.

The discipline:

**Resumable failures** — preserve `.heretic_tmp`:
- `httpx.TransportError` (DNS, TCP, TLS) — the bytes received before the failure were on a healthy connection
- `httpx.TimeoutException` — same, just slow
- `httpx.RequestError` (any other request-level error) — same
- Generic `OSError` during disk write — disk transient

**Non-resumable failures** — delete `.heretic_tmp`:
- `IntegrityError` from SHA-256 mismatch — the file at the source is no longer what the manifest says it is; the bytes are *poisoned*
- `IntegrityError` from safety size cap — the response is too large; the source has changed shape
- Range Not Satisfiable (416) — explicit signal from the server that the partial bytes do not align with the current source

This is the M-8 invariant. The body knows the difference between a recoverable interruption and a poisoned partial. Recoverable interruptions are forgiven; poisoned partials are dropped.

---

## VI. What v0.7.2 Promises

When v0.7.2 closes:

- An interrupted download leaves a usable `.heretic_tmp` file ready for resume on the next call.
- The next `heretic library download <id>` automatically detects the partial, hashes it, sends a Range request, and continues — no operator flag, no new command.
- The full-file SHA-256 hash is correct after resume — indistinguishable from an uninterrupted download (M-7).
- Servers that don't honour Range are handled gracefully — the body restarts the download fresh without raising (M-9).
- Range Not Satisfiable (416) is handled cleanly — partial deleted, operator told to start fresh.
- Resume-able vs non-resume-able failures are clearly distinguished — networks blinks preserve, integrity errors delete (M-8).

The body learns to honour its own past effort at the layer of bytes. The well is no longer the kind of well that punishes the cup-bearer for the world's interruptions.

---

## VII. The Lineage

Five faculties. Two named dispositions (measured drinking, measured looking). The *Blæja* lineage matured at v0.5.5 into a five-shape vocabulary. *Endurdrykkr* opens a different axis: **resilience disciplines**. The body needs not just measured drinking and measured looking; it needs *measured remembering* — the discipline of not forgetting partial progress when the world interrupts. This is the first of those.

There will be more. The Smiðja hand may need *measured reaching* — restraint when a tool call should be confirmed. The Hlust ear may need *measured listening* — restraint when audio should not be transcribed. The Tunga voice may need *measured speaking* — restraint when output should be silenced. Each new resilience discipline will get its own Skald-given name. v0.7.2 begins the line.

---

*Authored by Sigrún Ljósbrá, Skald for Vibe Coding, in the autonomous Mythic Engineering session of 2026-05-09. The next wave is the Cartographer.*

---

## VIII. Addendum — v0.7.3: continuity extends to the index (2026-05-09)

> *The Skald has decided not to coin a new name for v0.7.3. This is not because the milestone is unimportant — it is because the milestone is the same disposition, applied to a second layer.*

v0.7.2 *Endurdrykkr* taught the body's draught to pick up where it left off when the connection dropped. v0.7.3 teaches the same disposition to the *cup itself* — the keyword index that organises the bytes into something queryable. When the index is corrupt or missing but the source files are present, the body does not punish the operator with an actionable-error message demanding they run `heretic library rebuild-index` manually. The body simply rebuilds the index from the sources it already has — quietly, automatically, and identically to how a manual rebuild would build it. The continuity discipline now extends across two layers: bytes (v0.7.2) and structure-over-bytes (v0.7.3). Same Endurdrykkr; one layer deeper.

The decision not to add a separate vision passage for v0.7.3 is itself a discipline. The Skald's pen is reserved for milestones that name new dispositions, vocabularies, or major faculties. v0.7.3 does none of those — it deepens an existing discipline. A scribe-class milestone, recorded in the DEVLOG, but not earning a separate vision page. The lineage stays clean.

*Addendum authored by Sigrún Ljósbrá, 2026-05-09.*
