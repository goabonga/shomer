# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Shomer shared library: contracts, settings, models and the DI module."""

from shomer_lib.clock import SystemClock
from shomer_lib.contracts import Clock, Database, Settings
from shomer_lib.database import SqlAlchemyDatabase
from shomer_lib.models import Base, Client, User
from shomer_lib.module import ShomerModule, build_container
from shomer_lib.settings import EnvSettings

__version__ = "0.1.0"

__all__ = [
    "Base",
    "Client",
    "Clock",
    "Database",
    "EnvSettings",
    "Settings",
    "ShomerModule",
    "SqlAlchemyDatabase",
    "SystemClock",
    "User",
    "__version__",
    "build_container",
]
