"""
Minni sense tool definitions — OpenAI tool schemas (LOCKED at v0.6.2).

MINNI_TOOL_DEFINITIONS is a module-level constant. ToolDispatcher consumes this
list verbatim when building the tools array passed to the agent at TENGSL.
These definitions are the authoritative schema contract between the agent and
the Minni sense.

Tool naming: two-part format per SENSE_CONTRACTS.md §2 (sealed convention A-2).
    minni.<action>

v0.6.2 (3 tools — LOCKED):
    minni.read_file          — read file content within allowed_roots
    minni.write_file         — write file content within allowed_roots
    minni.list_directory     — list directory contents within allowed_roots

INVARIANT: do NOT rename these tools without a sense version bump. Tool names
are stable identifiers for agent tool_call routing. Renaming breaks all agents
that have been trained or prompted on these tool names.

Sandbox rule (enforced in client.py, validated in sandbox.py):
    Every path argument is validated against MinniConfig.allowed_roots via
    sandbox.path_within_allowed_roots() BEFORE any filesystem I/O occurs.
    Paths outside the sandbox return a structured error — no I/O is attempted.

Ref: TASK_HERETIC_v0.6.2_MORE_SENSES.md §Tools (Minni)
     docs/architecture/SENSE_CONTRACTS.md §2 (naming convention)
     src/heretic/skilningr/senses/minni/INTERFACE.md
"""

from __future__ import annotations


MINNI_TOOL_DEFINITIONS: list[dict] = [
    # ------------------------------------------------------------------
    # minni.read_file
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "minni.read_file",
            "description": (
                "Read the full text content of a file within the configured "
                "filesystem sandbox (allowed_roots). The path must be within "
                "the sandbox — paths outside are rejected with a permission error. "
                "File content is returned as a UTF-8 string. Files larger than "
                "the configured max_read_bytes limit are rejected. "
                "Use this to inspect configuration files, source code, data files, "
                "or any text document within the agent's workspace."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Path to the file to read. May be absolute or relative "
                            "to the working directory, but MUST resolve to within "
                            "one of the configured allowed_roots. "
                            "Example: ~/heretic_workspace/notes.md"
                        ),
                    },
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # minni.write_file
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "minni.write_file",
            "description": (
                "Write text content to a file within the configured filesystem "
                "sandbox (allowed_roots). Creates the file and any missing parent "
                "directories if they do not exist. Overwrites the file if it "
                "already exists. The path must be within allowed_roots. "
                "Content larger than max_write_bytes is rejected before any "
                "write occurs. Use this to save agent output, notes, or "
                "generated files to the workspace."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Path to write. May be absolute or relative, but "
                            "MUST resolve to within one of the allowed_roots. "
                            "Parent directories are created automatically. "
                            "Example: ~/heretic_workspace/output/result.txt"
                        ),
                    },
                    "content": {
                        "type": "string",
                        "description": (
                            "Text content to write. Must be a UTF-8 string. "
                            "The file is written atomically where the OS supports it. "
                            "Existing content is replaced entirely."
                        ),
                    },
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # minni.list_directory
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "minni.list_directory",
            "description": (
                "List the contents of a directory within the configured filesystem "
                "sandbox (allowed_roots). Returns a list of entries with name, "
                "type (file or directory), and size in bytes for files. "
                "With recurse=true, returns the full directory tree. "
                "The path must be within allowed_roots. "
                "Use this to discover the structure of the workspace before "
                "reading or writing specific files."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Path to the directory to list. Must be within one of "
                            "the configured allowed_roots. "
                            "Example: ~/heretic_workspace"
                        ),
                    },
                    "recurse": {
                        "type": "boolean",
                        "description": (
                            "If true, list the directory tree recursively. "
                            "If false (default), list only the immediate contents."
                        ),
                        "default": False,
                    },
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
]
"""The 3 OpenAI tool schemas for the Minni sense (v0.6.2). LOCKED.

Tool names locked at v0.6.2:
    minni.read_file
    minni.write_file
    minni.list_directory

Do NOT alter tool names. They are stable routing identifiers per
SENSE_CONTRACTS.md §2 rule 4: renaming is a breaking change.
"""
