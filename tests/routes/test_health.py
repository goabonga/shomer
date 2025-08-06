# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

from shomer.app import state
from shomer.routes.health import liveness, readiness


def test_liveness_ready() -> None:
    state["status"] = "ready"
    response = liveness()
    assert response.status_code == 200


def test_liveness_starting() -> None:
    state["status"] = "starting"
    response = liveness()
    assert response.status_code == 200


def test_liveness_shutting_down() -> None:
    state["status"] = "shutting_down"
    response = liveness()
    assert response.status_code == 503


def test_readiness_ready() -> None:
    state["status"] = "ready"
    response = readiness()
    assert response.status_code == 200


def test_readiness_starting() -> None:
    state["status"] = "starting"
    response = readiness()
    assert response.status_code == 503


def test_readiness_shutting_down() -> None:
    state["status"] = "shutting_down"
    response = readiness()
    assert response.status_code == 503
