# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Behave hooks for the shomer-api end-to-end suite.

The base URL comes from `SHOMER_API_URL`, so the same feature files run
against a local `uv run shomer-api` and against the cluster-deployed
instance CI port-forwards onto the same address. What is under test is
the deployed artifact — the image, its chart, its configuration — not the
Python objects a unit test can reach.
"""

from __future__ import annotations

import os

import httpx

DEFAULT_URL = "http://localhost:8000"


def before_all(context) -> None:
    context.base_url = os.environ.get("SHOMER_API_URL", DEFAULT_URL)
    context.client = httpx.Client(base_url=context.base_url, timeout=10.0)


def after_all(context) -> None:
    client = getattr(context, "client", None)
    if client is not None:
        client.close()
