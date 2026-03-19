# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Integration tests for password management UI pages."""

from __future__ import annotations

import asyncio

from httpx import ASGITransport, AsyncClient

from shomer.app import app


class TestPasswordUIPages:
    """Tests for GET /ui/password/reset, /ui/password/reset-verify, /ui/password/change."""

    def test_forgot_password_page(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get("/ui/password/reset")
                assert resp.status_code == 200
                assert "Forgot Password" in resp.text

        asyncio.run(_run())

    def test_reset_password_page(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get("/ui/password/reset-verify")
                assert resp.status_code == 200
                assert "Reset Password" in resp.text

        asyncio.run(_run())

    def test_reset_password_page_with_token(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get("/ui/password/reset-verify?token=abc123")
                assert resp.status_code == 200
                assert "abc123" in resp.text

        asyncio.run(_run())

    def test_change_password_page(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get("/ui/password/change")
                assert resp.status_code == 200
                assert "Change Password" in resp.text

        asyncio.run(_run())
