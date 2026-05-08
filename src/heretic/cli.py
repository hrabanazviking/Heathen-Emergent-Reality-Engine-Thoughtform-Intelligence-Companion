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
from typing import Any


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


async def _async_serve(args: argparse.Namespace) -> int:
    """Async implementation of the `serve` command — runs the Vebond WebSocket server.

    Wire-up order:
        1. Load config + logging
        2. Build EventBus
        3. Build Bifrost / Tunga / Hlust (same pattern as _async_light)
        4. Register EventBus hooks for all component state changes
        5. Register command handlers that drive ceremony transitions
        6. Build WebSocketServer, call start(), then serve() until SIGINT

    The EventBus is the only data path between vebond.serve and all other layers.
    vebond.serve does not import bifrost, rodd, or lifecycle directly — the CLI
    wires those together here and hands the server command_handlers + event_bus.
    This preserves the dependency direction documented in LAYER_INTERFACES.md.
    """
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
    from heretic.vebond.serve import EventBus, WebSocketServer
    from heretic.vebond.errors import VebondBindError, VebondConfigError
    from heretic.vebond.protocol import (
        CeremonyStateChanged,
        BifrostHealth,
        TungaActivity,
        HlustActivity,
        AgentToken,
        AgentTurnComplete,
        ErrorEvent,
    )
    import datetime

    # --- Load config ---
    try:
        cfg = load_config(args.config)
    except ConfigLoadError as exc:
        print(f"[HERETIC] Config error: {exc}", file=sys.stderr)
        return 1

    configure_logging(cfg.grunnr.log_level, cfg.grunnr.log_file)
    log = get_logger("heretic.cli.serve")

    # Apply CLI port/host overrides to VebondConfig
    vebond_cfg = cfg.vebond
    try:
        from heretic.vebond.config_model import VebondConfig
        # Build a new VebondConfig, applying any --port/--host CLI overrides
        override_host = args.host if args.host is not None else vebond_cfg.ws_host
        override_port = args.port if args.port is not None else vebond_cfg.ws_port
        vebond_cfg = VebondConfig(
            theme=vebond_cfg.theme,
            show_frame_thumbnail=vebond_cfg.show_frame_thumbnail,
            show_agent_text_stream=vebond_cfg.show_agent_text_stream,
            ceremony_button_confirm=vebond_cfg.ceremony_button_confirm,
            ws_host=override_host,
            ws_port=override_port,
            allow_remote_bind=vebond_cfg.allow_remote_bind,
            max_message_size_bytes=vebond_cfg.max_message_size_bytes,
            heartbeat_interval_seconds=vebond_cfg.heartbeat_interval_seconds,
            connection_timeout_seconds=vebond_cfg.connection_timeout_seconds,
        )
    except (VebondConfigError, AttributeError) as exc:
        print(f"[HERETIC] Vebond config error: {exc}", file=sys.stderr)
        return 1

    # --- Build EventBus ---
    event_bus = EventBus()

    # --- Build Lifecycle state machine ---
    lc = Lifecycle()

    # Hook: when lifecycle transitions, publish ceremony.state_changed on EventBus
    def _on_lifecycle_state_change(from_state_enum: Any, to_state_enum: Any) -> None:
        """Translate lifecycle enum transitions to IPC events."""
        # Map internal LifecycleState enum to the 5 public ceremony states
        _state_map = {
            LifecycleState.HVILD:        "hvild",
            LifecycleState.KYNDING:      "kynding",
            LifecycleState.READY:        "kynding",   # READY is a sub-state of kynding
            LifecycleState.OPENING:      "kynding",   # OPENING is a sub-state of kynding
            LifecycleState.TENGSL:       "tengsl",
            LifecycleState.SAMRAEDUR:    "samraedur",
            LifecycleState.RECOVERING:   "recovering",
            LifecycleState.SLOKNA:       "slokna",
            LifecycleState.EXTINGUISHED: "slokna",
            LifecycleState.CONFIG_ERROR: "config_error",
        }
        from_str = _state_map.get(from_state_enum, str(from_state_enum))
        to_str = _state_map.get(to_state_enum, str(to_state_enum))
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        event_bus.publish(CeremonyStateChanged(
            from_state=from_str,
            to_state=to_str,
            timestamp=ts,
        ))

    # Register lifecycle observer — fires on every state transition
    try:
        lc.on_state_change(_on_lifecycle_state_change)
    except AttributeError:
        log.warning(
            "Lifecycle.on_state_change not available — "
            "ceremony.state_changed events will not flow to UI"
        )

    lc.transition(LifecycleState.KYNDING)
    lc.transition(LifecycleState.READY)

    # --- Build BifrostConfig (same pattern as _async_light) ---
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

    # --- Build Tunga (TTS) if enabled ---
    tunga: Tunga | None = None
    rodd_tts_config: RoddTtsConfig = RoddTtsConfig()
    grunnr_rodd = cfg.rodd
    grunnr_tts = grunnr_rodd.tts
    if grunnr_tts.enabled:
        try:
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
            log.warning("Tunga init failed — serve continues text-only: %s", exc)
            tunga = None

    # --- Build Hlust (STT) if enabled ---
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
                log.warning("Hlust is_available=False — serve mode has no STT")
                hlust = None
        except Exception as exc:
            log.warning("Hlust init failed — serve continues without STT: %s", exc)
            hlust = None

    # --- State for the serve turn loop ---
    messages: list[dict] = []
    _in_flight_turn_id: list[str] = [None]  # mutable reference in closure
    _in_flight_task: list[asyncio.Task | None] = [None]

    # --- Build command handlers ---

    async def _handle_light(command: Any) -> None:
        """Light: READY -> OPENING -> try connect -> TENGSL or back to READY."""
        lc.transition(LifecycleState.OPENING)
        event_bus.publish(BifrostHealth(
            status="opening",
            endpoint=bf_config.endpoint,
            latency_ms=None,
        ))
        try:
            await client.open()
        except BifrostError as exc:
            log.warning("Light command: Bifrost open failed: %s", exc)
            lc.transition(LifecycleState.READY)
            event_bus.publish(BifrostHealth(status="failed", endpoint=bf_config.endpoint, latency_ms=None))
            event_bus.publish(ErrorEvent(
                level="error",
                source="bifrost",
                message=f"Connection failed: {exc}",
            ))
            return
        lc.transition(LifecycleState.TENGSL)
        event_bus.publish(BifrostHealth(
            status="open",
            endpoint=bf_config.endpoint,
            latency_ms=None,
        ))
        print(
            f"[HERETIC] Bifrost open via serve — connected to {bf_config.endpoint}",
            file=sys.stderr,
        )

    async def _handle_extinguish(command: Any) -> None:
        """Extinguish: cancel in-flight turn, close all, transition to SLOKNA."""
        if _in_flight_task[0] and not _in_flight_task[0].done():
            _in_flight_task[0].cancel()
        lc.transition(LifecycleState.SLOKNA)
        if hlust is not None:
            try:
                await hlust.close()
            except Exception as exc:
                log.warning("Hlust close error on extinguish: %s", exc)
        if tunga is not None:
            try:
                await tunga.close()
            except Exception as exc:
                log.warning("Tunga close error on extinguish: %s", exc)
        try:
            await client.close()
        except Exception as exc:
            log.warning("Bifrost close error on extinguish: %s", exc)
        event_bus.publish(BifrostHealth(status="closed", endpoint=bf_config.endpoint, latency_ms=None))
        lc.transition(LifecycleState.EXTINGUISHED)

    async def _handle_send_message(command: Any) -> None:
        """SendMessage: inject user text, run one bifrost turn, stream tokens."""
        import uuid

        text = command.text.strip()
        if not text:
            event_bus.publish(ErrorEvent(
                level="warn",
                source="vebond",
                message="Message text is empty after stripping whitespace.",
            ))
            return

        messages.append({"role": "user", "content": [{"type": "text", "text": text}]})
        lc.transition(LifecycleState.SAMRAEDUR)

        turn_id = str(uuid.uuid4())
        _in_flight_turn_id[0] = turn_id
        sequence = [0]

        async def _run_turn() -> None:
            assistant_text = ""
            try:
                async for chunk in client.send_message(messages):
                    if not chunk.startswith("{"):
                        event_bus.publish(AgentToken(
                            role="assistant",
                            text_delta=chunk,
                            sequence_id=sequence[0],
                        ))
                        sequence[0] += 1
                        assistant_text += chunk
                        if tunga is not None and not tunga.is_degraded:
                            try:
                                await tunga.feed_chunk(chunk)
                            except Exception as exc:
                                log.warning("Tunga.feed_chunk: %s", exc)
            except asyncio.CancelledError:
                event_bus.publish(AgentTurnComplete(turn_id=turn_id, finish_reason="cancelled"))
                return
            except BifrostError as exc:
                log.warning("Bifrost error during turn: %s", exc)
                event_bus.publish(ErrorEvent(level="error", source="bifrost", message=str(exc)))
                event_bus.publish(AgentTurnComplete(turn_id=turn_id, finish_reason="error"))
                return

            # Flush TTS at end of turn
            if tunga is not None and not tunga.is_degraded:
                try:
                    await tunga.flush()
                except Exception as exc:
                    log.warning("Tunga.flush: %s", exc)

            if assistant_text:
                messages.append({"role": "assistant", "content": assistant_text})

            event_bus.publish(AgentTurnComplete(turn_id=turn_id, finish_reason="stop"))
            _in_flight_turn_id[0] = None

            # Return to Tengsl state after turn completes
            try:
                lc.transition(LifecycleState.TENGSL)
            except Exception:
                pass

        task = asyncio.ensure_future(_run_turn())
        _in_flight_task[0] = task

    async def _handle_cancel_turn(command: Any) -> None:
        """CancelTurn: abort the in-flight turn if matching."""
        if _in_flight_task[0] and not _in_flight_task[0].done():
            if _in_flight_turn_id[0] == command.turn_id:
                _in_flight_task[0].cancel()
            else:
                event_bus.publish(ErrorEvent(
                    level="warn",
                    source="vebond",
                    message=f"No in-flight turn with id '{command.turn_id}'.",
                ))
        else:
            event_bus.publish(ErrorEvent(
                level="warn",
                source="vebond",
                message="No turn is currently in flight.",
            ))

    async def _handle_toggle_sense(command: Any) -> None:
        """ToggleSense: deferred to v0.4.x — reply with error (Cartographer thread #2)."""
        event_bus.publish(ErrorEvent(
            level="warn",
            source="vebond",
            message=(
                "Sense toggles are read-only in v0.4.0. "
                "Restart the ceremony with the updated heretic.yaml to change sense configuration."
            ),
        ))

    command_handlers = {
        "light":          _handle_light,
        "extinguish":     _handle_extinguish,
        "send_message":   _handle_send_message,
        "cancel_turn":    _handle_cancel_turn,
        "toggle_sense":   _handle_toggle_sense,
    }

    # --- Build and start the WebSocket server ---
    server = WebSocketServer(
        config=vebond_cfg,
        event_bus=event_bus,
        command_handlers=command_handlers,
        logger=log,
    )

    try:
        await server.start()
    except VebondBindError as exc:
        print(f"[HERETIC] Cannot start serve: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[HERETIC] Server start error: {exc}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1

    print(
        f"[HERETIC] Summoning Circle backend running:\n"
        f"  WebSocket:  ws://{vebond_cfg.ws_host}:{vebond_cfg.ws_port}/ws\n"
        f"  Health:     http://{vebond_cfg.ws_host}:{vebond_cfg.ws_port}/health\n"
        f"  Press Ctrl+C to extinguish the ceremony.",
        file=sys.stderr,
    )

    # Run the server main loop until SIGINT
    try:
        await server.serve()
    except KeyboardInterrupt:
        pass

    # --- Slokna: clean shutdown ---
    print("\n[HERETIC] Extinguishing serve mode...", file=sys.stderr)
    lc.transition(LifecycleState.SLOKNA)

    if _in_flight_task[0] and not _in_flight_task[0].done():
        _in_flight_task[0].cancel()

    if hlust is not None:
        try:
            await hlust.close()
        except Exception as exc:
            log.warning("Error closing Hlust: %s", exc)

    if tunga is not None:
        try:
            await tunga.close()
        except Exception as exc:
            log.warning("Error closing Tunga: %s", exc)

    try:
        await client.close()
    except Exception as exc:
        log.warning("Error closing Bifrost: %s", exc)

    await server.stop()
    lc.transition(LifecycleState.EXTINGUISHED)
    print("[HERETIC] Serve mode ended. Hvild.", file=sys.stderr)
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    """Start the L4 Vebond WebSocket and REST server (the Summoning Circle backend).

    Loads heretic.yaml (or the config at --config PATH), applies any CLI overrides
    for --port and --host, then binds a FastAPI + uvicorn WebSocket server at
    ws://<host>:<port>/ws and a REST health endpoint at http://<host>:<port>/health.

    Default bind: ws://127.0.0.1:8642/ws  (loopback; configurable via heretic.yaml
    vebond.ws_port and vebond.ws_host — see docs/architecture/IPC_PROTOCOL.md).

    Usage:
        heretic serve
        heretic serve --port 8643
        heretic serve --host 0.0.0.0 --port 8643  (requires allow_remote_bind: true)
        heretic serve --config /path/to/heretic.yaml
    """
    return asyncio.run(_async_serve(args))


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
