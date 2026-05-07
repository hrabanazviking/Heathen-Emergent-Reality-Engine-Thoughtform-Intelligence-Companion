"""
Tests for grunnr.lifecycle — LifecycleState enum and Lifecycle state machine.

Placeholder suite. Forge will implement real tests here covering:
    - All valid transitions from CEREMONY.md §7 State Machine Formal Summary
    - All invalid transitions → LifecycleError raised; state unchanged
    - Observer callbacks are called with correct (old_state, new_state) arguments
    - Multiple observers are all notified
    - An observer that raises does not prevent other observers from being notified
    - is_public_phase returns True for the five True Name states only
    - is_active() returns correct values for each state
    - Self-transition (state → same state) is silently ignored
    - Lifecycle.current_state starts as HVILD

Currently two structural tests are active (no Forge placeholder needed — they
test only the skeleton, not the NotImplementedError'd transition guard).
"""

from __future__ import annotations

import pytest

from heretic.grunnr.lifecycle import Lifecycle, LifecycleError, LifecycleState


def test_initial_state_is_hvild() -> None:
    """A freshly constructed Lifecycle starts in HVILD."""
    lc = Lifecycle()
    assert lc.current_state == LifecycleState.HVILD


def test_public_phase_flags() -> None:
    """The five True Name states are marked as public phases; sub-states are not."""
    public = {
        LifecycleState.HVILD,
        LifecycleState.KYNDING,
        LifecycleState.TENGSL,
        LifecycleState.SAMRAEDUR,
        LifecycleState.SLOKNA,
    }
    for state in LifecycleState:
        if state in public:
            assert state.is_public_phase, f"{state} should be a public phase"
        else:
            assert not state.is_public_phase, f"{state} should NOT be a public phase"


def test_on_state_change_registration() -> None:
    """on_state_change() accepts a callback without raising."""
    lc = Lifecycle()
    called: list[tuple[LifecycleState, LifecycleState]] = []
    lc.on_state_change(lambda old, new: called.append((old, new)))
    # No transition yet — callback should not have fired.
    assert called == []


@pytest.mark.skip(reason="Forge will implement: _validate_transition() not yet built")
def test_valid_transition_hvild_to_kynding() -> None:
    """Lifecycle transitions from HVILD to KYNDING on app launch."""
    pass


@pytest.mark.skip(reason="Forge will implement: _validate_transition() not yet built")
def test_invalid_transition_raises_lifecycle_error() -> None:
    """Attempting an invalid transition raises LifecycleError and leaves state unchanged."""
    pass


@pytest.mark.skip(reason="Forge will implement: _validate_transition() not yet built")
def test_observer_called_with_old_and_new_state() -> None:
    """Observer receives (old_state, new_state) on each valid transition."""
    pass


@pytest.mark.skip(reason="Forge will implement: _validate_transition() not yet built")
def test_crashing_observer_does_not_abort_transition() -> None:
    """A callback that raises does not prevent subsequent observers from running."""
    pass


@pytest.mark.skip(reason="Forge will implement: _validate_transition() not yet built")
def test_self_transition_is_noop() -> None:
    """Transitioning to the current state does not fire observers."""
    pass
