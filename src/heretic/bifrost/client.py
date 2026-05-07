"""
Bifröst client — abstract base and OpenAI-compatible implementation skeleton.

The BifrostClient ABC defines the contract every agent connection must satisfy.
OpenAICompatClient is the concrete implementation for v0.1: an async httpx-based
client that speaks the OpenAI Chat Completions API with streaming tool_use support.

The agent protocol spoken here is defined in docs/architecture/AGENT_AGNOSTIC_PROTOCOL.md.

Key design decisions locked by Architect at v0.1 scaffold:
    - httpx (not aiohttp, not requests) — async-native, modern, MIT-licensed
    - Server-Sent Events (SSE) streaming — httpx.AsyncClient supports this natively
    - Tool calls use the ``tools`` array format (not deprecated ``functions``) per
      ROADMAP.md §v0.1 Open architectural questions Q2
    - No LiteLLM normaliser in v0.1 — OpenAI-compat is sufficient (see ROADMAP.md D-5)

Capability flags:
    After a successful capability probe, OpenAICompatClient populates capability flags:
        ?tool_use   — agent supports tool_call / tool_result JSON
        ?vision_in  — agent can receive image content in messages
        ?streaming  — agent supports SSE streaming responses
    These flags gate feature injection in the turn-building logic.

Ref:
    docs/architecture/LAYER_INTERFACES.md §L1 Bifröst
    docs/architecture/AGENT_AGNOSTIC_PROTOCOL.md
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, AsyncIterator, Optional

if TYPE_CHECKING:
    from heretic.bifrost.config_model import BifrostConfig
    from heretic.grunnr.config import HereticConfig


class BifrostClient(abc.ABC):
    """Abstract base class: the contract every agent connection must satisfy.

    Implementations:
        OpenAICompatClient — default; speaks /v1/chat/completions with tools + SSE.

    Future implementations (v1.x+) might add native adapters for specific agents,
    but the ABC contract below must remain stable — it is what the rest of HERETIC
    calls, never the concrete class directly.
    """

    @abc.abstractmethod
    async def open(self) -> None:
        """Open the connection and perform the capability probe.

        Lifecycle: OPENING state. After this returns without raising, the client
        is ready to receive turns. Capability flags are populated.

        Raises:
            BifrostConnectionError: if the endpoint is unreachable.
            BifrostAuthError: if the agent rejects the Bearer token.
            BifrostProbeError: if the capability probe times out.
        """

    @abc.abstractmethod
    async def send_message(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> AsyncIterator[str]:
        """Send a turn to the agent and return an async iterator of response chunks.

        Each chunk is a UTF-8 text fragment of the agent's reply (delta content from
        the SSE stream). Tool call events are emitted as structured JSON strings per
        the AGENT_AGNOSTIC_PROTOCOL.md §Tool Call Format.

        Args:
            messages: The full conversation history in OpenAI message format.
                      The last message is the current user turn.
            tools: Optional list of tool schemas to inject into this turn.
                   If None, no tools are offered to the agent.

        Yields:
            str: Text delta chunks from the streaming response, or JSON-encoded
                 tool_call events when the agent requests a tool.

        Raises:
            BifrostTimeoutError: if the response stream does not start in time.
            BifrostProtocolError: if the response is malformed.
        """

    @abc.abstractmethod
    async def close(self) -> None:
        """Close the connection and release all resources.

        Safe to call if the connection was never opened (no-op in that case).
        After close() returns, the client instance must not be reused.
        """

    @property
    @abc.abstractmethod
    def capability_tool_use(self) -> bool:
        """True if the agent supports tool_call / tool_result JSON format."""

    @property
    @abc.abstractmethod
    def capability_vision_in(self) -> bool:
        """True if the agent can receive image content in messages."""

    @property
    @abc.abstractmethod
    def capability_streaming(self) -> bool:
        """True if the agent supports SSE streaming responses."""


class OpenAICompatClient(BifrostClient):
    """OpenAI Chat Completions API client with streaming and tool_use support.

    This is the default BifrostClient implementation for v0.1.
    Uses httpx.AsyncClient for all HTTP communication — never requests or aiohttp.

    Tailscale awareness is delegated to TailscaleAwareness (tailscale.py), which
    resolves the effective endpoint URL before the first open() call.

    The agent is the spirit; this client is the gate in Bifröst. It does not decide
    what to say or what tools mean — it only carries messages and calls faithfully.
    """

    def __init__(self, config: "BifrostConfig") -> None:
        """Initialise the client with the given Bifröst config.

        Args:
            config: Populated BifrostConfig from HereticConfig.bifrost.
                    The api_key field must already be resolved (env var expanded)
                    before passing here — call paths.resolve_env_var() first.
        """
        self._config = config
        self._http_client: Any = None  # httpx.AsyncClient — set in open()
        self._capability_tool_use: bool = False
        self._capability_vision_in: bool = False
        self._capability_streaming: bool = False

    async def open(self) -> None:
        """Open the httpx.AsyncClient and run the capability probe.

        Forge will implement the full probe logic per AGENT_AGNOSTIC_PROTOCOL.md §5.1.
        The probe sends a minimal /v1/chat/completions request and inspects the
        response to determine which capability flags to set.
        """
        raise NotImplementedError(
            "Forge will implement: OpenAICompatClient.open — "
            "instantiate httpx.AsyncClient with timeout from BifrostConfig, "
            "resolve endpoint via TailscaleAwareness.resolve_endpoint(), "
            "set Authorization header from resolved api_key, "
            "run capability probe per AGENT_AGNOSTIC_PROTOCOL.md §5.1, "
            "populate capability flags."
        )

    async def send_message(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> AsyncIterator[str]:
        """Stream a chat completion turn from the agent.

        Forge will implement SSE parsing, tool_call event detection, heartbeat
        management, and reconnect-on-drop logic.
        """
        raise NotImplementedError(
            "Forge will implement: OpenAICompatClient.send_message — "
            "POST to {endpoint}/chat/completions with messages + tools, "
            "stream SSE chunks, yield text deltas as str, "
            "detect tool_call events and yield as JSON-encoded tool call records, "
            "respect max_tokens, stream, and model from BifrostConfig, "
            "raise BifrostTimeoutError / BifrostProtocolError as appropriate."
        )
        # Unreachable; satisfies type checkers for the async iterator return type.
        yield  # type: ignore[misc]

    async def close(self) -> None:
        """Close the httpx client and zero session state."""
        raise NotImplementedError(
            "Forge will implement: OpenAICompatClient.close — "
            "await self._http_client.aclose() if not None, "
            "reset capability flags to False."
        )

    @property
    def capability_tool_use(self) -> bool:
        return self._capability_tool_use

    @property
    def capability_vision_in(self) -> bool:
        return self._capability_vision_in

    @property
    def capability_streaming(self) -> bool:
        return self._capability_streaming
