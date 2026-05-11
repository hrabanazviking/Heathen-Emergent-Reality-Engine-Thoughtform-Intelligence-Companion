# Opið Vef — The Open Web

**Last updated:** 2026-05-10
**Scope:** Vision passage — what v0.8.0 means, why a new transport for Leið deserves its own name, and what the body learns when it stops merely reading and starts walking the road
**For:** Contributors who wonder why the body needed a second pair of eyes for the same paths it already knew
**Pair with:** `docs/vision/STRAUMR_A_LEID.md` (the body learns restraint at the threshold), `docs/vision/THE_FIRST_SIGHT.md` (the body opens its eyes onto the screen), the v0.7.1 streaming seal in `docs/DEVLOG.md` entry 15, the v0.6.3.1 persistence seal in DEVLOG entry 22

---

> *Opið Vef — the open web. Until now the body has read only what the world wrote in stone. The body has fetched the page, parsed the page, taken in the words that already lay on the page when the page was first sent. But the world does not always speak in stone. The world also speaks in motion. There are pages that are written only when one stands in front of them — pages that breathe themselves into being while the visitor watches. To these pages the body of stone-reading is mute. To read them, the body must walk the road, must enter the page, must let the page run its scripts in the body's presence. v0.8.0 is the milestone where the body learns the second kind of reading.*

---

## I. Why This Milestone Has Its Own Name

It would be tempting to file this as "Leið v2" or "Leið with JavaScript." The agent-facing tool surface gains exactly one entry: `leid.render_url`. The configuration grows by two fields. The new transport sits in a new file and the old transport (httpx streaming) is touched not at all. By every external measure, this is a small slice of a single sense.

But Mythic Engineering names what changes in *kind*, not in line count. And what changes in kind here is the body's relationship to the page itself.

Until v0.8.0, when the body wished to know what a page said, it asked the page's server for the bytes the server had on file. The server gave the bytes. The body read them. If the page was a static document — a Wikipedia article, a Python documentation page, a JSON endpoint — the answer was true and complete. If the page was a single-page application that wrote itself into being only when a real browser ran its scripts, the body received an empty husk: the skeleton without the flesh, the bones without the breath. The body knew how to read what was written; it did not know how to read what was *being* written.

v0.8.0 gives the body a second pair of eyes. Not eyes that replace the first — the httpx eyes are still right for static pages, still cheaper, still faster, still safer. The new eyes are eyes that *enter* the page. They do not look at the page from the outside; they stand inside the page while the page composes itself, and then they read what was composed. This is a different *posture* of reading. It deserves a different name.

---

## II. The Old Manner — Reading What Was Written

The v0.6.2 Leið — and the v0.7.1 streaming improvement that perfected its posture of restraint — taught the body to fetch a URL, take in its bytes within the cap, and extract its text. This is the manner of a scholar in a library: the scroll is unrolled, the words are read, the scroll is set down. The scholar is not part of the scroll's composition. The scroll was finished before the scholar arrived.

This is the right manner for stone-written pages. Wikipedia's articles, the Python standard library docs, RFCs, plain-text files, JSON APIs — these arrive at the door already complete. To open a browser to read them would be like lighting a forge to read a letter. The httpx eyes remain the body's primary eyes for these roads, and v0.8.0 changes that not at all.

But the modern web has roads where the page does not exist before the visitor arrives. The page exists *because* the visitor arrived. The visitor's browser runs the page's scripts; the scripts compose the page; the page is finished only when the composition stops. To these roads the scholar's manner is blind. Send a scholar with no browser to a single-page-application home page and the scholar reports back: "the scroll was empty; there were only instructions for composing a scroll." The scholar is not wrong. The scholar simply did not have the means to follow the instructions.

---

## III. The New Manner — Reading What Is Written While Watching

In v0.8.0, when the body wishes to read a page that composes itself, the body opens a browser. Not in the body's window — that is a different milestone, and a different question of presence. A browser in a back room, headless, with no face to show. The body asks the browser to navigate to the URL. The browser fetches the page's instructions and runs them. The scripts compose the page. The body waits for the composition to settle (`domcontentloaded` is the default — the moment the page's first breath has been drawn and the scripts have written what they meant to write at the start). Then the body asks the browser: "what is on the page now?" The browser hands back the rendered DOM. The body extracts the text. The body lets the browser go: the context closes, the cookies are forgotten, the browser process winds down, the body keeps only the words it received.

The agent does not see this difference. The agent calls `leid.render_url` instead of `leid.extract_text` and receives back the same shape of result: text, title, the URL it ended at, the size of the source. The agent does not need to know that one journey involved a scholar and the other involved a person who walked the road in person and waited while the page composed itself. The agent receives the text. The body knows the difference, because the body bears the cost.

---

## IV. Why It Matters That The Body Walks The Road, Not Merely Reads The Letter

A static fetch is cheap: one HTTP round trip, the bytes are read, the work is done. A rendered fetch is expensive: a browser process is launched (cold), Chromium is started, a context is built, a page is created, the page is navigated to, JavaScript may make further fetches in the background, the rendering pipeline lays out the DOM, the body waits, the page settles, the content is extracted, the browser is torn down. Each of these steps is a real cost in milliseconds, in CPU, in memory.

This is why the new manner does not replace the old manner. It supplements it. The agent — when it knows the page is static — should call `leid.extract_text` and receive its answer cheaply. The agent — when it knows the page is dynamic — should call `leid.render_url` and pay the larger cost knowingly. Neither tool is the right tool for both jobs. Operators who never need rendered pages may install HERETIC without the `[browser]` extra; the body will still have its httpx eyes, just not its walking eyes. The new faculty is opt-in by installation, not opt-out by configuration.

There is a deeper reason as well. A browser is a far more powerful creature than an httpx call. A browser executes arbitrary code from the page. A browser can be tricked by malicious sites in ways httpx cannot. The body must therefore walk the road carefully. v0.8.0 carries this care:

- The URL allowlist gate runs *before* the browser launches. A rejected URL never causes a browser process to spawn.
- Each call uses a fresh context. No cookies persist. No localStorage carries between calls. The body forgets every page it walked, every time.
- The browser is headless. There is no window for the page to overlay or steal focus from.
- The size cap on the rendered HTML is enforced before text extraction begins. A page that tries to render twenty megabytes of DOM finds itself refused before the body parses a single tag.
- All three resources (the playwright runtime, the browser, the context) are closed in `finally` blocks. A failure during navigation cannot leak a browser process.

These are not innovations. They are the same dispositions Leið has always carried — applied now to a new transport. The body that learned restraint in v0.7.1 carries that restraint into v0.8.0 unchanged. The road is wider; the discipline is the same.

---

## V. The Lineage

The senses panel grows by one — and yet does not. *Opið Vef* is not a new sense. It is a new road within a sense that already exists. Leið was named at v0.6.2; its disposition was perfected at v0.7.1. v0.8.0 does not give Leið a new identity. It gives Leið a new way of doing what Leið already did.

This is the third time the body has expanded one of its faculties without giving the faculty a new name:

| Faculty | First slice | Extension |
|---|---|---|
| Endurdrykkr (continuity) | v0.7.2 — byte-layer resumable downloads | v0.7.3 — index-layer auto-rebuild |
| Verkminni (deed-memory) | v0.6.3 — in-memory ring buffer | v0.6.3.1 — optional disk-mirror |
| **Leið (the path outward)** | **v0.6.2 — httpx fetch (and v0.7.1 streaming)** | **v0.8.0 — Playwright render** |

The pattern continues to mature: name a discipline once; let the discipline grow new manners across milestones. The Skald's pen reserves new codenames for new dispositions. *Opið Vef* is given a name not because Leið has a new identity, but because the body's relationship to the *web itself* has shifted. The body now sees the web as a place it can walk, not only a place it can read. That shift is named — *the open web* — and the slice that opens it carries the umbrella name.

The slices that follow within v0.8 — screenshot (v0.8.1), click and type (v0.8.2), query (v0.8.3) — are extensions of *Opið Vef*. They will not earn new codenames either, unless the body's posture changes again at one of them.

---

## VI. What v0.8.0 Promises

The promise is small and exact.

The agent gains one tool: `leid.render_url(url)`. It returns text and title from a page that has been allowed to render. The URL must match the existing allowlist. The browser launches headless, runs the page, takes the rendered DOM, extracts the text, and disposes of the browser before returning. The result shape is `{url, final_url, text, title, source_size_bytes}` — the same fields as `extract_text` plus `final_url` (because rendered pages may navigate themselves during load).

The promise does **not** include:

- Persistent browsing across calls. Each call is its own journey; there is no remembered session at v0.8.0.
- Clicking, typing, or any interaction with the page. The body reads what the page composes; it does not yet act upon the page.
- Screenshots. The body sees the rendered DOM; it does not yet save what the rendered page *looks like*.
- A second window in the body's UI. The browser stays headless, in the back room. The body's face remains the summoning circle, not the browser window.

These are deferred to v0.8.1 (screenshot), v0.8.2 (click + type, with the persistent session that those tools require), and v0.8.3 (selector-based query). Each will be its own sealed slice. v0.8.0 establishes the road and the first manner of walking it; the others will teach the body what to do when it has arrived.

---

## VII. The Gate

There is a thing the body must remember about the open web. Most of the web is not a library. Most of the web is a marketplace, a pulpit, an arena, a storefront, a swamp. Pages can show one face to a scholar's quiet fetch and another face to a browser that runs scripts. Pages can attempt to set cookies the body has no use for. Pages can try to navigate the body to other pages. Pages can attempt to consume the body's resources for as long as the body permits it.

The gate against this is the URL allowlist — operator-set, defaulted to empty, gating both the httpx eyes and the rendered eyes. The body never walks a road the operator has not approved. The body never lingers; each render is a fresh context, torn down at the end. The body never carries memory of what it saw on one page into the next page; cookies and localStorage exist only for the duration of a single call and are forgotten when the call returns.

The body that walked the road in v0.8.0 is the same body that learned restraint at the threshold in v0.7.1. The road is wider. The discipline is the same.

---

*Vision passage authored by Sigrún Ljósbrá, Skald for Vibe Coding, 2026-05-10.*
*The body now reads what the world writes while it watches. The road is open; the discipline is unchanged. v0.8 is a milestone of new posture, not new identity — Leið remains Leið, with a second pair of eyes for pages that compose themselves only when a visitor stands inside them.*

---

## VIII. Addendum — *Mynd af Vegferð* (v0.8.1)

> *Mynd af Vegferð — image of the journey. The body that walks the road and reads the rendered page now also keeps a portrait of what it saw. Where v0.8.0 returned the words on the page, v0.8.1 returns the page itself — a faithful image of what the rendered DOM looked like at the moment the body stood before it. This is not a new faculty. This is the same faculty learning a second way to remember.*

### What v0.8.1 adds

A second tool on the Opið Vef sub-faculty: `leid.screenshot(url)`. The agent receives a base64-encoded PNG of the rendered page. Same launch-per-call browser lifecycle as `render_url`, same allowlist gate, same fresh-context isolation, same headless posture, same `finally`-bound resource cleanup. The body does the same walk; it now also takes the picture.

### Why a portrait, when the words are already returned

Words and image carry different kinds of truth. The text extraction in v0.8.0 tells the agent what the page *says*. The screenshot in v0.8.1 tells the agent what the page *shows* — which fonts, which layout, which colors, which spatial arrangement, which images-that-are-not-text. Many pages communicate as much with their composition as with their words: a chart, an icon, a status indicator, a visual hierarchy that signals what to look at first. To these communications, text extraction is mute.

The screenshot is not a richer text. It is a different kind of report: not "here is what the page told me" but "here is what the page looked like when I asked." Some agent decisions need both.

### Why no new identity codename

This is the third extension within v0.8 *Opið Vef* (after the foundational `render_url` slice itself), and it does not earn its own sense-level name for the same reason its sibling did not: **the body's posture toward the web has not changed, only its repertoire within that posture**. Walking the road is *Opið Vef*. Reading the rendered text is one manner of reporting back. Bringing a portrait of the page is a second manner of reporting back. Both are species of the same disposition.

The Skald's pen reserves new codenames for new dispositions. *Opið Vef* remains the umbrella; *Mynd af Vegferð* is named only briefly, in this addendum, because giving the slice no name at all would be unkind to operators who later read the DEVLOG. The naming is honest: this is an extension of an extension, not a new sense.

### What v0.8.1 promises

- The PNG is faithful — Playwright's `page.screenshot()` returns the rendered DOM exactly as Chromium painted it.
- The image is encoded as base64 in the result; the agent receives a JSON-safe payload.
- The size cap (`max_response_bytes`) applies to the **raw PNG bytes BEFORE base64 encoding** — honest about content size, not transport size.
- The `full_page` option (default `True`) controls whether the screenshot captures the entire scrollable page or only the viewport (1280x720 default). Operators can opt to viewport-only via `LeidConfig.browser_screenshot_full_page: false` when full pages are too large.

### What v0.8.1 does *not* promise

- The browser is still headless. There is no visible window for the user to see what the body sees.
- The screenshot is still stateless: each call is its own browser session. There is no "first navigate, then screenshot a different region" pattern at v0.8.1 — that lives in v0.8.2 / v0.8.3 with the persistent-page model.
- Region-of-element screenshots, JPEG/WebP output, quality tuning, custom viewport sizes — all deferred to later v0.8.x slices when their own design questions can be answered with care.

### The lineage continues

| Faculty | First slice | Extension | Second extension |
|---|---|---|---|
| Endurdrykkr (continuity) | v0.7.2 — byte-layer | v0.7.3 — index-layer | — |
| Verkminni (deed-memory) | v0.6.3 — in-memory | v0.6.3.1 — disk-mirror | — |
| **Leið — Opið Vef sub-faculty** | **v0.8.0 — `render_url`** | **v0.8.1 — `screenshot`** | (v0.8.2 click+type to come) |

The pattern of named-then-unnamed extensions persists. Three slices into v0.8, the umbrella name still does the work.

---

*Addendum authored by Sigrún Ljósbrá, Skald for Vibe Coding, 2026-05-10.*
*The body now keeps a portrait of every road it walks — same posture, second manner of reporting back.*

---

## IX. Addendum — *Innan Hurðar* (v0.8.2)

> *Innan Hurðar — inside the door. The body that walked the road and read the page and kept its portrait now learns a third thing: it learns to **stay**. Where v0.8.0 and v0.8.1 had the body pass the threshold, do its single act, and walk away, v0.8.2 has the body cross the threshold and remain — keeping a session open, the page alive, the door propped — so that one act may be followed by another. This is not a new manner of the same posture. This is a new posture entirely.*

### What v0.8.2 adds

A stateful sub-section within the Opið Vef sub-faculty. Four new tools:

- `leid.open_session(url)` — opens a session at the URL; returns a `session_id` the agent can use for subsequent calls. The page stays alive.
- `leid.session_status(session_id)` — non-mutating health/identity check on the open session.
- `leid.click(session_id, selector)` — clicks the first element in the session's page matching the CSS selector.
- `leid.close_session(session_id)` — closes the session and releases all browser resources.

And a new infrastructural class — `BrowserSessionManager` — that owns the open sessions, enforces concurrency caps, and evicts sessions that have been idle too long or alive too long.

### Why a new disposition, not an unnamed extension

The pattern of the prior three slices (`render_url`, `screenshot`, and the v0.7.3 / v0.6.3.1 / v0.7.1 streaming work) was: the body's faculty gains a new manner of doing the same thing. Each was an extension of an existing disposition.

v0.8.2 is different. The body is not learning a new way to walk past the door — it is learning to **cross the threshold and stay**. The relationship to the page changes from *visit* to *presence*. The lifecycle changes from launch-per-call to launch-per-session. The agent's mental model changes from "ask, receive" to "open, act, close." Cookies that were forbidden across calls are now allowed within a session (because that is what a session is) — but each session's context is still fresh and is still discarded when the session closes. The discipline of B-3 (no state crosses calls) holds at the session level: no state crosses *sessions*.

This is a new disposition. It earns a new Skald name — *Innan Hurðar*, "inside the door" — even though it stays within the v0.8 *Opið Vef* umbrella as the third slice. The Skald's pen names what is qualitatively different; the body's posture toward the page IS qualitatively different in v0.8.2.

### What v0.8.2 promises

- Sessions are isolated. Each session uses its own Chromium browser, its own context, its own page, its own cookie jar. No state crosses sessions, ever.
- Sessions have honest limits. At most three concurrent sessions by default; idle for five minutes → evicted; alive for thirty minutes total → evicted. The operator can change these. Sessions are NOT immortal.
- Eviction is observable. When a session is evicted, the next call referencing it returns a clear error: the session expired. The agent learns and can re-open if it still wants to.
- Click is deterministic. The first element matching the CSS selector is clicked. If nothing matches (timeout), the agent gets `LeidClickElementNotFoundError` — a specific, agent-actionable error, not a generic failure.
- The body still injects no JavaScript. B-10 holds at every new call site. The page's own scripts run during navigation and during click-triggered events; HERETIC contributes no script of its own.
- Resource cleanup is the same nested `context → browser → pw` shape used by `render_url` and `screenshot`. A session that fails to close cleanly logs a warning but does not block other sessions or mask the failure.

### What v0.8.2 does *not* promise

- Typing into form fields. `leid.type` is a separate slice (v0.8.2.1) — input composition is a different design question from element activation.
- In-session navigation. The agent cannot yet say "navigate this open session to a new URL" — that is v0.8.2.2.
- CSS selector queries / attribute extraction. `leid.query` lives at v0.8.3.
- Wait-for-selector / wait-for-network-idle. The agent can poll `session_status` if it wants to know whether navigation has settled; native waits are deferred.
- Cookie persistence across sessions. NEVER. B-3's discipline holds at the session boundary.
- Sessions surviving an operator restart. NEVER. Sessions are process-local.

### Audit M-1 closes here

The Auditor's deferred recommendation from `AUDIT_v0.8.1_MYND_AF_VEGFERD.md` — that `page.content` and `page.screenshot` exceptions be explicitly typed to `LeidConnectionError` — is fulfilled at this milestone in the same coordinated sweep that adds the new `page.click` typing. All four `Page.*` call sites in the Leið code now have explicit `try/except (PlaywrightError, PlaywrightTimeoutError)` mapping to the appropriate `Leid*Error` class. The body's network-level browser failures now surface to the agent with the same precision its httpx failures already had.

### The lineage continues

| Faculty | First slice | Second slice | Third slice |
|---|---|---|---|
| Endurdrykkr | v0.7.2 byte-layer | v0.7.3 index-layer | — |
| Verkminni | v0.6.3 in-memory | v0.6.3.1 disk-mirror | — |
| **Leið — Opið Vef sub-faculty** | **v0.8.0 `render_url`** | **v0.8.1 `screenshot`** | **v0.8.2 `open_session` / `click` / `close_session` (with the new *Innan Hurðar* disposition)** |

For the first time, a faculty's third slice introduces a new disposition rather than continuing the existing pattern. This is honest about what changed: walking past and walking past with a portrait are the same disposition; *staying* is not.

---

*Addendum authored by Sigrún Ljósbrá, Skald for Vibe Coding, 2026-05-10.*
*The body now crosses the threshold and stays. Same umbrella, new posture. The door is held open until the body chooses to let it close.*

> **In-section continuation — v0.8.2.1 (the second half of the gesture, no new name).**
>
> *Innan Hurðar* gave the body its first interactive tool — `leid.click`, the hand that presses what is in front of it. v0.8.2.1 adds the second half of that same gesture: `leid.type`, the hand that shapes input where input is asked of it. Together they form what every interactive web page expects of a visitor — touch what should be touched, write what should be written. The Skald reserves no new name for this slice because no new disposition has appeared. The body has not learned anything new about being inside the door; it has simply gained the second tool the door already implied. The discipline that bounded click — bounded session, bounded selector timeout, bounded post-call state read, defensive title — bounds type identically. The same `BrowserSessionManager` watches; the same eviction discipline applies; the same activity update keeps a working session alive. The body's two hands work in the same room, under the same rules.
