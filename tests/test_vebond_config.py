"""
Tests for VebondConfig — defaults, validation, and HereticConfig integration.

Canonical reference: src/heretic/vebond/config_model.py
"""

import pytest
from heretic.vebond.config_model import VebondConfig
from heretic.vebond.errors import VebondConfigError


class TestVebondConfigDefaults:
    """VebondConfig constructs with correct defaults."""

    def test_default_ws_host(self) -> None:
        assert VebondConfig().ws_host == "127.0.0.1"

    def test_default_ws_port(self) -> None:
        assert VebondConfig().ws_port == 8642

    def test_default_allow_remote_bind_is_false(self) -> None:
        assert VebondConfig().allow_remote_bind is False

    def test_default_max_message_size(self) -> None:
        assert VebondConfig().max_message_size_bytes == 1_048_576

    def test_default_heartbeat_interval(self) -> None:
        assert VebondConfig().heartbeat_interval_seconds == 30

    def test_default_connection_timeout(self) -> None:
        assert VebondConfig().connection_timeout_seconds == 60

    def test_default_theme(self) -> None:
        assert VebondConfig().theme == "dark_norse"

    def test_default_show_frame_thumbnail_is_false(self) -> None:
        assert VebondConfig().show_frame_thumbnail is False

    def test_default_ceremony_button_confirm_is_true(self) -> None:
        assert VebondConfig().ceremony_button_confirm is True

    def test_default_show_agent_text_stream_is_true(self) -> None:
        assert VebondConfig().show_agent_text_stream is True

    def test_constructs_without_args(self) -> None:
        # Should not raise
        cfg = VebondConfig()
        assert cfg is not None


class TestVebondConfigValidation:
    """VebondConfig.__post_init__ raises VebondConfigError on invalid values."""

    def test_invalid_port_zero(self) -> None:
        with pytest.raises(VebondConfigError, match="ws_port"):
            VebondConfig(ws_port=0)

    def test_invalid_port_too_high(self) -> None:
        with pytest.raises(VebondConfigError, match="ws_port"):
            VebondConfig(ws_port=65536)

    def test_valid_port_boundary_low(self) -> None:
        # Port 1 is valid (though unusual)
        cfg = VebondConfig(ws_port=1)
        assert cfg.ws_port == 1

    def test_valid_port_boundary_high(self) -> None:
        cfg = VebondConfig(ws_port=65535)
        assert cfg.ws_port == 65535

    def test_non_loopback_host_without_allow_remote_bind(self) -> None:
        with pytest.raises(VebondConfigError, match="allow_remote_bind"):
            VebondConfig(ws_host="0.0.0.0", allow_remote_bind=False)

    def test_non_loopback_host_with_allow_remote_bind(self) -> None:
        # Should NOT raise when allow_remote_bind is True
        cfg = VebondConfig(ws_host="0.0.0.0", allow_remote_bind=True)
        assert cfg.ws_host == "0.0.0.0"

    def test_loopback_ipv6_accepted_without_allow_remote_bind(self) -> None:
        # ::1 is loopback — no error required
        cfg = VebondConfig(ws_host="::1", allow_remote_bind=False)
        assert cfg.ws_host == "::1"

    def test_loopback_127_x_accepted(self) -> None:
        # Any 127.x.x.x address is loopback
        cfg = VebondConfig(ws_host="127.0.0.2")
        assert cfg.ws_host == "127.0.0.2"

    def test_loopback_localhost_string_accepted(self) -> None:
        cfg = VebondConfig(ws_host="localhost")
        assert cfg.ws_host == "localhost"

    def test_message_size_below_minimum(self) -> None:
        with pytest.raises(VebondConfigError, match="max_message_size_bytes"):
            VebondConfig(max_message_size_bytes=512)

    def test_message_size_exactly_minimum(self) -> None:
        # Exactly 1024 bytes is the minimum allowed
        cfg = VebondConfig(max_message_size_bytes=1024)
        assert cfg.max_message_size_bytes == 1024

    def test_timeout_less_than_heartbeat(self) -> None:
        with pytest.raises(VebondConfigError, match="connection_timeout_seconds"):
            VebondConfig(heartbeat_interval_seconds=60, connection_timeout_seconds=30)

    def test_timeout_equal_to_heartbeat_accepted(self) -> None:
        # Equal is allowed (timeout >= heartbeat)
        cfg = VebondConfig(heartbeat_interval_seconds=30, connection_timeout_seconds=30)
        assert cfg.heartbeat_interval_seconds == 30

    def test_heartbeat_zero_invalid(self) -> None:
        with pytest.raises(VebondConfigError, match="heartbeat_interval_seconds"):
            VebondConfig(heartbeat_interval_seconds=0)


class TestVebondConfigInHereticConfig:
    """VebondConfig is accessible via HereticConfig.vebond."""

    def test_heretic_config_has_vebond_field(self) -> None:
        from heretic.grunnr.config import HereticConfig
        cfg = HereticConfig()
        assert isinstance(cfg.vebond, VebondConfig)

    def test_heretic_config_vebond_has_ws_port(self) -> None:
        from heretic.grunnr.config import HereticConfig
        cfg = HereticConfig()
        assert cfg.vebond.ws_port == 8642

    def test_heretic_config_vebond_default_host(self) -> None:
        from heretic.grunnr.config import HereticConfig
        cfg = HereticConfig()
        assert cfg.vebond.ws_host == "127.0.0.1"

    def test_vebond_config_import_from_grunnr(self) -> None:
        # Backward-compat: grunnr.config re-exports VebondConfig
        from heretic.grunnr.config import VebondConfig as GrunnrVebondConfig
        assert GrunnrVebondConfig is VebondConfig
