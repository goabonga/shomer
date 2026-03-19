# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Integration tests for authentication UI pages."""

from __future__ import annotations

import asyncio

from httpx import ASGITransport, AsyncClient

from shomer.app import app


class TestAuthUIPages:
    """Tests for GET /ui/register, /ui/verify, /ui/login."""

    def test_register_page(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get("/ui/register")
                assert resp.status_code == 200
                assert "Register" in resp.text

        asyncio.run(_run())

    def test_verify_page(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get("/ui/verify")
                assert resp.status_code == 200
                assert "Verify Email" in resp.text

        asyncio.run(_run())

    def test_login_page(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get("/ui/login")
                assert resp.status_code == 200
                assert "Login" in resp.text

        asyncio.run(_run())

    def test_login_page_with_next(self) -> None:
        async def _run() -> None:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                resp = await client.get("/ui/login?next=/dashboard")
                assert resp.status_code == 200
                assert "/dashboard" in resp.text

        asyncio.run(_run())
