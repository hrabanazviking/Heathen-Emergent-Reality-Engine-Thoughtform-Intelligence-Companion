"""
Placeholder tests for heretic.sjon.config_model.

These tests are skip-marked during the v0.5 scaffold phase. Forge implements
the full test suite in Wave 2 after the stubs in config_model.py are filled.

Coverage targets (Forge):
    - SjonScreenConfig defaults match LAYER_INTERFACES.md §L3 config keys
    - SjonScreenConfig.__post_init__ validation: interval_ms<0, max_width<1,
      max_height<1, buffer_depth<1, monitor_index<0, min_interval_ms<0,
      crop with non-int / negative values
    - SjonScreenConfig save_frames=True emits a log warning (not an error)
    - SjonWebcamConfig defaults match heretic.example.yaml webcam block
    - SjonConfig default() round-trips through _merge_dict_into_dataclass in grunnr
    - heretic.grunnr.config.HereticConfig.sjon field is a SjonConfig instance
    - grunnr.config.SjonConfig, SjonScreenConfig, SjonWebcamConfig imports are
      identical objects to heretic.sjon.config_model exports (Approach B — no duplication)
"""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
def test_sjon_screen_config_defaults() -> None:
    """SjonScreenConfig default values match LAYER_INTERFACES.md §L3 canonical block."""
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


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
def test_sjon_screen_config_validation_rejects_negative_interval() -> None:
    """SjonScreenConfig raises ValueError for negative interval_ms."""
    from heretic.sjon.config_model import SjonScreenConfig
    with pytest.raises(ValueError, match="interval_ms"):
        SjonScreenConfig(interval_ms=-1)


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
def test_sjon_screen_config_save_frames_warning(caplog: pytest.LogCaptureFixture) -> None:
    """SjonScreenConfig(save_frames=True) emits a log warning (non-fatal)."""
    import logging
    from heretic.sjon.config_model import SjonScreenConfig
    with caplog.at_level(logging.WARNING, logger="heretic.sjon.config_model"):
        cfg = SjonScreenConfig(save_frames=True)
    assert cfg.save_frames is True
    assert any("save_frames" in record.message for record in caplog.records)


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
def test_grunnr_sjon_import_is_same_class() -> None:
    """Approach B: grunnr.config.SjonConfig is the same class as sjon.config_model.SjonConfig."""
    from heretic.grunnr.config import SjonConfig as GrunnrSjonConfig
    from heretic.sjon.config_model import SjonConfig as SjonModuleConfig
    assert GrunnrSjonConfig is SjonModuleConfig


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
def test_heretic_config_sjon_field_is_sjon_config() -> None:
    """HereticConfig.sjon is a SjonConfig instance populated from heretic.sjon.config_model."""
    from heretic.grunnr.config import HereticConfig
    from heretic.sjon.config_model import SjonConfig
    cfg = HereticConfig.default()
    assert isinstance(cfg.sjon, SjonConfig)
