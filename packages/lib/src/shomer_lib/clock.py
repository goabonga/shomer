# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""The system clock."""

from __future__ import annotations

import time


class SystemClock:
    """`Clock` backed by :func:`time.time`."""

    def now(self) -> float:
        """Return the current POSIX timestamp."""
        return time.time()
