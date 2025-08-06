# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Health check routes."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


# Imported at function level to avoid circular imports
def _get_state() -> dict[str, str]:
    from shomer.app import state

    return state


@router.get("/liveness", include_in_schema=False)
def liveness() -> JSONResponse:
    """Liveness probe: is the process alive? (k8s livenessProbe / docker HEALTHCHECK)."""
    state = _get_state()
    if state["status"] == "shutting_down":
        return JSONResponse({"status": state["status"]}, status_code=503)
    return JSONResponse({"status": state["status"]}, status_code=200)


@router.get("/readiness", include_in_schema=False)
def readiness() -> JSONResponse:
    """Readiness probe: is the app ready to serve traffic? (k8s readinessProbe)."""
    state = _get_state()
    if state["status"] != "ready":
        return JSONResponse({"status": state["status"]}, status_code=503)
    return JSONResponse({"status": state["status"]}, status_code=200)
