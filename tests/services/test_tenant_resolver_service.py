# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for TenantResolverService."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

from shomer.services.tenant_resolver_service import TenantResolverService


def _mock_request(host: str = "localhost", path: str = "/") -> MagicMock:
    req = MagicMock()
    headers = MagicMock()
    headers.get = MagicMock(side_effect=lambda k, d="": host if k == "host" else d)
    req.headers = headers
    req.url.path = path
    return req


class TestResolveSubdomain:
    """Tests for subdomain-based resolution."""

    def test_subdomain_resolves_tenant(self) -> None:
        async def _run() -> None:
            tid = uuid.uuid4()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = tid

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantResolverService(db)
            result = await svc._resolve_subdomain(_mock_request(host="acme.shomer.io"))
            assert result == tid

        asyncio.run(_run())

    def test_no_subdomain_returns_none(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            svc = TenantResolverService(db)
            result = await svc._resolve_subdomain(_mock_request(host="shomer.io"))
            assert result is None

        asyncio.run(_run())

    def test_excluded_subdomain_returns_none(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            svc = TenantResolverService(db)
            result = await svc._resolve_subdomain(_mock_request(host="www.shomer.io"))
            assert result is None

        asyncio.run(_run())

    def test_api_subdomain_excluded(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            svc = TenantResolverService(db)
            result = await svc._resolve_subdomain(_mock_request(host="api.shomer.io"))
            assert result is None

        asyncio.run(_run())

    def test_localhost_excluded(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            svc = TenantResolverService(db)
            result = await svc._resolve_subdomain(
                _mock_request(host="localhost.shomer.io")
            )
            assert result is None

        asyncio.run(_run())


class TestResolvePathPrefix:
    """Tests for path prefix resolution."""

    def test_path_prefix_resolves_tenant(self) -> None:
        async def _run() -> None:
            tid = uuid.uuid4()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = tid

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantResolverService(db)
            result = await svc._resolve_path_prefix(
                _mock_request(path="/t/acme/dashboard")
            )
            assert result == tid

        asyncio.run(_run())

    def test_no_prefix_returns_none(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            svc = TenantResolverService(db)
            result = await svc._resolve_path_prefix(_mock_request(path="/api/users"))
            assert result is None

        asyncio.run(_run())

    def test_empty_slug_returns_none(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            svc = TenantResolverService(db)
            result = await svc._resolve_path_prefix(_mock_request(path="/t/"))
            assert result is None

        asyncio.run(_run())

    def test_just_t_returns_none(self) -> None:
        async def _run() -> None:
            db = AsyncMock()
            svc = TenantResolverService(db)
            result = await svc._resolve_path_prefix(_mock_request(path="/t"))
            assert result is None

        asyncio.run(_run())


class TestResolveCustomDomain:
    """Tests for custom domain resolution."""

    def test_custom_domain_resolves_tenant(self) -> None:
        async def _run() -> None:
            tid = uuid.uuid4()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = tid

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantResolverService(db)
            result = await svc._resolve_custom_domain(
                _mock_request(host="auth.acme.com")
            )
            assert result == tid

        asyncio.run(_run())

    def test_unknown_domain_returns_none(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantResolverService(db)
            result = await svc._resolve_custom_domain(
                _mock_request(host="unknown.example.com")
            )
            assert result is None

        asyncio.run(_run())


class TestResolve:
    """Tests for the full resolve chain."""

    def test_subdomain_first(self) -> None:
        async def _run() -> None:
            tid = uuid.uuid4()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = tid

            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TenantResolverService(db)
            result = await svc.resolve(
                _mock_request(host="acme.shomer.io", path="/t/other/page")
            )
            assert result == tid

        asyncio.run(_run())

    def test_falls_back_to_path(self) -> None:
        async def _run() -> None:
            tid = uuid.uuid4()

            # Subdomain lookup returns None, path lookup returns tid
            mock_none = MagicMock()
            mock_none.scalar_one_or_none.return_value = None
            mock_found = MagicMock()
            mock_found.scalar_one_or_none.return_value = tid

            db = AsyncMock()
            db.execute.side_effect = [mock_none, mock_found]

            svc = TenantResolverService(db)
            result = await svc.resolve(
                _mock_request(host="unknown.shomer.io", path="/t/acme/page")
            )
            assert result == tid

        asyncio.run(_run())

    def test_returns_none_when_no_match(self) -> None:
        async def _run() -> None:
            mock_none = MagicMock()
            mock_none.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.return_value = mock_none

            svc = TenantResolverService(db)
            result = await svc.resolve(
                _mock_request(host="localhost", path="/api/users")
            )
            assert result is None

        asyncio.run(_run())


class TestGetHost:
    """Tests for _get_host helper."""

    def test_strips_port(self) -> None:
        req = _mock_request(host="acme.shomer.io:8080")
        assert TenantResolverService._get_host(req) == "acme.shomer.io"

    def test_lowercase(self) -> None:
        req = _mock_request(host="ACME.Shomer.IO")
        assert TenantResolverService._get_host(req) == "acme.shomer.io"

    def test_empty_host(self) -> None:
        req = _mock_request(host="")
        assert TenantResolverService._get_host(req) == ""
