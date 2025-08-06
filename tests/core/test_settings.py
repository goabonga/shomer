# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

from shomer.core.settings import Settings, get_settings


def test_default_settings() -> None:
    s = Settings()
    assert s.host == "0.0.0.0"
    assert s.port == 8000
    assert s.startup_delay == 1.0
    assert "postgresql+asyncpg" in s.database_url
    assert "redis" in s.celery_broker_url


def test_celery_backend_defaults_to_broker() -> None:
    s = Settings()
    assert s.celery_backend == s.celery_broker_url


def test_celery_backend_explicit() -> None:
    s = Settings(celery_result_backend="redis://other:6379/1")
    assert s.celery_backend == "redis://other:6379/1"


def test_database_url_sync() -> None:
    s = Settings()
    assert "+asyncpg" not in s.database_url_sync
    assert "postgresql://" in s.database_url_sync


def test_get_settings_cached() -> None:
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
