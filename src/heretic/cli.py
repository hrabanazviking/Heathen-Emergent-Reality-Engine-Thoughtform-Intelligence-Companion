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
import asyncio
import sys
from pathlib import Path


async def _async_light(args: argparse.Namespace) -> int:
    """Async implementation of the `light` command — runs the ceremony turn loop."""
    from heretic.grunnr.config import load_config, ConfigLoadError
    from heretic.grunnr.logger import configure_logging, get_logger
    from heretic.grunnr.lifecycle import Lifecycle, LifecycleState
    from heretic.bifrost.client import OpenAICompatClient
    from heretic.bifrost.config_model import BifrostConfig, TailscaleOptions
    from heretic.bifrost.errors import BifrostError
    from heretic.rodd.chatterbox import ChatterboxHttpClient
    from heretic.rodd.config_model import RoddConfig, RoddTtsConfig, RoddSttConfig
    from heretic.rodd.hlust import Hlust
    from heretic.rodd.microphone import MicrophoneCapture
    from heretic.rodd.playback import AudioPlayback
    from heretic.rodd.tunga import Tunga
    from heretic.rodd.vad import VadDetector
    from heretic.rodd.whisper_engine import WhisperEngine

    # --- Kynding: load config and configure logging ---
    try:
        cfg = load_config(args.config)
    except ConfigLoadError as exc:
        print(f"[HERETIC] Config error: {exc}", file=sys.stderr)
        return 1

    configure_logging(cfg.grunnr.log_level, cfg.grunnr.log_file)
    log = get_logger("heretic.cli")

    lc = Lifecycle()
    lc.transition(LifecycleState.KYNDING)
    lc.transition(LifecycleState.READY)

    # Build BifrostConfig from the hydrated grunnr config
    # The grunnr BifrostConfig and bifrost.config_model.BifrostConfig mirror each other;
    # we bridge them here in the CLI so neither layer imports the other directly.
    grunnr_bf = cfg.bifrost
    bf_config = BifrostConfig(
        endpoint=grunnr_bf.endpoint,
        api_key=grunnr_bf.api_key,
        model=grunnr_bf.model,
        timeout_seconds=grunnr_bf.timeout_seconds,
        stream_timeout_seconds=grunnr_bf.stream_timeout_seconds,
        connect_timeout_seconds=grunnr_bf.connect_timeout_seconds,
        max_retries=grunnr_bf.max_retries,
        backoff_seconds=list(grunnr_bf.backoff_seconds),
        heartbeat_interval_seconds=grunnr_bf.heartbeat_interval_seconds,
        heartbeat_miss_threshold=grunnr_bf.heartbeat_miss_threshold,
        heartbeat_enabled=grunnr_bf.heartbeat_enabled,
        stream=grunnr_bf.stream,
        max_tokens=grunnr_bf.max_tokens,
        max_parallel_tool_calls=grunnr_bf.max_parallel_tool_calls,
        max_tool_call_rounds=grunnr_bf.max_tool_call_rounds,
        drain_timeout_seconds=grunnr_bf.drain_timeout_seconds,
        input_queue_depth=grunnr_bf.input_queue_depth,
        inject_context_on_connect=grunnr_bf.inject_context_on_connect,
        tailscale=TailscaleOptions(
            prefer=grunnr_bf.tailscale.prefer,
            fallback_to_direct=grunnr_bf.tailscale.fallback_to_direct,
        ),
        vision_in=grunnr_bf.vision_in,
    )

    client = OpenAICompatClient(bf_config)

    # --- Opening: connect Bifröst ---
    lc.transition(LifecycleState.OPENING)
    try:
        await client.open()
    except BifrostError as exc:
        if not args.debug:
            print(f"\n[HERETIC] Connection failed: {exc}", file=sys.stderr)
        else:
            import traceback
            traceback.print_exc()
        lc.transition(LifecycleState.READY)
        return 1

    lc.transition(LifecycleState.TENGSL)

    # --- Tunga: initialise TTS voice if enabled ---
    # Build a full RoddTtsConfig bridging from the grunnr-layer config snapshot.
    # This mirrors the BifrostConfig bridge above — neither layer reads heretic.yaml
    # directly; the CLI wires the grunnr config snapshot into each layer's typed config.
    tunga: Tunga | None = None
    rodd_tts_config: RoddTtsConfig = RoddTtsConfig()  # default; overwritten if TTS enabled
    grunnr_rodd = cfg.rodd
    grunnr_tts = grunnr_rodd.tts
    if grunnr_tts.enabled:
        try:
            # Build the full RoddTtsConfig from the grunnr snapshot values.
            # The grunnr RoddTtsConfig is a lightweight stub; the rodd module's version
            # carries the full synthesis parameters. We copy what grunnr knows and fill
            # the rest with defaults from the canonical rodd config_model.
            rodd_tts_config = RoddTtsConfig(
                enabled=grunnr_tts.enabled,
                engine=grunnr_tts.engine,
                endpoint=grunnr_tts.endpoint,
                voice_id=grunnr_tts.voice_id,
                device=grunnr_tts.device,
                speed=grunnr_tts.speed,
            )
            rodd_config = RoddConfig(tts=rodd_tts_config)
            tts_client = ChatterboxHttpClient(rodd_tts_config, log)
            playback_backend = AudioPlayback.best_available(rodd_tts_config, log)
            tunga = Tunga(rodd_config, tts_client, playback_backend, log)
            await tunga.open()
        except Exception as exc:
            log.warning(
                "Tunga init failed — ceremony continues text-only: %s", exc
            )
            tunga = None

    # --- Hlust: initialise STT voice input if enabled ---
    # Constructed after Tunga; errors here are non-fatal — CLI falls back to stdin.
    hlust: Hlust | None = None
    grunnr_stt = grunnr_rodd.stt
    if grunnr_stt.enabled:
        try:
            rodd_stt_config = RoddSttConfig(
                enabled=grunnr_stt.enabled,
                engine=grunnr_stt.engine,
                model_path=grunnr_stt.model_path,
                device=grunnr_stt.device,
                vad_threshold=grunnr_stt.vad_threshold,
                language=grunnr_stt.language,
                load_strategy=grunnr_stt.load_strategy,
            )
            # Build RoddConfig with the STT config merged in (TTS already built above
            # if tunga is live; if tunga failed, use a default TTS config here).
            rodd_stt_full_config = RoddConfig(
                tts=rodd_tts_config if tunga is not None else RoddTtsConfig(),
                stt=rodd_stt_config,
            )
            mic_backend = MicrophoneCapture.best_available(rodd_stt_config.device, log)
            vad_backend = VadDetector.best_available(rodd_stt_config, log)
            whisper_backend = WhisperEngine.best_available(rodd_stt_config, log)
            hlust = Hlust(
                config=rodd_stt_full_config,
                mic=mic_backend,
                vad=vad_backend,
                engine=whisper_backend,
                logger=log,
            )
            await hlust.open()
            if not hlust.is_available:
                log.warning(
                    "Hlust init succeeded but is_available=False — "
                    "no real mic/Whisper backend found. Falling back to stdin."
                )
                hlust = None
        except Exception as exc:
            log.warning("Hlust init failed — ceremony continues text-only: %s", exc)
            hlust = None

    print(
        f"[HERETIC] Bifrost open - connected to {bf_config.endpoint} "
        f"(model: {bf_config.model})",
        file=sys.stderr,
    )
    print(
        f"[HERETIC] Capabilities: tool_use={client.capability_tool_use} "
        f"vision_in={client.capability_vision_in} streaming={client.capability_streaming}",
        file=sys.stderr,
    )
    print("[HERETIC] Enter Samraedur - type your message and press Enter.", file=sys.stderr)
    print("[HERETIC] Type /quit or press Ctrl+C to extinguish.", file=sys.stderr)

    # --- Samræður: turn loop ---
    lc.transition(LifecycleState.SAMRAEDUR)
    messages: list[dict] = []

    try:
        while True:
            # Read user input — voice (Hlust) if available and stdin is a TTY,
            # otherwise fall back to stdin readline (scriptable path).
            try:
                if hlust is not None and hlust.is_available and sys.stdin.isatty():
                    # Voice input path: Hlust captures utterance via mic + VAD + Whisper
                    try:
                        line = await hlust.capture_one_utterance()
                    except Exception as exc:
                        log.warning(
                            "Hlust capture_one_utterance failed: %s; falling back to stdin",
                            exc,
                        )
                        print("you> ", end="", flush=True)
                        line = await asyncio.get_running_loop().run_in_executor(
                            None, sys.stdin.readline
                        )
                    else:
                        # Echo what was heard so the user can confirm before it sends
                        if line:
                            print(f"you> {line}", flush=True)
                else:
                    # Stdin path: scripted input or voice disabled/unavailable
                    print("you> ", end="", flush=True)
                    line = await asyncio.get_running_loop().run_in_executor(
                        None, sys.stdin.readline
                    )
            except (EOFError, KeyboardInterrupt):
                break

            user_text = line.rstrip("\n").rstrip("\r\n")
            if not user_text:
                continue
            if user_text.strip().lower() == "/quit":
                break

            messages.append({"role": "user", "content": [{"type": "text", "text": user_text}]})

            # Stream the response
            print("agent> ", end="", flush=True)
            assistant_text = ""
            try:
                async for chunk in client.send_message(messages):
                    # Text chunks are printed directly; tool call JSON goes to log
                    if chunk.startswith("{") and '"type": "tool_call"' in chunk:
                        log.info("Tool call: %s", chunk)
                    else:
                        print(chunk, end="", flush=True)
                        assistant_text += chunk
                        # Feed each streaming text delta into Tunga's sentence chunker.
                        # Tunga accumulates until a sentence boundary + min_chars fires,
                        # then synthesises and plays. Degraded Tunga silently no-ops.
                        if tunga is not None and not tunga.is_degraded:
                            try:
                                await tunga.feed_chunk(chunk)
                            except Exception as exc:
                                log.warning("Tunga.feed_chunk error (ignored): %s", exc)
            except BifrostError as exc:
                print(f"\n[HERETIC] Error: {exc}", file=sys.stderr)
                if args.debug:
                    import traceback
                    traceback.print_exc()
            print()  # newline after streamed response

            # Flush any remaining buffered speech at end of agent turn
            if tunga is not None and not tunga.is_degraded:
                try:
                    await tunga.flush()
                except Exception as exc:
                    log.warning("Tunga.flush error (ignored): %s", exc)

            if assistant_text:
                messages.append({"role": "assistant", "content": assistant_text})

    except KeyboardInterrupt:
        pass

    # --- Slokna: clean shutdown ---
    print("\n[HERETIC] Extinguishing the ceremony...", file=sys.stderr)
    lc.transition(LifecycleState.SLOKNA)

    # Close Hlust first — stop mic capture before we close TTS
    if hlust is not None:
        try:
            await hlust.close()
        except Exception as exc:
            log.warning("Error closing Hlust: %s", exc)

    # Close Tunga — flush and speak any final buffered words before silence
    if tunga is not None:
        try:
            await tunga.close()
        except Exception as exc:
            log.warning("Error closing Tunga: %s", exc)

    try:
        await client.close()
    except Exception as exc:
        log.warning("Error during close: %s", exc)
    lc.transition(LifecycleState.EXTINGUISHED)
    print("[HERETIC] Ceremony ended. Hvíld.", file=sys.stderr)
    return 0


def _cmd_light(args: argparse.Namespace) -> int:
    """Light the candle — begin the Kynding ceremony phase.

    Loads heretic.yaml, initialises L0 Grunnr, and opens L1 Bifröst toward the
    configured agent endpoint. Transitions: Hvild -> Kynding -> READY -> OPENING ->
    Tengsl -> Samraedur.

    In v0.1 this runs as a blocking CLI loop. The Tauri GUI takes over at v0.4.
    """
    return asyncio.run(_async_light(args))


def _cmd_extinguish(args: argparse.Namespace) -> int:
    """Extinguish the ceremony — begin the Slokna phase.

    In v0.1, `light` owns its own lifecycle — each invocation creates and destroys
    its own Lifecycle + BifrostClient. There is no running background daemon to signal.
    Use Ctrl+C or /quit inside `light` to extinguish the ceremony cleanly.

    Note: in v0.4+ when the Tauri daemon runs as a persistent process, `extinguish`
    will signal the running Holdvörðr via IPC to begin Slokna.
    """
    print(
        "[HERETIC] extinguish: no running ceremony detected.\n"
        "          In v0.1, use /quit or Ctrl+C inside 'heretic light' to end the ceremony.\n"
        "          (Persistent daemon mode arrives at v0.4 with the Tauri UI.)",
        file=sys.stderr,
    )
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    """Report current lifecycle state and per-layer health.

    In v0.1, there is no persistent daemon process — each `light` invocation owns
    its own lifecycle instance. Calling `status` outside a running ceremony always
    reports HVILD (rest state).

    Note: In v0.4+ with the Tauri daemon, `status` will query the running Holdvörðr
    process via IPC and report live state.
    """
    from heretic.grunnr.config import load_config, ConfigLoadError

    # Attempt to load config to confirm HERETIC is configured at all
    config_ok = False
    config_path = "unknown"
    try:
        cfg = load_config(args.config)
        config_ok = True
        config_path = str(cfg.bifrost.endpoint)
    except ConfigLoadError as exc:
        config_path = str(exc)

    print("[HERETIC] Status")
    print(f"  Version:       {_get_version()}")
    print(f"  Lifecycle:     HVILD (rest - no ceremony active)")
    print(f"  Config OK:     {config_ok}")
    if config_ok:
        print(f"  Agent:         {config_path}")
    else:
        print(f"  Config error:  {config_path}")
    print(
        "  Note: v0.1 has no persistent daemon. "
        "Start a ceremony with: heretic light"
    )
    return 0


def _get_version() -> str:
    """Return the HERETIC version string."""
    import heretic
    return heretic.__version__


def _cmd_version(args: argparse.Namespace) -> int:
    """Print the HERETIC version string and exit 0."""
    print(_get_version())
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    """Start the L4 Vébond WebSocket and REST server (the Summoning Circle backend).

    Loads heretic.yaml (or the config at --config PATH), applies any CLI overrides
    for --port and --host, then binds a FastAPI + uvicorn WebSocket server at
    ws://<host>:<port>/ws and a REST health endpoint at http://<host>:<port>/health.

    The server integrates with the existing Lifecycle state machine and the
    L1 Bifröst / L2 Rödd / L3 Sjón layers via the EventBus. The React frontend
    (frontend/) connects to this server and sends LightCommand / ExtinguishCommand /
    SendMessageCommand / CancelTurnCommand / ToggleSenseCommand; the server pushes
    back CeremonyStateChanged / BifrostHealth / TungaActivity / HlustActivity /
    AgentToken / AgentTurnComplete / ErrorEvent.

    Default bind: ws://127.0.0.1:8642/ws  (loopback; configurable via heretic.yaml
    vebond.ws_port and vebond.ws_host — see docs/architecture/IPC_PROTOCOL.md).

    Usage:
        heretic serve
        heretic serve --port 8643
        heretic serve --host 0.0.0.0 --port 8643  (requires allow_remote_bind: true)
        heretic serve --config /path/to/heretic.yaml
    """
    raise NotImplementedError(
        "Forge will implement: load config, apply --port/--host CLI overrides to "
        "VebondConfig, construct EventBus and WebSocketServer, integrate with the "
        "Lifecycle / Bifrost / Tunga / Hlust layers via EventBus subscriptions, "
        "then call asyncio.run(server.start()) and keep the event loop alive. "
        "See src/heretic/vebond/serve.py for the WebSocketServer skeleton. "
        "See docs/architecture/IPC_PROTOCOL.md for the full event/command schema."
    )


def build_parser() -> argparse.ArgumentParser:
    """Construct and return the top-level argument parser.

    The parser is built here (not at module import time) so that it can be reused
    in tests without triggering sys.exit.
    """
    parser = argparse.ArgumentParser(
        prog="heretic",
        description=(
            "H.E.R.E.T.I.C. - Host Environment for Realtime Embodiment, "
            "Tooling & Interactive Control. The body that receives the spirit."
        ),
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        default=None,
        help=(
            "Path to heretic.yaml. Overrides the default search order: "
            "$HERETIC_CONFIG -> XDG config dir -> home dir."
        ),
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Show full tracebacks on errors instead of surfacing only the message.",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="command")
    subparsers.required = True

    # light
    p_light = subparsers.add_parser(
        "light",
        help="Light the candle - begin the Kynding ceremony.",
    )
    p_light.set_defaults(func=_cmd_light)

    # extinguish
    p_extinguish = subparsers.add_parser(
        "extinguish",
        help="Extinguish the ceremony - transition to Slokna and clean shutdown.",
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

    # serve
    p_serve = subparsers.add_parser(
        "serve",
        help=(
            "Start the L4 Vebond WebSocket server (Summoning Circle backend). "
            "The React frontend connects to this server. "
            "Default: ws://127.0.0.1:8642/ws — requires: pip install heretic[serve]"
        ),
    )
    p_serve.add_argument(
        "--port",
        type=int,
        default=None,
        metavar="N",
        help=(
            "WebSocket server port. Overrides vebond.ws_port in heretic.yaml. "
            "Default: 8642."
        ),
    )
    p_serve.add_argument(
        "--host",
        type=str,
        default=None,
        metavar="HOST",
        help=(
            "WebSocket server bind address. Overrides vebond.ws_host in heretic.yaml. "
            "Default: 127.0.0.1 (loopback). Non-loopback addresses require "
            "vebond.allow_remote_bind: true in heretic.yaml."
        ),
    )
    p_serve.set_defaults(func=_cmd_serve)

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
