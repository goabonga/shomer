# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

from shomer.core.settings import Settings, get_settings


def test_default_settings() -> None:
    s = Settings()
    assert s.startup_delay == 1.0
    assert s.database_host == "localhost"
    assert s.database_port == 5432
    assert s.database_name == "shomer"
    assert s.database_user == "shomer"
    assert s.redis_host == "localhost"
    assert s.redis_port == 6379


def test_database_url_without_password() -> None:
    s = Settings()
    assert s.database_url == "postgresql+asyncpg://shomer@localhost:5432/shomer"


def test_database_url_with_password() -> None:
    s = Settings(database_password="secret")
    assert s.database_url == "postgresql+asyncpg://shomer:secret@localhost:5432/shomer"


def test_database_url_sync() -> None:
    s = Settings()
    assert "+asyncpg" not in s.database_url_sync
    assert "postgresql://" in s.database_url_sync


def test_celery_broker_url_without_password() -> None:
    s = Settings()
    assert s.celery_broker_url == "redis://localhost:6379/0"


def test_celery_broker_url_with_password() -> None:
    s = Settings(redis_password="redispass")
    assert s.celery_broker_url == "redis://:redispass@localhost:6379/0"


def test_celery_backend_defaults_to_broker() -> None:
    s = Settings()
    assert s.celery_backend == s.celery_broker_url


def test_celery_backend_separate_host() -> None:
    s = Settings(celery_backend_host="backend-redis", celery_backend_port=6380)
    assert s.celery_backend == "redis://backend-redis:6380/0"


def test_celery_backend_with_password() -> None:
    s = Settings(
        celery_backend_host="backend-redis",
        celery_backend_password="backendpass",
    )
    assert s.celery_backend == "redis://:backendpass@backend-redis:6379/0"


def test_celery_backend_inherits_redis_password() -> None:
    s = Settings(redis_password="sharedpass")
    assert s.celery_backend == "redis://:sharedpass@localhost:6379/0"


def test_celery_backend_own_password_overrides_redis() -> None:
    s = Settings(redis_password="shared", celery_backend_password="own")
    assert "own" in s.celery_backend
    assert "shared" not in s.celery_backend


def test_get_settings_cached() -> None:
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
