# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Application settings using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="SHOMER_", env_file=".env")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    startup_delay: float = 1.0

    # Database
    database_url: str = "postgresql+asyncpg://shomer:shomer@localhost:5432/shomer"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = ""

    @property
    def celery_backend(self) -> str:
        """Return result backend, defaulting to broker URL."""
        return self.celery_result_backend or self.celery_broker_url

    @property
    def database_url_sync(self) -> str:
        """Return sync database URL for Alembic."""
        return self.database_url.replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
