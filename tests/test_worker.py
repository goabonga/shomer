# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

from shomer.worker import app


def test_worker_app_name() -> None:
    assert app.main == "shomer"


def test_worker_config() -> None:
    assert app.conf.task_serializer == "json"
    assert app.conf.timezone == "UTC"
    assert app.conf.enable_utc is True


def test_worker_beat_schedule_empty() -> None:
    assert app.conf.beat_schedule == {}


def test_worker_result_backend() -> None:
    assert app.backend is not None
