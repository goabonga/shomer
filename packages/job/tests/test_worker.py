# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Tests for the maintenance worker."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest

from shomer_job.worker import DEFAULT_INTERVAL_SECONDS, main, run_once, tick


class FakeClock:
    """A clock the test moves, so a duration is an assertion not a guess."""

    def __init__(self, readings: list[float]) -> None:
        self._readings = list(readings)

    def now(self) -> float:
        return self._readings.pop(0)


class FakeDatabase:
    """Records whether the tick opened a unit of work."""

    def __init__(self) -> None:
        self.sessions_opened = 0

    @contextmanager
    def session(self) -> Iterator[None]:
        self.sessions_opened += 1
        yield None

    def sessions(self) -> Iterator[None]:  # pragma: no cover - unused here
        yield None

    def close(self) -> None:  # pragma: no cover - unused here
        return None


@pytest.fixture(autouse=True)
def _isolated_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHOMER_DATABASE_URL", "sqlite+pysqlite:///:memory:")


def test_tick_runs_inside_a_unit_of_work() -> None:
    database = FakeDatabase()
    result = tick(FakeClock([10.0, 10.25]), database)  # type: ignore[arg-type]
    assert database.sessions_opened == 1
    assert result.started_at == 10.0
    assert result.duration == pytest.approx(0.25)
    assert result.swept == 0


def test_tick_reports_what_it_did_rather_than_only_logging_it() -> None:
    # The caller — a test, a scheduler wrapper, a metrics exporter — needs
    # something to assert on that is not a log line.
    result = tick(FakeClock([0.0, 0.0]), FakeDatabase())  # type: ignore[arg-type]
    assert result.swept == 0
    with pytest.raises(AttributeError):
        result.swept = 1  # type: ignore[misc]


def test_run_once_builds_and_tears_down_its_own_container() -> None:
    result = run_once()
    assert result.duration >= 0
    assert result.swept == 0


def test_main_runs_a_single_tick_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr("shomer_job.worker.run_once", lambda: calls.append("once"))
    main([])
    assert calls == ["once"]


def test_main_loops_when_asked(monkeypatch: pytest.MonkeyPatch) -> None:
    intervals: list[float] = []
    monkeypatch.setattr(
        "shomer_job.worker.run_forever", lambda interval: intervals.append(interval)
    )
    main(["--loop"])
    assert intervals == [DEFAULT_INTERVAL_SECONDS]


def test_main_honours_a_custom_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    intervals: list[float] = []
    monkeypatch.setattr(
        "shomer_job.worker.run_forever", lambda interval: intervals.append(interval)
    )
    main(["--loop", "--interval", "5"])
    assert intervals == [5.0]


def test_main_reads_argv_when_given_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[Any] = []
    monkeypatch.setattr("sys.argv", ["shomer-job"])
    monkeypatch.setattr("shomer_job.worker.run_once", lambda: calls.append("once"))
    main()
    assert calls == ["once"]
