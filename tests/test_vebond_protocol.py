"""
Placeholder tests for the Vébond IPC protocol schema.

These tests are skip-marked during the scaffold phase. Forge activates them
when pydantic is installed and the protocol models are wired into the server.

The structure below defines the expected test surface — Forge implements each
body when the [serve] extra is installed and integration tests run.

Canonical reference: src/heretic/vebond/protocol.py
Schema authority: docs/architecture/IPC_PROTOCOL.md
"""

import pytest


class TestProtocolAvailability:
    """Protocol models import cleanly when pydantic is installed."""

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates with pydantic installed")
    def test_protocol_imports(self) -> None:
        # Forge: from heretic.vebond.protocol import (
        #            ProtocolEvent, ProtocolCommand, CeremonyStateChanged, BifrostHealth,
        #            TungaActivity, HlustActivity, AgentToken, AgentTurnComplete, ErrorEvent,
        #            LightCommand, ExtinguishCommand, SendMessageCommand, CancelTurnCommand,
        #            ToggleSenseCommand,
        #        )
        pass


class TestEventModels:
    """Server->client event models construct and serialize correctly."""

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_ceremony_state_changed_roundtrip(self) -> None:
        # Forge: from heretic.vebond.protocol import CeremonyStateChanged
        #        event = CeremonyStateChanged(
        #            from_state="kynding", to_state="tengsl",
        #            timestamp="2026-05-07T14:32:00.000Z"
        #        )
        #        assert event.type == "ceremony.state_changed"
        #        raw = event.model_dump_json()
        #        assert '"type":"ceremony.state_changed"' in raw or '"type": "ceremony.state_changed"' in raw
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_bifrost_health_optional_latency(self) -> None:
        # Forge: from heretic.vebond.protocol import BifrostHealth
        #        event = BifrostHealth(status="open", endpoint="http://example.com/v1")
        #        assert event.latency_ms is None
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_hlust_activity_optional_level_db(self) -> None:
        # Forge: from heretic.vebond.protocol import HlustActivity
        #        event = HlustActivity(state="listening")
        #        assert event.level_db is None
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_agent_token_sequence_id_required(self) -> None:
        # Forge: from heretic.vebond.protocol import AgentToken
        #        import pytest
        #        with pytest.raises(Exception):  # pydantic ValidationError
        #            AgentToken(role="assistant", text_delta="Hello")  # missing sequence_id
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_error_event_levels(self) -> None:
        # Forge: from heretic.vebond.protocol import ErrorEvent
        #        warn_evt = ErrorEvent(level="warn", source="bifrost", message="Reconnecting")
        #        err_evt = ErrorEvent(level="error", source="lifecycle", message="Config invalid")
        #        assert warn_evt.level == "warn"
        #        assert err_evt.level == "error"
        pass


class TestCommandModels:
    """Client->server command models construct and discriminate correctly."""

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_light_command_type_literal(self) -> None:
        # Forge: from heretic.vebond.protocol import LightCommand
        #        cmd = LightCommand()
        #        assert cmd.type == "light"
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_send_message_command(self) -> None:
        # Forge: from heretic.vebond.protocol import SendMessageCommand
        #        cmd = SendMessageCommand(text="Hello agent")
        #        assert cmd.text == "Hello agent"
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_toggle_sense_command(self) -> None:
        # Forge: from heretic.vebond.protocol import ToggleSenseCommand
        #        cmd = ToggleSenseCommand(sense_id="hlust", enabled=False)
        #        assert cmd.sense_id == "hlust"
        #        assert cmd.enabled is False
        pass


class TestDiscriminatedUnions:
    """ProtocolEvent and ProtocolCommand discriminated unions deserialize correctly."""

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_protocol_event_deserialization(self) -> None:
        # Forge: import json
        #        from pydantic import TypeAdapter
        #        from heretic.vebond.protocol import ProtocolEvent, CeremonyStateChanged
        #        adapter = TypeAdapter(ProtocolEvent)
        #        raw = json.dumps({
        #            "type": "ceremony.state_changed",
        #            "from_state": "kynding",
        #            "to_state": "tengsl",
        #            "timestamp": "2026-05-07T00:00:00.000Z",
        #        })
        #        event = adapter.validate_python(json.loads(raw))
        #        assert isinstance(event, CeremonyStateChanged)
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_protocol_command_deserialization(self) -> None:
        # Forge: import json
        #        from pydantic import TypeAdapter
        #        from heretic.vebond.protocol import ProtocolCommand, LightCommand
        #        adapter = TypeAdapter(ProtocolCommand)
        #        cmd = adapter.validate_python({"type": "light"})
        #        assert isinstance(cmd, LightCommand)
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_unknown_event_type_raises(self) -> None:
        # Forge: import json
        #        from pydantic import TypeAdapter, ValidationError
        #        from heretic.vebond.protocol import ProtocolEvent
        #        adapter = TypeAdapter(ProtocolEvent)
        #        with pytest.raises(ValidationError):
        #            adapter.validate_python({"type": "totally.unknown"})
        pass
