"""
Leið sense tool definitions — OpenAI tool schemas.

LEID_TOOL_DEFINITIONS is a module-level constant. ToolDispatcher consumes
this list verbatim when building the tools array passed to the agent at TENGSL.

Tool naming: two-part format per SENSE_CONTRACTS.md §2 (sealed convention A-2).
    leid.<action>

v0.6.2 (2 tools — LOCKED):
    leid.fetch_url    — fetch raw HTTP response within URL allowlist (httpx)
    leid.extract_text — fetch URL and extract plain text content (httpx)

v0.8.0 (1 added tool — LOCKED):
    leid.render_url   — navigate via headless Chromium, extract rendered
                        text + title from the post-JS DOM (Playwright, opt-in
                        via `pip install heretic[browser]`)

v0.8.1 (1 added tool — LOCKED):
    leid.screenshot   — navigate via headless Chromium, return a base64-encoded
                        PNG of the rendered page (Playwright; same opt-in)

v0.8.2 (4 added tools — LOCKED):
    leid.open_session     — open a stateful browser session at a URL; returns
                            session_id; the page stays alive
    leid.session_status   — non-mutating health/identity check on an open session
    leid.click            — click the first element matching a CSS selector
                            inside an open session
    leid.close_session    — close a session and release all browser resources
                            (idempotent for unknown session_id)

v0.8.2.1 (1 added tool — LOCKED):
    leid.type             — fill the first element matching a CSS selector with
                            the supplied text inside an open session (uses
                            Playwright's locator.fill — clears + focuses + sets
                            + dispatches input event)

v0.8.2.2 (1 added tool — LOCKED):
    leid.navigate         — navigate an open session to a new URL; cookies +
                            localStorage persist (the session keeps its
                            identity, only the page URL changes)

v0.8.3 (1 added tool — LOCKED):
    leid.query            — read text or attribute of first element matching
                            a CSS selector inside an open session; "not
                            found" returns {found: false} rather than raising
                            (read-only divergence from click/type)

v0.8.4 (1 added tool — LOCKED):
    leid.press            — send a keyboard key (Enter, Tab, Escape, modifier
                            combos) at page-level focus; the body's keyboard
                            finger for form submission and modal dismissal

INVARIANT: do NOT rename these tools without a sense version bump.

Sandbox rule (enforced in client.py / playwright_client.py, validated in sandbox.py):
    Every URL submitted to ANY leid.* tool is validated via
    sandbox.url_matches_allowlist() BEFORE any HTTP request is sent OR any
    browser process is launched. HTTPS-only by default — HTTP URLs are
    rejected unless allow_http: true. httpx tools store no cookies and
    execute no JavaScript. Browser tool (render_url) uses a fresh browser
    context per call — cookies discarded at end of call; HERETIC injects
    no JavaScript, but the page's own scripts run during render.

Ref: TASK_HERETIC_v0.6.2_MORE_SENSES.md §Tools (Leið)
     TASK_HERETIC_v0.8.0_OPID_VEF.md §Tools (render_url)
     docs/architecture/SENSE_CONTRACTS.md §2 (naming convention)
     src/heretic/skilningr/senses/leid/INTERFACE.md
"""

from __future__ import annotations


LEID_TOOL_DEFINITIONS: list[dict] = [
    # ------------------------------------------------------------------
    # leid.fetch_url
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "leid.fetch_url",
            "description": (
                "Fetch the raw content of a URL via HTTP GET within the configured "
                "URL allowlist sandbox. The URL must match at least one pattern in "
                "url_allowlist_patterns — unmatched URLs are rejected before any "
                "request is sent. Returns the response body as a string (UTF-8 when "
                "the response is text; base64-encoded for binary content). "
                "Response size is capped at max_response_bytes. "
                "No cookies are stored or sent. No JavaScript is executed. "
                "HTTPS-only by default. "
                "Use this to retrieve documentation pages, JSON APIs, or text "
                "resources from the approved URL list."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": (
                            "The URL to fetch via HTTP GET. Must start with https:// "
                            "(or http:// if allow_http: true is configured). "
                            "Must match at least one pattern in url_allowlist_patterns. "
                            "Example: 'https://docs.python.org/3/library/os.html'"
                        ),
                    },
                },
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # leid.extract_text
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "leid.extract_text",
            "description": (
                "Fetch a URL and extract its plain text content, stripping HTML tags "
                "and returning only the readable text. The URL must match the "
                "url_allowlist_patterns. Response size is capped at max_response_bytes. "
                "No JavaScript is executed — this is a static HTTP fetch only. "
                "Use this to retrieve the text content of documentation pages, articles, "
                "or other HTML pages for summarisation or analysis."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": (
                            "The URL to fetch and extract text from. Must match "
                            "the url_allowlist_patterns. "
                            "Example: 'https://en.wikipedia.org/wiki/Norse_mythology'"
                        ),
                    },
                },
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # leid.render_url  (v0.8.0 Opið Vef — opt-in browser sub-faculty)
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "leid.render_url",
            "description": (
                "Navigate to a URL in a headless Chromium browser, allow the page's "
                "own JavaScript to run, then extract the plain text and title from "
                "the rendered DOM. Use this for Single Page Applications, JavaScript-"
                "rendered pages, or any URL where leid.extract_text returns an empty "
                "or skeletal result because the content is composed by client-side "
                "scripts. The URL must match url_allowlist_patterns (same gate as "
                "leid.fetch_url / leid.extract_text). Each call uses a fresh, isolated "
                "browser context — no cookies persist between calls. The browser is "
                "always headless. HERETIC injects no JavaScript; only the page's own "
                "scripts run. Response size (rendered HTML) is capped at "
                "max_response_bytes. Significantly slower and more expensive than "
                "leid.fetch_url / leid.extract_text — prefer the static tools when "
                "the page is known to be static. Requires the [browser] extra to be "
                "installed (`pip install heretic[browser]` and `playwright install "
                "chromium`); returns EXTERNAL_APP_UNAVAILABLE if absent."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": (
                            "The URL to navigate to in a headless Chromium browser. "
                            "Must start with https:// (or http:// if allow_http: true is "
                            "configured). Must match at least one pattern in "
                            "url_allowlist_patterns. "
                            "Example: 'https://example-spa.com/dashboard'"
                        ),
                    },
                },
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # leid.screenshot  (v0.8.1 Mynd af Vegferð — second browser tool)
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "leid.screenshot",
            "description": (
                "Navigate to a URL in a headless Chromium browser and return a "
                "base64-encoded PNG screenshot of the rendered page. Use this when "
                "you need to see what the page looks like — layout, fonts, images, "
                "spatial arrangement, visual indicators — not just its text content. "
                "By default captures the full scrollable page (configurable via "
                "browser_screenshot_full_page). The URL must match "
                "url_allowlist_patterns. Each call uses a fresh, isolated browser "
                "context — no cookies persist. Browser is always headless. "
                "HERETIC injects no JavaScript; only the page's own scripts run. "
                "PNG byte size is capped at max_response_bytes (BEFORE base64 "
                "encoding). The result includes image_base64 (PNG bytes encoded as "
                "ASCII base64), image_format ('png'), size_bytes (raw PNG length), "
                "and full_page (echo of the config value used). Significantly more "
                "expensive than leid.fetch_url. Requires the [browser] extra "
                "(`pip install heretic[browser]` and `playwright install chromium`); "
                "returns EXTERNAL_APP_UNAVAILABLE if absent."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": (
                            "The URL to screenshot in a headless Chromium browser. "
                            "Must start with https:// (or http:// if allow_http: true). "
                            "Must match at least one pattern in url_allowlist_patterns. "
                            "Example: 'https://example.com/dashboard'"
                        ),
                    },
                },
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    },
    # ------------------------------------------------------------------
    # leid.open_session  (v0.8.2 Innan Hurðar — stateful sessions)
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "leid.open_session",
            "description": (
                "Open a stateful headless Chromium browser session at the given "
                "URL. Returns a session_id that you must use for all subsequent "
                "tool calls referring to this session (leid.session_status, "
                "leid.click, leid.close_session). The page stays alive until you "
                "explicitly close it OR until it is evicted by the idle/absolute "
                "timeout (defaults: 5 minutes idle, 30 minutes max lifetime). "
                "Each session is fully isolated — its own browser, its own "
                "context, its own cookie jar; cookies persist within a session "
                "but never across sessions. There is a configured cap on "
                "concurrent sessions (default 3); opening when at the cap "
                "returns SENSE_UNAVAILABLE. The URL must match "
                "url_allowlist_patterns. ALWAYS call leid.close_session when "
                "done — open sessions are an expensive resource. Requires the "
                "[browser] extra (`pip install heretic[browser]` and "
                "`playwright install chromium`)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": (
                            "The URL to navigate to in the new session. Must match "
                            "url_allowlist_patterns. The page stays alive after the "
                            "navigation completes. "
                            "Example: 'https://example-spa.com/dashboard'"
                        ),
                    },
                },
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # leid.session_status  (v0.8.2 Innan Hurðar)
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "leid.session_status",
            "description": (
                "Get the current state, URL, and title of an open session. This "
                "is a non-mutating health check — useful when you suspect a click "
                "may have triggered navigation, or when you want to verify a "
                "session is still alive before issuing more calls. Returns "
                "{state, url, title, opened_at, last_activity_at, age_seconds, "
                "idle_seconds}. A status check counts as activity (resets the "
                "idle timer). Returns SENSE_UNAVAILABLE if the session_id is "
                "unknown or has been evicted."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": (
                            "The session_id returned by a prior leid.open_session "
                            "call. Format: 'leid-' followed by a hex string."
                        ),
                    },
                },
                "required": ["session_id"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # leid.click  (v0.8.2 Innan Hurðar — first interactive tool)
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "leid.click",
            "description": (
                "Click the first element in the session's page that matches the "
                "given CSS selector. The click may trigger navigation, modal "
                "appearance, or any other page behaviour the page's scripts "
                "implement. Returns {selector, clicked, current_url, "
                "current_title} so you know where the page ended up. If no "
                "element matches the selector within browser_click_timeout_seconds "
                "(default 10), returns INVALID_ARGUMENTS — refine the selector "
                "and retry. If the session_id is unknown or evicted, returns "
                "SENSE_UNAVAILABLE. Network-level failures during click return "
                "EXTERNAL_APP_UNAVAILABLE. HERETIC injects no JavaScript; only "
                "the page's own scripts respond to the click event."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": (
                            "The session_id returned by a prior leid.open_session call."
                        ),
                    },
                    "selector": {
                        "type": "string",
                        "description": (
                            "CSS selector for the element to click. The first "
                            "matching element is clicked. "
                            "Examples: 'button.submit', '#login-btn', "
                            "'a[href=\"/about\"]'."
                        ),
                    },
                },
                "required": ["session_id", "selector"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # leid.type  (v0.8.2.1 Innan Hurðar extension — second half of gesture)
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "leid.type",
            "description": (
                "Fill the first element in the session's page matching the given "
                "CSS selector with the supplied text. Uses Playwright's "
                "locator.fill primitive — waits for the element to be actionable, "
                "focuses it, clears any existing value, sets the new value, then "
                "dispatches an input event. This is the canonical 'set this "
                "field's value' operation; it works for inputs, textareas, and "
                "contenteditable elements. Returns {selector, typed, current_url, "
                "current_title}. If no element matches the selector within "
                "browser_click_timeout_seconds (default 10), returns "
                "INVALID_ARGUMENTS — refine the selector and retry. Unknown "
                "session_id returns SENSE_UNAVAILABLE. Network-level browser "
                "failures return EXTERNAL_APP_UNAVAILABLE. HERETIC injects no "
                "JavaScript; the input event is dispatched by Playwright itself "
                "as part of the fill primitive."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": (
                            "The session_id returned by a prior leid.open_session call."
                        ),
                    },
                    "selector": {
                        "type": "string",
                        "description": (
                            "CSS selector for the input element to fill. The first "
                            "matching element is filled. "
                            "Examples: 'input[name=\"email\"]', '#search-box', "
                            "'textarea.comment'."
                        ),
                    },
                    "text": {
                        "type": "string",
                        "description": (
                            "The text to fill into the matched element. Replaces "
                            "any existing value. Empty string is allowed (clears "
                            "the field)."
                        ),
                    },
                },
                "required": ["session_id", "selector", "text"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # leid.navigate  (v0.8.2.2 Innan Hurðar extension — in-session navigation)
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "leid.navigate",
            "description": (
                "Navigate an open session to a new URL while keeping the "
                "session alive. The session_id, cookies, and localStorage all "
                "survive the navigation — only the page URL changes. Use this "
                "for multi-page flows: log in, then navigate to a dashboard; "
                "submit a form, then navigate to a receipt page; etc. The new "
                "URL must match url_allowlist_patterns (same gate as "
                "leid.open_session). Returns {session_id, previous_url, "
                "final_url, title} so you have a coherent record of where the "
                "session moved from and to. A navigation failure does NOT "
                "close the session — it stays open at whatever URL it was at "
                "before the failed goto, ready for retry. Unknown session_id "
                "returns SENSE_UNAVAILABLE; URL-not-allowed returns "
                "PERMISSION_DENIED; navigation timeout returns SENSE_TIMEOUT; "
                "HTTP 4xx/5xx returns SENSE_INTERNAL_ERROR; network failure "
                "returns EXTERNAL_APP_UNAVAILABLE."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": (
                            "The session_id returned by a prior leid.open_session call."
                        ),
                    },
                    "url": {
                        "type": "string",
                        "description": (
                            "The new URL to navigate to. Must start with "
                            "https:// (or http:// if allow_http: true). Must "
                            "match at least one pattern in url_allowlist_patterns. "
                            "Example: 'https://example.com/dashboard'"
                        ),
                    },
                },
                "required": ["session_id", "url"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # leid.query  (v0.8.3 Innan Hurðar extension — read-only inspection)
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "leid.query",
            "description": (
                "Read the text content (or a specified HTML attribute) of "
                "the first element in the session's page matching the given "
                "CSS selector. Returns {selector, attribute, found, value, "
                "count}. Use this to extract data from the page or to check "
                "whether something is on the page. UNLIKE leid.click and "
                "leid.type, a selector that matches NO elements is NOT an "
                "error — instead returns {found: false, count: 0, value: null}. "
                "This lets you safely check 'is this element present?' "
                "without try/except. The count field tells you how many "
                "elements matched; if you only need the first match (the "
                "default), use the value field. Set the attribute parameter "
                "to read a specific HTML attribute (e.g. 'href' on an anchor); "
                "leave it empty/omitted to read the element's text content. "
                "An element that exists but lacks the requested attribute "
                "returns {found: true, value: null, count: >=1}. Unknown "
                "session_id returns SENSE_UNAVAILABLE; browser-level failures "
                "return EXTERNAL_APP_UNAVAILABLE. HERETIC injects no "
                "JavaScript — read is via Playwright's locator primitives."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": (
                            "The session_id returned by a prior leid.open_session call."
                        ),
                    },
                    "selector": {
                        "type": "string",
                        "description": (
                            "CSS selector for the element to inspect. Only the "
                            "FIRST matching element's value is returned, but "
                            "the count field reports total matches in the DOM. "
                            "Examples: 'h1.title', '.user-name', "
                            "'a[href*=\"/about\"]', '#order-total'."
                        ),
                    },
                    "attribute": {
                        "type": "string",
                        "description": (
                            "Optional. The HTML attribute name to read. If "
                            "omitted or set to empty string, returns the "
                            "element's text content instead. Examples: 'href', "
                            "'src', 'value', 'class', 'data-id', 'aria-label'."
                        ),
                    },
                },
                "required": ["session_id", "selector"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # leid.press  (v0.8.4 Innan Hurðar extension — page-level keyboard)
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "leid.press",
            "description": (
                "Send a keyboard key (or modifier combination) to the open "
                "session's page. The press goes to whatever element currently "
                "has focus — typically established by a prior leid.click or "
                "leid.type. Use this for: submitting a form via 'Enter' after "
                "filling a search box; dismissing a modal via 'Escape'; "
                "moving focus via 'Tab' or 'Shift+Tab'; navigating dropdowns "
                "via 'ArrowDown'/'ArrowUp'. Single keys (e.g. 'Enter', "
                "'Escape', 'Tab', 'a', 'F5') and modifier combinations "
                "(e.g. 'Control+A', 'Shift+Tab', 'Meta+S') are supported per "
                "Playwright's key syntax. Returns {key, pressed, current_url, "
                "current_title} so you can detect navigation triggered by the "
                "press. Unrecognized keys produce no event but do NOT raise "
                "(consistent with Playwright's design); verify via leid.query "
                "or leid.session_status if you need to confirm effect. "
                "Unknown session_id returns SENSE_UNAVAILABLE; browser "
                "failures return EXTERNAL_APP_UNAVAILABLE."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": (
                            "The session_id returned by a prior leid.open_session call."
                        ),
                    },
                    "key": {
                        "type": "string",
                        "description": (
                            "The key or modifier+key combination to press, "
                            "in Playwright's syntax. "
                            "Examples: 'Enter', 'Tab', 'Escape', 'ArrowDown', "
                            "'F5', 'Control+A', 'Shift+Tab', 'Meta+S'."
                        ),
                    },
                },
                "required": ["session_id", "key"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # leid.close_session  (v0.8.2 Innan Hurðar — idempotent close)
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "leid.close_session",
            "description": (
                "Close an open session and release all browser resources "
                "(context, browser process, playwright runtime). Idempotent: "
                "closing an unknown or already-closed session_id returns "
                "{closed: false} rather than raising an error — safe to retry. "
                "Closing an active session returns {closed: true}. ALWAYS call "
                "this when done with a session; sessions held open consume "
                "real resources and are subject to absolute-lifetime eviction "
                "anyway."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": (
                            "The session_id to close. Idempotent if unknown or "
                            "already closed."
                        ),
                    },
                },
                "required": ["session_id"],
                "additionalProperties": False,
            },
        },
    },
]
"""The 12 OpenAI tool schemas for the Leið sense.

Tool names locked at v0.6.2:
    leid.fetch_url
    leid.extract_text

Tool name added at v0.8.0 (LOCKED):
    leid.render_url

Tool name added at v0.8.1 (LOCKED):
    leid.screenshot

Tool names added at v0.8.2 (LOCKED):
    leid.open_session
    leid.session_status
    leid.click
    leid.close_session

Tool name added at v0.8.2.1 (LOCKED):
    leid.type

Tool name added at v0.8.2.2 (LOCKED):
    leid.navigate

Tool name added at v0.8.3 (LOCKED):
    leid.query

Tool name added at v0.8.4 (LOCKED):
    leid.press
"""
