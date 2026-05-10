# Verkminni — The Body's Memory of Its Own Acts

**Last updated:** 2026-05-09
**Scope:** Vision passage — why the hand keeps a record of what it has done
**For:** Contributors who want to understand what observability means for an embodied agent
**Pair with:** v0.6 *Hönd at Smiðju* (the body acts), `docs/vision/THE_FIRST_HAND.md` (the body learns to reach), `docs/vision/STRAUMR_A_LEID.md` (measured drinking), `docs/vision/BLAEJA.md` (measured looking), `docs/vision/ENDURDRYKKR.md` (continuity of draught)

---

> *Verkminni — deed-memory. The body's hand reaches into the world; the body remembers what it reached for. Not in the agent's transcript — that is the spirit's memory, and it belongs to the spirit. Verkminni is the body's own quiet record: every tool call the hand made, in order, with timing, with outcome. The operator does not have to ask the spirit to recount what the hand did. The body has already remembered, on its own behalf.*

---

## I. The Asymmetry That Was There

The body's hand has been able to act since v0.6 *Hönd at Smiðju*. The agent forms an intention, names a primitive (`smidja.click`, `smidja.type_text`, `smidja.vroid_export`), and the body carries that intention through the Brúarhönd daemon to the running application — VRoid Studio, Blender, or whatever the workshop holds. The act happens. The body is the executor; the act has consequences in the world.

But until v0.6.3, there was an asymmetry. The agent could speak of what it had done — "I took a screenshot, then I clicked on the menu, then I exported the avatar" — and the operator could read that account in the model's response stream. The agent's *narrated* memory was rich. The body's *own* memory of what its hand had actually done was nothing. There was no record except the running events in the EventBus, which were ephemeral and consumed by the UI as they fired.

This is the asymmetry v0.6.3 closes. The body now keeps **its own record** of what it has acted upon, independent of and parallel to the spirit's narration. When the operator asks "what did the agent's hand actually do in the last five minutes?" — the answer is no longer "let me scroll the chat transcript and trust the agent's account." The answer is "let me read the body's deed-memory." Two records, two perspectives, one truth.

---

## II. Why Two Memories Matter

A single memory of any event — even a true one — is more fragile than two. The agent's transcript is the *agent's account*. It is what the agent chose to narrate. It does not include calls the agent failed to mention; it does not include calls that errored before the agent could narrate them; it can be edited or summarised by the operator's transcript-management. It is also, fundamentally, a *first-person account* — and first-person accounts of one's own acts are subject to first-person framing.

The body's deed-memory is a *third-person* account, in the same way the body itself is a third-person observer of the spirit it hosts. The body did not choose to call the tool. The body simply executed the call when the agent emitted it. The body's record is therefore *what happened*, with no narrative shaping. Twelve calls happened in this order, with these arguments, with these results, taking these durations, and the body knows because the body did them.

When the two memories agree, the operator's trust is reinforced. When they disagree, the operator has the data to investigate. Trust by reproducibility. Verkminni is *the body's gift of reproducibility* to the operator.

---

## III. What An Audit Log Actually Is

It is tempting to treat "audit log" as a corporate compliance feature — a thing required by SOC 2, a thing for security teams, a thing operators tolerate rather than welcome. v0.6.3 deliberately reframes this.

An audit log, properly understood, is **the body's discipline of self-witness**. The body's hand acts, and the body witnesses its own act in the same gesture. Witnessing is not surveillance; witnessing is the basic function of being conscious of one's own behaviour. A body that acts without witnessing itself is acting unconsciously. A body that witnesses is *aware* — not of the world, exactly, but of what it has chosen to do *in* the world.

This framing matters because it determines the default. Surveillance defaults off (you opt in). Self-witness defaults *on* (you opt out). v0.6.3 chooses the second. The body's deed-memory is on by default; the operator who finds the small in-memory cost unwelcome can disable it. But the body's natural state — the state v0.6.3 ships — is a body that pays attention to what its hand is doing.

This is also why the Verkminni naming matters. *Audit log* is bureaucratic. *Verkminni* is dispositional. The body keeps memory of its work because the body is the kind of body that pays attention to itself.

---

## IV. The Disposition Family Now

Three named dispositions live in the body before v0.6.3:

- **Straumr á Leið** (measured drinking) — Leið learns to stop reading bytes when the cap is reached, instead of measuring after.
- **Blæja** (measured looking, articulate in 5 shapes) — Sjón learns to veil regions the operator declared off-limits, in the shape that fits the source.
- **Endurdrykkr** (continuity of draught) — Mímisbrunnr learns to pick up the same drink that was interrupted, rather than starting over.

v0.6.3 adds a fourth:

- **Verkminni** (deed-memory) — Smiðja learns to remember its own acts, so the operator and the agent share a verifiable record.

Each discipline pairs with a faculty. Each faculty's discipline expresses *that faculty's particular vulnerability* to acting unconsciously. Leið without measure could drink endlessly; Sjón without measure could look at everything; Mímisbrunnr without measure could forget partial draughts; **Smiðja without measure could act and not remember**. The disciplines are not generic best-practices applied uniformly. Each is the antibody to its faculty's specific failure mode.

---

## V. What Verkminni Is, Precisely

Each tool call goes through SmidjaSense.dispatch_tool_call. v0.6.3 adds two recording moments to that path:

**At entry — `started`:**
- timestamp (UTC ISO8601)
- call_id (the OpenAI tool_call id)
- tool_name (e.g., `smidja.screenshot`)
- arguments_json (truncated to 500 characters; the agent's exact arguments, as JSON, with `... (N more chars)` if longer)
- duration_ms (None at this point)
- error (None)

**At exit — `completed` or `failed`:**
- All the above, but now with
- duration_ms (integer milliseconds elapsed since the matching `started`)
- error (None on success; truncated error message on failure)

Both entries carry the same `call_id`, so the operator can correlate them as a pair.

The bounded ring buffer (default 100 entries) auto-evicts the oldest when at depth. At ceremony Slokna, the ring buffer is cleared — Verkminni is ceremony-scoped, not session-persistent. Privacy by disposition: the body's memory of its acts does not outlive the ceremony in which they happened. Future v0.6.3.x can add operator-opt-in disk persistence; v0.6.3 itself is in-memory only.

---

## VI. The Crucial Property: The Audit Hook Is Non-Load-Bearing

The dispatcher's most important architectural property — `dispatch_tool_call` NEVER raises — is older than v0.6.3 and must not be weakened. The audit hook is wrapped in `try/except Exception`. If the AuditLog instance is somehow corrupted or the deque mutation fails or any other unexpected exception occurs in the audit-write path, the exception is logged at warning level and the dispatch continues normally.

This is the V-2 invariant the Auditor will verify. The audit log is a *witness*, not a *gate*. A body whose record-keeping interferes with its acting is a body that has confused observability with behaviour. Verkminni does not act; it watches what was done. Its failure must never make the body itself fail.

---

## VII. What v0.6.3 Promises

When v0.6.3 closes:

- Every Smiðja tool call produces two audit entries (started + completed/failed) in a bounded in-memory ring buffer.
- The dispatcher's never-raise invariant holds even when the audit-write path encounters an exception.
- The ring buffer evicts oldest entries at depth (default 100); no unbounded memory growth.
- At Smiðja sense close (SLOKNA), the audit log clears — ceremony-scoped privacy.
- `verkminni.enabled: false` replaces the AuditLog with a NullAuditLog whose record() is a no-op; the dispatcher path is unchanged.
- arguments_json and error are truncated to 500 characters with `... (N more chars)` markers, bounding per-entry memory.
- Smiðja's existing tests (success path, error path, dispatch shape) all continue to pass — Verkminni is additive instrumentation.

The body now keeps memory of what it has done. The hand acts; the body witnesses. This is the smallest gesture of self-awareness, and it is a real one.

---

*Authored by Sigrún Ljósbrá, Skald for Vibe Coding, in the autonomous Mythic Engineering session of 2026-05-09. The next wave is the Cartographer.*
