# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

from starlette.requests import Request

from shomer.app import app
from shomer.routes.views import index


def test_index() -> None:
    scope = {"type": "http", "method": "GET", "path": "/", "app": app}
    request = Request(scope)
    response = index(request)
    assert response.status_code == 200
    assert "Shomer" in bytes(response.body).decode()
