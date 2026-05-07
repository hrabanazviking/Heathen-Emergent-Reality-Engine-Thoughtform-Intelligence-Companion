"""
HERETIC CLI — command-line interface skeleton.

Commands (v0.1 scope, stubs only):
    light       — Start the ceremony: load config, open Bifröst, enter Kynding.
    extinguish  — End the ceremony: drain pending calls, close Bifröst, reach Slokna.
    status      — Report the current lifecycle state and layer health.
    version     — Print the HERETIC version string and exit.

All commands raise NotImplementedError in this skeleton. Forge will implement the bodies.

The CLI is intentionally thin. It delegates to the domain modules (grunnr, bifrost) and
does no business logic of its own — this is the boundary NAMING.md enforces: the CLI is
the voice of the user, not the intelligence of the system.
"""

from __future__ import annotations

import argparse
import sys


def _cmd_light(args: argparse.Namespace) -> int:
    """Light the candle — begin the Kynding ceremony phase.

    Loads heretic.yaml, initialises L0 Grunnr, and opens L1 Bifröst toward the
    configured agent endpoint. Transitions: Hvíld → Kynding → READY → OPENING →
    Tengsl → Samræður.

    In v0.1 this runs as a blocking CLI loop. The Tauri GUI takes over at v0.4.
    """
    raise NotImplementedError(
        "Forge will implement: cli._cmd_light — "
        "load config via grunnr.config.load_config(), "
        "initialise Lifecycle, "
        "open BifrostClient, "
        "enter the Samraedur turn loop."
    )


def _cmd_extinguish(args: argparse.Namespace) -> int:
    """Extinguish the ceremony — begin the Slokna phase.

    Drains in-flight tool calls within bifrost.drain_timeout_seconds, closes the
    Bifröst connection, zeros session state, and returns the body to Hvíld.
    """
    raise NotImplementedError(
        "Forge will implement: cli._cmd_extinguish — "
        "signal running Lifecycle instance to transition to STATE_SLOKNA, "
        "await EXTINGUISHED, confirm clean shutdown."
    )


def _cmd_status(args: argparse.Namespace) -> int:
    """Report current lifecycle state and per-layer health.

    Reads the running Holdvörðr's state (or the last known persisted state if the
    process is not running) and prints a structured summary to stdout.
    """
    raise NotImplementedError(
        "Forge will implement: cli._cmd_status — "
        "query Lifecycle.current_state(), "
        "query per-layer health flags, "
        "format and print structured status output."
    )


def _cmd_version(args: argparse.Namespace) -> int:
    """Print the HERETIC version string and exit 0."""
    import heretic
    print(heretic.__version__)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construct and return the top-level argument parser.

    The parser is built here (not at module import time) so that it can be reused
    in tests without triggering sys.exit.
    """
    parser = argparse.ArgumentParser(
        prog="heretic",
        description=(
            "H.E.R.E.T.I.C. — Host Environment for Realtime Embodiment, "
            "Tooling & Interactive Control. The body that receives the spirit."
        ),
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        default=None,
        help=(
            "Path to heretic.yaml. Overrides the default search order: "
            "$HERETIC_CONFIG → XDG config dir → home dir."
        ),
    )

    subparsers = parser.add_subparsers(dest="command", metavar="command")
    subparsers.required = True

    # light
    p_light = subparsers.add_parser(
        "light",
        help="Light the candle — begin the Kynding ceremony.",
    )
    p_light.set_defaults(func=_cmd_light)

    # extinguish
    p_extinguish = subparsers.add_parser(
        "extinguish",
        help="Extinguish the ceremony — transition to Slokna and clean shutdown.",
    )
    p_extinguish.set_defaults(func=_cmd_extinguish)

    # status
    p_status = subparsers.add_parser(
        "status",
        help="Report lifecycle state and layer health.",
    )
    p_status.set_defaults(func=_cmd_status)

    # version
    p_version = subparsers.add_parser(
        "version",
        help="Print the HERETIC version and exit.",
    )
    p_version.set_defaults(func=_cmd_version)

    return parser


def main() -> None:
    """Entry point. Parses arguments and dispatches to the appropriate command."""
    parser = build_parser()
    args = parser.parse_args()
    try:
        exit_code: int = args.func(args)
    except NotImplementedError as exc:
        # Surface Forge placeholders clearly during development.
        print(f"[HERETIC] Not yet implemented: {exc}", file=sys.stderr)
        sys.exit(2)
    sys.exit(exit_code or 0)
