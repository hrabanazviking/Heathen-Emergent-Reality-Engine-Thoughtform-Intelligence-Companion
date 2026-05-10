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
]
"""The 3 OpenAI tool schemas for the Leið sense.

Tool names locked at v0.6.2:
    leid.fetch_url
    leid.extract_text

Tool name added at v0.8.0 (LOCKED):
    leid.render_url
"""
