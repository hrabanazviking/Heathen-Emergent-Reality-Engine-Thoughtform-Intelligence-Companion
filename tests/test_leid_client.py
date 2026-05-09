"""
Placeholder tests for LeidClient — sandboxed HTTP fetch operations.

Ref: src/heretic/skilningr/senses/leid/client.py
"""

from __future__ import annotations

import pytest

from heretic.skilningr.config_model import LeidConfig
from heretic.skilningr.senses.leid.client import LeidClient
from heretic.skilningr.senses.leid.errors import UrlNotAllowedError


class TestLeidClientUrlGateway:

    def test_validate_url_accepted(self):
        """_validate_url accepts a URL matching an allowlist pattern."""
        config = LeidConfig(url_allowlist_patterns=["https://docs.python.org/*"])
        client = LeidClient(config)
        normalised = client._validate_url("https://docs.python.org/3/library/os.html")
        assert "docs.python.org" in normalised

    def test_validate_url_not_in_allowlist_raises(self):
        """_validate_url raises UrlNotAllowedError for non-matching URLs."""
        config = LeidConfig(url_allowlist_patterns=["https://docs.python.org/*"])
        client = LeidClient(config)
        with pytest.raises(UrlNotAllowedError):
            client._validate_url("https://evil.com/steal")

    def test_validate_http_rejected_when_https_only(self):
        """HTTP URL is rejected when allow_http=False (default)."""
        config = LeidConfig(
            url_allowlist_patterns=["http://example.com/*"],
            allow_http=False,
        )
        client = LeidClient(config)
        with pytest.raises(UrlNotAllowedError, match="HTTP"):
            client._validate_url("http://example.com/page")

    def test_validate_http_accepted_when_allow_http(self):
        """HTTP URL is accepted when allow_http=True and pattern matches."""
        config = LeidConfig(
            url_allowlist_patterns=["http://example.com/*"],
            allow_http=True,
        )
        client = LeidClient(config)
        normalised = client._validate_url("http://example.com/page")
        assert "example.com" in normalised


@pytest.mark.skip(reason="Wave 2 — LeidClient.fetch_url not yet implemented by Forge")
class TestLeidClientFetchUrl:

    @pytest.mark.asyncio
    async def test_fetch_url_success(self):
        pass

    @pytest.mark.asyncio
    async def test_fetch_url_timeout(self):
        pass

    @pytest.mark.asyncio
    async def test_fetch_url_response_too_large(self):
        pass


@pytest.mark.skip(reason="Wave 2 — LeidClient.extract_text not yet implemented by Forge")
class TestLeidClientExtractText:

    @pytest.mark.asyncio
    async def test_extract_text_strips_html(self):
        pass
