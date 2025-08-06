# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

from starlette.requests import Request

from shomer.app import app
from shomer.routes.docs import docs, redoc


def _make_request(path: str) -> Request:
    scope = {"type": "http", "method": "GET", "path": path, "app": app}
    return Request(scope)


def test_docs() -> None:
    response = docs(_make_request("/docs"))
    assert response.status_code == 200
    assert "favicon.ico" in bytes(response.body).decode()


def test_redoc() -> None:
    response = redoc(_make_request("/redoc"))
    assert response.status_code == 200
    assert "favicon.ico" in bytes(response.body).decode()
