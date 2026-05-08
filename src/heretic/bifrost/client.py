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
import json
import logging
from typing import Any, AsyncIterator, Optional

import httpx

from heretic.bifrost.config_model import BifrostConfig
from heretic.bifrost.errors import (
    BifrostAuthError,
    BifrostConnectionError,
    BifrostProbeError,
    BifrostProtocolError,
    BifrostTimeoutError,
)
from heretic.bifrost.tailscale import TailscaleAwareness

_log = logging.getLogger("heretic.bifrost.client")


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

    @property
    @abc.abstractmethod
    def capability_vision_screen(self) -> bool:
        """True if HERETIC has a working screen capture backend (L3 Sjón body-state flag).

        Distinct from capability_vision_in (agent capability).
        Frames are injected only when BOTH are True.
        """


class OpenAICompatClient(BifrostClient):
    """OpenAI Chat Completions API client with streaming and tool_use support.

    Default BifrostClient implementation for v0.1. Uses httpx.AsyncClient for all
    HTTP — never requests or aiohttp. Tailscale awareness is delegated to
    TailscaleAwareness, which resolves the effective endpoint before open() calls.

    The agent is the spirit; this client is the gate in Bifröst. It carries messages
    faithfully — it does not decide meaning, tools, or persona.
    """

    def __init__(self, config: BifrostConfig) -> None:
        """Initialise the client with the given Bifröst config.

        Args:
            config: Populated BifrostConfig. The api_key field must already be resolved
                    (env var expanded) — raw ${VAR} strings must never reach HTTP headers.
        """
        self._config = config
        self._http_client: Optional[httpx.AsyncClient] = None
        self._base_url: str = ""
        self._capability_tool_use: bool = False
        self._capability_vision_in: bool = False
        self._capability_streaming: bool = False
        # ?vision_screen: HERETIC body-state flag (distinct from ?vision_in).
        # ?vision_in  — agent capability: does the spirit accept image content?
        # ?vision_screen — body state: does HERETIC have a working screen capture backend?
        # Frames are injected only when BOTH are True.
        # Set by the CLI/serve after Sjón initialises and reports is_available.
        self._capability_vision_screen: bool = False

    # ------------------------------------------------------------------
    # Public API — BifrostClient contract
    # ------------------------------------------------------------------

    async def open(self) -> None:
        """Open the httpx.AsyncClient and run the capability probe.

        Per AGENT_AGNOSTIC_PROTOCOL.md §5.1: sends a minimal chat completion
        request to determine which capability flags to set. On failure the flags
        default to False and a BifrostProbeError is raised — the ceremony may
        still proceed with conservative defaults.

        Raises:
            BifrostConnectionError: endpoint unreachable.
            BifrostAuthError: HTTP 401 or 403.
            BifrostProbeError: probe timed out.
        """
        ts = TailscaleAwareness(self._config)
        self._base_url = ts.resolve_endpoint()
        _log.info(
            "Opening Bifröst to %s (Tailscale active: %s)",
            self._base_url, ts.tailscale_active,
        )

        # Log whether this is a Tailscale address — informational only
        try:
            from urllib.parse import urlparse
            host = urlparse(self._base_url).hostname or ""
            if ts.is_tailscale_address(host):
                _log.debug("Endpoint host %r is in Tailscale CGNAT range (100.64.0.0/10)", host)
            else:
                _log.debug("Endpoint host %r is not a Tailscale address", host)
        except Exception:
            pass  # never let informational logging crash the open sequence

        timeout = httpx.Timeout(
            connect=float(self._config.connect_timeout_seconds),
            read=float(self._config.timeout_seconds),
            write=float(self._config.timeout_seconds),
            pool=float(self._config.connect_timeout_seconds),
        )
        self._http_client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self._config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

        await self._run_capability_probe()

    async def send_message(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> AsyncIterator[str]:
        """Send a turn to the agent and yield response chunks.

        Each yielded string is either:
          - A text delta from the agent's reply
          - A JSON-encoded tool call record when the agent requests a tool

        Raises:
            BifrostTimeoutError: if the stream does not start in time.
            BifrostProtocolError: if the response is malformed.
        """
        if self._http_client is None:
            raise BifrostConnectionError("Client is not open — call open() first.")

        payload = self._build_payload(messages, tools)
        url = f"{self._base_url}/chat/completions"

        try:
            async with self._http_client.stream("POST", url, json=payload) as response:
                self._check_http_status(response)
                async for chunk in self._parse_sse_stream(response):
                    yield chunk
        except httpx.TimeoutException as exc:
            raise BifrostTimeoutError(
                f"Agent did not respond within {self._config.timeout_seconds}s: {exc}"
            ) from exc
        except httpx.ConnectError as exc:
            raise BifrostConnectionError(
                f"Cannot reach agent at {self._base_url}: {exc}"
            ) from exc
        except (BifrostTimeoutError, BifrostProtocolError, BifrostAuthError,
                BifrostConnectionError):
            raise  # re-raise typed Bifrost errors as-is
        except Exception as exc:
            _log.error("Unexpected error in send_message: %s", exc, exc_info=True)
            raise BifrostProtocolError(f"Unexpected error during message send: {exc}") from exc

    async def close(self) -> None:
        """Close the httpx client and zero session state.

        Safe to call before open() — no-op in that case.
        After close() returns the instance must not be reused.
        """
        if self._http_client is not None:
            try:
                await self._http_client.aclose()
            except Exception as exc:
                _log.warning("Error while closing httpx client: %s", exc)
            finally:
                self._http_client = None
        # Zero capability flags — client is dead after close
        self._capability_tool_use = False
        self._capability_vision_in = False
        self._capability_streaming = False
        self._capability_vision_screen = False
        _log.info("Bifröst closed.")

    # ------------------------------------------------------------------
    # Capability properties
    # ------------------------------------------------------------------

    @property
    def capability_tool_use(self) -> bool:
        return self._capability_tool_use

    @property
    def capability_vision_in(self) -> bool:
        return self._capability_vision_in

    @property
    def capability_streaming(self) -> bool:
        return self._capability_streaming

    @property
    def capability_vision_screen(self) -> bool:
        """True if HERETIC has a working screen capture backend (L3 Sjón).

        This is a HERETIC body-state flag, distinct from capability_vision_in:
          ?vision_in     — agent can receive image content (agent probe result).
          ?vision_screen — HERETIC body has a screen capture backend available.

        Both must be True for frames to be injected into user messages.
        Set by the CLI or serve.py after Sjón initialises and calls is_available.
        """
        return self._capability_vision_screen

    @capability_vision_screen.setter
    def capability_vision_screen(self, value: bool) -> None:
        """Set the ?vision_screen body-state flag from the CLI or serve.py wiring."""
        self._capability_vision_screen = value

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_payload(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]],
    ) -> dict[str, Any]:
        """Construct the /v1/chat/completions request body.

        Per AGENT_AGNOSTIC_PROTOCOL.md §2.1:
          - Uses `tools` array (never the deprecated `functions` key)
          - Honours max_tokens, model, and stream from config
        """
        payload: dict[str, Any] = {
            "model": self._config.model,
            "messages": messages,
            "max_tokens": self._config.max_tokens,
            "stream": self._config.stream,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        return payload

    def _check_http_status(self, response: httpx.Response) -> None:
        """Inspect HTTP status and raise the appropriate Bifrost error."""
        if response.status_code in (401, 403):
            raise BifrostAuthError(
                f"Agent rejected Bearer token (HTTP {response.status_code}). "
                f"Check your HERETIC_AGENT_KEY environment variable."
            )
        if response.status_code >= 500:
            raise BifrostConnectionError(
                f"Agent returned server error HTTP {response.status_code}."
            )
        if response.status_code >= 400:
            raise BifrostProtocolError(
                f"Agent returned client error HTTP {response.status_code}.",
            )

    async def _parse_sse_stream(
        self, response: httpx.Response
    ) -> AsyncIterator[str]:
        """Parse an SSE stream and yield text deltas and tool call records.

        Handles:
          - Partial JSON chunks split across SSE boundary lines
          - [DONE] sentinel
          - Tool call assembly across multiple deltas
          - finish_reason variants (stop, tool_calls, length, content_filter)

        Per AGENT_AGNOSTIC_PROTOCOL.md §2.2 streaming format.
        """
        # Buffer for assembling tool call arguments that arrive in fragments
        tool_call_buffers: dict[int, dict[str, Any]] = {}
        buffer = ""  # accumulates partial SSE data lines

        async for line in response.aiter_lines():
            line = line.strip()

            if not line:
                continue

            if line.startswith("data:"):
                data = line[len("data:"):].strip()
            elif line.startswith("data: "):
                data = line[len("data: "):].strip()
            else:
                continue  # skip comment lines and SSE field types we don't use

            if data == "[DONE]":
                # Flush any assembled tool calls before exiting
                for tc in tool_call_buffers.values():
                    if tc.get("id") and tc.get("name"):
                        yield json.dumps({
                            "type": "tool_call",
                            "id": tc["id"],
                            "name": tc["name"],
                            "arguments": tc.get("arguments", ""),
                        })
                return

            # Parse the SSE JSON chunk
            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                # Partial chunk — buffer and continue (rare but possible at boundaries)
                buffer += data
                try:
                    chunk = json.loads(buffer)
                    buffer = ""
                except json.JSONDecodeError:
                    continue  # still incomplete; wait for next line

            choices = chunk.get("choices", [])
            if not choices:
                continue

            choice = choices[0]
            delta = choice.get("delta", {})
            finish_reason = choice.get("finish_reason")

            # Yield text content deltas
            content = delta.get("content")
            if content:
                yield content

            # Assemble tool call deltas — arguments arrive in fragments
            tool_calls_delta = delta.get("tool_calls", [])
            for tc_delta in tool_calls_delta:
                idx = tc_delta.get("index", 0)
                if idx not in tool_call_buffers:
                    tool_call_buffers[idx] = {"id": "", "name": "", "arguments": ""}

                tc_buf = tool_call_buffers[idx]
                tc_id = tc_delta.get("id", "")
                if tc_id:
                    tc_buf["id"] = tc_id

                fn = tc_delta.get("function", {})
                name_frag = fn.get("name", "")
                if name_frag:
                    tc_buf["name"] = tc_buf["name"] + name_frag

                args_frag = fn.get("arguments", "")
                if args_frag:
                    tc_buf["arguments"] = tc_buf["arguments"] + args_frag

            # On finish, emit completed tool calls
            if finish_reason == "tool_calls":
                for tc in tool_call_buffers.values():
                    if tc.get("id") and tc.get("name"):
                        yield json.dumps({
                            "type": "tool_call",
                            "id": tc["id"],
                            "name": tc["name"],
                            "arguments": tc.get("arguments", ""),
                        })
                tool_call_buffers.clear()
            elif finish_reason == "length":
                _log.warning(
                    "Agent response reached max_tokens limit (%d). Response may be truncated.",
                    self._config.max_tokens,
                )
            elif finish_reason == "content_filter":
                _log.warning("Agent response was filtered by content policy.")

    async def _run_capability_probe(self) -> None:
        """Run the capability probe per AGENT_AGNOSTIC_PROTOCOL.md §5.1.

        Sends a minimal chat completion with a heretic_probe tool and inspects
        the response to determine ?tool_use, ?vision_in, ?streaming capability flags.
        Conservative defaults (all False) are used on any failure — the ceremony
        proceeds without those capabilities rather than aborting.
        """
        assert self._http_client is not None

        probe_payload = {
            "model": self._config.model,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": "HERETIC_CAPABILITY_PROBE"}]}
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "heretic_probe",
                        "description": "Capability probe — respond with tool call to confirm tool support",
                        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
                    }
                }
            ],
            "tool_choice": "auto",
            "stream": False,  # probe is non-streaming so we get a simple response
            "max_tokens": 50,
        }

        url = f"{self._base_url}/chat/completions"
        try:
            probe_timeout = httpx.Timeout(float(self._config.connect_timeout_seconds))
            response = await self._http_client.post(
                url, json=probe_payload, timeout=probe_timeout
            )
        except httpx.TimeoutException as exc:
            _log.warning("Capability probe timed out: %s. Using conservative defaults.", exc)
            raise BifrostProbeError(
                f"Capability probe did not complete within "
                f"{self._config.connect_timeout_seconds}s."
            ) from exc
        except httpx.ConnectError as exc:
            raise BifrostConnectionError(
                f"Cannot reach agent at {self._base_url!r} during probe: {exc}"
            ) from exc

        if response.status_code in (401, 403):
            raise BifrostAuthError(
                f"Agent rejected Bearer token during probe (HTTP {response.status_code})."
            )
        if response.status_code >= 400:
            _log.warning(
                "Probe returned HTTP %d — continuing with conservative capability defaults.",
                response.status_code,
            )
            return  # conservative defaults already in place

        try:
            body = response.json()
        except Exception as exc:
            _log.warning("Could not parse probe response JSON: %s. Using conservative defaults.", exc)
            return

        choices = body.get("choices", [])
        if not choices:
            _log.warning("Probe response had no choices. Using conservative defaults.")
            return

        choice = choices[0]
        message = choice.get("message", {})
        finish_reason = choice.get("finish_reason", "")

        # ?tool_use — agent called heretic_probe tool
        if finish_reason == "tool_calls" or message.get("tool_calls"):
            self._capability_tool_use = True
            _log.info("Capability ?tool_use = True (agent responded to probe tool call)")

        # ?streaming — check if the agent sends SSE events (probed separately in real use;
        # here we assume streaming if agent responded correctly to the probe overall)
        # Full streaming probe would require a stream=True request — deferred to first real turn.
        # Conservative: assume streaming is available if basic connectivity works.
        self._capability_streaming = True
        _log.info("Capability ?streaming = True (optimistic default; verified on first turn)")

        # ?vision_in — not probed here (requires sending an image); set from config
        # A more complete probe would send a minimal base64 image and check for no error.
        self._capability_vision_in = self._config.vision_in
        _log.info("Capability ?vision_in = %s (from config)", self._capability_vision_in)

        _log.info(
            "Bifröst open — capabilities: tool_use=%s vision_in=%s streaming=%s",
            self._capability_tool_use,
            self._capability_vision_in,
            self._capability_streaming,
        )
