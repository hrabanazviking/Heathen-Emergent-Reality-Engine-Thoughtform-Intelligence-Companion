"""
Tests for the Vebond IPC protocol schema (pydantic models + discriminated unions).

Canonical reference: src/heretic/vebond/protocol.py
Schema authority: docs/architecture/IPC_PROTOCOL.md
"""

import json
import pytest
from pydantic import TypeAdapter, ValidationError

from heretic.vebond.protocol import (
    ProtocolEvent,
    ProtocolCommand,
    CeremonyStateChanged,
    BifrostHealth,
    TungaActivity,
    HlustActivity,
    AgentToken,
    AgentTurnComplete,
    ErrorEvent,
    LightCommand,
    ExtinguishCommand,
    SendMessageCommand,
    CancelTurnCommand,
    ToggleSenseCommand,
)

_EVENT_ADAPTER = TypeAdapter(ProtocolEvent)
_CMD_ADAPTER = TypeAdapter(ProtocolCommand)


class TestProtocolAvailability:
    """Protocol models import cleanly when pydantic is installed."""

    def test_protocol_imports(self) -> None:
        # All public symbols import without error
        assert ProtocolEvent is not None
        assert ProtocolCommand is not None
        assert CeremonyStateChanged is not None
        assert BifrostHealth is not None
        assert TungaActivity is not None
        assert HlustActivity is not None
        assert AgentToken is not None
        assert AgentTurnComplete is not None
        assert ErrorEvent is not None
        assert LightCommand is not None
        assert ExtinguishCommand is not None
        assert SendMessageCommand is not None
        assert CancelTurnCommand is not None
        assert ToggleSenseCommand is not None


class TestEventModels:
    """Server->client event models construct and serialize correctly."""

    def test_ceremony_state_changed_construct(self) -> None:
        event = CeremonyStateChanged(
            from_state="kynding",
            to_state="tengsl",
            timestamp="2026-05-07T14:32:00.000Z",
        )
        assert event.type == "ceremony.state_changed"
        assert event.from_state == "kynding"
        assert event.to_state == "tengsl"

    def test_ceremony_state_changed_roundtrip(self) -> None:
        event = CeremonyStateChanged(
            from_state="kynding",
            to_state="tengsl",
            timestamp="2026-05-07T14:32:00.000Z",
        )
        raw = event.model_dump_json()
        assert "ceremony.state_changed" in raw
        # Round-trip: deserialize back
        loaded = CeremonyStateChanged.model_validate_json(raw)
        assert loaded.to_state == "tengsl"

    def test_bifrost_health_optional_latency(self) -> None:
        event = BifrostHealth(status="open", endpoint="http://example.com/v1")
        assert event.latency_ms is None

    def test_bifrost_health_with_latency(self) -> None:
        event = BifrostHealth(status="open", endpoint="http://example.com/v1", latency_ms=42)
        assert event.latency_ms == 42

    def test_tunga_activity_states(self) -> None:
        for state in ("idle", "synthesizing", "speaking", "failed"):
            event = TungaActivity(state=state)
            assert event.state == state
            assert event.type == "tunga.activity"

    def test_hlust_activity_optional_level_db(self) -> None:
        event = HlustActivity(state="listening")
        assert event.level_db is None
        assert event.type == "hlust.activity"

    def test_hlust_activity_with_level_db(self) -> None:
        event = HlustActivity(state="listening", level_db=-18.5)
        assert event.level_db == pytest.approx(-18.5)

    def test_agent_token_construct(self) -> None:
        event = AgentToken(role="assistant", text_delta="Hello", sequence_id=0)
        assert event.type == "agent.token"
        assert event.text_delta == "Hello"
        assert event.sequence_id == 0

    def test_agent_token_sequence_id_required(self) -> None:
        with pytest.raises(ValidationError):
            AgentToken(role="assistant", text_delta="Hello")  # type: ignore

    def test_agent_turn_complete(self) -> None:
        event = AgentTurnComplete(turn_id="t-001", finish_reason="stop")
        assert event.type == "agent.turn_complete"
        assert event.turn_id == "t-001"
        assert event.finish_reason == "stop"

    def test_error_event_warn(self) -> None:
        event = ErrorEvent(level="warn", source="bifrost", message="Reconnecting")
        assert event.level == "warn"
        assert event.type == "error"

    def test_error_event_error(self) -> None:
        event = ErrorEvent(level="error", source="lifecycle", message="Config invalid")
        assert event.level == "error"

    def test_all_event_types_have_type_field(self) -> None:
        """Every event model has a Literal 'type' discriminator value."""
        events = [
            CeremonyStateChanged(from_state="hvild", to_state="kynding", timestamp="t"),
            BifrostHealth(status="closed", endpoint=""),
            TungaActivity(state="idle"),
            HlustActivity(state="idle"),
            AgentToken(role="assistant", text_delta="x", sequence_id=0),
            AgentTurnComplete(turn_id="t", finish_reason="stop"),
            ErrorEvent(level="warn", source="vebond", message="test"),
        ]
        type_fields = {e.type for e in events}
        assert len(type_fields) == 7  # All distinct

    def test_event_serializes_to_json_with_type_field(self) -> None:
        event = TungaActivity(state="speaking")
        raw = json.loads(event.model_dump_json())
        assert raw["type"] == "tunga.activity"
        assert raw["state"] == "speaking"


class TestCommandModels:
    """Client->server command models construct and discriminate correctly."""

    def test_light_command_type_literal(self) -> None:
        cmd = LightCommand()
        assert cmd.type == "light"

    def test_extinguish_command(self) -> None:
        cmd = ExtinguishCommand()
        assert cmd.type == "extinguish"

    def test_send_message_command(self) -> None:
        cmd = SendMessageCommand(text="Hello agent")
        assert cmd.text == "Hello agent"
        assert cmd.type == "send_message"

    def test_cancel_turn_command(self) -> None:
        cmd = CancelTurnCommand(turn_id="turn-abc-123")
        assert cmd.turn_id == "turn-abc-123"
        assert cmd.type == "cancel_turn"

    def test_toggle_sense_command(self) -> None:
        cmd = ToggleSenseCommand(sense_id="hlust", enabled=False)
        assert cmd.sense_id == "hlust"
        assert cmd.enabled is False
        assert cmd.type == "toggle_sense"

    def test_toggle_sense_enabled_true(self) -> None:
        cmd = ToggleSenseCommand(sense_id="tunga", enabled=True)
        assert cmd.enabled is True


class TestDiscriminatedUnions:
    """ProtocolEvent and ProtocolCommand discriminated unions deserialize correctly."""

    def test_protocol_event_ceremony_state_changed(self) -> None:
        raw = {
            "type": "ceremony.state_changed",
            "from_state": "kynding",
            "to_state": "tengsl",
            "timestamp": "2026-05-07T00:00:00.000Z",
        }
        event = _EVENT_ADAPTER.validate_python(raw)
        assert isinstance(event, CeremonyStateChanged)
        assert event.to_state == "tengsl"

    def test_protocol_event_bifrost_health(self) -> None:
        raw = {"type": "bifrost.health", "status": "open", "endpoint": "http://x/v1", "latency_ms": 10}
        event = _EVENT_ADAPTER.validate_python(raw)
        assert isinstance(event, BifrostHealth)
        assert event.status == "open"

    def test_protocol_event_agent_token(self) -> None:
        raw = {"type": "agent.token", "role": "assistant", "text_delta": "Hi", "sequence_id": 3}
        event = _EVENT_ADAPTER.validate_python(raw)
        assert isinstance(event, AgentToken)
        assert event.text_delta == "Hi"

    def test_protocol_event_error(self) -> None:
        raw = {"type": "error", "level": "warn", "source": "bifrost", "message": "Reconnecting"}
        event = _EVENT_ADAPTER.validate_python(raw)
        assert isinstance(event, ErrorEvent)

    def test_protocol_command_light(self) -> None:
        cmd = _CMD_ADAPTER.validate_python({"type": "light"})
        assert isinstance(cmd, LightCommand)

    def test_protocol_command_send_message(self) -> None:
        cmd = _CMD_ADAPTER.validate_python({"type": "send_message", "text": "Hello"})
        assert isinstance(cmd, SendMessageCommand)
        assert cmd.text == "Hello"

    def test_protocol_command_toggle_sense(self) -> None:
        cmd = _CMD_ADAPTER.validate_python({
            "type": "toggle_sense", "sense_id": "hlust", "enabled": True
        })
        assert isinstance(cmd, ToggleSenseCommand)

    def test_unknown_event_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            _EVENT_ADAPTER.validate_python({"type": "totally.unknown"})

    def test_unknown_command_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            _CMD_ADAPTER.validate_python({"type": "not_a_command"})

    def test_json_roundtrip_all_events(self) -> None:
        """Every event type serializes to JSON and round-trips through the discriminator."""
        events = [
            CeremonyStateChanged(from_state="hvild", to_state="kynding", timestamp="t"),
            BifrostHealth(status="closed", endpoint=""),
            TungaActivity(state="idle"),
            HlustActivity(state="idle"),
            AgentToken(role="assistant", text_delta="x", sequence_id=0),
            AgentTurnComplete(turn_id="t", finish_reason="stop"),
            ErrorEvent(level="warn", source="vebond", message="test"),
        ]
        for original in events:
            raw = json.loads(original.model_dump_json())
            reconstructed = _EVENT_ADAPTER.validate_python(raw)
            assert reconstructed.type == original.type
