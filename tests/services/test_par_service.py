# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for PARService."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

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
