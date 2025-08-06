# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

import asyncio

from shomer import __version__
from shomer.app import app, create_app, lifespan, state, templates


def test_create_app() -> None:
    new_app = create_app()
    assert new_app.title == "Shomer"


def test_lifespan() -> None:
    async def _run() -> None:
        state["status"] = "starting"
        async with lifespan(app):
            assert state["status"] == "ready"
        assert state["status"] == "shutting_down"

    asyncio.run(_run())


def test_app_metadata() -> None:
    assert app.title == "Shomer"
    assert app.version == __version__


def test_templates_directory() -> None:
    assert templates.env.loader is not None
