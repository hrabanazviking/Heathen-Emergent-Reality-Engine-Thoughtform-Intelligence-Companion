"""
Skepja sense tool definitions — OpenAI tool schemas (LOCKED at v0.6.2).

SKEPJA_TOOL_DEFINITIONS is a module-level constant. ToolDispatcher consumes
this list verbatim when building the tools array passed to the agent at TENGSL.

Tool naming: two-part format per SENSE_CONTRACTS.md §2 (sealed convention A-2).
    skepja.<action>

v0.6.2 (2 tools — LOCKED):
    skepja.run_command           — execute an allowlisted shell command
    skepja.get_working_directory — return the configured working directory

INVARIANT: do NOT rename these tools without a sense version bump.

Sandbox rule (enforced in client.py, validated in sandbox.py):
    Every command submitted to skepja.run_command is validated via
    sandbox.command_in_allowlist() BEFORE subprocess.run() is called.
    shell=False is invariant in client.py — commands are never passed to a shell.

Ref: TASK_HERETIC_v0.6.2_MORE_SENSES.md §Tools (Skepja)
     docs/architecture/SENSE_CONTRACTS.md §2 (naming convention)
     src/heretic/skilningr/senses/skepja/INTERFACE.md
"""

from __future__ import annotations


SKEPJA_TOOL_DEFINITIONS: list[dict] = [
    # ------------------------------------------------------------------
    # skepja.run_command
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "skepja.run_command",
            "description": (
                "Execute a shell command within the configured sandbox. "
                "The command's executable must be in the operator-defined "
                "command_allowlist — commands not on the list are rejected "
                "before execution. The command runs as a fresh subprocess "
                "(no persistent shell session) in the configured working_directory, "
                "with a timeout enforced. Returns stdout, stderr, and exit code. "
                "Output is truncated at the configured max_output_bytes limit. "
                "Use this to run build tools, tests, scripts, or other approved "
                "executables within the agent's workspace."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": (
                            "The command to execute, as a single string. "
                            "The executable (first token) must be in the "
                            "configured command_allowlist. The command is split "
                            "via shlex and executed with shell=False — shell "
                            "metacharacters (pipes, redirects) are NOT interpreted. "
                            "Example: 'git status' or 'python -m pytest tests/'"
                        ),
                    },
                },
                "required": ["command"],
                "additionalProperties": False,
            },
        },
    },

    # ------------------------------------------------------------------
    # skepja.get_working_directory
    # ------------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "skepja.get_working_directory",
            "description": (
                "Return the resolved absolute path of the working directory "
                "where all Skepja commands execute. This is the value of "
                "SkepjaConfig.working_directory (default: ~/heretic_workspace), "
                "resolved to an absolute path. Use this to confirm the base "
                "directory before running commands that produce file output."
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
"""The 2 OpenAI tool schemas for the Skepja sense (v0.6.2). LOCKED.

Tool names locked at v0.6.2:
    skepja.run_command
    skepja.get_working_directory
"""
