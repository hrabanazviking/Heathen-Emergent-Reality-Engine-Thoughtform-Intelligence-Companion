"""
pytest fixtures for the HERETIC test suite.

Forge will populate real fixtures here as each module gains implementation.
For now this file ensures pytest can discover the tests/ directory and provides
placeholder fixtures that test modules can reference.

Fixture design notes (Forge should follow these when implementing):
    - ``minimal_config``: returns a HereticConfig.default() — no file I/O
    - ``tmp_heretic_yaml``: writes a minimal heretic.yaml to a tmp_path and returns
      the path — for testing load_config() in isolation
    - ``mock_agent_server``: an httpx_mock-based fixture that emulates the
      OpenAI Chat Completions SSE endpoint for Bifröst client tests
    - ``lifecycle_fresh``: a freshly instantiated Lifecycle(HVILD) instance

All fixtures must be side-effect free and require no network access.
"""

from __future__ import annotations

import pytest

from heretic.grunnr.config import HereticConfig
from heretic.grunnr.lifecycle import Lifecycle, LifecycleState


@pytest.fixture
def minimal_config() -> HereticConfig:
    """Return a HereticConfig populated entirely with defaults.

    No file I/O. Safe to use in any test that needs a config without caring
    about specific values.
    """
    return HereticConfig.default()


@pytest.fixture
def lifecycle_fresh() -> Lifecycle:
    """Return a fresh Lifecycle instance in the HVILD (dormant) state."""
    return Lifecycle(initial=LifecycleState.HVILD)
