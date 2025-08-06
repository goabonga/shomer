# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

import subprocess
import sys

import pytest

from shomer import __version__
from shomer.cli import main


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit, match="0"):
        sys.argv = ["shomer", "--version"]
        main()
    captured = capsys.readouterr()
    assert captured.out.strip() == f"shomer v{__version__}"


def test_entrypoint() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "shomer.cli", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert __version__ in result.stdout
