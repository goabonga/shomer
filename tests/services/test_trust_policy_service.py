# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for TrustPolicyService."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from shomer.models.tenant import TenantTrustMode
from shomer.services.trust_policy_service import TrustPolicyService


def _mock_user(
    reg_tenant_id: uuid.UUID | None = None,
) -> MagicMock:
    u = MagicMock()
    u.id = uuid.uuid4()
    u.registration_tenant_id = reg_tenant_id
    return u


def _mock_tenant(
    tenant_id: uuid.UUID | None = None,
    trust_mode: TenantTrustMode = TenantTrustMode.NONE,
    is_active: bool = True,
    trusted_sources: "list[Any] | None" = None,
) -> MagicMock:
    t = MagicMock()
    t.id = tenant_id or uuid.uuid4()
    t.slug = "test"
    t.trust_mode = trust_mode
    t.is_active = is_active
    t.trusted_sources = trusted_sources or []
    return t


def _mock_trusted_source(trusted_tenant_id: uuid.UUID) -> MagicMock:
    s = MagicMock()
    s.trusted_tenant_id = trusted_tenant_id
    return s


class TestCanUserAccessTenant:
    """Tests for trust evaluation with all 4 modes."""

    def test_tenant_not_found(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TrustPolicyService(db)
            allowed, err = await svc.can_user_access_tenant(_mock_user(), uuid.uuid4())
            assert allowed is False
            assert "not found" in (err or "")

        asyncio.run(_run())

    def test_tenant_inactive(self) -> None:
        async def _run() -> None:
            tenant = _mock_tenant(is_active=False)
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = tenant
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TrustPolicyService(db)
            allowed, err = await svc.can_user_access_tenant(_mock_user(), tenant.id)
            assert allowed is False
            assert "inactive" in (err or "")

        asyncio.run(_run())

    def test_none_mode_registered_user_allowed(self) -> None:
        async def _run() -> None:
            tid = uuid.uuid4()
            tenant = _mock_tenant(tenant_id=tid, trust_mode=TenantTrustMode.NONE)
            user = _mock_user(reg_tenant_id=tid)

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = tenant
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TrustPolicyService(db)
            allowed, err = await svc.can_user_access_tenant(user, tid)
            assert allowed is True

        asyncio.run(_run())

    def test_none_mode_external_user_denied(self) -> None:
        async def _run() -> None:
            tid = uuid.uuid4()
            tenant = _mock_tenant(tenant_id=tid, trust_mode=TenantTrustMode.NONE)
            user = _mock_user(reg_tenant_id=uuid.uuid4())

            mock_tenant_result = MagicMock()
            mock_tenant_result.scalar_one_or_none.return_value = tenant
            mock_member_result = MagicMock()
            mock_member_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.side_effect = [mock_tenant_result, mock_member_result]

            svc = TrustPolicyService(db)
            allowed, err = await svc.can_user_access_tenant(user, tid)
            assert allowed is False
            assert "registered" in (err or "")

        asyncio.run(_run())

    def test_all_mode_any_user_allowed(self) -> None:
        async def _run() -> None:
            tenant = _mock_tenant(trust_mode=TenantTrustMode.ALL)
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = tenant
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TrustPolicyService(db)
            allowed, _ = await svc.can_user_access_tenant(_mock_user(), tenant.id)
            assert allowed is True

        asyncio.run(_run())

    def test_members_only_member_allowed(self) -> None:
        async def _run() -> None:
            tid = uuid.uuid4()
            tenant = _mock_tenant(
                tenant_id=tid, trust_mode=TenantTrustMode.MEMBERS_ONLY
            )

            mock_tenant_result = MagicMock()
            mock_tenant_result.scalar_one_or_none.return_value = tenant
            mock_member_result = MagicMock()
            mock_member_result.scalar_one_or_none.return_value = uuid.uuid4()

            db = AsyncMock()
            db.execute.side_effect = [mock_tenant_result, mock_member_result]

            svc = TrustPolicyService(db)
            allowed, _ = await svc.can_user_access_tenant(_mock_user(), tid)
            assert allowed is True

        asyncio.run(_run())

    def test_members_only_non_member_denied(self) -> None:
        async def _run() -> None:
            tid = uuid.uuid4()
            tenant = _mock_tenant(
                tenant_id=tid, trust_mode=TenantTrustMode.MEMBERS_ONLY
            )

            mock_tenant_result = MagicMock()
            mock_tenant_result.scalar_one_or_none.return_value = tenant
            mock_member_result = MagicMock()
            mock_member_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.side_effect = [mock_tenant_result, mock_member_result]

            svc = TrustPolicyService(db)
            allowed, err = await svc.can_user_access_tenant(_mock_user(), tid)
            assert allowed is False
            assert "member" in (err or "")

        asyncio.run(_run())

    def test_specific_mode_trusted_source_allowed(self) -> None:
        async def _run() -> None:
            tid = uuid.uuid4()
            trusted_tid = uuid.uuid4()
            source = _mock_trusted_source(trusted_tid)
            tenant = _mock_tenant(
                tenant_id=tid,
                trust_mode=TenantTrustMode.SPECIFIC,
                trusted_sources=[source],
            )
            user = _mock_user(reg_tenant_id=trusted_tid)

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = tenant
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TrustPolicyService(db)
            allowed, _ = await svc.can_user_access_tenant(user, tid)
            assert allowed is True

        asyncio.run(_run())

    def test_specific_mode_untrusted_denied(self) -> None:
        async def _run() -> None:
            tid = uuid.uuid4()
            source = _mock_trusted_source(uuid.uuid4())
            tenant = _mock_tenant(
                tenant_id=tid,
                trust_mode=TenantTrustMode.SPECIFIC,
                trusted_sources=[source],
            )
            user = _mock_user(reg_tenant_id=uuid.uuid4())

            mock_tenant_result = MagicMock()
            mock_tenant_result.scalar_one_or_none.return_value = tenant
            mock_member_result = MagicMock()
            mock_member_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.side_effect = [mock_tenant_result, mock_member_result]

            svc = TrustPolicyService(db)
            allowed, err = await svc.can_user_access_tenant(user, tid)
            assert allowed is False
            assert "not authorized" in (err or "")

        asyncio.run(_run())


class TestIsFromTrustedSource:
    """Tests for _is_from_trusted_source static method."""

    def test_none_registration_tenant(self) -> None:
        assert TrustPolicyService._is_from_trusted_source(None, []) is False

    def test_matching_source(self) -> None:
        tid = uuid.uuid4()
        source = _mock_trusted_source(tid)
        assert TrustPolicyService._is_from_trusted_source(tid, [source]) is True

    def test_no_matching_source(self) -> None:
        source = _mock_trusted_source(uuid.uuid4())
        assert (
            TrustPolicyService._is_from_trusted_source(uuid.uuid4(), [source]) is False
        )


class TestTrustCRUD:
    """Tests for trust CRUD operations."""

    def test_update_trust_mode(self) -> None:
        async def _run() -> None:
            tenant = MagicMock()
            tenant.trust_mode = TenantTrustMode.NONE
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = tenant
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TrustPolicyService(db)
            result = await svc.update_trust_mode(uuid.uuid4(), TenantTrustMode.ALL)
            assert result is True
            assert tenant.trust_mode == TenantTrustMode.ALL

        asyncio.run(_run())

    def test_update_trust_mode_not_found(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TrustPolicyService(db)
            result = await svc.update_trust_mode(uuid.uuid4(), TenantTrustMode.ALL)
            assert result is False

        asyncio.run(_run())

    def test_add_trusted_source(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TrustPolicyService(db)
            result = await svc.add_trusted_source(uuid.uuid4(), uuid.uuid4())
            assert result is not None
            db.add.assert_called_once()

        asyncio.run(_run())

    def test_add_trusted_source_duplicate(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = MagicMock()
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TrustPolicyService(db)
            result = await svc.add_trusted_source(uuid.uuid4(), uuid.uuid4())
            assert result is None

        asyncio.run(_run())

    def test_remove_trusted_source(self) -> None:
        async def _run() -> None:
            existing = MagicMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = existing
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TrustPolicyService(db)
            result = await svc.remove_trusted_source(uuid.uuid4(), uuid.uuid4())
            assert result is True
            db.delete.assert_awaited_once()

        asyncio.run(_run())

    def test_remove_trusted_source_not_found(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TrustPolicyService(db)
            result = await svc.remove_trusted_source(uuid.uuid4(), uuid.uuid4())
            assert result is False

        asyncio.run(_run())


class TestPlatformTenant:
    """Tests for platform tenant operations."""

    def test_get_platform_tenant(self) -> None:
        async def _run() -> None:
            platform = MagicMock()
            platform.is_platform = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = platform
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TrustPolicyService(db)
            result = await svc.get_platform_tenant()
            assert result is platform

        asyncio.run(_run())

    def test_get_platform_tenant_none(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TrustPolicyService(db)
            result = await svc.get_platform_tenant()
            assert result is None

        asyncio.run(_run())

    def test_is_platform_trusted_true(self) -> None:
        async def _run() -> None:
            platform = MagicMock()
            platform.id = uuid.uuid4()

            mock_platform_result = MagicMock()
            mock_platform_result.scalar_one_or_none.return_value = platform
            mock_source_result = MagicMock()
            mock_source_result.scalar_one_or_none.return_value = uuid.uuid4()

            db = AsyncMock()
            db.execute.side_effect = [mock_platform_result, mock_source_result]

            svc = TrustPolicyService(db)
            result = await svc.is_platform_trusted(uuid.uuid4())
            assert result is True

        asyncio.run(_run())

    def test_is_platform_trusted_false(self) -> None:
        async def _run() -> None:
            platform = MagicMock()
            platform.id = uuid.uuid4()

            mock_platform_result = MagicMock()
            mock_platform_result.scalar_one_or_none.return_value = platform
            mock_source_result = MagicMock()
            mock_source_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.side_effect = [mock_platform_result, mock_source_result]

            svc = TrustPolicyService(db)
            result = await svc.is_platform_trusted(uuid.uuid4())
            assert result is False

        asyncio.run(_run())

    def test_is_platform_trusted_no_platform(self) -> None:
        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            db = AsyncMock()
            db.execute.return_value = mock_result

            svc = TrustPolicyService(db)
            result = await svc.is_platform_trusted(uuid.uuid4())
            assert result is False

        asyncio.run(_run())
