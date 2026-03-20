# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for auth dependencies (get_current_user, get_optional_user)."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from shomer.auth import (
    CurrentUserInfo,
    _try_bearer,
    _try_session,
    get_current_user,
    get_optional_user,
)


def _req(
    auth_header: str | None = None, cookies: dict[str, str] | None = None
) -> MagicMock:
    r = MagicMock()
    r.headers = MagicMock()
    r.headers.get = (
        lambda k, d="": (auth_header if auth_header is not None else d)
        if k == "authorization"
        else d
    )
    cookie_data = cookies or {}
    r.cookies = MagicMock()
    r.cookies.get = lambda k, d=None: cookie_data.get(k, d)
    return r


class TestCurrentUserInfo:
    """Tests for CurrentUserInfo dataclass."""

    def test_defaults(self) -> None:
        user = CurrentUserInfo(user_id=uuid.uuid4())
        assert user.scopes == []
        assert user.tenant_id is None
        assert user.auth_method == "bearer"

    def test_custom_fields(self) -> None:
        uid = uuid.uuid4()
        tid = uuid.uuid4()
        user = CurrentUserInfo(
            user_id=uid, scopes=["openid"], tenant_id=tid, auth_method="session"
        )
        assert user.user_id == uid
        assert user.scopes == ["openid"]
        assert user.tenant_id == tid
        assert user.auth_method == "session"


class TestTryBearer:
    """Tests for _try_bearer()."""

    def test_no_auth_header_returns_none(self) -> None:
        async def _run() -> None:
            result = await _try_bearer(_req(), AsyncMock())
            assert result is None

        asyncio.run(_run())

    def test_bearer_empty_token_returns_none(self) -> None:
        """'Bearer ' with empty token returns None."""

        async def _run() -> None:
            result = await _try_bearer(_req("Bearer "), AsyncMock())
            assert result is None

        asyncio.run(_run())

    @patch("jwt.decode")
    def test_missing_jti_returns_none(self, mock_decode: MagicMock) -> None:
        """Token without jti claim returns None."""

        async def _run() -> None:
            mock_decode.return_value = {"sub": str(uuid.uuid4())}
            result = await _try_bearer(_req("Bearer tok"), AsyncMock())
            assert result is None

        asyncio.run(_run())

    @patch("jwt.decode")
    def test_non_uuid_sub_returns_placeholder(self, mock_decode: MagicMock) -> None:
        """Non-UUID sub (e.g. client_id for M2M) returns placeholder UUID."""

        async def _run() -> None:
            mock_decode.return_value = {
                "jti": "j1",
                "sub": "client-id-not-uuid",
                "scope": "",
            }
            db = AsyncMock()
            mock_at = MagicMock()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = mock_at
            db.execute.return_value = result_mock

            result = await _try_bearer(_req("Bearer tok"), db)
            assert result is not None
            assert result.user_id == uuid.UUID(int=0)

        asyncio.run(_run())

    def test_non_bearer_header_returns_none(self) -> None:
        async def _run() -> None:
            result = await _try_bearer(_req("Basic x"), AsyncMock())
            assert result is None

        asyncio.run(_run())

    def test_invalid_jwt_returns_none(self) -> None:
        async def _run() -> None:
            result = await _try_bearer(_req("Bearer not-a-jwt"), AsyncMock())
            assert result is None

        asyncio.run(_run())

    @patch("jwt.decode")
    def test_revoked_token_returns_none(self, mock_decode: MagicMock) -> None:
        async def _run() -> None:
            mock_decode.return_value = {"jti": "j1", "sub": str(uuid.uuid4())}
            db = AsyncMock()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = None
            db.execute.return_value = result_mock

            result = await _try_bearer(_req("Bearer valid-jwt"), db)
            assert result is None

        asyncio.run(_run())

    @patch("jwt.decode")
    def test_valid_token_returns_user(self, mock_decode: MagicMock) -> None:
        async def _run() -> None:
            uid = uuid.uuid4()
            mock_decode.return_value = {
                "jti": "j1",
                "sub": str(uid),
                "scope": "openid profile",
            }
            db = AsyncMock()
            mock_at = MagicMock()
            result_mock = MagicMock()
            result_mock.scalar_one_or_none.return_value = mock_at
            db.execute.return_value = result_mock

            result = await _try_bearer(_req("Bearer valid-jwt"), db)
            assert result is not None
            assert result.user_id == uid
            assert result.scopes == ["openid", "profile"]
            assert result.auth_method == "bearer"

        asyncio.run(_run())


class TestTrySession:
    """Tests for _try_session()."""

    def test_no_cookie_returns_none(self) -> None:
        async def _run() -> None:
            result = await _try_session(_req(), AsyncMock())
            assert result is None

        asyncio.run(_run())

    @patch("shomer.services.session_service.SessionService")
    def test_invalid_session_returns_none(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = None
            mock_cls.return_value = mock_svc

            result = await _try_session(
                _req(cookies={"session_id": "bad"}), AsyncMock()
            )
            assert result is None

        asyncio.run(_run())

    @patch("shomer.services.session_service.SessionService")
    def test_valid_session_returns_user(self, mock_cls: MagicMock) -> None:
        async def _run() -> None:
            uid = uuid.uuid4()
            mock_session = MagicMock()
            mock_session.user_id = uid
            mock_svc = AsyncMock()
            mock_svc.validate.return_value = mock_session
            mock_cls.return_value = mock_svc

            result = await _try_session(
                _req(cookies={"session_id": "good"}), AsyncMock()
            )
            assert result is not None
            assert result.user_id == uid
            assert result.auth_method == "session"

        asyncio.run(_run())


class TestGetCurrentUser:
    """Tests for get_current_user()."""

    @patch("shomer.auth.resolve_current_user")
    def test_returns_user_when_authenticated(self, mock_resolve: AsyncMock) -> None:
        async def _run() -> None:
            uid = uuid.uuid4()
            mock_resolve.return_value = CurrentUserInfo(user_id=uid)
            result = await get_current_user(MagicMock(), AsyncMock())
            assert result.user_id == uid

        asyncio.run(_run())

    @patch("shomer.auth.resolve_current_user")
    def test_raises_401_when_unauthenticated(self, mock_resolve: AsyncMock) -> None:
        async def _run() -> None:
            mock_resolve.return_value = None
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(MagicMock(), AsyncMock())
            assert exc_info.value.status_code == 401

        asyncio.run(_run())


class TestGetOptionalUser:
    """Tests for get_optional_user()."""

    @patch("shomer.auth.resolve_current_user")
    def test_returns_user_when_authenticated(self, mock_resolve: AsyncMock) -> None:
        async def _run() -> None:
            uid = uuid.uuid4()
            mock_resolve.return_value = CurrentUserInfo(user_id=uid)
            result = await get_optional_user(MagicMock(), AsyncMock())
            assert result is not None
            assert result.user_id == uid

        asyncio.run(_run())

    @patch("shomer.auth.resolve_current_user")
    def test_returns_none_when_unauthenticated(self, mock_resolve: AsyncMock) -> None:
        async def _run() -> None:
            mock_resolve.return_value = None
            result = await get_optional_user(MagicMock(), AsyncMock())
            assert result is None

        asyncio.run(_run())


class TestResolveCurrentUser:
    """Tests for resolve_current_user()."""

    @patch("shomer.auth._try_session")
    @patch("shomer.auth._try_bearer")
    def test_bearer_takes_priority(
        self, mock_bearer: AsyncMock, mock_session: AsyncMock
    ) -> None:
        from shomer.auth import resolve_current_user

        async def _run() -> None:
            uid = uuid.uuid4()
            mock_bearer.return_value = CurrentUserInfo(
                user_id=uid, auth_method="bearer"
            )
            mock_session.return_value = CurrentUserInfo(
                user_id=uuid.uuid4(), auth_method="session"
            )
            result = await resolve_current_user(MagicMock(), AsyncMock())
            assert result is not None
            assert result.auth_method == "bearer"
            mock_session.assert_not_awaited()

        asyncio.run(_run())

    @patch("shomer.auth._try_session")
    @patch("shomer.auth._try_bearer")
    def test_falls_back_to_session(
        self, mock_bearer: AsyncMock, mock_session: AsyncMock
    ) -> None:
        from shomer.auth import resolve_current_user

        async def _run() -> None:
            uid = uuid.uuid4()
            mock_bearer.return_value = None
            mock_session.return_value = CurrentUserInfo(
                user_id=uid, auth_method="session"
            )
            result = await resolve_current_user(MagicMock(), AsyncMock())
            assert result is not None
            assert result.auth_method == "session"

        asyncio.run(_run())

    @patch("shomer.auth._try_session")
    @patch("shomer.auth._try_bearer")
    def test_returns_none_when_both_fail(
        self, mock_bearer: AsyncMock, mock_session: AsyncMock
    ) -> None:
        from shomer.auth import resolve_current_user

        async def _run() -> None:
            mock_bearer.return_value = None
            mock_session.return_value = None
            result = await resolve_current_user(MagicMock(), AsyncMock())
            assert result is None

        asyncio.run(_run())
