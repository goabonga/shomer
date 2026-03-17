# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Benchmark tests for Argon2id timing targets."""

import time
from typing import Any, Callable, Tuple

import pytest

from shomer.core.security import (
    Argon2Params,
    hash_password,
    make_hasher,
    verify_password,
)

# Acceptable range for default params (time_cost=3, memory=64MiB)
MIN_HASH_MS = 50
MAX_HASH_MS = 2000


def _time_ms(fn: Callable[[], Any]) -> Tuple[Any, float]:
    start = time.perf_counter()
    result = fn()
    elapsed = (time.perf_counter() - start) * 1000
    return result, elapsed


class TestArgon2idBenchmark:
    def test_hash_timing_default_params(self) -> None:
        _, elapsed = _time_ms(lambda: hash_password("benchmark-password"))
        assert elapsed >= MIN_HASH_MS, (
            f"Hash too fast ({elapsed:.1f}ms) - params may be too weak"
        )
        assert elapsed <= MAX_HASH_MS, (
            f"Hash too slow ({elapsed:.1f}ms) - params may be too strong for target"
        )

    def test_verify_timing_default_params(self) -> None:
        h = hash_password("benchmark-password")
        _, elapsed = _time_ms(lambda: verify_password("benchmark-password", h))
        assert elapsed >= MIN_HASH_MS, f"Verify too fast ({elapsed:.1f}ms)"
        assert elapsed <= MAX_HASH_MS, f"Verify too slow ({elapsed:.1f}ms)"

    def test_weak_params_are_faster(self) -> None:
        weak = make_hasher(Argon2Params(time_cost=1, memory_cost=16384))
        _, weak_ms = _time_ms(lambda: hash_password("test", hasher=weak))
        _, default_ms = _time_ms(lambda: hash_password("test"))
        assert weak_ms < default_ms, (
            f"Weak params ({weak_ms:.1f}ms) should be faster "
            f"than defaults ({default_ms:.1f}ms)"
        )

    @pytest.mark.parametrize("time_cost", [1, 2, 3])
    def test_time_cost_scaling(self, time_cost: int) -> None:
        hasher = make_hasher(Argon2Params(time_cost=time_cost, memory_cost=32768))
        _, elapsed = _time_ms(lambda: hash_password("test", hasher=hasher))
        assert elapsed > 0, f"time_cost={time_cost} took {elapsed:.1f}ms"
