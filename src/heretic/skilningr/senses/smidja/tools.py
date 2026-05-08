"""
Smiðja sense tool definitions — the 6 OpenAI tool schemas for Brúarhönd primitives.

SMIDJA_TOOL_DEFINITIONS is a module-level constant. Forge consumes this list verbatim
when building the tools array passed to the agent at TENGSL. These definitions are the
authoritative schema contract between the agent and the Smiðja sense.

Tool naming: two-part format per SENSE_CONTRACTS.md §2 (sealed at v0.0 audit A-2).
    smidja.<action>

Request envelope invariant (per Brúarhönd daemon INTERFACE.md):
    Every POST to the daemon must include request_id, session_id, agent_id in the
    body. BrunhandHttpClient generates these automatically — the agent does NOT need
    to supply them. They are not exposed in the tool parameter schemas below.

API source of truth:
    C:/Users/volma/runa/Seidr-Smidja/src/seidr_smidja/brunhand/daemon/INTERFACE.md
    (Last verified: 2026-05-08, Rúnhild Svartdóttir)

IMPORTANT — discrepancies vs TASK §4 summary:
    1. vroid_open maps to POST /v1/brunhand/vroid/open_project (NOT /v1/brunhand/vroid-open)
    2. vroid_export maps to POST /v1/brunhand/vroid/export_vrm (NOT /v1/brunhand/vroid-export)
    3. Screenshot returns base64 JSON field (png_bytes_b64), not raw bytes over HTTP.
       BrunhandHttpClient.screenshot() returns the decoded bytes for the caller.
    4. The real API has additional primitives (move, drag, scroll, find_window,
       wait_for_window, vroid/save_project) not included in the initial 6-tool set.
       v0.6.1+ may add smidja.find_window, smidja.wait_for_window, smidja.save_project.

Ref: TASK_HERETIC_v0.6_HANDS_AT_FORGE.md §3 (tool naming, auth, format decisions)
     docs/architecture/SENSE_CONTRACTS.md §2 (naming convention)
     Seidr-Smidja daemon INTERFACE.md (endpoint contracts + request bodies)
"""

from __future__ import annotations


SMIDJA_TOOL_DEFINITIONS: list[dict] = [
    # ------------------------------------------------------------------
    # smidja.screenshot
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "smidja.screenshot",
            "description": (
                "Capture the full screen (or an optional region) on the Brúarhönd "
                "host machine as a PNG image. Returns the image as a base64-encoded "
                "data URL in the result. Use this to observe the current state of "
                "the desktop or VRoid Studio before issuing click/type commands."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": ["object", "null"],
                        "description": (
                            "Optional screen region to capture. "
                            "If null (default), captures the full primary monitor. "
                            "Fields: left (int), top (int), width (int), height (int) "
                            "— all in screen pixels."
                        ),
                        "properties": {
                            "left":   {"type": "integer", "description": "Left edge x-coordinate"},
                            "top":    {"type": "integer", "description": "Top edge y-coordinate"},
                            "width":  {"type": "integer", "description": "Region width in pixels"},
                            "height": {"type": "integer", "description": "Region height in pixels"},
                        },
                        "required": ["left", "top", "width", "height"],
                        "additionalProperties": False,
                        "default": None,
                    },
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # smidja.click
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "smidja.click",
            "description": (
                "Click a mouse button at the specified screen coordinates on the "
                "Brúarhönd host. Use this to press UI buttons, select menu items, "
                "focus fields, or navigate VRoid Studio's interface."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": "Screen X coordinate to click (pixels from left edge).",
                    },
                    "y": {
                        "type": "integer",
                        "description": "Screen Y coordinate to click (pixels from top edge).",
                    },
                    "button": {
                        "type": "string",
                        "enum": ["left", "right", "middle"],
                        "description": "Mouse button to press. Default: left.",
                        "default": "left",
                    },
                    "clicks": {
                        "type": "integer",
                        "description": "Number of clicks to deliver. 2 for double-click. Default: 1.",
                        "default": 1,
                        "minimum": 1,
                    },
                    "modifiers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Modifier keys held during the click. "
                            "Examples: ['shift'], ['ctrl', 'shift']. Default: []."
                        ),
                        "default": [],
                    },
                },
                "required": ["x", "y"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # smidja.type_text
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "smidja.type_text",
            "description": (
                "Type a string of text into the currently-focused field on the "
                "Brúarhönd host. Unicode is supported. Use click first to focus "
                "the target input field before calling type_text."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to type. Unicode supported.",
                    },
                    "interval": {
                        "type": "number",
                        "description": (
                            "Seconds between keystrokes. Slower values are more reliable "
                            "for applications that process key events individually. Default: 0.05."
                        ),
                        "default": 0.05,
                        "minimum": 0.0,
                    },
                },
                "required": ["text"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # smidja.hotkey
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "smidja.hotkey",
            "description": (
                "Press a key combination simultaneously on the Brúarhönd host. "
                "All keys are pressed at once and released together. Use this to "
                "trigger menu shortcuts (e.g. Ctrl+S to save) or VRoid Studio "
                "hotkeys. Keys are PyAutoGUI key name strings."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Ordered list of PyAutoGUI key names to press simultaneously. "
                            "Examples: ['ctrl', 's'] to save, ['alt', 'f4'] to close window, "
                            "['enter'] to confirm a dialog."
                        ),
                        "minItems": 1,
                    },
                },
                "required": ["keys"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # smidja.vroid_open
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "smidja.vroid_open",
            "description": (
                "Open a .vroid project file in VRoid Studio on the Brúarhönd host. "
                "The path is relative to the daemon's configured project_root — "
                "never an absolute path. The tool drives VRoid Studio's File > Open "
                "dialog and waits for the project to load."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": (
                            "Relative path to the .vroid file on the daemon host. "
                            "Relative to daemon's brunhand.daemon.project_root. "
                            "Example: characters/my_character.vroid"
                        ),
                    },
                    "wait_timeout_seconds": {
                        "type": "number",
                        "description": (
                            "Maximum seconds to wait for VRoid Studio to load the project. "
                            "Default: 60. Increase for large or complex projects."
                        ),
                        "default": 60.0,
                        "minimum": 1.0,
                    },
                },
                "required": ["project_path"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # smidja.vroid_export
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "smidja.vroid_export",
            "description": (
                "Export the currently-open VRoid Studio project as a .vrm file on "
                "the Brúarhönd host. The output path is relative to the daemon's "
                "configured export_root. The tool drives VRoid Studio's "
                "File > Export > Export VRM dialog and waits for completion."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "output_path": {
                        "type": "string",
                        "description": (
                            "Relative path where the .vrm file should be written on the "
                            "daemon host. Relative to daemon's brunhand.daemon.export_root. "
                            "Example: exports/my_avatar.vrm"
                        ),
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": (
                            "Whether to confirm overwrite if the output file already exists. "
                            "Default: true."
                        ),
                        "default": True,
                    },
                    "wait_timeout_seconds": {
                        "type": "number",
                        "description": (
                            "Maximum seconds to wait for the export dialog to appear and "
                            "the export to complete. Default: 120. Large models may need more."
                        ),
                        "default": 120.0,
                        "minimum": 1.0,
                    },
                },
                "required": ["output_path"],
                "additionalProperties": False,
            },
        },
    },
]
"""The 6 OpenAI tool schemas for the Smiðja sense (Brúarhönd v0.1 surface).

Forge consumes this list verbatim. Do NOT alter tool names — they are stable
identifiers (per SENSE_CONTRACTS.md §2 rule 4: renaming is a breaking change).

Tool names locked at v0.6.0:
    smidja.screenshot
    smidja.click
    smidja.type_text     (note: Python builtin 'type' avoided; two-word action name)
    smidja.hotkey
    smidja.vroid_open
    smidja.vroid_export

v0.6.1+ candidate additions (from real API surface, not in v0.6.0 scope):
    smidja.find_window
    smidja.wait_for_window
    smidja.save_project
    smidja.move
    smidja.drag
    smidja.scroll
"""
