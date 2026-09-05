# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Tests for the maintenance worker."""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from shomer_job.worker import (
    DEFAULT_INTERVAL_SECONDS,
    HEARTBEAT_ENV,
    heartbeat_path,
    is_healthy,
    main,
    record_heartbeat,
    run_once,
    tick,
)


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
def _isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("SHOMER_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    # Never the real path: a test must not decide whether the machine's
    # own worker looks alive.
    monkeypatch.setenv(HEARTBEAT_ENV, str(tmp_path / "heartbeat"))


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


def test_the_heartbeat_defaults_to_the_temporary_directory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The one place the container may write: the image runs with a
    # read-only root filesystem and an emptyDir mounted at /tmp.
    monkeypatch.delenv(HEARTBEAT_ENV, raising=False)
    assert heartbeat_path().name == "shomer-job.heartbeat"
    assert heartbeat_path().parent == Path(tempfile.gettempdir())


def test_a_worker_that_never_ticked_is_not_healthy() -> None:
    assert not is_healthy(0.0)


def test_an_unreadable_heartbeat_is_not_healthy() -> None:
    # Whatever is in the file, a value that cannot be read is not
    # evidence that a tick completed.
    heartbeat_path().write_text("not a timestamp")
    assert not is_healthy(0.0)


def test_a_recent_tick_is_healthy() -> None:
    record_heartbeat(1_000.0)
    assert is_healthy(1_000.0, max_age=60.0)
    assert is_healthy(1_059.0, max_age=60.0)


def test_a_stale_tick_is_not_healthy() -> None:
    record_heartbeat(1_000.0)
    assert not is_healthy(1_061.0, max_age=60.0)


def test_a_tick_records_its_completion() -> None:
    result = tick(FakeClock([10.0, 10.25]), FakeDatabase())  # type: ignore[arg-type]
    assert float(heartbeat_path().read_text()) == 10.25
    assert result.duration == pytest.approx(0.25)


def test_healthy_exits_zero_when_a_tick_is_recent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record_heartbeat(500.0)
    monkeypatch.setattr("time.time", lambda: 500.0)
    with pytest.raises(SystemExit) as exit_info:
        main(["--healthy"])
    assert exit_info.value.code == 0


def test_healthy_exits_one_when_the_worker_is_wedged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record_heartbeat(0.0)
    monkeypatch.setattr("time.time", lambda: 10_000.0)
    with pytest.raises(SystemExit) as exit_info:
        main(["--healthy"])
    assert exit_info.value.code == 1


def test_healthy_honours_a_custom_max_age(monkeypatch: pytest.MonkeyPatch) -> None:
    record_heartbeat(0.0)
    monkeypatch.setattr("time.time", lambda: 100.0)
    with pytest.raises(SystemExit) as exit_info:
        main(["--healthy", "--max-age", "200"])
    assert exit_info.value.code == 0
