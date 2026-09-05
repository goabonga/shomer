# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Chris <goabonga@pm.me>

"""Step implementations for the shomer-ssr end-to-end suite."""

from __future__ import annotations

import json
import re

from behave import given, then, when

CONFIG_SELECTOR = "#app-config"


@given("shomer-ssr is reachable at SHOMER_SSR_URL")
def step_reachable(context) -> None:
    response = context.client.get("/healthz")
    assert response.status_code == 200, (
        f"liveness check failed against {context.base_url}: "
        f"status={response.status_code} body={response.text!r}"
    )


@when('I open "{path}"')
def step_open(context, path: str) -> None:
    context.page.goto(f"{context.base_url}{path}", wait_until="networkidle")


@when('I request "{path}"')
def step_request(context, path: str) -> None:
    context.response = context.client.get(path)


@then('the page heading is "{text}"')
def step_heading(context, text: str) -> None:
    # Waits rather than reads: the heading is painted by the bundle, so
    # asserting on the initial document would pass on a page whose script
    # never ran.
    heading = context.page.wait_for_selector("h1", timeout=10_000)
    assert heading.inner_text().strip() == text, (
        f"heading is {heading.inner_text()!r}, want {text!r}"
    )


def _config(context) -> dict[str, str]:
    raw = context.page.inner_text(CONFIG_SELECTOR)
    return json.loads(raw)


@then('the runtime config key "{key}" is not empty')
def step_config_not_empty(context, key: str) -> None:
    value = _config(context).get(key)
    assert value, f"runtime config {key}={value!r} is empty"


@then('the runtime config key "{key}" matches "{pattern}"')
def step_config_matches(context, key: str, pattern: str) -> None:
    value = _config(context).get(key)
    assert isinstance(value, str), f"{key} is not a string: {value!r}"
    assert re.match(pattern, value), f"{key}={value!r} does not match /{pattern}/"


@then('the response content type is "{expected}"')
def step_content_type(context, expected: str) -> None:
    actual = context.response.headers.get("content-type", "")
    assert actual.startswith(expected), f"content-type is {actual!r}, want {expected!r}"
