"""
Tests for v0.5 vision integration in the CLI and BifrostClient.

Coverage:
    - capability_vision_screen property: getter, setter, reset on close
    - BifrostClient.capability_vision_screen defaults to False
    - capability_vision_screen + capability_vision_in dual-flag gate
    - User message content array structure with image_data_urls
    - OpenAI multimodal content array exactly matches AGENT_AGNOSTIC_PROTOCOL.md §2.1
    - Text-only content array when no vision
"""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# BifrostClient capability_vision_screen
# ---------------------------------------------------------------------------

class TestBifrostClientVisionScreenCapability:
    """Tests for the ?vision_screen body-state flag on OpenAICompatClient."""

    def _make_client(self) -> "OpenAICompatClient":
        from heretic.bifrost.client import OpenAICompatClient
        from heretic.bifrost.config_model import BifrostConfig

        cfg = BifrostConfig(
            endpoint="http://localhost:8643/v1",
            api_key="test-key",
            model="test-model",
        )
        return OpenAICompatClient(cfg)

    def test_capability_vision_screen_defaults_false(self) -> None:
        client = self._make_client()
        assert client.capability_vision_screen is False

    def test_capability_vision_screen_can_be_set(self) -> None:
        client = self._make_client()
        client.capability_vision_screen = True
        assert client.capability_vision_screen is True

    def test_capability_vision_screen_set_false(self) -> None:
        client = self._make_client()
        client.capability_vision_screen = True
        client.capability_vision_screen = False
        assert client.capability_vision_screen is False

    @pytest.mark.asyncio
    async def test_capability_vision_screen_resets_on_close(self) -> None:
        """close() zeroes the capability_vision_screen flag."""
        client = self._make_client()
        client.capability_vision_screen = True
        # close() without opening should be a no-op except for flag reset
        await client.close()
        assert client.capability_vision_screen is False

    def test_capability_vision_in_distinct_from_vision_screen(self) -> None:
        """?vision_in and ?vision_screen are independent flags."""
        client = self._make_client()
        # vision_screen can be True while vision_in is still False (default)
        client.capability_vision_screen = True
        assert client.capability_vision_screen is True
        assert client.capability_vision_in is False


# ---------------------------------------------------------------------------
# Multimodal content array construction
# ---------------------------------------------------------------------------

class TestMultimodalContentArrayConstruction:
    """Verify the content array shape matches AGENT_AGNOSTIC_PROTOCOL.md §2.1 EXACTLY."""

    def test_text_only_content_array(self) -> None:
        """Without images, user message content is a single-element text array."""
        user_text = "Hello agent"
        image_data_urls: list[str] = []

        user_content = [{"type": "text", "text": user_text}]
        for url in image_data_urls:
            user_content.append({"type": "image_url", "image_url": {"url": url}})

        assert len(user_content) == 1
        assert user_content[0] == {"type": "text", "text": "Hello agent"}

    def test_multimodal_content_array_one_image(self) -> None:
        """With one image, content array has text first then image_url block."""
        user_text = "What do you see?"
        fake_data_url = "data:image/png;base64,abc123"
        image_data_urls = [fake_data_url]

        user_content = [{"type": "text", "text": user_text}]
        for url in image_data_urls:
            user_content.append({"type": "image_url", "image_url": {"url": url}})

        # Matches AGENT_AGNOSTIC_PROTOCOL.md §2.1 exactly:
        # [{"type": "text", "text": "..."}, {"type": "image_url", "image_url": {"url": "..."}}]
        assert len(user_content) == 2
        assert user_content[0] == {"type": "text", "text": "What do you see?"}
        assert user_content[1] == {
            "type": "image_url",
            "image_url": {"url": "data:image/png;base64,abc123"},
        }

    def test_multimodal_content_array_multiple_images(self) -> None:
        """Multiple images are appended in order after the text block."""
        user_text = "What's in these frames?"
        image_data_urls = [
            "data:image/png;base64,frame1",
            "data:image/png;base64,frame2",
        ]

        user_content = [{"type": "text", "text": user_text}]
        for url in image_data_urls:
            user_content.append({"type": "image_url", "image_url": {"url": url}})

        assert len(user_content) == 3
        assert user_content[0]["type"] == "text"
        assert user_content[1]["type"] == "image_url"
        assert user_content[1]["image_url"]["url"] == "data:image/png;base64,frame1"
        assert user_content[2]["image_url"]["url"] == "data:image/png;base64,frame2"

    def test_image_url_structure_matches_openai_spec(self) -> None:
        """The image_url block structure matches AGENT_AGNOSTIC_PROTOCOL.md §2.1 contract."""
        data_url = "data:image/png;base64,iVBORw0K..."
        image_block = {"type": "image_url", "image_url": {"url": data_url}}

        # Verify the nested structure is correct — no "detail" field required,
        # no extra wrappers.
        assert image_block["type"] == "image_url"
        assert isinstance(image_block["image_url"], dict)
        assert "url" in image_block["image_url"]
        assert image_block["image_url"]["url"].startswith("data:image/png;base64,")


# ---------------------------------------------------------------------------
# Vision gate logic (dual flag: ?vision_in AND ?vision_screen)
# ---------------------------------------------------------------------------

class TestVisionGateLogic:
    """Tests for the dual-flag gate: frames injected only when BOTH flags are True."""

    def _make_mock_sjon(self, snapshot_result: list) -> MagicMock:
        """Build a mock Sjón orchestrator that returns the given snapshot result."""
        mock_sjon = MagicMock()
        mock_sjon.is_available = True

        async def _mock_snapshot():
            return snapshot_result

        mock_sjon.snapshot = _mock_snapshot
        return mock_sjon

    def _make_mock_client(
        self,
        vision_in: bool = False,
        vision_screen: bool = False,
    ) -> MagicMock:
        """Build a mock BifrostClient with controlled capability flags."""
        mock_client = MagicMock()
        mock_client.capability_vision_in = vision_in
        mock_client.capability_vision_screen = vision_screen
        return mock_client

    @pytest.mark.asyncio
    async def test_no_frame_when_vision_in_false(self) -> None:
        """No frame injected when ?vision_in is False (agent does not support vision)."""
        sjon = self._make_mock_sjon(["data:image/png;base64,frame"])
        client = self._make_mock_client(vision_in=False, vision_screen=True)

        image_data_urls: list[str] = []
        if (
            sjon is not None
            and client.capability_vision_in
            and client.capability_vision_screen
        ):
            image_data_urls = await sjon.snapshot()

        assert image_data_urls == []

    @pytest.mark.asyncio
    async def test_no_frame_when_vision_screen_false(self) -> None:
        """No frame injected when ?vision_screen is False (no screen capture backend)."""
        sjon = self._make_mock_sjon(["data:image/png;base64,frame"])
        client = self._make_mock_client(vision_in=True, vision_screen=False)

        image_data_urls: list[str] = []
        if (
            sjon is not None
            and client.capability_vision_in
            and client.capability_vision_screen
        ):
            image_data_urls = await sjon.snapshot()

        assert image_data_urls == []

    @pytest.mark.asyncio
    async def test_frame_injected_when_both_flags_true(self) -> None:
        """Frame IS injected when both ?vision_in and ?vision_screen are True."""
        sjon = self._make_mock_sjon(["data:image/png;base64,frame"])
        client = self._make_mock_client(vision_in=True, vision_screen=True)

        image_data_urls: list[str] = []
        if (
            sjon is not None
            and client.capability_vision_in
            and client.capability_vision_screen
        ):
            image_data_urls = await sjon.snapshot()

        assert image_data_urls == ["data:image/png;base64,frame"]

    @pytest.mark.asyncio
    async def test_no_frame_when_sjon_is_none(self) -> None:
        """No frame when sjon object is None (init failed)."""
        sjon = None  # Sjón init failed
        client = self._make_mock_client(vision_in=True, vision_screen=True)

        image_data_urls: list[str] = []
        if (
            sjon is not None
            and client.capability_vision_in
            and client.capability_vision_screen
        ):
            image_data_urls = await sjon.snapshot()  # type: ignore[union-attr]

        assert image_data_urls == []


# ---------------------------------------------------------------------------
# Sjón init wiring: vision_screen set from is_available
# ---------------------------------------------------------------------------

class TestSjonInitSetsVisionScreenFlag:
    """Verify that the CLI wires ?vision_screen from sjon.is_available."""

    def test_vision_screen_set_true_when_sjon_available(self) -> None:
        """Simulates the CLI: client.capability_vision_screen = (sjon.is_available)."""
        from heretic.bifrost.client import OpenAICompatClient
        from heretic.bifrost.config_model import BifrostConfig

        cfg = BifrostConfig(
            endpoint="http://localhost:8643/v1",
            api_key="test-key",
            model="test-model",
        )
        client = OpenAICompatClient(cfg)

        # Simulate: sjon init succeeded and is_available is True
        mock_sjon = MagicMock()
        mock_sjon.is_available = True
        if mock_sjon.is_available:
            client.capability_vision_screen = True

        assert client.capability_vision_screen is True

    def test_vision_screen_stays_false_when_sjon_not_available(self) -> None:
        """Simulates the CLI: sjon is None or is_available=False -> flag stays False."""
        from heretic.bifrost.client import OpenAICompatClient
        from heretic.bifrost.config_model import BifrostConfig

        cfg = BifrostConfig(
            endpoint="http://localhost:8643/v1",
            api_key="test-key",
            model="test-model",
        )
        client = OpenAICompatClient(cfg)

        # Simulate: sjon init failed -> sjon = None
        sjon = None
        if sjon is not None and sjon.is_available:
            client.capability_vision_screen = True

        assert client.capability_vision_screen is False


# ---------------------------------------------------------------------------
# v0.5.1 attach_policy logic tests
# ---------------------------------------------------------------------------

class TestAttachPolicyLogic:
    """Tests for per-turn attach_policy dispatch introduced in v0.5.1.

    These tests exercise the policy logic in isolation (not the full CLI),
    mirroring the pattern of TestVisionGateLogic above.
    """

    def _make_sjon_mock(
        self,
        snapshot_result: list[str],
        recent_frames_result: list[str] | None = None,
    ) -> MagicMock:
        """Build a mock Sjón with controlled snapshot() and recent_frames() results.

        snapshot() is an AsyncMock so callers can assert_not_called() / assert_called().
        recent_frames() is a regular MagicMock (sync method).
        """
        mock_sjon = MagicMock()
        mock_sjon.is_available = True

        # Use AsyncMock so the mock is awaitable AND trackable via assert_not_called etc.
        mock_sjon.snapshot = AsyncMock(return_value=snapshot_result)

        if recent_frames_result is not None:
            mock_sjon.recent_frames = MagicMock(return_value=recent_frames_result)
        else:
            mock_sjon.recent_frames = MagicMock(return_value=[])

        return mock_sjon

    def _make_screen_config(
        self,
        policy: str = "latest",
        continuous: bool = False,
    ):
        """Build a minimal screen config stub for policy dispatch tests."""
        cfg = MagicMock()
        cfg.attach_policy = policy
        cfg.continuous = continuous
        return cfg

    @pytest.mark.asyncio
    async def test_attach_policy_none_sends_no_image(self) -> None:
        """attach_policy='none' always results in an empty image list."""
        sjon = self._make_sjon_mock(snapshot_result=["data:image/png;base64,frame"])
        screen_cfg = self._make_screen_config(policy="none")

        # Replicate the CLI attach_policy dispatch logic
        image_data_urls: list[str] = []
        try:
            policy = screen_cfg.attach_policy
            if policy == "none":
                image_data_urls = []
            elif policy == "all_buffered" and screen_cfg.continuous:
                image_data_urls = sjon.recent_frames()
            elif policy == "latest" and screen_cfg.continuous:
                image_data_urls = sjon.recent_frames(n=1)
                if not image_data_urls:
                    image_data_urls = await sjon.snapshot()
            else:
                image_data_urls = await sjon.snapshot()
        except Exception:
            image_data_urls = []

        assert image_data_urls == []
        sjon.snapshot.assert_not_called()

    @pytest.mark.asyncio
    async def test_attach_policy_all_buffered_with_continuous_attaches_all_frames(self) -> None:
        """attach_policy='all_buffered' in continuous mode returns all buffered frames."""
        buffered = [
            "data:image/png;base64,f1",
            "data:image/png;base64,f2",
            "data:image/png;base64,f3",
        ]
        sjon = self._make_sjon_mock(snapshot_result=[], recent_frames_result=buffered)
        screen_cfg = self._make_screen_config(policy="all_buffered", continuous=True)

        image_data_urls: list[str] = []
        policy = screen_cfg.attach_policy
        if policy == "none":
            image_data_urls = []
        elif policy == "all_buffered" and screen_cfg.continuous:
            image_data_urls = sjon.recent_frames()
        elif policy == "latest" and screen_cfg.continuous:
            image_data_urls = sjon.recent_frames(n=1)
            if not image_data_urls:
                image_data_urls = await sjon.snapshot()
        else:
            image_data_urls = await sjon.snapshot()

        assert image_data_urls == buffered
        sjon.recent_frames.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_attach_policy_latest_with_continuous_uses_buffer(self) -> None:
        """attach_policy='latest' in continuous mode uses the single most-recent buffered frame."""
        sjon = self._make_sjon_mock(
            snapshot_result=[],
            recent_frames_result=["data:image/png;base64,most_recent"],
        )
        screen_cfg = self._make_screen_config(policy="latest", continuous=True)

        image_data_urls: list[str] = []
        policy = screen_cfg.attach_policy
        if policy == "none":
            image_data_urls = []
        elif policy == "all_buffered" and screen_cfg.continuous:
            image_data_urls = sjon.recent_frames()
        elif policy == "latest" and screen_cfg.continuous:
            image_data_urls = sjon.recent_frames(n=1)
            if not image_data_urls:
                image_data_urls = await sjon.snapshot()
        else:
            image_data_urls = await sjon.snapshot()

        assert image_data_urls == ["data:image/png;base64,most_recent"]
        sjon.recent_frames.assert_called_once_with(n=1)

    @pytest.mark.asyncio
    async def test_attach_policy_latest_with_empty_buffer_falls_back_to_snapshot(self) -> None:
        """'latest' with empty buffer (interval not yet fired) falls back to on-demand snapshot."""
        sjon = self._make_sjon_mock(
            snapshot_result=["data:image/png;base64,on_demand"],
            recent_frames_result=[],  # buffer empty
        )
        screen_cfg = self._make_screen_config(policy="latest", continuous=True)

        image_data_urls: list[str] = []
        policy = screen_cfg.attach_policy
        if policy == "none":
            image_data_urls = []
        elif policy == "all_buffered" and screen_cfg.continuous:
            image_data_urls = sjon.recent_frames()
        elif policy == "latest" and screen_cfg.continuous:
            image_data_urls = sjon.recent_frames(n=1)
            if not image_data_urls:
                image_data_urls = await sjon.snapshot()
        else:
            image_data_urls = await sjon.snapshot()

        assert image_data_urls == ["data:image/png;base64,on_demand"]

    @pytest.mark.asyncio
    async def test_attach_policy_latest_on_demand_uses_snapshot(self) -> None:
        """'latest' with continuous=False uses the on-demand snapshot() path."""
        sjon = self._make_sjon_mock(
            snapshot_result=["data:image/png;base64,snap"],
            recent_frames_result=["data:image/png;base64,should_not_use"],
        )
        screen_cfg = self._make_screen_config(policy="latest", continuous=False)

        image_data_urls: list[str] = []
        policy = screen_cfg.attach_policy
        if policy == "none":
            image_data_urls = []
        elif policy == "all_buffered" and screen_cfg.continuous:
            image_data_urls = sjon.recent_frames()
        elif policy == "latest" and screen_cfg.continuous:
            image_data_urls = sjon.recent_frames(n=1)
            if not image_data_urls:
                image_data_urls = await sjon.snapshot()
        else:
            image_data_urls = await sjon.snapshot()

        # On-demand: snapshot() called, recent_frames() never called
        assert image_data_urls == ["data:image/png;base64,snap"]
        sjon.recent_frames.assert_not_called()
