# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Runtime configuration, read from the environment.

Frozen and resolved once: a service that re-reads `os.environ` mid-flight
can answer two requests differently for reasons nothing records.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

ENV_PREFIX = "SHOMER_"

# SQLite by default so a fresh clone runs with no database to install. It
# is a development default, not a deployment one — every environment sets
# SHOMER_DATABASE_URL.
DEFAULT_DATABASE_URL = "sqlite+pysqlite:///./shomer.db"
DEFAULT_ISSUER = "http://localhost:8000"


@dataclass(frozen=True, slots=True)
class EnvSettings:
    """Settings resolved from `SHOMER_*` environment variables."""

    issuer: str = DEFAULT_ISSUER
    database_url: str = DEFAULT_DATABASE_URL

    @classmethod
    def from_env(cls, prefix: str = ENV_PREFIX) -> EnvSettings:
        """Read `{prefix}ISSUER` and `{prefix}DATABASE_URL`.

        The issuer is normalised without its trailing slash: it is
        concatenated with the OIDC endpoint paths, and `iss` is compared
        by exact string by every conforming client, so one stray slash is
        the difference between a token that validates and one that does
        not.
        """
        issuer = os.environ.get(f"{prefix}ISSUER", DEFAULT_ISSUER).rstrip("/")
        return cls(
            issuer=issuer,
            database_url=os.environ.get(f"{prefix}DATABASE_URL", DEFAULT_DATABASE_URL),
        )
