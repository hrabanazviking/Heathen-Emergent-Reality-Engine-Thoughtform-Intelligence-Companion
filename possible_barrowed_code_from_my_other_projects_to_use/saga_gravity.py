"""
Saga Gravity — Long-term Legend Cohesion (10-50+ turns)

Past events become narrative anchors that accumulate weight over time.
The longer an anchor persists, the stronger its gravitational pull
on the story — naturally resurfacing in narration and NPC behavior.

Part of the Norse Saga Engine Myth Engine (v4.2.0)
"""
import logging

logger = logging.getLogger(__name__)


class SagaGravity:
    """Long-term consequence layer — events grow in narrative weight."""

    def __init__(self):
        self.anchors = []
        self.max_anchors = 20
        self.cull_to = 15
        self.growth_rate = 1.05  # 5% per turn — exponential

    def add_anchor(self, theme, turn_count):
        """Add a new narrative anchor from a significant event."""
        # Avoid duplicate themes
        for existing in self.anchors:
            if existing["theme"].lower() == theme.lower():
                existing["gravity"] += 0.5  # Reinforce existing anchor
                existing["last_referenced"] = turn_count
                logger.info(f"Saga anchor reinforced: {theme} (gravity: {existing['gravity']:.2f})")
                return

        self.anchors.append({
            "theme": theme,
            "origin_turn": turn_count,
            "gravity": 1.0,
            "last_referenced": turn_count,
        })
        logger.info(f"Saga anchor created: {theme}")

    def update(self):
        """Grow all anchor gravity and cull weak ones if list is too large."""
        for anchor in self.anchors:
            anchor["gravity"] *= self.growth_rate

        # Cull weak old anchors if the list grows too large
        if len(self.anchors) > self.max_anchors:
            self.anchors.sort(key=lambda a: a["gravity"], reverse=True)
            self.anchors = self.anchors[:self.cull_to]

    def get_strongest_theme(self):
        """Return the theme with the highest gravity, or None."""
        if not self.anchors:
            return None
        strongest = max(self.anchors, key=lambda a: a["gravity"])
        return strongest["theme"]

    def build_context(self):
        """Build the saga gravity context block for prompt injection."""
        if not self.anchors:
            return ""
        top = sorted(self.anchors, key=lambda a: a["gravity"], reverse=True)[:3]
        lines = "\n".join([
            f"  - {a['theme']} "
            f"(pull: {'STRONG' if a['gravity'] > 2.0 else 'medium' if a['gravity'] > 1.3 else 'faint'}, "
            f"origin: turn {a['origin_turn']})"
            for a in top
        ])
        return (
            "=== SAGA GRAVITY — ECHOES PULLING ON THE WORLD ===\n"
            "Major narrative anchors accumulating weight.\n"
            "These themes may naturally resurface in narration, NPC memory, or consequences.\n"
            f"{lines}"
        )

    def to_dict(self):
        """Serialize for save."""
        return {
            "anchors": self.anchors,
        }

    def from_dict(self, data):
        """Restore from save."""
        if data:
            self.anchors = data.get("anchors", [])
