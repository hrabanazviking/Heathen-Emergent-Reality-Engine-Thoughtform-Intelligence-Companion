# Straumr á Leið — The Current on the Road

**Last updated:** 2026-05-09
**Scope:** Vision passage — what v0.7.1 means and why a small change earns a name
**For:** Contributors who wonder why an internal-mechanism milestone gets the Skald's pen at all
**Pair with:** `docs/vision/THE_FIRST_HAND.md` (the body learns to act), `docs/vision/STRAUMR_A_LEID.md` (this), the v0.7 Mímisbrunnr seal in `docs/DEVLOG.md` entry 14

---

> *Straumr á Leið — the current on the road. The body no longer needs to wait until the cup is full to know if it can be lifted. The body learns to drink as the water flows. If the draught will be too heavy, the body sets it down before the river has finished pouring.*

---

## I. Why This Milestone Has a Name

It would be tempting to ship v0.7.1 silently. The change is small in line count. The agent-facing surface does not move. The tests assert the same exception class. By every external measure, it is a refactor. The Skald's pen could be saved for a louder milestone.

But Mythic Engineering cares about what a thing *is*, not only what it *does*. And what v0.7.1 is, beneath the line-count, is a change of disposition. Before this milestone, when the body fetched a road's worth of bytes, it would carry the entire weight back before deciding whether the weight was bearable. The user could configure a cap; the cap would honestly refuse oversized payloads; but the refusal happened *after* the body had already lifted the burden. A malicious server pouring five hundred megabytes into the body's cup would succeed at having the body hold five hundred megabytes — for a moment — before the body decided to throw the cup away.

This is not the disposition of a body that has learned to drink. This is the disposition of a body that has not yet learned to *stop drinking*. v0.7.1 is the moment the body learns the second.

---

## II. The Old Manner

In the v0.6.2 Leið, the body's pattern was: ask for the page, receive every byte, count the bytes, and only then decide whether the count was acceptable. The decision was correct. The receiving was wasteful. A road that sent only a few kilobytes and a road that sent gigabytes met the same machinery — full intake, then judgement.

This was a known limitation. The audit said so plainly. The N-2 finding from the v0.6.2 audit named the gap: *"The connection is not closed early. A streaming implementation (httpx aiter\_bytes) would be the correct fix in v0.6.2.1."* The buffer-then-check pattern was authored as a placeholder pending exactly this milestone. The placeholder fulfilled the contract; it did not fulfill the disposition.

---

## III. The New Manner

In v0.7.1, the body opens the road — but it does not yet drink. It enters the streaming context. It asks for the next chunk. Each chunk lands in a small accumulator. After each chunk, the body asks itself a single question: *is the accumulator now larger than what I am willing to carry?* If yes, the body raises its hand. The streaming context unwinds. The connection is closed. The remaining bytes the road would have sent never travel. The body has refused without first having to lift.

This is the same contract the agent has always been promised. `LeidResponseTooLargeError` still rises when the cap is exceeded. The error message still names the cap. The agent's tool result still receives a structured error rather than partial content. **What changes is not what the agent sees, but what the body must endure to give the agent that answer.**

The Norse word for this is *hóf* — measure, restraint, the willingness to know how much is enough before the cup is full. The body now drinks *í hófi*. Not from a counting after, but from a knowing during.

---

## IV. Why It Matters That The Body, Not The Counter, Learns Restraint

In other architectures, a size cap is a property of a counter. The counter watches. The counter decides. The counter raises an alarm. The body keeps fetching until the counter pulls the lever.

In Mythic Engineering, the body itself is what learns. The streaming pattern is not a more sophisticated counter; it is a body that no longer divides itself between *act* and *judge*. The act and the judgement happen in the same gesture, chunk by chunk. The body that drinks is the body that decides. There is no committee.

This is also what makes the change resilient against new failure modes that have not yet been imagined. A counter-based cap is only as robust as the counter's vigilance. A streaming-based cap is robust because the body cannot, by its nature, hold what it has already refused. The disposition does the work the discipline would otherwise have to do.

---

## V. The Lineage

Five vision panels named the body's primary faculties: voice, listening, sight, face, hand. Each was a *what*: a new faculty the body acquired. *Straumr á Leið* names a sixth thing — not a faculty but a *manner*. The body has learned to act with restraint at the threshold. It does not need to be coached toward measure by the operator's configuration vigilance; the measure is now in the body itself.

The other senses will benefit from this disposition as they grow. When v0.8 brings full browser navigation through Playwright, when v0.9 brings the painter's hand through Photopea, when v0.10 brings the social body through VRChat — each will inherit the principle that the body stops before it is full, not after. The streaming temperament begins here, on the smallest sense, because the smallest sense is where new dispositions are easiest to learn cleanly.

---

## VI. What v0.7.1 Promises

When v0.7.1 closes:

- The road no longer demands the whole journey before the first taste.
- A page that exceeds the cap by a single byte will be refused without a single unnecessary byte traveling further.
- The agent-facing contract reads exactly as it did before. The body's interior reads as it should always have read.
- The N-2 note that has been patiently waiting in the v0.6.2 audit since 2026-05-08 closes cleanly. The audit trail records both the writing of the placeholder and the keeping of the promise.

That last item is the part the Skald most wants the contributor to notice. The placeholder was honest about being a placeholder. The audit was honest about it being a notable gap. The TASK file referenced it. The DEVLOG named the deferral. And then, in proper Mythic Engineering rhythm, the deferral was honored — not forgotten, not silently dropped, not justified-after-the-fact as "good enough." It was carried. It was named. It was, when its time came, made whole.

That is what continuity costs. That is what continuity is worth.

---

*Authored by Sigrún Ljósbrá, Skald for Vibe Coding, in the autonomous Mythic Engineering session of 2026-05-09. The next wave is the Cartographer.*
