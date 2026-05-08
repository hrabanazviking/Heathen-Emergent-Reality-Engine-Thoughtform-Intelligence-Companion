"""
Tests for heretic.sjon.config_model — SjonConfig, SjonScreenConfig, SjonWebcamConfig.

Coverage:
    - SjonScreenConfig defaults match LAYER_INTERFACES.md §L3 canonical block
    - SjonScreenConfig.__post_init__ validation: every guard condition
    - SjonScreenConfig save_frames=True emits a log warning (non-fatal)
    - SjonWebcamConfig defaults
    - SjonConfig default instance has correct sub-config types
    - Approach B: grunnr.config re-exports are the SAME class objects
    - HereticConfig.sjon field is a SjonConfig instance
"""

from __future__ import annotations

import logging

import pytest


# ---------------------------------------------------------------------------
# SjonScreenConfig
# ---------------------------------------------------------------------------

class TestSjonScreenConfigDefaults:
    """SjonScreenConfig default values match LAYER_INTERFACES.md §L3 config keys."""

    def test_defaults(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        cfg = SjonScreenConfig()
        assert cfg.enabled is True
        assert cfg.interval_ms == 5000
        assert cfg.max_width == 1280
        assert cfg.max_height == 720
        assert cfg.crop is None
        assert cfg.buffer_depth == 5
        assert cfg.save_frames is False
        assert cfg.monitor_index == 0
        assert cfg.min_interval_ms == 1000


class TestSjonScreenConfigValidation:
    """SjonScreenConfig.__post_init__ rejects invalid field values."""

    def test_negative_interval_ms(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        with pytest.raises(ValueError, match="interval_ms"):
            SjonScreenConfig(interval_ms=-1)

    def test_zero_max_width(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        with pytest.raises(ValueError, match="max_width"):
            SjonScreenConfig(max_width=0)

    def test_negative_max_width(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        with pytest.raises(ValueError, match="max_width"):
            SjonScreenConfig(max_width=-100)

    def test_zero_max_height(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        with pytest.raises(ValueError, match="max_height"):
            SjonScreenConfig(max_height=0)

    def test_negative_max_height(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        with pytest.raises(ValueError, match="max_height"):
            SjonScreenConfig(max_height=-1)

    def test_zero_buffer_depth(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        with pytest.raises(ValueError, match="buffer_depth"):
            SjonScreenConfig(buffer_depth=0)

    def test_negative_monitor_index(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        with pytest.raises(ValueError, match="monitor_index"):
            SjonScreenConfig(monitor_index=-1)

    def test_negative_min_interval_ms(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        with pytest.raises(ValueError, match="min_interval_ms"):
            SjonScreenConfig(min_interval_ms=-1)

    def test_crop_negative_x(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        with pytest.raises(ValueError, match="crop.x"):
            SjonScreenConfig(crop={"x": -1, "y": 0, "w": 100, "h": 100})

    def test_crop_non_integer_w(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        with pytest.raises(ValueError, match="crop.w"):
            SjonScreenConfig(crop={"x": 0, "y": 0, "w": 1.5, "h": 100})

    def test_crop_valid_passes(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        # Valid crop should not raise.
        cfg = SjonScreenConfig(crop={"x": 0, "y": 0, "w": 640, "h": 360})
        assert cfg.crop is not None

    def test_zero_interval_ms_is_valid(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        # interval_ms=0 is valid (disable periodic capture)
        cfg = SjonScreenConfig(interval_ms=0)
        assert cfg.interval_ms == 0

    def test_zero_min_interval_ms_is_valid(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        # min_interval_ms=0 means no throttle guard
        cfg = SjonScreenConfig(min_interval_ms=0)
        assert cfg.min_interval_ms == 0


class TestSjonScreenConfigSaveFramesWarning:
    """SjonScreenConfig(save_frames=True) emits a log warning — non-fatal."""

    def test_save_frames_true_warns(self, caplog: pytest.LogCaptureFixture) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        with caplog.at_level(logging.WARNING, logger="heretic.sjon.config_model"):
            cfg = SjonScreenConfig(save_frames=True)
        assert cfg.save_frames is True
        assert any("save_frames" in record.message for record in caplog.records)

    def test_save_frames_false_no_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        with caplog.at_level(logging.WARNING, logger="heretic.sjon.config_model"):
            SjonScreenConfig(save_frames=False)
        # No save_frames warning when False (the default)
        assert not any("save_frames" in record.message for record in caplog.records)


# ---------------------------------------------------------------------------
# SjonWebcamConfig
# ---------------------------------------------------------------------------

class TestSjonWebcamConfigDefaults:
    def test_defaults(self) -> None:
        from heretic.sjon.config_model import SjonWebcamConfig
        cfg = SjonWebcamConfig()
        assert cfg.enabled is False
        assert cfg.device == "default"
        assert cfg.interval_ms == 10000

    def test_negative_interval_ms_raises(self) -> None:
        from heretic.sjon.config_model import SjonWebcamConfig
        with pytest.raises(ValueError, match="interval_ms"):
            SjonWebcamConfig(interval_ms=-1)


# ---------------------------------------------------------------------------
# SjonConfig (root)
# ---------------------------------------------------------------------------

class TestSjonConfig:
    def test_default_sub_config_types(self) -> None:
        from heretic.sjon.config_model import SjonConfig, SjonScreenConfig, SjonWebcamConfig
        cfg = SjonConfig()
        assert isinstance(cfg.screen, SjonScreenConfig)
        assert isinstance(cfg.webcam, SjonWebcamConfig)

    def test_screen_defaults_accessible(self) -> None:
        from heretic.sjon.config_model import SjonConfig
        cfg = SjonConfig()
        assert cfg.screen.max_width == 1280
        assert cfg.screen.max_height == 720


# ---------------------------------------------------------------------------
# Approach B: grunnr.config re-exports the same class objects
# ---------------------------------------------------------------------------

class TestApproachBImports:
    """Verify that grunnr.config re-exports are identical class objects to sjon.config_model."""

    def test_sjon_config_same_class(self) -> None:
        from heretic.grunnr.config import SjonConfig as GrunnrSjonConfig
        from heretic.sjon.config_model import SjonConfig as SjonModuleConfig
        assert GrunnrSjonConfig is SjonModuleConfig

    def test_sjon_screen_config_same_class(self) -> None:
        from heretic.grunnr.config import SjonScreenConfig as GrunnrScreen
        from heretic.sjon.config_model import SjonScreenConfig as SjonScreen
        assert GrunnrScreen is SjonScreen

    def test_sjon_webcam_config_same_class(self) -> None:
        from heretic.grunnr.config import SjonWebcamConfig as GrunnrWebcam
        from heretic.sjon.config_model import SjonWebcamConfig as SjonWebcam
        assert GrunnrWebcam is SjonWebcam


# ---------------------------------------------------------------------------
# HereticConfig.sjon field
# ---------------------------------------------------------------------------

class TestHereticConfigSjonField:
    def test_heretic_config_sjon_is_sjon_config(self) -> None:
        from heretic.grunnr.config import HereticConfig
        from heretic.sjon.config_model import SjonConfig
        cfg = HereticConfig.default()
        assert isinstance(cfg.sjon, SjonConfig)

    def test_heretic_config_sjon_screen_defaults(self) -> None:
        from heretic.grunnr.config import HereticConfig
        cfg = HereticConfig.default()
        assert cfg.sjon.screen.max_width == 1280
        assert cfg.sjon.screen.max_height == 720
        assert cfg.sjon.screen.save_frames is False


# ---------------------------------------------------------------------------
# v0.5.1 placeholder tests — continuous + attach_policy fields
# Forge implements the logic; these stubs mark the scaffold complete.
# ---------------------------------------------------------------------------

class TestSjonScreenConfigContinuousField:
    """SjonScreenConfig.continuous field — v0.5.1 additions. (Placeholders: Forge implements.)"""

    @pytest.mark.skip(reason="v0.5.1 placeholder — Forge implements continuous default")
    def test_continuous_default_is_false(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        cfg = SjonScreenConfig()
        assert cfg.continuous is False

    @pytest.mark.skip(reason="v0.5.1 placeholder — Forge verifies continuous=True accepted")
    def test_continuous_true_accepted(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        cfg = SjonScreenConfig(continuous=True)
        assert cfg.continuous is True

    @pytest.mark.skip(
        reason="v0.5.1 placeholder — Forge verifies sub-500ms continuous interval warns"
    )
    def test_continuous_sub500ms_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        with caplog.at_level(logging.WARNING, logger="heretic.sjon.config_model"):
            SjonScreenConfig(continuous=True, interval_ms=200)
        assert any("interval_ms" in r.message for r in caplog.records)


class TestSjonScreenConfigAttachPolicyField:
    """SjonScreenConfig.attach_policy field — v0.5.1 additions. (Placeholders: Forge implements.)"""

    @pytest.mark.skip(reason="v0.5.1 placeholder — Forge verifies attach_policy default")
    def test_attach_policy_default_is_latest(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        cfg = SjonScreenConfig()
        assert cfg.attach_policy == "latest"

    @pytest.mark.skip(reason="v0.5.1 placeholder — Forge verifies all_buffered accepted")
    def test_attach_policy_all_buffered_accepted(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        cfg = SjonScreenConfig(attach_policy="all_buffered")
        assert cfg.attach_policy == "all_buffered"

    @pytest.mark.skip(reason="v0.5.1 placeholder — Forge verifies none accepted")
    def test_attach_policy_none_accepted(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        cfg = SjonScreenConfig(attach_policy="none")
        assert cfg.attach_policy == "none"

    @pytest.mark.skip(reason="v0.5.1 placeholder — Forge verifies invalid attach_policy raises")
    def test_attach_policy_invalid_raises(self) -> None:
        from heretic.sjon.config_model import SjonScreenConfig
        with pytest.raises(ValueError, match="attach_policy"):
            SjonScreenConfig(attach_policy="streaming")
