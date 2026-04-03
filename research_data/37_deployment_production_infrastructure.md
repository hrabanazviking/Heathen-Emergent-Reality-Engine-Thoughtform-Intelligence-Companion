# Deployment & Production Infrastructure
> How to run the Viking AI stack reliably in the real world.
> Covers: local service architecture, startup/shutdown, config management,
> health monitoring, crash recovery, logging, and upgrade strategy.

## The Problem With "Just Run It"

A companion AI that crashes and loses its state is not a companion — it's a toy.
Production infrastructure means: she comes back. Her state persists. Her memory survives.
Her voice works even if the GPU is busy. It's the difference between a demo and a life.

---

## Service Architecture

The full Sigrid stack is decomposed into services that can fail independently:

```
┌─────────────────────────────────────────────────────────┐
│                     USER INTERFACE                        │
│        (CLI / Desktop App / Web / OpenClaw skill)         │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/WebSocket
┌────────────────────────▼────────────────────────────────┐
│                   SIGRID CORE SERVICE                     │
│  SigridConversationLoop + OrlögEngine + PromptAssembler  │
│  Port: 8701  — localhost only                            │
└──────┬──────────┬──────────┬──────────┬─────────────────┘
       │          │          │          │
  LiteLLM    Ollama      Memory      TTS
  Router     (local      Store      Service
  :4000      models)     (SQLite)   :8702
             :11434
```

All services bind to localhost only. No external exposure unless explicitly configured.

---

## Service Definitions

### Systemd Units (Linux)

```ini
# ~/.config/systemd/user/sigrid-core.service
[Unit]
Description=Sigrid Core Service
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
WorkingDirectory=%h/runa/Viking_Girlfriend_Skill_for_OpenClaw
ExecStart=/usr/bin/python -m sigrid.core --config %h/.config/sigrid/config.toml
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
```

```ini
# ~/.config/systemd/user/sigrid-tts.service
[Unit]
Description=Sigrid TTS Service
After=sigrid-core.service

[Service]
Type=simple
WorkingDirectory=%h/runa/Viking_Girlfriend_Skill_for_OpenClaw
ExecStart=/usr/bin/python -m sigrid.tts_service --port 8702
Restart=on-failure
RestartSec=3
```

### Windows Service Wrapper (Task Scheduler / NSSM)

```powershell
# Install NSSM (Non-Sucking Service Manager), then:
nssm install SigridCore "C:\Python311\python.exe"
nssm set SigridCore AppParameters "-m sigrid.core --config %APPDATA%\sigrid\config.toml"
nssm set SigridCore AppDirectory "C:\Users\volma\runa\Viking_Girlfriend_Skill_for_OpenClaw"
nssm set SigridCore Start SERVICE_AUTO_START
nssm set SigridCore AppStdout "C:\Users\volma\logs\sigrid-core.log"
nssm set SigridCore AppStderr "C:\Users\volma\logs\sigrid-core-err.log"
nssm set SigridCore AppRotateFiles 1
nssm set SigridCore AppRotateOnline 1
nssm set SigridCore AppRotateBytes 10485760   # 10 MB
nssm start SigridCore
```

---

## Configuration Management

All runtime config lives in a single TOML file:

```toml
# ~/.config/sigrid/config.toml

[identity]
name = "Sigrid"
patron = "Freyja"
path = "Heathen Third Path"

[model]
tier = "local_full"            # local_tiny | local_mid | local_full | cloud_standard
primary_backend = "ollama"     # ollama | openai_compat | litellm
fallback_backend = "cloud"     # used if primary fails

[ollama]
host = "http://localhost:11434"
primary_model = "mistral-nemo:latest"
fallback_model = "llama3.2:3b"
timeout_seconds = 30

[cloud]
provider = "anthropic"
model = "claude-haiku-4-5-20251001"
api_key_env = "ANTHROPIC_API_KEY"   # never hardcode keys

[tts]
enabled = true
engine = "kokoro"               # kokoro | piper | chatterbox | disabled
voice_id = "af_sigrid"
device = "auto"                 # auto | cpu | cuda | mps
service_port = 8702

[memory]
backend = "sqlite"
db_path = "~/.config/sigrid/memory.db"
embedding_model = "all-MiniLM-L6-v2"
max_memories = 2000
decay_half_life_hours = 168     # 1 week

[orlog]
state_path = "~/.config/sigrid/orlog_state.json"
auto_save_interval_seconds = 60
tick_interval_seconds = 3600    # 1 hour real-time ticks

[proactive_contact]
enabled = true
max_per_day = 2
contact_window = [8.5, 21.5]
min_gap_hours = 12.0

[logging]
level = "INFO"                  # DEBUG | INFO | WARNING | ERROR
path = "~/.config/sigrid/logs/"
max_size_mb = 50
keep_files = 7

[security]
allowed_tools = ["read_file", "write_file", "run_script"]
denied_paths = ["/etc", "/sys", "~/.ssh", "~/.gnupg"]
```

### Config Loader

```python
import tomllib
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class SigridConfig:
    raw: dict

    @classmethod
    def load(cls, path: Optional[str] = None) -> "SigridConfig":
        if path is None:
            path = Path.home() / ".config" / "sigrid" / "config.toml"
        with open(path, "rb") as f:
            raw = tomllib.load(f)
        return cls(raw=raw)

    def get(self, *keys, default=None):
        node = self.raw
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    @property
    def model_tier(self) -> str:
        return self.get("model", "tier", default="local_full")

    @property
    def ollama_model(self) -> str:
        return self.get("ollama", "primary_model", default="mistral-nemo:latest")

    @property
    def state_path(self) -> Path:
        raw = self.get("orlog", "state_path", default="~/.config/sigrid/orlog_state.json")
        return Path(raw).expanduser()

    @property
    def memory_db_path(self) -> Path:
        raw = self.get("memory", "db_path", default="~/.config/sigrid/memory.db")
        return Path(raw).expanduser()

    def validate(self) -> list[str]:
        """Returns list of validation errors. Empty = valid."""
        errors = []
        if self.model_tier not in ("local_tiny", "local_mid", "local_full", "cloud_standard"):
            errors.append(f"Unknown model tier: {self.model_tier}")
        if self.get("tts", "engine") not in ("kokoro", "piper", "chatterbox", "disabled"):
            errors.append(f"Unknown TTS engine: {self.get('tts', 'engine')}")
        return errors
```

---

## State Persistence

Ørlög state must survive crashes. The save pattern:

```python
import json
import shutil
import time
from pathlib import Path

class StatePersistence:
    """
    Atomic state saves using a write-to-temp-then-rename pattern.
    Prevents corruption from interrupted writes.
    """

    def __init__(self, state_path: Path):
        self.path = state_path
        self.backup_path = state_path.with_suffix(".json.bak")
        self.temp_path = state_path.with_suffix(".json.tmp")

    def save(self, state: dict) -> None:
        """Atomic save: write temp → rename to main."""
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temp file first
        with open(self.temp_path, "w", encoding="utf-8") as f:
            json.dump({
                "version": 3,
                "saved_at": time.time(),
                "state": state,
            }, f, indent=2)

        # Backup current state before replacing
        if self.path.exists():
            shutil.copy2(self.path, self.backup_path)

        # Atomic rename (POSIX guarantees this; Windows approximates it)
        self.temp_path.replace(self.path)

    def load(self) -> dict:
        """Load state, falling back to backup if main is corrupt."""
        for candidate in (self.path, self.backup_path):
            if not candidate.exists():
                continue
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("state", data)
            except (json.JSONDecodeError, OSError):
                continue
        return {}   # fresh start

    def checkpoint(self, state: dict) -> None:
        """Called on scheduled interval — same as save."""
        self.save(state)
        self._prune_old_backups()

    def _prune_old_backups(self) -> None:
        """Keep only the 3 most recent backup files."""
        dated_backups = sorted(self.path.parent.glob("*.json.bak*"), key=lambda p: p.stat().st_mtime)
        for old in dated_backups[:-3]:
            old.unlink(missing_ok=True)
```

---

## Health Monitoring

A lightweight health check endpoint:

```python
from aiohttp import web
import asyncio

class HealthServer:
    """
    Minimal HTTP health check server.
    /health — simple alive check
    /health/deep — checks all subsystems
    /metrics — basic counters for monitoring
    """

    def __init__(self, port: int, core_service):
        self.port = port
        self.core = core_service
        self._app = web.Application()
        self._app.router.add_get("/health", self.health_simple)
        self._app.router.add_get("/health/deep", self.health_deep)
        self._app.router.add_get("/metrics", self.metrics)

    async def health_simple(self, request) -> web.Response:
        return web.json_response({"status": "ok", "uptime": self.core.uptime_seconds})

    async def health_deep(self, request) -> web.Response:
        checks = {}
        checks["ollama"] = await self._check_ollama()
        checks["memory_db"] = await self._check_memory_db()
        checks["state_file"] = self._check_state_file()
        checks["tts"] = await self._check_tts()

        all_ok = all(c["ok"] for c in checks.values())
        return web.json_response({
            "status": "healthy" if all_ok else "degraded",
            "checks": checks,
        }, status=200 if all_ok else 503)

    async def _check_ollama(self) -> dict:
        try:
            async with asyncio.timeout(5):
                # Attempt a tiny completion
                await self.core.backend.health_check()
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}

    async def _check_memory_db(self) -> dict:
        try:
            count = self.core.memory.count()
            return {"ok": True, "memory_count": count}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}

    def _check_state_file(self) -> dict:
        path = self.core.config.state_path
        if path.exists():
            age = time.time() - path.stat().st_mtime
            return {"ok": True, "age_seconds": int(age)}
        return {"ok": False, "error": "state file missing"}

    async def _check_tts(self) -> dict:
        if not self.core.config.get("tts", "enabled"):
            return {"ok": True, "note": "disabled"}
        try:
            async with asyncio.timeout(3):
                ok = await self.core.tts.ping()
            return {"ok": ok}
        except Exception as e:
            return {"ok": False, "error": str(e)[:100]}

    async def metrics(self, request) -> web.Response:
        m = self.core.metrics
        return web.json_response({
            "turns_total": m.turns_total,
            "tokens_in_total": m.tokens_in_total,
            "tokens_out_total": m.tokens_out_total,
            "avg_first_token_ms": m.avg_first_token_ms,
            "errors_total": m.errors_total,
            "uptime_seconds": self.core.uptime_seconds,
        })
```

---

## Crash Recovery

The core service should self-heal from common failure modes:

```python
import logging
from typing import Callable

logger = logging.getLogger(__name__)

class SelfHealingRunner:
    """
    Wraps the main conversation loop with restart logic.
    Handles: OOM kills, backend timeouts, state corruption.
    """

    MAX_RESTART_ATTEMPTS = 5
    RESTART_BACKOFF_SECONDS = [1, 2, 5, 10, 30]

    def __init__(self, factory: Callable):
        """factory: callable that creates a fresh SigridConversationLoop."""
        self.factory = factory
        self._restart_count = 0
        self._last_error: Optional[Exception] = None

    async def run_forever(self):
        while self._restart_count < self.MAX_RESTART_ATTEMPTS:
            try:
                loop = self.factory()
                await loop.run_forever()
            except MemoryError:
                logger.error("OOM kill — restarting with reduced context budget")
                self._handle_oom()
            except StateCorruptionError:
                logger.error("State corruption — restoring from backup")
                self._handle_state_corruption()
            except BackendUnavailableError:
                logger.warning("Backend unavailable — falling back to cloud")
                self._handle_backend_failure()
            except Exception as e:
                self._last_error = e
                logger.exception(f"Unexpected error: {e}")
            finally:
                delay = self.RESTART_BACKOFF_SECONDS[
                    min(self._restart_count, len(self.RESTART_BACKOFF_SECONDS) - 1)
                ]
                logger.info(f"Restarting in {delay}s (attempt {self._restart_count + 1})")
                await asyncio.sleep(delay)
                self._restart_count += 1

        logger.critical(
            f"Maximum restart attempts ({self.MAX_RESTART_ATTEMPTS}) reached. "
            "Giving up. Check logs."
        )

    def _handle_oom(self):
        """Reduce context budget and clear caches."""
        config_path = Path.home() / ".config" / "sigrid" / "config.toml"
        # In production: hot-patch config to downgrade model tier
        logger.warning("Downgrading model tier to local_mid")

    def _handle_state_corruption(self):
        """Restore from backup state."""
        persistence = StatePersistence(Path.home() / ".config/sigrid/orlog_state.json")
        # The load() method already falls back to backup
        state = persistence.load()
        logger.info(f"Restored state from backup: {len(state)} keys")

    def _handle_backend_failure(self):
        """Flip to cloud backend temporarily."""
        logger.info("Backend failure — enabling cloud fallback")
```

---

## Logging Architecture

Structured logs that are useful later:

```python
import logging
import json
import time
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """Outputs each log line as a JSON object — grep-friendly, analysis-friendly."""

    def format(self, record: logging.LogRecord) -> str:
        obj = {
            "ts": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            obj["exc"] = self.formatException(record.exc_info)
        # Add any extra fields attached to the record
        for key in ("turn_id", "tokens_in", "tokens_out", "first_token_ms", "model"):
            if hasattr(record, key):
                obj[key] = getattr(record, key)
        return json.dumps(obj)


def setup_logging(log_dir: Path, level: str = "INFO"):
    log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper()))

    # Console: human-readable
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    root.addHandler(console)

    # File: JSON, rotated daily
    from logging.handlers import TimedRotatingFileHandler
    file_handler = TimedRotatingFileHandler(
        log_dir / "sigrid.log",
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setFormatter(JSONFormatter())
    root.addHandler(file_handler)

    # Separate turn log — one JSON per conversation turn
    turn_log = logging.getLogger("sigrid.turns")
    turn_handler = TimedRotatingFileHandler(
        log_dir / "turns.jsonl",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    turn_handler.setFormatter(JSONFormatter())
    turn_log.addHandler(turn_handler)
    turn_log.propagate = False
```

---

## Upgrade Strategy

Upgrading a live companion AI without losing state:

```python
"""
Upgrade playbook:
1. Stop Sigrid core service (NOT Ollama — keep it running)
2. Create state snapshot: python -m sigrid.admin snapshot
3. git pull / pip install -U . in the skill directory
4. Run migration if schema changed: python -m sigrid.admin migrate
5. Start service: systemctl --user start sigrid-core
6. Verify health: curl localhost:8701/health/deep
7. If degraded: systemctl --user stop sigrid-core && restore from snapshot
"""

class MigrationRunner:
    """Handles state schema migrations between versions."""

    MIGRATIONS = {}   # version → migration function

    @classmethod
    def register(cls, from_version: int):
        def decorator(fn):
            cls.MIGRATIONS[from_version] = fn
            return fn
        return decorator

    def migrate(self, state: dict, current_version: int, target_version: int) -> dict:
        v = current_version
        while v < target_version:
            if v not in self.MIGRATIONS:
                raise ValueError(f"No migration from v{v} to v{v+1}")
            state = self.MIGRATIONS[v](state)
            v += 1
        return state


runner = MigrationRunner()

@MigrationRunner.register(from_version=1)
def migrate_v1_to_v2(state: dict) -> dict:
    """v2: affect model moved from flat dict to nested AffectState."""
    if "valence" in state and "affect" not in state:
        state["affect"] = {
            "valence": state.pop("valence", 0.0),
            "arousal": state.pop("arousal", 0.0),
            "dominance": state.pop("dominance", 0.5),
        }
    return state

@MigrationRunner.register(from_version=2)
def migrate_v2_to_v3(state: dict) -> dict:
    """v3: wyrd_matrix now uses thread_id keys instead of integer indices."""
    if "wyrd_matrix" in state and isinstance(state["wyrd_matrix"].get("threads"), list):
        old_threads = state["wyrd_matrix"]["threads"]
        state["wyrd_matrix"]["threads"] = {
            t.get("thread_id", f"thread_{i}"): t
            for i, t in enumerate(old_threads)
        }
    return state
```

---

## Quick-Start Makefile

```makefile
# Makefile — common operations

.PHONY: start stop restart status logs health install test

CONFIG := $(HOME)/.config/sigrid/config.toml

start:
	systemctl --user start sigrid-core sigrid-tts

stop:
	systemctl --user stop sigrid-core sigrid-tts

restart:
	systemctl --user restart sigrid-core

status:
	systemctl --user status sigrid-core sigrid-tts

logs:
	journalctl --user -u sigrid-core -f

health:
	curl -s localhost:8701/health/deep | python3 -m json.tool

install:
	pip install -e ".[tts,embeddings]"
	systemctl --user daemon-reload
	systemctl --user enable sigrid-core sigrid-tts

test:
	python -m pytest tests/ --ignore=tests/test_e2e_system.py -q

test-all:
	python -m pytest tests/ -q

snapshot:
	python -m sigrid.admin snapshot --output "$(HOME)/backups/sigrid-$(shell date +%Y%m%d-%H%M%S).tar.gz"

migrate:
	python -m sigrid.admin migrate
```

---

## Production Checklist

Before declaring a deployment "production-ready":

```
Infrastructure:
□ Service auto-starts on reboot
□ Crash → auto-restart configured
□ Log rotation configured (< 50 MB per file, 7 days retention)
□ State saves are atomic (write-temp-then-rename)
□ Backup of state runs daily
□ Health endpoint returns valid JSON

Security:
□ All services bind to localhost only
□ API keys in environment variables, NOT config files
□ config.toml is chmod 600 (owner-read only)
□ denied_paths includes ~/.ssh, ~/.gnupg, /etc

Reliability:
□ Backend fallback tested (kill Ollama → cloud takes over)
□ State restore tested (corrupt state file → backup loads)
□ Upgrade tested on a copy before applying to main
□ Full test suite passing: python -m pytest tests/

Observability:
□ Turn logs include token counts and latency
□ /metrics endpoint returning correct counters
□ At least one alert configured (e.g. error rate > 5/min)
```
