"""
Library sense tool definitions — OpenAI tool schemas (LOCKED at v0.7).

LIBRARY_TOOL_DEFINITIONS is a module-level constant. ToolDispatcher
consumes this list verbatim when building the tools array passed to the
agent at TENGSL. These definitions are the authoritative schema contract
between the agent and the Library sense.

Tool naming: two-part format per SENSE_CONTRACTS.md §2 (sealed convention A-2).
    library.<action>

v0.7 (3 tools — LOCKED):
    library.search          — keyword search over downloaded corpus
    library.get_text        — retrieve a line range from a source
    library.list_sources    — list available sources with download status

INVARIANT: do NOT rename these tools without a sense version bump.
Tool names are stable identifiers for agent tool_call routing. Renaming
breaks all agents that have been trained or prompted on these tool names.

Ref: TASK_HERETIC_v0.7_MIMISBRUNNR.md §Tools
     docs/architecture/SENSE_CONTRACTS.md §2 (naming convention)
     src/heretic/skilningr/senses/library/INTERFACE.md
"""

from __future__ import annotations


LIBRARY_TOOL_DEFINITIONS: list[dict] = [
    # ------------------------------------------------------------------
    # library.search
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "library.search",
            "description": (
                "Search the Mímisbrunnr Norse text corpus for lines matching "
                "a keyword or phrase. The corpus consists of public-domain "
                "Norse sagas, Eddas, and related texts. "
                "Returns up to max_results matching excerpts with source "
                "attribution and line numbers. "
                "The search is case-insensitive substring matching — no stemming "
                "or semantic expansion. Use specific proper nouns, character names, "
                "or poetic phrases for best results. "
                "If no index has been built yet (no sources downloaded), the tool "
                "returns an error — use library.list_sources to check download status."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "The search string. Case-insensitive substring match. "
                            "Examples: 'Odin', 'Yggdrasil', 'shield-maiden', "
                            "'the world-tree'. Leading and trailing whitespace "
                            "is stripped before matching."
                        ),
                    },
                    "max_results": {
                        "type": "integer",
                        "description": (
                            "Maximum number of search results to return. "
                            "Default 20. Must be between 1 and 100. "
                            "Higher values provide broader coverage but "
                            "consume more agent context window."
                        ),
                        "default": 20,
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # library.get_text
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "library.get_text",
            "description": (
                "Retrieve a specific range of lines from a downloaded Norse "
                "text source. Use library.list_sources to find valid source_ids "
                "and to confirm a source has been downloaded. "
                "Use library.search to find the line numbers that are relevant "
                "before calling this tool. "
                "Returns the raw plain-text content of the requested lines."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "source_id": {
                        "type": "string",
                        "description": (
                            "The stable identifier of the source to read. "
                            "Must be one of the ids returned by library.list_sources. "
                            "Examples: 'prose_edda_brodeur', 'poetic_edda_bellows', "
                            "'heimskringla_laing', 'volsunga_saga_morris', "
                            "'erik_red_saga'."
                        ),
                    },
                    "start_line": {
                        "type": "integer",
                        "description": (
                            "1-based line number of the first line to retrieve. "
                            "Default 1 (start of file). Must be >= 1."
                        ),
                        "default": 1,
                    },
                    "num_lines": {
                        "type": "integer",
                        "description": (
                            "Number of lines to retrieve starting from start_line. "
                            "Default 50. Must be between 1 and 500. "
                            "At end of file, fewer lines may be returned."
                        ),
                        "default": 50,
                    },
                },
                "required": ["source_id"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # library.list_sources
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "library.list_sources",
            "description": (
                "List all available sources in the Mímisbrunnr Norse corpus. "
                "Returns the complete list of sources from the starter pack "
                "with their titles, download status, and expected sizes. "
                "Use this tool first to determine which sources are available "
                "locally before calling library.search or library.get_text. "
                "If a source shows downloaded=false, it must be fetched by the "
                "operator using the 'heretic library download' CLI command before "
                "the agent can access its content."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
]
"""The 3 OpenAI tool schemas for the Library sense (v0.7). LOCKED.

Tool names locked at v0.7:
    library.search
    library.get_text
    library.list_sources

Do NOT alter tool names. They are stable routing identifiers per
SENSE_CONTRACTS.md §2 rule 4: renaming is a breaking change.
"""
