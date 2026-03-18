# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""FastAPI application for the Shomer authentication service."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import __version__
from .core.settings import get_settings
from .models import *  # noqa: F401,F403 — register all mappers

settings = get_settings()

state: dict[str, str] = {"status": "starting"}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler."""
    from shomer.core.database import engine

    await asyncio.sleep(settings.startup_delay)
    state["status"] = "ready"
    yield
    state["status"] = "shutting_down"
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Shomer",
        description="OIDC/OAuth2 authentication service.",
        version=__version__,
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )

    application.mount(
        "/static",
        StaticFiles(directory=str(Path(__file__).parent / "static")),
        name="static",
    )

    from shomer.middleware.cors import setup_cors
    from shomer.routes.auth import router as auth_router
    from shomer.routes.docs import router as docs_router
    from shomer.routes.health import router as health_router
    from shomer.routes.jwks import router as jwks_router
    from shomer.routes.views import router as views_router

    setup_cors(application, settings)

    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(docs_router)
    application.include_router(jwks_router)
    application.include_router(views_router)

    return application


templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app = create_app()
