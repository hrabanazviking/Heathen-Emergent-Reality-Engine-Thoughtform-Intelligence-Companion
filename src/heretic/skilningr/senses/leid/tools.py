"""
Leið sense tool definitions — OpenAI tool schemas (LOCKED at v0.6.2).

LEID_TOOL_DEFINITIONS is a module-level constant. ToolDispatcher consumes
this list verbatim when building the tools array passed to the agent at TENGSL.

Tool naming: two-part format per SENSE_CONTRACTS.md §2 (sealed convention A-2).
    leid.<action>

v0.6.2 (2 tools — LOCKED):
    leid.fetch_url    — fetch raw HTTP response within URL allowlist
    leid.extract_text — fetch URL and extract plain text content

INVARIANT: do NOT rename these tools without a sense version bump.

Sandbox rule (enforced in client.py, validated in sandbox.py):
    Every URL submitted to leid.fetch_url or leid.extract_text is validated via
    sandbox.url_matches_allowlist() BEFORE any HTTP request is sent.
    HTTPS-only by default — HTTP URLs are rejected unless allow_http: true.
    No cookies. No JavaScript. No redirects beyond max_redirects.

Ref: TASK_HERETIC_v0.6.2_MORE_SENSES.md §Tools (Leið)
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
]
"""The 2 OpenAI tool schemas for the Leið sense (v0.6.2). LOCKED.

Tool names locked at v0.6.2:
    leid.fetch_url
    leid.extract_text
"""
