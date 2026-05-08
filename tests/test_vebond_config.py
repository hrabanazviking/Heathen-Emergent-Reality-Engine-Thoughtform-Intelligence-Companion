"""
Placeholder tests for VebondConfig.

These tests are skip-marked during the scaffold phase. Forge activates them
(removes the pytest.mark.skip decorators) when VebondConfig.__post_init__
validation is exercised end-to-end in the real implementation.

The structure below defines the expected test surface — Forge should implement
each test body according to the comment inside.

Canonical reference: src/heretic/vebond/config_model.py
"""

import pytest
from heretic.vebond.config_model import VebondConfig
from heretic.vebond.errors import VebondConfigError


class TestVebondConfigDefaults:
    """VebondConfig constructs with correct defaults."""

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_default_ws_host(self) -> None:
        # Forge: assert VebondConfig().ws_host == "127.0.0.1"
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_default_ws_port(self) -> None:
        # Forge: assert VebondConfig().ws_port == 8642
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_default_allow_remote_bind_is_false(self) -> None:
        # Forge: assert VebondConfig().allow_remote_bind is False
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_default_max_message_size(self) -> None:
        # Forge: assert VebondConfig().max_message_size_bytes == 1_048_576
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_default_heartbeat_interval(self) -> None:
        # Forge: assert VebondConfig().heartbeat_interval_seconds == 30
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_default_connection_timeout(self) -> None:
        # Forge: assert VebondConfig().connection_timeout_seconds == 60
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_default_theme(self) -> None:
        # Forge: assert VebondConfig().theme == "dark_norse"
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_default_show_frame_thumbnail_is_false(self) -> None:
        # Forge: assert VebondConfig().show_frame_thumbnail is False
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_default_ceremony_button_confirm_is_true(self) -> None:
        # Forge: assert VebondConfig().ceremony_button_confirm is True
        pass


class TestVebondConfigValidation:
    """VebondConfig.__post_init__ raises VebondConfigError on invalid values."""

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_invalid_port_zero(self) -> None:
        # Forge: with pytest.raises(VebondConfigError): VebondConfig(ws_port=0)
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_invalid_port_too_high(self) -> None:
        # Forge: with pytest.raises(VebondConfigError): VebondConfig(ws_port=65536)
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_non_loopback_host_without_allow_remote_bind(self) -> None:
        # Forge: with pytest.raises(VebondConfigError):
        #     VebondConfig(ws_host="0.0.0.0", allow_remote_bind=False)
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_non_loopback_host_with_allow_remote_bind(self) -> None:
        # Forge: config = VebondConfig(ws_host="0.0.0.0", allow_remote_bind=True)
        #        assert config.ws_host == "0.0.0.0"  # no error raised
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_loopback_ipv6_accepted_without_allow_remote_bind(self) -> None:
        # Forge: config = VebondConfig(ws_host="::1", allow_remote_bind=False)
        #        assert config.ws_host == "::1"  # ::1 is loopback; no error
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_message_size_below_minimum(self) -> None:
        # Forge: with pytest.raises(VebondConfigError):
        #     VebondConfig(max_message_size_bytes=512)
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_timeout_less_than_heartbeat(self) -> None:
        # Forge: with pytest.raises(VebondConfigError):
        #     VebondConfig(heartbeat_interval_seconds=60, connection_timeout_seconds=30)
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_timeout_equal_to_heartbeat_accepted(self) -> None:
        # Forge: config = VebondConfig(heartbeat_interval_seconds=30,
        #                               connection_timeout_seconds=30)
        #        assert config.heartbeat_interval_seconds == 30  # no error
        pass


class TestVebondConfigInHereticConfig:
    """VebondConfig is accessible via HereticConfig.vebond."""

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_heretic_config_has_vebond_field(self) -> None:
        # Forge: from heretic.grunnr.config import HereticConfig
        #        cfg = HereticConfig()
        #        assert isinstance(cfg.vebond, VebondConfig)
        pass

    @pytest.mark.skip(reason="scaffold placeholder — Forge activates")
    def test_heretic_config_vebond_has_ws_port(self) -> None:
        # Forge: from heretic.grunnr.config import HereticConfig
        #        cfg = HereticConfig()
        #        assert cfg.vebond.ws_port == 8642
        pass
