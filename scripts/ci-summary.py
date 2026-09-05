#!/usr/bin/env python3

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Turn a security tool's output into a job summary worth reading.

A summary that says "`grype --fail-on high` on the api SBOM" repeats the
job name and reads the same whether the scan found nothing or forty
things. What a reader needs is what the tool actually found, and — for
the findings that were let through — why.

Reads one report, writes markdown to stdout. A missing or unparseable
report degrades to a one-line note rather than failing: a summary that
turns a green build red because reporting broke is a summary people
delete.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SEVERITY_ORDER = ["Critical", "High", "Medium", "Low", "Negligible", "Unknown"]


def note(message: str) -> int:
    print(f"_{message}_")
    return 0


def load(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        note(f"could not read {path.name}: {exc}")
        return None


def grype(path: Path) -> int:
    """Severity counts, the findings that matter, and what was ignored."""
    report = load(path)
    if report is None:
        return 0

    matches = report.get("matches", [])
    ignored = report.get("ignoredMatches", [])
    counts = Counter(m["vulnerability"].get("severity", "Unknown") for m in matches)

    if not matches and not ignored:
        print("No vulnerabilities matched. ✅")
        return 0

    print("| Severity | Count |")
    print("| --- | ---: |")
    for severity in SEVERITY_ORDER:
        if counts.get(severity):
            print(f"| {severity} | {counts[severity]} |")

    ranked = sorted(
        matches,
        key=lambda m: SEVERITY_ORDER.index(
            m["vulnerability"].get("severity", "Unknown")
        ),
    )
    shown = [
        m
        for m in ranked
        if m["vulnerability"].get("severity") in ("Critical", "High", "Medium")
    ][:20]
    if shown:
        print()
        print("| Severity | ID | Package | Version | Fixed in |")
        print("| --- | --- | --- | --- | --- |")
        for match in shown:
            vuln = match["vulnerability"]
            artifact = match["artifact"]
            fix = ", ".join(vuln.get("fix", {}).get("versions", [])) or "—"
            print(
                f"| {vuln.get('severity')} | {vuln.get('id')} "
                f"| `{artifact.get('name')}` | {artifact.get('version')} | {fix} |"
            )

    # The ignored ones are the point of the allowlist being reviewable.
    # Listing them here is what stops an exception from becoming invisible
    # the day after it was added.
    if ignored:
        print()
        print(f"<details><summary>{len(ignored)} ignored by .grype.yaml</summary>")
        print()
        for match in ignored:
            vuln = match["vulnerability"]
            artifact = match["artifact"]
            print(
                f"- `{vuln.get('id')}` {vuln.get('severity')} — "
                f"`{artifact.get('name')}` {artifact.get('version')}"
            )
        print()
        print("</details>")
    return 0


def sbom(path: Path) -> int:
    """How many packages the image actually ships, and of what kind."""
    report = load(path)
    if report is None:
        return 0
    packages = report.get("packages", [])
    print(f"{len(packages)} packages in the SBOM.")
    return 0


FORMATTERS = {"grype": grype, "sbom": sbom}


def main() -> int:
    if len(sys.argv) != 3:
        return note("ci-summary.py takes <format> <path>")
    fmt, raw_path = sys.argv[1], sys.argv[2]
    formatter = FORMATTERS.get(fmt)
    if formatter is None:
        return note(f"unknown summary format {fmt!r}")
    path = Path(raw_path)
    if not path.is_file():
        return note(f"{raw_path} was not produced")
    return formatter(path)


if __name__ == "__main__":
    sys.exit(main())
