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

    # --- Skilningr (L5): initialise sense hub and Smiðja hand if enabled ---
    # Constructed at TENGSL (Bifröst is open; agent capabilities known).
    # Failure here is non-fatal — ceremony continues without tool use.
    from heretic.skilningr.senses.smidja.client import BrunhandHttpClient
    from heretic.skilningr.senses.smidja.sense import SmidjaSense
    from heretic.skilningr.senses.smidja.errors import (
        BrunhandAuthError,
        BrunhandUnreachableError,
    )
    from heretic.skilningr.dispatcher import ToolDispatcher
    from heretic.skilningr.config_model import SmidjaConfig

    dispatcher: ToolDispatcher | None = None
    smidja_sense: SmidjaSense | None = None

    grunnr_skilningr = cfg.skilningr
    grunnr_smidja = grunnr_skilningr.smidja

    if grunnr_smidja.enabled:
        try:
            smidja_config = SmidjaConfig(
                enabled=grunnr_smidja.enabled,
                host=grunnr_smidja.host,
                port=grunnr_smidja.port,
                token_env=grunnr_smidja.token_env,
                request_timeout_seconds=grunnr_smidja.request_timeout_seconds,
                require_https=grunnr_smidja.require_https,
                host_name=grunnr_smidja.host_name,
            )
            smidja_client = BrunhandHttpClient(smidja_config, log)
            smidja_sense = SmidjaSense(smidja_config, smidja_client, log, event_emitter=None)
            await smidja_sense.open()
            if smidja_sense.is_available:
                dispatcher = ToolDispatcher()
                dispatcher.register_sense("smidja", smidja_sense)
                # Mark the Bifröst client as tool-use capable (body has hands now)
                client._capability_tool_use = True
                log.info(
                    "Smiðja sense ready — %d tools registered.",
                    len(dispatcher.all_tool_definitions()),
                )
            else:
                log.warning(
                    "Smiðja sense enabled but is_available=False after open() — "
                    "ceremony continues without hands."
                )
        except (BrunhandAuthError, BrunhandUnreachableError) as exc:
            log.warning(
                "Smiðja init failed — ceremony continues without the hand: %s", exc
            )
            smidja_sense = None
            dispatcher = None
        except Exception as exc:
            log.warning(
                "Smiðja init raised unexpected error — ceremony continues without the hand: %s",
                exc,
            )
            smidja_sense = None
            dispatcher = None

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

    # --- Sjón (L3 Vision): initialise screen capture if enabled ---
    # Constructed after Bifröst is open; errors here are non-fatal — ceremony
    # continues without screen frames if Sjón cannot initialise.
    sjon: Any | None = None
    grunnr_sjon = cfg.sjon
    if grunnr_sjon.screen.enabled:
        try:
            from heretic.sjon.sjon import Sjón
            from heretic.sjon.encoder import FrameEncoder as SjonFrameEncoder
            from heretic.sjon.capture import best_available as sjon_best_available
            sjon_encoder = SjonFrameEncoder(
                max_width=grunnr_sjon.screen.max_width,
                max_height=grunnr_sjon.screen.max_height,
                logger=log,
            )
            sjon_backend = sjon_best_available(log, grunnr_sjon.screen)
            sjon = Sjón(
                config=grunnr_sjon,
                capture_backend=sjon_backend,
                encoder=sjon_encoder,
                logger=log,
                event_emitter=None,  # CLI mode: no EventBus wiring
            )
            if sjon.is_available:
                # Wire the body-state flag: tell Bifröst the eye is open.
                client.capability_vision_screen = True
                log.info("Sjón initialised — screen capture available.")
            else:
                log.warning(
                    "Sjón init succeeded but is_available=False — "
                    "no screen capture backend available. Sight inactive."
                )
                sjon = None
        except Exception as exc:
            log.warning(
                "Sjón init failed — ceremony continues sightless: %s", exc
            )
            sjon = None

    # --- Sjón webcam (v0.5.2): initialise webcam backend if enabled ---
    # Runs after screen Sjón init; errors are non-fatal — ceremony continues
    # with screen-only or no vision if webcam cannot initialise.
    if sjon is not None and grunnr_sjon.webcam.enabled:
        try:
            from heretic.sjon.webcam import best_available as webcam_best_available
            from heretic.sjon.webcam import WebcamNullBackend
            webcam_backend = webcam_best_available(log, grunnr_sjon.webcam)
            if not webcam_backend.available():
                log.warning(
                    "Webcam configured but unavailable — "
                    "cv2 not installed or no device at index %d. "
                    "Degrading to WebcamNullBackend.",
                    grunnr_sjon.webcam.device_index,
                )
                webcam_backend = WebcamNullBackend()
            sjon._webcam_backend = webcam_backend
            log.info(
                "Sjón webcam backend wired (attach_policy=%s, device=%d).",
                grunnr_sjon.webcam.attach_policy,
                grunnr_sjon.webcam.device_index,
            )
        except Exception as exc:
            log.warning(
                "Sjón webcam init failed — ceremony continues without webcam: %s", exc
            )

    # --- Sjón continuous capture: kick off at TENGSL if configured ---
    # Only starts when sjon is available AND continuous mode is enabled in config.
    # On-demand mode (continuous=False) uses snapshot() per turn — no background task.
    if sjon is not None and sjon.is_available and grunnr_sjon.screen.continuous:
        try:
            await sjon.start_continuous_capture()
            log.info(
                "Sjon continuous capture started (interval_ms=%d, buffer_depth=%d).",
                grunnr_sjon.screen.interval_ms,
                grunnr_sjon.screen.buffer_depth,
            )
        except Exception as exc:
            log.warning(
                "Sjon start_continuous_capture failed — falling back to on-demand: %s", exc
            )

    print(
        f"[HERETIC] Bifrost open - connected to {bf_config.endpoint} "
        f"(model: {bf_config.model})",
        file=sys.stderr,
    )
    print(
        f"[HERETIC] Capabilities: tool_use={client.capability_tool_use} "
        f"vision_in={client.capability_vision_in} "
        f"vision_screen={client.capability_vision_screen} "
        f"streaming={client.capability_streaming}",
        file=sys.stderr,
    )
    print("[HERETIC] Enter Samraedur - type your message and press Enter.", file=sys.stderr)
    print("[HERETIC] Type /quit or press Ctrl+C to extinguish.", file=sys.stderr)

    # --- Samræður: turn loop ---
    lc.transition(LifecycleState.SAMRAEDUR)
    messages: list[dict] = []

    # Per-ceremony alternate-turn counter for webcam attach_policy="alternate".
    # Resets at TENGSL (here) — scope is per-ceremony, not global.
    # Even turns → webcam frame; odd turns → screen frame.
    # Cartographer invariant: counter is per-ceremony, not per-process.
    ceremony_state: dict[str, int] = {"alternate_turn": 0}

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

            # --- Vision attach (v0.5.2): per-turn frame attach with attach_policy.
            # Both capability flags must be True:
            #   ?vision_in     — agent capability (from probe): accepts image content.
            #   ?vision_screen — body state (from Sjón init): screen capture available.
            # Frames are only injected when the spirit can receive AND the eye can see.
            #
            # Screen attach_policy (sjon.screen.attach_policy):
            #   "none"         — no frames attached (continuous runs but silent)
            #   "latest"       — attach the single most-recent frame from buffer
            #                    (or on-demand snapshot if buffer empty / not continuous)
            #   "all_buffered" — attach all frames currently in ring buffer
            #
            # Webcam attach_policy (sjon.webcam.attach_policy, v0.5.2):
            #   "screen_only"  — webcam suppressed; screen-only (default, backward compat)
            #   "webcam_only"  — webcam frame only; screen suppressed even if enabled
            #   "alongside"    — both webcam + screen frames in one turn (highest token cost)
            #   "alternate"    — even turns webcam, odd turns screen; per-ceremony counter
            image_data_urls: list[str] = []
            if (
                sjon is not None
                and client.capability_vision_in
                and client.capability_vision_screen
            ):
                try:
                    webcam_policy = grunnr_sjon.webcam.attach_policy

                    if webcam_policy == "webcam_only":
                        # Webcam-only: ignore screen entirely for this turn.
                        image_data_urls = await sjon.snapshot_webcam()

                    elif webcam_policy == "alongside":
                        # Both: webcam first, then screen.
                        webcam_urls = await sjon.snapshot_webcam()
                        screen_urls = await sjon.snapshot()
                        image_data_urls = webcam_urls + screen_urls

                    elif webcam_policy == "alternate":
                        # Alternate per ceremony turn: even→webcam, odd→screen.
                        turn = ceremony_state["alternate_turn"]
                        if turn % 2 == 0:
                            image_data_urls = await sjon.snapshot_webcam()
                        else:
                            image_data_urls = await sjon.snapshot()
                        ceremony_state["alternate_turn"] = turn + 1

                    else:
                        # "screen_only" (default) or any unknown policy:
                        # use the existing screen attach_policy logic (v0.5/v0.5.1 path).
                        screen_policy = grunnr_sjon.screen.attach_policy
                        if screen_policy == "none":
                            image_data_urls = []
                        elif screen_policy == "all_buffered" and grunnr_sjon.screen.continuous:
                            # Return all buffered frames (up to buffer_depth).
                            image_data_urls = sjon.recent_frames()
                        elif screen_policy == "latest" and grunnr_sjon.screen.continuous:
                            # Return the single most-recent buffered frame.
                            # If the buffer is empty (first tick not yet fired), fall back
                            # to an on-demand snapshot so the turn is never frameless.
                            image_data_urls = sjon.recent_frames(n=1)
                            if not image_data_urls:
                                image_data_urls = await sjon.snapshot()
                        else:
                            # On-demand mode (continuous=False) — existing v0.5 path.
                            image_data_urls = await sjon.snapshot()

                except Exception as exc:
                    # Wrap defensively — snapshot() and recent_frames() never raise
                    # by contract, but we guard the whole block to be safe.
                    log.warning(
                        "Sjon attach failed; sending text-only: %s", exc
                    )
                    image_data_urls = []

            # Build the user message content.
            # When image_data_urls is non-empty, use OpenAI multimodal content array.
            # When empty, fall back to a simple text-only content array.
            # The content is ALWAYS a list per the protocol (§2.1 content array format).
            user_content: list[dict] = [{"type": "text", "text": user_text}]
            for url in image_data_urls:
                user_content.append({"type": "image_url", "image_url": {"url": url}})

            messages.append({"role": "user", "content": user_content})

            # --- Multi-round tool dispatch loop ---
            # Build tools array when dispatcher is ready and agent supports tool_use.
            # Loops until agent emits a text response (no tool calls) or
            # max_tool_call_rounds is reached (safety cap).
            tools_array = None
            if dispatcher is not None and client.capability_tool_use:
                tools_array = dispatcher.all_tool_definitions() or None

            tool_call_rounds = 0
            max_rounds = bf_config.max_tool_call_rounds

            print("agent> ", end="", flush=True)
            assistant_text = ""

            while True:
                # Collect streaming chunks and accumulated tool_calls in this pass
                accumulated_tool_calls: list[dict] = []
                collected_text = ""
                had_bifrost_error = False

                try:
                    import json as _json

                    async for chunk in client.send_message(messages, tools=tools_array):
                        # Determine if this chunk is a structured tool_call record.
                        # Bifröst's _parse_sse_stream assembles all tool-call argument
                        # fragments and yields them as a JSON string with {"type": "tool_call"}.
                        # Text deltas are yielded as plain strings (never wrapped in JSON).
                        #
                        # We parse the chunk as JSON and inspect the 'type' field — this is
                        # the canonical classification, not a string-heuristic on the raw
                        # bytes. A legitimate text response that *contains* the substring
                        # '"type": "tool_call"' will not be misrouted because it will either
                        # fail JSON parsing (not valid JSON) or — if it is valid JSON — will
                        # only route here if its top-level 'type' field IS "tool_call", which
                        # is reserved for Bifröst-assembled tool-call records.
                        #
                        # C-3 fix (Eldra Járnsdóttir, 2026-05-08): replaced string heuristic
                        # chunk.startswith("{") and '"type": "tool_call"' in chunk with
                        # structured JSON inspection of the parsed dict's 'type' field.
                        _parsed_event: dict | None = None
                        if chunk.startswith("{"):
                            try:
                                _parsed_event = _json.loads(chunk)
                            except _json.JSONDecodeError:
                                _parsed_event = None

                        if (
                            _parsed_event is not None
                            and isinstance(_parsed_event, dict)
                            and _parsed_event.get("type") == "tool_call"
                        ):
                            # Bifröst emits completed tool_call records as JSON strings
                            try:
                                # Re-shape into OpenAI tool_call format for dispatcher
                                accumulated_tool_calls.append({
                                    "id": _parsed_event.get("id", ""),
                                    "type": "function",
                                    "function": {
                                        "name": _parsed_event.get("name", ""),
                                        "arguments": _parsed_event.get("arguments", "{}"),
                                    },
                                })
                                log.info(
                                    "Tool call received: %s (id=%s)",
                                    _parsed_event.get("name"), _parsed_event.get("id"),
                                )
                            except Exception as exc:
                                log.warning("Could not process tool_call record: %s", exc)
                        else:
                            print(chunk, end="", flush=True)
                            collected_text += chunk
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
                    had_bifrost_error = True

                # If agent produced tool calls and we have a dispatcher and rounds left,
                # execute the tools and loop
                if (
                    accumulated_tool_calls
                    and dispatcher is not None
                    and tool_call_rounds < max_rounds
                    and not had_bifrost_error
                ):
                    tool_call_rounds += 1
                    log.info(
                        "Dispatching %d tool call(s) (round %d/%d).",
                        len(accumulated_tool_calls), tool_call_rounds, max_rounds,
                    )

                    # Append the assistant message with tool_calls to the context
                    if collected_text:
                        messages.append({
                            "role": "assistant",
                            "content": collected_text,
                            "tool_calls": accumulated_tool_calls,
                        })
                    else:
                        messages.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": accumulated_tool_calls,
                        })

                    # Dispatch each tool call and add results to messages
                    for tool_call in accumulated_tool_calls:
                        try:
                            tool_result = await dispatcher.dispatch(tool_call)
                        except Exception as exc:
                            log.error(
                                "Dispatcher raised unexpectedly for tool %r: %s",
                                tool_call.get("function", {}).get("name"), exc,
                            )
                            # Build a safe error result manually
                            import json as _json
                            tool_result = {
                                "tool_call_id": tool_call.get("id", "unknown"),
                                "role": "tool",
                                "content": _json.dumps({
                                    "error": True,
                                    "code": "SENSE_INTERNAL_ERROR",
                                    "message": f"Dispatcher error: {type(exc).__name__}",
                                }),
                            }
                        messages.append(tool_result)

                    # Print a separator before next agent response
                    print("\nagent> ", end="", flush=True)
                    continue  # Loop for the agent's next response

                # No tool calls OR dispatcher unavailable OR rounds exhausted — done
                if tool_call_rounds >= max_rounds and accumulated_tool_calls:
                    log.warning(
                        "Tool-call round cap reached at %d — breaking dispatch loop.",
                        max_rounds,
                    )
                assistant_text = collected_text
                break

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

    # Close Smiðja sense first (L5 hands) — stop any in-flight Brúarhönd sessions
    if smidja_sense is not None:
        try:
            await smidja_sense.close()
        except Exception as exc:
            log.warning("Error closing Smiðja sense: %s", exc)

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

    # Close Sjón — release screen + webcam capture resources
    if sjon is not None:
        # Close webcam backend first (releases OS device handle before Sjón closes)
        if sjon._webcam_backend is not None:
            try:
                sjon._webcam_backend.close()
            except Exception as exc:
                log.warning("Error closing Sjón webcam backend: %s", exc)
        try:
            await sjon.close()
        except Exception as exc:
            log.warning("Error closing Sjón: %s", exc)

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

    # --- Sjón (L3 Vision): initialise for serve mode ---
    sjon_serve: Any | None = None
    grunnr_sjon_serve = cfg.sjon
    if grunnr_sjon_serve.screen.enabled:
        try:
            from heretic.sjon.sjon import Sjón as SjonServe
            from heretic.sjon.encoder import FrameEncoder as SjonFrameEncoderServe
            from heretic.sjon.capture import best_available as sjon_best_available_serve
            from heretic.vebond.protocol import SjonActivity, SjonActivityState
            import datetime as _dt

            _sjon_encoder_serve = SjonFrameEncoderServe(
                max_width=grunnr_sjon_serve.screen.max_width,
                max_height=grunnr_sjon_serve.screen.max_height,
                logger=log,
            )
            _sjon_backend_serve = sjon_best_available_serve(log, grunnr_sjon_serve.screen)

            def _sjon_event_emitter(evt: object) -> None:
                """Forward SjonActivity events from the Sjón orchestrator to the EventBus."""
                try:
                    event_bus.publish(evt)
                except Exception as exc:
                    log.debug("Sjón event_emitter error (ignored): %s", exc)

            sjon_serve = SjonServe(
                config=grunnr_sjon_serve,
                capture_backend=_sjon_backend_serve,
                encoder=_sjon_encoder_serve,
                logger=log,
                event_emitter=_sjon_event_emitter,
            )
            if sjon_serve.is_available:
                client.capability_vision_screen = True
                log.info("Sjón initialised for serve mode — screen capture available.")
            else:
                log.warning("Sjón serve init: is_available=False — sight inactive.")
                sjon_serve = None
        except Exception as exc:
            log.warning("Sjón serve init failed — serve continues sightless: %s", exc)
            sjon_serve = None

    # --- Sjón webcam serve (v0.5.2 N-1 fix, Eldra Járnsdóttir 2026-05-08) ---
    # Mirror the _async_light webcam-init pattern for serve mode.
    # Deferred to _init_serve_webcam() (called from _handle_light at TENGSL) so it
    # fires after sjon_serve is confirmed available.  Close deferred to _handle_extinguish.
    # Per-ceremony alternate counter lives in serve_ceremony_state (reset at TENGSL).
    from heretic.sjon.webcam import WebcamNullBackend as _ServeWebcamNullBackend  # noqa: E402
    serve_webcam_backend: Any | None = None
    serve_ceremony_state: dict[str, int] = {"alternate_turn": 0}

    async def _init_serve_webcam() -> None:
        """Initialise webcam backend for serve mode at TENGSL.

        Mirrors the _async_light webcam wiring (cli.py:278–303).  Non-fatal — ceremony
        continues screen-only (or sightless) if webcam cannot be initialised.
        """
        nonlocal serve_webcam_backend, serve_ceremony_state

        if sjon_serve is None:
            return
        if not grunnr_sjon_serve.webcam.enabled:
            return

        try:
            from heretic.sjon.webcam import best_available as _webcam_best_available_serve
            from heretic.sjon.webcam import WebcamNullBackend as _WNB
            _wc = _webcam_best_available_serve(log, grunnr_sjon_serve.webcam)
            if not _wc.available():
                log.warning(
                    "Serve webcam configured but unavailable — "
                    "cv2 not installed or no device at index %d. "
                    "Degrading to WebcamNullBackend.",
                    grunnr_sjon_serve.webcam.device_index,
                )
                _wc = _WNB()
            sjon_serve._webcam_backend = _wc
            serve_webcam_backend = _wc
            # Reset per-ceremony alternate counter at TENGSL
            serve_ceremony_state["alternate_turn"] = 0
            log.info(
                "Sjón webcam backend wired for serve mode (attach_policy=%s, device=%d).",
                grunnr_sjon_serve.webcam.attach_policy,
                grunnr_sjon_serve.webcam.device_index,
            )
        except Exception as exc:
            log.warning(
                "Sjón webcam init failed in serve mode — serve continues without webcam: %s",
                exc,
            )
            serve_webcam_backend = None

    # --- Skilningr (L5): initialise Smiðja sense hub for serve mode ---
    # Mirrors the _async_light pattern; key difference is that event_emitter is wired
    # to event_bus.publish so SenseToolCall IPC events flow to all WS clients.
    # Constructed here (after Bifröst config is built); actual open() deferred to
    # _handle_light so it fires AFTER the Bifröst connection is established at TENGSL.
    #
    # N-1 fix (Eldra Járnsdóttir, 2026-05-08): serve mode previously had no Skilningr
    # wiring — tool calls were silently dropped in _handle_send_message and the
    # Smiðja LayerStatusPanel row never activated for serve-mode sessions.
    serve_dispatcher: "ToolDispatcher | None" = None  # type: ignore[name-defined]
    serve_smidja_sense: "SmidjaSense | None" = None  # type: ignore[name-defined]

    # Helper: build and open Smiðja in serve mode. Called from _handle_light so the
    # Bifröst client exists and capabilities are known when we set capability_tool_use.
    async def _init_serve_smidja() -> None:
        """Initialise Smiðja sense and dispatcher for serve mode at TENGSL."""
        nonlocal serve_dispatcher, serve_smidja_sense

        from heretic.skilningr.senses.smidja.client import BrunhandHttpClient
        from heretic.skilningr.senses.smidja.sense import SmidjaSense
        from heretic.skilningr.senses.smidja.errors import (
            BrunhandAuthError,
            BrunhandUnreachableError,
        )
        from heretic.skilningr.dispatcher import ToolDispatcher
        from heretic.skilningr.config_model import SmidjaConfig

        grunnr_skilningr = cfg.skilningr
        grunnr_smidja_serve = grunnr_skilningr.smidja

        if not grunnr_smidja_serve.enabled:
            return

        try:
            smidja_config_serve = SmidjaConfig(
                enabled=grunnr_smidja_serve.enabled,
                host=grunnr_smidja_serve.host,
                port=grunnr_smidja_serve.port,
                token_env=grunnr_smidja_serve.token_env,
                request_timeout_seconds=grunnr_smidja_serve.request_timeout_seconds,
                require_https=grunnr_smidja_serve.require_https,
                host_name=grunnr_smidja_serve.host_name,
            )
            smidja_client_serve = BrunhandHttpClient(smidja_config_serve, log)

            # Wire event_emitter to event_bus.publish so SenseToolCall events reach WS clients.
            # This is the critical difference from _async_light (CLI), where event_emitter=None.
            def _smidja_event_emitter(evt: object) -> None:
                try:
                    event_bus.publish(evt)
                except Exception as exc_emit:
                    log.debug("Smiðja event_emitter error (ignored): %s", exc_emit)

            serve_smidja_sense = SmidjaSense(
                smidja_config_serve,
                smidja_client_serve,
                log,
                event_emitter=_smidja_event_emitter,
            )
            await serve_smidja_sense.open()
            if serve_smidja_sense.is_available:
                serve_dispatcher = ToolDispatcher()
                serve_dispatcher.register_sense("smidja", serve_smidja_sense)
                # Signal Bifröst that the body now has hands (tool-use capability active)
                client._capability_tool_use = True
                log.info(
                    "Smiðja sense ready in serve mode — %d tools registered.",
                    len(serve_dispatcher.all_tool_definitions()),
                )
            else:
                log.warning(
                    "Smiðja sense enabled but is_available=False in serve mode — "
                    "ceremony continues without hands."
                )
        except (BrunhandAuthError, BrunhandUnreachableError) as exc_smidja:
            log.warning(
                "Smiðja init failed in serve mode — ceremony continues without the hand: %s",
                exc_smidja,
            )
            serve_smidja_sense = None
            serve_dispatcher = None
        except Exception as exc_smidja:
            log.warning(
                "Smiðja serve init raised unexpected error — ceremony continues without the hand: %s",
                exc_smidja,
            )
            serve_smidja_sense = None
            serve_dispatcher = None

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
        # Initialise Smiðja sense now that Bifröst is open (TENGSL state).
        # Non-fatal: ceremony continues without tool-use if this fails.
        await _init_serve_smidja()
        # Initialise webcam backend for serve mode (N-1 fix, v0.5.2 audit).
        # Non-fatal: ceremony continues without webcam if this fails.
        await _init_serve_webcam()
        print(
            f"[HERETIC] Bifrost open via serve — connected to {bf_config.endpoint}",
            file=sys.stderr,
        )

    async def _handle_extinguish(command: Any) -> None:
        """Extinguish: cancel in-flight turn, close all, transition to SLOKNA."""
        if _in_flight_task[0] and not _in_flight_task[0].done():
            _in_flight_task[0].cancel()
        lc.transition(LifecycleState.SLOKNA)
        # Close Smiðja sense first (L5 hands) before Bifröst closes
        if serve_smidja_sense is not None:
            try:
                await serve_smidja_sense.close()
            except Exception as exc:
                log.warning("Smiðja serve close error on extinguish: %s", exc)
        # Close webcam backend (N-1 fix) — skip WebcamNullBackend (no-op close, but safe)
        if serve_webcam_backend is not None and not isinstance(
            serve_webcam_backend, _ServeWebcamNullBackend
        ):
            try:
                serve_webcam_backend.close()
            except Exception as exc:
                log.warning("Sjón webcam serve close error on extinguish: %s", exc)
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

        # Vision attach for serve mode — mirrors _async_light 4-path attach_policy dispatch.
        # Gate: both capability flags must be True (vision_in from probe; vision_screen from
        # Sjón init).  webcam_policy maps to the same four paths as in the light turn loop.
        # Per-ceremony alternate counter is serve_ceremony_state["alternate_turn"].
        serve_image_urls: list[str] = []
        if (
            sjon_serve is not None
            and client.capability_vision_in
            and client.capability_vision_screen
        ):
            try:
                _webcam_policy_serve = grunnr_sjon_serve.webcam.attach_policy

                if _webcam_policy_serve == "webcam_only":
                    # Webcam-only: ignore screen entirely for this turn.
                    serve_image_urls = await sjon_serve.snapshot_webcam()

                elif _webcam_policy_serve == "alongside":
                    # Both: webcam first, then screen.
                    _wc_urls = await sjon_serve.snapshot_webcam()
                    _sc_urls = await sjon_serve.snapshot()
                    serve_image_urls = _wc_urls + _sc_urls

                elif _webcam_policy_serve == "alternate":
                    # Alternate per ceremony turn: even->webcam, odd->screen.
                    _turn = serve_ceremony_state["alternate_turn"]
                    if _turn % 2 == 0:
                        serve_image_urls = await sjon_serve.snapshot_webcam()
                    else:
                        serve_image_urls = await sjon_serve.snapshot()
                    serve_ceremony_state["alternate_turn"] = _turn + 1

                else:
                    # "screen_only" (default) or any unknown policy — existing screen path.
                    _screen_policy_serve = grunnr_sjon_serve.screen.attach_policy
                    if _screen_policy_serve == "none":
                        serve_image_urls = []
                    elif _screen_policy_serve == "all_buffered" and grunnr_sjon_serve.screen.continuous:
                        serve_image_urls = sjon_serve.recent_frames()
                    elif _screen_policy_serve == "latest" and grunnr_sjon_serve.screen.continuous:
                        serve_image_urls = sjon_serve.recent_frames(n=1)
                        if not serve_image_urls:
                            serve_image_urls = await sjon_serve.snapshot()
                    else:
                        serve_image_urls = await sjon_serve.snapshot()

            except Exception as exc:
                log.warning("Sjón serve vision attach error (text-only): %s", exc)
                serve_image_urls = []

        serve_content: list[dict] = [{"type": "text", "text": text}]
        for url in serve_image_urls:
            serve_content.append({"type": "image_url", "image_url": {"url": url}})

        messages.append({"role": "user", "content": serve_content})
        lc.transition(LifecycleState.SAMRAEDUR)

        turn_id = str(uuid.uuid4())
        _in_flight_turn_id[0] = turn_id
        sequence = [0]

        async def _run_turn() -> None:
            import json as _json_serve

            # --- Multi-round tool dispatch loop for serve mode ---
            # Mirrors _async_light: build tools_array when dispatcher ready,
            # loop until agent emits text response or max_tool_call_rounds is reached.
            # Key difference: text tokens are published to EventBus (not printed to stdout);
            # tool call events are emitted via SmidjaSense.event_emitter -> event_bus.publish.
            serve_tools_array = None
            if serve_dispatcher is not None and client.capability_tool_use:
                serve_tools_array = serve_dispatcher.all_tool_definitions() or None

            tool_call_rounds_serve = 0
            max_rounds_serve = bf_config.max_tool_call_rounds
            assistant_text = ""

            while True:
                accumulated_tool_calls_serve: list[dict] = []
                collected_text_serve = ""
                had_bifrost_error_serve = False

                try:
                    async for chunk in client.send_message(messages, tools=serve_tools_array):
                        # Structured tool_call detection — same C-3 fix as _async_light.
                        # Parse JSON and check 'type' field; never use string heuristics.
                        _parsed_serve: dict | None = None
                        if chunk.startswith("{"):
                            try:
                                _parsed_serve = _json_serve.loads(chunk)
                            except _json_serve.JSONDecodeError:
                                _parsed_serve = None

                        if (
                            _parsed_serve is not None
                            and isinstance(_parsed_serve, dict)
                            and _parsed_serve.get("type") == "tool_call"
                        ):
                            try:
                                accumulated_tool_calls_serve.append({
                                    "id": _parsed_serve.get("id", ""),
                                    "type": "function",
                                    "function": {
                                        "name": _parsed_serve.get("name", ""),
                                        "arguments": _parsed_serve.get("arguments", "{}"),
                                    },
                                })
                                log.info(
                                    "Serve tool call received: %s (id=%s)",
                                    _parsed_serve.get("name"), _parsed_serve.get("id"),
                                )
                            except Exception as exc_tc:
                                log.warning("Could not process serve tool_call record: %s", exc_tc)
                        else:
                            event_bus.publish(AgentToken(
                                role="assistant",
                                text_delta=chunk,
                                sequence_id=sequence[0],
                            ))
                            sequence[0] += 1
                            collected_text_serve += chunk
                            if tunga is not None and not tunga.is_degraded:
                                try:
                                    await tunga.feed_chunk(chunk)
                                except Exception as exc_tts:
                                    log.warning("Tunga.feed_chunk: %s", exc_tts)
                except asyncio.CancelledError:
                    event_bus.publish(AgentTurnComplete(turn_id=turn_id, finish_reason="cancelled"))
                    return
                except BifrostError as exc_bf:
                    log.warning("Bifrost error during serve turn: %s", exc_bf)
                    event_bus.publish(ErrorEvent(level="error", source="bifrost", message=str(exc_bf)))
                    event_bus.publish(AgentTurnComplete(turn_id=turn_id, finish_reason="error"))
                    return

                # If tool calls received and dispatcher available and rounds left, dispatch
                if (
                    accumulated_tool_calls_serve
                    and serve_dispatcher is not None
                    and tool_call_rounds_serve < max_rounds_serve
                    and not had_bifrost_error_serve
                ):
                    tool_call_rounds_serve += 1
                    log.info(
                        "Serve: dispatching %d tool call(s) (round %d/%d).",
                        len(accumulated_tool_calls_serve),
                        tool_call_rounds_serve,
                        max_rounds_serve,
                    )

                    # Append assistant message with tool_calls to context
                    if collected_text_serve:
                        messages.append({
                            "role": "assistant",
                            "content": collected_text_serve,
                            "tool_calls": accumulated_tool_calls_serve,
                        })
                    else:
                        messages.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": accumulated_tool_calls_serve,
                        })

                    # Dispatch each tool call and append results
                    for tool_call_serve in accumulated_tool_calls_serve:
                        try:
                            tool_result_serve = await serve_dispatcher.dispatch(tool_call_serve)
                        except Exception as exc_disp:
                            log.error(
                                "Serve dispatcher raised unexpectedly for tool %r: %s",
                                tool_call_serve.get("function", {}).get("name"), exc_disp,
                            )
                            tool_result_serve = {
                                "tool_call_id": tool_call_serve.get("id", "unknown"),
                                "role": "tool",
                                "content": _json_serve.dumps({
                                    "error": True,
                                    "code": "SENSE_INTERNAL_ERROR",
                                    "message": f"Dispatcher error: {type(exc_disp).__name__}",
                                }),
                            }
                        messages.append(tool_result_serve)

                    continue  # Loop for the agent's next response

                # No tool calls OR dispatcher unavailable OR rounds exhausted — done
                if tool_call_rounds_serve >= max_rounds_serve and accumulated_tool_calls_serve:
                    log.warning(
                        "Serve: tool-call round cap reached at %d — breaking dispatch loop.",
                        max_rounds_serve,
                    )
                assistant_text = collected_text_serve
                break

            # Flush TTS at end of turn
            if tunga is not None and not tunga.is_degraded:
                try:
                    await tunga.flush()
                except Exception as exc_flush:
                    log.warning("Tunga.flush: %s", exc_flush)

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

    if sjon_serve is not None:
        try:
            await sjon_serve.close()
        except Exception as exc:
            log.warning("Error closing Sjón (serve): %s", exc)

    try:
        await client.close()
    except Exception as exc:
        log.warning("Error closing Bifrost: %s", exc)

    # Close Smiðja sense at Slokna (L5 hands last active resource before Bifröst)
    if serve_smidja_sense is not None:
        try:
            await serve_smidja_sense.close()
        except Exception as exc:
            log.warning("Error closing Smiðja sense (serve Slokna): %s", exc)

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
