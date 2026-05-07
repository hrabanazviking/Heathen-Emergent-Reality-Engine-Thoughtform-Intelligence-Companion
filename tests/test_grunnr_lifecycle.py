"""
Tests for grunnr.lifecycle — LifecycleState enum and Lifecycle state machine.

Covers: all valid transitions from CEREMONY.md §7, invalid transitions,
observer callbacks, thread safety, self-transitions, and state queries.
"""

from __future__ import annotations

import threading
from typing import List, Tuple

import pytest

from heretic.grunnr.lifecycle import Lifecycle, LifecycleError, LifecycleState


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def test_initial_state_is_hvild() -> None:
    """A freshly constructed Lifecycle starts in HVILD."""
    lc = Lifecycle()
    assert lc.current_state == LifecycleState.HVILD


def test_custom_initial_state() -> None:
    """Lifecycle can be initialised with a non-default state (for testing)."""
    lc = Lifecycle(initial=LifecycleState.READY)
    assert lc.current_state == LifecycleState.READY


# ---------------------------------------------------------------------------
# Public phase flags
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Observer registration
# ---------------------------------------------------------------------------

def test_on_state_change_registration() -> None:
    """on_state_change() accepts a callback without raising."""
    lc = Lifecycle()
    called: List[Tuple[LifecycleState, LifecycleState]] = []
    lc.on_state_change(lambda old, new: called.append((old, new)))
    # No transition yet — callback should not have fired
    assert called == []


# ---------------------------------------------------------------------------
# Valid transitions from CEREMONY.md §7
# ---------------------------------------------------------------------------

def test_valid_transition_hvild_to_kynding() -> None:
    """Lifecycle transitions from HVILD to KYNDING on app launch."""
    lc = Lifecycle()
    lc.transition(LifecycleState.KYNDING)
    assert lc.current_state == LifecycleState.KYNDING


def test_valid_transition_kynding_to_ready() -> None:
    """KYNDING → READY when all layers initialise."""
    lc = Lifecycle(initial=LifecycleState.KYNDING)
    lc.transition(LifecycleState.READY)
    assert lc.current_state == LifecycleState.READY


def test_valid_transition_kynding_to_config_error() -> None:
    """KYNDING → CONFIG_ERROR when heretic.yaml is malformed."""
    lc = Lifecycle(initial=LifecycleState.KYNDING)
    lc.transition(LifecycleState.CONFIG_ERROR)
    assert lc.current_state == LifecycleState.CONFIG_ERROR


def test_valid_transition_ready_to_opening() -> None:
    """READY → OPENING when user clicks 'Light the Candle'."""
    lc = Lifecycle(initial=LifecycleState.READY)
    lc.transition(LifecycleState.OPENING)
    assert lc.current_state == LifecycleState.OPENING


def test_valid_transition_opening_to_tengsl() -> None:
    """OPENING → TENGSL when capability probe succeeds."""
    lc = Lifecycle(initial=LifecycleState.OPENING)
    lc.transition(LifecycleState.TENGSL)
    assert lc.current_state == LifecycleState.TENGSL


def test_valid_transition_opening_to_ready_on_failure() -> None:
    """OPENING → READY when probe fails or user cancels."""
    lc = Lifecycle(initial=LifecycleState.OPENING)
    lc.transition(LifecycleState.READY)
    assert lc.current_state == LifecycleState.READY


def test_valid_transition_tengsl_to_samraedur() -> None:
    """TENGSL → SAMRAEDUR on first user input."""
    lc = Lifecycle(initial=LifecycleState.TENGSL)
    lc.transition(LifecycleState.SAMRAEDUR)
    assert lc.current_state == LifecycleState.SAMRAEDUR


def test_valid_transition_samraedur_to_slokna() -> None:
    """SAMRAEDUR → SLOKNA when user clicks Extinguish."""
    lc = Lifecycle(initial=LifecycleState.SAMRAEDUR)
    lc.transition(LifecycleState.SLOKNA)
    assert lc.current_state == LifecycleState.SLOKNA


def test_valid_transition_samraedur_to_recovering() -> None:
    """SAMRAEDUR → RECOVERING on connection drop."""
    lc = Lifecycle(initial=LifecycleState.SAMRAEDUR)
    lc.transition(LifecycleState.RECOVERING)
    assert lc.current_state == LifecycleState.RECOVERING


def test_valid_transition_recovering_to_samraedur() -> None:
    """RECOVERING → SAMRAEDUR on successful reconnect."""
    lc = Lifecycle(initial=LifecycleState.RECOVERING)
    lc.transition(LifecycleState.SAMRAEDUR)
    assert lc.current_state == LifecycleState.SAMRAEDUR


def test_valid_transition_recovering_to_ready() -> None:
    """RECOVERING → READY when reconnect retries are exhausted."""
    lc = Lifecycle(initial=LifecycleState.RECOVERING)
    lc.transition(LifecycleState.READY)
    assert lc.current_state == LifecycleState.READY


def test_valid_transition_slokna_to_extinguished() -> None:
    """SLOKNA → EXTINGUISHED when drain completes."""
    lc = Lifecycle(initial=LifecycleState.SLOKNA)
    lc.transition(LifecycleState.EXTINGUISHED)
    assert lc.current_state == LifecycleState.EXTINGUISHED


def test_valid_transition_extinguished_to_hvild() -> None:
    """EXTINGUISHED → HVILD when app closes."""
    lc = Lifecycle(initial=LifecycleState.EXTINGUISHED)
    lc.transition(LifecycleState.HVILD)
    assert lc.current_state == LifecycleState.HVILD


def test_valid_full_ceremony_arc() -> None:
    """Walk the full ceremony arc without raising."""
    lc = Lifecycle()
    lc.transition(LifecycleState.KYNDING)
    lc.transition(LifecycleState.READY)
    lc.transition(LifecycleState.OPENING)
    lc.transition(LifecycleState.TENGSL)
    lc.transition(LifecycleState.SAMRAEDUR)
    lc.transition(LifecycleState.SLOKNA)
    lc.transition(LifecycleState.EXTINGUISHED)
    lc.transition(LifecycleState.HVILD)
    assert lc.current_state == LifecycleState.HVILD


# ---------------------------------------------------------------------------
# Invalid transitions
# ---------------------------------------------------------------------------

def test_invalid_transition_hvild_to_samraedur_raises() -> None:
    """HVILD → SAMRAEDUR is not a valid transition (must go through KYNDING)."""
    lc = Lifecycle()
    with pytest.raises(LifecycleError) as exc_info:
        lc.transition(LifecycleState.SAMRAEDUR)
    assert lc.current_state == LifecycleState.HVILD  # state unchanged
    assert "hvild" in str(exc_info.value).lower()


def test_invalid_transition_hvild_to_tengsl_raises() -> None:
    """HVILD → TENGSL is invalid."""
    lc = Lifecycle()
    with pytest.raises(LifecycleError):
        lc.transition(LifecycleState.TENGSL)
    assert lc.current_state == LifecycleState.HVILD


def test_invalid_transition_samraedur_to_kynding_raises() -> None:
    """SAMRAEDUR → KYNDING is invalid — must go through SLOKNA."""
    lc = Lifecycle(initial=LifecycleState.SAMRAEDUR)
    with pytest.raises(LifecycleError):
        lc.transition(LifecycleState.KYNDING)
    assert lc.current_state == LifecycleState.SAMRAEDUR


def test_config_error_is_terminal() -> None:
    """CONFIG_ERROR → anything (except HVILD) raises LifecycleError."""
    lc = Lifecycle(initial=LifecycleState.CONFIG_ERROR)
    for state in (
        LifecycleState.KYNDING,
        LifecycleState.READY,
        LifecycleState.SAMRAEDUR,
    ):
        with pytest.raises(LifecycleError):
            lc.transition(state)
        assert lc.current_state == LifecycleState.CONFIG_ERROR


# ---------------------------------------------------------------------------
# Observer callbacks
# ---------------------------------------------------------------------------

def test_observer_called_with_old_and_new_state() -> None:
    """Observer receives (old_state, new_state) on each valid transition."""
    lc = Lifecycle()
    calls: List[Tuple[LifecycleState, LifecycleState]] = []
    lc.on_state_change(lambda old, new: calls.append((old, new)))

    lc.transition(LifecycleState.KYNDING)
    assert calls == [(LifecycleState.HVILD, LifecycleState.KYNDING)]


def test_multiple_observers_all_called() -> None:
    """All registered observers are notified on a transition."""
    lc = Lifecycle()
    log_a: List[str] = []
    log_b: List[str] = []
    lc.on_state_change(lambda old, new: log_a.append(new.value))
    lc.on_state_change(lambda old, new: log_b.append(new.value))

    lc.transition(LifecycleState.KYNDING)
    assert log_a == ["kynding"]
    assert log_b == ["kynding"]


def test_crashing_observer_does_not_abort_transition() -> None:
    """A callback that raises does not prevent other observers from running."""
    lc = Lifecycle()
    log: List[str] = []

    def bad_observer(old: LifecycleState, new: LifecycleState) -> None:
        raise RuntimeError("I crash")

    lc.on_state_change(bad_observer)
    lc.on_state_change(lambda old, new: log.append(new.value))

    # Should not raise despite bad_observer
    lc.transition(LifecycleState.KYNDING)
    assert lc.current_state == LifecycleState.KYNDING
    # Second observer still ran
    assert log == ["kynding"]


# ---------------------------------------------------------------------------
# Self-transition
# ---------------------------------------------------------------------------

def test_self_transition_is_noop() -> None:
    """Transitioning to the current state does not fire observers and does not raise."""
    lc = Lifecycle()
    calls: List[Tuple[LifecycleState, LifecycleState]] = []
    lc.on_state_change(lambda old, new: calls.append((old, new)))

    lc.transition(LifecycleState.HVILD)  # same state
    assert calls == []
    assert lc.current_state == LifecycleState.HVILD


# ---------------------------------------------------------------------------
# is_active
# ---------------------------------------------------------------------------

def test_is_active_hvild_is_false() -> None:
    """HVILD is not an active state."""
    lc = Lifecycle()
    assert lc.is_active() is False


def test_is_active_config_error_is_false() -> None:
    """CONFIG_ERROR is not an active state."""
    lc = Lifecycle(initial=LifecycleState.CONFIG_ERROR)
    assert lc.is_active() is False


def test_is_active_kynding_is_true() -> None:
    """KYNDING is an active state."""
    lc = Lifecycle(initial=LifecycleState.KYNDING)
    assert lc.is_active() is True


def test_is_active_samraedur_is_true() -> None:
    """SAMRAEDUR is an active state."""
    lc = Lifecycle(initial=LifecycleState.SAMRAEDUR)
    assert lc.is_active() is True


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

def test_thread_safe_concurrent_transitions() -> None:
    """Multiple threads can read current_state concurrently without crashing."""
    lc = Lifecycle(initial=LifecycleState.SAMRAEDUR)
    errors: List[Exception] = []

    def reader() -> None:
        for _ in range(100):
            try:
                _ = lc.current_state
                _ = lc.is_active()
            except Exception as exc:
                errors.append(exc)

    threads = [threading.Thread(target=reader) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"Thread safety errors: {errors}"


def test_thread_safe_transition_and_read() -> None:
    """Concurrent transition + read from different threads does not corrupt state."""
    lc = Lifecycle()
    errors: List[Exception] = []

    def do_transitions() -> None:
        try:
            lc.transition(LifecycleState.KYNDING)
        except (LifecycleError, Exception) as exc:
            errors.append(exc)

    def do_reads() -> None:
        for _ in range(50):
            try:
                state = lc.current_state
                assert isinstance(state, LifecycleState)
            except Exception as exc:
                errors.append(exc)

    t1 = threading.Thread(target=do_transitions)
    t2 = threading.Thread(target=do_reads)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert errors == [], f"Thread safety errors: {errors}"
