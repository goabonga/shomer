# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""The declarative base every model derives from.

The naming convention is not cosmetic: without it, SQLAlchemy leaves
constraint and index names to the backend, which names them differently
per database and sometimes per version. Alembic then reports a diff for
constraints nobody touched, and a downgrade cannot find what to drop.
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base carrying the shared metadata."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
