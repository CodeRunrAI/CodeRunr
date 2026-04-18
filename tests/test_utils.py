import socket
from unittest.mock import patch

import pytest
from pydantic import TypeAdapter, ValidationError

from fastapi import HTTPException
from utils.security import require_api_key
from utils.ssrf_guard import assert_public_url
from config import settings
from pydantic import HttpUrl


class TestSecurityUtil:
    """Test the security utils"""

    @pytest.mark.asyncio
    async def test_require_api_key(self):
        key = await require_api_key(settings.AUTH_TOKEN.get_secret_value())
        assert key == settings.AUTH_TOKEN.get_secret_value()

    @pytest.mark.asyncio
    async def test_require_api_key_with_wrong_key(self):
        # This should raise HttpException
        with pytest.raises(HTTPException):
            await require_api_key("this is wrong key")

    @pytest.mark.asyncio
    async def test_require_api_key_with_none_key(self):
        # This should raise HttpException
        with pytest.raises(HTTPException):
            await require_api_key(None)


class TestSSRFGuard:
    """Tests for SSRF protection in webhook URL validation."""

    _URL_ADAPTER = TypeAdapter(HttpUrl)

    def _make_url(self, raw: str) -> HttpUrl:
        return self._URL_ADAPTER.validate_python(raw)

    def _ipv4_addr_info(self, ip: str):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 80))]

    def _ipv6_addr_info(self, ip: str):
        return [(socket.AF_INET6, socket.SOCK_STREAM, 6, "", (ip, 80, 0, 0))]

    # ------------------------------------------------------------------
    # Blocked private / reserved addresses
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "ip,label",
        [
            ("127.0.0.1", "loopback"),
            ("127.0.0.2", "loopback range"),
            ("10.0.0.1", "RFC-1918 class A"),
            ("172.16.0.1", "RFC-1918 class B"),
            ("172.31.255.255", "RFC-1918 class B boundary"),
            ("192.168.1.1", "RFC-1918 class C"),
            ("169.254.169.254", "link-local / AWS metadata"),
            ("100.64.0.1", "shared address space RFC-6598"),
            ("0.0.0.1", "this-network"),
            ("192.0.0.1", "IETF protocol assignments"),
        ],
    )
    def test_blocked_private_ipv4(self, ip, label):
        url = self._make_url("http://example.com/callback")
        with patch(
            "utils.ssrf_guard.socket.getaddrinfo",
            return_value=self._ipv4_addr_info(ip),
        ):
            with pytest.raises(ValueError, match="private or reserved"):
                assert_public_url(url)

    @pytest.mark.parametrize(
        "ip,label",
        [
            ("::1", "IPv6 loopback"),
            ("fc00::1", "IPv6 unique local"),
            ("fdff:ffff:ffff:ffff:ffff:ffff:ffff:ffff", "IPv6 unique local boundary"),
            ("fe80::1", "IPv6 link-local"),
        ],
    )
    def test_blocked_private_ipv6(self, ip, label):
        url = self._make_url("http://example.com/callback")
        with patch(
            "utils.ssrf_guard.socket.getaddrinfo",
            return_value=self._ipv6_addr_info(ip),
        ):
            with pytest.raises(ValueError, match="private or reserved"):
                assert_public_url(url)

    # ------------------------------------------------------------------
    # Public addresses — must be allowed
    # ------------------------------------------------------------------

    def test_public_ipv4_allowed(self):
        url = self._make_url("https://example.com/callback")
        with patch(
            "utils.ssrf_guard.socket.getaddrinfo",
            return_value=self._ipv4_addr_info("93.184.216.34"),
        ):
            result = assert_public_url(url)
            assert result == url

    def test_public_ipv6_allowed(self):
        url = self._make_url("https://example.com/callback")
        with patch(
            "utils.ssrf_guard.socket.getaddrinfo",
            return_value=self._ipv6_addr_info("2606:2800:220:1:248:1893:25c8:1946"),
        ):
            result = assert_public_url(url)
            assert result == url

    # ------------------------------------------------------------------
    # DNS edge cases
    # ------------------------------------------------------------------

    def test_unresolvable_host_is_blocked(self):
        url = self._make_url("https://this-does-not-exist.internal/cb")
        with patch(
            "utils.ssrf_guard.socket.getaddrinfo",
            side_effect=socket.gaierror("Name or service not known"),
        ):
            with pytest.raises(ValueError, match="could not be resolved"):
                assert_public_url(url)

    def test_mixed_public_and_private_resolves_is_blocked(self):
        """A host returning both a public and private IP must be rejected."""
        url = self._make_url("https://tricky.example.com/callback")
        mixed = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 80)),
        ]
        with patch("utils.ssrf_guard.socket.getaddrinfo", return_value=mixed):
            with pytest.raises(ValueError, match="private or reserved"):
                assert_public_url(url)

    # ------------------------------------------------------------------
    # Schema integration — SubmissionCreate
    # ------------------------------------------------------------------

    def test_submission_schema_rejects_private_webhook(self):
        from schema.submission import SubmissionCreate

        with patch(
            "utils.ssrf_guard.socket.getaddrinfo",
            return_value=self._ipv4_addr_info("169.254.169.254"),
        ):
            with pytest.raises(ValidationError) as exc_info:
                SubmissionCreate(
                    source_code="print('hi')",
                    language_id=3,
                    webhook_url="http://metadata.internal/latest/",
                )
            assert "private or reserved" in str(exc_info.value)

    def test_submission_schema_accepts_public_webhook(self):
        from schema.submission import SubmissionCreate

        with patch(
            "utils.ssrf_guard.socket.getaddrinfo",
            return_value=self._ipv4_addr_info("93.184.216.34"),
        ):
            submission = SubmissionCreate(
                source_code="print('hi')",
                language_id=3,
                webhook_url="https://example.com/callback",
            )
        assert submission.webhook_url is not None

    def test_submission_schema_accepts_no_webhook(self):
        from schema.submission import SubmissionCreate

        submission = SubmissionCreate(
            source_code="print('hi')",
            language_id=3,
            webhook_url=None,
        )
        assert submission.webhook_url is None
