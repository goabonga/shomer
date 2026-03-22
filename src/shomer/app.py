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
    from shomer.middleware.session import SessionMiddleware
    from shomer.routes.auth import router as auth_router
    from shomer.routes.auth_ui import router as auth_ui_router
    from shomer.routes.device_ui import router as device_ui_router
    from shomer.routes.discovery import router as discovery_router
    from shomer.routes.docs import router as docs_router
    from shomer.routes.federation import router as federation_router
    from shomer.routes.health import router as health_router
    from shomer.routes.jwks import router as jwks_router
    from shomer.routes.mfa import router as mfa_router
    from shomer.routes.mfa_ui import router as mfa_ui_router
    from shomer.routes.oauth2 import router as oauth2_router
    from shomer.routes.password_ui import router as password_ui_router
    from shomer.routes.pat import router as pat_router
    from shomer.routes.pat_ui import router as pat_ui_router
    from shomer.routes.profile import router as profile_router
    from shomer.routes.settings_ui import router as settings_ui_router
    from shomer.routes.userinfo import router as userinfo_router
    from shomer.routes.views import router as views_router

    setup_cors(application, settings)
    application.add_middleware(SessionMiddleware)

    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(auth_ui_router)
    application.include_router(password_ui_router)
    application.include_router(oauth2_router)
    application.include_router(docs_router)
    application.include_router(jwks_router)
    application.include_router(discovery_router)
    application.include_router(userinfo_router)
    application.include_router(profile_router)
    application.include_router(settings_ui_router)
    application.include_router(device_ui_router)
    application.include_router(mfa_router)
    application.include_router(mfa_ui_router)
    application.include_router(pat_router)
    application.include_router(pat_ui_router)
    application.include_router(federation_router)
    application.include_router(views_router)

    return application


templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app = create_app()
