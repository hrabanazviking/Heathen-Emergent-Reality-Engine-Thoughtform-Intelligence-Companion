"""
Grunnr lifecycle — ceremony state machine and observer hooks.

The five True Names of ceremony (NAMING.md §Lifecycle States) map onto the enum
``LifecycleState``. The sub-states that Holdvörðr tracks internally (READY, OPENING,
RECOVERING, EXTINGUISHED, CONFIG_ERROR) are also present — per CEREMONY.md §8 they are
implementation details, not public ceremony phases. The distinction is preserved in the
enum via the is_public_phase property.

The ``Lifecycle`` class holds the authoritative current state and calls registered
observers whenever the state changes. This is the primary internal event bus for the
Python-side runtime in v0.1 (before the Tauri IPC bus exists at v0.4).

Ref:
    docs/NAMING.md §Lifecycle States
    docs/architecture/CEREMONY.md §2 Full State Diagram, §8 Public vs Sub-States
    docs/architecture/LAYER_INTERFACES.md §L0 Grunnr Outputs
"""

from __future__ import annotations

import enum
from typing import Callable, Optional


class LifecycleState(enum.Enum):
    """All ceremony states — public phases and implementation sub-states.

    Public phases carry their True Names (transliterated per NAMING.md §5).
    Sub-states are ALL_CAPS English identifiers per CEREMONY.md §8.

    The five public states are: HVILD, KYNDING, TENGSL, SAMRAEDUR, SLOKNA.
    Sub-states are: READY, OPENING, RECOVERING, EXTINGUISHED, CONFIG_ERROR.
    """

    # --- Public ceremony phases (True Names) ---

    HVILD = "hvild"
    """Hvíld — rest; the body is dormant; no processes running; RAM free."""

    KYNDING = "kynding"
    """Kynding — kindling; app launched; config loading; senses spawning."""

    TENGSL = "tengsl"
    """Tengsl — bonds; Bifröst is open; the spirit is in covenant with the body."""

    SAMRAEDUR = "samraedur"
    """Samræður — communion; active session; the mutual exchange is alive."""

    SLOKNA = "slokna"
    """Slokna — extinguishing; clean shutdown in progress; drain window active."""

    # --- Implementation sub-states (CEREMONY.md §8) ---

    READY = "ready"
    """Within Kynding: all layers initialised; Bifröst not yet open; awaiting user."""

    OPENING = "opening"
    """Within Kynding: L1 Bifröst performing capability probe toward the agent."""

    RECOVERING = "recovering"
    """Within Tengsl/Samræður: connection dropped; reconnect in progress."""

    EXTINGUISHED = "extinguished"
    """Within Slokna: session state zeroed; transitioning back to READY or Hvíld."""

    CONFIG_ERROR = "config_error"
    """Kynding terminal failure: heretic.yaml is missing or malformed."""

    @property
    def is_public_phase(self) -> bool:
        """True if this state is one of the five ceremony phases visible to the user."""
        return self in {
            LifecycleState.HVILD,
            LifecycleState.KYNDING,
            LifecycleState.TENGSL,
            LifecycleState.SAMRAEDUR,
            LifecycleState.SLOKNA,
        }


# Type alias: an observer callback receives old state and new state.
StateChangeCallback = Callable[[LifecycleState, LifecycleState], None]


class Lifecycle:
    """Holds the authoritative HERETIC ceremony state and fires observer hooks.

    A single Lifecycle instance is created by Holdvörðr (the runtime process) at
    startup and passed into every layer that needs to query or react to state changes.

    Observer pattern:
        Register a callback with ``on_state_change(callback)``. The callback is called
        synchronously on every transition with ``(old_state, new_state)``.
        Observers must not block — long operations belong in a background task.

    Thread safety:
        In v0.1 the CLI is single-threaded. Forge will add thread-safety (asyncio
        event loop or threading.Lock) when the Tauri async bridge arrives at v0.4.

    Example::

        lc = Lifecycle()
        lc.on_state_change(lambda old, new: print(f"{old} → {new}"))
        lc.transition(LifecycleState.KYNDING)
    """

    def __init__(self, initial: LifecycleState = LifecycleState.HVILD) -> None:
        self._state: LifecycleState = initial
        self._observers: list[StateChangeCallback] = []

    @property
    def current_state(self) -> LifecycleState:
        """Return the current lifecycle state. Always valid; never None."""
        return self._state

    def on_state_change(self, callback: StateChangeCallback) -> None:
        """Register a callback to be called on every state transition.

        Args:
            callback: Callable(old_state, new_state) — must be non-blocking.
        """
        self._observers.append(callback)

    def transition(self, new_state: LifecycleState) -> None:
        """Transition to a new state and notify all observers.

        Transitions from a state to itself are silently ignored (no observer
        calls, no log noise). Invalid transitions raise LifecycleError.

        Args:
            new_state: The target LifecycleState.

        Raises:
            LifecycleError: If the transition is not permitted from the current state.
            NotImplementedError: Forge will implement the full transition guard table
                                 once the state machine spec is locked in CEREMONY.md.
        """
        if new_state == self._state:
            return

        _validate_transition(self._state, new_state)

        old_state = self._state
        self._state = new_state
        for observer in self._observers:
            try:
                observer(old_state, new_state)
            except Exception:
                # Observers must not crash the state machine.
                # Forge will wire this to get_logger(__name__).warning().
                pass

    def is_active(self) -> bool:
        """Return True if the ceremony is in an active (non-dormant) state.

        Active means: KYNDING, READY, OPENING, TENGSL, SAMRAEDUR, RECOVERING,
        SLOKNA, EXTINGUISHED. Inactive means: HVILD, CONFIG_ERROR.
        """
        return self._state not in {LifecycleState.HVILD, LifecycleState.CONFIG_ERROR}


def _validate_transition(
    current: LifecycleState,
    target: LifecycleState,
) -> None:
    """Validate that the transition from ``current`` to ``target`` is permitted.

    The full guard table is derived from CEREMONY.md §2 Full State Diagram and
    §7 State Machine Formal Summary. Forge will implement the complete table.

    Raises:
        LifecycleError: if the transition is not in the allowed table.
    """
    raise NotImplementedError(
        "Forge will implement: lifecycle._validate_transition — "
        "build the allowed transition table from CEREMONY.md §7, "
        "raise LifecycleError with a clear message on invalid transitions, "
        "return silently on valid ones."
    )


class LifecycleError(RuntimeError):
    """Raised when an invalid lifecycle state transition is attempted.

    Carries the attempted old/new states so the caller can surface a clear message.
    """

    def __init__(
        self,
        current: LifecycleState,
        target: LifecycleState,
        detail: Optional[str] = None,
    ) -> None:
        msg = f"Invalid lifecycle transition: {current.value} → {target.value}"
        if detail:
            msg += f" ({detail})"
        super().__init__(msg)
        self.current = current
        self.target = target
