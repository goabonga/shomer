# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Application settings using pydantic-settings."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def get_credential(name: str, default: str = "") -> str:
    """Read a secret from a file-based credentials directory or environment.

    Looks for a file named *name* inside the directory pointed to by the
    ``CREDENTIALS_DIRECTORY`` environment variable (set by systemd-creds,
    or manually pointed at a Vault / K8s secrets mount).  Falls back to
    the environment variable *name* if no file is found.

    Parameters
    ----------
    name : str
        Credential name (e.g. ``DATABASE_PASSWORD``).
    default : str
        Value returned when the credential is not found anywhere.

    Returns
    -------
    str
        The credential value.
    """
    creds_dir = os.environ.get("CREDENTIALS_DIRECTORY")
    if creds_dir:
        cred_file = Path(creds_dir) / name
        if cred_file.exists():
            return cred_file.read_text().strip()

    return os.environ.get(name, default)


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    All settings can be overridden via environment variables prefixed
    with ``SHOMER_`` or via a ``.env`` file.

    Attributes
    ----------
    startup_delay : float
        Delay in seconds before accepting requests.
    debug : bool
        Enable development mode (relaxed CORS for localhost).
    cors_allowed_origins : list[str]
        Allowed CORS origins. Empty list means none unless debug mode.
    cors_allow_credentials : bool
        Whether to allow credentials in CORS requests.
    cors_allowed_methods : list[str]
        Allowed HTTP methods for CORS.
    cors_allowed_headers : list[str]
        Allowed HTTP headers for CORS.
    cookie_secure : bool
        Set Secure flag on cookies.
    cookie_httponly : bool
        Set HttpOnly flag on cookies.
    cookie_samesite : str
        SameSite cookie attribute (lax, strict, or none).
    cookie_domain : str
        Cookie domain scope. Empty string means current domain.
    database_host : str
        PostgreSQL server hostname.
    database_port : int
        PostgreSQL server port.
    database_name : str
        PostgreSQL database name.
    database_user : str
        PostgreSQL username.
    database_password : str
        PostgreSQL password (loaded via ``get_credential``).
    redis_host : str
        Redis server hostname.
    redis_port : int
        Redis server port.
    redis_db : int
        Redis database number.
    redis_password : str
        Redis password (loaded via ``get_credential``).
    celery_backend_host : str
        Celery result backend Redis hostname. Defaults to ``redis_host``.
    celery_backend_port : int
        Celery result backend Redis port. Defaults to ``redis_port``.
    celery_backend_db : int
        Celery result backend Redis database number.
    smtp_host : str
        SMTP server hostname.
    smtp_port : int
        SMTP server port.
    smtp_user : str
        SMTP authentication username.
    smtp_password : str
        SMTP authentication password.
    smtp_use_tls : bool
        Whether to use STARTTLS for SMTP connections.
    email_from_address : str
        Default sender email address.
    email_from_name : str
        Default sender display name.
    celery_backend_password : str
        Celery result backend Redis password (loaded via ``get_credential``).
    """

    model_config = SettingsConfigDict(env_prefix="SHOMER_", env_file=".env")

    # Server
    startup_delay: float = 1.0
    debug: bool = False

    # CORS
    cors_allowed_origins: list[str] = []
    cors_allow_credentials: bool = True
    cors_allowed_methods: list[str] = ["*"]
    cors_allowed_headers: list[str] = ["*"]

    # Cookies
    cookie_secure: bool = True
    cookie_httponly: bool = True
    cookie_samesite: str = "lax"
    cookie_domain: str = ""

    # Database
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "shomer"
    database_user: str = "shomer"
    database_password: str = ""

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # Email / SMTP
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_from_address: str = "noreply@shomer.local"
    email_from_name: str = "Shomer"

    # Celery result backend (defaults to broker Redis when empty)
    celery_backend_host: str = ""
    celery_backend_port: int = 0
    celery_backend_db: int = 0
    celery_backend_password: str = ""

    @property
    def database_url(self) -> str:
        """Build async PostgreSQL connection URL."""
        userinfo = self.database_user
        if self.database_password:
            userinfo = f"{userinfo}:{self.database_password}"
        return (
            f"postgresql+asyncpg://{userinfo}"
            f"@{self.database_host}:{self.database_port}"
            f"/{self.database_name}"
        )

    @property
    def database_url_sync(self) -> str:
        """Build sync PostgreSQL connection URL for Alembic."""
        return self.database_url.replace("+asyncpg", "")

    @property
    def celery_broker_url(self) -> str:
        """Build Redis broker URL."""
        if self.redis_password:
            return (
                f"redis://:{self.redis_password}"
                f"@{self.redis_host}:{self.redis_port}"
                f"/{self.redis_db}"
            )
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def celery_backend(self) -> str:
        """Build Celery result backend URL, defaulting to broker Redis."""
        host = self.celery_backend_host or self.redis_host
        port = self.celery_backend_port or self.redis_port
        password = self.celery_backend_password or self.redis_password
        db = self.celery_backend_db
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings(
        database_password=get_credential(
            "DATABASE_PASSWORD",
            os.environ.get("SHOMER_DATABASE_PASSWORD", ""),
        ),
        redis_password=get_credential(
            "REDIS_PASSWORD",
            os.environ.get("SHOMER_REDIS_PASSWORD", ""),
        ),
        celery_backend_password=get_credential(
            "CELERY_BACKEND_PASSWORD",
            os.environ.get("SHOMER_CELERY_BACKEND_PASSWORD", ""),
        ),
    )
