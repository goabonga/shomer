# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Tests for the system clock."""

import time

from shomer_lib.clock import SystemClock
from shomer_lib.contracts import Clock


def test_now_reads_the_wall_clock() -> None:
    before = time.time()
    reading = SystemClock().now()
    assert before <= reading <= time.time()


def test_the_system_clock_satisfies_the_contract() -> None:
    assert isinstance(SystemClock(), Clock)
