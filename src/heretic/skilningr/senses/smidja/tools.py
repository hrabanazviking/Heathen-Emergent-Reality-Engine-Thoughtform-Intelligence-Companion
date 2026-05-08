"""
Smiðja sense tool definitions — OpenAI tool schemas for both Smiðja halves.

SMIDJA_TOOL_DEFINITIONS is a module-level constant. Forge consumes this list verbatim
when building the tools array passed to the agent at TENGSL. These definitions are the
authoritative schema contract between the agent and the Smiðja sense.

Tool naming: two-part format per SENSE_CONTRACTS.md §2 (sealed at v0.0 audit A-2).
    smidja.<action>

v0.6.0 (Brúarhönd half — 6 tools):
    smidja.screenshot, smidja.click, smidja.type_text,
    smidja.hotkey, smidja.vroid_open, smidja.vroid_export

v0.6.1 (Forge half — 3 new tools; exposed only when ForgeConfig.enabled=True):
    smidja.forge_build_avatar, smidja.forge_get_avatar, smidja.forge_inspect_avatar

ROUTING RULE (implemented in SmidjaSense._route):
    Tools whose action starts with "forge_" are routed to ForgeHttpClient.
    All other smidja.* tools are routed to BrunhandHttpClient (Brúarhönd).
    This rule is determined by the action part (everything after "smidja."):
        "smidja.screenshot"          → BrunhandHttpClient (action = "screenshot")
        "smidja.forge_build_avatar"  → ForgeHttpClient    (action starts with "forge_")
    SmidjaSense.tool_definitions returns both halves when both are enabled;
    if only one half is enabled, only that half's tools are included.

Brúarhönd request envelope invariant:
    Every POST to the Brúarhönd daemon must include request_id, session_id, agent_id.
    BrunhandHttpClient generates these automatically — the agent does NOT supply them.
    The Forge (Straumur) API does NOT use a request envelope.

API sources of truth:
    Brúarhönd: Seidr-Smidja/src/seidr_smidja/brunhand/daemon/INTERFACE.md
    Straumur:  Seidr-Smidja/src/seidr_smidja/bridges/straumur/api.py
    (Both verified 2026-05-08, Rúnhild Svartdóttir)

IMPORTANT — discrepancies vs TASK §4 (Brúarhönd half):
    1. vroid_open maps to POST /v1/brunhand/vroid/open_project (NOT /v1/brunhand/vroid-open)
    2. vroid_export maps to POST /v1/brunhand/vroid/export_vrm (NOT /v1/brunhand/vroid-export)
    3. Screenshot returns base64 JSON field (png_bytes_b64), not raw bytes over HTTP.
    4. The real API has additional primitives not in v0.6.0 scope.

IMPORTANT — discrepancies vs TASK §4 (Straumur / Forge half):
    1. Health endpoint is /v1/health (NOT /health — lives under /v1/).
    2. GET /v1/avatars/{id} returns the full Annáll session record, NOT avatar metadata.
       The {id} is a session_id (uuid4). See ForgeHttpClient.get_avatar() docstring.
    3. POST /v1/inspect takes {vrm_path, targets} NOT an avatar_id.
    4. Straumur has no bearer-token auth on localhost (H-005).

Ref: TASK_HERETIC_v0.6_HANDS_AT_FORGE.md §3
     TASK_HERETIC_v0.6.1_FORGE_DISPATCH.md §3
     docs/architecture/SENSE_CONTRACTS.md §2 (naming convention)
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

    # ------------------------------------------------------------------
    # smidja.forge_build_avatar  [v0.6.1 — Forge half]
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "smidja.forge_build_avatar",
            "description": (
                "Build a VRM avatar using the Seidr-Smidja headless Blender pipeline "
                "(Straumur REST bridge). Submits a Loom spec JSON to the forge, "
                "which runs Blender non-interactively to produce a .vrm output. "
                "This is a SLOW operation — expect 60–120 seconds for a standard build. "
                "It is NOT real-time GUI control (use smidja.screenshot/click for that). "
                "Returns a session_id, vrm_path, render_paths, compliance_passed, "
                "elapsed_seconds, and any errors. Use smidja.forge_get_avatar to "
                "retrieve the full session record after the build completes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "loom_spec": {
                        "type": "object",
                        "description": (
                            "Full Loom spec as a JSON object. Must include at minimum "
                            "base_asset_id (string identifying the VRoid base asset in "
                            "the Hoard). Additional fields per the Loom domain schema. "
                            "Example: {\"base_asset_id\": \"vroid_base_v1\", "
                            "\"name\": \"MyAvatar\"}. "
                            "The agent is responsible for providing a valid Loom spec — "
                            "no validation is performed before submission."
                        ),
                        "additionalProperties": True,
                    },
                },
                "required": ["loom_spec"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # smidja.forge_get_avatar  [v0.6.1 — Forge half]
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "smidja.forge_get_avatar",
            "description": (
                "Retrieve the full Annáll session record for a prior Forge build. "
                "The session_id comes from the smidja.forge_build_avatar response. "
                "Returns the complete audit record including agent_id, bridge_type, "
                "started_at, ended_at, success, summary, and the full event log. "
                "Use this to inspect the detailed outcome of a slow Blender build, "
                "check event-level diagnostics, or confirm a build succeeded."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "avatar_id": {
                        "type": "string",
                        "description": (
                            "The session_id (uuid4 string) returned in the "
                            "smidja.forge_build_avatar response under the key 'session_id'. "
                            "This is the Annáll session identifier for the build. "
                            "Example: \"3f2b7a1e-1234-5678-abcd-ef0123456789\""
                        ),
                    },
                },
                "required": ["avatar_id"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # smidja.forge_inspect_avatar  [v0.6.1 — Forge half]
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "smidja.forge_inspect_avatar",
            "description": (
                "Run a Gate compliance check on a .vrm file on the Seidr-Smidja "
                "Straumur server. This is a headless Blender Gate check — slower "
                "than a simple schema validation but authoritative. "
                "The vrm_path must be a server-side path to a .vrm file within "
                "Straumur's allowed directories (output/ or data/hoard/bases/). "
                "Returns passed, targets_checked, elapsed_seconds, and per-target "
                "results with violation details (rule_id, severity, description). "
                "Use this to verify a built avatar meets VRChat or VTube Studio "
                "compliance requirements before distribution."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "avatar_id": {
                        "type": "string",
                        "description": (
                            "Server-side path to the .vrm file to inspect. "
                            "Must be a .vrm file (by extension) and must be within "
                            "the Straumur server's allowed output or hoard directories. "
                            "Paths outside the allow-list will be rejected with an error. "
                            "Example: \"output/my_avatar_abc123.vrm\""
                        ),
                    },
                },
                "required": ["avatar_id"],
                "additionalProperties": False,
            },
        },
    },
]
"""The 9 OpenAI tool schemas for the Smiðja sense (v0.6.1).

v0.6.0 Brúarhönd half (6 tools) + v0.6.1 Forge half (3 tools) = 9 total.

Forge consumes this list verbatim. Do NOT alter tool names — they are stable
identifiers (per SENSE_CONTRACTS.md §2 rule 4: renaming is a breaking change).

Tool names locked at v0.6.0 (Brúarhönd half):
    smidja.screenshot
    smidja.click
    smidja.type_text     (note: Python builtin 'type' avoided; two-word action name)
    smidja.hotkey
    smidja.vroid_open
    smidja.vroid_export

Tool names locked at v0.6.1 (Forge half):
    smidja.forge_build_avatar
    smidja.forge_get_avatar
    smidja.forge_inspect_avatar

Routing rule: tools whose action starts with "forge_" → ForgeHttpClient.
              all other smidja.* tools → BrunhandHttpClient (Brúarhönd).

v0.6.1+ candidate additions (Brúarhönd real API surface, not in v0.6.x scope):
    smidja.find_window
    smidja.wait_for_window
    smidja.save_project
    smidja.move
    smidja.drag
    smidja.scroll
"""
