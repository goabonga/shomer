# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""The maintenance worker.

An authorization server accumulates state that expires on a clock rather
than on a request — authorization codes, sessions, refresh tokens. Nothing
in the request path is a good place to sweep it: the deletion cost lands
on whichever user happened to arrive at the wrong moment, and it never
runs at all while the service is idle.

A tick is deliberately a plain function of its dependencies rather than a
method on a long-lived object. It takes what it needs, does one pass, and
returns what it did — which is what makes it testable without a scheduler
and safe to call from either the one-shot or the looping entrypoint.

Each completed tick touches a heartbeat file, and `--healthy` reads it.
That is what a liveness probe can call: the worker serves nothing, so
there is no port to ask, and a loop that wedges without anything noticing
is the failure mode this exists for.
"""

from __future__ import annotations

import argparse
import logging
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from shomer_lib.contracts import Clock, Database
from shomer_lib.module import build_container

logger = logging.getLogger("shomer.job")

DEFAULT_INTERVAL_SECONDS = 60.0

# Where a completed tick records that it happened, and how stale that
# record may get before the process counts as wedged. Three intervals
# rather than one: a single slow pass is not a failure, and a probe that
# restarts on one is worse than no probe.
HEARTBEAT_ENV = "SHOMER_JOB_HEARTBEAT"
DEFAULT_MAX_AGE_SECONDS = DEFAULT_INTERVAL_SECONDS * 3


def heartbeat_path() -> Path:
    """The file a completed tick touches.

    Under the system temporary directory, which is the one place the
    container may write: the image runs with a read-only root filesystem
    and an emptyDir mounted at /tmp.
    """
    override = os.environ.get(HEARTBEAT_ENV)
    if override:
        return Path(override)
    return Path(tempfile.gettempdir()) / "shomer-job.heartbeat"


def record_heartbeat(when: float) -> None:
    """Record that a tick finished at `when`."""
    heartbeat_path().write_text(f"{when}\n")


def is_healthy(now: float, max_age: float = DEFAULT_MAX_AGE_SECONDS) -> bool:
    """Whether a tick completed recently enough.

    A missing or unreadable file counts as unhealthy: a worker that has
    never completed a pass is not working, whatever else is true of it.
    The probe that calls this gives startup enough delay that the first
    tick has already landed.
    """
    try:
        recorded = float(heartbeat_path().read_text().strip())
    except (OSError, ValueError):
        return False
    return now - recorded <= max_age


@dataclass(frozen=True, slots=True)
class TickResult:
    """What one pass did.

    Returned rather than logged and discarded so the caller — a test, a
    scheduler wrapper, a future metrics exporter — can assert on it.
    """

    started_at: float
    duration: float
    swept: int


def tick(clock: Clock, database: Database) -> TickResult:
    """Run one maintenance pass.

    There is nothing to sweep yet: the tables that expire on a clock
    arrive with the OAuth 2.0 grants. What exists today is the shape —
    open a unit of work, do the pass inside it, report what happened — so
    the first sweep is a query in this function rather than a new process
    to schedule and supervise.
    """
    started = clock.now()
    with database.session():
        swept = 0
    finished = clock.now()
    duration = finished - started
    record_heartbeat(finished)
    logger.info("tick swept %d expired rows in %.1f ms", swept, duration * 1000)
    return TickResult(started_at=started, duration=duration, swept=swept)


def run_once() -> TickResult:
    """Build a container, run one tick, tear it down."""
    with build_container() as container:
        return tick(container.resolve(Clock), container.resolve(Database))


def run_forever(interval: float = DEFAULT_INTERVAL_SECONDS) -> None:  # pragma: no cover
    """Tick every `interval` seconds until the process is stopped.

    The container is built once and reused: rebuilding it per tick would
    open a new connection pool every interval and leave the previous one
    to be collected whenever.
    """
    with build_container() as container:
        clock = container.resolve(Clock)
        database = container.resolve(Database)
        while True:
            tick(clock, database)
            time.sleep(interval)


def main(argv: list[str] | None = None) -> None:
    """Console-script entrypoint (`shomer-job`)."""
    parser = argparse.ArgumentParser(prog="shomer-job", description=__doc__)
    parser.add_argument(
        "--loop",
        action="store_true",
        help="keep ticking instead of running once and exiting",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL_SECONDS,
        help="seconds between ticks in --loop mode",
    )
    parser.add_argument(
        "--healthy",
        action="store_true",
        help="exit 0 if a tick completed recently, 1 otherwise",
    )
    parser.add_argument(
        "--max-age",
        type=float,
        default=DEFAULT_MAX_AGE_SECONDS,
        help="how stale the last tick may be for --healthy",
    )
    args = parser.parse_args(argv)
    if args.healthy:
        # Reads the clock directly rather than through the container: a
        # liveness probe that builds a container would open a connection
        # pool, on every probe, to read one file.
        raise SystemExit(0 if is_healthy(time.time(), args.max_age) else 1)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.loop:
        run_forever(args.interval)
    else:
        run_once()
