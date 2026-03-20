# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for TokenService (authorization_code, client_credentials and password grants)."""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import jwt as pyjwt
import pytest

from shomer.services.token_service import TokenError, TokenResponse, TokenService


def _settings() -> MagicMock:
    """Create a mock Settings object."""
    s = MagicMock()
    s.jwt_issuer = "https://test.shomer.local"
    s.jwt_access_token_exp = 3600
    s.jwt_id_token_exp = 3600
    s.jwk_encryption_key = "test-secret-key-that-is-at-least-32-bytes!"
    return s


def _make_auth_code(
    *,
    client_id: str = "test-client",
    redirect_uri: str = "https://app.example.com/cb",
    scopes: str = "openid profile",
    nonce: str | None = None,
    code_challenge: str | None = None,
    code_challenge_method: str | None = None,
    expired: bool = False,
    used: bool = False,
) -> MagicMock:
    """Create a mock AuthorizationCode."""
    now = datetime.now(timezone.utc)
    ac = MagicMock()
    ac.code = "test-code-value"
    ac.user_id = uuid.uuid4()
    ac.client_id = client_id
    ac.redirect_uri = redirect_uri
    ac.scopes = scopes
    ac.nonce = nonce
    ac.code_challenge = code_challenge
    ac.code_challenge_method = code_challenge_method
    ac.expires_at = now - timedelta(hours=1) if expired else now + timedelta(minutes=10)
    ac.is_used = used
    ac.used_at = now if used else None
    return ac


class TestExchangeAuthorizationCode:
    """Tests for TokenService.exchange_authorization_code()."""

    def test_successful_exchange(self) -> None:
        """Successful exchange returns access_token, refresh_token, scope."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            mock_ac = _make_auth_code()
            ac_result = MagicMock()
            ac_result.scalar_one_or_none.return_value = mock_ac
            db.execute.return_value = ac_result

            svc = TokenService(db, _settings())
            resp = await svc.exchange_authorization_code(
                code="test-code",
                client_id="test-client",
                redirect_uri="https://app.example.com/cb",
            )
            assert resp.access_token is not None
            assert resp.refresh_token is not None
            assert resp.token_type == "Bearer"
            assert resp.scope == "openid profile"

        asyncio.run(_run())

    def test_issues_id_token_with_openid_scope(self) -> None:
        """ID token is issued when openid scope is present."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            mock_ac = _make_auth_code(scopes="openid profile", nonce="abc")
            ac_result = MagicMock()
            ac_result.scalar_one_or_none.return_value = mock_ac
            db.execute.return_value = ac_result

            svc = TokenService(db, _settings())
            resp = await svc.exchange_authorization_code(
                code="test-code",
                client_id="test-client",
                redirect_uri="https://app.example.com/cb",
            )
            assert resp.id_token is not None

        asyncio.run(_run())

    def test_no_id_token_without_openid(self) -> None:
        """No ID token when openid scope is absent."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            mock_ac = _make_auth_code(scopes="profile")
            ac_result = MagicMock()
            ac_result.scalar_one_or_none.return_value = mock_ac
            db.execute.return_value = ac_result

            svc = TokenService(db, _settings())
            resp = await svc.exchange_authorization_code(
                code="test-code",
                client_id="test-client",
                redirect_uri="https://app.example.com/cb",
            )
            assert resp.id_token is None

        asyncio.run(_run())

    def test_invalid_code_raises(self) -> None:
        """Invalid code raises TokenError."""

        async def _run() -> None:
            db = AsyncMock()
            ac_result = MagicMock()
            ac_result.scalar_one_or_none.return_value = None
            db.execute.return_value = ac_result

            svc = TokenService(db, _settings())
            with pytest.raises(TokenError, match="Invalid"):
                await svc.exchange_authorization_code(
                    code="nonexistent",
                    client_id="test-client",
                    redirect_uri="https://app.example.com/cb",
                )

        asyncio.run(_run())

    def test_expired_code_raises(self) -> None:
        """Expired code raises TokenError."""

        async def _run() -> None:
            db = AsyncMock()
            mock_ac = _make_auth_code(expired=True)
            ac_result = MagicMock()
            ac_result.scalar_one_or_none.return_value = mock_ac
            db.execute.return_value = ac_result

            svc = TokenService(db, _settings())
            with pytest.raises(TokenError, match="expired"):
                await svc.exchange_authorization_code(
                    code="test-code",
                    client_id="test-client",
                    redirect_uri="https://app.example.com/cb",
                )

        asyncio.run(_run())

    def test_used_code_raises(self) -> None:
        """Already-used code raises TokenError."""

        async def _run() -> None:
            db = AsyncMock()
            mock_ac = _make_auth_code(used=True)
            ac_result = MagicMock()
            ac_result.scalar_one_or_none.return_value = mock_ac
            db.execute.return_value = ac_result

            svc = TokenService(db, _settings())
            with pytest.raises(TokenError, match="already used"):
                await svc.exchange_authorization_code(
                    code="test-code",
                    client_id="test-client",
                    redirect_uri="https://app.example.com/cb",
                )

        asyncio.run(_run())

    def test_client_mismatch_raises(self) -> None:
        """Client mismatch raises TokenError."""

        async def _run() -> None:
            db = AsyncMock()
            mock_ac = _make_auth_code()
            ac_result = MagicMock()
            ac_result.scalar_one_or_none.return_value = mock_ac
            db.execute.return_value = ac_result

            svc = TokenService(db, _settings())
            with pytest.raises(TokenError, match="Client mismatch"):
                await svc.exchange_authorization_code(
                    code="test-code",
                    client_id="wrong-client",
                    redirect_uri="https://app.example.com/cb",
                )

        asyncio.run(_run())

    def test_redirect_uri_mismatch_raises(self) -> None:
        """Redirect URI mismatch raises TokenError."""

        async def _run() -> None:
            db = AsyncMock()
            mock_ac = _make_auth_code()
            ac_result = MagicMock()
            ac_result.scalar_one_or_none.return_value = mock_ac
            db.execute.return_value = ac_result

            svc = TokenService(db, _settings())
            with pytest.raises(TokenError, match="Redirect URI"):
                await svc.exchange_authorization_code(
                    code="test-code",
                    client_id="test-client",
                    redirect_uri="https://evil.com/cb",
                )

        asyncio.run(_run())

    def test_marks_code_as_used(self) -> None:
        """Code is marked as used after exchange."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            mock_ac = _make_auth_code()
            ac_result = MagicMock()
            ac_result.scalar_one_or_none.return_value = mock_ac
            db.execute.return_value = ac_result

            svc = TokenService(db, _settings())
            await svc.exchange_authorization_code(
                code="test-code",
                client_id="test-client",
                redirect_uri="https://app.example.com/cb",
            )
            assert mock_ac.is_used is True
            assert mock_ac.used_at is not None

        asyncio.run(_run())


class TestPKCE:
    """Tests for PKCE verification."""

    def test_pkce_s256_success(self) -> None:
        """Correct S256 PKCE verifier passes."""
        import base64

        verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            mock_ac = _make_auth_code(
                code_challenge=challenge, code_challenge_method="S256"
            )
            ac_result = MagicMock()
            ac_result.scalar_one_or_none.return_value = mock_ac
            db.execute.return_value = ac_result

            svc = TokenService(db, _settings())
            resp = await svc.exchange_authorization_code(
                code="test-code",
                client_id="test-client",
                redirect_uri="https://app.example.com/cb",
                code_verifier=verifier,
            )
            assert resp.access_token is not None

        asyncio.run(_run())

    def test_pkce_missing_verifier_raises(self) -> None:
        """Missing code_verifier when code_challenge is set raises TokenError."""

        async def _run() -> None:
            db = AsyncMock()
            mock_ac = _make_auth_code(
                code_challenge="challenge", code_challenge_method="S256"
            )
            ac_result = MagicMock()
            ac_result.scalar_one_or_none.return_value = mock_ac
            db.execute.return_value = ac_result

            svc = TokenService(db, _settings())
            with pytest.raises(TokenError, match="code_verifier required"):
                await svc.exchange_authorization_code(
                    code="test-code",
                    client_id="test-client",
                    redirect_uri="https://app.example.com/cb",
                )

        asyncio.run(_run())

    def test_pkce_wrong_verifier_raises(self) -> None:
        """Wrong code_verifier raises TokenError."""

        async def _run() -> None:
            db = AsyncMock()
            mock_ac = _make_auth_code(
                code_challenge="correct-challenge", code_challenge_method="S256"
            )
            ac_result = MagicMock()
            ac_result.scalar_one_or_none.return_value = mock_ac
            db.execute.return_value = ac_result

            svc = TokenService(db, _settings())
            with pytest.raises(TokenError, match="PKCE verification failed"):
                await svc.exchange_authorization_code(
                    code="test-code",
                    client_id="test-client",
                    redirect_uri="https://app.example.com/cb",
                    code_verifier="wrong-verifier",
                )

        asyncio.run(_run())


class TestClientCredentials:
    """Tests for TokenService.issue_client_credentials()."""

    def test_successful_issue(self) -> None:
        """Issue access_token with all allowed scopes."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            svc = TokenService(db, _settings())
            resp = await svc.issue_client_credentials(
                client_id="m2m-client",
                client_scopes=["read", "write"],
            )
            assert resp.access_token is not None
            assert resp.token_type == "Bearer"
            assert resp.refresh_token is None
            assert resp.id_token is None
            assert resp.scope == "read write"

        asyncio.run(_run())

    def test_grants_requested_scope_subset(self) -> None:
        """Only requested scopes are granted."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            svc = TokenService(db, _settings())
            resp = await svc.issue_client_credentials(
                client_id="m2m-client",
                client_scopes=["read", "write", "admin"],
                requested_scope="read",
            )
            assert resp.scope == "read"

        asyncio.run(_run())

    def test_grants_all_scopes_when_none_requested(self) -> None:
        """All allowed scopes are granted when no scope is requested."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            svc = TokenService(db, _settings())
            resp = await svc.issue_client_credentials(
                client_id="m2m-client",
                client_scopes=["read", "write"],
            )
            assert resp.scope == "read write"

        asyncio.run(_run())

    def test_invalid_scope_raises(self) -> None:
        """Requesting a scope not allowed by the client raises TokenError."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            svc = TokenService(db, _settings())
            with pytest.raises(TokenError, match="Scope not allowed"):
                await svc.issue_client_credentials(
                    client_id="m2m-client",
                    client_scopes=["read"],
                    requested_scope="read admin",
                )

        asyncio.run(_run())

    def test_no_refresh_token(self) -> None:
        """client_credentials grant must NOT issue a refresh_token."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            svc = TokenService(db, _settings())
            resp = await svc.issue_client_credentials(
                client_id="m2m-client",
                client_scopes=["read"],
            )
            assert resp.refresh_token is None

        asyncio.run(_run())

    def test_no_id_token(self) -> None:
        """client_credentials grant must NOT issue an id_token."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            svc = TokenService(db, _settings())
            resp = await svc.issue_client_credentials(
                client_id="m2m-client",
                client_scopes=["openid"],
                requested_scope="openid",
            )
            assert resp.id_token is None

        asyncio.run(_run())

    def test_access_token_record_has_null_user_id(self) -> None:
        """AccessToken record should have user_id=None for M2M tokens."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            svc = TokenService(db, _settings())
            await svc.issue_client_credentials(
                client_id="m2m-client",
                client_scopes=["read"],
            )
            # Check the AccessToken that was added
            added_obj = db.add.call_args[0][0]
            assert added_obj.user_id is None
            assert added_obj.client_id == "m2m-client"

        asyncio.run(_run())

    def test_subject_is_client_id(self) -> None:
        """JWT subject claim should be the client_id."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            settings = _settings()
            svc = TokenService(db, settings)
            resp = await svc.issue_client_credentials(
                client_id="m2m-client",
                client_scopes=["read"],
            )
            payload = pyjwt.decode(
                resp.access_token,
                settings.jwk_encryption_key,
                algorithms=["HS256"],
                audience="m2m-client",
            )
            assert payload["sub"] == "m2m-client"
            assert payload["aud"] == "m2m-client"

        asyncio.run(_run())


class TestPasswordGrant:
    """Tests for TokenService.issue_password_grant()."""

    def test_successful_password_grant(self) -> None:
        """Valid email + password returns access_token + refresh_token."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_email = MagicMock()
            mock_email.is_primary = True
            mock_email.is_verified = True
            mock_user.emails = [mock_email]

            mock_pw = MagicMock()
            mock_pw.password_hash = "$argon2id$hash"

            pw_result = MagicMock()
            pw_result.scalar_one_or_none.return_value = mock_pw

            with (
                patch(
                    "shomer.models.queries.get_user_by_email",
                    new_callable=AsyncMock,
                    return_value=mock_user,
                ),
                patch(
                    "shomer.core.security.verify_password",
                    return_value=True,
                ),
            ):
                # First execute call: get current password
                db.execute.return_value = pw_result

                svc = TokenService(db, _settings())
                resp = await svc.issue_password_grant(
                    username="user@example.com",
                    password="securepassword123",
                    client_id="test-client",
                )
                assert resp.access_token is not None
                assert resp.refresh_token is not None
                assert resp.token_type == "Bearer"

        asyncio.run(_run())

    def test_password_grant_with_scope(self) -> None:
        """Requested scopes are included in the response."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_email = MagicMock()
            mock_email.is_primary = True
            mock_email.is_verified = True
            mock_user.emails = [mock_email]

            mock_pw = MagicMock()
            mock_pw.password_hash = "$argon2id$hash"

            pw_result = MagicMock()
            pw_result.scalar_one_or_none.return_value = mock_pw

            with (
                patch(
                    "shomer.models.queries.get_user_by_email",
                    new_callable=AsyncMock,
                    return_value=mock_user,
                ),
                patch(
                    "shomer.core.security.verify_password",
                    return_value=True,
                ),
            ):
                db.execute.return_value = pw_result

                svc = TokenService(db, _settings())
                resp = await svc.issue_password_grant(
                    username="user@example.com",
                    password="securepassword123",
                    client_id="test-client",
                    scope="openid profile",
                )
                assert resp.scope == "openid profile"

        asyncio.run(_run())

    def test_unknown_user_raises(self) -> None:
        """Unknown email returns invalid_grant."""

        async def _run() -> None:
            db = AsyncMock()

            with (
                patch(
                    "shomer.models.queries.get_user_by_email",
                    new_callable=AsyncMock,
                    return_value=None,
                ),
                patch("shomer.core.security.hash_password"),
            ):
                svc = TokenService(db, _settings())
                with pytest.raises(TokenError, match="Invalid credentials"):
                    await svc.issue_password_grant(
                        username="nobody@example.com",
                        password="anything",
                        client_id="test-client",
                    )

        asyncio.run(_run())

    def test_wrong_password_raises(self) -> None:
        """Wrong password returns invalid_grant."""

        async def _run() -> None:
            db = AsyncMock()

            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()

            mock_pw = MagicMock()
            mock_pw.password_hash = "$argon2id$hash"

            pw_result = MagicMock()
            pw_result.scalar_one_or_none.return_value = mock_pw

            with (
                patch(
                    "shomer.models.queries.get_user_by_email",
                    new_callable=AsyncMock,
                    return_value=mock_user,
                ),
                patch(
                    "shomer.core.security.verify_password",
                    return_value=False,
                ),
            ):
                db.execute.return_value = pw_result

                svc = TokenService(db, _settings())
                with pytest.raises(TokenError, match="Invalid credentials"):
                    await svc.issue_password_grant(
                        username="user@example.com",
                        password="wrongpassword",
                        client_id="test-client",
                    )

        asyncio.run(_run())

    def test_unverified_email_raises(self) -> None:
        """Unverified email returns invalid_grant."""

        async def _run() -> None:
            db = AsyncMock()

            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_email = MagicMock()
            mock_email.is_primary = True
            mock_email.is_verified = False
            mock_user.emails = [mock_email]

            mock_pw = MagicMock()
            mock_pw.password_hash = "$argon2id$hash"

            pw_result = MagicMock()
            pw_result.scalar_one_or_none.return_value = mock_pw

            with (
                patch(
                    "shomer.models.queries.get_user_by_email",
                    new_callable=AsyncMock,
                    return_value=mock_user,
                ),
                patch(
                    "shomer.core.security.verify_password",
                    return_value=True,
                ),
            ):
                db.execute.return_value = pw_result

                svc = TokenService(db, _settings())
                with pytest.raises(TokenError, match="Email not verified"):
                    await svc.issue_password_grant(
                        username="unverified@example.com",
                        password="securepassword123",
                        client_id="test-client",
                    )

        asyncio.run(_run())

    def test_subject_is_user_id(self) -> None:
        """JWT sub claim should be the user_id."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_email = MagicMock()
            mock_email.is_primary = True
            mock_email.is_verified = True
            mock_user.emails = [mock_email]

            mock_pw = MagicMock()
            mock_pw.password_hash = "$argon2id$hash"

            pw_result = MagicMock()
            pw_result.scalar_one_or_none.return_value = mock_pw

            with (
                patch(
                    "shomer.models.queries.get_user_by_email",
                    new_callable=AsyncMock,
                    return_value=mock_user,
                ),
                patch(
                    "shomer.core.security.verify_password",
                    return_value=True,
                ),
            ):
                db.execute.return_value = pw_result

                settings = _settings()
                svc = TokenService(db, settings)
                resp = await svc.issue_password_grant(
                    username="user@example.com",
                    password="securepassword123",
                    client_id="test-client",
                )
                payload = pyjwt.decode(
                    resp.access_token,
                    settings.jwk_encryption_key,
                    algorithms=["HS256"],
                    audience="test-client",
                )
                assert payload["sub"] == str(mock_user.id)

        asyncio.run(_run())

    def test_no_id_token(self) -> None:
        """password grant does not issue id_token."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_email = MagicMock()
            mock_email.is_primary = True
            mock_email.is_verified = True
            mock_user.emails = [mock_email]

            mock_pw = MagicMock()
            mock_pw.password_hash = "$argon2id$hash"

            pw_result = MagicMock()
            pw_result.scalar_one_or_none.return_value = mock_pw

            with (
                patch(
                    "shomer.models.queries.get_user_by_email",
                    new_callable=AsyncMock,
                    return_value=mock_user,
                ),
                patch(
                    "shomer.core.security.verify_password",
                    return_value=True,
                ),
            ):
                db.execute.return_value = pw_result

                svc = TokenService(db, _settings())
                resp = await svc.issue_password_grant(
                    username="user@example.com",
                    password="securepassword123",
                    client_id="test-client",
                    scope="openid",
                )
                assert resp.id_token is None

        asyncio.run(_run())


class TestTokenResponse:
    """Tests for TokenResponse.to_dict()."""

    def test_minimal_response(self) -> None:
        """Only access_token, token_type, expires_in when no optional fields."""
        resp = TokenResponse(access_token="tok")
        d = resp.to_dict()
        assert d == {"access_token": "tok", "token_type": "Bearer", "expires_in": 3600}
        assert "refresh_token" not in d
        assert "scope" not in d
        assert "id_token" not in d

    def test_full_response(self) -> None:
        """All fields present when set."""
        resp = TokenResponse(
            access_token="tok",
            refresh_token="ref",
            scope="openid",
            id_token="idt",
        )
        d = resp.to_dict()
        assert d["refresh_token"] == "ref"
        assert d["scope"] == "openid"
        assert d["id_token"] == "idt"

    def test_empty_scope_excluded(self) -> None:
        """Empty scope string is excluded from dict."""
        resp = TokenResponse(access_token="tok", scope="")
        d = resp.to_dict()
        assert "scope" not in d


class TestVerifyPKCEPlain:
    """Tests for PKCE plain method."""

    def test_plain_match(self) -> None:
        """Plain PKCE with matching verifier returns True."""
        assert TokenService._verify_pkce("verifier", "verifier", "plain") is True

    def test_plain_mismatch(self) -> None:
        """Plain PKCE with wrong verifier returns False."""
        assert TokenService._verify_pkce("verifier", "wrong", "plain") is False

    def test_unknown_method(self) -> None:
        """Unknown PKCE method returns False."""
        assert TokenService._verify_pkce("v", "c", "unknown") is False


class TestRotateRefreshToken:
    """Tests for TokenService.rotate_refresh_token()."""

    def test_successful_rotation(self) -> None:
        """Valid refresh token returns new access_token + refresh_token."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            mock_rt = MagicMock()
            mock_rt.token_hash = hashlib.sha256(b"raw-token").hexdigest()
            mock_rt.family_id = uuid.uuid4()
            mock_rt.user_id = uuid.uuid4()
            mock_rt.client_id = "test-client"
            mock_rt.scopes = "openid profile"
            mock_rt.revoked = False
            mock_rt.expires_at = datetime.now(timezone.utc) + timedelta(days=30)

            rt_result = MagicMock()
            rt_result.scalar_one_or_none.return_value = mock_rt
            db.execute.return_value = rt_result

            svc = TokenService(db, _settings())
            resp = await svc.rotate_refresh_token(
                refresh_token="raw-token",
                client_id="test-client",
            )
            assert resp.access_token is not None
            assert resp.refresh_token is not None
            assert resp.refresh_token != "raw-token"
            assert mock_rt.revoked is True

        asyncio.run(_run())

    def test_invalid_token_raises(self) -> None:
        """Unknown refresh token raises TokenError."""

        async def _run() -> None:
            db = AsyncMock()
            rt_result = MagicMock()
            rt_result.scalar_one_or_none.return_value = None
            db.execute.return_value = rt_result

            svc = TokenService(db, _settings())
            with pytest.raises(TokenError, match="Invalid refresh token"):
                await svc.rotate_refresh_token(
                    refresh_token="nonexistent",
                    client_id="c",
                )

        asyncio.run(_run())

    def test_reuse_detection_revokes_family(self) -> None:
        """Already-revoked token triggers family-wide revocation."""

        async def _run() -> None:
            db = AsyncMock()
            db.flush = AsyncMock()

            mock_rt = MagicMock()
            mock_rt.revoked = True
            mock_rt.family_id = uuid.uuid4()

            rt_result = MagicMock()
            rt_result.scalar_one_or_none.return_value = mock_rt
            db.execute.return_value = rt_result

            svc = TokenService(db, _settings())
            with pytest.raises(TokenError, match="reuse detected"):
                await svc.rotate_refresh_token(
                    refresh_token="reused-token",
                    client_id="c",
                )
            # execute called twice: SELECT + UPDATE (family revocation)
            assert db.execute.call_count == 2

        asyncio.run(_run())

    def test_expired_token_raises(self) -> None:
        """Expired refresh token raises TokenError."""

        async def _run() -> None:
            db = AsyncMock()

            mock_rt = MagicMock()
            mock_rt.revoked = False
            mock_rt.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

            rt_result = MagicMock()
            rt_result.scalar_one_or_none.return_value = mock_rt
            db.execute.return_value = rt_result

            svc = TokenService(db, _settings())
            with pytest.raises(TokenError, match="expired"):
                await svc.rotate_refresh_token(
                    refresh_token="expired-token",
                    client_id="c",
                )

        asyncio.run(_run())

    def test_client_mismatch_raises(self) -> None:
        """Token for a different client raises TokenError."""

        async def _run() -> None:
            db = AsyncMock()

            mock_rt = MagicMock()
            mock_rt.revoked = False
            mock_rt.client_id = "original-client"
            mock_rt.expires_at = datetime.now(timezone.utc) + timedelta(days=30)

            rt_result = MagicMock()
            rt_result.scalar_one_or_none.return_value = mock_rt
            db.execute.return_value = rt_result

            svc = TokenService(db, _settings())
            with pytest.raises(TokenError, match="Client mismatch"):
                await svc.rotate_refresh_token(
                    refresh_token="tok",
                    client_id="wrong-client",
                )

        asyncio.run(_run())

    def test_old_token_gets_replaced_by(self) -> None:
        """After rotation, old token's replaced_by is set."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            mock_rt = MagicMock()
            mock_rt.revoked = False
            mock_rt.family_id = uuid.uuid4()
            mock_rt.user_id = uuid.uuid4()
            mock_rt.client_id = "test-client"
            mock_rt.scopes = "openid"
            mock_rt.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
            mock_rt.replaced_by = None

            rt_result = MagicMock()
            rt_result.scalar_one_or_none.return_value = mock_rt
            db.execute.return_value = rt_result

            svc = TokenService(db, _settings())
            await svc.rotate_refresh_token(
                refresh_token="tok",
                client_id="test-client",
            )
            # Old token revoked and new token added
            assert mock_rt.revoked is True
            # db.add called for new RefreshToken + AccessToken
            assert db.add.call_count >= 2

        asyncio.run(_run())

    def test_id_token_included_with_openid_scope(self) -> None:
        """Refresh rotation includes id_token when openid scope is present."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            mock_rt = MagicMock()
            mock_rt.revoked = False
            mock_rt.family_id = uuid.uuid4()
            mock_rt.user_id = uuid.uuid4()
            mock_rt.client_id = "test-client"
            mock_rt.scopes = "openid profile"
            mock_rt.expires_at = datetime.now(timezone.utc) + timedelta(days=30)

            rt_result = MagicMock()
            rt_result.scalar_one_or_none.return_value = mock_rt
            db.execute.return_value = rt_result

            svc = TokenService(db, _settings())
            resp = await svc.rotate_refresh_token(
                refresh_token="tok",
                client_id="test-client",
            )
            assert resp.id_token is not None

        asyncio.run(_run())

    def test_no_id_token_without_openid_scope(self) -> None:
        """Refresh rotation excludes id_token without openid scope."""

        async def _run() -> None:
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()

            mock_rt = MagicMock()
            mock_rt.revoked = False
            mock_rt.family_id = uuid.uuid4()
            mock_rt.user_id = uuid.uuid4()
            mock_rt.client_id = "test-client"
            mock_rt.scopes = "profile"
            mock_rt.expires_at = datetime.now(timezone.utc) + timedelta(days=30)

            rt_result = MagicMock()
            rt_result.scalar_one_or_none.return_value = mock_rt
            db.execute.return_value = rt_result

            svc = TokenService(db, _settings())
            resp = await svc.rotate_refresh_token(
                refresh_token="tok",
                client_id="test-client",
            )
            assert resp.id_token is None

        asyncio.run(_run())
