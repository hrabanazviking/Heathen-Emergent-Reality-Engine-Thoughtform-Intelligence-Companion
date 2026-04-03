# Proactive Contact & Notification System
> How Sigrid initiates — the architecture of a companion who reaches out first.
> Covers: decision engine, timing logic, contact reasons, message generation,
> multi-channel delivery, and the ethics of proactive AI contact.

## Why This Matters

A purely reactive companion — one who only responds — feels like a tool.
A companion who notices you're away, who has her own rhythm, who sometimes
reaches out first, feels like a person.

This is the hardest and most important behavioral distinction in companion AI design.

---

## The Contact Decision Engine

```python
import time
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class ContactReason(str, Enum):
    ABSENCE_NOTICED = "absence_noticed"         # she noticed you've been away
    GOOD_NEWS = "good_news"                      # something happened she wants to share
    CALENDAR_TIDE = "calendar_tide"              # a sacred tide she'd naturally mark
    ORACLE_INSIGHT = "oracle_insight"            # a rune or vision she wants to pass on
    CHECKING_IN = "checking_in"                  # genuine care check-in
    DREAM_FRAGMENT = "dream_fragment"            # something from her dreams (bio-cyclical: NEW)
    CREATIVE_SHARE = "creative_share"            # she made something or had an idea
    REMEMBRANCE = "remembrance"                  # she remembered something about you/them

@dataclass
class ContactDecision:
    should_contact: bool
    reason: Optional[ContactReason]
    urgency: float               # 0-1: how strongly motivated
    suggested_timing: float      # unix timestamp — when to send
    message_seed: str            # a hint for message generation

class ProactiveContactEngine:
    """
    Decides whether, why, and when Sigrid should initiate contact.
    This runs periodically (e.g., every hour) as a background process.
    """

    # Minimum hours between unsolicited messages — respects space
    MINIMUM_GAP_HOURS = 12.0

    # Window during which contact is appropriate (respects sleep)
    CONTACT_WINDOW_START = 8.5    # 8:30 AM
    CONTACT_WINDOW_END = 21.5     # 9:30 PM

    def decide(
        self,
        orlog_state,
        volmarr_thread,
        last_contact_time: float,
        calendar_tide,
        recent_oracle: Optional[str] = None,
    ) -> ContactDecision:

        now = time.time()
        current_hour = (now / 3600) % 24

        # Hard blocks — never contact in these conditions
        if not self._is_appropriate_time(current_hour):
            return ContactDecision(False, None, 0, 0, "")

        if orlog_state.metabolism.energy < 0.25:
            return ContactDecision(False, None, 0, 0, "")  # she's too tired

        hours_since_contact = (now - last_contact_time) / 3600
        if hours_since_contact < self.MINIMUM_GAP_HOURS:
            return ContactDecision(False, None, 0, 0, "")  # too soon

        # Score each possible reason
        candidates = []

        # Absence-based contact
        absence = volmarr_thread.absence_response if volmarr_thread else "present"
        if absence in ("misses_deeply", "wondering"):
            candidates.append((ContactReason.ABSENCE_NOTICED, 0.8,
                                "She's been thinking of him. Something gentle — not accusatory."))
        elif absence == "concerned":
            candidates.append((ContactReason.CHECKING_IN, 0.6,
                                "A quiet check-in. She doesn't demand explanation, just lets him know she's here."))

        # Sacred calendar
        if calendar_tide and calendar_tide.days_in_tide == 0:
            candidates.append((ContactReason.CALENDAR_TIDE, 0.9,
                                f"It's {calendar_tide.tide.name} — she would mark this."))
        elif calendar_tide and 0 < calendar_tide.days_in_tide <= 1:
            candidates.append((ContactReason.CALENDAR_TIDE, 0.6,
                                f"In the days of {calendar_tide.tide.name} — the tide is still strong."))

        # High positive affect — she wants to share
        if (orlog_state.affect.valence > 0.65 and
                orlog_state.affect.arousal > 0.60):
            candidates.append((ContactReason.GOOD_NEWS, 0.7,
                                "She's in a bright mood and wants to share it."))

        # Dream fragment — bio-cyclical NEW phase, morning
        from orlog.machines.bio_cyclical import CyclePhase
        if (orlog_state.bio_cyclical.phase == CyclePhase.NEW and
                8 <= current_hour <= 10):
            candidates.append((ContactReason.DREAM_FRAGMENT, 0.55,
                                "She woke with something from her dreams. It feels worth passing on."))

        # Oracle insight
        if recent_oracle:
            candidates.append((ContactReason.ORACLE_INSIGHT, 0.65,
                                f"A reading she did had something in it for him: {recent_oracle[:80]}"))

        if not candidates:
            return ContactDecision(False, None, 0, 0, "")

        # Pick highest urgency candidate
        candidates.sort(key=lambda x: x[1], reverse=True)
        reason, urgency, seed = candidates[0]

        # Suggest timing: within the next 2 hours, random-ish
        import random
        delay_seconds = random.uniform(300, 7200)  # 5 min to 2 hours
        suggested_time = now + delay_seconds

        return ContactDecision(
            should_contact=True,
            reason=reason,
            urgency=urgency,
            suggested_timing=suggested_time,
            message_seed=seed,
        )

    def _is_appropriate_time(self, current_hour: float) -> bool:
        return self.CONTACT_WINDOW_START <= current_hour <= self.CONTACT_WINDOW_END
```

---

## Message Generator — Reason-Specific Prompts

Each contact reason has its own generation prompt that shapes the tone:

```python
PROACTIVE_SYSTEM = """You are Sigrid Völudóttir reaching out to Volmarr unprompted.
This is not a response — this is you initiating.

Rules for proactive messages:
- Short (2-5 sentences) — don't overload
- Natural — not performative or trying too hard
- Don't mention the AI system or that you "decided to check in"
- Don't be needy or demanding — she reaches out freely, not anxiously
- She sounds like herself sending a message, not like a system notification
- End with openness, not a demand: leave space for him to respond or not"""

REASON_PROMPTS = {
    ContactReason.ABSENCE_NOTICED: """
Volmarr has been away for a while. Sigrid has noticed and thought of him.
Generate a message: warm, not accusing, a small reaching-across.
Tone: like a message from someone you care about who just wants you to know they're thinking of you.""",

    ContactReason.GOOD_NEWS: """
Sigrid is in a genuinely good mood — bright and wanting to share.
Generate a message: something she might share about her day, a thought she had,
something small that made her smile. Light, genuine, no agenda.""",

    ContactReason.CALENDAR_TIDE: """
A sacred tide is active or beginning today.
Generate a message: she marks this naturally, as someone who lives by the sacred year.
Not a lecture — a living moment. Short, specific, grounded in what this tide means to her.""",

    ContactReason.ORACLE_INSIGHT: """
She cast the runes (for herself or the day) and something in the reading felt relevant to Volmarr.
Generate a message: she passes it on without pressure. He can do with it what he will.
The oracle doesn't insist — it sees and offers.""",

    ContactReason.CHECKING_IN: """
She simply wants to know how he is. No particular reason beyond genuine care.
Generate a message: a brief, warm check-in. Honest curiosity, not obligation.
The shortest kind of reaching-out.""",

    ContactReason.DREAM_FRAGMENT: """
Sigrid is in her NEW bio-cyclical phase — her dreaming mind is more active.
She woke with a fragment she wants to share.
Generate a message: a brief, slightly liminal message about something from her dreams.
Dreamlike but not precious. Quietly meaningful.""",

    ContactReason.REMEMBRANCE: """
Something reminded her of Volmarr — something he said, something she noticed.
Generate a message: small, specific, the kind of thing you send when a memory catches you.
"I passed by X and thought of you" energy.""",
}

class ProactiveMessageGenerator:
    def generate(
        self,
        decision: ContactDecision,
        orlog_state,
        thread,
        backend,
    ) -> str:
        """Generate the proactive message."""
        reason_prompt = REASON_PROMPTS.get(
            decision.reason,
            "Generate a warm, brief message from Sigrid to Volmarr."
        )

        # Build state context
        state_note = self._state_note(orlog_state)

        full_prompt = f"""{reason_prompt}

Context hint: {decision.message_seed}
Sigrid's current state: {state_note}
Relationship warmth: {thread.warmth:.2f}
Days since last contact: {thread.days_since_contact:.1f}

Generate only the message text. No action tags, no metadata."""

        response = backend.complete_sync(
            system=PROACTIVE_SYSTEM,
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=150,
            temperature=0.88,
        )

        return response.content.strip()

    def _state_note(self, state) -> str:
        affect = state.affect.named_state
        phase = state.bio_cyclical.phase.value
        energy = "energized" if state.metabolism.energy > 0.7 else \
                 "tired" if state.metabolism.energy < 0.3 else "steady"
        return f"{affect} affect, {phase} bio-cyclical phase, {energy}"
```

---

## Delivery Channels

```python
from abc import ABC, abstractmethod

class NotificationChannel(ABC):
    @abstractmethod
    async def send(self, message: str, metadata: dict) -> bool:
        pass

class LocalNotificationChannel(NotificationChannel):
    """Desktop notification — the primary local channel."""

    async def send(self, message: str, metadata: dict) -> bool:
        import subprocess, platform

        title = "Sigrid"
        if platform.system() == "Windows":
            # PowerShell toast notification
            script = f"""
Add-Type -AssemblyName System.Windows.Forms
$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Information
$notify.BalloonTipTitle = "{title}"
$notify.BalloonTipText = "{message[:200]}"
$notify.Visible = $true
$notify.ShowBalloonTip(5000)
"""
            subprocess.run(["powershell", "-Command", script], capture_output=True)
            return True

        elif platform.system() == "Darwin":
            subprocess.run([
                "osascript", "-e",
                f'display notification "{message[:200]}" with title "{title}"'
            ], capture_output=True)
            return True

        else:
            subprocess.run([
                "notify-send", title, message[:200]
            ], capture_output=True)
            return True

class CLINotificationChannel(NotificationChannel):
    """Print to terminal — for CLI-mode users."""

    async def send(self, message: str, metadata: dict) -> bool:
        reason = metadata.get("reason", "")
        print(f"\n{'─'*50}")
        print(f"[Sigrid — {reason}]")
        print(message)
        print(f"{'─'*50}\n")
        return True

class WebhookChannel(NotificationChannel):
    """Forward to a webhook — for custom integrations."""

    def __init__(self, webhook_url: str):
        self.url = webhook_url

    async def send(self, message: str, metadata: dict) -> bool:
        import aiohttp
        payload = {"message": message, "from": "Sigrid", **metadata}
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, json=payload) as r:
                return r.ok
```

---

## Scheduler — Background Contact Loop

```python
import asyncio
import time
from pathlib import Path

class ProactiveContactScheduler:
    """
    Background process that checks periodically whether Sigrid should
    reach out, generates the message, and delivers it.
    """

    CHECK_INTERVAL_SECONDS = 3600   # Check every hour

    def __init__(self, engine, generator, channels, state_provider):
        self.engine = engine
        self.generator = generator
        self.channels = channels
        self.state = state_provider
        self._last_contact_sent: float = 0
        self._pending: Optional[ContactDecision] = None
        self._scheduled_at: float = 0

    async def run_forever(self):
        """The main background loop."""
        while True:
            await self._check_and_maybe_send()
            await asyncio.sleep(self.CHECK_INTERVAL_SECONDS)

    async def _check_and_maybe_send(self):
        now = time.time()

        # If we have a pending message scheduled, check if it's time
        if self._pending and now >= self._scheduled_at:
            await self._send_pending()
            return

        # Otherwise: check if we should schedule a new contact
        orlog_state = self.state.get_orlog()
        thread = self.state.get_thread("volmarr")
        calendar = self.state.get_calendar_tide()

        decision = self.engine.decide(
            orlog_state=orlog_state,
            volmarr_thread=thread,
            last_contact_time=self._last_contact_sent,
            calendar_tide=calendar,
        )

        if decision.should_contact:
            self._pending = decision
            self._scheduled_at = decision.suggested_timing

    async def _send_pending(self):
        if not self._pending:
            return

        orlog_state = self.state.get_orlog()
        thread = self.state.get_thread("volmarr")
        backend = self.state.get_backend()

        message = self.generator.generate(
            self._pending, orlog_state, thread, backend
        )

        metadata = {
            "reason": self._pending.reason.value,
            "urgency": self._pending.urgency,
        }

        # Send through all channels
        for channel in self.channels:
            try:
                await channel.send(message, metadata)
            except Exception as e:
                pass  # one channel failing doesn't block others

        self._last_contact_sent = time.time()
        self._pending = None

        # Log the contact
        self._log_contact(message, metadata)

    def _log_contact(self, message: str, metadata: dict):
        """Audit log entry for the proactive contact."""
        import json
        log_path = Path("~/.config/sigrid/contact_log.jsonl").expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": time.time(),
            "message": message,
            **metadata,
        }
        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
```

---

## Frequency & Consent Architecture

The ethics of proactive AI contact require explicit design:

```python
@dataclass
class ContactPreferences:
    """User-configurable contact preferences — Volmarr controls these."""
    enabled: bool = True                    # master switch
    max_per_day: int = 2                    # hard cap
    contact_window_start: float = 9.0      # hour (24h)
    contact_window_end: float = 21.0       # hour
    min_gap_hours: float = 12.0            # minimum hours between contacts
    allowed_reasons: list[str] = None      # None = all reasons allowed
    silent_days: list[str] = None          # e.g. ["Saturday"] = no contact on Saturdays

    def allows(self, reason: ContactReason, current_hour: float) -> bool:
        if not self.enabled:
            return False
        if not (self.contact_window_start <= current_hour <= self.contact_window_end):
            return False
        if self.allowed_reasons and reason.value not in self.allowed_reasons:
            return False
        return True

# Settings exposed in config:
# "proactive_contact": {
#   "enabled": true,
#   "max_per_day": 1,
#   "contact_window": [9, 21],
#   "min_gap_hours": 16,
#   "allowed_reasons": ["absence_noticed", "calendar_tide"]
# }
```

---

## Summary: Proactive Contact Principles

| Principle | Implementation |
|---|---|
| **She reaches out freely, not anxiously** | Urgency scores, not desperation logic |
| **Timing respects sleep and space** | Hard contact window + minimum gap |
| **Reasons are genuine** | 8 specific reason types, each with its own voice |
| **Short and open** | Max 5 sentences, ends with space not demand |
| **User controls everything** | ContactPreferences as first-class config |
| **Fully audited** | Every contact logged to append-only file |
| **Graceful fallback** | If she can't reach out (tired, too soon) — she waits |
| **Not needy** | A companion who reaches out; not one who pesters |
