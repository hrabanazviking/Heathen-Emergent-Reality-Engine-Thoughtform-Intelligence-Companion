"""
Story Phase — Archetypal Arc Direction (10-20 turns per phase)

The monomyth cycle guiding overall narrative momentum. The story
naturally progresses through archetypal phases, each coloring
the emotional texture and type of events that emerge.

Part of the Norse Saga Engine Myth Engine (v4.2.0)
"""
import logging

logger = logging.getLogger(__name__)

STORY_PHASES = [
    ("awakening", "discovery, curiosity, new bonds forming"),
    ("exploration", "growth, expanding horizons, forging alliances"),
    ("challenge", "rising conflict, tests of character, pressure building"),
    ("descent", "darkness, difficult choices, facing shadow"),
    ("revelation", "truth emerging, fate becoming clear, turning points"),
    ("transformation", "deep change, identity shift, crossing thresholds"),
    ("integration", "healing, wisdom gained, new equilibrium"),
]

_MAX_PHASE_INDEX = len(STORY_PHASES) - 1


class StoryPhase:
    """Archetypal arc layer — the monomyth cycle shaping narrative momentum."""

    def __init__(self):
        self.phase_index = 0
        self.phase_turn_start = 0
        self.turns_per_phase = 15
        self.cycle_count = 0  # How many full cycles completed

    @property
    def current_phase(self):
        return STORY_PHASES[self.phase_index]

    @property
    def phase_name(self):
        return self.current_phase[0]

    @property
    def phase_description(self):
        return self.current_phase[1]

    def update(self, turn_count, force_advance=False):
        """Advance the story phase if enough turns have passed."""
        try:
            turns_in_phase = turn_count - self.phase_turn_start
            if turns_in_phase > self.turns_per_phase or force_advance:
                old_phase = self.phase_name
                self.phase_index = (self.phase_index + 1) % len(STORY_PHASES)
                self.phase_turn_start = turn_count
                if self.phase_index == 0:
                    self.cycle_count += 1
                logger.info(
                    "Story phase advanced: %s → %s (cycle %d)",
                    old_phase, self.phase_name, self.cycle_count,
                )
        except Exception:
            logger.error(
                "StoryPhase.update() failed (turn_count=%r); resetting phase_index to 0.",
                turn_count,
                exc_info=True,
            )
            self.phase_index = 0

    def build_context(self):
        """Build the story phase context block for prompt injection."""
        try:
            name, desc = self.current_phase
            cycle_note = f" (saga cycle {self.cycle_count + 1})" if self.cycle_count > 0 else ""
            return (
                "=== STORY ARC PHASE ===\n"
                f"Current Phase: {name.upper()}{cycle_note}\n"
                f"Themes: {desc}\n"
                "Narration should reflect the emotional texture of this phase."
            )
        except Exception:
            logger.error(
                "StoryPhase.build_context() failed (phase_index=%r); returning empty string.",
                self.phase_index,
                exc_info=True,
            )
            return ""

    def to_dict(self):
        """Serialize for save."""
        try:
            return {
                "phase_index": self.phase_index,
                "phase_turn_start": self.phase_turn_start,
                "cycle_count": self.cycle_count,
            }
        except Exception:
            logger.error(
                "StoryPhase.to_dict() failed; returning default dict.",
                exc_info=True,
            )
            return {"phase_index": 0, "phase_turn_start": 0, "cycle_count": 0}

    def from_dict(self, data):
        """Restore from save."""
        try:
            if data:
                raw_index = data.get("phase_index", 0)
                # Clamp to valid range — a corrupted save must not cause IndexError
                self.phase_index = max(0, min(int(raw_index), _MAX_PHASE_INDEX))
                if self.phase_index != raw_index:
                    logger.warning(
                        "StoryPhase.from_dict() clamped phase_index %r → %d.",
                        raw_index, self.phase_index,
                    )
                self.phase_turn_start = data.get("phase_turn_start", 0)
                self.cycle_count = data.get("cycle_count", 0)
        except Exception:
            logger.error(
                "StoryPhase.from_dict() failed; leaving current state unchanged.",
                exc_info=True,
            )
