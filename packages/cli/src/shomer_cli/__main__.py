# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Entrypoint: `shomer [COMMAND] [ARGS...]` and `python -m shomer_cli`."""

from __future__ import annotations

from shomer_lib.module import build_container

from .cli import cli


def main() -> None:
    """Build the container, run the CLI, tear it down on the way out.

    The `with` block is what closes the container, and closing it is what
    disposes the connection pool. Without it a command that touched the
    database leaves sockets open until the process is reaped.
    """
    with build_container() as container:
        cli(obj=container)


if __name__ == "__main__":  # pragma: no cover - module execution entrypoint
    main()
