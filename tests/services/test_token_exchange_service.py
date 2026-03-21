# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for TokenExchangeService."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from shomer.services.jwt_validation_service import (
    TokenError,
    TokenValidationResult,
)
from shomer.services.token_exchange_service import (
    TOKEN_EXCHANGE_GRANT,
    ExchangeRequest,
    ExchangeResult,
    TokenExchangeError,
    TokenExchangeService,
    TokenType,
)


def _make_service() -> tuple[TokenExchangeService, MagicMock]:
    """Create a TokenExchangeService with mocked dependencies."""
    settings = MagicMock()
    settings.jwt_issuer = "https://auth.shomer.local"
    settings.jwt_clock_skew = 0
    db = AsyncMock()
    svc = TokenExchangeService(settings, db)
    return svc, svc.jwt_validation  # type: ignore[return-value]


def _valid_result(
    sub: str = "user-123", scope: str = "openid profile"
) -> TokenValidationResult:
    return TokenValidationResult(
        valid=True,
        claims={"sub": sub, "scope": scope, "aud": "client-a"},
    )


def _invalid_result(
    error: TokenError = TokenError.EXPIRED, msg: str = "expired"
) -> TokenValidationResult:
    return TokenValidationResult(valid=False, error=error, error_message=msg)


class TestClientPermission:
    """Tests for client permission check."""

    def test_client_without_exchange_grant_rejected(self) -> None:
        async def _run() -> None:
            svc, jwt_val = _make_service()
            req = ExchangeRequest(
                subject_token="tok",
                subject_token_type=TokenType.ACCESS_TOKEN,
            )
            with pytest.raises(TokenExchangeError) as exc_info:
                await svc.validate_exchange(
                    request=req,
                    client_id="c",
                    client_grant_types=["authorization_code"],
                    client_scopes=["openid"],
                )
            assert exc_info.value.error == "unauthorized_client"

        asyncio.run(_run())

    def test_client_with_exchange_grant_accepted(self) -> None:
        async def _run() -> None:
            svc, jwt_val = _make_service()
            jwt_val.validate = AsyncMock(return_value=_valid_result())
            req = ExchangeRequest(
                subject_token="tok",
                subject_token_type=TokenType.ACCESS_TOKEN,
            )
            result = await svc.validate_exchange(
                request=req,
                client_id="c",
                client_grant_types=[TOKEN_EXCHANGE_GRANT],
                client_scopes=["openid", "profile"],
            )
            assert isinstance(result, ExchangeResult)

        asyncio.run(_run())


class TestSubjectTokenValidation:
    """Tests for subject token validation."""

    def test_expired_subject_token_rejected(self) -> None:
        async def _run() -> None:
            svc, jwt_val = _make_service()
            jwt_val.validate = AsyncMock(
                return_value=_invalid_result(TokenError.EXPIRED, "expired")
            )
            req = ExchangeRequest(
                subject_token="expired-tok",
                subject_token_type=TokenType.ACCESS_TOKEN,
            )
            with pytest.raises(TokenExchangeError) as exc_info:
                await svc.validate_exchange(
                    request=req,
                    client_id="c",
                    client_grant_types=[TOKEN_EXCHANGE_GRANT],
                    client_scopes=["openid"],
                )
            assert exc_info.value.error == "invalid_grant"
            assert "expired" in exc_info.value.description.lower()

        asyncio.run(_run())

    def test_invalid_signature_rejected(self) -> None:
        async def _run() -> None:
            svc, jwt_val = _make_service()
            jwt_val.validate = AsyncMock(
                return_value=_invalid_result(TokenError.INVALID_SIGNATURE, "bad sig")
            )
            req = ExchangeRequest(
                subject_token="bad-tok",
                subject_token_type=TokenType.ACCESS_TOKEN,
            )
            with pytest.raises(TokenExchangeError) as exc_info:
                await svc.validate_exchange(
                    request=req,
                    client_id="c",
                    client_grant_types=[TOKEN_EXCHANGE_GRANT],
                    client_scopes=[],
                )
            assert exc_info.value.error == "invalid_grant"
            assert "signature" in exc_info.value.description.lower()

        asyncio.run(_run())

    def test_malformed_token_rejected(self) -> None:
        async def _run() -> None:
            svc, jwt_val = _make_service()
            jwt_val.validate = AsyncMock(
                return_value=_invalid_result(TokenError.DECODE_ERROR, "malformed")
            )
            req = ExchangeRequest(
                subject_token="garbage",
                subject_token_type=TokenType.ACCESS_TOKEN,
            )
            with pytest.raises(TokenExchangeError) as exc_info:
                await svc.validate_exchange(
                    request=req,
                    client_id="c",
                    client_grant_types=[TOKEN_EXCHANGE_GRANT],
                    client_scopes=[],
                )
            assert exc_info.value.error == "invalid_grant"
            assert "malformed" in exc_info.value.description.lower()

        asyncio.run(_run())

    def test_missing_sub_claim_rejected(self) -> None:
        async def _run() -> None:
            svc, jwt_val = _make_service()
            jwt_val.validate = AsyncMock(
                return_value=TokenValidationResult(
                    valid=True, claims={"scope": "openid"}
                )
            )
            req = ExchangeRequest(
                subject_token="no-sub",
                subject_token_type=TokenType.ACCESS_TOKEN,
            )
            with pytest.raises(TokenExchangeError) as exc_info:
                await svc.validate_exchange(
                    request=req,
                    client_id="c",
                    client_grant_types=[TOKEN_EXCHANGE_GRANT],
                    client_scopes=["openid"],
                )
            assert "sub claim" in exc_info.value.description

        asyncio.run(_run())

    def test_valid_subject_token_extracts_sub(self) -> None:
        async def _run() -> None:
            svc, jwt_val = _make_service()
            jwt_val.validate = AsyncMock(return_value=_valid_result(sub="uid-456"))
            req = ExchangeRequest(
                subject_token="good-tok",
                subject_token_type=TokenType.ACCESS_TOKEN,
            )
            result = await svc.validate_exchange(
                request=req,
                client_id="c",
                client_grant_types=[TOKEN_EXCHANGE_GRANT],
                client_scopes=["openid", "profile"],
            )
            assert result.subject == "uid-456"

        asyncio.run(_run())


class TestScopeComputation:
    """Tests for scope intersection logic."""

    def test_no_requested_scope_uses_subject_filtered(self) -> None:
        async def _run() -> None:
            svc, jwt_val = _make_service()
            jwt_val.validate = AsyncMock(
                return_value=_valid_result(scope="openid profile email")
            )
            req = ExchangeRequest(
                subject_token="tok",
                subject_token_type=TokenType.ACCESS_TOKEN,
            )
            result = await svc.validate_exchange(
                request=req,
                client_id="c",
                client_grant_types=[TOKEN_EXCHANGE_GRANT],
                client_scopes=["openid", "profile"],
            )
            # email not in client_scopes → filtered out
            assert result.scopes == ["openid", "profile"]

        asyncio.run(_run())

    def test_requested_scope_intersection(self) -> None:
        async def _run() -> None:
            svc, jwt_val = _make_service()
            jwt_val.validate = AsyncMock(
                return_value=_valid_result(scope="openid profile email")
            )
            req = ExchangeRequest(
                subject_token="tok",
                subject_token_type=TokenType.ACCESS_TOKEN,
                scope="openid email",
            )
            result = await svc.validate_exchange(
                request=req,
                client_id="c",
                client_grant_types=[TOKEN_EXCHANGE_GRANT],
                client_scopes=["openid", "profile", "email"],
            )
            # requested ∩ subject ∩ client = openid, email
            assert result.scopes == ["email", "openid"]

        asyncio.run(_run())

    def test_requested_scope_not_in_subject_excluded(self) -> None:
        async def _run() -> None:
            svc, jwt_val = _make_service()
            jwt_val.validate = AsyncMock(return_value=_valid_result(scope="openid"))
            req = ExchangeRequest(
                subject_token="tok",
                subject_token_type=TokenType.ACCESS_TOKEN,
                scope="openid profile",
            )
            result = await svc.validate_exchange(
                request=req,
                client_id="c",
                client_grant_types=[TOKEN_EXCHANGE_GRANT],
                client_scopes=["openid", "profile"],
            )
            # profile not in subject → excluded
            assert result.scopes == ["openid"]

        asyncio.run(_run())

    def test_empty_subject_scopes_yields_empty(self) -> None:
        async def _run() -> None:
            svc, jwt_val = _make_service()
            jwt_val.validate = AsyncMock(return_value=_valid_result(scope=""))
            req = ExchangeRequest(
                subject_token="tok",
                subject_token_type=TokenType.ACCESS_TOKEN,
            )
            result = await svc.validate_exchange(
                request=req,
                client_id="c",
                client_grant_types=[TOKEN_EXCHANGE_GRANT],
                client_scopes=["openid"],
            )
            assert result.scopes == []

        asyncio.run(_run())


class TestImpersonation:
    """Tests for impersonation (act-as) flow."""

    def test_impersonation_no_actor_token(self) -> None:
        """Without actor_token, act claim is None (impersonation)."""

        async def _run() -> None:
            svc, jwt_val = _make_service()
            jwt_val.validate = AsyncMock(return_value=_valid_result())
            req = ExchangeRequest(
                subject_token="tok",
                subject_token_type=TokenType.ACCESS_TOKEN,
            )
            result = await svc.validate_exchange(
                request=req,
                client_id="c",
                client_grant_types=[TOKEN_EXCHANGE_GRANT],
                client_scopes=["openid", "profile"],
            )
            assert result.act is None
            assert result.subject == "user-123"

        asyncio.run(_run())


class TestDelegation:
    """Tests for delegation (on-behalf-of) flow with actor token."""

    def test_delegation_with_valid_actor_token(self) -> None:
        async def _run() -> None:
            svc, jwt_val = _make_service()
            jwt_val.validate = AsyncMock(
                side_effect=[
                    _valid_result(sub="user-123"),
                    _valid_result(sub="service-abc"),
                ]
            )
            req = ExchangeRequest(
                subject_token="user-tok",
                subject_token_type=TokenType.ACCESS_TOKEN,
                actor_token="service-tok",
                actor_token_type=TokenType.ACCESS_TOKEN,
            )
            result = await svc.validate_exchange(
                request=req,
                client_id="c",
                client_grant_types=[TOKEN_EXCHANGE_GRANT],
                client_scopes=["openid", "profile"],
            )
            assert result.subject == "user-123"
            assert result.act == {"sub": "service-abc"}

        asyncio.run(_run())

    def test_delegation_invalid_actor_token(self) -> None:
        async def _run() -> None:
            svc, jwt_val = _make_service()
            jwt_val.validate = AsyncMock(
                side_effect=[
                    _valid_result(sub="user-123"),
                    _invalid_result(TokenError.EXPIRED, "expired"),
                ]
            )
            req = ExchangeRequest(
                subject_token="user-tok",
                subject_token_type=TokenType.ACCESS_TOKEN,
                actor_token="bad-actor",
                actor_token_type=TokenType.ACCESS_TOKEN,
            )
            with pytest.raises(TokenExchangeError) as exc_info:
                await svc.validate_exchange(
                    request=req,
                    client_id="c",
                    client_grant_types=[TOKEN_EXCHANGE_GRANT],
                    client_scopes=["openid"],
                )
            assert exc_info.value.error == "invalid_grant"
            assert "Actor token" in exc_info.value.description

        asyncio.run(_run())

    def test_delegation_actor_missing_sub(self) -> None:
        async def _run() -> None:
            svc, jwt_val = _make_service()
            jwt_val.validate = AsyncMock(
                side_effect=[
                    _valid_result(sub="user-123"),
                    TokenValidationResult(valid=True, claims={"scope": "openid"}),
                ]
            )
            req = ExchangeRequest(
                subject_token="user-tok",
                subject_token_type=TokenType.ACCESS_TOKEN,
                actor_token="no-sub-actor",
                actor_token_type=TokenType.ACCESS_TOKEN,
            )
            with pytest.raises(TokenExchangeError) as exc_info:
                await svc.validate_exchange(
                    request=req,
                    client_id="c",
                    client_grant_types=[TOKEN_EXCHANGE_GRANT],
                    client_scopes=["openid"],
                )
            assert "sub claim" in exc_info.value.description

        asyncio.run(_run())

    def test_delegation_missing_actor_token_type(self) -> None:
        async def _run() -> None:
            svc, jwt_val = _make_service()
            jwt_val.validate = AsyncMock(return_value=_valid_result())
            req = ExchangeRequest(
                subject_token="user-tok",
                subject_token_type=TokenType.ACCESS_TOKEN,
                actor_token="actor-tok",
                actor_token_type=None,
            )
            with pytest.raises(TokenExchangeError) as exc_info:
                await svc.validate_exchange(
                    request=req,
                    client_id="c",
                    client_grant_types=[TOKEN_EXCHANGE_GRANT],
                    client_scopes=["openid"],
                )
            assert "actor_token_type" in exc_info.value.description

        asyncio.run(_run())


class TestAudience:
    """Tests for audience resolution."""

    def test_default_audience_is_client_id(self) -> None:
        async def _run() -> None:
            svc, jwt_val = _make_service()
            jwt_val.validate = AsyncMock(return_value=_valid_result())
            req = ExchangeRequest(
                subject_token="tok",
                subject_token_type=TokenType.ACCESS_TOKEN,
            )
            result = await svc.validate_exchange(
                request=req,
                client_id="my-client",
                client_grant_types=[TOKEN_EXCHANGE_GRANT],
                client_scopes=["openid", "profile"],
            )
            assert result.audience == "my-client"

        asyncio.run(_run())

    def test_explicit_audience_overrides_default(self) -> None:
        async def _run() -> None:
            svc, jwt_val = _make_service()
            jwt_val.validate = AsyncMock(return_value=_valid_result())
            req = ExchangeRequest(
                subject_token="tok",
                subject_token_type=TokenType.ACCESS_TOKEN,
                audience="target-service",
            )
            result = await svc.validate_exchange(
                request=req,
                client_id="my-client",
                client_grant_types=[TOKEN_EXCHANGE_GRANT],
                client_scopes=["openid", "profile"],
            )
            assert result.audience == "target-service"

        asyncio.run(_run())


class TestParseTokenType:
    """Tests for TokenExchangeService.parse_token_type."""

    def test_parse_access_token(self) -> None:
        result = TokenExchangeService.parse_token_type(
            "urn:ietf:params:oauth:token-type:access_token"
        )
        assert result == TokenType.ACCESS_TOKEN

    def test_parse_refresh_token(self) -> None:
        result = TokenExchangeService.parse_token_type(
            "urn:ietf:params:oauth:token-type:refresh_token"
        )
        assert result == TokenType.REFRESH_TOKEN

    def test_parse_id_token(self) -> None:
        result = TokenExchangeService.parse_token_type(
            "urn:ietf:params:oauth:token-type:id_token"
        )
        assert result == TokenType.ID_TOKEN

    def test_parse_jwt(self) -> None:
        result = TokenExchangeService.parse_token_type(
            "urn:ietf:params:oauth:token-type:jwt"
        )
        assert result == TokenType.JWT

    def test_parse_none_returns_none(self) -> None:
        assert TokenExchangeService.parse_token_type(None) is None

    def test_parse_empty_returns_none(self) -> None:
        assert TokenExchangeService.parse_token_type("") is None

    def test_parse_unknown_raises(self) -> None:
        with pytest.raises(TokenExchangeError) as exc_info:
            TokenExchangeService.parse_token_type("unknown:type")
        assert exc_info.value.error == "invalid_request"
        assert "Unsupported" in exc_info.value.description
