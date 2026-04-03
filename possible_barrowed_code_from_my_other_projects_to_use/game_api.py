"""HTTPS API bridge for Norse Saga Engine."""

from __future__ import annotations

import json
import logging
import os
import ssl
import threading
import time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from systems.thor_guardian import ThorGuardian

import yaml

if TYPE_CHECKING:
    from core.engine import YggdrasilEngine

logger = logging.getLogger(__name__)


class LogBufferHandler(logging.Handler):
    """Thread-safe buffer for capturing live engine logs."""

    def __init__(self, max_logs=200):
        super().__init__()
        self.max_logs = max_logs
        self.logs = []
        self.lock = threading.Lock()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_entry = self.format(record)
            if not log_entry.strip():
                return
            with self.lock:
                self.logs.append(log_entry)
                if len(self.logs) > self.max_logs:
                    self.logs.pop(0)
        except Exception:
            self.handleError(record)

    def get_logs(self) -> List[str]:
        with self.lock:
            return list(self.logs)


# Global log buffer for the Sacred Well effect — installed lazily on first API
# server start so it doesn't pollute test log output on import.
log_buffer_handler = LogBufferHandler()
log_buffer_handler.setFormatter(logging.Formatter("%(name)s:%(message)s"))


def _install_log_buffer_handler() -> None:
    """Attach the log buffer to the root logger (idempotent)."""
    root = logging.getLogger()
    if log_buffer_handler not in root.handlers:
        root.addHandler(log_buffer_handler)


@dataclass
class ApiRuntimeConfig:
    """Runtime API configuration loaded from config + environment."""

    host: str
    port: int
    bearer_token: str
    tls_cert_path: str
    tls_key_path: str
    config_path: str


def _load_yaml_config(config_path: str) -> Dict[str, Any]:
    config_file = Path(config_path)
    if not config_file.exists():
        return {}
    try:
        with open(config_file, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except Exception as exc:
        logger.warning("Could not read API config file %s: %s", config_path, exc)
        return {}


def load_api_runtime_config(config_path: str) -> ApiRuntimeConfig:
    """Load API runtime settings from config.yaml and environment."""
    config = _load_yaml_config(config_path)
    api_settings = config.get("api", {}) if isinstance(config, dict) else {}

    host = str(os.getenv("NORSE_API_HOST", api_settings.get("host", "0.0.0.0")))
    port = int(os.getenv("NORSE_API_PORT", api_settings.get("port", 8443)))
    bearer_token = str(
        os.getenv("NORSE_API_TOKEN", api_settings.get("token", ""))
    ).strip()
    tls_cert_path = str(
        os.getenv("NORSE_API_TLS_CERT", api_settings.get("tls_cert_path", ""))
    ).strip()
    tls_key_path = str(
        os.getenv("NORSE_API_TLS_KEY", api_settings.get("tls_key_path", ""))
    ).strip()

    return ApiRuntimeConfig(
        host=host,
        port=port,
        bearer_token=bearer_token,
        tls_cert_path=tls_cert_path,
        tls_key_path=tls_key_path,
        config_path=config_path,
    )


class ApiCommandRouter:
    """Handle slash command inputs from API clients."""

    def __init__(self, engine: "YggdrasilEngine"):
        self.engine = engine

    def handle(self, raw_input: str) -> Tuple[str, bool]:
        command_text = (raw_input or "").strip()
        if not command_text:
            return "No command provided.", False

        parts = command_text.split(maxsplit=1)
        command = parts[0].lower().rstrip(".,?!")
        arg = parts[1] if len(parts) > 1 else ""

        try:
            if command == "/help":
                return self._help_text(), False
            if command == "/status":
                return json.dumps(
                    build_status_payload(self.engine), ensure_ascii=False
                ), False
            if command == "/where":
                destinations = self.engine.get_available_destinations()
                if not destinations:
                    return "No destinations are available from this location.", False
                names = [d.get("name", "Unknown") for d in destinations]
                return "Available destinations: " + ", ".join(names), False
            if command == "/look":
                loc_disp = self.engine.get_current_location_display()
                npcs = [
                    n.get("identity", {}).get("name", n.get("id", "Unknown"))
                    for n in self.engine.state.npcs_present
                ]
                npc_str = (
                    "Also here: " + ", ".join(npcs)
                    if npcs
                    else "You appear to be alone."
                )
                summary = f"You look around.\nLocation: {loc_disp}\n{npc_str}"

                # Extract image for location or present NPCs
                images = []
                for n in self.engine.state.npcs_present:
                    name = n.get("identity", {}).get("name", n.get("id", ""))
                    if img := self.engine.generate_character_portrait(name):
                        images.append(img.replace("\\", "/"))

                return json.dumps(
                    {"summary": summary, "images": images}, ensure_ascii=False
                ), False
            if command == "/go":
                if not arg:
                    return "Usage: /go <place>", False
                _, message = self.engine.move_to_sublocation(arg)
                return message, False
            if command in {"/who", "/npcs"}:
                npcs = self.engine.get_npcs_at_location()
                if not npcs:
                    return "No one stands nearby.", False
                lines = ["Present in this location:"]
                for n in npcs:
                    identity = n.get("identity", {})
                    name = identity.get("name", n.get("id", "Unknown"))
                    role = identity.get("class", identity.get("role", "Commoner"))
                    gender = identity.get("gender", "unknown")
                    lines.append(
                        f"• {name} — {gender.capitalize()} {role.capitalize()}"
                    )
                return "\n".join(lines), False
            if command == "/location":
                return self.engine.get_current_location_display(), False
            if command == "/rune":
                if not self.engine.can_draw_rune(cooldown_seconds=60):
                    return "The runes are still veiled; wait a little longer.", False
                rune = self.engine.draw_rune()
                name = rune.get("name", "Unknown")
                meaning = rune.get("meaning", "")
                return f"Rune drawn: {name} — {meaning}", False
            if command == "/chaos":
                if arg and arg.strip().lower() == "actions":
                    if getattr(self.engine, "advanced_chaos", None):
                        actions = self.engine.advanced_chaos.get_action_modifiers()
                        return json.dumps(actions, ensure_ascii=False), False
                    return "Advanced chaos actions unavailable.", False
                return self.engine.get_chaos_display(), False
            if command == "/wyrd":
                wyrd_system = getattr(self.engine, "wyrd_system", None)
                if not wyrd_system:
                    return "Wyrd system unavailable.", False
                if hasattr(wyrd_system, "get_status_display"):
                    return str(wyrd_system.get_status_display()), False
                if hasattr(wyrd_system, "get_current_state"):
                    return json.dumps(
                        wyrd_system.get_current_state(), ensure_ascii=False
                    ), False
                return "Wyrd status unavailable.", False
            if command == "/shortrest":
                return json.dumps(self.engine.short_rest(), ensure_ascii=False), False
            if command == "/longrest":
                return json.dumps(self.engine.long_rest(), ensure_ascii=False), False
            if command == "/party":
                return json.dumps(
                    self.engine.get_party_status(), ensure_ascii=False
                ), False
            if command == "/invite":
                if not arg:
                    return "Usage: /invite <name>", False
                ok, message = self.engine.invite_to_party(arg)
                return message, False
            if command == "/dismiss":
                if not arg:
                    return "Usage: /dismiss <name>", False
                ok, message = self.engine.dismiss_from_party(arg)
                return message, False
            if command == "/factions":
                return json.dumps(
                    self.engine.get_all_faction_standings(), ensure_ascii=False
                ), False
            if command == "/sheet":
                if not arg:
                    char_data = self.engine.state.player_character or {}
                    summary = self.engine.get_character_sheet_for_data(char_data)
                    name = self.engine._fuzzy_get(char_data, "name", "adventurer")
                    img = self.engine.generate_character_portrait(name)
                    return json.dumps(
                        {
                            "data": char_data,
                            "summary": summary,
                            "image": img.replace("\\", "/") if img else None,
                        },
                        ensure_ascii=False,
                    ), False
                character = self.engine._find_character_record(arg)
                if not character:
                    return f"Character not found: {arg}", False
                summary = self.engine.get_character_sheet_for_data(character)
                name = self.engine._fuzzy_get(character, "name", arg)
                img = self.engine.generate_character_portrait(name)
                return json.dumps(
                    {
                        "data": character,
                        "summary": summary,
                        "image": img.replace("\\", "/") if img else None,
                    },
                    ensure_ascii=False,
                ), False
            if command == "/travel":
                if not arg:
                    return "Usage: /travel <destination>", False
                _, message = self.engine.travel_to(arg)
                return message, False
            if command == "/quest":
                tracker = getattr(self.engine, "quest_tracker", None)
                if not tracker:
                    return "Quest tracker unavailable.", False
                subparts = arg.split() if arg else []
                if not subparts:
                    payload = {
                        "active": list(getattr(tracker, "active_quests", {}).keys()),
                        "pending": [
                            q.get("id", "")
                            for q in getattr(tracker, "pending_quests", [])
                            if isinstance(q, dict)
                        ],
                    }
                    return json.dumps(payload, ensure_ascii=False), False
                subcmd = subparts[0].lower()
                if subcmd in {"accept", "decline", "abandon"} and len(subparts) >= 2:
                    quest_id = subparts[1]
                    action_fn = getattr(tracker, f"{subcmd}_quest", None)
                    if action_fn:
                        ok, message = action_fn(quest_id)
                        return message, False
                return "Usage: /quest [accept|decline|abandon] <quest_id>", False
            if command == "/undo":
                restored = self.engine.restore_previous_state()
                return (
                    "Previous state restored."
                    if restored
                    else "No previous state available.",
                    False,
                )
            if command == "/memory":
                if getattr(self.engine, "enhanced_memory", None):
                    return self.engine.enhanced_memory.get_full_context_for_ai(), False
                return self.engine.get_memory_summary(), False
            if command == "/save":
                success = self.engine.save_session()
                return "Session saved." if success else "Session save failed.", False
            if command == "/load":
                if not arg:
                    return "Usage: /load <session_id>", False
                loaded = self.engine.load_session(arg)
                return ("Session loaded." if loaded else "Session not found."), False
            if command in {"/quit", "/exit"}:
                self.engine.save_session()
                return "Session closed.", True

            suggestion = self.engine.suggest_command(command)
            if suggestion:
                return f"Unknown command: {command}. Did you mean {suggestion}?", False
            return f"Unknown command: {command}", False
        except Exception as exc:
            logger.warning("API command handling failed for %s: %s", command_text, exc)
            return "A mist of wyrd blocks this command right now.", False

    @staticmethod
    def _help_text() -> str:
        return (
            "API commands: /help, /status, /where, /go <place>, /who, /location, /rune, /wyrd, "
            "/chaos [actions], /shortrest, /longrest, /party, /invite <name>, /dismiss <name>, "
            "/factions, /sheet [name], /travel <dest>, /quest <subcommand>, /undo, /memory, "
            "/save, /load <session_id>, /quit"
        )


class ApiGameBridge:
    """Thread-safe API bridge for game input/output."""

    def __init__(self, engine: "YggdrasilEngine"):
        self.engine = engine
        self.command_router = ApiCommandRouter(engine)
        self._lock = threading.RLock()
        self.thor_guardian = ThorGuardian()

    def start_session(
        self, character_id: Optional[str] = None, force_new: bool = False
    ) -> Dict[str, Any]:
        with self._lock:
            try:
                should_boot = force_new or not bool(self.engine.state.player_character)
                if should_boot:
                    default_character = character_id or "adventurer"
                    self.engine.new_session(default_character)

                opening_text = self.engine.get_opening_narration()
                return {
                    "ok": True,
                    "text": opening_text,
                    "status": build_status_payload(self.engine),
                    "session_id": self.engine.state.session_id,
                }
            except Exception as exc:
                logger.warning("API session start failed: %s", exc)
                return {"ok": False, "error": "Failed to start session."}

    def process_text(self, text: str) -> Dict[str, Any]:
        with self._lock:
            clean_text = self.thor_guardian.sanitize_text_input(text, max_length=4000)
            if not clean_text:
                return {"ok": False, "error": "Input text is required."}

            try:
                if clean_text.startswith("/") or clean_text.startswith("\\"):
                    # Normalize backslash to forward slash to prevent fallback to AI
                    clean_text = "/" + clean_text[1:]
                    reply, should_close = self.command_router.handle(clean_text)
                    return {
                        "ok": True,
                        "text": reply,
                        "is_command": True,
                        "session_closed": should_close,
                        "status": build_status_payload(self.engine),
                    }

                response_text = self.engine.process_action(clean_text)
                return {
                    "ok": True,
                    "text": response_text,
                    "is_command": False,
                    "session_closed": False,
                    "status": build_status_payload(self.engine),
                }
            except Exception as exc:
                logger.warning("API text processing failed: %s", exc)
                return {"ok": False, "error": "Input could not be processed."}


def build_status_payload(engine: "YggdrasilEngine") -> Dict[str, Any]:
    """Build structured status payload for frontend clients."""
    character = engine.state.player_character or {}
    _fget = getattr(engine, "_fuzzy_get", lambda d, k, df: d.get(k, df))
    return {
        "session_id": engine.state.session_id,
        "turn": engine.state.turn_count,
        "location": {
            "city_id": engine.state.current_location_id,
            "sub_location_id": engine.state.current_sub_location_id,
            "display": engine.get_current_location_display(),
        },
        "player": {
            "name": _fget(character, "name", "Unknown")
            .replace("_", " ")
            .title(),
            "class": _fget(character, "class", "Unknown"),
            "image": _fget(character, "image", ""),
        },
        "chaos": engine.get_chaos_status(),
        "npcs_present": [
            npc.get("identity", {}).get("name", npc.get("id", "Unknown"))
            for npc in engine.state.npcs_present
        ],
    }


class SagaApiRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Norse Saga HTTPS API."""

    server_version = "NorseSagaHTTPSAPI/1.1"

    def do_GET(self) -> None:  # noqa: N802
        self._dispatch_request("GET")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch_request("POST")

    def _dispatch_request(self, method: str) -> None:
        server = self.server
        bridge: ApiGameBridge = getattr(server, "bridge")

        # Health check bypass — always accessible regardless of auth config.
        if method == "GET" and self.path == "/api/v1/health":
            self._send_json(HTTPStatus.OK, {"ok": True, "status": "healthy"})
            return

        if not self._is_authorized(server):
            self._send_json(
                HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "Unauthorized"}
            )
            return

        if method == "GET" and self.path == "/api/v1/health":
            self._send_json(HTTPStatus.OK, {"ok": True, "status": "healthy"})
            return

        if method == "GET" and self.path == "/api/v1/status":
            self._send_json(
                HTTPStatus.OK,
                {"ok": True, "status": build_status_payload(bridge.engine)},
            )
            return

        if method == "GET" and self.path == "/api/v1/characters":
            characters = bridge.engine._load_all_characters()
            # Filter for characters likely intended for players (e.g. in player_characters folder)
            player_chars = [
                {
                    "id": c.get("id"),
                    "name": bridge.engine._fuzzy_get(c, "name", c.get("id"))
                    .replace("_", " ")
                    .title(),
                    "class": bridge.engine._fuzzy_get(c, "class", "Unknown"),
                    "image": bridge.engine._fuzzy_get(c, "image", ""),
                    "summary": bridge.engine.get_character_sheet_for_data(c)
                    if hasattr(bridge.engine, "get_character_sheet_for_data")
                    else "",
                }
                for c in characters
                if "player_characters" in c.get("_source_path", "")
            ]
            self._send_json(HTTPStatus.OK, {"ok": True, "characters": player_chars})
            return

        if method == "GET" and self.path == "/api/v1/logs":
            self._send_json(
                HTTPStatus.OK, {"ok": True, "logs": log_buffer_handler.get_logs()}
            )
            return

        if method == "POST" and self.path == "/api/v1/session/start":
            payload = self._read_json_body()
            response = bridge.start_session(
                character_id=payload.get("character_id"),
                force_new=bool(payload.get("force_new", False)),
            )
            self._send_json(
                HTTPStatus.OK if response.get("ok") else HTTPStatus.BAD_REQUEST,
                response,
            )
            return

        if method == "POST" and self.path == "/api/v1/input":
            payload = self._read_json_body()
            response = bridge.process_text(str(payload.get("text", "")))
            code = HTTPStatus.OK if response.get("ok") else HTTPStatus.BAD_REQUEST
            self._send_json(code, response)
            return

        # ── Debug endpoints ──────────────────────────────────────────────────
        if method == "GET" and self.path == "/api/debug/emotions":
            eng = bridge.engine
            snapshot: Dict[str, Any] = {}

            # Per-character EmotionalEngine states
            for char_id, ee in getattr(eng, "_emotional_engines", {}).items():
                try:
                    snapshot[char_id] = {
                        "emotions": ee.get_all_emotions(),
                        "nature": ee.profile.nature_summary(),
                        "tf_axis": ee.profile.tf_axis,
                        "chronotype": ee.profile.chronotype,
                        "decay_rate": ee.profile.decay_rate,
                    }
                except Exception as ee_exc:
                    snapshot[char_id] = {"error": str(ee_exc)}

            # StressSystem levels
            stress_snapshot: Dict[str, Any] = {}
            ss = getattr(eng, "stress_system", None)
            if ss:
                for cid, acc in getattr(ss, "_registry", {}).items():
                    try:
                        stress_snapshot[cid] = {
                            "stress_level": acc.stress_level,
                            "label": acc.label,
                            "suppressed_total": (
                                sum(acc.suppressed_pool.values())
                                if hasattr(acc, "suppressed_pool")
                                else 0
                            ),
                        }
                    except Exception as se:
                        stress_snapshot[cid] = {"error": str(se)}

            self._send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "turn": getattr(eng.state, "turn_count", 0),
                    "emotional_engines": snapshot,
                    "stress_system": stress_snapshot,
                },
            )
            return

        if method == "GET" and self.path == "/api/debug/menstrual":
            eng = bridge.engine
            mcs = getattr(eng, "menstrual_cycle_system", None)
            if not mcs:
                self._send_json(
                    HTTPStatus.NOT_IMPLEMENTED,
                    {
                        "ok": False,
                        "error": "Menstrual cycle system disabled or missing",
                    },
                )
                return

            ms_snapshot: Dict[str, Any] = {}
            for char_id, state in getattr(mcs, "_registry", {}).items():
                try:
                    phase = state.current_phase()
                    ms_snapshot[char_id] = {
                        "cycle_day": state.cycle_day,
                        "cycle_length": state.cycle_length,
                        "phase_name": phase.name,
                        "energy_delta": state.energy_delta(),
                        "emotion_multipliers": {
                            ch: state.emotion_multiplier(ch)
                            for ch in phase.emotion_multiplier
                        },
                        "behavior_bias": state.behavior_bias(),
                        "sensitivity": state.sensitivity,
                        "is_premenopausal": state.is_premenopausal,
                        "narrator_str": state.to_prompt_string(),
                    }
                except Exception as me:
                    ms_snapshot[char_id] = {"error": str(me)}

            self._send_json(
                HTTPStatus.OK, {"ok": True, "menstrual_states": ms_snapshot}
            )
            return

        self._send_json(
            HTTPStatus.NOT_FOUND, {"ok": False, "error": "Route not found."}
        )

    def _is_authorized(self, server: ThreadingHTTPServer) -> bool:
        expected_token = getattr(server, "api_token", "")
        if not expected_token:
            return False

        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return False
        supplied_token = auth_header.replace("Bearer ", "", 1).strip()
        return ThorGuardian.safe_compare_secrets(expected_token, supplied_token)

    def _read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0") or "0")
        if content_length <= 0:
            return {}
        max_payload = 64 * 1024
        if content_length > max_payload:
            logger.warning("Rejected request body over limit: %s", content_length)
            return {}
        body = self.rfile.read(content_length)
        try:
            payload = json.loads(body.decode("utf-8"))
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    def _send_json(self, status_code: HTTPStatus, payload: Dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format_str: str, *args: Any) -> None:
        logger.info("API request: " + format_str, *args)


def create_secure_api_server(runtime: ApiRuntimeConfig) -> ThreadingHTTPServer:
    """Create HTTPS API server and enforce cert/token requirements."""
    if not runtime.bearer_token:
        raise ValueError("API token missing. Set api.token or NORSE_API_TOKEN.")
    if not runtime.tls_cert_path or not runtime.tls_key_path:
        raise ValueError(
            "TLS cert/key required. Set api.tls_cert_path and api.tls_key_path."
        )

    cert_path = Path(runtime.tls_cert_path)
    key_path = Path(runtime.tls_key_path)
    if not cert_path.exists() or not key_path.exists():
        raise ValueError("TLS cert/key files not found.")

    from core.engine import create_engine

    engine = create_engine(runtime.config_path)
    api_key = os.getenv("OPENROUTER_API_KEY") or _load_yaml_config(
        runtime.config_path
    ).get("openrouter", {}).get("api_key", "")
    if api_key:
        try:
            engine.initialize_ai(api_key)
        except Exception as exc:
            logger.warning("AI initialization failed in API mode: %s", exc)

    _install_log_buffer_handler()
    server = ThreadingHTTPServer((runtime.host, runtime.port), SagaApiRequestHandler)
    server.bridge = ApiGameBridge(engine)
    server.api_token = runtime.bearer_token
    server.request_started_at = int(time.time())

    tls_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    tls_context.minimum_version = ssl.TLSVersion.TLSv1_2
    tls_context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
    server.socket = tls_context.wrap_socket(server.socket, server_side=True)
    return server


def run_secure_api_server(config_path: str = "config.yaml") -> None:
    """Run the Norse Saga HTTPS API server."""
    runtime = load_api_runtime_config(config_path)
    server = create_secure_api_server(runtime)
    logger.info("Norse Saga API listening on https://%s:%s", runtime.host, runtime.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down API server")
    finally:
        try:
            server.bridge.engine.shutdown()
        except Exception as exc:
            logger.warning("Engine shutdown during API stop failed: %s", exc)
        server.server_close()
