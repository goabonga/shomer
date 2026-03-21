# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for PARService."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shomer.services.authorize_service import AuthorizeError
from shomer.services.par_service import PARError, PARResponse, PARService


class TestPARService:
    """Tests for PARService.push_authorization_request."""

    def test_success_returns_request_uri(self) -> None:
        """Valid parameters produce a request_uri starting with the URN prefix."""

        async def _run() -> None:
            db = AsyncMock()
            svc = PARService(db)
            with patch.object(
                svc.authorize_service, "validate_request", new_callable=AsyncMock
            ) as mock_validate:
                mock_validate.return_value = None
                resp = await svc.push_authorization_request(
                    client_id="c",
                    redirect_uri="https://app.example.com/cb",
                    response_type="code",
                    scope="openid",
                    state="xyz",
                )
            assert isinstance(resp, PARResponse)
            assert resp.request_uri.startswith("urn:ietf:params:oauth:request_uri:")
            assert resp.expires_in == 60
            db.add.assert_called_once()
            db.flush.assert_awaited_once()

        asyncio.run(_run())

    def test_stores_parameters_as_json(self) -> None:
        """All authorization parameters are stored in the PARRequest."""

        async def _run() -> None:
            db = AsyncMock()
            svc = PARService(db)
            with patch.object(
                svc.authorize_service, "validate_request", new_callable=AsyncMock
            ):
                await svc.push_authorization_request(
                    client_id="c",
                    redirect_uri="https://app.example.com/cb",
                    response_type="code",
                    scope="openid profile",
                    state="xyz",
                    nonce="n1",
                    code_challenge="cc",
                    code_challenge_method="S256",
                )
            par_obj = db.add.call_args[0][0]
            assert par_obj.parameters["client_id"] == "c"
            assert par_obj.parameters["scope"] == "openid profile"
            assert par_obj.parameters["nonce"] == "n1"
            assert par_obj.parameters["code_challenge"] == "cc"
            assert par_obj.parameters["code_challenge_method"] == "S256"

        asyncio.run(_run())

    def test_request_uri_is_unique_per_call(self) -> None:
        """Each call generates a unique request_uri."""

        async def _run() -> None:
            db = AsyncMock()
            svc = PARService(db)
            with patch.object(
                svc.authorize_service, "validate_request", new_callable=AsyncMock
            ):
                r1 = await svc.push_authorization_request(
                    client_id="c",
                    redirect_uri="https://app.example.com/cb",
                    response_type="code",
                    state="a",
                )
                r2 = await svc.push_authorization_request(
                    client_id="c",
                    redirect_uri="https://app.example.com/cb",
                    response_type="code",
                    state="b",
                )
            assert r1.request_uri != r2.request_uri

        asyncio.run(_run())

    def test_validation_error_raises_par_error(self) -> None:
        """AuthorizeError from validation is wrapped in PARError."""

        async def _run() -> None:
            db = AsyncMock()
            svc = PARService(db)
            with patch.object(
                svc.authorize_service,
                "validate_request",
                new_callable=AsyncMock,
                side_effect=AuthorizeError("invalid_request", "client_id is required"),
            ):
                with pytest.raises(PARError) as exc_info:
                    await svc.push_authorization_request(
                        client_id="",
                        response_type="code",
                    )
                assert exc_info.value.error == "invalid_request"
                assert "client_id" in exc_info.value.description

        asyncio.run(_run())

    def test_unsupported_response_type_raises_par_error(self) -> None:
        """Unsupported response_type from validation becomes PARError."""

        async def _run() -> None:
            db = AsyncMock()
            svc = PARService(db)
            with patch.object(
                svc.authorize_service,
                "validate_request",
                new_callable=AsyncMock,
                side_effect=AuthorizeError(
                    "unsupported_response_type", "bad response_type"
                ),
            ):
                with pytest.raises(PARError) as exc_info:
                    await svc.push_authorization_request(
                        client_id="c",
                        response_type="token",
                    )
                assert exc_info.value.error == "unsupported_response_type"

        asyncio.run(_run())

    def test_client_id_stored_on_par_request(self) -> None:
        """The client_id is stored on the PARRequest model."""

        async def _run() -> None:
            db = AsyncMock()
            svc = PARService(db)
            with patch.object(
                svc.authorize_service, "validate_request", new_callable=AsyncMock
            ):
                await svc.push_authorization_request(
                    client_id="my-client",
                    redirect_uri="https://app.example.com/cb",
                    response_type="code",
                    state="xyz",
                )
            par_obj = db.add.call_args[0][0]
            assert par_obj.client_id == "my-client"

        asyncio.run(_run())

    def test_expires_at_set(self) -> None:
        """The PARRequest has an expires_at in the future."""

        async def _run() -> None:
            from datetime import datetime, timezone

            db = AsyncMock()
            svc = PARService(db)
            with patch.object(
                svc.authorize_service, "validate_request", new_callable=AsyncMock
            ):
                await svc.push_authorization_request(
                    client_id="c",
                    redirect_uri="https://app.example.com/cb",
                    response_type="code",
                    state="xyz",
                )
            par_obj = db.add.call_args[0][0]
            assert par_obj.expires_at > datetime.now(timezone.utc)

        asyncio.run(_run())


class TestResolveRequestUri:
    """Tests for PARService.resolve_request_uri."""

    def _make_par(
        self,
        *,
        client_id: str = "c",
        expired: bool = False,
    ) -> MagicMock:
        """Create a mock PARRequest."""
        from datetime import datetime, timedelta, timezone

        par = MagicMock()
        par.client_id = client_id
        par.parameters = {
            "client_id": client_id,
            "redirect_uri": "https://app.example.com/cb",
            "response_type": "code",
            "scope": "openid",
            "state": "xyz",
            "nonce": None,
            "code_challenge": None,
            "code_challenge_method": None,
        }
        if expired:
            par.expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)
        else:
            par.expires_at = datetime.now(timezone.utc) + timedelta(seconds=50)
        return par

    def test_resolve_success(self) -> None:
        """Valid request_uri returns stored parameters and deletes the record."""

        async def _run() -> None:
            mock_par = self._make_par()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_par

            db = AsyncMock()
            db.execute.return_value = mock_result
            svc = PARService(db)

            params = await svc.resolve_request_uri(
                request_uri="urn:ietf:params:oauth:request_uri:abc",
                client_id="c",
            )
            assert params["response_type"] == "code"
            assert params["scope"] == "openid"
            db.delete.assert_awaited_once_with(mock_par)

        asyncio.run(_run())

    def test_unknown_request_uri_raises(self) -> None:
        """Unknown request_uri raises PARError."""

        async def _run() -> None:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None

            db = AsyncMock()
            db.execute.return_value = mock_result
            svc = PARService(db)

            with pytest.raises(PARError) as exc_info:
                await svc.resolve_request_uri(
                    request_uri="urn:ietf:params:oauth:request_uri:unknown",
                    client_id="c",
                )
            assert exc_info.value.error == "invalid_request"
            assert "Unknown" in exc_info.value.description

        asyncio.run(_run())

    def test_client_mismatch_raises(self) -> None:
        """Mismatched client_id raises PARError."""

        async def _run() -> None:
            mock_par = self._make_par(client_id="other-client")
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_par

            db = AsyncMock()
            db.execute.return_value = mock_result
            svc = PARService(db)

            with pytest.raises(PARError) as exc_info:
                await svc.resolve_request_uri(
                    request_uri="urn:ietf:params:oauth:request_uri:abc",
                    client_id="c",
                )
            assert exc_info.value.error == "invalid_request"
            assert "mismatch" in exc_info.value.description

        asyncio.run(_run())

    def test_expired_request_uri_raises(self) -> None:
        """Expired request_uri raises PARError and deletes the record."""

        async def _run() -> None:
            mock_par = self._make_par(expired=True)
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_par

            db = AsyncMock()
            db.execute.return_value = mock_result
            svc = PARService(db)

            with pytest.raises(PARError) as exc_info:
                await svc.resolve_request_uri(
                    request_uri="urn:ietf:params:oauth:request_uri:abc",
                    client_id="c",
                )
            assert exc_info.value.error == "invalid_request"
            assert "expired" in exc_info.value.description
            db.delete.assert_awaited_once_with(mock_par)

        asyncio.run(_run())

    def test_single_use_deletes_record(self) -> None:
        """After resolve, the PARRequest is deleted (single-use)."""

        async def _run() -> None:
            mock_par = self._make_par()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_par

            db = AsyncMock()
            db.execute.return_value = mock_result
            svc = PARService(db)

            await svc.resolve_request_uri(
                request_uri="urn:ietf:params:oauth:request_uri:abc",
                client_id="c",
            )
            db.delete.assert_awaited_once_with(mock_par)
            assert db.flush.await_count >= 1

        asyncio.run(_run())
